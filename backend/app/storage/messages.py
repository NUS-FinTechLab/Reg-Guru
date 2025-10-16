"""Storage helpers that wrap chat message models."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from ..models import ChatMessage


def insert_message(
    chat_id: str,
    role: str,
    body: str,
    *,
    user_id: Optional[str],
    sources: Optional[Iterable[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    return ChatMessage.create(
        chat_id,
        user_id=user_id,
        role=role,
        body=body,
        sources=sources,
    ).to_record()


def list_messages(chat_id: str) -> List[Dict[str, Any]]:
    return [message.to_record() for message in ChatMessage.list_for_chat(chat_id)]


__all__ = ["insert_message", "list_messages"]
