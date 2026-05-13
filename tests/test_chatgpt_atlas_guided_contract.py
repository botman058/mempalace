from __future__ import annotations

import json
from pathlib import PurePosixPath

import pytest

from mempalace import chatgpt_atlas_guided_contract as contract


RUN_ID = "20260512T120000Z_atlas_guided"
ATLAS_RUN_ID = "atlas_full2_20260512T0412Z_2fc8ac5"
CANDIDATE_ID = "cand_devops__postgres_latency"
CANDIDATE_KEY = "devops:postgres_latency"


def _assert_jsonl_safe_and_deterministic(row: dict[str, object]) -> None:
    first = contract.canonical_json_line(row)
    second = contract.canonical_json_line(dict(reversed(list(row.items()))))
    assert first == second
    assert first.endswith("\n")
    assert json.loads(first) == row


def _assert_valid(row: dict[str, object]) -> None:
    assert set(contract.REQUIRED_KEYS[row["schema"]]).issubset(row)
    assert contract.validate_row(row["schema"], row) == row
    _assert_jsonl_safe_and_deterministic(row)


def test_progress_artifact_index_and_canonical_artifact_records_contracts() -> None:
    progress = contract.build_progress(
        run_id=RUN_ID,
        atlas_run_id=ATLAS_RUN_ID,
        status="running",
        current_phase="bridge",
        phase_status="running",
        phase_order=["bridge", "coverage", "extraction", "reconciliation"],
        counts={"candidate_records": 1, "thread_lookups": 2},
        errors=0,
        warnings=1,
        started_at="2026-05-12T12:00:00Z",
        updated_at="2026-05-12T12:01:00Z",
    )
    _assert_valid(progress)
    assert progress["no_publish"] is True
    assert progress["publish_enabled"] is False
    assert progress["safety_contract"]["external_services"] == []
    assert progress["safety_contract"]["writes_existing_memory"] is False

    records = contract.canonical_artifact_records(
        {
            "candidate_bridge_records": 1,
            "atlas_thread_candidates": 2,
            "atlas_candidate_coverage": 1,
            "extraction_records": 3,
            "reconciled_signals": 1,
        }
    )
    index = contract.build_artifacts_index(
        run_id=RUN_ID,
        atlas_run_id=ATLAS_RUN_ID,
        artifacts=records,
    )
    _assert_valid(index)

    by_key = {item["artifact_key"]: item for item in index["artifacts"]}
    assert set(by_key) == {
        "progress",
        "artifacts_index",
        "candidate_bridge_records",
        "atlas_thread_candidates",
        "atlas_candidate_coverage",
        "extraction_records",
        "invalid_outputs",
        "reconciled_signals",
        "publish_checkpoint",
    }
    assert by_key["extraction_records"]["contains_raw_model_output"] is True
    assert by_key["extraction_records"]["dashboard_safe"] is False
    assert by_key["publish_checkpoint"]["publish_gate_required"] is True
    assert by_key["publish_checkpoint"]["privacy_level"] == "review_only"
    assert all(not item["relative_path"].startswith("/") for item in index["artifacts"])


def test_candidate_bridge_record_contract() -> None:
    row = contract.build_candidate_record(
        run_id=RUN_ID,
        atlas_run_id=ATLAS_RUN_ID,
        candidate_id=CANDIDATE_ID,
        candidate_key=CANDIDATE_KEY,
        bridge_status="candidate",
        atlas_cluster_id="cluster-001",
        atlas_cluster_status="candidate",
        topic_label="Postgres latency",
        label="Postgres latency",
        definition="Operational notes about PostgreSQL query and service latency.",
        thread_ids=["thread-001", "thread-002"],
        top_terms=[{"term": "postgres", "count": 6}, {"term": "latency", "count": 4}],
        evidence_titles=["Postgres tuning"],
        representative_thread_ids=["thread-001"],
        representative_excerpts=["EXPLAIN ANALYZE shows latency."],
        mixed_reasons=[],
    )

    _assert_valid(row)
    assert row["canonical_wing"] == "devops"
    assert row["canonical_room"] == "postgres_latency"
    assert row["support_thread_count"] == 2


