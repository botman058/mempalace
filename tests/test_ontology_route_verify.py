import json

from mempalace.ontology_candidates import build_candidate_id
from mempalace.ontology_route_verify import (
    PHASE_NAME,
    RAW_RESPONSE_EXCERPT_MAX_CHARS,
    build_route_verify_prompt,
    parse_route_verify_response,
)


RUN_ID = "20260505T143015Z_chatgpt_signal_ontology"


def _drawer(**overrides):
    drawer = {
        "drawer_id": "drawer_chatgpt_signals_general_verify001",
        "wing": "chatgpt_signals",
        "room": "general",
        "content": (
            "Please reschedule the appointment, update the intake form, and confirm the "
            "paperwork deadline before next Tuesday."
        ),
    }
    drawer.update(overrides)
    return drawer


def _route_candidate(
    *,
    rank: int,
    canonical_wing: str,
    canonical_room: str,
    label: str,
    definition: str,
    sequence: int,
):
    return {
        "rank": rank,
        "candidate_id": build_candidate_id(canonical_wing, canonical_room),
        "candidate_key": f"{canonical_wing}:{canonical_room}",
        "canonical_wing": canonical_wing,
        "canonical_room": canonical_room,
        "label": label,
        "definition": definition,
        "canonical_candidate_record_ref": f"canonical_candidates.jsonl#{sequence}",
        "source_candidate_refs": [
            {
                "source_candidate_id": build_candidate_id(canonical_wing, canonical_room),
                "source_candidate_key": f"{canonical_wing}:{canonical_room}",
                "canonical_candidate_record_ref": f"canonical_candidates.jsonl#{sequence}",
                "source_candidate_record_ref": f"candidate_clusters.jsonl#{sequence}",
                "action": "keep",
            }
        ],
        "examples": [
            {
                "proposal_label": label,
                "excerpt": f"Example excerpt for {label.lower()}.",
            }
        ],
    }


def _route_candidate_record(
    *,
    sequence: int = 54,
    route_candidates: list[dict] | None = None,
):
    candidates = route_candidates or [
        _route_candidate(
            rank=1,
            canonical_wing="life_admin",
            canonical_room="appointments_and_forms",
            label="Appointments and forms",
            definition="Scheduling, intake forms, and appointment paperwork.",
            sequence=1,
        ),
        _route_candidate(
            rank=2,
            canonical_wing="support",
            canonical_room="requests",
            label="Support requests",
            definition="Troubleshooting, tickets, and support request traffic.",
            sequence=2,
        ),
    ]
    return {
        "schema_name": "ontology.phase_record",
        "schema_version": 1,
        "run_id": RUN_ID,
        "phase": "route_candidates",
        "sequence": sequence,
        "attempt": 1,
        "recorded_at": "2026-05-05T17:10:00Z",
        "subject_type": "drawer",
        "subject_id": "drawer_chatgpt_signals_general_verify001",
        "record_status": "ok",
        "source": {
            "wing": "chatgpt_signals",
            "room": "general",
            "drawer_id": "drawer_chatgpt_signals_general_verify001",
        },
        "payload": {
            "drawer_excerpt": "Please reschedule the appointment and update the intake form.",
            "candidate_index_size": len(candidates),
            "candidate_count": len(candidates),
            "retrieval_status": "ok",
            "route_candidates": candidates,
        },
    }


def _route_pass2_record(
    *,
    sequence: int = 54,
    route_status: str = "selected",
    candidate: dict | None = None,
    route_confidence: float | None = 0.91,
    rationale_summary: str | None = "The drawer is about scheduling and forms.",
    reason_code: str | None = None,
    reason_detail: str | None = None,
    next_action: str | None = None,
):
    payload = {
        "drawer_excerpt": "Please reschedule the appointment and update the intake form.",
        "route_candidate_record_ref": f"route_candidates.jsonl#{sequence}",
        "route_status": route_status,
        "route_confidence": route_confidence,
        "rationale_summary": rationale_summary,
    }
    if candidate is None:
        payload.update(
            {
                "selected_candidate_id": None,
                "selected_candidate_key": None,
            }
        )
    else:
        payload.update(
            {
                "selected_candidate_id": candidate["candidate_id"],
                "selected_candidate_key": candidate["candidate_key"],
                "candidate_id": candidate["candidate_id"],
                "candidate_key": candidate["candidate_key"],
                "canonical_wing": candidate["canonical_wing"],
                "canonical_room": candidate["canonical_room"],
                "canonical_candidate_record_ref": candidate["canonical_candidate_record_ref"],
                "source_candidate_refs": candidate["source_candidate_refs"],
            }
        )
    if reason_code is not None:
        payload["reason_code"] = reason_code
    if reason_detail is not None:
        payload["reason_detail"] = reason_detail
    if next_action is not None:
        payload["next_action"] = next_action

    return {
        "schema_name": "ontology.phase_record",
        "schema_version": 1,
        "run_id": RUN_ID,
        "phase": "route_pass2",
        "sequence": sequence,
        "attempt": 1,
        "recorded_at": "2026-05-05T17:20:00Z",
        "subject_type": "drawer",
        "subject_id": "drawer_chatgpt_signals_general_verify001",
        "record_status": "ok",
        "source": {
            "wing": "chatgpt_signals",
            "room": "general",
            "drawer_id": "drawer_chatgpt_signals_general_verify001",
        },
        "payload": payload,
    }


