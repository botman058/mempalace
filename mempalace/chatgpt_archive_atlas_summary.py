from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from . import chatgpt_archive_atlas_contract as contract

_MAX_DISPLAY_CLUSTERS_PER_STATUS = 12
_MAX_ERROR_CODES = 8
_MAX_ERROR_EXAMPLES = 8
_MAX_EVIDENCE_TITLES = 3
_MAX_TOP_TERMS = 5
_MAX_EXCERPTS = 2
_MAX_MIXED_REASONS = 4


@dataclass(frozen=True)
class ChatGPTAtlasSummaryResult:
    markdown: str
    manifest: dict[str, Any]
    relative_path: str
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class _ClusterRecord:
    cluster_id: str
    status: str
    topic_label: Optional[str]
    size: int
    thread_ids: tuple[str, ...]
    evidence_titles: tuple[str, ...]
    top_terms: tuple[tuple[str, int], ...]
    representative_excerpts: tuple[str, ...]
    mixed_reasons: tuple[str, ...]
    candidate_wing: Optional[str]
    candidate_room: Optional[str]
    cluster_score: Optional[float]


def build_chatgpt_atlas_summary(
    topic_cluster_rows,
    *,
    run_id: str,
    source_counts: Mapping[str, int] | None = None,
    source_errors: Sequence[Mapping[str, Any]] | None = None,
    relative_path: str = "atlas_summary.md",
) -> ChatGPTAtlasSummaryResult:
    records, warnings = _normalize_cluster_rows(topic_cluster_rows)
    source_error_rows = _normalize_source_errors(source_errors or (), warnings)
    _append_summary_warnings(records, source_error_rows, warnings)

    records = tuple(sorted(records, key=_cluster_sort_key))
    shown_by_status, hidden_counts = _select_display_clusters(records)
    counts = _build_counts(records, source_counts or {}, source_error_rows, warnings, hidden_counts)

    sections = [
        "overview",
        "candidate_wings_rooms",
        "cluster_sizes",
        "evidence_titles",
        "top_terms",
        "representative_excerpts",
        "mixed_noisy_clusters",
        "source_error_summary",
    ]
    markdown = _build_markdown(
        run_id=run_id,
        records=records,
        shown_by_status=shown_by_status,
        hidden_counts=hidden_counts,
        source_counts=source_counts or {},
        source_error_rows=source_error_rows,
        warnings=warnings,
    )
    manifest = contract.build_atlas_summary_manifest(
        run_id=run_id,
        relative_path=relative_path,
        status="complete",
        source_schema_names=[contract.TOPIC_CLUSTER_SCHEMA],
        sections=sections,
        counts=counts,
    )
    return ChatGPTAtlasSummaryResult(
        markdown=markdown,
        manifest=manifest,
        relative_path=str(manifest["relative_path"]),
        warnings=tuple(warnings),
    )


def write_chatgpt_atlas_summary(
    topic_cluster_rows,
    run_dir,
    *,
    run_id: str,
    source_counts: Mapping[str, int] | None = None,
    source_errors: Sequence[Mapping[str, Any]] | None = None,
    relative_path: str = "atlas_summary.md",
) -> ChatGPTAtlasSummaryResult:
    result = build_chatgpt_atlas_summary(
        topic_cluster_rows,
        run_id=run_id,
        source_counts=source_counts,
        source_errors=source_errors,
        relative_path=relative_path,
    )
    root = Path(run_dir).resolve()
    output_path = (root / result.relative_path).resolve()
    try:
        output_path.relative_to(root)
    except ValueError as exc:
        raise ValueError("relative_path must resolve inside run_dir") from exc
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result.markdown, encoding="utf-8")
    return result


def _normalize_cluster_rows(
    topic_cluster_rows,
) -> tuple[tuple[_ClusterRecord, ...], list[str]]:
    warnings: list[str] = []
    records: list[_ClusterRecord] = []
    for index, row in enumerate(topic_cluster_rows or ()):
        if not isinstance(row, Mapping):
            warnings.append(
                f"topic cluster row {index} must be a mapping, got {type(row).__name__}; skipped"
            )
            continue
        try:
            validated = contract.validate_row(contract.TOPIC_CLUSTER_SCHEMA, row)
            records.append(_build_cluster_record(validated))
        except ValueError as exc:
            warnings.append(f"topic cluster row {index} is invalid: {exc}; skipped")
    return tuple(records), warnings


