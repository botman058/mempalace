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


class _FakeMCPCaller:
    def __init__(self, results: list[dict] | None = None) -> None:
        self.results = list(results or [])
        self.calls: list[dict] = []

    def call_tool(self, *, tool_name: str, arguments: dict, timeout: float) -> dict:
        self.calls.append({"tool_name": tool_name, "arguments": arguments, "timeout": timeout})
        if self.results:
            return self.results.pop(0)
        return {"success": True, "noop": False}


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


def test_publish_maps_reconciled_fields_to_add_signal_drawer_args(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    row = {
        "source_signal_id": "srcsig:abc",
        "room": "projects",
        "content": "LOCALAI_THREAD_SIGNAL\n\nDo thing",
        "logical_source_id": "chatgpt:c6",
        "source_hash": "h6",
        "conversation_id": "c6",
        "conversation_title": "T6",
        "subthread_id": "chatgpt:c6:subthread:000",
        "subthread_label": "projects",
        "segment_ids": ["seg-1", "seg-2"],
        "segment_refs": [{"segment_id": "seg-1", "segment_index": 0, "char_start": 0, "char_end": 8}],
        "evidence": ["proof line"],
        "extraction_version": "v6",
    }
    (run_dir / "reconciled_signals.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    source_dir = tmp_path / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "conversations.json").write_text("[]", encoding="utf-8")
    args = SimpleNamespace(
        source_dir=str(source_dir),
        run_dir=str(run_dir),
        localai_base_url="http://snow-white-iii:8080/v1",
        localai_token=None,
        localai_token_file=None,
        model="fake-model",
        localai_timeout=1.0,
        limit=0,
        publish=True,
        wing="chatgpt_thread_signals",
        added_by="localai_chatgpt_thread_signals",
        mempalace_url="http://localhost:8765",
        mempalace_token=None,
        mempalace_token_file=None,
        mempalace_timeout=5.0,
    )
    mcp = _FakeMCPCaller([{"success": True, "noop": False}])
    run(args, provider=_FakeProvider([]), mcp_caller=mcp)
    assert len(mcp.calls) == 1
    call = mcp.calls[0]
    assert call["tool_name"] == "mempalace_add_signal_drawer"
    assert call["arguments"]["wing"] == "chatgpt_thread_signals"
    assert call["arguments"]["room"] == "projects"
    assert call["arguments"]["source_signal_id"] == "srcsig:abc"
    assert call["arguments"]["logical_source_id"] == "chatgpt:c6"
    assert call["arguments"]["source_hash"] == "h6"
    assert call["arguments"]["conversation_id"] == "c6"
    assert call["arguments"]["conversation_title"] == "T6"
    assert call["arguments"]["subthread_id"] == "chatgpt:c6:subthread:000"
    assert call["arguments"]["subthread_label"] == "projects"
    assert call["arguments"]["segment_ids"] == ["seg-1", "seg-2"]
    assert isinstance(call["arguments"]["segment_ref"], str)
    assert call["arguments"]["segment_ref"] == "segment_id:seg-1|segment_index:0|chars:0-8"
    assert len(call["arguments"]["segment_ref"]) <= 128
    assert call["arguments"]["evidence_excerpt"] == "proof line"
    assert call["arguments"]["extraction_version"] == "v6"


def test_publish_rerun_skips_success_checkpoint_without_second_call(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    row = {
        "source_signal_id": "srcsig:rerun",
        "room": "general",
        "content": "x",
        "logical_source_id": "chatgpt:c7",
        "source_hash": "h7",
        "conversation_id": "c7",
        "conversation_title": "",
        "subthread_id": "chatgpt:c7:subthread:000",
        "subthread_label": "general",
        "segment_ids": ["seg-a"],
        "segment_refs": [],
        "evidence": [],
        "extraction_version": "v7",
    }
    (run_dir / "reconciled_signals.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    source_dir = tmp_path / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "conversations.json").write_text("[]", encoding="utf-8")
    args = SimpleNamespace(
        source_dir=str(source_dir),
        run_dir=str(run_dir),
        localai_base_url="http://snow-white-iii:8080/v1",
        localai_token=None,
        localai_token_file=None,
        model="fake-model",
        localai_timeout=1.0,
        limit=0,
        publish=True,
        wing="chatgpt_thread_signals",
        added_by="localai_chatgpt_thread_signals",
        mempalace_url="http://localhost:8765",
        mempalace_token=None,
        mempalace_token_file=None,
        mempalace_timeout=5.0,
    )
    mcp1 = _FakeMCPCaller([{"success": True, "noop": False}])
    run(args, provider=_FakeProvider([]), mcp_caller=mcp1)
    assert len(mcp1.calls) == 1
    mcp2 = _FakeMCPCaller([{"success": True, "noop": False}])
    run(args, provider=_FakeProvider([]), mcp_caller=mcp2)
    assert len(mcp2.calls) == 0


def test_publish_noop_result_counts_as_success(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    row = {
        "source_signal_id": "srcsig:noop",
        "room": "general",
        "content": "x",
        "logical_source_id": "chatgpt:c8",
        "source_hash": "h8",
        "conversation_id": "c8",
        "conversation_title": "",
        "subthread_id": "chatgpt:c8:subthread:000",
        "subthread_label": "general",
        "segment_ids": ["seg-n"],
        "segment_refs": [],
        "evidence": [],
        "extraction_version": "v8",
    }
    (run_dir / "reconciled_signals.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    source_dir = tmp_path / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "conversations.json").write_text("[]", encoding="utf-8")
    args = SimpleNamespace(
        source_dir=str(source_dir),
        run_dir=str(run_dir),
        localai_base_url="http://snow-white-iii:8080/v1",
        localai_token=None,
        localai_token_file=None,
        model="fake-model",
        localai_timeout=1.0,
        limit=0,
        publish=True,
        wing="chatgpt_thread_signals",
        added_by="localai_chatgpt_thread_signals",
        mempalace_url="http://localhost:8765",
        mempalace_token=None,
        mempalace_token_file=None,
        mempalace_timeout=5.0,
    )
    run(args, provider=_FakeProvider([]), mcp_caller=_FakeMCPCaller([{"success": True, "noop": True}]))
    progress = json.loads((run_dir / "progress.json").read_text(encoding="utf-8"))
    assert progress["publish_success"] == 1
    checkpoint = _read_jsonl(run_dir / "publish_checkpoint.jsonl")
    assert checkpoint[0]["status"] == "noop_success"


def test_publish_failed_result_is_checkpointed_and_progress_failed(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    row = {
        "source_signal_id": "srcsig:fail",
        "room": "general",
        "content": "x",
        "logical_source_id": "chatgpt:c9",
        "source_hash": "h9",
        "conversation_id": "c9",
        "conversation_title": "",
        "subthread_id": "chatgpt:c9:subthread:000",
        "subthread_label": "general",
        "segment_ids": ["seg-f"],
        "segment_refs": [],
        "evidence": [],
        "extraction_version": "v9",
    }
    (run_dir / "reconciled_signals.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    source_dir = tmp_path / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "conversations.json").write_text("[]", encoding="utf-8")
    args = SimpleNamespace(
        source_dir=str(source_dir),
        run_dir=str(run_dir),
        localai_base_url="http://snow-white-iii:8080/v1",
        localai_token=None,
        localai_token_file=None,
        model="fake-model",
        localai_timeout=1.0,
        limit=0,
        publish=True,
        wing="chatgpt_thread_signals",
        added_by="localai_chatgpt_thread_signals",
        mempalace_url="http://localhost:8765",
        mempalace_token=None,
        mempalace_token_file=None,
        mempalace_timeout=5.0,
    )
    run(args, provider=_FakeProvider([]), mcp_caller=_FakeMCPCaller([{"success": False, "error": "boom"}]))
    progress = json.loads((run_dir / "progress.json").read_text(encoding="utf-8"))
    assert progress["publish_failed"] == 1
    checkpoint = _read_jsonl(run_dir / "publish_checkpoint.jsonl")
    assert checkpoint[0]["status"] == "failed"


def test_run_without_publish_does_not_call_mcp(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "conversations.json").write_text(
        json.dumps([_conversation_from_messages([("user", "hello"), ("assistant", "hi")], "conv-no-pub")]),
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
        publish=False,
        wing="chatgpt_thread_signals",
        added_by="localai_chatgpt_thread_signals",
        mempalace_url="http://localhost:8765",
        mempalace_token=None,
        mempalace_token_file=None,
        mempalace_timeout=5.0,
    )
    mcp = _FakeMCPCaller()
    run(args, provider=_FakeProvider(['{"summary":"ok","items":[]}']), mcp_caller=mcp)
    assert len(mcp.calls) == 0
    progress = json.loads((run_dir / "progress.json").read_text(encoding="utf-8"))
    assert "publish_success" not in progress


def test_publish_string_only_fields_never_receive_dict_or_list(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    row = {
        "source_signal_id": "srcsig:flat",
        "room": "general",
        "content": "x",
        "logical_source_id": "chatgpt:c10",
        "source_hash": "h10",
        "conversation_id": "c10",
        "conversation_title": "",
        "subthread_id": "chatgpt:c10:subthread:000",
        "subthread_label": "general",
        "segment_ids": ["seg-z"],
        "segment_refs": [{"segment_id": "seg-z", "segment_index": 7, "char_start": 10, "char_end": 42}],
        "evidence": ["flat proof"],
        "extraction_version": "v10",
    }
    (run_dir / "reconciled_signals.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    source_dir = tmp_path / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "conversations.json").write_text("[]", encoding="utf-8")
    args = SimpleNamespace(
        source_dir=str(source_dir),
        run_dir=str(run_dir),
        localai_base_url="http://snow-white-iii:8080/v1",
        localai_token=None,
        localai_token_file=None,
        model="fake-model",
        localai_timeout=1.0,
        limit=0,
        publish=True,
        wing="chatgpt_thread_signals",
        added_by="localai_chatgpt_thread_signals",
        mempalace_url="http://localhost:8765",
        mempalace_token=None,
        mempalace_token_file=None,
        mempalace_timeout=5.0,
    )
    mcp = _FakeMCPCaller([{"success": True, "noop": False}])
    run(args, provider=_FakeProvider([]), mcp_caller=mcp)
    call_args = mcp.calls[0]["arguments"]
    assert isinstance(call_args["segment_ref"], str)
    assert isinstance(call_args["evidence_excerpt"], str)
    assert not isinstance(call_args["segment_ref"], (dict, list))
    assert not isinstance(call_args["evidence_excerpt"], (dict, list))


def test_publish_metadata_string_fields_are_bounded_to_128(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    long = "x" * 400
    row = {
        "source_signal_id": "srcsig:" + ("a" * 160),
        "room": "general",
        "content": "x" * 5000,
        "logical_source_id": long,
        "source_hash": long,
        "conversation_id": long,
        "conversation_title": long,
        "subthread_id": long,
        "subthread_label": long,
        "segment_ids": ["seg-long"],
        "segment_refs": [{"segment_id": "s" * 220, "segment_index": 123456, "char_start": 0, "char_end": 999999}],
        "evidence": [long],
        "extraction_version": long,
    }
    (run_dir / "reconciled_signals.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    source_dir = tmp_path / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "conversations.json").write_text("[]", encoding="utf-8")
    args = SimpleNamespace(
        source_dir=str(source_dir),
        run_dir=str(run_dir),
        localai_base_url="http://snow-white-iii:8080/v1",
        localai_token=None,
        localai_token_file=None,
        model="fake-model",
        localai_timeout=1.0,
        limit=0,
        publish=True,
        wing="chatgpt_thread_signals",
        added_by=long,
        mempalace_url="http://localhost:8765",
        mempalace_token=None,
        mempalace_token_file=None,
        mempalace_timeout=5.0,
    )
    mcp = _FakeMCPCaller([{"success": True, "noop": False}])
    run(args, provider=_FakeProvider([]), mcp_caller=mcp)
    call = mcp.calls[0]["arguments"]
    for field in (
        "source_signal_id",
        "logical_source_id",
        "source_hash",
        "conversation_id",
        "conversation_title",
        "subthread_id",
        "subthread_label",
        "segment_ref",
        "evidence_excerpt",
        "extraction_version",
        "added_by",
    ):
        assert isinstance(call[field], str)
        assert len(call[field]) <= 128
    assert len(call["content"]) == 5000
