from __future__ import annotations

import json
import math
import re
from pathlib import PurePath
from typing import Any, Iterable, Mapping, Optional, Sequence, Union

SCHEMA_VERSION = "v1"

RUN_PROGRESS_SCHEMA = "chatgpt_atlas_guided.progress.v1"
PROGRESS_SCHEMA = RUN_PROGRESS_SCHEMA
ARTIFACTS_INDEX_SCHEMA = "chatgpt_atlas_guided.artifacts_index.v1"
ARTIFACT_INDEX_RECORD_SCHEMA = "chatgpt_atlas_guided.artifact_index_record.v1"
CANDIDATE_BRIDGE_RECORD_SCHEMA = "chatgpt_atlas_guided.candidate_bridge_record.v1"
THREAD_CANDIDATE_LOOKUP_SCHEMA = "chatgpt_atlas_guided.thread_candidate_lookup.v1"
CANDIDATE_COVERAGE_REPORT_SCHEMA = "chatgpt_atlas_guided.candidate_coverage_report.v1"
EXTRACTION_RECORD_SCHEMA = "chatgpt_atlas_guided.extraction_record.v1"
RECONCILIATION_RECORD_SCHEMA = "chatgpt_atlas_guided.reconciliation_record.v1"
PUBLISH_CHECKPOINT_SCHEMA = "chatgpt_atlas_guided.publish_checkpoint.v1"

ARTIFACT_SCHEMAS = {
    "progress": RUN_PROGRESS_SCHEMA,
    "artifacts_index": ARTIFACTS_INDEX_SCHEMA,
    "candidate_bridge_records": CANDIDATE_BRIDGE_RECORD_SCHEMA,
    "atlas_thread_candidates": THREAD_CANDIDATE_LOOKUP_SCHEMA,
    "atlas_candidate_coverage": CANDIDATE_COVERAGE_REPORT_SCHEMA,
    "extraction_records": EXTRACTION_RECORD_SCHEMA,
    "reconciled_signals": RECONCILIATION_RECORD_SCHEMA,
    "publish_checkpoint": PUBLISH_CHECKPOINT_SCHEMA,
}

CANONICAL_ARTIFACT_PATHS = {
    "progress": "progress.json",
    "artifacts_index": "artifacts_index.json",
    "candidate_bridge_records": "candidate_bridge_records.jsonl",
    "atlas_thread_candidates": "atlas_thread_candidates.jsonl",
    "atlas_candidate_coverage": "atlas_candidate_coverage.json",
    "extraction_records": "extraction_records.jsonl",
    "invalid_outputs": "invalid_outputs.jsonl",
    "reconciled_signals": "reconciled_signals.jsonl",
    "publish_checkpoint": "publish_checkpoint.jsonl",
}

RUN_STATUSES = frozenset({"pending", "running", "complete", "failed"})
PHASE_STATUSES = frozenset({"pending", "running", "complete", "failed", "skipped"})
CANDIDATE_BRIDGE_STATUSES = frozenset({"candidate", "mixed", "noise"})
THREAD_LOOKUP_STATUSES = frozenset({"mapped", "mixed", "noise", "unmapped"})
COVERAGE_STATUSES = frozenset({"complete", "needs_review", "failed"})
EXTRACTION_STATUSES = frozenset(
    {"accepted", "null_signal", "invalid_output", "provider_error", "skipped"}
)
RECONCILIATION_STATUSES = frozenset({"accepted", "duplicate", "rejected", "needs_review"})
PUBLISH_CHECKPOINT_STATUSES = frozenset({"disabled", "pending_review", "approved", "rejected"})
ARTIFACT_CONTENT_TYPES = frozenset({"application/json", "application/jsonl"})
ARTIFACT_PRIVACY_LEVELS = frozenset({"summary", "bounded_excerpt", "model_output", "review_only"})

REQUIRED_KEYS = {
    RUN_PROGRESS_SCHEMA: (
        "schema",
        "run_id",
        "atlas_run_id",
        "status",
        "current_phase",
        "phase_status",
        "phase_order",
        "counts",
        "errors",
        "warnings",
        "no_publish",
        "publish_enabled",
        "safety_contract",
    ),
    ARTIFACTS_INDEX_SCHEMA: (
        "schema",
        "run_id",
        "atlas_run_id",
        "artifacts",
        "artifact_count",
        "no_publish",
        "publish_enabled",
        "safety_contract",
    ),
    ARTIFACT_INDEX_RECORD_SCHEMA: (
        "schema",
        "artifact_key",
        "schema_name",
        "relative_path",
        "phase",
        "content_type",
        "count",
        "append_only",
        "review_safe",
        "dashboard_safe",
        "contains_bounded_excerpts",
        "contains_raw_model_output",
        "publish_gate_required",
        "privacy_level",
    ),
    CANDIDATE_BRIDGE_RECORD_SCHEMA: (
        "schema",
        "run_id",
        "atlas_run_id",
        "candidate_id",
        "candidate_key",
        "canonical_wing",
        "canonical_room",
        "bridge_status",
        "atlas_cluster_id",
        "atlas_cluster_status",
        "topic_label",
        "label",
        "definition",
        "thread_ids",
        "support_thread_count",
        "top_terms",
        "evidence_titles",
        "representative_thread_ids",
        "representative_excerpts",
        "mixed_reasons",
        "safety_contract",
    ),
    THREAD_CANDIDATE_LOOKUP_SCHEMA: (
        "schema",
        "run_id",
        "atlas_run_id",
        "thread_id",
        "lookup_status",
        "candidate_ids",
        "candidate_keys",
        "cluster_ids",
        "primary_candidate_id",
        "primary_candidate_key",
        "reason_codes",
        "source_thread_ref",
        "safety_contract",
    ),
    CANDIDATE_COVERAGE_REPORT_SCHEMA: (
        "schema",
        "run_id",
        "atlas_run_id",
        "status",
        "total_threads",
        "mapped_threads",
        "mixed_threads",
        "noise_threads",
        "unmapped_threads",
        "candidate_count",
        "cluster_count",
        "duplicate_thread_refs",
        "missing_thread_refs",
        "counts",
        "safety_contract",
    ),
    EXTRACTION_RECORD_SCHEMA: (
        "schema",
        "run_id",
        "atlas_run_id",
        "extraction_id",
        "thread_id",
        "segment_id",
        "extraction_status",
        "candidate_id",
        "candidate_key",
        "canonical_wing",
        "canonical_room",
        "signal_type",
        "title",
        "summary",
        "source_excerpt",
        "confidence",
        "provenance",
        "no_publish",
        "publish_enabled",
        "safety_contract",
    ),
    RECONCILIATION_RECORD_SCHEMA: (
        "schema",
        "run_id",
        "atlas_run_id",
        "reconciled_signal_id",
        "reconciliation_status",
        "candidate_id",
        "candidate_key",
        "canonical_wing",
        "canonical_room",
        "source_extraction_ids",
        "dedupe_key",
        "duplicate_of",
        "title",
        "summary",
        "confidence",
        "provenance",
        "no_publish",
        "publish_enabled",
        "safety_contract",
    ),
    PUBLISH_CHECKPOINT_SCHEMA: (
        "schema",
        "run_id",
        "atlas_run_id",
        "checkpoint_id",
        "status",
        "publish_enabled",
        "publish_gate_open",
        "target_wing",
        "record_count",
        "approved_by",
        "approval_ref",
        "notes",
        "safety_contract",
    ),
}

