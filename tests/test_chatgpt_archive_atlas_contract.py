from __future__ import annotations

import json
from pathlib import PurePosixPath

import pytest

from mempalace import chatgpt_archive_atlas_contract as contract


RUN_ID = "20260510000102_atlas"


def _all_values(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _all_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from _all_values(item)


def _assert_jsonl_safe_and_deterministic(row):
    first = contract.canonical_json_line(row)
    second = contract.canonical_json_line(dict(reversed(list(row.items()))))
    assert first == second
    assert first.endswith("\n")
    assert json.loads(first) == row


def _assert_no_forbidden_fields(row):
    lowered = {str(value).lower() for value in _all_values(row)}
    forbidden = {"localai_base_url", "localai_token", "mcp_tool", "mcp_server", "palace_write_path"}
    assert lowered.isdisjoint(forbidden)
    contract.validate_row(row["schema"], row)


def test_progress_json_contract_is_required_key_complete_json_safe_and_deterministic():
    row = contract.build_progress(
        run_id=RUN_ID,
        phase="conversation_index",
        status="running",
        counts={"threads": 3, "conversations": 2},
        errors=0,
        warnings=1,
        started_at="2026-05-10T00:00:00Z",
        updated_at="2026-05-10T00:00:03Z",
        message="indexed conversations",
    )

    assert row["schema"] == contract.PROGRESS_SCHEMA
    assert set(contract.REQUIRED_KEYS[contract.PROGRESS_SCHEMA]).issubset(row)
    assert list(row["counts"]) == ["conversations", "threads"]
    assert row["safety_contract"]["external_services"] == []
    assert row["safety_contract"]["writes_existing_memory"] is False
    _assert_jsonl_safe_and_deterministic(row)
    _assert_no_forbidden_fields(row)


def test_artifacts_index_records_schema_names_relative_paths_and_review_flags():
    records = contract.canonical_artifact_records(
        {
            "conversation_index": 2,
            "thread_index": 4,
            "lexical_sketches": 4,
            "thread_embeddings": 4,
            "topic_clusters": 1,
        }
    )
    index = contract.build_artifacts_index(run_id=RUN_ID, artifacts=records)

    assert index["schema"] == contract.ARTIFACTS_INDEX_SCHEMA
    assert set(contract.REQUIRED_KEYS[contract.ARTIFACTS_INDEX_SCHEMA]).issubset(index)
    by_key = {row["artifact_key"]: row for row in index["artifacts"]}
    expected_keys = {
        "progress",
        "artifacts_index",
        "conversation_index",
        "thread_index",
        "lexical_sketches",
        "thread_embeddings",
        "topic_clusters",
        "atlas_summary",
    }
    assert set(by_key) == expected_keys
    assert by_key["conversation_index"]["schema_name"] == contract.CONVERSATION_INDEX_SCHEMA
    assert by_key["conversation_index"]["relative_path"] == "conversation_index.jsonl"
    assert by_key["thread_embeddings"]["relative_path"] == "thread_embeddings.jsonl"
    assert by_key["atlas_summary"]["schema_name"] == contract.ATLAS_SUMMARY_MANIFEST_SCHEMA
    assert by_key["atlas_summary"]["relative_path"] == "atlas_summary.md"
    assert all(not row["relative_path"].startswith("/") for row in index["artifacts"])
    assert all(".." not in row["relative_path"].split("/") for row in index["artifacts"])
    assert all(isinstance(row["review_safe"], bool) for row in index["artifacts"])
    _assert_jsonl_safe_and_deterministic(index)
    _assert_no_forbidden_fields(index)


def test_conversation_index_jsonl_row_contract():
    row = contract.build_conversation_index_row(
        run_id=RUN_ID,
        logical_source_id="chatgpt:source:001",
        conversation_id="conv-1",
        title="Postgres tuning",
        source_relative_path=PurePosixPath("exports/2026/conversations.json"),
        source_hash="sha256:abc123",
        source_ordinal=7,
        create_time="2026-05-01T12:00:00Z",
        update_time="2026-05-02T12:00:00Z",
        model_slug="gpt-4o",
        plugin_ids=["browser"],
        message_count=5,
        user_message_count=3,
        assistant_message_count=2,
        char_count=1234,
        first_user_excerpt="How do I tune this query?",
        top_user_prompt_excerpts=["EXPLAIN ANALYZE output", "index scan question"],
    )

    assert row["schema"] == contract.CONVERSATION_INDEX_SCHEMA
    assert set(contract.REQUIRED_KEYS[contract.CONVERSATION_INDEX_SCHEMA]).issubset(row)
    assert row["source_relative_path"] == "exports/2026/conversations.json"
    _assert_jsonl_safe_and_deterministic(row)
    _assert_no_forbidden_fields(row)


def test_thread_index_jsonl_row_contract():
    row = contract.build_thread_index_row(
        run_id=RUN_ID,
        thread_id="thread-001",
        logical_source_id="chatgpt:source:001",
        conversation_id="conv-1",
        conversation_title="Mixed work",
        source_hash="sha256:abc123",
        thread_index=0,
        message_start_index=0,
        message_end_index=3,
        char_start=0,
        char_end=900,
        user_message_count=2,
        assistant_message_count=2,
        char_count=900,
        title_hint="postgres latency",
        representative_excerpt="Let's debug postgres latency.",
    )

    assert row["schema"] == contract.THREAD_INDEX_SCHEMA
    assert set(contract.REQUIRED_KEYS[contract.THREAD_INDEX_SCHEMA]).issubset(row)
    _assert_jsonl_safe_and_deterministic(row)
    _assert_no_forbidden_fields(row)


def test_lexical_sketch_jsonl_row_contract():
    row = contract.build_lexical_sketch_row(
        run_id=RUN_ID,
        thread_id="thread-001",
        logical_source_id="chatgpt:source:001",
        top_terms=[{"term": "postgres", "count": 4}, {"term": "index", "count": 2}],
        keyphrases=["postgres latency"],
        domains=["example.com"],
        paths=["/var/log/postgresql/postgresql.log"],
        commands=["psql -c 'select 1'"],
        package_names=["psycopg"],
        model_names=["gpt-4o"],
        legal_citations=["17 USC 512"],
        capitalized_phrases=["PostgreSQL"],
        representative_excerpts=["query plan excerpt"],
        noise_terms_rejected=["the", "and", "you"],
    )

    assert row["schema"] == contract.LEXICAL_SKETCH_SCHEMA
    assert set(contract.REQUIRED_KEYS[contract.LEXICAL_SKETCH_SCHEMA]).issubset(row)
    assert row["top_terms"][0] == {"term": "postgres", "count": 4}
    assert "the" in row["noise_terms_rejected"]
    _assert_jsonl_safe_and_deterministic(row)
    _assert_no_forbidden_fields(row)


def test_thread_embedding_metadata_row_contract_has_no_vector_payload_or_remote_fields():
    row = contract.build_thread_embedding_metadata_row(
        run_id=RUN_ID,
        thread_id="thread-001",
        embedding_id="emb-001",
        embedding_model="all-MiniLM-L6-v2",
        effective_device="cuda",
        vector_dimensions=384,
        source_text_sha256="abc123",
        source_text_chars=900,
        batch_index=0,
        status="embedded",
    )

    assert row["schema"] == contract.THREAD_EMBEDDING_METADATA_SCHEMA
    assert set(contract.REQUIRED_KEYS[contract.THREAD_EMBEDDING_METADATA_SCHEMA]).issubset(row)
    assert "vector" not in row
    assert "embedding" in row["schema"]
    _assert_jsonl_safe_and_deterministic(row)
    _assert_no_forbidden_fields(row)


def test_topic_clusters_jsonl_row_contract():
    row = contract.build_topic_cluster_row(
        run_id=RUN_ID,
        cluster_id="cluster-001",
        status="candidate",
        topic_label="postgres performance",
        thread_ids=["thread-001", "thread-002"],
        top_terms=[{"term": "postgres", "count": 7}],
        evidence_titles=["Postgres tuning"],
        representative_thread_ids=["thread-001"],
        representative_excerpts=["index scan representative excerpt"],
        mixed_reasons=[],
    )

    assert row["schema"] == contract.TOPIC_CLUSTER_SCHEMA
    assert set(contract.REQUIRED_KEYS[contract.TOPIC_CLUSTER_SCHEMA]).issubset(row)
    assert row["size"] == 2
    _assert_jsonl_safe_and_deterministic(row)
    _assert_no_forbidden_fields(row)


def test_atlas_summary_markdown_manifest_contract():
    row = contract.build_atlas_summary_manifest(
        run_id=RUN_ID,
        status="draft",
        source_schema_names=[
            contract.CONVERSATION_INDEX_SCHEMA,
            contract.THREAD_INDEX_SCHEMA,
            contract.LEXICAL_SKETCH_SCHEMA,
            contract.THREAD_EMBEDDING_METADATA_SCHEMA,
            contract.TOPIC_CLUSTER_SCHEMA,
        ],
        sections=[
            "candidate_wings_rooms",
            "cluster_sizes",
            "evidence_titles",
            "top_terms",
            "representative_excerpts",
            "mixed_noisy_clusters",
        ],
        counts={"clusters": 1, "threads": 2},
    )

    assert row["schema"] == contract.ATLAS_SUMMARY_MANIFEST_SCHEMA
    assert set(contract.REQUIRED_KEYS[contract.ATLAS_SUMMARY_MANIFEST_SCHEMA]).issubset(row)
    assert row["relative_path"] == "atlas_summary.md"
    assert "mixed_noisy_clusters" in row["sections"]
    _assert_jsonl_safe_and_deterministic(row)
    _assert_no_forbidden_fields(row)


@pytest.mark.parametrize(
    "bad_run_id",
    ["", "../run", "/tmp/run", "run id", ".", "..", "run/child"],
)
def test_builders_reject_obvious_invalid_run_ids(bad_run_id):
    with pytest.raises(ValueError):
        contract.build_progress(run_id=bad_run_id, phase="source", status="running")


@pytest.mark.parametrize(
    "bad_path",
    ["", "/abs/conversation_index.jsonl", "../conversation_index.jsonl", "a/../b.jsonl", "C:/tmp/x.jsonl"],
)
def test_artifact_index_rejects_absolute_or_parent_relative_paths(bad_path):
    with pytest.raises(ValueError):
        contract.build_artifact_index_record(
            artifact_key="conversation_index",
            schema_name=contract.CONVERSATION_INDEX_SCHEMA,
            relative_path=bad_path,
            phase="conversation_index",
            content_type="application/jsonl",
            count=0,
            append_only=True,
            review_safe=True,
            dashboard_safe=True,
        )


@pytest.mark.parametrize("bad_status", ["done", "ok", "", "published"])
def test_progress_rejects_invalid_statuses(bad_status):
    with pytest.raises(ValueError):
        contract.build_progress(run_id=RUN_ID, phase="source", status=bad_status)


def test_embedding_and_cluster_statuses_are_bounded():
    with pytest.raises(ValueError):
        contract.build_thread_embedding_metadata_row(
            run_id=RUN_ID,
            thread_id="thread-001",
            embedding_id="emb-001",
            embedding_model="all-MiniLM-L6-v2",
            effective_device="cuda",
            vector_dimensions=384,
            source_text_sha256="abc123",
            source_text_chars=900,
            batch_index=0,
            status="uploaded",
        )
    with pytest.raises(ValueError):
        contract.build_topic_cluster_row(
            run_id=RUN_ID,
            cluster_id="cluster-001",
            status="merged",
            topic_label="postgres performance",
            thread_ids=["thread-001"],
            top_terms=[{"term": "postgres", "count": 1}],
        )


def test_validator_rejects_non_json_safe_and_forbidden_write_service_fields():
    row = contract.build_progress(run_id=RUN_ID, phase="source", status="running")
    unsafe = dict(row)
    unsafe["not_json"] = {"set"}
    with pytest.raises(ValueError):
        contract.canonical_json_line(unsafe)

    forbidden = dict(row)
    forbidden["localai_base_url"] = "http://snow-white-iii:8080/v1"
    with pytest.raises(ValueError):
        contract.canonical_json_line(forbidden)

    nested_forbidden = dict(row)
    nested_forbidden["nested"] = {"mcp_tool": "write_drawer"}
    with pytest.raises(ValueError):
        contract.canonical_json_line(nested_forbidden)

    broad_forbidden = dict(row)
    broad_forbidden["localai_config"] = {"url": "http://snow-white-iii:8080/v1"}
    with pytest.raises(ValueError):
        contract.canonical_json_line(broad_forbidden)