def test_candidate_bridge_mixed_records_may_be_unresolved_or_candidate_backed() -> None:
    unresolved = contract.build_candidate_record(
        run_id=RUN_ID,
        atlas_run_id=ATLAS_RUN_ID,
        bridge_status="mixed",
        atlas_cluster_id="cluster-mixed-001",
        atlas_cluster_status="mixed",
        topic_label="Postgres and planning",
        label="Mixed Postgres planning cluster",
        definition=None,
        thread_ids=["thread-010", "thread-011"],
        top_terms=[{"term": "postgres", "count": 2}, {"term": "planning", "count": 1}],
        evidence_titles=["Mixed operational planning"],
        representative_thread_ids=["thread-010"],
        representative_excerpts=["This cluster combines database work with planning notes."],
        mixed_reasons=["multiple_candidate_topics"],
    )
    _assert_valid(unresolved)
    assert unresolved["candidate_id"] is None
    assert unresolved["candidate_key"] is None
    assert unresolved["canonical_wing"] is None
    assert unresolved["canonical_room"] is None

    backed = contract.build_candidate_record(
        run_id=RUN_ID,
        atlas_run_id=ATLAS_RUN_ID,
        candidate_id=CANDIDATE_ID,
        candidate_key=CANDIDATE_KEY,
        bridge_status="mixed",
        atlas_cluster_id="cluster-mixed-002",
        atlas_cluster_status="mixed",
        topic_label="Postgres with some unrelated planning",
        label="Postgres latency candidate from mixed cluster",
        definition="Operational notes about PostgreSQL latency with mixed surrounding topics.",
        thread_ids=["thread-012"],
        top_terms=[{"term": "postgres", "count": 3}],
        mixed_reasons=["dominant_candidate_with_noise"],
    )
    _assert_valid(backed)
    assert backed["candidate_id"] == CANDIDATE_ID
    assert backed["canonical_wing"] == "devops"

    with pytest.raises(ValueError):
        contract.build_candidate_record(
            run_id=RUN_ID,
            atlas_run_id=ATLAS_RUN_ID,
            candidate_id=CANDIDATE_ID,
            bridge_status="mixed",
            atlas_cluster_id="cluster-mixed-003",
            atlas_cluster_status="mixed",
            topic_label="Incomplete mixed identity",
            label=None,
            definition=None,
            thread_ids=["thread-013"],
            top_terms=[{"term": "postgres", "count": 1}],
            mixed_reasons=["partial_candidate_identity"],
        )


def test_candidate_bridge_noise_records_preserve_atlas_evidence_without_identity() -> None:
    row = contract.build_candidate_record(
        run_id=RUN_ID,
        atlas_run_id=ATLAS_RUN_ID,
        bridge_status="noise",
        atlas_cluster_id="cluster-noise-001",
        atlas_cluster_status="noise",
        topic_label="Assorted fragments",
        label=None,
        definition=None,
        thread_ids=["thread-noise-001", "thread-noise-002"],
        top_terms=[{"term": "misc", "count": 4}],
        evidence_titles=["Untitled fragment"],
        representative_thread_ids=["thread-noise-001"],
        representative_excerpts=["A short fragment without durable room semantics."],
        mixed_reasons=["low_coherence", "no_canonical_candidate"],
    )
    _assert_valid(row)
    assert row["candidate_id"] is None
    assert row["candidate_key"] is None
    assert row["canonical_wing"] is None
    assert row["canonical_room"] is None
    assert row["atlas_cluster_id"] == "cluster-noise-001"
    assert row["bridge_status"] == "noise"
    assert row["thread_ids"] == ["thread-noise-001", "thread-noise-002"]
    assert row["evidence_titles"] == ["Untitled fragment"]
    assert row["mixed_reasons"] == ["low_coherence", "no_canonical_candidate"]

    for field, value in (
        ("candidate_id", CANDIDATE_ID),
        ("candidate_key", CANDIDATE_KEY),
        ("canonical_wing", "devops"),
        ("canonical_room", "postgres_latency"),
    ):
        tampered = dict(row)
        tampered[field] = value
        with pytest.raises(ValueError):
            contract.validate_row(contract.CANDIDATE_BRIDGE_RECORD_SCHEMA, tampered)


