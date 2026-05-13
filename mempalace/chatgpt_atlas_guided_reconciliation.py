from __future__ import annotations

import hashlib
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any, Iterable, Mapping

from . import chatgpt_atlas_guided_contract as guided_contract

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
_GENERIC_TOKENS = frozenset(
    {
        "a",
        "an",
        "and",
        "atlas",
        "chatgpt",
        "durable",
        "extract",
        "extracted",
        "for",
        "from",
        "guided",
        "in",
        "is",
        "memory",
        "no",
        "of",
        "or",
        "signal",
        "the",
        "this",
        "to",
    }
)
_SOURCE_RECORD_FIELD_NAMES = (
    "extraction_id",
    "thread_id",
    "segment_id",
    "logical_source_id",
    "source_hash",
    "conversation_id",
    "conversation_title",
    "subthread_id",
    "subthread_label",
    "segment_index",
    "message_start_index",
    "message_end_index",
    "char_start",
    "char_end",
    "source_path",
    "model",
    "extraction_version",
)


@dataclass(frozen=True)
class ChatGPTAtlasGuidedReconciliationResult:
    rows: tuple[dict[str, Any], ...]
    stats: dict[str, int]


@dataclass(frozen=True)
class _AcceptedExtraction:
    input_index: int
    row: dict[str, Any]
    extraction_id: str
    thread_id: str
    segment_id: str
    candidate_id: str
    candidate_key: str
    canonical_wing: str
    canonical_room: str
    signal_type: str
    title: str
    summary: str
    source_excerpt: str
    confidence: float | None
    title_norm: str
    summary_norm: str
    excerpt_norm: str
    combined_norm: str
    title_tokens: tuple[str, ...]
    summary_tokens: tuple[str, ...]
    excerpt_tokens: tuple[str, ...]
    combined_tokens: tuple[str, ...]


@dataclass
class _Cluster:
    candidate_id: str
    candidate_key: str
    canonical_wing: str
    canonical_room: str
    rows: list[_AcceptedExtraction] = field(default_factory=list)


def build_chatgpt_atlas_guided_reconciliation_rows(
    extraction_rows: Iterable[Mapping[str, Any]],
    *,
    run_id: str | None = None,
    atlas_run_id: str | None = None,
) -> tuple[dict[str, Any], ...]:
    return build_chatgpt_atlas_guided_reconciliation(
        extraction_rows,
        run_id=run_id,
        atlas_run_id=atlas_run_id,
    ).rows


