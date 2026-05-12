from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Optional

from . import chatgpt_archive_atlas_contract as contract
from .chatgpt_archive_atlas_lexical_policy import POLICY_VERSION, extract_lexical_evidence
from .chatgpt_archive_atlas_source import (
    ChatGPTAtlasSourceConversation,
    load_chatgpt_archive_source_dir,
)
from .chatgpt_archive_atlas_thread import build_chatgpt_thread_index_rows
from .normalize import _collect_chatgpt_messages

_DATE_RE = re.compile(
    r"\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}|"
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b",
    re.IGNORECASE,
)
_LEGAL_SIGNAL_RE = re.compile(
    r"\b(?:Section\s+\d+[A-Za-z-]*|GDPR|hold harmless|indemnif(?:y|ication|ies)?|"
    r"liabilit(?:y|ies)|negligence)\b",
    re.IGNORECASE,
)
_PERSON_OR_ORG_STOPWORDS = frozenset(
    {
        "Brown",
        "Federal",
        "January",
        "February",
        "March",
        "April",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
        "Rule",
    }
)


@dataclass(frozen=True)
class ChatGPTAtlasLexicalSketchResult:
    rows: tuple[dict[str, Any], ...]
    source_errors: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class _RenderedTurn:
    index: int
    role: str
    text: str
    rendered: str
    start: int
    end: int


def build_chatgpt_lexical_sketch_rows(
    conversations,
    *,
    run_id: str,
    max_terms: int = 20,
    max_items_per_kind: int = 20,
    excerpt_chars: int = 500,
) -> tuple[dict[str, Any], ...]:
    term_limit = _validate_nonnegative_int("max_terms", max_terms)
    item_limit = _validate_nonnegative_int("max_items_per_kind", max_items_per_kind)
    excerpt_limit = _validate_nonnegative_int("excerpt_chars", excerpt_chars)

    source_records = [
        record for record in conversations if isinstance(record, ChatGPTAtlasSourceConversation)
    ]
    if not source_records:
        return ()

    thread_rows = build_chatgpt_thread_index_rows(
        source_records,
        run_id=run_id,
        excerpt_chars=excerpt_limit,
    )
    if not thread_rows:
        return ()

    transcript_context = _build_transcript_context(source_records)
    rows: list[dict[str, Any]] = []

    for thread_row in thread_rows:
        matched = _match_source_record(transcript_context, thread_row)
        if matched is None:
            continue

        source_record, turns, transcript = matched
        char_start = _coerce_nonnegative_int(thread_row.get("char_start"))
        char_end = _coerce_nonnegative_int(thread_row.get("char_end"))
        if char_start is None or char_end is None or char_start >= char_end or char_end > len(transcript):
            continue

        thread_turns = [
            turn for turn in turns if turn.start >= char_start and turn.end <= char_end
        ]
        thread_text = transcript[char_start:char_end]
        evidence = extract_lexical_evidence(
            thread_text,
            max_terms=term_limit,
            max_items_per_kind=item_limit,
        )
        representative_excerpts = _build_representative_excerpts(
            thread_row=thread_row,
            thread_turns=thread_turns,
            thread_text=thread_text,
            excerpt_chars=excerpt_limit,
            limit=item_limit,
        )

        row = contract.build_lexical_sketch_row(
            run_id=run_id,
            thread_id=str(thread_row["thread_id"]),
            logical_source_id=str(thread_row["logical_source_id"]),
            top_terms=evidence.top_terms,
            keyphrases=evidence.keyphrases,
            domains=evidence.domains,
            paths=evidence.paths,
            commands=evidence.commands,
            package_names=evidence.package_names,
            model_names=evidence.model_names,
            legal_citations=_build_legal_citations(
                evidence.legal_citations,
                thread_text,
                item_limit,
            ),
            capitalized_phrases=evidence.capitalized_phrases,
            representative_excerpts=representative_excerpts,
            noise_terms_rejected=evidence.noise_terms_rejected,
            policy_version=POLICY_VERSION,
        )
        row.update(
            {
                "source_hash": source_record.source_hash,
                "conversation_id": source_record.identity.conversation_id,
                "conversation_title": source_record.identity.title,
                "thread_index": _coerce_nonnegative_int(thread_row.get("thread_index")),
                "message_start_index": _coerce_nonnegative_int(thread_row.get("message_start_index")),
                "message_end_index": _coerce_nonnegative_int(thread_row.get("message_end_index")),
                "char_start": char_start,
                "char_end": char_end,
                "source_relative_path": source_record.source_relative_path,
                "source_ordinal": source_record.source_ordinal,
                "top_level_shape": source_record.top_level_shape,
                "dates": _extract_dates(thread_text, item_limit),
                "project_terms": _extract_project_terms(evidence, item_limit),
                "person_org_candidates": _extract_person_org_candidates(evidence, item_limit),
            }
        )
        contract.validate_row(row["schema"], row)
        rows.append(row)

    return tuple(rows)


def build_chatgpt_lexical_sketches(
    source_dir,
    *,
    run_id: str,
    max_terms: int = 20,
    max_items_per_kind: int = 20,
    excerpt_chars: int = 500,
) -> ChatGPTAtlasLexicalSketchResult:
    loaded = load_chatgpt_archive_source_dir(source_dir)
    rows = build_chatgpt_lexical_sketch_rows(
        loaded.conversations,
        run_id=run_id,
        max_terms=max_terms,
        max_items_per_kind=max_items_per_kind,
        excerpt_chars=excerpt_chars,
    )
    return ChatGPTAtlasLexicalSketchResult(rows=rows, source_errors=loaded.source_errors)


