import json

from mempalace.ontology_candidates import build_candidate_id
from mempalace.ontology_route_candidates import (
    PHASE_NAME,
    build_candidate_index,
    build_route_candidate_records,
    select_route_candidates_for_drawer,
)


RUN_ID = "20260505T143015Z_chatgpt_signal_ontology"


def _drawer(
    drawer_id: str,
    content: str,
    *,
    wing: str = "chatgpt_signals",
    room: str = "general",
):
    return {
        "drawer_id": drawer_id,
        "wing": wing,
        "room": room,
        "content": content,
    }


def _canonical_record(
    sequence: int,
    *,
    action: str = "keep",
    source_wing: str = "support",
    source_room: str = "requests",
    canonical_wing: str | None = None,
    canonical_room: str | None = None,
    label: str | None = None,
    definition: str | None = None,
    target_source_wing: str | None = None,
    target_source_room: str | None = None,
    record_status: str = "ok",
    phase: str = "canonical_candidates",
    run_id: str = RUN_ID,
):
    source_candidate_id = build_candidate_id(source_wing, source_room)
    source_candidate_key = f"{source_wing}:{source_room}"
    canonical_wing = canonical_wing or source_wing
    canonical_room = canonical_room or source_room
    payload = {
        "action": action,
        "source_candidate_id": source_candidate_id,
        "source_candidate_key": source_candidate_key,
        "source_canonical_wing": source_wing,
        "source_canonical_room": source_room,
        "source_candidate_record_ref": f"candidate_clusters.jsonl#{sequence}",
        "cluster_stats": {
            "source_drawer_count": 2,
        },
        "centroid": {
            "proposal_labels": [{"proposal_label": label or canonical_room.replace("_", " "), "count": 2}],
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
                "proposal_label": label or canonical_room.replace("_", " "),
                "rationale_summary": definition or f"Signals for {canonical_room.replace('_', ' ')}.",
            }
        ],
    }

    if action == "keep":
        payload.update(
            {
                "candidate_id": build_candidate_id(canonical_wing, canonical_room),
                "candidate_key": f"{canonical_wing}:{canonical_room}",
                "canonical_wing": canonical_wing,
                "canonical_room": canonical_room,
                "label": label or canonical_room.replace("_", " "),
                "definition": definition or f"Signals about {canonical_room.replace('_', ' ')}.",
            }
        )
    elif action == "merge":
        target_source_wing = target_source_wing or "support"
        target_source_room = target_source_room or "requests"
        target_candidate_id = build_candidate_id(target_source_wing, target_source_room)
        target_candidate_key = f"{target_source_wing}:{target_source_room}"
        payload.update(
            {
                "candidate_id": target_candidate_id,
                "candidate_key": target_candidate_key,
                "canonical_wing": target_source_wing,
                "canonical_room": target_source_room,
                "merge_target_candidate_id": target_candidate_id,
                "merge_target_candidate_key": target_candidate_key,
            }
        )
    else:
        payload.update(
            {
                "candidate_id": build_candidate_id(canonical_wing, canonical_room),
                "candidate_key": f"{canonical_wing}:{canonical_room}",
                "canonical_wing": canonical_wing,
                "canonical_room": canonical_room,
                "prune_reason": "too_sparse",
            }
        )

    return {
        "schema_name": "ontology.phase_record",
        "schema_version": 1,
        "run_id": run_id,
        "phase": phase,
        "sequence": sequence,
        "attempt": 1,
        "recorded_at": f"2026-05-05T16:{sequence:02d}:00Z",
        "subject_type": "candidate",
        "subject_id": source_candidate_id,
        "record_status": record_status,
        "source": {
            "wing": source_wing,
            "room": source_room,
            "candidate_id": source_candidate_id,
            "candidate_key": source_candidate_key,
        },
        "payload": payload,
    }


def test_build_candidate_index_resolves_merges_and_excludes_pruned_candidates():
    records = [
        _canonical_record(
            1,
            action="keep",
            source_wing="support",
            source_room="requests",
            canonical_wing="support",
            canonical_room="customer_support",
            label="Customer support",
            definition="Bug reports, ticket triage, and troubleshooting requests.",
        ),
        _canonical_record(
            2,
            action="merge",
            source_wing="support",
            source_room="faq",
            target_source_wing="support",
            target_source_room="requests",
        ),
        _canonical_record(
            3,
            action="prune",
            source_wing="misc",
            source_room="scratch",
            canonical_wing="misc",
            canonical_room="scratch",
        ),
    ]

    result = build_candidate_index(records)

    assert [candidate.candidate_key for candidate in result.candidates] == ["support:customer_support"]
    candidate = result.candidates[0]
    assert candidate.candidate_id == "cand_support__customer_support"
    assert [ref["source_candidate_key"] for ref in candidate.source_candidate_refs] == [
        "support:requests",
        "support:faq",
    ]
    assert [ref["action"] for ref in candidate.source_candidate_refs] == ["keep", "merge"]
    assert result.skipped_summary["pruned_records"] == 1
    assert result.skipped_summary["resolved_merge_records"] == 1


def test_select_route_candidates_preserves_same_room_name_across_wings():
    index = build_candidate_index(
        [
            _canonical_record(
                1,
                source_wing="life_admin",
                source_room="requests",
                label="Life requests",
                definition="Personal logistics, appointments, and paperwork requests.",
            ),
            _canonical_record(
                2,
                source_wing="support",
                source_room="requests",
                label="Support requests",
                definition="Bug tickets, troubleshooting, and customer support requests.",
            ),
        ]
    )

    result = select_route_candidates_for_drawer(
        _drawer(
            "drawer_support_001",
            "Need support request triage for a login bug ticket and customer troubleshooting.",
        ),
        index,
    )

    assert result.record_status == "ok"
    assert [item["candidate_key"] for item in result.payload["route_candidates"]] == [
        "support:requests",
        "life_admin:requests",
    ]
    assert result.payload["route_candidates"][0]["score"] > result.payload["route_candidates"][1]["score"]


def test_select_route_candidates_caps_top_k_and_order_is_deterministic():
    canonical_records = [
        _canonical_record(
            1,
            source_wing="life_admin",
            source_room="appointments_and_forms",
            label="Appointments and forms",
            definition="Scheduling appointments, intake forms, and reschedule paperwork.",
        ),
        _canonical_record(
            2,
            source_wing="support",
            source_room="bug_reports",
            label="Bug reports",
            definition="Errors, crashes, and troubleshooting bugs.",
        ),
        _canonical_record(
            3,
            source_wing="finance",
            source_room="billing_questions",
            label="Billing questions",
            definition="Invoices, charges, billing, and refund questions.",
        ),
        _canonical_record(
            4,
            source_wing="work_admin",
            source_room="meeting_notes",
            label="Meeting notes",
            definition="Meeting agenda planning and notes.",
        ),
        _canonical_record(
            5,
            source_wing="wellness",
            source_room="medication_refills",
            label="Medication refills",
            definition="Prescription refill and medication requests.",
        ),
        _canonical_record(
            6,
            source_wing="travel",
            source_room="trip_plans",
            label="Trip plans",
            definition="Travel itineraries, flights, and hotel planning.",
        ),
    ]
    drawer = _drawer(
        "drawer_mix_001",
        (
            "Please reschedule the appointment, update the intake form, investigate the bug crash, "
            "check the invoice billing issue, prepare the meeting agenda, refill the medication, "
            "and maybe note one hotel question."
        ),
    )

    first = select_route_candidates_for_drawer(drawer, build_candidate_index(canonical_records))
    second = select_route_candidates_for_drawer(drawer, build_candidate_index(list(reversed(canonical_records))))

    assert len(first.payload["route_candidates"]) == 5
    assert first.payload["route_candidates"] == second.payload["route_candidates"]
    assert [item["rank"] for item in first.payload["route_candidates"]] == [1, 2, 3, 4, 5]
    candidate_keys = [item["candidate_key"] for item in first.payload["route_candidates"]]
    assert candidate_keys[0] == "life_admin:appointments_and_forms"
    assert "support:bug_reports" in candidate_keys
    assert "travel:trip_plans" not in candidate_keys


def test_build_route_candidate_records_handles_empty_candidates_and_no_matches():
    empty = build_route_candidate_records(
        [_drawer("drawer_empty_001", "Need something routed later.")],
        [],
        run_id=RUN_ID,
        recorded_at="2026-05-05T17:00:00Z",
    )

    assert empty.records[0]["record_status"] == "skipped"
    assert empty.records[0]["payload"]["error_code"] == "no_retrievable_candidates"
    assert empty.records[0]["payload"]["route_candidates"] == []

    no_match = build_route_candidate_records(
        [_drawer("drawer_nomatch_001", "Quantum entanglement tensor calculus and lattice proofs.")],
        [
            _canonical_record(
                1,
                source_wing="support",
                source_room="requests",
                label="Support requests",
                definition="Customer support and bug request traffic.",
            )
        ],
        recorded_at="2026-05-05T17:05:00Z",
    )

    assert no_match.records[0]["record_status"] == "ok"
    assert no_match.records[0]["payload"]["retrieval_status"] == "no_plausible_candidates"
    assert no_match.records[0]["payload"]["route_candidates"] == []


def test_build_candidate_index_summarizes_invalid_canonical_records():
    records = [
        _canonical_record(1, source_wing="support", source_room="requests"),
        _canonical_record(2, source_wing="support", source_room="broken", phase="route_pass2"),
        _canonical_record(3, source_wing="support", source_room="invalid", record_status="invalid_model_output"),
        {
            **_canonical_record(4, source_wing="support", source_room="mismatch"),
            "payload": {
                **_canonical_record(4, source_wing="support", source_room="mismatch")["payload"],
                "candidate_key": "Support:mismatch",
            },
        },
    ]

    result = build_candidate_index(records)

    assert [candidate.candidate_key for candidate in result.candidates] == ["support:requests"]
    assert result.skipped_summary["skipped_by_reason"] == {
        "invalid_candidate_key": 1,
        "record_status_invalid_model_output": 1,
        "wrong_phase": 1,
    }


def test_route_candidate_records_are_jsonl_ready():
    result = build_route_candidate_records(
        [
            _drawer(
                "drawer_jsonl_001",
                "Need support troubleshooting for this login bug request.",
            )
        ],
        [
            _canonical_record(
                1,
                source_wing="support",
                source_room="requests",
                label="Support requests",
                definition="Bug tickets and troubleshooting requests.",
            )
        ],
        recorded_at="2026-05-05T17:10:00Z",
    )

    record = result.records[0]
    line = json.dumps(record, separators=(",", ":")) + "\n"
    parsed = json.loads(line)

    assert line.endswith("\n")
    assert parsed["schema_name"] == "ontology.phase_record"
    assert parsed["phase"] == PHASE_NAME
    assert parsed["subject_type"] == "drawer"
    assert parsed["record_status"] == "ok"
    assert parsed["payload"]["route_candidates"][0]["candidate_key"] == "support:requests"
    assert parsed["payload"]["route_candidates"][0]["examples"][0]["pass1_record_ref"] == "pass1_open.jsonl#1"
