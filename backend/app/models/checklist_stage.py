"""Dataclass and helpers for checklist stages."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, Mapping, Sequence
from uuid import UUID

from ..db import execute, execute_returning, fetch_all

Row = Mapping[str, Any]


@dataclass(frozen=True)
class ChecklistStage:
    id: UUID
    checklist_id: UUID
    title: str
    description: str
    position: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row: Row) -> "ChecklistStage":
        return cls(
            id=row["id"],
            checklist_id=row["checklist_id"],
            title=row["title"],
            description=row["description"],
            position=int(row.get("position", 0) or 0),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @classmethod
    def create(
        cls,
        *,
        checklist_id: UUID | str,
        title: str,
        description: str,
        position: int,
    ) -> "ChecklistStage":
        normalized_title = title.strip()
        normalized_description = description.strip()
        row = execute_returning(
            """
            INSERT INTO app.checklist_stage (checklist_id, title, description, position)
            VALUES (%s, %s, %s, %s)
            RETURNING id, checklist_id, title, description, position, created_at, updated_at
            """,
            (checklist_id, normalized_title, normalized_description, position),
        )
        return cls.from_row(row)

    @classmethod
    def create_many(
        cls,
        *,
        checklist_id: UUID | str,
        stages: Sequence[Dict[str, Any]],
    ) -> Iterable["ChecklistStage"]:
        created: list[ChecklistStage] = []
        for stage in stages:
            created.append(
                cls.create(
                    checklist_id=checklist_id,
                    title=stage["title"],
                    description=stage.get("description", ""),
                    position=int(stage.get("position", 0) or 0),
                )
            )
        return created

    @classmethod
    def delete_for_checklist(cls, checklist_id: UUID | str) -> None:
        execute(
            """
            DELETE FROM app.checklist_stage
            WHERE checklist_id = %s
            """,
            (checklist_id,),
        )

    @classmethod
    def list_for_checklist(cls, checklist_id: UUID | str) -> Sequence["ChecklistStage"]:
        rows = fetch_all(
            """
            SELECT id,
                   checklist_id,
                   title,
                   description,
                   position,
                   created_at,
                   updated_at
            FROM app.checklist_stage
            WHERE checklist_id = %s
            ORDER BY position ASC, created_at ASC
            """,
            (checklist_id,),
        )
        return [cls.from_row(row) for row in rows]

    def to_record(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "checklist_id": self.checklist_id,
            "title": self.title,
            "description": self.description,
            "position": self.position,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_api_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "checklistId": str(self.checklist_id),
            "title": self.title,
            "description": self.description,
            "position": self.position,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }
