from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Any, Iterable, Mapping

from .ontology_run import validate_run_id


PHASE_NAME = "candidate_clusters"
DEFAULT_EXAMPLE_LIMIT = 3
DEFAULT_CENTROID_LIMIT = 5
DEFAULT_CANDIDATE_ID_MAX_LENGTH = 96
_SLUG_RE = re.compile(r"^[a-z0-9_]+$")


@dataclass(frozen=True)
class CandidateClusterBuildResult:
    records: list[dict[str, Any]]
    skipped_summary: dict[str, Any]


@dataclass(frozen=True)
class _EligiblePass1Record:
    run_id: str
    sequence: int
    attempt: int
    drawer_id: str
    source_wing: str
    source_room: str
    proposed_wing: str
    proposed_room: str
    proposal_label: str
    rationale_summary: str | None
    confidence: float | None
    record_ref: str


def build_candidate_id(
    canonical_wing: str,
    canonical_room: str,
    *,
    max_length: int = DEFAULT_CANDIDATE_ID_MAX_LENGTH,
) -> str:
    canonical_wing = _validate_slug(canonical_wing, "canonical_wing")
    canonical_room = _validate_slug(canonical_room, "canonical_room")
    if not isinstance(max_length, int) or max_length < 16:
        raise ValueError("max_length must be an integer >= 16")

    base = f"cand_{canonical_wing}__{canonical_room}"
    if len(base) <= max_length:
        return base

    digest = hashlib.sha256(f"{canonical_wing}:{canonical_room}".encode("utf-8")).hexdigest()[:10]
    prefix_budget = max_length - len(digest) - 1
    truncated = base[:prefix_budget].rstrip("_")
    return f"{truncated}_{digest}"


def cluster_pass1_phase_records(
    pass1_records: Iterable[Mapping[str, Any]],
    *,
    run_id: str | None = None,
    attempt: int = 1,
    sequence_start: int = 1,
    recorded_at: str | None = None,
    example_limit: int = DEFAULT_EXAMPLE_LIMIT,
    centroid_limit: int = DEFAULT_CENTROID_LIMIT,
) -> CandidateClusterBuildResult:
    if not isinstance(attempt, int) or attempt < 1:
        raise ValueError("attempt must be a positive integer")
    if not isinstance(sequence_start, int) or sequence_start < 1:
        raise ValueError("sequence_start must be a positive integer")
    if not isinstance(example_limit, int) or example_limit < 1:
        raise ValueError("example_limit must be a positive integer")
    if not isinstance(centroid_limit, int) or centroid_limit < 1:
        raise ValueError("centroid_limit must be a positive integer")

    records_list = list(pass1_records)
    resolved_run_id = _resolve_run_id(records_list, run_id=run_id)
    recorded_value = recorded_at or _utc_now()

    skipped_by_reason: Counter[str] = Counter()
    skipped_examples: list[dict[str, Any]] = []
    latest_by_drawer: dict[str, _EligiblePass1Record] = {}
    superseded_records = 0

    for record in records_list:
        eligible, skip_reason, skip_context = _normalize_pass1_record(record)
        if eligible is None:
            skipped_by_reason[skip_reason or "invalid_record"] += 1
            if skip_context and len(skipped_examples) < centroid_limit:
                skipped_examples.append(skip_context)
            continue
        if eligible.run_id != resolved_run_id:
            skipped_by_reason["run_id_mismatch"] += 1
            if len(skipped_examples) < centroid_limit:
                skipped_examples.append(
                    {
                        "reason": "run_id_mismatch",
                        "subject_id": eligible.drawer_id,
                        "pass1_record_ref": eligible.record_ref,
                    }
                )
            continue

        existing = latest_by_drawer.get(eligible.drawer_id)
        if existing is None or _sort_key(eligible) > _sort_key(existing):
            if existing is not None:
                superseded_records += 1
            latest_by_drawer[eligible.drawer_id] = eligible
        else:
            superseded_records += 1

    clustered: dict[tuple[str, str], list[_EligiblePass1Record]] = {}
    for eligible in latest_by_drawer.values():
        key = (eligible.proposed_wing, eligible.proposed_room)
        clustered.setdefault(key, []).append(eligible)

    records: list[dict[str, Any]] = []
    for offset, key in enumerate(sorted(clustered), start=sequence_start):
        proposed_wing, proposed_room = key
        members = sorted(
            clustered[key],
            key=lambda item: (item.sequence, item.attempt, item.drawer_id),
        )
        candidate_id = build_candidate_id(proposed_wing, proposed_room)
        records.append(
            {
                "schema_name": "ontology.phase_record",
                "schema_version": 1,
                "run_id": resolved_run_id,
                "phase": PHASE_NAME,
                "sequence": offset,
                "attempt": attempt,
                "recorded_at": recorded_value,
                "subject_type": "candidate",
                "subject_id": candidate_id,
                "record_status": "ok",
                "source": {
                    "wing": proposed_wing,
                    "room": proposed_room,
                },
                "payload": _build_candidate_payload(
                    candidate_id=candidate_id,
                    canonical_wing=proposed_wing,
                    canonical_room=proposed_room,
                    members=members,
                    example_limit=example_limit,
                    centroid_limit=centroid_limit,
                ),
            }
        )

    skipped_summary = {
        "input_records": len(records_list),
        "eligible_records": sum(len(members) for members in clustered.values()),
        "candidate_records": len(records),
        "skipped_records": int(sum(skipped_by_reason.values())),
        "superseded_records": superseded_records,
        "skipped_by_reason": dict(sorted(skipped_by_reason.items())),
        "skipped_examples": skipped_examples,
    }
    return CandidateClusterBuildResult(records=records, skipped_summary=skipped_summary)


