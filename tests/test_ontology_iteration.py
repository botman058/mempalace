import json

from mempalace.ontology_iteration import (
    build_apply_ready_manifest,
    build_convergence_report,
    build_iteration_decision_records,
)


RUN_ID = "20260505T143015Z_chatgpt_signal_ontology"


def _verification_record(
    *,
    sequence: int,
    attempt: int = 1,
    drawer_id: str = "drawer_chatgpt_signals_general_iteration001",
    source_wing: str = "chatgpt_signals",
    source_room: str = "general",
    record_status: str = "ok",
    route_status: str = "accepted",
    copy_ready: bool | None = True,
    selected_candidate_id: str | None = "cand_life_admin__appointments_and_forms",
    selected_candidate_key: str | None = "life_admin:appointments_and_forms",
    canonical_wing: str | None = "life_admin",
    canonical_room: str | None = "appointments_and_forms",
    route_confidence: float | None = 0.91,
    verification_confidence: float | None = 0.96,
    rationale_summary: str | None = "Verified against drawer text.",
    route_rationale_summary: str | None = "The drawer is about scheduling and forms.",
    reason_code: str | None = None,
    reason_detail: str | None = None,
    next_action: str | None = None,
    retryable: bool | None = None,
    route_record_ref: str | None = None,
    route_candidate_record_ref: str | None = None,
    canonical_candidate_record_ref: str | None = "canonical_candidates.jsonl#1",
    source_candidate_refs: list[dict] | None = None,
    shortlist_candidate_ids: list[str] | None = None,
    shortlist_candidate_keys: list[str] | None = None,
    drawer_excerpt: str = "Please reschedule the appointment and update the intake form.",
):
    payload = {
        "route_iteration": attempt,
        "route_status": route_status,
        "route_record_ref": route_record_ref or f"route_pass2.jsonl#{sequence}",
        "route_candidate_record_ref": route_candidate_record_ref or f"route_candidates.jsonl#{sequence}",
        "route_confidence": route_confidence,
        "verification_confidence": verification_confidence,
        "rationale_summary": rationale_summary,
        "route_rationale_summary": route_rationale_summary,
        "drawer_excerpt": drawer_excerpt,
        "shortlist_candidate_ids": shortlist_candidate_ids
        or ["cand_life_admin__appointments_and_forms", "cand_support__requests"],
        "shortlist_candidate_keys": shortlist_candidate_keys
        or ["life_admin:appointments_and_forms", "support:requests"],
    }
    if copy_ready is not None:
        payload["copy_ready"] = copy_ready
    if selected_candidate_id is not None:
        payload["selected_candidate_id"] = selected_candidate_id
        payload["candidate_id"] = selected_candidate_id
    if selected_candidate_key is not None:
        payload["selected_candidate_key"] = selected_candidate_key
        payload["candidate_key"] = selected_candidate_key
    if canonical_wing is not None:
        payload["canonical_wing"] = canonical_wing
    if canonical_room is not None:
        payload["canonical_room"] = canonical_room
    if canonical_candidate_record_ref is not None:
        payload["canonical_candidate_record_ref"] = canonical_candidate_record_ref
    if source_candidate_refs is not None:
        payload["source_candidate_refs"] = source_candidate_refs
    else:
        payload["source_candidate_refs"] = [
            {
                "source_candidate_id": "cand_life_admin__appointments_and_forms",
                "source_candidate_key": "life_admin:appointments_and_forms",
                "canonical_candidate_record_ref": "canonical_candidates.jsonl#1",
                "source_candidate_record_ref": "candidate_clusters.jsonl#1",
                "action": "keep",
            }
        ]
    if reason_code is not None:
        payload["reason_code"] = reason_code
    if reason_detail is not None:
        payload["reason_detail"] = reason_detail
    if next_action is not None:
        payload["next_action"] = next_action
    if retryable is not None:
        payload["retryable"] = retryable

    return {
        "schema_name": "ontology.phase_record",
        "schema_version": 1,
        "run_id": RUN_ID,
        "phase": "route_verify",
        "sequence": sequence,
        "attempt": attempt,
        "recorded_at": f"2026-05-05T17:{sequence:02d}:00Z",
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


def test_build_iteration_decision_records_generates_accepted_route():
    source_candidate_refs = [
        {
            "source_candidate_id": "cand_life_admin__appointments_and_forms",
            "source_candidate_key": "life_admin:appointments_and_forms",
            "canonical_candidate_record_ref": "canonical_candidates.jsonl#1",
            "source_candidate_record_ref": "candidate_clusters.jsonl#1",
            "action": "keep",
        }
    ]
    result = build_iteration_decision_records(
        [_verification_record(sequence=1, source_candidate_refs=source_candidate_refs)]
    )

    assert result.skipped_summary["skipped_records"] == 0
    assert result.unresolved_routes == []
    assert len(result.accepted_routes) == 1
    accepted = result.accepted_routes[0]
    assert accepted["schema_name"] == "ontology.accepted_route"
    assert accepted["sequence"] == 1
    assert accepted["route_status"] == "accepted"
    assert accepted["copy_ready"] is True
    assert accepted["source_drawer_id"] == "drawer_chatgpt_signals_general_iteration001"
    assert accepted["candidate_id"] == "cand_life_admin__appointments_and_forms"
    assert accepted["candidate_key"] == "life_admin:appointments_and_forms"
    assert accepted["canonical_wing"] == "life_admin"
    assert accepted["canonical_room"] == "appointments_and_forms"
    assert accepted["route_record_ref"] == "route_pass2.jsonl#1"
    assert accepted["verification_record_ref"] == "route_verify.jsonl#1"
    assert accepted["source_candidate_refs"] == source_candidate_refs


def test_null_route_becomes_unresolved():
    result = build_iteration_decision_records(
        [
            _verification_record(
                sequence=2,
                route_status="null_route",
                copy_ready=False,
                selected_candidate_id=None,
                selected_candidate_key=None,
                canonical_wing=None,
                canonical_room=None,
                route_confidence=0.22,
                verification_confidence=0.84,
                reason_code="no_clear_match",
                reason_detail="The shortlist does not fit well enough.",
                next_action="manual_review",
            )
        ]
    )

    assert result.accepted_routes == []
    unresolved = result.unresolved_routes[0]
    assert unresolved["unresolved_status"] == "null_route"
    assert unresolved["reason_code"] == "no_clear_match"
    assert unresolved["next_action"] == "manual_review"
    assert unresolved["retryable"] is False
    assert unresolved["candidate_ids"] == ["cand_life_admin__appointments_and_forms", "cand_support__requests"]


def test_verification_reject_becomes_unresolved_with_reason_and_next_action():
    result = build_iteration_decision_records(
        [
            _verification_record(
                sequence=3,
                route_status="verification_reject",
                copy_ready=False,
                verification_confidence=0.61,
                reason_code="needs_manual_review",
                reason_detail="Verifier rejected the route as too specific.",
                next_action="manual_review",
            )
        ]
    )

    unresolved = result.unresolved_routes[0]
    assert unresolved["unresolved_status"] == "verification_reject"
    assert unresolved["reason_code"] == "needs_manual_review"
    assert unresolved["reason_detail"] == "Verifier rejected the route as too specific."
    assert unresolved["next_action"] == "manual_review"
    assert unresolved["retryable"] is False


def test_invalid_model_output_becomes_unresolved_and_error_summary():
    records = [
        _verification_record(
            sequence=4,
            record_status="invalid_model_output",
            route_status="selected",
            copy_ready=False,
            selected_candidate_id=None,
            selected_candidate_key=None,
            canonical_wing=None,
            canonical_room=None,
            verification_confidence=None,
            rationale_summary=None,
            route_rationale_summary=None,
            reason_code="missing_reason_code",
            reason_detail="The verifier returned malformed JSON.",
            next_action="retry_later",
            retryable=True,
        )
    ]

    result = build_iteration_decision_records(records)
    assert result.accepted_routes == []
    unresolved = result.unresolved_routes[0]
    assert unresolved["unresolved_status"] == "invalid_model_output"
    assert unresolved["reason_code"] == "missing_reason_code"
    assert unresolved["retryable"] is True

    report = build_convergence_report(records)
    assert report["error_count"] == 1
    assert report["terminal_status"] == "error"
    assert report["reason_counts"] == {"missing_reason_code": 1}


def test_repeated_iterations_supersede_earlier_unresolved_in_convergence_report():
    records = [
        _verification_record(
            sequence=5,
            drawer_id="drawer_chatgpt_signals_general_repeat001",
            attempt=1,
            route_status="verification_reject",
            copy_ready=False,
            verification_confidence=0.64,
            reason_code="needs_manual_review",
            reason_detail="First pass stayed too broad.",
            next_action="manual_review",
        ),
        _verification_record(
            sequence=6,
            drawer_id="drawer_chatgpt_signals_general_repeat001",
            attempt=2,
            route_status="accepted",
            copy_ready=True,
            verification_confidence=0.94,
        ),
    ]

    built = build_iteration_decision_records(records)
    report = build_convergence_report(
        records,
        accepted_routes=built.accepted_routes,
        unresolved_routes=built.unresolved_routes,
    )

    assert len(built.accepted_routes) == 1
    assert len(built.unresolved_routes) == 1
    assert report["terminal_status"] == "converged"
    assert report["accepted_count"] == 1
    assert report["unresolved_count"] == 0
    assert report["error_count"] == 0
    assert report["unresolved_drawer_refs"] == []
    assert report["latest_terminal_drawer_states"] == [
        {
            "source_drawer_id": "drawer_chatgpt_signals_general_repeat001",
            "source_wing": "chatgpt_signals",
            "source_room": "general",
            "route_iteration": 2,
            "terminal_status": "accepted",
            "candidate_ids": ["cand_life_admin__appointments_and_forms"],
            "candidate_keys": ["life_admin:appointments_and_forms"],
            "reason_code": None,
            "reason_detail": None,
            "route_confidence": 0.91,
            "verification_confidence": 0.94,
            "next_action": None,
            "retryable": False,
            "route_record_ref": "route_pass2.jsonl#6",
            "verification_record_ref": "route_verify.jsonl#6",
            "source_excerpt": None,
        }
    ]


def test_conflict_and_low_confidence_reason_counts_are_materialized():
    records = [
        _verification_record(
            sequence=7,
            drawer_id="drawer_chatgpt_signals_general_conflict001",
            route_status="verification_reject",
            copy_ready=False,
            verification_confidence=0.82,
            reason_code="verifier_disagreed",
            reason_detail="The evidence is ambiguous and conflicts across two candidates.",
            next_action="manual_review",
        ),
        _verification_record(
            sequence=8,
            drawer_id="drawer_chatgpt_signals_general_low001",
            route_status="accepted",
            copy_ready=True,
            verification_confidence=0.41,
        ),
    ]

    report = build_convergence_report(records)

    assert report["terminal_status"] == "needs_review"
    assert report["accepted_count"] == 0
    assert report["unresolved_count"] == 2
    assert report["retryable_count"] == 1
    assert report["reason_counts"] == {
        "verification_confidence_below_threshold": 1,
        "verifier_disagreed": 1,
    }
    assert report["terminal_status_counts"] == {"conflict": 1, "low_confidence": 1}
    assert report["iteration_summaries"] == [
        {
            "route_iteration": 1,
            "verification_records": 2,
            "accepted_records": 0,
            "unresolved_records": 2,
            "error_records": 0,
            "retryable_records": 1,
            "status_counts": {"conflict": 1, "low_confidence": 1},
            "reason_counts": {
                "verification_confidence_below_threshold": 1,
                "verifier_disagreed": 1,
            },
        }
    ]


def test_apply_ready_manifest_includes_only_accepted_copy_ready_routes():
    built = build_iteration_decision_records(
        [
            _verification_record(
                sequence=9,
                drawer_id="drawer_chatgpt_signals_general_manifest001",
            ),
            _verification_record(
                sequence=10,
                drawer_id="drawer_chatgpt_signals_general_manifest001",
                attempt=2,
                verification_confidence=0.99,
                route_record_ref="route_pass2.jsonl#10",
            ),
        ]
    )
    invalid_accepted = dict(built.accepted_routes[0])
    invalid_accepted["copy_ready"] = False

    manifest = build_apply_ready_manifest(
        [built.accepted_routes[0], invalid_accepted, built.accepted_routes[1]]
    )

    assert manifest["schema_name"] == "ontology.apply_ready_manifest"
    assert manifest["route_count"] == 1
    assert manifest["routes"] == [
        {
            "source_drawer_id": "drawer_chatgpt_signals_general_manifest001",
            "source_wing": "chatgpt_signals",
            "source_room": "general",
            "route_iteration": 2,
            "candidate_id": "cand_life_admin__appointments_and_forms",
            "candidate_key": "life_admin:appointments_and_forms",
            "canonical_wing": "life_admin",
            "canonical_room": "appointments_and_forms",
            "route_confidence": 0.91,
            "verification_confidence": 0.99,
            "route_record_ref": "route_pass2.jsonl#10",
            "verification_record_ref": "route_verify.jsonl#10",
            "accepted_route_record_ref": "accepted_routes.jsonl#2",
            "route_candidate_record_ref": "route_candidates.jsonl#10",
            "rationale_summary": "Verified against drawer text.",
        }
    ]
    assert manifest["skipped_summary"]["skipped_by_reason"] == {"invalid_accepted_route": 1}


def test_apply_ready_manifest_excludes_stale_accepted_route_when_later_unresolved_is_provided():
    records = [
        _verification_record(
            sequence=11,
            drawer_id="drawer_chatgpt_signals_general_manifest_stale001",
            attempt=1,
            route_status="accepted",
            copy_ready=True,
        ),
        _verification_record(
            sequence=12,
            drawer_id="drawer_chatgpt_signals_general_manifest_stale001",
            attempt=2,
            route_status="verification_reject",
            copy_ready=False,
            verification_confidence=0.68,
            reason_code="verifier_disagreed",
            reason_detail="Later verification found conflicting evidence.",
            next_action="manual_review",
        ),
    ]
    built = build_iteration_decision_records(records)

    manifest = build_apply_ready_manifest(
        built.accepted_routes,
        unresolved_routes=built.unresolved_routes,
    )

    assert len(built.accepted_routes) == 1
    assert len(built.unresolved_routes) == 1
    assert manifest["route_count"] == 0
    assert manifest["routes"] == []
    assert manifest["skipped_summary"]["skipped_records"] == 0


def test_apply_ready_manifest_counts_unresolved_inputs_in_skipped_summary():
    built = build_iteration_decision_records(
        [
            _verification_record(
                sequence=13,
                drawer_id="drawer_chatgpt_signals_general_manifest_count001",
            )
        ]
    )
    invalid_unresolved = {
        "schema_name": "ontology.unresolved_route",
        "schema_version": 1,
        "run_id": RUN_ID,
        "sequence": 1,
        "recorded_at": "2026-05-05T17:13:00Z",
        "route_iteration": 2,
        "source_drawer_id": "drawer_chatgpt_signals_general_manifest_count001",
        "source_wing": "chatgpt_signals",
        "source_room": "general",
        "unresolved_status": "verification_reject",
        "candidate_ids": ["cand_life_admin__appointments_and_forms"],
        "candidate_keys": ["life_admin:appointments_and_forms"],
        "reason_code": "verifier_disagreed",
        "reason_detail": "Later verification found conflicting evidence.",
        "route_record_ref": "route_pass2.jsonl#13",
        "verification_record_ref": "route_verify.jsonl#13",
        "next_action": "not_valid",
        "retryable": False,
        "source_excerpt": "Please reschedule the appointment and update the intake form.",
    }

    manifest = build_apply_ready_manifest(
        built.accepted_routes,
        unresolved_routes=[invalid_unresolved],
    )

    assert manifest["route_count"] == 1
    assert manifest["skipped_summary"] == {
        "input_records": 2,
        "skipped_records": 1,
        "skipped_by_reason": {"invalid_unresolved_route": 1},
    }


def test_invalid_verification_inputs_are_summarized_and_skipped():
    invalid_run_id = _verification_record(sequence=11)
    invalid_run_id["run_id"] = "not valid"

    invalid_attempt = _verification_record(sequence=12)
    invalid_attempt["attempt"] = 0
    invalid_attempt["payload"]["route_iteration"] = 0

    valid = _verification_record(sequence=13, drawer_id="drawer_chatgpt_signals_general_valid001")
    result = build_iteration_decision_records([invalid_run_id, invalid_attempt, valid], run_id=RUN_ID)

    assert len(result.accepted_routes) == 1
    assert result.accepted_routes[0]["source_drawer_id"] == "drawer_chatgpt_signals_general_valid001"
    assert result.skipped_summary["skipped_records"] == 2
    assert result.skipped_summary["skipped_by_reason"] == {
        "invalid_attempt": 1,
        "invalid_run_id": 1,
    }


def test_accepted_and_unresolved_records_are_jsonl_serializable():
    result = build_iteration_decision_records(
        [
            _verification_record(sequence=14, drawer_id="drawer_chatgpt_signals_general_jsonl001"),
            _verification_record(
                sequence=15,
                drawer_id="drawer_chatgpt_signals_general_jsonl002",
                route_status="null_route",
                copy_ready=False,
                selected_candidate_id=None,
                selected_candidate_key=None,
                canonical_wing=None,
                canonical_room=None,
                reason_code="no_clear_match",
                reason_detail="The shortlist does not fit well enough.",
                next_action="manual_review",
            ),
        ]
    )

    accepted_line = json.dumps(result.accepted_routes[0], separators=(",", ":"))
    unresolved_line = json.dumps(result.unresolved_routes[0], separators=(",", ":"))

    assert '"schema_name":"ontology.accepted_route"' in accepted_line
    assert '"schema_name":"ontology.unresolved_route"' in unresolved_line


def test_convergence_report_sample_is_deterministic_and_dashboard_safe():
    records = [
        _verification_record(
            sequence=16,
            drawer_id="drawer_chatgpt_signals_general_b001",
            route_status="verification_reject",
            copy_ready=False,
            verification_confidence=0.74,
            reason_code="verifier_disagreed",
            reason_detail="Candidate evidence conflicts with the source drawer.",
            next_action="manual_review",
        ),
        _verification_record(
            sequence=17,
            drawer_id="drawer_chatgpt_signals_general_a001",
            route_status="accepted",
            copy_ready=True,
            verification_confidence=0.92,
        ),
    ]

    report = build_convergence_report(records)

    assert report["schema_name"] == "ontology.convergence_report"
    assert report["schema_version"] == 1
    assert report["run_id"] == RUN_ID
    assert report["terminal_status"] == "needs_review"
    assert report["total_verification_records"] == 2
    assert report["total_drawers"] == 2
    assert report["latest_terminal_drawer_states"][0]["source_drawer_id"] == (
        "drawer_chatgpt_signals_general_a001"
    )
    assert report["latest_terminal_drawer_states"][1]["source_drawer_id"] == (
        "drawer_chatgpt_signals_general_b001"
    )
    assert report["unresolved_drawer_refs"] == [
        {
            "source_drawer_id": "drawer_chatgpt_signals_general_b001",
            "source_wing": "chatgpt_signals",
            "source_room": "general",
            "route_iteration": 1,
            "unresolved_status": "conflict",
            "candidate_ids": ["cand_life_admin__appointments_and_forms", "cand_support__requests"],
            "candidate_keys": ["life_admin:appointments_and_forms", "support:requests"],
            "reason_code": "verifier_disagreed",
            "reason_detail": "Candidate evidence conflicts with the source drawer.",
            "route_confidence": 0.91,
            "verification_confidence": 0.74,
            "next_action": "manual_review",
            "retryable": False,
            "route_record_ref": "route_pass2.jsonl#16",
            "verification_record_ref": "route_verify.jsonl#16",
            "source_excerpt": "Please reschedule the appointment and update the intake form.",
        }
    ]
    assert "raw_response_excerpt" not in json.dumps(report, sort_keys=True)
