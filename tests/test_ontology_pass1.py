import json
from dataclasses import dataclass

from mempalace.llm_client import LLMResponse
from mempalace.ontology_pass1 import (
    PHASE_NAME,
    RAW_RESPONSE_EXCERPT_MAX_CHARS,
    build_pass1_phase_record,
    build_pass1_prompt,
    classify_drawer_pass1,
    parse_pass1_response,
)


def _source_drawer(**overrides):
    drawer = {
        "drawer_id": "drawer_chatgpt_signals_general_abc123",
        "wing": "chatgpt_signals",
        "room": "general",
        "content": (
            "Please help me reschedule the appointment and update the intake form "
            "before next Tuesday."
        ),
    }
    drawer.update(overrides)
    return drawer


def test_parse_pass1_response_valid_json_maps_to_phase_payload():
    result = parse_pass1_response(
        '{"wing":"life_admin","room":"appointments_and_forms","label":"appointments and forms",'
        '"confidence":0.78,"rationale":"The drawer centers on scheduling logistics."}'
    )

    assert result.record_status == "ok"
    assert result.payload == {
        "proposed_wing": "life_admin",
        "proposed_room": "appointments_and_forms",
        "proposal_label": "appointments and forms",
        "confidence": 0.78,
        "rationale_summary": "The drawer centers on scheduling logistics.",
    }


def test_parse_pass1_response_invalid_json_becomes_invalid_model_output():
    result = parse_pass1_response("not json at all")

    assert result.record_status == "invalid_model_output"
    assert result.payload["error_code"] == "invalid_json"
    assert result.payload["raw_response_excerpt"] == "not json at all"
    assert result.payload["retryable"] is True


def test_parse_pass1_response_missing_room_key_is_rejected():
    result = parse_pass1_response('{"wing":"life_admin"}')

    assert result.record_status == "invalid_model_output"
    assert result.payload["error_code"] == "missing_room_key"
    assert result.payload["raw_response_excerpt"] == '{"wing":"life_admin"}'


def test_parse_pass1_response_rejects_non_slug_room_and_wing():
    room_result = parse_pass1_response('{"wing":"life_admin","room":"Appointments-Forms"}')
    wing_result = parse_pass1_response('{"wing":"Life Admin","room":"appointments_and_forms"}')

    assert room_result.record_status == "invalid_model_output"
    assert room_result.payload["error_code"] == "invalid_room_key"
    assert wing_result.record_status == "invalid_model_output"
    assert wing_result.payload["error_code"] == "invalid_wing_key"


def test_parse_pass1_response_accepts_json_wrapped_in_prose_and_code_fence():
    result = parse_pass1_response(
        'Here is the JSON:\n```json\n{"wing":"life_admin","room":"appointments_and_forms"}\n```'
    )

    assert result.record_status == "ok"
    assert result.payload["proposed_wing"] == "life_admin"
    assert result.payload["proposed_room"] == "appointments_and_forms"


def test_parse_pass1_response_bounds_raw_excerpt():
    raw = "not-json " + ("x" * (RAW_RESPONSE_EXCERPT_MAX_CHARS + 50))
    result = parse_pass1_response(raw)

    assert result.record_status == "invalid_model_output"
    excerpt = result.payload["raw_response_excerpt"]
    assert len(excerpt) == RAW_RESPONSE_EXCERPT_MAX_CHARS
    assert excerpt.endswith("...")


def test_build_pass1_phase_record_emits_jsonl_ready_contract_shape():
    record = build_pass1_phase_record(
        run_id="20260505T143015Z_chatgpt_signal_ontology",
        sequence=148,
        attempt=1,
        source_drawer=_source_drawer(),
        provider_response='{"wing":"life_admin","room":"appointments_and_forms"}',
        recorded_at="2026-05-05T14:41:01Z",
    )

    assert record == {
        "schema_name": "ontology.phase_record",
        "schema_version": 1,
        "run_id": "20260505T143015Z_chatgpt_signal_ontology",
        "phase": PHASE_NAME,
        "sequence": 148,
        "attempt": 1,
        "recorded_at": "2026-05-05T14:41:01Z",
        "subject_type": "drawer",
        "subject_id": "drawer_chatgpt_signals_general_abc123",
        "record_status": "ok",
        "source": {
            "wing": "chatgpt_signals",
            "room": "general",
            "drawer_id": "drawer_chatgpt_signals_general_abc123",
        },
        "payload": {
            "proposed_wing": "life_admin",
            "proposed_room": "appointments_and_forms",
            "proposal_label": "appointments and forms",
        },
    }


def test_build_pass1_phase_record_non_text_response_becomes_invalid_model_output():
    record = build_pass1_phase_record(
        run_id="20260505T143015Z_chatgpt_signal_ontology",
        sequence=149,
        attempt=1,
        source_drawer=_source_drawer(),
        provider_response={"unexpected": "shape"},
        recorded_at="2026-05-05T14:41:02Z",
    )

    assert record["record_status"] == "invalid_model_output"
    assert record["payload"]["error_code"] == "invalid_response_text"
    assert record["payload"]["raw_response_excerpt"] == '{"unexpected":"shape"}'
    assert record["payload"]["retryable"] is True


def test_build_pass1_phase_record_jsonl_round_trip_evidence():
    record = build_pass1_phase_record(
        run_id="20260505T143015Z_chatgpt_signal_ontology",
        sequence=150,
        attempt=1,
        source_drawer=_source_drawer(),
        provider_response='{"wing":"life_admin","room":"appointments_and_forms"}',
        recorded_at="2026-05-05T14:41:03Z",
    )

    line = json.dumps(record, separators=(",", ":")) + "\n"
    parsed = json.loads(line)

    assert line.endswith("\n")
    assert parsed["schema_name"] == "ontology.phase_record"
    assert parsed["phase"] == PHASE_NAME
    assert parsed["record_status"] == "ok"
    assert parsed["subject_type"] == "drawer"
    assert parsed["payload"]["proposed_wing"] == "life_admin"
    assert parsed["payload"]["proposed_room"] == "appointments_and_forms"


@dataclass
class FakeProvider:
    response_text: str
    call_count: int = 0
    last_system: str = ""
    last_user: str = ""
    last_json_mode: bool | None = None

    def classify(self, system, user, json_mode=True):
        self.call_count += 1
        self.last_system = system
        self.last_user = user
        self.last_json_mode = json_mode
        return LLMResponse(text=self.response_text, model="fake", provider="fake", raw={})


def test_classify_drawer_pass1_uses_provider_and_returns_phase_record():
    provider = FakeProvider(
        response_text=(
            '{"wing":"life_admin","room":"appointments_and_forms","label":"appointments and forms"}'
        )
    )

    record = classify_drawer_pass1(
        provider=provider,
        run_id="20260505T143015Z_chatgpt_signal_ontology",
        sequence=147,
        attempt=1,
        source_drawer=_source_drawer(),
        recorded_at="2026-05-05T14:40:56Z",
    )

    prompt = build_pass1_prompt(_source_drawer())
    assert provider.call_count == 1
    assert provider.last_json_mode is True
    assert provider.last_system == prompt.system
    assert "source_wing: chatgpt_signals" in provider.last_user
    assert "reschedule the appointment" in provider.last_user
    assert record["record_status"] == "ok"
    assert record["payload"]["proposed_wing"] == "life_admin"
    assert record["payload"]["proposed_room"] == "appointments_and_forms"
