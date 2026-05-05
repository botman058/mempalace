from __future__ import annotations

import json
import os
import ipaddress
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Iterable, Mapping
from urllib.parse import urlparse

from .http_client import RemoteMCPError, call_tool
from .llm_client import get_provider
from .ontology_candidate_names import build_candidate_naming_prompt, build_canonical_candidate_records
from .ontology_candidates import cluster_pass1_phase_records
from .ontology_iteration import (
    build_apply_ready_manifest,
    build_convergence_report,
    build_iteration_decision_records,
)
from .ontology_pass1 import classify_drawer_pass1
from .ontology_route_candidates import build_route_candidate_records
from .ontology_route_pass2 import build_route_pass2_prompt, parse_route_pass2_response
from .ontology_route_verify import build_route_verify_prompt, parse_route_verify_response
from .ontology_run import OntologyRunShell, _write_artifact_index


DEFAULT_LOCALAI_BASE_URL = "http://snow-white-iii:8080/v1"
DEFAULT_LOCALAI_TOKEN_FILE = "/media/u0/OneDrive_Backup/mempalace/secrets/localai_token"
DEFAULT_LOCALAI_MODEL = "qwen3-vl-8b-instruct"
DEFAULT_MCP_URL = "http://100.112.179.49:8765"
DEFAULT_MCP_TOKEN_FILE = "/media/u0/OneDrive_Backup/mempalace/secrets/http_token"
DEFAULT_PAGE_LIMIT = 100
_PHASE_ORDER = [
    "pass1_open",
    "candidate_clusters",
    "canonical_candidates",
    "route_candidates",
    "route_pass2",
    "route_verify",
    "apply_copies",
]
_PHASE_UNITS = {
    "pass1_open": "drawer",
    "candidate_clusters": "candidate",
    "canonical_candidates": "candidate",
    "route_candidates": "drawer",
    "route_pass2": "drawer",
    "route_verify": "drawer",
    "apply_copies": "copy",
}


@dataclass(frozen=True)
class RunnerConfig:
    localai_base_url: str
    localai_model: str
    localai_token: str | None
    mcp_url: str
    mcp_token: str | None
    source_wing: str
    apply_copies: bool
    page_limit: int = DEFAULT_PAGE_LIMIT


class _Provider:
    def __init__(self, *, base_url: str, model: str, token: str | None):
        self._provider = get_provider(
            "openai-compat",
            model=model,
            endpoint=base_url,
            api_key=token,
            timeout=180,
        )

    def classify(self, system: str, user: str, json_mode: bool = True) -> Any:
        return self._provider.classify(system, user, json_mode=json_mode)


def ensure_localai_base_url(base_url: str) -> str:
    value = base_url.strip().rstrip("/")
    lowered = value.lower()
    if not value:
        raise ValueError("LocalAI base URL is required")
    if "api.openai.com" in lowered:
        raise ValueError("Refusing LocalAI run because base URL contains api.openai.com")
    host = (urlparse(value).hostname or "").lower()
    if not _is_local_allowed_host(host):
        raise ValueError(f"Refusing non-local LocalAI host: {host or value}")
    return value


def ensure_mcp_base_url(base_url: str) -> str:
    value = base_url.strip().rstrip("/")
    if not value:
        raise ValueError("MCP URL is required")
    host = (urlparse(value).hostname or "").lower()
    if not _is_local_allowed_host(host):
        raise ValueError(f"Refusing non-local MCP host: {host or value}")
    return value


