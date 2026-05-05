from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import re
from typing import Any, Iterable, Mapping

from .ontology_candidates import build_candidate_id
from .ontology_run import validate_run_id


PHASE_NAME = "route_candidates"
_SOURCE_PHASE_NAME = "canonical_candidates"
DEFAULT_TOP_K = 5
DEFAULT_DRAWER_EXCERPT_MAX_CHARS = 240
DEFAULT_EXAMPLE_LIMIT = 3
DEFAULT_SOURCE_DRAWER_REF_LIMIT = 8
_SLUG_RE = re.compile(r"^[a-z0-9_]+$")
_TOKEN_RE = re.compile(r"[a-z0-9]+")
_EXAMPLE_TEXT_KEYS = ("excerpt", "content_excerpt", "rationale_summary", "definition")
_STOPWORD_TOKENS = frozenset(
    {
        "a",
        "an",
        "and",
        "for",
        "in",
        "of",
        "on",
        "or",
        "the",
        "to",
        "with",
    }
)


@dataclass(frozen=True)
class CandidateIndexEntry:
    candidate_id: str
    candidate_key: str
    canonical_wing: str
    canonical_room: str
    label: str
    definition: str
    canonical_candidate_record_ref: str
    source_candidate_refs: list[dict[str, Any]]
    source_drawer_refs: list[dict[str, Any]]
    examples: list[dict[str, Any]]
    room_tokens: Counter[str]
    wing_tokens: Counter[str]
    label_tokens: Counter[str]
    definition_tokens: Counter[str]
    example_tokens: Counter[str]
    source_room_tokens: Counter[str]
    support_drawer_count: int


@dataclass(frozen=True)
class CandidateIndexBuildResult:
    run_id: str
    candidates: list[CandidateIndexEntry]
    skipped_summary: dict[str, Any]


@dataclass(frozen=True)
class RouteCandidateSelectionResult:
    record_status: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class RouteCandidateBuildResult:
    records: list[dict[str, Any]]
    skipped_summary: dict[str, Any]


@dataclass(frozen=True)
class _CanonicalCandidateRecord:
    run_id: str
    sequence: int
    attempt: int
    subject_id: str
    source_candidate_id: str
    source_candidate_key: str
    source_canonical_wing: str
    source_canonical_room: str
    action: str
    candidate_id: str
    candidate_key: str
    canonical_wing: str
    canonical_room: str
    label: str | None
    definition: str | None
    source_candidate_record_ref: str
    source_drawer_refs: list[dict[str, Any]]
    examples: list[dict[str, Any]]
    record_ref: str


@dataclass(frozen=True)
class _CanonicalRecordEnvelope:
    run_id: str
    sequence: int
    attempt: int
    subject_id: str
    payload: Mapping[str, Any]


@dataclass(frozen=True)
class _NormalizedDrawer:
    drawer_id: str
    wing: str
    room: str
    content: str
    drawer_excerpt: str
    token_counts: Counter[str]
    normalized_text: str


