from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import re
from typing import Any, Iterable, Mapping

from .ontology_run import validate_run_id


LOW_CONFIDENCE_THRESHOLD = 0.5
ACCEPTED_ROUTE_SCHEMA = "ontology.accepted_route"
UNRESOLVED_ROUTE_SCHEMA = "ontology.unresolved_route"
CONVERGENCE_REPORT_SCHEMA = "ontology.convergence_report"
APPLY_READY_MANIFEST_SCHEMA = "ontology.apply_ready_manifest"
_ROUTE_VERIFY_PHASE = "route_verify"
_ROUTE_PASS2_PHASE = "route_pass2"
_VALID_NEXT_ACTIONS = frozenset({"reroute", "manual_review", "drop", "retry_later"})
_SLUG_RE = re.compile(r"^[a-z0-9_]+$")
_REF_SEQUENCE_RE = re.compile(r"#([1-9][0-9]*)$")


@dataclass(frozen=True)
class IterationDecisionBuildResult:
    accepted_routes: list[dict[str, Any]]
    unresolved_routes: list[dict[str, Any]]
    skipped_summary: dict[str, Any]


@dataclass(frozen=True)
class _NormalizedVerificationRecord:
    run_id: str
    sequence: int
    attempt: int
    route_iteration: int
    recorded_at: str
    source_drawer_id: str
    source_wing: str
    source_room: str
    record_status: str
    route_status: str | None
    copy_ready: bool | None
    selected_candidate_id: str | None
    selected_candidate_key: str | None
    canonical_wing: str | None
    canonical_room: str | None
    canonical_candidate_record_ref: str | None
    route_record_ref: str
    verification_record_ref: str
    route_candidate_record_ref: str | None
    route_confidence: float | None
    verification_confidence: float | None
    rationale_summary: str | None
    route_rationale_summary: str | None
    reason_code: str | None
    reason_detail: str | None
    next_action: str | None
    retryable: bool | None
    source_excerpt: str | None
    shortlist_candidate_ids: list[str]
    shortlist_candidate_keys: list[str]
    source_candidate_refs: list[dict[str, Any]]


@dataclass(frozen=True)
class _DecisionTemplate:
    kind: str
    status: str
    route_iteration: int
    verification_sequence: int
    source_drawer_id: str
    reason_code: str | None
    retryable: bool
    record: dict[str, Any]


@dataclass(frozen=True)
class _NormalizedAcceptedRoute:
    run_id: str
    sequence: int
    route_iteration: int
    source_drawer_id: str
    source_wing: str
    source_room: str
    candidate_id: str
    candidate_key: str
    canonical_wing: str
    canonical_room: str
    route_confidence: float | None
    verification_confidence: float | None
    route_record_ref: str
    verification_record_ref: str
    route_candidate_record_ref: str | None
    recorded_at: str
    rationale_summary: str


@dataclass(frozen=True)
class _NormalizedUnresolvedRoute:
    run_id: str
    sequence: int
    route_iteration: int
    source_drawer_id: str
    source_wing: str
    source_room: str
    unresolved_status: str
    candidate_ids: list[str]
    candidate_keys: list[str]
    reason_code: str
    reason_detail: str
    route_confidence: float | None
    verification_confidence: float | None
    next_action: str
    retryable: bool
    route_record_ref: str
    verification_record_ref: str
    source_excerpt: str | None
    recorded_at: str


def build_iteration_decision_records(
    route_verify_records: Iterable[Mapping[str, Any]],
    *,
    run_id: str | None = None,
    sequence_start: int = 1,
    low_confidence_threshold: float = LOW_CONFIDENCE_THRESHOLD,
) -> IterationDecisionBuildResult:
    if not isinstance(sequence_start, int) or isinstance(sequence_start, bool) or sequence_start < 1:
        raise ValueError("sequence_start must be a positive integer")
    threshold = _validate_threshold(low_confidence_threshold)

    records_list = list(route_verify_records)
    resolved_run_id = _resolve_run_id(records_list, run_id=run_id)
    decisions, skipped_summary = _derive_decisions(
        records_list,
        run_id=resolved_run_id,
        low_confidence_threshold=threshold,
    )

    accepted_routes: list[dict[str, Any]] = []
    unresolved_routes: list[dict[str, Any]] = []
    accepted_sequence = sequence_start
    unresolved_sequence = sequence_start

    for decision in decisions:
        materialized = dict(decision.record)
        if decision.kind == "accepted":
            materialized["sequence"] = accepted_sequence
            accepted_routes.append(materialized)
            accepted_sequence += 1
        else:
            materialized["sequence"] = unresolved_sequence
            unresolved_routes.append(materialized)
            unresolved_sequence += 1

    return IterationDecisionBuildResult(
        accepted_routes=accepted_routes,
        unresolved_routes=unresolved_routes,
        skipped_summary=skipped_summary,
    )


def build_convergence_report(
    route_verify_records: Iterable[Mapping[str, Any]],
    *,
    accepted_routes: Iterable[Mapping[str, Any]] | None = None,
    unresolved_routes: Iterable[Mapping[str, Any]] | None = None,
    run_id: str | None = None,
    low_confidence_threshold: float = LOW_CONFIDENCE_THRESHOLD,
) -> dict[str, Any]:
    threshold = _validate_threshold(low_confidence_threshold)
    records_list = list(route_verify_records)
    resolved_run_id = _resolve_run_id(records_list, run_id=run_id)
    decisions, skipped_summary = _derive_decisions(
        records_list,
        run_id=resolved_run_id,
        low_confidence_threshold=threshold,
    )

    if accepted_routes is None or unresolved_routes is None:
        built = build_iteration_decision_records(
            records_list,
            run_id=resolved_run_id,
            low_confidence_threshold=threshold,
        )
        resolved_accepted_routes = (
            built.accepted_routes if accepted_routes is None else list(accepted_routes)
        )
        resolved_unresolved_routes = (
            built.unresolved_routes if unresolved_routes is None else list(unresolved_routes)
        )
    else:
        resolved_accepted_routes = list(accepted_routes)
        resolved_unresolved_routes = list(unresolved_routes)

    iteration_counts: dict[int, dict[str, Any]] = {}
    for decision in decisions:
        bucket = iteration_counts.setdefault(
            decision.route_iteration,
            {
                "route_iteration": decision.route_iteration,
                "verification_records": 0,
                "accepted_records": 0,
                "unresolved_records": 0,
                "error_records": 0,
                "retryable_records": 0,
                "status_counts": Counter(),
                "reason_counts": Counter(),
            },
        )
        bucket["verification_records"] += 1
        if decision.kind == "accepted":
            bucket["accepted_records"] += 1
        else:
            bucket["unresolved_records"] += 1
            if decision.status in {"invalid_model_output", "error"}:
                bucket["error_records"] += 1
        if decision.retryable:
            bucket["retryable_records"] += 1
        bucket["status_counts"][decision.status] += 1
        if decision.reason_code is not None:
            bucket["reason_counts"][decision.reason_code] += 1

    iteration_summaries = [
        {
            "route_iteration": route_iteration,
            "verification_records": bucket["verification_records"],
            "accepted_records": bucket["accepted_records"],
            "unresolved_records": bucket["unresolved_records"],
            "error_records": bucket["error_records"],
            "retryable_records": bucket["retryable_records"],
            "status_counts": dict(sorted(bucket["status_counts"].items())),
            "reason_counts": dict(sorted(bucket["reason_counts"].items())),
        }
        for route_iteration, bucket in sorted(iteration_counts.items())
    ]

    latest_by_drawer: dict[str, tuple[tuple[int, int, int], dict[str, Any]]] = {}
    for record in resolved_accepted_routes:
        normalized = _normalize_accepted_route_record(record)
        if normalized is None or normalized.run_id != resolved_run_id:
            continue
        terminal = _accepted_terminal_entry(normalized)
        _update_latest_terminal(latest_by_drawer, terminal)
    for record in resolved_unresolved_routes:
        normalized = _normalize_unresolved_route_record(record)
        if normalized is None or normalized.run_id != resolved_run_id:
            continue
        terminal = _unresolved_terminal_entry(normalized)
        _update_latest_terminal(latest_by_drawer, terminal)

    terminal_entries = [
        entry
        for _, entry in sorted(latest_by_drawer.values(), key=lambda item: item[1]["source_drawer_id"])
    ]
    terminal_status_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    latest_terminal_drawer_states: list[dict[str, Any]] = []
    unresolved_drawer_refs: list[dict[str, Any]] = []
    accepted_count = 0
    unresolved_count = 0
    error_count = 0
    retryable_count = 0

    for entry in terminal_entries:
        status = entry["status"]
        terminal_status_counts[status] += 1
        latest_terminal_drawer_states.append(
            {
                "source_drawer_id": entry["source_drawer_id"],
                "source_wing": entry["source_wing"],
                "source_room": entry["source_room"],
                "route_iteration": entry["route_iteration"],
                "terminal_status": status,
                "candidate_ids": list(entry["candidate_ids"]),
                "candidate_keys": list(entry["candidate_keys"]),
                "reason_code": entry["reason_code"],
                "reason_detail": entry["reason_detail"],
                "route_confidence": entry["route_confidence"],
                "verification_confidence": entry["verification_confidence"],
                "next_action": entry["next_action"],
                "retryable": entry["retryable"],
                "route_record_ref": entry["route_record_ref"],
                "verification_record_ref": entry["verification_record_ref"],
                "source_excerpt": entry["source_excerpt"],
            }
        )
        if status == "accepted":
            accepted_count += 1
            continue
        if status in {"invalid_model_output", "error"}:
            error_count += 1
        else:
            unresolved_count += 1
        if entry["retryable"]:
            retryable_count += 1
        if entry["reason_code"] is not None:
            reason_counts[entry["reason_code"]] += 1
        unresolved_drawer_refs.append(
            {
                "source_drawer_id": entry["source_drawer_id"],
                "source_wing": entry["source_wing"],
                "source_room": entry["source_room"],
                "route_iteration": entry["route_iteration"],
                "unresolved_status": status,
                "candidate_ids": list(entry["candidate_ids"]),
                "candidate_keys": list(entry["candidate_keys"]),
                "reason_code": entry["reason_code"],
                "reason_detail": entry["reason_detail"],
                "route_confidence": entry["route_confidence"],
                "verification_confidence": entry["verification_confidence"],
                "next_action": entry["next_action"],
                "retryable": entry["retryable"],
                "route_record_ref": entry["route_record_ref"],
                "verification_record_ref": entry["verification_record_ref"],
                "source_excerpt": entry["source_excerpt"],
            }
        )

    if not terminal_entries:
        terminal_status = "empty"
    elif error_count > 0:
        terminal_status = "error"
    elif unresolved_count > 0:
        terminal_status = "needs_review"
    else:
        terminal_status = "converged"

    return {
        "schema_name": CONVERGENCE_REPORT_SCHEMA,
        "schema_version": 1,
        "run_id": resolved_run_id,
        "terminal_status": terminal_status,
        "total_verification_records": len(decisions),
        "total_drawers": len(terminal_entries),
        "iteration_count": len(iteration_summaries),
        "iteration_summaries": iteration_summaries,
        "accepted_count": accepted_count,
        "unresolved_count": unresolved_count,
        "error_count": error_count,
        "retryable_count": retryable_count,
        "reason_counts": dict(sorted(reason_counts.items())),
        "terminal_status_counts": dict(sorted(terminal_status_counts.items())),
        "latest_terminal_drawer_states": latest_terminal_drawer_states,
        "unresolved_drawer_refs": unresolved_drawer_refs,
        "skipped_summary": skipped_summary,
    }


