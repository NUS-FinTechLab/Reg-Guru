"""Authentication handlers for user registration and login."""

from __future__ import annotations

from flask import jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from ..auth import generate_jwt
from ..models import User
from . import api
from .serializers import serialize_user


@api.route("/auth/register", methods=["POST"])
def register():
    data = request.json or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not username or not email or not password:
        return (
            jsonify({"error": "username, email, and password are required"}),
            400,
        )

    if User.get_by_username(username):
        return jsonify({"error": "Username already taken"}), 409

    if User.get_by_email(email):
        return jsonify({"error": "Email already registered"}), 409

    password_hash = generate_password_hash(password)
    user = User.create(username=username, email=email, password_hash=password_hash)
    token = generate_jwt(str(user.id))

    return jsonify({"user": serialize_user(user), "token": token}), 201


@api.route("/auth/login", methods=["POST"])
def login():
    data = request.json or {}
    identifier = (data.get("username") or data.get("email") or "").strip()
    password = data.get("password") or ""

    if not identifier or not password:
        return jsonify({"error": "identifier and password are required"}), 400

    user = User.get_by_username(identifier) or User.get_by_email(identifier)
    if user is None or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = generate_jwt(str(user.id))
    return jsonify({"user": serialize_user(user), "token": token}), 200


@api.route("/auth/logout", methods=["POST"])
def logout():
    return jsonify({"message": "Logout successful"}), 200
