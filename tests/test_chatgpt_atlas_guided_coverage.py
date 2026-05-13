from __future__ import annotations

import dataclasses

import pytest

from mempalace import chatgpt_archive_atlas_contract as atlas_contract
from mempalace import chatgpt_atlas_guided_contract as guided_contract
from mempalace import chatgpt_atlas_guided_coverage as coverage


RUN_ID = "20260512T150000Z_atlas_guided_coverage"
ATLAS_RUN_ID = "atlas_full2_20260512T0412Z_2fc8ac5"


def _make_bridge_row(
    cluster_id: str,
    *,
    bridge_status: str,
    thread_ids: list[str],
    candidate_id: str | None = None,
    candidate_key: str | None = None,
    mixed_reasons: list[str] | None = None,
) -> dict[str, object]:
    return guided_contract.build_candidate_bridge_record(
        run_id=RUN_ID,
        atlas_run_id=ATLAS_RUN_ID,
        candidate_id=candidate_id,
        candidate_key=candidate_key,
        bridge_status=bridge_status,
        atlas_cluster_id=cluster_id,
        atlas_cluster_status=bridge_status,
        topic_label="Topic",
        label="Topic",
        definition="Definition",
        thread_ids=thread_ids,
        top_terms=[{"term": "topic", "count": 1}],
        evidence_titles=["Evidence"],
        representative_thread_ids=thread_ids[:1],
        representative_excerpts=["Representative excerpt"],
        mixed_reasons=mixed_reasons or [],
    )


def _make_thread_row(thread_id: str, *, ordinal: int) -> dict[str, object]:
    return atlas_contract.build_thread_index_row(
        run_id=ATLAS_RUN_ID,
        thread_id=thread_id,
        logical_source_id=f"logical-{thread_id}",
        conversation_id=f"conversation-{thread_id}",
        conversation_title=f"Conversation {thread_id}",
        source_hash=f"hash-{thread_id}",
        thread_index=ordinal,
        message_start_index=ordinal * 10,
        message_end_index=ordinal * 10 + 3,
        char_start=ordinal * 100,
        char_end=ordinal * 100 + 40,
        user_message_count=2,
        assistant_message_count=2,
        char_count=40,
        title_hint=f"Hint {thread_id}",
        representative_excerpt=f"Excerpt {thread_id}",
    )


def _assert_valid_result(result: coverage.ChatGPTAtlasGuidedCoverageResult) -> None:
    assert isinstance(result.rows, tuple)
    assert guided_contract.validate_row(
        guided_contract.CANDIDATE_COVERAGE_REPORT_SCHEMA, result.report
    ) == result.report
    for row in result.rows:
        assert row["schema"] == guided_contract.THREAD_CANDIDATE_LOOKUP_SCHEMA
        assert guided_contract.validate_row(row["schema"], row) == row


def test_public_api_dataclass_is_frozen_and_tuple_backed() -> None:
    assert dataclasses.is_dataclass(coverage.ChatGPTAtlasGuidedCoverageResult)
    result = coverage.ChatGPTAtlasGuidedCoverageResult(rows=(), report={})
    assert isinstance(result.rows, tuple)
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.rows = ()


def test_builds_mapped_mixed_noise_and_unmapped_rows_with_coverage_report() -> None:
    result = coverage.build_chatgpt_atlas_guided_coverage(
        (
            _make_bridge_row(
                "cluster-001",
                bridge_status="candidate",
                thread_ids=["thread-001"],
                candidate_id="cand_devops__postgres_latency",
                candidate_key="devops:postgres_latency",
            ),
            _make_bridge_row(
                "cluster-002",
                bridge_status="mixed",
                thread_ids=["thread-002"],
                mixed_reasons=["multiple_candidate_topics"],
            ),
            _make_bridge_row(
                "cluster-003",
                bridge_status="noise",
                thread_ids=["thread-003"],
                mixed_reasons=["low_coherence"],
            ),
        ),
        (
            _make_thread_row("thread-001", ordinal=1),
            _make_thread_row("thread-002", ordinal=2),
            _make_thread_row("thread-003", ordinal=3),
            _make_thread_row("thread-004", ordinal=4),
        ),
        run_id=RUN_ID,
    )

    _assert_valid_result(result)
    mapped, mixed, noise, unmapped = result.rows

    assert mapped["thread_id"] == "thread-001"
    assert mapped["lookup_status"] == "mapped"
    assert mapped["candidate_ids"] == ["cand_devops__postgres_latency"]
    assert mapped["candidate_keys"] == ["devops:postgres_latency"]
    assert mapped["cluster_ids"] == ["cluster-001"]
    assert mapped["primary_candidate_id"] == "cand_devops__postgres_latency"
    assert mapped["reason_codes"] == ["candidate_cluster_member"]
    assert mapped["source_thread_ref"] == "thread_index.jsonl#1"

    assert mixed["thread_id"] == "thread-002"
    assert mixed["lookup_status"] == "mixed"
    assert mixed["candidate_ids"] == []
    assert mixed["candidate_keys"] == []
    assert mixed["cluster_ids"] == ["cluster-002"]
    assert mixed["reason_codes"] == [
        "mixed_cluster_member",
        "mixed_without_candidate_identity",
    ]
    assert mixed["source_thread_ref"] == "thread_index.jsonl#2"

    assert noise["thread_id"] == "thread-003"
    assert noise["lookup_status"] == "noise"
    assert noise["candidate_ids"] == []
    assert noise["candidate_keys"] == []
    assert noise["cluster_ids"] == ["cluster-003"]
    assert noise["reason_codes"] == ["noise_cluster_member"]
    assert noise["source_thread_ref"] == "thread_index.jsonl#3"

    assert unmapped["thread_id"] == "thread-004"
    assert unmapped["lookup_status"] == "unmapped"
    assert unmapped["candidate_ids"] == []
    assert unmapped["candidate_keys"] == []
    assert unmapped["cluster_ids"] == []
    assert unmapped["reason_codes"] == ["not_in_candidate_bridge"]
    assert unmapped["source_thread_ref"] == "thread_index.jsonl#4"

    assert result.report["status"] == "needs_review"
    assert result.report["total_threads"] == 4
    assert result.report["mapped_threads"] == 1
    assert result.report["mixed_threads"] == 1
    assert result.report["noise_threads"] == 1
    assert result.report["unmapped_threads"] == 1
    assert result.report["candidate_count"] == 1
    assert result.report["cluster_count"] == 3
    assert result.report["duplicate_thread_refs"] == []
    assert result.report["missing_thread_refs"] == []
    assert result.report["counts"] == {
        "bridge_records": 3,
        "bridge_thread_refs": 3,
        "candidate_bridge_records": 1,
        "duplicate_thread_ref_count": 0,
        "mapped_threads": 1,
        "missing_thread_ref_count": 0,
        "mixed_bridge_records": 1,
        "mixed_threads": 1,
        "noise_bridge_records": 1,
        "noise_threads": 1,
        "thread_index_rows": 4,
        "unmapped_threads": 1,
    }


