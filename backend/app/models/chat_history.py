"""Dataclass and helpers for chat history entries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Mapping, Optional
from uuid import UUID

from ..db import execute_returning, fetch_all

Row = Mapping[str, Any]


@dataclass(frozen=True)
class ChatHistory:
    id: int
    chat_id: Optional[UUID]
    query_text: str
    response_summary: Optional[str]
    created_at: datetime

    @classmethod
    def from_row(cls, row: Row) -> "ChatHistory":
        return cls(
            id=row["id"],
            chat_id=row.get("chat_id"),
            query_text=row["query_text"],
            response_summary=row.get("response_summary"),
            created_at=row["created_at"],
        )

    @classmethod
    def list_recent(cls, limit: int = 25, chat_id: UUID | str | None = None) -> List["ChatHistory"]:
        sql = """
            SELECT
                ch.id,
                ch.chat_id,
                ch.query_text,
                ch.response_summary,
                ch.created_at
            FROM app.chat_history ch
            WHERE (%s IS NULL) OR ch.chat_id = %s
            ORDER BY ch.created_at DESC
            LIMIT %s
        """
        params = (chat_id, chat_id, limit)
        rows = fetch_all(sql, params)
        return [cls.from_row(row) for row in rows]

    @classmethod
    def create(
        cls,
        query_text: str,
        response_summary: Optional[str],
        *,
        chat_id: UUID | str,
    ) -> "ChatHistory":
        row = execute_returning(
            """
            INSERT INTO app.chat_history (chat_id, query_text, response_summary)
            VALUES (%s, %s, %s)
            RETURNING id, chat_id, query_text, response_summary, created_at
            """,
            (chat_id, query_text, response_summary),
        )
        return cls.from_row(row)

    def to_record(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "chat_id": self.chat_id,
            "query_text": self.query_text,
            "response_summary": self.response_summary,
            "created_at": self.created_at,
        }

    def to_api_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "chatId": str(self.chat_id) if self.chat_id else None,
            "queryText": self.query_text,
            "responseSummary": self.response_summary,
            "createdAt": self.created_at.isoformat(),
        }
