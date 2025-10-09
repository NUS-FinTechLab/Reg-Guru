"""Data access helpers for working with refresh token records."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping, Optional
from uuid import UUID

from ..auth import generate_refresh_token
from ..db import execute, execute_returning, fetch_one

Row = Mapping[str, Any]

_DEFAULT_REFRESH_EXPIRATION = timedelta(days=30)


@dataclass(frozen=True)
class RefreshToken:
    id: UUID
    user_id: UUID
    token_hash: str
    expires_at: datetime
    revoked_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def compute_hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @classmethod
    def from_row(cls, row: Row) -> RefreshToken:
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            token_hash=row["token_hash"],
            expires_at=row["expires_at"],
            revoked_at=row.get("revoked_at"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _normalize_user_id(user_id: UUID | str) -> str:
        return str(user_id)

    @classmethod
    def issue(
        cls,
        user_id: UUID | str,
        *,
        expires_delta: Optional[timedelta] = None,
    ) -> tuple[str, "RefreshToken"]:
        token_value = generate_refresh_token()
        expires_at = datetime.now(timezone.utc) + (expires_delta or _DEFAULT_REFRESH_EXPIRATION)
        token_hash = cls.compute_hash(token_value)
        row = execute_returning(
            """
            INSERT INTO app.refresh_token (user_id, token_hash, expires_at)
            VALUES (%s, %s, %s)
            RETURNING id, user_id, token_hash, expires_at, revoked_at, created_at, updated_at
            """,
            (
                cls._normalize_user_id(user_id),
                token_hash,
                expires_at,
            ),
        )
        return token_value, cls.from_row(row)

    @classmethod
    def get_active_by_token(cls, token: str) -> Optional["RefreshToken"]:
        token_hash = cls.compute_hash(token)
        row = fetch_one(
            """
            SELECT id, user_id, token_hash, expires_at, revoked_at, created_at, updated_at
            FROM app.refresh_token
            WHERE token_hash = %s
              AND revoked_at IS NULL
              AND expires_at > NOW()
            LIMIT 1
            """,
            (token_hash,),
        )
        return cls.from_row(row) if row else None

    @classmethod
    def revoke(cls, token_id: UUID | str) -> None:
        execute(
            """
            UPDATE app.refresh_token
            SET revoked_at = NOW(), updated_at = NOW()
            WHERE id = %s AND revoked_at IS NULL
            """,
            (str(token_id),),
        )

    def revoke_this(self) -> None:
        RefreshToken.revoke(self.id)
