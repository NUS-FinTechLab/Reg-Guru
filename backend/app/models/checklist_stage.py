"""Dataclass and helpers for checklist stages."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, Mapping, Sequence
from uuid import UUID

from ..db import execute, execute_returning, fetch_all, fetch_one, to_jsonb

Row = Mapping[str, Any]

_REFERENCE_LINKS_SUPPORTED: bool | None = None


def _supports_reference_links() -> bool:
    """Detect whether the checklist_stage table has the reference_links column."""

    global _REFERENCE_LINKS_SUPPORTED
    if _REFERENCE_LINKS_SUPPORTED is not None:
        return _REFERENCE_LINKS_SUPPORTED

    row = fetch_one(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'app'
          AND table_name = 'checklist_stage'
          AND column_name = 'reference_links'
        LIMIT 1
        """
    )
    _REFERENCE_LINKS_SUPPORTED = bool(row)
    return _REFERENCE_LINKS_SUPPORTED


@dataclass(frozen=True)
class ChecklistStage:
    id: UUID
    checklist_id: UUID
    title: str
    description: str
    position: int
    reference_links: list[Dict[str, str]]
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
            reference_links=_normalize_reference_links(row.get("reference_links")),
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
        reference_links: Sequence[Dict[str, Any]] | None = None,
    ) -> "ChecklistStage":
        normalized_title = title.strip()
        normalized_description = description.strip()
        normalized_references = _normalize_reference_links(reference_links)
        references_supported = _supports_reference_links()
        if not references_supported and normalized_references:
            raise RuntimeError(
                "checklist_stage.reference_links column not found; apply the latest database migrations (e.g. python scripts/apply_migrations.py)"
            )

        if references_supported:
            row = execute_returning(
                """
                INSERT INTO app.checklist_stage (checklist_id, title, description, position, reference_links)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, checklist_id, title, description, position, reference_links, created_at, updated_at
                """,
                (
                    checklist_id,
                    normalized_title,
                    normalized_description,
                    position,
                    to_jsonb(normalized_references),
                ),
            )
        else:
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
                    reference_links=stage.get("referenceLinks") or stage.get("reference_links"),
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
        if _supports_reference_links():
            rows = fetch_all(
                """
                SELECT id,
                       checklist_id,
                       title,
                       description,
                       position,
                       reference_links,
                       created_at,
                       updated_at
                FROM app.checklist_stage
                WHERE checklist_id = %s
                ORDER BY position ASC, created_at ASC
                """,
                (checklist_id,),
            )
        else:
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
            "reference_links": self.reference_links,
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
            "referenceLinks": self.reference_links,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }


def _normalize_reference_links(raw: Any) -> list[Dict[str, str]]:
    if not raw:
        return []

    if isinstance(raw, Mapping):
        raw_iterable = [raw]
    elif isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
        raw_iterable = raw
    else:
        raw_iterable = [raw]

    normalized: list[Dict[str, str]] = []
    for entry in raw_iterable:
        if isinstance(entry, Mapping):
            title = str(entry.get("title") or "").strip()
            url = str(entry.get("url") or "").strip()
            if not (title or url):
                continue
            normalized.append({"title": title, "url": url})
            continue

        if entry in (None, ""):
            continue
        url = str(entry).strip()
        if not url:
            continue
        normalized.append({"title": "", "url": url})

    return normalized
