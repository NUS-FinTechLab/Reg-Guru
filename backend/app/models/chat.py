"""Dataclass and helpers for chat records."""

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
class Chat:
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row: Row) -> "Chat":
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @classmethod
    def get_by_id(cls, chat_id: UUID | str) -> Optional["Chat"]:
        row = fetch_one(
            """
            SELECT id, user_id, created_at, updated_at
            FROM app.chats
            WHERE id = %s
            """,
            (chat_id,),
        )
        return cls.from_row(row) if row else None

    @classmethod
    def create(
        cls,
        user_id: UUID | str,
        *,
        chat_id: Optional[UUID | str] = None,
    ) -> "Chat":
        if chat_id is not None:
            row = execute_returning(
                """
                INSERT INTO app.chats (id, user_id)
                VALUES (%s, %s)
                RETURNING id, user_id, created_at, updated_at
                """,
                (chat_id, user_id),
            )
        else:
            row = execute_returning(
                """
                INSERT INTO app.chats (user_id)
                VALUES (%s)
                RETURNING id, user_id, created_at, updated_at
                """,
                (user_id,),
            )
        return cls.from_row(row)

    @classmethod
    def ensure(cls, chat_id: Optional[UUID | str], user_id: UUID | str) -> "Chat":
        if chat_id is not None:
            existing = cls.get_by_id(chat_id)
            if existing is not None:
                if str(existing.user_id) != str(user_id):
                    raise ValueError("Chat belongs to a different user")
                cls.touch(existing.id)
                return existing
            return cls.create(user_id=user_id, chat_id=chat_id)
        return cls.create(user_id=user_id)

    @staticmethod
    def touch(chat_id: UUID | str) -> None:
        execute(
            """
            UPDATE app.chats
            SET updated_at = NOW()
            WHERE id = %s
            """,
            (chat_id,),
        )

    def to_record(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_api_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "userId": str(self.user_id),
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }

    def list_messages(self) -> List["ChatMessage"]:
        from .chat_message import ChatMessage

        return ChatMessage.list_for_chat(self.id)

    @classmethod
    def list_for_user(cls, user_id: UUID | str) -> List["Chat"]:
        rows = fetch_all(
            """
            SELECT id, user_id, created_at, updated_at
            FROM app.chats
            WHERE user_id = %s
            ORDER BY updated_at DESC
            """,
            (user_id,),
        )
        return [cls.from_row(row) for row in rows]

    @classmethod
    def list_with_last_message_for_user(
        cls,
        user_id: UUID | str,
    ) -> List[Dict[str, Any]]:
        rows = fetch_all(
            """
            SELECT
                c.id,
                c.user_id,
                c.created_at,
                c.updated_at,
                lm.role AS last_message_role,
                lm.body AS last_message_body,
                lm.created_at AS last_message_created_at
            FROM app.chats AS c
            LEFT JOIN LATERAL (
                SELECT role, body, created_at
                FROM app.chat_messages
                WHERE chat_id = c.id
                ORDER BY created_at DESC
                LIMIT 1
            ) AS lm ON TRUE
            WHERE c.user_id = %s
            ORDER BY c.updated_at DESC
            """,
            (user_id,),
        )

        results: List[Dict[str, Any]] = []
        for row in rows:
            data = dict(row)
            chat = cls.from_row(data)
            last_message = None
            if data.get("last_message_body") is not None:
                created_at = data.get("last_message_created_at")
                last_message = {
                    "text": data["last_message_body"],
                    "role": data["last_message_role"],
                    "createdAt": created_at.isoformat() if created_at else None,
                }
            results.append({"chat": chat, "last_message": last_message})
        return results
