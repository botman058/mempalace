from mempalace.http_client import mcp_endpoint, should_use_remote


def test_mcp_endpoint_normalizes_base_url():
    assert mcp_endpoint("http://snow-white-iii:8765") == "http://snow-white-iii:8765/mcp"
    assert mcp_endpoint("http://snow-white-iii:8765/mcp") == "http://snow-white-iii:8765/mcp"


def test_should_use_remote_respects_local_escape_hatch(monkeypatch):
    monkeypatch.setenv("MEMPALACE_HTTP_URL", "http://snow-white-iii:8765")
    assert should_use_remote() is True
    monkeypatch.setenv("MEMPALACE_LOCAL", "1")
    assert should_use_remote() is False


def test_should_use_remote_respects_explicit_palace(monkeypatch):
    monkeypatch.setenv("MEMPALACE_HTTP_URL", "http://snow-white-iii:8765")
    assert should_use_remote(explicit_palace="/tmp/palace") is False
