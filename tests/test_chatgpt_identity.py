import copy
import hashlib
import json

from mempalace.chatgpt_identity import (
    extract_chatgpt_identity,
    iter_chatgpt_identity_records_from_json_file,
)


def _conversation_with_pair():
    return {
        "title": "Greeting",
        "current_node": "a1",
        "mapping": {
            "root": {"parent": None, "message": None, "children": ["u1"]},
            "u1": {
                "parent": "root",
                "message": {
                    "author": {"role": "user"},
                    "content": {"parts": ["Hello ChatGPT"]},
                },
                "children": ["a1"],
            },
            "a1": {
                "parent": "u1",
                "message": {
                    "author": {"role": "assistant"},
                    "content": {"parts": ["Hello back"]},
                },
                "children": [],
            },
        },
    }


def test_extract_chatgpt_identity_uses_id_key():
    conversation = _conversation_with_pair()
    conversation["id"] = "convo-123"

    record = extract_chatgpt_identity(conversation)

    assert record is not None
    assert record.logical_source_id == "chatgpt:convo-123"
    assert record.conversation_id == "convo-123"
    assert record.title == "Greeting"
    assert record.transcript == "> Hello ChatGPT\nHello back\n"
    expected_hash = hashlib.sha256(record.transcript.encode("utf-8")).hexdigest()[:24]
    assert record.source_hash == expected_hash


def test_extract_chatgpt_identity_falls_back_to_mapping_digest():
    conversation = _conversation_with_pair()

    record = extract_chatgpt_identity(conversation)

    assert record is not None
    digest = hashlib.sha256(
        json.dumps(
            conversation["mapping"],
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
    ).hexdigest()[:24]
    assert record.logical_source_id == f"chatgpt:sha256:{digest}"
    assert record.conversation_id is None


def test_extract_chatgpt_identity_uses_selected_branch_for_transcript_and_hash():
    conversation = {
        "title": "Branching",
        "current_node": "selected_a",
        "mapping": {
            "root": {"parent": None, "message": None, "children": ["u1"]},
            "u1": {
                "parent": "root",
                "message": {
                    "author": {"role": "user"},
                    "content": {"parts": ["Question"]},
                },
                "children": ["old_a", "selected_a"],
            },
            "old_a": {
                "parent": "u1",
                "message": {
                    "author": {"role": "assistant"},
                    "content": {"parts": ["Old branch"]},
                },
                "children": [],
            },
            "selected_a": {
                "parent": "u1",
                "message": {
                    "author": {"role": "assistant"},
                    "content": {"parts": ["Selected branch"]},
                },
                "children": [],
            },
        },
    }

    selected_record = extract_chatgpt_identity(conversation)
    old_branch_conversation = copy.deepcopy(conversation)
    old_branch_conversation["current_node"] = "old_a"
    old_record = extract_chatgpt_identity(old_branch_conversation)

    assert selected_record is not None
    assert old_record is not None
    assert "Selected branch" in selected_record.transcript
    assert "Old branch" not in selected_record.transcript
    assert selected_record.transcript != old_record.transcript
    assert selected_record.source_hash != old_record.source_hash


def test_extract_chatgpt_identity_requires_two_selected_messages():
    conversation = {
        "title": "Too short",
        "current_node": "u1",
        "mapping": {
            "root": {"parent": None, "message": None, "children": ["u1"]},
            "u1": {
                "parent": "root",
                "message": {
                    "author": {"role": "user"},
                    "content": {"parts": ["Only one message"]},
                },
                "children": [],
            },
        },
    }

    assert extract_chatgpt_identity(conversation) is None


def test_iter_chatgpt_identity_records_from_json_file_supports_dict_and_list(tmp_path):
    single_path = tmp_path / "single.json"
    single_conversation = _conversation_with_pair()
    single_conversation["conversation_id"] = "single-456"
    single_path.write_text(json.dumps(single_conversation), encoding="utf-8")

    single_records = list(iter_chatgpt_identity_records_from_json_file(single_path))

    assert len(single_records) == 1
    assert single_records[0].logical_source_id == "chatgpt:single-456"

    list_path = tmp_path / "list.json"
    list_path.write_text(
        json.dumps(
            [
                {"not_chatgpt": True},
                _conversation_with_pair(),
                {
                    "mapping": {
                        "root": {"parent": None, "message": None, "children": ["u1"]},
                        "u1": {
                            "parent": "root",
                            "message": {
                                "author": {"role": "user"},
                                "content": {"parts": ["skip me"]},
                            },
                            "children": [],
                        },
                    }
                },
            ]
        ),
        encoding="utf-8",
    )

    list_records = list(iter_chatgpt_identity_records_from_json_file(list_path))

    assert len(list_records) == 1
    assert list_records[0].title == "Greeting"


def test_non_chatgpt_json_shapes_are_ignored(tmp_path):
    assert extract_chatgpt_identity({"title": "plain dict"}) is None

    dict_path = tmp_path / "dict.json"
    dict_path.write_text(json.dumps({"random": "data"}), encoding="utf-8")
    assert list(iter_chatgpt_identity_records_from_json_file(dict_path)) == []

    list_path = tmp_path / "list.json"
    list_path.write_text(json.dumps([{"random": "data"}]), encoding="utf-8")
    assert list(iter_chatgpt_identity_records_from_json_file(list_path)) == []
