from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from mempalace import chatgpt_archive_atlas_contract as contract
from mempalace.chatgpt_archive_atlas_source import (
    ChatGPTAtlasSourceConversation,
    iter_chatgpt_archive_source_conversations,
    iter_chatgpt_conversation_json_files,
    load_chatgpt_archive_source_dir,
    load_chatgpt_conversation_json_file,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "chatgpt_archive_atlas"


def _fixture_path(name: str) -> Path:
    return FIXTURE_DIR / name


def _copy_fixture(
    tmp_path: Path,
    *,
    fixture_name: str,
    relative_path: str,
) -> Path:
    destination = tmp_path / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(_fixture_path(fixture_name), destination)
    return destination


def _loaded_relative_paths(rows: list[ChatGPTAtlasSourceConversation]) -> list[str]:
    return [row.source_relative_path for row in rows]


def test_iter_chatgpt_conversation_json_files_is_sorted_and_filename_scoped(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    _copy_fixture(
        source_dir,
        fixture_name="single_dict_export.json",
        relative_path="z-last/conversations.json",
    )
    _copy_fixture(
        source_dir,
        fixture_name="list_export.json",
        relative_path="a-first/conversations.json",
    )
    _copy_fixture(
        source_dir,
        fixture_name="duplicate_source_identity.json",
        relative_path="m-middle/nested/conversations.json",
    )
    _copy_fixture(
        source_dir,
        fixture_name="single_dict_export.json",
        relative_path="ignored/not_conversations.json",
    )

    discovered = list(iter_chatgpt_conversation_json_files(source_dir))

    assert [path.relative_to(source_dir).as_posix() for path in discovered] == [
        "a-first/conversations.json",
        "m-middle/nested/conversations.json",
        "z-last/conversations.json",
    ]


def test_load_chatgpt_conversation_json_file_supports_dict_and_list_exports(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    dict_path = _copy_fixture(
        source_dir,
        fixture_name="single_dict_export.json",
        relative_path="single/conversations.json",
    )
    list_path = _copy_fixture(
        source_dir,
        fixture_name="list_export.json",
        relative_path="multi/conversations.json",
    )

    dict_loaded = load_chatgpt_conversation_json_file(dict_path, source_dir=source_dir)
    list_loaded = load_chatgpt_conversation_json_file(list_path, source_dir=source_dir)

    assert len(dict_loaded.conversations) == 1
    assert dict_loaded.source_errors == ()
    assert dict_loaded.conversations[0].top_level_shape == "dict"
    assert dict_loaded.conversations[0].source_relative_path == "single/conversations.json"
    assert dict_loaded.conversations[0].source_ordinal == 0
    assert dict_loaded.conversations[0].identity.logical_source_id == "chatgpt:atlas-single-01"

    assert [row.top_level_shape for row in list_loaded.conversations] == ["list", "list"]
    assert [row.source_ordinal for row in list_loaded.conversations] == [0, 1]
    assert [row.identity.logical_source_id for row in list_loaded.conversations] == [
        "chatgpt:atlas-list-tech-01",
        "chatgpt:atlas-list-personal-02",
    ]
    assert _loaded_relative_paths(list(list_loaded.conversations)) == [
        "multi/conversations.json",
        "multi/conversations.json",
    ]


def test_load_chatgpt_conversation_json_file_records_malformed_json_error(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    malformed_path = _copy_fixture(
        source_dir,
        fixture_name="malformed_source.json",
        relative_path="broken/conversations.json",
    )

    loaded = load_chatgpt_conversation_json_file(malformed_path, source_dir=source_dir)

    assert loaded.conversations == ()
    assert len(loaded.source_errors) == 1
    error = loaded.source_errors[0]
    assert error["error_code"] == "source_json_decode_error"
    assert error["status"] == "error"
    assert error["source_relative_path"] == "broken/conversations.json"
    assert error["source_hash"] == error["source_version_token"]
    assert error["source_hash"].startswith("sha256:")
    assert error["top_level_shape"] is None
    assert error["safety_contract"] == contract.safety_contract()
    contract.validate_json_safe(error)


def test_load_chatgpt_conversation_json_file_records_wrong_shape_errors(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"

    scalar_path = source_dir / "scalar" / "conversations.json"
    scalar_path.parent.mkdir(parents=True, exist_ok=True)
    scalar_path.write_text('"not a conversation export"', encoding="utf-8")

    dict_path = source_dir / "wrong-dict" / "conversations.json"
    dict_path.parent.mkdir(parents=True, exist_ok=True)
    dict_path.write_text(json.dumps({"random": "data"}), encoding="utf-8")

    scalar_loaded = load_chatgpt_conversation_json_file(scalar_path, source_dir=source_dir)
    dict_loaded = load_chatgpt_conversation_json_file(dict_path, source_dir=source_dir)

    assert scalar_loaded.conversations == ()
    assert scalar_loaded.source_errors[0]["error_code"] == "source_shape_error"
    assert scalar_loaded.source_errors[0]["top_level_shape"] == "str"

    assert dict_loaded.conversations == ()
    assert dict_loaded.source_errors[0]["error_code"] == "source_shape_error"
    assert dict_loaded.source_errors[0]["top_level_shape"] == "dict"
    assert "not a valid ChatGPT conversation export" in dict_loaded.source_errors[0]["error_detail"]


def test_duplicate_identity_fixture_loading_preserves_duplicate_logical_source_ids(
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "source"
    fixture_path = _copy_fixture(
        source_dir,
        fixture_name="duplicate_source_identity.json",
        relative_path="dupes/conversations.json",
    )

    loaded = load_chatgpt_conversation_json_file(fixture_path, source_dir=source_dir)

    assert len(loaded.conversations) == 2
    assert loaded.source_errors == ()
    assert [row.source_ordinal for row in loaded.conversations] == [0, 1]
    assert len({row.identity.logical_source_id for row in loaded.conversations}) == 1
    assert len({row.source_hash for row in loaded.conversations}) == 1


def test_source_hash_is_deterministic_and_content_based(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    first = _copy_fixture(
        source_dir,
        fixture_name="single_dict_export.json",
        relative_path="one/conversations.json",
    )
    second = _copy_fixture(
        source_dir,
        fixture_name="single_dict_export.json",
        relative_path="two/conversations.json",
    )

    first_loaded = load_chatgpt_conversation_json_file(first, source_dir=source_dir)
    second_loaded = load_chatgpt_conversation_json_file(second, source_dir=source_dir)
    expected_hash = "sha256:" + hashlib.sha256(
        _fixture_path("single_dict_export.json").read_text(encoding="utf-8").encode("utf-8")
    ).hexdigest()

    assert first_loaded.conversations[0].source_hash == expected_hash
    assert second_loaded.conversations[0].source_hash == expected_hash
    assert first_loaded.conversations[0].source_hash == second_loaded.conversations[0].source_hash


def test_relative_path_safety_rejects_files_outside_source_dir(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    outside_path = _copy_fixture(
        tmp_path,
        fixture_name="single_dict_export.json",
        relative_path="outside/conversations.json",
    )

    loaded = load_chatgpt_conversation_json_file(outside_path, source_dir=source_dir)

    assert loaded.conversations == ()
    assert len(loaded.source_errors) == 1
    error = loaded.source_errors[0]
    assert error["error_code"] == "source_relative_path_error"
    assert error["source_relative_path"] is None
    assert error["source_hash"] is None


def test_load_chatgpt_archive_source_dir_uses_fixture_tree_only(tmp_path: Path) -> None:
    # The atlas source loader should be fully testable against the fixture tree
    # without depending on the live ChatGPT archive source directory.
    source_dir = tmp_path / "source"
    _copy_fixture(
        source_dir,
        fixture_name="list_export.json",
        relative_path="alpha/conversations.json",
    )
    _copy_fixture(
        source_dir,
        fixture_name="single_dict_export.json",
        relative_path="beta/conversations.json",
    )
    _copy_fixture(
        source_dir,
        fixture_name="malformed_source.json",
        relative_path="gamma/conversations.json",
    )

    loaded = load_chatgpt_archive_source_dir(source_dir)
    iterated = list(iter_chatgpt_archive_source_conversations(source_dir))

    assert len(loaded.conversations) == 3
    assert len(loaded.source_errors) == 1
    assert len(iterated) == 3
    assert {row.source_relative_path for row in loaded.conversations} == {
        "alpha/conversations.json",
        "beta/conversations.json",
    }
    assert all(str(row.source_path).startswith(str(source_dir)) for row in loaded.conversations)
