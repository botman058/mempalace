from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile


DEFAULT_ONTOLOGY_RUN_ROOT = Path("/media/u0/OneDrive_Backup/mempalace/data/ontology")
FORBIDDEN_RUN_ROOT = Path("/media/u0/Extreme SSD")
_RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
_PHASE_ORDER = [
    "pass1_open",
    "candidate_clusters",
    "canonical_candidates",
    "route_candidates",
    "route_pass2",
    "route_verify",
    "apply_copies",
]


@dataclass(frozen=True)
class MaterializeResult:
    created_run_dir: bool
    resumed: bool


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


def materialize_run_shell(run: OntologyRunShell) -> MaterializeResult:
    created_run_dir = False
    if not run.run_dir.exists():
        run.run_dir.mkdir(parents=True, exist_ok=False)
        created_run_dir = True
    elif not run.run_dir.is_dir():
        raise OSError(f"run_dir exists and is not a directory: {run.run_dir}")
    else:
        _validate_existing_source_wing(run)

    now = _utc_now()
    metadata_path = run.run_dir / "run_metadata.json"
    payload = {
        "schema_name": "ontology.run_shell",
        "schema_version": 1,
        "run_id": run.run_id,
        "run_kind": "chatgpt_signal_ontology",
        "source_wing": run.source_wing,
        "dry_run_default": run.dry_run,
        "initialized_at": now,
    }
    if not metadata_path.exists():
        _write_json_atomic(metadata_path, payload)

    _ensure_append_ready_files(run.run_dir)
    _write_initial_progress_if_missing(run, now=now)
    _write_artifact_index(run, now=now)

    resumed = not created_run_dir
    _append_resume_marker(run, now=now, event="resumed" if resumed else "initialized")

    # Refresh index once more for resume marker byte/record updates.
    _write_artifact_index(run, now=_utc_now())
    return MaterializeResult(created_run_dir=created_run_dir, resumed=resumed)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_json_atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.tmp.",
        delete=False,
    ) as tmp:
        tmp.write(json.dumps(payload, indent=2))
        tmp.write("\n")
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


def _ensure_append_ready_files(run_dir: Path) -> None:
    append_ready_files = [
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
    for relative in append_ready_files:
        target = run_dir / relative
        if not target.exists():
            target.write_text("", encoding="utf-8")


def _write_initial_progress_if_missing(run: OntologyRunShell, *, now: str) -> None:
    progress_path = run.run_dir / "progress.json"
    if progress_path.exists():
        return

    payload = {
        "schema_name": "ontology.progress",
        "schema_version": 1,
        "run_id": run.run_id,
        "run_kind": "chatgpt_signal_ontology",
        "source_wing": run.source_wing,
        "status": "pending",
        "current_phase": None,
        "current_phase_status": "not_started",
        "phase_order": list(_PHASE_ORDER),
        "phase_attempts": {phase: 0 for phase in _PHASE_ORDER},
        "started_at": now,
        "updated_at": now,
        "ended_at": None,
        "elapsed_seconds": 0,
        "current_phase_progress": {
            "unit": "drawer",
            "total": None,
            "processed": 0,
            "accepted": 0,
            "unresolved": 0,
            "errors": 0,
        },
        "totals": {
            "source_drawers_total": 0,
            "source_drawers_processed": 0,
            "routes_accepted": 0,
            "routes_unresolved": 0,
            "copies_materialized": 0,
            "phase_records_written": 0,
        },
        "last_record": None,
        "warning_count": 0,
        "error_count": 0,
    }
    _write_json_atomic(progress_path, payload)


def _append_resume_marker(run: OntologyRunShell, *, now: str, event: str) -> None:
    marker_path = run.run_dir / "resume_markers.jsonl"
    count = 0
    with marker_path.open("r", encoding="utf-8") as existing:
        for line in existing:
            if line.strip():
                count += 1

    marker = {
        "schema_name": "ontology.resume_marker",
        "schema_version": 1,
        "run_id": run.run_id,
        "sequence": count + 1,
        "recorded_at": now,
        "event": event,
        "source_wing": run.source_wing,
    }
    with marker_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(marker, separators=(",", ":")))
        fh.write("\n")


def _write_artifact_index(run: OntologyRunShell, *, now: str) -> None:
    def _entry(
        *,
        key: str,
        relative_path: str,
        schema_name: str,
        artifact_kind: str,
        phase: str | None,
        content_type: str,
        append_only: bool,
        dashboard_safe: bool,
        privacy_level: str,
    ) -> dict:
        file_path = run.run_dir / relative_path
        exists = file_path.exists()
        size = file_path.stat().st_size if exists else 0
        if content_type == "application/json" and not append_only:
            records = 1 if exists else 0
        else:
            records = _count_jsonl(file_path)
        return {
            "artifact_key": key,
            "relative_path": relative_path,
            "schema_name": schema_name,
            "schema_version": 1,
            "artifact_kind": artifact_kind,
            "phase": phase,
            "content_type": content_type,
            "append_only": append_only,
            "records": records,
            "bytes": size,
            "status": "active",
            "dashboard_safe": dashboard_safe,
            "privacy_level": privacy_level,
            "updated_at": now,
        }

    artifacts = [
        _entry(
            key="progress",
            relative_path="progress.json",
            schema_name="ontology.progress",
            artifact_kind="summary",
            phase=None,
            content_type="application/json",
            append_only=False,
            dashboard_safe=True,
            privacy_level="summary",
        ),
        _entry(
            key="pass1_open",
            relative_path="pass1_open.jsonl",
            schema_name="ontology.phase_record",
            artifact_kind="phase_records",
            phase="pass1_open",
            content_type="application/jsonl",
            append_only=True,
            dashboard_safe=False,
            privacy_level="restricted",
        ),
        _entry(
            key="candidate_clusters",
            relative_path="candidate_clusters.jsonl",
            schema_name="ontology.phase_record",
            artifact_kind="phase_records",
            phase="candidate_clusters",
            content_type="application/jsonl",
            append_only=True,
            dashboard_safe=False,
            privacy_level="restricted",
        ),
        _entry(
            key="canonical_candidates",
            relative_path="canonical_candidates.jsonl",
            schema_name="ontology.phase_record",
            artifact_kind="phase_records",
            phase="canonical_candidates",
            content_type="application/jsonl",
            append_only=True,
            dashboard_safe=False,
            privacy_level="restricted",
        ),
        _entry(
            key="route_candidates",
            relative_path="route_candidates.jsonl",
            schema_name="ontology.phase_record",
            artifact_kind="phase_records",
            phase="route_candidates",
            content_type="application/jsonl",
            append_only=True,
            dashboard_safe=False,
            privacy_level="restricted",
        ),
        _entry(
            key="route_pass2",
            relative_path="route_pass2.jsonl",
            schema_name="ontology.phase_record",
            artifact_kind="phase_records",
            phase="route_pass2",
            content_type="application/jsonl",
            append_only=True,
            dashboard_safe=False,
            privacy_level="restricted",
        ),
        _entry(
            key="route_verify",
            relative_path="route_verify.jsonl",
            schema_name="ontology.phase_record",
            artifact_kind="phase_records",
            phase="route_verify",
            content_type="application/jsonl",
            append_only=True,
            dashboard_safe=False,
            privacy_level="restricted",
        ),
        _entry(
            key="apply_copies",
            relative_path="apply_copies.jsonl",
            schema_name="ontology.phase_record",
            artifact_kind="phase_records",
            phase="apply_copies",
            content_type="application/jsonl",
            append_only=True,
            dashboard_safe=False,
            privacy_level="restricted",
        ),
        _entry(
            key="accepted_routes",
            relative_path="accepted_routes.jsonl",
            schema_name="ontology.accepted_route",
            artifact_kind="decision_records",
            phase="route_verify",
            content_type="application/jsonl",
            append_only=True,
            dashboard_safe=True,
            privacy_level="bounded_excerpt",
        ),
        _entry(
            key="unresolved_routes",
            relative_path="unresolved.jsonl",
            schema_name="ontology.unresolved_route",
            artifact_kind="decision_records",
            phase="route_verify",
            content_type="application/jsonl",
            append_only=True,
            dashboard_safe=True,
            privacy_level="bounded_excerpt",
        ),
        _entry(
            key="resume_markers",
            relative_path="resume_markers.jsonl",
            schema_name="ontology.resume_marker",
            artifact_kind="metadata",
            phase=None,
            content_type="application/jsonl",
            append_only=True,
            dashboard_safe=True,
            privacy_level="summary",
        ),
        _entry(
            key="convergence_report",
            relative_path="convergence_report.json",
            schema_name="ontology.convergence_report",
            artifact_kind="summary",
            phase=None,
            content_type="application/json",
            append_only=False,
            dashboard_safe=True,
            privacy_level="summary",
        ),
        _entry(
            key="apply_ready_manifest",
            relative_path="apply_ready_manifest.json",
            schema_name="ontology.apply_ready_manifest",
            artifact_kind="summary",
            phase=None,
            content_type="application/json",
            append_only=False,
            dashboard_safe=True,
            privacy_level="summary",
        ),
    ]

    payload = {
        "schema_name": "ontology.artifact_index",
        "schema_version": 1,
        "run_id": run.run_id,
        "updated_at": now,
        "artifacts": artifacts,
    }
    _write_json_atomic(run.run_dir / "artifacts_index.json", payload)


def _count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                count += 1
    return count


def _validate_existing_source_wing(run: OntologyRunShell) -> None:
    expected = run.source_wing
    metadata_path = run.run_dir / "run_metadata.json"
    progress_path = run.run_dir / "progress.json"

    for path, label in ((metadata_path, "run_metadata.json"), (progress_path, "progress.json")):
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise OSError(f"failed to parse existing {label}: {exc}") from exc
        existing = payload.get("source_wing")
        if isinstance(existing, str) and existing and existing != expected:
            raise OSError(
                f"source_wing mismatch for existing run '{run.run_id}': "
                f"existing='{existing}' requested='{expected}'"
            )