FORBIDDEN_FIELD_NAMES = frozenset(
    {
        "chroma_collection",
        "drawer_write_path",
        "localai",
        "localai_base_url",
        "localai_model",
        "localai_token",
        "mcp",
        "mcp_server",
        "mcp_tool",
        "palace_path",
        "palace_root",
        "palace_write",
        "palace_write_path",
        "write_drawer",
    }
)

_RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$")
_SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_CANONICAL_SLUG_RE = re.compile(r"^[a-z0-9_]{1,96}$")
_CANDIDATE_ID_RE = re.compile(r"^cand_[a-z0-9_]{1,96}__[a-z0-9_]{1,96}(?:_[a-f0-9]{10})?$")
_RECONCILED_ID_RE = re.compile(r"^atlas_signal_[A-Za-z0-9_.:-]{1,128}$")

_BASE_SAFETY_CONTRACT = {
    "artifact_only": True,
    "contract_module_only": True,
    "external_services": [],
    "network_required": False,
    "vector_store_required": False,
    "tool_server_required": False,
    "writes_existing_memory": False,
    "emits_memory_records": False,
    "deletes_source_data": False,
    "publishes_by_default": False,
    "publish_enabled": False,
}

PUBLISH_TARGET_WING = "chatgpt_atlas_signals"


def build_progress(
    *,
    run_id: str,
    atlas_run_id: str,
    status: str,
    current_phase: str,
    phase_status: str,
    phase_order: Sequence[str],
    counts: Optional[Mapping[str, int]] = None,
    errors: int = 0,
    warnings: int = 0,
    started_at: Optional[str] = None,
    updated_at: Optional[str] = None,
    message: Optional[str] = None,
) -> dict[str, Any]:
    row = {
        "schema": RUN_PROGRESS_SCHEMA,
        "run_id": _validate_run_id(run_id),
        "atlas_run_id": _validate_run_id(atlas_run_id),
        "status": _validate_choice("status", status, RUN_STATUSES),
        "current_phase": _validate_slug("current_phase", current_phase),
        "phase_status": _validate_choice("phase_status", phase_status, PHASE_STATUSES),
        "phase_order": [_validate_slug("phase_order", item) for item in phase_order],
        "counts": _normalize_count_map(counts or {}),
        "errors": _validate_nonnegative_int("errors", errors),
        "warnings": _validate_nonnegative_int("warnings", warnings),
        "started_at": _optional_str(started_at),
        "updated_at": _optional_str(updated_at),
        "message": _optional_str(message),
        "no_publish": True,
        "publish_enabled": False,
        "safety_contract": safety_contract(),
    }
    return validate_row(RUN_PROGRESS_SCHEMA, row)


def build_artifact_index_record(
    *,
    artifact_key: str,
    schema_name: str,
    relative_path: Union[str, PurePath],
    phase: str,
    count: int,
    content_type: str,
    append_only: bool,
    review_safe: bool,
    dashboard_safe: bool,
    contains_bounded_excerpts: bool = False,
    contains_raw_model_output: bool = False,
    publish_gate_required: bool = False,
    privacy_level: str = "summary",
) -> dict[str, Any]:
    row = {
        "schema": ARTIFACT_INDEX_RECORD_SCHEMA,
        "artifact_key": _validate_slug("artifact_key", artifact_key),
        "schema_name": _validate_schema_name(schema_name),
        "relative_path": _validate_relative_path(relative_path),
        "phase": _validate_slug("phase", phase),
        "content_type": _validate_choice("content_type", content_type, ARTIFACT_CONTENT_TYPES),
        "count": _validate_nonnegative_int("count", count),
        "append_only": _validate_bool("append_only", append_only),
        "review_safe": _validate_bool("review_safe", review_safe),
        "dashboard_safe": _validate_bool("dashboard_safe", dashboard_safe),
        "contains_bounded_excerpts": _validate_bool(
            "contains_bounded_excerpts", contains_bounded_excerpts
        ),
        "contains_raw_model_output": _validate_bool(
            "contains_raw_model_output", contains_raw_model_output
        ),
        "publish_gate_required": _validate_bool("publish_gate_required", publish_gate_required),
        "privacy_level": _validate_choice("privacy_level", privacy_level, ARTIFACT_PRIVACY_LEVELS),
    }
    return validate_row(ARTIFACT_INDEX_RECORD_SCHEMA, row)


