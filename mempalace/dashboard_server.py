"""Read-only FastAPI dashboard backend with active-mining guard rails."""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import subprocess
from dataclasses import dataclass
from ipaddress import ip_address, ip_network
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

try:
    from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request as FastAPIRequest
    from fastapi.concurrency import run_in_threadpool
    from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
except ImportError:  # pragma: no cover - exercised only without the server extra.
    Depends = FastAPI = Header = HTTPException = Query = FastAPIRequest = None
    FileResponse = HTMLResponse = JSONResponse = StaticFiles = None
    run_in_threadpool = None

from .version import __version__
from .ontology_run import resolve_run_root, validate_run_id

_DASHBOARD_TOKEN_ENV_VARS = (
    "MEMPALACE_DASHBOARD_TOKEN",
)
_DASHBOARD_TOKEN_FILE_ENV_VARS = (
    "MEMPALACE_DASHBOARD_TOKEN_FILE",
)
_UPSTREAM_URL_ENV_VARS = (
    "MEMPALACE_DASHBOARD_MCP_URL",
    "MEMPALACE_HTTP_URL",
    "MEMPALACE_MCP_URL",
    "MEMPALACE_REMOTE_URL",
)
_UPSTREAM_TOKEN_ENV_VARS = (
    "MEMPALACE_DASHBOARD_MCP_TOKEN",
    "MEMPALACE_HTTP_TOKEN",
    "MEMPALACE_MCP_TOKEN",
)
_UPSTREAM_TOKEN_FILE_ENV_VARS = (
    "MEMPALACE_DASHBOARD_MCP_TOKEN_FILE",
    "MEMPALACE_HTTP_TOKEN_FILE",
    "MEMPALACE_MCP_TOKEN_FILE",
)
_LOCALAI_URL_ENV_VARS = (
    "MEMPALACE_DASHBOARD_LOCALAI_URL",
    "LOCALAI_BASE_URL",
    "ARCHIVEKG_OPENAI_BASE_URL",
)
_LOCALAI_TOKEN_ENV_VARS = (
    "MEMPALACE_DASHBOARD_LOCALAI_TOKEN",
    "LOCALAI_TOKEN",
    "ARCHIVEKG_OPENAI_API_KEY",
)
_LOCALAI_TOKEN_FILE_ENV_VARS = (
    "MEMPALACE_DASHBOARD_LOCALAI_TOKEN_FILE",
    "LOCALAI_TOKEN_FILE",
)
_LOCALAI_MODEL_ENV_VARS = (
    "MEMPALACE_DASHBOARD_LOCALAI_MODEL",
    "LOCALAI_MODEL",
    "ARCHIVEKG_CHAT_ROLLUP_MODEL",
)
_LOCALAI_CHECKPOINT_ENV_VARS = (
    "MEMPALACE_DASHBOARD_LOCALAI_CHECKPOINT",
    "LOCALAI_SIGNAL_CHECKPOINT",
)
_ONTOLOGY_RUN_ROOT_ENV_VARS = (
    "MEMPALACE_DASHBOARD_ONTOLOGY_RUN_ROOT",
    "MEMPALACE_ONTOLOGY_RUN_ROOT",
)
_DEFAULT_MINING_SERVICES = (
    "mempalace-mine-chatgpt.service",
    "mempalace-localai-chatgpt-signals.service",
    "mempalace-ontology-chatgpt-signals.service",
)
_DEFAULT_MINING_PROCESS_PATTERNS = (
    r"(^|[=/ ])ingest_chatgpt_canonical\.(py|sh)([ ]|$)",
    r"(^|[=/ ])localai_chatgpt_signals\.py([ ]|$)",
    r"(^|[=/ ])localai_chatgpt_thread_signals\.py([ ]|$)",
    r"(^|[=/ ])start_chatgpt_thread_signal_rebuild_snow_white_iii\.sh([ ]|$)",
    r"(^|[=/ ])mempalace([ ]+.+)?[ ]ontology[ ]chatgpt-signals([ ]|$)",
    r"chatgpt[_-]thread[_-]signal",
)
_DEFAULT_ALLOWED_HOSTS = {"localhost", "snow-white-iii"}
_DEFAULT_ALLOWED_HOST_SUFFIXES = (".ts.net", ".local", ".lan", ".internal", ".home.arpa")
_TAILNET_CGNAT = ip_network("100.64.0.0/10")
_CHECKPOINT_TAIL_BYTES = 65536
_JSONL_TAIL_BYTES = 65536
_UNRESOLVED_PREVIEW_DEFAULT_LIMIT = 10
_UNRESOLVED_PREVIEW_MAX_LIMIT = 50
_UNRESOLVED_PREVIEW_DEFAULT_EXCERPT_CHARS = 240
_READ_ONLY_TOOLS = frozenset(
    {
        "mempalace_get_taxonomy",
        "mempalace_search",
        "mempalace_list_drawers",
        "mempalace_get_drawer",
    }
)


def _env_flag_enabled(name: str) -> bool:
    raw = os.environ.get(name, "")
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _load_first_env(env_vars: Sequence[str]) -> Optional[str]:
    for name in env_vars:
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


