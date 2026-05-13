from __future__ import annotations

import dataclasses

import pytest

from mempalace import chatgpt_archive_atlas_contract as atlas_contract
from mempalace import chatgpt_atlas_guided_bridge as bridge
from mempalace import chatgpt_atlas_guided_contract as guided_contract


RUN_ID = "20260512T130000Z_atlas_guided_bridge"
ATLAS_RUN_ID = "atlas_full2_20260512T0412Z_2fc8ac5"


def _make_cluster_row(
    cluster_id: str,
    *,
    status: str,
    topic_label: str | None,
    thread_ids: list[str],
    top_terms: list[dict[str, object]],
    evidence_titles: list[str] | None = None,
    representative_thread_ids: list[str] | None = None,
    representative_excerpts: list[str] | None = None,
    mixed_reasons: list[str] | None = None,
) -> dict[str, object]:
    return atlas_contract.build_topic_cluster_row(
        run_id=ATLAS_RUN_ID,
        cluster_id=cluster_id,
        status=status,
        topic_label=topic_label,
        thread_ids=thread_ids,
        top_terms=top_terms,
        evidence_titles=evidence_titles or [],
        representative_thread_ids=representative_thread_ids or [],
        representative_excerpts=representative_excerpts or [],
        mixed_reasons=mixed_reasons or [],
    )


def _assert_valid_bridge_rows(rows: tuple[dict[str, object], ...]) -> None:
    assert isinstance(rows, tuple)
    for row in rows:
        assert row["schema"] == guided_contract.CANDIDATE_BRIDGE_RECORD_SCHEMA
        assert guided_contract.validate_row(row["schema"], row) == row
        assert not (set(row) & guided_contract.FORBIDDEN_FIELD_NAMES)


def test_public_api_dataclass_is_frozen_and_tuple_backed() -> None:
    assert dataclasses.is_dataclass(bridge.ChatGPTAtlasGuidedBridgeResult)
    result = bridge.ChatGPTAtlasGuidedBridgeResult(rows=(), warnings=())
    assert isinstance(result.rows, tuple)
    assert isinstance(result.warnings, tuple)
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.rows = ()


def test_candidate_cluster_rows_become_candidate_bridge_records() -> None:
    rows = bridge.build_chatgpt_atlas_guided_bridge_rows(
        (
            _make_cluster_row(
                "cluster-001",
                status="candidate",
                topic_label="Postgres latency",
                thread_ids=["thread-001", "thread-002"],
                top_terms=[
                    {"term": "postgres", "count": 6},
                    {"term": "latency", "count": 4},
                ],
                evidence_titles=["Postgres tuning"],
                representative_thread_ids=["thread-001"],
                representative_excerpts=["EXPLAIN ANALYZE shows latency."],
            ),
        ),
        run_id=RUN_ID,
    )

    _assert_valid_bridge_rows(rows)
    row = rows[0]
    assert row["atlas_run_id"] == ATLAS_RUN_ID
    assert row["candidate_key"] == "devops:postgres_latency"
    assert row["candidate_id"] == "cand_devops__postgres_latency"
    assert row["canonical_wing"] == "devops"
    assert row["canonical_room"] == "postgres_latency"
    assert row["atlas_cluster_id"] == "cluster-001"
    assert row["atlas_cluster_status"] == "candidate"
    assert row["bridge_status"] == "candidate"
    assert row["representative_thread_ids"] == ["thread-001"]
    assert row["representative_excerpts"] == ["EXPLAIN ANALYZE shows latency."]
    assert row["top_terms"] == [
        {"term": "postgres", "count": 6},
        {"term": "latency", "count": 4},
    ]


def test_mixed_cluster_rows_may_resolve_or_remain_unresolved() -> None:
    rows = bridge.build_chatgpt_atlas_guided_bridge_rows(
        (
            _make_cluster_row(
                "cluster-mixed-001",
                status="mixed",
                topic_label="Postgres and sprint planning",
                thread_ids=["thread-010", "thread-011"],
                top_terms=[
                    {"term": "postgres", "count": 4},
                    {"term": "planning", "count": 4},
                ],
                evidence_titles=["Mixed operational planning"],
                representative_thread_ids=["thread-010"],
                representative_excerpts=[
                    "This cluster combines database work with planning notes."
                ],
                mixed_reasons=["multiple_candidate_topics"],
            ),
            _make_cluster_row(
                "cluster-mixed-002",
                status="mixed",
                topic_label="Postgres latency with unrelated chatter",
                thread_ids=["thread-012"],
                top_terms=[
                    {"term": "postgres", "count": 5},
                    {"term": "latency", "count": 3},
                    {"term": "chatter", "count": 1},
                ],
                evidence_titles=["Database tuning drift"],
                representative_thread_ids=["thread-012"],
                representative_excerpts=["Most of the thread is still about database latency."],
                mixed_reasons=["dominant_candidate_with_noise"],
            ),
        ),
        run_id=RUN_ID,
    )

    _assert_valid_bridge_rows(rows)
    unresolved, resolved = rows

    assert unresolved["bridge_status"] == "mixed"
    assert unresolved["candidate_id"] is None
    assert unresolved["candidate_key"] is None
    assert unresolved["canonical_wing"] is None
    assert unresolved["canonical_room"] is None
    assert unresolved["mixed_reasons"] == ["multiple_candidate_topics"]

    assert resolved["bridge_status"] == "mixed"
    assert resolved["candidate_key"] == "devops:postgres_latency"
    assert resolved["candidate_id"] == "cand_devops__postgres_latency"
    assert resolved["canonical_wing"] == "devops"
    assert resolved["canonical_room"] == "postgres_latency"
    assert resolved["mixed_reasons"] == ["dominant_candidate_with_noise"]


