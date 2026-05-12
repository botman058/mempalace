from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pytest

from mempalace import chatgpt_archive_atlas_contract as contract
from mempalace.chatgpt_archive_atlas_source import (
    load_chatgpt_archive_source_dir,
    load_chatgpt_conversation_json_file,
)
from mempalace.normalize import _collect_chatgpt_messages

_thread_index_module = pytest.importorskip(
    "mempalace.chatgpt_archive_atlas_thread",
    reason="thread index implementation is not present yet",
)
ChatGPTAtlasThreadIndexResult = _thread_index_module.ChatGPTAtlasThreadIndexResult
build_chatgpt_thread_index = _thread_index_module.build_chatgpt_thread_index
build_chatgpt_thread_index_rows = _thread_index_module.build_chatgpt_thread_index_rows

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "chatgpt_archive_atlas"


def _fixture_path(name: str) -> Path:
    return FIXTURE_DIR / name


def _copy_fixture(tmp_path: Path, name: str, relative_path: str) -> Path:
    destination = tmp_path / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(_fixture_path(name), destination)
    return destination


def _load_conversations(tmp_path: Path, fixture_specs: list[tuple[str, str]]) -> tuple:
    source_dir = tmp_path / "source"
    loaded_conversations = []
    for fixture_name, relative_path in fixture_specs:
        path = _copy_fixture(
            source_dir,
            name=fixture_name,
            relative_path=relative_path,
        )
        loaded = load_chatgpt_conversation_json_file(path, source_dir=source_dir)
        loaded_conversations.extend(loaded.conversations)
    return tuple(loaded_conversations)


def _assert_valid_thread_rows(rows: tuple[dict[str, Any], ...]) -> None:
    for row in rows:
        assert contract.validate_row(contract.THREAD_INDEX_SCHEMA, row) == row
        assert row["safety_contract"] == contract.safety_contract()


def test_single_short_conversation_emits_single_full_thread(tmp_path: Path) -> None:
    (conversation,) = _load_conversations(
        tmp_path,
        [("single_dict_export.json", "single/conversations.json")],
    )
    rows = build_chatgpt_thread_index_rows(
        conversations=(conversation,),
        run_id="run-single-thread",
    )
    messages = _collect_chatgpt_messages(conversation.conversation)

    assert len(rows) == 1
    row = rows[0]
    assert row["thread_index"] == 0
    assert row["logical_source_id"] == "chatgpt:atlas-single-01"
    assert row["conversation_id"] == "atlas-single-01"
    assert row["conversation_title"] == "Single export object"
    assert row["source_hash"] == conversation.source_hash
    assert row["message_start_index"] == 0
    assert row["message_end_index"] == len(messages) - 1
    assert row["user_message_count"] == 1
    assert row["assistant_message_count"] == 1
    assert row["char_count"] > 0
    assert row["representative_excerpt"] is not None
    _assert_valid_thread_rows(rows)


def test_explicit_topic_switch_starts_new_thread_at_switch_turn(tmp_path: Path) -> None:
    (conversation,) = _load_conversations(
        tmp_path,
        [("explicit_topic_switch.json", "explicit/conversations.json")],
    )
    rows = build_chatgpt_thread_index_rows(
        conversations=(conversation,),
        run_id="run-topic-switch",
    )
    _assert_valid_thread_rows(rows)

    messages = _collect_chatgpt_messages(conversation.conversation)
    assert len(messages) >= 6

    # Switch turn is the third user message in this fixture (zero-based message index 2).
    switch_start = 2
    rows_by_thread = sorted(rows, key=lambda row: row["thread_index"])
    assert len(rows_by_thread) >= 2
    assert rows_by_thread[0]["message_start_index"] == 0
    assert rows_by_thread[0]["message_end_index"] < switch_start
    assert any(row["message_start_index"] == switch_start for row in rows_by_thread)


def test_mixed_legal_sysadmin_personal_fixtures_emit_multiple_threads(tmp_path: Path) -> None:
    (conversation,) = _load_conversations(
        tmp_path,
        [("mixed_legal_sysadmin_personal.json", "mixed/conversations.json")],
    )
    rows = build_chatgpt_thread_index_rows(
        conversations=(conversation,),
        run_id="run-mixed",
    )

    assert len(rows) > 1
    thread_ids = [row["thread_id"] for row in rows]
    assert len(thread_ids) == len(set(thread_ids))
    _assert_valid_thread_rows(rows)


def test_long_first_user_message_has_full_span_and_truncated_excerpt(tmp_path: Path) -> None:
    (conversation,) = _load_conversations(
        tmp_path,
        [("long_first_user_message.json", "long/conversations.json")],
    )
    rows = build_chatgpt_thread_index_rows(
        conversations=(conversation,),
        run_id="run-long-first",
        excerpt_chars=80,
    )
    messages = _collect_chatgpt_messages(conversation.conversation)
    first_role, first_text = messages[0]
    assert first_role == "user"
    assert len(first_text) > 80

    # The thread path must expose spans that cover the long first user message
    # while keeping per-thread excerpts constrained by excerpt_chars.
    first_turn_rows = [row for row in rows if row["message_start_index"] == 0]
    assert first_turn_rows
    assert min(row["char_start"] for row in first_turn_rows) == 0
    expected_first_turn_chars = len(f"> {first_text}\n\n")
    assert max(row["char_end"] for row in first_turn_rows) >= expected_first_turn_chars

    for row in rows:
        assert row["representative_excerpt"] is not None
        assert len(row["representative_excerpt"]) <= 80

    first_turn_excerpt = first_turn_rows[0]["representative_excerpt"]
    assert len(first_turn_excerpt) <= 80
    assert len(first_turn_excerpt) < len(first_text)

    _assert_valid_thread_rows(rows)


def test_thread_rows_cover_final_selected_suffix_message(tmp_path: Path) -> None:
    (conversation,) = _load_conversations(
        tmp_path,
        [("explicit_topic_switch.json", "explicit/conversations.json")],
    )
    rows = build_chatgpt_thread_index_rows(
        conversations=(conversation,),
        run_id="run-suffix",
    )
    _assert_valid_thread_rows(rows)

    messages = _collect_chatgpt_messages(conversation.conversation)
    assert rows
    assert max(row["message_end_index"] for row in rows) == len(messages) - 1

    ordered_by_index = sorted(rows, key=lambda row: row["thread_index"])
    assert ordered_by_index[-1]["message_end_index"] == len(messages) - 1


def test_thread_ids_are_stable_across_repeated_calls(tmp_path: Path) -> None:
    (conversation,) = _load_conversations(
        tmp_path,
        [("explicit_topic_switch.json", "explicit/conversations.json")],
    )
    first = build_chatgpt_thread_index_rows(
        conversations=(conversation,),
        run_id="run-stable",
        excerpt_chars=120,
    )
    second = build_chatgpt_thread_index_rows(
        conversations=(conversation,),
        run_id="run-stable",
        excerpt_chars=120,
    )

    assert first == second
    assert [row["thread_id"] for row in first] == [row["thread_id"] for row in second]
    _assert_valid_thread_rows(first)


def test_build_chatgpt_thread_index_passes_source_errors(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    _copy_fixture(source_dir, "single_dict_export.json", "good/conversations.json")
    _copy_fixture(source_dir, "malformed_source.json", "broken/conversations.json")

    loaded = load_chatgpt_archive_source_dir(source_dir)
    result = build_chatgpt_thread_index(
        source_dir,
        run_id="run-pass-errors",
        excerpt_chars=120,
    )

    assert isinstance(result, ChatGPTAtlasThreadIndexResult)
    assert len(result.rows) >= 1
    assert len(result.source_errors) == 1
    assert result.source_errors[0]["error_code"] == "source_json_decode_error"
    assert result.source_errors[0]["source_relative_path"] == "broken/conversations.json"

    assert len(loaded.source_errors) == len(result.source_errors)
    assert [row["error_code"] for row in result.source_errors] == [
        row["error_code"] for row in loaded.source_errors
    ]
    assert [
        row["source_relative_path"] for row in result.source_errors
    ] == [
        row["source_relative_path"] for row in loaded.source_errors
    ]
    _assert_valid_thread_rows(result.rows)
