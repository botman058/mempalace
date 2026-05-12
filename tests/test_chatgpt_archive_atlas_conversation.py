from __future__ import annotations

import json
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
_conversation_index_module = pytest.importorskip(
    "mempalace.chatgpt_archive_atlas_conversation",
    reason="conversation index implementation is not present yet",
)
ChatGPTAtlasConversationIndexResult = _conversation_index_module.ChatGPTAtlasConversationIndexResult
build_chatgpt_conversation_index = _conversation_index_module.build_chatgpt_conversation_index
build_chatgpt_conversation_index_rows = _conversation_index_module.build_chatgpt_conversation_index_rows

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "chatgpt_archive_atlas"


def _fixture_path(name: str) -> Path:
    return FIXTURE_DIR / name


def _copy_fixture(tmp_path: Path, name: str, relative_path: str) -> Path:
    destination = tmp_path / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(_fixture_path(name), destination)
    return destination


def _assert_valid_rows(rows: tuple[dict[str, Any], ...]) -> None:
    for row in rows:
        assert contract.validate_row(contract.CONVERSATION_INDEX_SCHEMA, row) == row
        assert row["safety_contract"] == contract.safety_contract()


def _selected_message_counts(conversation: dict[str, Any]) -> tuple[int, int, int, int]:
    messages = _collect_chatgpt_messages(conversation)
    message_count = len(messages)
    user_message_count = sum(1 for role, _ in messages if role == "user")
    assistant_message_count = sum(1 for role, _ in messages if role == "assistant")
    char_count = sum(len(text) for _, text in messages)
    return message_count, user_message_count, assistant_message_count, char_count


def _build_rows_from_fixtures(
    tmp_path: Path,
    fixture_specs: list[tuple[str, str]],
) -> tuple[list[tuple], list[str]]:
    source_dir = tmp_path / "source"
    rows = []
    file_relative_paths = []
    for fixture_name, relative_path in fixture_specs:
        source_path = _copy_fixture(
            source_dir,
            name=fixture_name,
            relative_path=relative_path,
        )
        loaded = load_chatgpt_conversation_json_file(source_path, source_dir=source_dir)
        file_relative_paths.append(relative_path)
        rows.append(loaded.conversations)
    conversations = tuple(conversation for batch in rows for conversation in batch)
    return conversations, file_relative_paths


def _write_custom_conversation(tmp_path: Path, *, conversation: dict[str, Any], relative_path: str) -> tuple:
    source_dir = tmp_path / "source"
    path = source_dir / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(conversation), encoding="utf-8")
    loaded = load_chatgpt_conversation_json_file(path, source_dir=source_dir)
    assert len(loaded.conversations) == 1
    return loaded.conversations[0], source_dir


def test_conversation_rows_emit_per_conversation_for_dict_and_list_exports(tmp_path: Path) -> None:
    conversations, _ = _build_rows_from_fixtures(
        tmp_path,
        [
            ("single_dict_export.json", "single/conversations.json"),
            ("list_export.json", "list/conversations.json"),
        ],
    )

    rows = build_chatgpt_conversation_index_rows(
        conversations=conversations,
        run_id="run-list-dict",
    )

    assert len(rows) == 3
    assert rows[0]["logical_source_id"] == "chatgpt:atlas-single-01"
    assert rows[1]["logical_source_id"] == "chatgpt:atlas-list-tech-01"
    assert rows[2]["logical_source_id"] == "chatgpt:atlas-list-personal-02"

    _assert_valid_rows(rows)


def test_selected_path_keeps_only_current_node_branch_messages(tmp_path: Path) -> None:
    conversation: dict[str, Any] = {
        "id": "atlas-branch-metadata-01",
        "title": "Branch selection fixture",
        "create_time": "2026-01-01T00:00:00Z",
        "update_time": "2026-01-01T00:01:00Z",
        "current_node": "a2",
        "mapping": {
            "root": {
                "parent": None,
                "children": ["u1"],
                "message": None,
            },
            "u1": {
                "parent": "root",
                "children": ["a1"],
                "message": {
                    "author": {"role": "user"},
                    "content": {"parts": ["selected user anchor"]},
                },
            },
            "a1": {
                "parent": "u1",
                "children": ["u2", "u3"],
                "message": {
                    "author": {"role": "assistant"},
                    "content": {"parts": ["selected assistant bridge"]},
                },
            },
            "u2": {
                "parent": "a1",
                "children": ["a2"],
                "message": {
                    "author": {"role": "user"},
                    "content": {"parts": ["selected branch user"]},
                },
            },
            "a2": {
                "parent": "u2",
                "children": [],
                "message": {
                    "author": {"role": "assistant"},
                    "content": {"parts": ["selected branch assistant"]},
                },
            },
            "u3": {
                "parent": "a1",
                "children": ["a4"],
                "message": {
                    "author": {"role": "user"},
                    "content": {"parts": ["non-selected branch user should be skipped"]},
                },
            },
            "a4": {
                "parent": "u3",
                "children": [],
                "message": {
                    "author": {"role": "assistant"},
                    "content": {"parts": ["non-selected branch assistant should be skipped"]},
                },
            },
        },
    }

    conversation_row, _source_dir = _write_custom_conversation(
        tmp_path,
        conversation=conversation,
        relative_path="branch/conversations.json",
    )
    rows = build_chatgpt_conversation_index_rows(
        conversations=(conversation_row,),
        run_id="run-selected-path",
        excerpt_chars=120,
        top_prompt_count=5,
    )

    assert len(rows) == 1
    row = rows[0]
    expected_counts = _selected_message_counts(conversation)
    assert row["message_count"] == expected_counts[0]
    assert row["user_message_count"] == expected_counts[1]
    assert row["assistant_message_count"] == expected_counts[2]
    assert row["char_count"] == expected_counts[3]
    assert row["first_user_excerpt"] == "selected user anchor"
    _assert_valid_rows(rows)


def test_duplicate_logical_source_ids_preserve_source_ordinal_and_hash(tmp_path: Path) -> None:
    conversations, _ = _build_rows_from_fixtures(
        tmp_path,
        [("duplicate_source_identity.json", "dupes/conversations.json")],
    )

    rows = build_chatgpt_conversation_index_rows(
        conversations=conversations,
        run_id="run-duplicates",
    )

    assert len(rows) == 2
    assert [row["source_ordinal"] for row in rows] == [0, 1]
    assert len({row["logical_source_id"] for row in rows}) == 1
    assert len({row["source_hash"] for row in rows}) == 1
    assert rows[0]["source_relative_path"] == "dupes/conversations.json"
    assert rows[1]["source_relative_path"] == "dupes/conversations.json"
    _assert_valid_rows(rows)


def test_create_and_update_timestamps_are_preserved_as_strings(tmp_path: Path) -> None:
    conversations, _ = _build_rows_from_fixtures(
        tmp_path,
        [("single_dict_export.json", "single/conversations.json")],
    )

    rows = build_chatgpt_conversation_index_rows(
        conversations=conversations,
        run_id="run-timestamps",
    )

    row = rows[0]
    assert isinstance(row["create_time"], str)
    assert isinstance(row["update_time"], str)
    assert row["create_time"] == "1746961000"
    assert row["update_time"] == "1746961100"
    _assert_valid_rows(rows)


def test_first_user_excerpt_and_top_user_prompts_are_deterministic_and_truncated(tmp_path: Path) -> None:
    conversation = _build_rows_from_fixtures(
        tmp_path,
        [("long_first_user_message.json", "long/conversations.json")],
    )[0][0]
    rows = build_chatgpt_conversation_index_rows(
        conversations=(conversation,),
        run_id="run-long",
        excerpt_chars=75,
        top_prompt_count=1,
    )
    rows_repeat = build_chatgpt_conversation_index_rows(
        conversations=(conversation,),
        run_id="run-long",
        excerpt_chars=75,
        top_prompt_count=1,
    )

    row = rows[0]
    assert row == rows_repeat[0]
    assert len(row["first_user_excerpt"]) <= 75
    assert len(row["top_user_prompt_excerpts"]) == 1
    assert len(row["top_user_prompt_excerpts"][0]) <= 75
    assert row["top_user_prompt_excerpts"][0] == row["first_user_excerpt"]
    _assert_valid_rows(rows)


def test_model_slug_and_plugin_ids_preserved(tmp_path: Path) -> None:
    conversation = {
        "id": "atlas-model-plugin-01",
        "title": "Model + plugins metadata",
        "model_slug": "gpt-4.1-mini",
        "plugin_ids": ["browser", "terminal", "files"],
        "create_time": "2026-05-01T00:00:00Z",
        "update_time": "2026-05-02T00:00:00Z",
        "current_node": "a1",
        "mapping": {
            "root": {"parent": None, "children": ["u1"], "message": None},
            "u1": {
                "parent": "root",
                "children": ["a1"],
                "message": {
                    "author": {"role": "user"},
                    "content": {"parts": ["Need metadata from model_slug and plugin_ids"]},
                },
            },
            "a1": {
                "parent": "u1",
                "children": [],
                "message": {
                    "author": {"role": "assistant"},
                    "content": {"parts": ["Stored for row metadata checks."]},
                },
            },
        },
    }

    row_source, _ = _write_custom_conversation(
        tmp_path,
        conversation=conversation,
        relative_path="meta/conversations.json",
    )

    rows = build_chatgpt_conversation_index_rows(
        conversations=(row_source,),
        run_id="run-model-plugin",
    )

    row = rows[0]
    assert row["model_slug"] == "gpt-4.1-mini"
    assert row["plugin_ids"] == ["browser", "terminal", "files"]
    assert row["create_time"] == "2026-05-01T00:00:00Z"
    assert row["update_time"] == "2026-05-02T00:00:00Z"
    _assert_valid_rows(rows)


def test_build_chatgpt_conversation_index_passes_source_errors(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    _copy_fixture(source_dir, "single_dict_export.json", "good/conversations.json")
    _copy_fixture(source_dir, "malformed_source.json", "broken/conversations.json")

    source_loaded = load_chatgpt_archive_source_dir(source_dir)
    index = build_chatgpt_conversation_index(source_dir, run_id="run-pass-errors")

    assert isinstance(index, ChatGPTAtlasConversationIndexResult)
    assert index.rows
    assert len(index.rows) == 1
    assert len(index.source_errors) == 1
    assert index.source_errors[0]["error_code"] == "source_json_decode_error"
    assert index.source_errors[0]["source_relative_path"] == "broken/conversations.json"

    for observed, expected in zip(index.source_errors, source_loaded.source_errors):
        assert observed["error_code"] == expected["error_code"]
        assert observed["source_relative_path"] == expected["source_relative_path"]
        assert observed["top_level_shape"] == expected["top_level_shape"]

    _assert_valid_rows(index.rows)


def test_build_conversation_rows_match_source_row_metadata(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    list_path = _copy_fixture(source_dir, "single_dict_export.json", "single/conversations.json")
    list_loaded = load_chatgpt_conversation_json_file(list_path, source_dir=source_dir)
    source_row = list_loaded.conversations[0]

    rows = build_chatgpt_conversation_index_rows(
        (source_row,),
        run_id="run-metadata",
    )[0]

    assert rows["logical_source_id"] == source_row.identity.logical_source_id
    assert rows["conversation_id"] == source_row.identity.conversation_id
    assert rows["title"] == source_row.identity.title
    assert rows["source_relative_path"] == "single/conversations.json"
    assert rows["source_ordinal"] == source_row.source_ordinal
    assert rows["source_hash"] == source_row.source_hash
    assert rows["model_slug"] is None
    assert rows["plugin_ids"] == []
    _assert_valid_rows((rows,))
