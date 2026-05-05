import json

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from mempalace.dashboard_server import MiningStatus, create_app, load_ontology_run_root, load_upstream_token


def _headers():
    return {"Authorization": "Bearer secret"}


def _get_path(payload, path):
    current = payload
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(path)
        current = current[part]
    return current


def _assert_telemetry_value(body, expected, *paths):
    for path in paths:
        try:
            value = _get_path(body, path)
        except KeyError:
            continue
        if isinstance(value, dict):
            if value.get("status") == expected or value.get("state") == expected:
                return
            continue
        if value == expected:
            return
    raise AssertionError(f"Missing {expected!r} at all expected paths: {paths}")


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, separators=(",", ":")))
            handle.write("\n")


def _progress_payload(run_id, *, status, current_phase, current_phase_status, ended_at):
    return {
        "schema_name": "ontology.progress",
        "schema_version": 1,
        "run_id": run_id,
        "run_kind": "chatgpt_signal_ontology",
        "source_wing": "chatgpt_signals",
        "status": status,
        "current_phase": current_phase,
        "current_phase_status": current_phase_status,
        "phase_order": [
            "pass1_open",
            "candidate_clusters",
            "route_pass2",
            "route_verify",
            "apply_copies",
        ],
        "phase_attempts": {
            "pass1_open": 1,
            "candidate_clusters": 1,
            "route_pass2": 1,
            "route_verify": 0,
            "apply_copies": 0,
        },
        "started_at": "2026-05-05T14:30:15Z",
        "updated_at": "2026-05-05T14:41:02Z",
        "ended_at": ended_at,
        "elapsed_seconds": 647,
        "current_phase_progress": {
            "unit": "drawer",
            "total": 1200,
            "processed": 148,
            "accepted": 12,
            "unresolved": 3,
            "errors": 1,
        },
        "totals": {
            "source_drawers_total": 1200,
            "source_drawers_processed": 148,
            "routes_accepted": 12,
            "routes_unresolved": 3,
            "copies_materialized": 4,
            "phase_records_written": 148,
        },
        "last_record": {
            "phase": "pass1_open",
            "relative_path": "pass1_open.jsonl",
            "sequence": 148,
            "subject_id": "drawer_chatgpt_signals_general_9f2a5ef5a06c8bd0c9c1a8c1",
            "recorded_at": "2026-05-05T14:41:01Z",
        },
        "warning_count": 3,
        "error_count": 1,
    }


def _artifact_index_payload(run_id, artifacts):
    return {
        "schema_name": "ontology.artifact_index",
        "schema_version": 1,
        "run_id": run_id,
        "updated_at": "2026-05-05T14:41:02Z",
        "artifacts": artifacts,
    }


def _make_run(root, run_id, progress, artifacts=None, unresolved_rows=None):
    run_dir = root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_json(run_dir / "progress.json", progress)
    if artifacts is not None:
        _write_json(run_dir / "artifacts_index.json", _artifact_index_payload(run_id, artifacts))
    if unresolved_rows is not None:
        _write_jsonl(run_dir / "unresolved.jsonl", unresolved_rows)
    return run_dir


class FakeMiningDetector:
    def __init__(self, active=False):
        self.active = active

    def detect(self):
        return MiningStatus(
            active=self.active,
            active_services=(
                [
                    {
                        "service": "mempalace-mine-chatgpt.service",
                        "active_state": "active",
                        "sub_state": "running",
                    }
                ]
                if self.active
                else []
            ),
            matched_processes=[],
            configured_services=["mempalace-mine-chatgpt.service"],
            configured_process_patterns=[],
            detection_errors=[],
        )


