from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Optional

from . import chatgpt_archive_atlas_contract as contract
from .chatgpt_identity import ChatGPTIdentityRecord, extract_chatgpt_identity

SOURCE_FILENAME = "conversations.json"


@dataclass(frozen=True)
class ChatGPTAtlasSourceConversation:
    conversation: dict[str, Any]
    identity: ChatGPTIdentityRecord
    source_path: Path
    source_relative_path: str
    source_hash: str
    source_version_token: str
    source_ordinal: int
    top_level_shape: str


@dataclass(frozen=True)
class ChatGPTAtlasSourceLoadResult:
    conversations: tuple[ChatGPTAtlasSourceConversation, ...]
    source_errors: tuple[dict[str, Any], ...]


def iter_chatgpt_conversation_json_files(source_dir: str | Path) -> Iterator[Path]:
    root = Path(source_dir)
    if not root.exists() or not root.is_dir():
        return

    files: list[tuple[str, Path]] = []
    for path in root.rglob(SOURCE_FILENAME):
        if not path.is_file() or path.name != SOURCE_FILENAME:
            continue
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError:
            continue
        files.append((relative, path))

    for _, path in sorted(files, key=lambda item: item[0]):
        yield path


def load_chatgpt_conversation_json_file(
    source_path: str | Path,
    *,
    source_dir: str | Path,
) -> ChatGPTAtlasSourceLoadResult:
    path = Path(source_path)
    root = Path(source_dir)
    source_relative_path = _safe_source_relative_path(path, root)
    if source_relative_path is None:
        return ChatGPTAtlasSourceLoadResult(
            conversations=(),
            source_errors=(
                _build_source_error_row(
                    source_path=path,
                    source_relative_path=None,
                    source_hash=None,
                    source_ordinal=None,
                    top_level_shape=None,
                    error_code="source_relative_path_error",
                    error_detail="source file must stay under source_dir",
                ),
            ),
        )

    try:
        source_text = _read_source_text(path)
    except OSError as exc:
        return ChatGPTAtlasSourceLoadResult(
            conversations=(),
            source_errors=(
                _build_source_error_row(
                    source_path=path,
                    source_relative_path=source_relative_path,
                    source_hash=None,
                    source_ordinal=None,
                    top_level_shape=None,
                    error_code="source_read_error",
                    error_detail=str(exc),
                ),
            ),
        )

    source_hash = _source_text_hash(source_text)

    try:
        payload = json.loads(source_text)
    except json.JSONDecodeError as exc:
        return ChatGPTAtlasSourceLoadResult(
            conversations=(),
            source_errors=(
                _build_source_error_row(
                    source_path=path,
                    source_relative_path=source_relative_path,
                    source_hash=source_hash,
                    source_ordinal=None,
                    top_level_shape=None,
                    error_code="source_json_decode_error",
                    error_detail=str(exc),
                ),
            ),
        )

    top_level_shape = _top_level_shape(payload)
    if top_level_shape is None:
        return ChatGPTAtlasSourceLoadResult(
            conversations=(),
            source_errors=(
                _build_source_error_row(
                    source_path=path,
                    source_relative_path=source_relative_path,
                    source_hash=source_hash,
                    source_ordinal=None,
                    top_level_shape=type(payload).__name__,
                    error_code="source_shape_error",
                    error_detail=(
                        "top-level JSON must be an object or array, "
                        f"got {type(payload).__name__}"
                    ),
                ),
            ),
        )

    items = [payload] if isinstance(payload, dict) else payload
    conversations: list[ChatGPTAtlasSourceConversation] = []
    source_errors: list[dict[str, Any]] = []

    for source_ordinal, item in enumerate(items):
        if not isinstance(item, dict):
            source_errors.append(
                _build_source_error_row(
                    source_path=path,
                    source_relative_path=source_relative_path,
                    source_hash=source_hash,
                    source_ordinal=source_ordinal,
                    top_level_shape=top_level_shape,
                    error_code="source_shape_error",
                    error_detail=(
                        f"conversation item {source_ordinal} must be an object, "
                        f"got {type(item).__name__}"
                    ),
                )
            )
            continue

        identity = extract_chatgpt_identity(item)
        if identity is None:
            source_errors.append(
                _build_source_error_row(
                    source_path=path,
                    source_relative_path=source_relative_path,
                    source_hash=source_hash,
                    source_ordinal=source_ordinal,
                    top_level_shape=top_level_shape,
                    error_code="source_shape_error",
                    error_detail=(
                        f"conversation item {source_ordinal} is not a valid ChatGPT "
                        "conversation export"
                    ),
                )
            )
            continue

        conversations.append(
            ChatGPTAtlasSourceConversation(
                conversation=item,
                identity=identity,
                source_path=path,
                source_relative_path=source_relative_path,
                source_hash=source_hash,
                source_version_token=source_hash,
                source_ordinal=source_ordinal,
                top_level_shape=top_level_shape,
            )
        )

    if conversations or source_errors:
        return ChatGPTAtlasSourceLoadResult(
            conversations=tuple(conversations),
            source_errors=tuple(source_errors),
        )

    return ChatGPTAtlasSourceLoadResult(
        conversations=(),
        source_errors=(
            _build_source_error_row(
                source_path=path,
                source_relative_path=source_relative_path,
                source_hash=source_hash,
                source_ordinal=None,
                top_level_shape=top_level_shape,
                error_code="source_shape_error",
                error_detail="no valid ChatGPT conversations found in source file",
            ),
        ),
    )