def build_runner_config(args: Any) -> RunnerConfig:
    localai_base = ensure_localai_base_url(
        (
            getattr(args, "localai_base_url", None)
            or os.environ.get("MEMPALACE_ONTOLOGY_LOCALAI_BASE_URL")
            or os.environ.get("LOCALAI_BASE_URL")
            or os.environ.get("ARCHIVEKG_OPENAI_BASE_URL")
            or DEFAULT_LOCALAI_BASE_URL
        )
    )
    localai_token = _resolve_token(
        explicit_token=getattr(args, "localai_token", None) or os.environ.get("LOCALAI_TOKEN"),
        token_file=(
            getattr(args, "localai_token_file", None)
            or os.environ.get("MEMPALACE_ONTOLOGY_LOCALAI_TOKEN_FILE")
            or os.environ.get("LOCALAI_TOKEN_FILE")
            or DEFAULT_LOCALAI_TOKEN_FILE
        ),
    )
    mcp_url = ensure_mcp_base_url(
        (
        getattr(args, "mcp_url", None)
        or os.environ.get("MEMPALACE_ONTOLOGY_MCP_URL")
        or os.environ.get("MEMPALACE_ONTOLOGY_MCP_BASE_URL")
        or os.environ.get("MEMPALACE_HTTP_URL")
        or os.environ.get("MEMPALACE_MCP_URL")
        or DEFAULT_MCP_URL
        )
    )
    mcp_token = _resolve_token(
        explicit_token=(
            getattr(args, "mcp_token", None)
            or os.environ.get("MEMPALACE_ONTOLOGY_MCP_TOKEN")
            or os.environ.get("MEMPALACE_HTTP_TOKEN")
        ),
        token_file=(
            getattr(args, "mcp_token_file", None)
            or os.environ.get("MEMPALACE_ONTOLOGY_MCP_TOKEN_FILE")
            or os.environ.get("MEMPALACE_HTTP_TOKEN_FILE")
            or DEFAULT_MCP_TOKEN_FILE
        ),
    )
    return RunnerConfig(
        localai_base_url=localai_base,
        localai_model=(
            getattr(args, "localai_model", None)
            or os.environ.get("MEMPALACE_ONTOLOGY_LOCALAI_MODEL")
            or os.environ.get("LOCALAI_MODEL")
            or os.environ.get("ARCHIVEKG_CHAT_ROLLUP_MODEL")
            or DEFAULT_LOCALAI_MODEL
        ).strip(),
        localai_token=localai_token,
        mcp_url=mcp_url,
        mcp_token=mcp_token,
        source_wing=(getattr(args, "source_wing", None) or "chatgpt_signals").strip(),
        apply_copies=bool(getattr(args, "apply_copies", False)),
        page_limit=max(1, min(int(getattr(args, "page_limit", DEFAULT_PAGE_LIMIT)), 100)),
    )


def run_chatgpt_signal_ontology(run: OntologyRunShell, config: RunnerConfig) -> None:
    provider = _Provider(
        base_url=config.localai_base_url,
        model=config.localai_model,
        token=config.localai_token,
    )
    pass1_path = run.run_dir / "pass1_open.jsonl"
    cluster_path = run.run_dir / "candidate_clusters.jsonl"
    canonical_path = run.run_dir / "canonical_candidates.jsonl"
    route_candidates_path = run.run_dir / "route_candidates.jsonl"
    route_pass2_path = run.run_dir / "route_pass2.jsonl"
    route_verify_path = run.run_dir / "route_verify.jsonl"
    accepted_path = run.run_dir / "accepted_routes.jsonl"
    unresolved_path = run.run_dir / "unresolved.jsonl"
    apply_copies_path = run.run_dir / "apply_copies.jsonl"

    progress = _load_progress(run.run_dir / "progress.json")

    try:
        _set_phase(progress, "pass1_open")
        pass1_subjects = _existing_subject_ids(pass1_path)
        progress["totals"]["source_drawers_processed"] = max(
            int(progress["totals"].get("source_drawers_processed", 0)),
            len(pass1_subjects),
        )
        pass1_sequence = _next_sequence(pass1_path)
        for page, discovered_total in _iter_drawer_pages(config=config):
            _update_drawer_progress(
                run,
                progress,
                phase="pass1_open",
                total=discovered_total,
            )
            pending = [drawer for drawer in page if drawer.get("drawer_id") not in pass1_subjects]
            for drawer in pending:
                record = classify_drawer_pass1(
                    provider=provider,
                    run_id=run.run_id,
                    sequence=pass1_sequence,
                    attempt=1,
                    source_drawer=drawer,
                )
                _append_jsonl(pass1_path, record)
                pass1_subjects.add(record.get("subject_id"))
                progress["totals"]["source_drawers_processed"] = max(
                    int(progress["totals"].get("source_drawers_processed", 0)),
                    len(pass1_subjects),
                )
                pass1_sequence += 1
                _bump_after_write(
                    run,
                    progress,
                    phase="pass1_open",
                    status=record.get("record_status", "ok"),
                    processed_inc=1,
                    record=record,
                    record_relative_path="pass1_open.jsonl",
                )
        _phase_done(run, progress, "pass1_open")

        _set_phase(progress, "candidate_clusters")
        clustered = cluster_pass1_phase_records(_load_jsonl(pass1_path), run_id=run.run_id)
        _update_drawer_progress(
            run,
            progress,
            phase="candidate_clusters",
            total=len(clustered.records),
        )
        cluster_subject_ids = _existing_subject_ids(cluster_path)
        for record in clustered.records:
            subject_id = record.get("subject_id")
            if not isinstance(subject_id, str) or not subject_id or subject_id in cluster_subject_ids:
                continue
            _append_jsonl(cluster_path, record)
            cluster_subject_ids.add(subject_id)
            _bump_after_write(
                run,
                progress,
                phase="candidate_clusters",
                status=record.get("record_status", "ok"),
                processed_inc=1,
                record=record,
                record_relative_path="candidate_clusters.jsonl",
            )
        _phase_done(run, progress, "candidate_clusters")

        _set_phase(progress, "canonical_candidates")
        cluster_records = _load_jsonl(cluster_path)
        canonical_subject_ids = _existing_subject_ids(canonical_path)
        missing_cluster_records: list[dict[str, Any]] = []
        outputs: dict[str, Any] = {}
        for record in cluster_records:
            if record.get("record_status") != "ok":
                continue
            subject_id = record.get("subject_id")
            if not isinstance(subject_id, str) or not subject_id:
                continue
            if subject_id in canonical_subject_ids:
                continue
            prompt = build_candidate_naming_prompt(record)
            outputs[subject_id] = provider.classify("", prompt, json_mode=True)
            missing_cluster_records.append(record)
        built = build_canonical_candidate_records(
            missing_cluster_records,
            outputs,
            run_id=run.run_id,
            sequence_start=_next_sequence(canonical_path),
        )
        _update_drawer_progress(
            run,
            progress,
            phase="canonical_candidates",
            total=len(cluster_records),
        )
        for record in built.records:
            subject_id = record.get("subject_id")
            if not isinstance(subject_id, str) or not subject_id or subject_id in canonical_subject_ids:
                continue
            _append_jsonl(canonical_path, record)
            canonical_subject_ids.add(subject_id)
            _bump_after_write(
                run,
                progress,
                phase="canonical_candidates",
                status=record.get("record_status", "ok"),
                processed_inc=1,
                record=record,
                record_relative_path="canonical_candidates.jsonl",
            )
        _phase_done(run, progress, "canonical_candidates")

        canonical_records = _load_jsonl(canonical_path)

        _set_phase(progress, "route_candidates")
        route_subjects = _existing_subject_ids(route_candidates_path)
        route_sequence = _next_sequence(route_candidates_path)
        for page, discovered_total in _iter_drawer_pages(config=config):
            _update_drawer_progress(
                run,
                progress,
                phase="route_candidates",
                total=discovered_total,
            )
            pending = [drawer for drawer in page if drawer.get("drawer_id") not in route_subjects]
            if not pending:
                continue
            built = build_route_candidate_records(
                pending,
                canonical_records,
                run_id=run.run_id,
                sequence_start=route_sequence,
                attempt=1,
            )
            for record in built.records:
                _append_jsonl(route_candidates_path, record)
                route_subjects.add(record.get("subject_id"))
                route_sequence += 1
                _bump_after_write(
                    run,
                    progress,
                    phase="route_candidates",
                    status=record.get("record_status", "ok"),
                    processed_inc=1,
                    record=record,
                    record_relative_path="route_candidates.jsonl",
                )
        _phase_done(run, progress, "route_candidates")

        _set_phase(progress, "route_pass2")
        route_candidate_records = {
            record.get("subject_id"): record for record in _load_jsonl(route_candidates_path) if isinstance(record.get("subject_id"), str)
        }
        route_pass2_subjects = _existing_subject_ids(route_pass2_path)
        route_pass2_sequence = _next_sequence(route_pass2_path)
        for page, discovered_total in _iter_drawer_pages(config=config):
            _update_drawer_progress(
                run,
                progress,
                phase="route_pass2",
                total=discovered_total,
            )
            for drawer in page:
                drawer_id = drawer.get("drawer_id")
                if drawer_id in route_pass2_subjects or drawer_id not in route_candidate_records:
                    continue
                route_record = route_candidate_records[drawer_id]
                prompt = build_route_pass2_prompt(drawer, route_record)
                response = provider.classify("", prompt, json_mode=True)
                parsed = parse_route_pass2_response(drawer, route_record, response)
                parsed["sequence"] = route_pass2_sequence
                _append_jsonl(route_pass2_path, parsed)
                route_pass2_subjects.add(drawer_id)
                route_pass2_sequence += 1
                _bump_after_write(
                    run,
                    progress,
                    phase="route_pass2",
                    status=parsed.get("record_status", "ok"),
                    processed_inc=1,
                    record=parsed,
                    record_relative_path="route_pass2.jsonl",
                )
        _phase_done(run, progress, "route_pass2")

        _set_phase(progress, "route_verify")
        route_pass2_records = {
            record.get("subject_id"): record for record in _load_jsonl(route_pass2_path) if isinstance(record.get("subject_id"), str)
        }
        verify_subjects = _existing_subject_ids(route_verify_path)
        verify_sequence = _next_sequence(route_verify_path)
        accepted_keys = _existing_verification_record_refs(accepted_path)
        unresolved_keys = _existing_verification_record_refs(unresolved_path)
        accepted_sequence = _next_sequence(accepted_path)
        unresolved_sequence = _next_sequence(unresolved_path)
        for page, discovered_total in _iter_drawer_pages(config=config):
            _update_drawer_progress(
                run,
                progress,
                phase="route_verify",
                total=discovered_total,
            )
            for drawer in page:
                drawer_id = drawer.get("drawer_id")
                if drawer_id in verify_subjects:
                    continue
                route_candidate = route_candidate_records.get(drawer_id)
                route_pass2 = route_pass2_records.get(drawer_id)
                if route_candidate is None or route_pass2 is None:
                    continue
                prompt = build_route_verify_prompt(drawer, route_candidate, route_pass2)
                response = provider.classify("", prompt, json_mode=True)
                parsed = parse_route_verify_response(drawer, route_candidate, route_pass2, response)
                parsed["sequence"] = verify_sequence
                _append_jsonl(route_verify_path, parsed)
                verify_subjects.add(drawer_id)
                verify_sequence += 1
                _bump_after_write(
                    run,
                    progress,
                    phase="route_verify",
                    status=parsed.get("record_status", "ok"),
                    processed_inc=1,
                    accepted_inc=1 if parsed.get("record_status") == "ok" and parsed.get("payload", {}).get("route_status") == "accepted" else 0,
                    unresolved_inc=1 if parsed.get("record_status") == "ok" and parsed.get("payload", {}).get("route_status") != "accepted" else 0,
                    record=parsed,
                    record_relative_path="route_verify.jsonl",
                )
                accepted_sequence, unresolved_sequence = _append_decision_backfill(
                    run=run,
                    progress=progress,
                    verify_records=[parsed],
                    accepted_path=accepted_path,
                    unresolved_path=unresolved_path,
                    accepted_keys=accepted_keys,
                    unresolved_keys=unresolved_keys,
                    accepted_sequence=accepted_sequence,
                    unresolved_sequence=unresolved_sequence,
                )
        _phase_done(run, progress, "route_verify")

        manifest = _materialize_decisions_and_reports(
            run=run,
            progress=progress,
            route_verify_path=route_verify_path,
            accepted_path=accepted_path,
            unresolved_path=unresolved_path,
        )
        _materialize_apply_copies(
            run=run,
            progress=progress,
            config=config,
            manifest=manifest,
            apply_copies_path=apply_copies_path,
        )
        _mark_completed(run, progress, final_phase="apply_copies")
    except Exception:
        _mark_failed(run, progress)
        raise


