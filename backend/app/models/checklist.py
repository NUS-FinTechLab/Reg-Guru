"""Dataclass and helpers for compliance checklists."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence
from uuid import UUID

from ..db import execute, execute_returning, fetch_all, fetch_one

Row = Mapping[str, Any]


@dataclass(frozen=True)
class Checklist:
    id: UUID
    user_id: UUID
    title: str
    description: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row: Row) -> "Checklist":
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            title=row["title"],
            description=row["description"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @classmethod
    def create(cls, *, user_id: UUID | str, title: str, description: str) -> "Checklist":
        row = execute_returning(
            """
            INSERT INTO app.checklist (user_id, title, description)
            VALUES (%s, %s, %s)
            RETURNING id, user_id, title, description, created_at, updated_at
            """,
            (user_id, title, description),
        )
        return cls.from_row(row)

    @classmethod
    def get_for_user(
        cls,
        checklist_id: UUID | str,
        user_id: UUID | str,
    ) -> Optional["Checklist"]:
        row = fetch_one(
            """
            SELECT id, user_id, title, description, created_at, updated_at
            FROM app.checklist
            WHERE id = %s AND user_id = %s
            """,
            (checklist_id, user_id),
        )
        return cls.from_row(row) if row else None

    @classmethod
    def update(
        cls,
        *,
        checklist_id: UUID | str,
        user_id: UUID | str,
        title: str,
        description: str,
    ) -> Optional["Checklist"]:
        row = fetch_one(
            """
            UPDATE app.checklist
            SET title = %s,
                description = %s,
                updated_at = NOW()
            WHERE id = %s
              AND user_id = %s
            RETURNING id, user_id, title, description, created_at, updated_at
            """,
            (title, description, checklist_id, user_id),
        )
        return cls.from_row(row) if row else None

    @classmethod
    def delete(cls, *, checklist_id: UUID | str, user_id: UUID | str) -> bool:
        row = fetch_one(
            """
            DELETE FROM app.checklist
            WHERE id = %s AND user_id = %s
            RETURNING id
            """,
            (checklist_id, user_id),
        )
        return row is not None

    @classmethod
    def list_for_user(cls, user_id: UUID | str) -> Iterable["Checklist"]:
        rows = fetch_all(
            """
            SELECT id, user_id, title, description, created_at, updated_at
            FROM app.checklist
            WHERE user_id = %s
            ORDER BY updated_at DESC
            """,
            (user_id,),
        )
        return [cls.from_row(row) for row in rows]

    @classmethod
    def list_with_progress_for_user(
        cls,
        user_id: UUID | str,
    ) -> Sequence[Dict[str, Any]]:
        rows = fetch_all(
            """
            SELECT
                c.id,
                c.user_id,
                c.title,
                c.description,
                c.created_at,
                c.updated_at,
                COUNT(DISTINCT cs.id) AS stage_count,
                COUNT(ci.*)            AS total_items,
                COUNT(ci.*) FILTER (WHERE ci.status = 'finished') AS finished_items
            FROM app.checklist AS c
            LEFT JOIN app.checklist_stage AS cs ON cs.checklist_id = c.id
            LEFT JOIN app.checklist_item AS ci ON ci.stage_id = cs.id
            WHERE c.user_id = %s
            GROUP BY c.id
            ORDER BY c.updated_at DESC
            """,
            (user_id,),
        )

        summaries: list[Dict[str, Any]] = []
        for row in rows:
            checklist = cls.from_row(row)
            total_items = int(row.get("total_items", 0) or 0)
            finished_items = int(row.get("finished_items", 0) or 0)
            stage_count = int(row.get("stage_count", 0) or 0)
            summaries.append(
                {
                    "checklist": checklist,
                    "total_items": total_items,
                    "finished_items": finished_items,
                    "stage_count": stage_count,
                }
            )
        return summaries

    def to_record(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_api_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "userId": str(self.user_id),
            "title": self.title,
            "description": self.description,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }
