from __future__ import annotations

import dataclasses
import json

import pytest

from mempalace import chatgpt_atlas_guided_contract as guided_contract
from mempalace import chatgpt_atlas_guided_prompt as guided_prompt


RUN_ID = "20260512T180000Z_atlas_guided_prompt"
ATLAS_RUN_ID = "atlas_full2_20260512T0412Z_2fc8ac5"
THREAD_ID = "thread-001"
SEGMENT_ID = "segment-001"
PRIMARY_CANDIDATE_ID = "cand_devops__postgres_latency"
PRIMARY_CANDIDATE_KEY = "devops:postgres_latency"


def _bridge_row(
    *,
    candidate_id: str,
    candidate_key: str,
    cluster_id: str,
    thread_ids: list[str] | None = None,
) -> dict[str, object]:
    return guided_contract.build_candidate_bridge_record(
        run_id=RUN_ID,
        atlas_run_id=ATLAS_RUN_ID,
        candidate_id=candidate_id,
        candidate_key=candidate_key,
        bridge_status="candidate",
        atlas_cluster_id=cluster_id,
        atlas_cluster_status="candidate",
        topic_label="Topic label",
        label=f"Label {candidate_key}",
        definition=f"Definition for {candidate_key}.",
        thread_ids=thread_ids or [THREAD_ID],
        top_terms=[{"term": "postgres", "count": 3}, {"term": "latency", "count": 2}],
        evidence_titles=[f"Evidence {candidate_key}", "Query tuning notes"],
        representative_thread_ids=[(thread_ids or [THREAD_ID])[0]],
        representative_excerpts=[f"Representative excerpt for {candidate_key}."],
        mixed_reasons=[],
    )


def _lookup_row(
    *,
    candidate_ids: list[str] | None = None,
    candidate_keys: list[str] | None = None,
    lookup_status: str = "mapped",
) -> dict[str, object]:
    ids = [PRIMARY_CANDIDATE_ID] if candidate_ids is None else candidate_ids
    keys = [PRIMARY_CANDIDATE_KEY] if candidate_keys is None else candidate_keys
    return guided_contract.build_thread_candidate_record(
        run_id=RUN_ID,
        atlas_run_id=ATLAS_RUN_ID,
        thread_id=THREAD_ID,
        lookup_status=lookup_status,
        candidate_ids=ids,
        candidate_keys=keys,
        cluster_ids=["cluster-001"],
        primary_candidate_id=ids[0] if ids else None,
        primary_candidate_key=keys[0] if keys else None,
        reason_codes=["candidate_cluster_member"] if ids else ["not_in_candidate_bridge"],
        source_thread_ref="thread_index.jsonl#1",
    )


def _assert_valid_records(result: guided_prompt.ChatGPTAtlasGuidedPromptParseResult) -> None:
    assert dataclasses.is_dataclass(result)
    assert isinstance(result.records, tuple)
    for record in result.records:
        assert (
            guided_contract.validate_row(guided_contract.EXTRACTION_RECORD_SCHEMA, record) == record
        )


def _valid_response_payload() -> dict[str, object]:
    return {
        "signals": [
            {
                "signal_status": "accepted",
                "candidate_id": PRIMARY_CANDIDATE_ID,
                "candidate_key": PRIMARY_CANDIDATE_KEY,
                "canonical_wing": "devops",
                "canonical_room": "postgres_latency",
                "signal_type": "technical_note",
                "title": "Investigate postgres latency",
                "summary": "The segment keeps a durable note about tuning postgres latency.",
                "source_excerpt": "Investigate the EXPLAIN ANALYZE output and fix the postgres latency spike.",
                "confidence": 0.84,
            }
        ]
    }