def _build_cluster_record(row: Mapping[str, Any]) -> _ClusterRecord:
    cluster_id = _require_nonempty_str("cluster_id", row.get("cluster_id"))
    status = _require_nonempty_str("status", row.get("status"))
    topic_label = _optional_nonempty_str(row.get("topic_label"))
    thread_ids = tuple(_normalize_string_list(row.get("thread_ids")))
    size = _coerce_nonnegative_int(row.get("size"))
    if size is None:
        size = len(thread_ids)
    evidence_titles = tuple(_normalize_string_list(row.get("evidence_titles")))
    representative_excerpts = tuple(_normalize_string_list(row.get("representative_excerpts")))
    mixed_reasons = tuple(_normalize_string_list(row.get("mixed_reasons")))
    candidate_wing = _optional_nonempty_str(row.get("candidate_wing"))
    candidate_room = _optional_nonempty_str(row.get("candidate_room"))
    cluster_score = _optional_float(row.get("cluster_score"))
    return _ClusterRecord(
        cluster_id=cluster_id,
        status=status,
        topic_label=topic_label,
        size=size,
        thread_ids=thread_ids,
        evidence_titles=evidence_titles,
        top_terms=tuple(_normalize_top_terms(row.get("top_terms"))),
        representative_excerpts=representative_excerpts,
        mixed_reasons=mixed_reasons,
        candidate_wing=candidate_wing,
        candidate_room=candidate_room,
        cluster_score=cluster_score,
    )


def _normalize_source_errors(
    rows: Sequence[Mapping[str, Any]],
    warnings: list[str],
) -> tuple[dict[str, Any], ...]:
    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            warnings.append(
                f"source error row {index} must be a mapping, got {type(row).__name__}; skipped"
            )
            continue
        normalized.append(dict(row))
    return tuple(normalized)


def _select_display_clusters(
    records: Sequence[_ClusterRecord],
) -> tuple[dict[str, tuple[_ClusterRecord, ...]], dict[str, int]]:
    shown: dict[str, tuple[_ClusterRecord, ...]] = {}
    hidden_counts: dict[str, int] = {}
    for status in ("candidate", "mixed", "noise"):
        status_records = [record for record in records if record.status == status]
        shown_records = tuple(status_records[:_MAX_DISPLAY_CLUSTERS_PER_STATUS])
        shown[status] = shown_records
        hidden_counts[status] = max(0, len(status_records) - len(shown_records))
    return shown, hidden_counts


