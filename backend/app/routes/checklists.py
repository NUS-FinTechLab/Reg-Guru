"""Checklist CRUD HTTP handlers."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List
from uuid import UUID

from flask import g, jsonify, request

from ..models import Checklist, ChecklistItem
from . import api


def _require_user_id() -> str | tuple[Any, int]:
    user_id = getattr(g, "authenticated_user_id", None)
    if not user_id:
        return jsonify({"error": "Authenticated user mismatch"}), 403
    return str(user_id)


def _parse_uuid(raw_id: str) -> str | tuple[Any, int]:
    try:
        return str(UUID(str(raw_id)))
    except ValueError:
        return jsonify({"error": "Invalid checklist id"}), 400


def _normalize_status(raw_status: Any) -> str:
    value = str(raw_status or "not_started").strip().lower().replace("-", "_")
    if value not in ChecklistItem.STATUSES:
        raise ValueError(
            f"Invalid status '{raw_status}'. Expected one of: {', '.join(ChecklistItem.STATUSES)}"
        )
    return value


def _normalize_priority(raw_priority: Any) -> str:
    value = str(raw_priority or "medium").strip().lower()
    if value not in ChecklistItem.PRIORITIES:
        raise ValueError(
            "Invalid priority '{0}'. Expected one of: {1}".format(
                raw_priority, ", ".join(ChecklistItem.PRIORITIES)
            )
        )
    return value


def _parse_items(raw_items: Any) -> List[Dict[str, str]]:
    if raw_items in (None, ""):
        return []
    if not isinstance(raw_items, list):
        raise ValueError("items must be provided as an array")

    parsed: List[Dict[str, str]] = []
    for index, raw_item in enumerate(raw_items):
        if not isinstance(raw_item, dict):
            raise ValueError(f"Checklist item at index {index} must be an object")

        content = str(raw_item.get("content", "")).strip()
        if not content:
            raise ValueError(f"Checklist item content is required at index {index}")

        status = _normalize_status(raw_item.get("status"))
        priority = _normalize_priority(raw_item.get("priority"))

        parsed.append({
            "content": content,
            "status": status,
            "priority": priority,
        })
    return parsed


def _serialize_checklist_with_items(
    checklist: Checklist,
    items: Iterable[ChecklistItem],
) -> Dict[str, Any]:
    item_list = list(items)
    total_items = len(item_list)
    finished = sum(1 for item in item_list if item.status == "finished")
    progress = (finished / total_items) if total_items else 0.0

    return {
        **checklist.to_api_dict(),
        "items": [item.to_api_dict() for item in item_list],
        "totalItems": total_items,
        "finishedItems": finished,
        "progress": progress,
    }


@api.route("/checklists", methods=["GET"])
def list_checklists():
    user_id = _require_user_id()
    if isinstance(user_id, tuple):
        return user_id

    summaries = Checklist.list_with_progress_for_user(user_id)
    payload = []
    for entry in summaries:
        checklist: Checklist = entry["checklist"]
        total_items = int(entry.get("total_items", 0) or 0)
        finished_items = int(entry.get("finished_items", 0) or 0)
        progress = (finished_items / total_items) if total_items else 0.0
        payload.append(
            {
                **checklist.to_api_dict(),
                "totalItems": total_items,
                "finishedItems": finished_items,
                "progress": progress,
            }
        )

    return jsonify({"checklists": payload}), 200


@api.route("/checklists", methods=["POST"])
def create_checklist():
    user_id = _require_user_id()
    if isinstance(user_id, tuple):
        return user_id

    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    description = str(data.get("description", "")).strip()

    if not title:
        return jsonify({"error": "title is required"}), 400
    if not description:
        return jsonify({"error": "description is required"}), 400

    try:
        items = _parse_items(data.get("items"))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    checklist = Checklist.create(user_id=user_id, title=title, description=description)
    created_items = ChecklistItem.create_many(checklist_id=checklist.id, items=items)

    return jsonify({"checklist": _serialize_checklist_with_items(checklist, created_items)}), 201


@api.route("/checklists/<checklist_id>", methods=["GET"])
def get_checklist(checklist_id: str):
    user_id = _require_user_id()
    if isinstance(user_id, tuple):
        return user_id

    normalized_id = _parse_uuid(checklist_id)
    if isinstance(normalized_id, tuple):
        return normalized_id

    checklist = Checklist.get_for_user(normalized_id, user_id)
    if checklist is None:
        return jsonify({"error": "Checklist not found"}), 404

    items = ChecklistItem.list_for_checklist(checklist.id)
    return jsonify({"checklist": _serialize_checklist_with_items(checklist, items)}), 200


@api.route("/checklists/<checklist_id>", methods=["PUT"])
def update_checklist(checklist_id: str):
    user_id = _require_user_id()
    if isinstance(user_id, tuple):
        return user_id

    normalized_id = _parse_uuid(checklist_id)
    if isinstance(normalized_id, tuple):
        return normalized_id

    data = request.get_json(silent=True) or {}
    if "title" not in data or "description" not in data:
        return jsonify({"error": "title and description are required"}), 400

    title = str(data.get("title", "")).strip()
    description = str(data.get("description", "")).strip()

    if not title:
        return jsonify({"error": "title is required"}), 400
    if not description:
        return jsonify({"error": "description is required"}), 400

    items_payload: List[Dict[str, str]] | None = None
    if "items" in data:
        try:
            items_payload = _parse_items(data.get("items"))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

    checklist = Checklist.update(
        checklist_id=normalized_id,
        user_id=user_id,
        title=title,
        description=description,
    )
    if checklist is None:
        return jsonify({"error": "Checklist not found"}), 404

    if items_payload is not None:
        ChecklistItem.replace_for_checklist(checklist_id=checklist.id, items=items_payload)

    items = ChecklistItem.list_for_checklist(checklist.id)
    return jsonify({"checklist": _serialize_checklist_with_items(checklist, items)}), 200


@api.route("/checklists/<checklist_id>", methods=["DELETE"])
def delete_checklist(checklist_id: str):
    user_id = _require_user_id()
    if isinstance(user_id, tuple):
        return user_id

    normalized_id = _parse_uuid(checklist_id)
    if isinstance(normalized_id, tuple):
        return normalized_id

    deleted = Checklist.delete(checklist_id=normalized_id, user_id=user_id)
    if not deleted:
        return jsonify({"error": "Checklist not found"}), 404

    return ("", 204)

