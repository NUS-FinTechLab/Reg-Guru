"""Chat history HTTP handlers."""

from __future__ import annotations

from flask import jsonify, request

from ..auth import decode_auth_header
from ..models import ChatHistory, ChatSession
from . import api
from .serializers import serialize_history_entry


@api.route("/chat/<string:chat_external_id>/history", methods=["GET"])
def list_chat_history_for_chat(chat_external_id: str):
    auth_header = request.headers.get("Authorization")
    if auth_header:
        try:
            decode_auth_header(auth_header)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 401

    session = ChatSession.get_by_external_id(chat_external_id)
    if session is None:
        return jsonify({"error": "Chat session not found"}), 404

    history = [
        serialize_history_entry(entry)
        for entry in ChatHistory.list_recent(chat_id=session.id)
    ]
    return jsonify({"history": history}), 200


@api.route("/chat/<string:chat_external_id>/history", methods=["POST"])
def create_chat_history_entry(chat_external_id: str):
    auth_header = request.headers.get("Authorization")
    if auth_header:
        try:
            decode_auth_header(auth_header)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 401

    session = ChatSession.get_by_external_id(chat_external_id)
    if session is None:
        return jsonify({"error": "Chat session not found"}), 404

    data = request.json or {}
    query_text = (data.get("query") or "").strip()
    response_summary = (data.get("responseSummary") or "").strip() or None

    if not query_text:
        return jsonify({"error": "query is required"}), 400

    entry = ChatHistory.create(
        query_text=query_text,
        response_summary=response_summary,
        chat_id=session.id,
        chat_external_id=session.external_id,
    )
    return jsonify({"historyEntry": serialize_history_entry(entry)}), 201


@api.route("/chat_history", methods=["GET"])
def list_recent_history():
    auth_header = request.headers.get("Authorization")
    if auth_header:
        try:
            decode_auth_header(auth_header)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 401

    limit = request.args.get("limit", type=int) or 25
    history = [
        serialize_history_entry(entry)
        for entry in ChatHistory.list_recent(limit=limit)
    ]
    return jsonify({"history": history, "limit": limit}), 200