def build_chatgpt_atlas_guided_reconciliation(
    extraction_rows: Iterable[Mapping[str, Any]],
    *,
    run_id: str | None = None,
    atlas_run_id: str | None = None,
) -> ChatGPTAtlasGuidedReconciliationResult:
    validated_rows: list[dict[str, Any]] = []
    accepted_rows: list[_AcceptedExtraction] = []
    seen_run_ids: set[str] = set()
    seen_atlas_run_ids: set[str] = set()
    status_counts: Counter[str] = Counter()

    for index, raw_row in enumerate(extraction_rows):
        if not isinstance(raw_row, Mapping):
            raise ValueError(
                f"extraction row {index} must be a mapping, got {type(raw_row).__name__}"
            )
        validated = guided_contract.validate_row(guided_contract.EXTRACTION_RECORD_SCHEMA, raw_row)
        row_run_id = _require_nonempty_str("run_id", validated.get("run_id"))
        row_atlas_run_id = _require_nonempty_str("atlas_run_id", validated.get("atlas_run_id"))
        seen_run_ids.add(row_run_id)
        seen_atlas_run_ids.add(row_atlas_run_id)
        validated_rows.append(validated)
        status = _require_nonempty_str("extraction_status", validated.get("extraction_status"))
        status_counts[status] += 1
        if status != "accepted":
            continue
        accepted_rows.append(_normalize_accepted_row(index=index, row=validated))

    resolved_run_id = _resolve_id("run_id", requested=run_id, seen=seen_run_ids)
    resolved_atlas_run_id = _resolve_id(
        "atlas_run_id",
        requested=atlas_run_id,
        seen=seen_atlas_run_ids,
    )

    rows: list[dict[str, Any]] = []
    clusters = _build_clusters(accepted_rows)

    for candidate_id in sorted(clusters):
        for cluster in sorted(
            clusters[candidate_id],
            key=lambda item: _accepted_sort_key(min(item.rows, key=_accepted_sort_key)),
        ):
            rows.extend(
                _build_cluster_rows(
                    cluster=cluster,
                    run_id=resolved_run_id,
                    atlas_run_id=resolved_atlas_run_id,
                )
            )

    ordered_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                str(row["candidate_key"]),
                str(row["dedupe_key"]),
                0 if row["reconciliation_status"] == "accepted" else 1,
                str(row["reconciled_signal_id"]),
            ),
        )
    )

    duplicate_count = sum(
        1 for row in ordered_rows if row["reconciliation_status"] == "duplicate"
    )
    stats = {
        "reconciled_signals": len(ordered_rows),
        "reconciled_accepted_signals": len(ordered_rows) - duplicate_count,
        "reconciled_duplicate_signals": duplicate_count,
        "reconciled_source_extractions": len(validated_rows),
        "reconciliation_candidate_groups": sum(len(items) for items in clusters.values()),
        "reconciliation_accepted_extractions": status_counts.get("accepted", 0),
        "reconciliation_null_signal_extractions": status_counts.get("null_signal", 0),
        "reconciliation_invalid_output_extractions": status_counts.get("invalid_output", 0),
        "reconciliation_provider_error_extractions": status_counts.get("provider_error", 0),
        "reconciliation_skipped_extractions": status_counts.get("skipped", 0),
    }
    return ChatGPTAtlasGuidedReconciliationResult(rows=ordered_rows, stats=stats)


def _normalize_accepted_row(*, index: int, row: dict[str, Any]) -> _AcceptedExtraction:
    title = _coerce_text("title", row.get("title"))
    summary = _coerce_text("summary", row.get("summary"))
    source_excerpt = _coerce_text("source_excerpt", row.get("source_excerpt"))
    signal_type = _coerce_signal_type(row.get("signal_type"))
    title_norm = _normalize_text(title)
    summary_norm = _normalize_text(summary)
    excerpt_norm = _normalize_text(source_excerpt)
    combined_norm = _normalize_text(" ".join(part for part in (title, summary) if part))
    return _AcceptedExtraction(
        input_index=index,
        row=row,
        extraction_id=_require_nonempty_str("extraction_id", row.get("extraction_id")),
        thread_id=_require_nonempty_str("thread_id", row.get("thread_id")),
        segment_id=_require_nonempty_str("segment_id", row.get("segment_id")),
        candidate_id=_require_nonempty_str("candidate_id", row.get("candidate_id")),
        candidate_key=_require_nonempty_str("candidate_key", row.get("candidate_key")),
        canonical_wing=_require_nonempty_str("canonical_wing", row.get("canonical_wing")),
        canonical_room=_require_nonempty_str("canonical_room", row.get("canonical_room")),
        signal_type=signal_type,
        title=title,
        summary=summary,
        source_excerpt=source_excerpt,
        confidence=_optional_float(row.get("confidence")),
        title_norm=title_norm,
        summary_norm=summary_norm,
        excerpt_norm=excerpt_norm,
        combined_norm=combined_norm,
        title_tokens=_tokenize(title_norm),
        summary_tokens=_tokenize(summary_norm),
        excerpt_tokens=_tokenize(excerpt_norm),
        combined_tokens=_tokenize(combined_norm),
    )


