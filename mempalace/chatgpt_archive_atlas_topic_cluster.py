from __future__ import annotations

import hashlib
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from . import chatgpt_archive_atlas_contract as contract

_GENERIC_LABELS = frozenset(
    {
        "a",
        "an",
        "and",
        "any",
        "assistant",
        "chat",
        "chatgpt",
        "conversation",
        "data",
        "fact",
        "for",
        "from",
        "general",
        "help",
        "in",
        "is",
        "it",
        "misc",
        "of",
        "on",
        "or",
        "question",
        "task",
        "text",
        "the",
        "thread",
        "to",
        "topic",
        "user",
        "with",
        "you",
    }
)
_TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/+-]*")
_MAX_LABEL_CANDIDATES = 8
_MAX_TOP_TERMS = 8
_MAX_EVIDENCE_TITLES = 4
_MAX_REPRESENTATIVE_IDS = 3
_MAX_REPRESENTATIVE_EXCERPTS = 3
_MAX_LEXICAL_SIGNATURE = 8


@dataclass(frozen=True)
class ChatGPTAtlasTopicClusterResult:
    rows: tuple[dict[str, Any], ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class _VectorRecord:
    thread_id: str
    embedding_id: str
    vector: tuple[float, ...]
    dimensions: int
    status: str


@dataclass(frozen=True)
class _LexicalRecord:
    input_index: int
    thread_id: str
    lexical_row: dict[str, Any]
    vector: tuple[float, ...] | None
    vector_dimensions: int | None
    evidence_tokens: frozenset[str]
    lexical_signature: tuple[str, ...]
    label_candidates: tuple[str, ...]
    titles: tuple[str, ...]
    representative_excerpts: tuple[str, ...]
    top_terms: tuple[tuple[str, int], ...]
    candidate_wing_hint: str | None
    clusterable: bool
    noise_reason: str | None


@dataclass(frozen=True)
class _ClusterDraft:
    members: tuple[_LexicalRecord, ...]
    status: str
    mixed_reasons: tuple[str, ...]
    lexical_signature: tuple[str, ...]
    topic_label: str | None
    candidate_wing: str | None
    candidate_room: str | None
    top_terms: tuple[tuple[str, int], ...]
    evidence_titles: tuple[str, ...]
    representative_thread_ids: tuple[str, ...]
    representative_excerpts: tuple[str, ...]
    centroid: tuple[float, ...] | None
    vector_dimensions: int
    cluster_score: float
    similarity_min: float
    similarity_max: float
    similarity_mean: float


def build_chatgpt_topic_cluster_rows(
    lexical_rows,
    vector_rows,
    *,
    run_id: str,
    similarity_threshold: float = 0.82,
    min_shared_terms: int = 1,
    max_cluster_size: int = 8,
) -> tuple[dict[str, Any], ...]:
    rows, _warnings = _build_topic_cluster_result(
        lexical_rows,
        vector_rows,
        run_id=run_id,
        similarity_threshold=similarity_threshold,
        min_shared_terms=min_shared_terms,
        max_cluster_size=max_cluster_size,
    )
    return rows


def build_chatgpt_topic_clusters(
    lexical_rows,
    vector_rows,
    *,
    run_id: str,
    similarity_threshold: float = 0.82,
    min_shared_terms: int = 1,
    max_cluster_size: int = 8,
) -> ChatGPTAtlasTopicClusterResult:
    rows, warnings = _build_topic_cluster_result(
        lexical_rows,
        vector_rows,
        run_id=run_id,
        similarity_threshold=similarity_threshold,
        min_shared_terms=min_shared_terms,
        max_cluster_size=max_cluster_size,
    )
    return ChatGPTAtlasTopicClusterResult(rows=rows, warnings=warnings)


def _build_topic_cluster_result(
    lexical_rows,
    vector_rows,
    *,
    run_id: str,
    similarity_threshold: float,
    min_shared_terms: int,
    max_cluster_size: int,
) -> tuple[tuple[dict[str, Any], ...], tuple[str, ...]]:
    contract.build_progress(run_id=run_id, phase="topic_clusters", status="pending")
    similarity_cutoff = _validate_similarity_threshold(similarity_threshold)
    shared_terms_floor = _validate_positive_int("min_shared_terms", min_shared_terms)
    cluster_size_limit = _validate_positive_int("max_cluster_size", max_cluster_size)

    warnings: list[str] = []
    vectors_by_thread = _index_vector_rows(vector_rows, warnings)
    lexical_records = _normalize_lexical_rows(lexical_rows, vectors_by_thread, warnings)

    clustered = [record for record in lexical_records if record.clusterable]
    noise_records = [record for record in lexical_records if not record.clusterable]

    reference_dimensions = _dominant_vector_dimensions(clustered)
    dimension_mismatch_noise: list[_LexicalRecord] = []
    if reference_dimensions is not None:
        retained_clustered: list[_LexicalRecord] = []
        for record in clustered:
            if record.vector_dimensions != reference_dimensions:
                warnings.append(
                    _warning_text(
                        code="vector_dimensions_mismatch",
                        detail=(
                            f"thread {record.thread_id!r} has vector dimensions "
                            f"{record.vector_dimensions}, expected {reference_dimensions}"
                        ),
                        thread_id=record.thread_id,
                    )
                )
                dimension_mismatch_noise.append(
                    _with_noise_reason(record, "vector_dimensions_mismatch")
                )
                continue
            retained_clustered.append(record)
        clustered = retained_clustered
    noise_records.extend(dimension_mismatch_noise)

    pair_metrics = _build_pair_metrics(clustered)
    cluster_groups = _cluster_records(
        clustered,
        pair_metrics,
        similarity_threshold=similarity_cutoff,
        min_shared_terms=shared_terms_floor,
        max_cluster_size=cluster_size_limit,
    )

    drafts: list[_ClusterDraft] = []
    for group in cluster_groups:
        drafts.append(
            _build_cluster_draft(
                group,
                pair_metrics,
                similarity_threshold=similarity_cutoff,
                min_shared_terms=shared_terms_floor,
            )
        )
    for record in noise_records:
        drafts.append(
            _build_noise_draft(
                record,
                similarity_threshold=similarity_cutoff,
                min_shared_terms=shared_terms_floor,
            )
        )

    drafts.sort(key=_cluster_sort_key)
    rows = tuple(
        _materialize_cluster_row(
            draft,
            run_id=run_id,
            similarity_threshold=similarity_cutoff,
            min_shared_terms=shared_terms_floor,
            max_cluster_size=cluster_size_limit,
        )
        for draft in drafts
    )
    return rows, tuple(warnings)


def _index_vector_rows(
    vector_rows: Iterable[Mapping[str, Any]],
    warnings: list[str],
) -> dict[str, _VectorRecord]:
    indexed: dict[str, _VectorRecord] = {}
    duplicates: dict[str, list[_VectorRecord]] = defaultdict(list)

    for index, raw_row in enumerate(vector_rows):
        if not isinstance(raw_row, Mapping):
            warnings.append(
                _warning_text(
                    code="vector_row_type_error",
                    detail=f"vector row {index} must be a mapping, got {type(raw_row).__name__}",
                    thread_id=None,
                )
            )
            continue
        try:
            record = _normalize_vector_row(raw_row)
        except ValueError as exc:
            warnings.append(
                _warning_text(
                    code="vector_row_validation_error",
                    detail=f"vector row {index} is invalid: {exc}",
                    thread_id=_optional_nonempty_str(raw_row.get("thread_id")),
                )
            )
            continue
        duplicates[record.thread_id].append(record)

    for thread_id, records in duplicates.items():
        records.sort(key=lambda item: (item.status != "embedded", item.embedding_id, item.dimensions))
        indexed[thread_id] = records[0]
        if len(records) > 1:
            warnings.append(
                _warning_text(
                    code="duplicate_vector_rows",
                    detail=f"thread {thread_id!r} has {len(records)} vector rows; using the first stable record",
                    thread_id=thread_id,
                )
            )
    return indexed


def _normalize_lexical_rows(
    lexical_rows: Iterable[Mapping[str, Any]],
    vectors_by_thread: Mapping[str, _VectorRecord],
    warnings: list[str],
) -> list[_LexicalRecord]:
    records: list[_LexicalRecord] = []
    seen_threads: set[str] = set()

    for index, raw_row in enumerate(lexical_rows):
        if not isinstance(raw_row, Mapping):
            warnings.append(
                _warning_text(
                    code="lexical_row_type_error",
                    detail=f"lexical row {index} must be a mapping, got {type(raw_row).__name__}",
                    thread_id=None,
                )
            )
            continue
        try:
            lexical_row = contract.validate_row(contract.LEXICAL_SKETCH_SCHEMA, raw_row)
            thread_id = _require_nonempty_str("thread_id", lexical_row.get("thread_id"))
        except ValueError as exc:
            warnings.append(
                _warning_text(
                    code="lexical_row_validation_error",
                    detail=f"lexical row {index} is invalid: {exc}",
                    thread_id=_optional_nonempty_str(raw_row.get("thread_id")),
                )
            )
            continue

        if thread_id in seen_threads:
            warnings.append(
                _warning_text(
                    code="duplicate_lexical_rows",
                    detail=f"thread {thread_id!r} appears more than once; keeping the first lexical row",
                    thread_id=thread_id,
                )
            )
            continue
        seen_threads.add(thread_id)

        evidence_tokens = _build_evidence_tokens(lexical_row)
        lexical_signature = _build_lexical_signature(lexical_row, evidence_tokens)
        label_candidates = _build_label_candidates(lexical_row)
        titles = _build_titles(lexical_row)
        excerpts = _limit_unique(
            _normalize_string_list(lexical_row.get("representative_excerpts")),
            _MAX_REPRESENTATIVE_EXCERPTS,
        )
        top_terms = tuple(_normalize_top_terms(lexical_row.get("top_terms"))[:_MAX_TOP_TERMS])
        candidate_wing_hint = _candidate_wing_hint(lexical_row)

        clusterable = True
        noise_reason: str | None = None
        vector: tuple[float, ...] | None = None
        vector_dimensions: int | None = None
        if len(evidence_tokens) < 1 or not lexical_signature:
            clusterable = False
            noise_reason = "insufficient_lexical_evidence"
        else:
            vector_record = vectors_by_thread.get(thread_id)
            if vector_record is None:
                clusterable = False
                noise_reason = "missing_vector"
            elif vector_record.status != "embedded":
                clusterable = False
                noise_reason = "invalid_vector_status"
            else:
                vector = vector_record.vector
                vector_dimensions = vector_record.dimensions

        records.append(
            _LexicalRecord(
                input_index=index,
                thread_id=thread_id,
                lexical_row=lexical_row,
                vector=vector,
                vector_dimensions=vector_dimensions,
                evidence_tokens=evidence_tokens,
                lexical_signature=lexical_signature,
                label_candidates=label_candidates,
                titles=titles,
                representative_excerpts=excerpts,
                top_terms=top_terms,
                candidate_wing_hint=candidate_wing_hint,
                clusterable=clusterable,
                noise_reason=noise_reason,
            )
        )
    records.sort(key=lambda item: item.thread_id)
    return records


def _with_noise_reason(record: _LexicalRecord, noise_reason: str) -> _LexicalRecord:
    return _LexicalRecord(
        input_index=record.input_index,
        thread_id=record.thread_id,
        lexical_row=record.lexical_row,
        vector=None,
        vector_dimensions=record.vector_dimensions,
        evidence_tokens=record.evidence_tokens,
        lexical_signature=record.lexical_signature,
        label_candidates=record.label_candidates,
        titles=record.titles,
        representative_excerpts=record.representative_excerpts,
        top_terms=record.top_terms,
        candidate_wing_hint=record.candidate_wing_hint,
        clusterable=False,
        noise_reason=noise_reason,
    )


def _dominant_vector_dimensions(records: Sequence[_LexicalRecord]) -> int | None:
    counts = Counter(
        record.vector_dimensions
        for record in records
        if record.vector_dimensions is not None and record.vector is not None
    )
    if not counts:
        return None
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def _build_pair_metrics(
    records: Sequence[_LexicalRecord],
) -> dict[tuple[str, str], tuple[float, int]]:
    metrics: dict[tuple[str, str], tuple[float, int]] = {}
    for left_index, left in enumerate(records):
        for right in records[left_index + 1 :]:
            similarity = _cosine_similarity(left.vector, right.vector)
            overlap = len(left.evidence_tokens.intersection(right.evidence_tokens))
            metrics[(left.thread_id, right.thread_id)] = (similarity, overlap)
    return metrics


def _cluster_records(
    records: Sequence[_LexicalRecord],
    pair_metrics: Mapping[tuple[str, str], tuple[float, int]],
    *,
    similarity_threshold: float,
    min_shared_terms: int,
    max_cluster_size: int,
) -> list[tuple[_LexicalRecord, ...]]:
    remaining = {record.thread_id: record for record in records}
    clusters: list[tuple[_LexicalRecord, ...]] = []

    while remaining:
        anchor_id = sorted(remaining)[0]
        anchor = remaining.pop(anchor_id)
        cluster_members = [anchor]

        candidates: list[tuple[float, int, str, _LexicalRecord]] = []
        for other_id, other in remaining.items():
            similarity, overlap = _pair_metric(pair_metrics, anchor.thread_id, other_id)
            if similarity >= similarity_threshold and overlap >= min_shared_terms:
                candidates.append((-similarity, -overlap, other.thread_id, other))
        candidates.sort()

        for _neg_similarity, _neg_overlap, candidate_id, candidate in candidates:
            if len(cluster_members) >= max_cluster_size:
                break
            if candidate_id not in remaining:
                continue
            if all(
                _pair_metric(pair_metrics, member.thread_id, candidate.thread_id)[0]
                >= similarity_threshold
                and _pair_metric(pair_metrics, member.thread_id, candidate.thread_id)[1]
                >= min_shared_terms
                for member in cluster_members
            ):
                cluster_members.append(candidate)
                remaining.pop(candidate_id, None)

        clusters.append(tuple(sorted(cluster_members, key=lambda item: item.thread_id)))

    return clusters


def _build_cluster_draft(
    members: Sequence[_LexicalRecord],
    pair_metrics: Mapping[tuple[str, str], tuple[float, int]],
    *,
    similarity_threshold: float,
    min_shared_terms: int,
) -> _ClusterDraft:
    ordered_members = tuple(sorted(members, key=lambda item: item.thread_id))
    all_signatures = [set(member.lexical_signature) for member in ordered_members if member.lexical_signature]
    common_signature = set.intersection(*all_signatures) if all_signatures else set()

    pairwise_similarities = _pairwise_similarities(ordered_members, pair_metrics)
    similarity_min = min(pairwise_similarities) if pairwise_similarities else 1.0
    similarity_max = max(pairwise_similarities) if pairwise_similarities else 1.0
    similarity_mean = (
        sum(pairwise_similarities) / len(pairwise_similarities) if pairwise_similarities else 1.0
    )

    mixed_reasons: list[str] = []
    if len(ordered_members) == 1:
        if _is_sparse_singleton(ordered_members[0]):
            mixed_reasons.append("singleton_sparse_evidence")
            status = "noise"
        else:
            status = "candidate"
    else:
        if len(common_signature) < min_shared_terms:
            mixed_reasons.append("weak_common_lexical_signature")
        if similarity_max - similarity_min > 0.08:
            mixed_reasons.append("wide_similarity_band")
        status = "mixed" if mixed_reasons else "candidate"
    lexical_signature = _cluster_lexical_signature(ordered_members, common_signature)
    topic_label = _derive_topic_label(ordered_members, lexical_signature)
    candidate_wing = _derive_candidate_wing(ordered_members, lexical_signature)
    candidate_room = _slugify(topic_label) if topic_label else None
    top_terms = _aggregate_top_terms(ordered_members)
    evidence_titles = _aggregate_evidence_titles(ordered_members)
    representative_thread_ids = _representative_thread_ids(ordered_members)
    representative_excerpts = _aggregate_representative_excerpts(ordered_members)
    centroid = _centroid(ordered_members)
    vector_dimensions = ordered_members[0].vector_dimensions or 0
    cluster_score = min(similarity_mean, similarity_min) if len(ordered_members) > 1 else 1.0

    return _ClusterDraft(
        members=ordered_members,
        status=status,
        mixed_reasons=tuple(mixed_reasons),
        lexical_signature=lexical_signature,
        topic_label=topic_label,
        candidate_wing=candidate_wing,
        candidate_room=candidate_room,
        top_terms=top_terms,
        evidence_titles=evidence_titles,
        representative_thread_ids=representative_thread_ids,
        representative_excerpts=representative_excerpts,
        centroid=centroid,
        vector_dimensions=vector_dimensions,
        cluster_score=cluster_score,
        similarity_min=similarity_min,
        similarity_max=similarity_max,
        similarity_mean=similarity_mean,
    )


def _build_noise_draft(
    record: _LexicalRecord,
    *,
    similarity_threshold: float,
    min_shared_terms: int,
) -> _ClusterDraft:
    lexical_signature = record.lexical_signature[:_MAX_LEXICAL_SIGNATURE]
    topic_label = _derive_topic_label((record,), lexical_signature)
    candidate_wing = _derive_candidate_wing((record,), lexical_signature)
    candidate_room = _slugify(topic_label) if topic_label else None
    mixed_reasons = (record.noise_reason,) if record.noise_reason else ()
    return _ClusterDraft(
        members=(record,),
        status="noise",
        mixed_reasons=mixed_reasons,
        lexical_signature=lexical_signature,
        topic_label=topic_label,
        candidate_wing=candidate_wing,
        candidate_room=candidate_room,
        top_terms=record.top_terms[:_MAX_TOP_TERMS],
        evidence_titles=record.titles[:_MAX_EVIDENCE_TITLES],
        representative_thread_ids=(record.thread_id,),
        representative_excerpts=record.representative_excerpts[:_MAX_REPRESENTATIVE_EXCERPTS],
        centroid=tuple(record.vector) if record.vector is not None else None,
        vector_dimensions=record.vector_dimensions or 0,
        cluster_score=0.0 if record.noise_reason else similarity_threshold,
        similarity_min=0.0,
        similarity_max=0.0,
        similarity_mean=0.0,
    )


def _materialize_cluster_row(
    draft: _ClusterDraft,
    *,
    run_id: str,
    similarity_threshold: float,
    min_shared_terms: int,
    max_cluster_size: int,
) -> dict[str, Any]:
    cluster_id = _build_cluster_id(draft)
    topic_label = draft.topic_label if draft.topic_label and draft.topic_label.lower() not in _GENERIC_LABELS else None
    top_terms = [{"term": term, "count": count} for term, count in draft.top_terms[:_MAX_TOP_TERMS]]
    if not top_terms:
        top_terms = [{"term": "noise", "count": 1}] if draft.status == "noise" else [{"term": "topic", "count": 1}]

    row = contract.build_topic_cluster_row(
        run_id=run_id,
        cluster_id=cluster_id,
        status=draft.status,
        topic_label=topic_label,
        thread_ids=[member.thread_id for member in draft.members],
        top_terms=top_terms,
        evidence_titles=list(draft.evidence_titles[:_MAX_EVIDENCE_TITLES]),
        representative_thread_ids=list(
            draft.representative_thread_ids[:_MAX_REPRESENTATIVE_IDS]
        ),
        representative_excerpts=list(
            draft.representative_excerpts[:_MAX_REPRESENTATIVE_EXCERPTS]
        ),
        mixed_reasons=list(draft.mixed_reasons),
    )
    row.update(
        {
            "candidate_wing": draft.candidate_wing,
            "candidate_room": draft.candidate_room,
            "centroid": list(draft.centroid) if draft.centroid is not None else None,
            "vector_dimensions": draft.vector_dimensions,
            "lexical_signature": list(draft.lexical_signature),
            "similarity_threshold": similarity_threshold,
            "min_shared_terms": min_shared_terms,
            "max_cluster_size": max_cluster_size,
            "cluster_score": round(draft.cluster_score, 6),
            "similarity_min": round(draft.similarity_min, 6),
            "similarity_max": round(draft.similarity_max, 6),
            "similarity_mean": round(draft.similarity_mean, 6),
        }
    )
    contract.validate_row(contract.TOPIC_CLUSTER_SCHEMA, row)
    return row


def _build_cluster_id(draft: _ClusterDraft) -> str:
    member_ids = [member.thread_id for member in draft.members]
    lexical_signature = list(draft.lexical_signature[:_MAX_LEXICAL_SIGNATURE])
    seed = "|".join(member_ids) + "#" + "|".join(lexical_signature) + "#" + draft.status
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]
    return f"topic:{digest}"


