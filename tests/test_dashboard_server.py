import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from mempalace.dashboard_server import MiningStatus, create_app, load_upstream_token


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


def _client(*, mining_active=False, token="secret"):
    upstream = FakeUpstream()
    app = create_app(
        token=token,
        upstream_client=upstream,
        mining_detector=FakeMiningDetector(active=mining_active),
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

    response = client.get("/api/overview")

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
    _assert_telemetry_value(body, "online", "localai_status", "telemetry.localai.status")
    _assert_telemetry_value(
        body,
        "saved",
        "checkpoint_status",
        "checkpoint",
        "checkpoint.status",
        "telemetry.checkpoint",
        "telemetry.checkpoint.status",
    )


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


def test_api_requests_refuse_without_configured_token(monkeypatch):
    monkeypatch.delenv("MEMPALACE_DASHBOARD_TOKEN", raising=False)
    monkeypatch.delenv("MEMPALACE_DASHBOARD_TOKEN_FILE", raising=False)

    client, upstream = _client(token=None)

    response = client.get("/api/overview")

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "MEMPALACE_DASHBOARD_TOKEN or MEMPALACE_DASHBOARD_TOKEN_FILE must be set before serving the dashboard"
    )
    assert upstream.calls == []


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
