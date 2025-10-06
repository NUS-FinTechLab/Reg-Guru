"""Session-related HTTP handlers."""

from __future__ import annotations

from flask import jsonify

from ..models import ChatSession
from . import api
from .serializers import serialize_message, serialize_session


@api.route("/chat/<string:chat_external_id>", methods=["GET"])
def get_chat(chat_external_id: str):
    session = ChatSession.get_by_external_id(chat_external_id)
    if session is None:
        return jsonify({"error": "Chat session not found"}), 404

    messages = [serialize_message(message) for message in session.list_messages()]

    return (
        jsonify(
            {
                "session": serialize_session(session),
                "messages": messages,
            }
        ),
        200,
    )
