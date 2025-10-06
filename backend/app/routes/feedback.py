"""Feedback-related HTTP handlers."""

from __future__ import annotations

from flask import jsonify, request

from ..utils import log_feedback
from . import api


@api.route("/log_feedback", methods=["POST"])
def log_feedback_route():
    """Log user feedback."""
    data = request.json or {}

    try:
        chat_external_id = str(data.get("chatId", "")).strip()
        if not chat_external_id:
            return jsonify({"error": "chatId is required"}), 400

        message_id = data.get("messageId")
        if message_id is not None:
            try:
                message_id = int(message_id)
            except (TypeError, ValueError):
                return jsonify({"error": "messageId must be numeric"}), 400

        log_feedback(
            chat_external_id=chat_external_id,
            rating=data.get("rating", ""),
            comments=data.get("comments", ""),
            message_id=message_id,
        )
        return jsonify({"status": "feedback recorded"}), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
