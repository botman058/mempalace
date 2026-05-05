import json

from mempalace.ontology_candidate_names import (
    PHASE_NAME,
    RAW_RESPONSE_EXCERPT_MAX_CHARS,
    build_candidate_naming_prompt,
    build_canonical_candidate_records,
    parse_candidate_naming_response,
)


RUN_ID = "20260505T143015Z_chatgpt_signal_ontology"


def _cluster_record(
    sequence: int,
    *,
    candidate_id: str | None = None,
    canonical_wing: str = "life_admin",
    canonical_room: str = "requests",
    proposal_label: str | None = None,
    source_drawer_count: int = 2,
    record_status: str = "ok",
    phase: str = "candidate_clusters",
    attempt: int = 1,
    run_id: str = RUN_ID,
):
    candidate_id = candidate_id or f"cand_{canonical_wing}__{canonical_room}"
    candidate_key = f"{canonical_wing}:{canonical_room}"
    return {
        "schema_name": "ontology.phase_record",
        "schema_version": 1,
        "run_id": run_id,
        "phase": phase,
        "sequence": sequence,
        "attempt": attempt,
        "recorded_at": f"2026-05-05T15:{sequence:02d}:00Z",
        "subject_type": "candidate",
        "subject_id": candidate_id,
        "record_status": record_status,
        "source": {
            "wing": canonical_wing,
            "room": canonical_room,
        },
        "payload": {
            "candidate_id": candidate_id,
            "candidate_key": candidate_key,
            "canonical_wing": canonical_wing,
            "canonical_room": canonical_room,
            "proposal_label": proposal_label or canonical_room.replace("_", " "),
            "cluster_stats": {
                "source_drawer_count": source_drawer_count,
                "source_wing_count": 1,
                "source_room_count": 1,
                "proposal_label_count": 1,
                "rationale_summary_count": 1,
                "confidence_count": source_drawer_count,
                "confidence_avg": 0.83,
            },
            "centroid": {
                "source_wings": [{"source_wing": "chatgpt_signals", "count": source_drawer_count}],
                "source_rooms": [{"source_room": "general", "count": source_drawer_count}],
                "proposal_labels": [
                    {
                        "proposal_label": proposal_label or canonical_room.replace("_", " "),
                        "count": source_drawer_count,
                    }
                ],
                "rationale_summaries": [{"rationale_summary": "Cluster summary.", "count": 1}],
            },
            "source_drawer_refs": [
                {
                    "drawer_id": f"drawer_{sequence}_a",
                    "source_wing": "chatgpt_signals",
                    "source_room": "general",
                    "pass1_record_ref": f"pass1_open.jsonl#{sequence}",
                },
                {
                    "drawer_id": f"drawer_{sequence}_b",
                    "source_wing": "chatgpt_signals",
                    "source_room": "general",
                    "pass1_record_ref": f"pass1_open.jsonl#{sequence + 100}",
                },
            ],
            "examples": [
                {
                    "drawer_id": f"drawer_{sequence}_a",
                    "source_wing": "chatgpt_signals",
                    "source_room": "general",
                    "pass1_record_ref": f"pass1_open.jsonl#{sequence}",
                    "proposal_label": proposal_label or canonical_room.replace("_", " "),
                }
            ],
        },
    }


def test_build_candidate_naming_prompt_includes_source_identity_and_merge_targets():
    prompt = build_candidate_naming_prompt(
        _cluster_record(1, canonical_wing="life_admin", canonical_room="requests"),
        [
            _cluster_record(1, canonical_wing="life_admin", canonical_room="requests"),
            _cluster_record(2, canonical_wing="support", canonical_room="requests"),
        ],
    )

    assert "SOURCE CANDIDATE" in prompt
    assert '"candidate_key": "life_admin:requests"' in prompt
    assert '"candidate_key": "support:requests"' in prompt
    assert '"candidate_key": "life_admin:requests"' in prompt
    assert "Rooms are not globally unique; preserve wing context." in prompt


def test_parse_candidate_naming_response_keep_path():
    result = parse_candidate_naming_response(
        _cluster_record(1, canonical_wing="life_admin", canonical_room="requests"),
        (
            '{"action":"keep","canonical_wing":"life_admin","canonical_room":"intake_requests",'
            '"label":"Intake requests","definition":"Requests for intake paperwork and scheduling."}'
        ),
    )

    assert result.record_status == "ok"
    assert result.payload == {
        "action": "keep",
        "candidate_id": "cand_life_admin__intake_requests",
        "candidate_key": "life_admin:intake_requests",
        "canonical_wing": "life_admin",
        "canonical_room": "intake_requests",
        "label": "Intake requests",
        "definition": "Requests for intake paperwork and scheduling.",
    }


def test_parse_candidate_naming_response_merge_path_preserves_room_ambiguity_across_wings():
    cluster_record = _cluster_record(1, canonical_wing="life_admin", canonical_room="requests")
    candidate_choices = [
        _cluster_record(1, canonical_wing="life_admin", canonical_room="requests"),
        _cluster_record(2, canonical_wing="support", canonical_room="requests"),
    ]

    result = parse_candidate_naming_response(
        cluster_record,
        (
            '{"action":"merge","canonical_wing":"support","canonical_room":"requests",'
            '"merge_target_candidate_id":"cand_support__requests",'
            '"merge_target_candidate_key":"support:requests"}'
        ),
        candidate_choices,
    )

    assert result.record_status == "ok"
    assert result.payload["action"] == "merge"
    assert result.payload["candidate_id"] == "cand_support__requests"
    assert result.payload["candidate_key"] == "support:requests"
    assert result.payload["merge_target_candidate_key"] == "support:requests"
    assert result.payload["canonical_room"] == "requests"
    assert result.payload["canonical_wing"] == "support"


def test_parse_candidate_naming_response_prune_path():
    result = parse_candidate_naming_response(
        _cluster_record(1),
        (
            '{"action":"prune","canonical_wing":"life_admin","canonical_room":"requests",'
            '"prune_reason":"too_sparse_to_stand_alone"}'
        ),
    )

    assert result.record_status == "ok"
    assert result.payload == {
        "action": "prune",
        "candidate_id": "cand_life_admin__requests",
        "candidate_key": "life_admin:requests",
        "canonical_wing": "life_admin",
        "canonical_room": "requests",
        "prune_reason": "too_sparse_to_stand_alone",
    }


def test_parse_candidate_naming_response_invalid_output_paths():
    cases = [
        ("not json at all", "invalid_json"),
        ('{"canonical_wing":"life_admin","canonical_room":"requests"}', "missing_action"),
        (
            '{"action":"keep","canonical_wing":"Life Admin","canonical_room":"requests",'
            '"label":"Requests","definition":"Definition."}',
            "invalid_canonical_wing",
        ),
        (
            '{"action":"rename","canonical_wing":"life_admin","canonical_room":"requests"}',
            "invalid_action",
        ),
        ('["not","an","object"]', "invalid_response_shape"),
        (
            '{"action":"merge","canonical_wing":"support","canonical_room":"requests",'
            '"merge_target_candidate_id":"cand_missing","merge_target_candidate_key":"support:requests"}',
            "invalid_merge_target",
        ),
    ]

    candidate_choices = [
        _cluster_record(1, canonical_wing="life_admin", canonical_room="requests"),
        _cluster_record(2, canonical_wing="support", canonical_room="requests"),
    ]

    for response_text, error_code in cases:
        result = parse_candidate_naming_response(
            _cluster_record(1, canonical_wing="life_admin", canonical_room="requests"),
            response_text,
            candidate_choices,
        )
        assert result.record_status == "invalid_model_output"
        assert result.payload["error_code"] == error_code
        assert "retryable" in result.payload


def test_parse_candidate_naming_response_bounds_raw_excerpt():
    raw = "not-json " + ("x" * (RAW_RESPONSE_EXCERPT_MAX_CHARS + 30))
    result = parse_candidate_naming_response(_cluster_record(1), raw)

    assert result.record_status == "invalid_model_output"
    excerpt = result.payload["raw_response_excerpt"]
    assert len(excerpt) == RAW_RESPONSE_EXCERPT_MAX_CHARS
    assert excerpt.endswith("...")


def test_build_canonical_candidate_records_emits_deterministic_jsonl_ready_records():
    cluster_records = [
        _cluster_record(3, canonical_wing="support", canonical_room="requests"),
        _cluster_record(1, canonical_wing="life_admin", canonical_room="requests"),
        _cluster_record(2, canonical_wing="work_admin", canonical_room="meetings"),
    ]
    model_outputs = {
        "cand_support__requests": (
            '{"action":"keep","canonical_wing":"support","canonical_room":"requests",'
            '"label":"Support requests","definition":"User-facing help and request traffic."}'
        ),
        "cand_life_admin__requests": (
            '{"action":"keep","canonical_wing":"life_admin","canonical_room":"requests",'
            '"label":"Life requests","definition":"Personal logistics and intake requests."}'
        ),
        "cand_work_admin__meetings": (
            '{"action":"prune","canonical_wing":"work_admin","canonical_room":"meetings",'
            '"prune_reason":"too_broad"}'
        ),
    }

    first = build_canonical_candidate_records(
        cluster_records,
        model_outputs,
        recorded_at="2026-05-05T16:00:00Z",
    )
    second = build_canonical_candidate_records(
        list(reversed(cluster_records)),
        model_outputs,
        recorded_at="2026-05-05T16:00:00Z",
    )

    assert [record["subject_id"] for record in first.records] == [
        "cand_life_admin__requests",
        "cand_support__requests",
        "cand_work_admin__meetings",
    ]
    assert first.records == second.records
    line = json.dumps(first.records[0], separators=(",", ":")) + "\n"
    parsed = json.loads(line)
    assert line.endswith("\n")
    assert parsed["schema_name"] == "ontology.phase_record"
    assert parsed["phase"] == PHASE_NAME
    assert parsed["subject_type"] == "candidate"
    assert parsed["payload"]["examples"][0]["pass1_record_ref"] == "pass1_open.jsonl#1"


def test_build_canonical_candidate_records_preserves_same_room_name_under_different_wings():
    result = build_canonical_candidate_records(
        [
            _cluster_record(1, canonical_wing="life_admin", canonical_room="requests"),
            _cluster_record(2, canonical_wing="support", canonical_room="requests"),
        ],
        {
            "cand_life_admin__requests": (
                '{"action":"keep","canonical_wing":"life_admin","canonical_room":"requests",'
                '"label":"Life requests","definition":"Personal logistics requests."}'
            ),
            "cand_support__requests": (
                '{"action":"keep","canonical_wing":"support","canonical_room":"requests",'
                '"label":"Support requests","definition":"Support and help requests."}'
            ),
        },
        recorded_at="2026-05-05T16:00:00Z",
    )

    candidate_keys = [record["payload"]["candidate_key"] for record in result.records]
    assert candidate_keys == ["life_admin:requests", "support:requests"]


def test_build_canonical_candidate_records_invalid_and_missing_outputs_become_durable_records():
    result = build_canonical_candidate_records(
        [
            _cluster_record(1, canonical_wing="life_admin", canonical_room="requests"),
            _cluster_record(2, canonical_wing="support", canonical_room="requests"),
        ],
        {
            "cand_life_admin__requests": "not json at all",
        },
        recorded_at="2026-05-05T16:00:00Z",
    )

    assert [record["record_status"] for record in result.records] == [
        "invalid_model_output",
        "skipped",
    ]
    invalid_payload = result.records[0]["payload"]
    skipped_payload = result.records[1]["payload"]
    assert invalid_payload["error_code"] == "invalid_json"
    assert invalid_payload["raw_response_excerpt"] == "not json at all"
    assert skipped_payload["error_code"] == "missing_model_output"
    assert skipped_payload["source_candidate_key"] == "support:requests"


def test_build_canonical_candidate_records_skips_non_ok_and_wrong_phase_inputs():
    result = build_canonical_candidate_records(
        [
            _cluster_record(1, canonical_wing="life_admin", canonical_room="requests"),
            _cluster_record(
                2,
                canonical_wing="support",
                canonical_room="requests",
                record_status="invalid_model_output",
            ),
            _cluster_record(
                3,
                canonical_wing="work_admin",
                canonical_room="meetings",
                phase="route_pass2",
            ),
        ],
        {
            "cand_life_admin__requests": (
                '{"action":"keep","canonical_wing":"life_admin","canonical_room":"requests",'
                '"label":"Life requests","definition":"Personal logistics requests."}'
            ),
        },
        recorded_at="2026-05-05T16:00:00Z",
    )

    assert len(result.records) == 1
    assert result.records[0]["payload"]["candidate_key"] == "life_admin:requests"
    assert result.skipped_summary["skipped_records"] == 2
    assert result.skipped_summary["skipped_by_reason"] == {
        "record_status_invalid_model_output": 1,
        "wrong_phase": 1,
    }
