from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.localai_chatgpt_thread_signals import ensure_localai_base_url, reconcile_segment_extractions, run


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


def test_reconcile_dedupes_overlapping_items_and_merges_segment_ids(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "status": "classified",
            "logical_source_id": "chatgpt:c1",
            "source_hash": "h1",
            "conversation_id": "c1",
            "conversation_title": "T1",
            "subthread_id": "chatgpt:c1:subthread:000",
            "subthread_label": "projects",
            "segment_id": "seg-1",
            "segment_index": 0,
            "char_start": 0,
            "char_end": 100,
            "extraction_version": "v1",
            "items": [
                {"type": "task", "text": "Refactor login flow", "importance": 3, "evidence": "Refactor login flow now"}
            ],
        },
        {
            "status": "classified",
            "logical_source_id": "chatgpt:c1",
            "source_hash": "h1",
            "conversation_id": "c1",
            "conversation_title": "T1",
            "subthread_id": "chatgpt:c1:subthread:000",
            "subthread_label": "projects",
            "segment_id": "seg-2",
            "segment_index": 1,
            "char_start": 90,
            "char_end": 180,
            "extraction_version": "v1",
            "items": [
                {"type": "task", "text": "refactor   login flow.", "importance": 4, "evidence": "refactor login flow"}
            ],
        },
    ]
    with (run_dir / "segment_extractions.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")

    stats = reconcile_segment_extractions(run_dir=run_dir, model="fake-model")
    out = _read_jsonl(run_dir / "reconciled_signals.jsonl")
    assert stats["reconciled_signals"] == 1
    assert len(out) == 1
    assert out[0]["segment_ids"] == ["seg-1", "seg-2"]
    assert out[0]["subthread_id"] == "chatgpt:c1:subthread:000"


def test_reconcile_preserves_distinct_items_in_same_subthread(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "status": "classified",
            "logical_source_id": "chatgpt:c2",
            "source_hash": "h2",
            "conversation_id": "c2",
            "conversation_title": "T2",
            "subthread_id": "chatgpt:c2:subthread:000",
            "subthread_label": "general",
            "segment_id": "seg-a",
            "segment_index": 0,
            "char_start": 0,
            "char_end": 50,
            "items": [
                {"type": "task", "text": "Ship release checklist", "importance": 3, "evidence": "release checklist"},
                {"type": "problem", "text": "Staging deploy keeps failing", "importance": 4, "evidence": "deploy fails"},
            ],
        }
    ]
    with (run_dir / "segment_extractions.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
    reconcile_segment_extractions(run_dir=run_dir, model="fake-model")
    out = _read_jsonl(run_dir / "reconciled_signals.jsonl")
    assert len(out) == 2
    texts = {row["content"] for row in out}
    assert any("Ship release checklist" in text for text in texts)
    assert any("Staging deploy keeps failing" in text for text in texts)


def test_reconcile_keeps_distinct_provenance_across_subthreads_and_conversations(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "status": "classified",
            "logical_source_id": "chatgpt:c3",
            "source_hash": "h3",
            "conversation_id": "c3",
            "conversation_title": "T3",
            "subthread_id": "chatgpt:c3:subthread:000",
            "subthread_label": "general",
            "segment_id": "seg-1",
            "segment_index": 0,
            "char_start": 0,
            "char_end": 30,
            "items": [{"type": "fact", "text": "Room alpha", "importance": 2, "evidence": "alpha"}],
        },
        {
            "status": "classified",
            "logical_source_id": "chatgpt:c3",
            "source_hash": "h3",
            "conversation_id": "c3",
            "conversation_title": "T3",
            "subthread_id": "chatgpt:c3:subthread:001",
            "subthread_label": "general",
            "segment_id": "seg-2",
            "segment_index": 1,
            "char_start": 31,
            "char_end": 60,
            "items": [{"type": "fact", "text": "Room alpha", "importance": 2, "evidence": "alpha"}],
        },
    ]
    with (run_dir / "segment_extractions.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
    reconcile_segment_extractions(run_dir=run_dir, model="fake-model")
    out = _read_jsonl(run_dir / "reconciled_signals.jsonl")
    assert len(out) == 2
    assert out[0]["source_signal_id"] != out[1]["source_signal_id"]


def test_reconcile_rerun_is_idempotent_and_does_not_duplicate(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    row = {
        "status": "classified",
        "logical_source_id": "chatgpt:c4",
        "source_hash": "h4",
        "conversation_id": "c4",
        "conversation_title": "T4",
        "subthread_id": "chatgpt:c4:subthread:000",
        "subthread_label": "plans",
        "segment_id": "seg-x",
        "segment_index": 0,
        "char_start": 0,
        "char_end": 10,
        "items": [{"type": "task", "text": "Book dentist", "importance": 4, "evidence": "book dentist"}],
    }
    (run_dir / "segment_extractions.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    reconcile_segment_extractions(run_dir=run_dir, model="fake-model")
    first = (run_dir / "reconciled_signals.jsonl").read_text(encoding="utf-8")
    reconcile_segment_extractions(run_dir=run_dir, model="fake-model")
    second = (run_dir / "reconciled_signals.jsonl").read_text(encoding="utf-8")
    assert first == second
    assert len(_read_jsonl(run_dir / "reconciled_signals.jsonl")) == 1


def test_reconcile_records_include_fields_for_signal_drawer_write(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    row = {
        "status": "classified",
        "logical_source_id": "chatgpt:c5",
        "source_hash": "h5",
        "conversation_id": "c5",
        "conversation_title": "T5",
        "subthread_id": "chatgpt:c5:subthread:000",
        "subthread_label": "finance",
        "segment_id": "seg-y",
        "segment_index": 0,
        "char_start": 0,
        "char_end": 12,
        "extraction_version": "v5",
        "items": [{"type": "fact", "text": "Budget is due Friday", "importance": 3, "evidence": "due Friday"}],
    }
    (run_dir / "segment_extractions.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    reconcile_segment_extractions(run_dir=run_dir, model="fake-model")
    out = _read_jsonl(run_dir / "reconciled_signals.jsonl")
    assert len(out) == 1
    record = out[0]
    for field in (
        "source_signal_id",
        "room",
        "content",
        "logical_source_id",
        "source_hash",
        "conversation_id",
        "conversation_title",
        "subthread_id",
        "subthread_label",
        "segment_ids",
        "segment_refs",
        "evidence",
        "extraction_version",
    ):
        assert field in record