def build_candidate_index(
    canonical_candidate_records: Iterable[Mapping[str, Any]],
    *,
    run_id: str | None = None,
    example_limit: int = DEFAULT_EXAMPLE_LIMIT,
    source_drawer_ref_limit: int = DEFAULT_SOURCE_DRAWER_REF_LIMIT,
) -> CandidateIndexBuildResult:
    if not isinstance(example_limit, int) or isinstance(example_limit, bool) or example_limit < 1:
        raise ValueError("example_limit must be a positive integer")
    if (
        not isinstance(source_drawer_ref_limit, int)
        or isinstance(source_drawer_ref_limit, bool)
        or source_drawer_ref_limit < 1
    ):
        raise ValueError("source_drawer_ref_limit must be a positive integer")

    records_list = list(canonical_candidate_records)
    resolved_run_id = _resolve_run_id(records_list, run_id=run_id)

    skipped_by_reason: Counter[str] = Counter()
    skipped_examples: list[dict[str, Any]] = []
    latest_by_subject: dict[str, _CanonicalCandidateRecord] = {}
    superseded_records = 0

    for record in records_list:
        normalized, skip_reason, skip_context = _normalize_canonical_record(record)
        if normalized is None:
            skipped_by_reason[skip_reason or "invalid_record"] += 1
            if skip_context and len(skipped_examples) < 10:
                skipped_examples.append(skip_context)
            continue
        if normalized.run_id != resolved_run_id:
            skipped_by_reason["run_id_mismatch"] += 1
            if len(skipped_examples) < 10:
                skipped_examples.append(
                    {
                        "reason": "run_id_mismatch",
                        "subject_id": normalized.subject_id,
                        "canonical_candidate_record_ref": normalized.record_ref,
                    }
                )
            continue

        existing = latest_by_subject.get(normalized.subject_id)
        if existing is None or _sort_key(normalized) > _sort_key(existing):
            if existing is not None:
                superseded_records += 1
            latest_by_subject[normalized.subject_id] = normalized
        else:
            superseded_records += 1

    resolved_merge_records = 0
    pruned_records = 0
    aggregates: dict[str, dict[str, Any]] = {}
    latest_records = sorted(
        latest_by_subject.values(),
        key=lambda item: (item.source_candidate_key, item.subject_id),
    )
    for candidate in latest_records:
        if candidate.action == "prune":
            pruned_records += 1
            continue

        terminal_subject_id, resolution_reason = _resolve_terminal_subject_id(
            candidate.subject_id,
            latest_by_subject,
        )
        if terminal_subject_id is None:
            skipped_by_reason[resolution_reason or "unresolved_merge"] += 1
            if len(skipped_examples) < 10:
                skipped_examples.append(
                    {
                        "reason": resolution_reason or "unresolved_merge",
                        "subject_id": candidate.subject_id,
                        "canonical_candidate_record_ref": candidate.record_ref,
                    }
                )
            continue

        terminal = latest_by_subject[terminal_subject_id]
        if terminal.action != "keep":
            skipped_by_reason["terminal_candidate_not_keep"] += 1
            if len(skipped_examples) < 10:
                skipped_examples.append(
                    {
                        "reason": "terminal_candidate_not_keep",
                        "subject_id": candidate.subject_id,
                        "canonical_candidate_record_ref": candidate.record_ref,
                    }
                )
            continue

        aggregate = aggregates.setdefault(
            terminal.candidate_id,
            _new_candidate_aggregate(terminal),
        )
        if candidate.subject_id != terminal.subject_id:
            resolved_merge_records += 1
        _append_candidate_source(aggregate, candidate)

    candidates = [
        _materialize_candidate_entry(
            aggregate,
            example_limit=example_limit,
            source_drawer_ref_limit=source_drawer_ref_limit,
        )
        for _, aggregate in sorted(aggregates.items(), key=lambda item: item[0])
    ]
    skipped_summary = {
        "input_records": len(records_list),
        "eligible_records": len(latest_records),
        "retrievable_candidates": len(candidates),
        "skipped_records": int(sum(skipped_by_reason.values())),
        "superseded_records": superseded_records,
        "pruned_records": pruned_records,
        "resolved_merge_records": resolved_merge_records,
        "skipped_by_reason": dict(sorted(skipped_by_reason.items())),
        "skipped_examples": skipped_examples,
    }
    return CandidateIndexBuildResult(
        run_id=resolved_run_id,
        candidates=candidates,
        skipped_summary=skipped_summary,
    )


