from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Protocol

from .config import sanitize_content, sanitize_name
from .ontology_run import validate_run_id


PHASE_NAME = "pass1_open"
RAW_RESPONSE_EXCERPT_MAX_CHARS = 280
DRAWER_CONTENT_CHAR_LIMIT = 12000
_SLUG_RE = re.compile(r"^[a-z0-9_]+$")

_SYSTEM_PROMPT = """You classify one source drawer into a first-pass ontology proposal.

This is an open-ended hypothesis pass, not a final canonical route. Propose a
semantic wing and room that may later be clustered with similar drawers.

Return JSON only. No prose. No code fences.
"""


@dataclass(frozen=True)
class Pass1Prompt:
    system: str
    user: str


@dataclass(frozen=True)
class Pass1ParseResult:
    record_status: str
    payload: dict[str, Any]


class Pass1Provider(Protocol):
    def classify(self, system: str, user: str, json_mode: bool = True) -> Any:
        ...


def build_pass1_prompt(source_drawer: Mapping[str, Any]) -> Pass1Prompt:
    drawer = _normalize_source_drawer(source_drawer)
    content = drawer["content"][:DRAWER_CONTENT_CHAR_LIMIT]
    user = (
        "SOURCE DRAWER\n"
        f"- drawer_id: {drawer['drawer_id']}\n"
        f"- source_wing: {drawer['wing']}\n"
        f"- source_room: {drawer['room']}\n\n"
        "DRAWER CONTENT\n"
        f"{content}\n\n"
        "Return exactly one JSON object with these fields:\n"
        "{\n"
        '  "wing": "lowercase_slug",\n'
        '  "room": "lowercase_slug",\n'
        '  "label": "short human label",\n'
        '  "confidence": 0.0,\n'
        '  "rationale": "one short sentence"\n'
        "}\n\n"
        "Rules:\n"
        "- `wing` and `room` must match ^[a-z0-9_]+$.\n"
        "- Propose open-ended semantic buckets for clustering later.\n"
        "- Do not assume an existing canonical taxonomy.\n"
        "- `label` should be 2-6 words in plain language.\n"
        "- `confidence` must be between 0 and 1.\n"
        "- `rationale` must stay concise.\n"
    )
    return Pass1Prompt(system=_SYSTEM_PROMPT, user=user)


def parse_pass1_response(
    raw_response: str | Any,
    *,
    raw_excerpt_max_chars: int = RAW_RESPONSE_EXCERPT_MAX_CHARS,
) -> Pass1ParseResult:
    try:
        text = _response_text(raw_response)
    except TypeError:
        return _invalid_model_output(
            "invalid_response_text",
            _raw_response_debug_text(raw_response),
            raw_excerpt_max_chars=raw_excerpt_max_chars,
        )
    data = None
    for candidate in _extract_json_candidates(text):
        try:
            data = json.loads(candidate)
            break
        except json.JSONDecodeError:
            continue
    if data is None:
        return _invalid_model_output(
            "invalid_json",
            text,
            raw_excerpt_max_chars=raw_excerpt_max_chars,
        )
    if not isinstance(data, dict):
        return _invalid_model_output(
            "invalid_response_shape",
            text,
            raw_excerpt_max_chars=raw_excerpt_max_chars,
        )

    wing = _first_string(data, "wing", "proposed_wing")
    if wing is None:
        return _invalid_model_output(
            "missing_wing_key",
            text,
            raw_excerpt_max_chars=raw_excerpt_max_chars,
        )
    room = _first_string(data, "room", "proposed_room")
    if room is None:
        return _invalid_model_output(
            "missing_room_key",
            text,
            raw_excerpt_max_chars=raw_excerpt_max_chars,
        )
    if not _is_slug_key(wing, "wing"):
        return _invalid_model_output(
            "invalid_wing_key",
            text,
            raw_excerpt_max_chars=raw_excerpt_max_chars,
        )
    if not _is_slug_key(room, "room"):
        return _invalid_model_output(
            "invalid_room_key",
            text,
            raw_excerpt_max_chars=raw_excerpt_max_chars,
        )

    proposal_label = _first_string(data, "label", "proposal_label")
    rationale_summary = _first_string(data, "rationale", "rationale_summary")
    confidence = _coerce_confidence(data.get("confidence"))
    if "confidence" in data and confidence is None:
        return _invalid_model_output(
            "invalid_confidence",
            text,
            raw_excerpt_max_chars=raw_excerpt_max_chars,
        )

    payload: dict[str, Any] = {
        "proposed_wing": wing,
        "proposed_room": room,
        "proposal_label": (proposal_label or room.replace("_", " "))[:80],
    }
    if confidence is not None:
        payload["confidence"] = confidence
    if rationale_summary:
        payload["rationale_summary"] = rationale_summary[:240]

    return Pass1ParseResult(record_status="ok", payload=payload)


def build_pass1_phase_record(
    *,
    run_id: str,
    sequence: int,
    attempt: int,
    source_drawer: Mapping[str, Any],
    provider_response: str | Any,
    recorded_at: str | None = None,
    raw_excerpt_max_chars: int = RAW_RESPONSE_EXCERPT_MAX_CHARS,
) -> dict[str, Any]:
    drawer = _normalize_source_drawer(source_drawer)
    validated_run_id = validate_run_id(run_id)
    if not isinstance(sequence, int) or sequence < 1:
        raise ValueError("sequence must be a positive integer")
    if not isinstance(attempt, int) or attempt < 1:
        raise ValueError("attempt must be a positive integer")

    parsed = parse_pass1_response(
        provider_response,
        raw_excerpt_max_chars=raw_excerpt_max_chars,
    )
    return {
        "schema_name": "ontology.phase_record",
        "schema_version": 1,
        "run_id": validated_run_id,
        "phase": PHASE_NAME,
        "sequence": sequence,
        "attempt": attempt,
        "recorded_at": recorded_at or _utc_now(),
        "subject_type": "drawer",
        "subject_id": drawer["drawer_id"],
        "record_status": parsed.record_status,
        "source": {
            "wing": drawer["wing"],
            "room": drawer["room"],
            "drawer_id": drawer["drawer_id"],
        },
        "payload": parsed.payload,
    }


def classify_drawer_pass1(
    *,
    provider: Pass1Provider,
    run_id: str,
    sequence: int,
    attempt: int,
    source_drawer: Mapping[str, Any],
    recorded_at: str | None = None,
    raw_excerpt_max_chars: int = RAW_RESPONSE_EXCERPT_MAX_CHARS,
) -> dict[str, Any]:
    prompt = build_pass1_prompt(source_drawer)
    try:
        response = provider.classify(prompt.system, prompt.user, json_mode=True)
    except Exception as exc:
        drawer = _normalize_source_drawer(source_drawer)
        validated_run_id = validate_run_id(run_id)
        return {
            "schema_name": "ontology.phase_record",
            "schema_version": 1,
            "run_id": validated_run_id,
            "phase": PHASE_NAME,
            "sequence": sequence,
            "attempt": attempt,
            "recorded_at": recorded_at or _utc_now(),
            "subject_type": "drawer",
            "subject_id": drawer["drawer_id"],
            "record_status": "error",
            "source": {
                "wing": drawer["wing"],
                "room": drawer["room"],
                "drawer_id": drawer["drawer_id"],
            },
            "payload": {
                "error_code": "provider_error",
                "detail_excerpt": _bounded_excerpt(str(exc), raw_excerpt_max_chars),
                "retryable": True,
            },
        }

    return build_pass1_phase_record(
        run_id=run_id,
        sequence=sequence,
        attempt=attempt,
        source_drawer=source_drawer,
        provider_response=response,
        recorded_at=recorded_at,
        raw_excerpt_max_chars=raw_excerpt_max_chars,
    )


def _normalize_source_drawer(source_drawer: Mapping[str, Any]) -> dict[str, str]:
    if not isinstance(source_drawer, Mapping):
        raise ValueError("source_drawer must be a mapping")
    drawer_id = source_drawer.get("drawer_id")
    wing = source_drawer.get("wing")
    room = source_drawer.get("room")
    content = source_drawer.get("content")

    if not isinstance(drawer_id, str) or not drawer_id.strip():
        raise ValueError("source_drawer.drawer_id must be a non-empty string")
    if "\x00" in drawer_id:
        raise ValueError("source_drawer.drawer_id contains null bytes")

    return {
        "drawer_id": drawer_id.strip(),
        "wing": sanitize_name(wing, "source_drawer.wing"),
        "room": sanitize_name(room, "source_drawer.room"),
        "content": sanitize_content(content, max_length=1_000_000),
    }


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
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _coerce_confidence(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
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


def _is_slug_key(value: str, field_name: str) -> bool:
    try:
        sanitized = sanitize_name(value, field_name)
    except ValueError:
        return False
    return bool(_SLUG_RE.fullmatch(sanitized))


def _invalid_model_output(
    error_code: str,
    raw_response: str,
    *,
    raw_excerpt_max_chars: int,
) -> Pass1ParseResult:
    return Pass1ParseResult(
        record_status="invalid_model_output",
        payload={
            "error_code": error_code,
            "raw_response_excerpt": _bounded_excerpt(raw_response, raw_excerpt_max_chars),
            "retryable": True,
        },
    )


def _response_text(raw_response: str | Any) -> str:
    if isinstance(raw_response, str):
        return raw_response
    text = getattr(raw_response, "text", None)
    if isinstance(text, str):
        return text
    raise TypeError("provider_response must be a string or expose a string .text attribute")


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