def test_build_route_verify_prompt_includes_drawer_excerpt_selected_candidate_and_route_rationale():
    route_record = _route_pass2_record(candidate=_route_candidate_record()["payload"]["route_candidates"][0])

    prompt = build_route_verify_prompt(_drawer(), _route_candidate_record(), route_record)

    assert "Please reschedule the appointment" in prompt
    assert '"candidate_key": "life_admin:appointments_and_forms"' in prompt
    assert "The drawer is about scheduling and forms." in prompt


def test_parse_route_verify_response_approves_selected_candidate():
    selected = _route_candidate_record()["payload"]["route_candidates"][0]
    record = parse_route_verify_response(
        _drawer(),
        _route_candidate_record(),
        _route_pass2_record(candidate=selected),
        (
            '{"verdict":"approve","selected_candidate_id":"cand_life_admin__appointments_and_forms",'
            '"selected_candidate_key":"life_admin:appointments_and_forms",'
            '"canonical_wing":"life_admin","canonical_room":"appointments_and_forms",'
            '"verification_confidence":0.96,"rationale_summary":"Verified against the drawer text."}'
        ),
        recorded_at="2026-05-05T17:30:00Z",
    )

    assert record["record_status"] == "ok"
    assert record["phase"] == PHASE_NAME
    assert record["payload"]["route_status"] == "accepted"
    assert record["payload"]["copy_ready"] is True
    assert record["payload"]["route_record_ref"] == "route_pass2.jsonl#54"
    assert record["payload"]["route_candidate_record_ref"] == "route_candidates.jsonl#54"
    assert record["payload"]["selected_candidate_id"] == "cand_life_admin__appointments_and_forms"
    assert record["payload"]["selected_candidate_key"] == "life_admin:appointments_and_forms"
    assert record["payload"]["canonical_wing"] == "life_admin"
    assert record["payload"]["canonical_room"] == "appointments_and_forms"
    assert record["payload"]["canonical_candidate_record_ref"] == "canonical_candidates.jsonl#1"
    assert record["payload"]["source_candidate_refs"][0]["source_candidate_record_ref"] == (
        "candidate_clusters.jsonl#1"
    )
    assert record["payload"]["route_confidence"] == 0.91
    assert record["payload"]["verification_confidence"] == 0.96
    assert record["payload"]["route_rationale_summary"] == "The drawer is about scheduling and forms."
    assert record["payload"]["rationale_summary"] == "Verified against the drawer text."


def test_parse_route_verify_response_rejects_selected_candidate():
    selected = _route_candidate_record()["payload"]["route_candidates"][0]
    record = parse_route_verify_response(
        _drawer(),
        _route_candidate_record(),
        _route_pass2_record(candidate=selected),
        (
            '{"verdict":"reject","selected_candidate_id":"cand_life_admin__appointments_and_forms",'
            '"selected_candidate_key":"life_admin:appointments_and_forms",'
            '"canonical_wing":"life_admin","canonical_room":"appointments_and_forms",'
            '"verification_confidence":0.24,"reason_code":"needs_manual_review",'
            '"reason_detail":"The drawer still mixes scheduling with other tasks.",'
            '"next_action":"manual_review","rationale_summary":"Route looks too specific."}'
        ),
        recorded_at="2026-05-05T17:31:00Z",
    )

    assert record["record_status"] == "ok"
    assert record["payload"]["route_status"] == "verification_reject"
    assert record["payload"]["copy_ready"] is False
    assert record["payload"]["reason_code"] == "needs_manual_review"
    assert record["payload"]["reason_detail"] == "The drawer still mixes scheduling with other tasks."
    assert record["payload"]["next_action"] == "manual_review"
    assert record["payload"]["verification_confidence"] == 0.24
    assert record["payload"]["selected_candidate_key"] == "life_admin:appointments_and_forms"


def test_parse_route_verify_response_approves_null_route():
    record = parse_route_verify_response(
        _drawer(),
        _route_candidate_record(),
        _route_pass2_record(
            route_status="null_route",
            candidate=None,
            route_confidence=0.22,
            rationale_summary="The shortlist does not fit well enough.",
            reason_code="no_clear_match",
            reason_detail="The shortlist does not fit well enough.",
            next_action="manual_review",
        ),
        (
            '{"verdict":"approve","selected_candidate_id":null,"selected_candidate_key":null,'
            '"canonical_wing":null,"canonical_room":null,"verification_confidence":0.81,'
            '"rationale_summary":"No shortlist candidate is credible."}'
        ),
        recorded_at="2026-05-05T17:32:00Z",
    )

    assert record["record_status"] == "ok"
    assert record["payload"]["route_status"] == "null_route"
    assert record["payload"]["copy_ready"] is False
    assert record["payload"]["selected_candidate_id"] is None
    assert record["payload"]["route_confidence"] == 0.22
    assert record["payload"]["verification_confidence"] == 0.81
    assert record["payload"]["reason_code"] == "no_clear_match"
    assert record["payload"]["reason_detail"] == "The shortlist does not fit well enough."
    assert record["payload"]["next_action"] == "manual_review"


def test_parse_route_verify_response_rejects_null_route():
    record = parse_route_verify_response(
        _drawer(),
        _route_candidate_record(),
        _route_pass2_record(
            route_status="null_route",
            candidate=None,
            route_confidence=0.22,
            rationale_summary="The shortlist does not fit well enough.",
            reason_code="no_clear_match",
            reason_detail="The shortlist does not fit well enough.",
            next_action="manual_review",
        ),
        (
            '{"verdict":"reject","selected_candidate_id":null,"selected_candidate_key":null,'
            '"canonical_wing":null,"canonical_room":null,"verification_confidence":0.64,'
            '"reason_code":"retry_with_shortlist","reason_detail":"A shortlist candidate should be retried.",'
            '"next_action":"reroute","rationale_summary":"Null route was too strict."}'
        ),
        recorded_at="2026-05-05T17:33:00Z",
    )

    assert record["record_status"] == "ok"
    assert record["payload"]["route_status"] == "verification_reject"
    assert record["payload"]["copy_ready"] is False
    assert record["payload"]["selected_candidate_id"] is None
    assert record["payload"]["reason_code"] == "retry_with_shortlist"
    assert record["payload"]["reason_detail"] == "A shortlist candidate should be retried."
    assert record["payload"]["next_action"] == "reroute"


def test_parse_route_verify_response_invalid_json_becomes_invalid_model_output():
    selected = _route_candidate_record()["payload"]["route_candidates"][0]
    record = parse_route_verify_response(
        _drawer(),
        _route_candidate_record(),
        _route_pass2_record(candidate=selected),
        "not json at all",
        recorded_at="2026-05-05T17:34:00Z",
    )

    assert record["record_status"] == "invalid_model_output"
    assert record["payload"]["error_code"] == "invalid_json"
    assert record["payload"]["raw_response_excerpt"] == "not json at all"
    assert record["payload"]["retryable"] is True


def test_parse_route_verify_response_invalid_shape_becomes_invalid_model_output():
    selected = _route_candidate_record()["payload"]["route_candidates"][0]
    record = parse_route_verify_response(
        _drawer(),
        _route_candidate_record(),
        _route_pass2_record(candidate=selected),
        "[]",
        recorded_at="2026-05-05T17:35:00Z",
    )

    assert record["record_status"] == "invalid_model_output"
    assert record["payload"]["error_code"] == "invalid_response_shape"


def test_parse_route_verify_response_missing_verdict_is_invalid():
    selected = _route_candidate_record()["payload"]["route_candidates"][0]
    record = parse_route_verify_response(
        _drawer(),
        _route_candidate_record(),
        _route_pass2_record(candidate=selected),
        (
            '{"selected_candidate_id":"cand_life_admin__appointments_and_forms",'
            '"selected_candidate_key":"life_admin:appointments_and_forms",'
            '"canonical_wing":"life_admin","canonical_room":"appointments_and_forms"}'
        ),
        recorded_at="2026-05-05T17:36:00Z",
    )

    assert record["record_status"] == "invalid_model_output"
    assert record["payload"]["error_code"] == "missing_verdict"


def test_parse_route_verify_response_invalid_confidence_is_invalid():
    selected = _route_candidate_record()["payload"]["route_candidates"][0]
    record = parse_route_verify_response(
        _drawer(),
        _route_candidate_record(),
        _route_pass2_record(candidate=selected),
        (
            '{"verdict":"approve","selected_candidate_id":"cand_life_admin__appointments_and_forms",'
            '"selected_candidate_key":"life_admin:appointments_and_forms",'
            '"canonical_wing":"life_admin","canonical_room":"appointments_and_forms",'
            '"verification_confidence":1.5}'
        ),
        recorded_at="2026-05-05T17:37:00Z",
    )

    assert record["record_status"] == "invalid_model_output"
    assert record["payload"]["error_code"] == "invalid_confidence"


def test_parse_route_verify_response_candidate_provenance_mismatch_is_invalid():
    selected = _route_candidate_record()["payload"]["route_candidates"][0]
    record = parse_route_verify_response(
        _drawer(),
        _route_candidate_record(),
        _route_pass2_record(candidate=selected),
        (
            '{"verdict":"approve","selected_candidate_id":"cand_support__requests",'
            '"selected_candidate_key":"support:requests","canonical_wing":"support",'
            '"canonical_room":"requests","verification_confidence":0.88}'
        ),
        recorded_at="2026-05-05T17:38:00Z",
    )

    assert record["record_status"] == "invalid_model_output"
    assert record["payload"]["error_code"] == "candidate_provenance_mismatch"


def test_parse_route_verify_response_non_text_response_becomes_invalid_model_output():
    selected = _route_candidate_record()["payload"]["route_candidates"][0]
    record = parse_route_verify_response(
        _drawer(),
        _route_candidate_record(),
        _route_pass2_record(candidate=selected),
        {"unexpected": "shape"},
        recorded_at="2026-05-05T17:39:00Z",
    )

    assert record["record_status"] == "invalid_model_output"
    assert record["payload"]["error_code"] == "invalid_response_text"
    assert record["payload"]["raw_response_excerpt"] == '{"unexpected":"shape"}'


def test_parse_route_verify_response_is_jsonl_ready():
    selected = _route_candidate_record()["payload"]["route_candidates"][0]
    record = parse_route_verify_response(
        _drawer(),
        _route_candidate_record(),
        _route_pass2_record(candidate=selected),
        (
            '{"verdict":"approve","selected_candidate_id":"cand_life_admin__appointments_and_forms",'
            '"selected_candidate_key":"life_admin:appointments_and_forms",'
            '"canonical_wing":"life_admin","canonical_room":"appointments_and_forms"}'
        ),
        recorded_at="2026-05-05T17:40:00Z",
    )

    line = json.dumps(record, separators=(",", ":")) + "\n"
    parsed = json.loads(line)

    assert line.endswith("\n")
    assert parsed["schema_name"] == "ontology.phase_record"
    assert parsed["phase"] == PHASE_NAME
    assert parsed["subject_type"] == "drawer"
    assert parsed["payload"]["selected_candidate_key"] == "life_admin:appointments_and_forms"


def test_prompt_and_parser_keep_same_room_different_wing_candidate_keys_distinct():
    route_record = _route_candidate_record(
        route_candidates=[
            _route_candidate(
                rank=1,
                canonical_wing="life_admin",
                canonical_room="requests",
                label="Life requests",
                definition="Personal logistics and intake requests.",
                sequence=1,
            ),
            _route_candidate(
                rank=2,
                canonical_wing="support",
                canonical_room="requests",
                label="Support requests",
                definition="Troubleshooting and support requests.",
                sequence=2,
            ),
        ]
    )
    selected = route_record["payload"]["route_candidates"][1]

    prompt = build_route_verify_prompt(
        _drawer(),
        route_record,
        _route_pass2_record(candidate=selected),
    )
    record = parse_route_verify_response(
        _drawer(),
        route_record,
        _route_pass2_record(candidate=selected),
        (
            '{"verdict":"approve","selected_candidate_id":"cand_support__requests",'
            '"selected_candidate_key":"support:requests","canonical_wing":"support",'
            '"canonical_room":"requests","verification_confidence":0.83}'
        ),
        recorded_at="2026-05-05T17:41:00Z",
    )

    assert '"candidate_key": "life_admin:requests"' in prompt
    assert '"candidate_key": "support:requests"' in prompt
    assert record["record_status"] == "ok"
    assert record["payload"]["selected_candidate_id"] == "cand_support__requests"
    assert record["payload"]["selected_candidate_key"] == "support:requests"
    assert record["payload"]["canonical_wing"] == "support"
    assert record["payload"]["canonical_room"] == "requests"


def test_parse_route_verify_response_bounds_raw_excerpt():
    selected = _route_candidate_record()["payload"]["route_candidates"][0]
    raw = "not-json " + ("x" * (RAW_RESPONSE_EXCERPT_MAX_CHARS + 40))

    record = parse_route_verify_response(
        _drawer(),
        _route_candidate_record(),
        _route_pass2_record(candidate=selected),
        raw,
        recorded_at="2026-05-05T17:42:00Z",
    )

    excerpt = record["payload"]["raw_response_excerpt"]
    assert record["record_status"] == "invalid_model_output"
    assert len(excerpt) == RAW_RESPONSE_EXCERPT_MAX_CHARS
    assert excerpt.endswith("...")