def test_thread_candidate_lookup_record_contract_for_mapped_and_unmapped_threads() -> None:
    mapped = contract.build_thread_candidate_record(
        run_id=RUN_ID,
        atlas_run_id=ATLAS_RUN_ID,
        thread_id="thread-001",
        lookup_status="mapped",
        candidate_ids=[CANDIDATE_ID],
        candidate_keys=[CANDIDATE_KEY],
        cluster_ids=["cluster-001"],
        primary_candidate_id=CANDIDATE_ID,
        primary_candidate_key=CANDIDATE_KEY,
        reason_codes=["cluster_member"],
        source_thread_ref="thread_index.jsonl#1",
    )
    _assert_valid(mapped)

    unmapped = contract.build_thread_candidate_record(
        run_id=RUN_ID,
        atlas_run_id=ATLAS_RUN_ID,
        thread_id="thread-999",
        lookup_status="unmapped",
        reason_codes=["not_in_cluster"],
        source_thread_ref="thread_index.jsonl#999",
    )
    _assert_valid(unmapped)
    assert unmapped["candidate_ids"] == []
    assert unmapped["primary_candidate_id"] is None


def test_candidate_coverage_report_contract() -> None:
    row = contract.build_candidate_coverage_report(
        run_id=RUN_ID,
        atlas_run_id=ATLAS_RUN_ID,
        status="needs_review",
        total_threads=4,
        mapped_threads=1,
        mixed_threads=1,
        noise_threads=1,
        unmapped_threads=1,
        candidate_count=1,
        cluster_count=3,
        duplicate_thread_refs=[{"thread_id": "thread-001", "cluster_ids": ["cluster-001", "cluster-002"]}],
        missing_thread_refs=["thread-999"],
        counts={"candidate_clusters": 1, "noise_clusters": 1},
    )

    _assert_valid(row)
    assert row["duplicate_thread_refs"][0]["cluster_ids"] == ["cluster-001", "cluster-002"]


def test_extraction_reconciliation_and_publish_checkpoint_contracts_default_to_no_publish() -> None:
    extraction = contract.build_extraction_record(
        run_id=RUN_ID,
        atlas_run_id=ATLAS_RUN_ID,
        extraction_id="extract-thread-001-0001",
        thread_id="thread-001",
        segment_id="segment-001",
        extraction_status="accepted",
        candidate_id=CANDIDATE_ID,
        candidate_key=CANDIDATE_KEY,
        signal_type="technical_note",
        title="Postgres latency investigation",
        summary="The segment preserves query latency tuning details.",
        source_excerpt="EXPLAIN ANALYZE shows the slow index scan.",
        confidence=0.82,
        provenance={
            "atlas_candidate_ids": [CANDIDATE_ID],
            "atlas_candidate_keys": [CANDIDATE_KEY],
            "atlas_cluster_ids": ["cluster-001"],
            "thread_candidate_lookup_ref": "atlas_thread_candidates.jsonl#1",
        },
    )
    _assert_valid(extraction)
    assert extraction["no_publish"] is True
    assert extraction["publish_enabled"] is False
    assert extraction["safety_contract"]["publish_enabled"] is False

    null_signal = contract.build_extraction_record(
        run_id=RUN_ID,
        atlas_run_id=ATLAS_RUN_ID,
        extraction_id="extract-thread-002-0001",
        thread_id="thread-002",
        segment_id="segment-001",
        extraction_status="null_signal",
        summary="No durable memory candidate in this segment.",
    )
    _assert_valid(null_signal)
    assert null_signal["candidate_id"] is None
    assert null_signal["canonical_wing"] is None

    reconciled = contract.build_reconciliation_record(
        run_id=RUN_ID,
        atlas_run_id=ATLAS_RUN_ID,
        reconciled_signal_id="atlas_signal_thread-001_0001",
        reconciliation_status="accepted",
        candidate_id=CANDIDATE_ID,
        candidate_key=CANDIDATE_KEY,
        source_extraction_ids=["extract-thread-001-0001"],
        dedupe_key="devops:postgres_latency:sha256:abc123",
        title="Postgres latency investigation",
        summary="The reconciled record keeps one deduped Postgres latency note.",
        confidence=0.86,
        provenance={"extraction_ids": ["extract-thread-001-0001"], "atlas_cluster_ids": ["cluster-001"]},
    )
    _assert_valid(reconciled)
    assert reconciled["no_publish"] is True
    assert reconciled["publish_enabled"] is False

    checkpoint = contract.build_publish_checkpoint(
        run_id=RUN_ID,
        atlas_run_id=ATLAS_RUN_ID,
        checkpoint_id="publish-disabled-001",
    )
    _assert_valid(checkpoint)
    assert checkpoint["status"] == "disabled"
    assert checkpoint["publish_enabled"] is False
    assert checkpoint["publish_gate_open"] is False
    assert checkpoint["target_wing"] is None


