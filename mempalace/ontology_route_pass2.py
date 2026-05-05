from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from .ontology_run import validate_run_id


PHASE_NAME = "route_pass2"
RAW_RESPONSE_EXCERPT_MAX_CHARS = 280
DRAWER_EXCERPT_MAX_CHARS = 240
PROMPT_DRAWER_EXCERPT_MAX_CHARS = 1200
LOW_CONFIDENCE_THRESHOLD = 0.5
_ROUTE_CANDIDATES_PHASE_NAME = "route_candidates"
_VALID_NEXT_ACTIONS = frozenset({"reroute", "manual_review", "drop", "retry_later"})
_SLUG_RE = re.compile(r"^[a-z0-9_]+$")


@dataclass(frozen=True)
class _NormalizedDrawer:
    drawer_id: str
    wing: str
    room: str
    drawer_excerpt: str


@dataclass(frozen=True)
class _ShortlistCandidate:
    rank: int
    candidate_id: str
    candidate_key: str
    canonical_wing: str
    canonical_room: str
    label: str
    definition: str
    canonical_candidate_record_ref: str | None
    source_candidate_refs: list[dict[str, Any]]
    examples: list[dict[str, Any]]


@dataclass(frozen=True)
class _RouteCandidateContext:
    run_id: str | None
    sequence: int | None
    attempt: int | None
    route_candidate_record_ref: str | None
    shortlist: list[_ShortlistCandidate]


def build_route_pass2_prompt(
    drawer: Mapping[str, Any],
    route_candidate_record: Mapping[str, Any],
) -> str:
    normalized_drawer = _normalize_drawer(
        drawer,
        drawer_excerpt_max_chars=PROMPT_DRAWER_EXCERPT_MAX_CHARS,
    )
    context = _normalize_route_candidate_context(
        route_candidate_record,
        require_phase_metadata=False,
    )

    shortlist = [
        {
            "rank": candidate.rank,
            "candidate_id": candidate.candidate_id,
            "candidate_key": candidate.candidate_key,
            "canonical_wing": candidate.canonical_wing,
            "canonical_room": candidate.canonical_room,
            "label": candidate.label,
            "definition": candidate.definition,
            "canonical_candidate_record_ref": candidate.canonical_candidate_record_ref,
            "source_candidate_record_refs": [
                ref["source_candidate_record_ref"]
                for ref in candidate.source_candidate_refs
                if isinstance(ref.get("source_candidate_record_ref"), str)
            ],
            "example_excerpts": [
                item["excerpt"]
                for item in candidate.examples
                if isinstance(item.get("excerpt"), str)
            ][:2],
        }
        for candidate in context.shortlist
    ]

    lines = [
        "You route one source drawer to one canonical ontology candidate.",
        "",
        "Return JSON only. No prose. No code fences.",
        "",
        "SOURCE DRAWER",
        json.dumps(
            {
                "drawer_id": normalized_drawer.drawer_id,
                "source_wing": normalized_drawer.wing,
                "source_room": normalized_drawer.room,
                "drawer_excerpt": normalized_drawer.drawer_excerpt,
            },
            indent=2,
            sort_keys=True,
        ),
        "",
        "SHORTLIST",
        json.dumps(shortlist, indent=2, sort_keys=True),
        "",
        "TASK",
        "- Choose exactly one shortlist candidate or `null`.",
        "- Never invent a candidate outside the shortlist.",
        "- If you choose a candidate, copy `candidate_id`, `candidate_key`, `canonical_wing`, and `canonical_room` exactly from the shortlist.",
        "- Use `route: \"null\"` when no shortlist candidate is a credible match.",
        "- `route_confidence` must be a number from 0 to 1.",
        "",
        "Return exactly one JSON object with this shape:",
        "{",
        '  "route": "candidate|null",',
        '  "selected_candidate_id": "candidate id or null",',
        '  "selected_candidate_key": "candidate key or null",',
        '  "canonical_wing": "lowercase_slug or null",',
        '  "canonical_room": "lowercase_slug or null",',
        '  "route_confidence": 0.0,',
        '  "rationale_summary": "one short sentence",',
        '  "reason_code": "required for null, else null",',
        '  "reason_detail": "required for null, else null",',
        '  "next_action": "optional for null; one of reroute, manual_review, drop, retry_later"',
        "}",
        "",
        "Rules:",
        '- For `route: "candidate"`, `reason_code`, `reason_detail`, and `next_action` must be null.',
        '- For `route: "null"`, all selected candidate and canonical fields must be null.',
        "- Keep `rationale_summary` concise.",
    ]
    return "\n".join(lines)


