"""Dataclass and helpers for chat messages."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Mapping, Optional, TYPE_CHECKING
from uuid import UUID

from ..db import execute_returning, fetch_all, to_jsonb

Row = Mapping[str, Any]

if TYPE_CHECKING:  # pragma: no cover
    from .chat_session import ChatSession


@dataclass(frozen=True)
class ChatMessage:
    id: int
    session_id: UUID
    role: str
    body: str
    sources: List[Dict[str, Any]]
    sent_at: datetime

    @classmethod
    def from_row(cls, row: Row) -> "ChatMessage":
        return cls(
            id=row["id"],
            session_id=row["session_id"],
            role=row["role"],
            body=row["body"],
            sources=row["sources"],
            sent_at=row["sent_at"],
        )

    @classmethod
    def create(
        cls,
        session_id: UUID | str,
        role: str,
        body: str,
        sources: Optional[Iterable[Dict[str, Any]]] = None,
    ) -> "ChatMessage":
        row = execute_returning(
            """
            INSERT INTO app.chat_messages (session_id, role, body, sources)
            VALUES (%s, %s, %s, %s)
            RETURNING id, session_id, role, body, sources, sent_at
            """,
            (
                session_id,
                role,
                body,
                to_jsonb(list(sources) if sources is not None else []),
            ),
        )

        from .chat_session import ChatSession

        ChatSession.touch(session_id)
        return cls.from_row(row)

    @classmethod
    def list_for_session(cls, session_id: UUID | str) -> List["ChatMessage"]:
        rows = fetch_all(
            """
            SELECT id, session_id, role, body, sources, sent_at
            FROM app.chat_messages
            WHERE session_id = %s
            ORDER BY sent_at ASC
            """,
            (session_id,),
        )
        return [cls.from_row(row) for row in rows]

    def to_record(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "body": self.body,
            "sources": self.sources,
            "sent_at": self.sent_at,
        }

    def to_api_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "text": self.body,
            "sources": self.sources,
            "timestamp": self.sent_at.isoformat(),
        }