@pytest.mark.parametrize("bad_status", ["done", "ok", "", "published"])
def test_progress_rejects_unknown_or_invalid_status(bad_status: str) -> None:
    with pytest.raises(ValueError):
        contract.build_progress(
            run_id=RUN_ID,
            atlas_run_id=ATLAS_RUN_ID,
            status=bad_status,
            current_phase="bridge",
            phase_status="running",
            phase_order=["bridge"],
        )


@pytest.mark.parametrize("bad_phase_status", ["active", "done", "", "published"])
def test_progress_rejects_bad_phase_state(bad_phase_status: str) -> None:
    with pytest.raises(ValueError):
        contract.build_progress(
            run_id=RUN_ID,
            atlas_run_id=ATLAS_RUN_ID,
            status="running",
            current_phase="bridge",
            phase_status=bad_phase_status,
            phase_order=["bridge"],
        )


@pytest.mark.parametrize(
    ("candidate_id", "candidate_key"),
    [
        ("candidate_devops_postgres_latency", CANDIDATE_KEY),
        ("cand_devops_postgres_latency", CANDIDATE_KEY),
        ("cand_devops__postgres_latency", "DevOps:postgres_latency"),
        ("cand_devops__postgres_latency", "devops/postgres_latency"),
        ("cand_other__room", CANDIDATE_KEY),
    ],
)
def test_candidate_bridge_rejects_invalid_candidate_ids_or_keys(
    candidate_id: str, candidate_key: str
) -> None:
    with pytest.raises(ValueError):
        contract.build_candidate_record(
            run_id=RUN_ID,
            atlas_run_id=ATLAS_RUN_ID,
            candidate_id=candidate_id,
            candidate_key=candidate_key,
            bridge_status="candidate",
            atlas_cluster_id="cluster-001",
            atlas_cluster_status="candidate",
            topic_label="Postgres latency",
            label="Postgres latency",
            definition="Operational notes.",
            thread_ids=["thread-001"],
            top_terms=[{"term": "postgres", "count": 1}],
        )


def test_thread_lookup_rejects_bad_candidate_shapes_and_invalid_statuses() -> None:
    with pytest.raises(ValueError):
        contract.build_thread_candidate_record(
            run_id=RUN_ID,
            atlas_run_id=ATLAS_RUN_ID,
            thread_id="thread-001",
            lookup_status="mapped",
            candidate_ids=[CANDIDATE_ID],
            candidate_keys=[],
        )
    with pytest.raises(ValueError):
        contract.build_thread_candidate_record(
            run_id=RUN_ID,
            atlas_run_id=ATLAS_RUN_ID,
            thread_id="thread-001",
            lookup_status="published",
        )


def test_coverage_rejects_counts_that_do_not_sum_to_total() -> None:
    with pytest.raises(ValueError):
        contract.build_candidate_coverage_report(
            run_id=RUN_ID,
            atlas_run_id=ATLAS_RUN_ID,
            status="complete",
            total_threads=3,
            mapped_threads=1,
            mixed_threads=1,
            noise_threads=1,
            unmapped_threads=1,
            candidate_count=1,
            cluster_count=1,
        )