class FakeUpstream:
    def __init__(self):
        self.calls = []

    def healthz(self):
        return {
            "status": "ok",
            "drawer_count": 42,
            "effective_embedding_device": "cuda",
            "localai_status": "online",
            "checkpoint_status": "saved",
            "localai": {"status": "online"},
            "checkpoint": {"status": "saved"},
        }

    def call_tool(self, name, arguments=None):
        self.calls.append((name, dict(arguments or {})))
        if name == "mempalace_get_taxonomy":
            return {"taxonomy": {"wing-a": {"room-a": 2}}}
        if name == "mempalace_search":
            return {
                "results": [
                    {
                        "drawer_id": "drawer-1",
                        "wing": "wing-a",
                        "room": "room-a",
                        "text": arguments["query"],
                    }
                ]
            }
        if name == "mempalace_list_drawers":
            return {
                "drawers": [
                    {
                        "drawer_id": "drawer-1",
                        "wing": "wing-a",
                        "room": "room-a",
                        "content_preview": "preview text",
                    }
                ],
                "count": 1,
                "offset": 0,
                "limit": 20,
            }
        if name == "mempalace_get_drawer":
            return {
                "drawer_id": "drawer-1",
                "content": "full drawer text",
                "wing": "wing-a",
                "room": "room-a",
                "metadata": {"source_file": "source.md"},
            }
        raise AssertionError(f"Unexpected MCP tool call: {name}")


def _client(*, mining_active=False, token="secret", ontology_run_root=None):
    upstream = FakeUpstream()
    app = create_app(
        token=token,
        upstream_client=upstream,
        mining_detector=FakeMiningDetector(active=mining_active),
        ontology_run_root=ontology_run_root,
    )
    return TestClient(app), upstream


def _assert_locked(response):
    assert response.status_code == 423
    payload = response.json()
    assert payload["status"] == "locked"
    assert payload["mode"] == "telemetry-only"
    assert payload["mining"]["active"] is True


def test_unauthenticated_api_request_fails():
    client, _ = _client()

    response = client.get("/api/ontology/runs")

    assert response.status_code == 401
    assert response.headers.get("www-authenticate") == "Bearer"


