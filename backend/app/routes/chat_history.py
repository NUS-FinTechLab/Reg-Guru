"""Chat history HTTP handlers."""

from __future__ import annotations

from uuid import UUID

from flask import g, jsonify, request

from ..models import Chat, ChatHistory
from . import api
from .serializers import serialize_history_entry


@api.route("/chat/<string:chat_id>/history", methods=["GET"])
def list_chat_history_for_chat(chat_id: str):
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

    history = [
        serialize_history_entry(entry)
        for entry in ChatHistory.list_recent(chat_id=chat.id)
    ]
    return jsonify({"history": history}), 200


@api.route("/chat/<string:chat_id>/history", methods=["POST"])
def create_chat_history_entry(chat_id: str):
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

    data = request.json or {}
    query_text = (data.get("query") or "").strip()
    response_summary = (data.get("responseSummary") or "").strip() or None

    if not query_text:
        return jsonify({"error": "query is required"}), 400

    entry = ChatHistory.create(
        query_text=query_text,
        response_summary=response_summary,
        chat_id=chat.id,
    )
    return jsonify({"historyEntry": serialize_history_entry(entry)}), 201


@api.route("/chat_history", methods=["GET"])
def list_recent_history():
    limit = request.args.get("limit", type=int) or 25
    history = [
        serialize_history_entry(entry)
        for entry in ChatHistory.list_recent(limit=limit)
    ]
    return jsonify({"history": history, "limit": limit}), 200
