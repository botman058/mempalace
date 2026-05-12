from __future__ import annotations

import dataclasses
from typing import Any

import pytest

from mempalace import chatgpt_archive_atlas_contract as contract

_topic_cluster_module = pytest.importorskip(
    "mempalace.chatgpt_archive_atlas_topic_cluster",
    reason="topic cluster implementation is not present yet",
)
ChatGPTAtlasTopicClusterResult = _topic_cluster_module.ChatGPTAtlasTopicClusterResult
build_chatgpt_topic_cluster_rows = _topic_cluster_module.build_chatgpt_topic_cluster_rows
build_chatgpt_topic_clusters = _topic_cluster_module.build_chatgpt_topic_clusters


def _make_lexical_row(
    thread_id: str,
    *,
    top_terms: list[dict[str, Any]],
    keyphrases: list[str],
    excerpt: str,
) -> dict[str, Any]:
    return contract.build_lexical_sketch_row(
        run_id="run-wp09",
        thread_id=thread_id,
        logical_source_id=f"chatgpt:source:{thread_id}",
        top_terms=top_terms,
        keyphrases=keyphrases,
        domains=["example.com"],
        paths=["/tmp/example.txt"],
        commands=["echo cluster"],
        package_names=["numpy"],
        model_names=["all-MiniLM-L6-v2"],
        legal_citations=["17 USC 512"],
        capitalized_phrases=["ChatGPT"],
        representative_excerpts=[excerpt],
        noise_terms_rejected=["the"],
    )


def _make_vector_row(thread_id: str, vector: list[float]) -> dict[str, Any]:
    return {
        "run_id": "run-wp09",
        "thread_id": thread_id,
        "embedding_id": f"emb-{thread_id}",
        "vector_dimensions": len(vector),
        "vector": list(vector),
    }


def _validate_cluster_rows(rows: tuple[dict[str, Any], ...]) -> None:
    assert isinstance(rows, tuple)
    for row in rows:
        assert contract.validate_row(contract.TOPIC_CLUSTER_SCHEMA, row) == row
        assert row["safety_contract"] == contract.safety_contract()