def test_api_overview_succeeds_with_token_and_returns_mining_active_telemetry():
    client, _ = _client(mining_active=True)

    response = client.get("/api/overview", headers=_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["mining_active"] is True
    assert body["mode"] == "telemetry-only"
    assert body["telemetry"]["mining_active"] is True
    assert body["drawer_count"] == 42
    assert body["embedding_device"] == "cuda"
    _assert_telemetry_value(body, "not_configured", "localai_status", "telemetry.localai.status")
    _assert_telemetry_value(
        body,
        "not_configured",
        "checkpoint_status",
        "checkpoint",
        "checkpoint.status",
        "telemetry.checkpoint",
        "telemetry.checkpoint.status",
    )


def test_invalid_run_id_is_rejected_without_file_access(tmp_path):
    client, upstream = _client(ontology_run_root=tmp_path)

    response = client.get("/api/ontology/runs/bad..id", headers=_headers())

    assert response.status_code == 400
    assert upstream.calls == []


def test_run_list_detail_and_artifact_endpoints_read_temp_root(tmp_path):
    active_id = "20260505T143015Z_chatgpt_signal_ontology"
    completed_id = "20260505T120000Z_chatgpt_signal_ontology"
    failed_id = "20260505T110000Z_chatgpt_signal_ontology"
    interrupted_id = "20260505T100000Z_chatgpt_signal_ontology"

    active_progress = _progress_payload(
        active_id,
        status="running",
        current_phase="pass1_open",
        current_phase_status="running",
        ended_at=None,
    )
    completed_progress = _progress_payload(
        completed_id,
        status="completed",
        current_phase="apply_copies",
        current_phase_status="completed",
        ended_at="2026-05-05T15:10:00Z",
    )
    failed_progress = _progress_payload(
        failed_id,
        status="failed",
        current_phase="route_verify",
        current_phase_status="failed",
        ended_at="2026-05-05T15:20:00Z",
    )
    interrupted_progress = _progress_payload(
        interrupted_id,
        status="interrupted",
        current_phase="candidate_clusters",
        current_phase_status="failed",
        ended_at="2026-05-05T15:30:00Z",
    )

    _make_run(tmp_path, active_id, active_progress)
    completed_artifacts = [
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
            "bytes": 1234,
            "status": "active",
            "dashboard_safe": True,
            "privacy_level": "summary",
            "updated_at": "2026-05-05T14:41:02Z",
        },
        {
            "artifact_key": "unresolved_routes",
            "relative_path": "unresolved.jsonl",
            "schema_name": "ontology.unresolved_route",
            "schema_version": 1,
            "artifact_kind": "decision_records",
            "phase": "route_verify",
            "content_type": "application/jsonl",
            "append_only": True,
            "records": 3,
            "bytes": 2345,
            "status": "active",
            "dashboard_safe": True,
            "privacy_level": "bounded_excerpt",
            "updated_at": "2026-05-05T14:41:02Z",
        },
    ]
    unresolved_rows = [
        {
            "schema_name": "ontology.unresolved_route",
            "schema_version": 1,
            "run_id": completed_id,
            "sequence": sequence,
            "recorded_at": f"2026-05-05T15:13:{sequence:02d}Z",
            "route_iteration": sequence,
            "source_drawer_id": f"drawer-{sequence}",
            "source_wing": "chatgpt_signals",
            "source_room": "general",
            "unresolved_status": "conflict",
            "candidate_ids": [f"cand-{sequence}-{ix}" for ix in range(10)],
            "reason_code": "verifier_disagreed",
            "reason_detail": f"reason detail {sequence} " + ("x" * 80),
            "route_confidence": 0.5 + sequence / 10.0,
            "next_action": "manual_review",
            "retryable": False,
            "source_excerpt": f"source excerpt {sequence} " + ("y" * 120),
        }
        for sequence in range(1, 4)
    ]
    _make_run(tmp_path, completed_id, completed_progress, artifacts=completed_artifacts, unresolved_rows=unresolved_rows)
    _make_run(tmp_path, failed_id, failed_progress)
    _make_run(tmp_path, interrupted_id, interrupted_progress)

    client, upstream = _client(ontology_run_root=tmp_path)

    response = client.get("/api/ontology/runs", headers=_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 4
    assert body["run_root"] == str(tmp_path)
    statuses = {item["run_id"]: item["status"] for item in body["runs"]}
    assert statuses[active_id] == "running"
    assert statuses[completed_id] == "completed"
    assert statuses[failed_id] == "failed"
    assert statuses[interrupted_id] == "interrupted"

    active_detail = client.get(f"/api/ontology/runs/{active_id}", headers=_headers())
    assert active_detail.status_code == 200
    active_body = active_detail.json()
    assert active_body["status"] == "ok"
    assert active_body["progress"]["status"] == "running"
    assert active_body["progress"]["ended_at"] is None
    assert active_body["artifact_count"] == 0
    assert active_body["unresolved_preview"] == []

    completed_detail = client.get(f"/api/ontology/runs/{completed_id}", headers=_headers())
    assert completed_detail.status_code == 200
    completed_body = completed_detail.json()
    assert completed_body["progress"]["status"] == "completed"
    assert completed_body["progress"]["ended_at"] == "2026-05-05T15:10:00Z"
    assert completed_body["artifact_count"] == 2

    failed_detail = client.get(f"/api/ontology/runs/{failed_id}", headers=_headers())
    assert failed_detail.status_code == 200
    assert failed_detail.json()["progress"]["status"] == "failed"

    interrupted_detail = client.get(f"/api/ontology/runs/{interrupted_id}", headers=_headers())
    assert interrupted_detail.status_code == 200
    assert interrupted_detail.json()["progress"]["status"] == "interrupted"

    artifacts_response = client.get(f"/api/ontology/runs/{completed_id}/artifacts", headers=_headers())
    assert artifacts_response.status_code == 200
    artifacts_body = artifacts_response.json()
    assert artifacts_body["artifact_count"] == 2
    assert artifacts_body["artifacts"][1]["privacy_level"] == "bounded_excerpt"
    assert artifacts_body["artifacts"][1]["dashboard_safe"] is True

    preview_response = client.get(
        f"/api/ontology/runs/{completed_id}/unresolved-preview?limit=2&excerpt_chars=20",
        headers=_headers(),
    )
    assert preview_response.status_code == 200
    preview_body = preview_response.json()
    assert preview_body["status"] == "ok"
    assert preview_body["count"] == 2
    assert preview_body["truncated"] is True
    assert [item["sequence"] for item in preview_body["preview"]] == [2, 3]
    assert all(len(item["source_excerpt"]) <= 20 for item in preview_body["preview"])
    assert all(len(item["reason_detail"]) <= 20 for item in preview_body["preview"])
    assert all(item["candidate_ids_truncated"] is True for item in preview_body["preview"])

    assert upstream.calls == []


def test_mining_active_still_allows_ontology_progress_endpoints(tmp_path):
    run_id = "20260505T143015Z_chatgpt_signal_ontology"
    progress = _progress_payload(
        run_id,
        status="running",
        current_phase="pass1_open",
        current_phase_status="running",
        ended_at=None,
    )
    artifacts = [
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
            "bytes": 1234,
            "status": "active",
            "dashboard_safe": True,
            "privacy_level": "summary",
            "updated_at": "2026-05-05T14:41:02Z",
        },
        {
            "artifact_key": "unresolved_routes",
            "relative_path": "unresolved.jsonl",
            "schema_name": "ontology.unresolved_route",
            "schema_version": 1,
            "artifact_kind": "decision_records",
            "phase": "route_verify",
            "content_type": "application/jsonl",
            "append_only": True,
            "records": 1,
            "bytes": 345,
            "status": "active",
            "dashboard_safe": True,
            "privacy_level": "bounded_excerpt",
            "updated_at": "2026-05-05T14:41:02Z",
        },
    ]
    unresolved_rows = [
        {
            "schema_name": "ontology.unresolved_route",
            "schema_version": 1,
            "run_id": run_id,
            "sequence": 1,
            "recorded_at": "2026-05-05T15:13:12Z",
            "route_iteration": 1,
            "source_drawer_id": "drawer-1",
            "source_wing": "chatgpt_signals",
            "source_room": "general",
            "unresolved_status": "conflict",
            "candidate_ids": ["cand-1", "cand-2"],
            "reason_code": "verifier_disagreed",
            "reason_detail": "short detail",
            "route_confidence": 0.58,
            "next_action": "manual_review",
            "retryable": False,
            "source_excerpt": "short excerpt",
        }
    ]
    _make_run(tmp_path, run_id, progress, artifacts=artifacts, unresolved_rows=unresolved_rows)

    client, upstream = _client(mining_active=True, ontology_run_root=tmp_path)

    response = client.get("/api/ontology/runs", headers=_headers())
    assert response.status_code == 200

    detail = client.get(f"/api/ontology/runs/{run_id}", headers=_headers())
    assert detail.status_code == 200
    assert detail.json()["progress"]["status"] == "running"

    artifacts_response = client.get(f"/api/ontology/runs/{run_id}/artifacts", headers=_headers())
    assert artifacts_response.status_code == 200

    preview_response = client.get(f"/api/ontology/runs/{run_id}/unresolved-preview", headers=_headers())
    assert preview_response.status_code == 200
    assert preview_response.json()["preview"][0]["source_excerpt"] == "short excerpt"

    assert upstream.calls == []


