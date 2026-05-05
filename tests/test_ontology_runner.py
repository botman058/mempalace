from __future__ import annotations

import json
import pytest
from types import SimpleNamespace

from mempalace.ontology_run import initialize_run_shell, materialize_run_shell
from mempalace.ontology_runner import (
    RunnerConfig,
    build_runner_config,
    ensure_localai_base_url,
    run_chatgpt_signal_ontology,
)


class _FakeProvider:
    def classify(self, _system: str, user: str, json_mode: bool = True):
        assert json_mode is True
        if "SOURCE DRAWER" in user and '"wing": "lowercase_slug"' in user:
            return '{"wing":"life_admin","room":"appointments","label":"Appointments","confidence":0.9,"rationale":"fit"}'
        if "AVAILABLE ACTIONS" in user:
            return '{"action":"keep","canonical_wing":"life_admin","canonical_room":"appointments","label":"Appointments","definition":"Scheduling and intake form coordination."}'
        if "You route one source drawer" in user:
            return '{"route":"null","selected_candidate_id":null,"selected_candidate_key":null,"canonical_wing":null,"canonical_room":null,"route_confidence":0.45,"rationale_summary":"No confident match.","reason_code":"ambiguous","reason_detail":"Insufficient evidence.","next_action":"manual_review"}'
        if "You locally verify one proposed ontology route decision" in user:
            return '{"verdict":"approve","selected_candidate_id":null,"selected_candidate_key":null,"canonical_wing":null,"canonical_room":null,"verification_confidence":0.88,"rationale_summary":"Null route is appropriate.","reason_code":"ambiguous","reason_detail":"Needs manual review.","next_action":"manual_review"}'
        raise AssertionError(f"Unexpected prompt: {user[:120]}")


class _FakeProviderAccepted:
    def classify(self, _system: str, user: str, json_mode: bool = True):
        assert json_mode is True
        if "SOURCE DRAWER" in user and '"wing": "lowercase_slug"' in user:
            return '{"wing":"life_admin","room":"appointments","label":"Appointments","confidence":0.9,"rationale":"fit"}'
        if "AVAILABLE ACTIONS" in user:
            return '{"action":"keep","canonical_wing":"life_admin","canonical_room":"appointments","label":"Appointments","definition":"Scheduling and intake form coordination."}'
        if "You route one source drawer" in user:
            return '{"route":"candidate","selected_candidate_id":"cand_life_admin__appointments","selected_candidate_key":"life_admin:appointments","canonical_wing":"life_admin","canonical_room":"appointments","route_confidence":0.91,"rationale_summary":"Direct match.","reason_code":null,"reason_detail":null,"next_action":null}'
        if "You locally verify one proposed ontology route decision" in user:
            return '{"verdict":"approve","selected_candidate_id":"cand_life_admin__appointments","selected_candidate_key":"life_admin:appointments","canonical_wing":"life_admin","canonical_room":"appointments","verification_confidence":0.95,"rationale_summary":"Approved.","reason_code":null,"reason_detail":null,"next_action":null}'
        raise AssertionError(f"Unexpected prompt: {user[:120]}")


class _FakeProviderTwoClusters:
    def classify(self, _system: str, user: str, json_mode: bool = True):
        assert json_mode is True
        if "SOURCE DRAWER" in user and '"wing": "lowercase_slug"' in user:
            if "billing" in user:
                return '{"wing":"finance_admin","room":"billing","label":"Billing","confidence":0.9,"rationale":"fit"}'
            return '{"wing":"life_admin","room":"appointments","label":"Appointments","confidence":0.9,"rationale":"fit"}'
        if "AVAILABLE ACTIONS" in user:
            if '"canonical_wing": "finance_admin"' in user:
                return '{"action":"keep","canonical_wing":"finance_admin","canonical_room":"billing","label":"Billing","definition":"Billing and payment records."}'
            return '{"action":"keep","canonical_wing":"life_admin","canonical_room":"appointments","label":"Appointments","definition":"Scheduling and intake form coordination."}'
        if "You route one source drawer" in user:
            return '{"route":"null","selected_candidate_id":null,"selected_candidate_key":null,"canonical_wing":null,"canonical_room":null,"route_confidence":0.45,"rationale_summary":"No confident match.","reason_code":"ambiguous","reason_detail":"Insufficient evidence.","next_action":"manual_review"}'
        if "You locally verify one proposed ontology route decision" in user:
            return '{"verdict":"approve","selected_candidate_id":null,"selected_candidate_key":null,"canonical_wing":null,"canonical_room":null,"verification_confidence":0.88,"rationale_summary":"Null route is appropriate.","reason_code":"ambiguous","reason_detail":"Needs manual review.","next_action":"manual_review"}'
        raise AssertionError(f"Unexpected prompt: {user[:120]}")


