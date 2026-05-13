from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from scripts.localai_chatgpt_thread_signals import run
from mempalace import chatgpt_atlas_guided_contract as guided_contract


def _conversation_from_messages(
    messages: list[tuple[str, str]], conversation_id: str = "conv-1"
) -> dict:
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


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _base_args(source_dir: Path, run_dir: Path, atlas_run_dir: Path, **overrides) -> SimpleNamespace:
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
        "atlas_guided": True,
        "atlas_run_dir": str(atlas_run_dir),
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


def _atlas_artifact_rows(conversation_id: str) -> tuple[dict, dict]:
    atlas_run_id = "atlas_full2_20260512T0412Z_2fc8ac5"
    thread_id = f"chatgpt:{conversation_id}"
    return (
        guided_contract.build_thread_candidate_record(
            run_id="run-id-placeholder",
            atlas_run_id=atlas_run_id,
            thread_id=thread_id,
            lookup_status="mapped",
            candidate_ids=["cand_devops__postgres_latency"],
            candidate_keys=["devops:postgres_latency"],
            cluster_ids=["cluster-001"],
            primary_candidate_id="cand_devops__postgres_latency",
            primary_candidate_key="devops:postgres_latency",
            reason_codes=["candidate_cluster_member"],
            source_thread_ref="atlas_thread_candidates.jsonl#1",
        ),
        guided_contract.build_candidate_bridge_record(
            run_id="run-id-placeholder",
            atlas_run_id=atlas_run_id,
            candidate_id="cand_devops__postgres_latency",
            candidate_key="devops:postgres_latency",
            bridge_status="candidate",
            atlas_cluster_id="cluster-001",
            atlas_cluster_status="candidate",
            topic_label="Ops readiness",
            label="Postgres latency",
            definition="Signals related to postgres latency and ops stability.",
            thread_ids=[thread_id],
            top_terms=[{"term": "postgres", "count": 6}],
            evidence_titles=["thread export"],
            representative_thread_ids=[thread_id],
            representative_excerpts=["Latency spike observed."],
            mixed_reasons=[],
        ),
    )


def _write_atlas_guided_artifacts(atlas_run_dir: Path, conversation_id: str) -> None:
    lookup_row, bridge_row = _atlas_artifact_rows(conversation_id=conversation_id)
    _write_jsonl(
        atlas_run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["atlas_thread_candidates"],
        [lookup_row],
    )
    _write_jsonl(
        atlas_run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["candidate_bridge_records"],
        [bridge_row],
    )


def _atlas_payload(
    signals: list[dict[str, object]] | None = None,
    *,
    error_code: str | None = None,
) -> str:
    if error_code is not None:
        return error_code
    return json.dumps(
        {
            "signals": (
                signals
                if signals is not None
                else [
                    {
                        "signal_status": "accepted",
                        "signal_type": "technical_note",
                        "title": "Track query latency",
                        "summary": "Latency tuning work is still in progress for this segment.",
                        "source_excerpt": "Latency tuning work is still in progress.",
                        "confidence": 0.91,
                        "candidate_id": "cand_devops__postgres_latency",
                        "candidate_key": "devops:postgres_latency",
                        "canonical_wing": "devops",
                        "canonical_room": "postgres_latency",
                    }
                ]
            )
        }
    )


def _atlas_signal(
    *,
    signal_status: str = "accepted",
    signal_type: str = "technical_note",
    title: str = "Track query latency",
    summary: str = "Latency tuning work is still in progress for this segment.",
    source_excerpt: str = "Latency tuning work is still in progress.",
    candidate_id: str | None = "cand_devops__postgres_latency",
    candidate_key: str | None = "devops:postgres_latency",
    canonical_wing: str | None = "devops",
    canonical_room: str | None = "postgres_latency",
    confidence: float = 0.91,
) -> dict[str, object]:
    if signal_status == "null_signal":
        return {
            "signal_status": "null_signal",
            "signal_type": "null_signal",
            "title": title,
            "summary": summary,
            "source_excerpt": source_excerpt,
            "confidence": confidence,
            "candidate_id": None,
            "candidate_key": None,
            "canonical_wing": None,
            "canonical_room": None,
        }
    return {
        "signal_status": signal_status,
        "signal_type": signal_type,
        "title": title,
        "summary": summary,
        "source_excerpt": source_excerpt,
        "confidence": confidence,
        "candidate_id": candidate_id,
        "candidate_key": candidate_key,
        "canonical_wing": canonical_wing,
        "canonical_room": canonical_room,
    }


class _FakeProvider:
    def __init__(self, responses: list[str | Exception]) -> None:
        self.responses = list(responses)
        self.calls: list[str] = []

    def classify_segment(self, *, prompt_messages: list[dict[str, str]]) -> str:
        if not self.responses:
            raise RuntimeError("No more scripted provider responses")
        self.calls.append(prompt_messages[-1]["content"])
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class _FakeMCPCaller:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def call_tool(self, *, tool_name: str, arguments: dict, timeout: float) -> dict:
        self.calls.append({"tool_name": tool_name, "arguments": arguments, "timeout": timeout})
        return {"success": True, "noop": False}


def _run_atlas_with_provider(
    *,
    tmp_path: Path,
    messages: list[tuple[str, str]],
    conversation_id: str,
    provider: _FakeProvider,
    run_id: str = "run-id-placeholder",
    mcp: _FakeMCPCaller | None = None,
) -> tuple[Path, Path]:
    source_dir = tmp_path / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    source_dir.joinpath("conversations.json").write_text(
        json.dumps([_conversation_from_messages(messages, conversation_id)]),
        encoding="utf-8",
    )

    run_dir = tmp_path / run_id
    atlas_run_dir = tmp_path / "atlas_run"
    _write_atlas_guided_artifacts(atlas_run_dir=atlas_run_dir, conversation_id=conversation_id)

    args = _base_args(
        source_dir=source_dir,
        run_dir=run_dir,
        atlas_run_dir=atlas_run_dir,
    )
    run(args, provider=provider, mcp_caller=mcp)
    return run_dir, atlas_run_dir


def _assert_reconciliation_rows_valid(rows: list[dict]) -> None:
    for row in rows:
        guided_contract.validate_row(guided_contract.RECONCILIATION_RECORD_SCHEMA, row)


def test_atlas_reconciliation_deduplicates_overlapping_accepted_signals(tmp_path):
    messages = [
        ("user", "The database shows latency spikes in the request path."),
        ("assistant", "Understood, we should tune indexes."),
    ]
    duplicate = _atlas_signal(
        signal_type="technical_note",
        title="Track query latency",
        summary="Latency tuning work is still in progress.",
        source_excerpt="Latency tuning work is still in progress.",
    )
    provider = _FakeProvider(
        [
            _atlas_payload(
                signals=[duplicate, duplicate],
            ),
        ]
    )

    run_dir, _ = _run_atlas_with_provider(
        tmp_path=tmp_path,
        messages=messages,
        conversation_id="conv-atlas-recon-dedupe",
        provider=provider,
    )
    rows = _read_jsonl(
        run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["reconciled_signals"]
    )
    _assert_reconciliation_rows_valid(rows)

    accepted_rows = [row for row in rows if row["reconciliation_status"] == "accepted"]
    assert len(accepted_rows) == 1
    accepted = accepted_rows[0]
    assert accepted["candidate_id"] == "cand_devops__postgres_latency"
    assert accepted["candidate_key"] == "devops:postgres_latency"
    assert accepted["canonical_wing"] == "devops"
    assert accepted["canonical_room"] == "postgres_latency"
    assert accepted["reconciliation_status"] == "accepted"
    assert accepted["source_extraction_ids"]
    assert len(accepted["source_extraction_ids"]) >= 2 or any(
        row["reconciliation_status"] == "duplicate" for row in rows
    )

    if len(accepted["source_extraction_ids"]) >= 2:
        assert len({row.get("reconciliation_status") for row in rows if row["reconciliation_status"] == "accepted"}) == 1


def test_atlas_reconciliation_keeps_distinct_signals_for_same_candidate(tmp_path):
    messages = [
        ("user", "We tuned an index and also need to rewrite the migration script."),
        ("assistant", "Let's track both."),
    ]
    provider = _FakeProvider(
        [
            _atlas_payload(
                signals=[
                    _atlas_signal(
                        signal_type="task",
                        title="Track query latency",
                        summary="Index tuning is in progress.",
                        source_excerpt="Index tuning is in progress.",
                    ),
                    _atlas_signal(
                        signal_type="problem",
                        title="Rewrite migration script",
                        summary="The migration script must be rewritten.",
                        source_excerpt="Rewrite the migration script.",
                    ),
                ]
            )
        ]
    )
    run_dir, _ = _run_atlas_with_provider(
        tmp_path=tmp_path,
        messages=messages,
        conversation_id="conv-atlas-recon-distinct",
        provider=provider,
    )
    rows = _read_jsonl(
        run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["reconciled_signals"]
    )
    _assert_reconciliation_rows_valid(rows)

    accepted_rows = [row for row in rows if row["reconciliation_status"] == "accepted"]
    assert len(accepted_rows) == 2
    assert len({row["dedupe_key"] for row in accepted_rows}) == 2
    assert accepted_rows[0]["title"] != accepted_rows[1]["title"]
    assert accepted_rows[0]["candidate_id"] == accepted_rows[1]["candidate_id"] == "cand_devops__postgres_latency"
    assert accepted_rows[0]["candidate_key"] == accepted_rows[1]["candidate_key"] == "devops:postgres_latency"


def test_atlas_reconciliation_preserves_candidate_key_and_wing_room(tmp_path):
    messages = [
        ("user", "Latency regression requires a plan for query throughput."),
        ("assistant", "We'll coordinate later."),
    ]
    provider = _FakeProvider(
        [
            _atlas_payload(
                signals=[
                    _atlas_signal(
                        signal_type="technical_note",
                        title="Query throughput plan",
                        summary="Plan for query throughput in the next sprint.",
                        source_excerpt="Plan for query throughput in the next sprint.",
                        canonical_wing="devops",
                        canonical_room="postgres_latency",
                        candidate_id="cand_devops__postgres_latency",
                        candidate_key="devops:postgres_latency",
                    )
                ]
            )
        ]
    )
    run_dir, _ = _run_atlas_with_provider(
        tmp_path=tmp_path,
        messages=messages,
        conversation_id="conv-atlas-recon-prov",
        provider=provider,
    )
    rows = _read_jsonl(
        run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["reconciled_signals"]
    )
    _assert_reconciliation_rows_valid(rows)
    assert len(rows) == 1

    row = rows[0]
    assert row["candidate_id"] == "cand_devops__postgres_latency"
    assert row["candidate_key"] == "devops:postgres_latency"
    assert row["canonical_wing"] == "devops"
    assert row["canonical_room"] == "postgres_latency"
    provenance = row.get("provenance", {})
    assert isinstance(provenance, dict)
    assert provenance.get("candidate_id") == "cand_devops__postgres_latency" or provenance.get(
        "atlas_candidate_ids"
    ) == ["cand_devops__postgres_latency"]


