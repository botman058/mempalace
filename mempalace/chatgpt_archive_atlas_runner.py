from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Mapping, Sequence

from . import chatgpt_archive_atlas_contract as contract
from .chatgpt_archive_atlas_conversation import build_chatgpt_conversation_index_rows
from .chatgpt_archive_atlas_embedding_cache import materialize_chatgpt_thread_embedding_cache
from .chatgpt_archive_atlas_lexical_sketch import build_chatgpt_lexical_sketch_rows
from .chatgpt_archive_atlas_source import load_chatgpt_archive_source_dir
from .chatgpt_archive_atlas_summary import build_chatgpt_atlas_summary
from .chatgpt_archive_atlas_thread import build_chatgpt_thread_index_rows
from .chatgpt_archive_atlas_topic_cluster import build_chatgpt_topic_clusters

_RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    source_dir = _validate_source_dir(args.source_dir)
    run_root = _validate_run_root(args.run_root)
    run_id = _validate_run_id(args.run_id)
    run_dir = _resolve_run_dir(run_root, run_id)

    run_dir.mkdir(parents=True, exist_ok=True)
    started_at = _timestamp_utc()
    counts: dict[str, int] = {}
    source_errors: list[dict[str, Any]] = []

    try:
        _write_progress(
            run_dir=run_dir,
            run_id=run_id,
            phase="source_inventory",
            status="running",
            counts=counts,
            errors=0,
            warnings=0,
            started_at=started_at,
            updated_at=started_at,
            message="starting atlas artifact build",
        )

        loaded = load_chatgpt_archive_source_dir(source_dir)
        source_errors.extend(dict(row) for row in loaded.source_errors)
        conversations = list(loaded.conversations)
        if args.limit is not None:
            conversations = conversations[: args.limit]
        counts["loaded_conversations"] = len(conversations)
        counts["source_errors"] = len(source_errors)
        _write_jsonl(run_dir / "source_file_errors.jsonl", source_errors)
        _write_progress(
            run_dir=run_dir,
            run_id=run_id,
            phase="source_inventory",
            status="running",
            counts=counts,
            errors=len(source_errors),
            warnings=0,
            started_at=started_at,
            updated_at=_timestamp_utc(),
            message="source inventory written",
        )

        conversation_rows = list(
            build_chatgpt_conversation_index_rows(
                conversations,
                run_id=run_id,
            )
        )
        _write_jsonl(
            run_dir / "conversation_index.jsonl",
            conversation_rows,
            validate_schema=contract.CONVERSATION_INDEX_SCHEMA,
        )
        counts["conversation_rows"] = len(conversation_rows)
        _write_progress(
            run_dir=run_dir,
            run_id=run_id,
            phase="conversation_index",
            status="running",
            counts=counts,
            errors=len(source_errors),
            warnings=0,
            started_at=started_at,
            updated_at=_timestamp_utc(),
            message="conversation index written",
        )

        thread_rows = list(build_chatgpt_thread_index_rows(conversations, run_id=run_id))
        _write_jsonl(run_dir / "thread_index.jsonl", thread_rows, validate_schema=contract.THREAD_INDEX_SCHEMA)
        counts["thread_rows"] = len(thread_rows)
        _write_progress(
            run_dir=run_dir,
            run_id=run_id,
            phase="thread_index",
            status="running",
            counts=counts,
            errors=len(source_errors),
            warnings=0,
            started_at=started_at,
            updated_at=_timestamp_utc(),
            message="thread index written",
        )

        lexical_rows = list(build_chatgpt_lexical_sketch_rows(conversations, run_id=run_id))
        _write_jsonl(
            run_dir / "lexical_sketches.jsonl",
            lexical_rows,
            validate_schema=contract.LEXICAL_SKETCH_SCHEMA,
        )
        counts["lexical_rows"] = len(lexical_rows)
        _write_progress(
            run_dir=run_dir,
            run_id=run_id,
            phase="lexical_sketches",
            status="running",
            counts=counts,
            errors=len(source_errors),
            warnings=0,
            started_at=started_at,
            updated_at=_timestamp_utc(),
            message="lexical sketches written",
        )

        embedding_result = materialize_chatgpt_thread_embedding_cache(
            lexical_rows,
            run_dir,
            run_id=run_id,
            embedding_model=args.embedding_model,
            requested_device=args.embedding_device,
            batch_size=args.embedding_batch_size,
            force=args.force_embeddings,
        )
        source_errors.extend(dict(row) for row in embedding_result.source_errors)
        _write_jsonl(run_dir / "source_file_errors.jsonl", source_errors)
        for row in embedding_result.metadata_rows:
            contract.validate_row(contract.THREAD_EMBEDDING_METADATA_SCHEMA, dict(row))
        for row in embedding_result.vector_rows:
            contract.validate_json_safe(dict(row))
        counts["source_errors"] = len(source_errors)
        counts["embedding_metadata_rows"] = len(embedding_result.metadata_rows)
        counts["embedding_vector_rows"] = len(embedding_result.vector_rows)
        _write_progress(
            run_dir=run_dir,
            run_id=run_id,
            phase="thread_embeddings",
            status="running",
            counts=counts,
            errors=len(source_errors),
            warnings=0,
            started_at=started_at,
            updated_at=_timestamp_utc(),
            message="embedding cache complete",
        )

        topic_cluster_result = build_chatgpt_topic_clusters(
            lexical_rows,
            embedding_result.vector_rows,
            run_id=run_id,
        )
        _write_jsonl(
            run_dir / "topic_clusters.jsonl",
            topic_cluster_result.rows,
            validate_schema=contract.TOPIC_CLUSTER_SCHEMA,
        )
        counts["topic_cluster_rows"] = len(topic_cluster_result.rows)
        _write_progress(
            run_dir=run_dir,
            run_id=run_id,
            phase="topic_clusters",
            status="running",
            counts=counts,
            errors=len(source_errors),
            warnings=len(topic_cluster_result.warnings),
            started_at=started_at,
            updated_at=_timestamp_utc(),
            message="topic clusters written",
        )

        summary_result = build_chatgpt_atlas_summary(
            topic_cluster_result.rows,
            run_id=run_id,
            source_counts=counts,
            source_errors=source_errors,
        )
        _write_text_atomic(run_dir / "atlas_summary.md", summary_result.markdown)
        _write_json_atomic(run_dir / "atlas_summary_manifest.json", summary_result.manifest)
        _write_progress(
            run_dir=run_dir,
            run_id=run_id,
            phase="summary",
            status="running",
            counts=counts,
            errors=len(source_errors),
            warnings=len(topic_cluster_result.warnings) + len(summary_result.warnings),
            started_at=started_at,
            updated_at=_timestamp_utc(),
            message="summary and manifest written",
        )

        artifacts_index = _build_artifacts_index(
            run_id=run_id,
            counts={
                "progress": 1,
                "artifacts_index": 1,
                "conversation_index": len(conversation_rows),
                "thread_index": len(thread_rows),
                "lexical_sketches": len(lexical_rows),
                "thread_embeddings": len(embedding_result.metadata_rows),
                "topic_clusters": len(topic_cluster_result.rows),
                "atlas_summary": 1,
                "source_file_errors": len(source_errors),
                "thread_embedding_vectors": len(embedding_result.vector_rows),
                "atlas_summary_manifest": 1,
            },
        )
        _write_json_atomic(run_dir / "artifacts_index.json", artifacts_index)
        _write_progress(
            run_dir=run_dir,
            run_id=run_id,
            phase="artifacts_index",
            status="running",
            counts=counts,
            errors=len(source_errors),
            warnings=len(topic_cluster_result.warnings) + len(summary_result.warnings),
            started_at=started_at,
            updated_at=_timestamp_utc(),
            message="artifacts index written",
        )

        _write_progress(
            run_dir=run_dir,
            run_id=run_id,
            phase="complete",
            status="complete",
            counts=counts,
            errors=len(source_errors),
            warnings=len(topic_cluster_result.warnings) + len(summary_result.warnings),
            started_at=started_at,
            updated_at=_timestamp_utc(),
            message="atlas artifact build complete",
        )
        return 0
    except Exception as exc:
        try:
            _write_progress(
                run_dir=run_dir,
                run_id=run_id,
                phase="failed",
                status="failed",
                counts=counts,
                errors=max(1, len(source_errors)),
                warnings=0,
                started_at=started_at,
                updated_at=_timestamp_utc(),
                message=f"atlas artifact build failed: {exc}",
            )
        except Exception:
            pass
        raise


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pre-LLM ChatGPT archive atlas artifact runner")
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--embedding-device", default=None)
    parser.add_argument("--embedding-model", default="all-MiniLM-L6-v2")
    parser.add_argument("--embedding-batch-size", type=int, default=32)
    parser.add_argument("--force-embeddings", action="store_true")
    args = parser.parse_args(argv)
    if args.limit is not None and args.limit < 0:
        raise ValueError("--limit must be >= 0")
    if args.embedding_batch_size <= 0:
        raise ValueError("--embedding-batch-size must be > 0")
    return args


