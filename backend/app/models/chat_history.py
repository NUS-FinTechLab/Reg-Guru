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
    chat_external_id: Optional[str] = None

    @classmethod
    def from_row(cls, row: Row) -> "ChatHistory":
        return cls(
            id=row["id"],
            chat_id=row.get("chat_id"),
            query_text=row["query_text"],
            response_summary=row.get("response_summary"),
            created_at=row["created_at"],
            chat_external_id=row.get("chat_external_id"),
        )

    @classmethod
    def list_recent(cls, limit: int = 25, chat_id: UUID | str | None = None) -> List["ChatHistory"]:
        if chat_id is not None:
            rows = fetch_all(
                """
                SELECT
                    ch.id,
                    ch.chat_id,
                    ch.query_text,
                    ch.response_summary,
                    ch.created_at,
                    cs.external_id AS chat_external_id
                FROM app.chat_history ch
                LEFT JOIN app.chat_sessions cs ON cs.id = ch.chat_id
                WHERE ch.chat_id = %s
                ORDER BY ch.created_at DESC
                LIMIT %s
                """,
                (chat_id, limit),
            )
        else:
            rows = fetch_all(
                """
                SELECT
                    ch.id,
                    ch.chat_id,
                    ch.query_text,
                    ch.response_summary,
                    ch.created_at,
                    cs.external_id AS chat_external_id
                FROM app.chat_history ch
                LEFT JOIN app.chat_sessions cs ON cs.id = ch.chat_id
                ORDER BY ch.created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
        return [cls.from_row(row) for row in rows]

    @classmethod
    def create(
        cls,
        query_text: str,
        response_summary: Optional[str],
        *,
        chat_id: UUID | str,
        chat_external_id: Optional[str] = None,
    ) -> "ChatHistory":
        row = execute_returning(
            """
            INSERT INTO app.chat_history (chat_id, query_text, response_summary)
            VALUES (%s, %s, %s)
            RETURNING id, chat_id, query_text, response_summary, created_at
            """,
            (chat_id, query_text, response_summary),
        )
        data: Dict[str, Any] = dict(row)
        data["chat_external_id"] = chat_external_id
        return cls.from_row(data)

    def to_record(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "chat_id": self.chat_id,
            "query_text": self.query_text,
            "response_summary": self.response_summary,
            "created_at": self.created_at,
            "chat_external_id": self.chat_external_id,
        }

    def to_api_dict(self) -> Dict[str, Any]:
        chat_value = str(self.chat_id) if self.chat_id else None
        return {
            "id": self.id,
            "chatId": chat_value,
            "queryText": self.query_text,
            "responseSummary": self.response_summary,
            "createdAt": self.created_at.isoformat(),
            "chatExternalId": self.chat_external_id,
        }