def test_atlas_reconciliation_ignores_null_and_invalid_provider_error_extraction_rows(tmp_path):
    conversation_id = "conv-atlas-recon-filter"
    messages = [
        ("user", "x" * 11000),
        ("assistant", "ack"),
        ("user", "y" * 11000),
        ("assistant", "done"),
    ]
    provider = _FakeProvider(
        [
            _atlas_payload(
                signals=[
                    _atlas_signal(
                        signal_type="task",
                        title="Accepted signal",
                        summary="A durable atlas-grounded task exists.",
                        source_excerpt="A durable atlas-grounded task exists.",
                    )
                ]
            ),
            _atlas_payload(signals=[_atlas_signal(signal_status="null_signal")]),
            _atlas_payload(error_code="not json"),
            Exception("provider failed"),
        ]
    )
    run_dir, _ = _run_atlas_with_provider(
        tmp_path=tmp_path,
        messages=messages,
        conversation_id=conversation_id,
        provider=provider,
    )

    extraction_rows = _read_jsonl(
        run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["extraction_records"]
    )
    reconciled_rows = _read_jsonl(
        run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["reconciled_signals"]
    )

    accepted_ids = {
        row["extraction_id"]
        for row in extraction_rows
        if row.get("extraction_status") == "accepted"
    }
    disallowed_ids = {
        row["extraction_id"]
        for row in extraction_rows
        if row.get("extraction_status") in {"null_signal", "invalid_output", "provider_error"}
    }
    reconciled_ids = {
        source_id
        for row in reconciled_rows
        for source_id in row.get("source_extraction_ids", [])
    }

    _assert_reconciliation_rows_valid(reconciled_rows)
    assert reconciled_ids.issubset(accepted_ids)
    assert not reconciled_ids.intersection(disallowed_ids)


def test_atlas_reconciliation_is_deterministic_on_rerun(tmp_path):
    messages = [
        ("user", "Index tuning remains unstable during high write load."),
        ("assistant", "Let's keep monitoring."),
    ]
    payload = _atlas_payload(
        signals=[
            _atlas_signal(
                title="Track write load tuning",
                summary="Index tuning remains unstable during high write load.",
                source_excerpt="Index tuning remains unstable during high write load.",
            ),
            _atlas_signal(
                title="Track write load tuning",
                summary="Index tuning remains unstable during high write load.",
                source_excerpt="Index tuning remains unstable during high write load.",
            ),
        ]
    )
    provider = _FakeProvider([payload])
    run_dir, _ = _run_atlas_with_provider(
        tmp_path=tmp_path,
        messages=messages,
        conversation_id="conv-atlas-recon-idem",
        provider=provider,
    )

    snapshot = (
        run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["reconciled_signals"]
    ).read_text(encoding="utf-8")
    second_provider = _FakeProvider([payload])
    run_dir_2, _ = _run_atlas_with_provider(
        tmp_path=tmp_path,
        messages=messages,
        conversation_id="conv-atlas-recon-idem",
        provider=second_provider,
    )
    snapshot_2 = (
        run_dir_2
        / guided_contract.CANONICAL_ARTIFACT_PATHS["reconciled_signals"]
    ).read_text(encoding="utf-8")

    assert second_provider.calls == []
    assert snapshot == snapshot_2


def test_atlas_runner_materializes_reconciled_outputs_and_updates_counts_without_publish(tmp_path):
    messages = [
        ("user", "Latency dropped after we added a composite index to the main query."),
        ("assistant", "Great update."),
    ]
    provider = _FakeProvider(
        [_atlas_payload(signals=[_atlas_signal(title="Composite index rollout", summary="Composite index rollout.")])]
    )
    mcp = _FakeMCPCaller()
    run_dir, _ = _run_atlas_with_provider(
        tmp_path=tmp_path,
        messages=messages,
        conversation_id="conv-atlas-recon-artifacts",
        provider=provider,
        mcp=mcp,
    )

    reconciled_rows = _read_jsonl(
        run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["reconciled_signals"]
    )
    progress = json.loads((run_dir / "progress.json").read_text(encoding="utf-8"))
    artifacts = json.loads(
        (run_dir / guided_contract.CANONICAL_ARTIFACT_PATHS["artifacts_index"]).read_text(
            encoding="utf-8"
        )
    )

    assert mcp.calls == []
    assert progress["no_publish"] is True
    assert progress["publish_enabled"] is False
    assert reconciled_rows
    assert progress["counts"]["reconciled_signals"] == len(reconciled_rows)
    by_key = {row["artifact_key"]: row for row in artifacts["artifacts"]}
    assert by_key["reconciled_signals"]["count"] == len(reconciled_rows)
