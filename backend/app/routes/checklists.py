"""Checklist CRUD HTTP handlers."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence, Tuple
from uuid import UUID

from flask import g, jsonify, request

from ..config import CHECKLIST_DEFAULT_PROMPT
from ..models import Checklist, ChecklistItem, ChecklistStage
from ..utils import generate_checklist_draft
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

def _normalize_position(raw_position: Any, default: int) -> int:
    if raw_position in (None, ""):
        return default
    try:
        position = int(raw_position)
    except (TypeError, ValueError):
        return default
    return max(0, position)


def _parse_stage_items(raw_items: Any, stage_index: int) -> List[Dict[str, Any]]:
    if raw_items in (None, ""):
        return []
    if not isinstance(raw_items, list):
        raise ValueError(f"items for stage {stage_index + 1} must be provided as an array")

    parsed: List[Dict[str, Any]] = []
    for item_index, raw_item in enumerate(raw_items):
        if not isinstance(raw_item, dict):
            raise ValueError(
                f"Checklist item at stage {stage_index + 1} index {item_index} must be an object"
            )

        content = str(raw_item.get("content") or "").strip()
        if not content:
            raise ValueError(
                f"Checklist item content is required at stage {stage_index + 1}, index {item_index}"
            )

        status = _normalize_status(raw_item.get("status"))
        priority = _normalize_priority(raw_item.get("priority"))
        position = _normalize_position(raw_item.get("position"), item_index)

        parsed.append(
            {
                "content": content,
                "status": status,
                "priority": priority,
                "position": position,
            }
        )
    return parsed


def _parse_stage_payload(data: Mapping[str, Any]) -> List[Dict[str, Any]]:
    if "stages" in data:
        raw_stages = data.get("stages")
        if raw_stages in (None, ""):
            return []
        if not isinstance(raw_stages, list):
            raise ValueError("stages must be provided as an array")

        parsed: List[Dict[str, Any]] = []
        for stage_index, raw_stage in enumerate(raw_stages):
            if not isinstance(raw_stage, dict):
                raise ValueError(f"Stage at index {stage_index} must be an object")

            title = str(raw_stage.get("title") or "").strip()
            if not title:
                raise ValueError(f"Stage title is required at index {stage_index}")

            description = str(raw_stage.get("description") or "").strip()
            position = _normalize_position(raw_stage.get("position"), stage_index)
            items = _parse_stage_items(raw_stage.get("items"), stage_index)

            parsed.append(
                {
                    "title": title,
                    "description": description,
                    "position": position,
                    "items": items,
                }
            )
        return parsed

    fallback_items = _parse_stage_items(data.get("items"), 0)
    if not fallback_items:
        return []
    return [
        {
            "title": "Stage 1",
            "description": "",
            "position": 0,
            "items": fallback_items,
        }
    ]


def _load_stages_with_items(
    checklist_id: UUID | str,
) -> Tuple[List[ChecklistStage], Dict[UUID, List[ChecklistItem]]]:
    stages = list(ChecklistStage.list_for_checklist(checklist_id))
    items = list(ChecklistItem.list_for_checklist(checklist_id))

    items_by_stage: Dict[UUID, List[ChecklistItem]] = {stage.id: [] for stage in stages}
    for item in items:
        items_by_stage.setdefault(item.stage_id, []).append(item)
    return stages, items_by_stage


def _persist_stages(
    *,
    checklist_id: UUID | str,
    stage_payloads: Sequence[Dict[str, Any]],
) -> Tuple[List[ChecklistStage], Dict[UUID, List[ChecklistItem]]]:
    created_stages: List[ChecklistStage] = []
    items_by_stage: Dict[UUID, List[ChecklistItem]] = {}

    for index, stage_payload in enumerate(stage_payloads):
        stage_position = _normalize_position(stage_payload.get("position"), index)
        stage = ChecklistStage.create(
            checklist_id=checklist_id,
            title=stage_payload["title"],
            description=str(stage_payload.get("description") or ""),
            position=stage_position,
        )
        created_stages.append(stage)

        raw_items: Sequence[Dict[str, Any]] = stage_payload.get("items") or []
        normalized_items: List[Dict[str, Any]] = []
        for item_index, item_payload in enumerate(raw_items):
            normalized_items.append(
                {
                    "content": item_payload["content"],
                    "status": item_payload["status"],
                    "priority": item_payload["priority"],
                    "position": _normalize_position(item_payload.get("position"), item_index),
                }
            )

        created_items = ChecklistItem.create_many(
            checklist_id=checklist_id,
            stage_id=stage.id,
            items=normalized_items,
        )
        items_by_stage[stage.id] = list(created_items)

    return created_stages, items_by_stage


def _serialize_checklist_with_stages(
    checklist: Checklist,
    stages: Sequence[ChecklistStage],
    items_by_stage: Mapping[UUID, Sequence[ChecklistItem]],
) -> Dict[str, Any]:
    stage_payloads: List[Dict[str, Any]] = []
    flattened_items: List[Dict[str, Any]] = []
    total_items = 0
    finished_items = 0

    for stage in stages:
        stage_items = list(items_by_stage.get(stage.id, []))
        total_items += len(stage_items)
        finished_items += sum(1 for item in stage_items if item.status == "finished")

        stage_item_payloads = [item.to_api_dict() for item in stage_items]
        stage_payload = {**stage.to_api_dict(), "items": stage_item_payloads}

        stage_payloads.append(stage_payload)
        flattened_items.extend(stage_item_payloads)

    progress = (finished_items / total_items) if total_items else 0.0

    return {
        **checklist.to_api_dict(),
        "stages": stage_payloads,
        "stageCount": len(stage_payloads),
        "items": flattened_items,
        "totalItems": total_items,
        "finishedItems": finished_items,
        "progress": progress,
    }


def _normalize_generated_priority(raw_priority: Any) -> str:
    value = str(raw_priority or "medium").strip().lower()
    if value not in ChecklistItem.PRIORITIES:
        return "medium"
    return value


def _compose_generated_item_content(item: Dict[str, Any]) -> str:
    title = str(item.get("title", "")).strip()
    description = str(item.get("description", "")).strip()

    content_parts: List[str] = []
    if title and description:
        content_parts.append(f"{title}: {description}")
    elif title:
        content_parts.append(title)
    elif description:
        content_parts.append(description)

    return "\n".join(content_parts) if content_parts else "Generated task"


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
        stage_count = int(entry.get("stage_count", 0) or 0)
        progress = (finished_items / total_items) if total_items else 0.0
        payload.append(
            {
                **checklist.to_api_dict(),
                "stageCount": stage_count,
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
        stage_payloads = _parse_stage_payload(data)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    checklist = Checklist.create(user_id=user_id, title=title, description=description)
    stages: List[ChecklistStage]
    items_by_stage: Dict[UUID, List[ChecklistItem]]
    if stage_payloads:
        stages, items_by_stage = _persist_stages(
            checklist_id=checklist.id,
            stage_payloads=stage_payloads,
        )
    else:
        stages, items_by_stage = [], {}

    serialized = _serialize_checklist_with_stages(checklist, stages, items_by_stage)
    return jsonify({"checklist": serialized}), 201


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

    stages, items_by_stage = _load_stages_with_items(checklist.id)
    serialized = _serialize_checklist_with_stages(checklist, stages, items_by_stage)
    return jsonify({"checklist": serialized}), 200


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

    stage_payloads: List[Dict[str, Any]] | None = None
    if "stages" in data or "items" in data:
        try:
            stage_payloads = _parse_stage_payload(data)
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

    if stage_payloads is None:
        stages, items_by_stage = _load_stages_with_items(checklist.id)
    else:
        ChecklistStage.delete_for_checklist(checklist.id)
        if stage_payloads:
            stages, items_by_stage = _persist_stages(
                checklist_id=checklist.id,
                stage_payloads=stage_payloads,
            )
        else:
            stages, items_by_stage = [], {}

    serialized = _serialize_checklist_with_stages(checklist, stages, items_by_stage)
    return jsonify({"checklist": serialized}), 200


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


@api.route("/checklists/<checklist_id>/items/<item_id>/status", methods=["PATCH"])
def update_checklist_item_status(checklist_id: str, item_id: str):
    user_id = _require_user_id()
    if isinstance(user_id, tuple):
        return user_id

    normalized_checklist_id = _parse_uuid(checklist_id)
    if isinstance(normalized_checklist_id, tuple):
        return normalized_checklist_id

    normalized_item_id = _parse_uuid(item_id)
    if isinstance(normalized_item_id, tuple):
        return normalized_item_id

    data = request.get_json(silent=True) or {}
    if "status" not in data:
        return jsonify({"error": "status is required"}), 400

    try:
        normalized_status = _normalize_status(data.get("status"))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    updated_item = ChecklistItem.update_status_for_user(
        checklist_id=normalized_checklist_id,
        item_id=normalized_item_id,
        user_id=user_id,
        status=normalized_status,
    )
    if updated_item is None:
        return jsonify({"error": "Checklist item not found"}), 404

    checklist = Checklist.get_for_user(normalized_checklist_id, user_id)
    checklist_payload = (
        {
            "id": normalized_checklist_id,
            "updatedAt": checklist.updated_at.isoformat(),
        }
        if checklist
        else None
    )

    return (
        jsonify(
            {
                "item": updated_item.to_api_dict(),
                "checklist": checklist_payload,
            }
        ),
        200,
    )


@api.route("/checklists/<checklist_id>/items/<item_id>", methods=["PATCH"])
def update_checklist_item(checklist_id: str, item_id: str):
    user_id = _require_user_id()
    if isinstance(user_id, tuple):
        return user_id

    normalized_checklist_id = _parse_uuid(checklist_id)
    if isinstance(normalized_checklist_id, tuple):
        return normalized_checklist_id

    normalized_item_id = _parse_uuid(item_id)
    if isinstance(normalized_item_id, tuple):
        return normalized_item_id

    data = request.get_json(silent=True) or {}

    if not any(key in data for key in ("content", "status", "priority")):
        return jsonify({"error": "At least one of content, status, or priority is required"}), 400

    try:
        normalized_status = _normalize_status(data.get("status")) if "status" in data else None
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        normalized_priority = _normalize_priority(data.get("priority")) if "priority" in data else None
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    content = data.get("content")
    if content is not None:
        content = str(content or "").strip()
        if not content:
            return jsonify({"error": "content cannot be empty"}), 400

    updated_item = ChecklistItem.update_for_user(
        checklist_id=normalized_checklist_id,
        item_id=normalized_item_id,
        user_id=user_id,
        content=content,
        status=normalized_status,
        priority=normalized_priority,
    )

    if updated_item is None:
        return jsonify({"error": "Checklist item not found"}), 404

    checklist = Checklist.get_for_user(normalized_checklist_id, user_id)
    checklist_payload = (
        {
            "id": normalized_checklist_id,
            "updatedAt": checklist.updated_at.isoformat(),
        }
        if checklist
        else None
    )

    return (
        jsonify(
            {
                "item": updated_item.to_api_dict(),
                "checklist": checklist_payload,
            }
        ),
        200,
    )


@api.route("/checklists/<checklist_id>/items/<item_id>", methods=["DELETE"])
def delete_checklist_item(checklist_id: str, item_id: str):
    user_id = _require_user_id()
    if isinstance(user_id, tuple):
        return user_id

    normalized_checklist_id = _parse_uuid(checklist_id)
    if isinstance(normalized_checklist_id, tuple):
        return normalized_checklist_id

    normalized_item_id = _parse_uuid(item_id)
    if isinstance(normalized_item_id, tuple):
        return normalized_item_id

    deleted = ChecklistItem.delete_for_user(
        checklist_id=normalized_checklist_id,
        item_id=normalized_item_id,
        user_id=user_id,
    )

    if not deleted:
        return jsonify({"error": "Checklist item not found"}), 404

    return ("", 204)


@api.route("/checklists/generate", methods=["POST"])
def generate_checklist_draft_route():
    user_id = _require_user_id()
    if isinstance(user_id, tuple):
        return user_id

    data = request.get_json(silent=True) or {}
    mission = str(data.get("mission", "")).strip()
    context = str(data.get("context", "")).strip()
    prompt_text = str(data.get("prompt", "")).strip()
    region_raw = str(data.get("region", "us")).strip().lower()

    if not mission:
        return jsonify({"error": "mission is required"}), 400

    valid_regions = {"us", "sg", "eu"}
    if region_raw not in valid_regions:
        allowed = ", ".join(sorted(valid_regions))
        return jsonify({"error": f"region must be one of: {allowed}"}), 400

    if not prompt_text:
        prompt_text = CHECKLIST_DEFAULT_PROMPT

    try:
        result_payload = generate_checklist_draft(
            prompt_text,
            region_raw,
            mission=mission,
            context=context,
        )
    except NotImplementedError:
        return jsonify({"error": "Checklist generation is not implemented yet"}), 501
    except Exception as exc:  # pragma: no cover - defensive logging
        return jsonify({"error": f"Failed to generate checklist: {exc}"}), 500

    generated_checklist = result_payload.get("checklist") or {}
    if not isinstance(generated_checklist, dict):
        return jsonify({"error": "Generated checklist payload is invalid"}), 502

    overview = str(generated_checklist.get("overview", "")).strip()
    focus_areas = generated_checklist.get("focusAreas") or []
    if not isinstance(focus_areas, list):
        focus_areas = []

    title = mission or overview or "Generated Compliance Checklist"

    description_lines: List[str] = []
    if overview:
        description_lines.append(overview)
    if context:
        description_lines.append(f"Context: {context}")
    if focus_areas:
        focus_summary = ", ".join(str(area).strip() for area in focus_areas if str(area).strip())
        if focus_summary:
            description_lines.append(f"Focus areas: {focus_summary}")

    description = "\n\n".join(description_lines).strip() or context or overview or title

    checklist_record = Checklist.create(user_id=user_id, title=title, description=description)

    stage_payloads: List[Dict[str, Any]] = []
    generated_stages = generated_checklist.get("stages") or []
    if isinstance(generated_stages, list):
        for stage_index, raw_stage in enumerate(generated_stages):
            if not isinstance(raw_stage, dict):
                continue

            stage_title = str(raw_stage.get("title") or "").strip() or f"Stage {stage_index + 1}"
            stage_description = str(raw_stage.get("description") or "").strip()
            stage_position = _normalize_position(raw_stage.get("position"), stage_index)

            raw_stage_items = raw_stage.get("items") or []
            if not isinstance(raw_stage_items, list):
                raw_stage_items = []

            normalized_items: List[Dict[str, Any]] = []
            for item_index, stage_item in enumerate(raw_stage_items):
                if not isinstance(stage_item, dict):
                    continue
                content = _compose_generated_item_content(stage_item)
                priority = _normalize_generated_priority(stage_item.get("priority"))
                normalized_items.append(
                    {
                        "content": content,
                        "status": "not_started",
                        "priority": priority,
                        "position": item_index,
                    }
                )

            stage_payloads.append(
                {
                    "title": stage_title,
                    "description": stage_description,
                    "position": stage_position,
                    "items": normalized_items,
                }
            )

    if not stage_payloads:
        generated_items = generated_checklist.get("items") or []
        if not isinstance(generated_items, list):
            generated_items = []

        persistence_payload: List[Dict[str, Any]] = []
        for item in generated_items:
            if not isinstance(item, dict):
                continue
            content = _compose_generated_item_content(item)
            priority = _normalize_generated_priority(item.get("priority"))
            persistence_payload.append(
                {
                    "content": content,
                    "status": "not_started",
                    "priority": priority,
                }
            )

        if persistence_payload:
            summary_description = str(focus_areas[0]).strip() if focus_areas else ""
            stage_payloads = [
                {
                    "title": "Initial Stage",
                    "description": summary_description,
                    "position": 0,
                    "items": [
                        {
                            **item,
                            "position": index,
                        }
                        for index, item in enumerate(persistence_payload)
                    ],
                }
            ]

    stages: List[ChecklistStage]
    items_by_stage: Dict[UUID, List[ChecklistItem]]
    if stage_payloads:
        stages, items_by_stage = _persist_stages(
            checklist_id=checklist_record.id,
            stage_payloads=stage_payloads,
        )
    else:
        stages, items_by_stage = [], {}

    serialized_checklist = _serialize_checklist_with_stages(
        checklist_record,
        stages,
        items_by_stage,
    )

    metadata = result_payload.get("metadata") or {}
    if isinstance(metadata, dict):
        metadata = {
            **metadata,
            "createdChecklistId": serialized_checklist["id"],
        }
    else:
        metadata = {"createdChecklistId": serialized_checklist["id"]}

    response_payload = {
        "checklist": generated_checklist,
        "sources": result_payload.get("sources") or [],
        "metadata": metadata,
        "createdChecklist": serialized_checklist,
    }

    return jsonify({"result": response_payload}), 201