def _build_clusters(
    accepted_rows: Iterable[_AcceptedExtraction],
) -> dict[str, list[_Cluster]]:
    clusters_by_candidate: dict[str, list[_Cluster]] = defaultdict(list)
    for row in sorted(accepted_rows, key=_accepted_sort_key):
        candidate_clusters = clusters_by_candidate[row.candidate_id]
        matched_cluster = next(
            (cluster for cluster in candidate_clusters if _cluster_matches(cluster, row)),
            None,
        )
        if matched_cluster is None:
            candidate_clusters.append(
                _Cluster(
                    candidate_id=row.candidate_id,
                    candidate_key=row.candidate_key,
                    canonical_wing=row.canonical_wing,
                    canonical_room=row.canonical_room,
                    rows=[row],
                )
            )
            continue
        matched_cluster.rows.append(row)
    return clusters_by_candidate


def _cluster_matches(cluster: _Cluster, row: _AcceptedExtraction) -> bool:
    if (
        row.candidate_id != cluster.candidate_id
        or row.candidate_key != cluster.candidate_key
        or row.canonical_wing != cluster.canonical_wing
        or row.canonical_room != cluster.canonical_room
    ):
        return False
    return any(_rows_are_duplicates(existing, row) for existing in cluster.rows)


def _rows_are_duplicates(left: _AcceptedExtraction, right: _AcceptedExtraction) -> bool:
    if left.signal_type != right.signal_type:
        return False
    if left.combined_norm and left.combined_norm == right.combined_norm:
        return True
    if left.title_norm and left.title_norm == right.title_norm:
        if left.summary_norm == right.summary_norm or left.excerpt_norm == right.excerpt_norm:
            return True
    if left.summary_norm and left.summary_norm == right.summary_norm:
        if _grounding_overlap(left, right) >= 0.55:
            return True

    grounding_overlap = _grounding_overlap(left, right)
    if grounding_overlap < 0.68:
        return False

    title_overlap = _token_overlap(left.title_tokens, right.title_tokens)
    summary_overlap = _token_overlap(left.summary_tokens, right.summary_tokens)
    combined_overlap = _token_overlap(left.combined_tokens, right.combined_tokens)
    summary_ratio = _similarity_ratio(left.summary_norm, right.summary_norm)
    title_ratio = _similarity_ratio(left.title_norm, right.title_norm)
    combined_ratio = _similarity_ratio(left.combined_norm, right.combined_norm)

    if combined_overlap >= 0.84 or combined_ratio >= 0.88:
        return True
    if summary_overlap >= 0.8 and (title_overlap >= 0.6 or title_ratio >= 0.72):
        return True
    if grounding_overlap >= 0.8 and (summary_ratio >= 0.78 or title_ratio >= 0.82):
        return True
    return False


def _build_cluster_rows(
    *,
    cluster: _Cluster,
    run_id: str,
    atlas_run_id: str,
) -> list[dict[str, Any]]:
    ordered = sorted(cluster.rows, key=_accepted_sort_key)
    anchor = ordered[0]
    representative = min(ordered, key=_representative_sort_key)
    dedupe_key = _build_dedupe_key(cluster=cluster, anchor=anchor)
    accepted_id = _build_reconciled_signal_id(
        "accepted",
        cluster.candidate_key,
        dedupe_key,
        anchor.extraction_id,
    )
    all_extraction_ids = [row.extraction_id for row in ordered]
    cluster_provenance = _cluster_provenance(
        cluster=cluster,
        ordered=ordered,
        anchor=anchor,
        representative=representative,
    )
    rows = [
        guided_contract.build_reconciliation_record(
            run_id=run_id,
            atlas_run_id=atlas_run_id,
            reconciled_signal_id=accepted_id,
            reconciliation_status="accepted",
            candidate_id=cluster.candidate_id,
            candidate_key=cluster.candidate_key,
            source_extraction_ids=all_extraction_ids,
            dedupe_key=dedupe_key,
            duplicate_of=None,
            title=representative.title,
            summary=representative.summary,
            confidence=representative.confidence,
            provenance=cluster_provenance,
        )
    ]
    for duplicate in ordered[1:]:
        rows.append(
            guided_contract.build_reconciliation_record(
                run_id=run_id,
                atlas_run_id=atlas_run_id,
                reconciled_signal_id=_build_reconciled_signal_id(
                    "duplicate",
                    cluster.candidate_key,
                    dedupe_key,
                    duplicate.extraction_id,
                ),
                reconciliation_status="duplicate",
                candidate_id=cluster.candidate_id,
                candidate_key=cluster.candidate_key,
                source_extraction_ids=[duplicate.extraction_id],
                dedupe_key=dedupe_key,
                duplicate_of=accepted_id,
                title=duplicate.title,
                summary=duplicate.summary,
                confidence=duplicate.confidence,
                provenance=_duplicate_provenance(
                    duplicate=duplicate,
                    cluster=cluster,
                    ordered=ordered,
                    anchor=anchor,
                    representative=representative,
                ),
            )
        )
    return rows


