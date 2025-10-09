"""Dataclass and helpers for checklist items."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, ClassVar, Dict, Iterable, Mapping, Sequence
from uuid import UUID

from ..db import execute, execute_returning, fetch_all

Row = Mapping[str, Any]


@dataclass(frozen=True)
class ChecklistItem:
    id: UUID
    checklist_id: UUID
    content: str
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime

    STATUSES: ClassVar[tuple[str, ...]] = ("not_started", "ongoing", "finished")
    PRIORITIES: ClassVar[tuple[str, ...]] = ("low", "medium", "high")

    @classmethod
    def from_row(cls, row: Row) -> "ChecklistItem":
        return cls(
            id=row["id"],
            checklist_id=row["checklist_id"],
            content=row["content"],
            status=row["status"],
            priority=row["priority"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @classmethod
    def list_for_checklist(cls, checklist_id: UUID | str) -> Iterable["ChecklistItem"]:
        rows = fetch_all(
            """
            SELECT
                id,
                checklist_id,
                content,
                status::TEXT     AS status,
                priority::TEXT   AS priority,
                created_at,
                updated_at
            FROM app.checklist_item
            WHERE checklist_id = %s
            ORDER BY created_at ASC
            """,
            (checklist_id,),
        )
        return [cls.from_row(row) for row in rows]

    @classmethod
    def create_many(
        cls,
        *,
        checklist_id: UUID | str,
        items: Sequence[Dict[str, str]],
    ) -> Iterable["ChecklistItem"]:
        created: list[ChecklistItem] = []
        for item in items:
            row = execute_returning(
                """
                INSERT INTO app.checklist_item (checklist_id, content, status, priority)
                VALUES (%s, %s, %s, %s)
                RETURNING
                    id,
                    checklist_id,
                    content,
                    status::TEXT AS status,
                    priority::TEXT AS priority,
                    created_at,
                    updated_at
                """,
                (
                    checklist_id,
                    item["content"],
                    item["status"],
                    item["priority"],
                ),
            )
            created.append(cls.from_row(row))
        return created

    @classmethod
    def replace_for_checklist(
        cls,
        *,
        checklist_id: UUID | str,
        items: Sequence[Dict[str, str]],
    ) -> Iterable["ChecklistItem"]:
        execute(
            """
            DELETE FROM app.checklist_item
            WHERE checklist_id = %s
            """,
            (checklist_id,),
        )
        if not items:
            return []
        return cls.create_many(checklist_id=checklist_id, items=items)

    def to_record(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "checklist_id": self.checklist_id,
            "content": self.content,
            "status": self.status,
            "priority": self.priority,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_api_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "checklistId": str(self.checklist_id),
            "content": self.content,
            "status": self.status,
            "priority": self.priority,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }
