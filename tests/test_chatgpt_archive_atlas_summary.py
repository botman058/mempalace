from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any

import pytest

from mempalace import chatgpt_archive_atlas_contract as contract

_summary_module = pytest.importorskip(
    "mempalace.chatgpt_archive_atlas_summary",
    reason="atlas summary implementation is not present yet",
)
ChatGPTAtlasSummaryResult = _summary_module.ChatGPTAtlasSummaryResult
build_chatgpt_atlas_summary = _summary_module.build_chatgpt_atlas_summary
write_chatgpt_atlas_summary = getattr(_summary_module, "write_chatgpt_atlas_summary", None)


def _cluster_row(
    *,
    cluster_id: str,
    status: str,
    topic_label: str | None,
    thread_ids: list[str],
    top_terms: list[dict[str, Any]],
    evidence_titles: list[str],
    representative_thread_ids: list[str],
    representative_excerpts: list[str],
    mixed_reasons: list[str] | None = None,
) -> dict[str, Any]:
    return contract.build_topic_cluster_row(
        run_id="run-wp10-summary",
        cluster_id=cluster_id,
        status=status,
        topic_label=topic_label,
        thread_ids=thread_ids,
        top_terms=top_terms,
        evidence_titles=evidence_titles,
        representative_thread_ids=representative_thread_ids,
        representative_excerpts=representative_excerpts,
        mixed_reasons=mixed_reasons,
    )


def _topic_cluster_rows() -> tuple[dict[str, Any], ...]:
    return (
        _cluster_row(
            cluster_id="wing-beta-room-402",
            status="candidate",
            topic_label="wing beta room 402 postgres tuning",
            thread_ids=["thread-003", "thread-004"],
            top_terms=[{"term": "postgres", "count": 9}, {"term": "index", "count": 4}],
            evidence_titles=["Postgres tuning checklist", "Vacuum and explain plans"],
            representative_thread_ids=["thread-003"],
            representative_excerpts=[
                "We should benchmark the index scan after the vacuum window closes.",
            ],
        ),
        _cluster_row(
            cluster_id="wing-alpha-room-101",
            status="candidate",
            topic_label="wing alpha room 101 privacy review",
            thread_ids=["thread-001", "thread-002", "thread-005"],
            top_terms=[{"term": "gdpr", "count": 8}, {"term": "policy", "count": 5}],
            evidence_titles=["Privacy review notes"],
            representative_thread_ids=["thread-001", "thread-005"],
            representative_excerpts=[
                "The legal memo mentions GDPR and data retention policy changes.",
            ],
        ),
        _cluster_row(
            cluster_id="wing-gamma-room-007",
            status="mixed",
            topic_label="wing gamma room 007 mixed sysadmin and legal",
            thread_ids=["thread-006", "thread-007"],
            top_terms=[{"term": "ssh", "count": 6}, {"term": "liability", "count": 2}],
            evidence_titles=["Sysadmin follow-up", "Liability clause notes"],
            representative_thread_ids=["thread-006"],
            representative_excerpts=[
                "Restarting ssh and reviewing the liability section are both in scope.",
            ],
            mixed_reasons=["crosses sysadmin and legal evidence"],
        ),
        _cluster_row(
            cluster_id="noise-standalone",
            status="noise",
            topic_label=None,
            thread_ids=["thread-008"],
            top_terms=[{"term": "misc", "count": 1}],
            evidence_titles=["Noisy fragment"],
            representative_thread_ids=["thread-008"],
            representative_excerpts=["Sparse one-off fragment without a stable topic."],
            mixed_reasons=["too sparse to form a stable cluster"],
        ),
    )


def _source_errors() -> tuple[dict[str, Any], ...]:
    return (
        {
            "source_relative_path": "exports/2026/bad-1.json",
            "error_code": "parse_failed",
            "message": "failed to parse export",
        },
        {
            "source_relative_path": "exports/2026/bad-2.json",
            "error_code": "empty_mapping",
            "message": "missing message mapping",
        },
    )


def _source_counts() -> dict[str, int]:
    return {
        "conversation_index": 3,
        "thread_index": 8,
        "lexical_sketches": 8,
        "thread_embeddings": 8,
        "topic_clusters": 4,
    }


def test_public_api_dataclass_is_frozen_and_tuple_backed() -> None:
    assert dataclasses.is_dataclass(ChatGPTAtlasSummaryResult)
    result = ChatGPTAtlasSummaryResult(
        markdown="# Atlas Summary\n",
        manifest=contract.build_atlas_summary_manifest(
            run_id="run-wp10-summary",
            status="draft",
            source_schema_names=[
                contract.CONVERSATION_INDEX_SCHEMA,
                contract.THREAD_INDEX_SCHEMA,
                contract.LEXICAL_SKETCH_SCHEMA,
                contract.THREAD_EMBEDDING_METADATA_SCHEMA,
                contract.TOPIC_CLUSTER_SCHEMA,
            ],
            sections=["candidate_wings_rooms"],
            counts={"topic_clusters": 1},
        ),
        relative_path="atlas_summary.md",
        warnings=(),
    )
    assert isinstance(result.markdown, str)
    assert isinstance(result.manifest, dict)
    assert isinstance(result.relative_path, str)
    assert isinstance(result.warnings, tuple)
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.markdown = ""


def test_build_chatgpt_atlas_summary_emits_contract_valid_manifest_and_expected_sections() -> None:
    result = build_chatgpt_atlas_summary(
        _topic_cluster_rows(),
        run_id="run-wp10-summary",
        source_counts=_source_counts(),
        source_errors=_source_errors(),
        relative_path="reports/atlas_summary.md",
    )

    assert result.relative_path == "reports/atlas_summary.md"
    assert result.manifest["relative_path"] == "reports/atlas_summary.md"
    assert contract.validate_row(contract.ATLAS_SUMMARY_MANIFEST_SCHEMA, result.manifest) == result.manifest
    assert result.manifest["counts"]["topic_clusters"] == 4
    assert result.manifest["counts"]["conversation_index"] == 3
    assert result.warnings
    assert all(isinstance(item, str) for item in result.warnings)

    markdown = result.markdown.lower()
    assert "candidate wings/rooms" in markdown
    assert "cluster sizes" in markdown
    assert "evidence titles" in markdown
    assert "top terms" in markdown
    assert "representative excerpts" in markdown
    assert "mixed/noisy clusters" in markdown
    assert "source errors" in markdown
    assert "postgres tuning checklist" in markdown
    assert "privacy review notes" in markdown
    assert "index scan" in markdown
    assert "gdpr" in markdown
    assert "liability clause" in markdown
    assert "sparse one-off fragment" in markdown
    assert "parse failed" in markdown
    assert "missing message mapping" in markdown


def test_build_chatgpt_atlas_summary_is_deterministic_and_input_order_independent() -> None:
    rows = _topic_cluster_rows()
    result_a = build_chatgpt_atlas_summary(
        rows,
        run_id="run-wp10-summary",
        source_counts=_source_counts(),
        source_errors=_source_errors(),
    )
    result_b = build_chatgpt_atlas_summary(
        rows,
        run_id="run-wp10-summary",
        source_counts=_source_counts(),
        source_errors=_source_errors(),
    )
    result_c = build_chatgpt_atlas_summary(
        tuple(reversed(rows)),
        run_id="run-wp10-summary",
        source_counts=_source_counts(),
        source_errors=_source_errors(),
    )

    assert result_a == result_b
    assert result_a.markdown == result_b.markdown == result_c.markdown
    assert result_a.manifest == result_b.manifest == result_c.manifest
    assert result_a.warnings == result_b.warnings == result_c.warnings


def test_write_chatgpt_atlas_summary_writes_only_under_run_dir(tmp_path: Path) -> None:
    if write_chatgpt_atlas_summary is None:
        pytest.skip("write_chatgpt_atlas_summary is not implemented yet")

    run_dir = tmp_path / "atlas-run"
    result = write_chatgpt_atlas_summary(
        _topic_cluster_rows(),
        run_dir,
        run_id="run-wp10-summary",
        source_counts=_source_counts(),
        source_errors=_source_errors(),
        relative_path="nested/atlas_summary.md",
    )

    written_path = run_dir / result.relative_path
    assert result.relative_path == "nested/atlas_summary.md"
    assert written_path.exists()
    assert written_path.read_text(encoding="utf-8") == result.markdown
    assert written_path.resolve().is_relative_to(run_dir.resolve())
    assert contract.validate_row(contract.ATLAS_SUMMARY_MANIFEST_SCHEMA, result.manifest) == result.manifest
