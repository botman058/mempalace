from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from . import chatgpt_archive_atlas_contract as atlas_contract
from . import chatgpt_atlas_guided_contract as guided_contract


@dataclass(frozen=True)
class ChatGPTAtlasGuidedCoverageResult:
    rows: tuple[dict[str, Any], ...]
    report: dict[str, Any]


@dataclass(frozen=True)
class _BridgeRecord:
    input_index: int
    run_id: str
    atlas_run_id: str
    cluster_id: str
    bridge_status: str
    candidate_id: str | None
    candidate_key: str | None
    thread_ids: tuple[str, ...]


@dataclass(frozen=True)
class _ThreadIndexRecord:
    input_index: int
    atlas_run_id: str
    thread_id: str
    source_thread_ref: str


@dataclass(frozen=True)
class _ThreadMembership:
    cluster_id: str
    bridge_status: str
    candidate_id: str | None
    candidate_key: str | None


def build_chatgpt_atlas_guided_coverage_rows(
    candidate_bridge_rows: Iterable[Mapping[str, Any]],
    thread_index_rows: Iterable[Mapping[str, Any]],
    *,
    run_id: str,
    atlas_run_id: str | None = None,
) -> tuple[dict[str, Any], ...]:
    return build_chatgpt_atlas_guided_coverage(
        candidate_bridge_rows,
        thread_index_rows,
        run_id=run_id,
        atlas_run_id=atlas_run_id,
    ).rows


def build_chatgpt_atlas_guided_coverage(
    candidate_bridge_rows: Iterable[Mapping[str, Any]],
    thread_index_rows: Iterable[Mapping[str, Any]],
    *,
    run_id: str,
    atlas_run_id: str | None = None,
) -> ChatGPTAtlasGuidedCoverageResult:
    bridge_records, bridge_atlas_run_ids = _normalize_bridge_rows(candidate_bridge_rows, run_id=run_id)
    thread_records, thread_atlas_run_ids = _normalize_thread_rows(thread_index_rows)

    resolved_atlas_run_id = _resolve_atlas_run_id(
        requested_atlas_run_id=atlas_run_id,
        bridge_atlas_run_ids=bridge_atlas_run_ids,
        thread_atlas_run_ids=thread_atlas_run_ids,
    )
    _validate_atlas_run_id_alignment(
        bridge_records=bridge_records,
        thread_records=thread_records,
        atlas_run_id=resolved_atlas_run_id,
    )

    memberships_by_thread: dict[str, list[_ThreadMembership]] = defaultdict(list)
    bridge_status_counts: Counter[str] = Counter()
    candidate_ids: dict[str, None] = {}
    cluster_ids: dict[str, None] = {}

    for record in bridge_records:
        cluster_ids.setdefault(record.cluster_id, None)
        bridge_status_counts[record.bridge_status] += 1
        if record.candidate_id is not None:
            candidate_ids.setdefault(record.candidate_id, None)
        for thread_id in record.thread_ids:
            memberships_by_thread[thread_id].append(
                _ThreadMembership(
                    cluster_id=record.cluster_id,
                    bridge_status=record.bridge_status,
                    candidate_id=record.candidate_id,
                    candidate_key=record.candidate_key,
                )
            )

    duplicate_thread_refs = _build_duplicate_thread_refs(memberships_by_thread)
    thread_ids_in_index = {record.thread_id for record in thread_records}
    missing_thread_refs = [
        thread_id
        for thread_id in memberships_by_thread
        if thread_id not in thread_ids_in_index
    ]

    rows = tuple(
        _build_lookup_row(
            thread_record=record,
            memberships=memberships_by_thread.get(record.thread_id, []),
            run_id=run_id,
            atlas_run_id=resolved_atlas_run_id,
        )
        for record in thread_records
    )
    lookup_status_counts = Counter(str(row["lookup_status"]) for row in rows)
    report = _build_coverage_report(
        run_id=run_id,
        atlas_run_id=resolved_atlas_run_id,
        rows=rows,
        bridge_record_count=len(bridge_records),
        bridge_status_counts=bridge_status_counts,
        candidate_count=len(candidate_ids),
        cluster_count=len(cluster_ids),
        duplicate_thread_refs=duplicate_thread_refs,
        missing_thread_refs=missing_thread_refs,
        bridge_thread_ref_count=len(memberships_by_thread),
        thread_index_row_count=len(thread_records),
        lookup_status_counts=lookup_status_counts,
    )
    return ChatGPTAtlasGuidedCoverageResult(rows=rows, report=report)


