import argparse
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


def test_cmd_ontology_chatgpt_signals_materializes(tmp_path):
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