def _build_transcript_context(
    source_records: list[ChatGPTAtlasSourceConversation],
) -> dict[
    tuple[str, Optional[str], str, str, int],
    tuple[ChatGPTAtlasSourceConversation, list[_RenderedTurn], str],
]:
    context: dict[
        tuple[str, Optional[str], str, str, int],
        tuple[ChatGPTAtlasSourceConversation, list[_RenderedTurn], str],
    ] = {}
    for source_record in source_records:
        messages = _collect_chatgpt_messages(source_record.conversation)
        turns = _build_rendered_turns(messages)
        if not turns:
            continue
        transcript = "".join(turn.rendered for turn in turns)
        context[_source_record_key(source_record)] = (source_record, turns, transcript)
    return context


def _source_record_key(
    source_record: ChatGPTAtlasSourceConversation,
) -> tuple[str, Optional[str], str, str, int]:
    return (
        source_record.identity.logical_source_id,
        source_record.identity.conversation_id,
        source_record.source_hash,
        source_record.source_relative_path,
        source_record.source_ordinal,
    )


def _match_source_record(
    transcript_context: dict[
        tuple[str, Optional[str], str, str, int],
        tuple[ChatGPTAtlasSourceConversation, list[_RenderedTurn], str],
    ],
    thread_row: dict[str, Any],
) -> Optional[tuple[ChatGPTAtlasSourceConversation, list[_RenderedTurn], str]]:
    source_ordinal = _coerce_nonnegative_int(thread_row.get("source_ordinal"))
    key = (
        _coerce_str(thread_row.get("logical_source_id")),
        _coerce_optional_str(thread_row.get("conversation_id")),
        _coerce_str(thread_row.get("source_hash")),
        _coerce_str(thread_row.get("source_relative_path")),
        source_ordinal,
    )
    if key[0] is None or key[2] is None or key[3] is None or source_ordinal is None:
        return None
    return transcript_context.get((key[0], key[1], key[2], key[3], source_ordinal))


def _build_rendered_turns(messages: list[tuple[str, str]]) -> list[_RenderedTurn]:
    turns: list[_RenderedTurn] = []
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
            _RenderedTurn(
                index=index,
                role=role,
                text=text,
                rendered=rendered,
                start=start,
                end=end,
            )
        )
    return turns


def _build_representative_excerpts(
    *,
    thread_row: dict[str, Any],
    thread_turns: list[_RenderedTurn],
    thread_text: str,
    excerpt_chars: int,
    limit: int,
) -> list[str]:
    excerpts: list[str] = []
    for key in ("representative_excerpt", "title_hint"):
        value = _coerce_str(thread_row.get(key))
        if value is not None:
            _append_unique(excerpts, _truncate_text(value, excerpt_chars))

    user_turns = [(turn.index, turn.text) for turn in thread_turns if turn.role == "user"]
    if user_turns:
        ranked = sorted(user_turns, key=lambda item: (-len(item[1]), item[0]))
        for _, text in ranked[:2]:
            _append_unique(excerpts, _truncate_text(text, excerpt_chars))
    elif thread_turns:
        _append_unique(excerpts, _truncate_text(thread_turns[0].text, excerpt_chars))

    if not excerpts:
        _append_unique(excerpts, _truncate_text(_strip_rendering(thread_text), excerpt_chars))
    return excerpts[:limit]


def _extract_dates(text: str, limit: int) -> list[str]:
    dates: list[str] = []
    for match in _DATE_RE.finditer(text):
        _append_unique(dates, match.group(0).strip())
        if len(dates) >= limit:
            break
    return dates


def _build_legal_citations(base_items: list[str], text: str, limit: int) -> list[str]:
    citations: list[str] = []
    for item in base_items:
        _append_unique(citations, item)
        if len(citations) >= limit:
            return citations
    for match in _LEGAL_SIGNAL_RE.finditer(text):
        _append_unique(citations, match.group(0).strip())
        if len(citations) >= limit:
            break
    return citations


def _extract_project_terms(evidence, limit: int) -> list[str]:
    terms: list[str] = []
    for item in evidence.top_terms:
        term = item.get("term")
        if not isinstance(term, str):
            continue
        if _is_project_term(term):
            _append_unique(terms, term)
        if len(terms) >= limit:
            break
    for phrase in evidence.keyphrases:
        if _is_project_term(phrase):
            _append_unique(terms, phrase)
        if len(terms) >= limit:
            break
    return terms[:limit]


def _is_project_term(value: str) -> bool:
    return any(char in value for char in "-_/") or any(char.isdigit() for char in value)


def _extract_person_org_candidates(evidence, limit: int) -> list[str]:
    candidates: list[str] = []
    for phrase in evidence.capitalized_phrases:
        if not phrase or phrase in _PERSON_OR_ORG_STOPWORDS:
            continue
        _append_unique(candidates, phrase)
        if len(candidates) >= limit:
            break
    return candidates


def _strip_rendering(text: str) -> str:
    stripped = re.sub(r"(?m)^>\s*", "", text).strip()
    return stripped or text.strip()


def _append_unique(values: list[str], value: str) -> None:
    if not value or value in values:
        return
    values.append(value)


def _coerce_nonnegative_int(value: object) -> Optional[int]:
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return None


def _coerce_str(value: object) -> Optional[str]:
    if isinstance(value, str) and value:
        return value
    return None


def _coerce_optional_str(value: object) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str) and value:
        return value
    return None


def _truncate_text(text: str, limit: int) -> str:
    if limit <= 0:
        return ""
    return text[:limit]


def _validate_nonnegative_int(name: str, value: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value
