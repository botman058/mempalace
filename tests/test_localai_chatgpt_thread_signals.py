from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.localai_chatgpt_thread_signals import (
    DEFAULT_ATLAS_GUIDED_RUN_DIR,
    FatalRemoteError,
    ensure_localai_base_url,
    parse_args,
    reconcile_segment_extractions,
    run,
)
from mempalace import chatgpt_atlas_guided_contract as guided_contract


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


def _base_args(source_dir: Path, run_dir: Path, **overrides):
    args = {
        "source_dir": str(source_dir),
        "run_dir": str(run_dir),
        "localai_base_url": "http://snow-white-iii:8080/v1",
        "localai_token": None,
        "localai_token_file": None,
        "model": "fake-model",
        "localai_timeout": 1.0,
        "limit": 0,
        "retry_errors": False,
        "provider_max_attempts": 2,
        "atlas_guided": False,
        "atlas_run_dir": None,
        "candidate_records": None,
        "publish": False,
        "publish_limit": 0,
        "wing": "chatgpt_thread_signals",
        "added_by": "localai_chatgpt_thread_signals",
        "mempalace_url": "http://localhost:8765",
        "mempalace_token": None,
        "mempalace_token_file": None,
        "mempalace_timeout": 5.0,
    }
    args.update(overrides)
    return SimpleNamespace(**args)


_ATLAS_TEST_RUN_ID = "atlas_full2_20260512T0412Z_2fc8ac5"
_ATLAS_TEST_CANDIDATE_ID = "cand_devops__postgres_latency"
_ATLAS_TEST_CANDIDATE_KEY = "devops:postgres_latency"


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def _atlas_artifact_rows(conversation_id: str, thread_id: str | None = None) -> tuple[dict, dict]:
    effective_thread_id = thread_id or f"chatgpt:{conversation_id}"
    return (
        guided_contract.build_thread_candidate_record(
            run_id=_ATLAS_TEST_RUN_ID,
            atlas_run_id=_ATLAS_TEST_RUN_ID,
            thread_id=effective_thread_id,
            lookup_status="mapped",
            candidate_ids=[_ATLAS_TEST_CANDIDATE_ID],
            candidate_keys=[_ATLAS_TEST_CANDIDATE_KEY],
            cluster_ids=["cluster-001"],
            primary_candidate_id=_ATLAS_TEST_CANDIDATE_ID,
            primary_candidate_key=_ATLAS_TEST_CANDIDATE_KEY,
            reason_codes=["candidate_cluster_member"],
            source_thread_ref="atlas_thread_candidates.jsonl#1",
        ),
        guided_contract.build_candidate_bridge_record(
            run_id=_ATLAS_TEST_RUN_ID,
            atlas_run_id=_ATLAS_TEST_RUN_ID,
            candidate_id=_ATLAS_TEST_CANDIDATE_ID,
            candidate_key=_ATLAS_TEST_CANDIDATE_KEY,
            bridge_status="candidate",
            atlas_cluster_id="cluster-001",
            atlas_cluster_status="candidate",
            topic_label="Ops readiness",
            label="Postgres latency",
            definition="Signals related to postgres latency and ops stability.",
            thread_ids=[effective_thread_id],
            top_terms=[{"term": "postgres", "count": 6}],
            evidence_titles=["thread export"],
            representative_thread_ids=[effective_thread_id],
            representative_excerpts=["Latency spike observed."],
            mixed_reasons=[],
        ),
    )


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
    args = _base_args(source_dir, run_dir)

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
    args = _base_args(source_dir, run_dir, limit=3)

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
    args = _base_args(source_dir, run_dir, limit=2)
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
    args = _base_args(source_dir, run_dir)
    run(args, provider=_FakeProvider(["not json"]))
    invalid_rows = _read_jsonl(run_dir / "invalid_outputs.jsonl")
    checkpoint_rows = _read_jsonl(run_dir / "segment_checkpoint.jsonl")
    assert invalid_rows
    assert invalid_rows[0]["error_code"] == "invalid_json"
    assert checkpoint_rows[0]["status"] == "invalid_output"


