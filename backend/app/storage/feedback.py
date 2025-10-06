"""Storage helpers that wrap feedback models."""

from __future__ import annotations

from typing import Dict, Optional

from ..models import Feedback


def insert_feedback(
    session_id: str,
    rating: str,
    comments: str = "",
    message_id: Optional[int] = None,
) -> Dict[str, object]:
    return Feedback.create(session_id, rating, comments, message_id).to_record()


__all__ = ["insert_feedback"]
