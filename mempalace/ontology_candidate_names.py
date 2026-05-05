from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from .ontology_candidates import build_candidate_id
from .ontology_run import validate_run_id


PHASE_NAME = "canonical_candidates"
RAW_RESPONSE_EXCERPT_MAX_CHARS = 280
_SOURCE_PHASE_NAME = "candidate_clusters"
_SLUG_RE = re.compile(r"^[a-z0-9_]+$")
_VALID_ACTIONS = frozenset({"keep", "merge", "prune"})


@dataclass(frozen=True)
class CandidateNamingParseResult:
    record_status: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class CanonicalCandidateBuildResult:
    records: list[dict[str, Any]]
    skipped_summary: dict[str, Any]


@dataclass(frozen=True)
class _EligibleCandidateCluster:
    run_id: str
    sequence: int
    attempt: int
    candidate_id: str
    candidate_key: str
    canonical_wing: str
    canonical_room: str
    proposal_label: str
    cluster_stats: Mapping[str, Any]
    centroid: Mapping[str, Any]
    source_drawer_refs: list[dict[str, Any]]
    examples: list[dict[str, Any]]
    record_ref: str
    raw_record: Mapping[str, Any]


def build_candidate_naming_prompt(
    cluster_record: Mapping[str, Any],
    candidate_choices: Iterable[Mapping[str, Any]] | None = None,
) -> str:
    candidate = _require_candidate_cluster(cluster_record)
    choices = _normalize_candidate_choices(
        candidate_choices,
        source_candidate_id=candidate.candidate_id,
        source_candidate_key=candidate.candidate_key,
    )

    candidate_block = {
        "candidate_id": candidate.candidate_id,
        "candidate_key": candidate.candidate_key,
        "canonical_wing": candidate.canonical_wing,
        "canonical_room": candidate.canonical_room,
        "proposal_label": candidate.proposal_label,
        "cluster_stats": dict(candidate.cluster_stats),
        "centroid": dict(candidate.centroid),
        "examples": list(candidate.examples),
    }

    lines = [
        "You reconcile one clustered ontology candidate into a canonical candidate decision.",
        "",
        "Return JSON only. No prose. No code fences.",
        "",
        "SOURCE CANDIDATE",
        json.dumps(candidate_block, indent=2, sort_keys=True),
        "",
        "AVAILABLE ACTIONS",
        '- `keep`: keep this candidate as a canonical `wing:room` pair and provide `label` and `definition`.',
        "- `merge`: merge this candidate into one supplied merge target using its `candidate_id` or `candidate_key`.",
        "- `prune`: drop this candidate as too weak, redundant, or non-semantic and provide `prune_reason`.",
        "",
        "RULES",
        "- `canonical_wing` and `canonical_room` must match ^[a-z0-9_]+$.",
        "- Rooms are not globally unique; preserve wing context.",
        "- Only merge to one of the supplied candidate IDs or keys.",
        "- Do not merge a candidate into itself.",
        "",
    ]

    if choices:
        lines.extend(
            [
                "MERGE TARGETS",
                json.dumps(choices, indent=2, sort_keys=True),
                "",
            ]
        )
    else:
        lines.extend(
            [
                "MERGE TARGETS",
                "[]",
                "",
            ]
        )

    lines.extend(
        [
            "Return exactly one JSON object with this shape:",
            "{",
            '  "action": "keep|merge|prune",',
            '  "canonical_wing": "lowercase_slug",',
            '  "canonical_room": "lowercase_slug",',
            '  "label": "short human label for keep decisions",',
            '  "definition": "one or two concise sentences for keep decisions",',
            '  "merge_target_candidate_id": "required for merge unless key supplied",',
            '  "merge_target_candidate_key": "required for merge unless id supplied",',
            '  "prune_reason": "required for prune decisions"',
            "}",
        ]
    )
    return "\n".join(lines)