def parse_route_pass2_response(
    drawer: Mapping[str, Any],
    route_candidate_record: Mapping[str, Any],
    response_text: str | Any,
    *,
    recorded_at: str | None = None,
    raw_excerpt_max_chars: int = RAW_RESPONSE_EXCERPT_MAX_CHARS,
    drawer_excerpt_max_chars: int = DRAWER_EXCERPT_MAX_CHARS,
    low_confidence_threshold: float = LOW_CONFIDENCE_THRESHOLD,
) -> dict[str, Any]:
    normalized_drawer = _normalize_drawer(
        drawer,
        drawer_excerpt_max_chars=drawer_excerpt_max_chars,
    )
    context = _normalize_route_candidate_context(
        route_candidate_record,
        require_phase_metadata=True,
    )
    if context.run_id is None or context.sequence is None or context.attempt is None:
        raise ValueError("route_candidate_record must include run_id, sequence, and attempt")

    try:
        text = _response_text(response_text)
    except TypeError:
        return build_route_pass2_record(
            drawer=normalized_drawer,
            context=context,
            record_status="invalid_model_output",
            payload=_invalid_payload(
                context=context,
                drawer=normalized_drawer,
                error_code="invalid_response_text",
                raw_response=_raw_response_debug_text(response_text),
                raw_excerpt_max_chars=raw_excerpt_max_chars,
            ),
            recorded_at=recorded_at,
        )

    data = None
    for candidate in _extract_json_candidates(text):
        try:
            data = json.loads(candidate)
            break
        except json.JSONDecodeError:
            continue
    if data is None:
        return build_route_pass2_record(
            drawer=normalized_drawer,
            context=context,
            record_status="invalid_model_output",
            payload=_invalid_payload(
                context=context,
                drawer=normalized_drawer,
                error_code="invalid_json",
                raw_response=text,
                raw_excerpt_max_chars=raw_excerpt_max_chars,
            ),
            recorded_at=recorded_at,
        )
    if not isinstance(data, Mapping):
        return build_route_pass2_record(
            drawer=normalized_drawer,
            context=context,
            record_status="invalid_model_output",
            payload=_invalid_payload(
                context=context,
                drawer=normalized_drawer,
                error_code="invalid_response_shape",
                raw_response=text,
                raw_excerpt_max_chars=raw_excerpt_max_chars,
            ),
            recorded_at=recorded_at,
        )

    decision = _resolve_route_decision(data)
    if decision is None:
        return build_route_pass2_record(
            drawer=normalized_drawer,
            context=context,
            record_status="invalid_model_output",
            payload=_invalid_payload(
                context=context,
                drawer=normalized_drawer,
                error_code="missing_route_decision",
                raw_response=text,
                raw_excerpt_max_chars=raw_excerpt_max_chars,
            ),
            recorded_at=recorded_at,
        )
    if decision not in {"candidate", "null"}:
        return build_route_pass2_record(
            drawer=normalized_drawer,
            context=context,
            record_status="invalid_model_output",
            payload=_invalid_payload(
                context=context,
                drawer=normalized_drawer,
                error_code="invalid_route_decision",
                raw_response=text,
                raw_excerpt_max_chars=raw_excerpt_max_chars,
            ),
            recorded_at=recorded_at,
        )

    confidence = _coerce_confidence(data.get("route_confidence", data.get("confidence")))
    if (
        "route_confidence" in data or "confidence" in data
    ) and confidence is None:
        return build_route_pass2_record(
            drawer=normalized_drawer,
            context=context,
            record_status="invalid_model_output",
            payload=_invalid_payload(
                context=context,
                drawer=normalized_drawer,
                error_code="invalid_confidence",
                raw_response=text,
                raw_excerpt_max_chars=raw_excerpt_max_chars,
            ),
            recorded_at=recorded_at,
        )

    rationale_summary = _first_string(data, "rationale_summary", "rationale")
    if decision == "candidate":
        payload = _parse_candidate_payload(
            data,
            context=context,
            drawer=normalized_drawer,
            confidence=confidence,
            rationale_summary=rationale_summary,
            raw_response=text,
            raw_excerpt_max_chars=raw_excerpt_max_chars,
            low_confidence_threshold=low_confidence_threshold,
        )
        record_status = "ok" if payload.get("error_code") is None else "invalid_model_output"
        return build_route_pass2_record(
            drawer=normalized_drawer,
            context=context,
            record_status=record_status,
            payload=payload,
            recorded_at=recorded_at,
        )

    payload = _parse_null_payload(
        data,
        context=context,
        drawer=normalized_drawer,
        confidence=confidence,
        rationale_summary=rationale_summary,
        raw_response=text,
        raw_excerpt_max_chars=raw_excerpt_max_chars,
    )
    record_status = "ok" if payload.get("error_code") is None else "invalid_model_output"
    return build_route_pass2_record(
        drawer=normalized_drawer,
        context=context,
        record_status=record_status,
        payload=payload,
        recorded_at=recorded_at,
    )


