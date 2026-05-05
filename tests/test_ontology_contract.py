from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from mempalace.mcp_server import _ontology_copy_drawer_id
from mempalace.ontology_candidate_names import build_canonical_candidate_records
from mempalace.ontology_candidates import (
    build_candidate_id,
    cluster_pass1_phase_records,
)
from mempalace.ontology_iteration import (
    build_apply_ready_manifest,
    build_convergence_report,
    build_iteration_decision_records,
)
from mempalace.ontology_pass1 import build_pass1_phase_record, parse_pass1_response
from mempalace.ontology_route_candidates import build_route_candidate_records
from mempalace.ontology_route_candidates import build_candidate_index
from mempalace.ontology_route_pass2 import parse_route_pass2_response
from mempalace.ontology_route_verify import parse_route_verify_response


RUN_ID = "20260505T143015Z_chatgpt_signal_ontology"
UPDATED_AT = "2026-05-05T17:45:00Z"


def _drawer(drawer_id: str, content: str) -> dict[str, str]:
    return {
        "drawer_id": drawer_id,
        "wing": "chatgpt_signals",
        "room": "general",
        "content": content,
    }


def _pass1_response(*, confidence: float, rationale: str) -> str:
    return json.dumps(
        {
            "wing": "life_admin",
            "room": "appointments_and_forms",
            "label": "Appointments and forms",
            "confidence": confidence,
            "rationale": rationale,
        }
    )