def test_duplicate_and_missing_bridge_refs_are_reported_and_mixed_rows_keep_candidates() -> None:
    result = coverage.build_chatgpt_atlas_guided_coverage(
        (
            _make_bridge_row(
                "cluster-010",
                bridge_status="candidate",
                thread_ids=["thread-010"],
                candidate_id="cand_devops__postgres_latency",
                candidate_key="devops:postgres_latency",
            ),
            _make_bridge_row(
                "cluster-011",
                bridge_status="mixed",
                thread_ids=["thread-010", "thread-missing"],
                candidate_id="cand_product__release_planning",
                candidate_key="product:release_planning",
                mixed_reasons=["dominant_candidate_with_noise"],
            ),
        ),
        (_make_thread_row("thread-010", ordinal=1),),
        run_id=RUN_ID,
    )

    _assert_valid_result(result)
    row = result.rows[0]
    assert row["lookup_status"] == "mixed"
    assert row["candidate_ids"] == [
        "cand_devops__postgres_latency",
        "cand_product__release_planning",
    ]
    assert row["candidate_keys"] == [
        "devops:postgres_latency",
        "product:release_planning",
    ]
    assert row["primary_candidate_id"] == "cand_devops__postgres_latency"
    assert row["primary_candidate_key"] == "devops:postgres_latency"
    assert row["cluster_ids"] == ["cluster-010", "cluster-011"]
    assert row["reason_codes"] == [
        "candidate_cluster_member",
        "mixed_cluster_member",
        "duplicate_bridge_thread_ref",
    ]

    assert result.report["candidate_count"] == 2
    assert result.report["cluster_count"] == 2
    assert result.report["duplicate_thread_refs"] == [
        {"thread_id": "thread-010", "cluster_ids": ["cluster-010", "cluster-011"]}
    ]
    assert result.report["missing_thread_refs"] == ["thread-missing"]
    assert result.report["counts"]["duplicate_thread_ref_count"] == 1
    assert result.report["counts"]["missing_thread_ref_count"] == 1


@pytest.mark.parametrize(
    ("bridge_rows", "thread_rows", "expected"),
    [
        (
            (
                {
                    "schema": guided_contract.THREAD_CANDIDATE_LOOKUP_SCHEMA,
                    "run_id": RUN_ID,
                    "atlas_run_id": ATLAS_RUN_ID,
                },
            ),
            (_make_thread_row("thread-001", ordinal=1),),
            "row schema must be",
        ),
        (
            (
                _make_bridge_row(
                    "cluster-001",
                    bridge_status="candidate",
                    thread_ids=["thread-001"],
                    candidate_id="cand_devops__postgres_latency",
                    candidate_key="devops:postgres_latency",
                ),
            ),
            (
                {
                    "schema": guided_contract.CANDIDATE_BRIDGE_RECORD_SCHEMA,
                    "run_id": RUN_ID,
                    "atlas_run_id": ATLAS_RUN_ID,
                },
            ),
            "row schema must be",
        ),
    ],
)
def test_invalid_bridge_or_thread_rows_are_rejected(
    bridge_rows: tuple[dict[str, object], ...],
    thread_rows: tuple[dict[str, object], ...],
    expected: str,
) -> None:
    with pytest.raises(ValueError, match=expected):
        coverage.build_chatgpt_atlas_guided_coverage(bridge_rows, thread_rows, run_id=RUN_ID)


def test_output_is_deterministic() -> None:
    bridge_rows = (
        _make_bridge_row(
            "cluster-001",
            bridge_status="candidate",
            thread_ids=["thread-001", "thread-002"],
            candidate_id="cand_devops__postgres_latency",
            candidate_key="devops:postgres_latency",
        ),
        _make_bridge_row(
            "cluster-002",
            bridge_status="noise",
            thread_ids=["thread-003"],
            mixed_reasons=["low_coherence"],
        ),
    )
    thread_rows = (
        _make_thread_row("thread-001", ordinal=1),
        _make_thread_row("thread-002", ordinal=2),
        _make_thread_row("thread-003", ordinal=3),
    )

    result_a = coverage.build_chatgpt_atlas_guided_coverage(
        bridge_rows,
        thread_rows,
        run_id=RUN_ID,
    )
    result_b = coverage.build_chatgpt_atlas_guided_coverage(
        bridge_rows,
        thread_rows,
        run_id=RUN_ID,
    )

    _assert_valid_result(result_a)
    assert result_a == result_b