def test_artifact_index_rejects_bad_paths_and_bad_safety_fields() -> None:
    for bad_path in (
        PurePosixPath("../candidate_bridge_records.jsonl"),
        "/tmp/candidate_bridge_records.jsonl",
        "C:/tmp/candidate_bridge_records.jsonl",
        "atlas/../candidate_bridge_records.jsonl",
    ):
        with pytest.raises(ValueError):
            contract.build_artifact_index_record(
                artifact_key="candidate_bridge_records",
                schema_name=contract.CANDIDATE_BRIDGE_RECORD_SCHEMA,
                relative_path=bad_path,
                phase="bridge",
                content_type="application/jsonl",
                count=0,
                append_only=True,
                review_safe=True,
                dashboard_safe=True,
            )

    raw_dashboard_safe = contract.build_artifact_index_record(
        artifact_key="extraction_records",
        schema_name=contract.EXTRACTION_RECORD_SCHEMA,
        relative_path="extraction_records.jsonl",
        phase="extraction",
        content_type="application/jsonl",
        count=0,
        append_only=True,
        review_safe=True,
        dashboard_safe=False,
        contains_raw_model_output=True,
        privacy_level="model_output",
    )
    raw_dashboard_safe["dashboard_safe"] = True
    with pytest.raises(ValueError):
        contract.validate_row(contract.ARTIFACT_INDEX_RECORD_SCHEMA, raw_dashboard_safe)

    publish_gate = contract.build_artifact_index_record(
        artifact_key="publish_checkpoint",
        schema_name=contract.PUBLISH_CHECKPOINT_SCHEMA,
        relative_path="publish_checkpoint.jsonl",
        phase="publish_gate",
        content_type="application/jsonl",
        count=0,
        append_only=True,
        review_safe=True,
        dashboard_safe=True,
        publish_gate_required=True,
        privacy_level="review_only",
    )
    publish_gate["privacy_level"] = "summary"
    with pytest.raises(ValueError):
        contract.validate_row(contract.ARTIFACT_INDEX_RECORD_SCHEMA, publish_gate)


def test_extraction_validator_rejects_publish_enabled_and_invalid_candidate_defaults() -> None:
    extraction = contract.build_extraction_record(
        run_id=RUN_ID,
        atlas_run_id=ATLAS_RUN_ID,
        extraction_id="extract-thread-001-0001",
        thread_id="thread-001",
        segment_id="segment-001",
        extraction_status="accepted",
        candidate_id=CANDIDATE_ID,
        candidate_key=CANDIDATE_KEY,
    )
    extraction["publish_enabled"] = True
    with pytest.raises(ValueError):
        contract.validate_row(contract.EXTRACTION_RECORD_SCHEMA, extraction)

    with pytest.raises(ValueError):
        contract.build_extraction_record(
            run_id=RUN_ID,
            atlas_run_id=ATLAS_RUN_ID,
            extraction_id="extract-thread-001-0002",
            thread_id="thread-001",
            segment_id="segment-001",
            extraction_status="accepted",
            candidate_id=None,
            candidate_key=None,
        )

    with pytest.raises(ValueError):
        contract.build_extraction_record(
            run_id=RUN_ID,
            atlas_run_id=ATLAS_RUN_ID,
            extraction_id="extract-thread-001-0003",
            thread_id="thread-001",
            segment_id="segment-001",
            extraction_status="invalid_shape",
        )


