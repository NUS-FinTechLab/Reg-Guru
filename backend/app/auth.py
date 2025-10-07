"""Minimal helpers for generating and validating JWT access tokens."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from .config import JWT_ALGORITHM, JWT_SECRET_KEY

_DEFAULT_EXPIRATION = timedelta(hours=12)
_SUPPORTED_ALGORITHM = "HS256"


def _ensure_supported_algorithm() -> None:
    if JWT_ALGORITHM.upper() != _SUPPORTED_ALGORITHM:
        raise RuntimeError(
            f"Unsupported JWT algorithm '{JWT_ALGORITHM}'. Only '{_SUPPORTED_ALGORITHM}' is supported."
        )


def _urlsafe_b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _urlsafe_b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def generate_jwt(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """Generate a signed JWT for the provided user identifier using HMAC-SHA256."""

    _ensure_supported_algorithm()

    now = datetime.now(timezone.utc)
    expiration = now + (expires_delta or _DEFAULT_EXPIRATION)

    header = {"alg": _SUPPORTED_ALGORITHM, "typ": "JWT"}
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int(expiration.timestamp()),
    }

    header_b64 = _urlsafe_b64encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    signature = hmac.new(
        JWT_SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256
    ).digest()
    signature_b64 = _urlsafe_b64encode(signature)

    return f"{header_b64}.{payload_b64}.{signature_b64}"


def decode_auth_header(auth_header: str) -> Dict[str, Any]:
    """Decode and validate a bearer Authorization header using HMAC-SHA256."""

    _ensure_supported_algorithm()

    if not auth_header:
        raise ValueError("Missing Authorization header")

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise ValueError("Invalid authorization header format")

    token = parts[1]
    segments = token.split(".")
    if len(segments) != 3:
        raise ValueError("Invalid authorization token")

    header_b64, payload_b64, signature_b64 = segments

    try:
        header = json.loads(_urlsafe_b64decode(header_b64))
        payload = json.loads(_urlsafe_b64decode(payload_b64))
    except (ValueError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid authorization token") from exc

    if header.get("alg", "").upper() != _SUPPORTED_ALGORITHM:
        raise ValueError("Unsupported token algorithm")

    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    expected_sig = hmac.new(
        JWT_SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256
    ).digest()
    try:
        provided_sig = _urlsafe_b64decode(signature_b64)
    except (ValueError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid authorization token") from exc

    if not hmac.compare_digest(expected_sig, provided_sig):
        raise ValueError("Invalid authorization token")

    exp_ts = payload.get("exp")
    if isinstance(exp_ts, (int, float)):
        now_ts = int(datetime.now(timezone.utc).timestamp())
        if now_ts > int(exp_ts):
            raise ValueError("Authorization token expired")

    return payload
