"""Dataclass and helpers for feedback records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Mapping, Optional
from uuid import UUID

from ..db import execute_returning

Row = Mapping[str, Any]


@dataclass(frozen=True)
class Feedback:
    id: int
    session_id: UUID
    message_id: Optional[int]
    rating: str
    comments: Optional[str]
    created_at: datetime

    @classmethod
    def from_row(cls, row: Row) -> "Feedback":
        return cls(
            id=row["id"],
            session_id=row["session_id"],
            message_id=row["message_id"],
            rating=row["rating"],
            comments=row.get("comments"),
            created_at=row["created_at"],
        )

    @classmethod
    def create(
        cls,
        session_id: UUID | str,
        rating: str,
        comments: str = "",
        message_id: Optional[int] = None,
    ) -> "Feedback":
        row = execute_returning(
            """
            INSERT INTO app.feedback (session_id, message_id, rating, comments)
            VALUES (%s, %s, %s, NULLIF(%s, ''))
            RETURNING id, session_id, message_id, rating, comments, created_at
            """,
            (session_id, message_id, rating, comments or ""),
        )
        return cls.from_row(row)

    def to_record(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "message_id": self.message_id,
            "rating": self.rating,
            "comments": self.comments,
            "created_at": self.created_at,
        }
