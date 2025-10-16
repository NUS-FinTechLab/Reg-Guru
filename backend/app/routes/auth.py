"""Authentication handlers for user registration and login."""

from __future__ import annotations

from flask import jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from ..auth import generate_jwt
from ..models import RefreshToken, User
from . import api
from .serializers import serialize_user


def _issue_auth_tokens(user: User) -> dict:
    access_token = generate_jwt(str(user.id))
    refresh_token_value, _ = RefreshToken.issue(user.id)
    return {
        "user": serialize_user(user),
        "token": access_token,
        "refreshToken": refresh_token_value,
    }


def _extract_refresh_token(payload: dict) -> str:
    raw_value = payload.get("refreshToken") if isinstance(payload, dict) else None
    return raw_value.strip() if isinstance(raw_value, str) else ""


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
    payload = _issue_auth_tokens(user)

    return jsonify(payload), 201


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

    payload = _issue_auth_tokens(user)
    return jsonify(payload), 200


@api.route("/auth/logout", methods=["POST"])
def logout():
    data = request.json or {}
    provided_refresh = _extract_refresh_token(data)
    if provided_refresh:
        token_record = RefreshToken.get_active_by_token(provided_refresh)
        if token_record:
            token_record.revoke_this()

    return jsonify({"message": "Logout successful"}), 200


@api.route("/auth/refresh", methods=["POST"])
def refresh_token():
    data = request.json or {}
    provided_refresh = _extract_refresh_token(data)

    if not provided_refresh:
        return jsonify({"error": "refreshToken is required"}), 400

    token_record = RefreshToken.get_active_by_token(provided_refresh)
    if token_record is None:
        return jsonify({"error": "Invalid refresh token"}), 401

    user = User.get_by_id(token_record.user_id)
    if user is None:
        token_record.revoke_this()
        return jsonify({"error": "Invalid refresh token"}), 401

    token_record.revoke_this()
    payload = _issue_auth_tokens(user)
    return jsonify(payload), 200
