"""Shared serialization helpers for API responses."""

from __future__ import annotations

from typing import Dict

from ..models import ChatHistory, ChatMessage, ChatSession, User


def serialize_session(session: ChatSession) -> Dict[str, str]:
    return session.to_api_dict()


def serialize_message(message: ChatMessage) -> Dict[str, object]:
    return message.to_api_dict()


def serialize_history_entry(entry: ChatHistory) -> Dict[str, object]:
    return entry.to_api_dict()


def serialize_user(user: User) -> Dict[str, object]:
    return user.to_public_dict()


__all__ = [
    "serialize_message",
    "serialize_history_entry",
    "serialize_session",
    "serialize_user",
]
