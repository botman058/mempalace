"""Token-protected HTTP transport for the MemPalace MCP server."""

from __future__ import annotations

import argparse
import os
import secrets
import sqlite3
import sys
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Optional

try:
    from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
    from fastapi.responses import JSONResponse
except ImportError:  # pragma: no cover - exercised only without the server extra.
    Depends = FastAPI = Header = HTTPException = Request = Response = JSONResponse = None

from .config import MempalaceConfig
from .embedding import describe_device
from .version import __version__

_REAL_ARGV = sys.argv[:]
try:
    sys.argv = [sys.argv[0]]
    from . import mcp_server as _mcp_server
finally:
    sys.argv = _REAL_ARGV

_mcp_server._restore_stdout()

_TOKEN_ENV_VARS = ("MEMPALACE_HTTP_TOKEN", "MEMPALACE_MCP_TOKEN")
_TOKEN_FILE_ENV_VARS = ("MEMPALACE_HTTP_TOKEN_FILE", "MEMPALACE_MCP_TOKEN_FILE")
_TRUTHY = {"1", "true", "yes", "on"}


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in _TRUTHY


def _read_token_file(path: str) -> Optional[str]:
    try:
        token = Path(path).expanduser().read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return token or None


def load_auth_token() -> Optional[str]:
    """Load the bearer token from env or a token file."""
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


def _jsonrpc_error(req_id: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def _validate_message(message: Any) -> Optional[dict]:
    if not isinstance(message, dict):
        return _jsonrpc_error(None, -32600, "Invalid Request")
    req_id = message.get("id")
    if "jsonrpc" in message and message.get("jsonrpc") != "2.0":
        return _jsonrpc_error(req_id, -32600, "Invalid Request")
    if not isinstance(message.get("method"), str):
        return _jsonrpc_error(req_id, -32600, "Invalid Request")
    return None


def _dispatch_message(message: Any) -> Optional[dict]:
    invalid = _validate_message(message)
    if invalid is not None:
        return invalid
    return _mcp_server.handle_request(message)


def _drawer_count_via_sqlite(palace_path: str) -> Optional[int]:
    db_path = os.path.join(palace_path, "chroma.sqlite3")
    if not os.path.isfile(db_path):
        return None
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        try:
            row = conn.execute(
                """
                SELECT COUNT(*)
                FROM embeddings e
                JOIN segments s ON e.segment_id = s.id
                JOIN collections c ON s.collection = c.id
                WHERE c.name = ?
                """,
                (MempalaceConfig().collection_name,),
            ).fetchone()
        finally:
            conn.close()
    except sqlite3.Error:
        return None
    return int(row[0]) if row and row[0] is not None else None


def _health_payload() -> dict:
    config = MempalaceConfig()
    effective_device = describe_device(config.embedding_device)
    drawer_count = _drawer_count_via_sqlite(config.palace_path)
    payload = {
        "status": "ok",
        "version": __version__,
        "palace_path": config.palace_path,
        "configured_embedding_device": config.embedding_device,
        "effective_embedding_device": effective_device,
        "drawer_count": drawer_count,
    }
    if drawer_count is None:
        payload["drawer_count_available"] = False
    return payload


def _configure_palace(palace: str) -> None:
    palace_path = os.path.abspath(os.path.expanduser(palace))
    os.environ["MEMPALACE_PALACE_PATH"] = palace_path
    _mcp_server._config = MempalaceConfig()
    from .knowledge_graph import KnowledgeGraph

    _mcp_server._kg = KnowledgeGraph(db_path=os.path.join(palace_path, "knowledge_graph.sqlite3"))
    _mcp_server._client_cache = None
    _mcp_server._collection_cache = None
    _mcp_server._palace_db_inode = 0
    _mcp_server._palace_db_mtime = 0.0


def create_app(token: Optional[str] = None, allow_no_auth: Optional[bool] = None):
    """Create the FastAPI app.

    Production defaults to requiring a configured token. Tests and explicit
    local-only development can pass ``allow_no_auth=True``.
    """
    if FastAPI is None:
        raise RuntimeError("Install the HTTP server extra: pip install 'mempalace[server]'")

    if token is None:
        token = load_auth_token()
    if allow_no_auth is None:
        allow_no_auth = _env_truthy("MEMPALACE_HTTP_ALLOW_NO_AUTH")
    auth_required_but_missing = token is None and not allow_no_auth

    async def require_bearer(authorization: Optional[str] = Header(default=None)):
        if auth_required_but_missing:
            raise HTTPException(
                status_code=503,
                detail=(
                    "MEMPALACE_HTTP_TOKEN or MEMPALACE_HTTP_TOKEN_FILE must be set "
                    "before serving MemPalace over HTTP"
                ),
            )
        if token is None:
            return
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Missing bearer token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        candidate = authorization[len("Bearer ") :].strip()
        if not secrets.compare_digest(candidate, token):
            raise HTTPException(
                status_code=403,
                detail="Invalid bearer token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    app = FastAPI(title="MemPalace HTTP MCP", version=__version__)

    @app.get("/healthz", dependencies=[Depends(require_bearer)])
    async def healthz():
        return _health_payload()

    @app.post("/mcp", dependencies=[Depends(require_bearer)])
    async def mcp(request: Request):
        try:
            payload = await request.json()
        except JSONDecodeError:
            return JSONResponse(_jsonrpc_error(None, -32700, "Parse error"), status_code=400)

        if isinstance(payload, list):
            if not payload:
                return JSONResponse(_jsonrpc_error(None, -32600, "Invalid Request"))
            responses = []
            for item in payload:
                response = _dispatch_message(item)
                if response is not None:
                    responses.append(response)
            if not responses:
                return Response(status_code=204)
            return responses

        response = _dispatch_message(payload)
        if response is None:
            return Response(status_code=204)
        return response

    return app


app = create_app()


def _parse_args(argv: Optional[list[str]] = None):
    parser = argparse.ArgumentParser(description="Serve MemPalace MCP over token-protected HTTP")
    parser.add_argument(
        "--palace",
        metavar="PATH",
        help="Path to the palace directory (overrides config file and env var)",
    )
    parser.add_argument("--host", default=os.environ.get("MEMPALACE_HTTP_HOST", "127.0.0.1"))
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("MEMPALACE_HTTP_PORT", "8765")),
    )
    parser.add_argument(
        "--allow-no-auth",
        action="store_true",
        help="Allow unauthenticated HTTP. Intended only for isolated local development.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None):
    args = _parse_args(argv)
    if args.palace:
        _configure_palace(args.palace)
    token = load_auth_token()
    if token is None and not args.allow_no_auth:
        raise SystemExit(
            "Refusing to serve without MEMPALACE_HTTP_TOKEN or MEMPALACE_HTTP_TOKEN_FILE"
        )

    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover - missing optional dependency.
        raise SystemExit("Install the HTTP server extra: pip install 'mempalace[server]'") from exc

    uvicorn.run(
        create_app(token=token, allow_no_auth=args.allow_no_auth),
        host=args.host,
        port=args.port,
    )


if __name__ == "__main__":
    main()
