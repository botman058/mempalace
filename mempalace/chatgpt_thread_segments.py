from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Optional

from .chatgpt_identity import ChatGPTIdentityRecord, extract_chatgpt_identity
from .normalize import _collect_chatgpt_messages, _messages_to_transcript

_DIGEST_LENGTH = 24
_TOPIC_WORD_RE = re.compile(r"[a-z0-9]{3,}")
_NEW_TOPIC_RE = re.compile(
    r"\b(new topic|switch(?:ing)? gears|another thing|separately|different question)\b",
    re.IGNORECASE,
)
_STOPWORDS = {
    "about",
    "after",
    "also",
    "because",
    "could",
    "from",
    "have",
    "just",
    "need",
    "please",
    "that",
    "this",
    "what",
    "with",
    "would",
    "your",
}


@dataclass(frozen=True)
class ChatGPTThreadSegment:
    segment_id: str
    subthread_id: str
    subthread_label: str
    logical_source_id: str
    conversation_id: Optional[str]
    title: Optional[str]
    source_hash: str
    segment_index: int
    message_start_index: int
    message_end_index: int
    char_start: int
    char_end: int
    content: str


@dataclass(frozen=True)
class _Turn:
    index: int
    role: str
    text: str
    rendered: str
    start: int
    end: int
    topic_tokens: frozenset[str]


def build_chatgpt_thread_segments(
    *,
    conversation: Optional[object] = None,
    identity: Optional[ChatGPTIdentityRecord] = None,
    messages: Optional[list[tuple[str, str]]] = None,
    transcript: Optional[str] = None,
    target_chars: int = 10_000,
    max_message_chars: int = 12_000,
    message_overlap_chars: int = 1_000,
    turn_overlap_count: int = 1,
) -> list[ChatGPTThreadSegment]:
    if target_chars < 64:
        raise ValueError("target_chars must be >= 64")
    if max_message_chars < target_chars:
        max_message_chars = target_chars
    if message_overlap_chars < 0:
        message_overlap_chars = 0

    resolved_identity = identity
    if resolved_identity is None and conversation is not None:
        resolved_identity = extract_chatgpt_identity(conversation)
    if resolved_identity is None:
        return []

    resolved_messages = messages
    if resolved_messages is None and conversation is not None:
        resolved_messages = _collect_chatgpt_messages(conversation)
    if not resolved_messages:
        return []

    if transcript is None:
        transcript = _messages_to_transcript(resolved_messages, spellcheck=False)

    turns = _build_turns(resolved_messages)
    if not turns:
        return []

    subthread_assignments = _assign_subthreads(turns)
    subthread_labels = _build_subthread_labels(turns, subthread_assignments)
    segment_rows = _segment_turns(
        turns=turns,
        subthread_assignments=subthread_assignments,
        target_chars=target_chars,
        max_message_chars=max_message_chars,
        message_overlap_chars=message_overlap_chars,
        turn_overlap_count=turn_overlap_count,
    )

    records: list[ChatGPTThreadSegment] = []
    for segment_index, row in enumerate(segment_rows):
        subthread_id = f"{resolved_identity.logical_source_id}:subthread:{row['subthread_index']:03d}"
        subthread_label = subthread_labels.get(row["subthread_index"], "general")
        content = row["content"]
        message_start = int(row["message_start"])
        message_end = int(row["message_end"])
        char_start = int(row["char_start"])
        char_end = int(row["char_end"])
        segment_id = _digest_text(
            "|".join(
                [
                    resolved_identity.logical_source_id,
                    resolved_identity.source_hash,
                    subthread_id,
                    str(segment_index),
                    str(message_start),
                    str(message_end),
                    str(char_start),
                    str(char_end),
                    content,
                ]
            )
        )
        records.append(
            ChatGPTThreadSegment(
                segment_id=segment_id,
                subthread_id=subthread_id,
                subthread_label=subthread_label,
                logical_source_id=resolved_identity.logical_source_id,
                conversation_id=resolved_identity.conversation_id,
                title=resolved_identity.title,
                source_hash=resolved_identity.source_hash,
                segment_index=segment_index,
                message_start_index=message_start,
                message_end_index=message_end,
                char_start=char_start,
                char_end=char_end,
                content=content,
            )
        )
    return records