def test_runner_is_resumable_and_does_not_apply_copies_by_default(tmp_path, monkeypatch):
    run = initialize_run_shell(
        run_dir=str(tmp_path / "runs"),
        run_id="runner_resume_1",
        source_wing="chatgpt_signals",
        dry_run=False,
    )
    materialize_run_shell(run)

    drawers = [
        {"drawer_id": "drawer_1", "content": "reschedule appointment", "wing": "chatgpt_signals", "room": "general", "metadata": {}},
        {"drawer_id": "drawer_2", "content": "update intake form", "wing": "chatgpt_signals", "room": "general", "metadata": {}},
    ]
    copy_calls = []

    def fake_call_tool(name, arguments=None, url=None, token=None, timeout=60.0):
        if name == "mempalace_export_drawers":
            offset = int((arguments or {}).get("offset", 0))
            limit = int((arguments or {}).get("limit", 100))
            page = drawers[offset : offset + limit]
            return {"drawers": page, "count": len(page), "offset": offset, "limit": limit}
        if name == "mempalace_copy_drawer":
            copy_calls.append((arguments, url, token))
            return {"success": True, "noop": True}
        raise AssertionError(name)

    monkeypatch.setattr("mempalace.ontology_runner.call_tool", fake_call_tool)
    monkeypatch.setattr("mempalace.ontology_runner._Provider", lambda **_: _FakeProvider())

    cfg = RunnerConfig(
        localai_base_url="http://snow-white-iii:8080/v1",
        localai_model="qwen3-vl-8b-instruct",
        localai_token="token",
        mcp_url="http://100.112.179.49:8765",
        mcp_token="token",
        source_wing="chatgpt_signals",
        apply_copies=False,
    )
    run_chatgpt_signal_ontology(run, cfg)
    run_chatgpt_signal_ontology(run, cfg)

    pass1_lines = [
        line for line in (run.run_dir / "pass1_open.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    assert len(pass1_lines) == 2

    manifest = json.loads((run.run_dir / "apply_ready_manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema_name"] == "ontology.apply_ready_manifest"
    assert copy_calls == []
    progress = json.loads((run.run_dir / "progress.json").read_text(encoding="utf-8"))
    assert progress["status"] == "completed"
    assert progress["current_phase_status"] == "completed"
    assert progress["ended_at"] is not None
    assert progress["totals"]["source_drawers_processed"] > 0
    assert progress["totals"]["source_drawers_total"] > 0
    assert progress["totals"]["source_drawers_processed"] <= progress["totals"]["source_drawers_total"]
    assert progress["totals"]["source_drawers_processed"] == 2
    assert progress["current_phase_progress"]["total"] >= 0
    assert progress["last_record"] is not None
    assert progress["last_record"]["relative_path"].endswith(".jsonl")
    assert isinstance(progress["last_record"]["subject_id"], str)


def test_runner_export_error_fails_closed_and_marks_progress_failed(tmp_path, monkeypatch):
    run = initialize_run_shell(
        run_dir=str(tmp_path / "runs"),
        run_id="runner_fail_1",
        source_wing="chatgpt_signals",
        dry_run=False,
    )
    materialize_run_shell(run)

    def fake_call_tool(name, arguments=None, url=None, token=None, timeout=60.0):
        assert name == "mempalace_export_drawers"
        return {"error": "No palace found"}

    monkeypatch.setattr("mempalace.ontology_runner.call_tool", fake_call_tool)
    monkeypatch.setattr("mempalace.ontology_runner._Provider", lambda **_: _FakeProvider())

    cfg = RunnerConfig(
        localai_base_url="http://snow-white-iii:8080/v1",
        localai_model="qwen3-vl-8b-instruct",
        localai_token="token",
        mcp_url="http://100.112.179.49:8765",
        mcp_token="token",
        source_wing="chatgpt_signals",
        apply_copies=False,
    )
    with pytest.raises(Exception, match="No palace found"):
        run_chatgpt_signal_ontology(run, cfg)

    progress = json.loads((run.run_dir / "progress.json").read_text(encoding="utf-8"))
    assert progress["status"] == "failed"
    assert progress["current_phase_status"] == "failed"
    assert progress["ended_at"] is not None
    assert progress["error_count"] >= 1


def test_runner_apply_copies_uses_manifest_routes_and_updates_totals(tmp_path, monkeypatch):
    run = initialize_run_shell(
        run_dir=str(tmp_path / "runs"),
        run_id="runner_apply_1",
        source_wing="chatgpt_signals",
        dry_run=False,
    )
    materialize_run_shell(run)

    drawers = [
        {"drawer_id": "drawer_apply_1", "content": "reschedule appointment", "wing": "chatgpt_signals", "room": "general", "metadata": {}},
    ]
    copy_calls = []

    def fake_call_tool(name, arguments=None, url=None, token=None, timeout=60.0):
        if name == "mempalace_export_drawers":
            offset = int((arguments or {}).get("offset", 0))
            limit = int((arguments or {}).get("limit", 100))
            page = drawers[offset : offset + limit]
            return {"drawers": page, "count": len(page), "offset": offset, "limit": limit}
        if name == "mempalace_copy_drawer":
            copy_calls.append(arguments or {})
            return {"success": True, "drawer_id": "copy_1"}
        raise AssertionError(name)

    monkeypatch.setattr("mempalace.ontology_runner.call_tool", fake_call_tool)
    monkeypatch.setattr("mempalace.ontology_runner._Provider", lambda **_: _FakeProviderAccepted())

    cfg = RunnerConfig(
        localai_base_url="http://snow-white-iii:8080/v1",
        localai_model="qwen3-vl-8b-instruct",
        localai_token="token",
        mcp_url="http://100.112.179.49:8765",
        mcp_token="token",
        source_wing="chatgpt_signals",
        apply_copies=True,
    )
    run_chatgpt_signal_ontology(run, cfg)

    assert len(copy_calls) == 1
    apply_lines = [
        line for line in (run.run_dir / "apply_copies.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    assert len(apply_lines) == 1
    progress = json.loads((run.run_dir / "progress.json").read_text(encoding="utf-8"))
    assert progress["totals"]["copies_materialized"] == 1


def test_localai_base_url_accepts_single_label_lan_and_refuses_public_cloud():
    assert ensure_localai_base_url("http://snow-white-iii:8080/v1") == "http://snow-white-iii:8080/v1"
    with pytest.raises(ValueError, match="non-local"):
        ensure_localai_base_url("https://openrouter.ai/api/v1")


def test_build_runner_config_rejects_non_local_mcp_url(monkeypatch):
    monkeypatch.delenv("MEMPALACE_ONTOLOGY_MCP_URL", raising=False)
    with pytest.raises(ValueError, match="non-local MCP host"):
        build_runner_config(
            SimpleNamespace(
                localai_base_url="http://snow-white-iii:8080/v1",
                localai_token=None,
                localai_token_file=None,
                localai_model="qwen3-vl-8b-instruct",
                mcp_url="https://example.com/mcp",
                mcp_token=None,
                mcp_token_file=None,
                source_wing="chatgpt_signals",
                apply_copies=False,
                page_limit=10,
            )
        )


def test_runner_backfills_partial_candidate_aggregate_files(tmp_path, monkeypatch):
    run = initialize_run_shell(
        run_dir=str(tmp_path / "runs"),
        run_id="runner_backfill_1",
        source_wing="chatgpt_signals",
        dry_run=False,
    )
    materialize_run_shell(run)
    cluster_path = run.run_dir / "candidate_clusters.jsonl"
    canonical_path = run.run_dir / "canonical_candidates.jsonl"
    drawers = [
        {"drawer_id": "drawer_a", "content": "reschedule appointment", "wing": "chatgpt_signals", "room": "general", "metadata": {}},
        {"drawer_id": "drawer_b", "content": "review billing statement", "wing": "chatgpt_signals", "room": "general", "metadata": {}},
    ]

    def fake_call_tool(name, arguments=None, url=None, token=None, timeout=60.0):
        if name == "mempalace_export_drawers":
            offset = int((arguments or {}).get("offset", 0))
            limit = int((arguments or {}).get("limit", 100))
            page = drawers[offset : offset + limit]
            return {"drawers": page, "count": len(page), "offset": offset, "limit": limit}
        raise AssertionError(name)

    monkeypatch.setattr("mempalace.ontology_runner.call_tool", fake_call_tool)
    monkeypatch.setattr("mempalace.ontology_runner._Provider", lambda **_: _FakeProviderTwoClusters())
    cfg = RunnerConfig(
        localai_base_url="http://snow-white-iii:8080/v1",
        localai_model="qwen3-vl-8b-instruct",
        localai_token="token",
        mcp_url="http://100.112.179.49:8765",
        mcp_token="token",
        source_wing="chatgpt_signals",
        apply_copies=False,
    )
    run_chatgpt_signal_ontology(run, cfg)
    cluster_lines = [line for line in cluster_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    canonical_lines = [line for line in canonical_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(cluster_lines) == 2
    assert len(canonical_lines) == 2

    cluster_path.write_text(cluster_lines[0] + "\n", encoding="utf-8")
    canonical_path.write_text(canonical_lines[0] + "\n", encoding="utf-8")

    run_chatgpt_signal_ontology(run, cfg)
    run_chatgpt_signal_ontology(run, cfg)

    cluster_lines = [line for line in cluster_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    canonical_lines = [line for line in canonical_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(cluster_lines) == 2
    assert len(canonical_lines) == 2


def test_runner_progressively_writes_unresolved_before_final_materialization(tmp_path, monkeypatch):
    run = initialize_run_shell(
        run_dir=str(tmp_path / "runs"),
        run_id="runner_progressive_1",
        source_wing="chatgpt_signals",
        dry_run=False,
    )
    materialize_run_shell(run)
    drawers = [{"drawer_id": "drawer_1", "content": "reschedule appointment", "wing": "chatgpt_signals", "room": "general", "metadata": {}}]

    def fake_call_tool(name, arguments=None, url=None, token=None, timeout=60.0):
        if name == "mempalace_export_drawers":
            offset = int((arguments or {}).get("offset", 0))
            if offset > 0:
                return {"drawers": [], "count": 0, "offset": offset, "limit": 100}
            return {"drawers": drawers, "count": 1, "offset": 0, "limit": 100}
        raise AssertionError(name)

    def fail_materialize(*args, **kwargs):
        raise RuntimeError("stop_after_verify")

    monkeypatch.setattr("mempalace.ontology_runner.call_tool", fake_call_tool)
    monkeypatch.setattr("mempalace.ontology_runner._Provider", lambda **_: _FakeProvider())
    monkeypatch.setattr("mempalace.ontology_runner._materialize_decisions_and_reports", fail_materialize)
    cfg = RunnerConfig(
        localai_base_url="http://snow-white-iii:8080/v1",
        localai_model="qwen3-vl-8b-instruct",
        localai_token="token",
        mcp_url="http://100.112.179.49:8765",
        mcp_token="token",
        source_wing="chatgpt_signals",
        apply_copies=False,
    )
    with pytest.raises(RuntimeError, match="stop_after_verify"):
        run_chatgpt_signal_ontology(run, cfg)

    unresolved_lines = [line for line in (run.run_dir / "unresolved.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(unresolved_lines) == 1


def test_build_runner_config_honors_mempalace_ontology_env_precedence(monkeypatch):
    monkeypatch.setenv("MEMPALACE_ONTOLOGY_LOCALAI_BASE_URL", "http://snow-white-iii:8080/v1")
    monkeypatch.setenv("LOCALAI_BASE_URL", "http://localhost:9999/v1")
    monkeypatch.setenv("MEMPALACE_ONTOLOGY_LOCALAI_MODEL", "model_a")
    monkeypatch.setenv("LOCALAI_MODEL", "model_b")
    monkeypatch.setenv("ARCHIVEKG_CHAT_ROLLUP_MODEL", "model_c")
    monkeypatch.setenv("MEMPALACE_ONTOLOGY_LOCALAI_TOKEN_FILE", "/tmp/token_a")
    monkeypatch.setenv("LOCALAI_TOKEN_FILE", "/tmp/token_b")
    monkeypatch.setenv("MEMPALACE_ONTOLOGY_MCP_URL", "http://100.112.179.49:8765")
    monkeypatch.setenv("MEMPALACE_ONTOLOGY_MCP_TOKEN", "tok_a")
    monkeypatch.setenv("MEMPALACE_HTTP_TOKEN", "tok_b")

    cfg = build_runner_config(
        SimpleNamespace(
            localai_base_url=None,
            localai_token=None,
            localai_token_file=None,
            localai_model=None,
            mcp_url=None,
            mcp_token=None,
            mcp_token_file=None,
            source_wing="chatgpt_signals",
            apply_copies=False,
            page_limit=10,
        )
    )
    assert cfg.localai_base_url == "http://snow-white-iii:8080/v1"
    assert cfg.localai_model == "model_a"
    assert cfg.mcp_url == "http://100.112.179.49:8765"
    assert cfg.mcp_token == "tok_a"