def build_route_pass2_record(
    *,
    drawer: _NormalizedDrawer | Mapping[str, Any],
    context: _RouteCandidateContext | Mapping[str, Any],
    record_status: str,
    payload: Mapping[str, Any],
    recorded_at: str | None = None,
) -> dict[str, Any]:
    normalized_drawer = (
        drawer
        if isinstance(drawer, _NormalizedDrawer)
        else _normalize_drawer(drawer, drawer_excerpt_max_chars=DRAWER_EXCERPT_MAX_CHARS)
    )
    route_context = (
        context
        if isinstance(context, _RouteCandidateContext)
        else _normalize_route_candidate_context(context, require_phase_metadata=True)
    )
    if route_context.run_id is None or route_context.sequence is None or route_context.attempt is None:
        raise ValueError("route_candidate_record must include run_id, sequence, and attempt")
    if not isinstance(record_status, str) or not record_status:
        raise ValueError("record_status must be a non-empty string")

    return {
        "schema_name": "ontology.phase_record",
        "schema_version": 1,
        "run_id": validate_run_id(route_context.run_id),
        "phase": PHASE_NAME,
        "sequence": route_context.sequence,
        "attempt": route_context.attempt,
        "recorded_at": recorded_at or _utc_now(),
        "subject_type": "drawer",
        "subject_id": normalized_drawer.drawer_id,
        "record_status": record_status,
        "source": {
            "wing": normalized_drawer.wing,
            "room": normalized_drawer.room,
            "drawer_id": normalized_drawer.drawer_id,
        },
        "payload": dict(payload),
    }


