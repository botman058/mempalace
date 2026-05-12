from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from . import chatgpt_archive_atlas_contract as contract
from .chatgpt_archive_atlas_source import (
    ChatGPTAtlasSourceConversation,
    load_chatgpt_archive_source_dir,
)
from .normalize import _collect_chatgpt_messages


@dataclass(frozen=True)
class ChatGPTAtlasConversationIndexResult:
    rows: tuple[dict[str, Any], ...]
    source_errors: tuple[dict[str, Any], ...]


def build_chatgpt_conversation_index_rows(
    conversations,
    *,
    run_id: str,
    excerpt_chars: int = 500,
    top_prompt_count: int = 5,
) -> tuple[dict[str, Any], ...]:
    excerpt_limit = _validate_nonnegative_int("excerpt_chars", excerpt_chars)
    prompt_limit = _validate_nonnegative_int("top_prompt_count", top_prompt_count)

    rows: list[dict[str, Any]] = []
    for source_record in conversations:
        if not isinstance(source_record, ChatGPTAtlasSourceConversation):
            continue

        messages = _collect_chatgpt_messages(source_record.conversation)
        if not messages:
            continue

        user_messages = [(index, text) for index, (role, text) in enumerate(messages) if role == "user"]
        assistant_messages = [text for role, text in messages if role == "assistant"]
        first_user_excerpt = None
        if user_messages:
            first_user_excerpt = _truncate_text(user_messages[0][1], excerpt_limit)

        row = contract.build_conversation_index_row(
            run_id=run_id,
            logical_source_id=source_record.identity.logical_source_id,
            conversation_id=source_record.identity.conversation_id,
            title=source_record.identity.title,
            source_relative_path=source_record.source_relative_path,
            source_hash=source_record.source_hash,
            source_ordinal=source_record.source_ordinal,
            create_time=_stringify_optional(source_record.conversation.get("create_time")),
            update_time=_stringify_optional(source_record.conversation.get("update_time")),
            model_slug=_extract_model_slug(source_record.conversation, messages),
            plugin_ids=_extract_plugin_ids(source_record.conversation, messages),
            message_count=len(messages),
            user_message_count=len(user_messages),
            assistant_message_count=len(assistant_messages),
            char_count=sum(len(text) for _, text in messages),
            first_user_excerpt=first_user_excerpt,
            top_user_prompt_excerpts=_top_user_prompt_excerpts(
                user_messages,
                excerpt_chars=excerpt_limit,
                top_prompt_count=prompt_limit,
            ),
        )
        rows.append(row)

    return tuple(rows)


def build_chatgpt_conversation_index(
    source_dir,
    *,
    run_id: str,
    excerpt_chars: int = 500,
    top_prompt_count: int = 5,
) -> ChatGPTAtlasConversationIndexResult:
    loaded = load_chatgpt_archive_source_dir(source_dir)
    rows = build_chatgpt_conversation_index_rows(
        loaded.conversations,
        run_id=run_id,
        excerpt_chars=excerpt_chars,
        top_prompt_count=top_prompt_count,
    )
    return ChatGPTAtlasConversationIndexResult(
        rows=rows,
        source_errors=loaded.source_errors,
    )


def _top_user_prompt_excerpts(
    user_messages: list[tuple[int, str]],
    *,
    excerpt_chars: int,
    top_prompt_count: int,
) -> list[str]:
    ranked = sorted(user_messages, key=lambda item: (-len(item[1]), item[0]))
    return [_truncate_text(text, excerpt_chars) for _, text in ranked[:top_prompt_count]]


def _truncate_text(text: str, limit: int) -> str:
    if limit <= 0:
        return ""
    return text[:limit]


def _stringify_optional(value: object) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return str(value)
    return None


def _extract_model_slug(
    conversation: dict[str, Any],
    messages: list[tuple[str, str]],
) -> Optional[str]:
    for key in ("model_slug", "default_model_slug"):
        value = conversation.get(key)
        if isinstance(value, str) and value:
            return value

    assistant_count = 0
    for metadata in _selected_message_metadata(conversation):
        role = _metadata_role(metadata)
        if role == "assistant":
            assistant_count += 1
        if role not in {None, "assistant"}:
            continue
        for key in ("model_slug", "default_model_slug"):
            value = metadata.get(key)
            if isinstance(value, str) and value:
                return value

    if assistant_count == 0 and any(role == "assistant" for role, _ in messages):
        for metadata in _selected_message_metadata(conversation):
            for key in ("model_slug", "default_model_slug"):
                value = metadata.get(key)
                if isinstance(value, str) and value:
                    return value
    return None