def _cluster_provenance(
    *,
    cluster: _Cluster,
    ordered: list[_AcceptedExtraction],
    anchor: _AcceptedExtraction,
    representative: _AcceptedExtraction,
) -> dict[str, Any]:
    return {
        "reconciliation_method": "candidate_grounded_signal_dedupe_v1",
        "candidate_metadata": _candidate_metadata(cluster),
        **_candidate_provenance_fields(cluster),
        "signal_type": representative.signal_type,
        "signal_types": sorted({row.signal_type for row in ordered}),
        "source_record_count": len(ordered),
        "duplicate_source_count": max(0, len(ordered) - 1),
        "anchor_extraction_id": anchor.extraction_id,
        "representative_extraction_id": representative.extraction_id,
        "source_titles": _unique_values(row.title for row in ordered),
        "source_summaries": _unique_values(row.summary for row in ordered),
        "source_excerpts": _unique_values(row.source_excerpt for row in ordered),
        "source_records": [_build_source_record(row) for row in ordered],
    }


def _duplicate_provenance(
    *,
    duplicate: _AcceptedExtraction,
    cluster: _Cluster,
    ordered: list[_AcceptedExtraction],
    anchor: _AcceptedExtraction,
    representative: _AcceptedExtraction,
) -> dict[str, Any]:
    return {
        "reconciliation_method": "candidate_grounded_signal_dedupe_v1",
        "duplicate_reason": "same_candidate_and_grounded_signal",
        "candidate_metadata": _candidate_metadata(cluster),
        **_candidate_provenance_fields(cluster),
        "signal_type": duplicate.signal_type,
        "cluster_source_count": len(ordered),
        "anchor_extraction_id": anchor.extraction_id,
        "representative_extraction_id": representative.extraction_id,
        "canonical_group_extraction_ids": [row.extraction_id for row in ordered],
        "source_records": [_build_source_record(duplicate)],
    }


def _candidate_metadata(cluster: _Cluster) -> dict[str, str]:
    return {
        "candidate_id": cluster.candidate_id,
        "candidate_key": cluster.candidate_key,
        "canonical_wing": cluster.canonical_wing,
        "canonical_room": cluster.canonical_room,
    }


def _candidate_provenance_fields(cluster: _Cluster) -> dict[str, Any]:
    return {
        "candidate_id": cluster.candidate_id,
        "candidate_key": cluster.candidate_key,
        "canonical_wing": cluster.canonical_wing,
        "canonical_room": cluster.canonical_room,
        "atlas_candidate_ids": [cluster.candidate_id],
        "atlas_candidate_keys": [cluster.candidate_key],
    }