def _cluster_sort_key(draft: _ClusterDraft) -> tuple[int, str, str]:
    status_rank = {"candidate": 0, "mixed": 1, "noise": 2}
    first_thread = draft.members[0].thread_id
    return (status_rank.get(draft.status, 9), first_thread, _build_cluster_id(draft))


def _normalize_vector_row(row: Mapping[str, Any]) -> _VectorRecord:
    thread_id = _require_nonempty_str("thread_id", row.get("thread_id"))
    embedding_id = _optional_nonempty_str(row.get("embedding_id")) or f"vector:{thread_id}"
    status = _optional_nonempty_str(row.get("status")) or "embedded"
    if status not in {"embedded", "skipped"}:
        raise ValueError("status must be 'embedded' or 'skipped' when present")
    dimensions = _require_positive_or_zero_int("vector_dimensions", row.get("vector_dimensions"))
    vector = tuple(_normalize_vector(row.get("vector")))
    if len(vector) != dimensions:
        raise ValueError("vector_dimensions must match vector length")
    return _VectorRecord(
        thread_id=thread_id,
        embedding_id=embedding_id,
        vector=vector,
        dimensions=dimensions,
        status=status,
    )


def _normalize_vector(value: Any) -> list[float]:
    if hasattr(value, "tolist"):
        value = value.tolist()
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ValueError("vector must be a numeric sequence")
    vector: list[float] = []
    for index, item in enumerate(value):
        if isinstance(item, bool):
            raise ValueError(f"vector item {index} must be numeric")
        if isinstance(item, int):
            vector.append(float(item))
            continue
        if isinstance(item, float):
            if not math.isfinite(item):
                raise ValueError(f"vector item {index} must be finite")
            vector.append(item)
            continue
        raise ValueError(f"vector item {index} must be numeric")
    if not vector:
        raise ValueError("vector must not be empty")
    norm = math.sqrt(sum(item * item for item in vector))
    if norm == 0.0:
        raise ValueError("vector must not be zero-norm")
    return vector