def load_chatgpt_archive_source_dir(source_dir: str | Path) -> ChatGPTAtlasSourceLoadResult:
    conversations: list[ChatGPTAtlasSourceConversation] = []
    source_errors: list[dict[str, Any]] = []

    for path in iter_chatgpt_conversation_json_files(source_dir):
        loaded = load_chatgpt_conversation_json_file(path, source_dir=source_dir)
        conversations.extend(loaded.conversations)
        source_errors.extend(loaded.source_errors)

    return ChatGPTAtlasSourceLoadResult(
        conversations=tuple(conversations),
        source_errors=tuple(source_errors),
    )


def iter_chatgpt_archive_source_conversations(
    source_dir: str | Path,
) -> Iterator[ChatGPTAtlasSourceConversation]:
    for path in iter_chatgpt_conversation_json_files(source_dir):
        loaded = load_chatgpt_conversation_json_file(path, source_dir=source_dir)
        for conversation in loaded.conversations:
            yield conversation


def _safe_source_relative_path(source_path: Path, source_dir: Path) -> Optional[str]:
    try:
        resolved_path = source_path.resolve()
        resolved_root = source_dir.resolve()
    except OSError:
        return None

    try:
        relative = resolved_path.relative_to(resolved_root)
    except ValueError:
        return None

    raw = relative.as_posix()
    if not raw or raw in {".", ".."}:
        return None
    if any(part in {"", ".", ".."} for part in relative.parts):
        return None
    return raw


def _read_source_text(path: Path) -> str:
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        return handle.read()


def _source_text_hash(source_text: str) -> str:
    return f"sha256:{hashlib.sha256(source_text.encode('utf-8')).hexdigest()}"


def _top_level_shape(payload: object) -> Optional[str]:
    if isinstance(payload, dict):
        return "dict"
    if isinstance(payload, list):
        return "list"
    return None


def _build_source_error_row(
    *,
    source_path: Path,
    source_relative_path: Optional[str],
    source_hash: Optional[str],
    source_ordinal: Optional[int],
    top_level_shape: Optional[str],
    error_code: str,
    error_detail: str,
) -> dict[str, Any]:
    row = {
        "source_path": str(source_path),
        "source_relative_path": source_relative_path,
        "source_hash": source_hash,
        "source_version_token": source_hash,
        "source_ordinal": source_ordinal,
        "top_level_shape": top_level_shape,
        "status": "error",
        "error_code": error_code,
        "error_detail": error_detail,
        "safety_contract": contract.safety_contract(),
    }
    contract.validate_json_safe(row)
    return row
