"""Storage helpers for working with user records."""

from __future__ import annotations

from typing import Dict, List, Optional

from ..models import User


def create_user(username: str, email: str, password_hash: str) -> Dict[str, object]:
    return User.create(username, email, password_hash).to_record()


def get_user_by_id(user_id: str) -> Optional[Dict[str, object]]:
    user = User.get_by_id(user_id)
    return user.to_record() if user else None


def get_user_by_username(username: str) -> Optional[Dict[str, object]]:
    user = User.get_by_username(username)
    return user.to_record() if user else None


def get_user_by_email(email: str) -> Optional[Dict[str, object]]:
    user = User.get_by_email(email)
    return user.to_record() if user else None


def list_users() -> List[Dict[str, object]]:
    return [user.to_record() for user in User.list_all()]


__all__ = [
    "create_user",
    "get_user_by_email",
    "get_user_by_id",
    "get_user_by_username",
    "list_users",
]