def test_api_requests_refuse_without_configured_token(monkeypatch):
    monkeypatch.delenv("MEMPALACE_DASHBOARD_TOKEN", raising=False)
    monkeypatch.delenv("MEMPALACE_DASHBOARD_TOKEN_FILE", raising=False)

    client, upstream = _client(token=None)

    response = client.get("/api/ontology/runs")

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "MEMPALACE_DASHBOARD_TOKEN or MEMPALACE_DASHBOARD_TOKEN_FILE must be set before serving the dashboard"
    )
    assert upstream.calls == []


def test_load_upstream_token_prefers_http_token_over_dashboard_token(monkeypatch):
    monkeypatch.delenv("MEMPALACE_DASHBOARD_TOKEN", raising=False)
    monkeypatch.delenv("MEMPALACE_DASHBOARD_TOKEN_FILE", raising=False)
    monkeypatch.delenv("MEMPALACE_DASHBOARD_MCP_TOKEN", raising=False)
    monkeypatch.delenv("MEMPALACE_MCP_TOKEN", raising=False)
    monkeypatch.delenv("MEMPALACE_DASHBOARD_MCP_TOKEN_FILE", raising=False)
    monkeypatch.delenv("MEMPALACE_HTTP_TOKEN", raising=False)
    monkeypatch.delenv("MEMPALACE_HTTP_TOKEN_FILE", raising=False)
    monkeypatch.delenv("MEMPALACE_MCP_TOKEN_FILE", raising=False)
    monkeypatch.delenv("TOKEN_FILE", raising=False)
    monkeypatch.setenv("MEMPALACE_DASHBOARD_TOKEN", "dashboard-token")
    monkeypatch.setenv("MEMPALACE_HTTP_TOKEN", "http-token")

    assert load_upstream_token() == "http-token"