def parse_candidate_naming_response(
    cluster_record: Mapping[str, Any],
    response_text: str | Any,
    candidate_choices: Iterable[Mapping[str, Any]] | None = None,
    *,
    raw_excerpt_max_chars: int = RAW_RESPONSE_EXCERPT_MAX_CHARS,
) -> CandidateNamingParseResult:
    candidate = _require_candidate_cluster(cluster_record)
    choices = _normalize_candidate_choices(
        candidate_choices,
        source_candidate_id=candidate.candidate_id,
        source_candidate_key=candidate.candidate_key,
    )

    try:
        text = _response_text(response_text)
    except TypeError:
        return _invalid_model_output(
            "invalid_response_text",
            _raw_response_debug_text(response_text),
            raw_excerpt_max_chars=raw_excerpt_max_chars,
        )

    data = None
    for json_candidate in _extract_json_candidates(text):
        try:
            data = json.loads(json_candidate)
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

    action = _first_string(data, "action")
    if action is None:
        return _invalid_model_output(
            "missing_action",
            text,
            raw_excerpt_max_chars=raw_excerpt_max_chars,
        )
    if action not in _VALID_ACTIONS:
        return _invalid_model_output(
            "invalid_action",
            text,
            raw_excerpt_max_chars=raw_excerpt_max_chars,
        )

    canonical_wing = _first_string(data, "canonical_wing", "wing")
    canonical_room = _first_string(data, "canonical_room", "room")
    if canonical_wing is None:
        return _invalid_model_output(
            "missing_canonical_wing",
            text,
            raw_excerpt_max_chars=raw_excerpt_max_chars,
        )
    if canonical_room is None:
        return _invalid_model_output(
            "missing_canonical_room",
            text,
            raw_excerpt_max_chars=raw_excerpt_max_chars,
        )
    if not _is_slug(canonical_wing):
        return _invalid_model_output(
            "invalid_canonical_wing",
            text,
            raw_excerpt_max_chars=raw_excerpt_max_chars,
        )
    if not _is_slug(canonical_room):
        return _invalid_model_output(
            "invalid_canonical_room",
            text,
            raw_excerpt_max_chars=raw_excerpt_max_chars,
        )

    if action == "keep":
        label = _required_string(data, "label")
        definition = _required_string(data, "definition")
        if label is None:
            return _invalid_model_output(
                "missing_label",
                text,
                raw_excerpt_max_chars=raw_excerpt_max_chars,
            )
        if definition is None:
            return _invalid_model_output(
                "missing_definition",
                text,
                raw_excerpt_max_chars=raw_excerpt_max_chars,
            )
        return CandidateNamingParseResult(
            record_status="ok",
            payload={
                "action": "keep",
                "candidate_id": build_candidate_id(canonical_wing, canonical_room),
                "candidate_key": f"{canonical_wing}:{canonical_room}",
                "canonical_wing": canonical_wing,
                "canonical_room": canonical_room,
                "label": label[:80],
                "definition": definition[:400],
            },
        )

    if action == "merge":
        merge_target_id = _first_string(
            data,
            "merge_target_candidate_id",
            "merge_target_id",
            "target_candidate_id",
        )
        merge_target_key = _first_string(
            data,
            "merge_target_candidate_key",
            "merge_target_key",
            "target_candidate_key",
        )
        target = _resolve_merge_target(
            choices,
            source_candidate=candidate,
            merge_target_id=merge_target_id,
            merge_target_key=merge_target_key,
            canonical_wing=canonical_wing,
            canonical_room=canonical_room,
        )
        if target is None:
            return _invalid_model_output(
                "invalid_merge_target",
                text,
                raw_excerpt_max_chars=raw_excerpt_max_chars,
            )
        payload = {
            "action": "merge",
            "candidate_id": target["candidate_id"],
            "candidate_key": target["candidate_key"],
            "canonical_wing": target["canonical_wing"],
            "canonical_room": target["canonical_room"],
            "merge_target_candidate_id": target["candidate_id"],
            "merge_target_candidate_key": target["candidate_key"],
        }
        label = _optional_string(data, "label")
        definition = _optional_string(data, "definition")
        if label:
            payload["label"] = label[:80]
        if definition:
            payload["definition"] = definition[:400]
        return CandidateNamingParseResult(record_status="ok", payload=payload)

    prune_reason = _required_string(data, "prune_reason", "reason")
    if prune_reason is None:
        return _invalid_model_output(
            "missing_prune_reason",
            text,
            raw_excerpt_max_chars=raw_excerpt_max_chars,
        )
    payload = {
        "action": "prune",
        "candidate_id": build_candidate_id(canonical_wing, canonical_room),
        "candidate_key": f"{canonical_wing}:{canonical_room}",
        "canonical_wing": canonical_wing,
        "canonical_room": canonical_room,
        "prune_reason": prune_reason[:240],
    }
    label = _optional_string(data, "label")
    definition = _optional_string(data, "definition")
    if label:
        payload["label"] = label[:80]
    if definition:
        payload["definition"] = definition[:400]
    return CandidateNamingParseResult(record_status="ok", payload=payload)


