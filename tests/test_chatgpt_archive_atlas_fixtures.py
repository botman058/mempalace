from __future__ import annotations

from pathlib import Path
from json import JSONDecodeError
import json

import pytest

from mempalace.chatgpt_identity import (
    extract_chatgpt_identity,
    iter_chatgpt_identity_records_from_json_file,
)
from mempalace.normalize import _collect_chatgpt_messages

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "chatgpt_archive_atlas"
MANIFEST_PATH = FIXTURE_DIR / "manifest.json"


def load_fixture_manifest() -> dict[str, dict]:
    """Read the shared fixture registry used by atlas fixture tests."""
    with MANIFEST_PATH.open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    if not isinstance(manifest, dict):
        raise AssertionError("Fixture manifest must be a JSON object")
    return manifest


def fixture_path(fixture_key: str) -> Path:
    """Locate a named fixture from the registry."""
    manifest = load_fixture_manifest()
    spec = manifest.get(fixture_key)
    if spec is None or "filename" not in spec:
        raise KeyError(f"Unknown fixture key: {fixture_key}")
    return FIXTURE_DIR / str(spec["filename"])


def _fixture_messages(fixture_key: str) -> list[tuple[str, str]]:
    path = fixture_path(fixture_key)
    conversation = json.loads(path.read_text(encoding="utf-8"))
    messages = _collect_chatgpt_messages(conversation)
    return messages


def test_fixture_inventory_is_stable_and_discoverable():
    manifest = load_fixture_manifest()

    assert FIXTURE_DIR.is_dir(), f"missing fixture directory: {FIXTURE_DIR}"
    assert "list_export" in manifest
    assert "single_dict_export" in manifest
    assert "malformed_source" in manifest
    assert "duplicate_source_identity" in manifest
    assert "explicit_topic_switch" in manifest
    assert "long_first_user_message" in manifest
    assert "mixed_legal_sysadmin_personal" in manifest

    for key, spec in manifest.items():
        path = fixture_path(key)
        assert path.exists(), f"fixture missing for {key}: {path}"
        assert path.suffix == ".json"
        assert path.parent == FIXTURE_DIR
        assert isinstance(spec.get("top_level"), str)
        assert spec["top_level"] in {"list", "dict", "malformed"}


@pytest.mark.parametrize(
    ("fixture_key", "expected_shape"),
    [
        ("list_export", list),
        ("single_dict_export", dict),
        ("duplicate_source_identity", list),
        ("explicit_topic_switch", dict),
        ("long_first_user_message", dict),
        ("mixed_legal_sysadmin_personal", dict),
    ],
)
def test_valid_fixtures_match_expected_top_level_shape(
    fixture_key: str,
    expected_shape: type,
) -> None:
    manifest = load_fixture_manifest()
    path = fixture_path(fixture_key)
    spec = manifest[fixture_key]
    assert spec["expected_records"] > 0
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, expected_shape)
    if expected_shape is list:
        assert len(payload) > 0
        assert len(payload) == spec["expected_records"]
    else:
        assert payload
        assert spec["expected_records"] == 1


def test_malformed_source_fixture_is_invalid_json():
    path = fixture_path("malformed_source")
    manifest = load_fixture_manifest()
    assert manifest["malformed_source"]["expected_records"] == 0
    assert manifest["malformed_source"]["top_level"] == "malformed"
    with pytest.raises(JSONDecodeError):
        json.loads(path.read_text(encoding="utf-8"))


def test_malformed_source_fixture_is_skipped_by_live_source_loaders():
    # This verifies the malformed artifact is intentionally malformed and
    # fails fast, so future atlas loading tests can confirm parser behavior.
    with pytest.raises(JSONDecodeError):
        list(iter_chatgpt_identity_records_from_json_file(fixture_path("malformed_source")))


def test_identity_loader_distinguishes_list_and_single_dict_shapes():
    single_records = list(iter_chatgpt_identity_records_from_json_file(fixture_path("single_dict_export")))
    list_records = list(iter_chatgpt_identity_records_from_json_file(fixture_path("list_export")))

    assert len(single_records) == 1
    assert len(list_records) == 2
    assert single_records[0].logical_source_id == "chatgpt:atlas-single-01"
    assert list_records[0].logical_source_id == "chatgpt:atlas-list-tech-01"
    assert list_records[1].logical_source_id == "chatgpt:atlas-list-personal-02"


def test_duplicate_source_identity_fixture_has_repeating_logical_id():
    path = fixture_path("duplicate_source_identity")
    payload = json.loads(path.read_text(encoding="utf-8"))
    ids = [extract_chatgpt_identity(item).logical_source_id for item in payload if extract_chatgpt_identity(item)]
    assert len(ids) >= 2
    assert len(ids) == len(payload)
    assert len(set(ids)) == 1


def test_explicit_topic_switch_turn_is_present():
    messages = _fixture_messages("explicit_topic_switch")
    switch_turns = [
        text
        for role, text in messages
        if role == "user" and "explicit topic switch" in text.lower()
    ]
    assert messages
    assert messages[0][0] == "user"
    assert switch_turns


def test_long_first_user_message_fixture_keeps_first_turn_intact():
    messages = _fixture_messages("long_first_user_message")
    assert len(messages) >= 2
    assert messages[0][0] == "user"
    assert len(messages[0][1]) >= 250


def test_mixed_legal_sysadmin_personal_fixture_contains_all_domains():
    messages = _fixture_messages("mixed_legal_sysadmin_personal")
    all_text = " ".join(text.lower() for _, text in messages)

    assert "indemnify" in all_text
    assert "systemctl" in all_text and "sudo" in all_text
    assert "recital" in all_text or "sister" in all_text
