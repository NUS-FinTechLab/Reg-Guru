"""Chat-related HTTP handlers."""

from __future__ import annotations

from uuid import UUID

from flask import g, jsonify, request

from ..models import Chat, ChatMessage, User
from ..utils import process_chat_query
from . import api
from .serializers import serialize_chat, serialize_message


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

        user_message_obj = ChatMessage.create(
            chat_id=chat.id,
            user_id=user.id,
            role="user",
            body=user_message,
            sources=[],
        )

        result = process_chat_query(user_message, region)
        if isinstance(result, tuple):
            response, sources = result
        else:
            response = result
            sources = {"sources": []}

        source_list = sources.get("sources", [])

        bot_message_obj = ChatMessage.create(
            chat_id=chat.id,
            user_id=chat.user_id,
            role="ai",
            body=response,
            sources=source_list,
        )

        print("Sources:", sources)
        return (
            jsonify(
                {
                    "response": response,
                    "sources": source_list,
                    "chat": serialize_chat(chat),
                    "messages": {
                        "user": serialize_message(user_message_obj),
                        "ai": serialize_message(bot_message_obj),
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
