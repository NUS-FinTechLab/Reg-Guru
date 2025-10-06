"""API route package that registers all endpoint modules."""

from __future__ import annotations

from flask import Blueprint

api = Blueprint("api", __name__, url_prefix="/api")

# Import route modules so they attach their handlers to the blueprint.
from . import auth  # noqa: F401  (imported for side effects)
from . import chat  # noqa: F401
from . import feedback  # noqa: F401
from . import misc  # noqa: F401
from . import chat_history  # noqa: F401
from . import sessions  # noqa: F401
from . import users  # noqa: F401

__all__ = ["api"]