def _validate_source_dir(path: str) -> Path:
    source_dir = Path(path).resolve()
    if not source_dir.exists() or not source_dir.is_dir():
        raise ValueError(f"source dir does not exist or is not a directory: {path}")
    return source_dir


def _validate_run_root(path: str) -> Path:
    return Path(path).resolve()


def _validate_run_id(run_id: str) -> str:
    if not isinstance(run_id, str) or not _RUN_ID_RE.match(run_id) or run_id in {".", ".."}:
        raise ValueError("run_id must match ^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")
    return run_id


def _resolve_run_dir(run_root: Path, run_id: str) -> Path:
    run_dir = (run_root / run_id).resolve()
    try:
        run_dir.relative_to(run_root)
    except ValueError as exc:
        raise ValueError("run_dir must resolve under run_root") from exc
    return run_dir


def _write_progress(
    *,
    run_dir: Path,
    run_id: str,
    phase: str,
    status: str,
    counts: Mapping[str, int],
    errors: int,
    warnings: int,
    started_at: str,
    updated_at: str,
    message: str,
) -> None:
    row = contract.build_progress(
        run_id=run_id,
        phase=phase,
        status=status,
        counts=dict(counts),
        errors=errors,
        warnings=warnings,
        started_at=started_at,
        updated_at=updated_at,
        message=message,
    )
    _write_json_atomic(run_dir / "progress.json", row)


