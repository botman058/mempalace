from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Optional

from . import chatgpt_archive_atlas_contract as contract
from .chatgpt_archive_atlas_source import (
    ChatGPTAtlasSourceConversation,
    load_chatgpt_archive_source_dir,
)
from .normalize import _collect_chatgpt_messages

_DIGEST_LENGTH = 24
_EXPLICIT_SWITCH_RE = re.compile(
    r"\b(explicit topic switch|new topic|switch(?:ing)? gears|another thing|separately|different question)\b",
    re.IGNORECASE,
)
_LEGAL_PATTERNS = (
    "agreement",
    "clause",
    "contract",
    "data retention",
    "gdpr",
    "hold harmless",
    "indemnif",
    "legal",
    "liabilit",
    "negligence",
    "section ",
    "tenant",
    "vendor",
)
_SYSADMIN_PATTERNS = (
    "/var/log/",
    "auth.log",
    "deploy",
    "deployment",
    "failed logins",
    "logins",
    "nginx",
    "restart ssh",
    "reverse-proxy",
    "server",
    "smoke tests",
    "ssh",
    "sudo",
    "systemctl",
    "tail -n",
)
_PERSONAL_PATTERNS = (
    "bring my sister",
    "family",
    "forget",
    "itinerary",
    "personal",
    "recital",
    "saturday",
    "sunday",
    "weekend",
)


@dataclass(frozen=True)
class ChatGPTAtlasThreadIndexResult:
    rows: tuple[dict[str, Any], ...]
    source_errors: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class _Turn:
    index: int
    role: str
    text: str
    rendered: str
    start: int
    end: int
    domain: str


def build_chatgpt_thread_index_rows(
    conversations,
    *,
    run_id: str,
    excerpt_chars: int = 500,
) -> tuple[dict[str, Any], ...]:
    excerpt_limit = _validate_nonnegative_int("excerpt_chars", excerpt_chars)
    rows: list[dict[str, Any]] = []

    for source_record in conversations:
        if not isinstance(source_record, ChatGPTAtlasSourceConversation):
            continue

        messages = _collect_chatgpt_messages(source_record.conversation)
        if not messages:
            continue

        turns = _build_turns(messages)
        if not turns:
            continue

        threads = _segment_turns(turns)
        for thread_index, thread in enumerate(threads):
            thread_turns = turns[thread["start_turn"] : thread["end_turn"]]
            if not thread_turns:
                continue

            row = contract.build_thread_index_row(
                run_id=run_id,
                thread_id=_build_thread_id(
                    logical_source_id=source_record.identity.logical_source_id,
                    source_hash=source_record.source_hash,
                    thread_index=thread_index,
                    message_start_index=thread_turns[0].index,
                    message_end_index=thread_turns[-1].index,
                    char_start=thread_turns[0].start,
                    char_end=thread_turns[-1].end,
                    transition_reasons=thread["transition_reasons"],
                ),
                logical_source_id=source_record.identity.logical_source_id,
                conversation_id=source_record.identity.conversation_id,
                conversation_title=source_record.identity.title,
                source_hash=source_record.source_hash,
                thread_index=thread_index,
                message_start_index=thread_turns[0].index,
                message_end_index=thread_turns[-1].index,
                char_start=thread_turns[0].start,
                char_end=thread_turns[-1].end,
                user_message_count=sum(1 for turn in thread_turns if turn.role == "user"),
                assistant_message_count=sum(1 for turn in thread_turns if turn.role == "assistant"),
                char_count=thread_turns[-1].end - thread_turns[0].start,
                title_hint=_build_title_hint(thread_turns, excerpt_limit),
                representative_excerpt=_build_representative_excerpt(thread_turns, excerpt_limit),
            )
            row.update(
                {
                    "transition_reasons": list(thread["transition_reasons"]),
                    "conversation_create_time": _stringify_optional(
                        source_record.conversation.get("create_time")
                    ),
                    "conversation_update_time": _stringify_optional(
                        source_record.conversation.get("update_time")
                    ),
                    "source_relative_path": source_record.source_relative_path,
                    "source_ordinal": source_record.source_ordinal,
                    "top_level_shape": source_record.top_level_shape,
                }
            )
            contract.validate_row(row["schema"], row)
            rows.append(row)

    return tuple(rows)


def build_chatgpt_thread_index(
    source_dir,
    *,
    run_id: str,
    excerpt_chars: int = 500,
) -> ChatGPTAtlasThreadIndexResult:
    loaded = load_chatgpt_archive_source_dir(source_dir)
    rows = build_chatgpt_thread_index_rows(
        loaded.conversations,
        run_id=run_id,
        excerpt_chars=excerpt_chars,
    )
    return ChatGPTAtlasThreadIndexResult(rows=rows, source_errors=loaded.source_errors)