def test_build_prompt_bounds_candidates_to_thread_lookup_context() -> None:
    messages = guided_prompt.build_chatgpt_atlas_guided_prompt_messages(
        "Segment text about query tuning and postgres latency." * 40,
        _lookup_row(),
        [
            _bridge_row(
                candidate_id=PRIMARY_CANDIDATE_ID,
                candidate_key=PRIMARY_CANDIDATE_KEY,
                cluster_id="cluster-001",
            ),
            _bridge_row(
                candidate_id="cand_product__release_planning",
                candidate_key="product:release_planning",
                cluster_id="cluster-999",
                thread_ids=["thread-999"],
            ),
        ],
    )

    assert len(messages) == 2
    assert "Constrain every accepted item to the provided candidate shortlist." in messages[0]["content"]

    payload = json.loads(messages[1]["content"])
    shortlist = payload["candidate_shortlist"]
    assert payload["rules"][0] == "Return strict JSON only. No prose. No code fences."
    assert len(shortlist) == 1
    assert shortlist[0]["candidate_id"] == PRIMARY_CANDIDATE_ID
    assert shortlist[0]["candidate_key"] == PRIMARY_CANDIDATE_KEY
    assert "cand_product__release_planning" not in messages[1]["content"]
    assert "product:release_planning" not in messages[1]["content"]


def test_parse_valid_candidate_selection_builds_accepted_extraction_record() -> None:
    result = guided_prompt.parse_chatgpt_atlas_guided_response(
        "Investigate the EXPLAIN ANALYZE output and fix the postgres latency spike.",
        segment_id=SEGMENT_ID,
        thread_candidate_lookup_row=_lookup_row(),
        candidate_bridge_rows=[
            _bridge_row(
                candidate_id=PRIMARY_CANDIDATE_ID,
                candidate_key=PRIMARY_CANDIDATE_KEY,
                cluster_id="cluster-001",
            )
        ],
        response_text=json.dumps(
            {
                "signals": [
                    {
                        "signal_status": "accepted",
                        "candidate_id": PRIMARY_CANDIDATE_ID,
                        "candidate_key": PRIMARY_CANDIDATE_KEY,
                        "canonical_wing": "devops",
                        "canonical_room": "postgres_latency",
                        "signal_type": "technical_note",
                        "title": "Investigate postgres latency",
                        "summary": "The segment keeps a durable note about tuning postgres latency.",
                        "source_excerpt": "Investigate the EXPLAIN ANALYZE output and fix the postgres latency spike.",
                        "confidence": 0.84,
                    }
                ]
            }
        ),
    )

    _assert_valid_records(result)
    assert result.ok is True
    assert result.error_code is None
    record = result.records[0]
    assert record["extraction_status"] == "accepted"
    assert record["candidate_id"] == PRIMARY_CANDIDATE_ID
    assert record["candidate_key"] == PRIMARY_CANDIDATE_KEY
    assert record["canonical_wing"] == "devops"
    assert record["canonical_room"] == "postgres_latency"
    assert record["signal_type"] == "technical_note"
    assert record["no_publish"] is True
    assert record["publish_enabled"] is False
    assert record["provenance"]["atlas_candidate_ids"] == [PRIMARY_CANDIDATE_ID]
    assert record["provenance"]["atlas_cluster_ids"] == ["cluster-001"]


def test_parse_null_signal_builds_null_signal_record() -> None:
    result = guided_prompt.parse_chatgpt_atlas_guided_response(
        "This segment is mostly conversational filler without a durable memory signal.",
        segment_id=SEGMENT_ID,
        thread_candidate_lookup_row=_lookup_row(
            candidate_ids=[],
            candidate_keys=[],
            lookup_status="unmapped",
        ),
        candidate_bridge_rows=[],
        response_text=json.dumps(
            {
                "signals": [
                    {
                        "signal_status": "null_signal",
                        "candidate_id": None,
                        "candidate_key": None,
                        "canonical_wing": None,
                        "canonical_room": None,
                        "signal_type": "null_signal",
                        "title": None,
                        "summary": "No atlas-constrained durable memory fits this segment.",
                        "source_excerpt": "mostly conversational filler",
                        "confidence": 0.12,
                    }
                ]
            }
        ),
    )

    _assert_valid_records(result)
    record = result.records[0]
    assert result.ok is True
    assert record["extraction_status"] == "null_signal"
    assert record["candidate_id"] is None
    assert record["candidate_key"] is None
    assert record["canonical_wing"] is None
    assert record["canonical_room"] is None
    assert record["signal_type"] == "null_signal"


@pytest.mark.parametrize(
    ("payload", "error_code"),
    [
        (
            {
                "signals": [
                    {
                        "signal_status": "accepted",
                        "candidate_id": "cand_unknown__room",
                        "candidate_key": PRIMARY_CANDIDATE_KEY,
                        "canonical_wing": "devops",
                        "canonical_room": "postgres_latency",
                        "signal_type": "technical_note",
                        "title": "Bad candidate",
                        "summary": "Should fail.",
                        "source_excerpt": "bad candidate id",
                        "confidence": 0.4,
                    }
                ]
            },
            "unknown_candidate_id",
        ),
        (
            {
                "signals": [
                    {
                        "signal_status": "accepted",
                        "candidate_id": PRIMARY_CANDIDATE_ID,
                        "candidate_key": "finance:billing",
                        "canonical_wing": "finance",
                        "canonical_room": "billing",
                        "signal_type": "technical_note",
                        "title": "Bad key",
                        "summary": "Should fail.",
                        "source_excerpt": "bad candidate key",
                        "confidence": 0.4,
                    }
                ]
            },
            "unknown_candidate_key",
        ),
        (
            {
                "signals": [
                    {
                        "signal_status": "accepted",
                        "candidate_id": PRIMARY_CANDIDATE_ID,
                        "candidate_key": "devops:postgres_latency_extra",
                        "canonical_wing": "devops",
                        "canonical_room": "postgres_latency_extra",
                        "signal_type": "technical_note",
                        "title": "Unknown room",
                        "summary": "Should fail.",
                        "source_excerpt": "unknown room",
                        "confidence": 0.4,
                    }
                ]
            },
            "unknown_candidate_key",
        ),
        (
            {
                "signals": [
                    {
                        "signal_status": "accepted",
                        "candidate_id": PRIMARY_CANDIDATE_ID,
                        "candidate_key": "not a key",
                        "canonical_wing": "devops",
                        "canonical_room": "postgres_latency",
                        "signal_type": "technical_note",
                        "title": "Malformed key",
                        "summary": "Should fail.",
                        "source_excerpt": "malformed key",
                        "confidence": 0.4,
                    }
                ]
            },
            "invalid_candidate_key",
        ),
        (
            {
                "signals": [
                    {
                        "signal_status": "accepted",
                        "candidate_id": PRIMARY_CANDIDATE_ID,
                        "candidate_key": PRIMARY_CANDIDATE_KEY,
                        "canonical_wing": "Bad Wing",
                        "canonical_room": "postgres_latency",
                        "signal_type": "technical_note",
                        "title": "Bad wing",
                        "summary": "Should fail.",
                        "source_excerpt": "invalid wing",
                        "confidence": 0.4,
                    }
                ]
            },
            "invalid_canonical_wing",
        ),
        (
            {
                "signals": [
                    {
                        "signal_status": "accepted",
                        "candidate_id": PRIMARY_CANDIDATE_ID,
                        "candidate_key": "support:requests",
                        "canonical_wing": "support",
                        "canonical_room": "requests",
                        "signal_type": "technical_note",
                        "title": "Mismatch",
                        "summary": "Should fail.",
                        "source_excerpt": "candidate mismatch",
                        "confidence": 0.4,
                    }
                ]
            },
            "candidate_id_key_mismatch",
        ),
    ],
)
def test_parse_rejects_invalid_candidate_shapes(payload: dict[str, object], error_code: str) -> None:
    result = guided_prompt.parse_chatgpt_atlas_guided_response(
        "Postgres segment",
        segment_id=SEGMENT_ID,
        thread_candidate_lookup_row=_lookup_row(
            candidate_ids=[PRIMARY_CANDIDATE_ID, "cand_support__requests"],
            candidate_keys=[PRIMARY_CANDIDATE_KEY, "support:requests"],
        ),
        candidate_bridge_rows=[
            _bridge_row(
                candidate_id=PRIMARY_CANDIDATE_ID,
                candidate_key=PRIMARY_CANDIDATE_KEY,
                cluster_id="cluster-001",
            ),
            _bridge_row(
                candidate_id="cand_support__requests",
                candidate_key="support:requests",
                cluster_id="cluster-002",
            ),
        ],
        response_text=json.dumps(payload),
    )

    _assert_valid_records(result)
    assert result.ok is False
    assert result.error_code == error_code
    assert result.records[0]["extraction_status"] == "invalid_output"
    assert result.records[0]["provenance"]["error_code"] == error_code


