"""User management endpoints."""

from __future__ import annotations

from flask import jsonify

from ..models import Chat, User
from . import api
from .serializers import serialize_chat, serialize_user


@api.route("/users", methods=["GET"])
def list_users():
    users = [serialize_user(user) for user in User.list_all()]
    return jsonify({"users": users}), 200


@api.route("/users/<string:user_id>", methods=["GET"])
def get_user(user_id: str):
    user = User.get_by_id(user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": serialize_user(user)}), 200


@api.route("/users/<string:user_id>/chats", methods=["GET"])
def get_user_chats(user_id: str):
    user = User.get_by_id(user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404

    chats = [serialize_chat(chat) for chat in Chat.list_for_user(user.id)]
    return jsonify({"user": serialize_user(user), "chats": chats}), 200
