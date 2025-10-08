"""Shared serialization helpers for API responses."""

from __future__ import annotations

from typing import Dict

from ..models import Chat, ChatHistory, ChatMessage, User


def serialize_chat(chat: Chat) -> Dict[str, str]:
    return chat.to_api_dict()


def serialize_message(message: ChatMessage) -> Dict[str, object]:
    return message.to_api_dict()


def serialize_history_entry(entry: ChatHistory) -> Dict[str, object]:
    return entry.to_api_dict()


def serialize_user(user: User) -> Dict[str, object]:
    return user.to_public_dict()


__all__ = [
    "serialize_message",
    "serialize_history_entry",
    "serialize_chat",
    "serialize_user",
]
