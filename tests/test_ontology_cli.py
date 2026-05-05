import argparse
import json
from unittest.mock import patch

import pytest

from mempalace.cli import cmd_ontology_chatgpt_signals, main
from mempalace.ontology_run import generate_run_id, initialize_run_shell, validate_run_id


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
    assert (run_dir / "pass1_open.jsonl").exists()
    assert (run_dir / "resume_markers.jsonl").exists()

    progress = json.loads((run_dir / "progress.json").read_text(encoding="utf-8"))
    assert progress["schema_name"] == "ontology.progress"
    assert progress["status"] == "pending"
    assert progress["phase_attempts"]["pass1_open"] == 0

    index = json.loads((run_dir / "artifacts_index.json").read_text(encoding="utf-8"))
    assert index["schema_name"] == "ontology.artifact_index"
    keys = {entry["artifact_key"] for entry in index["artifacts"]}
    assert "progress" in keys
    assert "pass1_open" in keys
    assert "resume_markers" in keys

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


def test_main_ontology_dispatches():
    with (
        patch("sys.argv", ["mempalace", "ontology", "chatgpt-signals"]),
        patch("mempalace.cli.cmd_ontology_chatgpt_signals") as mock_cmd,
    ):
        main()
        mock_cmd.assert_called_once()


def test_main_ontology_without_subcommand_prints_help(capsys):
    with patch("sys.argv", ["mempalace", "ontology"]):
        main()
    out = capsys.readouterr().out
    assert "ontology" in out.lower()
