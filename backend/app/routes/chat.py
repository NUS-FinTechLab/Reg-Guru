"""Chat-related HTTP handlers."""

from __future__ import annotations

from flask import jsonify, request

from ..models import ChatMessage, ChatSession, User
from ..utils import process_chat_query
from . import api
from .serializers import serialize_message, serialize_session


@api.route("/chat", methods=["POST"])
def chat():
    """Handle chat queries using the RAG system."""
    data = request.json or {}
    print("Received data:", data)

    user_message = data.get("message", {}).get("text", "").strip()
    region = (data.get("region") or "us").lower()
    chat_external_id = str(data.get("chatId") or data.get("chat_id") or "").strip()
    user_id = str(
        data.get("userId")
        or data.get("user_id")
        or (data.get("user") or {}).get("id")
        or ""
    ).strip()

    valid_regions = ["us", "eu", "sg"]
    if region not in valid_regions:
        return (
            jsonify(
                {"error": f"Invalid region '{region}'. Must be one of: {valid_regions}"}
            ),
            400,
        )

    if not chat_external_id:
        return jsonify({"error": "chatId is required"}), 400

    if not user_message:
        return jsonify({"error": "message text is required"}), 400

    if not user_id:
        return jsonify({"error": "userId is required"}), 400

    user = User.get_by_id(user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404

    try:
        session = ChatSession.upsert(chat_external_id, region, user.id)

        user_message_obj = ChatMessage.create(
            session_id=session.id,
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
            session_id=session.id,
            role="bot",
            body=response,
            sources=source_list,
        )

        print("Sources:", sources)
        return (
            jsonify(
                {
                    "response": response,
                    "sources": source_list,
                    "session": serialize_session(session),
                    "messages": {
                        "user": serialize_message(user_message_obj),
                        "bot": serialize_message(bot_message_obj),
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