def build_canonical_candidate_records(
    cluster_records: Iterable[Mapping[str, Any]],
    model_outputs_by_candidate_id: Mapping[str, Any],
    *,
    run_id: str | None = None,
    attempt: int = 1,
    sequence_start: int = 1,
    recorded_at: str | None = None,
    raw_excerpt_max_chars: int = RAW_RESPONSE_EXCERPT_MAX_CHARS,
) -> CanonicalCandidateBuildResult:
    if not isinstance(model_outputs_by_candidate_id, Mapping):
        raise ValueError("model_outputs_by_candidate_id must be a mapping")
    if not isinstance(attempt, int) or isinstance(attempt, bool) or attempt < 1:
        raise ValueError("attempt must be a positive integer")
    if not isinstance(sequence_start, int) or isinstance(sequence_start, bool) or sequence_start < 1:
        raise ValueError("sequence_start must be a positive integer")

    records_list = list(cluster_records)
    resolved_run_id = _resolve_run_id(records_list, run_id=run_id)
    recorded_value = recorded_at or _utc_now()

    skipped_by_reason: Counter[str] = Counter()
    skipped_examples: list[dict[str, Any]] = []
    latest_by_candidate: dict[str, _EligibleCandidateCluster] = {}
    superseded_records = 0

    for record in records_list:
        eligible, skip_reason, skip_context = _normalize_cluster_record(record)
        if eligible is None:
            skipped_by_reason[skip_reason or "invalid_record"] += 1
            if skip_context and len(skipped_examples) < 10:
                skipped_examples.append(skip_context)
            continue
        if eligible.run_id != resolved_run_id:
            skipped_by_reason["run_id_mismatch"] += 1
            if len(skipped_examples) < 10:
                skipped_examples.append(
                    {
                        "reason": "run_id_mismatch",
                        "subject_id": eligible.candidate_id,
                        "candidate_record_ref": eligible.record_ref,
                    }
                )
            continue

        existing = latest_by_candidate.get(eligible.candidate_id)
        if existing is None or _sort_key(eligible) > _sort_key(existing):
            if existing is not None:
                superseded_records += 1
            latest_by_candidate[eligible.candidate_id] = eligible
        else:
            superseded_records += 1

    eligible_candidates = sorted(
        latest_by_candidate.values(),
        key=lambda item: (item.candidate_key, item.candidate_id),
    )
    candidate_choices = [_choice_from_candidate(candidate) for candidate in eligible_candidates]

    records: list[dict[str, Any]] = []
    for sequence, candidate in enumerate(eligible_candidates, start=sequence_start):
        response = model_outputs_by_candidate_id.get(candidate.candidate_id)
        if response is None:
            parsed = CandidateNamingParseResult(
                record_status="skipped",
                payload={
                    "error_code": "missing_model_output",
                    "retryable": True,
                },
            )
        else:
            try:
                parsed = parse_candidate_naming_response(
                    candidate.raw_record,
                    response,
                    candidate_choices,
                    raw_excerpt_max_chars=raw_excerpt_max_chars,
                )
            except Exception as exc:
                parsed = CandidateNamingParseResult(
                    record_status="error",
                    payload={
                        "error_code": "candidate_naming_parse_error",
                        "detail_excerpt": _bounded_excerpt(str(exc), raw_excerpt_max_chars),
                        "retryable": False,
                    },
                )

        records.append(
            {
                "schema_name": "ontology.phase_record",
                "schema_version": 1,
                "run_id": resolved_run_id,
                "phase": PHASE_NAME,
                "sequence": sequence,
                "attempt": attempt,
                "recorded_at": recorded_value,
                "subject_type": "candidate",
                "subject_id": candidate.candidate_id,
                "record_status": parsed.record_status,
                "source": {
                    "wing": candidate.canonical_wing,
                    "room": candidate.canonical_room,
                    "candidate_id": candidate.candidate_id,
                    "candidate_key": candidate.candidate_key,
                },
                "payload": _build_output_payload(candidate, parsed.payload),
            }
        )

    skipped_summary = {
        "input_records": len(records_list),
        "eligible_records": len(eligible_candidates),
        "phase_records": len(records),
        "skipped_records": int(sum(skipped_by_reason.values())),
        "superseded_records": superseded_records,
        "skipped_by_reason": dict(sorted(skipped_by_reason.items())),
        "skipped_examples": skipped_examples,
    }
    return CanonicalCandidateBuildResult(records=records, skipped_summary=skipped_summary)