def select_route_candidates_for_drawer(
    drawer: Mapping[str, Any],
    candidate_index: CandidateIndexBuildResult,
    *,
    top_k: int = DEFAULT_TOP_K,
    drawer_excerpt_max_chars: int = DEFAULT_DRAWER_EXCERPT_MAX_CHARS,
) -> RouteCandidateSelectionResult:
    if not isinstance(candidate_index, CandidateIndexBuildResult):
        raise ValueError("candidate_index must be a CandidateIndexBuildResult")
    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
        raise ValueError("top_k must be a positive integer")
    if (
        not isinstance(drawer_excerpt_max_chars, int)
        or isinstance(drawer_excerpt_max_chars, bool)
        or drawer_excerpt_max_chars < 32
    ):
        raise ValueError("drawer_excerpt_max_chars must be an integer >= 32")

    normalized_drawer = _normalize_drawer(drawer, drawer_excerpt_max_chars=drawer_excerpt_max_chars)
    payload = {
        "drawer_excerpt": normalized_drawer.drawer_excerpt,
        "candidate_index_size": len(candidate_index.candidates),
        "route_candidates": [],
    }

    if not candidate_index.candidates:
        payload.update(
            {
                "retrieval_status": "empty_candidate_index",
                "candidate_count": 0,
                "error_code": "no_retrievable_candidates",
                "retryable": True,
            }
        )
        return RouteCandidateSelectionResult(record_status="skipped", payload=payload)

    scored_candidates: list[tuple[float, dict[str, Any], CandidateIndexEntry]] = []
    for candidate in candidate_index.candidates:
        score, features = _score_candidate(normalized_drawer, candidate)
        if score <= 0:
            continue
        scored_candidates.append((score, features, candidate))

    scored_candidates.sort(
        key=lambda item: (
            -item[0],
            -int(item[1]["room_overlap_count"]),
            -int(item[1]["label_overlap_count"]),
            -int(item[1]["definition_overlap_count"]),
            item[2].candidate_key,
            item[2].candidate_id,
        )
    )

    selected = scored_candidates[:top_k]
    payload["candidate_count"] = len(selected)
    if not selected:
        payload["retrieval_status"] = "no_plausible_candidates"
        return RouteCandidateSelectionResult(record_status="ok", payload=payload)

    payload["retrieval_status"] = "ok"
    payload["route_candidates"] = [
        _serialize_scored_candidate(rank=index, score=score, features=features, candidate=candidate)
        for index, (score, features, candidate) in enumerate(selected, start=1)
    ]
    return RouteCandidateSelectionResult(record_status="ok", payload=payload)


def build_route_candidate_records(
    drawers: Iterable[Mapping[str, Any]],
    canonical_candidate_records: Iterable[Mapping[str, Any]],
    *,
    run_id: str | None = None,
    attempt: int = 1,
    sequence_start: int = 1,
    recorded_at: str | None = None,
    top_k: int = DEFAULT_TOP_K,
    drawer_excerpt_max_chars: int = DEFAULT_DRAWER_EXCERPT_MAX_CHARS,
) -> RouteCandidateBuildResult:
    if not isinstance(attempt, int) or isinstance(attempt, bool) or attempt < 1:
        raise ValueError("attempt must be a positive integer")
    if not isinstance(sequence_start, int) or isinstance(sequence_start, bool) or sequence_start < 1:
        raise ValueError("sequence_start must be a positive integer")

    candidate_index = build_candidate_index(canonical_candidate_records, run_id=run_id)
    recorded_value = recorded_at or _utc_now()

    skipped_by_reason: Counter[str] = Counter()
    skipped_examples: list[dict[str, Any]] = []
    record_status_counts: Counter[str] = Counter()
    valid_drawers: list[_NormalizedDrawer] = []

    drawers_list = list(drawers)
    for drawer in drawers_list:
        normalized, skip_reason, skip_context = _normalize_drawer_record(
            drawer,
            drawer_excerpt_max_chars=drawer_excerpt_max_chars,
        )
        if normalized is None:
            skipped_by_reason[skip_reason or "invalid_drawer"] += 1
            if skip_context and len(skipped_examples) < 10:
                skipped_examples.append(skip_context)
            continue
        valid_drawers.append(normalized)

    records: list[dict[str, Any]] = []
    for sequence, normalized_drawer in enumerate(valid_drawers, start=sequence_start):
        try:
            selection = select_route_candidates_for_drawer(
                {
                    "drawer_id": normalized_drawer.drawer_id,
                    "wing": normalized_drawer.wing,
                    "room": normalized_drawer.room,
                    "content": normalized_drawer.content,
                },
                candidate_index,
                top_k=top_k,
                drawer_excerpt_max_chars=drawer_excerpt_max_chars,
            )
        except Exception as exc:
            selection = RouteCandidateSelectionResult(
                record_status="error",
                payload={
                    "drawer_excerpt": normalized_drawer.drawer_excerpt,
                    "candidate_index_size": len(candidate_index.candidates),
                    "route_candidates": [],
                    "error_code": "route_candidate_selection_error",
                    "detail_excerpt": _bounded_excerpt(str(exc), drawer_excerpt_max_chars),
                    "retryable": False,
                },
            )

        record_status_counts[selection.record_status] += 1
        records.append(
            {
                "schema_name": "ontology.phase_record",
                "schema_version": 1,
                "run_id": candidate_index.run_id,
                "phase": PHASE_NAME,
                "sequence": sequence,
                "attempt": attempt,
                "recorded_at": recorded_value,
                "subject_type": "drawer",
                "subject_id": normalized_drawer.drawer_id,
                "record_status": selection.record_status,
                "source": {
                    "wing": normalized_drawer.wing,
                    "room": normalized_drawer.room,
                    "drawer_id": normalized_drawer.drawer_id,
                },
                "payload": selection.payload,
            }
        )

    skipped_summary = {
        "input_drawers": len(drawers_list),
        "valid_drawers": len(valid_drawers),
        "phase_records": len(records),
        "skipped_drawers": int(sum(skipped_by_reason.values())),
        "skipped_by_reason": dict(sorted(skipped_by_reason.items())),
        "skipped_examples": skipped_examples,
        "record_status_counts": dict(sorted(record_status_counts.items())),
        "candidate_index_summary": candidate_index.skipped_summary,
    }
    return RouteCandidateBuildResult(records=records, skipped_summary=skipped_summary)