def _iter_drawer_pages(*, config: RunnerConfig) -> Iterable[tuple[list[dict[str, Any]], int]]:
    offset = 0
    discovered_total = 0
    while True:
        result = call_tool(
            "mempalace_export_drawers",
            arguments={"wing": config.source_wing, "limit": config.page_limit, "offset": offset},
            url=config.mcp_url,
            token=config.mcp_token,
        )
        if not isinstance(result, Mapping):
            raise RemoteMCPError("Invalid response from mempalace_export_drawers")
        if result.get("error"):
            raise RemoteMCPError(str(result.get("error")))
        drawers = result.get("drawers") if isinstance(result, Mapping) else None
        if not isinstance(drawers, list):
            raise RemoteMCPError("Invalid mempalace_export_drawers shape: missing drawers list")
        if not drawers:
            return
        normalized = [item for item in drawers if isinstance(item, dict)]
        if not normalized:
            return
        discovered_total += len(normalized)
        yield normalized, discovered_total
        offset += len(normalized)
        if len(normalized) < config.page_limit:
            return


def _materialize_decisions_and_reports(
    *,
    run: OntologyRunShell,
    progress: dict[str, Any],
    route_verify_path: Path,
    accepted_path: Path,
    unresolved_path: Path,
) -> dict[str, Any]:
    verify_records = _load_jsonl(route_verify_path)
    _append_decision_backfill(
        run=run,
        progress=progress,
        verify_records=verify_records,
        accepted_path=accepted_path,
        unresolved_path=unresolved_path,
        accepted_keys=_existing_verification_record_refs(accepted_path),
        unresolved_keys=_existing_verification_record_refs(unresolved_path),
        accepted_sequence=_next_sequence(accepted_path),
        unresolved_sequence=_next_sequence(unresolved_path),
    )
    accepted_records = _load_jsonl(accepted_path)
    unresolved_records = _load_jsonl(unresolved_path)
    progress["totals"]["routes_accepted"] = len(accepted_records)
    progress["totals"]["routes_unresolved"] = len(unresolved_records)
    _refresh_progress(run, progress, phase="route_verify", status="running")
    report = build_convergence_report(
        verify_records,
        accepted_routes=accepted_records,
        unresolved_routes=unresolved_records,
        run_id=run.run_id,
    )
    _write_json_atomic(run.run_dir / "convergence_report.json", report)
    manifest = build_apply_ready_manifest(
        accepted_records,
        unresolved_routes=unresolved_records,
        run_id=run.run_id,
    )
    _write_json_atomic(run.run_dir / "apply_ready_manifest.json", manifest)
    return manifest