def build_apply_ready_manifest(
    accepted_routes: Iterable[Mapping[str, Any]],
    *,
    unresolved_routes: Iterable[Mapping[str, Any]] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    records_list = list(accepted_routes)
    unresolved_list = list(unresolved_routes) if unresolved_routes is not None else None
    input_record_count = len(records_list) + (len(unresolved_list) if unresolved_list is not None else 0)
    run_id_records: list[Mapping[str, Any]] = list(records_list)
    if unresolved_list is not None:
        run_id_records.extend(unresolved_list)
    resolved_run_id = _resolve_run_id(run_id_records, run_id=run_id)

    skipped_by_reason: Counter[str] = Counter()
    latest_accepted_by_drawer: dict[str, tuple[tuple[int, int, int], _NormalizedAcceptedRoute]] = {}
    latest_terminal_by_drawer: dict[str, tuple[tuple[int, int, int], dict[str, Any]]] | None = (
        {} if unresolved_routes is not None else None
    )

    for record in records_list:
        normalized = _normalize_accepted_route_record(record)
        if normalized is None:
            skipped_by_reason["invalid_accepted_route"] += 1
            continue
        if normalized.run_id != resolved_run_id:
            skipped_by_reason["run_id_mismatch"] += 1
            continue
        order_key = _decision_order_key(
            normalized.route_iteration,
            _ref_sequence(normalized.verification_record_ref),
            normalized.sequence,
        )
        existing = latest_accepted_by_drawer.get(normalized.source_drawer_id)
        if existing is None or order_key > existing[0]:
            latest_accepted_by_drawer[normalized.source_drawer_id] = (order_key, normalized)
        if latest_terminal_by_drawer is not None:
            _update_latest_terminal(latest_terminal_by_drawer, _accepted_terminal_entry(normalized))

    if unresolved_list is not None:
        for record in unresolved_list:
            normalized = _normalize_unresolved_route_record(record)
            if normalized is None:
                skipped_by_reason["invalid_unresolved_route"] += 1
                continue
            if normalized.run_id != resolved_run_id:
                skipped_by_reason["run_id_mismatch"] += 1
                continue
            _update_latest_terminal(latest_terminal_by_drawer, _unresolved_terminal_entry(normalized))

    materialized_routes: list[_NormalizedAcceptedRoute] = []
    for drawer_id, (_, accepted_route) in sorted(
        latest_accepted_by_drawer.items(),
        key=lambda item: item[0],
    ):
        if latest_terminal_by_drawer is not None:
            terminal_entry = latest_terminal_by_drawer.get(drawer_id)
            if terminal_entry is None or terminal_entry[1]["status"] != "accepted":
                continue
        materialized_routes.append(accepted_route)

    routes = [
        {
            "source_drawer_id": item.source_drawer_id,
            "source_wing": item.source_wing,
            "source_room": item.source_room,
            "route_iteration": item.route_iteration,
            "candidate_id": item.candidate_id,
            "candidate_key": item.candidate_key,
            "canonical_wing": item.canonical_wing,
            "canonical_room": item.canonical_room,
            "route_confidence": item.route_confidence,
            "verification_confidence": item.verification_confidence,
            "route_record_ref": item.route_record_ref,
            "verification_record_ref": item.verification_record_ref,
            "accepted_route_record_ref": f"accepted_routes.jsonl#{item.sequence}",
            "route_candidate_record_ref": item.route_candidate_record_ref,
            "rationale_summary": item.rationale_summary,
        }
        for item in sorted(materialized_routes, key=lambda entry: entry.source_drawer_id)
    ]

    return {
        "schema_name": APPLY_READY_MANIFEST_SCHEMA,
        "schema_version": 1,
        "run_id": resolved_run_id,
        "route_count": len(routes),
        "routes": routes,
        "skipped_summary": {
            "input_records": input_record_count,
            "skipped_records": int(sum(skipped_by_reason.values())),
            "skipped_by_reason": dict(sorted(skipped_by_reason.items())),
        },
    }


def _derive_decisions(
    records_list: list[Mapping[str, Any]],
    *,
    run_id: str,
    low_confidence_threshold: float,
) -> tuple[list[_DecisionTemplate], dict[str, Any]]:
    skipped_by_reason: Counter[str] = Counter()
    skipped_examples: list[dict[str, Any]] = []
    decisions: list[_DecisionTemplate] = []

    for record in records_list:
        normalized, skip_reason, skip_context = _normalize_verification_record(record)
        if normalized is None:
            skipped_by_reason[skip_reason or "invalid_record"] += 1
            _append_skipped_example(skipped_examples, skip_context)
            continue
        if normalized.run_id != run_id:
            skipped_by_reason["run_id_mismatch"] += 1
            _append_skipped_example(
                skipped_examples,
                {
                    "reason": "run_id_mismatch",
                    "source_drawer_id": normalized.source_drawer_id,
                    "verification_record_ref": normalized.verification_record_ref,
                },
            )
            continue

        decision, skip_reason, skip_context = _classify_decision(
            normalized,
            low_confidence_threshold=low_confidence_threshold,
        )
        if decision is None:
            skipped_by_reason[skip_reason or "invalid_record"] += 1
            _append_skipped_example(skipped_examples, skip_context)
            continue
        decisions.append(decision)

    skipped_summary = {
        "input_records": len(records_list),
        "accepted_records": sum(1 for decision in decisions if decision.kind == "accepted"),
        "unresolved_records": sum(1 for decision in decisions if decision.kind == "unresolved"),
        "skipped_records": int(sum(skipped_by_reason.values())),
        "skipped_by_reason": dict(sorted(skipped_by_reason.items())),
        "skipped_examples": skipped_examples,
    }
    return decisions, skipped_summary


def _classify_decision(
    record: _NormalizedVerificationRecord,
    *,
    low_confidence_threshold: float,
) -> tuple[_DecisionTemplate | None, str | None, dict[str, Any] | None]:
    if record.record_status == "invalid_model_output":
        reason_code = record.reason_code or "invalid_model_output"
        next_action = record.next_action or "retry_later"
        retryable = _coalesce_retryable(record.retryable, next_action=next_action, default=True)
        return (
            _build_unresolved_template(
                record,
                unresolved_status="invalid_model_output",
                reason_code=reason_code,
                reason_detail=record.reason_detail or "Verification record contained invalid model output.",
                next_action=next_action,
                retryable=retryable,
            ),
            None,
            None,
        )

    if record.record_status == "error":
        reason_code = record.reason_code or "error"
        next_action = record.next_action or "retry_later"
        retryable = _coalesce_retryable(record.retryable, next_action=next_action, default=True)
        return (
            _build_unresolved_template(
                record,
                unresolved_status="error",
                reason_code=reason_code,
                reason_detail=record.reason_detail or "Verification phase reported an error.",
                next_action=next_action,
                retryable=retryable,
            ),
            None,
            None,
        )

    if record.record_status != "ok":
        return None, "unsupported_record_status", {"record_status": record.record_status}

    if record.route_status == "accepted":
        if record.copy_ready is not True:
            return (
                _build_unresolved_template(
                    record,
                    unresolved_status="error",
                    reason_code="accepted_not_copy_ready",
                    reason_detail="Approved candidate route was not marked copy-ready.",
                    next_action="manual_review",
                    retryable=False,
                ),
                None,
                None,
            )
        if not isinstance(record.selected_candidate_id, str) or not record.selected_candidate_id:
            return None, "missing_selected_candidate_id", _skip_context(record)
        if not _is_slug(record.canonical_wing) or not _is_slug(record.canonical_room):
            return None, "invalid_canonical_slug", _skip_context(record)
        candidate_key = record.selected_candidate_key or f"{record.canonical_wing}:{record.canonical_room}"
        if candidate_key != f"{record.canonical_wing}:{record.canonical_room}":
            return None, "candidate_key_mismatch", _skip_context(record)
        if _is_low_confidence(record, threshold=low_confidence_threshold):
            reason_code, reason_detail = _low_confidence_reason(record, threshold=low_confidence_threshold)
            return (
                _build_unresolved_template(
                    record,
                    unresolved_status="low_confidence",
                    reason_code=reason_code,
                    reason_detail=reason_detail,
                    next_action="reroute",
                    retryable=True,
                ),
                None,
                None,
            )
        return (
            _build_accepted_template(
                record,
                candidate_key=candidate_key,
            ),
            None,
            None,
        )

    if record.route_status == "null_route":
        next_action = record.next_action or "manual_review"
        retryable = _coalesce_retryable(record.retryable, next_action=next_action, default=False)
        return (
            _build_unresolved_template(
                record,
                unresolved_status="null_route",
                reason_code=record.reason_code or "null_route",
                reason_detail=record.reason_detail or "Verifier approved a null route.",
                next_action=next_action,
                retryable=retryable,
            ),
            None,
            None,
        )

    if record.route_status == "verification_reject":
        unresolved_status = _classify_reject_status(record, threshold=low_confidence_threshold)
        next_action = record.next_action or _default_next_action(unresolved_status)
        retryable = _coalesce_retryable(
            record.retryable,
            next_action=next_action,
            default=next_action in {"reroute", "retry_later"},
        )
        reason_code = record.reason_code or unresolved_status
        reason_detail = (
            record.reason_detail
            or record.rationale_summary
            or record.route_rationale_summary
            or "Verifier rejected the proposed route."
        )
        return (
            _build_unresolved_template(
                record,
                unresolved_status=unresolved_status,
                reason_code=reason_code,
                reason_detail=reason_detail,
                next_action=next_action,
                retryable=retryable,
            ),
            None,
            None,
        )

    return None, "unsupported_route_status", _skip_context(record)


def _build_accepted_template(
    record: _NormalizedVerificationRecord,
    *,
    candidate_key: str,
) -> _DecisionTemplate:
    rationale_summary = (
        record.rationale_summary
        or record.route_rationale_summary
        or "Verified accepted candidate route."
    )
    materialized = {
        "schema_name": ACCEPTED_ROUTE_SCHEMA,
        "schema_version": 1,
        "run_id": record.run_id,
        "recorded_at": record.recorded_at,
        "route_status": "accepted",
        "route_iteration": record.route_iteration,
        "source_drawer_id": record.source_drawer_id,
        "source_wing": record.source_wing,
        "source_room": record.source_room,
        "candidate_id": record.selected_candidate_id,
        "candidate_key": candidate_key,
        "canonical_wing": record.canonical_wing,
        "canonical_room": record.canonical_room,
        "route_confidence": record.route_confidence,
        "verification_confidence": record.verification_confidence,
        "copy_ready": True,
        "route_record_ref": record.route_record_ref,
        "verification_record_ref": record.verification_record_ref,
        "route_candidate_record_ref": record.route_candidate_record_ref,
        "canonical_candidate_record_ref": record.canonical_candidate_record_ref,
        "rationale_summary": _truncate_text(rationale_summary),
    }
    if record.route_rationale_summary is not None:
        materialized["route_rationale_summary"] = _truncate_text(record.route_rationale_summary)
    if record.source_candidate_refs:
        materialized["source_candidate_refs"] = [dict(item) for item in record.source_candidate_refs]

    return _DecisionTemplate(
        kind="accepted",
        status="accepted",
        route_iteration=record.route_iteration,
        verification_sequence=record.sequence,
        source_drawer_id=record.source_drawer_id,
        reason_code=None,
        retryable=False,
        record=materialized,
    )


def _build_unresolved_template(
    record: _NormalizedVerificationRecord,
    *,
    unresolved_status: str,
    reason_code: str,
    reason_detail: str,
    next_action: str,
    retryable: bool,
) -> _DecisionTemplate:
    materialized = {
        "schema_name": UNRESOLVED_ROUTE_SCHEMA,
        "schema_version": 1,
        "run_id": record.run_id,
        "recorded_at": record.recorded_at,
        "route_iteration": record.route_iteration,
        "source_drawer_id": record.source_drawer_id,
        "source_wing": record.source_wing,
        "source_room": record.source_room,
        "unresolved_status": unresolved_status,
        "candidate_ids": _candidate_ids(record),
        "candidate_keys": _candidate_keys(record),
        "reason_code": reason_code,
        "reason_detail": _truncate_text(reason_detail),
        "route_confidence": record.route_confidence,
        "verification_confidence": record.verification_confidence,
        "next_action": next_action,
        "retryable": retryable,
        "route_record_ref": record.route_record_ref,
        "verification_record_ref": record.verification_record_ref,
        "route_candidate_record_ref": record.route_candidate_record_ref,
        "source_excerpt": record.source_excerpt,
    }
    if record.selected_candidate_id is not None:
        materialized["selected_candidate_id"] = record.selected_candidate_id
    if record.selected_candidate_key is not None:
        materialized["selected_candidate_key"] = record.selected_candidate_key
    if record.canonical_wing is not None:
        materialized["canonical_wing"] = record.canonical_wing
    if record.canonical_room is not None:
        materialized["canonical_room"] = record.canonical_room
    if record.rationale_summary is not None:
        materialized["rationale_summary"] = _truncate_text(record.rationale_summary)
    if record.route_rationale_summary is not None:
        materialized["route_rationale_summary"] = _truncate_text(record.route_rationale_summary)

    return _DecisionTemplate(
        kind="unresolved",
        status=unresolved_status,
        route_iteration=record.route_iteration,
        verification_sequence=record.sequence,
        source_drawer_id=record.source_drawer_id,
        reason_code=reason_code,
        retryable=retryable,
        record=materialized,
    )


def _normalize_verification_record(
    record: Mapping[str, Any],
) -> tuple[_NormalizedVerificationRecord | None, str | None, dict[str, Any] | None]:
    if not isinstance(record, Mapping):
        return None, "record_not_mapping", {"reason": "record_not_mapping"}

    raw_run_id = record.get("run_id")
    if not isinstance(raw_run_id, str) or not raw_run_id.strip():
        return None, "missing_run_id", {"reason": "missing_run_id"}
    try:
        resolved_run_id = validate_run_id(raw_run_id)
    except ValueError:
        return None, "invalid_run_id", {"reason": "invalid_run_id", "run_id": raw_run_id}

    phase = record.get("phase")
    if phase is not None and phase != _ROUTE_VERIFY_PHASE:
        return None, "invalid_phase", {"reason": "invalid_phase", "phase": phase}

    sequence = record.get("sequence")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
        return None, "invalid_sequence", {"reason": "invalid_sequence", "sequence": sequence}

    attempt = record.get("attempt")
    if not isinstance(attempt, int) or isinstance(attempt, bool) or attempt < 1:
        return None, "invalid_attempt", {"reason": "invalid_attempt", "attempt": attempt}

    recorded_at = record.get("recorded_at")
    if not isinstance(recorded_at, str) or not recorded_at.strip():
        return None, "invalid_recorded_at", {"reason": "invalid_recorded_at", "sequence": sequence}

    source = record.get("source")
    if not isinstance(source, Mapping):
        return None, "missing_source", {"reason": "missing_source", "sequence": sequence}
    source_drawer_id = _strip_string(source.get("drawer_id"))
    source_wing = _strip_string(source.get("wing"))
    source_room = _strip_string(source.get("room"))
    if source_drawer_id is None or source_wing is None or source_room is None:
        return None, "invalid_source", {"reason": "invalid_source", "sequence": sequence}

    record_status = _strip_string(record.get("record_status"))
    if record_status is None:
        return None, "missing_record_status", {"reason": "missing_record_status", "sequence": sequence}

    payload = record.get("payload")
    if not isinstance(payload, Mapping):
        return None, "missing_payload", {"reason": "missing_payload", "sequence": sequence}

    route_iteration = payload.get("route_iteration", attempt)
    if not isinstance(route_iteration, int) or isinstance(route_iteration, bool) or route_iteration < 1:
        return None, "invalid_route_iteration", {"reason": "invalid_route_iteration", "sequence": sequence}
    if route_iteration != attempt:
        return None, "route_iteration_mismatch", {"reason": "route_iteration_mismatch", "sequence": sequence}

    next_action = _normalize_next_action(payload.get("next_action", payload.get("route_next_action")))
    if payload.get("next_action", payload.get("route_next_action")) is not None and next_action is None:
        return None, "invalid_next_action", {"reason": "invalid_next_action", "sequence": sequence}

    route_confidence = _coerce_confidence(payload.get("route_confidence"))
    if payload.get("route_confidence") is not None and route_confidence is None:
        return None, "invalid_route_confidence", {"reason": "invalid_route_confidence", "sequence": sequence}
    verification_confidence = _coerce_confidence(payload.get("verification_confidence"))
    if payload.get("verification_confidence") is not None and verification_confidence is None:
        return (
            None,
            "invalid_verification_confidence",
            {"reason": "invalid_verification_confidence", "sequence": sequence},
        )

    canonical_wing = _strip_string(payload.get("canonical_wing"))
    canonical_room = _strip_string(payload.get("canonical_room"))
    selected_candidate_key = _strip_string(payload.get("selected_candidate_key"))
    if selected_candidate_key is None and canonical_wing is not None and canonical_room is not None:
        selected_candidate_key = f"{canonical_wing}:{canonical_room}"

    route_record_ref = _strip_string(payload.get("route_record_ref")) or f"{_ROUTE_PASS2_PHASE}.jsonl#{sequence}"
    route_candidate_record_ref = _strip_string(payload.get("route_candidate_record_ref"))
    verification_record_ref = f"{_ROUTE_VERIFY_PHASE}.jsonl#{sequence}"

    reason_code = (
        _strip_string(payload.get("reason_code"))
        or _strip_string(payload.get("error_code"))
        or _strip_string(payload.get("route_reason_code"))
    )
    reason_detail = (
        _strip_string(payload.get("reason_detail"))
        or _strip_string(payload.get("raw_response_excerpt"))
        or _strip_string(payload.get("route_reason_detail"))
    )
    source_excerpt = _bounded_optional_text(payload.get("drawer_excerpt"))
    rationale_summary = _bounded_optional_text(payload.get("rationale_summary"))
    route_rationale_summary = _bounded_optional_text(payload.get("route_rationale_summary"))
    retryable = payload.get("retryable")
    if retryable is not None and not isinstance(retryable, bool):
        return None, "invalid_retryable", {"reason": "invalid_retryable", "sequence": sequence}

    shortlist_candidate_ids = _string_list(payload.get("shortlist_candidate_ids"))
    shortlist_candidate_keys = _string_list(payload.get("shortlist_candidate_keys"))
    source_candidate_refs = _mapping_list(payload.get("source_candidate_refs"))

    return (
        _NormalizedVerificationRecord(
            run_id=resolved_run_id,
            sequence=sequence,
            attempt=attempt,
            route_iteration=route_iteration,
            recorded_at=recorded_at.strip(),
            source_drawer_id=source_drawer_id,
            source_wing=source_wing,
            source_room=source_room,
            record_status=record_status,
            route_status=_strip_string(payload.get("route_status")),
            copy_ready=payload.get("copy_ready") if isinstance(payload.get("copy_ready"), bool) else None,
            selected_candidate_id=_strip_string(payload.get("selected_candidate_id", payload.get("candidate_id"))),
            selected_candidate_key=selected_candidate_key,
            canonical_wing=canonical_wing,
            canonical_room=canonical_room,
            canonical_candidate_record_ref=_strip_string(payload.get("canonical_candidate_record_ref")),
            route_record_ref=route_record_ref,
            verification_record_ref=verification_record_ref,
            route_candidate_record_ref=route_candidate_record_ref,
            route_confidence=route_confidence,
            verification_confidence=verification_confidence,
            rationale_summary=rationale_summary,
            route_rationale_summary=route_rationale_summary,
            reason_code=reason_code,
            reason_detail=reason_detail,
            next_action=next_action,
            retryable=retryable,
            source_excerpt=source_excerpt,
            shortlist_candidate_ids=shortlist_candidate_ids,
            shortlist_candidate_keys=shortlist_candidate_keys,
            source_candidate_refs=source_candidate_refs,
        ),
        None,
        None,
    )


def _normalize_accepted_route_record(record: Mapping[str, Any]) -> _NormalizedAcceptedRoute | None:
    if not isinstance(record, Mapping):
        return None
    if record.get("schema_name") not in (None, ACCEPTED_ROUTE_SCHEMA):
        return None
    try:
        run_id = validate_run_id(_require_string(record.get("run_id")))
        sequence = _require_positive_int(record.get("sequence"))
        route_iteration = _require_positive_int(record.get("route_iteration"))
        source_drawer_id = _require_string(record.get("source_drawer_id"))
        source_wing = _require_string(record.get("source_wing"))
        source_room = _require_string(record.get("source_room"))
        candidate_id = _require_string(record.get("candidate_id"))
        canonical_wing = _require_slug(record.get("canonical_wing"))
        canonical_room = _require_slug(record.get("canonical_room"))
        candidate_key = _strip_string(record.get("candidate_key")) or f"{canonical_wing}:{canonical_room}"
        if candidate_key != f"{canonical_wing}:{canonical_room}":
            return None
        if record.get("route_status") != "accepted":
            return None
        if record.get("copy_ready") is not True:
            return None
        route_record_ref = _require_string(record.get("route_record_ref"))
        verification_record_ref = _require_string(record.get("verification_record_ref"))
        recorded_at = _require_string(record.get("recorded_at"))
        route_confidence = _coerce_confidence(record.get("route_confidence"))
        if record.get("route_confidence") is not None and route_confidence is None:
            return None
        verification_confidence = _coerce_confidence(record.get("verification_confidence"))
        if record.get("verification_confidence") is not None and verification_confidence is None:
            return None
        rationale_summary = _bounded_optional_text(record.get("rationale_summary")) or ""
        route_candidate_record_ref = _strip_string(record.get("route_candidate_record_ref"))
    except (TypeError, ValueError):
        return None

    return _NormalizedAcceptedRoute(
        run_id=run_id,
        sequence=sequence,
        route_iteration=route_iteration,
        source_drawer_id=source_drawer_id,
        source_wing=source_wing,
        source_room=source_room,
        candidate_id=candidate_id,
        candidate_key=candidate_key,
        canonical_wing=canonical_wing,
        canonical_room=canonical_room,
        route_confidence=route_confidence,
        verification_confidence=verification_confidence,
        route_record_ref=route_record_ref,
        verification_record_ref=verification_record_ref,
        route_candidate_record_ref=route_candidate_record_ref,
        recorded_at=recorded_at,
        rationale_summary=rationale_summary,
    )


def _normalize_unresolved_route_record(record: Mapping[str, Any]) -> _NormalizedUnresolvedRoute | None:
    if not isinstance(record, Mapping):
        return None
    if record.get("schema_name") not in (None, UNRESOLVED_ROUTE_SCHEMA):
        return None
    try:
        run_id = validate_run_id(_require_string(record.get("run_id")))
        sequence = _require_positive_int(record.get("sequence"))
        route_iteration = _require_positive_int(record.get("route_iteration"))
        source_drawer_id = _require_string(record.get("source_drawer_id"))
        source_wing = _require_string(record.get("source_wing"))
        source_room = _require_string(record.get("source_room"))
        unresolved_status = _require_string(record.get("unresolved_status"))
        reason_code = _require_string(record.get("reason_code"))
        reason_detail = _require_string(record.get("reason_detail"))
        route_record_ref = _require_string(record.get("route_record_ref"))
        verification_record_ref = _require_string(record.get("verification_record_ref"))
        next_action = _require_string(record.get("next_action"))
        if next_action not in _VALID_NEXT_ACTIONS:
            return None
        retryable = record.get("retryable")
        if not isinstance(retryable, bool):
            return None
        route_confidence = _coerce_confidence(record.get("route_confidence"))
        if record.get("route_confidence") is not None and route_confidence is None:
            return None
        verification_confidence = _coerce_confidence(record.get("verification_confidence"))
        if record.get("verification_confidence") is not None and verification_confidence is None:
            return None
        candidate_ids = _string_list(record.get("candidate_ids"))
        candidate_keys = _string_list(record.get("candidate_keys"))
        source_excerpt = _bounded_optional_text(record.get("source_excerpt"))
        recorded_at = _require_string(record.get("recorded_at"))
    except (TypeError, ValueError):
        return None

    return _NormalizedUnresolvedRoute(
        run_id=run_id,
        sequence=sequence,
        route_iteration=route_iteration,
        source_drawer_id=source_drawer_id,
        source_wing=source_wing,
        source_room=source_room,
        unresolved_status=unresolved_status,
        candidate_ids=candidate_ids,
        candidate_keys=candidate_keys,
        reason_code=reason_code,
        reason_detail=_truncate_text(reason_detail),
        route_confidence=route_confidence,
        verification_confidence=verification_confidence,
        next_action=next_action,
        retryable=retryable,
        route_record_ref=route_record_ref,
        verification_record_ref=verification_record_ref,
        source_excerpt=source_excerpt,
        recorded_at=recorded_at,
    )


def _accepted_terminal_entry(record: _NormalizedAcceptedRoute) -> dict[str, Any]:
    return {
        "order_key": _decision_order_key(
            record.route_iteration,
            _ref_sequence(record.verification_record_ref),
            record.sequence,
        ),
        "source_drawer_id": record.source_drawer_id,
        "source_wing": record.source_wing,
        "source_room": record.source_room,
        "route_iteration": record.route_iteration,
        "status": "accepted",
        "candidate_ids": [record.candidate_id],
        "candidate_keys": [record.candidate_key],
        "reason_code": None,
        "reason_detail": None,
        "route_confidence": record.route_confidence,
        "verification_confidence": record.verification_confidence,
        "next_action": None,
        "retryable": False,
        "route_record_ref": record.route_record_ref,
        "verification_record_ref": record.verification_record_ref,
        "source_excerpt": None,
    }


def _unresolved_terminal_entry(record: _NormalizedUnresolvedRoute) -> dict[str, Any]:
    return {
        "order_key": _decision_order_key(
            record.route_iteration,
            _ref_sequence(record.verification_record_ref),
            record.sequence,
        ),
        "source_drawer_id": record.source_drawer_id,
        "source_wing": record.source_wing,
        "source_room": record.source_room,
        "route_iteration": record.route_iteration,
        "status": record.unresolved_status,
        "candidate_ids": list(record.candidate_ids),
        "candidate_keys": list(record.candidate_keys),
        "reason_code": record.reason_code,
        "reason_detail": record.reason_detail,
        "route_confidence": record.route_confidence,
        "verification_confidence": record.verification_confidence,
        "next_action": record.next_action,
        "retryable": record.retryable,
        "route_record_ref": record.route_record_ref,
        "verification_record_ref": record.verification_record_ref,
        "source_excerpt": record.source_excerpt,
    }


def _update_latest_terminal(
    latest_by_drawer: dict[str, tuple[tuple[int, int, int], dict[str, Any]]],
    entry: dict[str, Any],
) -> None:
    order_key = entry["order_key"]
    drawer_id = entry["source_drawer_id"]
    existing = latest_by_drawer.get(drawer_id)
    if existing is None or order_key > existing[0]:
        latest_by_drawer[drawer_id] = (order_key, entry)


def _classify_reject_status(
    record: _NormalizedVerificationRecord,
    *,
    threshold: float,
) -> str:
    combined = " ".join(
        part
        for part in (
            record.reason_code,
            record.reason_detail,
            record.rationale_summary,
            record.route_rationale_summary,
        )
        if isinstance(part, str) and part
    ).lower()
    if _is_low_confidence(record, threshold=threshold):
        return "low_confidence"
    if any(token in combined for token in ("conflict", "disagree", "mixed", "overlap", "ambiguous")):
        return "conflict"
    if any(
        token in combined
        for token in ("candidate_gap", "shortlist", "reroute", "no_clear_match", "retry_with_shortlist")
    ):
        return "candidate_gap"
    return "verification_reject"


def _candidate_ids(record: _NormalizedVerificationRecord) -> list[str]:
    ordered: list[str] = []
    if record.selected_candidate_id is not None:
        ordered.append(record.selected_candidate_id)
    ordered.extend(record.shortlist_candidate_ids)
    return _dedupe_strings(ordered)


def _candidate_keys(record: _NormalizedVerificationRecord) -> list[str]:
    ordered: list[str] = []
    if record.selected_candidate_key is not None:
        ordered.append(record.selected_candidate_key)
    ordered.extend(record.shortlist_candidate_keys)
    return _dedupe_strings(ordered)


def _coalesce_retryable(
    explicit: bool | None,
    *,
    next_action: str,
    default: bool,
) -> bool:
    if explicit is not None:
        return explicit
    if next_action in {"reroute", "retry_later"}:
        return True
    if next_action in {"manual_review", "drop"}:
        return False
    return default


def _default_next_action(unresolved_status: str) -> str:
    if unresolved_status in {"candidate_gap", "low_confidence", "invalid_model_output", "error"}:
        return "reroute" if unresolved_status in {"candidate_gap", "low_confidence"} else "retry_later"
    return "manual_review"


def _low_confidence_reason(
    record: _NormalizedVerificationRecord,
    *,
    threshold: float,
) -> tuple[str, str]:
    if record.verification_confidence is not None and record.verification_confidence < threshold:
        return (
            "verification_confidence_below_threshold",
            f"Verification confidence {record.verification_confidence:.2f} is below {threshold:.2f}.",
        )
    if record.route_confidence is not None and record.route_confidence < threshold:
        return (
            "route_confidence_below_threshold",
            f"Route confidence {record.route_confidence:.2f} is below {threshold:.2f}.",
        )
    return ("low_confidence", "Route confidence evidence was too weak to converge.")


def _is_low_confidence(record: _NormalizedVerificationRecord, *, threshold: float) -> bool:
    return any(
        value is not None and value < threshold
        for value in (record.route_confidence, record.verification_confidence)
    )


def _resolve_run_id(records: Iterable[Mapping[str, Any]], *, run_id: str | None) -> str:
    if run_id is not None:
        return validate_run_id(run_id)
    for record in records:
        if not isinstance(record, Mapping):
            continue
        candidate = record.get("run_id")
        if isinstance(candidate, str) and candidate.strip():
            try:
                return validate_run_id(candidate)
            except ValueError:
                continue
    raise ValueError("run_id is required when it cannot be inferred from input records")


def _validate_threshold(threshold: float) -> float:
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
        raise ValueError("low_confidence_threshold must be a number between 0 and 1")
    threshold = float(threshold)
    if threshold < 0 or threshold > 1:
        raise ValueError("low_confidence_threshold must be a number between 0 and 1")
    return threshold


def _decision_order_key(route_iteration: int, verification_sequence: int | None, sequence: int) -> tuple[int, int, int]:
    return (route_iteration, verification_sequence or 0, sequence)


def _ref_sequence(record_ref: str) -> int | None:
    match = _REF_SEQUENCE_RE.search(record_ref)
    if match is None:
        return None
    return int(match.group(1))


def _dedupe_strings(items: Iterable[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def _normalize_next_action(value: Any) -> str | None:
    value = _strip_string(value)
    if value is None:
        return None
    if value not in _VALID_NEXT_ACTIONS:
        return None
    return value


def _coerce_confidence(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    confidence = float(value)
    if confidence < 0 or confidence > 1:
        return None
    return confidence


def _strip_string(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _mapping_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _bounded_optional_text(value: Any) -> str | None:
    value = _strip_string(value)
    if value is None:
        return None
    return _truncate_text(value)


def _truncate_text(value: str, limit: int = 240) -> str:
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 3)] + "..."


def _is_slug(value: str | None) -> bool:
    return isinstance(value, str) and bool(_SLUG_RE.match(value))


def _require_string(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("value must be a non-empty string")
    return value.strip()


def _require_positive_int(value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError("value must be a positive integer")
    return value


def _require_slug(value: Any) -> str:
    value = _require_string(value)
    if not _is_slug(value):
        raise ValueError("value must be a lowercase slug")
    return value


def _append_skipped_example(examples: list[dict[str, Any]], value: dict[str, Any] | None) -> None:
    if value is not None and len(examples) < 10:
        examples.append(value)


def _skip_context(record: _NormalizedVerificationRecord) -> dict[str, Any]:
    return {
        "source_drawer_id": record.source_drawer_id,
        "verification_record_ref": record.verification_record_ref,
        "route_iteration": record.route_iteration,
    }