def _build_turns(messages: list[tuple[str, str]]) -> list[_Turn]:
    turns: list[_Turn] = []
    cursor = 0
    for idx, item in enumerate(messages):
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
        tokens = _topic_tokens(text)
        turns.append(
            _Turn(
                index=idx,
                role=role,
                text=text,
                rendered=rendered,
                start=start,
                end=end,
                topic_tokens=tokens,
            )
        )
    return turns


def _topic_tokens(text: str) -> frozenset[str]:
    words = [w for w in _TOPIC_WORD_RE.findall(text.lower()) if w not in _STOPWORDS]
    return frozenset(words[:12])


def _assign_subthreads(turns: list[_Turn]) -> list[int]:
    if not turns:
        return []
    assignments: list[int] = []
    active_tokens: set[str] = set()
    current = 0
    for turn in turns:
        if not assignments:
            assignments.append(current)
            active_tokens = set(turn.topic_tokens)
            continue
        overlap = len(active_tokens.intersection(turn.topic_tokens))
        new_topic = bool(
            turn.role == "user"
            and (
                _NEW_TOPIC_RE.search(turn.text)
                or (len(turn.topic_tokens) >= 3 and overlap == 0 and len(active_tokens) >= 3)
            )
        )
        if new_topic:
            current += 1
            active_tokens = set(turn.topic_tokens)
        else:
            active_tokens.update(turn.topic_tokens)
        assignments.append(current)
    return assignments


def _build_subthread_labels(turns: list[_Turn], assignments: list[int]) -> dict[int, str]:
    by_subthread: dict[int, dict[str, int]] = {}
    for turn, sub in zip(turns, assignments):
        bucket = by_subthread.setdefault(sub, {})
        for token in turn.topic_tokens:
            bucket[token] = bucket.get(token, 0) + 1
    labels: dict[int, str] = {}
    for sub, counts in by_subthread.items():
        if not counts:
            labels[sub] = f"subthread_{sub + 1}"
            continue
        ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        labels[sub] = ordered[0][0]
    return labels


def _segment_turns(
    *,
    turns: list[_Turn],
    subthread_assignments: list[int],
    target_chars: int,
    max_message_chars: int,
    message_overlap_chars: int,
    turn_overlap_count: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    i = 0
    while i < len(turns):
        turn = turns[i]
        sub_idx = subthread_assignments[i]
        turn_len = len(turn.rendered)
        if turn_len > max_message_chars:
            rows.extend(
                _split_oversized_turn(
                    turn=turn,
                    subthread_index=sub_idx,
                    target_chars=target_chars,
                    overlap_chars=message_overlap_chars,
                )
            )
            i += 1
            continue

        end = i
        total = 0
        while end < len(turns):
            if subthread_assignments[end] != sub_idx:
                break
            next_len = len(turns[end].rendered)
            if total and total + next_len > target_chars:
                break
            if next_len > max_message_chars:
                break
            total += next_len
            end += 1
        if end == i:
            rows.extend(
                _split_oversized_turn(
                    turn=turn,
                    subthread_index=sub_idx,
                    target_chars=target_chars,
                    overlap_chars=message_overlap_chars,
                )
            )
            i += 1
            continue

        segment_turns = turns[i:end]
        rows.append(
            {
                "subthread_index": sub_idx,
                "message_start": segment_turns[0].index,
                "message_end": segment_turns[-1].index,
                "char_start": segment_turns[0].start,
                "char_end": segment_turns[-1].end,
                "content": "".join(t.rendered for t in segment_turns),
            }
        )

        if end >= len(turns):
            break
        overlap = max(0, turn_overlap_count)
        i = max(i + 1, end - overlap)
    return rows


def _split_oversized_turn(
    *,
    turn: _Turn,
    subthread_index: int,
    target_chars: int,
    overlap_chars: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    text = turn.rendered
    start_local = 0
    step = max(1, target_chars - overlap_chars)
    while start_local < len(text):
        end_local = min(len(text), start_local + target_chars)
        chunk = text[start_local:end_local]
        rows.append(
            {
                "subthread_index": subthread_index,
                "message_start": turn.index,
                "message_end": turn.index,
                "char_start": turn.start + start_local,
                "char_end": turn.start + end_local,
                "content": chunk,
            }
        )
        if end_local >= len(text):
            break
        start_local += step
    return rows


def _digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:_DIGEST_LENGTH]
