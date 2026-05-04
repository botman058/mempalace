from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional

from .normalize import _collect_chatgpt_messages, _messages_to_transcript

_DIGEST_LENGTH = 24


@dataclass(frozen=True)
class ChatGPTIdentityRecord:
    logical_source_id: str
    conversation_id: Optional[str]
    title: Optional[str]
    transcript: str
    source_hash: str


def extract_chatgpt_identity(conversation: object) -> Optional[ChatGPTIdentityRecord]:
    """Return a stable identity record for one ChatGPT conversation dict."""
    if not isinstance(conversation, dict):
        return None

    mapping = conversation.get("mapping")
    if not isinstance(mapping, dict):
        return None

    messages = _collect_chatgpt_messages(conversation)
    if len(messages) < 2:
        return None

    transcript = _messages_to_transcript(messages)
    hash_transcript = _messages_to_transcript(messages, spellcheck=False)
    conversation_id = _get_conversation_id(conversation)
    title = conversation.get("title")
    if not isinstance(title, str):
        title = None

    if conversation_id:
        logical_source_id = f"chatgpt:{conversation_id}"
    else:
        logical_source_id = f"chatgpt:sha256:{_json_digest(mapping)}"

    return ChatGPTIdentityRecord(
        logical_source_id=logical_source_id,
        conversation_id=conversation_id,
        title=title,
        transcript=transcript,
        source_hash=_text_digest(hash_transcript),
    )


def iter_chatgpt_identity_records_from_json_file(path: str | Path) -> Iterator[ChatGPTIdentityRecord]:
    """Yield ChatGPT identity records from a JSON file containing one export."""
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)

    if isinstance(data, dict):
        record = extract_chatgpt_identity(data)
        if record is not None:
            yield record
        return

    if not isinstance(data, list):
        return

    for item in data:
        record = extract_chatgpt_identity(item)
        if record is not None:
            yield record


def _get_conversation_id(conversation: dict) -> Optional[str]:
    for key in ("id", "conversation_id"):
        value = conversation.get(key)
        if isinstance(value, str):
            value = value.strip()
            if value:
                return value
    return None


def _json_digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return _text_digest(payload)


def _text_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:_DIGEST_LENGTH]
