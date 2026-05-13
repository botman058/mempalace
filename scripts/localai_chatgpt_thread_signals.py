#!/usr/bin/env python3
"""Segment-level ChatGPT thread signal extraction with progressive checkpoints."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from mempalace import chatgpt_archive_atlas_contract as atlas_contract
from mempalace import chatgpt_atlas_guided_contract as guided_contract
from mempalace import chatgpt_atlas_guided_prompt as guided_prompt
from mempalace import chatgpt_atlas_guided_reconciliation as guided_reconciliation
from mempalace.chatgpt_thread_segments import ChatGPTThreadSegment, build_chatgpt_thread_segments

DEFAULT_SOURCE_DIR = "/media/u0/OneDrive_Backup/mempalace/sources/chatgpt"
DEFAULT_RUN_DIR = "/media/u0/OneDrive_Backup/mempalace/data/localai_chatgpt_thread_signals"
DEFAULT_ATLAS_GUIDED_RUN_DIR = "/media/u0/OneDrive_Backup/mempalace/data/atlas_guided_chatgpt_signals"
_BLOCKED_ATLAS_GUIDED_RUN_DIR_ROOT = "/media/u0/Extreme SSD"
DEFAULT_MEMPALACE_URL = "http://100.112.179.49:8765"
DEFAULT_MEMPALACE_TOKEN_FILE = "/media/u0/OneDrive_Backup/mempalace/secrets/http_token"
DEFAULT_LOCALAI_BASE_URL = "http://snow-white-iii:8080/v1"
DEFAULT_LOCALAI_TOKEN_FILE = "/media/u0/OneDrive_Backup/mempalace/secrets/localai_token"
DEFAULT_MODEL = "qwen3-vl-8b-instruct"
EXTRACTION_VERSION = "localai_chatgpt_thread_signals_v1"
ATLAS_GUIDED_EXTRACTION_VERSION = "atlas_guided_chatgpt_thread_signals_v1"
_MAX_EVIDENCE_CHARS = 280
_MAX_INVALID_EXCERPT_CHARS = 500
_MAX_SEGMENT_EXCERPT_CHARS = 320
_MAX_RECON_EVIDENCE = 3
_MAX_MCP_METADATA_CHARS = 128
_ATLAS_GUIDED_PHASE_ORDER = ("load_inputs", "extract", "finalize")
_PROVIDER_BLOCKLIST = (
    "api.openai.com",
    "anthropic.com",
    "openrouter.ai",
    "together.xyz",
    "groq.com",
    "generativelanguage.googleapis.com",
    "vertexai.googleapis.com",
)
_ATLAS_GUIDED_ALLOWED_LOCALAI_BASE_URLS = (
    "http://snow-white-iii:8080/v1",
    "http://snow-white-iii.local:8080/v1",
)
_ATLAS_GUIDED_ALLOWED_LOCALAI_HOSTS = {"snow-white-iii", "snow-white-iii.local"}


class FatalRemoteError(RuntimeError):
    """Raised when extraction cannot safely continue."""


class SegmentProvider(Protocol):
    def classify_segment(self, *, prompt_messages: list[dict[str, str]]) -> str: ...


class MCPCaller(Protocol):
    def call_tool(
        self, *, tool_name: str, arguments: dict[str, Any], timeout: float
    ) -> dict[str, Any]: ...


def read_token(value: str | None, path: str | None, label: str) -> str:
    if value and value.strip():
        return value.strip()
    if path:
        try:
            token = Path(path).expanduser().read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise FatalRemoteError(f"{label} token file is not readable: {path}: {exc}") from exc
        if token:
            return token
    raise FatalRemoteError(f"{label} token is required")


def ensure_localai_base_url(base_url: str) -> str:
    value = base_url.strip().rstrip("/")
    if not value:
        raise FatalRemoteError("LocalAI base URL is required")
    lowered = value.lower()
    for blocked in _PROVIDER_BLOCKLIST:
        if blocked in lowered:
            raise FatalRemoteError(f"Refusing non-local LocalAI provider URL: {blocked}")
    return value


def ensure_atlas_guided_localai_base_url(base_url: str) -> str:
    value = ensure_localai_base_url(base_url)
    parsed = urlsplit(value)
    try:
        port = parsed.port
    except ValueError as exc:
        raise FatalRemoteError(f"Invalid LocalAI base URL: {value}") from exc
    if (
        parsed.scheme.lower() != "http"
        or parsed.hostname is None
        or parsed.hostname.lower() not in _ATLAS_GUIDED_ALLOWED_LOCALAI_HOSTS
        or parsed.username is not None
        or parsed.password is not None
        or port != 8080
        or parsed.path != "/v1"
        or parsed.query
        or parsed.fragment
    ):
        allowed = " or ".join(_ATLAS_GUIDED_ALLOWED_LOCALAI_BASE_URLS)
        raise FatalRemoteError(
            f"Atlas-guided LocalAI base URL must target snow-white-iii: {allowed}"
        )
    return value


def _post_json(url: str, payload: dict[str, Any], token: str, timeout: float) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise FatalRemoteError(f"HTTP {exc.code} from {url}: {detail[:1000]}") from exc
    except (OSError, URLError) as exc:
        raise FatalRemoteError(f"Could not reach {url}: {exc}") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise FatalRemoteError(f"Invalid JSON from {url}: {raw[:1000]}") from exc
    if not isinstance(data, dict):
        raise FatalRemoteError(f"Unexpected response shape from {url}")
    return data


class HttpMCPCaller:
    def __init__(self, *, base_url: str, token: str) -> None:
        self.base_url = base_url
        self.token = token

    def call_tool(
        self, *, tool_name: str, arguments: dict[str, Any], timeout: float
    ) -> dict[str, Any]:
        endpoint = self.base_url.rstrip("/")
        if not endpoint.endswith("/mcp"):
            endpoint = f"{endpoint}/mcp"
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }
        data = _post_json(endpoint, payload, self.token, timeout)
        if data.get("error"):
            raise FatalRemoteError(f"MemPalace MCP error from {tool_name}: {data['error']}")
        try:
            text = data["result"]["content"][0]["text"]
            result = json.loads(text)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise FatalRemoteError(f"Unexpected MCP response from {tool_name}: {data}") from exc
        if not isinstance(result, dict):
            raise FatalRemoteError(f"Unexpected MCP result from {tool_name}: {result}")
        return result


class HttpSegmentProvider:
    def __init__(self, *, base_url: str, token: str, model: str, timeout: float) -> None:
        self.base_url = base_url
        self.token = token
        self.model = model
        self.timeout = timeout

    def classify_segment(self, *, prompt_messages: list[dict[str, str]]) -> str:
        payload = {
            "model": self.model,
            "messages": prompt_messages,
            "temperature": 0.1,
            "max_tokens": 1400,
            "response_format": {"type": "json_object"},
        }
        data = _post_json(f"{self.base_url}/chat/completions", payload, self.token, self.timeout)
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise FatalRemoteError(f"Unexpected LocalAI response shape: {data}") from exc
        if not isinstance(content, str) or not content.strip():
            raise FatalRemoteError("LocalAI returned empty content")
        return content


def _strip_json_fence(value: str) -> str:
    text = value.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _parse_segment_output(raw_text: str) -> dict[str, Any]:
    try:
        obj = json.loads(_strip_json_fence(raw_text))
    except json.JSONDecodeError as exc:
        raise ValueError("invalid_json") from exc
    if not isinstance(obj, dict):
        raise ValueError("invalid_shape")
    summary = obj.get("summary")
    if not isinstance(summary, str):
        raise ValueError("invalid_summary")
    items = obj.get("items")
    if not isinstance(items, list):
        raise ValueError("invalid_items")
    normalized_items: list[dict[str, Any]] = []
    for item in items[:8]:
        if not isinstance(item, dict):
            raise ValueError("invalid_item_shape")
        item_type = item.get("type")
        text = item.get("text")
        if not isinstance(item_type, str) or not item_type.strip():
            raise ValueError("invalid_item_type")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("invalid_item_text")
        evidence = item.get("evidence")
        if not isinstance(evidence, str):
            evidence = ""
        importance = item.get("importance", 3)
        try:
            importance_int = max(1, min(5, int(importance)))
        except (TypeError, ValueError):
            importance_int = 3
        normalized_items.append(
            {
                "type": item_type.strip(),
                "text": text.strip(),
                "importance": importance_int,
                "evidence": evidence.strip()[:_MAX_EVIDENCE_CHARS],
            }
        )
    return {"summary": summary.strip(), "items": normalized_items}


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
        handle.flush()


def _write_progress(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(row, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _text_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _atlas_run_id_from_dir(run_dir: Path) -> str:
    raw = re.sub(r"[^A-Za-z0-9_.-]+", "_", run_dir.name).strip("._-")
    if not raw:
        raw = f"atlas_guided_{_text_digest(str(run_dir.resolve()))}"
    if not re.match(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$", raw):
        raw = f"atlas_guided_{_text_digest(raw)}"
    return raw[:96]


def _default_atlas_guided_run_dir(atlas_run_dir_value: str | None) -> Path:
    raw_source = str(atlas_run_dir_value or "").strip()
    if raw_source:
        expanded = Path(raw_source).expanduser()
        slug_source = expanded.name or raw_source
        digest_source = str(expanded)
    else:
        slug_source = "atlas_guided"
        digest_source = DEFAULT_ATLAS_GUIDED_RUN_DIR
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", slug_source).strip("._-")
    if not slug:
        slug = "atlas_guided"
    child_name = f"{slug}_{_text_digest(digest_source)}"
    return Path(DEFAULT_ATLAS_GUIDED_RUN_DIR) / child_name


def _resolve_path_for_guard(path_value: str) -> Path:
    return Path(path_value).expanduser().resolve(strict=False)


def _validate_atlas_guided_cli_run_dir(run_dir_value: str) -> None:
    resolved_run_dir = _resolve_path_for_guard(run_dir_value)
    atlas_root = _resolve_path_for_guard(DEFAULT_ATLAS_GUIDED_RUN_DIR)
    blocked_root = _resolve_path_for_guard(_BLOCKED_ATLAS_GUIDED_RUN_DIR_ROOT)

    if resolved_run_dir == blocked_root or blocked_root in resolved_run_dir.parents:
        raise FatalRemoteError(
            f"Atlas-guided --run-dir must not use {_BLOCKED_ATLAS_GUIDED_RUN_DIR_ROOT}"
        )
    if resolved_run_dir == atlas_root:
        raise FatalRemoteError(
            "Atlas-guided --run-dir must use a child directory under "
            f"{DEFAULT_ATLAS_GUIDED_RUN_DIR}"
        )
    if atlas_root not in resolved_run_dir.parents:
        raise FatalRemoteError(
            "Atlas-guided --run-dir must resolve under "
            f"{DEFAULT_ATLAS_GUIDED_RUN_DIR}"
        )


def _normalize_room(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    room = re.sub(r"[^a-z0-9_]+", "_", value.strip().lower()).strip("_")
    return room


def _canonical_item_text(value: str) -> str:
    lowered = value.lower()
    lowered = re.sub(r"\s+", " ", lowered).strip()
    lowered = re.sub(r"[^a-z0-9 ]+", "", lowered)
    return lowered


def _content_body(*, room: str, item_type: str, text: str, importance: int, evidence: list[str]) -> str:
    lines = [
        "LOCALAI_THREAD_SIGNAL",
        f"room: {room}",
        f"item_type: {item_type}",
        f"importance: {importance}",
        "",
        text,
    ]
    if evidence:
        lines.append("")
        lines.append("evidence:")
        lines.extend([f"- {item}" for item in evidence])
    return "\n".join(lines)


def _load_jsonl_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _load_strict_jsonl_object_rows(
    path: Path,
    *,
    label: str,
    required: bool,
) -> list[dict[str, Any]]:
    if not path.exists():
        if required:
            raise FatalRemoteError(f"{label} is required: {path}")
        return []
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise FatalRemoteError(
                        f"{label} has invalid JSONL row at {path}:{line_number}: {exc}"
                    ) from exc
                if not isinstance(row, dict):
                    raise FatalRemoteError(
                        f"{label} row at {path}:{line_number} must be a JSON object"
                    )
                rows.append(row)
    except OSError as exc:
        raise FatalRemoteError(f"{label} is not readable: {path}: {exc}") from exc
    return rows


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _load_publish_checkpoint(path: Path) -> dict[str, str]:
    seen: dict[str, str] = {}
    for row in _load_jsonl_rows(path):
        source_signal_id = row.get("source_signal_id")
        status = row.get("status")
        if isinstance(source_signal_id, str) and isinstance(status, str):
            seen[source_signal_id] = status
    return seen


def _serialize_segment_ref(segment_refs: list[Any]) -> str:
    if not segment_refs:
        return ""
    first = segment_refs[0]
    if isinstance(first, dict):
        segment_id = str(first.get("segment_id") or "").strip()
        segment_index = first.get("segment_index")
        char_start = first.get("char_start")
        char_end = first.get("char_end")
        parts = []
        if segment_id:
            parts.append(f"segment_id:{segment_id}")
        if isinstance(segment_index, int):
            parts.append(f"segment_index:{segment_index}")
        if isinstance(char_start, int) and isinstance(char_end, int):
            parts.append(f"chars:{char_start}-{char_end}")
        value = "|".join(parts)
        return value[:_MAX_MCP_METADATA_CHARS]
    if isinstance(first, str):
        return first.strip()[:_MAX_MCP_METADATA_CHARS]
    return str(first)[:_MAX_MCP_METADATA_CHARS]


def _metadata_str(value: Any, *, fallback: str = "") -> str:
    if value is None:
        text = fallback
    else:
        text = str(value)
    return text.strip()[:_MAX_MCP_METADATA_CHARS]


def reconcile_segment_extractions(*, run_dir: Path, model: str) -> dict[str, int]:
    extracted_path = run_dir / "segment_extractions.jsonl"
    reconciled_path = run_dir / "reconciled_signals.jsonl"
    rows = _load_jsonl_rows(extracted_path)
    by_group: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        if row.get("status") != "classified":
            continue
        logical_source_id = row.get("logical_source_id")
        source_hash = row.get("source_hash")
        subthread_id = row.get("subthread_id")
        if not all(isinstance(v, str) and v for v in (logical_source_id, source_hash, subthread_id)):
            continue
        by_group.setdefault((logical_source_id, source_hash, subthread_id), []).append(row)

    final_rows: list[dict[str, Any]] = []
    for (logical_source_id, source_hash, subthread_id), group in sorted(by_group.items()):
        group = sorted(group, key=lambda r: (int(r.get("segment_index", 0)), str(r.get("segment_id", ""))))
        item_bucket: dict[str, dict[str, Any]] = {}
        for segment in group:
            items = segment.get("items")
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                text = item.get("text")
                if not isinstance(text, str) or not text.strip():
                    continue
                canonical_text = _canonical_item_text(text)
                if not canonical_text:
                    continue
                item_type = str(item.get("type") or "fact").strip().lower() or "fact"
                key = f"{item_type}|{canonical_text}"
                entry = item_bucket.get(key)
                evidence_text = str(item.get("evidence") or "").strip()[:_MAX_EVIDENCE_CHARS]
                room = _normalize_room(item.get("room"))
                if not room:
                    sub_label = _normalize_room(segment.get("subthread_label"))
                    room = _normalize_room(item_type) or sub_label or "general"
                if entry is None:
                    importance = item.get("importance", 3)
                    try:
                        importance_int = max(1, min(5, int(importance)))
                    except (TypeError, ValueError):
                        importance_int = 3
                    entry = {
                        "room": room,
                        "item_type": item_type,
                        "text": text.strip(),
                        "importance": importance_int,
                        "segment_ids": set(),
                        "segment_refs": [],
                        "evidence": [],
                    }
                    item_bucket[key] = entry
                importance_update = item.get("importance", 3)
                try:
                    importance_int_update = max(1, min(5, int(importance_update)))
                except (TypeError, ValueError):
                    importance_int_update = 3
                entry["segment_ids"].add(str(segment.get("segment_id") or ""))
                entry["segment_refs"].append(
                    {
                        "segment_id": str(segment.get("segment_id") or ""),
                        "segment_index": int(segment.get("segment_index", 0)),
                        "char_start": int(segment.get("char_start", 0)),
                        "char_end": int(segment.get("char_end", 0)),
                    }
                )
                if evidence_text and evidence_text not in entry["evidence"] and len(entry["evidence"]) < _MAX_RECON_EVIDENCE:
                    entry["evidence"].append(evidence_text)
                if len(text.strip()) > len(entry["text"]):
                    entry["text"] = text.strip()
                entry["importance"] = max(entry["importance"], importance_int_update)

        for item_key, entry in sorted(item_bucket.items()):
            first = group[0]
            segment_ids = sorted([sid for sid in entry["segment_ids"] if sid])
            signal_basis = "|".join([logical_source_id, source_hash, subthread_id, item_key])
            source_signal_id = f"srcsig:{_text_digest(signal_basis)}"
            final_rows.append(
                {
                    "source_signal_id": source_signal_id,
                    "room": entry["room"],
                    "content": _content_body(
                        room=entry["room"],
                        item_type=entry["item_type"],
                        text=entry["text"],
                        importance=entry["importance"],
                        evidence=entry["evidence"],
                    ),
                    "logical_source_id": logical_source_id,
                    "source_hash": source_hash,
                    "conversation_id": first.get("conversation_id"),
                    "conversation_title": first.get("conversation_title") or "",
                    "subthread_id": subthread_id,
                    "subthread_label": first.get("subthread_label") or "",
                    "segment_ids": segment_ids,
                    "segment_refs": sorted(entry["segment_refs"], key=lambda r: (r["segment_index"], r["segment_id"])),
                    "evidence": entry["evidence"],
                    "extraction_version": first.get("extraction_version") or EXTRACTION_VERSION,
                    "model": model,
                }
            )

    reconciled_path.parent.mkdir(parents=True, exist_ok=True)
    with reconciled_path.open("w", encoding="utf-8") as handle:
        for row in sorted(final_rows, key=lambda r: r["source_signal_id"]):
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")

    return {
        "reconciled_groups": len(by_group),
        "reconciled_signals": len(final_rows),
        "reconciled_source_rows": len(rows),
    }


def publish_reconciled_signals(
    *,
    run_dir: Path,
    wing: str,
    added_by: str,
    mcp_timeout: float,
    mcp_caller: MCPCaller,
    publish_limit: int = 0,
) -> dict[str, int]:
    reconciled_path = run_dir / "reconciled_signals.jsonl"
    checkpoint_path = run_dir / "publish_checkpoint.jsonl"
    rows = _load_jsonl_rows(reconciled_path)
    seen = _load_publish_checkpoint(checkpoint_path)
    published = 0
    skipped = 0
    failed = 0
    attempted = 0
    for row in rows:
        source_signal_id = row.get("source_signal_id")
        if not isinstance(source_signal_id, str) or not source_signal_id:
            continue
        if seen.get(source_signal_id) in {"success", "noop_success"}:
            skipped += 1
            continue
        if publish_limit and attempted >= publish_limit:
            break
        attempted += 1
        evidence = row.get("evidence")
        segment_refs = row.get("segment_refs")
        segment_ids = row.get("segment_ids")
        if not isinstance(evidence, list):
            evidence = []
        if not isinstance(segment_refs, list):
            segment_refs = []
        if not isinstance(segment_ids, list):
            segment_ids = []
        room = _normalize_room(row.get("room")) or "general"
        arguments = {
            "wing": wing,
            "room": room,
            "content": row.get("content") or "",
            "source_signal_id": _metadata_str(source_signal_id),
            "logical_source_id": _metadata_str(row.get("logical_source_id")),
            "source_hash": _metadata_str(row.get("source_hash")),
            "conversation_id": _metadata_str(row.get("conversation_id")),
            "conversation_title": _metadata_str(row.get("conversation_title")),
            "subthread_id": _metadata_str(row.get("subthread_id")),
            "subthread_label": _metadata_str(row.get("subthread_label")),
            "segment_ids": segment_ids[:48],
            "segment_ref": _serialize_segment_ref(segment_refs),
            "evidence_excerpt": _metadata_str(evidence[0] if evidence else ""),
            "extraction_version": _metadata_str(row.get("extraction_version") or EXTRACTION_VERSION),
            "added_by": _metadata_str(added_by, fallback="localai_chatgpt_thread_signals"),
        }
        status = "failed"
        result_payload: dict[str, Any] = {}
        error_code = ""
        try:
            result = mcp_caller.call_tool(
                tool_name="mempalace_add_signal_drawer",
                arguments=arguments,
                timeout=mcp_timeout,
            )
            result_payload = result
            if result.get("success"):
                noop = bool(result.get("noop"))
                status = "noop_success" if noop else "success"
                published += 1
            else:
                status = "failed"
                error_code = str(result.get("error") or "mcp_result_error")
                failed += 1
        except Exception as exc:
            status = "failed"
            failed += 1
            error_code = str(exc)[:_MAX_INVALID_EXCERPT_CHARS]
        _append_jsonl(
            checkpoint_path,
            {
                "source_signal_id": source_signal_id,
                "status": status,
                "wing": wing,
                "error": error_code,
                "result": result_payload,
            },
        )
        seen[source_signal_id] = status

    return {
        "publish_attempted": attempted,
        "publish_success": published,
        "publish_failed": failed,
        "publish_skipped": skipped,
    }


def _reconciled_stats_from_existing(run_dir: Path) -> dict[str, int]:
    rows = _load_jsonl_rows(run_dir / "reconciled_signals.jsonl")
    groups: set[tuple[str, str, str]] = set()
    for row in rows:
        logical_source_id = row.get("logical_source_id")
        source_hash = row.get("source_hash")
        subthread_id = row.get("subthread_id")
        if isinstance(logical_source_id, str) and isinstance(source_hash, str) and isinstance(subthread_id, str):
            groups.add((logical_source_id, source_hash, subthread_id))
    return {
        "reconciled_groups": len(groups),
        "reconciled_signals": len(rows),
        "reconciled_source_rows": len(_load_jsonl_rows(run_dir / "segment_extractions.jsonl")),
    }


def _load_required_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise FatalRemoteError(f"{label} is required: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FatalRemoteError(f"{label} is not valid JSON: {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise FatalRemoteError(f"{label} must be a JSON object: {path}")
    return raw


def _load_required_jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    return _load_strict_jsonl_object_rows(path, label=label, required=True)


def _load_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FatalRemoteError(f"Optional JSON artifact is invalid: {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise FatalRemoteError(f"Optional JSON artifact must be a JSON object: {path}")
    return raw


def _load_optional_jsonl(path: Path) -> list[dict[str, Any]]:
    return _load_strict_jsonl_object_rows(path, label="Optional JSONL artifact", required=False)


def _normalize_guided_row_for_run(
    row: dict[str, Any],
    *,
    schema_name: str,
    run_id: str,
) -> dict[str, Any]:
    copied = dict(row)
    copied["run_id"] = run_id
    return guided_contract.validate_row(schema_name, copied)


def _write_jsonl_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def _load_atlas_guided_inputs(
    *,
    run_id: str,
    atlas_run_dir: Path,
    candidate_records_path: Path | None,
) -> dict[str, Any]:
    candidate_path = candidate_records_path or (
        atlas_run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["candidate_bridge_records"]
    )
    lookup_path = atlas_run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["atlas_thread_candidates"]
    coverage_path = atlas_run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["atlas_candidate_coverage"]
    thread_index_path = atlas_run_dir / "thread_index.jsonl"

    raw_candidate_rows = _load_required_jsonl(candidate_path, "atlas candidate bridge records")
    raw_lookup_rows = _load_required_jsonl(lookup_path, "atlas thread candidate lookup")
    raw_thread_rows = _load_optional_jsonl(thread_index_path)
    raw_coverage = _load_optional_json(coverage_path)

    candidate_rows: list[dict[str, Any]] = []
    lookup_rows: list[dict[str, Any]] = []
    thread_rows: list[dict[str, Any]] = []
    seen_atlas_run_ids: set[str] = set()

    for row in raw_candidate_rows:
        validated = guided_contract.validate_row(guided_contract.CANDIDATE_BRIDGE_RECORD_SCHEMA, row)
        seen_atlas_run_ids.add(str(validated["atlas_run_id"]))
        candidate_rows.append(
            _normalize_guided_row_for_run(
                validated,
                schema_name=guided_contract.CANDIDATE_BRIDGE_RECORD_SCHEMA,
                run_id=run_id,
            )
        )

    for row in raw_lookup_rows:
        validated = guided_contract.validate_row(guided_contract.THREAD_CANDIDATE_LOOKUP_SCHEMA, row)
        seen_atlas_run_ids.add(str(validated["atlas_run_id"]))
        lookup_rows.append(
            _normalize_guided_row_for_run(
                validated,
                schema_name=guided_contract.THREAD_CANDIDATE_LOOKUP_SCHEMA,
                run_id=run_id,
            )
        )

    for row in raw_thread_rows:
        validated = atlas_contract.validate_row(atlas_contract.THREAD_INDEX_SCHEMA, row)
        seen_atlas_run_ids.add(str(validated["run_id"]))
        thread_rows.append(validated)

    if not seen_atlas_run_ids:
        raise FatalRemoteError(f"Could not resolve atlas_run_id from {atlas_run_dir}")
    if len(seen_atlas_run_ids) != 1:
        raise FatalRemoteError(
            f"Atlas-guided inputs must share one atlas_run_id, got {sorted(seen_atlas_run_ids)}"
        )
    atlas_run_id = next(iter(seen_atlas_run_ids))

    if raw_coverage is not None:
        validated_coverage = guided_contract.validate_row(
            guided_contract.CANDIDATE_COVERAGE_REPORT_SCHEMA,
            raw_coverage,
        )
        if str(validated_coverage["atlas_run_id"]) != atlas_run_id:
            raise FatalRemoteError("atlas candidate coverage report atlas_run_id does not match inputs")
        coverage_row = _normalize_guided_row_for_run(
            validated_coverage,
            schema_name=guided_contract.CANDIDATE_COVERAGE_REPORT_SCHEMA,
            run_id=run_id,
        )
    else:
        lookup_statuses = [str(row.get("lookup_status") or "") for row in lookup_rows]
        mapped_threads = sum(1 for status in lookup_statuses if status == "mapped")
        mixed_threads = sum(1 for status in lookup_statuses if status == "mixed")
        noise_threads = sum(1 for status in lookup_statuses if status == "noise")
        unmapped_threads = sum(1 for status in lookup_statuses if status == "unmapped")
        coverage_row = guided_contract.build_candidate_coverage_report(
            run_id=run_id,
            atlas_run_id=atlas_run_id,
            status="needs_review" if mixed_threads or noise_threads or unmapped_threads else "complete",
            total_threads=len(lookup_rows),
            mapped_threads=mapped_threads,
            mixed_threads=mixed_threads,
            noise_threads=noise_threads,
            unmapped_threads=unmapped_threads,
            candidate_count=len(
                {str(row["candidate_id"]) for row in candidate_rows if row.get("candidate_id")}
            ),
            cluster_count=len({str(row["atlas_cluster_id"]) for row in candidate_rows}),
            duplicate_thread_refs=[],
            missing_thread_refs=[],
            counts={"lookup_rows": len(lookup_rows), "candidate_bridge_records": len(candidate_rows)},
        )

    lookup_by_thread_id: dict[str, dict[str, Any]] = {}
    for row in lookup_rows:
        lookup_by_thread_id[str(row["thread_id"])] = row

    thread_rows_by_logical_source: dict[str, list[dict[str, Any]]] = {}
    for index, row in enumerate(thread_rows, start=1):
        thread_rows_by_logical_source.setdefault(str(row["logical_source_id"]), []).append(
            {
                "thread_id": str(row["thread_id"]),
                "logical_source_id": str(row["logical_source_id"]),
                "conversation_id": row.get("conversation_id"),
                "source_hash": str(row["source_hash"]),
                "thread_index": int(row["thread_index"]),
                "message_start_index": int(row["message_start_index"]),
                "message_end_index": int(row["message_end_index"]),
                "char_start": int(row["char_start"]),
                "char_end": int(row["char_end"]),
                "source_thread_ref": f"thread_index.jsonl#{index}",
            }
        )
    for rows in thread_rows_by_logical_source.values():
        rows.sort(
            key=lambda row: (
                row["message_start_index"],
                row["char_start"],
                row["thread_index"],
                row["thread_id"],
            )
        )

    return {
        "atlas_run_id": atlas_run_id,
        "candidate_rows": candidate_rows,
        "lookup_rows": lookup_rows,
        "lookup_by_thread_id": lookup_by_thread_id,
        "coverage_row": coverage_row,
        "thread_rows_by_logical_source": thread_rows_by_logical_source,
    }


def _overlap_size(start_a: int, end_a: int, start_b: int, end_b: int) -> int:
    return max(0, min(end_a, end_b) - max(start_a, start_b) + 1)


def _select_thread_lookup_for_segment(
    *,
    segment: ChatGPTThreadSegment,
    atlas_inputs: dict[str, Any],
    run_id: str,
) -> tuple[dict[str, Any], str | None]:
    candidate_threads = list(
        atlas_inputs["thread_rows_by_logical_source"].get(segment.logical_source_id, [])
    )
    matching_threads = [
        row
        for row in candidate_threads
        if row["source_hash"] == segment.source_hash
        and (
            row["conversation_id"] is None
            or segment.conversation_id is None
            or row["conversation_id"] == segment.conversation_id
        )
    ]
    if matching_threads:
        candidate_threads = matching_threads

    if not candidate_threads and len(atlas_inputs["lookup_rows"]) == 1:
        only_row = atlas_inputs["lookup_rows"][0]
        return only_row, str(only_row["thread_id"])

    best_thread: dict[str, Any] | None = None
    best_score: tuple[int, int, int, int] | None = None
    for row in candidate_threads:
        message_overlap = _overlap_size(
            segment.message_start_index,
            segment.message_end_index,
            row["message_start_index"],
            row["message_end_index"],
        )
        char_overlap = _overlap_size(
            segment.char_start,
            max(segment.char_end - 1, segment.char_start),
            row["char_start"],
            max(row["char_end"] - 1, row["char_start"]),
        )
        exact_identity = int(
            row["source_hash"] == segment.source_hash
            and (
                row["conversation_id"] is None
                or segment.conversation_id is None
                or row["conversation_id"] == segment.conversation_id
            )
        )
        score = (message_overlap, char_overlap, exact_identity, -row["thread_index"])
        if best_score is None or score > best_score:
            best_score = score
            best_thread = row

    if best_thread is not None and (
        best_score is not None and (best_score[0] > 0 or best_score[1] > 0 or len(candidate_threads) == 1)
    ):
        lookup_row = atlas_inputs["lookup_by_thread_id"].get(best_thread["thread_id"])
        if lookup_row is None:
            return (
                guided_contract.build_thread_candidate_record(
                    run_id=run_id,
                    atlas_run_id=str(atlas_inputs["atlas_run_id"]),
                    thread_id=best_thread["thread_id"],
                    lookup_status="unmapped",
                    candidate_ids=[],
                    candidate_keys=[],
                    cluster_ids=[],
                    primary_candidate_id=None,
                    primary_candidate_key=None,
                    reason_codes=["lookup_row_missing"],
                    source_thread_ref=best_thread["source_thread_ref"],
                ),
                best_thread["thread_id"],
            )
        return lookup_row, best_thread["thread_id"]

    synthetic_thread_id = f"{segment.logical_source_id}:atlas_unmapped:{segment.segment_id}"
    return (
        guided_contract.build_thread_candidate_record(
            run_id=run_id,
            atlas_run_id=str(atlas_inputs["atlas_run_id"]),
            thread_id=synthetic_thread_id,
            lookup_status="unmapped",
            candidate_ids=[],
            candidate_keys=[],
            cluster_ids=[],
            primary_candidate_id=None,
            primary_candidate_key=None,
            reason_codes=["atlas_thread_match_missing"],
            source_thread_ref=None,
        ),
        None,
    )


def _atlas_counts_snapshot(
    *,
    candidate_rows: list[dict[str, Any]],
    lookup_rows: list[dict[str, Any]],
    extraction_rows: list[dict[str, Any]],
    invalid_rows: list[dict[str, Any]],
    coverage_rows: int,
    source_file_errors: int,
    processed_this_run: int,
    skipped_this_run: int,
    mapped_segments: int,
    synthetic_unmapped_segments: int,
    source_files_total: int,
    source_files_processed: int,
    reconciliation_stats: dict[str, int] | None = None,
) -> dict[str, int]:
    counts: dict[str, int] = {
        "candidate_bridge_records": len(candidate_rows),
        "atlas_thread_candidates": len(lookup_rows),
        "atlas_candidate_coverage": coverage_rows,
        "extraction_records": len(extraction_rows),
        "invalid_outputs": len(invalid_rows),
        "source_file_errors": source_file_errors,
        "segments_processed_this_run": processed_this_run,
        "segments_processed_total": len(extraction_rows),
        "segments_skipped_this_run": skipped_this_run,
        "mapped_segments": mapped_segments,
        "synthetic_unmapped_segments": synthetic_unmapped_segments,
        "source_files_total": source_files_total,
        "source_files_processed": source_files_processed,
        "accepted_records": 0,
        "null_signal_records": 0,
        "invalid_output_records": 0,
        "provider_error_records": 0,
        "reconciled_signals": 0,
        "reconciled_accepted_signals": 0,
        "reconciled_duplicate_signals": 0,
        "reconciled_source_extractions": len(extraction_rows),
        "publish_checkpoint": 0,
    }
    for row in extraction_rows:
        status = str(row.get("extraction_status") or "")
        if status == "accepted":
            counts["accepted_records"] += 1
        elif status == "null_signal":
            counts["null_signal_records"] += 1
        if status == "invalid_output":
            counts["invalid_output_records"] += 1
        elif status == "provider_error":
            counts["provider_error_records"] += 1
    if reconciliation_stats:
        counts.update(reconciliation_stats)
    return counts


def _atlas_artifact_counts(counts: dict[str, int]) -> dict[str, int]:
    return {
        "progress": 1,
        "candidate_bridge_records": counts["candidate_bridge_records"],
        "atlas_thread_candidates": counts["atlas_thread_candidates"],
        "atlas_candidate_coverage": counts["atlas_candidate_coverage"],
        "extraction_records": counts["extraction_records"],
        "invalid_outputs": counts["invalid_outputs"],
        "reconciled_signals": counts.get("reconciled_signals", 0),
        "publish_checkpoint": counts.get("publish_checkpoint", 0),
        "artifacts_index": 1,
    }


def _write_atlas_progress(
    *,
    path: Path,
    run_id: str,
    atlas_run_id: str,
    status: str,
    current_phase: str,
    phase_status: str,
    counts: dict[str, int],
    errors: int,
    warnings: int,
    started_at: str,
    message: str,
) -> dict[str, Any]:
    row = guided_contract.build_progress(
        run_id=run_id,
        atlas_run_id=atlas_run_id,
        status=status,
        current_phase=current_phase,
        phase_status=phase_status,
        phase_order=_ATLAS_GUIDED_PHASE_ORDER,
        counts=counts,
        errors=errors,
        warnings=warnings,
        started_at=started_at,
        updated_at=_utc_now_iso(),
        message=message,
    )
    _write_progress(path, row)
    return row


def _write_atlas_artifacts_index(
    *,
    path: Path,
    run_id: str,
    atlas_run_id: str,
    counts: dict[str, int],
) -> dict[str, Any]:
    row = guided_contract.build_artifacts_index(
        run_id=run_id,
        atlas_run_id=atlas_run_id,
        artifacts=guided_contract.canonical_artifact_records(
            counts=_atlas_artifact_counts(counts)
        ),
    )
    _write_progress(path, row)
    return row


def _ensure_atlas_publish_checkpoint(
    *,
    path: Path,
    run_id: str,
    atlas_run_id: str,
) -> int:
    rows = _load_jsonl_rows(path)
    checkpoint_id = "atlas_guided_no_publish_default"
    for row in rows:
        if row.get("checkpoint_id") == checkpoint_id:
            return len(rows)
    _append_jsonl(
        path,
        guided_contract.build_publish_checkpoint(
            run_id=run_id,
            atlas_run_id=atlas_run_id,
            checkpoint_id=checkpoint_id,
            status="disabled",
            publish_enabled=False,
            publish_gate_open=False,
            target_wing=None,
            record_count=0,
            notes="WP-05 atlas-guided extraction mode is no-publish.",
        ),
    )
    return len(rows) + 1


def _atlas_provider_error_record(
    *,
    lookup_row: dict[str, Any],
    segment: ChatGPTThreadSegment,
    error_code: str,
    error_detail: str,
) -> dict[str, Any]:
    error_basis = "|".join([str(lookup_row["thread_id"]), segment.segment_id, error_code])
    return guided_contract.build_extraction_record(
        run_id=str(lookup_row["run_id"]),
        atlas_run_id=str(lookup_row["atlas_run_id"]),
        extraction_id=f"atlas_provider_error_{_text_digest(error_basis)}",
        thread_id=str(lookup_row["thread_id"]),
        segment_id=segment.segment_id,
        extraction_status="provider_error",
        candidate_id=None,
        candidate_key=None,
        signal_type="provider_error",
        title=None,
        summary=f"Atlas-guided provider error: {error_code}",
        source_excerpt=segment.content[: guided_prompt.PARSED_SOURCE_EXCERPT_MAX_CHARS],
        confidence=0.0,
        provenance={
            "error_code": error_code,
            "error_detail": error_detail[:_MAX_INVALID_EXCERPT_CHARS],
            "logical_source_id": segment.logical_source_id,
            "conversation_id": segment.conversation_id,
            "subthread_id": segment.subthread_id,
            "segment_excerpt": segment.content[: guided_prompt.PROVENANCE_SEGMENT_EXCERPT_MAX_CHARS],
        },
    )


def _atlas_write_state(
    *,
    progress_path: Path,
    artifacts_index_path: Path,
    run_id: str,
    atlas_run_id: str,
    atlas_inputs: dict[str, Any],
    extraction_rows: list[dict[str, Any]],
    invalid_rows: list[dict[str, Any]],
    source_file_errors: int,
    processed_this_run: int,
    skipped_this_run: int,
    mapped_segments: int,
    synthetic_unmapped_segments: int,
    source_files_total: int,
    source_files_processed: int,
    publish_checkpoint_count: int,
    errors: int,
    warnings: int,
    started_at: str,
    status: str,
    current_phase: str,
    phase_status: str,
    message: str,
    reconciliation_stats: dict[str, int] | None = None,
) -> dict[str, int]:
    counts = _atlas_counts_snapshot(
        candidate_rows=atlas_inputs["candidate_rows"],
        lookup_rows=atlas_inputs["lookup_rows"],
        extraction_rows=extraction_rows,
        invalid_rows=invalid_rows,
        coverage_rows=1,
        source_file_errors=source_file_errors,
        processed_this_run=processed_this_run,
        skipped_this_run=skipped_this_run,
        mapped_segments=mapped_segments,
        synthetic_unmapped_segments=synthetic_unmapped_segments,
        source_files_total=source_files_total,
        source_files_processed=source_files_processed,
        reconciliation_stats=reconciliation_stats,
    )
    counts["publish_checkpoint"] = publish_checkpoint_count
    _write_atlas_progress(
        path=progress_path,
        run_id=run_id,
        atlas_run_id=atlas_run_id,
        status=status,
        current_phase=current_phase,
        phase_status=phase_status,
        counts=counts,
        errors=errors + source_file_errors,
        warnings=warnings,
        started_at=started_at,
        message=message,
    )
    _write_atlas_artifacts_index(
        path=artifacts_index_path,
        run_id=run_id,
        atlas_run_id=atlas_run_id,
        counts=counts,
    )
    return counts


def _load_conversation_payload(source_file: Path) -> list[Any]:
    data = json.loads(source_file.read_text(encoding="utf-8", errors="replace"))
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise ValueError("not_conversations_list")
    return data


def _atlas_segment_base_record(
    *,
    segment: ChatGPTThreadSegment,
    source_file: Path,
    lookup_row: dict[str, Any],
    model: str,
) -> dict[str, Any]:
    return {
        "segment_key": _segment_key(segment),
        "logical_source_id": segment.logical_source_id,
        "source_hash": segment.source_hash,
        "conversation_id": segment.conversation_id,
        "conversation_title": segment.title or "",
        "subthread_id": segment.subthread_id,
        "subthread_label": segment.subthread_label,
        "segment_id": segment.segment_id,
        "segment_index": segment.segment_index,
        "message_start_index": segment.message_start_index,
        "message_end_index": segment.message_end_index,
        "char_start": segment.char_start,
        "char_end": segment.char_end,
        "source_path": str(source_file),
        "atlas_thread_id": lookup_row["thread_id"],
        "atlas_lookup_status": lookup_row["lookup_status"],
        "atlas_source_thread_ref": lookup_row.get("source_thread_ref"),
        "extraction_version": ATLAS_GUIDED_EXTRACTION_VERSION,
        "model": model,
    }


def _append_atlas_record(
    path: Path,
    record: dict[str, Any],
    *,
    bucket: list[dict[str, Any]],
    segment: ChatGPTThreadSegment,
    source_file: Path,
    model: str,
    extra_fields: dict[str, Any] | None = None,
) -> None:
    payload = dict(record)
    payload["model"] = model
    payload["extraction_version"] = ATLAS_GUIDED_EXTRACTION_VERSION
    payload["logical_source_id"] = segment.logical_source_id
    payload["source_hash"] = segment.source_hash
    payload["conversation_id"] = segment.conversation_id
    payload["conversation_title"] = segment.title or ""
    payload["subthread_id"] = segment.subthread_id
    payload["subthread_label"] = segment.subthread_label
    payload["segment_index"] = segment.segment_index
    payload["message_start_index"] = segment.message_start_index
    payload["message_end_index"] = segment.message_end_index
    payload["char_start"] = segment.char_start
    payload["char_end"] = segment.char_end
    payload["source_path"] = str(source_file)
    if extra_fields:
        payload.update(extra_fields)
    _append_jsonl(path, payload)
    bucket.append(payload)


def _process_atlas_segment(
    *,
    segment: ChatGPTThreadSegment,
    source_file: Path,
    lookup_row: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
    provider: SegmentProvider,
    provider_max_attempts: int,
    model: str,
    extraction_path: Path,
    invalid_path: Path,
    extraction_rows: list[dict[str, Any]],
    invalid_rows: list[dict[str, Any]],
) -> tuple[str, int, int]:
    invalid_warning = 0
    provider_error = 0
    status = "error"
    raw_text = ""
    try:
        last_exc: Exception | None = None
        for attempt in range(1, provider_max_attempts + 1):
            try:
                raw_text = provider.classify_segment(
                    prompt_messages=guided_prompt.build_chatgpt_atlas_guided_prompt_messages(
                        segment.content,
                        lookup_row,
                        candidate_rows,
                    )
                )
                last_exc = None
                break
            except Exception as exc:
                last_exc = exc
                if attempt >= provider_max_attempts:
                    raise
                time.sleep(min(0.3 * attempt, 1.0))
        if last_exc is not None:
            raise last_exc

        parsed = guided_prompt.parse_chatgpt_atlas_guided_response(
            segment.content,
            segment_id=segment.segment_id,
            thread_candidate_lookup_row=lookup_row,
            candidate_bridge_rows=candidate_rows,
            response_text=raw_text,
        )
        if parsed.error_code is not None:
            status = "invalid_output"
            invalid_warning = 1
        else:
            status = "classified"
        for row in parsed.records:
            _append_atlas_record(
                extraction_path,
                row,
                bucket=extraction_rows,
                segment=segment,
                source_file=source_file,
                model=model,
            )
            if parsed.error_code is not None:
                _append_atlas_record(
                    invalid_path,
                    row,
                    bucket=invalid_rows,
                    segment=segment,
                    source_file=source_file,
                    model=model,
                    extra_fields={"status": "invalid_output", "error_code": parsed.error_code},
                )
    except Exception as exc:
        status = "error"
        provider_error = 1
        error_record = _atlas_provider_error_record(
            lookup_row=lookup_row,
            segment=segment,
            error_code="provider_error",
            error_detail=str(exc),
        )
        _append_atlas_record(
            extraction_path,
            error_record,
            bucket=extraction_rows,
            segment=segment,
            source_file=source_file,
            model=model,
        )
        _append_atlas_record(
            invalid_path,
            error_record,
            bucket=invalid_rows,
            segment=segment,
            source_file=source_file,
            model=model,
            extra_fields={"status": "error", "error_code": "provider_error"},
        )
    return status, invalid_warning, provider_error


def _iter_conversations(source_dir: Path):
    files = sorted(source_dir.rglob("conversations.json"))
    if not files:
        raise FatalRemoteError(f"No conversations.json files found under {source_dir}")
    for source_file in files:
        yield source_file


def _segment_key(segment: ChatGPTThreadSegment) -> str:
    return "|".join(
        [
            segment.logical_source_id,
            segment.source_hash,
            segment.subthread_id,
            segment.segment_id,
        ]
    )


def _load_segment_checkpoint_statuses(checkpoint_path: Path) -> dict[str, str]:
    statuses: dict[str, str] = {}
    if not checkpoint_path.exists():
        return statuses
    with checkpoint_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = row.get("segment_key")
            status = row.get("status")
            if isinstance(key, str) and status in {"classified", "invalid_output", "error"}:
                statuses[key] = status
    return statuses


def _should_skip_segment(*, status: str | None, retry_errors: bool) -> bool:
    if status in {"classified", "invalid_output"}:
        return True
    if status == "error":
        return not retry_errors
    return False


def _build_prompt(segment: ChatGPTThreadSegment, source_file: Path) -> list[dict[str, str]]:
    system = (
        "Extract durable memory signals from one ChatGPT transcript segment. "
        "Use only the provided segment text. Return strict JSON only."
    )
    payload = {
        "provenance": {
            "logical_source_id": segment.logical_source_id,
            "source_hash": segment.source_hash,
            "conversation_id": segment.conversation_id,
            "conversation_title": segment.title or "",
            "subthread_id": segment.subthread_id,
            "subthread_label": segment.subthread_label,
            "segment_id": segment.segment_id,
            "segment_index": segment.segment_index,
            "message_start_index": segment.message_start_index,
            "message_end_index": segment.message_end_index,
            "char_start": segment.char_start,
            "char_end": segment.char_end,
            "source_path": str(source_file),
            "extraction_version": EXTRACTION_VERSION,
        },
        "schema": {
            "summary": "one sentence grounded in segment text",
            "items": [
                {
                    "type": "decision|preference|project|task|fact|problem|open_question",
                    "text": "durable signal from this segment only",
                    "importance": "integer 1-5",
                    "evidence": "bounded excerpt from this segment",
                }
            ],
        },
        "rules": [
            "Return at most 8 items.",
            "Do not use outside context.",
            "Use an empty items list when there are no durable signals.",
        ],
        "segment_text": segment.content,
    }
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]


def _run_legacy(
    args: argparse.Namespace,
    *,
    provider: SegmentProvider | None = None,
    mcp_caller: MCPCaller | None = None,
) -> int:
    source_dir = Path(args.source_dir)
    run_dir = Path(args.run_dir)
    progress_path = run_dir / "progress.json"
    checkpoint_path = run_dir / "segment_checkpoint.jsonl"
    extracted_path = run_dir / "segment_extractions.jsonl"
    invalid_path = run_dir / "invalid_outputs.jsonl"
    source_checkpoint_path = run_dir / "source_checkpoint.jsonl"
    source_error_path = run_dir / "source_file_errors.jsonl"
    seen_statuses = _load_segment_checkpoint_statuses(checkpoint_path)

    localai_base = ensure_localai_base_url(args.localai_base_url)
    if provider is None:
        token = read_token(args.localai_token, args.localai_token_file, "LocalAI")
        provider = HttpSegmentProvider(
            base_url=localai_base,
            token=token,
            model=args.model,
            timeout=args.localai_timeout,
        )

    processed = 0
    skipped = 0
    classified = 0
    invalid = 0
    errors = 0
    source_file_errors = 0
    source_files_total = 0
    source_files_processed = 0
    started = time.time()
    stop = False
    publish_enabled = bool(getattr(args, "publish", False))
    retry_errors = bool(getattr(args, "retry_errors", False))
    provider_max_attempts = max(1, int(getattr(args, "provider_max_attempts", 2)))

    for source_file in _iter_conversations(source_dir):
        source_files_total += 1
        try:
            data = json.loads(source_file.read_text(encoding="utf-8", errors="replace"))
            if isinstance(data, dict):
                data = [data]
            if not isinstance(data, list):
                raise ValueError("not_conversations_list")
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            source_files_processed += 1
            source_file_errors += 1
            elapsed = round(time.time() - started, 2)
            detail = str(exc)
            if isinstance(exc, json.JSONDecodeError):
                code = "source_json_decode_error"
            elif isinstance(exc, OSError):
                code = "source_read_error"
            else:
                code = "source_shape_error"
            source_row = {
                "source_path": str(source_file),
                "status": "error",
                "error_code": code,
                "error_detail": detail[:_MAX_INVALID_EXCERPT_CHARS],
                "elapsed_seconds": elapsed,
            }
            _append_jsonl(source_error_path, source_row)
            _append_jsonl(source_checkpoint_path, source_row)
            _write_progress(
                progress_path,
                {
                    "status": "running",
                    "processed_segments": processed,
                    "skipped_segments": skipped,
                    "classified_segments": classified,
                    "invalid_segments": invalid,
                    "error_segments": errors,
                    "source_files_total": source_files_total,
                    "source_files_processed": source_files_processed,
                    "source_file_error_count": source_file_errors,
                    "elapsed_seconds": elapsed,
                    "last_source_path": str(source_file),
                },
            )
            continue
        source_files_processed += 1
        _append_jsonl(
            source_checkpoint_path,
            {"source_path": str(source_file), "status": "loaded", "elapsed_seconds": round(time.time() - started, 2)},
        )
        for conversation in data:
            if not (isinstance(conversation, dict) and "mapping" in conversation):
                continue
            segments = build_chatgpt_thread_segments(conversation=conversation)
            for segment in segments:
                key = _segment_key(segment)
                if _should_skip_segment(status=seen_statuses.get(key), retry_errors=retry_errors):
                    skipped += 1
                    continue
                prompt_messages = _build_prompt(segment, source_file)
                base_record = {
                    "segment_key": key,
                    "logical_source_id": segment.logical_source_id,
                    "source_hash": segment.source_hash,
                    "conversation_id": segment.conversation_id,
                    "conversation_title": segment.title or "",
                    "subthread_id": segment.subthread_id,
                    "subthread_label": segment.subthread_label,
                    "segment_id": segment.segment_id,
                    "segment_index": segment.segment_index,
                    "message_start_index": segment.message_start_index,
                    "message_end_index": segment.message_end_index,
                    "char_start": segment.char_start,
                    "char_end": segment.char_end,
                    "source_path": str(source_file),
                    "extraction_version": EXTRACTION_VERSION,
                    "model": args.model,
                }
                status = "error"
                try:
                    last_exc: Exception | None = None
                    raw_text = ""
                    for attempt in range(1, provider_max_attempts + 1):
                        try:
                            raw_text = provider.classify_segment(prompt_messages=prompt_messages)
                            last_exc = None
                            break
                        except Exception as exc:
                            last_exc = exc
                            if attempt >= provider_max_attempts:
                                raise
                            time.sleep(min(0.3 * attempt, 1.0))
                    if last_exc is not None:
                        raise last_exc
                    parsed = _parse_segment_output(raw_text)
                    _append_jsonl(
                        extracted_path,
                        {
                            **base_record,
                            "status": "classified",
                            "summary": parsed["summary"],
                            "items": parsed["items"],
                            "segment_excerpt": segment.content[:_MAX_SEGMENT_EXCERPT_CHARS],
                        },
                    )
                    status = "classified"
                    classified += 1
                except ValueError as exc:
                    status = "invalid_output"
                    invalid += 1
                    _append_jsonl(
                        invalid_path,
                        {
                            **base_record,
                            "status": "invalid_output",
                            "error_code": str(exc),
                            "raw_response_excerpt": (locals().get("raw_text") or "")[
                                :_MAX_INVALID_EXCERPT_CHARS
                            ],
                        },
                    )
                except Exception as exc:
                    status = "error"
                    errors += 1
                    _append_jsonl(
                        invalid_path,
                        {
                            **base_record,
                            "status": "error",
                            "error_code": "provider_error",
                            "error_detail": str(exc)[:_MAX_INVALID_EXCERPT_CHARS],
                        },
                    )

                processed += 1
                seen_statuses[key] = status
                elapsed = round(time.time() - started, 2)
                _append_jsonl(
                    checkpoint_path,
                    {
                        **base_record,
                        "status": status,
                        "processed": processed,
                        "elapsed_seconds": elapsed,
                    },
                )
                _write_progress(
                    progress_path,
                    {
                        "status": "running",
                        "processed_segments": processed,
                        "skipped_segments": skipped,
                        "classified_segments": classified,
                        "invalid_segments": invalid,
                        "error_segments": errors,
                        "source_files_total": source_files_total,
                        "source_files_processed": source_files_processed,
                        "source_file_error_count": source_file_errors,
                        "elapsed_seconds": elapsed,
                        "last_segment_key": key,
                    },
                )
                if args.limit and processed >= args.limit:
                    stop = True
                    break
            if stop:
                break
        if stop:
            break

    _write_progress(
        progress_path,
        {
            "status": "complete",
            "processed_segments": processed,
            "skipped_segments": skipped,
            "classified_segments": classified,
            "invalid_segments": invalid,
            "error_segments": errors,
            "source_files_total": source_files_total,
            "source_files_processed": source_files_processed,
            "source_file_error_count": source_file_errors,
            "elapsed_seconds": round(time.time() - started, 2),
        },
    )
    if processed > 0 or not (run_dir / "reconciled_signals.jsonl").exists():
        recon_stats = reconcile_segment_extractions(run_dir=run_dir, model=args.model)
    else:
        recon_stats = _reconciled_stats_from_existing(run_dir)
    progress = json.loads(progress_path.read_text(encoding="utf-8"))
    progress.update(recon_stats)
    if publish_enabled:
        if mcp_caller is None:
            mempalace_token = read_token(
                args.mempalace_token, args.mempalace_token_file, "MemPalace"
            )
            mcp_caller = HttpMCPCaller(base_url=args.mempalace_url, token=mempalace_token)
        publish_stats = publish_reconciled_signals(
            run_dir=run_dir,
            wing=args.wing,
            added_by=args.added_by,
            mcp_timeout=args.mempalace_timeout,
            mcp_caller=mcp_caller,
            publish_limit=getattr(args, "publish_limit", 0),
        )
        progress.update(publish_stats)
    _write_progress(progress_path, progress)
    print(
        json.dumps(
            {
                "status": "complete",
                "processed_segments": processed,
                "skipped_segments": skipped,
                "classified_segments": classified,
                "invalid_segments": invalid,
                "error_segments": errors,
                "source_files_total": source_files_total,
                "source_files_processed": source_files_processed,
                "source_file_error_count": source_file_errors,
                **recon_stats,
                **(
                    {
                        "publish_attempted": progress.get("publish_attempted", 0),
                        "publish_success": progress.get("publish_success", 0),
                        "publish_failed": progress.get("publish_failed", 0),
                        "publish_skipped": progress.get("publish_skipped", 0),
                    }
                    if publish_enabled
                    else {}
                ),
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


def _run_atlas_guided(
    args: argparse.Namespace,
    *,
    provider: SegmentProvider | None = None,
) -> int:
    if getattr(args, "publish", False):
        raise FatalRemoteError("Atlas-guided mode is no-publish in WP-05; refusing --publish")
    atlas_run_dir_value = str(getattr(args, "atlas_run_dir", "") or "").strip()
    if not atlas_run_dir_value:
        raise FatalRemoteError("--atlas-run-dir is required with --atlas-guided")

    source_dir = Path(args.source_dir)
    run_dir = Path(args.run_dir)
    atlas_run_dir = Path(atlas_run_dir_value)
    candidate_records_path = None
    if getattr(args, "candidate_records", None):
        candidate_records_path = Path(str(args.candidate_records))

    run_id = _atlas_run_id_from_dir(run_dir)
    progress_path = run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["progress"]
    artifacts_index_path = run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["artifacts_index"]
    candidate_bridge_path = run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["candidate_bridge_records"]
    lookup_path = run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["atlas_thread_candidates"]
    coverage_path = run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["atlas_candidate_coverage"]
    extraction_path = run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["extraction_records"]
    invalid_path = run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["invalid_outputs"]
    reconciled_path = run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["reconciled_signals"]
    publish_checkpoint_path = run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["publish_checkpoint"]
    checkpoint_path = run_dir / "segment_checkpoint.jsonl"
    source_checkpoint_path = run_dir / "source_checkpoint.jsonl"
    source_error_path = run_dir / "source_file_errors.jsonl"

    atlas_inputs = _load_atlas_guided_inputs(
        run_id=run_id,
        atlas_run_dir=atlas_run_dir,
        candidate_records_path=candidate_records_path,
    )

    localai_base = ensure_atlas_guided_localai_base_url(args.localai_base_url)
    if provider is None:
        token = read_token(args.localai_token, args.localai_token_file, "LocalAI")
        provider = HttpSegmentProvider(
            base_url=localai_base,
            token=token,
            model=args.model,
            timeout=args.localai_timeout,
        )

    atlas_run_id = str(atlas_inputs["atlas_run_id"])
    _write_jsonl_rows(candidate_bridge_path, atlas_inputs["candidate_rows"])
    _write_jsonl_rows(lookup_path, atlas_inputs["lookup_rows"])
    _write_progress(coverage_path, atlas_inputs["coverage_row"])

    seen_statuses = _load_segment_checkpoint_statuses(checkpoint_path)
    extraction_rows = _load_jsonl_rows(extraction_path)
    invalid_rows = _load_jsonl_rows(invalid_path)
    source_file_errors = len(_load_jsonl_rows(source_error_path))
    publish_checkpoint_count = _ensure_atlas_publish_checkpoint(
        path=publish_checkpoint_path,
        run_id=run_id,
        atlas_run_id=atlas_run_id,
    )

    retry_errors = bool(getattr(args, "retry_errors", False))
    provider_max_attempts = max(1, int(getattr(args, "provider_max_attempts", 2)))
    started_at = _utc_now_iso()
    processed_this_run = 0
    skipped_this_run = 0
    mapped_segments = 0
    synthetic_unmapped_segments = 0
    warnings = 0
    errors = sum(1 for row in invalid_rows if row.get("extraction_status") == "provider_error")
    source_files_total = 0
    source_files_processed = 0
    stop = False

    counts = _atlas_write_state(
        progress_path=progress_path,
        artifacts_index_path=artifacts_index_path,
        run_id=run_id,
        atlas_run_id=atlas_run_id,
        atlas_inputs=atlas_inputs,
        extraction_rows=extraction_rows,
        invalid_rows=invalid_rows,
        source_file_errors=source_file_errors,
        processed_this_run=processed_this_run,
        skipped_this_run=skipped_this_run,
        mapped_segments=mapped_segments,
        synthetic_unmapped_segments=synthetic_unmapped_segments,
        source_files_total=source_files_total,
        source_files_processed=source_files_processed,
        publish_checkpoint_count=publish_checkpoint_count,
        errors=errors,
        warnings=warnings,
        started_at=started_at,
        status="running",
        current_phase="load_inputs",
        phase_status="complete",
        message="Loaded atlas-guided bridge, lookup, coverage, and thread index inputs.",
    )

    for source_file in _iter_conversations(source_dir):
        source_files_total += 1
        try:
            data = _load_conversation_payload(source_file)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            source_files_processed += 1
            source_file_errors += 1
            error_code = "source_shape_error"
            if isinstance(exc, json.JSONDecodeError):
                error_code = "source_json_decode_error"
            elif isinstance(exc, OSError):
                error_code = "source_read_error"
            source_row = {
                "source_path": str(source_file),
                "status": "error",
                "error_code": error_code,
                "error_detail": str(exc)[:_MAX_INVALID_EXCERPT_CHARS],
            }
            _append_jsonl(source_error_path, source_row)
            _append_jsonl(source_checkpoint_path, source_row)
            counts = _atlas_write_state(
                progress_path=progress_path,
                artifacts_index_path=artifacts_index_path,
                run_id=run_id,
                atlas_run_id=atlas_run_id,
                atlas_inputs=atlas_inputs,
                extraction_rows=extraction_rows,
                invalid_rows=invalid_rows,
                source_file_errors=source_file_errors,
                processed_this_run=processed_this_run,
                skipped_this_run=skipped_this_run,
                mapped_segments=mapped_segments,
                synthetic_unmapped_segments=synthetic_unmapped_segments,
                source_files_total=source_files_total,
                source_files_processed=source_files_processed,
                publish_checkpoint_count=publish_checkpoint_count,
                errors=errors,
                warnings=warnings,
                started_at=started_at,
                status="running",
                current_phase="extract",
                phase_status="running",
                message=f"Skipped unreadable source file {source_file}.",
            )
            continue

        source_files_processed += 1
        _append_jsonl(source_checkpoint_path, {"source_path": str(source_file), "status": "loaded"})
        for conversation in data:
            if not (isinstance(conversation, dict) and "mapping" in conversation):
                continue
            segments = build_chatgpt_thread_segments(conversation=conversation)
            for segment in segments:
                key = _segment_key(segment)
                if _should_skip_segment(status=seen_statuses.get(key), retry_errors=retry_errors):
                    skipped_this_run += 1
                    continue

                lookup_row, matched_thread_id = _select_thread_lookup_for_segment(
                    segment=segment,
                    atlas_inputs=atlas_inputs,
                    run_id=run_id,
                )
                if matched_thread_id is None:
                    synthetic_unmapped_segments += 1
                    warnings += 1
                else:
                    mapped_segments += 1

                base_record = _atlas_segment_base_record(
                    segment=segment,
                    source_file=source_file,
                    lookup_row=lookup_row,
                    model=args.model,
                )
                status, invalid_warning, provider_error = _process_atlas_segment(
                    segment=segment,
                    source_file=source_file,
                    lookup_row=lookup_row,
                    candidate_rows=atlas_inputs["candidate_rows"],
                    provider=provider,
                    provider_max_attempts=provider_max_attempts,
                    model=args.model,
                    extraction_path=extraction_path,
                    invalid_path=invalid_path,
                    extraction_rows=extraction_rows,
                    invalid_rows=invalid_rows,
                )
                warnings += invalid_warning
                errors += provider_error

                processed_this_run += 1
                seen_statuses[key] = status
                _append_jsonl(
                    checkpoint_path,
                    {
                        **base_record,
                        "status": status,
                        "processed_this_run": processed_this_run,
                    },
                )
                counts = _atlas_write_state(
                    progress_path=progress_path,
                    artifacts_index_path=artifacts_index_path,
                    run_id=run_id,
                    atlas_run_id=atlas_run_id,
                    atlas_inputs=atlas_inputs,
                    extraction_rows=extraction_rows,
                    invalid_rows=invalid_rows,
                    source_file_errors=source_file_errors,
                    processed_this_run=processed_this_run,
                    skipped_this_run=skipped_this_run,
                    mapped_segments=mapped_segments,
                    synthetic_unmapped_segments=synthetic_unmapped_segments,
                    source_files_total=source_files_total,
                    source_files_processed=source_files_processed,
                    publish_checkpoint_count=publish_checkpoint_count,
                    errors=errors,
                    warnings=warnings,
                    started_at=started_at,
                    status="running",
                    current_phase="extract",
                    phase_status="running",
                    message=f"Processed atlas-guided segment {segment.segment_id}.",
                )
                if args.limit and processed_this_run >= args.limit:
                    stop = True
                    break
            if stop:
                break
        if stop:
            break

    try:
        reconciliation = guided_reconciliation.build_chatgpt_atlas_guided_reconciliation(
            extraction_rows,
            run_id=run_id,
            atlas_run_id=atlas_run_id,
        )
    except ValueError as exc:
        raise FatalRemoteError(f"Atlas-guided reconciliation failed: {exc}") from exc
    _write_jsonl_rows(reconciled_path, list(reconciliation.rows))

    counts = _atlas_write_state(
        progress_path=progress_path,
        artifacts_index_path=artifacts_index_path,
        run_id=run_id,
        atlas_run_id=atlas_run_id,
        atlas_inputs=atlas_inputs,
        extraction_rows=extraction_rows,
        invalid_rows=invalid_rows,
        source_file_errors=source_file_errors,
        processed_this_run=processed_this_run,
        skipped_this_run=skipped_this_run,
        mapped_segments=mapped_segments,
        synthetic_unmapped_segments=synthetic_unmapped_segments,
        source_files_total=source_files_total,
        source_files_processed=source_files_processed,
        publish_checkpoint_count=publish_checkpoint_count,
        errors=errors,
        warnings=warnings,
        started_at=started_at,
        status="complete",
        current_phase="finalize",
        phase_status="complete",
        message="Atlas-guided extraction and reconciliation artifacts are complete for this invocation.",
        reconciliation_stats=reconciliation.stats,
    )
    print(
        json.dumps(
            {
                "status": "complete",
                "run_id": run_id,
                "atlas_run_id": atlas_run_id,
                "processed_segments": processed_this_run,
                "skipped_segments": skipped_this_run,
                "accepted_records": counts["accepted_records"],
                "null_signal_records": counts["null_signal_records"],
                "invalid_output_records": counts["invalid_output_records"],
                "provider_error_records": counts["provider_error_records"],
                "reconciled_signals": counts["reconciled_signals"],
                "reconciled_duplicate_signals": counts["reconciled_duplicate_signals"],
                "reconciled_source_extractions": counts["reconciled_source_extractions"],
                "source_file_error_count": source_file_errors,
                "warnings": warnings,
                "no_publish": True,
                "publish_enabled": False,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


def run(
    args: argparse.Namespace,
    *,
    provider: SegmentProvider | None = None,
    mcp_caller: MCPCaller | None = None,
) -> int:
    if getattr(args, "atlas_guided", False):
        return _run_atlas_guided(args, provider=provider)
    return _run_legacy(args, provider=provider, mcp_caller=mcp_caller)


def parse_args(argv: list[str]) -> argparse.Namespace:
    explicit_run_dir = any(arg == "--run-dir" or arg.startswith("--run-dir=") for arg in argv)
    run_dir_from_env = "LOCALAI_THREAD_SIGNAL_RUN_DIR" in os.environ
    parser = argparse.ArgumentParser(
        description="Extract thread-aware ChatGPT segment signals with LocalAI and durable checkpoints."
    )
    parser.add_argument("--source-dir", default=os.environ.get("CHATGPT_SOURCE_DIR", DEFAULT_SOURCE_DIR))
    parser.add_argument("--run-dir", default=os.environ.get("LOCALAI_THREAD_SIGNAL_RUN_DIR", DEFAULT_RUN_DIR))
    parser.add_argument(
        "--atlas-guided",
        action="store_true",
        default=_env_bool("LOCALAI_THREAD_SIGNAL_ATLAS_GUIDED", False),
        help="Run atlas-guided no-publish extraction using precomputed atlas bridge and coverage artifacts.",
    )
    parser.add_argument(
        "--atlas-run-dir",
        default=os.environ.get("CHATGPT_ATLAS_RUN_DIR"),
        help="Directory containing atlas-guided candidate bridge, thread lookup, coverage, and thread_index artifacts.",
    )
    parser.add_argument(
        "--candidate-records",
        default=os.environ.get("CHATGPT_ATLAS_CANDIDATE_RECORDS"),
        help="Optional path override for candidate_bridge_records.jsonl.",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("LOCALAI_MODEL")
        or os.environ.get("ARCHIVEKG_CHAT_ROLLUP_MODEL")
        or DEFAULT_MODEL,
    )
    parser.add_argument(
        "--localai-base-url",
        default=os.environ.get("LOCALAI_BASE_URL")
        or os.environ.get("ARCHIVEKG_OPENAI_BASE_URL")
        or DEFAULT_LOCALAI_BASE_URL,
    )
    parser.add_argument("--localai-token", default=os.environ.get("LOCALAI_TOKEN") or os.environ.get("ARCHIVEKG_OPENAI_API_KEY"))
    parser.add_argument("--localai-token-file", default=os.environ.get("LOCALAI_TOKEN_FILE") or DEFAULT_LOCALAI_TOKEN_FILE)
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--wing", default=os.environ.get("LOCALAI_THREAD_SIGNAL_WING", "chatgpt_thread_signals"))
    parser.add_argument(
        "--added-by",
        default=os.environ.get("LOCALAI_THREAD_SIGNAL_ADDED_BY", "localai_chatgpt_thread_signals"),
    )
    parser.add_argument("--mempalace-url", default=os.environ.get("MEMPALACE_HTTP_URL") or DEFAULT_MEMPALACE_URL)
    parser.add_argument("--mempalace-token", default=os.environ.get("MEMPALACE_HTTP_TOKEN"))
    parser.add_argument(
        "--mempalace-token-file",
        default=os.environ.get("MEMPALACE_HTTP_TOKEN_FILE") or DEFAULT_MEMPALACE_TOKEN_FILE,
    )
    parser.add_argument("--mempalace-timeout", type=float, default=float(os.environ.get("MEMPALACE_HTTP_TIMEOUT", "120")))
    parser.add_argument("--publish-limit", type=int, default=int(os.environ.get("LOCALAI_THREAD_SIGNAL_PUBLISH_LIMIT", "0")))
    parser.add_argument("--limit", type=int, default=int(os.environ.get("LOCALAI_THREAD_SIGNAL_LIMIT", "0")))
    parser.add_argument("--localai-timeout", type=float, default=float(os.environ.get("LOCALAI_TIMEOUT", "180")))
    parser.add_argument(
        "--retry-errors",
        action="store_true",
        default=_env_bool("LOCALAI_THREAD_SIGNAL_RETRY_ERRORS", False),
        help="Retry segments whose latest checkpoint status is error.",
    )
    parser.add_argument(
        "--provider-max-attempts",
        type=int,
        default=max(1, int(os.environ.get("LOCALAI_THREAD_SIGNAL_PROVIDER_MAX_ATTEMPTS", "2"))),
        help="Maximum LocalAI classify attempts per segment for transient provider failures.",
    )
    args = parser.parse_args(argv)
    if args.atlas_guided:
        if explicit_run_dir or run_dir_from_env:
            try:
                _validate_atlas_guided_cli_run_dir(str(args.run_dir))
            except FatalRemoteError as exc:
                parser.error(str(exc))
        else:
            args.run_dir = str(_default_atlas_guided_run_dir(args.atlas_run_dir))
    return args


def main(argv: list[str] | None = None) -> int:
    try:
        return run(parse_args(argv or sys.argv[1:]))
    except FatalRemoteError as exc:
        print(f"fatal: {exc}", file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
