"""Storage package exposing compatibility helpers."""

from ..models import Chat, ChatHistory, ChatMessage, Feedback, User
from .chats import (
    create_chat,
    ensure_chat,
    get_chat_by_id,
    list_chats_for_user,
    touch_chat,
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
    "Chat",
    "ChatHistory",
    "ChatMessage",
    "Feedback",
    "User",
    "create_chat",
    "ensure_chat",
    "get_chat_by_id",
    "list_chats_for_user",
    "touch_chat",
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
