"""Storage package exposing compatibility helpers."""

from ..models import ChatHistory, ChatMessage, ChatSession, Feedback, User
from .chat_sessions import (
    create_session,
    get_session_by_external_id,
    get_session_by_id,
    list_sessions_for_user,
    touch_session,
    upsert_session,
)
from .feedback import insert_feedback
from .messages import insert_message, list_messages
from .chat_history import insert_chat_history, list_chat_history
from .users import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
    list_users,
)

__all__ = [
    "ChatHistory",
    "ChatMessage",
    "ChatSession",
    "Feedback",
    "User",
    "create_session",
    "get_session_by_external_id",
    "get_session_by_id",
    "list_sessions_for_user",
    "touch_session",
    "upsert_session",
    "insert_feedback",
    "insert_message",
    "list_messages",
    "insert_chat_history",
    "list_chat_history",
    "create_user",
    "get_user_by_email",
    "get_user_by_id",
    "get_user_by_username",
    "list_users",
]
