"""Storage helpers that wrap chat models."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..models import Chat


def _record_or_none(chat: Chat | None) -> Optional[Dict[str, Any]]:
    return chat.to_record() if chat else None


def get_chat_by_id(chat_id: str) -> Optional[Dict[str, Any]]:
    return _record_or_none(Chat.get_by_id(chat_id))


def create_chat(user_id: str, *, chat_id: Optional[str] = None) -> Dict[str, Any]:
    return Chat.create(user_id=user_id, chat_id=chat_id).to_record()


def ensure_chat(chat_id: Optional[str], user_id: str) -> Dict[str, Any]:
    return Chat.ensure(chat_id, user_id).to_record()


def touch_chat(chat_id: str) -> None:
    Chat.touch(chat_id)


def list_chats_for_user(user_id: str) -> list[Dict[str, Any]]:
    return [chat.to_record() for chat in Chat.list_for_user(user_id)]


__all__ = [
    "get_chat_by_id",
    "create_chat",
    "ensure_chat",
    "touch_chat",
    "list_chats_for_user",
]
