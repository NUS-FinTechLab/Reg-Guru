"""Dataclass and helpers for chat messages."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Mapping, Optional, TYPE_CHECKING
from uuid import UUID

from ..db import execute_returning, fetch_all, to_jsonb

Row = Mapping[str, Any]

if TYPE_CHECKING:  # pragma: no cover
    from .chat import Chat


@dataclass(frozen=True)
class ChatMessage:
    id: int
    chat_id: UUID
    user_id: Optional[UUID]
    role: str
    body: str
    sources: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row: Row) -> "ChatMessage":
        return cls(
            id=row["id"],
            chat_id=row["chat_id"],
            user_id=row.get("user_id"),
            role=row["role"],
            body=row["body"],
            sources=row["sources"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @classmethod
    def create(
        cls,
        chat_id: UUID | str,
        *,
        user_id: Optional[UUID | str],
        role: str,
        body: str,
        sources: Optional[Iterable[Dict[str, Any]]] = None,
    ) -> "ChatMessage":
        row = execute_returning(
            """
            INSERT INTO app.chat_messages (chat_id, user_id, role, body, sources)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, chat_id, user_id, role, body, sources, created_at, updated_at
            """,
            (
                chat_id,
                user_id,
                role,
                body,
                to_jsonb(list(sources) if sources is not None else []),
            ),
        )

        from .chat import Chat

        Chat.touch(chat_id)
        return cls.from_row(row)

    @classmethod
    def list_for_chat(cls, chat_id: UUID | str) -> List["ChatMessage"]:
        rows = fetch_all(
            """
            SELECT id, chat_id, user_id, role, body, sources, created_at, updated_at
            FROM app.chat_messages
            WHERE chat_id = %s
            ORDER BY created_at ASC
            """,
            (chat_id,),
        )
        return [cls.from_row(row) for row in rows]

    def to_record(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "chat_id": self.chat_id,
            "user_id": self.user_id,
            "role": self.role,
            "body": self.body,
            "sources": self.sources,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_api_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "userId": str(self.user_id) if self.user_id else None,
            "text": self.body,
            "sources": self.sources,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }
