from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from . import chatgpt_atlas_guided_contract as guided_contract


PROMPT_SEGMENT_EXCERPT_MAX_CHARS = 2400
PROMPT_REPRESENTATIVE_EXCERPT_MAX_CHARS = 180
PROMPT_DEFINITION_MAX_CHARS = 240
PROMPT_TITLE_MAX_CHARS = 120
PARSED_SOURCE_EXCERPT_MAX_CHARS = 280
PROVENANCE_SEGMENT_EXCERPT_MAX_CHARS = 280
RAW_RESPONSE_EXCERPT_MAX_CHARS = 500
MAX_SIGNAL_ITEMS = 8
_CANONICAL_SLUG_RE = re.compile(r"^[a-z0-9_]{1,96}$")

_FORBIDDEN_RESPONSE_KEYS = frozenset(
    {
        "no_publish",
        "publish",
        "publish_enabled",
        "publish_gate_open",
        "publish_limit",
        "target_wing",
        "write_drawer",
        "drawer_write_path",
        "palace_write",
        "palace_write_path",
        "mcp_tool",
    }
)
_FORBIDDEN_RESPONSE_KEY_PREFIXES = (
    "localai",
    "chroma",
    "mcp",
    "network",
    "provider",
    "vector",
    "tool",
    "publish",
    "palace",
    "drawer",
    "write",
)
_FORBIDDEN_RESPONSE_KEY_PARTS = frozenset(
    {
        "localai",
        "chroma",
        "mcp",
        "network",
        "provider",
        "vector",
        "tool",
        "publish",
        "write",
        "drawer",
        "palace",
        "url",
        "path",
        "root",
    }
)


@dataclass(frozen=True)
class ChatGPTAtlasGuidedPromptParseResult:
    records: tuple[dict[str, Any], ...]
    error_code: str | None = None
    raw_response_excerpt: str | None = None

    @property
    def ok(self) -> bool:
        return self.error_code is None


@dataclass(frozen=True)
class _CandidateContext:
    candidate_id: str
    candidate_key: str
    canonical_wing: str
    canonical_room: str
    atlas_cluster_id: str
    bridge_status: str
    label: str
    definition: str
    top_terms: tuple[str, ...]
    evidence_titles: tuple[str, ...]
    representative_excerpt: str | None


class _ParseError(ValueError):
    def __init__(self, error_code: str):
        super().__init__(error_code)
        self.error_code = error_code


def build_chatgpt_atlas_guided_prompt_messages(
    segment_text: str,
    thread_candidate_lookup_row: Mapping[str, Any],
    candidate_bridge_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    segment_text = _require_segment_text(segment_text)
    lookup = _normalize_lookup_row(thread_candidate_lookup_row)
    candidate_contexts = _candidate_contexts_for_thread(lookup, candidate_bridge_rows)
    payload = {
        "thread_context": {
            "thread_id": lookup["thread_id"],
            "lookup_status": lookup["lookup_status"],
            "reason_codes": list(lookup["reason_codes"]),
            "primary_candidate_id": lookup["primary_candidate_id"],
            "primary_candidate_key": lookup["primary_candidate_key"],
            "candidate_ids": list(lookup["candidate_ids"]),
            "candidate_keys": list(lookup["candidate_keys"]),
        },
        "candidate_shortlist": [
            {
                "candidate_id": item.candidate_id,
                "candidate_key": item.candidate_key,
                "canonical_wing": item.canonical_wing,
                "canonical_room": item.canonical_room,
                "atlas_cluster_id": item.atlas_cluster_id,
                "bridge_status": item.bridge_status,
                "label": _bounded_text(item.label, PROMPT_TITLE_MAX_CHARS),
                "definition": _bounded_text(item.definition, PROMPT_DEFINITION_MAX_CHARS),
                "top_terms": list(item.top_terms),
                "evidence_titles": list(item.evidence_titles),
                "representative_excerpt": item.representative_excerpt,
            }
            for item in candidate_contexts
        ],
        "schema": {
            "signals": [
                {
                    "signal_status": "accepted|null_signal",
                    "candidate_id": "candidate id from the shortlist or null",
                    "candidate_key": "candidate key from the shortlist or null",
                    "canonical_wing": "candidate wing or null",
                    "canonical_room": "candidate room or null",
                    "signal_type": (
                        "decision|preference|project|task|fact|problem|open_question|"
                        "technical_note|null_signal"
                    ),
                    "title": "short title or null",
                    "summary": "grounded summary from this segment only",
                    "source_excerpt": "bounded excerpt copied from this segment",
                    "confidence": 0.0,
                }
            ]
        },
        "rules": [
            "Return strict JSON only. No prose. No code fences.",
            "Use only the segment text and shortlist candidates in this prompt.",
            "Never invent a candidate outside the shortlist.",
            "If a signal is accepted, copy candidate_id, candidate_key, canonical_wing, and canonical_room exactly from one shortlist item.",
            "If no shortlist candidate is supported by the segment, return one signal item with signal_status set to null_signal and all candidate fields set to null.",
            "Never include publish, target_wing, write, MCP, palace, or network instructions.",
            "confidence must be a finite number from 0 to 1.",
            f"Return at most {MAX_SIGNAL_ITEMS} signal items.",
        ],
        "segment_text": _bounded_text(segment_text, PROMPT_SEGMENT_EXCERPT_MAX_CHARS),
    }
    system = (
        "Extract atlas-guided ChatGPT memory signals from one bounded thread segment. "
        "Constrain every accepted item to the provided candidate shortlist."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(payload, sort_keys=True, ensure_ascii=False)},
    ]


def parse_chatgpt_atlas_guided_response(
    segment_text: str,
    *,
    segment_id: str,
    thread_candidate_lookup_row: Mapping[str, Any],
    candidate_bridge_rows: Sequence[Mapping[str, Any]],
    response_text: str | Any,
) -> ChatGPTAtlasGuidedPromptParseResult:
    segment_text = _require_segment_text(segment_text)
    lookup = _normalize_lookup_row(thread_candidate_lookup_row)
    candidate_contexts = _candidate_contexts_for_thread(lookup, candidate_bridge_rows)
    candidate_by_id = {item.candidate_id: item for item in candidate_contexts}
    candidate_by_key = {item.candidate_key: item for item in candidate_contexts}

    try:
        raw_text = _response_text(response_text)
    except TypeError:
        return _invalid_parse_result(
            lookup=lookup,
            segment_id=segment_id,
            segment_text=segment_text,
            error_code="invalid_response_text",
            raw_response=_debug_text(response_text),
        )

    try:
        data = json.loads(_strip_json_fence(raw_text))
    except json.JSONDecodeError:
        return _invalid_parse_result(
            lookup=lookup,
            segment_id=segment_id,
            segment_text=segment_text,
            error_code="invalid_json",
            raw_response=raw_text,
        )

    if not isinstance(data, Mapping):
        return _invalid_parse_result(
            lookup=lookup,
            segment_id=segment_id,
            segment_text=segment_text,
            error_code="invalid_response_shape",
            raw_response=raw_text,
        )

    if _contains_forbidden_output_key(data):
        return _invalid_parse_result(
            lookup=lookup,
            segment_id=segment_id,
            segment_text=segment_text,
            error_code="publish_attempt",
            raw_response=raw_text,
        )

    signals = data.get("signals")
    if not isinstance(signals, list):
        return _invalid_parse_result(
            lookup=lookup,
            segment_id=segment_id,
            segment_text=segment_text,
            error_code="missing_signals",
            raw_response=raw_text,
        )

    if len(signals) > MAX_SIGNAL_ITEMS:
        return _invalid_parse_result(
            lookup=lookup,
            segment_id=segment_id,
            segment_text=segment_text,
            error_code="too_many_signals",
            raw_response=raw_text,
        )

    try:
        if not signals:
            records = (
                _build_extraction_record(
                    lookup=lookup,
                    segment_id=segment_id,
                    segment_text=segment_text,
                    item_index=1,
                    extraction_status="null_signal",
                    summary="No atlas-constrained durable signal extracted.",
                    source_excerpt="",
                    confidence=0.0,
                    provenance={"model_signal_count": 0},
                ),
            )
        else:
            records = tuple(
                _parse_signal_item(
                    lookup=lookup,
                    candidate_by_id=candidate_by_id,
                    candidate_by_key=candidate_by_key,
                    segment_id=segment_id,
                    segment_text=segment_text,
                    item=item,
                    item_index=index + 1,
                )
                for index, item in enumerate(signals)
            )
    except _ParseError as exc:
        return _invalid_parse_result(
            lookup=lookup,
            segment_id=segment_id,
            segment_text=segment_text,
            error_code=exc.error_code,
            raw_response=raw_text,
        )

    return ChatGPTAtlasGuidedPromptParseResult(records=records)


def _parse_signal_item(
    *,
    lookup: Mapping[str, Any],
    candidate_by_id: Mapping[str, _CandidateContext],
    candidate_by_key: Mapping[str, _CandidateContext],
    segment_id: str,
    segment_text: str,
    item: Any,
    item_index: int,
) -> dict[str, Any]:
    if not isinstance(item, Mapping):
        raise _ParseError("invalid_signal_item")

    signal_status = item.get("signal_status")
    if signal_status not in {"accepted", "null_signal"}:
        raise _ParseError("invalid_signal_status")

    confidence = _coerce_confidence(item.get("confidence"))
    if confidence is None:
        raise _ParseError("invalid_confidence")

    summary = _required_text(item.get("summary"), "missing_summary")
    source_excerpt = _required_text(item.get("source_excerpt"), "missing_source_excerpt")

    if signal_status == "null_signal":
        candidate_id = _null_candidate_field(item.get("candidate_id"), "invalid_null_candidate_id")
        candidate_key = _null_candidate_field(item.get("candidate_key"), "invalid_null_candidate_key")
        canonical_wing = _null_candidate_field(
            item.get("canonical_wing"), "invalid_null_canonical_wing"
        )
        canonical_room = _null_candidate_field(
            item.get("canonical_room"), "invalid_null_canonical_room"
        )
        title = item.get("title")
        if title is not None and (not isinstance(title, str) or not title.strip()):
            raise _ParseError("invalid_null_title")
        signal_type = item.get("signal_type")
        if signal_type is not None and signal_type != "null_signal":
            raise _ParseError("invalid_null_signal_type")
        return _build_extraction_record(
            lookup=lookup,
            segment_id=segment_id,
            segment_text=segment_text,
            item_index=item_index,
            extraction_status="null_signal",
            summary=summary,
            source_excerpt=source_excerpt,
            confidence=confidence,
            title=title.strip() if isinstance(title, str) and title.strip() else None,
            signal_type="null_signal",
            provenance={
                "model_signal_status": "null_signal",
                "candidate_id": candidate_id,
                "candidate_key": candidate_key,
                "canonical_wing": canonical_wing,
                "canonical_room": canonical_room,
            },
        )

    candidate_id = _required_text(item.get("candidate_id"), "missing_candidate_id")
    candidate_key = _required_text(item.get("candidate_key"), "missing_candidate_key")
    title = _required_text(item.get("title"), "missing_title")
    signal_type = _required_text(item.get("signal_type"), "missing_signal_type")
    if _split_candidate_key(candidate_key) is None:
        raise _ParseError("invalid_candidate_key")

    selected_by_id = candidate_by_id.get(candidate_id)
    if selected_by_id is None:
        raise _ParseError("unknown_candidate_id")

    selected_by_key = candidate_by_key.get(candidate_key)
    if selected_by_key is None:
        raise _ParseError("unknown_candidate_key")
    if selected_by_id != selected_by_key:
        raise _ParseError("candidate_id_key_mismatch")

    expected_wing = selected_by_id.canonical_wing
    expected_room = selected_by_id.canonical_room
    canonical_wing = _required_text(item.get("canonical_wing"), "missing_canonical_wing")
    canonical_room = _required_text(item.get("canonical_room"), "missing_canonical_room")
    if not _is_canonical_slug(canonical_wing):
        raise _ParseError("invalid_canonical_wing")
    if not _is_canonical_slug(canonical_room):
        raise _ParseError("invalid_canonical_room")
    if canonical_wing != expected_wing or canonical_room != expected_room:
        raise _ParseError("canonical_wing_room_mismatch")

    return _build_extraction_record(
        lookup=lookup,
        segment_id=segment_id,
        segment_text=segment_text,
        item_index=item_index,
        extraction_status="accepted",
        candidate_id=candidate_id,
        candidate_key=candidate_key,
        signal_type=signal_type,
        title=title,
        summary=summary,
        source_excerpt=source_excerpt,
        confidence=confidence,
        provenance={
            "model_signal_status": "accepted",
            "atlas_candidate_ids": [candidate_id],
            "atlas_candidate_keys": [candidate_key],
            "atlas_cluster_ids": [selected_by_id.atlas_cluster_id],
            "candidate_bridge_status": selected_by_id.bridge_status,
        },
    )


def _build_extraction_record(
    *,
    lookup: Mapping[str, Any],
    segment_id: str,
    segment_text: str,
    item_index: int,
    extraction_status: str,
    summary: str,
    source_excerpt: str,
    confidence: float,
    candidate_id: str | None = None,
    candidate_key: str | None = None,
    signal_type: str | None = None,
    title: str | None = None,
    provenance: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return guided_contract.build_extraction_record(
        run_id=lookup["run_id"],
        atlas_run_id=lookup["atlas_run_id"],
        extraction_id=_extraction_id(
            lookup["thread_id"], segment_id, item_index, extraction_status
        ),
        thread_id=lookup["thread_id"],
        segment_id=segment_id,
        extraction_status=extraction_status,
        candidate_id=candidate_id,
        candidate_key=candidate_key,
        signal_type=signal_type,
        title=title,
        summary=_bounded_text(summary, PARSED_SOURCE_EXCERPT_MAX_CHARS * 2),
        source_excerpt=_bounded_text(source_excerpt, PARSED_SOURCE_EXCERPT_MAX_CHARS),
        confidence=confidence,
        provenance=_build_provenance(
            lookup=lookup,
            segment_text=segment_text,
            item_index=item_index,
            extra=provenance or {},
        ),
    )


def _invalid_parse_result(
    *,
    lookup: Mapping[str, Any],
    segment_id: str,
    segment_text: str,
    error_code: str,
    raw_response: str,
) -> ChatGPTAtlasGuidedPromptParseResult:
    raw_excerpt = _bounded_text(raw_response, RAW_RESPONSE_EXCERPT_MAX_CHARS)
    record = _build_extraction_record(
        lookup=lookup,
        segment_id=segment_id,
        segment_text=segment_text,
        item_index=1,
        extraction_status="invalid_output",
        summary=f"Invalid atlas-guided model output: {error_code}",
        source_excerpt="",
        confidence=0.0,
        signal_type="invalid_output",
        provenance={
            "error_code": error_code,
            "raw_response_excerpt": raw_excerpt,
        },
    )
    return ChatGPTAtlasGuidedPromptParseResult(
        records=(record,),
        error_code=error_code,
        raw_response_excerpt=raw_excerpt,
    )


def _normalize_lookup_row(row: Mapping[str, Any]) -> dict[str, Any]:
    validated = guided_contract.validate_row(guided_contract.THREAD_CANDIDATE_LOOKUP_SCHEMA, row)
    return {
        "run_id": validated["run_id"],
        "atlas_run_id": validated["atlas_run_id"],
        "thread_id": validated["thread_id"],
        "lookup_status": validated["lookup_status"],
        "candidate_ids": tuple(validated["candidate_ids"]),
        "candidate_keys": tuple(validated["candidate_keys"]),
        "primary_candidate_id": validated["primary_candidate_id"],
        "primary_candidate_key": validated["primary_candidate_key"],
        "reason_codes": tuple(validated["reason_codes"]),
        "source_thread_ref": validated["source_thread_ref"],
    }


def _candidate_contexts_for_thread(
    lookup: Mapping[str, Any], candidate_bridge_rows: Sequence[Mapping[str, Any]]
) -> tuple[_CandidateContext, ...]:
    ordered_ids = list(lookup["candidate_ids"])
    if not ordered_ids:
        return ()
    candidate_ids = set(ordered_ids)
    thread_id = lookup["thread_id"]
    rows_by_id: dict[str, _CandidateContext] = {}

    for raw_row in candidate_bridge_rows:
        row = guided_contract.validate_row(guided_contract.CANDIDATE_BRIDGE_RECORD_SCHEMA, raw_row)
        if row["run_id"] != lookup["run_id"] or row["atlas_run_id"] != lookup["atlas_run_id"]:
            continue
        if row["thread_ids"] and thread_id not in row["thread_ids"]:
            continue
        candidate_id = row.get("candidate_id")
        candidate_key = row.get("candidate_key")
        if candidate_id is None or candidate_key is None:
            continue
        if candidate_ids and candidate_id not in candidate_ids:
            continue
        if candidate_id in rows_by_id:
            continue
        rows_by_id[candidate_id] = _CandidateContext(
            candidate_id=candidate_id,
            candidate_key=candidate_key,
            canonical_wing=row["canonical_wing"],
            canonical_room=row["canonical_room"],
            atlas_cluster_id=row["atlas_cluster_id"],
            bridge_status=row["bridge_status"],
            label=row["label"],
            definition=row["definition"],
            top_terms=tuple(item["term"] for item in row["top_terms"][:3]),
            evidence_titles=tuple(row["evidence_titles"][:2]),
            representative_excerpt=(
                _bounded_text(row["representative_excerpts"][0], PROMPT_REPRESENTATIVE_EXCERPT_MAX_CHARS)
                if row["representative_excerpts"]
                else None
            ),
        )

    ordered_contexts = [rows_by_id[candidate_id] for candidate_id in ordered_ids if candidate_id in rows_by_id]
    if ordered_contexts:
        return tuple(ordered_contexts)
    return tuple(rows_by_id.values())


def _build_provenance(
    *,
    lookup: Mapping[str, Any],
    segment_text: str,
    item_index: int,
    extra: Mapping[str, Any],
) -> dict[str, Any]:
    provenance = {
        "thread_candidate_lookup_status": lookup["lookup_status"],
        "thread_candidate_ids": list(lookup["candidate_ids"]),
        "thread_candidate_keys": list(lookup["candidate_keys"]),
        "thread_candidate_reason_codes": list(lookup["reason_codes"]),
        "source_thread_ref": lookup["source_thread_ref"],
        "model_signal_index": item_index,
        "segment_excerpt": _bounded_text(segment_text, PROVENANCE_SEGMENT_EXCERPT_MAX_CHARS),
    }
    provenance.update(extra)
    return provenance


def _contains_forbidden_output_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _is_forbidden_output_key(key):
                return True
            if _contains_forbidden_output_key(item):
                return True
        return False
    if isinstance(value, list):
        return any(_contains_forbidden_output_key(item) for item in value)
    return False


def _is_forbidden_output_key(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    normalized = _normalize_output_key(value)
    if not normalized:
        return False
    if normalized in _FORBIDDEN_RESPONSE_KEYS:
        return True
    if normalized.startswith(_FORBIDDEN_RESPONSE_KEY_PREFIXES):
        return True
    if normalized in {"target", "target_room", "target_drawer"}:
        return True
    parts = tuple(part for part in normalized.split("_") if part)
    if not parts:
        return False
    if "target" in parts and "wing" in parts:
        return True
    if "base" in parts and "url" in parts:
        return True
    if "collection" in parts and any(part in {"chroma", "vector"} for part in parts):
        return True
    if any(part in _FORBIDDEN_RESPONSE_KEY_PARTS for part in parts):
        return True
    return False


def _normalize_output_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def _response_text(value: Any) -> str:
    if isinstance(value, str):
        text = value.strip()
        if text:
            return text
    raise TypeError("response_text must be a non-empty string")


def _require_segment_text(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("segment_text must be a non-empty string")
    return value.strip()


def _strip_json_fence(value: str) -> str:
    text = value.strip()
    if text.startswith("```"):
        first_newline = text.find("\n")
        if first_newline == -1:
            return text
        text = text[first_newline + 1 :]
        if text.endswith("```"):
            text = text[:-3]
    return text.strip()


def _required_text(value: Any, error_code: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _ParseError(error_code)
    return value.strip()


def _null_candidate_field(value: Any, error_code: str) -> None:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    raise _ParseError(error_code)


def _coerce_confidence(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    numeric = float(value)
    if not (0.0 <= numeric <= 1.0):
        return None
    return round(numeric, 4)


def _is_canonical_slug(value: str) -> bool:
    return bool(_CANONICAL_SLUG_RE.match(value))


def _split_candidate_key(value: str) -> tuple[str, str] | None:
    if value.count(":") != 1:
        return None
    canonical_wing, canonical_room = value.split(":", 1)
    if not _is_canonical_slug(canonical_wing) or not _is_canonical_slug(canonical_room):
        return None
    return canonical_wing, canonical_room


def _extraction_id(thread_id: str, segment_id: str, item_index: int, extraction_status: str) -> str:
    return f"extract-{thread_id}-{segment_id}-{extraction_status}-{item_index:04d}"


def _bounded_text(value: str, limit: int) -> str:
    text = value.strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."


def _debug_text(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    except TypeError:
        return repr(value)
