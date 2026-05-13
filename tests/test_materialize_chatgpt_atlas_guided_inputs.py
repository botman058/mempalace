from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

from mempalace import chatgpt_archive_atlas_contract as atlas_contract
from mempalace import chatgpt_atlas_guided_contract as guided_contract


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "materialize_chatgpt_atlas_guided_inputs.py"
ATLAS_RUN_ID = "atlas_full2_20260512T0412Z_2fc8ac5"


def _load_script_module():
    module_name = "tests_materialize_chatgpt_atlas_guided_inputs"
    existing = sys.modules.get(module_name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(module_name, SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_script = _load_script_module()


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _make_cluster_row(cluster_id: str, *, thread_ids: list[str]) -> dict[str, Any]:
    return atlas_contract.build_topic_cluster_row(
        run_id=ATLAS_RUN_ID,
        cluster_id=cluster_id,
        status="candidate",
        topic_label="Postgres latency",
        thread_ids=thread_ids,
        top_terms=[{"term": "postgres", "count": 5}, {"term": "latency", "count": 3}],
        evidence_titles=["Postgres tuning"],
        representative_thread_ids=thread_ids[:1],
        representative_excerpts=["Representative excerpt"],
        mixed_reasons=[],
    )


def _make_thread_row(thread_id: str, *, ordinal: int) -> dict[str, Any]:
    return atlas_contract.build_thread_index_row(
        run_id=ATLAS_RUN_ID,
        thread_id=thread_id,
        logical_source_id=f"logical-{thread_id}",
        conversation_id=f"conversation-{thread_id}",
        conversation_title=f"Conversation {thread_id}",
        source_hash=f"hash-{thread_id}",
        thread_index=ordinal,
        message_start_index=ordinal * 10,
        message_end_index=ordinal * 10 + 2,
        char_start=ordinal * 100,
        char_end=ordinal * 100 + 48,
        user_message_count=2,
        assistant_message_count=2,
        char_count=48,
        title_hint=f"Hint {thread_id}",
        representative_excerpt=f"Excerpt {thread_id}",
    )


def _build_atlas_run_dir(tmp_path: Path) -> tuple[Path, Path]:
    canonical_root = tmp_path / "chatgpt_archive_atlas"
    atlas_run_dir = canonical_root / ATLAS_RUN_ID
    _write_jsonl(
        atlas_run_dir / atlas_contract.CANONICAL_ARTIFACT_PATHS["topic_clusters"],
        [_make_cluster_row("cluster-001", thread_ids=["thread-001"])],
    )
    _write_jsonl(
        atlas_run_dir / atlas_contract.CANONICAL_ARTIFACT_PATHS["thread_index"],
        [
            _make_thread_row("thread-001", ordinal=1),
            _make_thread_row("thread-002", ordinal=2),
        ],
    )
    return canonical_root, atlas_run_dir


def test_materialize_cli_creates_guided_inputs_and_prints_json_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    canonical_root, atlas_run_dir = _build_atlas_run_dir(tmp_path)
    monkeypatch.setattr(_script, "CANONICAL_ATLAS_RUN_ROOT", canonical_root)

    exit_code = _script.main(["--atlas-run-dir", str(atlas_run_dir)])

    assert exit_code == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["status"] == "materialized"
    assert summary["run_id"] == ATLAS_RUN_ID
    assert summary["atlas_run_id"] == ATLAS_RUN_ID
    assert summary["input_counts"] == {"topic_clusters": 1, "thread_index_rows": 2}
    assert summary["output_counts"] == {
        "candidate_bridge_records": 1,
        "atlas_thread_candidates": 2,
        "atlas_candidate_coverage": 1,
    }
    assert summary["coverage_status"] == "needs_review"
    assert summary["bridge_warnings"] == []
    assert {
        details["status"] for details in summary["files"].values()
    } == {"created"}

    candidate_path = atlas_run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["candidate_bridge_records"]
    lookup_path = atlas_run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["atlas_thread_candidates"]
    coverage_path = atlas_run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["atlas_candidate_coverage"]

    candidate_rows = _read_jsonl(candidate_path)
    lookup_rows = _read_jsonl(lookup_path)
    coverage_row = json.loads(coverage_path.read_text(encoding="utf-8"))

    assert len(candidate_rows) == 1
    assert len(lookup_rows) == 2
    assert coverage_row["status"] == "needs_review"
    for row in candidate_rows:
        assert guided_contract.validate_row(guided_contract.CANDIDATE_BRIDGE_RECORD_SCHEMA, row) == row
    for row in lookup_rows:
        assert guided_contract.validate_row(guided_contract.THREAD_CANDIDATE_LOOKUP_SCHEMA, row) == row
    assert (
        guided_contract.validate_row(guided_contract.CANDIDATE_COVERAGE_REPORT_SCHEMA, coverage_row)
        == coverage_row
    )


def test_materialize_is_idempotent_when_existing_outputs_match(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    canonical_root, atlas_run_dir = _build_atlas_run_dir(tmp_path)
    monkeypatch.setattr(_script, "CANONICAL_ATLAS_RUN_ROOT", canonical_root)

    first = _script.materialize_atlas_guided_inputs(atlas_run_dir=atlas_run_dir)
    candidate_path = atlas_run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["candidate_bridge_records"]
    lookup_path = atlas_run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["atlas_thread_candidates"]
    coverage_path = atlas_run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["atlas_candidate_coverage"]
    before_mtimes = {
        candidate_path: candidate_path.stat().st_mtime_ns,
        lookup_path: lookup_path.stat().st_mtime_ns,
        coverage_path: coverage_path.stat().st_mtime_ns,
    }

    second = _script.materialize_atlas_guided_inputs(atlas_run_dir=atlas_run_dir)

    assert first["status"] == "materialized"
    assert second["status"] == "already_materialized"
    assert {
        details["status"] for details in second["files"].values()
    } == {"already_materialized"}
    after_mtimes = {
        candidate_path: candidate_path.stat().st_mtime_ns,
        lookup_path: lookup_path.stat().st_mtime_ns,
        coverage_path: coverage_path.stat().st_mtime_ns,
    }
    assert after_mtimes == before_mtimes


def test_materialize_refuses_non_identical_existing_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    canonical_root, atlas_run_dir = _build_atlas_run_dir(tmp_path)
    monkeypatch.setattr(_script, "CANONICAL_ATLAS_RUN_ROOT", canonical_root)
    candidate_path = atlas_run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["candidate_bridge_records"]
    candidate_path.write_text('{"unexpected": true}\n', encoding="utf-8")

    with pytest.raises(_script.MaterializationError, match="Refusing to overwrite non-identical"):
        _script.materialize_atlas_guided_inputs(atlas_run_dir=atlas_run_dir)

    assert not (
        atlas_run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["atlas_thread_candidates"]
    ).exists()
    assert not (
        atlas_run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["atlas_candidate_coverage"]
    ).exists()


def test_materialize_refuses_extreme_ssd_paths() -> None:
    with pytest.raises(_script.MaterializationError, match="must not use /media/u0/Extreme SSD"):
        _script.materialize_atlas_guided_inputs(
            atlas_run_dir="/media/u0/Extreme SSD/chatgpt_archive_atlas/atlas_full2_demo"
        )


def test_materialize_refuses_paths_outside_canonical_root(tmp_path: Path) -> None:
    outside_dir = tmp_path / "atlas_full2_outside_root"

    with pytest.raises(_script.MaterializationError, match="must resolve to a child directory under"):
        _script.materialize_atlas_guided_inputs(atlas_run_dir=outside_dir)


def test_materializer_does_not_use_tempfile_cleanup_or_unlink() -> None:
    script_text = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "tempfile" not in script_text
    assert ".unlink(" not in script_text
    assert "os.O_EXCL" in script_text