def _extract_plugin_ids(
    conversation: dict[str, Any],
    messages: list[tuple[str, str]],
) -> list[str]:
    plugin_ids: list[str] = []
    seen: set[str] = set()

    def add(value: object) -> None:
        for item in _coerce_plugin_ids(value):
            if item not in seen:
                seen.add(item)
                plugin_ids.append(item)

    for key in ("plugin_ids", "plugins"):
        add(conversation.get(key))
    for key in ("gizmo_id", "conversation_template_id"):
        value = conversation.get(key)
        if isinstance(value, str) and value:
            add([value])

    for metadata in _selected_message_metadata(conversation):
        role = _metadata_role(metadata)
        if role not in {None, "assistant", "tool"}:
            continue
        for key in (
            "plugin_ids",
            "plugins",
            "invoked_plugin_ids",
            "enabled_plugin_ids",
            "mentioned_plugin_ids",
            "gizmo_id",
            "conversation_template_id",
        ):
            add(metadata.get(key))

    if plugin_ids or not any(role == "assistant" for role, _ in messages):
        return plugin_ids
    return plugin_ids


def _selected_message_metadata(conversation: dict[str, Any]) -> list[dict[str, Any]]:
    mapping = conversation.get("mapping")
    if not isinstance(mapping, dict):
        return []

    current_node = conversation.get("current_node")
    if isinstance(current_node, str) and current_node in mapping:
        node_ids = _walk_chatgpt_current_path(mapping, current_node)
    else:
        node_ids = _walk_chatgpt_first_child_path(mapping)

    selected: list[dict[str, Any]] = []
    for node_id in node_ids:
        node = mapping.get(node_id)
        if not isinstance(node, dict):
            continue
        message = node.get("message")
        if not isinstance(message, dict):
            continue
        metadata = message.get("metadata")
        if isinstance(metadata, dict):
            selected.append(metadata)
    return selected


def _metadata_role(metadata: dict[str, Any]) -> Optional[str]:
    author = metadata.get("author")
    if isinstance(author, dict):
        role = author.get("role")
        if isinstance(role, str) and role:
            return role
    role = metadata.get("role")
    if isinstance(role, str) and role:
        return role
    return None


def _coerce_plugin_ids(value: object) -> list[str]:
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, dict):
        result: list[str] = []
        for key in ("id", "plugin_id", "namespace"):
            item = value.get(key)
            if isinstance(item, str) and item:
                result.append(item)
        return result
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(_coerce_plugin_ids(item))
        return result
    return []


def _walk_chatgpt_current_path(mapping: dict[str, Any], current_node: str) -> list[str]:
    node_ids: list[str] = []
    visited: set[str] = set()
    node_id = current_node
    while node_id and node_id not in visited:
        visited.add(node_id)
        node = mapping.get(node_id)
        if not isinstance(node, dict):
            break
        node_ids.append(node_id)
        parent = node.get("parent")
        node_id = parent if isinstance(parent, str) else ""
    node_ids.reverse()
    return node_ids


def _walk_chatgpt_first_child_path(mapping: dict[str, Any]) -> list[str]:
    root_id = None
    fallback_root = None
    for node_id, node in mapping.items():
        if not isinstance(node, dict):
            continue
        if node.get("parent") is None:
            if node.get("message") is None:
                root_id = node_id
                break
            if fallback_root is None:
                fallback_root = node_id
    if root_id is None:
        root_id = fallback_root

    node_ids: list[str] = []
    current_id = root_id
    visited: set[str] = set()
    while isinstance(current_id, str) and current_id and current_id not in visited:
        visited.add(current_id)
        node = mapping.get(current_id, {})
        if not isinstance(node, dict):
            break
        node_ids.append(current_id)
        children = node.get("children", [])
        if isinstance(children, list) and children:
            child = children[0]
            current_id = child if isinstance(child, str) else None
        else:
            current_id = None
    return node_ids


def _validate_nonnegative_int(name: str, value: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value
