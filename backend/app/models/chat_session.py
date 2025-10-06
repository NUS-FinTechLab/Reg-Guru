"""Dataclass and helpers for chat sessions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Mapping, Optional, TYPE_CHECKING
from uuid import UUID

from ..db import execute, execute_returning, fetch_all, fetch_one

Row = Mapping[str, Any]

if TYPE_CHECKING:  # pragma: no cover
    from .chat_message import ChatMessage


@dataclass(frozen=True)
class ChatSession:
    id: UUID
    external_id: str
    region: str
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row: Row) -> "ChatSession":
        return cls(
            id=row["id"],
            external_id=row["external_id"],
            region=row["region"],
            user_id=row["user_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @classmethod
    def get_by_external_id(cls, external_id: str) -> Optional["ChatSession"]:
        row = fetch_one(
            """
            SELECT id, external_id, region, user_id, created_at, updated_at
            FROM app.chat_sessions
            WHERE external_id = %s
            """,
            (external_id,),
        )
        return cls.from_row(row) if row else None

    @classmethod
    def get_by_id(cls, session_id: UUID | str) -> Optional["ChatSession"]:
        row = fetch_one(
            """
            SELECT id, external_id, region, user_id, created_at, updated_at
            FROM app.chat_sessions
            WHERE id = %s
            """,
            (session_id,),
        )
        return cls.from_row(row) if row else None

    @classmethod
    def create(cls, external_id: str, region: str, user_id: UUID | str) -> "ChatSession":
        row = execute_returning(
            """
            INSERT INTO app.chat_sessions (external_id, region, user_id)
            VALUES (%s, %s, %s)
            RETURNING id, external_id, region, user_id, created_at, updated_at
            """,
            (external_id, region, user_id),
        )
        return cls.from_row(row)

    @classmethod
    def upsert(cls, external_id: str, region: str, user_id: UUID | str) -> "ChatSession":
        session = cls.get_by_external_id(external_id)
        if session is None:
            return cls.create(external_id, region, user_id)
        if session.region != region or session.user_id != user_id:
            row = execute_returning(
                """
                UPDATE app.chat_sessions
                SET region = %s, user_id = %s, updated_at = NOW()
                WHERE id = %s
                RETURNING id, external_id, region, user_id, created_at, updated_at
                """,
                (region, user_id, session.id),
            )
            return cls.from_row(row)
        return session

    @staticmethod
    def touch(session_id: UUID | str) -> None:
        execute(
            """
            UPDATE app.chat_sessions
            SET updated_at = NOW()
            WHERE id = %s
            """,
            (session_id,),
        )

    def to_record(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "external_id": self.external_id,
            "region": self.region,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_api_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "chatId": self.external_id,
            "region": self.region,
            "userId": str(self.user_id),
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }

    def list_messages(self) -> List["ChatMessage"]:
        from .chat_message import ChatMessage

        return ChatMessage.list_for_session(self.id)

    @classmethod
    def list_for_user(cls, user_id: UUID | str) -> List["ChatSession"]:
        rows = fetch_all(
            """
            SELECT id, external_id, region, user_id, created_at, updated_at
            FROM app.chat_sessions
            WHERE user_id = %s
            ORDER BY updated_at DESC
            """,
            (user_id,),
        )
        return [cls.from_row(row) for row in rows]
