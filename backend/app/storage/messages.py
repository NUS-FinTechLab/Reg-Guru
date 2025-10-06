"""Storage helpers that wrap chat message models."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from ..models import ChatMessage


def insert_message(
    session_id: str,
    role: str,
    body: str,
    sources: Optional[Iterable[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    return ChatMessage.create(session_id, role, body, sources).to_record()


def list_messages(session_id: str) -> List[Dict[str, Any]]:
    return [message.to_record() for message in ChatMessage.list_for_session(session_id)]


__all__ = ["insert_message", "list_messages"]
