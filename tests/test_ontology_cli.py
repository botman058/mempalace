import argparse
import json
from unittest.mock import patch

import pytest

from mempalace.cli import cmd_ontology_chatgpt_signals, main
from mempalace.ontology_run import generate_run_id, initialize_run_shell, validate_run_id


EXPECTED_PHASE_ORDER = [
    "pass1_open",
    "candidate_clusters",
    "canonical_candidates",
    "route_candidates",
    "route_pass2",
    "route_verify",
    "apply_copies",
]


def test_generate_run_id_shape():
    run_id = generate_run_id()
    assert run_id.endswith("_chatgpt_signal_ontology")
    assert "T" in run_id


def test_validate_run_id_rejects_invalid():
    with pytest.raises(ValueError):
        validate_run_id("bad/id")


def test_initialize_run_shell_refuses_extreme_ssd():
    with pytest.raises(ValueError, match="forbidden"):
        initialize_run_shell(
            run_dir="/media/u0/Extreme SSD/ontology",
            run_id=None,
            source_wing="chatgpt_signals",
            dry_run=True,
        )


def test_cmd_ontology_chatgpt_signals_dry_run_does_not_materialize(capsys):
    args = argparse.Namespace(
        run_dir=None,
        run_id=None,
        source_wing="chatgpt_signals",
        dry_run=True,
    )
    with patch("mempalace.cli.materialize_run_shell") as mock_materialize:
        cmd_ontology_chatgpt_signals(args)
    out = capsys.readouterr().out
    assert "Dry run only" in out
    mock_materialize.assert_not_called()


def test_cmd_ontology_chatgpt_signals_dry_run_writes_no_run_directory(tmp_path, capsys):
    run_root = tmp_path / "ontology_runs"
    args = argparse.Namespace(
        run_dir=str(run_root),
        run_id="dry_run_1",
        source_wing="chatgpt_signals",
        dry_run=True,
    )
    cmd_ontology_chatgpt_signals(args)
    out = capsys.readouterr().out
    assert "Dry run only" in out
    assert not (run_root / "dry_run_1").exists()


def test_cmd_ontology_chatgpt_signals_materializes_progress_and_artifacts(tmp_path):
    run_root = tmp_path / "ontology_runs"
    args = argparse.Namespace(
        run_dir=str(run_root),
        run_id="custom_run_1",
        source_wing="chatgpt_signals",
        dry_run=False,
    )
    cmd_ontology_chatgpt_signals(args)
    run_dir = run_root / "custom_run_1"
    assert run_dir.exists()
    assert (run_dir / "run_metadata.json").exists()
    assert (run_dir / "progress.json").exists()
    assert (run_dir / "artifacts_index.json").exists()
    append_ready_expected = [
        "pass1_open.jsonl",
        "candidate_clusters.jsonl",
        "canonical_candidates.jsonl",
        "route_candidates.jsonl",
        "route_pass2.jsonl",
        "route_verify.jsonl",
        "apply_copies.jsonl",
        "accepted_routes.jsonl",
        "unresolved.jsonl",
        "resume_markers.jsonl",
    ]
    for relative in append_ready_expected:
        assert (run_dir / relative).exists()

    progress = json.loads((run_dir / "progress.json").read_text(encoding="utf-8"))
    assert progress["schema_name"] == "ontology.progress"
    assert progress["status"] == "pending"
    assert progress["phase_order"] == EXPECTED_PHASE_ORDER
    assert set(progress["phase_attempts"]) == set(EXPECTED_PHASE_ORDER)
    assert progress["phase_attempts"]["pass1_open"] == 0

    index = json.loads((run_dir / "artifacts_index.json").read_text(encoding="utf-8"))
    assert index["schema_name"] == "ontology.artifact_index"
    artifacts_by_key = {entry["artifact_key"]: entry for entry in index["artifacts"]}
    assert "progress" in artifacts_by_key
    assert "resume_markers" in artifacts_by_key

    for phase in EXPECTED_PHASE_ORDER:
        entry = artifacts_by_key[phase]
        assert entry["schema_name"] == "ontology.phase_record"
        assert entry["artifact_kind"] == "phase_records"
        assert entry["phase"] == phase
        assert entry["content_type"] == "application/jsonl"
        assert entry["append_only"] is True
        assert entry["dashboard_safe"] is False
        assert entry["privacy_level"] == "restricted"

    convergence = artifacts_by_key["convergence_report"]
    assert convergence["schema_name"] == "ontology.convergence_report"
    assert convergence["artifact_kind"] == "summary"
    assert convergence["content_type"] == "application/json"
    assert convergence["append_only"] is False
    assert convergence["records"] == 0
    assert convergence["bytes"] == 0

    apply_ready = artifacts_by_key["apply_ready_manifest"]
    assert apply_ready["schema_name"] == "ontology.apply_ready_manifest"
    assert apply_ready["artifact_kind"] == "summary"
    assert apply_ready["content_type"] == "application/json"
    assert apply_ready["append_only"] is False
    assert apply_ready["records"] == 0
    assert apply_ready["bytes"] == 0

    marker_lines = [
        line
        for line in (run_dir / "resume_markers.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(marker_lines) == 1
    marker = json.loads(marker_lines[0])
    assert marker["event"] == "initialized"
    assert marker["sequence"] == 1

    assert not list(run_dir.glob(".progress.json.tmp.*"))
    assert not list(run_dir.glob(".artifacts_index.json.tmp.*"))


def test_cmd_ontology_chatgpt_signals_rerun_appends_resume_marker(tmp_path):
    run_root = tmp_path / "ontology_runs"
    args = argparse.Namespace(
        run_dir=str(run_root),
        run_id="custom_run_resume",
        source_wing="chatgpt_signals",
        dry_run=False,
    )
    cmd_ontology_chatgpt_signals(args)
    cmd_ontology_chatgpt_signals(args)
    run_dir = run_root / "custom_run_resume"

    marker_lines = [
        line
        for line in (run_dir / "resume_markers.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(marker_lines) == 2
    first = json.loads(marker_lines[0])
    second = json.loads(marker_lines[1])
    assert first["event"] == "initialized"
    assert second["event"] == "resumed"
    assert second["sequence"] == 2


def test_cmd_ontology_chatgpt_signals_resume_updates_summary_artifact_records(tmp_path):
    run_root = tmp_path / "ontology_runs"
    args = argparse.Namespace(
        run_dir=str(run_root),
        run_id="custom_run_summary_records",
        source_wing="chatgpt_signals",
        dry_run=False,
    )
    cmd_ontology_chatgpt_signals(args)
    run_dir = run_root / "custom_run_summary_records"

    (run_dir / "convergence_report.json").write_text(
        json.dumps({"summary": {"accepted": 3, "unresolved": 1}}, indent=2) + "\n",
        encoding="utf-8",
    )

    cmd_ontology_chatgpt_signals(args)

    index = json.loads((run_dir / "artifacts_index.json").read_text(encoding="utf-8"))
    artifacts_by_key = {entry["artifact_key"]: entry for entry in index["artifacts"]}
    convergence = artifacts_by_key["convergence_report"]
    assert convergence["records"] == 1
    assert convergence["bytes"] > 0


def test_cmd_ontology_chatgpt_signals_rerun_with_different_source_wing_fails(tmp_path, capsys):
    run_root = tmp_path / "ontology_runs"
    first = argparse.Namespace(
        run_dir=str(run_root),
        run_id="custom_run_mismatch",
        source_wing="chatgpt_signals",
        dry_run=False,
    )
    second = argparse.Namespace(
        run_dir=str(run_root),
        run_id="custom_run_mismatch",
        source_wing="other_wing",
        dry_run=False,
    )
    cmd_ontology_chatgpt_signals(first)
    with pytest.raises(SystemExit) as excinfo:
        cmd_ontology_chatgpt_signals(second)
    assert excinfo.value.code == 1
    err = capsys.readouterr().err
    assert "source_wing mismatch" in err
    assert "existing='chatgpt_signals'" in err
    assert "requested='other_wing'" in err

    run_dir = run_root / "custom_run_mismatch"
    marker_lines = [
        line
        for line in (run_dir / "resume_markers.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(marker_lines) == 1


def test_cmd_ontology_chatgpt_signals_no_run_flag_only_initializes(tmp_path):
    run_root = tmp_path / "ontology_runs"
    args = argparse.Namespace(
        run_dir=str(run_root),
        run_id="run_without_execute",
        source_wing="chatgpt_signals",
        dry_run=False,
        run=False,
    )
    with patch("mempalace.cli.run_chatgpt_signal_ontology") as mock_run:
        cmd_ontology_chatgpt_signals(args)
    mock_run.assert_not_called()
    assert (run_root / "run_without_execute" / "progress.json").exists()


def test_cmd_ontology_chatgpt_signals_run_executes_runner(tmp_path):
    run_root = tmp_path / "ontology_runs"
    args = argparse.Namespace(
        run_dir=str(run_root),
        run_id="run_execute",
        source_wing="chatgpt_signals",
        dry_run=False,
        run=True,
        localai_base_url="http://snow-white-iii:8080/v1",
        localai_token=None,
        localai_token_file=None,
        localai_model="qwen3-vl-8b-instruct",
        mcp_url="http://100.112.179.49:8765",
        mcp_token=None,
        mcp_token_file=None,
        page_limit=10,
        apply_copies=False,
    )
    with patch("mempalace.cli.run_chatgpt_signal_ontology") as mock_run:
        cmd_ontology_chatgpt_signals(args)
    mock_run.assert_called_once()


def test_cmd_ontology_chatgpt_signals_run_refuses_openai_base_url(tmp_path, capsys):
    run_root = tmp_path / "ontology_runs"
    args = argparse.Namespace(
        run_dir=str(run_root),
        run_id="run_bad_localai",
        source_wing="chatgpt_signals",
        dry_run=False,
        run=True,
        localai_base_url="https://api.openai.com/v1",
        localai_token=None,
        localai_token_file=None,
        localai_model="qwen3-vl-8b-instruct",
        mcp_url="http://100.112.179.49:8765",
        mcp_token=None,
        mcp_token_file=None,
        page_limit=10,
        apply_copies=False,
    )
    with pytest.raises(SystemExit) as excinfo:
        cmd_ontology_chatgpt_signals(args)
    assert excinfo.value.code == 1
    err = capsys.readouterr().err
    assert "api.openai.com" in err


def test_cmd_ontology_chatgpt_signals_run_refuses_non_local_mcp_url(tmp_path, capsys):
    run_root = tmp_path / "ontology_runs"
    args = argparse.Namespace(
        run_dir=str(run_root),
        run_id="run_bad_mcp",
        source_wing="chatgpt_signals",
        dry_run=False,
        run=True,
        localai_base_url="http://snow-white-iii:8080/v1",
        localai_token=None,
        localai_token_file=None,
        localai_model="qwen3-vl-8b-instruct",
        mcp_url="https://mempalace.example.com/mcp",
        mcp_token=None,
        mcp_token_file=None,
        page_limit=10,
        apply_copies=False,
    )
    with pytest.raises(SystemExit) as excinfo:
        cmd_ontology_chatgpt_signals(args)
    assert excinfo.value.code == 1
    err = capsys.readouterr().err
    assert "non-local MCP host" in err


def test_main_ontology_dispatches():
    with (
        patch("sys.argv", ["mempalace", "ontology", "chatgpt-signals"]),
        patch("mempalace.cli.cmd_ontology_chatgpt_signals") as mock_cmd,
    ):
        main()
        mock_cmd.assert_called_once()


def test_main_ontology_chatgpt_signals_uses_ontology_env_defaults(monkeypatch):
    monkeypatch.setenv("MEMPALACE_ONTOLOGY_RUN_ROOT", "/tmp/ontology-runs")
    monkeypatch.setenv("MEMPALACE_ONTOLOGY_SOURCE_WING", "chatgpt_signals_env")
    with (
        patch("sys.argv", ["mempalace", "ontology", "chatgpt-signals"]),
        patch("mempalace.cli.cmd_ontology_chatgpt_signals") as mock_cmd,
    ):
        main()
    args = mock_cmd.call_args.args[0]
    assert args.run_dir == "/tmp/ontology-runs"
    assert args.source_wing == "chatgpt_signals_env"


def test_main_ontology_without_subcommand_prints_help(capsys):
    with patch("sys.argv", ["mempalace", "ontology"]):
        main()
    out = capsys.readouterr().out
    assert "ontology" in out.lower()