def _status_counts(rows: tuple[dict[str, Any], ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        status = str(row["status"])
        counts[status] = counts.get(status, 0) + 1
    return counts


def test_public_api_dataclass_is_frozen_and_tuple_backed() -> None:
    assert dataclasses.is_dataclass(ChatGPTAtlasTopicClusterResult)
    result = ChatGPTAtlasTopicClusterResult(rows=(), warnings=())
    assert isinstance(result.rows, tuple)
    assert isinstance(result.warnings, tuple)
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.rows = ()


def test_deterministic_fake_vectors_return_identical_cluster_rows() -> None:
    lexical_rows = (
        _make_lexical_row(
            "thread-001",
            top_terms=[{"term": "postgres", "count": 3}],
            keyphrases=["postgres tuning"],
            excerpt="index scan tuning",
        ),
        _make_lexical_row(
            "thread-002",
            top_terms=[{"term": "postgres", "count": 2}],
            keyphrases=["postgres latency"],
            excerpt="buffer cache diagnostics",
        ),
    )
    vector_rows = (
        _make_vector_row("thread-001", [1.0, 0.0, 0.0]),
        _make_vector_row("thread-002", [0.98, 0.02, 0.0]),
    )

    rows_a = build_chatgpt_topic_cluster_rows(
        lexical_rows,
        vector_rows,
        run_id="run-wp09",
        similarity_threshold=0.82,
        min_shared_terms=1,
        max_cluster_size=8,
    )
    rows_b = build_chatgpt_topic_cluster_rows(
        lexical_rows,
        vector_rows,
        run_id="run-wp09",
        similarity_threshold=0.82,
        min_shared_terms=1,
        max_cluster_size=8,
    )

    _validate_cluster_rows(rows_a)
    assert rows_a == rows_b


def test_conservative_split_requires_both_semantic_and_lexical_evidence() -> None:
    lexical_rows = (
        _make_lexical_row(
            "thread-a",
            top_terms=[{"term": "docker", "count": 4}],
            keyphrases=["docker compose"],
            excerpt="container startup",
        ),
        _make_lexical_row(
            "thread-b",
            top_terms=[{"term": "gdpr", "count": 4}],
            keyphrases=["gdpr liability"],
            excerpt="privacy legal clause",
        ),
        _make_lexical_row(
            "thread-c",
            top_terms=[{"term": "postgres", "count": 4}],
            keyphrases=["postgres index"],
            excerpt="btree reindex",
        ),
        _make_lexical_row(
            "thread-d",
            top_terms=[{"term": "postgres", "count": 3}],
            keyphrases=["postgres index"],
            excerpt="vacuum explain",
        ),
    )
    vector_rows = (
        _make_vector_row("thread-a", [1.0, 0.0, 0.0]),
        _make_vector_row("thread-b", [0.99, 0.01, 0.0]),
        _make_vector_row("thread-c", [0.0, 1.0, 0.0]),
        _make_vector_row("thread-d", [1.0, 0.0, 0.0]),
    )

    rows = build_chatgpt_topic_cluster_rows(
        lexical_rows,
        vector_rows,
        run_id="run-wp09",
        similarity_threshold=0.82,
        min_shared_terms=1,
        max_cluster_size=8,
    )
    _validate_cluster_rows(rows)

    cluster_sets = [set(row["thread_ids"]) for row in rows]
    assert {"thread-a", "thread-b"} not in cluster_sets
    assert {"thread-c", "thread-d"} not in cluster_sets


def test_high_similarity_with_shared_terms_merges_into_candidate_cluster() -> None:
    lexical_rows = (
        _make_lexical_row(
            "thread-001",
            top_terms=[{"term": "postgres", "count": 3}, {"term": "index", "count": 2}],
            keyphrases=["postgres index"],
            excerpt="query plan and btree",
        ),
        _make_lexical_row(
            "thread-002",
            top_terms=[{"term": "postgres", "count": 2}, {"term": "vacuum", "count": 1}],
            keyphrases=["postgres tuning"],
            excerpt="vacuum analyze settings",
        ),
    )
    vector_rows = (
        _make_vector_row("thread-001", [1.0, 0.0, 0.0]),
        _make_vector_row("thread-002", [0.97, 0.03, 0.0]),
    )

    rows = build_chatgpt_topic_cluster_rows(
        lexical_rows,
        vector_rows,
        run_id="run-wp09",
    )
    _validate_cluster_rows(rows)

    candidate_rows = [row for row in rows if row["status"] == "candidate"]
    assert any(set(row["thread_ids"]) == {"thread-001", "thread-002"} for row in candidate_rows)


def test_noise_rows_are_flagged_as_noise_instead_of_forced_merge() -> None:
    lexical_rows = (
        _make_lexical_row(
            "thread-001",
            top_terms=[{"term": "x1", "count": 1}],
            keyphrases=["one-off phrase alpha"],
            excerpt="single sparse snippet",
        ),
        _make_lexical_row(
            "thread-002",
            top_terms=[{"term": "y1", "count": 1}],
            keyphrases=["one-off phrase beta"],
            excerpt="another sparse snippet",
        ),
        _make_lexical_row(
            "thread-003",
            top_terms=[{"term": "z1", "count": 1}],
            keyphrases=["one-off phrase gamma"],
            excerpt="third sparse snippet",
        ),
    )
    vector_rows = (
        _make_vector_row("thread-001", [1.0, 0.0, 0.0]),
        _make_vector_row("thread-002", [0.0, 1.0, 0.0]),
        _make_vector_row("thread-003", [0.0, 0.0, 1.0]),
    )

    rows = build_chatgpt_topic_cluster_rows(
        lexical_rows,
        vector_rows,
        run_id="run-wp09",
        similarity_threshold=0.95,
        min_shared_terms=2,
        max_cluster_size=2,
    )
    _validate_cluster_rows(rows)

    assert any(row["status"] == "noise" for row in rows)


def test_divergent_evidence_does_not_broadly_collapse() -> None:
    lexical_rows = (
        _make_lexical_row(
            "thread-001",
            top_terms=[{"term": "postgres", "count": 4}],
            keyphrases=["postgres tuning"],
            excerpt="query planning details",
        ),
        _make_lexical_row(
            "thread-002",
            top_terms=[{"term": "postgres", "count": 3}],
            keyphrases=["postgres index"],
            excerpt="index btree details",
        ),
        _make_lexical_row(
            "thread-003",
            top_terms=[{"term": "gdpr", "count": 4}],
            keyphrases=["gdpr liability"],
            excerpt="legal policy details",
        ),
        _make_lexical_row(
            "thread-004",
            top_terms=[{"term": "ssh", "count": 4}],
            keyphrases=["ssh restart"],
            excerpt="systemctl ssh restart",
        ),
    )
    vector_rows = (
        _make_vector_row("thread-001", [1.0, 0.0, 0.0]),
        _make_vector_row("thread-002", [0.98, 0.02, 0.0]),
        _make_vector_row("thread-003", [0.97, 0.03, 0.0]),
        _make_vector_row("thread-004", [0.96, 0.04, 0.0]),
    )

    rows = build_chatgpt_topic_cluster_rows(
        lexical_rows,
        vector_rows,
        run_id="run-wp09",
        similarity_threshold=0.82,
        min_shared_terms=1,
        max_cluster_size=8,
    )
    _validate_cluster_rows(rows)

    assert rows
    assert max(len(set(row["thread_ids"])) for row in rows) < len(lexical_rows)
    assert len(rows) >= 2 or any(row["status"] == "mixed" for row in rows)


def test_cluster_ids_and_representative_thread_refs_are_stable() -> None:
    lexical_rows = (
        _make_lexical_row(
            "thread-001",
            top_terms=[{"term": "postgres", "count": 3}],
            keyphrases=["postgres tuning"],
            excerpt="plan tuning",
        ),
        _make_lexical_row(
            "thread-002",
            top_terms=[{"term": "postgres", "count": 2}],
            keyphrases=["postgres tuning"],
            excerpt="vacuum tuning",
        ),
        _make_lexical_row(
            "thread-003",
            top_terms=[{"term": "ssh", "count": 3}],
            keyphrases=["ssh restart"],
            excerpt="systemctl restart ssh",
        ),
    )
    vector_rows = (
        _make_vector_row("thread-001", [1.0, 0.0, 0.0]),
        _make_vector_row("thread-002", [0.99, 0.01, 0.0]),
        _make_vector_row("thread-003", [0.0, 1.0, 0.0]),
    )

    rows_a = build_chatgpt_topic_cluster_rows(lexical_rows, vector_rows, run_id="run-wp09")
    rows_b = build_chatgpt_topic_cluster_rows(lexical_rows, vector_rows, run_id="run-wp09")
    _validate_cluster_rows(rows_a)

    by_id_a = {row["cluster_id"]: row for row in rows_a}
    by_id_b = {row["cluster_id"]: row for row in rows_b}
    assert by_id_a.keys() == by_id_b.keys()
    for cluster_id, row in by_id_a.items():
        assert cluster_id
        assert isinstance(cluster_id, str)
        assert row["representative_thread_ids"]
        assert set(row["representative_thread_ids"]).issubset(set(row["thread_ids"]))


def test_result_summary_fields_are_inspectable_via_rows_or_warnings() -> None:
    lexical_rows = (
        _make_lexical_row(
            "thread-001",
            top_terms=[{"term": "postgres", "count": 2}],
            keyphrases=["postgres tuning"],
            excerpt="query plan",
        ),
        _make_lexical_row(
            "thread-002",
            top_terms=[{"term": "gdpr", "count": 2}],
            keyphrases=["gdpr liability"],
            excerpt="policy clause",
        ),
    )
    vector_rows = (
        _make_vector_row("thread-001", [1.0, 0.0, 0.0]),
        _make_vector_row("thread-002", [0.0, 1.0, 0.0]),
    )

    result = build_chatgpt_topic_clusters(
        lexical_rows,
        vector_rows,
        run_id="run-wp09",
        similarity_threshold=0.82,
        min_shared_terms=1,
        max_cluster_size=8,
    )

    assert isinstance(result, ChatGPTAtlasTopicClusterResult)
    assert isinstance(result.rows, tuple)
    assert isinstance(result.warnings, tuple)
    _validate_cluster_rows(result.rows)
    counts = _status_counts(result.rows)
    assert sum(counts.values()) == len(result.rows)
    for warning in result.warnings:
        assert isinstance(warning, str)