def _build_evidence_tokens(lexical_row: Mapping[str, Any]) -> frozenset[str]:
    tokens: set[str] = set()
    for key in ("project_terms",):
        for item in _normalize_string_list(lexical_row.get(key)):
            normalized = _normalize_overlap_value(item)
            if normalized is not None:
                tokens.add(normalized)
    for term, _count in _normalize_top_terms(lexical_row.get("top_terms"))[:_MAX_TOP_TERMS]:
        normalized = _normalize_overlap_value(term)
        if normalized is not None:
            tokens.add(normalized)
    return frozenset(sorted(tokens))


def _build_lexical_signature(
    lexical_row: Mapping[str, Any],
    evidence_tokens: frozenset[str],
) -> tuple[str, ...]:
    ranked: list[str] = []
    for phrase in _build_label_candidates(lexical_row):
        for token in _evidence_key_tokens(phrase):
            if token not in ranked and token in evidence_tokens:
                ranked.append(token)
                if len(ranked) >= _MAX_LEXICAL_SIGNATURE:
                    return tuple(ranked)
    for token in sorted(evidence_tokens):
        if token not in ranked:
            ranked.append(token)
            if len(ranked) >= _MAX_LEXICAL_SIGNATURE:
                break
    return tuple(ranked)


def _build_label_candidates(lexical_row: Mapping[str, Any]) -> tuple[str, ...]:
    ranked: list[str] = []
    fields = (
        "keyphrases",
        "domains",
        "package_names",
        "model_names",
        "legal_citations",
        "project_terms",
    )
    for key in fields:
        for item in _normalize_string_list(lexical_row.get(key)):
            normalized = _normalize_label_value(item)
            if normalized is None or normalized in ranked:
                continue
            ranked.append(normalized)
            if len(ranked) >= _MAX_LABEL_CANDIDATES:
                return tuple(ranked)
    for term, _count in _normalize_top_terms(lexical_row.get("top_terms")):
        normalized = _normalize_label_value(term)
        if normalized is None or normalized in ranked:
            continue
        ranked.append(normalized)
        if len(ranked) >= _MAX_LABEL_CANDIDATES:
            break
    return tuple(ranked)


