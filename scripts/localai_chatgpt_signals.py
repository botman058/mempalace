#!/usr/bin/env python3
"""Classify ChatGPT privacy exports with LocalAI and file signal drawers.

This is intentionally fail-closed:
  - LocalAI must be enabled and reachable.
  - The base URL may not point at OpenAI's cloud API.
  - No heuristic fallback is used when the model, HTTP call, or JSON schema fails.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    from mempalace.chatgpt_identity import extract_chatgpt_identity
    from mempalace.normalize import _collect_chatgpt_messages, _messages_to_transcript
except ImportError as exc:  # pragma: no cover - deployment/environment failure.
    raise SystemExit(f"Could not import mempalace normalization helpers: {exc}") from exc


DEFAULT_SOURCE_DIR = "/media/u0/OneDrive_Backup/mempalace/sources/chatgpt"
DEFAULT_CHECKPOINT = (
    "/media/u0/OneDrive_Backup/mempalace/data/localai_chatgpt_signals.checkpoint.jsonl"
)
DEFAULT_MEMPALACE_URL = "http://100.112.179.49:8765"
DEFAULT_MEMPALACE_TOKEN_FILE = "/media/u0/OneDrive_Backup/mempalace/secrets/http_token"
DEFAULT_LOCALAI_BASE_URL = "http://snow-white-iii:8080/v1"
DEFAULT_LOCALAI_TOKEN_FILE = "/media/u0/OneDrive_Backup/mempalace/secrets/localai_token"
DEFAULT_MODEL = "qwen3-vl-8b-instruct"

ROOM_RE = re.compile(r"[^a-z0-9_]+")
ALLOWED_ITEM_TYPES = {
    "decision",
    "preference",
    "project",
    "task",
    "fact",
    "problem",
    "open_question",
}


class FatalRemoteError(RuntimeError):
    """Raised when a remote dependency fails and the pass must stop."""


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
    base_url = base_url.rstrip("/")
    lowered = base_url.lower()
    if lowered in {"https://api.openai.com/v1", "http://api.openai.com/v1"}:
        raise FatalRemoteError("Refusing to use OpenAI cloud API for LocalAI pass")
    if "api.openai.com" in lowered:
        raise FatalRemoteError("Refusing LocalAI pass because base URL contains api.openai.com")
    if not base_url:
        raise FatalRemoteError("LocalAI base URL is required")
    return base_url


def post_json(url: str, payload: dict[str, Any], token: str, timeout: float) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
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
        raise FatalRemoteError(f"Unexpected JSON shape from {url}")
    return data


def localai_chat_completion(
    *,
    base_url: str,
    token: str,
    model: str,
    messages: list[dict[str, str]],
    timeout: float,
) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 1400,
        "response_format": {"type": "json_object"},
    }
    data = post_json(f"{base_url}/chat/completions", payload, token, timeout)
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise FatalRemoteError(f"Unexpected LocalAI response shape: {data}") from exc
    if not isinstance(content, str) or not content.strip():
        raise FatalRemoteError("LocalAI returned an empty classification")
    return parse_model_json(content)


def parse_model_json(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise FatalRemoteError(f"LocalAI did not return valid JSON: {text[:1000]}") from exc
    if not isinstance(data, dict):
        raise FatalRemoteError("LocalAI JSON response must be an object")
    return data


def mcp_call(
    *,
    base_url: str,
    token: str,
    tool_name: str,
    arguments: dict[str, Any],
    timeout: float,
) -> dict[str, Any]:
    endpoint = base_url.rstrip("/")
    if not endpoint.endswith("/mcp"):
        endpoint = f"{endpoint}/mcp"
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }
    data = post_json(endpoint, payload, token, timeout)
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


def conversation_key(source_file: Path, conversation: dict[str, Any]) -> str:
    raw_id = conversation.get("id") or conversation.get("conversation_id")
    if isinstance(raw_id, str) and raw_id.strip():
        return f"{source_file.name}:{raw_id.strip()}"
    digest = hashlib.sha256(
        json.dumps(conversation.get("mapping", {}), sort_keys=True).encode("utf-8")
    ).hexdigest()[:24]
    return f"{source_file.name}:sha256:{digest}"


def legacy_checkpoint_key(source_file: Path, conversation_id: str) -> str:
    return f"{source_file.name}:{conversation_id}"


def iter_conversations(source_dir: Path):
    files = sorted(source_dir.rglob("conversations.json"))
    if not files:
        raise FatalRemoteError(f"No conversations.json files found under {source_dir}")
    for path in files:
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except (OSError, json.JSONDecodeError) as exc:
            raise FatalRemoteError(f"Could not load {path}: {exc}") from exc
        if isinstance(data, dict):
            data = [data]
        if not isinstance(data, list):
            raise FatalRemoteError(f"{path} is not a ChatGPT conversations list")
        for conversation in data:
            if isinstance(conversation, dict) and "mapping" in conversation:
                yield path, conversation


def load_checkpoint(path: Path) -> dict[str, str]:
    seen: dict[str, str] = {}
    if not path.exists():
        return seen
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = row.get("key")
            if isinstance(key, str):
                status = row.get("status")
                seen[key] = status if isinstance(status, str) else ""
    return seen


def append_checkpoint(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")
        fh.flush()


def _checkpoint_status(seen: Any, key: str) -> str | None:
    if isinstance(seen, dict):
        return seen.get(key)
    if key in seen:
        return ""
    return None


def seen_checkpoint_key(seen: Any, source_file: Path, identity: Any) -> bool:
    logical_source_id = getattr(identity, "logical_source_id", None)
    if isinstance(logical_source_id, str):
        status = _checkpoint_status(seen, logical_source_id)
        if status is not None and status != "skipped_empty":
            return True

    conversation_id = getattr(identity, "conversation_id", None)
    if isinstance(conversation_id, str):
        legacy_key = legacy_checkpoint_key(source_file, conversation_id)
        status = _checkpoint_status(seen, legacy_key)
        if status is not None and status != "skipped_empty":
            return True

    return False


def sanitize_room(value: Any, fallback: str = "general") -> str:
    if not isinstance(value, str):
        value = fallback
    room = ROOM_RE.sub("_", value.strip().lower()).strip("_")
    return room or fallback


def normalize_item_type(value: Any) -> str:
    if not isinstance(value, str):
        return "fact"
    normalized = ROOM_RE.sub("_", value.strip().lower()).strip("_")
    return normalized if normalized in ALLOWED_ITEM_TYPES else "fact"


def make_prompt(title: str, key: str, transcript: str) -> list[dict[str, str]]:
    system = (
        "You classify private ChatGPT transcript material into durable memory signals. "
        "Use only the provided transcript. Return strict JSON only. Do not mention that "
        "you are an AI model. Do not invent facts. If the transcript has no durable "
        "signal, return an empty items list."
    )
    user = {
        "conversation_id": key,
        "title": title,
        "schema": {
            "room": "short lowercase topic slug",
            "summary": "one sentence grounded in the transcript",
            "items": [
                {
                    "type": "decision|preference|project|task|fact|problem|open_question",
                    "room": "optional short lowercase topic slug",
                    "text": "specific durable memory signal",
                    "importance": "integer 1-5",
                    "evidence": "short quote or paraphrase from the transcript",
                }
            ],
        },
        "rules": [
            "Return at most 6 items.",
            "Prefer concrete decisions, preferences, project facts, tasks, and recurring problems.",
            "Avoid generic summaries and transient small talk.",
            "Use room slugs such as projects, technical, planning, operations, decisions, preferences, people, finance, health, creative, research, or general.",
        ],
        "transcript": transcript,
    }
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
    ]


def clamp_importance(value: Any) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return 3
    return max(1, min(5, number))


def validate_classification(data: dict[str, Any]) -> tuple[str, str, list[dict[str, Any]]]:
    room = sanitize_room(data.get("room"))
    summary = data.get("summary")
    if not isinstance(summary, str):
        summary = ""
    items = data.get("items")
    if items is None:
        items = []
    if not isinstance(items, list):
        raise FatalRemoteError("LocalAI classification field 'items' must be a list")

    cleaned: list[dict[str, Any]] = []
    for item in items[:6]:
        if not isinstance(item, dict):
            raise FatalRemoteError("LocalAI classification item must be an object")
        text = item.get("text")
        if not isinstance(text, str) or not text.strip():
            continue
        cleaned.append(
            {
                "type": normalize_item_type(item.get("type")),
                "room": sanitize_room(item.get("room"), room),
                "text": text.strip(),
                "importance": clamp_importance(item.get("importance")),
                "evidence": str(item.get("evidence") or "").strip(),
            }
        )
    return room, summary.strip(), cleaned


def drawer_content(
    *,
    key: str,
    title: str,
    source_file: Path,
    summary: str,
    item: dict[str, Any],
) -> str:
    parts = [
        "LOCALAI_CLASSIFIED_SIGNAL",
        f"conversation_id: {key}",
        f"title: {title or '(untitled)'}",
        f"source_file: {source_file}",
        f"item_type: {item['type']}",
        f"importance: {item['importance']}",
    ]
    if summary:
        parts.append(f"conversation_summary: {summary}")
    parts.append("")
    parts.append(str(item["text"]))
    evidence = item.get("evidence")
    if evidence:
        parts.append("")
        parts.append(f"evidence: {evidence}")
    return "\n".join(parts)


def run(args: argparse.Namespace) -> int:
    source_dir = Path(args.source_dir)
    checkpoint = Path(args.checkpoint)
    seen = load_checkpoint(checkpoint)

    localai_base = ensure_localai_base_url(args.localai_base_url)
    localai_token = read_token(args.localai_token, args.localai_token_file, "LocalAI")
    mempalace_token = read_token(args.mempalace_token, args.mempalace_token_file, "MemPalace")

    mcp_call(
        base_url=args.mempalace_url,
        token=mempalace_token,
        tool_name="mempalace_reconnect",
        arguments={},
        timeout=args.mempalace_timeout,
    )

    processed = 0
    skipped = 0
    filed = 0
    started = time.time()
    for source_file, conversation in iter_conversations(source_dir):
        identity = extract_chatgpt_identity(conversation)
        if identity is None:
            key = conversation_key(source_file, conversation)
            if key in seen:
                skipped += 1
                continue
            messages = _collect_chatgpt_messages(conversation)
            if len(messages) < 2:
                append_checkpoint(checkpoint, {"key": key, "status": "skipped_empty"})
                seen[key] = "skipped_empty"
                skipped += 1
                continue
            title = str(conversation.get("title") or "").strip()
            transcript = _messages_to_transcript(messages, spellcheck=False)
        else:
            key = identity.logical_source_id
            if seen_checkpoint_key(seen, source_file, identity):
                skipped += 1
                continue
            title = identity.title or ""
            transcript = identity.transcript

        if len(transcript) > args.max_chars:
            transcript = transcript[: args.max_chars] + "\n\n[truncated for classification]"
        classification = localai_chat_completion(
            base_url=localai_base,
            token=localai_token,
            model=args.model,
            messages=make_prompt(title, key, transcript),
            timeout=args.localai_timeout,
        )
        default_room, summary, items = validate_classification(classification)
        for item in items:
            room = sanitize_room(item.get("room"), default_room)
            result = mcp_call(
                base_url=args.mempalace_url,
                token=mempalace_token,
                tool_name="mempalace_add_drawer",
                arguments={
                    "wing": args.wing,
                    "room": room,
                    "content": drawer_content(
                        key=key,
                        title=title,
                        source_file=source_file,
                        summary=summary,
                        item=item,
                    ),
                    "source_file": str(source_file),
                    "added_by": "localai_chatgpt_signals",
                },
                timeout=args.mempalace_timeout,
            )
            if not result.get("success"):
                raise FatalRemoteError(f"Could not file drawer for {key}: {result}")
            filed += 1
        append_checkpoint(
            checkpoint,
            {
                "key": key,
                "status": "classified",
                "items": len(items),
                "filed": filed,
                "elapsed_seconds": round(time.time() - started, 2),
            },
        )
        seen[key] = "classified"
        if identity is not None and isinstance(identity.conversation_id, str):
            seen[legacy_checkpoint_key(source_file, identity.conversation_id)] = "classified"
        processed += 1
        if processed % args.progress_every == 0:
            print(
                json.dumps(
                    {
                        "processed": processed,
                        "skipped": skipped,
                        "filed": filed,
                        "elapsed_seconds": round(time.time() - started, 2),
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
        if args.limit and processed >= args.limit:
            break

    mcp_call(
        base_url=args.mempalace_url,
        token=mempalace_token,
        tool_name="mempalace_reconnect",
        arguments={},
        timeout=args.mempalace_timeout,
    )
    print(
        json.dumps(
            {
                "status": "complete",
                "processed": processed,
                "skipped": skipped,
                "filed": filed,
                "elapsed_seconds": round(time.time() - started, 2),
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Classify ChatGPT privacy exports with LocalAI and file MemPalace signals."
    )
    parser.add_argument("--source-dir", default=os.environ.get("CHATGPT_SOURCE_DIR", DEFAULT_SOURCE_DIR))
    parser.add_argument("--checkpoint", default=os.environ.get("LOCALAI_SIGNAL_CHECKPOINT", DEFAULT_CHECKPOINT))
    parser.add_argument("--wing", default=os.environ.get("LOCALAI_SIGNAL_WING", "chatgpt_signals"))
    parser.add_argument("--model", default=os.environ.get("LOCALAI_MODEL") or os.environ.get("ARCHIVEKG_CHAT_ROLLUP_MODEL") or DEFAULT_MODEL)
    parser.add_argument("--localai-base-url", default=os.environ.get("LOCALAI_BASE_URL") or os.environ.get("ARCHIVEKG_OPENAI_BASE_URL") or DEFAULT_LOCALAI_BASE_URL)
    parser.add_argument("--localai-token", default=os.environ.get("LOCALAI_TOKEN") or os.environ.get("ARCHIVEKG_OPENAI_API_KEY"))
    parser.add_argument("--localai-token-file", default=os.environ.get("LOCALAI_TOKEN_FILE") or DEFAULT_LOCALAI_TOKEN_FILE)
    parser.add_argument("--mempalace-url", default=os.environ.get("MEMPALACE_HTTP_URL") or DEFAULT_MEMPALACE_URL)
    parser.add_argument("--mempalace-token", default=os.environ.get("MEMPALACE_HTTP_TOKEN"))
    parser.add_argument("--mempalace-token-file", default=os.environ.get("MEMPALACE_HTTP_TOKEN_FILE") or DEFAULT_MEMPALACE_TOKEN_FILE)
    parser.add_argument("--max-chars", type=int, default=int(os.environ.get("LOCALAI_SIGNAL_MAX_CHARS", "12000")))
    parser.add_argument("--limit", type=int, default=int(os.environ.get("LOCALAI_SIGNAL_LIMIT", "0")))
    parser.add_argument("--progress-every", type=int, default=int(os.environ.get("LOCALAI_SIGNAL_PROGRESS_EVERY", "10")))
    parser.add_argument("--localai-timeout", type=float, default=float(os.environ.get("LOCALAI_TIMEOUT", "180")))
    parser.add_argument("--mempalace-timeout", type=float, default=float(os.environ.get("MEMPALACE_HTTP_TIMEOUT", "120")))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        return run(parse_args(argv or sys.argv[1:]))
    except FatalRemoteError as exc:
        print(f"fatal: {exc}", file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
