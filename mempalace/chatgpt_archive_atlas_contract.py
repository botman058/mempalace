from __future__ import annotations

import json
import math
import re
from pathlib import PurePath
from typing import Any, Iterable, Mapping, Optional, Sequence, Union

SCHEMA_VERSION = "v1"

PROGRESS_SCHEMA = "chatgpt_archive_atlas.progress.v1"
ARTIFACTS_INDEX_SCHEMA = "chatgpt_archive_atlas.artifacts_index.v1"
ARTIFACT_INDEX_RECORD_SCHEMA = "chatgpt_archive_atlas.artifact_index_record.v1"
CONVERSATION_INDEX_SCHEMA = "chatgpt_archive_atlas.conversation_index.v1"
THREAD_INDEX_SCHEMA = "chatgpt_archive_atlas.thread_index.v1"
LEXICAL_SKETCH_SCHEMA = "chatgpt_archive_atlas.lexical_sketch.v1"
THREAD_EMBEDDING_METADATA_SCHEMA = "chatgpt_archive_atlas.thread_embedding_metadata.v1"
TOPIC_CLUSTER_SCHEMA = "chatgpt_archive_atlas.topic_cluster.v1"
ATLAS_SUMMARY_MANIFEST_SCHEMA = "chatgpt_archive_atlas.atlas_summary_manifest.v1"

ARTIFACT_SCHEMAS = {
    "progress": PROGRESS_SCHEMA,
    "artifacts_index": ARTIFACTS_INDEX_SCHEMA,
    "conversation_index": CONVERSATION_INDEX_SCHEMA,
    "thread_index": THREAD_INDEX_SCHEMA,
    "lexical_sketches": LEXICAL_SKETCH_SCHEMA,
    "thread_embeddings": THREAD_EMBEDDING_METADATA_SCHEMA,
    "topic_clusters": TOPIC_CLUSTER_SCHEMA,
    "atlas_summary": ATLAS_SUMMARY_MANIFEST_SCHEMA,
}

CANONICAL_ARTIFACT_PATHS = {
    "progress": "progress.json",
    "artifacts_index": "artifacts_index.json",
    "conversation_index": "conversation_index.jsonl",
    "thread_index": "thread_index.jsonl",
    "lexical_sketches": "lexical_sketches.jsonl",
    "thread_embeddings": "thread_embeddings.jsonl",
    "topic_clusters": "topic_clusters.jsonl",
    "atlas_summary": "atlas_summary.md",
}

PROGRESS_STATUSES = frozenset({"pending", "running", "complete", "failed"})
EMBEDDING_STATUSES = frozenset({"pending", "embedded", "skipped", "failed"})
TOPIC_CLUSTER_STATUSES = frozenset({"candidate", "mixed", "noise"})
SUMMARY_STATUSES = frozenset({"draft", "complete", "failed"})
ARTIFACT_CONTENT_TYPES = frozenset({"application/json", "application/jsonl", "text/markdown"})

FORBIDDEN_FIELD_NAMES = frozenset(
    {
        "chroma_collection",
        "drawer_id",
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
        "publish_checkpoint",
    }
)

_RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")
_SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")

_SAFETY_CONTRACT = {
    "pre_llm_only": True,
    "artifact_only": True,
    "external_services": [],
    "target_stores": ["atlas_run_directory"],
    "writes_existing_memory": False,
    "emits_memory_records": False,
    "deletes_source_data": False,
}