def _materialize_apply_copies(
    *,
    run: OntologyRunShell,
    progress: dict[str, Any],
    config: RunnerConfig,
    manifest: Mapping[str, Any],
    apply_copies_path: Path,
) -> None:
    _set_phase(progress, "apply_copies")
    routes = manifest.get("routes", [])
    _update_drawer_progress(run, progress, phase="apply_copies", total=len(routes))
    if not config.apply_copies:
        return

    done = _existing_subject_ids(apply_copies_path)
    sequence = _next_sequence(apply_copies_path)
    for route in routes:
        source_drawer_id = route.get("source_drawer_id")
        if not isinstance(source_drawer_id, str) or source_drawer_id in done:
            continue
        payload = call_tool(
            "mempalace_copy_drawer",
            arguments={
                "source_drawer_id": source_drawer_id,
                "canonical_wing": route.get("canonical_wing"),
                "canonical_room": route.get("canonical_room"),
                "ontology_run_id": run.run_id,
                "ontology_route_iteration": route.get("route_iteration"),
                "ontology_candidate_id": route.get("candidate_id"),
                "ontology_route_record_ref": route.get("accepted_route_record_ref"),
            },
            url=config.mcp_url,
            token=config.mcp_token,
        )
        record = {
            "schema_name": "ontology.phase_record",
            "schema_version": 1,
            "run_id": run.run_id,
            "phase": "apply_copies",
            "sequence": sequence,
            "attempt": 1,
            "recorded_at": _utc_now(),
            "subject_type": "drawer",
            "subject_id": source_drawer_id,
            "record_status": "ok" if payload.get("success") else "error",
            "source": {
                "wing": route.get("source_wing"),
                "room": route.get("source_room"),
                "drawer_id": source_drawer_id,
            },
            "payload": payload,
        }
        _append_jsonl(apply_copies_path, record)
        done.add(source_drawer_id)
        sequence += 1
        _bump_after_write(
            run,
            progress,
            phase="apply_copies",
            status=record.get("record_status", "ok"),
            processed_inc=1,
            copies_inc=1 if record.get("record_status") == "ok" else 0,
            record=record,
            record_relative_path="apply_copies.jsonl",
        )