def _build_output_payload(
    candidate: _EligibleCandidateCluster,
    parsed_payload: Mapping[str, Any],
) -> dict[str, Any]:
    payload = {
        "source_candidate_id": candidate.candidate_id,
        "source_candidate_key": candidate.candidate_key,
        "source_canonical_wing": candidate.canonical_wing,
        "source_canonical_room": candidate.canonical_room,
        "source_candidate_record_ref": candidate.record_ref,
        "cluster_stats": dict(candidate.cluster_stats),
        "centroid": dict(candidate.centroid),
        "source_drawer_refs": list(candidate.source_drawer_refs),
        "examples": list(candidate.examples),
    }
    payload.update(parsed_payload)
    return payload


def _normalize_cluster_record(
    record: Mapping[str, Any] | Any,
) -> tuple[_EligibleCandidateCluster | None, str | None, dict[str, Any] | None]:
    if not isinstance(record, Mapping):
        return None, "non_mapping_record", {"reason": "non_mapping_record"}

    phase = record.get("phase")
    if phase != _SOURCE_PHASE_NAME:
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

    candidate_id = payload.get("candidate_id", record.get("subject_id"))
    candidate_key = payload.get("candidate_key")
    canonical_wing = payload.get("canonical_wing")
    canonical_room = payload.get("canonical_room")
    proposal_label = payload.get("proposal_label")
    cluster_stats = payload.get("cluster_stats")
    centroid = payload.get("centroid")
    source_drawer_refs = payload.get("source_drawer_refs")
    examples = payload.get("examples")

    if not isinstance(candidate_id, str) or not candidate_id.strip():
        return None, "missing_candidate_id", _skip_context(record, "missing_candidate_id")
    if not _is_slug(canonical_wing):
        return None, "invalid_canonical_wing", _skip_context(record, "invalid_canonical_wing")
    if not _is_slug(canonical_room):
        return None, "invalid_canonical_room", _skip_context(record, "invalid_canonical_room")
    if not isinstance(candidate_key, str) or candidate_key != f"{canonical_wing}:{canonical_room}":
        return None, "invalid_candidate_key", _skip_context(record, "invalid_candidate_key")
    if not isinstance(cluster_stats, Mapping):
        return None, "missing_cluster_stats", _skip_context(record, "missing_cluster_stats")
    if not isinstance(centroid, Mapping):
        return None, "missing_centroid", _skip_context(record, "missing_centroid")
    if not isinstance(source_drawer_refs, list):
        return None, "missing_source_drawer_refs", _skip_context(record, "missing_source_drawer_refs")
    if not isinstance(examples, list):
        return None, "missing_examples", _skip_context(record, "missing_examples")

    if not isinstance(proposal_label, str) or not proposal_label.strip():
        proposal_label = canonical_room.replace("_", " ")
    else:
        proposal_label = proposal_label.strip()

    return (
        _EligibleCandidateCluster(
            run_id=run_id.strip(),
            sequence=sequence,
            attempt=attempt,
            candidate_id=candidate_id.strip(),
            candidate_key=candidate_key,
            canonical_wing=canonical_wing,
            canonical_room=canonical_room,
            proposal_label=proposal_label,
            cluster_stats=dict(cluster_stats),
            centroid=dict(centroid),
            source_drawer_refs=[item for item in source_drawer_refs if isinstance(item, dict)],
            examples=[item for item in examples if isinstance(item, dict)],
            record_ref=f"{_SOURCE_PHASE_NAME}.jsonl#{sequence}",
            raw_record=record,
        ),
        None,
        None,
    )