def _normalize_canonical_record(
    record: Mapping[str, Any] | Any,
) -> tuple[_CanonicalCandidateRecord | None, str | None, dict[str, Any] | None]:
    if not isinstance(record, Mapping):
        return None, "non_mapping_record", {"reason": "non_mapping_record"}

    phase = record.get("phase")
    if phase != _SOURCE_PHASE_NAME:
        return None, "wrong_phase", _skip_context(record, "wrong_phase")

    record_status = record.get("record_status")
    if record_status != "ok":
        reason = f"record_status_{record_status or 'missing'}"
        return None, reason, _skip_context(record, reason)

    envelope, reason, context = _normalize_canonical_record_envelope(record)
    if envelope is None:
        return None, reason, context

    payload = envelope.payload
    source_candidate_id = payload.get("source_candidate_id", envelope.subject_id)
    source_candidate_key = payload.get("source_candidate_key")
    source_canonical_wing = payload.get("source_canonical_wing")
    source_canonical_room = payload.get("source_canonical_room")
    action = payload.get("action")
    candidate_id = payload.get("candidate_id")
    candidate_key = payload.get("candidate_key")
    canonical_wing = payload.get("canonical_wing")
    canonical_room = payload.get("canonical_room")
    source_candidate_record_ref = payload.get("source_candidate_record_ref")
    source_drawer_refs = payload.get("source_drawer_refs")
    examples = payload.get("examples")

    if not isinstance(source_candidate_id, str) or source_candidate_id != envelope.subject_id:
        return None, "invalid_source_candidate_id", _skip_context(record, "invalid_source_candidate_id")
    if action not in {"keep", "merge", "prune"}:
        return None, "invalid_action", _skip_context(record, "invalid_action")
    if not isinstance(source_candidate_key, str) or ":" not in source_candidate_key:
        return None, "invalid_source_candidate_key", _skip_context(record, "invalid_source_candidate_key")
    if not _is_slug(source_canonical_wing):
        return None, "invalid_source_canonical_wing", _skip_context(record, "invalid_source_canonical_wing")
    if not _is_slug(source_canonical_room):
        return None, "invalid_source_canonical_room", _skip_context(record, "invalid_source_canonical_room")
    if source_candidate_key != f"{source_canonical_wing}:{source_canonical_room}":
        return None, "invalid_source_candidate_key", _skip_context(record, "invalid_source_candidate_key")
    if not isinstance(source_candidate_record_ref, str) or not source_candidate_record_ref.strip():
        return None, "missing_source_candidate_record_ref", _skip_context(record, "missing_source_candidate_record_ref")
    if not isinstance(source_drawer_refs, list):
        return None, "missing_source_drawer_refs", _skip_context(record, "missing_source_drawer_refs")
    if not isinstance(examples, list):
        return None, "missing_examples", _skip_context(record, "missing_examples")
    if not _is_slug(canonical_wing):
        return None, "invalid_canonical_wing", _skip_context(record, "invalid_canonical_wing")
    if not _is_slug(canonical_room):
        return None, "invalid_canonical_room", _skip_context(record, "invalid_canonical_room")
    if not isinstance(candidate_key, str) or candidate_key != f"{canonical_wing}:{canonical_room}":
        return None, "invalid_candidate_key", _skip_context(record, "invalid_candidate_key")
    if not isinstance(candidate_id, str) or candidate_id != build_candidate_id(canonical_wing, canonical_room):
        if action != "merge":
            return None, "invalid_candidate_id", _skip_context(record, "invalid_candidate_id")
    if action == "keep":
        label = payload.get("label")
        definition = payload.get("definition")
        if not isinstance(label, str) or not label.strip():
            return None, "missing_label", _skip_context(record, "missing_label")
        if not isinstance(definition, str) or not definition.strip():
            return None, "missing_definition", _skip_context(record, "missing_definition")
    else:
        label = payload.get("label")
        definition = payload.get("definition")
        if label is not None and (not isinstance(label, str) or not label.strip()):
            return None, "invalid_label", _skip_context(record, "invalid_label")
        if definition is not None and (not isinstance(definition, str) or not definition.strip()):
            return None, "invalid_definition", _skip_context(record, "invalid_definition")

    return (
        _CanonicalCandidateRecord(
            run_id=envelope.run_id,
            sequence=envelope.sequence,
            attempt=envelope.attempt,
            subject_id=envelope.subject_id,
            source_candidate_id=source_candidate_id.strip(),
            source_candidate_key=source_candidate_key,
            source_canonical_wing=source_canonical_wing,
            source_canonical_room=source_canonical_room,
            action=action,
            candidate_id=candidate_id.strip(),
            candidate_key=candidate_key,
            canonical_wing=canonical_wing,
            canonical_room=canonical_room,
            label=label.strip() if isinstance(label, str) else None,
            definition=definition.strip() if isinstance(definition, str) else None,
            source_candidate_record_ref=source_candidate_record_ref.strip(),
            source_drawer_refs=[item for item in source_drawer_refs if isinstance(item, dict)],
            examples=[item for item in examples if isinstance(item, dict)],
            record_ref=f"{_SOURCE_PHASE_NAME}.jsonl#{envelope.sequence}",
        ),
        None,
        None,
    )


