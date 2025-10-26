"""Database helpers for interacting with PostgreSQL."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Dict, Iterable, Optional

import psycopg2
from psycopg2.extras import RealDictCursor, Json
from psycopg2.pool import SimpleConnectionPool

from .config import (
    DB_HOST,
    DB_PORT,
    DB_USER,
    DB_PASSWORD,
    DB_NAME,
    DB_SSLMODE,
    DB_MIN_CONN,
    DB_MAX_CONN,
)


logger = logging.getLogger(__name__)

_pool: Optional[SimpleConnectionPool] = None


def _dsn() -> str:
    required = {
        "DB_HOST": DB_HOST,
        "DB_PORT": DB_PORT,
        "DB_USER": DB_USER,
        "DB_PASSWORD": DB_PASSWORD,
        "DB_NAME": DB_NAME,
    }

    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError(
            "Missing database configuration for: " + ", ".join(sorted(missing))
        )

    params = [
        f"host={DB_HOST}",
        f"port={DB_PORT}",
        f"user={DB_USER}",
        f"password={DB_PASSWORD}",
        f"dbname={DB_NAME}",
    ]

    if DB_SSLMODE:
        params.append(f"sslmode={DB_SSLMODE}")

    return " ".join(params)


def _get_pool() -> SimpleConnectionPool:
    global _pool
    if _pool is None:
        _pool = SimpleConnectionPool(DB_MIN_CONN, DB_MAX_CONN, _dsn())
        logger.info("Initialized PostgreSQL connection pool")
    return _pool


@contextmanager
def get_connection():
    pool = _get_pool()
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        try:
            if conn and not conn.closed:
                conn.rollback()
        except psycopg2.InterfaceError:
            logger.warning("Failed to roll back connection; already closed", exc_info=True)
        raise
    finally:
        try:
            if conn and not conn.closed:
                pool.putconn(conn)
            else:
                pool.putconn(conn, close=True)
        except Exception:
            logger.exception("Failed to return connection to pool")


def close_pool():
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None
        logger.info("Closed PostgreSQL connection pool")


def fetch_one(query: str, params: Optional[Iterable[Any]] = None) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchone()


def fetch_all(query: str, params: Optional[Iterable[Any]] = None) -> Iterable[Dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchall()


def execute(query: str, params: Optional[Iterable[Any]] = None) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)


def execute_returning(query: str, params: Optional[Iterable[Any]] = None) -> Dict[str, Any]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("Expected row but query returned nothing")
            return row


def to_jsonb(value: Any) -> Json:
    """Helper to serialize Python structures into JSONB columns."""

    return Json(value, dumps=None)