def _require_candidate_cluster(cluster_record: Mapping[str, Any]) -> _EligibleCandidateCluster:
    candidate, reason, _ = _normalize_cluster_record(cluster_record)
    if candidate is None:
        raise ValueError(reason or "invalid_cluster_record")
    return candidate


def _choice_from_candidate(candidate: _EligibleCandidateCluster) -> dict[str, Any]:
    choice = {
        "candidate_id": candidate.candidate_id,
        "candidate_key": candidate.candidate_key,
        "canonical_wing": candidate.canonical_wing,
        "canonical_room": candidate.canonical_room,
        "proposal_label": candidate.proposal_label,
    }
    source_drawer_count = candidate.cluster_stats.get("source_drawer_count")
    if isinstance(source_drawer_count, int) and not isinstance(source_drawer_count, bool):
        choice["source_drawer_count"] = source_drawer_count
    return choice


def _normalize_candidate_choices(
    candidate_choices: Iterable[Mapping[str, Any]] | None,
    *,
    source_candidate_id: str,
    source_candidate_key: str,
) -> list[dict[str, Any]]:
    if candidate_choices is None:
        return []

    normalized: list[dict[str, Any]] = []
    for choice in candidate_choices:
        if not isinstance(choice, Mapping):
            raise ValueError("candidate_choices entries must be mappings")
        payload = choice.get("payload")
        candidate_id = choice.get("candidate_id")
        candidate_key = choice.get("candidate_key")
        canonical_wing = choice.get("canonical_wing")
        canonical_room = choice.get("canonical_room")
        proposal_label = choice.get("proposal_label")
        source_drawer_count = choice.get("source_drawer_count")
        if isinstance(payload, Mapping):
            candidate_id = payload.get("candidate_id", candidate_id)
            candidate_key = payload.get("candidate_key", candidate_key)
            canonical_wing = payload.get("canonical_wing", canonical_wing)
            canonical_room = payload.get("canonical_room", canonical_room)
            proposal_label = payload.get("proposal_label", proposal_label)
            if source_drawer_count is None:
                cluster_stats = payload.get("cluster_stats")
                if isinstance(cluster_stats, Mapping):
                    source_drawer_count = cluster_stats.get("source_drawer_count")

        if not isinstance(candidate_id, str) or not candidate_id.strip():
            raise ValueError("candidate_choices entries must include candidate_id")
        if not _is_slug(canonical_wing):
            raise ValueError("candidate_choices entries must include slug-safe canonical_wing")
        if not _is_slug(canonical_room):
            raise ValueError("candidate_choices entries must include slug-safe canonical_room")
        expected_key = f"{canonical_wing}:{canonical_room}"
        if not isinstance(candidate_key, str) or candidate_key != expected_key:
            raise ValueError("candidate_choices entries must include a valid candidate_key")

        normalized.append(
            {
                "candidate_id": candidate_id.strip(),
                "candidate_key": candidate_key,
                "canonical_wing": canonical_wing,
                "canonical_room": canonical_room,
                "proposal_label": (
                    proposal_label.strip()
                    if isinstance(proposal_label, str) and proposal_label.strip()
                    else canonical_room.replace("_", " ")
                ),
                "source_drawer_count": (
                    source_drawer_count
                    if isinstance(source_drawer_count, int) and not isinstance(source_drawer_count, bool)
                    else None
                ),
            }
        )

    normalized.sort(key=lambda item: (item["candidate_key"], item["candidate_id"]))
    return [
        item
        for item in normalized
        if item["candidate_id"] != source_candidate_id and item["candidate_key"] != source_candidate_key
    ]