REQUIRED_KEYS = {
    PROGRESS_SCHEMA: (
        "schema",
        "run_id",
        "phase",
        "status",
        "counts",
        "errors",
        "warnings",
        "safety_contract",
    ),
    ARTIFACTS_INDEX_SCHEMA: (
        "schema",
        "run_id",
        "artifacts",
        "artifact_count",
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
    ),
    CONVERSATION_INDEX_SCHEMA: (
        "schema",
        "run_id",
        "logical_source_id",
        "conversation_id",
        "title",
        "source_relative_path",
        "source_hash",
        "source_ordinal",
        "create_time",
        "update_time",
        "model_slug",
        "plugin_ids",
        "message_count",
        "user_message_count",
        "assistant_message_count",
        "char_count",
        "first_user_excerpt",
        "top_user_prompt_excerpts",
        "safety_contract",
    ),
    THREAD_INDEX_SCHEMA: (
        "schema",
        "run_id",
        "thread_id",
        "logical_source_id",
        "conversation_id",
        "conversation_title",
        "source_hash",
        "thread_index",
        "message_start_index",
        "message_end_index",
        "char_start",
        "char_end",
        "user_message_count",
        "assistant_message_count",
        "char_count",
        "title_hint",
        "representative_excerpt",
        "safety_contract",
    ),
    LEXICAL_SKETCH_SCHEMA: (
        "schema",
        "run_id",
        "thread_id",
        "logical_source_id",
        "top_terms",
        "keyphrases",
        "domains",
        "paths",
        "commands",
        "package_names",
        "model_names",
        "legal_citations",
        "capitalized_phrases",
        "representative_excerpts",
        "noise_terms_rejected",
        "policy_version",
        "safety_contract",
    ),
    THREAD_EMBEDDING_METADATA_SCHEMA: (
        "schema",
        "run_id",
        "thread_id",
        "embedding_id",
        "embedding_model",
        "effective_device",
        "vector_dimensions",
        "source_text_sha256",
        "source_text_chars",
        "batch_index",
        "status",
        "error_code",
        "safety_contract",
    ),
    TOPIC_CLUSTER_SCHEMA: (
        "schema",
        "run_id",
        "cluster_id",
        "status",
        "topic_label",
        "thread_ids",
        "size",
        "top_terms",
        "evidence_titles",
        "representative_thread_ids",
        "representative_excerpts",
        "mixed_reasons",
        "safety_contract",
    ),
    ATLAS_SUMMARY_MANIFEST_SCHEMA: (
        "schema",
        "run_id",
        "relative_path",
        "status",
        "source_schema_names",
        "sections",
        "counts",
        "safety_contract",
    ),
}


def build_progress(
    *,
    run_id: str,
    phase: str,
    status: str,
    counts: Optional[Mapping[str, int]] = None,
    errors: int = 0,
    warnings: int = 0,
    started_at: Optional[str] = None,
    updated_at: Optional[str] = None,
    message: Optional[str] = None,
) -> dict[str, Any]:
    row = {
        "schema": PROGRESS_SCHEMA,
        "run_id": _validate_run_id(run_id),
        "phase": _validate_slug("phase", phase),
        "status": _validate_choice("status", status, PROGRESS_STATUSES),
        "counts": _normalize_count_map(counts or {}),
        "errors": _validate_nonnegative_int("errors", errors),
        "warnings": _validate_nonnegative_int("warnings", warnings),
        "started_at": _optional_str(started_at),
        "updated_at": _optional_str(updated_at),
        "message": _optional_str(message),
        "safety_contract": safety_contract(),
    }
    return validate_row(PROGRESS_SCHEMA, row)


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
    }
    return validate_row(ARTIFACT_INDEX_RECORD_SCHEMA, row)


