"""Chat-related HTTP handlers."""

from __future__ import annotations

from uuid import UUID

from flask import g, jsonify, request

from ..models import Chat, ChatMessage, User
from ..utils import process_chat_query
from . import api
from .serializers import serialize_chat, serialize_message


MAX_SESSION_CONTEXT_CHARS = 3000
MAX_SESSION_HISTORY_MESSAGES = 10
MAX_MESSAGE_SNIPPET_CHARS = 320


def _render_session_context(chat: Chat, history: list[ChatMessage]) -> str:
    lines: list[str] = [
        "Chat metadata:",
        f"- chat_id: {chat.id}",
        f"- user_id: {chat.user_id}",
        f"- created_at: {chat.created_at.isoformat()}",
        f"- updated_at: {chat.updated_at.isoformat()}",
    ]

    if history:
        lines.append("")
        lines.append("Recent messages (oldest to newest):")
        for message in history:
            content = " ".join((message.body or "").split())
            if len(content) > MAX_MESSAGE_SNIPPET_CHARS:
                content = f"{content[:MAX_MESSAGE_SNIPPET_CHARS].rstrip()}…"
            role = "User" if message.role == "user" else "Assistant"
            lines.append(
                f"[{message.created_at.isoformat()}] {role}: {content or '[no content recorded]'}"
            )
    else:
        lines.append("")
        lines.append("No previous messages recorded for this chat.")

    rendered = "\n".join(lines).strip()
    if len(rendered) <= MAX_SESSION_CONTEXT_CHARS:
        return rendered

    metadata_section = "\n".join(lines[:5]).strip()
    history_section = "\n".join(lines[5:]).strip()
    if not history_section:
        return metadata_section

    available_chars = MAX_SESSION_CONTEXT_CHARS - len(metadata_section) - 1
    if available_chars <= 0:
        return metadata_section

    trimmed_history = history_section[-available_chars:]
    return f"{metadata_section}\n{trimmed_history.strip()}"


@api.route("/chats", methods=["GET"])
def list_user_chats():
    authenticated_user_id = getattr(g, "authenticated_user_id", None)
    if not authenticated_user_id:
        return jsonify({"error": "Authenticated user mismatch"}), 403

    chats = []
    for item in Chat.list_with_last_message_for_user(authenticated_user_id):
        chat = item["chat"]
        last_message = item["last_message"]
        chat_payload = {
            **chat.to_api_dict(),
            "lastMessage": last_message,
        }
        chats.append(chat_payload)

    return jsonify({"chats": chats}), 200


@api.route("/chat", methods=["POST"])
def chat():
    """Handle chat queries using the RAG system."""
    data = request.json or {}
    print("Received data:", data)

    user_message = data.get("message", {}).get("text", "").strip()
    region = (data.get("region") or "us").lower()
    raw_chat_id = str(data.get("chatId") or data.get("chat_id") or "").strip()
    chat_id: UUID | str | None = raw_chat_id or None
    user_id = str(
        data.get("userId")
        or data.get("user_id")
        or (data.get("user") or {}).get("id")
        or ""
    ).strip()

    authenticated_user_id = getattr(g, "authenticated_user_id", None)
    if authenticated_user_id and user_id != authenticated_user_id:
        return jsonify({"error": "Authenticated user mismatch"}), 403

    valid_regions = ["us", "eu", "sg"]
    if region not in valid_regions:
        return (
            jsonify(
                {"error": f"Invalid region '{region}'. Must be one of: {valid_regions}"}
            ),
            400,
        )

    if not user_message:
        return jsonify({"error": "message text is required"}), 400

    if not user_id:
        return jsonify({"error": "userId is required"}), 400

    user = User.get_by_id(user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404

    if chat_id is not None:
        try:
            chat_id = str(UUID(str(chat_id)))
        except ValueError:
            return jsonify({"error": "chatId must be a valid UUID"}), 400

    try:
        chat = Chat.ensure(chat_id, user.id)

        history_messages = ChatMessage.list_recent_for_chat(
            chat.id,
            limit=MAX_SESSION_HISTORY_MESSAGES,
        )
        session_context = _render_session_context(chat, history_messages)

        user_message_obj = ChatMessage.create(
            chat_id=chat.id,
            user_id=user.id,
            role="user",
            body=user_message,
            sources=[],
        )

        result = process_chat_query(
            user_message,
            region,
            session_context=session_context,
        )
        metadata = {}
        if isinstance(result, tuple) and len(result) == 2:
            response, metadata = result
        else:
            response = result

        source_list = metadata.get("sources") if isinstance(metadata, dict) else []
        if not isinstance(source_list, list):
            source_list = []

        should_create_checklist = False
        if isinstance(metadata, dict):
            should_create_checklist = bool(
                metadata.get("should_create_checklist", False)
            )

        bot_message_obj = ChatMessage.create(
            chat_id=chat.id,
            user_id=None,
            role="ai",
            body=response,
            sources=source_list,
        )

        ai_message_payload = serialize_message(bot_message_obj)
        ai_message_payload["shouldCreateChecklist"] = should_create_checklist

        print("Sources:", source_list)
        return (
            jsonify(
                {
                    "response": response,
                    "sources": source_list,
                    "shouldCreateChecklist": should_create_checklist,
                    "chat": serialize_chat(chat),
                    "messages": {
                        "user": serialize_message(user_message_obj),
                        "ai": ai_message_payload,
                    },
                }
            ),
            200,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except FileNotFoundError as exc:
        return jsonify({"error": str(exc)}), 404
    except Exception as exc:  # pragma: no cover - best effort logging
        print(f"Error during query processing: {exc}")
        return jsonify({"error": f"Failed to process query: {exc}"}), 500