def _build_titles(lexical_row: Mapping[str, Any]) -> tuple[str, ...]:
    values: list[str] = []
    for key in ("conversation_title", "title_hint"):
        value = _optional_nonempty_str(lexical_row.get(key))
        if value is not None and value not in values:
            values.append(value)
    return tuple(values[:_MAX_EVIDENCE_TITLES])


def _candidate_wing_hint(lexical_row: Mapping[str, Any]) -> str | None:
    for key in ("domains", "package_names", "model_names", "legal_citations", "project_terms"):
        values = _normalize_string_list(lexical_row.get(key))
        if not values:
            continue
        candidate = _slugify(values[0])
        if candidate:
            return candidate
    signature = _build_label_candidates(lexical_row)
    return _slugify(signature[0]) if signature else None


def _aggregate_top_terms(records: Sequence[_LexicalRecord]) -> tuple[tuple[str, int], ...]:
    counts: Counter[str] = Counter()
    supports: Counter[str] = Counter()
    for record in records:
        seen_for_record: set[str] = set()
        for term, count in record.top_terms:
            normalized = term.strip()
            if not normalized or normalized.lower() in _GENERIC_LABELS:
                continue
            counts[normalized] += count
            if normalized not in seen_for_record:
                supports[normalized] += 1
                seen_for_record.add(normalized)
    ranked = sorted(
        counts,
        key=lambda term: (-supports[term], -counts[term], term.lower()),
    )
    return tuple((term, counts[term]) for term in ranked[:_MAX_TOP_TERMS])


def _aggregate_evidence_titles(records: Sequence[_LexicalRecord]) -> tuple[str, ...]:
    titles: list[str] = []
    for record in records:
        for title in record.titles:
            if title not in titles:
                titles.append(title)
            if len(titles) >= _MAX_EVIDENCE_TITLES:
                return tuple(titles)
    return tuple(titles)


def _representative_thread_ids(records: Sequence[_LexicalRecord]) -> tuple[str, ...]:
    ranked = sorted(
        records,
        key=lambda record: (-len(record.evidence_tokens), -len(record.top_terms), record.thread_id),
    )
    return tuple(record.thread_id for record in ranked[:_MAX_REPRESENTATIVE_IDS])


def _aggregate_representative_excerpts(records: Sequence[_LexicalRecord]) -> tuple[str, ...]:
    excerpts: list[str] = []
    for record in records:
        for excerpt in record.representative_excerpts:
            if excerpt and excerpt not in excerpts:
                excerpts.append(excerpt)
            if len(excerpts) >= _MAX_REPRESENTATIVE_EXCERPTS:
                return tuple(excerpts)
    return tuple(excerpts)


def _cluster_lexical_signature(
    records: Sequence[_LexicalRecord],
    common_signature: set[str],
) -> tuple[str, ...]:
    if common_signature:
        return tuple(sorted(common_signature)[:_MAX_LEXICAL_SIGNATURE])
    counts: Counter[str] = Counter()
    for record in records:
        counts.update(record.lexical_signature)
    ranked = sorted(counts, key=lambda token: (-counts[token], token))
    return tuple(ranked[:_MAX_LEXICAL_SIGNATURE])


