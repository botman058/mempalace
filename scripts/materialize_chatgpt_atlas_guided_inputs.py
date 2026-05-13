#!/usr/bin/env python3
"""Materialize atlas-guided ChatGPT input artifacts from archive-atlas outputs."""
# ruff: noqa: E402

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mempalace import chatgpt_archive_atlas_contract as atlas_contract
from mempalace import chatgpt_atlas_guided_bridge as guided_bridge
from mempalace import chatgpt_atlas_guided_contract as guided_contract
from mempalace import chatgpt_atlas_guided_coverage as guided_coverage

CANONICAL_ATLAS_RUN_ROOT = Path("/media/u0/OneDrive_Backup/mempalace/data/chatgpt_archive_atlas")
BLOCKED_ATLAS_RUN_ROOT = Path("/media/u0/Extreme SSD")


class MaterializationError(RuntimeError):
    """Raised when materialization cannot safely proceed."""


def _resolve_path(path_value: str | Path) -> Path:
    return Path(path_value).expanduser().resolve(strict=False)


def _validate_atlas_run_dir(atlas_run_dir: str | Path) -> Path:
    resolved = _resolve_path(atlas_run_dir)
    canonical_root = _resolve_path(CANONICAL_ATLAS_RUN_ROOT)
    blocked_root = _resolve_path(BLOCKED_ATLAS_RUN_ROOT)

    if resolved == blocked_root or blocked_root in resolved.parents:
        raise MaterializationError(
            f"--atlas-run-dir must not use {BLOCKED_ATLAS_RUN_ROOT}"
        )
    if resolved == canonical_root or canonical_root not in resolved.parents:
        raise MaterializationError(
            "--atlas-run-dir must resolve to a child directory under "
            f"{CANONICAL_ATLAS_RUN_ROOT}"
        )
    return resolved


def _read_required_jsonl(
    path: Path,
    *,
    label: str,
    schema_name: str,
    validator: Callable[[str, dict[str, Any]], dict[str, Any]],
) -> tuple[dict[str, Any], ...]:
    if not path.is_file():
        raise MaterializationError(f"Missing required {label}: {path}")

    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise MaterializationError(
                        f"Invalid JSON in {label} at {path}:{line_number}: {exc.msg}"
                    ) from exc
                if not isinstance(payload, dict):
                    raise MaterializationError(
                        f"{label} row {line_number} must be a JSON object"
                    )
                try:
                    rows.append(validator(schema_name, payload))
                except ValueError as exc:
                    raise MaterializationError(
                        f"Invalid {label} row {line_number} at {path}: {exc}"
                    ) from exc
    except OSError as exc:
        raise MaterializationError(f"Could not read {label} at {path}: {exc}") from exc
    return tuple(rows)


def _collect_input_run_ids(
    topic_cluster_rows: tuple[dict[str, Any], ...],
    thread_index_rows: tuple[dict[str, Any], ...],
) -> frozenset[str]:
    seen: set[str] = set()
    for row in topic_cluster_rows:
        seen.add(str(row["run_id"]))
    for row in thread_index_rows:
        seen.add(str(row["run_id"]))
    return frozenset(seen)


def _resolve_atlas_run_id(
    *,
    atlas_run_dir: Path,
    topic_cluster_rows: tuple[dict[str, Any], ...],
    thread_index_rows: tuple[dict[str, Any], ...],
    requested_atlas_run_id: str | None,
) -> str:
    seen_run_ids = _collect_input_run_ids(topic_cluster_rows, thread_index_rows)
    if requested_atlas_run_id is not None:
        atlas_run_id = requested_atlas_run_id
    elif seen_run_ids:
        if len(seen_run_ids) != 1:
            raise MaterializationError(
                f"topic_clusters.jsonl and thread_index.jsonl must share one atlas run_id, got {sorted(seen_run_ids)}"
            )
        atlas_run_id = next(iter(seen_run_ids))
    else:
        atlas_run_id = atlas_run_dir.name

    for run_id in seen_run_ids:
        if run_id != atlas_run_id:
            raise MaterializationError(
                f"Input atlas run_id {run_id} does not match requested atlas_run_id {atlas_run_id}"
            )
    return atlas_run_id


def _serialize_jsonl(rows: tuple[dict[str, Any], ...]) -> bytes:
    payload = "".join(
        json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows
    )
    return payload.encode("utf-8")