def _normalize_bridge_rows(
    candidate_bridge_rows: Iterable[Mapping[str, Any]],
    *,
    run_id: str,
) -> tuple[tuple[_BridgeRecord, ...], frozenset[str]]:
    records: list[_BridgeRecord] = []
    seen_atlas_run_ids: set[str] = set()

    for index, raw_row in enumerate(candidate_bridge_rows):
        if not isinstance(raw_row, Mapping):
            raise ValueError(
                f"candidate bridge row {index} must be a mapping, got {type(raw_row).__name__}"
            )
        validated = guided_contract.validate_row(guided_contract.CANDIDATE_BRIDGE_RECORD_SCHEMA, raw_row)
        if validated.get("run_id") != run_id:
            raise ValueError("candidate_bridge_rows run_id does not match run_id")
        row_atlas_run_id = _require_nonempty_str("atlas_run_id", validated.get("atlas_run_id"))
        seen_atlas_run_ids.add(row_atlas_run_id)
        records.append(
            _BridgeRecord(
                input_index=index,
                run_id=run_id,
                atlas_run_id=row_atlas_run_id,
                cluster_id=_require_nonempty_str("atlas_cluster_id", validated.get("atlas_cluster_id")),
                bridge_status=_require_lookup_status(
                    "bridge_status",
                    validated.get("bridge_status"),
                    guided_contract.CANDIDATE_BRIDGE_STATUSES,
                ),
                candidate_id=_optional_nonempty_str(validated.get("candidate_id")),
                candidate_key=_optional_nonempty_str(validated.get("candidate_key")),
                thread_ids=_dedupe_string_list(validated.get("thread_ids")),
            )
        )
    return tuple(records), frozenset(seen_atlas_run_ids)


def _normalize_thread_rows(
    thread_index_rows: Iterable[Mapping[str, Any]],
) -> tuple[tuple[_ThreadIndexRecord, ...], frozenset[str]]:
    records: list[_ThreadIndexRecord] = []
    seen_atlas_run_ids: set[str] = set()
    seen_thread_ids: set[str] = set()

    for index, raw_row in enumerate(thread_index_rows):
        if not isinstance(raw_row, Mapping):
            raise ValueError(
                f"thread index row {index} must be a mapping, got {type(raw_row).__name__}"
            )
        validated = atlas_contract.validate_row(atlas_contract.THREAD_INDEX_SCHEMA, raw_row)
        row_atlas_run_id = _require_nonempty_str("run_id", validated.get("run_id"))
        thread_id = _require_nonempty_str("thread_id", validated.get("thread_id"))
        if thread_id in seen_thread_ids:
            raise ValueError(f"duplicate thread_id in thread_index_rows: {thread_id}")
        seen_thread_ids.add(thread_id)
        seen_atlas_run_ids.add(row_atlas_run_id)
        records.append(
            _ThreadIndexRecord(
                input_index=index,
                atlas_run_id=row_atlas_run_id,
                thread_id=thread_id,
                source_thread_ref=f"thread_index.jsonl#{index + 1}",
            )
        )
    return tuple(records), frozenset(seen_atlas_run_ids)