def _build_artifacts_index(*, run_id: str, counts: Mapping[str, int]) -> dict[str, Any]:
    records = contract.canonical_artifact_records(counts)
    records.extend(
        [
            contract.build_artifact_index_record(
                artifact_key="source_file_errors",
                schema_name=contract.ARTIFACT_INDEX_RECORD_SCHEMA,
                relative_path="source_file_errors.jsonl",
                phase="source_inventory",
                count=counts.get("source_file_errors", 0),
                content_type="application/jsonl",
                append_only=True,
                review_safe=True,
                dashboard_safe=True,
            ),
            contract.build_artifact_index_record(
                artifact_key="thread_embedding_vectors",
                schema_name=contract.ARTIFACT_INDEX_RECORD_SCHEMA,
                relative_path="thread_embedding_vectors.jsonl",
                phase="thread_embeddings",
                count=counts.get("thread_embedding_vectors", 0),
                content_type="application/jsonl",
                append_only=True,
                review_safe=True,
                dashboard_safe=False,
            ),
            contract.build_artifact_index_record(
                artifact_key="atlas_summary_manifest",
                schema_name=contract.ATLAS_SUMMARY_MANIFEST_SCHEMA,
                relative_path="atlas_summary_manifest.json",
                phase="summary",
                count=counts.get("atlas_summary_manifest", 0),
                content_type="application/json",
                append_only=False,
                review_safe=True,
                dashboard_safe=True,
            ),
        ]
    )
    return contract.build_artifacts_index(run_id=run_id, artifacts=records)


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]], validate_schema: str | None = None) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        for row in rows:
            normalized = dict(row)
            if validate_schema is not None:
                normalized = contract.validate_row(validate_schema, normalized)
                handle.write(contract.canonical_json_line(normalized))
            else:
                contract.validate_json_safe(normalized)
                handle.write(json.dumps(normalized, ensure_ascii=True, separators=(",", ":"), sort_keys=True))
                handle.write("\n")


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    contract.validate_json_safe(payload)
    rendered = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    _write_text_atomic(path, f"{rendered}\n")


def _write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", newline="", delete=False, dir=path.parent) as temp:
        temp.write(content)
        temp.flush()
        temp_path = Path(temp.name)
    temp_path.replace(path)


def _timestamp_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"chatgpt_archive_atlas_runner failed: {exc}", file=sys.stderr)
        raise