def _serialize_json(row: dict[str, Any]) -> bytes:
    return (json.dumps(row, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _write_missing_file_exclusively(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(path, flags, 0o644)
    with os.fdopen(fd, "wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _read_existing_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise MaterializationError(f"Could not read existing artifact {path}: {exc}") from exc


def materialize_atlas_guided_inputs(
    *,
    atlas_run_dir: str | Path,
    run_id: str | None = None,
    atlas_run_id: str | None = None,
) -> dict[str, Any]:
    resolved_atlas_run_dir = _validate_atlas_run_dir(atlas_run_dir)
    topic_clusters_path = (
        resolved_atlas_run_dir / atlas_contract.CANONICAL_ARTIFACT_PATHS["topic_clusters"]
    )
    thread_index_path = resolved_atlas_run_dir / atlas_contract.CANONICAL_ARTIFACT_PATHS["thread_index"]

    topic_cluster_rows = _read_required_jsonl(
        topic_clusters_path,
        label="topic clusters",
        schema_name=atlas_contract.TOPIC_CLUSTER_SCHEMA,
        validator=atlas_contract.validate_row,
    )
    thread_index_rows = _read_required_jsonl(
        thread_index_path,
        label="thread index",
        schema_name=atlas_contract.THREAD_INDEX_SCHEMA,
        validator=atlas_contract.validate_row,
    )

    resolved_atlas_run_id = _resolve_atlas_run_id(
        atlas_run_dir=resolved_atlas_run_dir,
        topic_cluster_rows=topic_cluster_rows,
        thread_index_rows=thread_index_rows,
        requested_atlas_run_id=atlas_run_id,
    )
    resolved_run_id = run_id or resolved_atlas_run_id

    bridge_result = guided_bridge.build_chatgpt_atlas_guided_bridge(
        topic_cluster_rows,
        run_id=resolved_run_id,
        atlas_run_id=resolved_atlas_run_id,
    )
    coverage_result = guided_coverage.build_chatgpt_atlas_guided_coverage(
        bridge_result.rows,
        thread_index_rows,
        run_id=resolved_run_id,
        atlas_run_id=resolved_atlas_run_id,
    )

    artifact_payloads = {
        "candidate_bridge_records": {
            "path": resolved_atlas_run_dir
            / guided_contract.CANONICAL_ARTIFACT_PATHS["candidate_bridge_records"],
            "bytes": _serialize_jsonl(bridge_result.rows),
            "count": len(bridge_result.rows),
        },
        "atlas_thread_candidates": {
            "path": resolved_atlas_run_dir
            / guided_contract.CANONICAL_ARTIFACT_PATHS["atlas_thread_candidates"],
            "bytes": _serialize_jsonl(coverage_result.rows),
            "count": len(coverage_result.rows),
        },
        "atlas_candidate_coverage": {
            "path": resolved_atlas_run_dir
            / guided_contract.CANONICAL_ARTIFACT_PATHS["atlas_candidate_coverage"],
            "bytes": _serialize_json(coverage_result.report),
            "count": 1,
        },
    }

    file_summaries: dict[str, dict[str, Any]] = {}
    pending_creates: list[tuple[str, Path, bytes]] = []

    for artifact_key, spec in artifact_payloads.items():
        artifact_path = Path(spec["path"])
        payload = bytes(spec["bytes"])
        payload_sha256 = _sha256_hex(payload)
        existing_status = "created"

        if artifact_path.exists():
            existing_bytes = _read_existing_bytes(artifact_path)
            if existing_bytes != payload:
                raise MaterializationError(
                    f"Refusing to overwrite non-identical existing artifact: {artifact_path}"
                )
            existing_status = "already_materialized"
        else:
            pending_creates.append((artifact_key, artifact_path, payload))

        file_summaries[artifact_key] = {
            "path": str(artifact_path),
            "status": existing_status,
            "count": int(spec["count"]),
            "bytes": len(payload),
            "sha256": payload_sha256,
        }

    for artifact_key, artifact_path, payload in pending_creates:
        try:
            _write_missing_file_exclusively(artifact_path, payload)
        except FileExistsError:
            existing_bytes = _read_existing_bytes(artifact_path)
            if existing_bytes != payload:
                raise MaterializationError(
                    f"Refusing to overwrite concurrently created non-identical artifact: {artifact_path}"
                ) from None
            file_summaries[artifact_key]["status"] = "already_materialized"

    statuses = {details["status"] for details in file_summaries.values()}
    overall_status = "already_materialized" if statuses == {"already_materialized"} else "materialized"

    return {
        "status": overall_status,
        "atlas_run_dir": str(resolved_atlas_run_dir),
        "run_id": resolved_run_id,
        "atlas_run_id": resolved_atlas_run_id,
        "input_counts": {
            "topic_clusters": len(topic_cluster_rows),
            "thread_index_rows": len(thread_index_rows),
        },
        "output_counts": {
            "candidate_bridge_records": len(bridge_result.rows),
            "atlas_thread_candidates": len(coverage_result.rows),
            "atlas_candidate_coverage": 1,
        },
        "coverage_status": str(coverage_result.report["status"]),
        "bridge_warnings": list(bridge_result.warnings),
        "files": file_summaries,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize candidate_bridge_records.jsonl, atlas_thread_candidates.jsonl, "
            "and atlas_candidate_coverage.json from archive-atlas topic_clusters.jsonl "
            "and thread_index.jsonl."
        )
    )
    parser.add_argument(
        "--atlas-run-dir",
        required=True,
        help="Atlas run directory under the canonical chatgpt_archive_atlas root.",
    )
    parser.add_argument(
        "--run-id",
        help="Optional deterministic run_id to stamp into the materialized guided artifacts.",
    )
    parser.add_argument(
        "--atlas-run-id",
        help="Optional atlas run id override; must match the input rows when present.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv or sys.argv[1:])
        summary = materialize_atlas_guided_inputs(
            atlas_run_dir=args.atlas_run_dir,
            run_id=args.run_id,
            atlas_run_id=args.atlas_run_id,
        )
    except MaterializationError as exc:
        print(f"fatal: {exc}", file=sys.stderr, flush=True)
        return 2

    print(json.dumps(summary, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