def _normalize_canonical_record_envelope(
    record: Mapping[str, Any],
) -> tuple[_CanonicalRecordEnvelope | None, str | None, dict[str, Any] | None]:
    run_id = record.get("run_id")
    sequence = record.get("sequence")
    attempt = record.get("attempt")
    payload = record.get("payload")
    subject_id = record.get("subject_id")

    if not isinstance(run_id, str) or not run_id.strip():
        return None, "missing_run_id", _skip_context(record, "missing_run_id")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
        return None, "invalid_sequence", _skip_context(record, "invalid_sequence")
    if not isinstance(attempt, int) or isinstance(attempt, bool) or attempt < 1:
        return None, "invalid_attempt", _skip_context(record, "invalid_attempt")
    if not isinstance(payload, Mapping):
        return None, "missing_payload", _skip_context(record, "missing_payload")
    if not isinstance(subject_id, str) or not subject_id.strip():
        return None, "missing_subject_id", _skip_context(record, "missing_subject_id")

    return (
        _CanonicalRecordEnvelope(
            run_id=run_id.strip(),
            sequence=sequence,
            attempt=attempt,
            subject_id=subject_id.strip(),
            payload=payload,
        ),
        None,
        None,
    )


def _normalize_drawer_record(
    drawer: Mapping[str, Any] | Any,
    *,
    drawer_excerpt_max_chars: int,
) -> tuple[_NormalizedDrawer | None, str | None, dict[str, Any] | None]:
    if not isinstance(drawer, Mapping):
        return None, "non_mapping_drawer", {"reason": "non_mapping_drawer"}

    try:
        return (
            _normalize_drawer(drawer, drawer_excerpt_max_chars=drawer_excerpt_max_chars),
            None,
            None,
        )
    except ValueError as exc:
        reason = str(exc)
        context = {"reason": reason}
        drawer_id = drawer.get("drawer_id")
        if isinstance(drawer_id, str) and drawer_id:
            context["drawer_id"] = drawer_id
        return None, reason, context