def _parse_candidate_payload(
    data: Mapping[str, Any],
    *,
    context: _RouteCandidateContext,
    drawer: _NormalizedDrawer,
    confidence: float | None,
    rationale_summary: str | None,
    raw_response: str,
    raw_excerpt_max_chars: int,
    low_confidence_threshold: float,
) -> dict[str, Any]:
    selected_candidate_id = _first_string(data, "selected_candidate_id", "candidate_id")
    selected_candidate_key = _first_string(data, "selected_candidate_key", "candidate_key")
    if selected_candidate_id is None and selected_candidate_key is None:
        return _invalid_payload(
            context=context,
            drawer=drawer,
            error_code="missing_selected_candidate",
            raw_response=raw_response,
            raw_excerpt_max_chars=raw_excerpt_max_chars,
        )

    selected = _match_shortlist_candidate(
        context.shortlist,
        candidate_id=selected_candidate_id,
        candidate_key=selected_candidate_key,
    )
    if selected is None:
        return _invalid_payload(
            context=context,
            drawer=drawer,
            error_code="candidate_not_in_shortlist",
            raw_response=raw_response,
            raw_excerpt_max_chars=raw_excerpt_max_chars,
        )

    canonical_wing = _first_string(data, "canonical_wing", "wing")
    if canonical_wing is None:
        return _invalid_payload(
            context=context,
            drawer=drawer,
            error_code="missing_canonical_wing",
            raw_response=raw_response,
            raw_excerpt_max_chars=raw_excerpt_max_chars,
        )
    canonical_room = _first_string(data, "canonical_room", "room")
    if canonical_room is None:
        return _invalid_payload(
            context=context,
            drawer=drawer,
            error_code="missing_canonical_room",
            raw_response=raw_response,
            raw_excerpt_max_chars=raw_excerpt_max_chars,
        )
    if not _is_slug(canonical_wing):
        return _invalid_payload(
            context=context,
            drawer=drawer,
            error_code="invalid_canonical_wing",
            raw_response=raw_response,
            raw_excerpt_max_chars=raw_excerpt_max_chars,
        )
    if not _is_slug(canonical_room):
        return _invalid_payload(
            context=context,
            drawer=drawer,
            error_code="invalid_canonical_room",
            raw_response=raw_response,
            raw_excerpt_max_chars=raw_excerpt_max_chars,
        )
    if canonical_wing != selected.canonical_wing or canonical_room != selected.canonical_room:
        return _invalid_payload(
            context=context,
            drawer=drawer,
            error_code="canonical_wing_room_mismatch",
            raw_response=raw_response,
            raw_excerpt_max_chars=raw_excerpt_max_chars,
        )

    payload = _base_payload(context=context, drawer=drawer)
    payload.update(
        {
            "route_status": "selected",
            "selected_candidate_id": selected.candidate_id,
            "selected_candidate_key": selected.candidate_key,
            "selected_candidate_rank": selected.rank,
            "candidate_id": selected.candidate_id,
            "candidate_key": selected.candidate_key,
            "canonical_wing": selected.canonical_wing,
            "canonical_room": selected.canonical_room,
            "canonical_candidate_record_ref": selected.canonical_candidate_record_ref,
            "source_candidate_refs": [dict(item) for item in selected.source_candidate_refs],
        }
    )
    if confidence is not None:
        payload["route_confidence"] = confidence
    if rationale_summary:
        payload["rationale_summary"] = rationale_summary[:240]

    if confidence is not None and confidence < low_confidence_threshold:
        payload["route_status"] = "low_confidence"
        payload["reason_code"] = "low_route_confidence"
        payload["reason_detail"] = (
            f"Selected candidate confidence {confidence:.4f} is below {low_confidence_threshold:.2f}."
        )
        payload["next_action"] = "reroute"
    return payload


def _parse_null_payload(
    data: Mapping[str, Any],
    *,
    context: _RouteCandidateContext,
    drawer: _NormalizedDrawer,
    confidence: float | None,
    rationale_summary: str | None,
    raw_response: str,
    raw_excerpt_max_chars: int,
) -> dict[str, Any]:
    selected_candidate_id = _first_string(data, "selected_candidate_id", "candidate_id")
    selected_candidate_key = _first_string(data, "selected_candidate_key", "candidate_key")
    canonical_wing = _first_string(data, "canonical_wing", "wing")
    canonical_room = _first_string(data, "canonical_room", "room")
    if any(
        value is not None
        for value in (
            selected_candidate_id,
            selected_candidate_key,
            canonical_wing,
            canonical_room,
        )
    ):
        return _invalid_payload(
            context=context,
            drawer=drawer,
            error_code="invalid_null_route_payload",
            raw_response=raw_response,
            raw_excerpt_max_chars=raw_excerpt_max_chars,
        )

    reason_code = _first_string(data, "reason_code")
    if reason_code is None:
        return _invalid_payload(
            context=context,
            drawer=drawer,
            error_code="missing_reason_code",
            raw_response=raw_response,
            raw_excerpt_max_chars=raw_excerpt_max_chars,
        )
    reason_detail = _first_string(data, "reason_detail")
    if reason_detail is None:
        return _invalid_payload(
            context=context,
            drawer=drawer,
            error_code="missing_reason_detail",
            raw_response=raw_response,
            raw_excerpt_max_chars=raw_excerpt_max_chars,
        )

    next_action = _first_string(data, "next_action", "next_action_hint")
    if next_action is not None and next_action not in _VALID_NEXT_ACTIONS:
        return _invalid_payload(
            context=context,
            drawer=drawer,
            error_code="invalid_next_action",
            raw_response=raw_response,
            raw_excerpt_max_chars=raw_excerpt_max_chars,
        )

    payload = _base_payload(context=context, drawer=drawer)
    payload.update(
        {
            "route_status": "null_route",
            "selected_candidate_id": None,
            "selected_candidate_key": None,
            "reason_code": reason_code,
            "reason_detail": reason_detail[:240],
        }
    )
    if confidence is not None:
        payload["route_confidence"] = confidence
    if rationale_summary:
        payload["rationale_summary"] = rationale_summary[:240]
    if next_action is not None:
        payload["next_action"] = next_action
    return payload


