from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from .ontology_run import validate_run_id


PHASE_NAME = "route_verify"
RAW_RESPONSE_EXCERPT_MAX_CHARS = 280
DRAWER_EXCERPT_MAX_CHARS = 240
PROMPT_DRAWER_EXCERPT_MAX_CHARS = 1200
_ROUTE_CANDIDATES_PHASE_NAME = "route_candidates"
_ROUTE_PASS2_PHASE_NAME = "route_pass2"
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


@dataclass(frozen=True)
class _RouteDecision:
    run_id: str
    sequence: int
    attempt: int
    route_record_ref: str
    route_candidate_record_ref: str | None
    route_status: str
    decision_kind: str
    route_confidence: float | None
    rationale_summary: str | None
    reason_code: str | None
    reason_detail: str | None
    next_action: str | None
    selected_candidate: _ShortlistCandidate | None


class _RouteDecisionError(ValueError):
    def __init__(self, error_code: str):
        super().__init__(error_code)
        self.error_code = error_code


def build_route_verify_prompt(
    drawer: Mapping[str, Any],
    route_candidate_record: Mapping[str, Any],
    route_pass2_record: Mapping[str, Any],
) -> str:
    normalized_drawer = _normalize_drawer(
        drawer,
        drawer_excerpt_max_chars=PROMPT_DRAWER_EXCERPT_MAX_CHARS,
    )
    context = _normalize_route_candidate_context(
        route_candidate_record,
        require_phase_metadata=False,
    )
    decision = _normalize_route_pass2_record(
        route_pass2_record,
        context=context,
        drawer=normalized_drawer,
    )

    route_block = {
        "route_record_ref": decision.route_record_ref,
        "route_candidate_record_ref": decision.route_candidate_record_ref,
        "route_status": decision.route_status,
        "route_confidence": decision.route_confidence,
        "selected_candidate_id": (
            decision.selected_candidate.candidate_id if decision.selected_candidate is not None else None
        ),
        "selected_candidate_key": (
            decision.selected_candidate.candidate_key if decision.selected_candidate is not None else None
        ),
        "canonical_wing": (
            decision.selected_candidate.canonical_wing if decision.selected_candidate is not None else None
        ),
        "canonical_room": (
            decision.selected_candidate.canonical_room if decision.selected_candidate is not None else None
        ),
        "reason_code": decision.reason_code,
        "reason_detail": decision.reason_detail,
        "next_action": decision.next_action,
        "rationale_summary": decision.rationale_summary,
    }

    selected_candidate_block: dict[str, Any] | None = None
    if decision.selected_candidate is not None:
        selected_candidate_block = {
            "rank": decision.selected_candidate.rank,
            "candidate_id": decision.selected_candidate.candidate_id,
            "candidate_key": decision.selected_candidate.candidate_key,
            "canonical_wing": decision.selected_candidate.canonical_wing,
            "canonical_room": decision.selected_candidate.canonical_room,
            "label": decision.selected_candidate.label,
            "definition": decision.selected_candidate.definition,
            "canonical_candidate_record_ref": decision.selected_candidate.canonical_candidate_record_ref,
            "source_candidate_record_refs": [
                ref["source_candidate_record_ref"]
                for ref in decision.selected_candidate.source_candidate_refs
                if isinstance(ref.get("source_candidate_record_ref"), str)
            ],
            "example_excerpts": [
                item["excerpt"]
                for item in decision.selected_candidate.examples
                if isinstance(item.get("excerpt"), str)
            ][:2],
        }

    shortlist = [
        {
            "rank": candidate.rank,
            "candidate_id": candidate.candidate_id,
            "candidate_key": candidate.candidate_key,
            "canonical_wing": candidate.canonical_wing,
            "canonical_room": candidate.canonical_room,
        }
        for candidate in context.shortlist
    ]

    lines = [
        "You locally verify one proposed ontology route decision for one source drawer.",
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
        "ROUTE DECISION UNDER REVIEW",
        json.dumps(route_block, indent=2, sort_keys=True),
        "",
        "SHORTLIST CANDIDATES",
        json.dumps(shortlist, indent=2, sort_keys=True),
        "",
        "SELECTED CANDIDATE",
        json.dumps(selected_candidate_block, indent=2, sort_keys=True)
        if selected_candidate_block is not None
        else "null",
        "",
        "TASK",
        "- Approve or reject the reviewed route decision only.",
        "- Use the drawer excerpt, selected candidate, route rationale, and shortlist as evidence.",
        "- Do not invent a candidate outside the shortlist.",
        "- For candidate routes, copy the selected candidate ID/key and canonical wing/room exactly from the reviewed route.",
        "- For null routes, keep selected candidate fields null.",
        "- `verification_confidence` must be a number from 0 to 1 when present.",
        "",
        "Return exactly one JSON object with this shape:",
        "{",
        '  "verdict": "approve|reject",',
        '  "selected_candidate_id": "reviewed candidate id or null",',
        '  "selected_candidate_key": "reviewed candidate key or null",',
        '  "canonical_wing": "reviewed canonical wing or null",',
        '  "canonical_room": "reviewed canonical room or null",',
        '  "verification_confidence": 0.0,',
        '  "rationale_summary": "one short sentence",',
        '  "reason_code": "required for reject; optional for approved null route; else null",',
        '  "reason_detail": "required for reject; optional for approved null route; else null",',
        '  "next_action": "optional; one of reroute, manual_review, drop, retry_later"',
        "}",
        "",
        "Rules:",
        "- Approved selected candidate routes must keep reason fields null.",
        "- Approved null routes may keep or restate the null-route reason.",
        "- Rejected routes must include reason_code and reason_detail.",
        "- Keep rationale_summary concise.",
    ]
    return "\n".join(lines)


