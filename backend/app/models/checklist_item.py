"""Dataclass and helpers for checklist items."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, ClassVar, Dict, Iterable, Mapping, Sequence
from uuid import UUID

from ..db import execute, execute_returning, fetch_all, fetch_one

Row = Mapping[str, Any]


@dataclass(frozen=True)
class ChecklistItem:
    id: UUID
    checklist_id: UUID
    stage_id: UUID
    content: str
    status: str
    priority: str
    position: int
    referenceLink: list[str] | None = None
    created_at: datetime
    updated_at: datetime

    STATUSES: ClassVar[tuple[str, ...]] = ("not_started", "ongoing", "finished")
    PRIORITIES: ClassVar[tuple[str, ...]] = ("low", "medium", "high")

    @classmethod
    def from_row(cls, row: Row) -> "ChecklistItem":
        return cls(
            id=row["id"],
            checklist_id=row["checklist_id"],
            stage_id=row["stage_id"],
            content=row["content"],
            status=row["status"],
            priority=row["priority"],
            position=int(row.get("position", 0) or 0),
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
                stage_id,
                content,
                status::TEXT     AS status,
                priority::TEXT   AS priority,
                position,
                created_at,
                updated_at
            FROM app.checklist_item
            WHERE checklist_id = %s
            ORDER BY position ASC, created_at ASC
            """,
            (checklist_id,),
        )
        return [cls.from_row(row) for row in rows]

    @classmethod
    def list_for_stage(cls, stage_id: UUID | str) -> Iterable["ChecklistItem"]:
        rows = fetch_all(
            """
            SELECT
                id,
                checklist_id,
                stage_id,
                content,
                status::TEXT   AS status,
                priority::TEXT AS priority,
                position,
                created_at,
                updated_at
            FROM app.checklist_item
            WHERE stage_id = %s
            ORDER BY position ASC, created_at ASC
            """,
            (stage_id,),
        )
        return [cls.from_row(row) for row in rows]

    @classmethod
    def create_many(
        cls,
        *,
        checklist_id: UUID | str,
        stage_id: UUID | str,
        items: Sequence[Dict[str, str]],
    ) -> Iterable["ChecklistItem"]:
        created: list[ChecklistItem] = []
        for item in items:
            row = execute_returning(
                """
                INSERT INTO app.checklist_item (checklist_id, stage_id, content, status, priority, position)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING
                    id,
                    checklist_id,
                    stage_id,
                    content,
                    status::TEXT AS status,
                    priority::TEXT AS priority,
                    position,
                    created_at,
                    updated_at
                """,
                (
                    checklist_id,
                    stage_id,
                    item["content"],
                    item["status"],
                    item["priority"],
                    int(item.get("position", 0) or 0),
                ),
            )
            created.append(cls.from_row(row))
        return created

    @classmethod
    def update_status_for_user(
        cls,
        *,
        checklist_id: UUID | str,
        item_id: UUID | str,
        user_id: UUID | str,
        status: str,
    ) -> "ChecklistItem" | None:
        row = fetch_one(
            """
            UPDATE app.checklist_item AS ci
            SET status = %s,
                updated_at = NOW()
            FROM app.checklist AS c
            WHERE ci.id = %s
              AND ci.checklist_id = %s
              AND ci.checklist_id = c.id
              AND c.user_id = %s
            RETURNING
                ci.id,
                ci.checklist_id,
                ci.stage_id,
                ci.content,
                ci.status::TEXT   AS status,
                ci.priority::TEXT AS priority,
                ci.position,
                ci.created_at,
                ci.updated_at
            """,
            (status, item_id, checklist_id, user_id),
        )

        if row is None:
            return None

        execute(
            "UPDATE app.checklist_stage SET updated_at = NOW() WHERE id = %s",
            (row["stage_id"],),
        )
        execute(
            "UPDATE app.checklist SET updated_at = NOW() WHERE id = %s",
            (row["checklist_id"],),
        )

        return cls.from_row(row)

    @classmethod
    def update_for_user(
        cls,
        *,
        checklist_id: UUID | str,
        item_id: UUID | str,
        user_id: UUID | str,
        content: str | None = None,
        status: str | None = None,
        priority: str | None = None,
    ) -> "ChecklistItem" | None:
        assignments: list[str] = []
        params: list[Any] = []

        if content is not None:
            assignments.append("content = %s")
            params.append(content)
        if status is not None:
            assignments.append("status = %s")
            params.append(status)
        if priority is not None:
            assignments.append("priority = %s")
            params.append(priority)

        if not assignments:
            return None

        assignments.append("updated_at = NOW()")
        set_clause = ", ".join(assignments)

        row = fetch_one(
            f"""
            UPDATE app.checklist_item AS ci
            SET {set_clause}
            FROM app.checklist AS c
            WHERE ci.id = %s
              AND ci.checklist_id = %s
              AND ci.checklist_id = c.id
              AND c.user_id = %s
            RETURNING
                ci.id,
                ci.checklist_id,
                ci.stage_id,
                ci.content,
                ci.status::TEXT   AS status,
                ci.priority::TEXT AS priority,
                ci.position,
                ci.created_at,
                ci.updated_at
            """,
            (*params, item_id, checklist_id, user_id),
        )

        if row is None:
            return None

        execute(
            "UPDATE app.checklist_stage SET updated_at = NOW() WHERE id = %s",
            (row["stage_id"],),
        )
        execute(
            "UPDATE app.checklist SET updated_at = NOW() WHERE id = %s",
            (row["checklist_id"],),
        )

        return cls.from_row(row)

    @classmethod
    def delete_for_user(
        cls,
        *,
        checklist_id: UUID | str,
        item_id: UUID | str,
        user_id: UUID | str,
    ) -> bool:
        row = fetch_one(
            """
            DELETE FROM app.checklist_item AS ci
            USING app.checklist AS c
            WHERE ci.id = %s
              AND ci.checklist_id = %s
              AND ci.checklist_id = c.id
              AND c.user_id = %s
            RETURNING ci.stage_id AS stage_id, ci.checklist_id AS checklist_id
            """,
            (item_id, checklist_id, user_id),
        )

        if row is None:
            return False

        execute(
            "UPDATE app.checklist_stage SET updated_at = NOW() WHERE id = %s",
            (row["stage_id"],),
        )
        execute(
            "UPDATE app.checklist SET updated_at = NOW() WHERE id = %s",
            (row["checklist_id"],),
        )

        return True

    def to_record(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "checklist_id": self.checklist_id,
            "stage_id": self.stage_id,
            "content": self.content,
            "status": self.status,
            "priority": self.priority,
            "position": self.position,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_api_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "checklistId": str(self.checklist_id),
            "stageId": str(self.stage_id),
            "content": self.content,
            "status": self.status,
            "priority": self.priority,
            "position": self.position,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }
