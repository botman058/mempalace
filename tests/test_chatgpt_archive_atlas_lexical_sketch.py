from __future__ import annotations

import dataclasses
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

_thread_index_module = pytest.importorskip(
    "mempalace.chatgpt_archive_atlas_thread",
    reason="thread index implementation is not present yet",
)
build_chatgpt_thread_index_rows = _thread_index_module.build_chatgpt_thread_index_rows

_lexical_sketch_module = pytest.importorskip(
    "mempalace.chatgpt_archive_atlas_lexical_sketch",
    reason="lexical sketch implementation is not present yet",
)
ChatGPTAtlasLexicalSketchResult = _lexical_sketch_module.ChatGPTAtlasLexicalSketchResult
build_chatgpt_lexical_sketch_rows = _lexical_sketch_module.build_chatgpt_lexical_sketch_rows
build_chatgpt_lexical_sketches = _lexical_sketch_module.build_chatgpt_lexical_sketches

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
        path = _copy_fixture(source_dir, fixture_name, relative_path)
        loaded = load_chatgpt_conversation_json_file(path, source_dir=source_dir)
        loaded_conversations.extend(loaded.conversations)
    return tuple(loaded_conversations)


def _assert_valid_lexical_rows(rows: tuple[dict[str, Any], ...]) -> None:
    for row in rows:
        assert contract.validate_row(contract.LEXICAL_SKETCH_SCHEMA, row) == row
        assert row["safety_contract"] == contract.safety_contract()


def _write_single_conversation(tmp_path: Path, conversation: dict[str, Any]) -> tuple:
    source_dir = tmp_path / "source"
    path = source_dir / "synthetic" / "conversations.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(conversation), encoding="utf-8")
    loaded = load_chatgpt_conversation_json_file(path, source_dir=source_dir)
    assert len(loaded.conversations) == 1
    return loaded.conversations[0], source_dir


def test_public_api_dataclass_is_frozen_and_tuple_backed() -> None:
    assert dataclasses.is_dataclass(ChatGPTAtlasLexicalSketchResult)
    result = ChatGPTAtlasLexicalSketchResult(rows=(), source_errors=())
    assert isinstance(result.rows, tuple)
    assert isinstance(result.source_errors, tuple)
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.rows = ()


def test_emits_one_lexical_row_per_thread_row_for_same_conversations(tmp_path: Path) -> None:
    conversations = _load_conversations(
        tmp_path,
        [
            ("single_dict_export.json", "single/conversations.json"),
            ("explicit_topic_switch.json", "switch/conversations.json"),
        ],
    )

    thread_rows = build_chatgpt_thread_index_rows(
        conversations=conversations,
        run_id="run-wp07-threads",
        excerpt_chars=120,
    )
    lexical_rows = build_chatgpt_lexical_sketch_rows(
        conversations=conversations,
        run_id="run-wp07-threads",
        excerpt_chars=120,
    )

    assert len(lexical_rows) == len(thread_rows)
    assert {row["thread_id"] for row in lexical_rows} == {row["thread_id"] for row in thread_rows}
    _assert_valid_lexical_rows(lexical_rows)


def test_missing_top_level_conversation_id_keeps_lexical_thread_mapping(tmp_path: Path) -> None:
    conversation: dict[str, Any] = {
        "title": "No explicit top-level id",
        "create_time": "2026-05-01T00:00:00Z",
        "update_time": "2026-05-01T00:01:00Z",
        "current_node": "a1",
        "mapping": {
            "root": {"parent": None, "children": ["u1"], "message": None},
            "u1": {
                "parent": "root",
                "children": ["a1"],
                "message": {
                    "author": {"role": "user"},
                    "content": {"parts": ["Please check sudo systemctl restart ssh now."]},
                },
            },
            "a1": {
                "parent": "u1",
                "children": [],
                "message": {
                    "author": {"role": "assistant"},
                    "content": {"parts": ["Use tail -n 80 /var/log/auth.log after restart."]},
                },
            },
        },
    }
    source_conversation, _source_dir = _write_single_conversation(tmp_path, conversation)
    assert source_conversation.identity.conversation_id is None

    thread_rows = build_chatgpt_thread_index_rows(
        conversations=(source_conversation,),
        run_id="run-wp07-missing-conversation-id",
        excerpt_chars=120,
    )
    lexical_rows = build_chatgpt_lexical_sketch_rows(
        conversations=(source_conversation,),
        run_id="run-wp07-missing-conversation-id",
        excerpt_chars=120,
    )

    assert len(lexical_rows) == len(thread_rows)
    assert {row["thread_id"] for row in lexical_rows} == {row["thread_id"] for row in thread_rows}
    assert {row["logical_source_id"] for row in lexical_rows} == {row["logical_source_id"] for row in thread_rows}
    _assert_valid_lexical_rows(lexical_rows)


def test_duplicate_logical_source_fixture_does_not_collapse_or_skew_rows(tmp_path: Path) -> None:
    conversations = _load_conversations(
        tmp_path,
        [("duplicate_source_identity.json", "dupes/conversations.json")],
    )
    assert len(conversations) == 2
    assert len({row.identity.logical_source_id for row in conversations}) == 1
    assert [row.source_ordinal for row in conversations] == [0, 1]

    thread_rows = build_chatgpt_thread_index_rows(
        conversations=conversations,
        run_id="run-wp07-duplicate-identity",
        excerpt_chars=120,
    )
    lexical_rows = build_chatgpt_lexical_sketch_rows(
        conversations=conversations,
        run_id="run-wp07-duplicate-identity",
        excerpt_chars=120,
    )

    assert len(lexical_rows) == len(thread_rows)
    assert {row["thread_id"] for row in lexical_rows} == {row["thread_id"] for row in thread_rows}
    assert len({row["thread_id"] for row in lexical_rows}) == len(lexical_rows)
    assert {row["logical_source_id"] for row in lexical_rows} == {
        row["logical_source_id"] for row in thread_rows
    }
    assert len({row["source_hash"] for row in thread_rows}) == 1
    _assert_valid_lexical_rows(lexical_rows)


def test_mixed_fixture_yields_legal_sysadmin_and_capitalized_evidence(tmp_path: Path) -> None:
    (conversation,) = _load_conversations(
        tmp_path,
        [("mixed_legal_sysadmin_personal.json", "mixed/conversations.json")],
    )

    rows = build_chatgpt_lexical_sketch_rows(
        conversations=(conversation,),
        run_id="run-wp07-mixed",
        max_terms=30,
        max_items_per_kind=30,
        excerpt_chars=160,
    )

    _assert_valid_lexical_rows(rows)
    assert rows
    all_commands = [item for row in rows for item in row["commands"]]
    all_paths = [item for row in rows for item in row["paths"]]
    all_legal = [item.lower() for row in rows for item in row["legal_citations"]]
    all_caps = [item.lower() for row in rows for item in row["capitalized_phrases"]]

    assert any("sudo systemctl restart ssh" in item for item in all_commands)
    assert any("tail -n 80 /var/log/auth.log" in item for item in all_commands)
    assert any("/var/log/auth.log" in item for item in all_paths)
    assert any("section 12" in item or "indemnify" in item or "liability" in item for item in all_legal)
    assert any("gdpr" in item or "saturday" in item for item in all_caps)


def test_synthetic_conversation_yields_domains_packages_models_and_project_terms(tmp_path: Path) -> None:
    conversation: dict[str, Any] = {
        "id": "atlas-lexical-synthetic-01",
        "title": "Synthetic lexical evidence",
        "create_time": "2026-05-01T00:00:00Z",
        "update_time": "2026-05-01T00:01:00Z",
        "current_node": "a2",
        "mapping": {
            "root": {"parent": None, "children": ["u1"], "message": None},
            "u1": {
                "parent": "root",
                "children": ["a1"],
                "message": {
                    "author": {"role": "user"},
                    "content": {
                        "parts": [
                            "In mempalace atlas project we use mempalace atlas indexing. "
                            "See https://docs.python.org and https://openai.com/api. "
                            "Install pydantic and httpx. Model gpt-4.1-mini and llama-3.1-8b."
                        ]
                    },
                },
            },
            "a1": {
                "parent": "u1",
                "children": ["u2"],
                "message": {
                    "author": {"role": "assistant"},
                    "content": {"parts": ["Acknowledged: mempalace atlas stack details captured."]},
                },
            },
            "u2": {
                "parent": "a1",
                "children": ["a2"],
                "message": {
                    "author": {"role": "user"},
                    "content": {"parts": ["mempalace atlas lexical mempalace atlas"]},
                },
            },
            "a2": {
                "parent": "u2",
                "children": [],
                "message": {"author": {"role": "assistant"}, "content": {"parts": ["done"]}},
            },
        },
    }
    source_conversation, _source_dir = _write_single_conversation(tmp_path, conversation)

    rows = build_chatgpt_lexical_sketch_rows(
        conversations=(source_conversation,),
        run_id="run-wp07-synth",
        max_terms=25,
        max_items_per_kind=25,
    )

    _assert_valid_lexical_rows(rows)
    assert rows
    domains = {item for row in rows for item in row["domains"]}
    packages = {item for row in rows for item in row["package_names"]}
    models = {item for row in rows for item in row["model_names"]}
    keyphrases = {item.lower() for row in rows for item in row["keyphrases"]}
    top_terms = {item["term"] for row in rows for item in row["top_terms"]}

    assert "docs.python.org" in domains
    assert "openai.com" in domains
    assert "pydantic" in packages
    assert "httpx" in packages
    assert "gpt-4.1-mini" in models
    assert "llama-3.1-8b" in models
    assert "mempalace" in top_terms
    assert "atlas" in top_terms
    assert any("mempalace" in phrase or "atlas" in phrase for phrase in keyphrases)


def test_primary_top_terms_reject_common_noise_terms(tmp_path: Path) -> None:
    conversation: dict[str, Any] = {
        "id": "atlas-lexical-stopwords-01",
        "title": "Stopwords lexical check",
        "create_time": "2026-05-01T00:00:00Z",
        "current_node": "a1",
        "mapping": {
            "root": {"parent": None, "children": ["u1"], "message": None},
            "u1": {
                "parent": "root",
                "children": ["a1"],
                "message": {
                    "author": {"role": "user"},
                    "content": {
                        "parts": [
                            "the and you for the and you for mempalace atlas mempalace atlas thread sketch"
                        ]
                    },
                },
            },
            "a1": {
                "parent": "u1",
                "children": [],
                "message": {"author": {"role": "assistant"}, "content": {"parts": ["noted"]}},
            },
        },
    }
    source_conversation, _source_dir = _write_single_conversation(tmp_path, conversation)
    rows = build_chatgpt_lexical_sketch_rows(conversations=(source_conversation,), run_id="run-wp07-stop")
    assert rows
    top_terms = {item["term"] for row in rows for item in row["top_terms"]}
    assert {"the", "and", "you", "for"}.isdisjoint(top_terms)


def test_deterministic_and_bounded_output_across_repeated_calls(tmp_path: Path) -> None:
    (conversation,) = _load_conversations(
        tmp_path,
        [("explicit_topic_switch.json", "switch/conversations.json")],
    )

    first = build_chatgpt_lexical_sketch_rows(
        conversations=(conversation,),
        run_id="run-wp07-deterministic",
        max_terms=5,
        max_items_per_kind=3,
        excerpt_chars=80,
    )
    second = build_chatgpt_lexical_sketch_rows(
        conversations=(conversation,),
        run_id="run-wp07-deterministic",
        max_terms=5,
        max_items_per_kind=3,
        excerpt_chars=80,
    )

    assert first == second
    for row in first:
        assert len(row["top_terms"]) <= 5
        assert len(row["keyphrases"]) <= 3
        assert len(row["domains"]) <= 3
        assert len(row["paths"]) <= 3
        assert len(row["commands"]) <= 3
        assert len(row["package_names"]) <= 3
        assert len(row["model_names"]) <= 3
        assert len(row["legal_citations"]) <= 3
        assert len(row["capitalized_phrases"]) <= 3
        assert len(row["noise_terms_rejected"]) <= 3


def test_build_chatgpt_lexical_sketches_passes_source_errors(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    _copy_fixture(source_dir, "single_dict_export.json", "good/conversations.json")
    _copy_fixture(source_dir, "malformed_source.json", "broken/conversations.json")

    loaded = load_chatgpt_archive_source_dir(source_dir)
    result = build_chatgpt_lexical_sketches(
        source_dir,
        run_id="run-wp07-pass-errors",
        excerpt_chars=120,
    )

    assert isinstance(result, ChatGPTAtlasLexicalSketchResult)
    assert isinstance(result.rows, tuple)
    assert isinstance(result.source_errors, tuple)
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
    _assert_valid_lexical_rows(result.rows)
