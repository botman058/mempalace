import json

from mempalace.ontology_candidates import PHASE_NAME, cluster_pass1_phase_records


RUN_ID = "20260505T143015Z_chatgpt_signal_ontology"


def _pass1_record(
    sequence: int,
    *,
    drawer_id: str,
    proposed_wing: str = "life_admin",
    proposed_room: str = "appointments_and_forms",
    source_wing: str = "chatgpt_signals",
    source_room: str = "general",
    record_status: str = "ok",
    phase: str = "pass1_open",
    attempt: int = 1,
    proposal_label: str | None = None,
    rationale_summary: str | None = None,
    confidence: float | None = None,
    run_id: str = RUN_ID,
):
    payload = {
        "proposed_wing": proposed_wing,
        "proposed_room": proposed_room,
        "proposal_label": proposal_label or proposed_room.replace("_", " "),
    }
    if rationale_summary is not None:
        payload["rationale_summary"] = rationale_summary
    if confidence is not None:
        payload["confidence"] = confidence
    return {
        "schema_name": "ontology.phase_record",
        "schema_version": 1,
        "run_id": run_id,
        "phase": phase,
        "sequence": sequence,
        "attempt": attempt,
        "recorded_at": f"2026-05-05T14:{sequence:02d}:00Z",
        "subject_type": "drawer",
        "subject_id": drawer_id,
        "record_status": record_status,
        "source": {
            "wing": source_wing,
            "room": source_room,
            "drawer_id": drawer_id,
        },
        "payload": payload,
    }


def _payload_by_candidate_key(result):
    return {
        record["payload"]["candidate_key"]: record["payload"]
        for record in result.records
    }


def test_cluster_groups_same_wing_room_together():
    result = cluster_pass1_phase_records(
        [
            _pass1_record(
                3,
                drawer_id="drawer_b",
                proposal_label="appointments and forms",
                confidence=0.7,
            ),
            _pass1_record(
                1,
                drawer_id="drawer_a",
                proposal_label="appointments and forms",
                rationale_summary="Scheduling paperwork and forms.",
                confidence=0.9,
            ),
            _pass1_record(
                2,
                drawer_id="drawer_c",
                proposed_wing="support",
                proposed_room="requests",
            ),
        ],
        recorded_at="2026-05-05T15:00:00Z",
    )

    payload = _payload_by_candidate_key(result)["life_admin:appointments_and_forms"]
    assert payload["candidate_id"] == "cand_life_admin__appointments_and_forms"
    assert payload["cluster_stats"]["source_drawer_count"] == 2
    assert payload["cluster_stats"]["confidence_avg"] == 0.8
    assert payload["source_drawer_refs"] == [
        {
            "drawer_id": "drawer_a",
            "source_wing": "chatgpt_signals",
            "source_room": "general",
            "pass1_record_ref": "pass1_open.jsonl#1",
        },
        {
            "drawer_id": "drawer_b",
            "source_wing": "chatgpt_signals",
            "source_room": "general",
            "pass1_record_ref": "pass1_open.jsonl#3",
        },
    ]


def test_cluster_preserves_same_room_name_under_different_wings():
    result = cluster_pass1_phase_records(
        [
            _pass1_record(
                1,
                drawer_id="drawer_life",
                proposed_wing="life_admin",
                proposed_room="requests",
            ),
            _pass1_record(
                2,
                drawer_id="drawer_support",
                proposed_wing="support",
                proposed_room="requests",
            ),
        ],
        recorded_at="2026-05-05T15:00:00Z",
    )

    candidate_keys = [record["payload"]["candidate_key"] for record in result.records]
    candidate_ids = [record["subject_id"] for record in result.records]

    assert candidate_keys == ["life_admin:requests", "support:requests"]
    assert candidate_ids == ["cand_life_admin__requests", "cand_support__requests"]


def test_cluster_output_order_and_ids_are_deterministic():
    records = [
        _pass1_record(4, drawer_id="drawer_d", proposed_wing="work_admin", proposed_room="meetings"),
        _pass1_record(2, drawer_id="drawer_b", proposed_wing="support", proposed_room="requests"),
        _pass1_record(1, drawer_id="drawer_a", proposed_wing="life_admin", proposed_room="forms"),
        _pass1_record(3, drawer_id="drawer_c", proposed_wing="support", proposed_room="requests"),
    ]

    first = cluster_pass1_phase_records(records, recorded_at="2026-05-05T15:00:00Z")
    second = cluster_pass1_phase_records(list(reversed(records)), recorded_at="2026-05-05T15:00:00Z")

    assert [record["subject_id"] for record in first.records] == [
        "cand_life_admin__forms",
        "cand_support__requests",
        "cand_work_admin__meetings",
    ]
    assert first.records == second.records


def test_cluster_respects_example_limit_without_dropping_refs():
    result = cluster_pass1_phase_records(
        [
            _pass1_record(1, drawer_id="drawer_1"),
            _pass1_record(2, drawer_id="drawer_2"),
            _pass1_record(3, drawer_id="drawer_3"),
            _pass1_record(4, drawer_id="drawer_4"),
        ],
        recorded_at="2026-05-05T15:00:00Z",
        example_limit=2,
    )

    payload = result.records[0]["payload"]
    assert len(payload["examples"]) == 2
    assert [example["drawer_id"] for example in payload["examples"]] == ["drawer_1", "drawer_2"]
    assert len(payload["source_drawer_refs"]) == 4
    assert payload["cluster_stats"]["source_drawer_count"] == 4


def test_cluster_skips_invalid_non_ok_pass1_records():
    result = cluster_pass1_phase_records(
        [
            _pass1_record(1, drawer_id="drawer_ok"),
            _pass1_record(2, drawer_id="drawer_invalid_status", record_status="invalid_model_output"),
            _pass1_record(
                3,
                drawer_id="drawer_bad_slug",
                proposed_wing="Life Admin",
            ),
            _pass1_record(
                4,
                drawer_id="drawer_wrong_phase",
                phase="route_pass2",
            ),
        ],
        recorded_at="2026-05-05T15:00:00Z",
    )

    assert len(result.records) == 1
    assert result.records[0]["payload"]["candidate_key"] == "life_admin:appointments_and_forms"
    assert result.skipped_summary["skipped_records"] == 3
    assert result.skipped_summary["skipped_by_reason"] == {
        "invalid_proposed_wing": 1,
        "record_status_invalid_model_output": 1,
        "wrong_phase": 1,
    }


def test_candidate_cluster_record_is_jsonl_ready():
    result = cluster_pass1_phase_records(
        [
            _pass1_record(
                1,
                drawer_id="drawer_a",
                rationale_summary="Scheduling paperwork and forms.",
                confidence=0.91,
            )
        ],
        recorded_at="2026-05-05T15:00:00Z",
    )

    record = result.records[0]
    line = json.dumps(record, separators=(",", ":")) + "\n"
    parsed = json.loads(line)

    assert line.endswith("\n")
    assert parsed["schema_name"] == "ontology.phase_record"
    assert parsed["phase"] == PHASE_NAME
    assert parsed["subject_type"] == "candidate"
    assert parsed["subject_id"] == "cand_life_admin__appointments_and_forms"
    assert parsed["payload"]["canonical_wing"] == "life_admin"
    assert parsed["payload"]["canonical_room"] == "appointments_and_forms"
    assert parsed["payload"]["examples"][0]["pass1_record_ref"] == "pass1_open.jsonl#1"
