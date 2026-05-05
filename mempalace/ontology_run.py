from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_ONTOLOGY_RUN_ROOT = Path("/media/u0/OneDrive_Backup/mempalace/data/ontology")
FORBIDDEN_RUN_ROOT = Path("/media/u0/Extreme SSD")
_RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


@dataclass(frozen=True)
class OntologyRunShell:
    run_id: str
    run_root: Path
    run_dir: Path
    dry_run: bool
    source_wing: str


def generate_run_id(now: datetime | None = None) -> str:
    dt = now or datetime.now(timezone.utc)
    stamp = dt.strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}_chatgpt_signal_ontology"


def validate_run_id(run_id: str) -> str:
    candidate = run_id.strip()
    if not candidate:
        raise ValueError("run_id must not be empty")
    if not _RUN_ID_RE.match(candidate):
        raise ValueError("run_id must contain only letters, numbers, '_' or '-'")
    return candidate


def resolve_run_root(run_dir: str | None) -> Path:
    root = Path(run_dir).expanduser() if run_dir else DEFAULT_ONTOLOGY_RUN_ROOT
    root = root.resolve(strict=False)
    forbidden = FORBIDDEN_RUN_ROOT.resolve(strict=False)
    try:
        if root == forbidden or forbidden in root.parents:
            raise ValueError(f"run_dir '{root}' is forbidden")
    except RuntimeError:
        pass
    return root


def initialize_run_shell(
    *,
    run_dir: str | None,
    run_id: str | None,
    source_wing: str,
    dry_run: bool,
) -> OntologyRunShell:
    selected_run_id = validate_run_id(run_id) if run_id else generate_run_id()
    run_root = resolve_run_root(run_dir)
    return OntologyRunShell(
        run_id=selected_run_id,
        run_root=run_root,
        run_dir=run_root / selected_run_id,
        dry_run=dry_run,
        source_wing=source_wing,
    )


def materialize_run_shell(run: OntologyRunShell) -> None:
    run.run_dir.mkdir(parents=True, exist_ok=False)
    metadata_path = run.run_dir / "run_metadata.json"
    payload = {
        "schema_name": "ontology.run_shell",
        "schema_version": 1,
        "run_id": run.run_id,
        "run_kind": "chatgpt_signal_ontology",
        "source_wing": run.source_wing,
        "dry_run_default": run.dry_run,
        "initialized_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    metadata_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
