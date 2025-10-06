"""Storage helpers wrapping chat history models."""

from __future__ import annotations

from typing import Dict, List

from ..models import ChatHistory


def list_chat_history(limit: int = 25, chat_id: str | None = None) -> List[Dict[str, object]]:
    entries = ChatHistory.list_recent(limit=limit, chat_id=chat_id)
    return [entry.to_record() for entry in entries]


def insert_chat_history(
    chat_id: str,
    query_text: str,
    response_summary: str | None = None,
) -> Dict[str, object]:
    return ChatHistory.create(
        query_text=query_text,
        response_summary=response_summary,
        chat_id=chat_id,
    ).to_record()


__all__ = ["list_chat_history", "insert_chat_history"]
