"""Storage helpers that wrap feedback models."""

from __future__ import annotations

from typing import Dict, Optional

from ..models import Feedback


def insert_feedback(
    chat_id: str,
    rating: str,
    comments: str = "",
    message_id: Optional[int] = None,
) -> Dict[str, object]:
    return Feedback.create(chat_id, rating, comments, message_id).to_record()


__all__ = ["insert_feedback"]