def parse_route_verify_response(
    drawer: Mapping[str, Any],
    route_candidate_record: Mapping[str, Any],
    route_pass2_record: Mapping[str, Any],
    response_text: str | Any,
    *,
    recorded_at: str | None = None,
    raw_excerpt_max_chars: int = RAW_RESPONSE_EXCERPT_MAX_CHARS,
    drawer_excerpt_max_chars: int = DRAWER_EXCERPT_MAX_CHARS,
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
        decision = _normalize_route_pass2_record(
            route_pass2_record,
            context=context,
            drawer=normalized_drawer,
        )
    except _RouteDecisionError as exc:
        decision = _fallback_route_decision(route_pass2_record, context)
        return build_route_verify_record(
            drawer=normalized_drawer,
            decision=decision,
            record_status="invalid_model_output",
            payload=_invalid_payload(
                context=context,
                drawer=normalized_drawer,
                decision=decision,
                error_code=exc.error_code,
                raw_response=_raw_response_debug_text(response_text),
                raw_excerpt_max_chars=raw_excerpt_max_chars,
            ),
            recorded_at=recorded_at,
        )

    try:
        text = _response_text(response_text)
    except TypeError:
        return build_route_verify_record(
            drawer=normalized_drawer,
            decision=decision,
            record_status="invalid_model_output",
            payload=_invalid_payload(
                context=context,
                drawer=normalized_drawer,
                decision=decision,
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
        return build_route_verify_record(
            drawer=normalized_drawer,
            decision=decision,
            record_status="invalid_model_output",
            payload=_invalid_payload(
                context=context,
                drawer=normalized_drawer,
                decision=decision,
                error_code="invalid_json",
                raw_response=text,
                raw_excerpt_max_chars=raw_excerpt_max_chars,
            ),
            recorded_at=recorded_at,
        )
    if not isinstance(data, Mapping):
        return build_route_verify_record(
            drawer=normalized_drawer,
            decision=decision,
            record_status="invalid_model_output",
            payload=_invalid_payload(
                context=context,
                drawer=normalized_drawer,
                decision=decision,
                error_code="invalid_response_shape",
                raw_response=text,
                raw_excerpt_max_chars=raw_excerpt_max_chars,
            ),
            recorded_at=recorded_at,
        )

    verdict = _resolve_verdict(data)
    if verdict is None:
        return build_route_verify_record(
            drawer=normalized_drawer,
            decision=decision,
            record_status="invalid_model_output",
            payload=_invalid_payload(
                context=context,
                drawer=normalized_drawer,
                decision=decision,
                error_code="missing_verdict",
                raw_response=text,
                raw_excerpt_max_chars=raw_excerpt_max_chars,
            ),
            recorded_at=recorded_at,
        )
    if verdict not in {"approve", "reject"}:
        return build_route_verify_record(
            drawer=normalized_drawer,
            decision=decision,
            record_status="invalid_model_output",
            payload=_invalid_payload(
                context=context,
                drawer=normalized_drawer,
                decision=decision,
                error_code="invalid_verdict",
                raw_response=text,
                raw_excerpt_max_chars=raw_excerpt_max_chars,
            ),
            recorded_at=recorded_at,
        )

    verification_confidence = _coerce_confidence(
        data.get("verification_confidence", data.get("confidence"))
    )
    if (
        "verification_confidence" in data or "confidence" in data
    ) and verification_confidence is None:
        return build_route_verify_record(
            drawer=normalized_drawer,
            decision=decision,
            record_status="invalid_model_output",
            payload=_invalid_payload(
                context=context,
                drawer=normalized_drawer,
                decision=decision,
                error_code="invalid_confidence",
                raw_response=text,
                raw_excerpt_max_chars=raw_excerpt_max_chars,
            ),
            recorded_at=recorded_at,
        )

    payload = _parse_verification_payload(
        data,
        context=context,
        decision=decision,
        drawer=normalized_drawer,
        verdict=verdict,
        verification_confidence=verification_confidence,
        raw_response=text,
        raw_excerpt_max_chars=raw_excerpt_max_chars,
    )
    record_status = "ok" if payload.get("error_code") is None else "invalid_model_output"
    return build_route_verify_record(
        drawer=normalized_drawer,
        decision=decision,
        record_status=record_status,
        payload=payload,
        recorded_at=recorded_at,
    )


def build_route_verify_record(
    *,
    drawer: _NormalizedDrawer | Mapping[str, Any],
    decision: _RouteDecision,
    record_status: str,
    payload: Mapping[str, Any],
    recorded_at: str | None = None,
) -> dict[str, Any]:
    normalized_drawer = (
        drawer
        if isinstance(drawer, _NormalizedDrawer)
        else _normalize_drawer(drawer, drawer_excerpt_max_chars=DRAWER_EXCERPT_MAX_CHARS)
    )
    if not isinstance(record_status, str) or not record_status:
        raise ValueError("record_status must be a non-empty string")

    return {
        "schema_name": "ontology.phase_record",
        "schema_version": 1,
        "run_id": validate_run_id(decision.run_id),
        "phase": PHASE_NAME,
        "sequence": decision.sequence,
        "attempt": decision.attempt,
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


def _parse_verification_payload(
    data: Mapping[str, Any],
    *,
    context: _RouteCandidateContext,
    decision: _RouteDecision,
    drawer: _NormalizedDrawer,
    verdict: str,
    verification_confidence: float | None,
    raw_response: str,
    raw_excerpt_max_chars: int,
) -> dict[str, Any]:
    provenance_error = _validate_reviewed_route_identity(data, decision=decision)
    if provenance_error is not None:
        return _invalid_payload(
            context=context,
            drawer=drawer,
            decision=decision,
            error_code=provenance_error,
            raw_response=raw_response,
            raw_excerpt_max_chars=raw_excerpt_max_chars,
        )

    payload = _base_payload(context=context, drawer=drawer, decision=decision)
    payload["verification_verdict"] = "approved" if verdict == "approve" else "rejected"

    if verification_confidence is not None:
        payload["verification_confidence"] = verification_confidence

    rationale_summary = _first_string(data, "rationale_summary", "rationale")
    if rationale_summary is not None:
        payload["rationale_summary"] = rationale_summary[:240]

    if verdict == "approve":
        if decision.decision_kind == "candidate":
            if _first_string(data, "reason_code", "reason_detail", "next_action") is not None:
                return _invalid_payload(
                    context=context,
                    drawer=drawer,
                    decision=decision,
                    error_code="unexpected_reason_fields",
                    raw_response=raw_response,
                    raw_excerpt_max_chars=raw_excerpt_max_chars,
                )
            payload.update(
                {
                    "route_status": "accepted",
                    "copy_ready": True,
                }
            )
            return payload

        reason_code = _first_string(data, "reason_code") or decision.reason_code
        reason_detail = _first_string(data, "reason_detail") or decision.reason_detail
        if reason_code is None:
            return _invalid_payload(
                context=context,
                drawer=drawer,
                decision=decision,
                error_code="missing_reason_code",
                raw_response=raw_response,
                raw_excerpt_max_chars=raw_excerpt_max_chars,
            )
        if reason_detail is None:
            return _invalid_payload(
                context=context,
                drawer=drawer,
                decision=decision,
                error_code="missing_reason_detail",
                raw_response=raw_response,
                raw_excerpt_max_chars=raw_excerpt_max_chars,
            )
        next_action = _normalize_next_action(data, fallback=decision.next_action)
        if next_action is _MISSING:
            return _invalid_payload(
                context=context,
                drawer=drawer,
                decision=decision,
                error_code="invalid_next_action",
                raw_response=raw_response,
                raw_excerpt_max_chars=raw_excerpt_max_chars,
            )
        payload.update(
            {
                "route_status": "null_route",
                "copy_ready": False,
                "reason_code": reason_code,
                "reason_detail": reason_detail[:240],
            }
        )
        if next_action is not None:
            payload["next_action"] = next_action
        return payload

    reason_code = _first_string(data, "reason_code")
    reason_detail = _first_string(data, "reason_detail")
    if reason_code is None:
        return _invalid_payload(
            context=context,
            drawer=drawer,
            decision=decision,
            error_code="missing_reason_code",
            raw_response=raw_response,
            raw_excerpt_max_chars=raw_excerpt_max_chars,
        )
    if reason_detail is None:
        return _invalid_payload(
            context=context,
            drawer=drawer,
            decision=decision,
            error_code="missing_reason_detail",
            raw_response=raw_response,
            raw_excerpt_max_chars=raw_excerpt_max_chars,
        )
    next_action = _normalize_next_action(data, fallback=None)
    if next_action is _MISSING:
        return _invalid_payload(
            context=context,
            drawer=drawer,
            decision=decision,
            error_code="invalid_next_action",
            raw_response=raw_response,
            raw_excerpt_max_chars=raw_excerpt_max_chars,
        )

    payload.update(
        {
            "route_status": "verification_reject",
            "copy_ready": False,
            "reason_code": reason_code,
            "reason_detail": reason_detail[:240],
        }
    )
    if next_action is not None:
        payload["next_action"] = next_action
    return payload


def _base_payload(
    *,
    context: _RouteCandidateContext,
    drawer: _NormalizedDrawer,
    decision: _RouteDecision,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "drawer_excerpt": drawer.drawer_excerpt,
        "route_iteration": decision.attempt,
        "route_record_ref": decision.route_record_ref,
        "route_pass2_status": decision.route_status,
        "shortlist_size": len(context.shortlist),
        "shortlist_candidate_ids": [candidate.candidate_id for candidate in context.shortlist],
        "shortlist_candidate_keys": [candidate.candidate_key for candidate in context.shortlist],
        "selected_candidate_id": None,
        "selected_candidate_key": None,
    }
    if decision.route_candidate_record_ref is not None:
        payload["route_candidate_record_ref"] = decision.route_candidate_record_ref
    if decision.route_confidence is not None:
        payload["route_confidence"] = decision.route_confidence
    if decision.rationale_summary:
        payload["route_rationale_summary"] = decision.rationale_summary[:240]
    if decision.selected_candidate is not None:
        payload.update(
            {
                "selected_candidate_id": decision.selected_candidate.candidate_id,
                "selected_candidate_key": decision.selected_candidate.candidate_key,
                "selected_candidate_rank": decision.selected_candidate.rank,
                "candidate_id": decision.selected_candidate.candidate_id,
                "candidate_key": decision.selected_candidate.candidate_key,
                "canonical_wing": decision.selected_candidate.canonical_wing,
                "canonical_room": decision.selected_candidate.canonical_room,
                "canonical_candidate_record_ref": decision.selected_candidate.canonical_candidate_record_ref,
                "source_candidate_refs": [dict(item) for item in decision.selected_candidate.source_candidate_refs],
            }
        )
    if decision.reason_code:
        payload["route_reason_code"] = decision.reason_code
    if decision.reason_detail:
        payload["route_reason_detail"] = decision.reason_detail[:240]
    if decision.next_action:
        payload["route_next_action"] = decision.next_action
    return payload


def _invalid_payload(
    *,
    context: _RouteCandidateContext,
    drawer: _NormalizedDrawer,
    decision: _RouteDecision,
    error_code: str,
    raw_response: str,
    raw_excerpt_max_chars: int,
) -> dict[str, Any]:
    payload = _base_payload(context=context, drawer=drawer, decision=decision)
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


def _normalize_route_pass2_record(
    route_pass2_record: Mapping[str, Any],
    *,
    context: _RouteCandidateContext,
    drawer: _NormalizedDrawer,
) -> _RouteDecision:
    if not isinstance(route_pass2_record, Mapping):
        raise ValueError("route_pass2_record must be a mapping")
    phase = route_pass2_record.get("phase")
    if phase is not None and phase != _ROUTE_PASS2_PHASE_NAME:
        raise ValueError("route_pass2_record.phase must be route_pass2")
    record_status = route_pass2_record.get("record_status")
    if record_status is not None and record_status != "ok":
        raise ValueError("route_pass2_record.record_status must be ok")

    run_id = route_pass2_record.get("run_id")
    sequence = route_pass2_record.get("sequence")
    attempt = route_pass2_record.get("attempt")
    if not isinstance(run_id, str) or not run_id.strip():
        raise ValueError("route_pass2_record.run_id must be a non-empty string")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
        raise ValueError("route_pass2_record.sequence must be a positive integer")
    if not isinstance(attempt, int) or isinstance(attempt, bool) or attempt < 1:
        raise ValueError("route_pass2_record.attempt must be a positive integer")
    if context.run_id is not None and run_id.strip() != context.run_id:
        raise _RouteDecisionError("candidate_provenance_mismatch")

    source = route_pass2_record.get("source")
    if isinstance(source, Mapping):
        if source.get("drawer_id") not in (None, drawer.drawer_id):
            raise _RouteDecisionError("candidate_provenance_mismatch")
        if source.get("wing") not in (None, drawer.wing):
            raise _RouteDecisionError("candidate_provenance_mismatch")
        if source.get("room") not in (None, drawer.room):
            raise _RouteDecisionError("candidate_provenance_mismatch")

    payload = route_pass2_record.get("payload")
    if not isinstance(payload, Mapping):
        raise ValueError("route_pass2_record.payload must be a mapping")

    route_record_ref = _first_string(payload, "route_record_ref")
    if route_record_ref is None:
        route_record_ref = f"{_ROUTE_PASS2_PHASE_NAME}.jsonl#{sequence}"

    route_candidate_record_ref = _first_string(payload, "route_candidate_record_ref")
    if route_candidate_record_ref is None:
        route_candidate_record_ref = context.route_candidate_record_ref
    elif context.route_candidate_record_ref is not None and route_candidate_record_ref != context.route_candidate_record_ref:
        raise _RouteDecisionError("candidate_provenance_mismatch")

    route_confidence = _coerce_confidence(payload.get("route_confidence", payload.get("confidence")))
    rationale_summary = _first_string(payload, "rationale_summary", "route_rationale_summary", "rationale")
    reason_code = _first_string(payload, "reason_code", "route_reason_code")
    reason_detail = _first_string(payload, "reason_detail", "route_reason_detail")
    next_action = _normalize_next_action(payload, fallback=None)
    if next_action is _MISSING:
        raise ValueError("route_pass2_record.payload.next_action must be valid when present")

    route_status = _first_string(payload, "route_status")
    selected_candidate_id = _first_string(payload, "selected_candidate_id", "candidate_id")
    selected_candidate_key = _first_string(payload, "selected_candidate_key", "candidate_key")
    canonical_wing = _first_string(payload, "canonical_wing", "wing")
    canonical_room = _first_string(payload, "canonical_room", "room")

    is_null_route = route_status == "null_route" or (
        selected_candidate_id is None
        and selected_candidate_key is None
        and (canonical_wing is None and canonical_room is None)
        and reason_code is not None
    )
    if is_null_route:
        if any(
            value is not None
            for value in (
                selected_candidate_id,
                selected_candidate_key,
                canonical_wing,
                canonical_room,
            )
        ):
            raise _RouteDecisionError("candidate_provenance_mismatch")
        return _RouteDecision(
            run_id=run_id.strip(),
            sequence=sequence,
            attempt=attempt,
            route_record_ref=route_record_ref,
            route_candidate_record_ref=route_candidate_record_ref,
            route_status=route_status or "null_route",
            decision_kind="null",
            route_confidence=route_confidence,
            rationale_summary=rationale_summary,
            reason_code=reason_code,
            reason_detail=reason_detail,
            next_action=next_action,
            selected_candidate=None,
        )

    selected = _match_shortlist_candidate(
        context.shortlist,
        candidate_id=selected_candidate_id,
        candidate_key=selected_candidate_key,
    )
    if selected is None:
        raise _RouteDecisionError("candidate_provenance_mismatch")
    if canonical_wing is not None and canonical_wing != selected.canonical_wing:
        raise _RouteDecisionError("candidate_provenance_mismatch")
    if canonical_room is not None and canonical_room != selected.canonical_room:
        raise _RouteDecisionError("candidate_provenance_mismatch")

    return _RouteDecision(
        run_id=run_id.strip(),
        sequence=sequence,
        attempt=attempt,
        route_record_ref=route_record_ref,
        route_candidate_record_ref=route_candidate_record_ref,
        route_status=route_status or "selected",
        decision_kind="candidate",
        route_confidence=route_confidence,
        rationale_summary=rationale_summary,
        reason_code=reason_code,
        reason_detail=reason_detail,
        next_action=next_action,
        selected_candidate=selected,
    )


def _fallback_route_decision(
    route_pass2_record: Mapping[str, Any],
    context: _RouteCandidateContext,
) -> _RouteDecision:
    run_id_value = route_pass2_record.get("run_id") if isinstance(route_pass2_record, Mapping) else None
    run_id = run_id_value.strip() if isinstance(run_id_value, str) and run_id_value.strip() else context.run_id
    sequence_value = route_pass2_record.get("sequence") if isinstance(route_pass2_record, Mapping) else None
    attempt_value = route_pass2_record.get("attempt") if isinstance(route_pass2_record, Mapping) else None
    sequence = (
        sequence_value
        if isinstance(sequence_value, int) and not isinstance(sequence_value, bool) and sequence_value > 0
        else (context.sequence or 1)
    )
    attempt = (
        attempt_value
        if isinstance(attempt_value, int) and not isinstance(attempt_value, bool) and attempt_value > 0
        else (context.attempt or 1)
    )
    resolved_run_id = run_id or "fallback_run_id"
    try:
        validate_run_id(resolved_run_id)
    except ValueError:
        resolved_run_id = "fallback_run_id"

    return _RouteDecision(
        run_id=resolved_run_id,
        sequence=sequence,
        attempt=attempt,
        route_record_ref=f"{_ROUTE_PASS2_PHASE_NAME}.jsonl#{sequence}",
        route_candidate_record_ref=context.route_candidate_record_ref,
        route_status="unknown",
        decision_kind="null",
        route_confidence=None,
        rationale_summary=None,
        reason_code=None,
        reason_detail=None,
        next_action=None,
        selected_candidate=None,
    )


def _validate_reviewed_route_identity(
    data: Mapping[str, Any],
    *,
    decision: _RouteDecision,
) -> str | None:
    selected_candidate_id = _first_string(data, "selected_candidate_id", "candidate_id")
    selected_candidate_key = _first_string(data, "selected_candidate_key", "candidate_key")
    canonical_wing = _first_string(data, "canonical_wing", "wing")
    canonical_room = _first_string(data, "canonical_room", "room")

    if decision.decision_kind == "null":
        if any(
            value is not None
            for value in (
                selected_candidate_id,
                selected_candidate_key,
                canonical_wing,
                canonical_room,
            )
        ):
            return "candidate_provenance_mismatch"
        return None

    if decision.selected_candidate is None:
        return "candidate_provenance_mismatch"
    if selected_candidate_id != decision.selected_candidate.candidate_id:
        return "candidate_provenance_mismatch"
    if selected_candidate_key != decision.selected_candidate.candidate_key:
        return "candidate_provenance_mismatch"
    if canonical_wing != decision.selected_candidate.canonical_wing:
        return "candidate_provenance_mismatch"
    if canonical_room != decision.selected_candidate.canonical_room:
        return "candidate_provenance_mismatch"
    return None


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


def _resolve_verdict(data: Mapping[str, Any]) -> str | None:
    verdict = _first_string(data, "verdict", "verification_verdict", "decision")
    if verdict is None:
        return None
    normalized = verdict.lower()
    if normalized in {"approve", "approved"}:
        return "approve"
    if normalized in {"reject", "rejected"}:
        return "reject"
    return normalized


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


def _normalize_next_action(data: Mapping[str, Any], *, fallback: str | None) -> object:
    next_action = data.get("next_action")
    if next_action is None:
        return fallback
    if not isinstance(next_action, str):
        return _MISSING
    normalized = next_action.strip()
    if not normalized:
        return fallback
    if normalized not in _VALID_NEXT_ACTIONS:
        return _MISSING
    return normalized


def _is_slug(value: Any) -> bool:
    return isinstance(value, str) and bool(_SLUG_RE.fullmatch(value))


def _response_text(raw_response: str | Any) -> str:
    if isinstance(raw_response, str):
        return raw_response
    text = getattr(raw_response, "text", None)
    if isinstance(text, str):
        return text
    raise TypeError("response text must be a string or expose .text")


def _raw_response_debug_text(raw_response: Any) -> str:
    if isinstance(raw_response, str):
        return raw_response
    text = getattr(raw_response, "text", None)
    if isinstance(text, str):
        return text
    try:
        return json.dumps(raw_response, separators=(",", ":"), sort_keys=True, default=str)
    except TypeError:
        return repr(raw_response)


def _bounded_excerpt(text: str, max_chars: int) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_chars:
        return compact
    if max_chars <= 3:
        return compact[:max_chars]
    return compact[: max_chars - 3] + "..."


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


_MISSING = object()
