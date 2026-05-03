"""Small stdlib client for a remote MemPalace HTTP MCP endpoint."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

_URL_ENV_VARS = ("MEMPALACE_HTTP_URL", "MEMPALACE_MCP_URL", "MEMPALACE_REMOTE_URL")
_TOKEN_ENV_VARS = ("MEMPALACE_HTTP_TOKEN", "MEMPALACE_MCP_TOKEN")
_TOKEN_FILE_ENV_VARS = ("MEMPALACE_HTTP_TOKEN_FILE", "MEMPALACE_MCP_TOKEN_FILE")
_TRUTHY = {"1", "true", "yes", "on"}


class RemoteMCPError(Exception):
    """Raised when the remote MCP endpoint cannot satisfy a request."""


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in _TRUTHY


def remote_url() -> Optional[str]:
    for name in _URL_ENV_VARS:
        value = os.environ.get(name)
        if value and value.strip():
            return value.strip()
    return None


def _read_token_file(path: str) -> Optional[str]:
    try:
        token = Path(path).expanduser().read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return token or None


def remote_token() -> Optional[str]:
    for name in _TOKEN_ENV_VARS:
        value = os.environ.get(name)
        if value and value.strip():
            return value.strip()
    for name in _TOKEN_FILE_ENV_VARS:
        value = os.environ.get(name)
        if value and value.strip():
            token = _read_token_file(value.strip())
            if token:
                return token
    return None


def should_use_remote(explicit_palace: Optional[str] = None) -> bool:
    """Return True when CLI reads should route to the HTTP endpoint."""
    return bool(remote_url()) and explicit_palace is None and not _env_truthy("MEMPALACE_LOCAL")


def mcp_endpoint(url: str) -> str:
    url = url.rstrip("/")
    if url.endswith("/mcp"):
        return url
    return f"{url}/mcp"


def call_tool(
    name: str,
    arguments: Optional[dict] = None,
    url: Optional[str] = None,
    token: Optional[str] = None,
    timeout: float = 60.0,
) -> dict:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments or {}},
    }
    rpc_response = post_jsonrpc(payload, url=url, token=token, timeout=timeout)
    if rpc_response is None:
        raise RemoteMCPError("Unexpected empty response from remote MCP endpoint")
    if "error" in rpc_response:
        error = rpc_response["error"]
        message = error.get("message", "remote MCP error") if isinstance(error, dict) else error
        raise RemoteMCPError(str(message))

    try:
        text = rpc_response["result"]["content"][0]["text"]
        return json.loads(text)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise RemoteMCPError("Unexpected tools/call response from remote MCP endpoint") from exc


def post_jsonrpc(
    payload,
    url: Optional[str] = None,
    token: Optional[str] = None,
    timeout: float = 60.0,
):
    raw_url = url or remote_url()
    if not raw_url:
        raise RemoteMCPError("No remote MemPalace URL configured")
    url = mcp_endpoint(raw_url)
    token = token if token is not None else remote_token()
    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, data=body, headers=headers, method="POST")

    try:
        with urlopen(request, timeout=timeout) as response:
            if response.status == 204:
                return None
            response_body = response.read().decode("utf-8")
    except HTTPError as exc:
        if exc.code == 204:
            return None
        detail = exc.read().decode("utf-8", errors="replace")
        raise RemoteMCPError(f"HTTP {exc.code} from {url}: {detail}") from exc
    except (URLError, OSError) as exc:
        raise RemoteMCPError(f"Could not reach {url}: {exc}") from exc

    try:
        return json.loads(response_body)
    except json.JSONDecodeError as exc:
        raise RemoteMCPError(f"Invalid JSON response from {url}") from exc


def format_status(result: dict) -> str:
    if result.get("error"):
        hint = result.get("hint")
        return f"\n  {result['error']}" + (f"\n  {hint}" if hint else "")

    total = result.get("total_drawers", 0)
    wings = result.get("wings") or {}
    rooms_by_wing = result.get("taxonomy") or {}

    lines = [
        "",
        "=" * 55,
        f"  MemPalace Status - {total} drawers",
        "=" * 55,
        "",
    ]
    if rooms_by_wing:
        for wing, rooms in sorted(rooms_by_wing.items()):
            lines.append(f"  WING: {wing}")
            for room, count in sorted(rooms.items(), key=lambda item: item[1], reverse=True):
                lines.append(f"    ROOM: {room:20} {count:5} drawers")
            lines.append("")
    else:
        for wing, count in sorted(wings.items(), key=lambda item: item[0]):
            lines.append(f"  WING: {wing:24} {count:5} drawers")
        if wings:
            lines.append("")
    lines.extend([("=" * 55), ""])
    return "\n".join(lines)


def format_search(query: str, result: dict, wing: str = None, room: str = None) -> str:
    if result.get("error"):
        hint = result.get("hint")
        return f"\n  Search error: {result['error']}" + (f"\n  {hint}" if hint else "")

    hits = result.get("results") or []
    if not hits:
        return f'\n  No results found for: "{query}"'

    lines = ["", "=" * 60, f'  Results for: "{query}"']
    if wing:
        lines.append(f"  Wing: {wing}")
    if room:
        lines.append(f"  Room: {room}")
    lines.extend([("=" * 60), ""])

    for index, hit in enumerate(hits, 1):
        wing_name = hit.get("wing", "?")
        room_name = hit.get("room", "?")
        source = hit.get("source_file", "?")
        similarity = hit.get("similarity")
        bm25 = hit.get("bm25_score", 0.0)
        match = f"similarity={similarity}" if similarity is not None else "similarity=n/a"

        lines.append(f"  [{index}] {wing_name} / {room_name}")
        lines.append(f"      Source: {source}")
        lines.append(f"      Match:  {match}  bm25={bm25}")
        lines.append("")
        for text_line in str(hit.get("text", "")).strip().split("\n"):
            lines.append(f"      {text_line}")
        lines.append("")
        lines.append(f"  {'-' * 56}")
    lines.append("")
    return "\n".join(lines)