def _derive_topic_label(
    records: Sequence[_LexicalRecord],
    lexical_signature: Sequence[str],
) -> str | None:
    candidate_scores: dict[str, tuple[int, int]] = {}
    for record in records:
        seen: set[str] = set()
        for index, candidate in enumerate(record.label_candidates):
            if candidate in seen:
                continue
            support, score = candidate_scores.get(candidate, (0, 0))
            candidate_scores[candidate] = (support + 1, score + (_MAX_LABEL_CANDIDATES - index))
            seen.add(candidate)
    ranked_candidates = sorted(
        candidate_scores,
        key=lambda candidate: (
            -candidate_scores[candidate][0],
            -candidate_scores[candidate][1],
            len(candidate),
            candidate,
        ),
    )
    for candidate in ranked_candidates:
        if _is_useful_label(candidate):
            return candidate
    if lexical_signature:
        fallback = " ".join(lexical_signature[:3]).strip()
        if _is_useful_label(fallback):
            return fallback
    return None


def _derive_candidate_wing(
    records: Sequence[_LexicalRecord],
    lexical_signature: Sequence[str],
) -> str | None:
    hints = Counter(
        record.candidate_wing_hint
        for record in records
        if record.candidate_wing_hint is not None
    )
    if hints:
        return sorted(hints, key=lambda item: (-hints[item], item))[0]
    if lexical_signature:
        return _slugify(lexical_signature[0])
    return None


