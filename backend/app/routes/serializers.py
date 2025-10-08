"""Shared serialization helpers for API responses."""

from __future__ import annotations

from typing import Dict

from ..models import Chat, ChatMessage, User


def serialize_chat(chat: Chat) -> Dict[str, str]:
    return chat.to_api_dict()


def serialize_message(message: ChatMessage) -> Dict[str, object]:
    return message.to_api_dict()


def serialize_user(user: User) -> Dict[str, object]:
    return user.to_public_dict()


__all__ = [
    "serialize_message",
    "serialize_chat",
    "serialize_user",
]