def _base_payload(
    *,
    context: _RouteCandidateContext,
    drawer: _NormalizedDrawer,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "drawer_excerpt": drawer.drawer_excerpt,
        "shortlist_size": len(context.shortlist),
        "shortlist_candidate_ids": [candidate.candidate_id for candidate in context.shortlist],
        "shortlist_candidate_keys": [candidate.candidate_key for candidate in context.shortlist],
    }
    if context.route_candidate_record_ref is not None:
        payload["route_candidate_record_ref"] = context.route_candidate_record_ref
    return payload


def _invalid_payload(
    *,
    context: _RouteCandidateContext,
    drawer: _NormalizedDrawer,
    error_code: str,
    raw_response: str,
    raw_excerpt_max_chars: int,
) -> dict[str, Any]:
    payload = _base_payload(context=context, drawer=drawer)
    payload.update(
        {
            "error_code": error_code,
            "raw_response_excerpt": _bounded_excerpt(raw_response, raw_excerpt_max_chars),
            "retryable": True,
        }
    )
    return payload


def _normalize_drawer(
    drawer: Mapping[str, Any],
    *,
    drawer_excerpt_max_chars: int,
) -> _NormalizedDrawer:
    if not isinstance(drawer, Mapping):
        raise ValueError("drawer must be a mapping")

    drawer_id = drawer.get("drawer_id")
    wing = drawer.get("wing")
    room = drawer.get("room")
    content = drawer.get("content")
    if content is None:
        content = drawer.get("document", drawer.get("text", drawer.get("drawer_excerpt", "")))

    if not isinstance(drawer_id, str) or not drawer_id.strip():
        raise ValueError("drawer.drawer_id must be a non-empty string")
    if not isinstance(wing, str) or not wing.strip():
        raise ValueError("drawer.wing must be a non-empty string")
    if not isinstance(room, str) or not room.strip():
        raise ValueError("drawer.room must be a non-empty string")
    if content is None:
        content = ""
    if not isinstance(content, str):
        raise ValueError("drawer.content must be a string when present")

    return _NormalizedDrawer(
        drawer_id=drawer_id.strip(),
        wing=wing.strip(),
        room=room.strip(),
        drawer_excerpt=_bounded_excerpt(content, drawer_excerpt_max_chars),
    )


