from __future__ import annotations

import argparse

from mempalace.mcp_server import _ontology_copy_drawer_id, tool_copy_drawer
from mempalace.ontology_iteration import (
    build_apply_ready_manifest,
    build_iteration_decision_records,
)
from mempalace.cli import cmd_ontology_chatgpt_signals


RUN_ID = "20260505T143015Z_chatgpt_signal_ontology"


def _patch_mcp_server(monkeypatch, config, kg):
    from mempalace import mcp_server

    monkeypatch.setattr(mcp_server, "_config", config)
    monkeypatch.setattr(mcp_server, "_kg", kg)


def _verification_record(
    *,
    sequence: int,
    drawer_id: str,
    source_wing: str = "chatgpt_signals",
    source_room: str = "general",
):
    return {
        "schema_name": "ontology.phase_record",
        "schema_version": 1,
        "run_id": RUN_ID,
        "phase": "route_verify",
        "sequence": sequence,
        "attempt": 1,
        "recorded_at": f"2026-05-05T17:{sequence:02d}:00Z",
        "subject_type": "drawer",
        "subject_id": drawer_id,
        "record_status": "ok",
        "source": {
            "wing": source_wing,
            "room": source_room,
            "drawer_id": drawer_id,
        },
        "payload": {
            "route_iteration": 1,
            "route_status": "accepted",
            "route_record_ref": f"route_pass2.jsonl#{sequence}",
            "route_candidate_record_ref": f"route_candidates.jsonl#{sequence}",
            "route_confidence": 0.92,
            "verification_confidence": 0.97,
            "rationale_summary": "Verified against the drawer text.",
            "route_rationale_summary": "The drawer is about scheduling and forms.",
            "drawer_excerpt": "Please reschedule the appointment and update the intake form.",
            "shortlist_candidate_ids": ["cand_life_admin__appointments_and_forms"],
            "shortlist_candidate_keys": ["life_admin:appointments_and_forms"],
            "copy_ready": True,
            "selected_candidate_id": "cand_life_admin__appointments_and_forms",
            "candidate_id": "cand_life_admin__appointments_and_forms",
            "selected_candidate_key": "life_admin:appointments_and_forms",
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
        },
    }


def _build_apply_route(drawer_id: str):
    built = build_iteration_decision_records(
        [_verification_record(sequence=1, drawer_id=drawer_id)]
    )
    manifest = build_apply_ready_manifest(built.accepted_routes, run_id=RUN_ID)
    route = manifest["routes"][0]
    return built.accepted_routes[0], manifest, route


def test_ontology_chatgpt_signals_dry_run_creates_no_run_directory_or_palace_writes(
    tmp_path, capsys
):
    run_root = tmp_path / "ontology_runs"
    args = argparse.Namespace(
        run_dir=str(run_root),
        run_id="dry_run_1",
        source_wing="chatgpt_signals",
        dry_run=True,
    )

    cmd_ontology_chatgpt_signals(args)

    out = capsys.readouterr().out
    assert "Dry run only" in out
    assert not run_root.exists()
    assert list(tmp_path.iterdir()) == []


def test_apply_ready_manifest_routes_into_copy_drawer_and_preserves_source(
    monkeypatch, config, collection, kg
):
    _patch_mcp_server(monkeypatch, config, kg)

    source_drawer_id = "drawer_chatgpt_signals_general_apply_001"
    source_content = (
        "Please reschedule the appointment and update the intake form.\n"
        "I also need the insurance card on file."
    )
    source_metadata = {
        "wing": "chatgpt_signals",
        "room": "general",
        "source_file": "/private/home/alice/chatgpt_exports/conversations.json",
        "chunk_index": 7,
        "added_by": "localai_chatgpt_signals",
        "conversation_id": "chatgpt:conv-001",
        "filed_at": "2026-05-05T14:30:15Z",
    }
    collection.add(
        ids=[source_drawer_id],
        documents=[source_content],
        metadatas=[source_metadata],
    )

    source_before = collection.get(ids=[source_drawer_id], include=["documents", "metadatas"])
    accepted_route, manifest, route = _build_apply_route(source_drawer_id)

    assert manifest["schema_name"] == "ontology.apply_ready_manifest"
    assert manifest["route_count"] == 1
    assert route["source_drawer_id"] == source_drawer_id
    assert route["accepted_route_record_ref"] == "accepted_routes.jsonl#1"
    assert accepted_route["source_drawer_id"] == source_drawer_id

    result = tool_copy_drawer(
        source_drawer_id=route["source_drawer_id"],
        canonical_wing=route["canonical_wing"],
        canonical_room=route["canonical_room"],
        ontology_run_id=manifest["run_id"],
        ontology_route_iteration=route["route_iteration"],
        ontology_candidate_id=route["candidate_id"],
        ontology_route_record_ref=route["accepted_route_record_ref"],
    )

    expected_copy_id = _ontology_copy_drawer_id(
        source_drawer_id, route["canonical_wing"], route["canonical_room"]
    )
    copied = collection.get(ids=[expected_copy_id], include=["documents", "metadatas"])
    source_after = collection.get(ids=[source_drawer_id], include=["documents", "metadatas"])

    assert result["success"] is True
    assert result["drawer_id"] == expected_copy_id
    assert collection.count() == 2
    assert copied["documents"][0] == source_content
    assert copied["metadatas"][0]["wing"] == "life_admin"
    assert copied["metadatas"][0]["room"] == "appointments_and_forms"
    assert copied["metadatas"][0]["ontology_source_drawer_id"] == source_drawer_id
    assert copied["metadatas"][0]["ontology_route_record_ref"] == "accepted_routes.jsonl#1"
    assert copied["metadatas"][0]["ontology_candidate_id"] == "cand_life_admin__appointments_and_forms"
    assert source_after == source_before


def test_apply_ready_manifest_repeat_apply_is_idempotent(
    monkeypatch, config, collection, kg
):
    _patch_mcp_server(monkeypatch, config, kg)

    source_drawer_id = "drawer_chatgpt_signals_general_repeat_001"
    collection.add(
        ids=[source_drawer_id],
        documents=["Repeatable ontology source drawer body."],
        metadatas=[
            {
                "wing": "chatgpt_signals",
                "room": "general",
                "chunk_index": 0,
            }
        ],
    )

    _, manifest, route = _build_apply_route(source_drawer_id)

    result1 = tool_copy_drawer(
        source_drawer_id=source_drawer_id,
        canonical_wing=route["canonical_wing"],
        canonical_room=route["canonical_room"],
        ontology_run_id=manifest["run_id"],
        ontology_route_iteration=route["route_iteration"],
        ontology_candidate_id=route["candidate_id"],
        ontology_route_record_ref=route["accepted_route_record_ref"],
    )
    result2 = tool_copy_drawer(
        source_drawer_id=source_drawer_id,
        canonical_wing=route["canonical_wing"],
        canonical_room=route["canonical_room"],
        ontology_run_id="20260505T150000Z_chatgpt_signal_ontology",
        ontology_route_iteration=2,
        ontology_candidate_id=route["candidate_id"],
        ontology_route_record_ref="accepted_routes.jsonl#2",
    )

    expected_copy_id = _ontology_copy_drawer_id(
        source_drawer_id, route["canonical_wing"], route["canonical_room"]
    )

    assert result1["success"] is True
    assert result2["success"] is True
    assert result2["drawer_id"] == expected_copy_id
    assert result2["reason"] == "already_exists"
    assert result2["noop"] is True
    assert collection.count() == 2