def _build_counts(
    records: Sequence[_ClusterRecord],
    source_counts: Mapping[str, int],
    source_error_rows: Sequence[Mapping[str, Any]],
    warnings: Sequence[str],
    hidden_counts: Mapping[str, int],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    counts["clusters"] = len(records)
    counts["candidate_clusters"] = sum(1 for record in records if record.status == "candidate")
    counts["mixed_clusters"] = sum(1 for record in records if record.status == "mixed")
    counts["noise_clusters"] = sum(1 for record in records if record.status == "noise")
    counts["threads"] = sum(record.size for record in records)
    counts["source_errors"] = len(source_error_rows)
    counts["warnings"] = len(warnings)
    counts["displayed_candidate_clusters"] = len(
        [record for record in records if record.status == "candidate"][:_MAX_DISPLAY_CLUSTERS_PER_STATUS]
    )
    counts["displayed_mixed_clusters"] = len(
        [record for record in records if record.status == "mixed"][:_MAX_DISPLAY_CLUSTERS_PER_STATUS]
    )
    counts["displayed_noise_clusters"] = len(
        [record for record in records if record.status == "noise"][:_MAX_DISPLAY_CLUSTERS_PER_STATUS]
    )
    counts["hidden_candidate_clusters"] = int(hidden_counts.get("candidate", 0))
    counts["hidden_mixed_clusters"] = int(hidden_counts.get("mixed", 0))
    counts["hidden_noise_clusters"] = int(hidden_counts.get("noise", 0))
    for key, value in source_counts.items():
        if _is_nonnegative_int(value):
            counts[str(key)] = int(value)
    return counts


def _build_markdown(
    *,
    run_id: str,
    records: Sequence[_ClusterRecord],
    shown_by_status: Mapping[str, Sequence[_ClusterRecord]],
    hidden_counts: Mapping[str, int],
    source_counts: Mapping[str, int],
    source_error_rows: Sequence[Mapping[str, Any]],
    warnings: Sequence[str],
) -> str:
    lines: list[str] = []
    lines.append("# ChatGPT Archive Atlas Summary")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append(f"- Run ID: `{run_id}`")
    lines.append(f"- Clusters: {len(records)}")
    lines.append(f"- Candidate clusters: {sum(1 for record in records if record.status == 'candidate')}")
    lines.append(f"- Mixed clusters: {sum(1 for record in records if record.status == 'mixed')}")
    lines.append(f"- Noise clusters: {sum(1 for record in records if record.status == 'noise')}")
    lines.append(f"- Threads represented: {sum(record.size for record in records)}")
    lines.append(f"- Source errors: {len(source_error_rows)}")
    lines.append("")

    lines.append("## Candidate Wings/Rooms")
    lines.append("")
    if records:
        lines.append("| Status | Size | Wing | Room | Topic label | Cluster ID |")
        lines.append("| --- | ---: | --- | --- | --- | --- |")
        for status in ("candidate", "mixed", "noise"):
            for record in shown_by_status.get(status, ()):
                lines.append(
                    "| "
                    f"{record.status} | {record.size} | {_md_cell(record.candidate_wing)} | "
                    f"{_md_cell(record.candidate_room)} | {_md_cell(record.topic_label)} | "
                    f"`{record.cluster_id}` |"
                )
            hidden = int(hidden_counts.get(status, 0))
            if hidden > 0:
                lines.append(
                    f"| {status} | ... | ... | ... | {hidden} additional {status} clusters not shown | ... |"
                )
    else:
        lines.append("No valid topic cluster rows were available.")
    lines.append("")

    lines.append("## Cluster Sizes")
    lines.append("")
    for status in ("candidate", "mixed", "noise"):
        status_records = [record for record in records if record.status == status]
        if not status_records:
            lines.append(f"- {status}: 0")
            continue
        sizes = ", ".join(
            f"`{record.cluster_id}`={record.size}" for record in shown_by_status.get(status, ())
        )
        lines.append(f"- {status}: {len(status_records)} clusters; shown sizes {sizes}")
        hidden = int(hidden_counts.get(status, 0))
        if hidden > 0:
            lines.append(f"  Remaining {status} clusters not shown: {hidden}")
    lines.append("")

    lines.append("## Evidence Titles")
    lines.append("")
    _append_cluster_details(lines, shown_by_status, detail_kind="titles")

    lines.append("## Top Terms")
    lines.append("")
    _append_cluster_details(lines, shown_by_status, detail_kind="terms")

    lines.append("## Representative Excerpts")
    lines.append("")
    _append_cluster_details(lines, shown_by_status, detail_kind="excerpts")

    lines.append("## Mixed/Noisy Clusters")
    lines.append("")
    mixed_or_noise = [record for record in records if record.status in {"mixed", "noise"}]
    if mixed_or_noise:
        for record in mixed_or_noise[: _MAX_DISPLAY_CLUSTERS_PER_STATUS * 2]:
            label = record.topic_label or "unlabeled"
            lines.append(f"### `{record.cluster_id}` - {label}")
            lines.append("")
            lines.append(f"- Status: {record.status}")
            lines.append(f"- Size: {record.size}")
            if record.mixed_reasons:
                lines.append(
                    "- Mixed reasons: "
                    + ", ".join(f"`{reason}`" for reason in record.mixed_reasons[:_MAX_MIXED_REASONS])
                )
            else:
                lines.append("- Mixed reasons: none recorded")
            if record.top_terms:
                lines.append(
                    "- Top terms: "
                    + ", ".join(
                        f"`{term}` ({count})" for term, count in record.top_terms[:_MAX_TOP_TERMS]
                    )
                )
            lines.append("")
        hidden_total = max(0, len(mixed_or_noise) - (_MAX_DISPLAY_CLUSTERS_PER_STATUS * 2))
        if hidden_total > 0:
            lines.append(f"- Additional mixed/noise clusters not shown: {hidden_total}")
            lines.append("")
    else:
        lines.append("No mixed or noise clusters were present.")
        lines.append("")

    lines.append("## Source Errors and Counts")
    lines.append("")
    if source_counts:
        for key in sorted(source_counts):
            value = source_counts[key]
            if _is_nonnegative_int(value):
                lines.append(f"- {key}: {int(value)}")
        lines.append("")
    if source_error_rows:
        error_counts = Counter(
            _optional_nonempty_str(row.get("error_code")) or "unknown_error" for row in source_error_rows
        )
        lines.append("### Source Error Counts")
        lines.append("")
        for error_code, count in sorted(error_counts.items(), key=lambda item: (-item[1], item[0]))[
            :_MAX_ERROR_CODES
        ]:
            lines.append(f"- `{_display_error_code(error_code)}`: {count}")
        lines.append("")
        lines.append("### Source Error Examples")
        lines.append("")
        for row in source_error_rows[:_MAX_ERROR_EXAMPLES]:
            path = _optional_nonempty_str(row.get("source_relative_path")) or "(unknown path)"
            error_code = _optional_nonempty_str(row.get("error_code")) or "unknown_error"
            detail = _optional_nonempty_str(row.get("message")) or _optional_nonempty_str(
                row.get("error_detail")
            )
            line = f"- `{_display_error_code(error_code)}` in `{path}`"
            if detail:
                line += f": {detail}"
            lines.append(line)
        lines.append("")
    else:
        lines.append("No source errors were reported.")
        lines.append("")

    if warnings:
        lines.append("## Warnings")
        lines.append("")
        for warning in warnings:
            lines.append(f"- {warning}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _append_cluster_details(
    lines: list[str],
    shown_by_status: Mapping[str, Sequence[_ClusterRecord]],
    *,
    detail_kind: str,
) -> None:
    any_rows = False
    for status in ("candidate", "mixed", "noise"):
        records = shown_by_status.get(status, ())
        if not records:
            continue
        any_rows = True
        lines.append(f"### {status.capitalize()} Clusters")
        lines.append("")
        for record in records:
            label = record.topic_label or "unlabeled"
            lines.append(f"- `{record.cluster_id}` ({label})")
            if detail_kind == "titles":
                values = list(record.evidence_titles[:_MAX_EVIDENCE_TITLES])
                lines.append(
                    "  Evidence titles: "
                    + (_join_or_none(values, quote=False))
                )
            elif detail_kind == "terms":
                values = [
                    f"`{term}` ({count})" for term, count in record.top_terms[:_MAX_TOP_TERMS]
                ]
                lines.append("  Top terms: " + (_join_or_none(values, raw=True)))
            elif detail_kind == "excerpts":
                values = list(record.representative_excerpts[:_MAX_EXCERPTS])
                if values:
                    lines.append("  Representative excerpts:")
                    for excerpt in values:
                        lines.append(f"  - {excerpt}")
                else:
                    lines.append("  Representative excerpts: none")
        lines.append("")
    if not any_rows:
        lines.append("No cluster details were available.")
        lines.append("")


def _append_summary_warnings(
    records: Sequence[_ClusterRecord],
    source_error_rows: Sequence[Mapping[str, Any]],
    warnings: list[str],
) -> None:
    warnings.append(f"summary built from {len(records)} valid topic cluster rows")
    if source_error_rows:
        warnings.append(f"source errors present: {len(source_error_rows)}")


def _join_or_none(values: Sequence[str], *, quote: bool = True, raw: bool = False) -> str:
    if not values:
        return "none"
    if raw:
        return ", ".join(values)
    if quote:
        return ", ".join(f"`{value}`" for value in values)
    return ", ".join(values)


def _cluster_sort_key(record: _ClusterRecord) -> tuple[int, int, float, str, str]:
    status_rank = {"candidate": 0, "mixed": 1, "noise": 2}
    label = (record.topic_label or "").lower()
    score = record.cluster_score if record.cluster_score is not None else -1.0
    return (status_rank.get(record.status, 9), -record.size, -score, label, record.cluster_id)


def _normalize_top_terms(value: Any) -> list[tuple[str, int]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    terms: list[tuple[str, int]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        term = _optional_nonempty_str(item.get("term"))
        count = _coerce_nonnegative_int(item.get("count"))
        if term is None or count is None:
            continue
        terms.append((term, count))
    return terms


def _normalize_string_list(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    result: list[str] = []
    for item in value:
        normalized = _optional_nonempty_str(item)
        if normalized is not None:
            result.append(normalized)
    return result


def _require_nonempty_str(name: str, value: Any) -> str:
    normalized = _optional_nonempty_str(value)
    if normalized is None:
        raise ValueError(f"{name} must be a non-empty string")
    return normalized


def _optional_nonempty_str(value: Any) -> Optional[str]:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _optional_float(value: Any) -> Optional[float]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return float(value)
    if isinstance(value, float):
        return value
    return None


def _coerce_nonnegative_int(value: Any) -> Optional[int]:
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return None


def _is_nonnegative_int(value: Any) -> bool:
    return _coerce_nonnegative_int(value) is not None


def _md_cell(value: Optional[str]) -> str:
    if not value:
        return "-"
    return value.replace("\n", " ").replace("|", "/")


def _display_error_code(value: str) -> str:
    return value.replace("_", " ")