def test_ensure_localai_base_url_accepts_local_and_refuses_cloud_urls():
    assert ensure_localai_base_url("http://snow-white-iii:8080/v1") == "http://snow-white-iii:8080/v1"
    assert ensure_localai_base_url("http://localhost:8080/v1") == "http://localhost:8080/v1"
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
    args = _base_args(
        source_dir,
        run_dir,
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
    args = _base_args(
        source_dir,
        run_dir,
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
    args = _base_args(
        source_dir,
        run_dir,
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


def test_publish_limit_bounds_publish_attempts(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "source_signal_id": "srcsig:limit-1",
            "room": "general",
            "content": "x",
            "logical_source_id": "chatgpt:limit",
            "source_hash": "h-limit",
            "conversation_id": "limit",
            "conversation_title": "",
            "subthread_id": "chatgpt:limit:subthread:000",
            "subthread_label": "general",
            "segment_ids": ["seg-1"],
            "segment_refs": [],
            "evidence": [],
            "extraction_version": "v-limit",
        },
        {
            "source_signal_id": "srcsig:limit-2",
            "room": "general",
            "content": "y",
            "logical_source_id": "chatgpt:limit",
            "source_hash": "h-limit",
            "conversation_id": "limit",
            "conversation_title": "",
            "subthread_id": "chatgpt:limit:subthread:000",
            "subthread_label": "general",
            "segment_ids": ["seg-2"],
            "segment_refs": [],
            "evidence": [],
            "extraction_version": "v-limit",
        },
    ]
    (run_dir / "reconciled_signals.jsonl").write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )
    source_dir = tmp_path / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "conversations.json").write_text("[]", encoding="utf-8")
    args = _base_args(
        source_dir,
        run_dir,
        publish=True,
        publish_limit=1,
        wing="chatgpt_thread_signals",
        added_by="localai_chatgpt_thread_signals",
        mempalace_url="http://localhost:8765",
        mempalace_token=None,
        mempalace_token_file=None,
        mempalace_timeout=5.0,
    )
    mcp = _FakeMCPCaller([{"success": True, "noop": False}, {"success": True, "noop": False}])
    run(args, provider=_FakeProvider([]), mcp_caller=mcp)
    assert len(mcp.calls) == 1
    progress = json.loads((run_dir / "progress.json").read_text(encoding="utf-8"))
    assert progress["publish_attempted"] == 1
    assert progress["publish_success"] == 1
    assert len(_read_jsonl(run_dir / "publish_checkpoint.jsonl")) == 1


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
    args = _base_args(
        source_dir,
        run_dir,
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
    args = _base_args(
        source_dir,
        run_dir,
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


def _write_atlas_guided_input_artifacts(
    atlas_run_dir: Path, *, conversation_id: str
) -> None:
    lookup_row, bridge_row = _atlas_artifact_rows(conversation_id=conversation_id)
    _write_jsonl(
        atlas_run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["atlas_thread_candidates"],
        [lookup_row],
    )
    _write_jsonl(
        atlas_run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["candidate_bridge_records"],
        [bridge_row],
    )


def _atlas_guided_payload(
    *,
    signal_status: str = "accepted",
    candidate_id: str | None = _ATLAS_TEST_CANDIDATE_ID,
    candidate_key: str | None = _ATLAS_TEST_CANDIDATE_KEY,
    error_code: str | None = None,
) -> str:
    if error_code is not None:
        return error_code
    record: dict[str, object] = {
        "signals": [
            {
                "signal_status": signal_status,
                "signal_type": "task",
                "title": "Track query latency",
                "summary": "A durable planning or ops signal was extracted.",
                "source_excerpt": "Reduce index contention and improve planner stats.",
                "confidence": 0.91,
                "candidate_id": candidate_id,
                "candidate_key": candidate_key,
                "canonical_wing": "devops",
                "canonical_room": "postgres_latency",
            }
        ]
    }
    if signal_status == "null_signal":
        for key in ("candidate_id", "candidate_key", "canonical_wing", "canonical_room"):
            record["signals"][0][key] = None
    return json.dumps(record)


def _atlas_multisegment_conversation(conversation_id: str) -> dict:
    oversized = "atlas multi segment " + ("X" * 13_500)
    return _conversation_from_messages([("user", oversized), ("assistant", "ack")], conversation_id)


def test_atlas_guided_no_publish_writes_contract_progress_and_extraction_records(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    source_dir.joinpath("conversations.json").write_text(
        json.dumps([_atlas_multisegment_conversation("conv-atlas-guided")]),
        encoding="utf-8",
    )
    run_dir = tmp_path / "run"
    atlas_run_dir = tmp_path / "atlas_run"
    _write_atlas_guided_input_artifacts(atlas_run_dir, conversation_id="conv-atlas-guided")
    args = _base_args(
        source_dir,
        run_dir,
        atlas_guided=True,
        atlas_run_dir=str(atlas_run_dir),
        candidate_records=str(
            atlas_run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["candidate_bridge_records"]
        ),
        publish=False,
        limit=2,
    )
    provider = _FakeProvider(
        [
            _atlas_guided_payload(signal_status="accepted"),
            "not json",
            _atlas_guided_payload(signal_status="accepted"),
        ]
    )
    mcp = _FakeMCPCaller()
    run(args, provider=provider, mcp_caller=mcp)
    assert len(mcp.calls) == 0
    assert len(provider.calls) == 2

    progress = json.loads((run_dir / "progress.json").read_text(encoding="utf-8"))
    assert guided_contract.validate_row(guided_contract.RUN_PROGRESS_SCHEMA, progress) == progress

    extraction_records = _read_jsonl(
        run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["extraction_records"]
    )
    checkpoints = _read_jsonl(run_dir / "segment_checkpoint.jsonl")
    invalid_outputs = _read_jsonl(run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["invalid_outputs"])
    assert len(extraction_records) == 2
    assert len(checkpoints) == 2
    assert any(row["extraction_status"] == "invalid_output" for row in extraction_records)
    assert len(invalid_outputs) == 1
    for row in extraction_records:
        guided_contract.validate_row(guided_contract.EXTRACTION_RECORD_SCHEMA, row)


def test_atlas_guided_unknown_candidate_produces_durable_invalid_output(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    source_dir.joinpath("conversations.json").write_text(
        json.dumps([_conversation_from_messages([("user", "hello"), ("assistant", "hi")], "conv-atlas-unknown")]),
        encoding="utf-8",
    )
    run_dir = tmp_path / "run"
    atlas_run_dir = tmp_path / "atlas_run"
    _write_atlas_guided_input_artifacts(atlas_run_dir, conversation_id="conv-atlas-unknown")
    args = _base_args(
        source_dir,
        run_dir,
        atlas_guided=True,
        atlas_run_dir=str(atlas_run_dir),
    )
    run(
        args,
        provider=_FakeProvider(
            [
                _atlas_guided_payload(
                    signal_status="accepted",
                    candidate_id="cand_unknown__ops",
                    candidate_key="ops:unknown",
                )
            ]
        ),
    )
    invalid_rows = _read_jsonl(run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["invalid_outputs"])
    extraction_rows = _read_jsonl(run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["extraction_records"])
    assert invalid_rows or extraction_rows
    if invalid_rows:
        assert invalid_rows[0]["status"] == "invalid_output" or invalid_rows[0].get("extraction_status") == "invalid_output"
        assert (
            invalid_rows[0].get("error_code") == "unknown_candidate_id"
            or invalid_rows[0].get("provenance", {}).get("error_code") == "unknown_candidate_id"
        )
    if extraction_rows:
        invalid = [row for row in extraction_rows if row["extraction_status"] == "invalid_output"]
        assert invalid
        for row in invalid:
            assert row["provenance"]["error_code"] == "unknown_candidate_id"


def test_atlas_guided_resume_skips_already_completed_segments(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    source_dir.joinpath("conversations.json").write_text(
        json.dumps([_conversation_from_messages([("user", "hello"), ("assistant", "hi")], "conv-atlas-resume")]),
        encoding="utf-8",
    )
    run_dir = tmp_path / "run"
    atlas_run_dir = tmp_path / "atlas_run"
    _write_atlas_guided_input_artifacts(atlas_run_dir, conversation_id="conv-atlas-resume")
    args = _base_args(
        source_dir,
        run_dir,
        atlas_guided=True,
        atlas_run_dir=str(atlas_run_dir),
    )
    first = _FakeProvider([_atlas_guided_payload(signal_status="accepted")])
    run(args, provider=first)
    before = _read_jsonl(run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["extraction_records"])
    assert len(before) == 1

    second = _FakeProvider([_atlas_guided_payload(signal_status="accepted")])
    run(args, provider=second)
    after = _read_jsonl(run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["extraction_records"])
    assert len(after) == 1
    assert second.calls == []


def test_atlas_guided_requires_atlas_run_and_candidate_artifacts(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    source_dir.joinpath("conversations.json").write_text(
        json.dumps([_conversation_from_messages([("user", "hello"), ("assistant", "hi")], "conv-atlas-missing")]),
        encoding="utf-8",
    )
    run_dir = tmp_path / "run"
    atlas_run_dir = tmp_path / "atlas_run"
    args = _base_args(
        source_dir,
        run_dir,
        atlas_guided=True,
        atlas_run_dir=str(atlas_run_dir),
        candidate_records=str(atlas_run_dir / "missing_candidate_bridge_records.jsonl"),
    )
    provider = _FakeProvider([_atlas_guided_payload()])
    with pytest.raises(Exception):
        run(args, provider=provider)
    assert provider.calls == []


def test_atlas_guided_required_jsonl_is_strict_before_provider_calls(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    source_dir.joinpath("conversations.json").write_text(
        json.dumps([_conversation_from_messages([("user", "hello"), ("assistant", "hi")], "conv-atlas-bad-jsonl")]),
        encoding="utf-8",
    )
    run_dir = tmp_path / "run"
    atlas_run_dir = tmp_path / "atlas_run"
    _write_atlas_guided_input_artifacts(atlas_run_dir, conversation_id="conv-atlas-bad-jsonl")
    (
        atlas_run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["atlas_thread_candidates"]
    ).write_text('{"truncated":\n', encoding="utf-8")
    provider = _FakeProvider([_atlas_guided_payload(signal_status="accepted")])

    with pytest.raises(FatalRemoteError, match="atlas thread candidate lookup has invalid JSONL row"):
        run(
            _base_args(
                source_dir,
                run_dir,
                atlas_guided=True,
                atlas_run_dir=str(atlas_run_dir),
            ),
            provider=provider,
        )

    assert provider.calls == []


def test_atlas_guided_thread_index_non_object_row_is_strict_before_provider_calls(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    source_dir.joinpath("conversations.json").write_text(
        json.dumps([_conversation_from_messages([("user", "hello"), ("assistant", "hi")], "conv-atlas-bad-thread-index")]),
        encoding="utf-8",
    )
    run_dir = tmp_path / "run"
    atlas_run_dir = tmp_path / "atlas_run"
    _write_atlas_guided_input_artifacts(atlas_run_dir, conversation_id="conv-atlas-bad-thread-index")
    (atlas_run_dir / "thread_index.jsonl").write_text("[]\n", encoding="utf-8")
    provider = _FakeProvider([_atlas_guided_payload(signal_status="accepted")])

    with pytest.raises(FatalRemoteError, match="Optional JSONL artifact row .* must be a JSON object"):
        run(
            _base_args(
                source_dir,
                run_dir,
                atlas_guided=True,
                atlas_run_dir=str(atlas_run_dir),
            ),
            provider=provider,
        )

    assert provider.calls == []


@pytest.mark.parametrize(
    "base_url",
    [
        "http://localhost:8080/v1",
        "http://example.test:8080/v1",
    ],
)
def test_atlas_guided_localai_base_url_is_strict_before_provider_calls(tmp_path, base_url):
    source_dir = tmp_path / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    source_dir.joinpath("conversations.json").write_text(
        json.dumps([_conversation_from_messages([("user", "hello"), ("assistant", "hi")], "conv-atlas-url-guard")]),
        encoding="utf-8",
    )
    run_dir = tmp_path / "run"
    atlas_run_dir = tmp_path / "atlas_run"
    _write_atlas_guided_input_artifacts(atlas_run_dir, conversation_id="conv-atlas-url-guard")
    provider = _FakeProvider([_atlas_guided_payload(signal_status="accepted")])

    with pytest.raises(FatalRemoteError, match="Atlas-guided LocalAI base URL must target snow-white-iii"):
        run(
            _base_args(
                source_dir,
                run_dir,
                atlas_guided=True,
                atlas_run_dir=str(atlas_run_dir),
                localai_base_url=base_url,
            ),
            provider=provider,
        )

    assert provider.calls == []


def test_non_atlas_mode_retains_legacy_segment_extractions_output(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    source_dir.joinpath("conversations.json").write_text(
        json.dumps([_conversation_from_messages([("user", "hello"), ("assistant", "hi")], "conv-legacy")]),
        encoding="utf-8",
    )
    run_dir = tmp_path / "run"
    args = _base_args(source_dir, run_dir)
    run(args, provider=_FakeProvider(['{"summary":"ok","items":[]}']))
    assert (run_dir / "segment_extractions.jsonl").exists()
    assert not (run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["extraction_records"]).exists()


def test_parse_args_atlas_guided_default_run_dir_uses_deterministic_child(monkeypatch):
    monkeypatch.delenv("LOCALAI_THREAD_SIGNAL_RUN_DIR", raising=False)
    monkeypatch.delenv("CHATGPT_ATLAS_RUN_DIR", raising=False)
    monkeypatch.delenv("LOCALAI_THREAD_SIGNAL_ATLAS_GUIDED", raising=False)
    atlas_run_dir = "/tmp/atlas runs/WP-05 candidate set"

    args = parse_args(["--atlas-guided", "--atlas-run-dir", atlas_run_dir])
    parsed_run_dir = Path(args.run_dir)

    assert parsed_run_dir.parent == Path(DEFAULT_ATLAS_GUIDED_RUN_DIR)
    assert parsed_run_dir != Path(DEFAULT_ATLAS_GUIDED_RUN_DIR)
    assert parsed_run_dir.name

    explicit = parse_args(
        [
            "--atlas-guided",
            "--atlas-run-dir",
            atlas_run_dir,
            "--run-dir",
            "/tmp/custom-atlas-guided-run",
        ]
    )
    assert explicit.run_dir == "/tmp/custom-atlas-guided-run"


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
    args = _base_args(
        source_dir,
        run_dir,
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
    args = _base_args(
        source_dir,
        run_dir,
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


class _FailThenSucceedProvider:
    def __init__(self, fail_count: int) -> None:
        self.fail_count = fail_count
        self.calls = 0

    def classify_segment(self, *, prompt_messages: list[dict[str, str]]) -> str:
        self.calls += 1
        if self.calls <= self.fail_count:
            raise RuntimeError("connection reset by peer")
        return '{"summary":"ok","items":[]}'


def test_malformed_source_file_is_checkpointed_and_run_continues(tmp_path):
    source_dir = tmp_path / "source"
    good = source_dir / "a" / "conversations.json"
    bad = source_dir / "b" / "conversations.json"
    good.parent.mkdir(parents=True, exist_ok=True)
    bad.parent.mkdir(parents=True, exist_ok=True)
    good.write_text(
        json.dumps([_conversation_from_messages([("user", "hello"), ("assistant", "hi")], "conv-good")]),
        encoding="utf-8",
    )
    bad.write_text('{"truncated": ', encoding="utf-8")
    run_dir = tmp_path / "run"
    args = _base_args(source_dir, run_dir)
    rc = run(args, provider=_FakeProvider(['{"summary":"ok","items":[]}']))
    assert rc == 0
    source_errors = _read_jsonl(run_dir / "source_file_errors.jsonl")
    assert len(source_errors) == 1
    assert source_errors[0]["error_code"] == "source_json_decode_error"
    source_ckpt = _read_jsonl(run_dir / "source_checkpoint.jsonl")
    statuses = {row["status"] for row in source_ckpt}
    assert "loaded" in statuses
    assert "error" in statuses
    progress = json.loads((run_dir / "progress.json").read_text(encoding="utf-8"))
    assert progress["source_file_error_count"] == 1
    assert progress["classified_segments"] == 1


def test_retry_errors_retries_prior_error_without_reprocessing_classified(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "conversations.json").write_text(
        json.dumps([_conversation_from_messages([("user", "u"), ("assistant", "a")], "conv-r")]),
        encoding="utf-8",
    )
    run_dir = tmp_path / "run"
    # First run: force a durable checkpointed provider error.
    run(_base_args(source_dir, run_dir, provider_max_attempts=1), provider=_FailThenSucceedProvider(fail_count=1))
    first_ckpt = _read_jsonl(run_dir / "segment_checkpoint.jsonl")
    assert first_ckpt and first_ckpt[-1]["status"] == "error"

    # Second run: retry-errors should re-attempt prior error and classify it.
    provider = _FailThenSucceedProvider(fail_count=0)
    run(_base_args(source_dir, run_dir, retry_errors=True, provider_max_attempts=2), provider=provider)
    checkpoints = _read_jsonl(run_dir / "segment_checkpoint.jsonl")
    assert checkpoints[-1]["status"] == "classified"
    progress = json.loads((run_dir / "progress.json").read_text(encoding="utf-8"))
    assert progress["processed_segments"] == 1
    assert progress["classified_segments"] == 1
    assert provider.calls == 1


def test_retry_errors_does_not_duplicate_prior_classified_rows(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "conversations.json").write_text(
        json.dumps([_conversation_from_messages([("user", "hello"), ("assistant", "hi")], "conv-classified")]),
        encoding="utf-8",
    )
    run_dir = tmp_path / "run"
    args = _base_args(source_dir, run_dir)
    run(args, provider=_FakeProvider(['{"summary":"ok","items":[]}']))
    first = _read_jsonl(run_dir / "segment_extractions.jsonl")
    run(_base_args(source_dir, run_dir, retry_errors=True), provider=_FakeProvider(['{"summary":"ok","items":[]}']))
    second = _read_jsonl(run_dir / "segment_extractions.jsonl")
    keys = [row["segment_key"] for row in second]
    assert len(first) == 1
    assert len(second) == 1
    assert len(keys) == len(set(keys))


def test_provider_retry_succeeds_after_transient_failure(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "conversations.json").write_text(
        json.dumps([_conversation_from_messages([("user", "hello"), ("assistant", "hi")], "conv-transient")]),
        encoding="utf-8",
    )
    run_dir = tmp_path / "run"
    provider = _FailThenSucceedProvider(fail_count=1)
    args = _base_args(source_dir, run_dir, provider_max_attempts=2)
    run(args, provider=provider)
    checkpoints = _read_jsonl(run_dir / "segment_checkpoint.jsonl")
    assert checkpoints[0]["status"] == "classified"
    progress = json.loads((run_dir / "progress.json").read_text(encoding="utf-8"))
    assert progress["error_segments"] == 0
    assert progress["classified_segments"] == 1