def _build_chain() -> dict[str, object]:
    drawer_a = _drawer(
        "drawer_chatgpt_signals_general_a001",
        "Please reschedule the appointment and update the intake form before next Tuesday.",
    )
    drawer_b = _drawer(
        "drawer_chatgpt_signals_general_b001",
        "Please confirm the paperwork deadline and reschedule the appointment before next Tuesday.",
    )

    pass1_parsed = parse_pass1_response(
        _pass1_response(
            confidence=0.91,
            rationale="The drawer centers on scheduling and forms.",
        )
    )
    assert pass1_parsed.record_status == "ok"
    assert pass1_parsed.payload["proposed_wing"] == "life_admin"
    assert pass1_parsed.payload["proposed_room"] == "appointments_and_forms"

    pass1_a = build_pass1_phase_record(
        run_id=RUN_ID,
        sequence=1,
        attempt=1,
        source_drawer=drawer_a,
        provider_response=_pass1_response(
            confidence=0.91,
            rationale="The drawer centers on scheduling and forms.",
        ),
        recorded_at="2026-05-05T14:40:56Z",
    )
    pass1_b = build_pass1_phase_record(
        run_id=RUN_ID,
        sequence=2,
        attempt=1,
        source_drawer=drawer_b,
        provider_response=_pass1_response(
            confidence=0.84,
            rationale="The drawer still centers on scheduling and forms.",
        ),
        recorded_at="2026-05-05T14:40:57Z",
    )

    cluster_result = cluster_pass1_phase_records(
        [pass1_a, pass1_b],
        run_id=RUN_ID,
        recorded_at="2026-05-05T16:00:00Z",
    )
    assert cluster_result.skipped_summary["skipped_records"] == 0
    assert len(cluster_result.records) == 1

    cluster_record = cluster_result.records[0]
    candidate_id = cluster_record["subject_id"]
    canonical_result = build_canonical_candidate_records(
        cluster_result.records,
        {
            candidate_id: json.dumps(
                {
                    "action": "keep",
                    "canonical_wing": "life_admin",
                    "canonical_room": "appointments_and_forms",
                    "label": "Appointments and forms",
                    "definition": "Scheduling, intake forms, and appointment paperwork.",
                }
            )
        },
        run_id=RUN_ID,
        recorded_at="2026-05-05T16:05:00Z",
    )
    assert canonical_result.skipped_summary["skipped_records"] == 0
    assert len(canonical_result.records) == 1

    canonical_record = canonical_result.records[0]
    candidate_index = build_candidate_index(
        canonical_result.records,
        run_id=RUN_ID,
    )
    assert candidate_index.skipped_summary["skipped_records"] == 0
    assert len(candidate_index.candidates) == 1
    index_candidate = candidate_index.candidates[0]
    assert index_candidate.candidate_id == canonical_record["payload"]["candidate_id"]
    assert index_candidate.candidate_key == "life_admin:appointments_and_forms"
    assert index_candidate.support_drawer_count == 2

    route_candidates_result = build_route_candidate_records(
        [drawer_a, drawer_b],
        canonical_result.records,
        run_id=RUN_ID,
        recorded_at="2026-05-05T16:10:00Z",
    )
    assert route_candidates_result.skipped_summary["skipped_drawers"] == 0
    assert len(route_candidates_result.records) == 2
    assert all(record["payload"]["retrieval_status"] == "ok" for record in route_candidates_result.records)
    assert all(record["payload"]["candidate_count"] == 1 for record in route_candidates_result.records)
    assert all(
        record["payload"]["route_candidates"][0]["candidate_key"] == "life_admin:appointments_and_forms"
        for record in route_candidates_result.records
    )

    selected_route = route_candidates_result.records[0]
    null_route = route_candidates_result.records[1]
    route_pass2_selected = parse_route_pass2_response(
        drawer_a,
        selected_route,
        json.dumps(
            {
                "route": "candidate",
                "selected_candidate_id": candidate_id,
                "selected_candidate_key": "life_admin:appointments_and_forms",
                "canonical_wing": "life_admin",
                "canonical_room": "appointments_and_forms",
                "route_confidence": 0.91,
                "rationale_summary": "The drawer is about scheduling and forms.",
            }
        ),
        recorded_at="2026-05-05T16:15:00Z",
    )
    route_pass2_null = parse_route_pass2_response(
        drawer_b,
        null_route,
        json.dumps(
            {
                "route": "null",
                "selected_candidate_id": None,
                "selected_candidate_key": None,
                "canonical_wing": None,
                "canonical_room": None,
                "route_confidence": 0.19,
                "reason_code": "no_clear_match",
                "reason_detail": "The shortlist does not fit well enough.",
                "next_action": "manual_review",
                "rationale_summary": "The drawer mixes multiple intents.",
            }
        ),
        recorded_at="2026-05-05T16:16:00Z",
    )
    assert route_pass2_selected["payload"]["route_status"] == "selected"
    assert route_pass2_selected["payload"]["selected_candidate_id"] == candidate_id
    assert route_pass2_null["payload"]["route_status"] == "null_route"
    assert route_pass2_null["payload"]["reason_code"] == "no_clear_match"
    assert route_pass2_null["payload"]["next_action"] == "manual_review"

    route_verify_selected = parse_route_verify_response(
        drawer_a,
        selected_route,
        route_pass2_selected,
        json.dumps(
            {
                "verdict": "approve",
                "selected_candidate_id": candidate_id,
                "selected_candidate_key": "life_admin:appointments_and_forms",
                "canonical_wing": "life_admin",
                "canonical_room": "appointments_and_forms",
                "verification_confidence": 0.96,
                "rationale_summary": "Verified against the drawer text.",
            }
        ),
        recorded_at="2026-05-05T16:20:00Z",
    )
    route_verify_null = parse_route_verify_response(
        drawer_b,
        null_route,
        route_pass2_null,
        json.dumps(
            {
                "verdict": "approve",
                "selected_candidate_id": None,
                "selected_candidate_key": None,
                "canonical_wing": None,
                "canonical_room": None,
                "verification_confidence": 0.71,
                "reason_code": "no_clear_match",
                "reason_detail": "The drawer still mixes multiple intents.",
                "next_action": "manual_review",
                "rationale_summary": "Null route remains appropriate.",
            }
        ),
        recorded_at="2026-05-05T16:21:00Z",
    )
    assert route_verify_selected["payload"]["copy_ready"] is True
    assert route_verify_null["payload"]["copy_ready"] is False
    assert route_verify_null["payload"]["route_status"] == "null_route"

    decision_result = build_iteration_decision_records(
        [route_verify_selected, route_verify_null],
        run_id=RUN_ID,
    )
    assert len(decision_result.accepted_routes) == 1
    assert len(decision_result.unresolved_routes) == 1

    accepted_route = decision_result.accepted_routes[0]
    unresolved_route = decision_result.unresolved_routes[0]
    assert accepted_route["schema_name"] == "ontology.accepted_route"
    assert accepted_route["route_status"] == "accepted"
    assert accepted_route["copy_ready"] is True
    assert accepted_route["candidate_id"] == candidate_id
    assert accepted_route["candidate_key"] == "life_admin:appointments_and_forms"
    assert accepted_route["route_record_ref"] == "route_pass2.jsonl#1"
    assert accepted_route["verification_record_ref"] == "route_verify.jsonl#1"
    assert unresolved_route["schema_name"] == "ontology.unresolved_route"
    assert unresolved_route["unresolved_status"] == "null_route"
    assert unresolved_route["reason_code"] == "no_clear_match"
    assert unresolved_route["next_action"] == "manual_review"
    assert unresolved_route["retryable"] is False

    report = build_convergence_report(
        [route_verify_selected, route_verify_null],
        accepted_routes=decision_result.accepted_routes,
        unresolved_routes=decision_result.unresolved_routes,
        run_id=RUN_ID,
    )
    assert report["schema_name"] == "ontology.convergence_report"
    assert report["run_id"] == RUN_ID
    assert report["terminal_status"] == "needs_review"
    assert report["accepted_count"] == 1
    assert report["unresolved_count"] == 1
    assert report["error_count"] == 0
    assert report["reason_counts"] == {"no_clear_match": 1}
    assert report["terminal_status_counts"] == {"accepted": 1, "null_route": 1}
    assert [item["source_drawer_id"] for item in report["latest_terminal_drawer_states"]] == [
        "drawer_chatgpt_signals_general_a001",
        "drawer_chatgpt_signals_general_b001",
    ]

    manifest = build_apply_ready_manifest(
        decision_result.accepted_routes,
        unresolved_routes=decision_result.unresolved_routes,
        run_id=RUN_ID,
    )
    assert manifest["schema_name"] == "ontology.apply_ready_manifest"
    assert manifest["run_id"] == RUN_ID
    assert manifest["route_count"] == 1
    assert manifest["routes"] == [
        {
            "source_drawer_id": "drawer_chatgpt_signals_general_a001",
            "source_wing": "chatgpt_signals",
            "source_room": "general",
            "route_iteration": 1,
            "candidate_id": candidate_id,
            "candidate_key": "life_admin:appointments_and_forms",
            "canonical_wing": "life_admin",
            "canonical_room": "appointments_and_forms",
            "route_confidence": 0.91,
            "verification_confidence": 0.96,
            "route_record_ref": "route_pass2.jsonl#1",
            "verification_record_ref": "route_verify.jsonl#1",
            "accepted_route_record_ref": "accepted_routes.jsonl#1",
            "route_candidate_record_ref": "route_candidates.jsonl#1",
            "rationale_summary": "Verified against the drawer text.",
        }
    ]

    copy_id = _ontology_copy_drawer_id(
        drawer_a["drawer_id"],
        accepted_route["canonical_wing"],
        accepted_route["canonical_room"],
    )
    expected_copy_id = "drawer_life_admin_appointments_and_forms_" + hashlib.sha256(
        (
            "ontology-copy:v1\0"
            + drawer_a["drawer_id"]
            + "\0"
            + accepted_route["canonical_wing"]
            + "\0"
            + accepted_route["canonical_room"]
        ).encode("utf-8")
    ).hexdigest()[:24]
    assert copy_id == expected_copy_id
    assert copy_id == _ontology_copy_drawer_id(
        drawer_a["drawer_id"],
        accepted_route["canonical_wing"],
        accepted_route["canonical_room"],
    )
    assert copy_id != _ontology_copy_drawer_id(
        drawer_a["drawer_id"],
        accepted_route["canonical_wing"],
        "requests",
    )

    progress = {
        "schema_name": "ontology.progress",
        "schema_version": 1,
        "run_id": RUN_ID,
        "run_kind": "chatgpt_signal_ontology",
        "source_wing": "chatgpt_signals",
        "status": "running",
        "current_phase": "route_verify",
        "current_phase_status": "running",
        "phase_order": [
            "pass1_open",
            "candidate_clusters",
            "canonical_candidates",
            "route_candidates",
            "route_pass2",
            "route_verify",
            "apply_copies",
        ],
        "phase_attempts": {
            "pass1_open": 1,
            "candidate_clusters": 1,
            "canonical_candidates": 1,
            "route_candidates": 1,
            "route_pass2": 1,
            "route_verify": 1,
            "apply_copies": 0,
        },
        "started_at": "2026-05-05T14:30:15Z",
        "updated_at": UPDATED_AT,
        "ended_at": None,
        "elapsed_seconds": 660,
        "current_phase_progress": {
            "unit": "route",
            "total": 2,
            "processed": 2,
            "accepted": 1,
            "unresolved": 1,
            "errors": 0,
        },
        "totals": {
            "source_drawers_total": 2,
            "source_drawers_processed": 2,
            "routes_accepted": 1,
            "routes_unresolved": 1,
            "copies_materialized": 1,
            "phase_records_written": 10,
        },
        "last_record": {
            "phase": "route_verify",
            "relative_path": "route_verify.jsonl",
            "sequence": 2,
            "subject_id": drawer_b["drawer_id"],
            "recorded_at": "2026-05-05T16:21:00Z",
        },
        "warning_count": 0,
        "error_count": 0,
    }
    progress_bytes = _json_bytes(progress)
    accepted_routes_bytes = _json_bytes(
        {
            "schema_name": "ontology.accepted_route",
            "schema_version": 1,
            "run_id": RUN_ID,
            "sequence": 1,
            "recorded_at": "2026-05-05T16:20:00Z",
            "route_status": "accepted",
            "route_iteration": 1,
            "source_drawer_id": "drawer_chatgpt_signals_general_a001",
            "source_wing": "chatgpt_signals",
            "source_room": "general",
            "candidate_id": "cand_life_admin__appointments_and_forms",
            "canonical_wing": "life_admin",
            "canonical_room": "appointments_and_forms",
            "route_confidence": 0.91,
            "verification_confidence": 0.96,
            "copy_ready": True,
            "route_record_ref": "route_pass2.jsonl#1",
            "verification_record_ref": "route_verify.jsonl#1",
            "rationale_summary": "Verified against the drawer text.",
        }
    )
    unresolved_routes_bytes = _json_bytes(
        {
            "schema_name": "ontology.unresolved_route",
            "schema_version": 1,
            "run_id": RUN_ID,
            "sequence": 1,
            "recorded_at": "2026-05-05T16:21:00Z",
            "route_iteration": 1,
            "source_drawer_id": "drawer_chatgpt_signals_general_b001",
            "source_wing": "chatgpt_signals",
            "source_room": "general",
            "unresolved_status": "null_route",
            "candidate_ids": ["cand_life_admin__appointments_and_forms"],
            "candidate_keys": ["life_admin:appointments_and_forms"],
            "reason_code": "no_clear_match",
            "reason_detail": "The drawer still mixes multiple intents.",
            "route_confidence": 0.19,
            "verification_confidence": 0.71,
            "next_action": "manual_review",
            "retryable": False,
            "source_excerpt": "Please confirm the paperwork deadline and reschedule the appointment before next Tuesday.",
        }
    )
    artifacts_index = {
        "schema_name": "ontology.artifact_index",
        "schema_version": 1,
        "run_id": RUN_ID,
        "updated_at": UPDATED_AT,
        "artifacts": [
            {
                "artifact_key": "progress",
                "relative_path": "progress.json",
                "schema_name": "ontology.progress",
                "schema_version": 1,
                "artifact_kind": "summary",
                "phase": None,
                "content_type": "application/json",
                "append_only": False,
                "records": 1,
                "bytes": progress_bytes,
                "status": "active",
                "dashboard_safe": True,
                "privacy_level": "summary",
                "updated_at": UPDATED_AT,
            },
            {
                "artifact_key": "accepted_routes",
                "relative_path": "accepted_routes.jsonl",
                "schema_name": "ontology.accepted_route",
                "schema_version": 1,
                "artifact_kind": "decision_records",
                "phase": None,
                "content_type": "application/jsonl",
                "append_only": True,
                "records": len(decision_result.accepted_routes),
                "bytes": accepted_routes_bytes,
                "status": "active",
                "dashboard_safe": True,
                "privacy_level": "summary",
                "updated_at": UPDATED_AT,
            },
            {
                "artifact_key": "unresolved_routes",
                "relative_path": "unresolved.jsonl",
                "schema_name": "ontology.unresolved_route",
                "schema_version": 1,
                "artifact_kind": "decision_records",
                "phase": None,
                "content_type": "application/jsonl",
                "append_only": True,
                "records": len(decision_result.unresolved_routes),
                "bytes": unresolved_routes_bytes,
                "status": "active",
                "dashboard_safe": True,
                "privacy_level": "bounded_excerpt",
                "updated_at": UPDATED_AT,
            },
        ],
    }

    assert "Please reschedule the appointment" not in json.dumps(progress)
    assert "Please reschedule the appointment" not in json.dumps(artifacts_index)

    return {
        "drawer_a": drawer_a,
        "drawer_b": drawer_b,
        "pass1_records": [pass1_a, pass1_b],
        "cluster_result": cluster_result,
        "canonical_result": canonical_result,
        "candidate_index": candidate_index,
        "route_candidates_result": route_candidates_result,
        "route_pass2_records": [route_pass2_selected, route_pass2_null],
        "verification_records": [route_verify_selected, route_verify_null],
        "decision_result": decision_result,
        "report": report,
        "manifest": manifest,
        "progress": progress,
        "artifacts_index": artifacts_index,
    }


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    lines = [json.dumps(row, separators=(",", ":")) for row in rows]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _json_bytes(payload: dict[str, object]) -> int:
    return len(json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")) + 1


def test_ontology_contract_chain_covers_checkpoints_b_through_i() -> None:
    chain = _build_chain()

    pass1_record = chain["pass1_records"][0]
    cluster_record = chain["cluster_result"].records[0]
    canonical_record = chain["canonical_result"].records[0]
    route_record = chain["route_candidates_result"].records[0]
    route_pass2_record = chain["route_pass2_records"][0]
    route_verify_record = chain["verification_records"][0]

    assert pass1_record["schema_name"] == "ontology.phase_record"
    assert pass1_record["phase"] == "pass1_open"
    assert pass1_record["subject_type"] == "drawer"
    assert pass1_record["source"] == {
        "wing": "chatgpt_signals",
        "room": "general",
        "drawer_id": "drawer_chatgpt_signals_general_a001",
    }
    assert pass1_record["payload"]["proposed_wing"] == "life_admin"
    assert pass1_record["payload"]["proposed_room"] == "appointments_and_forms"

    assert cluster_record["schema_name"] == "ontology.phase_record"
    assert cluster_record["phase"] == "candidate_clusters"
    assert cluster_record["payload"]["candidate_id"] == build_candidate_id(
        "life_admin",
        "appointments_and_forms",
    )
    assert cluster_record["payload"]["candidate_key"] == "life_admin:appointments_and_forms"
    assert cluster_record["payload"]["cluster_stats"]["source_drawer_count"] == 2
    assert len(cluster_record["payload"]["source_drawer_refs"]) == 2

    assert canonical_record["phase"] == "canonical_candidates"
    assert canonical_record["payload"]["action"] == "keep"
    assert canonical_record["payload"]["candidate_id"] == cluster_record["payload"]["candidate_id"]
    assert canonical_record["payload"]["source_candidate_id"] == cluster_record["payload"]["candidate_id"]
    assert canonical_record["payload"]["source_drawer_refs"][0]["drawer_id"] == "drawer_chatgpt_signals_general_a001"

    assert chain["candidate_index"].candidates[0].candidate_key == "life_admin:appointments_and_forms"
    assert route_record["phase"] == "route_candidates"
    assert route_record["payload"]["route_candidates"][0]["candidate_id"] == cluster_record["payload"]["candidate_id"]
    assert route_pass2_record["phase"] == "route_pass2"
    assert route_pass2_record["payload"]["route_status"] == "selected"
    assert route_verify_record["phase"] == "route_verify"
    assert route_verify_record["payload"]["route_status"] == "accepted"
    assert route_verify_record["payload"]["copy_ready"] is True

    assert chain["decision_result"].skipped_summary["skipped_records"] == 0
    assert chain["manifest"]["route_count"] == 1
    assert chain["report"]["total_verification_records"] == 2
    assert chain["report"]["latest_terminal_drawer_states"][0]["terminal_status"] == "accepted"
    assert chain["report"]["latest_terminal_drawer_states"][1]["terminal_status"] == "null_route"


def test_ontology_dashboard_reads_fixture_files_without_mutating_them(tmp_path: Path) -> None:
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient
    from mempalace.dashboard_server import MiningStatus, create_app

    chain = _build_chain()
    run_root = tmp_path / RUN_ID
    run_root.mkdir(parents=True, exist_ok=True)

    _write_json(run_root / "progress.json", chain["progress"])
    _write_json(run_root / "artifacts_index.json", chain["artifacts_index"])
    _write_jsonl(run_root / "accepted_routes.jsonl", chain["decision_result"].accepted_routes)
    _write_jsonl(run_root / "unresolved.jsonl", chain["decision_result"].unresolved_routes)

    mtimes_before = {
        path: path.stat().st_mtime_ns
        for path in (
            run_root / "progress.json",
            run_root / "artifacts_index.json",
            run_root / "accepted_routes.jsonl",
            run_root / "unresolved.jsonl",
        )
    }

    class _Upstream:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict[str, object]]] = []

        def healthz(self) -> dict[str, object]:
            return {
                "status": "ok",
                "drawer_count": 0,
                "effective_embedding_device": "cpu",
                "localai_status": "offline",
                "checkpoint_status": "saved",
                "localai": {"status": "offline"},
                "checkpoint": {"status": "saved"},
            }

        def call_tool(self, name, arguments=None):
            self.calls.append((name, dict(arguments or {})))
            raise AssertionError(f"unexpected upstream call: {name}")

    class _MiningDetector:
        def detect(self) -> MiningStatus:
            return MiningStatus(
                active=False,
                active_services=[],
                matched_processes=[],
                configured_services=[],
                configured_process_patterns=[],
                detection_errors=[],
            )

    upstream = _Upstream()
    client = TestClient(
        create_app(
            token="secret",
            upstream_client=upstream,
            mining_detector=_MiningDetector(),
            ontology_run_root=tmp_path,
        )
    )
    headers = {"Authorization": "Bearer secret"}

    runs_response = client.get("/api/ontology/runs", headers=headers)
    assert runs_response.status_code == 200
    runs_body = runs_response.json()
    assert runs_body["count"] == 1
    assert runs_body["runs"][0]["run_id"] == RUN_ID
    assert runs_body["runs"][0]["status"] == "running"

    detail_response = client.get(f"/api/ontology/runs/{RUN_ID}", headers=headers)
    assert detail_response.status_code == 200
    detail_body = detail_response.json()
    assert detail_body["progress"]["schema_name"] == "ontology.progress"
    assert detail_body["progress"]["current_phase_progress"]["processed"] == 2
    assert detail_body["artifact_count"] == 3

    artifacts_response = client.get(f"/api/ontology/runs/{RUN_ID}/artifacts", headers=headers)
    assert artifacts_response.status_code == 200
    artifacts_body = artifacts_response.json()
    assert [item["artifact_key"] for item in artifacts_body["artifacts"]] == [
        "progress",
        "accepted_routes",
        "unresolved_routes",
    ]
    assert all(isinstance(item["records"], int) for item in artifacts_body["artifacts"])
    assert all(isinstance(item["bytes"], int) and item["bytes"] > 0 for item in artifacts_body["artifacts"])
    assert artifacts_body["artifacts"][2]["privacy_level"] == "bounded_excerpt"
    assert artifacts_body["artifacts"][2]["dashboard_safe"] is True

    preview_response = client.get(
        f"/api/ontology/runs/{RUN_ID}/unresolved-preview?limit=1&excerpt_chars=40",
        headers=headers,
    )
    assert preview_response.status_code == 200
    preview_body = preview_response.json()
    assert preview_body["status"] == "ok"
    assert preview_body["count"] == 1
    assert preview_body["truncated"] is True
    assert preview_body["preview"][0]["source_drawer_id"] == "drawer_chatgpt_signals_general_b001"
    assert len(preview_body["preview"][0]["source_excerpt"]) <= 40

    assert upstream.calls == []
    assert {
        path: path.stat().st_mtime_ns
        for path in mtimes_before
    } == mtimes_before