def _load_token_from(env_vars: Sequence[str], file_env_vars: Sequence[str]) -> Optional[str]:
    for name in env_vars:
        value = os.environ.get(name)
        if value and value.strip():
            return value.strip()
    for name in file_env_vars:
        value = os.environ.get(name)
        if value and value.strip():
            token = _read_token_file(value.strip())
            if token:
                return token
    return None


def load_auth_token() -> Optional[str]:
    """Load the bearer token for the dashboard itself."""
    return _load_token_from(_DASHBOARD_TOKEN_ENV_VARS, _DASHBOARD_TOKEN_FILE_ENV_VARS)


def load_upstream_token() -> Optional[str]:
    """Load the bearer token used to reach the upstream HTTP MCP server."""
    return _load_token_from(_UPSTREAM_TOKEN_ENV_VARS, _UPSTREAM_TOKEN_FILE_ENV_VARS)


def load_upstream_url() -> Optional[str]:
    return _load_first_env(_UPSTREAM_URL_ENV_VARS) or "http://127.0.0.1:8765"


def load_localai_url() -> Optional[str]:
    return _load_first_env(_LOCALAI_URL_ENV_VARS)


def load_localai_token() -> Optional[str]:
    return _load_token_from(_LOCALAI_TOKEN_ENV_VARS, _LOCALAI_TOKEN_FILE_ENV_VARS)


def load_localai_model() -> Optional[str]:
    return _load_first_env(_LOCALAI_MODEL_ENV_VARS)


def load_localai_checkpoint_path() -> Optional[Path]:
    raw = _load_first_env(_LOCALAI_CHECKPOINT_ENV_VARS)
    if not raw:
        return None
    return Path(raw).expanduser()


def load_ontology_run_root() -> Path:
    raw = _load_first_env(_ONTOLOGY_RUN_ROOT_ENV_VARS)
    if raw:
        return resolve_run_root(raw)
    return resolve_run_root(None)


def _split_env_list(name: str, default: Sequence[str]) -> List[str]:
    raw = os.environ.get(name, "")
    if not raw.strip():
        return [item for item in default if item]
    values: List[str] = []
    for chunk in raw.replace("\n", ",").split(","):
        item = chunk.strip()
        if item:
            values.append(item)
    return values


def _normalize_base_url(url: str) -> str:
    return url.strip().rstrip("/")


def _allowed_local_host(hostname: str) -> bool:
    host = hostname.strip().lower()
    if not host:
        return False
    if host in _DEFAULT_ALLOWED_HOSTS:
        return True
    extra_hosts = {
        item.lower()
        for item in _split_env_list("MEMPALACE_DASHBOARD_ALLOWED_MCP_HOSTS", ())
        if item.strip()
    }
    if host in extra_hosts:
        return True
    if host.endswith(_DEFAULT_ALLOWED_HOST_SUFFIXES):
        return True
    try:
        parsed_ip = ip_address(host)
    except ValueError:
        return False
    return bool(
        parsed_ip.is_loopback
        or parsed_ip.is_private
        or parsed_ip.is_link_local
        or parsed_ip in _TAILNET_CGNAT
    )


def _validate_local_url(url: str, label: str) -> str:
    normalized = _normalize_base_url(url)
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"{label} must use http or https")
    if not parsed.hostname:
        raise ValueError(f"{label} must include a hostname")
    if not _allowed_local_host(parsed.hostname):
        raise ValueError(
            f"{label} must stay on localhost, LAN, or tailnet; "
            f"refusing host {parsed.hostname!r}"
        )
    return normalized


def validate_upstream_url(url: str) -> str:
    normalized = _validate_local_url(url, "Dashboard upstream URL")
    if normalized.endswith("/mcp"):
        normalized = normalized[: -len("/mcp")]
    return normalized


def validate_localai_url(url: str) -> str:
    return _validate_local_url(url, "LocalAI URL")


def _static_dir_from_env() -> Path:
    value = os.environ.get("MEMPALACE_DASHBOARD_STATIC_DIR")
    if value and value.strip():
        return Path(value.strip()).expanduser()
    return Path(__file__).resolve().parent / "dashboard_static"


def _is_valid_relative_path(relative_path: str) -> bool:
    candidate = PurePosixPath(relative_path)
    if candidate.is_absolute():
        return False
    if not candidate.parts:
        return False
    return all(part not in {"", ".", ".."} for part in candidate.parts)