def _build_candidate_payload(
    *,
    candidate_id: str,
    canonical_wing: str,
    canonical_room: str,
    members: list[_EligiblePass1Record],
    example_limit: int,
    centroid_limit: int,
) -> dict[str, Any]:
    proposal_labels = Counter(member.proposal_label for member in members if member.proposal_label)
    rationale_summaries = Counter(
        member.rationale_summary for member in members if member.rationale_summary
    )
    source_wings = Counter(member.source_wing for member in members)
    source_rooms = Counter(member.source_room for member in members)
    confidences = [member.confidence for member in members if member.confidence is not None]

    top_label = _ranked_counter_items(proposal_labels, "proposal_label", centroid_limit)
    top_rationales = _ranked_counter_items(
        rationale_summaries,
        "rationale_summary",
        centroid_limit,
    )
    confidence_avg = None
    if confidences:
        confidence_avg = round(sum(confidences) / len(confidences), 4)

    return {
        "candidate_id": candidate_id,
        "candidate_key": f"{canonical_wing}:{canonical_room}",
        "canonical_wing": canonical_wing,
        "canonical_room": canonical_room,
        "proposal_label": (
            top_label[0]["proposal_label"]
            if top_label
            else canonical_room.replace("_", " ")
        ),
        "cluster_stats": {
            "source_drawer_count": len(members),
            "source_wing_count": len(source_wings),
            "source_room_count": len(source_rooms),
            "proposal_label_count": len(proposal_labels),
            "rationale_summary_count": len(rationale_summaries),
            "confidence_count": len(confidences),
            "confidence_avg": confidence_avg,
        },
        "centroid": {
            "source_wings": _ranked_counter_items(source_wings, "source_wing", centroid_limit),
            "source_rooms": _ranked_counter_items(source_rooms, "source_room", centroid_limit),
            "proposal_labels": top_label,
            "rationale_summaries": top_rationales,
        },
        "source_drawer_refs": [
            {
                "drawer_id": member.drawer_id,
                "source_wing": member.source_wing,
                "source_room": member.source_room,
                "pass1_record_ref": member.record_ref,
            }
            for member in members
        ],
        "examples": [
            _build_example(member)
            for member in members[:example_limit]
        ],
    }


def _build_example(member: _EligiblePass1Record) -> dict[str, Any]:
    example = {
        "drawer_id": member.drawer_id,
        "source_wing": member.source_wing,
        "source_room": member.source_room,
        "pass1_record_ref": member.record_ref,
        "proposal_label": member.proposal_label,
    }
    if member.confidence is not None:
        example["confidence"] = member.confidence
    if member.rationale_summary:
        example["rationale_summary"] = member.rationale_summary
    return example