def test_noise_cluster_rows_preserve_evidence_without_candidate_identity() -> None:
    rows = bridge.build_chatgpt_atlas_guided_bridge_rows(
        (
            _make_cluster_row(
                "cluster-noise-001",
                status="noise",
                topic_label="Assorted fragments",
                thread_ids=["thread-noise-001", "thread-noise-002"],
                top_terms=[{"term": "misc", "count": 4}],
                evidence_titles=["Untitled fragment"],
                representative_thread_ids=["thread-noise-001"],
                representative_excerpts=[
                    "A short fragment without durable room semantics."
                ],
                mixed_reasons=["low_coherence", "no_canonical_candidate"],
            ),
        ),
        run_id=RUN_ID,
    )

    _assert_valid_bridge_rows(rows)
    row = rows[0]
    assert row["bridge_status"] == "noise"
    assert row["candidate_id"] is None
    assert row["candidate_key"] is None
    assert row["canonical_wing"] is None
    assert row["canonical_room"] is None
    assert row["atlas_cluster_id"] == "cluster-noise-001"
    assert row["evidence_titles"] == ["Untitled fragment"]
    assert row["representative_thread_ids"] == ["thread-noise-001"]
    assert row["mixed_reasons"] == ["low_coherence", "no_canonical_candidate"]


@pytest.mark.parametrize(
    ("bad_rows", "expected"),
    [
            (
                (
                    {
                    "schema": guided_contract.CANDIDATE_BRIDGE_RECORD_SCHEMA,
                    "run_id": RUN_ID,
                    "atlas_run_id": ATLAS_RUN_ID,
                },
            ),
            "row schema must be",
        ),
        (
            (
                {
                    "schema": atlas_contract.TOPIC_CLUSTER_SCHEMA,
                    "run_id": ATLAS_RUN_ID,
                    "cluster_id": "cluster-invalid",
                    "status": "candidate",
                    "topic_label": "Broken cluster",
                    "thread_ids": ["thread-bad"],
                    "size": 1,
                    "top_terms": [{"term": "postgres", "count": "bad"}],
                    "evidence_titles": [],
                    "representative_thread_ids": [],
                    "representative_excerpts": [],
                    "mixed_reasons": [],
                        "safety_contract": atlas_contract.safety_contract(),
                    },
                ),
            r"top_terms\[\]\.count",
            ),
        ],
    )
def test_invalid_atlas_rows_or_schema_are_rejected(
    bad_rows: tuple[dict[str, object], ...],
    expected: str,
) -> None:
    with pytest.raises(ValueError, match=expected):
        bridge.build_chatgpt_atlas_guided_bridge_rows(bad_rows, run_id=RUN_ID)


def test_output_is_deterministic_and_disambiguates_duplicate_candidate_keys() -> None:
    cluster_rows = (
        _make_cluster_row(
            "cluster-dup-001",
            status="candidate",
            topic_label="Release planning",
            thread_ids=["thread-101"],
            top_terms=[
                {"term": "release", "count": 4},
                {"term": "planning", "count": 3},
            ],
            evidence_titles=["Release planning notes"],
        ),
        _make_cluster_row(
            "cluster-dup-002",
            status="candidate",
            topic_label="Release planning",
            thread_ids=["thread-102"],
            top_terms=[
                {"term": "release", "count": 5},
                {"term": "planning", "count": 2},
            ],
            evidence_titles=["Second release planning pass"],
        ),
    )

    result_a = bridge.build_chatgpt_atlas_guided_bridge(cluster_rows, run_id=RUN_ID)
    result_b = bridge.build_chatgpt_atlas_guided_bridge(cluster_rows, run_id=RUN_ID)

    _assert_valid_bridge_rows(result_a.rows)
    assert result_a == result_b
    assert len(result_a.warnings) == 2

    keys = [row["candidate_key"] for row in result_a.rows]
    assert keys[0] != keys[1]
    assert all(str(key).startswith("work_admin:release_planning_") for key in keys)
    assert all(str(row["candidate_id"]).startswith("cand_work_admin__release_planning_") for row in result_a.rows)