def build_artifacts_index(
    *,
    run_id: str,
    artifacts: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    normalized = [validate_row(ARTIFACT_INDEX_RECORD_SCHEMA, dict(item)) for item in artifacts]
    normalized.sort(key=lambda item: item["artifact_key"])
    row = {
        "schema": ARTIFACTS_INDEX_SCHEMA,
        "run_id": _validate_run_id(run_id),
        "artifacts": normalized,
        "artifact_count": len(normalized),
        "safety_contract": safety_contract(),
    }
    return validate_row(ARTIFACTS_INDEX_SCHEMA, row)


def build_conversation_index_row(
    *,
    run_id: str,
    logical_source_id: str,
    conversation_id: Optional[str],
    title: Optional[str],
    source_relative_path: Union[str, PurePath],
    source_hash: str,
    source_ordinal: int,
    create_time: Optional[str],
    update_time: Optional[str],
    model_slug: Optional[str],
    plugin_ids: Optional[Sequence[str]],
    message_count: int,
    user_message_count: int,
    assistant_message_count: int,
    char_count: int,
    first_user_excerpt: Optional[str],
    top_user_prompt_excerpts: Optional[Sequence[str]],
) -> dict[str, Any]:
    row = {
        "schema": CONVERSATION_INDEX_SCHEMA,
        "run_id": _validate_run_id(run_id),
        "logical_source_id": _validate_text_id("logical_source_id", logical_source_id),
        "conversation_id": _optional_str(conversation_id),
        "title": _optional_str(title),
        "source_relative_path": _validate_relative_path(source_relative_path),
        "source_hash": _validate_text_id("source_hash", source_hash),
        "source_ordinal": _validate_nonnegative_int("source_ordinal", source_ordinal),
        "create_time": _optional_str(create_time),
        "update_time": _optional_str(update_time),
        "model_slug": _optional_str(model_slug),
        "plugin_ids": _normalize_str_list(plugin_ids or []),
        "message_count": _validate_nonnegative_int("message_count", message_count),
        "user_message_count": _validate_nonnegative_int("user_message_count", user_message_count),
        "assistant_message_count": _validate_nonnegative_int(
            "assistant_message_count", assistant_message_count
        ),
        "char_count": _validate_nonnegative_int("char_count", char_count),
        "first_user_excerpt": _optional_str(first_user_excerpt),
        "top_user_prompt_excerpts": _normalize_str_list(top_user_prompt_excerpts or []),
        "safety_contract": safety_contract(),
    }
    return validate_row(CONVERSATION_INDEX_SCHEMA, row)


def build_thread_index_row(
    *,
    run_id: str,
    thread_id: str,
    logical_source_id: str,
    conversation_id: Optional[str],
    conversation_title: Optional[str],
    source_hash: str,
    thread_index: int,
    message_start_index: int,
    message_end_index: int,
    char_start: int,
    char_end: int,
    user_message_count: int,
    assistant_message_count: int,
    char_count: int,
    title_hint: Optional[str],
    representative_excerpt: Optional[str],
) -> dict[str, Any]:
    if message_end_index < message_start_index:
        raise ValueError("message_end_index must be >= message_start_index")
    if char_end < char_start:
        raise ValueError("char_end must be >= char_start")
    row = {
        "schema": THREAD_INDEX_SCHEMA,
        "run_id": _validate_run_id(run_id),
        "thread_id": _validate_text_id("thread_id", thread_id),
        "logical_source_id": _validate_text_id("logical_source_id", logical_source_id),
        "conversation_id": _optional_str(conversation_id),
        "conversation_title": _optional_str(conversation_title),
        "source_hash": _validate_text_id("source_hash", source_hash),
        "thread_index": _validate_nonnegative_int("thread_index", thread_index),
        "message_start_index": _validate_nonnegative_int("message_start_index", message_start_index),
        "message_end_index": _validate_nonnegative_int("message_end_index", message_end_index),
        "char_start": _validate_nonnegative_int("char_start", char_start),
        "char_end": _validate_nonnegative_int("char_end", char_end),
        "user_message_count": _validate_nonnegative_int("user_message_count", user_message_count),
        "assistant_message_count": _validate_nonnegative_int(
            "assistant_message_count", assistant_message_count
        ),
        "char_count": _validate_nonnegative_int("char_count", char_count),
        "title_hint": _optional_str(title_hint),
        "representative_excerpt": _optional_str(representative_excerpt),
        "safety_contract": safety_contract(),
    }
    return validate_row(THREAD_INDEX_SCHEMA, row)


def build_lexical_sketch_row(
    *,
    run_id: str,
    thread_id: str,
    logical_source_id: str,
    top_terms: Sequence[Mapping[str, Any]],
    keyphrases: Optional[Sequence[str]] = None,
    domains: Optional[Sequence[str]] = None,
    paths: Optional[Sequence[str]] = None,
    commands: Optional[Sequence[str]] = None,
    package_names: Optional[Sequence[str]] = None,
    model_names: Optional[Sequence[str]] = None,
    legal_citations: Optional[Sequence[str]] = None,
    capitalized_phrases: Optional[Sequence[str]] = None,
    representative_excerpts: Optional[Sequence[str]] = None,
    noise_terms_rejected: Optional[Sequence[str]] = None,
    policy_version: str = "lexical_sketch.v1",
) -> dict[str, Any]:
    row = {
        "schema": LEXICAL_SKETCH_SCHEMA,
        "run_id": _validate_run_id(run_id),
        "thread_id": _validate_text_id("thread_id", thread_id),
        "logical_source_id": _validate_text_id("logical_source_id", logical_source_id),
        "top_terms": _normalize_term_counts(top_terms),
        "keyphrases": _normalize_str_list(keyphrases or []),
        "domains": _normalize_str_list(domains or []),
        "paths": _normalize_str_list(paths or []),
        "commands": _normalize_str_list(commands or []),
        "package_names": _normalize_str_list(package_names or []),
        "model_names": _normalize_str_list(model_names or []),
        "legal_citations": _normalize_str_list(legal_citations or []),
        "capitalized_phrases": _normalize_str_list(capitalized_phrases or []),
        "representative_excerpts": _normalize_str_list(representative_excerpts or []),
        "noise_terms_rejected": _normalize_str_list(noise_terms_rejected or []),
        "policy_version": _validate_text_id("policy_version", policy_version),
        "safety_contract": safety_contract(),
    }
    return validate_row(LEXICAL_SKETCH_SCHEMA, row)


def build_thread_embedding_metadata_row(
    *,
    run_id: str,
    thread_id: str,
    embedding_id: str,
    embedding_model: str,
    effective_device: str,
    vector_dimensions: int,
    source_text_sha256: str,
    source_text_chars: int,
    batch_index: int,
    status: str,
    error_code: Optional[str] = None,
) -> dict[str, Any]:
    row = {
        "schema": THREAD_EMBEDDING_METADATA_SCHEMA,
        "run_id": _validate_run_id(run_id),
        "thread_id": _validate_text_id("thread_id", thread_id),
        "embedding_id": _validate_text_id("embedding_id", embedding_id),
        "embedding_model": _validate_text_id("embedding_model", embedding_model),
        "effective_device": _validate_text_id("effective_device", effective_device),
        "vector_dimensions": _validate_nonnegative_int("vector_dimensions", vector_dimensions),
        "source_text_sha256": _validate_text_id("source_text_sha256", source_text_sha256),
        "source_text_chars": _validate_nonnegative_int("source_text_chars", source_text_chars),
        "batch_index": _validate_nonnegative_int("batch_index", batch_index),
        "status": _validate_choice("status", status, EMBEDDING_STATUSES),
        "error_code": _optional_str(error_code),
        "safety_contract": safety_contract(),
    }
    return validate_row(THREAD_EMBEDDING_METADATA_SCHEMA, row)


def build_topic_cluster_row(
    *,
    run_id: str,
    cluster_id: str,
    status: str,
    topic_label: Optional[str],
    thread_ids: Sequence[str],
    top_terms: Sequence[Mapping[str, Any]],
    evidence_titles: Optional[Sequence[str]] = None,
    representative_thread_ids: Optional[Sequence[str]] = None,
    representative_excerpts: Optional[Sequence[str]] = None,
    mixed_reasons: Optional[Sequence[str]] = None,
) -> dict[str, Any]:
    normalized_thread_ids = _normalize_str_list(thread_ids)
    row = {
        "schema": TOPIC_CLUSTER_SCHEMA,
        "run_id": _validate_run_id(run_id),
        "cluster_id": _validate_text_id("cluster_id", cluster_id),
        "status": _validate_choice("status", status, TOPIC_CLUSTER_STATUSES),
        "topic_label": _optional_str(topic_label),
        "thread_ids": normalized_thread_ids,
        "size": len(normalized_thread_ids),
        "top_terms": _normalize_term_counts(top_terms),
        "evidence_titles": _normalize_str_list(evidence_titles or []),
        "representative_thread_ids": _normalize_str_list(representative_thread_ids or []),
        "representative_excerpts": _normalize_str_list(representative_excerpts or []),
        "mixed_reasons": _normalize_str_list(mixed_reasons or []),
        "safety_contract": safety_contract(),
    }
    return validate_row(TOPIC_CLUSTER_SCHEMA, row)


def build_atlas_summary_manifest(
    *,
    run_id: str,
    relative_path: Union[str, PurePath] = "atlas_summary.md",
    status: str,
    source_schema_names: Sequence[str],
    sections: Sequence[str],
    counts: Optional[Mapping[str, int]] = None,
) -> dict[str, Any]:
    row = {
        "schema": ATLAS_SUMMARY_MANIFEST_SCHEMA,
        "run_id": _validate_run_id(run_id),
        "relative_path": _validate_relative_path(relative_path),
        "status": _validate_choice("status", status, SUMMARY_STATUSES),
        "source_schema_names": [_validate_schema_name(item) for item in source_schema_names],
        "sections": _normalize_str_list(sections),
        "counts": _normalize_count_map(counts or {}),
        "safety_contract": safety_contract(),
    }
    return validate_row(ATLAS_SUMMARY_MANIFEST_SCHEMA, row)


def safety_contract() -> dict[str, Any]:
    return json.loads(json.dumps(_SAFETY_CONTRACT, sort_keys=True))


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


def canonical_artifact_records(counts: Optional[Mapping[str, int]] = None) -> list[dict[str, Any]]:
    counts = counts or {}
    specs = [
        ("progress", PROGRESS_SCHEMA, "source_inventory", "application/json", False, True, True),
        (
            "conversation_index",
            CONVERSATION_INDEX_SCHEMA,
            "conversation_index",
            "application/jsonl",
            True,
            True,
            True,
        ),
        ("thread_index", THREAD_INDEX_SCHEMA, "thread_index", "application/jsonl", True, True, True),
        (
            "lexical_sketches",
            LEXICAL_SKETCH_SCHEMA,
            "lexical_sketches",
            "application/jsonl",
            True,
            True,
            True,
        ),
        (
            "thread_embeddings",
            THREAD_EMBEDDING_METADATA_SCHEMA,
            "thread_embeddings",
            "application/jsonl",
            True,
            True,
            False,
        ),
        (
            "topic_clusters",
            TOPIC_CLUSTER_SCHEMA,
            "topic_clusters",
            "application/jsonl",
            True,
            True,
            True,
        ),
        (
            "atlas_summary",
            ATLAS_SUMMARY_MANIFEST_SCHEMA,
            "summary",
            "text/markdown",
            False,
            True,
            True,
        ),
        (
            "artifacts_index",
            ARTIFACTS_INDEX_SCHEMA,
            "manifest",
            "application/json",
            False,
            True,
            True,
        ),
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
        )
        for artifact_key, schema_name, phase, content_type, append_only, review_safe, dashboard_safe in specs
    ]


def _validate_run_id(run_id: str) -> str:
    if not isinstance(run_id, str) or not _RUN_ID_RE.match(run_id) or run_id in {".", ".."}:
        raise ValueError("run_id must be a relative slug with no path separators")
    return run_id


def _validate_schema_name(schema_name: str) -> str:
    if not isinstance(schema_name, str) or schema_name not in set(REQUIRED_KEYS).union(
        {ARTIFACT_INDEX_RECORD_SCHEMA}
    ):
        raise ValueError(f"unknown schema name: {schema_name!r}")
    return schema_name


def _validate_slug(name: str, value: str) -> str:
    if not isinstance(value, str) or not _SLUG_RE.match(value) or value in {".", ".."}:
        raise ValueError(f"{name} must be a non-empty slug")
    return value


def _validate_text_id(name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
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


def _normalize_str_list(values: Sequence[str]) -> list[str]:
    result = []
    for value in values:
        if not isinstance(value, str):
            raise ValueError("expected a sequence of strings")
        result.append(value)
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
                raise ValueError(f"{path}.{key} is forbidden by the atlas no-write contract")
            _reject_forbidden_fields(item, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_forbidden_fields(item, path=f"{path}[{index}]")
