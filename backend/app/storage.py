"""Persistence helpers for chat sessions, messages, and feedback."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from psycopg2.extras import RealDictRow

from .db import execute, execute_returning, fetch_all, fetch_one, to_jsonb


def get_session_by_external_id(external_id: str) -> Optional[Dict[str, Any]]:
    return fetch_one(
        """
        SELECT id, external_id, region, created_at, updated_at
        FROM app.chat_sessions
        WHERE external_id = %s
        """,
        (external_id,),
    )


def get_session_by_id(session_id: str) -> Optional[Dict[str, Any]]:
    return fetch_one(
        """
        SELECT id, external_id, region, created_at, updated_at
        FROM app.chat_sessions
        WHERE id = %s
        """,
        (session_id,),
    )


def create_session(external_id: str, region: str) -> Dict[str, Any]:
    return execute_returning(
        """
        INSERT INTO app.chat_sessions (external_id, region)
        VALUES (%s, %s)
        RETURNING id, external_id, region, created_at, updated_at
        """,
        (external_id, region),
    )


def touch_session(session_id: str) -> None:
    execute(
        """
        UPDATE app.chat_sessions
        SET updated_at = NOW()
        WHERE id = %s
        """,
        (session_id,),
    )


def upsert_session(external_id: str, region: str) -> Dict[str, Any]:
    session = get_session_by_external_id(external_id)
    if session is None:
        session = create_session(external_id, region)
    elif session["region"] != region:
        session = execute_returning(
            """
            UPDATE app.chat_sessions
            SET region = %s, updated_at = NOW()
            WHERE id = %s
            RETURNING id, external_id, region, created_at, updated_at
            """,
            (region, session["id"]),
        )
    return session


def insert_message(
    session_id: str,
    role: str,
    body: str,
    sources: Optional[Iterable[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    row = execute_returning(
        """
        INSERT INTO app.chat_messages (session_id, role, body, sources)
        VALUES (%s, %s, %s, %s)
        RETURNING id, session_id, role, body, sources, sent_at
        """,
        (
            session_id,
            role,
            body,
            to_jsonb(list(sources) if sources is not None else []),
        ),
    )
    touch_session(session_id)
    return row


def list_messages(session_id: str) -> Iterable[RealDictRow]:
    return fetch_all(
        """
        SELECT id, session_id, role, body, sources, sent_at
        FROM app.chat_messages
        WHERE session_id = %s
        ORDER BY sent_at ASC
        """,
        (session_id,),
    )


def insert_feedback(
    session_id: str,
    rating: str,
    comments: str = "",
    message_id: Optional[int] = None,
) -> Dict[str, Any]:
    return execute_returning(
        """
        INSERT INTO app.feedback (session_id, message_id, rating, comments)
        VALUES (%s, %s, %s, NULLIF(%s, ''))
        RETURNING id, session_id, message_id, rating, comments, created_at
        """,
        (session_id, message_id, rating, comments or ""),
    )


def list_saved_queries(limit: int = 25) -> Iterable[RealDictRow]:
    return fetch_all(
        """
        SELECT
            sq.id,
            sq.session_id,
            cs.external_id AS chat_external_id,
            sq.query_text,
            sq.response_summary,
            sq.created_at
        FROM app.saved_queries sq
        LEFT JOIN app.chat_sessions cs ON cs.id = sq.session_id
        ORDER BY sq.created_at DESC
        LIMIT %s
        """,
        (limit,),
    )


def insert_saved_query(
    session_id: Optional[str], query_text: str, response_summary: Optional[str] = None
) -> Dict[str, Any]:
    return execute_returning(
        """
        INSERT INTO app.saved_queries (session_id, query_text, response_summary)
        VALUES (%s, %s, %s)
        RETURNING id, session_id, query_text, response_summary, created_at
        """,
        (session_id, query_text, response_summary),
    )