def _normalize_pass1_record(
    record: Mapping[str, Any] | Any,
) -> tuple[_EligiblePass1Record | None, str | None, dict[str, Any] | None]:
    if not isinstance(record, Mapping):
        return None, "non_mapping_record", {"reason": "non_mapping_record"}

    phase = record.get("phase")
    if phase != "pass1_open":
        return None, "wrong_phase", _skip_context(record, "wrong_phase")

    record_status = record.get("record_status")
    if record_status != "ok":
        reason = f"record_status_{record_status or 'missing'}"
        return None, reason, _skip_context(record, reason)

    run_id = record.get("run_id")
    sequence = record.get("sequence")
    attempt = record.get("attempt")
    source = record.get("source")
    payload = record.get("payload")
    if not isinstance(run_id, str) or not run_id.strip():
        return None, "missing_run_id", _skip_context(record, "missing_run_id")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
        return None, "invalid_sequence", _skip_context(record, "invalid_sequence")
    if not isinstance(attempt, int) or isinstance(attempt, bool) or attempt < 1:
        return None, "invalid_attempt", _skip_context(record, "invalid_attempt")
    if not isinstance(source, Mapping):
        return None, "missing_source", _skip_context(record, "missing_source")
    if not isinstance(payload, Mapping):
        return None, "missing_payload", _skip_context(record, "missing_payload")

    drawer_id = source.get("drawer_id")
    source_wing = source.get("wing")
    source_room = source.get("room")
    proposed_wing = payload.get("proposed_wing")
    proposed_room = payload.get("proposed_room")
    proposal_label = payload.get("proposal_label")
    rationale_summary = payload.get("rationale_summary")
    confidence = payload.get("confidence")

    if not isinstance(drawer_id, str) or not drawer_id.strip():
        return None, "missing_drawer_id", _skip_context(record, "missing_drawer_id")
    if not isinstance(source_wing, str) or not source_wing.strip():
        return None, "missing_source_wing", _skip_context(record, "missing_source_wing")
    if not isinstance(source_room, str) or not source_room.strip():
        return None, "missing_source_room", _skip_context(record, "missing_source_room")
    if not _is_slug(proposed_wing):
        return None, "invalid_proposed_wing", _skip_context(record, "invalid_proposed_wing")
    if not _is_slug(proposed_room):
        return None, "invalid_proposed_room", _skip_context(record, "invalid_proposed_room")

    if not isinstance(proposal_label, str) or not proposal_label.strip():
        proposal_label = proposed_room.replace("_", " ")
    else:
        proposal_label = proposal_label.strip()

    if rationale_summary is not None:
        if not isinstance(rationale_summary, str):
            rationale_summary = None
        else:
            rationale_summary = rationale_summary.strip() or None

    if confidence is not None:
        if isinstance(confidence, bool):
            confidence = None
        elif isinstance(confidence, (int, float)):
            confidence = float(confidence)
        else:
            confidence = None

    return (
        _EligiblePass1Record(
            run_id=run_id.strip(),
            sequence=sequence,
            attempt=attempt,
            drawer_id=drawer_id.strip(),
            source_wing=source_wing.strip(),
            source_room=source_room.strip(),
            proposed_wing=proposed_wing,
            proposed_room=proposed_room,
            proposal_label=proposal_label,
            rationale_summary=rationale_summary,
            confidence=confidence,
            record_ref=f"pass1_open.jsonl#{sequence}",
        ),
        None,
        None,
    )


def _resolve_run_id(
    pass1_records: list[Mapping[str, Any]],
    *,
    run_id: str | None,
) -> str:
    if run_id is not None:
        return validate_run_id(run_id)

    seen: set[str] = set()
    for record in pass1_records:
        if isinstance(record, Mapping):
            value = record.get("run_id")
            if isinstance(value, str) and value.strip():
                try:
                    seen.add(validate_run_id(value))
                except ValueError:
                    continue
    if not seen:
        raise ValueError("run_id is required when no input records carry a valid run_id")
    if len(seen) != 1:
        raise ValueError("pass1_records must belong to exactly one run_id")
    return next(iter(seen))


def _skip_context(record: Mapping[str, Any], reason: str) -> dict[str, Any]:
    context = {"reason": reason}
    subject_id = record.get("subject_id")
    sequence = record.get("sequence")
    if isinstance(subject_id, str) and subject_id:
        context["subject_id"] = subject_id
    if isinstance(sequence, int) and sequence >= 1:
        context["pass1_record_ref"] = f"pass1_open.jsonl#{sequence}"
    return context


def _sort_key(record: _EligiblePass1Record) -> tuple[int, int]:
    return (record.attempt, record.sequence)


def _ranked_counter_items(
    counter: Counter[str],
    value_key: str,
    limit: int,
) -> list[dict[str, Any]]:
    ranked = sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    return [{value_key: value, "count": count} for value, count in ranked[:limit]]


def _validate_slug(value: str, field_name: str) -> str:
    if not _is_slug(value):
        raise ValueError(f"{field_name} must match ^[a-z0-9_]+$")
    return value


def _is_slug(value: Any) -> bool:
    return isinstance(value, str) and bool(_SLUG_RE.fullmatch(value))


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