def _normalize_route_candidate_context(
    route_candidate_record: Mapping[str, Any],
    *,
    require_phase_metadata: bool,
) -> _RouteCandidateContext:
    if not isinstance(route_candidate_record, Mapping):
        raise ValueError("route_candidate_record must be a mapping")

    payload = route_candidate_record.get("payload")
    payload_mapping = payload if isinstance(payload, Mapping) else route_candidate_record
    phase = route_candidate_record.get("phase")
    if phase is not None and phase != _ROUTE_CANDIDATES_PHASE_NAME:
        raise ValueError("route_candidate_record.phase must be route_candidates")

    run_id = route_candidate_record.get("run_id")
    sequence = route_candidate_record.get("sequence")
    attempt = route_candidate_record.get("attempt")
    if require_phase_metadata:
        if not isinstance(run_id, str) or not run_id.strip():
            raise ValueError("route_candidate_record.run_id must be a non-empty string")
        if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
            raise ValueError("route_candidate_record.sequence must be a positive integer")
        if not isinstance(attempt, int) or isinstance(attempt, bool) or attempt < 1:
            raise ValueError("route_candidate_record.attempt must be a positive integer")
        run_id = run_id.strip()
    else:
        run_id = run_id.strip() if isinstance(run_id, str) and run_id.strip() else None
        sequence = sequence if isinstance(sequence, int) and not isinstance(sequence, bool) and sequence > 0 else None
        attempt = attempt if isinstance(attempt, int) and not isinstance(attempt, bool) and attempt > 0 else None

    route_candidates = payload_mapping.get("route_candidates")
    if not isinstance(route_candidates, list):
        raise ValueError("route_candidate_record.payload.route_candidates must be a list")

    shortlist = [
        _normalize_shortlist_candidate(item, index=index)
        for index, item in enumerate(route_candidates, start=1)
    ]
    route_candidate_record_ref = payload_mapping.get("route_candidate_record_ref")
    if not isinstance(route_candidate_record_ref, str) or not route_candidate_record_ref.strip():
        if sequence is not None:
            route_candidate_record_ref = f"{_ROUTE_CANDIDATES_PHASE_NAME}.jsonl#{sequence}"
        else:
            route_candidate_record_ref = None
    else:
        route_candidate_record_ref = route_candidate_record_ref.strip()

    return _RouteCandidateContext(
        run_id=run_id,
        sequence=sequence,
        attempt=attempt,
        route_candidate_record_ref=route_candidate_record_ref,
        shortlist=shortlist,
    )


def _normalize_shortlist_candidate(item: Mapping[str, Any], *, index: int) -> _ShortlistCandidate:
    if not isinstance(item, Mapping):
        raise ValueError("route_candidate_record.payload.route_candidates items must be mappings")

    candidate_id = item.get("candidate_id")
    candidate_key = item.get("candidate_key")
    canonical_wing = item.get("canonical_wing")
    canonical_room = item.get("canonical_room")
    label = item.get("label")
    definition = item.get("definition")
    rank = item.get("rank", index)
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        raise ValueError("route_candidates[].candidate_id must be a non-empty string")
    if not isinstance(candidate_key, str) or not candidate_key.strip():
        raise ValueError("route_candidates[].candidate_key must be a non-empty string")
    if not isinstance(rank, int) or isinstance(rank, bool) or rank < 1:
        raise ValueError("route_candidates[].rank must be a positive integer")
    if not _is_slug(canonical_wing):
        raise ValueError("route_candidates[].canonical_wing must be a lowercase slug")
    if not _is_slug(canonical_room):
        raise ValueError("route_candidates[].canonical_room must be a lowercase slug")
    if candidate_key.strip() != f"{canonical_wing}:{canonical_room}":
        raise ValueError("route_candidates[].candidate_key must match canonical_wing:canonical_room")

    canonical_candidate_record_ref = item.get("canonical_candidate_record_ref")
    if not isinstance(canonical_candidate_record_ref, str) or not canonical_candidate_record_ref.strip():
        canonical_candidate_record_ref = None
    else:
        canonical_candidate_record_ref = canonical_candidate_record_ref.strip()

    source_candidate_refs = _normalize_source_candidate_refs(item.get("source_candidate_refs"))
    examples = _normalize_examples(item.get("examples"))
    return _ShortlistCandidate(
        rank=rank,
        candidate_id=candidate_id.strip(),
        candidate_key=candidate_key.strip(),
        canonical_wing=canonical_wing,
        canonical_room=canonical_room,
        label=label.strip() if isinstance(label, str) else "",
        definition=definition.strip() if isinstance(definition, str) else "",
        canonical_candidate_record_ref=canonical_candidate_record_ref,
        source_candidate_refs=source_candidate_refs,
        examples=examples,
    )


