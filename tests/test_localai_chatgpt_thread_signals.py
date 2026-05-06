from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.localai_chatgpt_thread_signals import ensure_localai_base_url, run


def _conversation_from_messages(messages: list[tuple[str, str]], conversation_id: str = "conv-1") -> dict:
    mapping: dict[str, dict] = {
        "root": {"id": "root", "parent": None, "children": ["n0"], "message": None}
    }
    prev = "root"
    for i, (role, text) in enumerate(messages):
        node_id = f"n{i}"
        next_id = f"n{i + 1}" if i + 1 < len(messages) else None
        mapping[node_id] = {
            "id": node_id,
            "parent": prev,
            "children": [next_id] if next_id else [],
            "message": {
                "author": {"role": role},
                "content": {"parts": [text]},
            },
        }
        if prev in mapping:
            mapping[prev]["children"] = [node_id]
        prev = node_id
    return {
        "id": conversation_id,
        "title": "Thread Fixture",
        "mapping": mapping,
        "current_node": prev if prev != "root" else "root",
    }


class _FakeProvider:
    def __init__(self, outputs: list[str]) -> None:
        self.outputs = list(outputs)
        self.calls: list[dict[str, str]] = []

    def classify_segment(self, *, prompt_messages: list[dict[str, str]]) -> str:
        self.calls.append(prompt_messages[-1])
        if self.outputs:
            return self.outputs.pop(0)
        return '{"summary":"ok","items":[]}'


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def test_long_oversized_conversation_drives_multiple_segment_calls_and_suffix(tmp_path):
    source_dir = tmp_path / "source"
    nested = source_dir / "a" / "conversations.json"
    nested.parent.mkdir(parents=True, exist_ok=True)
    huge = ("X" * 13_500) + "SUFFIX_MARKER"
    convo = _conversation_from_messages(
        [
            ("user", huge),
            ("assistant", "ack"),
            ("user", "later turn marker"),
            ("assistant", "later reply marker"),
        ],
        conversation_id="conv-huge",
    )
    nested.write_text(json.dumps([convo]), encoding="utf-8")
    run_dir = tmp_path / "run"
    provider = _FakeProvider(['{"summary":"ok","items":[]}' for _ in range(8)])
    args = SimpleNamespace(
        source_dir=str(source_dir),
        run_dir=str(run_dir),
        localai_base_url="http://snow-white-iii:8080/v1",
        localai_token=None,
        localai_token_file=None,
        model="fake-model",
        localai_timeout=1.0,
        limit=0,
    )

    rc = run(args, provider=provider)
    assert rc == 0
    assert len(provider.calls) > 1
    payloads = [json.loads(call["content"]) for call in provider.calls]
    assert any("SUFFIX_MARKER" in p["segment_text"] for p in payloads)
    assert any("later turn marker" in p["segment_text"] for p in payloads)


def test_progress_and_checkpoint_update_after_each_segment(tmp_path):
    source_dir = tmp_path / "source"
    path = source_dir / "conversations.json"
    source_dir.mkdir(parents=True, exist_ok=True)
    msgs = []
    for i in range(20):
        msgs.append(("user", f"user {i} " + ("a" * 300)))
        msgs.append(("assistant", f"assistant {i} " + ("b" * 300)))
    path.write_text(json.dumps([_conversation_from_messages(msgs, "conv-long")]), encoding="utf-8")
    run_dir = tmp_path / "run"
    provider = _FakeProvider(['{"summary":"ok","items":[]}' for _ in range(20)])
    args = SimpleNamespace(
        source_dir=str(source_dir),
        run_dir=str(run_dir),
        localai_base_url="http://snow-white-iii:8080/v1",
        localai_token=None,
        localai_token_file=None,
        model="fake-model",
        localai_timeout=1.0,
        limit=3,
    )

    run(args, provider=provider)
    progress = json.loads((run_dir / "progress.json").read_text(encoding="utf-8"))
    checkpoints = _read_jsonl(run_dir / "segment_checkpoint.jsonl")
    assert 1 <= progress["processed_segments"] <= 3
    assert progress["processed_segments"] == len(checkpoints)
    assert len(provider.calls) == len(checkpoints)


def test_rerun_skips_already_checkpointed_segments_without_duplicates(tmp_path):
    source_dir = tmp_path / "source"
    path = source_dir / "conversations.json"
    source_dir.mkdir(parents=True, exist_ok=True)
    msgs = []
    for i in range(16):
        msgs.append(("user", f"user {i} " + ("a" * 340)))
        msgs.append(("assistant", f"assistant {i} " + ("b" * 340)))
    path.write_text(json.dumps([_conversation_from_messages(msgs, "conv-rerun")]), encoding="utf-8")
    run_dir = tmp_path / "run"
    args = SimpleNamespace(
        source_dir=str(source_dir),
        run_dir=str(run_dir),
        localai_base_url="http://snow-white-iii:8080/v1",
        localai_token=None,
        localai_token_file=None,
        model="fake-model",
        localai_timeout=1.0,
        limit=2,
    )
    run(args, provider=_FakeProvider(['{"summary":"ok","items":[]}' for _ in range(10)]))
    first_checkpoint = _read_jsonl(run_dir / "segment_checkpoint.jsonl")
    run(args, provider=_FakeProvider(['{"summary":"ok","items":[]}' for _ in range(10)]))
    second_checkpoint = _read_jsonl(run_dir / "segment_checkpoint.jsonl")
    assert len(first_checkpoint) == len(second_checkpoint)
    keys = [row["segment_key"] for row in second_checkpoint]
    assert len(keys) == len(set(keys))


def test_invalid_output_writes_invalid_record_and_failed_status(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "conversations.json").write_text(
        json.dumps([_conversation_from_messages([("user", "hello"), ("assistant", "hi")], "conv-invalid")]),
        encoding="utf-8",
    )
    run_dir = tmp_path / "run"
    args = SimpleNamespace(
        source_dir=str(source_dir),
        run_dir=str(run_dir),
        localai_base_url="http://snow-white-iii:8080/v1",
        localai_token=None,
        localai_token_file=None,
        model="fake-model",
        localai_timeout=1.0,
        limit=0,
    )
    run(args, provider=_FakeProvider(["not json"]))
    invalid_rows = _read_jsonl(run_dir / "invalid_outputs.jsonl")
    checkpoint_rows = _read_jsonl(run_dir / "segment_checkpoint.jsonl")
    assert invalid_rows
    assert invalid_rows[0]["error_code"] == "invalid_json"
    assert checkpoint_rows[0]["status"] == "invalid_output"


def test_ensure_localai_base_url_accepts_local_and_refuses_cloud_urls():
    assert ensure_localai_base_url("http://snow-white-iii:8080/v1") == "http://snow-white-iii:8080/v1"
    with pytest.raises(Exception):
        ensure_localai_base_url("https://api.openai.com/v1")
    with pytest.raises(Exception):
        ensure_localai_base_url("https://openrouter.ai/api/v1")