def _resolve_merge_target(
    candidate_choices: list[dict[str, Any]],
    *,
    source_candidate: _EligibleCandidateCluster,
    merge_target_id: str | None,
    merge_target_key: str | None,
    canonical_wing: str,
    canonical_room: str,
) -> dict[str, Any] | None:
    if merge_target_id is None and merge_target_key is None:
        return None

    matches = candidate_choices
    if merge_target_id is not None:
        matches = [item for item in matches if item["candidate_id"] == merge_target_id]
    if merge_target_key is not None:
        matches = [item for item in matches if item["candidate_key"] == merge_target_key]
    if len(matches) != 1:
        return None

    match = matches[0]
    if match["candidate_id"] == source_candidate.candidate_id:
        return None
    if match["candidate_key"] == source_candidate.candidate_key:
        return None
    if match["canonical_wing"] != canonical_wing:
        return None
    if match["canonical_room"] != canonical_room:
        return None
    return match


def _resolve_run_id(
    cluster_records: list[Mapping[str, Any]],
    *,
    run_id: str | None,
) -> str:
    if run_id is not None:
        return validate_run_id(run_id)

    seen: set[str] = set()
    for record in cluster_records:
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
        raise ValueError("cluster_records must belong to exactly one run_id")
    return next(iter(seen))


def _skip_context(record: Mapping[str, Any], reason: str) -> dict[str, Any]:
    context = {"reason": reason}
    subject_id = record.get("subject_id")
    sequence = record.get("sequence")
    if isinstance(subject_id, str) and subject_id:
        context["subject_id"] = subject_id
    if isinstance(sequence, int) and sequence >= 1:
        context["candidate_record_ref"] = f"{_SOURCE_PHASE_NAME}.jsonl#{sequence}"
    return context


def _sort_key(record: _EligibleCandidateCluster) -> tuple[int, int]:
    return (record.attempt, record.sequence)


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
        for end in range(start, len(text)):
            char = text[end]
            if char == opener:
                depth += 1
            elif char == closer:
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


def _required_string(data: Mapping[str, Any], *keys: str) -> str | None:
    return _first_string(data, *keys)


def _optional_string(data: Mapping[str, Any], *keys: str) -> str | None:
    return _first_string(data, *keys)


def _is_slug(value: Any) -> bool:
    return isinstance(value, str) and bool(_SLUG_RE.fullmatch(value))


def _invalid_model_output(
    error_code: str,
    raw_response: str,
    *,
    raw_excerpt_max_chars: int,
) -> CandidateNamingParseResult:
    return CandidateNamingParseResult(
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
