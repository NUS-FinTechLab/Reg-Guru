"""Session-related HTTP handlers."""

from __future__ import annotations

from uuid import UUID

from flask import g, jsonify

from ..models import Chat
from . import api
from .serializers import serialize_chat, serialize_message


@api.route("/chat/<string:chat_id>", methods=["GET"])
def get_chat(chat_id: str):
    try:
        chat_uuid = str(UUID(chat_id))
    except ValueError:
        return jsonify({"error": "Invalid chat id"}), 400

    chat = Chat.get_by_id(chat_uuid)
    if chat is None:
        return jsonify({"error": "Chat not found"}), 404

    authenticated_user_id = getattr(g, "authenticated_user_id", None)
    if authenticated_user_id and str(chat.user_id) != str(authenticated_user_id):
        return jsonify({"error": "Authenticated user mismatch"}), 403

    messages = [serialize_message(message) for message in chat.list_messages()]

    return (
        jsonify(
            {
                "chat": serialize_chat(chat),
                "messages": messages,
            }
        ),
        200,
    )