def test_parse_rejects_invalid_json() -> None:
    result = guided_prompt.parse_chatgpt_atlas_guided_response(
        "Postgres segment",
        segment_id=SEGMENT_ID,
        thread_candidate_lookup_row=_lookup_row(),
        candidate_bridge_rows=[
            _bridge_row(
                candidate_id=PRIMARY_CANDIDATE_ID,
                candidate_key=PRIMARY_CANDIDATE_KEY,
                cluster_id="cluster-001",
            )
        ],
        response_text="not json at all",
    )

    _assert_valid_records(result)
    assert result.ok is False
    assert result.error_code == "invalid_json"
    assert result.raw_response_excerpt == "not json at all"


def test_parse_rejects_missing_required_fields_and_bad_confidence() -> None:
    result = guided_prompt.parse_chatgpt_atlas_guided_response(
        "Postgres segment",
        segment_id=SEGMENT_ID,
        thread_candidate_lookup_row=_lookup_row(),
        candidate_bridge_rows=[
            _bridge_row(
                candidate_id=PRIMARY_CANDIDATE_ID,
                candidate_key=PRIMARY_CANDIDATE_KEY,
                cluster_id="cluster-001",
            )
        ],
        response_text=json.dumps(
            {
                "signals": [
                    {
                        "signal_status": "accepted",
                        "candidate_id": PRIMARY_CANDIDATE_ID,
                        "candidate_key": PRIMARY_CANDIDATE_KEY,
                        "canonical_wing": "devops",
                        "canonical_room": "postgres_latency",
                        "summary": "Missing title and source excerpt.",
                        "confidence": 1.5,
                    }
                ]
            }
        ),
    )

    _assert_valid_records(result)
    assert result.ok is False
    assert result.error_code == "invalid_confidence"


def test_parse_bounds_provenance_and_source_excerpt() -> None:
    long_segment = "segment evidence " * 80
    long_source_excerpt = "source evidence " * 80
    result = guided_prompt.parse_chatgpt_atlas_guided_response(
        long_segment,
        segment_id=SEGMENT_ID,
        thread_candidate_lookup_row=_lookup_row(),
        candidate_bridge_rows=[
            _bridge_row(
                candidate_id=PRIMARY_CANDIDATE_ID,
                candidate_key=PRIMARY_CANDIDATE_KEY,
                cluster_id="cluster-001",
            )
        ],
        response_text=json.dumps(
            {
                "signals": [
                    {
                        "signal_status": "accepted",
                        "candidate_id": PRIMARY_CANDIDATE_ID,
                        "candidate_key": PRIMARY_CANDIDATE_KEY,
                        "canonical_wing": "devops",
                        "canonical_room": "postgres_latency",
                        "signal_type": "technical_note",
                        "title": "Long evidence",
                        "summary": "Keep bounded provenance and source evidence.",
                        "source_excerpt": long_source_excerpt,
                        "confidence": 0.77,
                    }
                ]
            }
        ),
    )

    _assert_valid_records(result)
    record = result.records[0]
    assert len(record["source_excerpt"]) == guided_prompt.PARSED_SOURCE_EXCERPT_MAX_CHARS
    assert record["source_excerpt"].endswith("...")
    assert len(record["provenance"]["segment_excerpt"]) == (
        guided_prompt.PROVENANCE_SEGMENT_EXCERPT_MAX_CHARS
    )
    assert record["provenance"]["segment_excerpt"].endswith("...")