def _normalize_drawer(
    drawer: Mapping[str, Any],
    *,
    drawer_excerpt_max_chars: int,
) -> _NormalizedDrawer:
    drawer_id = drawer.get("drawer_id")
    wing = drawer.get("wing")
    room = drawer.get("room")
    title = drawer.get("title")
    metadata = drawer.get("metadata")
    content = drawer.get("content")
    if content is None:
        content = drawer.get("document", drawer.get("text", ""))

    if not isinstance(drawer_id, str) or not drawer_id.strip():
        raise ValueError("missing_drawer_id")
    if not isinstance(wing, str) or not wing.strip():
        raise ValueError("missing_wing")
    if not isinstance(room, str) or not room.strip():
        raise ValueError("missing_room")
    if content is None:
        content = ""
    if not isinstance(content, str):
        raise ValueError("invalid_content")
    if "\x00" in content:
        raise ValueError("invalid_content")

    title_text = title.strip() if isinstance(title, str) else ""
    metadata_text = _metadata_text(metadata)
    full_text = " ".join(part for part in (wing, room, title_text, metadata_text, content) if part)
    return _NormalizedDrawer(
        drawer_id=drawer_id.strip(),
        wing=wing.strip(),
        room=room.strip(),
        content=content,
        drawer_excerpt=_bounded_excerpt(content, drawer_excerpt_max_chars),
        token_counts=_token_counts(full_text),
        normalized_text=_normalize_phrase_text(full_text),
    )


def _resolve_terminal_subject_id(
    subject_id: str,
    candidates_by_subject: Mapping[str, _CanonicalCandidateRecord],
    *,
    trail: tuple[str, ...] = (),
) -> tuple[str | None, str | None]:
    if subject_id in trail:
        return None, "merge_cycle"

    candidate = candidates_by_subject.get(subject_id)
    if candidate is None:
        return None, "merge_target_missing"
    if candidate.action == "keep":
        return subject_id, None
    if candidate.action == "prune":
        return None, "merge_target_pruned"
    if candidate.action != "merge":
        return None, "invalid_action"

    target_subject_id = candidate.candidate_id
    if target_subject_id == subject_id:
        return None, "merge_cycle"
    return _resolve_terminal_subject_id(
        target_subject_id,
        candidates_by_subject,
        trail=trail + (subject_id,),
    )


def _new_candidate_aggregate(terminal: _CanonicalCandidateRecord) -> dict[str, Any]:
    return {
        "candidate_id": terminal.candidate_id,
        "candidate_key": terminal.candidate_key,
        "canonical_wing": terminal.canonical_wing,
        "canonical_room": terminal.canonical_room,
        "label": terminal.label or terminal.canonical_room.replace("_", " "),
        "definition": terminal.definition or "",
        "canonical_candidate_record_ref": terminal.record_ref,
        "source_candidate_refs": [],
        "source_drawer_refs": [],
        "examples": [],
    }


def _append_candidate_source(aggregate: dict[str, Any], candidate: _CanonicalCandidateRecord) -> None:
    aggregate["source_candidate_refs"].append(
        {
            "source_candidate_id": candidate.source_candidate_id,
            "source_candidate_key": candidate.source_candidate_key,
            "canonical_candidate_record_ref": candidate.record_ref,
            "source_candidate_record_ref": candidate.source_candidate_record_ref,
            "action": candidate.action,
        }
    )
    aggregate["source_drawer_refs"].extend(
        _normalize_source_drawer_refs(candidate.source_drawer_refs, candidate.record_ref)
    )
    aggregate["examples"].extend(_normalize_examples(candidate.examples))


def _materialize_candidate_entry(
    aggregate: dict[str, Any],
    *,
    example_limit: int,
    source_drawer_ref_limit: int,
) -> CandidateIndexEntry:
    source_drawer_refs = _dedupe_dicts(aggregate["source_drawer_refs"])
    examples = _dedupe_dicts(aggregate["examples"])
    source_candidate_refs = _sort_source_candidate_refs(_dedupe_dicts(aggregate["source_candidate_refs"]))
    source_rooms = " ".join(
        str(item["source_room"])
        for item in source_drawer_refs
        if isinstance(item.get("source_room"), str)
    )
    example_text = " ".join(
        str(item.get("excerpt", item.get("proposal_label", "")))
        for item in examples
    )
    return CandidateIndexEntry(
        candidate_id=aggregate["candidate_id"],
        candidate_key=aggregate["candidate_key"],
        canonical_wing=aggregate["canonical_wing"],
        canonical_room=aggregate["canonical_room"],
        label=aggregate["label"],
        definition=aggregate["definition"],
        canonical_candidate_record_ref=aggregate["canonical_candidate_record_ref"],
        source_candidate_refs=source_candidate_refs,
        source_drawer_refs=source_drawer_refs[:source_drawer_ref_limit],
        examples=examples[:example_limit],
        room_tokens=_token_counts(aggregate["canonical_room"].replace("_", " ")),
        wing_tokens=_token_counts(aggregate["canonical_wing"].replace("_", " ")),
        label_tokens=_token_counts(aggregate["label"]),
        definition_tokens=_token_counts(aggregate["definition"]),
        example_tokens=_token_counts(example_text),
        source_room_tokens=_token_counts(source_rooms),
        support_drawer_count=len(source_drawer_refs),
    )


