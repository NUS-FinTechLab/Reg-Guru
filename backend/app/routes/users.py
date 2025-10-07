"""User management endpoints."""

from __future__ import annotations

from flask import jsonify, request

from ..auth import decode_auth_header
from ..models import ChatSession, User
from . import api
from .serializers import serialize_session, serialize_user


@api.route("/users", methods=["GET"])
def list_users():
    auth_header = request.headers.get("Authorization")
    if auth_header:
        try:
            decode_auth_header(auth_header)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 401

    users = [serialize_user(user) for user in User.list_all()]
    return jsonify({"users": users}), 200


@api.route("/users/<string:user_id>", methods=["GET"])
def get_user(user_id: str):
    auth_header = request.headers.get("Authorization")
    if auth_header:
        try:
            decode_auth_header(auth_header)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 401

    user = User.get_by_id(user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": serialize_user(user)}), 200


@api.route("/users/<string:user_id>/chats", methods=["GET"])
def get_user_chats(user_id: str):
    auth_header = request.headers.get("Authorization")
    if auth_header:
        try:
            decode_auth_header(auth_header)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 401

    user = User.get_by_id(user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404

    chats = [serialize_session(chat) for chat in ChatSession.list_for_user(user.id)]
    return jsonify({"user": serialize_user(user), "chats": chats}), 200
