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
from pathlib import Path
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from mempalace.chatgpt_thread_segments import ChatGPTThreadSegment, build_chatgpt_thread_segments

DEFAULT_SOURCE_DIR = "/media/u0/OneDrive_Backup/mempalace/sources/chatgpt"
DEFAULT_RUN_DIR = "/media/u0/OneDrive_Backup/mempalace/data/localai_chatgpt_thread_signals"
DEFAULT_MEMPALACE_URL = "http://100.112.179.49:8765"
DEFAULT_MEMPALACE_TOKEN_FILE = "/media/u0/OneDrive_Backup/mempalace/secrets/http_token"
DEFAULT_LOCALAI_BASE_URL = "http://snow-white-iii:8080/v1"
DEFAULT_LOCALAI_TOKEN_FILE = "/media/u0/OneDrive_Backup/mempalace/secrets/localai_token"
DEFAULT_MODEL = "qwen3-vl-8b-instruct"
EXTRACTION_VERSION = "localai_chatgpt_thread_signals_v1"
_MAX_EVIDENCE_CHARS = 280
_MAX_INVALID_EXCERPT_CHARS = 500
_MAX_SEGMENT_EXCERPT_CHARS = 320
_MAX_RECON_EVIDENCE = 3
_MAX_MCP_METADATA_CHARS = 128
_PROVIDER_BLOCKLIST = (
    "api.openai.com",
    "anthropic.com",
    "openrouter.ai",
    "together.xyz",
    "groq.com",
    "generativelanguage.googleapis.com",
    "vertexai.googleapis.com",
)


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


def _iter_conversations(source_dir: Path):
    files = sorted(source_dir.rglob("conversations.json"))
    if not files:
        raise FatalRemoteError(f"No conversations.json files found under {source_dir}")
    for source_file in files:
        try:
            data = json.loads(source_file.read_text(encoding="utf-8", errors="replace"))
        except (OSError, json.JSONDecodeError) as exc:
            raise FatalRemoteError(f"Could not load {source_file}: {exc}") from exc
        if isinstance(data, dict):
            data = [data]
        if not isinstance(data, list):
            raise FatalRemoteError(f"{source_file} is not a ChatGPT conversations list")
        for conversation in data:
            if isinstance(conversation, dict) and "mapping" in conversation:
                yield source_file, conversation


def _segment_key(segment: ChatGPTThreadSegment) -> str:
    return "|".join(
        [
            segment.logical_source_id,
            segment.source_hash,
            segment.subthread_id,
            segment.segment_id,
        ]
    )


def _load_seen_segment_keys(checkpoint_path: Path) -> set[str]:
    seen: set[str] = set()
    if not checkpoint_path.exists():
        return seen
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
                seen.add(key)
    return seen


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


def run(
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
    seen = _load_seen_segment_keys(checkpoint_path)

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
    started = time.time()
    stop = False
    publish_enabled = bool(getattr(args, "publish", False))

    for source_file, conversation in _iter_conversations(source_dir):
        segments = build_chatgpt_thread_segments(conversation=conversation)
        for segment in segments:
            key = _segment_key(segment)
            if key in seen:
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
                raw_text = provider.classify_segment(prompt_messages=prompt_messages)
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
            seen.add(key)
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
                    "elapsed_seconds": elapsed,
                    "last_segment_key": key,
                },
            )
            if args.limit and processed >= args.limit:
                stop = True
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


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract thread-aware ChatGPT segment signals with LocalAI and durable checkpoints."
    )
    parser.add_argument("--source-dir", default=os.environ.get("CHATGPT_SOURCE_DIR", DEFAULT_SOURCE_DIR))
    parser.add_argument("--run-dir", default=os.environ.get("LOCALAI_THREAD_SIGNAL_RUN_DIR", DEFAULT_RUN_DIR))
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
    parser.add_argument("--limit", type=int, default=int(os.environ.get("LOCALAI_THREAD_SIGNAL_LIMIT", "0")))
    parser.add_argument("--localai-timeout", type=float, default=float(os.environ.get("LOCALAI_TIMEOUT", "180")))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        return run(parse_args(argv or sys.argv[1:]))
    except FatalRemoteError as exc:
        print(f"fatal: {exc}", file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