def test_load_ontology_run_root_prefers_configured_env(monkeypatch, tmp_path):
    monkeypatch.setenv("MEMPALACE_ONTOLOGY_RUN_ROOT", str(tmp_path))
    assert load_ontology_run_root() == tmp_path.resolve()


def test_load_ontology_run_root_refuses_forbidden_root(monkeypatch):
    monkeypatch.setenv("MEMPALACE_ONTOLOGY_RUN_ROOT", "/media/u0/Extreme SSD")

    with pytest.raises(ValueError, match="forbidden"):
        load_ontology_run_root()


def test_create_app_refuses_forbidden_explicit_ontology_run_root():
    upstream = FakeUpstream()
    detector = FakeMiningDetector(active=False)

    with pytest.raises(ValueError, match="forbidden"):
        create_app(
            token="secret",
            upstream_client=upstream,
            mining_detector=detector,
            ontology_run_root="/media/u0/Extreme SSD",
        )


def test_mining_active_locks_heavy_endpoints_without_mcp():
    client, upstream = _client(mining_active=True)

    response = client.get("/api/taxonomy", headers=_headers())
    _assert_locked(response)

    response = client.get("/api/search?q=alpha", headers=_headers())
    _assert_locked(response)

    response = client.get("/api/drawers", headers=_headers())
    _assert_locked(response)

    response = client.get("/api/drawers/drawer-1", headers=_headers())
    _assert_locked(response)

    assert upstream.calls == []


def test_idle_heavy_endpoints_call_only_read_only_mcp_tools():
    client, upstream = _client(mining_active=False)

    response = client.get("/api/taxonomy", headers=_headers())
    assert response.status_code == 200

    response = client.get(
        "/api/search?q=alpha&wing=wing-a&room=room-a",
        headers=_headers(),
    )
    assert response.status_code == 200

    response = client.get("/api/drawers?wing=wing-a&room=room-a", headers=_headers())
    assert response.status_code == 200

    response = client.get("/api/drawers/drawer-1", headers=_headers())
    assert response.status_code == 200

    assert [name for name, _ in upstream.calls] == [
        "mempalace_get_taxonomy",
        "mempalace_search",
        "mempalace_list_drawers",
        "mempalace_get_drawer",
    ]
    assert upstream.calls[1][1]["query"] == "alpha"
    assert {name for name, _ in upstream.calls} <= {
        "mempalace_get_taxonomy",
        "mempalace_search",
        "mempalace_list_drawers",
        "mempalace_get_drawer",
    }


def test_static_index_route_serves_html_without_api_token():
    client, _ = _client()

    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "MemPalace Dashboard" in response.text