def _build_turns(messages: list[tuple[str, str]]) -> list[_Turn]:
    turns: list[_Turn] = []
    cursor = 0
    for index, item in enumerate(messages):
        if not isinstance(item, tuple) or len(item) != 2:
            continue
        role, text = item
        if role not in {"user", "assistant"}:
            continue
        if not isinstance(text, str) or not text:
            continue
        rendered = f"> {text}\n\n" if role == "user" else f"{text}\n\n"
        start = cursor
        end = start + len(rendered)
        cursor = end
        turns.append(
            _Turn(
                index=index,
                role=role,
                text=text,
                rendered=rendered,
                start=start,
                end=end,
                domain=_classify_domain(text),
            )
        )
    return turns


def _segment_turns(turns: list[_Turn]) -> list[dict[str, object]]:
    if not turns:
        return []

    boundaries: list[dict[str, object]] = [{"start_turn": 0, "transition_reasons": ("conversation_start",)}]
    current_thread_start = 0

    for turn_index, turn in enumerate(turns):
        if turn_index == 0 or turn.role != "user":
            continue
        reasons = _transition_reasons(turns, current_thread_start, turn_index)
        if not reasons:
            continue
        boundaries.append(
            {
                "start_turn": turn_index,
                "transition_reasons": tuple(reasons),
            }
        )
        current_thread_start = turn_index

    rows: list[dict[str, object]] = []
    for index, boundary in enumerate(boundaries):
        start_turn = int(boundary["start_turn"])
        if index + 1 < len(boundaries):
            end_turn = int(boundaries[index + 1]["start_turn"])
        else:
            end_turn = len(turns)
        rows.append(
            {
                "start_turn": start_turn,
                "end_turn": end_turn,
                "transition_reasons": boundary["transition_reasons"],
            }
        )
    return rows


def _transition_reasons(
    turns: list[_Turn],
    current_thread_start: int,
    candidate_index: int,
) -> list[str]:
    turn = turns[candidate_index]
    reasons: list[str] = []

    if _EXPLICIT_SWITCH_RE.search(turn.text):
        reasons.append("explicit_topic_switch")

    current_domain = _dominant_user_domain(turns[current_thread_start:candidate_index])
    next_domain = turn.domain
    if current_domain != "general" and next_domain != "general" and current_domain != next_domain:
        reasons.append(f"domain_shift:{current_domain}_to_{next_domain}")

    return reasons


def _dominant_user_domain(turns: list[_Turn]) -> str:
    counts: dict[str, int] = {}
    for turn in turns:
        if turn.role != "user":
            continue
        counts[turn.domain] = counts.get(turn.domain, 0) + 1
    best_domain = "general"
    best_count = 0
    for domain, count in counts.items():
        if domain == "general":
            continue
        if count > best_count or (count == best_count and domain < best_domain):
            best_domain = domain
            best_count = count
    return best_domain


def _classify_domain(text: str) -> str:
    lowered = text.lower()
    legal_score = _domain_score(lowered, _LEGAL_PATTERNS)
    sysadmin_score = _domain_score(lowered, _SYSADMIN_PATTERNS)
    personal_score = _domain_score(lowered, _PERSONAL_PATTERNS)

    scores = [
        ("legal", legal_score),
        ("personal", personal_score),
        ("sysadmin", sysadmin_score),
    ]
    scores.sort(key=lambda item: (-item[1], item[0]))
    if not scores or scores[0][1] <= 0:
        return "general"
    return scores[0][0]


def _domain_score(text: str, patterns: tuple[str, ...]) -> int:
    return sum(1 for pattern in patterns if pattern in text)


def _build_title_hint(turns: list[_Turn], excerpt_chars: int) -> Optional[str]:
    user_turn = _first_user_turn(turns)
    if user_turn is None:
        return None
    text = _strip_transition_prefix(user_turn.text)
    return _truncate_text(text, min(excerpt_chars, 120))


def _build_representative_excerpt(turns: list[_Turn], excerpt_chars: int) -> Optional[str]:
    user_turns = [(index, turn.text) for index, turn in enumerate(turns) if turn.role == "user"]
    if user_turns:
        ranked = sorted(user_turns, key=lambda item: (-len(item[1]), item[0]))
        return _truncate_text(ranked[0][1], excerpt_chars)
    if turns:
        return _truncate_text(turns[0].text, excerpt_chars)
    return None


def _first_user_turn(turns: list[_Turn]) -> Optional[_Turn]:
    for turn in turns:
        if turn.role == "user":
            return turn
    return None


def _strip_transition_prefix(text: str) -> str:
    cleaned = re.sub(r"^\s*explicit topic switch\s*:\s*", "", text, flags=re.IGNORECASE)
    return cleaned.strip() or text.strip()


def _build_thread_id(
    *,
    logical_source_id: str,
    source_hash: str,
    thread_index: int,
    message_start_index: int,
    message_end_index: int,
    char_start: int,
    char_end: int,
    transition_reasons: tuple[str, ...],
) -> str:
    digest = _digest_text(
        "|".join(
            [
                logical_source_id,
                source_hash,
                str(message_start_index),
                str(message_end_index),
                str(char_start),
                str(char_end),
                ",".join(transition_reasons),
            ]
        )
    )
    return f"{logical_source_id}:thread:{thread_index:03d}:{digest}"


def _digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:_DIGEST_LENGTH]


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


def _validate_nonnegative_int(name: str, value: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value
