import json

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient


def _client():
    from mempalace.http_mcp_server import create_app

    return TestClient(create_app(token="secret"))


def _headers():
    return {"Authorization": "Bearer secret"}


def test_http_initialize():
    client = _client()
    response = client.post(
        "/mcp",
        headers=_headers(),
        json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == 1
    assert body["result"]["serverInfo"]["name"] == "mempalace"


def test_http_tools_list():
    client = _client()
    response = client.post(
        "/mcp",
        headers=_headers(),
        json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    )
    assert response.status_code == 200
    names = {tool["name"] for tool in response.json()["result"]["tools"]}
    assert "mempalace_status" in names
    assert "mempalace_search" in names


def test_http_tools_call():
    client = _client()
    response = client.post(
        "/mcp",
        headers=_headers(),
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "mempalace_get_aaak_spec", "arguments": {}},
        },
    )
    assert response.status_code == 200
    content = response.json()["result"]["content"][0]["text"]
    result = json.loads(content)
    assert "aaak_spec" in result


def test_http_auth_failure():
    client = _client()
    response = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}},
    )
    assert response.status_code == 401


def test_http_healthz():
    client = _client()
    response = client.get("/healthz", headers=_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "palace_path" in body
    assert "effective_embedding_device" in body
    assert "drawer_count" in body


def test_http_invalid_jsonrpc():
    client = _client()
    response = client.post("/mcp", headers=_headers(), json={"jsonrpc": "2.0", "id": 4})
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == 4
    assert body["error"]["code"] == -32600


def test_http_parse_error():
    client = _client()
    response = client.post(
        "/mcp",
        headers={**_headers(), "Content-Type": "application/json"},
        content="{",
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == -32700


def test_http_notification_returns_no_content():
    client = _client()
    response = client.post(
        "/mcp",
        headers=_headers(),
        json={"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
    )
    assert response.status_code == 204
    assert response.content == b""