def _build_source_record(row: _AcceptedExtraction) -> dict[str, Any]:
    source_record = {
        "signal_type": row.signal_type,
        "title": row.title,
        "summary": row.summary,
        "source_excerpt": row.source_excerpt,
        "confidence": row.confidence,
        "provenance": row.row.get("provenance", {}),
    }
    for field_name in _SOURCE_RECORD_FIELD_NAMES:
        value = row.row.get(field_name)
        if value is not None:
            source_record[field_name] = value
    return source_record


def _build_dedupe_key(*, cluster: _Cluster, anchor: _AcceptedExtraction) -> str:
    return "atlas_dedupe_" + _text_digest(
        "|".join(
            [
                cluster.candidate_key,
                anchor.signal_type,
                anchor.title_norm,
                anchor.summary_norm,
                anchor.excerpt_norm,
            ]
        )
    )


def _build_reconciled_signal_id(
    kind: str,
    candidate_key: str,
    dedupe_key: str,
    extraction_id: str,
) -> str:
    return "atlas_signal_" + _text_digest(
        "|".join([kind, candidate_key, dedupe_key, extraction_id])
    )


def _accepted_sort_key(row: _AcceptedExtraction) -> tuple[Any, ...]:
    return (
        str(row.row.get("logical_source_id") or ""),
        str(row.row.get("source_hash") or ""),
        str(row.row.get("subthread_id") or ""),
        _optional_int(row.row.get("segment_index")),
        _optional_int(row.row.get("message_start_index")),
        _optional_int(row.row.get("char_start")),
        row.thread_id,
        row.segment_id,
        row.extraction_id,
        row.input_index,
    )


def _representative_sort_key(row: _AcceptedExtraction) -> tuple[Any, ...]:
    confidence = -(row.confidence if row.confidence is not None else -1.0)
    richness = -(len(row.title_norm) + len(row.summary_norm) + len(row.excerpt_norm))
    return (confidence, richness, _accepted_sort_key(row))


def _grounding_overlap(left: _AcceptedExtraction, right: _AcceptedExtraction) -> float:
    return max(
        _token_overlap(left.excerpt_tokens, right.excerpt_tokens),
        _similarity_ratio(left.excerpt_norm, right.excerpt_norm),
    )


def _token_overlap(left: tuple[str, ...], right: tuple[str, ...]) -> float:
    left_set = set(left)
    right_set = set(right)
    if not left_set or not right_set:
        return 0.0
    shared = len(left_set & right_set)
    return shared / min(len(left_set), len(right_set))


def _similarity_ratio(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    if left == right:
        return 1.0
    return SequenceMatcher(a=left, b=right).ratio()


def _normalize_text(value: str) -> str:
    return " ".join(part for part in _TOKEN_RE.findall(value.lower()) if part)


def _tokenize(value: str) -> tuple[str, ...]:
    return tuple(
        token
        for token in _TOKEN_RE.findall(value.lower())
        if len(token) > 1 and token not in _GENERIC_TOKENS
    )


def _coerce_text(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"accepted extraction {name} must be a non-empty string")
    return value.strip()


def _coerce_signal_type(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        return "accepted"
    return value.strip().lower()


def _require_nonempty_str(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _resolve_id(name: str, *, requested: str | None, seen: set[str]) -> str:
    if requested is not None:
        requested = _require_nonempty_str(name, requested)
    if not seen:
        if requested is None:
            raise ValueError(f"{name} is required when extraction_rows is empty")
        return requested
    if len(seen) != 1:
        raise ValueError(f"{name} must be consistent across extraction rows")
    resolved = next(iter(seen))
    if requested is not None and requested != resolved:
        raise ValueError(f"{name} does not match extraction_rows")
    return resolved


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("confidence must be numeric or None")
    return float(value)


def _optional_int(value: Any) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return -1


def _text_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def _unique_values(values: Iterable[str]) -> list[str]:
    seen: dict[str, None] = {}
    for value in values:
        if value and value not in seen:
            seen[value] = None
    return list(seen)