def _resolve_token(*, explicit_token: str | None, token_file: str | None) -> str | None:
    if explicit_token and explicit_token.strip():
        return explicit_token.strip()
    if not token_file:
        return None
    try:
        token = Path(token_file).expanduser().read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return token or None


def _load_progress(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _refresh_progress(run: OntologyRunShell, progress: dict[str, Any], *, phase: str | None, status: str) -> None:
    progress["status"] = status
    progress["current_phase"] = phase
    progress["current_phase_status"] = "running" if status not in {"completed", "failed"} else status
    progress["updated_at"] = _utc_now()
    _write_json_atomic(run.run_dir / "progress.json", progress)
    _write_artifact_index(run, now=_utc_now())


def _set_phase(progress: dict[str, Any], phase: str) -> None:
    progress["current_phase"] = phase
    progress["current_phase_status"] = "running"
    progress["current_phase_progress"] = {
        "unit": _PHASE_UNITS.get(phase, "drawer"),
        "total": None,
        "processed": 0,
        "accepted": 0,
        "unresolved": 0,
        "errors": 0,
    }
    attempts = progress.get("phase_attempts") or {}
    if phase in _PHASE_ORDER:
        attempts[phase] = int(attempts.get(phase, 0)) + 1
    progress["phase_attempts"] = attempts


def _phase_done(run: OntologyRunShell, progress: dict[str, Any], phase: str) -> None:
    progress["current_phase"] = phase
    progress["current_phase_status"] = "completed"
    progress["status"] = "running"
    progress["updated_at"] = _utc_now()
    _write_json_atomic(run.run_dir / "progress.json", progress)
    _write_artifact_index(run, now=_utc_now())


def _bump_after_write(
    run: OntologyRunShell,
    progress: dict[str, Any],
    *,
    phase: str,
    status: str,
    processed_inc: int = 0,
    accepted_inc: int = 0,
    unresolved_inc: int = 0,
    copies_inc: int = 0,
    record: Mapping[str, Any] | None = None,
    record_relative_path: str | None = None,
) -> None:
    totals = progress.get("totals") or {}
    totals["phase_records_written"] = int(totals.get("phase_records_written", 0)) + 1
    if accepted_inc:
        totals["routes_accepted"] = int(totals.get("routes_accepted", 0)) + accepted_inc
    if unresolved_inc:
        totals["routes_unresolved"] = int(totals.get("routes_unresolved", 0)) + unresolved_inc
    if copies_inc:
        totals["copies_materialized"] = int(totals.get("copies_materialized", 0)) + copies_inc
    progress["totals"] = totals
    phase_progress = progress.get("current_phase_progress") or {}
    phase_progress["processed"] = int(phase_progress.get("processed", 0)) + max(0, processed_inc)
    if status in {"error", "invalid_model_output"}:
        phase_progress["errors"] = int(phase_progress.get("errors", 0)) + 1
        progress["error_count"] = int(progress.get("error_count", 0)) + 1
    phase_progress["accepted"] = int(phase_progress.get("accepted", 0)) + max(0, accepted_inc)
    phase_progress["unresolved"] = int(phase_progress.get("unresolved", 0)) + max(0, unresolved_inc)
    progress["current_phase_progress"] = phase_progress
    if record is not None and record_relative_path:
        sequence = record.get("sequence")
        subject_id = record.get("subject_id")
        recorded_at = record.get("recorded_at")
        prior_last_record = progress.get("last_record") if isinstance(progress.get("last_record"), Mapping) else {}
        progress["last_record"] = {
            "phase": phase,
            "relative_path": record_relative_path,
            "sequence": sequence if isinstance(sequence, int) else None,
            "subject_id": (
                subject_id
                if isinstance(subject_id, str)
                else prior_last_record.get("subject_id")
                if isinstance(prior_last_record.get("subject_id"), str)
                else None
            ),
            "recorded_at": recorded_at if isinstance(recorded_at, str) else _utc_now(),
        }
    _refresh_progress(run, progress, phase=phase, status="running")


def _update_drawer_progress(
    run: OntologyRunShell,
    progress: dict[str, Any],
    *,
    phase: str,
    total: int,
) -> None:
    totals = progress.get("totals") or {}
    totals["source_drawers_total"] = max(int(totals.get("source_drawers_total", 0)), int(total))
    progress["totals"] = totals
    phase_progress = progress.get("current_phase_progress") or {}
    phase_progress["total"] = max(int(phase_progress.get("total") or 0), int(total))
    progress["current_phase_progress"] = phase_progress
    _refresh_progress(run, progress, phase=phase, status="running")


def _mark_completed(run: OntologyRunShell, progress: dict[str, Any], *, final_phase: str) -> None:
    now = _utc_now()
    progress["status"] = "completed"
    progress["current_phase"] = final_phase
    progress["current_phase_status"] = "completed"
    progress["updated_at"] = now
    progress["ended_at"] = now
    _write_json_atomic(run.run_dir / "progress.json", progress)
    _write_artifact_index(run, now=now)


def _mark_failed(run: OntologyRunShell, progress: dict[str, Any]) -> None:
    now = _utc_now()
    progress["status"] = "failed"
    progress["current_phase_status"] = "failed"
    progress["updated_at"] = now
    progress["ended_at"] = now
    progress["error_count"] = int(progress.get("error_count", 0)) + 1
    _write_json_atomic(run.run_dir / "progress.json", progress)
    _write_artifact_index(run, now=now)


def _next_sequence(path: Path) -> int:
    last = 0
    for record in _load_jsonl(path):
        value = record.get("sequence")
        if isinstance(value, int) and value > last:
            last = value
    return last + 1


def _existing_subject_ids(path: Path) -> set[str]:
    subject_ids: set[str] = set()
    for record in _load_jsonl(path):
        value = record.get("subject_id")
        if isinstance(value, str) and value:
            subject_ids.add(value)
    return subject_ids


def _existing_verification_record_refs(path: Path) -> set[str]:
    refs: set[str] = set()
    for record in _load_jsonl(path):
        value = record.get("verification_record_ref")
        if isinstance(value, str) and value:
            refs.add(value)
    return refs


def _append_decision_backfill(
    *,
    run: OntologyRunShell,
    progress: dict[str, Any],
    verify_records: list[dict[str, Any]],
    accepted_path: Path,
    unresolved_path: Path,
    accepted_keys: set[str],
    unresolved_keys: set[str],
    accepted_sequence: int,
    unresolved_sequence: int,
) -> tuple[int, int]:
    if not verify_records:
        return accepted_sequence, unresolved_sequence
    built = build_iteration_decision_records(
        verify_records,
        run_id=run.run_id,
        sequence_start=1,
    )
    for record in built.accepted_routes:
        key = record.get("verification_record_ref")
        if not isinstance(key, str) or not key or key in accepted_keys:
            continue
        materialized = dict(record)
        materialized["sequence"] = accepted_sequence
        _append_jsonl(accepted_path, materialized)
        accepted_keys.add(key)
        accepted_sequence += 1
        _bump_after_write(
            run,
            progress,
            phase="route_verify",
            status=materialized.get("record_status", "ok"),
            processed_inc=0,
            record=materialized,
            record_relative_path="accepted_routes.jsonl",
        )
    for record in built.unresolved_routes:
        key = record.get("verification_record_ref")
        if not isinstance(key, str) or not key or key in unresolved_keys:
            continue
        materialized = dict(record)
        materialized["sequence"] = unresolved_sequence
        _append_jsonl(unresolved_path, materialized)
        unresolved_keys.add(key)
        unresolved_sequence += 1
        _bump_after_write(
            run,
            progress,
            phase="route_verify",
            status=materialized.get("record_status", "ok"),
            processed_inc=0,
            record=materialized,
            record_relative_path="unresolved.jsonl",
        )
    return accepted_sequence, unresolved_sequence


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _append_jsonl(path: Path, record: Mapping[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, separators=(",", ":")))
        fh.write("\n")


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
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


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _is_local_allowed_host(host: str) -> bool:
    if not host:
        return False
    if host in {"localhost", "127.0.0.1", "::1"}:
        return True
    if host.endswith(".local"):
        return True
    if "." not in host:
        return True
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    if ip.is_loopback:
        return True
    if isinstance(ip, ipaddress.IPv4Address):
        if ip.is_private:
            return True
        if ipaddress.ip_network("100.64.0.0/10").supernet_of(ipaddress.ip_network(f"{ip}/32")):
            return True
        return False
    if isinstance(ip, ipaddress.IPv6Address) and ip.is_private:
        return True
    return False
