"""Storage helpers that wrap chat session models."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..models import ChatSession


def _record_or_none(session: ChatSession | None) -> Optional[Dict[str, Any]]:
    return session.to_record() if session else None


def get_session_by_external_id(external_id: str) -> Optional[Dict[str, Any]]:
    return _record_or_none(ChatSession.get_by_external_id(external_id))


def get_session_by_id(session_id: str) -> Optional[Dict[str, Any]]:
    return _record_or_none(ChatSession.get_by_id(session_id))


def create_session(external_id: str, region: str, user_id: str) -> Dict[str, Any]:
    return ChatSession.create(external_id, region, user_id).to_record()


def touch_session(session_id: str) -> None:
    ChatSession.touch(session_id)


def upsert_session(external_id: str, region: str, user_id: str) -> Dict[str, Any]:
    return ChatSession.upsert(external_id, region, user_id).to_record()


def list_sessions_for_user(user_id: str) -> list[Dict[str, Any]]:
    return [session.to_record() for session in ChatSession.list_for_user(user_id)]


__all__ = [
    "get_session_by_external_id",
    "get_session_by_id",
    "create_session",
    "touch_session",
    "upsert_session",
    "list_sessions_for_user",
]