def _normalize_source_candidate_refs(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        ref: dict[str, Any] = {}
        for key in (
            "source_candidate_id",
            "source_candidate_key",
            "canonical_candidate_record_ref",
            "source_candidate_record_ref",
            "action",
        ):
            item_value = item.get(key)
            if isinstance(item_value, str) and item_value.strip():
                ref[key] = item_value.strip()
        if ref:
            normalized.append(ref)
    return normalized


def _normalize_examples(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        example: dict[str, Any] = {}
        excerpt = item.get("excerpt")
        proposal_label = item.get("proposal_label")
        if isinstance(excerpt, str) and excerpt.strip():
            example["excerpt"] = _bounded_excerpt(excerpt, 180)
        if isinstance(proposal_label, str) and proposal_label.strip():
            example["proposal_label"] = proposal_label.strip()[:80]
        if example:
            normalized.append(example)
    return normalized


def _match_shortlist_candidate(
    shortlist: list[_ShortlistCandidate],
    *,
    candidate_id: str | None,
    candidate_key: str | None,
) -> _ShortlistCandidate | None:
    matched: list[_ShortlistCandidate] = []
    for candidate in shortlist:
        if candidate_id is not None and candidate.candidate_id == candidate_id:
            matched.append(candidate)
            continue
        if candidate_key is not None and candidate.candidate_key == candidate_key:
            matched.append(candidate)

    if not matched:
        return None
    if candidate_id is not None and candidate_key is not None:
        for candidate in matched:
            if candidate.candidate_id == candidate_id and candidate.candidate_key == candidate_key:
                return candidate
        return None
    return matched[0]


def _resolve_route_decision(data: Mapping[str, Any]) -> str | None:
    decision = _first_string(data, "route", "decision", "selection")
    if decision is not None:
        return decision

    selected_candidate_id = _first_string(data, "selected_candidate_id", "candidate_id")
    selected_candidate_key = _first_string(data, "selected_candidate_key", "candidate_key")
    if selected_candidate_id is not None or selected_candidate_key is not None:
        return "candidate"
    if _first_string(data, "reason_code") is not None:
        return "null"
    return None


def _extract_json_candidates(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []

    candidates: list[str] = [text]
    for match in re.finditer(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE):
        candidate = match.group(1).strip()
        if candidate and candidate not in candidates:
            candidates.append(candidate)

    for start, opener in ((i, ch) for i, ch in enumerate(text) if ch in "{["):
        closer = "}" if opener == "{" else "]"
        depth = 0
        in_string = False
        escaped = False
        for end in range(start, len(text)):
            ch = text[end]
            if in_string:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    in_string = False
                continue

            if ch == '"':
                in_string = True
            elif ch == opener:
                depth += 1
            elif ch == closer:
                depth -= 1
                if depth == 0:
                    candidate = text[start : end + 1].strip()
                    if candidate and candidate not in candidates:
                        candidates.append(candidate)
                    break
    return candidates


def _first_string(data: Mapping[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = data.get(key)
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                return stripped
    return None


def _coerce_confidence(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        confidence = float(value)
    elif isinstance(value, str):
        try:
            confidence = float(value.strip())
        except ValueError:
            return None
    else:
        return None
    if confidence < 0 or confidence > 1:
        return None
    return round(confidence, 4)


def _is_slug(value: Any) -> bool:
    return isinstance(value, str) and bool(_SLUG_RE.fullmatch(value))


def _response_text(raw_response: str | Any) -> str:
    if isinstance(raw_response, str):
        return raw_response
    text = getattr(raw_response, "text", None)
    if isinstance(text, str):
        return text
    raise TypeError("response_text must be a string or expose a string .text attribute")


def _raw_response_debug_text(raw_response: Any) -> str:
    if isinstance(raw_response, str):
        return raw_response
    try:
        return json.dumps(raw_response, separators=(",", ":"), default=str)
    except (TypeError, ValueError):
        return repr(raw_response)


def _bounded_excerpt(text: str, limit: int) -> str:
    compact = " ".join(text.split())
    if limit < 4 or len(compact) <= limit:
        return compact[:limit]
    return f"{compact[: limit - 3]}..."


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