def build_artifacts_index(
    *,
    run_id: str,
    atlas_run_id: str,
    artifacts: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    normalized = [validate_row(ARTIFACT_INDEX_RECORD_SCHEMA, dict(item)) for item in artifacts]
    normalized.sort(key=lambda item: item["artifact_key"])
    row = {
        "schema": ARTIFACTS_INDEX_SCHEMA,
        "run_id": _validate_run_id(run_id),
        "atlas_run_id": _validate_run_id(atlas_run_id),
        "artifacts": normalized,
        "artifact_count": len(normalized),
        "no_publish": True,
        "publish_enabled": False,
        "safety_contract": safety_contract(),
    }
    return validate_row(ARTIFACTS_INDEX_SCHEMA, row)


def build_candidate_record(
    *,
    run_id: str,
    atlas_run_id: str,
    candidate_id: Optional[str] = None,
    candidate_key: Optional[str] = None,
    bridge_status: str,
    atlas_cluster_id: str,
    atlas_cluster_status: str,
    topic_label: Optional[str],
    label: Optional[str],
    definition: Optional[str],
    thread_ids: Sequence[str],
    top_terms: Sequence[Mapping[str, Any]],
    evidence_titles: Optional[Sequence[str]] = None,
    representative_thread_ids: Optional[Sequence[str]] = None,
    representative_excerpts: Optional[Sequence[str]] = None,
    mixed_reasons: Optional[Sequence[str]] = None,
) -> dict[str, Any]:
    normalized_bridge_status = _validate_choice(
        "bridge_status", bridge_status, CANDIDATE_BRIDGE_STATUSES
    )
    normalized_atlas_cluster_status = _validate_choice(
        "atlas_cluster_status", atlas_cluster_status, CANDIDATE_BRIDGE_STATUSES
    )
    if normalized_bridge_status != normalized_atlas_cluster_status:
        raise ValueError("bridge_status must match atlas_cluster_status")
    canonical_wing, canonical_room = _split_optional_candidate_key(candidate_key)
    normalized_thread_ids = _normalize_str_list(thread_ids)
    normalized_candidate_id = _optional_candidate_id(candidate_id)
    if normalized_candidate_id and canonical_wing and canonical_room:
        _validate_candidate_id_matches_key(normalized_candidate_id, canonical_wing, canonical_room)
    row = {
        "schema": CANDIDATE_BRIDGE_RECORD_SCHEMA,
        "run_id": _validate_run_id(run_id),
        "atlas_run_id": _validate_run_id(atlas_run_id),
        "candidate_id": normalized_candidate_id,
        "candidate_key": (
            _build_candidate_key(canonical_wing, canonical_room)
            if canonical_wing is not None and canonical_room is not None
            else None
        ),
        "canonical_wing": canonical_wing,
        "canonical_room": canonical_room,
        "bridge_status": normalized_bridge_status,
        "atlas_cluster_id": _validate_text_id("atlas_cluster_id", atlas_cluster_id),
        "atlas_cluster_status": normalized_atlas_cluster_status,
        "topic_label": _optional_str(topic_label),
        "label": _optional_str(label),
        "definition": _optional_str(definition),
        "thread_ids": normalized_thread_ids,
        "support_thread_count": len(normalized_thread_ids),
        "top_terms": _normalize_term_counts(top_terms),
        "evidence_titles": _normalize_str_list(evidence_titles or []),
        "representative_thread_ids": _normalize_str_list(representative_thread_ids or []),
        "representative_excerpts": _normalize_str_list(representative_excerpts or []),
        "mixed_reasons": _normalize_str_list(mixed_reasons or []),
        "safety_contract": safety_contract(),
    }
    return validate_row(CANDIDATE_BRIDGE_RECORD_SCHEMA, row)


def build_candidate_bridge_record(**kwargs: Any) -> dict[str, Any]:
    return build_candidate_record(**kwargs)


def build_thread_candidate_record(
    *,
    run_id: str,
    atlas_run_id: str,
    thread_id: str,
    lookup_status: str,
    candidate_ids: Optional[Sequence[str]] = None,
    candidate_keys: Optional[Sequence[str]] = None,
    cluster_ids: Optional[Sequence[str]] = None,
    primary_candidate_id: Optional[str] = None,
    primary_candidate_key: Optional[str] = None,
    reason_codes: Optional[Sequence[str]] = None,
    source_thread_ref: Optional[str] = None,
) -> dict[str, Any]:
    row = {
        "schema": THREAD_CANDIDATE_LOOKUP_SCHEMA,
        "run_id": _validate_run_id(run_id),
        "atlas_run_id": _validate_run_id(atlas_run_id),
        "thread_id": _validate_text_id("thread_id", thread_id),
        "lookup_status": _validate_choice("lookup_status", lookup_status, THREAD_LOOKUP_STATUSES),
        "candidate_ids": [_validate_candidate_id(item) for item in (candidate_ids or [])],
        "candidate_keys": [_validate_candidate_key(item) for item in (candidate_keys or [])],
        "cluster_ids": _normalize_str_list(cluster_ids or []),
        "primary_candidate_id": _optional_candidate_id(primary_candidate_id),
        "primary_candidate_key": _optional_candidate_key(primary_candidate_key),
        "reason_codes": [_validate_slug("reason_code", item) for item in (reason_codes or [])],
        "source_thread_ref": _optional_str(source_thread_ref),
        "safety_contract": safety_contract(),
    }
    return validate_row(THREAD_CANDIDATE_LOOKUP_SCHEMA, row)


def build_thread_candidate_lookup_record(**kwargs: Any) -> dict[str, Any]:
    return build_thread_candidate_record(**kwargs)


def build_candidate_coverage_report(
    *,
    run_id: str,
    atlas_run_id: str,
    status: str,
    total_threads: int,
    mapped_threads: int,
    mixed_threads: int,
    noise_threads: int,
    unmapped_threads: int,
    candidate_count: int,
    cluster_count: int,
    duplicate_thread_refs: Optional[Sequence[Mapping[str, Any]]] = None,
    missing_thread_refs: Optional[Sequence[str]] = None,
    counts: Optional[Mapping[str, int]] = None,
) -> dict[str, Any]:
    row = {
        "schema": CANDIDATE_COVERAGE_REPORT_SCHEMA,
        "run_id": _validate_run_id(run_id),
        "atlas_run_id": _validate_run_id(atlas_run_id),
        "status": _validate_choice("status", status, COVERAGE_STATUSES),
        "total_threads": _validate_nonnegative_int("total_threads", total_threads),
        "mapped_threads": _validate_nonnegative_int("mapped_threads", mapped_threads),
        "mixed_threads": _validate_nonnegative_int("mixed_threads", mixed_threads),
        "noise_threads": _validate_nonnegative_int("noise_threads", noise_threads),
        "unmapped_threads": _validate_nonnegative_int("unmapped_threads", unmapped_threads),
        "candidate_count": _validate_nonnegative_int("candidate_count", candidate_count),
        "cluster_count": _validate_nonnegative_int("cluster_count", cluster_count),
        "duplicate_thread_refs": _normalize_duplicate_refs(duplicate_thread_refs or []),
        "missing_thread_refs": _normalize_str_list(missing_thread_refs or []),
        "counts": _normalize_count_map(counts or {}),
        "safety_contract": safety_contract(),
    }
    return validate_row(CANDIDATE_COVERAGE_REPORT_SCHEMA, row)


def build_extraction_record(
    *,
    run_id: str,
    atlas_run_id: str,
    extraction_id: str,
    thread_id: str,
    segment_id: str,
    extraction_status: str,
    candidate_id: Optional[str] = None,
    candidate_key: Optional[str] = None,
    signal_type: Optional[str] = None,
    title: Optional[str] = None,
    summary: Optional[str] = None,
    source_excerpt: Optional[str] = None,
    confidence: Optional[float] = None,
    provenance: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    canonical_wing, canonical_room = _split_optional_candidate_key(candidate_key)
    normalized_candidate_id = _optional_candidate_id(candidate_id)
    if normalized_candidate_id and canonical_wing and canonical_room:
        _validate_candidate_id_matches_key(normalized_candidate_id, canonical_wing, canonical_room)
    row = {
        "schema": EXTRACTION_RECORD_SCHEMA,
        "run_id": _validate_run_id(run_id),
        "atlas_run_id": _validate_run_id(atlas_run_id),
        "extraction_id": _validate_text_id("extraction_id", extraction_id),
        "thread_id": _validate_text_id("thread_id", thread_id),
        "segment_id": _validate_text_id("segment_id", segment_id),
        "extraction_status": _validate_choice(
            "extraction_status", extraction_status, EXTRACTION_STATUSES
        ),
        "candidate_id": normalized_candidate_id,
        "candidate_key": _optional_candidate_key(candidate_key),
        "canonical_wing": canonical_wing,
        "canonical_room": canonical_room,
        "signal_type": _optional_str(signal_type),
        "title": _optional_str(title),
        "summary": _optional_str(summary),
        "source_excerpt": _optional_str(source_excerpt),
        "confidence": _optional_confidence(confidence),
        "provenance": _normalize_provenance(provenance or {}),
        "no_publish": True,
        "publish_enabled": False,
        "safety_contract": safety_contract(),
    }
    return validate_row(EXTRACTION_RECORD_SCHEMA, row)


def build_reconciliation_record(
    *,
    run_id: str,
    atlas_run_id: str,
    reconciled_signal_id: str,
    reconciliation_status: str,
    candidate_id: str,
    candidate_key: str,
    source_extraction_ids: Sequence[str],
    dedupe_key: str,
    title: Optional[str],
    summary: Optional[str],
    confidence: Optional[float] = None,
    duplicate_of: Optional[str] = None,
    provenance: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    canonical_wing, canonical_room = _split_candidate_key(candidate_key)
    normalized_candidate_id = _validate_candidate_id(candidate_id)
    _validate_candidate_id_matches_key(normalized_candidate_id, canonical_wing, canonical_room)
    row = {
        "schema": RECONCILIATION_RECORD_SCHEMA,
        "run_id": _validate_run_id(run_id),
        "atlas_run_id": _validate_run_id(atlas_run_id),
        "reconciled_signal_id": _validate_reconciled_signal_id(reconciled_signal_id),
        "reconciliation_status": _validate_choice(
            "reconciliation_status", reconciliation_status, RECONCILIATION_STATUSES
        ),
        "candidate_id": normalized_candidate_id,
        "candidate_key": _build_candidate_key(canonical_wing, canonical_room),
        "canonical_wing": canonical_wing,
        "canonical_room": canonical_room,
        "source_extraction_ids": _normalize_nonempty_str_list(
            "source_extraction_ids", source_extraction_ids
        ),
        "dedupe_key": _validate_text_id("dedupe_key", dedupe_key),
        "duplicate_of": _optional_str(duplicate_of),
        "title": _optional_str(title),
        "summary": _optional_str(summary),
        "confidence": _optional_confidence(confidence),
        "provenance": _normalize_provenance(provenance or {}),
        "no_publish": True,
        "publish_enabled": False,
        "safety_contract": safety_contract(),
    }
    return validate_row(RECONCILIATION_RECORD_SCHEMA, row)


def build_publish_checkpoint(
    *,
    run_id: str,
    atlas_run_id: str,
    checkpoint_id: str,
    status: str = "disabled",
    publish_enabled: bool = False,
    publish_gate_open: bool = False,
    target_wing: Optional[str] = None,
    record_count: int = 0,
    approved_by: Optional[str] = None,
    approval_ref: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict[str, Any]:
    normalized_status = _validate_choice("status", status, PUBLISH_CHECKPOINT_STATUSES)
    normalized_publish_enabled = _validate_bool("publish_enabled", publish_enabled)
    normalized_publish_gate_open = _validate_bool("publish_gate_open", publish_gate_open)
    normalized_record_count = _validate_nonnegative_int("record_count", record_count)
    normalized_approved_by = _optional_str(approved_by)
    normalized_approval_ref = _optional_str(approval_ref)
    normalized_target_wing = _optional_str(target_wing)
    checkpoint_safety_contract = safety_contract()
    checkpoint_safety_contract["publish_enabled"] = normalized_publish_enabled
    row = {
        "schema": PUBLISH_CHECKPOINT_SCHEMA,
        "run_id": _validate_run_id(run_id),
        "atlas_run_id": _validate_run_id(atlas_run_id),
        "checkpoint_id": _validate_text_id("checkpoint_id", checkpoint_id),
        "status": normalized_status,
        "publish_enabled": normalized_publish_enabled,
        "publish_gate_open": normalized_publish_gate_open,
        "target_wing": normalized_target_wing,
        "record_count": normalized_record_count,
        "approved_by": normalized_approved_by,
        "approval_ref": normalized_approval_ref,
        "notes": _optional_str(notes),
        "safety_contract": checkpoint_safety_contract,
    }
    return validate_row(PUBLISH_CHECKPOINT_SCHEMA, row)


def canonical_artifact_records(counts: Optional[Mapping[str, int]] = None) -> list[dict[str, Any]]:
    counts = counts or {}
    specs = [
        ("progress", RUN_PROGRESS_SCHEMA, "run", "application/json", False, True, True, False, False, False, "summary"),
        (
            "candidate_bridge_records",
            CANDIDATE_BRIDGE_RECORD_SCHEMA,
            "bridge",
            "application/jsonl",
            True,
            True,
            True,
            True,
            False,
            False,
            "bounded_excerpt",
        ),
        (
            "atlas_thread_candidates",
            THREAD_CANDIDATE_LOOKUP_SCHEMA,
            "coverage",
            "application/jsonl",
            True,
            True,
            True,
            False,
            False,
            False,
            "summary",
        ),
        (
            "atlas_candidate_coverage",
            CANDIDATE_COVERAGE_REPORT_SCHEMA,
            "coverage",
            "application/json",
            False,
            True,
            True,
            False,
            False,
            False,
            "summary",
        ),
        (
            "extraction_records",
            EXTRACTION_RECORD_SCHEMA,
            "extraction",
            "application/jsonl",
            True,
            True,
            False,
            True,
            True,
            False,
            "model_output",
        ),
        (
            "invalid_outputs",
            EXTRACTION_RECORD_SCHEMA,
            "extraction",
            "application/jsonl",
            True,
            True,
            False,
            True,
            True,
            False,
            "model_output",
        ),
        (
            "reconciled_signals",
            RECONCILIATION_RECORD_SCHEMA,
            "reconciliation",
            "application/jsonl",
            True,
            True,
            True,
            True,
            False,
            False,
            "bounded_excerpt",
        ),
        (
            "publish_checkpoint",
            PUBLISH_CHECKPOINT_SCHEMA,
            "publish_gate",
            "application/jsonl",
            True,
            True,
            True,
            False,
            False,
            True,
            "review_only",
        ),
        ("artifacts_index", ARTIFACTS_INDEX_SCHEMA, "run", "application/json", False, True, True, False, False, False, "summary"),
    ]
    return [
        build_artifact_index_record(
            artifact_key=artifact_key,
            schema_name=schema_name,
            relative_path=CANONICAL_ARTIFACT_PATHS[artifact_key],
            phase=phase,
            content_type=content_type,
            count=counts.get(artifact_key, 0),
            append_only=append_only,
            review_safe=review_safe,
            dashboard_safe=dashboard_safe,
            contains_bounded_excerpts=contains_bounded_excerpts,
            contains_raw_model_output=contains_raw_model_output,
            publish_gate_required=publish_gate_required,
            privacy_level=privacy_level,
        )
        for (
            artifact_key,
            schema_name,
            phase,
            content_type,
            append_only,
            review_safe,
            dashboard_safe,
            contains_bounded_excerpts,
            contains_raw_model_output,
            publish_gate_required,
            privacy_level,
        ) in specs
    ]


def safety_contract() -> dict[str, Any]:
    payload = json.loads(json.dumps(_BASE_SAFETY_CONTRACT, sort_keys=True))
    return payload


def canonical_json_line(row: Mapping[str, Any]) -> str:
    validate_json_safe(row)
    _reject_forbidden_fields(row)
    return json.dumps(row, ensure_ascii=True, separators=(",", ":"), sort_keys=True) + "\n"


def validate_row(schema_name: str, row: Mapping[str, Any]) -> dict[str, Any]:
    schema = _validate_schema_name(schema_name)
    if row.get("schema") != schema:
        raise ValueError(f"row schema must be {schema!r}")
    missing = [key for key in REQUIRED_KEYS.get(schema, ()) if key not in row]
    if missing:
        raise ValueError(f"{schema} missing required keys: {', '.join(missing)}")
    validate_json_safe(row)
    _reject_forbidden_fields(row)
    _validate_schema_shape(schema, row)
    return dict(row)


def validate_json_safe(value: Any, *, path: str = "$") -> None:
    if value is None or isinstance(value, (str, bool)):
        return
    if isinstance(value, int) and not isinstance(value, bool):
        return
    if isinstance(value, float):
        if math.isfinite(value):
            return
        raise ValueError(f"{path} is not a finite JSON number")
    if isinstance(value, list):
        for index, item in enumerate(value):
            validate_json_safe(item, path=f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{path} contains a non-string key")
            validate_json_safe(item, path=f"{path}.{key}")
        return
    raise ValueError(f"{path} is not JSON-safe: {type(value).__name__}")


def _validate_schema_shape(schema: str, row: Mapping[str, Any]) -> None:
    if schema == RUN_PROGRESS_SCHEMA:
        _validate_run_id(row["run_id"])
        _validate_run_id(row["atlas_run_id"])
        _validate_choice("status", row["status"], RUN_STATUSES)
        _validate_choice("phase_status", row["phase_status"], PHASE_STATUSES)
        _require_no_publish(row)
    elif schema == ARTIFACTS_INDEX_SCHEMA:
        _require_no_publish(row)
        for item in row["artifacts"]:
            validate_row(ARTIFACT_INDEX_RECORD_SCHEMA, item)
        if row["artifact_count"] != len(row["artifacts"]):
            raise ValueError("artifact_count must match artifacts length")
    elif schema == ARTIFACT_INDEX_RECORD_SCHEMA:
        _validate_artifact_index_record_shape(row)
    elif schema == CANDIDATE_BRIDGE_RECORD_SCHEMA:
        _validate_candidate_bridge_shape(row)
    elif schema == THREAD_CANDIDATE_LOOKUP_SCHEMA:
        _validate_thread_candidate_lookup_shape(row)
    elif schema == CANDIDATE_COVERAGE_REPORT_SCHEMA:
        _validate_candidate_coverage_shape(row)
    elif schema == EXTRACTION_RECORD_SCHEMA:
        _validate_extraction_shape(row)
    elif schema == RECONCILIATION_RECORD_SCHEMA:
        _validate_reconciliation_shape(row)
    elif schema == PUBLISH_CHECKPOINT_SCHEMA:
        _validate_publish_checkpoint_shape(row)


def _validate_artifact_index_record_shape(row: Mapping[str, Any]) -> None:
    _validate_schema_name(row["schema_name"])
    _validate_relative_path(row["relative_path"])
    _validate_choice("content_type", row["content_type"], ARTIFACT_CONTENT_TYPES)
    _validate_choice("privacy_level", row["privacy_level"], ARTIFACT_PRIVACY_LEVELS)
    for key in (
        "append_only",
        "review_safe",
        "dashboard_safe",
        "contains_bounded_excerpts",
        "contains_raw_model_output",
        "publish_gate_required",
    ):
        _validate_bool(key, row[key])
    _validate_nonnegative_int("count", row["count"])
    if row["contains_raw_model_output"] and row["dashboard_safe"]:
        raise ValueError("raw model output artifacts must not be dashboard_safe")
    if row["publish_gate_required"] and row["privacy_level"] != "review_only":
        raise ValueError("publish gate artifacts must use review_only privacy")


def _validate_candidate_bridge_shape(row: Mapping[str, Any]) -> None:
    bridge_status = _validate_choice(
        "bridge_status", row["bridge_status"], CANDIDATE_BRIDGE_STATUSES
    )
    atlas_cluster_status = _validate_choice(
        "atlas_cluster_status", row["atlas_cluster_status"], CANDIDATE_BRIDGE_STATUSES
    )
    if bridge_status != atlas_cluster_status:
        raise ValueError("bridge_status must match atlas_cluster_status")
    candidate_id = _optional_candidate_id(row["candidate_id"])
    candidate_key = _optional_candidate_key(row["candidate_key"])
    canonical_wing, canonical_room = _split_optional_candidate_key(candidate_key)
    if bridge_status == "noise":
        if any(
            row.get(key) is not None
            for key in ("candidate_id", "candidate_key", "canonical_wing", "canonical_room")
        ):
            raise ValueError("noise candidate bridge records must not set candidate identity")
    elif bridge_status == "candidate":
        if not candidate_id or not candidate_key:
            raise ValueError("candidate bridge records require candidate identity")
    elif (candidate_id is None) != (candidate_key is None):
        raise ValueError("mixed candidate bridge records require complete candidate identity")
    if candidate_key is None:
        if row["canonical_wing"] is not None or row["canonical_room"] is not None:
            raise ValueError("canonical fields require candidate_key")
    else:
        if row["canonical_wing"] != canonical_wing or row["canonical_room"] != canonical_room:
            raise ValueError("canonical wing/room must match candidate_key")
        if candidate_id is None:
            raise ValueError("candidate_key requires candidate_id")
        _validate_candidate_id_matches_key(candidate_id, canonical_wing, canonical_room)
    if row["support_thread_count"] != len(row["thread_ids"]):
        raise ValueError("support_thread_count must match thread_ids length")
    _normalize_term_counts(row["top_terms"])


def _validate_thread_candidate_lookup_shape(row: Mapping[str, Any]) -> None:
    _validate_choice("lookup_status", row["lookup_status"], THREAD_LOOKUP_STATUSES)
    candidate_ids = [_validate_candidate_id(item) for item in row["candidate_ids"]]
    candidate_keys = [_validate_candidate_key(item) for item in row["candidate_keys"]]
    if len(candidate_ids) != len(candidate_keys):
        raise ValueError("candidate_ids and candidate_keys must have the same length")
    if row["lookup_status"] == "mapped" and not candidate_ids:
        raise ValueError("mapped thread lookups require at least one candidate")
    if row["lookup_status"] in {"noise", "unmapped"} and candidate_ids:
        raise ValueError("noise and unmapped thread lookups must not include candidates")
    if row["primary_candidate_id"] is not None:
        primary_id = _validate_candidate_id(row["primary_candidate_id"])
        primary_key = _validate_candidate_key(row["primary_candidate_key"])
        if primary_id not in candidate_ids or primary_key not in candidate_keys:
            raise ValueError("primary candidate must be included in candidate_ids/candidate_keys")
    elif row["primary_candidate_key"] is not None:
        raise ValueError("primary_candidate_key requires primary_candidate_id")


def _validate_candidate_coverage_shape(row: Mapping[str, Any]) -> None:
    _validate_choice("status", row["status"], COVERAGE_STATUSES)
    total = _validate_nonnegative_int("total_threads", row["total_threads"])
    covered = sum(
        _validate_nonnegative_int(name, row[name])
        for name in ("mapped_threads", "mixed_threads", "noise_threads", "unmapped_threads")
    )
    if covered != total:
        raise ValueError("thread coverage counts must sum to total_threads")
    _validate_nonnegative_int("candidate_count", row["candidate_count"])
    _validate_nonnegative_int("cluster_count", row["cluster_count"])


def _validate_extraction_shape(row: Mapping[str, Any]) -> None:
    _require_no_publish(row)
    status = _validate_choice("extraction_status", row["extraction_status"], EXTRACTION_STATUSES)
    candidate_id = _optional_candidate_id(row["candidate_id"])
    candidate_key = _optional_candidate_key(row["candidate_key"])
    if status == "accepted":
        if not candidate_id or not candidate_key:
            raise ValueError("accepted extraction records require candidate_id and candidate_key")
        canonical_wing, canonical_room = _split_candidate_key(candidate_key)
        if row["canonical_wing"] != canonical_wing or row["canonical_room"] != canonical_room:
            raise ValueError("accepted extraction canonical fields must match candidate_key")
        _validate_candidate_id_matches_key(candidate_id, canonical_wing, canonical_room)
    elif any(row.get(key) is not None for key in ("canonical_wing", "canonical_room")):
        raise ValueError("non-accepted extraction records must not set canonical wing/room")
    _optional_confidence(row["confidence"])
    _normalize_provenance(row["provenance"])


def _validate_reconciliation_shape(row: Mapping[str, Any]) -> None:
    _require_no_publish(row)
    _validate_choice("reconciliation_status", row["reconciliation_status"], RECONCILIATION_STATUSES)
    canonical_wing, canonical_room = _split_candidate_key(row["candidate_key"])
    if row["canonical_wing"] != canonical_wing or row["canonical_room"] != canonical_room:
        raise ValueError("reconciliation canonical fields must match candidate_key")
    _validate_candidate_id_matches_key(row["candidate_id"], canonical_wing, canonical_room)
    _normalize_nonempty_str_list("source_extraction_ids", row["source_extraction_ids"])
    _validate_reconciled_signal_id(row["reconciled_signal_id"])
    _optional_confidence(row["confidence"])
    if row["reconciliation_status"] == "duplicate" and not row["duplicate_of"]:
        raise ValueError("duplicate reconciliation records require duplicate_of")


def _validate_publish_checkpoint_shape(row: Mapping[str, Any]) -> None:
    status = _validate_choice("status", row["status"], PUBLISH_CHECKPOINT_STATUSES)
    publish_enabled = _validate_bool("publish_enabled", row["publish_enabled"])
    publish_gate_open = _validate_bool("publish_gate_open", row["publish_gate_open"])
    record_count = _validate_nonnegative_int("record_count", row["record_count"])
    target_wing = _optional_str(row["target_wing"])
    approved_by = _optional_str(row["approved_by"])
    approval_ref = _optional_str(row["approval_ref"])
    open_publish_gate = publish_enabled or publish_gate_open or target_wing is not None
    if open_publish_gate:
        if status != "approved" or not publish_enabled or not publish_gate_open:
            raise ValueError("publish checkpoints may open only with approved status")
        if target_wing != PUBLISH_TARGET_WING:
            raise ValueError(f"publish checkpoints may target only {PUBLISH_TARGET_WING}")
        if record_count <= 0:
            raise ValueError("approved publish checkpoints require positive record_count")
        if not approved_by or not approval_ref:
            raise ValueError("approved publish checkpoints require approval fields")
    elif status != "disabled":
        raise ValueError("non-open publish checkpoints must stay disabled")
    elif record_count != 0 or approved_by is not None or approval_ref is not None:
        raise ValueError("disabled publish checkpoints must not carry approval evidence")
    safety = row.get("safety_contract")
    if not isinstance(safety, Mapping) or safety.get("publish_enabled") is not publish_enabled:
        raise ValueError("publish checkpoint safety_contract must match publish_enabled")
    if safety.get("publishes_by_default") is not False:
        raise ValueError("publish checkpoint safety_contract must not publish by default")
    if safety.get("writes_existing_memory") is not False or safety.get("emits_memory_records") is not False:
        raise ValueError("publish checkpoint safety_contract must not write memory records")


def _require_no_publish(row: Mapping[str, Any]) -> None:
    if row.get("no_publish") is not True:
        raise ValueError("artifact row must default to no_publish=True")
    if row.get("publish_enabled") is not False:
        raise ValueError("artifact row must default to publish_enabled=False")
    safety = row.get("safety_contract")
    if not isinstance(safety, Mapping) or safety.get("publish_enabled") is not False:
        raise ValueError("safety_contract must keep publish_enabled=False")
    if safety.get("writes_existing_memory") is not False or safety.get("emits_memory_records") is not False:
        raise ValueError("safety_contract must forbid memory writes")


def _validate_run_id(run_id: str) -> str:
    if not isinstance(run_id, str) or not _RUN_ID_RE.match(run_id) or run_id in {".", ".."}:
        raise ValueError("run_id must be a relative slug with no path separators")
    if "/" in run_id or "\\" in run_id:
        raise ValueError("run_id must not contain path separators")
    return run_id


def _validate_schema_name(schema_name: str) -> str:
    if not isinstance(schema_name, str) or schema_name not in REQUIRED_KEYS:
        raise ValueError(f"unknown schema name: {schema_name!r}")
    return schema_name


def _validate_slug(name: str, value: str) -> str:
    if not isinstance(value, str) or not _SLUG_RE.match(value) or value in {".", ".."}:
        raise ValueError(f"{name} must be a non-empty slug")
    return value


def _validate_text_id(name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    if "/" in value or "\\" in value:
        raise ValueError(f"{name} must not contain path separators")
    return value


def _validate_relative_path(path: Union[str, PurePath]) -> str:
    if isinstance(path, PurePath):
        raw = path.as_posix()
    elif isinstance(path, str):
        raw = path.replace("\\", "/")
    else:
        raise ValueError("relative_path must be a string path")
    if not raw or raw.startswith("/") or raw in {".", ".."}:
        raise ValueError("relative_path must be relative")
    if ":" in raw.split("/")[0]:
        raise ValueError("relative_path must not include a drive or scheme")
    if any(part in {"", ".", ".."} for part in raw.split("/")):
        raise ValueError("relative_path must not contain empty, dot, or parent segments")
    return raw


def _validate_choice(name: str, value: str, allowed: Iterable[str]) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise ValueError(f"{name} must be one of: {', '.join(sorted(allowed))}")
    return value


def _validate_nonnegative_int(name: str, value: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _validate_bool(name: str, value: bool) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a bool")
    return value


def _optional_str(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("expected string or None")
    return value


def _optional_confidence(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        raise ValueError("confidence must be a finite number or None")
    if value < 0 or value > 1:
        raise ValueError("confidence must be between 0 and 1")
    return round(float(value), 4)


def _validate_candidate_id(value: str) -> str:
    if not isinstance(value, str) or not _CANDIDATE_ID_RE.match(value):
        raise ValueError("candidate_id must look like cand_<wing>__<room>")
    return value


def _optional_candidate_id(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    return _validate_candidate_id(value)


def _validate_candidate_key(value: str) -> str:
    _split_candidate_key(value)
    return value


def _optional_candidate_key(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    return _validate_candidate_key(value)


def _split_candidate_key(candidate_key: str) -> tuple[str, str]:
    if not isinstance(candidate_key, str) or candidate_key.count(":") != 1:
        raise ValueError("candidate_key must be canonical_wing:canonical_room")
    canonical_wing, canonical_room = candidate_key.split(":", 1)
    if not _CANONICAL_SLUG_RE.match(canonical_wing):
        raise ValueError("canonical_wing must be a lowercase slug")
    if not _CANONICAL_SLUG_RE.match(canonical_room):
        raise ValueError("canonical_room must be a lowercase slug")
    return canonical_wing, canonical_room


def _split_optional_candidate_key(candidate_key: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    if candidate_key is None:
        return None, None
    return _split_candidate_key(candidate_key)


def _build_candidate_key(canonical_wing: str, canonical_room: str) -> str:
    if not _CANONICAL_SLUG_RE.match(canonical_wing):
        raise ValueError("canonical_wing must be a lowercase slug")
    if not _CANONICAL_SLUG_RE.match(canonical_room):
        raise ValueError("canonical_room must be a lowercase slug")
    return f"{canonical_wing}:{canonical_room}"


def _validate_candidate_id_matches_key(
    candidate_id: str, canonical_wing: str, canonical_room: str
) -> None:
    expected_prefix = f"cand_{canonical_wing}__{canonical_room}"
    if candidate_id != expected_prefix and not candidate_id.startswith(f"{expected_prefix}_"):
        raise ValueError("candidate_id must match candidate_key wing and room")


def _validate_reconciled_signal_id(value: str) -> str:
    if not isinstance(value, str) or not _RECONCILED_ID_RE.match(value):
        raise ValueError("reconciled_signal_id must start with atlas_signal_")
    return value


def _normalize_str_list(values: Sequence[str]) -> list[str]:
    result = []
    for value in values:
        if not isinstance(value, str):
            raise ValueError("expected a sequence of strings")
        result.append(value)
    return result


def _normalize_nonempty_str_list(name: str, values: Sequence[str]) -> list[str]:
    result = _normalize_str_list(values)
    if not result:
        raise ValueError(f"{name} must not be empty")
    return result


def _normalize_count_map(values: Mapping[str, int]) -> dict[str, int]:
    result = {}
    for key in sorted(values):
        if not isinstance(key, str) or not key:
            raise ValueError("count keys must be non-empty strings")
        result[key] = _validate_nonnegative_int(f"counts.{key}", values[key])
    return result


def _normalize_term_counts(values: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for item in values:
        term = item.get("term")
        if not isinstance(term, str) or not term:
            raise ValueError("term count entries require a non-empty term")
        result.append(
            {
                "term": term,
                "count": _validate_nonnegative_int("term.count", item.get("count")),
            }
        )
    return result


def _normalize_duplicate_refs(values: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for item in values:
        thread_id = _validate_text_id("duplicate_thread_ref.thread_id", item.get("thread_id"))
        cluster_ids = _normalize_nonempty_str_list(
            "duplicate_thread_ref.cluster_ids", item.get("cluster_ids", [])
        )
        result.append({"thread_id": thread_id, "cluster_ids": cluster_ids})
    return result


def _normalize_provenance(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("provenance must be a mapping")
    normalized: dict[str, Any] = {}
    for key, item in value.items():
        if key in {"candidate_ids", "atlas_candidate_ids"}:
            normalized[key] = [_validate_candidate_id(candidate_id) for candidate_id in item]
        elif key in {"candidate_keys", "atlas_candidate_keys"}:
            normalized[key] = [_validate_candidate_key(candidate_key) for candidate_key in item]
        elif key in {"cluster_ids", "atlas_cluster_ids", "extraction_ids", "thread_ids"}:
            normalized[key] = _normalize_str_list(item)
        elif key.endswith("_ref") or key.endswith("_refs"):
            normalized[key] = item
        else:
            normalized[key] = item
    validate_json_safe(normalized)
    _reject_forbidden_fields(normalized)
    return normalized


def _reject_forbidden_fields(value: Any, *, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized_key = key.lower()
            if (
                normalized_key in FORBIDDEN_FIELD_NAMES
                or "localai" in normalized_key
                or normalized_key == "mcp"
                or normalized_key.startswith("mcp_")
                or "chroma" in normalized_key
                or "palace_write" in normalized_key
                or "drawer_write" in normalized_key
            ):
                raise ValueError(f"{path}.{key} is forbidden by the atlas-guided no-write contract")
            _reject_forbidden_fields(item, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_forbidden_fields(item, path=f"{path}[{index}]")