def _resolve_atlas_run_id(
    *,
    requested_atlas_run_id: str | None,
    bridge_atlas_run_ids: frozenset[str],
    thread_atlas_run_ids: frozenset[str],
) -> str:
    if requested_atlas_run_id is not None:
        return requested_atlas_run_id
    seen = set(bridge_atlas_run_ids)
    seen.update(thread_atlas_run_ids)
    if not seen:
        raise ValueError(
            "atlas_run_id is required when candidate_bridge_rows and thread_index_rows are empty"
        )
    if len(seen) != 1:
        raise ValueError("candidate_bridge_rows and thread_index_rows must belong to one atlas_run_id")
    return next(iter(seen))


def _validate_atlas_run_id_alignment(
    *,
    bridge_records: tuple[_BridgeRecord, ...],
    thread_records: tuple[_ThreadIndexRecord, ...],
    atlas_run_id: str,
) -> None:
    for record in bridge_records:
        if record.atlas_run_id != atlas_run_id:
            raise ValueError("candidate_bridge_rows atlas_run_id does not match atlas_run_id")
    for record in thread_records:
        if record.atlas_run_id != atlas_run_id:
            raise ValueError("thread_index_rows run_id does not match atlas_run_id")


def _build_duplicate_thread_refs(
    memberships_by_thread: Mapping[str, list[_ThreadMembership]],
) -> list[dict[str, Any]]:
    duplicates: list[dict[str, Any]] = []
    for thread_id, memberships in memberships_by_thread.items():
        unique_cluster_ids = _unique_cluster_ids(memberships)
        if len(unique_cluster_ids) <= 1:
            continue
        duplicates.append({"thread_id": thread_id, "cluster_ids": unique_cluster_ids})
    return duplicates


def _build_lookup_row(
    *,
    thread_record: _ThreadIndexRecord,
    memberships: list[_ThreadMembership],
    run_id: str,
    atlas_run_id: str,
) -> dict[str, Any]:
    lookup_status = _lookup_status_for_memberships(memberships)
    cluster_ids = _unique_cluster_ids(memberships)
    candidate_pairs = _unique_candidate_pairs(memberships)
    candidate_ids = [candidate_id for candidate_id, _candidate_key in candidate_pairs]
    candidate_keys = [candidate_key for _candidate_id, candidate_key in candidate_pairs]

    if lookup_status in {"noise", "unmapped"}:
        candidate_ids = []
        candidate_keys = []

    primary_candidate_id = candidate_ids[0] if candidate_ids else None
    primary_candidate_key = candidate_keys[0] if candidate_keys else None
    return guided_contract.build_thread_candidate_record(
        run_id=run_id,
        atlas_run_id=atlas_run_id,
        thread_id=thread_record.thread_id,
        lookup_status=lookup_status,
        candidate_ids=candidate_ids,
        candidate_keys=candidate_keys,
        cluster_ids=cluster_ids,
        primary_candidate_id=primary_candidate_id,
        primary_candidate_key=primary_candidate_key,
        reason_codes=_reason_codes_for_memberships(memberships, lookup_status=lookup_status),
        source_thread_ref=thread_record.source_thread_ref,
    )


def _lookup_status_for_memberships(memberships: list[_ThreadMembership]) -> str:
    if not memberships:
        return "unmapped"
    statuses = {membership.bridge_status for membership in memberships}
    if statuses == {"candidate"}:
        return "mapped"
    if statuses == {"noise"}:
        return "noise"
    return "mixed"


def _reason_codes_for_memberships(
    memberships: list[_ThreadMembership],
    *,
    lookup_status: str,
) -> list[str]:
    if not memberships:
        return ["not_in_candidate_bridge"]

    statuses = {membership.bridge_status for membership in memberships}
    codes: list[str] = []
    if "candidate" in statuses:
        codes.append("candidate_cluster_member")
    if "mixed" in statuses:
        codes.append("mixed_cluster_member")
    if "noise" in statuses:
        codes.append("noise_cluster_member")
    if lookup_status == "mixed" and not any(membership.candidate_id for membership in memberships):
        codes.append("mixed_without_candidate_identity")
    if len(_unique_cluster_ids(memberships)) > 1:
        codes.append("duplicate_bridge_thread_ref")
    return codes


def _build_coverage_report(
    *,
    run_id: str,
    atlas_run_id: str,
    rows: tuple[dict[str, Any], ...],
    bridge_record_count: int,
    bridge_status_counts: Counter[str],
    candidate_count: int,
    cluster_count: int,
    duplicate_thread_refs: list[dict[str, Any]],
    missing_thread_refs: list[str],
    bridge_thread_ref_count: int,
    thread_index_row_count: int,
    lookup_status_counts: Counter[str],
) -> dict[str, Any]:
    mapped_threads = lookup_status_counts.get("mapped", 0)
    mixed_threads = lookup_status_counts.get("mixed", 0)
    noise_threads = lookup_status_counts.get("noise", 0)
    unmapped_threads = lookup_status_counts.get("unmapped", 0)
    status = "complete"
    if (
        mixed_threads
        or noise_threads
        or unmapped_threads
        or duplicate_thread_refs
        or missing_thread_refs
    ):
        status = "needs_review"

    return guided_contract.build_candidate_coverage_report(
        run_id=run_id,
        atlas_run_id=atlas_run_id,
        status=status,
        total_threads=len(rows),
        mapped_threads=mapped_threads,
        mixed_threads=mixed_threads,
        noise_threads=noise_threads,
        unmapped_threads=unmapped_threads,
        candidate_count=candidate_count,
        cluster_count=cluster_count,
        duplicate_thread_refs=duplicate_thread_refs,
        missing_thread_refs=missing_thread_refs,
        counts={
            "bridge_records": bridge_record_count,
            "bridge_thread_refs": bridge_thread_ref_count,
            "candidate_bridge_records": bridge_status_counts.get("candidate", 0),
            "duplicate_thread_ref_count": len(duplicate_thread_refs),
            "mapped_threads": mapped_threads,
            "missing_thread_ref_count": len(missing_thread_refs),
            "mixed_bridge_records": bridge_status_counts.get("mixed", 0),
            "mixed_threads": mixed_threads,
            "noise_bridge_records": bridge_status_counts.get("noise", 0),
            "noise_threads": noise_threads,
            "thread_index_rows": thread_index_row_count,
            "unmapped_threads": unmapped_threads,
        },
    )


def _unique_candidate_pairs(
    memberships: list[_ThreadMembership],
) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for membership in memberships:
        if membership.candidate_id is None or membership.candidate_key is None:
            continue
        pair = (membership.candidate_id, membership.candidate_key)
        if pair in seen:
            continue
        seen.add(pair)
        pairs.append(pair)
    return pairs


def _unique_cluster_ids(memberships: list[_ThreadMembership]) -> list[str]:
    cluster_ids: list[str] = []
    seen: set[str] = set()
    for membership in memberships:
        if membership.cluster_id in seen:
            continue
        seen.add(membership.cluster_id)
        cluster_ids.append(membership.cluster_id)
    return cluster_ids


def _dedupe_string_list(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"thread_ids must be a list, got {type(value).__name__}")
    items: list[str] = []
    seen: set[str] = set()
    for item in value:
        text = _require_nonempty_str("thread_id", item)
        if text in seen:
            continue
        seen.add(text)
        items.append(text)
    return tuple(items)


def _require_lookup_status(name: str, value: Any, allowed: frozenset[str]) -> str:
    if not isinstance(value, str) or value not in allowed:
        allowed_values = ", ".join(sorted(allowed))
        raise ValueError(f"{name} must be one of: {allowed_values}")
    return value


def _require_nonempty_str(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _optional_nonempty_str(value: Any) -> str | None:
    if value is None:
        return None
    return _require_nonempty_str("value", value)
