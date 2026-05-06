#!/usr/bin/env python3
"""Segment-level ChatGPT thread signal extraction with progressive checkpoints."""

from __future__ import annotations

import argparse
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
DEFAULT_LOCALAI_BASE_URL = "http://snow-white-iii:8080/v1"
DEFAULT_LOCALAI_TOKEN_FILE = "/media/u0/OneDrive_Backup/mempalace/secrets/localai_token"
DEFAULT_MODEL = "qwen3-vl-8b-instruct"
EXTRACTION_VERSION = "localai_chatgpt_thread_signals_v1"
_MAX_EVIDENCE_CHARS = 280
_MAX_INVALID_EXCERPT_CHARS = 500
_MAX_SEGMENT_EXCERPT_CHARS = 320
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


def run(args: argparse.Namespace, *, provider: SegmentProvider | None = None) -> int:
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
    print(
        json.dumps(
            {
                "status": "complete",
                "processed_segments": processed,
                "skipped_segments": skipped,
                "classified_segments": classified,
                "invalid_segments": invalid,
                "error_segments": errors,
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
