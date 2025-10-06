"""Dataclass and helpers for user records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, Mapping, Optional
from uuid import UUID

from ..db import execute_returning, fetch_all, fetch_one

Row = Mapping[str, Any]


@dataclass(frozen=True)
class User:
    id: UUID
    username: str
    email: str
    password_hash: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row: Row) -> "User":
        return cls(
            id=row["id"],
            username=row["username"],
            email=row["email"],
            password_hash=row["password_hash"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @classmethod
    def get_by_id(cls, user_id: UUID | str) -> Optional["User"]:
        row = fetch_one(
            """
            SELECT id, username, email, password_hash, created_at, updated_at
            FROM app.user
            WHERE id = %s
            """,
            (user_id,),
        )
        return cls.from_row(row) if row else None

    @classmethod
    def get_by_username(cls, username: str) -> Optional["User"]:
        row = fetch_one(
            """
            SELECT id, username, email, password_hash, created_at, updated_at
            FROM app.user
            WHERE username = %s
            """,
            (username,),
        )
        return cls.from_row(row) if row else None

    @classmethod
    def get_by_email(cls, email: str) -> Optional["User"]:
        row = fetch_one(
            """
            SELECT id, username, email, password_hash, created_at, updated_at
            FROM app.user
            WHERE email = %s
            """,
            (email,),
        )
        return cls.from_row(row) if row else None

    @classmethod
    def create(cls, username: str, email: str, password_hash: str) -> "User":
        row = execute_returning(
            """
            INSERT INTO app.user (username, email, password_hash)
            VALUES (%s, %s, %s)
            RETURNING id, username, email, password_hash, created_at, updated_at
            """,
            (username, email, password_hash),
        )
        return cls.from_row(row)

    @classmethod
    def list_all(cls) -> Iterable["User"]:
        rows = fetch_all(
            """
            SELECT id, username, email, password_hash, created_at, updated_at
            FROM app.user
            ORDER BY created_at DESC
            """
        )
        return [cls.from_row(row) for row in rows]

    def to_record(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_public_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }
