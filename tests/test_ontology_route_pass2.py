import json

from mempalace.ontology_candidates import build_candidate_id
from mempalace.ontology_route_pass2 import (
    PHASE_NAME,
    RAW_RESPONSE_EXCERPT_MAX_CHARS,
    build_route_pass2_prompt,
    parse_route_pass2_response,
)


RUN_ID = "20260505T143015Z_chatgpt_signal_ontology"


def _drawer(**overrides):
    drawer = {
        "drawer_id": "drawer_chatgpt_signals_general_route001",
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
        "subject_id": "drawer_chatgpt_signals_general_route001",
        "record_status": "ok",
        "source": {
            "wing": "chatgpt_signals",
            "room": "general",
            "drawer_id": "drawer_chatgpt_signals_general_route001",
        },
        "payload": {
            "drawer_excerpt": "Please reschedule the appointment and update the intake form.",
            "candidate_index_size": len(candidates),
            "candidate_count": len(candidates),
            "retrieval_status": "ok",
            "route_candidates": candidates,
        },
    }


def test_build_route_pass2_prompt_includes_drawer_excerpt_and_exact_shortlist_choices():
    prompt = build_route_pass2_prompt(_drawer(), _route_candidate_record())

    assert "Please reschedule the appointment" in prompt
    assert '"candidate_key": "life_admin:appointments_and_forms"' in prompt
    assert '"candidate_id": "cand_life_admin__appointments_and_forms"' in prompt
    assert '"candidate_key": "support:requests"' in prompt
    assert 'Choose exactly one shortlist candidate or `null`.' in prompt


def test_parse_route_pass2_response_valid_candidate_selection_preserves_provenance():
    record = parse_route_pass2_response(
        _drawer(),
        _route_candidate_record(),
        (
            '{"route":"candidate","selected_candidate_id":"cand_life_admin__appointments_and_forms",'
            '"selected_candidate_key":"life_admin:appointments_and_forms",'
            '"canonical_wing":"life_admin","canonical_room":"appointments_and_forms",'
            '"route_confidence":0.91,"rationale_summary":"The drawer is about scheduling and forms."}'
        ),
        recorded_at="2026-05-05T17:20:00Z",
    )

    assert record["record_status"] == "ok"
    assert record["phase"] == PHASE_NAME
    assert record["subject_type"] == "drawer"
    assert record["payload"] == {
        "drawer_excerpt": (
            "Please reschedule the appointment, update the intake form, and confirm the "
            "paperwork deadline before next Tuesday."
        ),
        "shortlist_size": 2,
        "shortlist_candidate_ids": [
            "cand_life_admin__appointments_and_forms",
            "cand_support__requests",
        ],
        "shortlist_candidate_keys": [
            "life_admin:appointments_and_forms",
            "support:requests",
        ],
        "route_candidate_record_ref": "route_candidates.jsonl#54",
        "route_status": "selected",
        "selected_candidate_id": "cand_life_admin__appointments_and_forms",
        "selected_candidate_key": "life_admin:appointments_and_forms",
        "selected_candidate_rank": 1,
        "candidate_id": "cand_life_admin__appointments_and_forms",
        "candidate_key": "life_admin:appointments_and_forms",
        "canonical_wing": "life_admin",
        "canonical_room": "appointments_and_forms",
        "canonical_candidate_record_ref": "canonical_candidates.jsonl#1",
        "source_candidate_refs": [
            {
                "source_candidate_id": "cand_life_admin__appointments_and_forms",
                "source_candidate_key": "life_admin:appointments_and_forms",
                "canonical_candidate_record_ref": "canonical_candidates.jsonl#1",
                "source_candidate_record_ref": "candidate_clusters.jsonl#1",
                "action": "keep",
            }
        ],
        "route_confidence": 0.91,
        "rationale_summary": "The drawer is about scheduling and forms.",
    }


def test_parse_route_pass2_response_valid_null_route():
    record = parse_route_pass2_response(
        _drawer(),
        _route_candidate_record(),
        (
            '{"route":"null","selected_candidate_id":null,"selected_candidate_key":null,'
            '"canonical_wing":null,"canonical_room":null,"route_confidence":0.22,'
            '"reason_code":"no_clear_match","reason_detail":"The shortlist does not fit well enough.",'
            '"next_action":"manual_review","rationale_summary":"The drawer mixes multiple intents."}'
        ),
        recorded_at="2026-05-05T17:21:00Z",
    )

    assert record["record_status"] == "ok"
    assert record["payload"]["route_status"] == "null_route"
    assert record["payload"]["selected_candidate_id"] is None
    assert record["payload"]["route_confidence"] == 0.22
    assert record["payload"]["reason_code"] == "no_clear_match"
    assert record["payload"]["reason_detail"] == "The shortlist does not fit well enough."
    assert record["payload"]["next_action"] == "manual_review"
    assert record["payload"]["rationale_summary"] == "The drawer mixes multiple intents."


def test_parse_route_pass2_response_invalid_json_becomes_invalid_model_output():
    record = parse_route_pass2_response(
        _drawer(),
        _route_candidate_record(),
        "not json at all",
        recorded_at="2026-05-05T17:22:00Z",
    )

    assert record["record_status"] == "invalid_model_output"
    assert record["payload"]["error_code"] == "invalid_json"
    assert record["payload"]["raw_response_excerpt"] == "not json at all"
    assert record["payload"]["retryable"] is True


def test_parse_route_pass2_response_missing_selected_candidate_is_invalid():
    record = parse_route_pass2_response(
        _drawer(),
        _route_candidate_record(),
        '{"route":"candidate","canonical_wing":"life_admin","canonical_room":"appointments_and_forms"}',
        recorded_at="2026-05-05T17:23:00Z",
    )

    assert record["record_status"] == "invalid_model_output"
    assert record["payload"]["error_code"] == "missing_selected_candidate"


def test_parse_route_pass2_response_selected_candidate_not_in_shortlist_is_invalid():
    record = parse_route_pass2_response(
        _drawer(),
        _route_candidate_record(),
        (
            '{"route":"candidate","selected_candidate_id":"cand_finance__billing",'
            '"selected_candidate_key":"finance:billing","canonical_wing":"finance",'
            '"canonical_room":"billing"}'
        ),
        recorded_at="2026-05-05T17:24:00Z",
    )

    assert record["record_status"] == "invalid_model_output"
    assert record["payload"]["error_code"] == "candidate_not_in_shortlist"


def test_parse_route_pass2_response_wing_room_mismatch_is_invalid():
    record = parse_route_pass2_response(
        _drawer(),
        _route_candidate_record(),
        (
            '{"route":"candidate","selected_candidate_id":"cand_life_admin__appointments_and_forms",'
            '"selected_candidate_key":"life_admin:appointments_and_forms",'
            '"canonical_wing":"support","canonical_room":"requests"}'
        ),
        recorded_at="2026-05-05T17:25:00Z",
    )

    assert record["record_status"] == "invalid_model_output"
    assert record["payload"]["error_code"] == "canonical_wing_room_mismatch"


def test_parse_route_pass2_response_invalid_confidence_is_invalid():
    record = parse_route_pass2_response(
        _drawer(),
        _route_candidate_record(),
        (
            '{"route":"candidate","selected_candidate_id":"cand_life_admin__appointments_and_forms",'
            '"selected_candidate_key":"life_admin:appointments_and_forms",'
            '"canonical_wing":"life_admin","canonical_room":"appointments_and_forms",'
            '"route_confidence":1.5}'
        ),
        recorded_at="2026-05-05T17:26:00Z",
    )

    assert record["record_status"] == "invalid_model_output"
    assert record["payload"]["error_code"] == "invalid_confidence"


def test_parse_route_pass2_response_is_jsonl_ready():
    record = parse_route_pass2_response(
        _drawer(),
        _route_candidate_record(),
        (
            '{"route":"candidate","selected_candidate_id":"cand_life_admin__appointments_and_forms",'
            '"selected_candidate_key":"life_admin:appointments_and_forms",'
            '"canonical_wing":"life_admin","canonical_room":"appointments_and_forms"}'
        ),
        recorded_at="2026-05-05T17:27:00Z",
    )

    line = json.dumps(record, separators=(",", ":")) + "\n"
    parsed = json.loads(line)

    assert line.endswith("\n")
    assert parsed["schema_name"] == "ontology.phase_record"
    assert parsed["phase"] == PHASE_NAME
    assert parsed["subject_type"] == "drawer"
    assert parsed["payload"]["selected_candidate_key"] == "life_admin:appointments_and_forms"


def test_prompt_and_parser_preserve_same_room_name_across_wings():
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

    prompt = build_route_pass2_prompt(_drawer(), route_record)
    record = parse_route_pass2_response(
        _drawer(),
        route_record,
        (
            '{"route":"candidate","selected_candidate_id":"cand_support__requests",'
            '"selected_candidate_key":"support:requests","canonical_wing":"support",'
            '"canonical_room":"requests","route_confidence":0.83}'
        ),
        recorded_at="2026-05-05T17:28:00Z",
    )

    assert '"candidate_key": "life_admin:requests"' in prompt
    assert '"candidate_key": "support:requests"' in prompt
    assert record["record_status"] == "ok"
    assert record["payload"]["selected_candidate_id"] == "cand_support__requests"
    assert record["payload"]["selected_candidate_key"] == "support:requests"
    assert record["payload"]["canonical_wing"] == "support"
    assert record["payload"]["canonical_room"] == "requests"


def test_parse_route_pass2_response_non_text_response_becomes_invalid_model_output():
    record = parse_route_pass2_response(
        _drawer(),
        _route_candidate_record(),
        {"unexpected": "shape"},
        recorded_at="2026-05-05T17:29:00Z",
    )

    assert record["record_status"] == "invalid_model_output"
    assert record["payload"]["error_code"] == "invalid_response_text"
    assert record["payload"]["raw_response_excerpt"] == '{"unexpected":"shape"}'


def test_parse_route_pass2_response_bounds_raw_excerpt():
    raw = "not-json " + ("x" * (RAW_RESPONSE_EXCERPT_MAX_CHARS + 40))

    record = parse_route_pass2_response(
        _drawer(),
        _route_candidate_record(),
        raw,
        recorded_at="2026-05-05T17:30:00Z",
    )

    excerpt = record["payload"]["raw_response_excerpt"]
    assert record["record_status"] == "invalid_model_output"
    assert len(excerpt) == RAW_RESPONSE_EXCERPT_MAX_CHARS
    assert excerpt.endswith("...")