def _normalize_source_drawer_refs(
    refs: Iterable[Mapping[str, Any]],
    canonical_candidate_record_ref: str,
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for ref in refs:
        if not isinstance(ref, Mapping):
            continue
        item: dict[str, Any] = {
            "canonical_candidate_record_ref": canonical_candidate_record_ref,
        }
        for key in ("drawer_id", "source_wing", "source_room", "pass1_record_ref"):
            value = ref.get(key)
            if isinstance(value, str) and value.strip():
                item[key] = value.strip()
        if "drawer_id" in item:
            normalized.append(item)
    return normalized


def _normalize_examples(examples: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for example in examples:
        if not isinstance(example, Mapping):
            continue
        item: dict[str, Any] = {}
        for key in ("drawer_id", "source_wing", "source_room", "pass1_record_ref", "proposal_label"):
            value = example.get(key)
            if isinstance(value, str) and value.strip():
                item[key] = value.strip()
        confidence = example.get("confidence")
        if isinstance(confidence, (int, float)) and not isinstance(confidence, bool):
            item["confidence"] = round(float(confidence), 4)
        excerpt = _extract_example_excerpt(example)
        if excerpt:
            item["excerpt"] = excerpt
        if item:
            normalized.append(item)
    return normalized


def _extract_example_excerpt(example: Mapping[str, Any]) -> str | None:
    for key in _EXAMPLE_TEXT_KEYS:
        value = example.get(key)
        if isinstance(value, str) and value.strip():
            return _bounded_excerpt(value, 180)
    return None


def _dedupe_dicts(items: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, Mapping):
            continue
        serialized = json.dumps(item, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        if serialized in seen:
            continue
        seen.add(serialized)
        deduped.append(dict(item))
    return deduped


def _sort_source_candidate_refs(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    action_order = {"keep": 0, "merge": 1, "prune": 2}
    return sorted(
        items,
        key=lambda item: (
            action_order.get(str(item.get("action")), 99),
            str(item.get("source_candidate_key", "")),
            str(item.get("source_candidate_id", "")),
            str(item.get("canonical_candidate_record_ref", "")),
        ),
    )


def _score_candidate(
    drawer: _NormalizedDrawer,
    candidate: CandidateIndexEntry,
) -> tuple[float, dict[str, Any]]:
    room_overlap = _overlap_count(drawer.token_counts, candidate.room_tokens)
    wing_overlap = _overlap_count(drawer.token_counts, candidate.wing_tokens)
    label_overlap = _overlap_count(drawer.token_counts, candidate.label_tokens)
    definition_overlap = _overlap_count(drawer.token_counts, candidate.definition_tokens)
    example_overlap = _overlap_count(drawer.token_counts, candidate.example_tokens)
    source_room_overlap = _overlap_count(drawer.token_counts, candidate.source_room_tokens)
    room_phrase_match = int(
        bool(candidate.canonical_room) and _normalize_phrase_text(candidate.canonical_room) in drawer.normalized_text
    )
    label_phrase_match = int(
        bool(candidate.label) and _normalize_phrase_text(candidate.label) in drawer.normalized_text
    )

    score = (
        (6.0 * room_phrase_match)
        + (5.0 * room_overlap)
        + (4.0 * label_overlap)
        + (2.0 * definition_overlap)
        + (1.5 * example_overlap)
        + (1.0 * wing_overlap)
        + (2.0 * label_phrase_match)
    )
    features = {
        "room_overlap_count": room_overlap,
        "wing_overlap_count": wing_overlap,
        "label_overlap_count": label_overlap,
        "definition_overlap_count": definition_overlap,
        "example_overlap_count": example_overlap,
        "source_room_overlap_count": source_room_overlap,
        "room_phrase_match": room_phrase_match,
        "label_phrase_match": label_phrase_match,
        "support_drawer_count": candidate.support_drawer_count,
        "source_candidate_count": len(candidate.source_candidate_refs),
    }
    return round(score, 4), features


def _serialize_scored_candidate(
    *,
    rank: int,
    score: float,
    features: Mapping[str, Any],
    candidate: CandidateIndexEntry,
) -> dict[str, Any]:
    return {
        "rank": rank,
        "candidate_id": candidate.candidate_id,
        "candidate_key": candidate.candidate_key,
        "canonical_wing": candidate.canonical_wing,
        "canonical_room": candidate.canonical_room,
        "label": candidate.label,
        "definition": candidate.definition,
        "canonical_candidate_record_ref": candidate.canonical_candidate_record_ref,
        "source_candidate_refs": [dict(item) for item in candidate.source_candidate_refs],
        "source_drawer_refs": [dict(item) for item in candidate.source_drawer_refs],
        "examples": [dict(item) for item in candidate.examples],
        "score": round(score, 4),
        "score_features": dict(features),
    }


def _resolve_run_id(
    canonical_candidate_records: list[Mapping[str, Any]],
    *,
    run_id: str | None,
) -> str:
    if run_id is not None:
        return validate_run_id(run_id)

    seen: set[str] = set()
    for record in canonical_candidate_records:
        if not isinstance(record, Mapping):
            continue
        value = record.get("run_id")
        if isinstance(value, str) and value.strip():
            try:
                seen.add(validate_run_id(value))
            except ValueError:
                continue
    if not seen:
        raise ValueError("run_id is required when no input records carry a valid run_id")
    if len(seen) != 1:
        raise ValueError("canonical_candidate_records must belong to exactly one run_id")
    return next(iter(seen))


def _skip_context(record: Mapping[str, Any], reason: str) -> dict[str, Any]:
    context = {"reason": reason}
    subject_id = record.get("subject_id")
    sequence = record.get("sequence")
    if isinstance(subject_id, str) and subject_id:
        context["subject_id"] = subject_id
    if isinstance(sequence, int) and sequence >= 1:
        context["canonical_candidate_record_ref"] = f"{_SOURCE_PHASE_NAME}.jsonl#{sequence}"
    return context


def _sort_key(record: _CanonicalCandidateRecord) -> tuple[int, int]:
    return (record.attempt, record.sequence)


def _token_counts(text: str) -> Counter[str]:
    counter: Counter[str] = Counter()
    for token in _TOKEN_RE.findall(text.lower().replace("_", " ")):
        normalized = _normalize_token(token)
        if normalized:
            counter[normalized] += 1
    return counter


def _normalize_token(token: str) -> str:
    if not token:
        return ""
    if token.endswith("ies") and len(token) > 4:
        token = token[:-3] + "y"
    elif token.endswith(("ches", "shes", "sses", "xes", "zes")) and len(token) > 5:
        token = token[:-2]
    elif token.endswith("s") and len(token) > 4 and not token.endswith("ss"):
        token = token[:-1]
    if token in _STOPWORD_TOKENS:
        return ""
    return token


def _normalize_phrase_text(text: str) -> str:
    return " ".join(_TOKEN_RE.findall(text.lower().replace("_", " ")))


def _overlap_count(left: Counter[str], right: Counter[str]) -> int:
    overlap = 0
    for token, count in right.items():
        overlap += min(left.get(token, 0), count)
    return overlap


def _metadata_text(metadata: Any) -> str:
    if metadata is None:
        return ""
    if isinstance(metadata, str):
        return metadata
    if isinstance(metadata, Mapping):
        parts = [
            str(value).strip()
            for _, value in sorted(metadata.items())
            if isinstance(value, (str, int, float)) and not isinstance(value, bool)
        ]
        return " ".join(part for part in parts if part)
    return ""


def _is_slug(value: Any) -> bool:
    return isinstance(value, str) and bool(_SLUG_RE.match(value))


def _bounded_excerpt(text: str, max_chars: int) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= max_chars:
        return collapsed
    if max_chars <= 3:
        return collapsed[:max_chars]
    return collapsed[: max_chars - 3].rstrip() + "..."


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
