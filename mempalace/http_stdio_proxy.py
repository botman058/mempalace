"""stdio-to-HTTP MCP proxy used when MEMPALACE_HTTP_URL is configured."""

from __future__ import annotations

import json
import logging
import sys
from typing import Any, Optional

from .http_client import RemoteMCPError, post_jsonrpc, remote_url

logger = logging.getLogger("mempalace_mcp_http_proxy")


def _error_response(req_id: Any, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32000, "message": message}}


def _request_id(payload: Any) -> Optional[Any]:
    if isinstance(payload, dict):
        return payload.get("id")
    return None


def main() -> None:
    logger.info("MemPalace MCP stdio proxy forwarding to %s", remote_url())
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
            except json.JSONDecodeError:
                response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": "Parse error"},
                }
            else:
                try:
                    response = post_jsonrpc(request)
                except RemoteMCPError as exc:
                    req_id = _request_id(request)
                    if req_id is None:
                        logger.error("Remote MemPalace MCP notification failed: %s", exc)
                        continue
                    response = _error_response(req_id, str(exc))
            if response is not None:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
        except KeyboardInterrupt:
            break
        except Exception as exc:  # noqa: BLE001 - keep stdio transport alive if possible.
            logger.error("Proxy error: %s", exc)