def test_parse_rejects_publish_attempt_and_keeps_no_publish_defaults() -> None:
    result = guided_prompt.parse_chatgpt_atlas_guided_response(
        "Postgres segment",
        segment_id=SEGMENT_ID,
        thread_candidate_lookup_row=_lookup_row(),
        candidate_bridge_rows=[
            _bridge_row(
                candidate_id=PRIMARY_CANDIDATE_ID,
                candidate_key=PRIMARY_CANDIDATE_KEY,
                cluster_id="cluster-001",
            )
        ],
        response_text=json.dumps(
            {
                "publish_enabled": True,
                "signals": [
                    {
                        "signal_status": "accepted",
                        "candidate_id": PRIMARY_CANDIDATE_ID,
                        "candidate_key": PRIMARY_CANDIDATE_KEY,
                        "canonical_wing": "devops",
                        "canonical_room": "postgres_latency",
                        "signal_type": "technical_note",
                        "title": "Publish attempt",
                        "summary": "Should fail closed.",
                        "source_excerpt": "publish me",
                        "confidence": 0.8,
                    }
                ],
            }
        ),
    )

    _assert_valid_records(result)
    record = result.records[0]
    assert result.ok is False
    assert result.error_code == "publish_attempt"
    assert record["extraction_status"] == "invalid_output"
    assert record["no_publish"] is True
    assert record["publish_enabled"] is False


@pytest.mark.parametrize(
    ("forbidden_key", "placement"),
    [
        ("localai_base_url", "root"),
        ("localai_model", "signal"),
        ("chroma_collection", "signal_nested"),
        ("mcp", "root_nested"),
        ("mcp_tool", "signal"),
        ("network_url", "root_nested"),
        ("palace_root", "root"),
        ("palace_write_path", "signal"),
        ("drawer_write_path", "signal_nested"),
        ("write_drawer", "root"),
        ("publish_enabled", "root"),
        ("target_wing", "signal"),
    ],
)
def test_parse_rejects_forbidden_control_keys_anywhere(
    forbidden_key: str, placement: str
) -> None:
    payload = _valid_response_payload()
    signal = payload["signals"][0]

    if placement == "root":
        payload[forbidden_key] = "blocked"
    elif placement == "signal":
        signal[forbidden_key] = "blocked"
    elif placement == "signal_nested":
        signal["extra_context"] = {"safe_label": "ok", forbidden_key: "blocked"}
    elif placement == "root_nested":
        payload["extra_context"] = [{"safe_label": "ok"}, {forbidden_key: "blocked"}]
    else:
        raise AssertionError(f"Unhandled placement: {placement}")

    result = guided_prompt.parse_chatgpt_atlas_guided_response(
        "Postgres segment",
        segment_id=SEGMENT_ID,
        thread_candidate_lookup_row=_lookup_row(),
        candidate_bridge_rows=[
            _bridge_row(
                candidate_id=PRIMARY_CANDIDATE_ID,
                candidate_key=PRIMARY_CANDIDATE_KEY,
                cluster_id="cluster-001",
            )
        ],
        response_text=json.dumps(payload),
    )

    _assert_valid_records(result)
    record = result.records[0]
    assert result.ok is False
    assert result.error_code == "publish_attempt"
    assert record["extraction_status"] == "invalid_output"
    assert record["provenance"]["error_code"] == "publish_attempt"
    assert record["no_publish"] is True
    assert record["publish_enabled"] is False