def _read_json_file(path: Path) -> Optional[Dict[str, Any]]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _truncate_text(value: Any, limit: int) -> Optional[str]:
    if value is None:
        return None
    text = str(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def _tail_jsonl_records(path: Path, *, limit: int, max_bytes: int = _JSONL_TAIL_BYTES) -> List[Dict[str, Any]]:
    if limit <= 0 or not path.exists():
        return []

    try:
        stat_result = path.stat()
    except OSError:
        return []

    if stat_result.st_size <= 0:
        return []

    read_size = min(stat_result.st_size, max_bytes)
    start = stat_result.st_size - read_size
    try:
        with path.open("rb") as handle:
            handle.seek(start)
            chunk = handle.read(read_size)
    except OSError:
        return []

    lines = chunk.decode("utf-8", errors="replace").splitlines()
    if start > 0 and lines:
        lines = lines[1:]

    records: List[Dict[str, Any]] = []
    for line in reversed(lines):
        if len(records) >= limit:
            break
        text = line.strip()
        if not text:
            continue
        try:
            row = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            records.append(row)
    records.reverse()
    return records


def _safe_run_dir(run_root: Path, run_id: str) -> Path:
    validated_run_id = validate_run_id(run_id)
    run_dir = (run_root / validated_run_id).resolve(strict=False)
    resolved_root = run_root.resolve(strict=False)
    try:
        run_dir.relative_to(resolved_root)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid run_id") from exc
    return run_dir


def _list_run_dirs(run_root: Path) -> List[Path]:
    if not run_root.exists():
        return []
    try:
        children = list(run_root.iterdir())
    except OSError:
        return []
    run_dirs: List[Path] = []
    for child in children:
        if not child.is_dir():
            continue
        try:
            validate_run_id(child.name)
        except ValueError:
            continue
        run_dirs.append(child)
    return run_dirs


def _artifact_entries(artifact_index: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not artifact_index:
        return []
    artifacts = artifact_index.get("artifacts")
    if not isinstance(artifacts, list):
        return []
    result: List[Dict[str, Any]] = []
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            continue
        relative_path = artifact.get("relative_path")
        if not isinstance(relative_path, str) or not _is_valid_relative_path(relative_path):
            continue
        result.append(dict(artifact))
    return result


def _run_summary_payload(
    *,
    run_id: str,
    run_dir: Path,
    progress: Optional[Dict[str, Any]],
    artifact_index: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "run_id": run_id,
        "run_dir": str(run_dir),
        "progress_available": progress is not None,
        "artifact_index_available": artifact_index is not None,
        "artifacts_available": bool(_artifact_entries(artifact_index)),
    }
    if progress:
        for key in (
            "schema_name",
            "schema_version",
            "run_kind",
            "source_wing",
            "status",
            "current_phase",
            "current_phase_status",
            "phase_order",
            "phase_attempts",
            "started_at",
            "updated_at",
            "ended_at",
            "elapsed_seconds",
            "current_phase_progress",
            "totals",
            "last_record",
            "warning_count",
            "error_count",
        ):
            summary[key] = progress.get(key)
    else:
        summary["status"] = "missing"
    if artifact_index:
        summary["artifact_index_updated_at"] = artifact_index.get("updated_at")
        summary["artifact_count"] = len(_artifact_entries(artifact_index))
    else:
        summary["artifact_index_updated_at"] = None
        summary["artifact_count"] = 0
    return summary


def _run_detail_payload(
    *,
    run_id: str,
    run_dir: Path,
    progress: Optional[Dict[str, Any]],
    artifact_index: Optional[Dict[str, Any]],
    unresolved_preview: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    artifacts = _artifact_entries(artifact_index)
    return {
        "status": "ok" if progress is not None else "missing",
        "run_id": run_id,
        "run_dir": str(run_dir),
        "progress": progress,
        "artifact_index": artifact_index,
        "artifacts": artifacts,
        "artifact_count": len(artifacts),
        "unresolved_preview": unresolved_preview or [],
    }


def _preview_unresolved_artifact(
    run_dir: Path,
    artifact_index: Optional[Dict[str, Any]],
    *,
    limit: int = _UNRESOLVED_PREVIEW_DEFAULT_LIMIT,
    excerpt_chars: int = _UNRESOLVED_PREVIEW_DEFAULT_EXCERPT_CHARS,
) -> Dict[str, Any]:
    artifacts = _artifact_entries(artifact_index)
    unresolved_entry = next(
        (artifact for artifact in artifacts if artifact.get("relative_path") == "unresolved.jsonl"),
        None,
    )
    if unresolved_entry is None:
        return {
            "status": "missing",
            "run_dir": str(run_dir),
            "artifact": None,
            "preview": [],
            "count": 0,
            "limit": limit,
        }
    if not unresolved_entry.get("dashboard_safe", False):
        return {
            "status": "restricted",
            "run_dir": str(run_dir),
            "artifact": unresolved_entry,
            "preview": [],
            "count": 0,
            "limit": limit,
        }
    if unresolved_entry.get("privacy_level") not in {"summary", "bounded_excerpt"}:
        return {
            "status": "restricted",
            "run_dir": str(run_dir),
            "artifact": unresolved_entry,
            "preview": [],
            "count": 0,
            "limit": limit,
        }

    preview_limit = max(1, min(int(limit), _UNRESOLVED_PREVIEW_MAX_LIMIT))
    records = _tail_jsonl_records(run_dir / "unresolved.jsonl", limit=preview_limit)
    preview: List[Dict[str, Any]] = []
    for record in records:
        candidate_ids = record.get("candidate_ids")
        preview_record = {
            "sequence": record.get("sequence"),
            "recorded_at": record.get("recorded_at"),
            "route_iteration": record.get("route_iteration"),
            "source_drawer_id": record.get("source_drawer_id"),
            "source_wing": record.get("source_wing"),
            "source_room": record.get("source_room"),
            "unresolved_status": record.get("unresolved_status"),
            "reason_code": record.get("reason_code"),
            "reason_detail": _truncate_text(record.get("reason_detail"), excerpt_chars),
            "route_confidence": record.get("route_confidence"),
            "next_action": record.get("next_action"),
            "retryable": record.get("retryable"),
            "source_excerpt": _truncate_text(record.get("source_excerpt"), excerpt_chars),
        }
        if isinstance(candidate_ids, list):
            preview_record["candidate_ids"] = [
                str(candidate_id)
                for candidate_id in candidate_ids[:8]
            ]
            preview_record["candidate_ids_truncated"] = len(candidate_ids) > 8
        preview.append(preview_record)
    return {
        "status": "ok",
        "run_dir": str(run_dir),
        "artifact": unresolved_entry,
        "preview": preview,
        "count": len(preview),
        "limit": preview_limit,
        "truncated": len(records) >= preview_limit,
    }


@dataclass
class MiningStatus:
    active: bool
    active_services: List[Dict[str, str]]
    matched_processes: List[Dict[str, Any]]
    configured_services: List[str]
    configured_process_patterns: List[str]
    detection_errors: List[str]
    forced_telemetry_only: bool = False

    def mode(self) -> str:
        return "telemetry-only" if (self.active or self.forced_telemetry_only) else "idle"

    def to_payload(self) -> Dict[str, Any]:
        return {
            "active": self.active,
            "mode": self.mode(),
            "forced_telemetry_only": self.forced_telemetry_only,
            "active_services": list(self.active_services),
            "matched_processes": list(self.matched_processes),
            "configured_services": list(self.configured_services),
            "configured_process_patterns": list(self.configured_process_patterns),
            "detection_errors": list(self.detection_errors),
        }


class UpstreamClientError(Exception):
    """Raised when the dashboard cannot use the upstream HTTP MCP service."""


class LocalAITelemetryError(Exception):
    """Raised when LocalAI telemetry cannot be collected."""


class DashboardMCPClient:
    """Local/tailnet HTTP client for the upstream MemPalace MCP service."""

    def __init__(
        self,
        base_url: str,
        token: Optional[str] = None,
        timeout: float = 30.0,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        self.base_url = validate_upstream_url(base_url)
        self.token = token
        self.timeout = timeout
        self.opener = opener

    def healthz(self) -> Dict[str, Any]:
        return self._request_json("GET", f"{self.base_url}/healthz")

    def call_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if name not in _READ_ONLY_TOOLS:
            raise UpstreamClientError(f"Refusing non-read-only tool {name!r}")
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments or {}},
        }
        response = self._request_json("POST", f"{self.base_url}/mcp", payload=payload)
        if response is None:
            raise UpstreamClientError("Unexpected empty response from upstream MCP endpoint")
        if "error" in response:
            error = response["error"]
            message = (
                error.get("message", "upstream MCP error")
                if isinstance(error, dict)
                else error
            )
            raise UpstreamClientError(str(message))
        try:
            text = response["result"]["content"][0]["text"]
            return json.loads(text)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise UpstreamClientError(
                "Unexpected tools/call response from upstream MCP endpoint"
            ) from exc

    def _request_json(
        self,
        method: str,
        url: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        body = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = Request(url, data=body, headers=headers, method=method)
        try:
            with self.opener(request, timeout=self.timeout) as response:
                if response.status == 204:
                    return None
                response_body = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise UpstreamClientError(f"HTTP {exc.code} from {url}: {detail}") from exc
        except (URLError, OSError) as exc:
            raise UpstreamClientError(f"Could not reach {url}: {exc}") from exc

        try:
            return json.loads(response_body)
        except json.JSONDecodeError as exc:
            raise UpstreamClientError(f"Invalid JSON response from {url}") from exc


class LocalAITelemetryClient:
    """Bounded local/tailnet client for overview-only LocalAI telemetry."""

    def __init__(
        self,
        base_url: str,
        token: str,
        timeout: float = 2.0,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        self.base_url = validate_localai_url(base_url)
        self.token = token
        self.timeout = timeout
        self.opener = opener

    def summary(self) -> Dict[str, Any]:
        response = self._request_json("GET", f"{self.base_url}/models")
        data = response.get("data")
        model_ids: List[str] = []
        if isinstance(data, list):
            for item in data[:5]:
                if isinstance(item, dict):
                    model_id = item.get("id")
                    if model_id is not None:
                        model_ids.append(str(model_id))
        return {
            "status": "ok",
            "model_count": len(data) if isinstance(data, list) else None,
            "models": model_ids,
        }

    def _request_json(
        self,
        method: str,
        url: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        body = None
        headers = {"Accept": "application/json", "Authorization": f"Bearer {self.token}"}
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = Request(url, data=body, headers=headers, method=method)
        try:
            with self.opener(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8", errors="replace")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise LocalAITelemetryError(f"HTTP {exc.code} from {url}: {detail[:500]}") from exc
        except (URLError, OSError) as exc:
            raise LocalAITelemetryError(f"Could not reach {url}: {exc}") from exc
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LocalAITelemetryError(f"Invalid JSON response from {url}") from exc
        if not isinstance(data, dict):
            raise LocalAITelemetryError(f"Unexpected JSON shape from {url}")
        return data


def _checkpoint_summary(path: Optional[Path]) -> Dict[str, Any]:
    if path is None:
        return {
            "status": "not_configured",
            "detail": "LocalAI checkpoint path is not configured",
        }

    try:
        resolved = path.expanduser()
        stat_result = resolved.stat()
    except FileNotFoundError:
        return {
            "status": "unavailable",
            "path": str(path),
            "detail": f"Checkpoint file not found: {path}",
        }
    except OSError as exc:
        return {
            "status": "unavailable",
            "path": str(path),
            "detail": f"Checkpoint file is not readable: {path}: {exc}",
        }

    if not resolved.is_file():
        return {
            "status": "unavailable",
            "path": str(resolved),
            "detail": f"Checkpoint path is not a file: {resolved}",
        }

    if stat_result.st_size == 0:
        return {
            "status": "empty",
            "path": str(resolved),
            "size_bytes": 0,
            "detail": "Checkpoint file exists but has no rows yet",
        }

    try:
        with resolved.open("rb") as handle:
            start = max(0, stat_result.st_size - _CHECKPOINT_TAIL_BYTES)
            handle.seek(start)
            chunk = handle.read(_CHECKPOINT_TAIL_BYTES)
    except OSError as exc:
        return {
            "status": "unavailable",
            "path": str(resolved),
            "detail": f"Checkpoint file could not be read: {resolved}: {exc}",
        }

    lines = chunk.decode("utf-8", errors="replace").splitlines()
    if start > 0 and lines:
        lines = lines[1:]

    last_row: Optional[Dict[str, Any]] = None
    for line in reversed(lines):
        text = line.strip()
        if not text:
            continue
        try:
            row = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            last_row = row
            break

    payload: Dict[str, Any] = {
        "status": "ok",
        "path": str(resolved),
        "size_bytes": int(stat_result.st_size),
        "tail_bytes_read": min(int(stat_result.st_size), _CHECKPOINT_TAIL_BYTES),
    }
    if last_row is None:
        payload["detail"] = "Checkpoint file is readable but no JSON row was parsed from the bounded tail"
        return payload

    payload["last_status"] = last_row.get("status")
    payload["last_key"] = last_row.get("key")
    payload["last_row"] = {
        key: last_row.get(key)
        for key in ("key", "status", "classified", "timestamp", "ts")
        if key in last_row
    }
    return payload


def _localai_summary() -> Dict[str, Any]:
    url = load_localai_url()
    token = load_localai_token()
    model = load_localai_model()
    payload: Dict[str, Any] = {"configured_model": model}

    if not url:
        payload["status"] = "not_configured"
        payload["detail"] = "LocalAI URL is not configured"
        return payload
    if not token:
        payload["status"] = "not_configured"
        payload["detail"] = "LocalAI token is not configured"
        payload["url"] = url
        return payload

    try:
        client = LocalAITelemetryClient(url, token=token)
    except ValueError as exc:
        payload["status"] = "unavailable"
        payload["detail"] = str(exc)
        payload["url"] = url
        return payload

    payload["url"] = client.base_url
    try:
        payload.update(client.summary())
    except LocalAITelemetryError as exc:
        payload["status"] = "unavailable"
        payload["detail"] = str(exc)
    return payload


def _default_service_state_reader(service: str) -> Dict[str, str]:
    try:
        proc = subprocess.run(
            [
                "systemctl",
                "show",
                service,
                "--property=ActiveState",
                "--property=SubState",
                "--value",
            ],
            capture_output=True,
            check=False,
            text=True,
            timeout=2.0,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError(f"systemctl lookup failed for {service}: {exc}") from exc

    values = [line.strip().lower() for line in proc.stdout.splitlines() if line.strip()]
    active_state = values[0] if values else ""
    sub_state = values[1] if len(values) > 1 else ""
    return {"active_state": active_state, "sub_state": sub_state}


def _default_process_lister() -> List[Dict[str, Any]]:
    try:
        proc = subprocess.run(
            ["ps", "-eo", "pid=,args="],
            capture_output=True,
            check=False,
            text=True,
            timeout=2.0,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError(f"ps lookup failed: {exc}") from exc

    processes: List[Dict[str, Any]] = []
    for raw_line in proc.stdout.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        try:
            pid = int(parts[0])
        except ValueError:
            continue
        processes.append({"pid": pid, "args": parts[1]})
    return processes


class MiningDetector:
    """Determine whether active mining/classification is currently running."""

    def __init__(
        self,
        services: Optional[Sequence[str]] = None,
        process_patterns: Optional[Sequence[str]] = None,
        service_state_reader: Callable[[str], Dict[str, str]] = _default_service_state_reader,
        process_lister: Callable[[], List[Dict[str, Any]]] = _default_process_lister,
    ) -> None:
        self.services = list(
            services
            if services is not None
            else _split_env_list("MEMPALACE_DASHBOARD_MINING_SERVICES", _DEFAULT_MINING_SERVICES)
        )
        pattern_texts = list(
            process_patterns
            if process_patterns is not None
            else _split_env_list(
                "MEMPALACE_DASHBOARD_MINING_PROCESS_PATTERNS",
                _DEFAULT_MINING_PROCESS_PATTERNS,
            )
        )
        self.pattern_texts = pattern_texts
        self.patterns = [re.compile(pattern, re.IGNORECASE) for pattern in pattern_texts]
        self.service_state_reader = service_state_reader
        self.process_lister = process_lister

    def detect(self) -> MiningStatus:
        active_services: List[Dict[str, str]] = []
        matched_processes: List[Dict[str, Any]] = []
        detection_errors: List[str] = []

        for service in self.services:
            try:
                state = self.service_state_reader(service)
            except Exception as exc:  # pragma: no cover - exercised through injection in tests.
                detection_errors.append(str(exc))
                continue
            active_state = state.get("active_state", "").lower()
            sub_state = state.get("sub_state", "").lower()
            if active_state in {"active", "activating", "reloading"} or sub_state == "running":
                active_services.append(
                    {
                        "service": service,
                        "active_state": active_state or "unknown",
                        "sub_state": sub_state or "unknown",
                    }
                )

        try:
            processes = self.process_lister()
        except Exception as exc:  # pragma: no cover - exercised through injection in tests.
            detection_errors.append(str(exc))
            processes = []

        current_pid = os.getpid()
        for process in processes:
            pid = process.get("pid")
            if pid == current_pid:
                continue
            args = str(process.get("args", ""))
            for pattern_text, pattern in zip(self.pattern_texts, self.patterns):
                if pattern.search(args):
                    matched_processes.append({"pid": pid, "args": args, "pattern": pattern_text})
                    break

        return MiningStatus(
            active=bool(active_services or matched_processes),
            active_services=active_services,
            matched_processes=matched_processes,
            configured_services=list(self.services),
            configured_process_patterns=list(self.pattern_texts),
            detection_errors=detection_errors,
        )


def _make_locked_payload(mining: MiningStatus) -> Dict[str, Any]:
    return {
        "status": "locked",
        "mode": "telemetry-only",
        "detail": "Read-heavy dashboard endpoints are disabled while mining is active.",
        "mining": mining.to_payload(),
    }


def _make_upstream_error_payload(detail: str, mining: MiningStatus) -> Dict[str, Any]:
    return {
        "status": "upstream_unavailable",
        "mode": mining.mode(),
        "detail": detail,
        "mining": mining.to_payload(),
    }


def _attach_dashboard_context(payload: Dict[str, Any], mining: MiningStatus) -> Dict[str, Any]:
    response = dict(payload)
    response["mining_active"] = mining.active
    response["mode"] = mining.mode()
    response["mining"] = mining.to_payload()
    return response


def create_app(
    token: Optional[str] = None,
    upstream_client: Optional[DashboardMCPClient] = None,
    mining_detector: Optional[MiningDetector] = None,
    static_dir: Optional[Path] = None,
    ontology_run_root: Optional[Path] = None,
):
    """Create the FastAPI dashboard app."""
    if FastAPI is None or run_in_threadpool is None:
        raise RuntimeError("Install the HTTP server extra: pip install 'mempalace[server]'")

    if token is None:
        token = load_auth_token()
    auth_required_but_missing = token is None

    if mining_detector is None:
        mining_detector = MiningDetector()

    upstream_error: Optional[str] = None
    if upstream_client is None:
        raw_upstream_url = load_upstream_url()
        try:
            upstream_client = DashboardMCPClient(
                base_url=raw_upstream_url,
                token=load_upstream_token(),
            )
        except (UpstreamClientError, ValueError) as exc:
            upstream_error = str(exc)
            upstream_client = None

    if static_dir is None:
        static_dir = _static_dir_from_env()
    static_dir = static_dir.expanduser()
    if ontology_run_root is None:
        ontology_run_root = load_ontology_run_root()
    else:
        ontology_run_root = resolve_run_root(str(ontology_run_root))

    async def require_bearer(authorization: Optional[str] = Header(default=None)):
        if auth_required_but_missing:
            raise HTTPException(
                status_code=503,
                detail=(
                    "MEMPALACE_DASHBOARD_TOKEN or MEMPALACE_DASHBOARD_TOKEN_FILE "
                    "must be set before serving the dashboard"
                ),
            )
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

    async def current_mining_status() -> MiningStatus:
        mining = await run_in_threadpool(mining_detector.detect)
        if _env_flag_enabled("MEMPALACE_DASHBOARD_FORCE_TELEMETRY_ONLY"):
            return MiningStatus(
                active=True,
                active_services=list(mining.active_services),
                matched_processes=list(mining.matched_processes),
                configured_services=list(mining.configured_services),
                configured_process_patterns=list(mining.configured_process_patterns),
                detection_errors=list(mining.detection_errors),
                forced_telemetry_only=True,
            )
        return mining

    async def current_overview(mining: MiningStatus) -> Tuple[int, Dict[str, Any]]:
        localai = await run_in_threadpool(_localai_summary)
        checkpoint = await run_in_threadpool(_checkpoint_summary, load_localai_checkpoint_path())
        payload = {
            "status": "ok",
            "mining_active": mining.active,
            "dashboard": {
                "version": __version__,
                "static_available": bool(
                    static_dir.is_dir() and (static_dir / "index.html").is_file()
                ),
                "upstream_configured": upstream_client is not None and upstream_error is None,
            },
            "telemetry": {
                "mining_active": mining.active,
                "mode": mining.mode(),
                "active_services": list(mining.active_services),
                "matched_processes": list(mining.matched_processes),
            },
            "mining": mining.to_payload(),
            "mode": mining.mode(),
            "localai": localai,
            "localai_status": localai.get("status", "unknown"),
            "checkpoint": checkpoint.get("status", "unknown"),
            "checkpoint_status": checkpoint.get("status", "unknown"),
            "checkpoint_telemetry": checkpoint,
        }
        payload["telemetry"]["localai"] = localai
        payload["telemetry"]["checkpoint"] = payload["checkpoint_status"]
        payload["telemetry"]["checkpoint_info"] = checkpoint
        if upstream_client is None:
            payload["upstream"] = {
                "status": "unavailable",
                "detail": upstream_error or "No upstream MemPalace HTTP endpoint configured",
            }
            return 503, payload
        try:
            upstream = await run_in_threadpool(upstream_client.healthz)
        except UpstreamClientError as exc:
            payload["upstream"] = {"status": "unavailable", "detail": str(exc)}
            return 503, payload
        payload["upstream"] = upstream
        payload["health"] = upstream.get("status", "unknown")
        payload["drawer_count"] = upstream.get("drawer_count")
        payload["embedding_device"] = upstream.get("effective_embedding_device") or upstream.get(
            "configured_embedding_device"
        )
        payload["telemetry"]["health"] = payload["health"]
        payload["telemetry"]["drawer_count"] = payload["drawer_count"]
        payload["telemetry"]["embedding_device"] = payload["embedding_device"]
        return 200, payload

    async def _run_read_only_tool(
        name: str,
        arguments: Optional[Dict[str, Any]],
        mining: MiningStatus,
    ) -> Any:
        if mining.active:
            return JSONResponse(_make_locked_payload(mining), status_code=423)
        if upstream_client is None:
            return JSONResponse(
                _make_upstream_error_payload(
                    upstream_error or "No upstream MemPalace HTTP endpoint configured", mining
                ),
                status_code=503,
            )
        try:
            payload = await run_in_threadpool(upstream_client.call_tool, name, arguments or {})
        except UpstreamClientError as exc:
            return JSONResponse(_make_upstream_error_payload(str(exc), mining), status_code=503)
        return _attach_dashboard_context(payload, mining)

    async def _ontology_run_snapshot(run_id: str) -> Dict[str, Any]:
        try:
            run_dir = _safe_run_dir(ontology_run_root, run_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        progress = _read_json_file(run_dir / "progress.json")
        if progress is not None and progress.get("run_id") not in {None, run_id}:
            raise HTTPException(status_code=409, detail="Run progress payload does not match run_id")
        artifact_index = _read_json_file(run_dir / "artifacts_index.json")
        if artifact_index is not None and artifact_index.get("run_id") not in {None, run_id}:
            raise HTTPException(status_code=409, detail="Artifact index payload does not match run_id")
        return {
            "run_id": run_id,
            "run_dir": run_dir,
            "progress": progress,
            "artifact_index": artifact_index,
        }

    async def _ontology_run_list() -> Dict[str, Any]:
        runs: List[Dict[str, Any]] = []
        for run_dir in _list_run_dirs(ontology_run_root):
            run_id = run_dir.name
            progress = _read_json_file(run_dir / "progress.json")
            artifact_index = _read_json_file(run_dir / "artifacts_index.json")
            runs.append(
                _run_summary_payload(
                    run_id=run_id,
                    run_dir=run_dir,
                    progress=progress,
                    artifact_index=artifact_index,
                )
            )
        runs.sort(
            key=lambda item: (
                item.get("updated_at") or "",
                item.get("started_at") or "",
                item.get("run_id") or "",
            ),
            reverse=True,
        )
        return {
            "status": "ok",
            "run_root": str(ontology_run_root),
            "count": len(runs),
            "runs": runs,
        }

    app = FastAPI(
        title="MemPalace Dashboard",
        version=__version__,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    @app.get("/api/overview", dependencies=[Depends(require_bearer)])
    async def overview(mining: MiningStatus = Depends(current_mining_status)):
        status_code, payload = await current_overview(mining)
        return JSONResponse(payload, status_code=status_code)

    @app.get("/api/taxonomy", dependencies=[Depends(require_bearer)])
    async def taxonomy(mining: MiningStatus = Depends(current_mining_status)):
        return await _run_read_only_tool("mempalace_get_taxonomy", {}, mining)

    @app.get("/api/search", dependencies=[Depends(require_bearer)])
    async def search(
        query: Optional[str] = Query(default=None, min_length=1, max_length=250),
        q: Optional[str] = Query(default=None, min_length=1, max_length=250),
        limit: int = Query(5, ge=1, le=100),
        wing: Optional[str] = Query(default=None),
        room: Optional[str] = Query(default=None),
        max_distance: Optional[float] = Query(default=None, ge=0.0, le=2.0),
        candidate_strategy: Optional[str] = Query(default=None),
        context: Optional[str] = Query(default=None),
        mining: MiningStatus = Depends(current_mining_status),
    ):
        search_query = query or q
        if not search_query:
            raise HTTPException(status_code=422, detail="query or q is required")
        arguments: Dict[str, Any] = {"query": search_query, "limit": limit}
        if wing:
            arguments["wing"] = wing
        if room:
            arguments["room"] = room
        if max_distance is not None:
            arguments["max_distance"] = max_distance
        if candidate_strategy:
            arguments["candidate_strategy"] = candidate_strategy
        if context:
            arguments["context"] = context
        return await _run_read_only_tool("mempalace_search", arguments, mining)

    @app.get("/api/drawers", dependencies=[Depends(require_bearer)])
    async def drawers(
        wing: Optional[str] = Query(default=None),
        room: Optional[str] = Query(default=None),
        limit: int = Query(20, ge=1, le=100),
        offset: int = Query(0, ge=0),
        mining: MiningStatus = Depends(current_mining_status),
    ):
        arguments: Dict[str, Any] = {"limit": limit, "offset": offset}
        if wing:
            arguments["wing"] = wing
        if room:
            arguments["room"] = room
        return await _run_read_only_tool("mempalace_list_drawers", arguments, mining)

    @app.get("/api/drawers/{drawer_id}", dependencies=[Depends(require_bearer)])
    async def drawer_detail(drawer_id: str, mining: MiningStatus = Depends(current_mining_status)):
        return await _run_read_only_tool(
            "mempalace_get_drawer",
            {"drawer_id": drawer_id},
            mining,
        )

    @app.get("/api/ontology/runs", dependencies=[Depends(require_bearer)])
    async def ontology_runs():
        return await _ontology_run_list()

    @app.get("/api/ontology/runs/{run_id}", dependencies=[Depends(require_bearer)])
    async def ontology_run_detail(run_id: str):
        snapshot = await _ontology_run_snapshot(run_id)
        unresolved_preview = _preview_unresolved_artifact(
            snapshot["run_dir"],
            snapshot["artifact_index"],
        )
        return _run_detail_payload(
            run_id=run_id,
            run_dir=snapshot["run_dir"],
            progress=snapshot["progress"],
            artifact_index=snapshot["artifact_index"],
            unresolved_preview=unresolved_preview.get("preview", []),
        )

    @app.get("/api/ontology/runs/{run_id}/artifacts", dependencies=[Depends(require_bearer)])
    async def ontology_run_artifacts(run_id: str):
        snapshot = await _ontology_run_snapshot(run_id)
        artifacts = _artifact_entries(snapshot["artifact_index"])
        return {
            "status": "ok" if snapshot["artifact_index"] is not None else "missing",
            "run_id": run_id,
            "run_dir": str(snapshot["run_dir"]),
            "artifact_index": snapshot["artifact_index"],
            "artifact_count": len(artifacts),
            "artifacts": artifacts,
        }

    @app.get("/api/ontology/runs/{run_id}/unresolved-preview", dependencies=[Depends(require_bearer)])
    async def ontology_run_unresolved_preview(
        run_id: str,
        limit: int = Query(_UNRESOLVED_PREVIEW_DEFAULT_LIMIT, ge=1, le=_UNRESOLVED_PREVIEW_MAX_LIMIT),
        excerpt_chars: int = Query(_UNRESOLVED_PREVIEW_DEFAULT_EXCERPT_CHARS, ge=16, le=2000),
    ):
        snapshot = await _ontology_run_snapshot(run_id)
        preview = _preview_unresolved_artifact(
            snapshot["run_dir"],
            snapshot["artifact_index"],
            limit=limit,
            excerpt_chars=excerpt_chars,
        )
        preview["run_id"] = run_id
        return preview

    if static_dir.is_dir() and (static_dir / "index.html").is_file():
        static_files = StaticFiles(directory=str(static_dir), html=False)
        index_file = static_dir / "index.html"

        @app.get("/")
        async def root():
            return FileResponse(index_file)

        @app.get("/{path:path}")
        async def dashboard_static(path: str, request: FastAPIRequest):
            if not path or path.startswith("api/"):
                raise HTTPException(status_code=404, detail="Not found")
            response = await static_files.get_response(path, request.scope)
            if getattr(response, "status_code", None) == 404 and "." not in Path(path).name:
                return FileResponse(index_file)
            return response
    else:

        @app.get("/", response_class=HTMLResponse)
        async def root():
            return """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>MemPalace Dashboard</title>
  </head>
  <body>
    <h1>MemPalace Dashboard</h1>
    <p>Static dashboard assets are not packaged in this build yet.</p>
    <p>Use <code>/api/overview</code> for telemetry.</p>
  </body>
</html>
"""

    return app


app = create_app()


def _parse_args(argv: Optional[Sequence[str]] = None):
    parser = argparse.ArgumentParser(description="Serve the MemPalace dashboard backend")
    parser.add_argument(
        "--host",
        default=os.environ.get("MEMPALACE_DASHBOARD_HOST", "127.0.0.1"),
        help="Host interface to bind (default: %(default)s)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("MEMPALACE_DASHBOARD_PORT", "8766")),
        help="Port to bind (default: %(default)s)",
    )
    parser.add_argument(
        "--static-dir",
        metavar="PATH",
        help="Optional directory containing dashboard static assets",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = _parse_args(argv)
    token = load_auth_token()
    if token is None:
        raise SystemExit(
            "Refusing to serve without MEMPALACE_DASHBOARD_TOKEN "
            "or MEMPALACE_DASHBOARD_TOKEN_FILE"
        )

    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover - missing optional dependency.
        raise SystemExit("Install the HTTP server extra: pip install 'mempalace[server]'") from exc

    static_dir = Path(args.static_dir).expanduser() if args.static_dir else None
    uvicorn.run(
        create_app(token=token, static_dir=static_dir),
        host=args.host,
        port=args.port,
    )


if __name__ == "__main__":
    main()
