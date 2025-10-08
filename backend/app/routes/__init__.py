"""API route package that registers all endpoint modules."""

from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from ..auth import decode_auth_header

api = Blueprint("api", __name__, url_prefix="/api")


_EXEMPT_ENDPOINTS = {
    "api.register",
    "api.login",
    "api.logout",
    "api.test",
    "api.options_handler",
}


@api.before_request
def enforce_authenticated_user():
    """Ensure provided user ID header matches the authenticated token subject."""

    if request.method == "OPTIONS":
        return None

    endpoint = request.endpoint or ""
    if not endpoint.startswith(f"{api.name}."):
        return None

    if endpoint in _EXEMPT_ENDPOINTS:
        return None

    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return jsonify({"error": "Authorization header required"}), 401

    try:
        payload = decode_auth_header(auth_header)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 401

    provided_user_id = (request.headers.get("X-User-Id") or "").strip()
    if not provided_user_id:
        return jsonify({"error": "Missing X-User-Id header"}), 400

    token_user_id = str(payload.get("sub"))
    if token_user_id != provided_user_id:
        return jsonify({"error": "Authenticated user mismatch"}), 403

    g.authenticated_user_id = token_user_id
    return None

# Import route modules so they attach their handlers to the blueprint.
from . import auth  # noqa: F401  (imported for side effects)
from . import chat  # noqa: F401
from . import feedback  # noqa: F401
from . import misc  # noqa: F401
from . import sessions  # noqa: F401
from . import users  # noqa: F401

__all__ = ["api"]