def _centroid(records: Sequence[_LexicalRecord]) -> tuple[float, ...] | None:
    vectors = [record.vector for record in records if record.vector is not None]
    if not vectors:
        return None
    dimensions = len(vectors[0])
    totals = [0.0] * dimensions
    for vector in vectors:
        for index, value in enumerate(vector):
            totals[index] += value
    return tuple(round(total / len(vectors), 6) for total in totals)


def _pairwise_similarities(
    records: Sequence[_LexicalRecord],
    pair_metrics: Mapping[tuple[str, str], tuple[float, int]],
) -> list[float]:
    similarities: list[float] = []
    for left_index, left in enumerate(records):
        for right in records[left_index + 1 :]:
            similarity, _overlap = _pair_metric(pair_metrics, left.thread_id, right.thread_id)
            similarities.append(similarity)
    return similarities


def _pair_metric(
    pair_metrics: Mapping[tuple[str, str], tuple[float, int]],
    left_thread_id: str,
    right_thread_id: str,
) -> tuple[float, int]:
    key = tuple(sorted((left_thread_id, right_thread_id)))
    return pair_metrics.get(key, (0.0, 0))


def _cosine_similarity(
    left: Sequence[float] | None,
    right: Sequence[float] | None,
) -> float:
    if left is None or right is None or len(left) != len(right) or not left:
        return 0.0
    numerator = sum(left_value * right_value for left_value, right_value in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    similarity = numerator / (left_norm * right_norm)
    if similarity < -1.0:
        return -1.0
    if similarity > 1.0:
        return 1.0
    return similarity


def _normalize_top_terms(value: Any) -> list[tuple[str, int]]:
    if value is None:
        return []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ValueError("top_terms must be a sequence")
    items: list[tuple[str, int]] = []
    for entry in value:
        if not isinstance(entry, Mapping):
            raise ValueError("top_terms entries must be mappings")
        term = _require_nonempty_str("term", entry.get("term"))
        count = _require_positive_or_zero_int("count", entry.get("count"))
        items.append((term, count))
    return items


def _normalize_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ValueError("expected a sequence of strings")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError("expected a sequence of strings")
        if item.strip():
            result.append(item.strip())
    return result


def _evidence_key_tokens(value: str) -> set[str]:
    tokens: set[str] = set()
    for token in _TOKEN_RE.findall(value.lower()):
        normalized = token.strip("._:-/+")
        if len(normalized) < 2 or normalized in _GENERIC_LABELS:
            continue
        tokens.add(normalized)
    return tokens


def _normalize_label_value(value: str) -> str | None:
    value = " ".join(value.strip().split())
    if not value:
        return None
    if value.lower() in _GENERIC_LABELS:
        return None
    useful_tokens = [token for token in _evidence_key_tokens(value) if token not in _GENERIC_LABELS]
    if not useful_tokens:
        return None
    return value


def _normalize_overlap_value(value: str) -> str | None:
    normalized = " ".join(value.strip().lower().split())
    if not normalized or normalized in _GENERIC_LABELS:
        return None
    slug = _slugify(normalized)
    if slug is None or slug in _GENERIC_LABELS:
        return None
    return slug


def _is_useful_label(value: str) -> bool:
    normalized = _normalize_label_value(value)
    if normalized is None:
        return False
    lowered = normalized.lower()
    if lowered in _GENERIC_LABELS:
        return False
    if lowered.startswith("thread ") or lowered.startswith("chatgpt "):
        return False
    return True


def _is_sparse_singleton(record: _LexicalRecord) -> bool:
    top_term_total = sum(count for _term, count in record.top_terms)
    strongest_top_term = max((count for _term, count in record.top_terms), default=0)
    if strongest_top_term >= 2 or top_term_total >= 3:
        return False
    if len(record.top_terms) >= 2:
        return False
    return True


def _slugify(value: str | None) -> str | None:
    if value is None:
        return None
    lowered = value.strip().lower()
    if not lowered:
        return None
    slug = re.sub(r"[^a-z0-9]+", "_", lowered).strip("_")
    return slug or None


def _limit_unique(values: Sequence[str], limit: int) -> tuple[str, ...]:
    unique: list[str] = []
    for value in values:
        if value not in unique:
            unique.append(value)
        if len(unique) >= limit:
            break
    return tuple(unique)


def _validate_similarity_threshold(value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("similarity_threshold must be a number")
    numeric = float(value)
    if not math.isfinite(numeric) or numeric < -1.0 or numeric > 1.0:
        raise ValueError("similarity_threshold must be between -1.0 and 1.0")
    return numeric


def _validate_positive_int(name: str, value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _require_positive_or_zero_int(name: str, value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _require_nonempty_str(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _optional_nonempty_str(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _warning_text(*, code: str, detail: str, thread_id: str | None) -> str:
    parts = [code]
    if thread_id is not None:
        parts.append(f"thread_id={thread_id}")
    parts.append(detail)
    warning = " | ".join(parts)
    contract.validate_json_safe(warning)
    return warning