def test_publish_checkpoint_defaults_disabled_and_requires_explicit_gate_for_publish() -> None:
    disabled = contract.build_publish_checkpoint(
        run_id=RUN_ID,
        atlas_run_id=ATLAS_RUN_ID,
        checkpoint_id="publish-disabled-001",
    )
    assert disabled["publish_enabled"] is False
    assert disabled["safety_contract"]["publish_enabled"] is False

    approved = contract.build_publish_checkpoint(
        run_id=RUN_ID,
        atlas_run_id=ATLAS_RUN_ID,
        checkpoint_id="publish-approved-001",
        status="approved",
        publish_enabled=True,
        publish_gate_open=True,
        target_wing="chatgpt_atlas_signals",
        record_count=3,
        approved_by="reviewer",
        approval_ref="checkpoint-m-review",
        notes="Explicit WP-13 reviewed publish gate.",
    )
    _assert_valid(approved)
    assert approved["target_wing"] == "chatgpt_atlas_signals"
    assert approved["record_count"] == 3
    assert approved["safety_contract"]["publish_enabled"] is True
    assert approved["safety_contract"]["publishes_by_default"] is False

    for forbidden_wing in ("chatgpt", "chatgpt_signals", "chatgpt_thread_signals"):
        with pytest.raises(ValueError):
            contract.build_publish_checkpoint(
                run_id=RUN_ID,
                atlas_run_id=ATLAS_RUN_ID,
                checkpoint_id=f"publish-bad-{forbidden_wing}",
                status="approved",
                publish_enabled=True,
                publish_gate_open=True,
                target_wing=forbidden_wing,
                record_count=1,
                approved_by="reviewer",
                approval_ref="checkpoint-m-review",
            )

    for missing_field in ("approved_by", "approval_ref"):
        kwargs = {
            "run_id": RUN_ID,
            "atlas_run_id": ATLAS_RUN_ID,
            "checkpoint_id": f"publish-missing-{missing_field}",
            "status": "approved",
            "publish_enabled": True,
            "publish_gate_open": True,
            "target_wing": "chatgpt_atlas_signals",
            "record_count": 1,
            "approved_by": "reviewer",
            "approval_ref": "checkpoint-m-review",
        }
        kwargs[missing_field] = None
        with pytest.raises(ValueError):
            contract.build_publish_checkpoint(**kwargs)

    with pytest.raises(ValueError):
        contract.build_publish_checkpoint(
            run_id=RUN_ID,
            atlas_run_id=ATLAS_RUN_ID,
            checkpoint_id="publish-bad-003",
            status="approved",
            publish_enabled=True,
            publish_gate_open=True,
            target_wing="chatgpt_atlas_signals",
            record_count=0,
            approved_by="reviewer",
            approval_ref="checkpoint-k",
        )

    with pytest.raises(ValueError):
        contract.build_publish_checkpoint(
            run_id=RUN_ID,
            atlas_run_id=ATLAS_RUN_ID,
            checkpoint_id="publish-bad-004",
            status="pending_review",
            publish_enabled=True,
            publish_gate_open=True,
            target_wing="chatgpt_atlas_signals",
            record_count=1,
            approved_by="reviewer",
            approval_ref="checkpoint-k",
        )

    with pytest.raises(ValueError):
        contract.build_publish_checkpoint(
            run_id=RUN_ID,
            atlas_run_id=ATLAS_RUN_ID,
            checkpoint_id="publish-bad-005",
            target_wing="chatgpt_atlas_signals",
        )

    tampered = dict(disabled)
    tampered["publish_gate_open"] = True
    with pytest.raises(ValueError):
        contract.validate_row(contract.PUBLISH_CHECKPOINT_SCHEMA, tampered)


@pytest.mark.parametrize("bad_run_id", ["", "../run", "/tmp/run", "run id", ".", "..", "run/child"])
def test_builders_reject_invalid_run_ids(bad_run_id: str) -> None:
    with pytest.raises(ValueError):
        contract.build_progress(
            run_id=bad_run_id,
            atlas_run_id=ATLAS_RUN_ID,
            status="running",
            current_phase="bridge",
            phase_status="running",
            phase_order=["bridge"],
        )

    with pytest.raises(ValueError):
        contract.build_progress(
            run_id=RUN_ID,
            atlas_run_id=bad_run_id,
            status="running",
            current_phase="bridge",
            phase_status="running",
            phase_order=["bridge"],
        )


def test_validator_rejects_non_json_safe_and_forbidden_live_service_fields() -> None:
    row = contract.build_progress(
        run_id=RUN_ID,
        atlas_run_id=ATLAS_RUN_ID,
        status="running",
        current_phase="bridge",
        phase_status="running",
        phase_order=["bridge"],
    )

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
    broad_forbidden["nested"] = {"palace_write_path": "/tmp/palace"}
    with pytest.raises(ValueError):
        contract.canonical_json_line(broad_forbidden)
