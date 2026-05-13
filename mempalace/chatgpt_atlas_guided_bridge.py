from __future__ import annotations

import hashlib
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from . import chatgpt_archive_atlas_contract as atlas_contract
from . import chatgpt_atlas_guided_contract as guided_contract
from .ontology_candidates import build_candidate_id

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
_MAX_DIRECT_LABEL_TOKENS = 3
_MAX_SLUG_LENGTH = 96
_MAX_ROOM_TOKENS = 4
_MAX_TOP_TERM_TOKENS = 3
_BLOCKING_MIXED_REASONS = frozenset(
    {
        "multiple_candidate_topics",
        "weak_common_lexical_signature",
        "wide_similarity_band",
    }
)
_GENERIC_TOKENS = frozenset(
    {
        "a",
        "an",
        "and",
        "assorted",
        "chat",
        "chatgpt",
        "cluster",
        "conversation",
        "data",
        "for",
        "fragment",
        "fragments",
        "general",
        "help",
        "in",
        "misc",
        "noise",
        "notes",
        "of",
        "or",
        "other",
        "room",
        "signal",
        "some",
        "stuff",
        "the",
        "thread",
        "topic",
        "with",
    }
)
_WING_HINTS = {
    "code": frozenset(
        {
            "api",
            "bug",
            "code",
            "debug",
            "fixture",
            "javascript",
            "json",
            "migrate",
            "migration",
            "parser",
            "pytest",
            "python",
            "react",
            "refactor",
            "ruff",
            "schema",
            "sqlalchemy",
            "test",
            "testing",
            "typescript",
            "ui",
        }
    ),
    "data": frozenset(
        {
            "analytics",
            "chroma",
            "dataset",
            "embedding",
            "embeddings",
            "etl",
            "indexing",
            "metrics",
            "pipeline",
            "query",
            "rerank",
            "vector",
        }
    ),
    "devops": frozenset(
        {
            "ansible",
            "cache",
            "container",
            "database",
            "deploy",
            "deployment",
            "docker",
            "grafana",
            "infra",
            "infrastructure",
            "k8s",
            "kubernetes",
            "latency",
            "linux",
            "nginx",
            "ops",
            "postgres",
            "postgresql",
            "prometheus",
            "redis",
            "server",
            "sql",
            "systemd",
            "terraform",
            "ubuntu",
            "vacuum",
        }
    ),
    "finance": frozenset(
        {
            "budget",
            "cost",
            "finance",
            "forecast",
            "invoice",
            "pricing",
            "revenue",
            "tax",
        }
    ),
    "health": frozenset(
        {
            "doctor",
            "health",
            "medical",
            "medication",
            "symptom",
            "therapy",
            "treatment",
            "wellness",
        }
    ),
    "legal": frozenset(
        {
            "agreement",
            "compliance",
            "contract",
            "copyright",
            "gdpr",
            "legal",
            "liability",
            "policy",
            "privacy",
            "terms",
        }
    ),
    "product": frozenset(
        {
            "backlog",
            "feature",
            "launch",
            "product",
            "requirements",
            "roadmap",
            "ux",
        }
    ),
    "research": frozenset(
        {
            "analysis",
            "benchmark",
            "experiment",
            "paper",
            "research",
            "study",
        }
    ),
    "work_admin": frozenset(
        {
            "agenda",
            "coordination",
            "deadline",
            "meeting",
            "milestone",
            "planning",
            "project",
            "release",
            "schedule",
            "sprint",
            "standup",
        }
    ),
}
_WING_PRIORITY = tuple(
    "devops code data product research work_admin legal finance health general".split()
)


@dataclass(frozen=True)
class ChatGPTAtlasGuidedBridgeResult:
    rows: tuple[dict[str, Any], ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class _AtlasClusterRecord:
    input_index: int
    atlas_run_id: str
    cluster_id: str
    status: str
    topic_label: str | None
    thread_ids: tuple[str, ...]
    top_terms: tuple[dict[str, Any], ...]
    evidence_titles: tuple[str, ...]
    representative_thread_ids: tuple[str, ...]
    representative_excerpts: tuple[str, ...]
    mixed_reasons: tuple[str, ...]


@dataclass(frozen=True)
class _CandidateIdentity:
    canonical_wing: str
    canonical_room: str
    label: str
    definition: str | None
    safe_for_mixed: bool
    wing_conflict: bool
    semantic_seed: str


@dataclass(frozen=True)
class _BridgeDraft:
    record: _AtlasClusterRecord
    identity: _CandidateIdentity | None


def build_chatgpt_atlas_guided_bridge_rows(
    topic_cluster_rows: Iterable[Mapping[str, Any]],
    *,
    run_id: str,
    atlas_run_id: str | None = None,
) -> tuple[dict[str, Any], ...]:
    rows, _warnings = _build_bridge_result(
        topic_cluster_rows,
        run_id=run_id,
        atlas_run_id=atlas_run_id,
    )
    return rows


def build_chatgpt_atlas_guided_bridge(
    topic_cluster_rows: Iterable[Mapping[str, Any]],
    *,
    run_id: str,
    atlas_run_id: str | None = None,
) -> ChatGPTAtlasGuidedBridgeResult:
    rows, warnings = _build_bridge_result(
        topic_cluster_rows,
        run_id=run_id,
        atlas_run_id=atlas_run_id,
    )
    return ChatGPTAtlasGuidedBridgeResult(rows=rows, warnings=warnings)


def _build_bridge_result(
    topic_cluster_rows: Iterable[Mapping[str, Any]],
    *,
    run_id: str,
    atlas_run_id: str | None,
) -> tuple[tuple[dict[str, Any], ...], tuple[str, ...]]:
    records, resolved_atlas_run_id = _normalize_cluster_rows(
        topic_cluster_rows,
        atlas_run_id=atlas_run_id,
    )
    guided_contract.build_progress(
        run_id=run_id,
        atlas_run_id=resolved_atlas_run_id,
        status="pending",
        current_phase="bridge",
        phase_status="pending",
        phase_order=["bridge"],
    )
    warnings: list[str] = []
    drafts = [_build_bridge_draft(record) for record in records]
    resolved_identity = _resolve_duplicate_keys(drafts, warnings)
    rows = tuple(
        _materialize_bridge_row(
            draft,
            run_id=run_id,
            atlas_run_id=resolved_atlas_run_id,
            identity=resolved_identity.get(draft.record.cluster_id),
        )
        for draft in drafts
    )
    return rows, tuple(warnings)


def _normalize_cluster_rows(
    topic_cluster_rows: Iterable[Mapping[str, Any]],
    *,
    atlas_run_id: str | None,
) -> tuple[tuple[_AtlasClusterRecord, ...], str]:
    records: list[_AtlasClusterRecord] = []
    seen_run_ids: set[str] = set()

    for index, raw_row in enumerate(topic_cluster_rows):
        if not isinstance(raw_row, Mapping):
            raise ValueError(
                f"topic cluster row {index} must be a mapping, got {type(raw_row).__name__}"
            )
        validated = atlas_contract.validate_row(atlas_contract.TOPIC_CLUSTER_SCHEMA, raw_row)
        row_run_id = _require_nonempty_str("run_id", validated.get("run_id"))
        seen_run_ids.add(row_run_id)
        records.append(
            _AtlasClusterRecord(
                input_index=index,
                atlas_run_id=row_run_id,
                cluster_id=_require_nonempty_str("cluster_id", validated.get("cluster_id")),
                status=_require_choice(
                    "status",
                    validated.get("status"),
                    atlas_contract.TOPIC_CLUSTER_STATUSES,
                ),
                topic_label=_optional_nonempty_str(validated.get("topic_label")),
                thread_ids=tuple(_normalize_string_list("thread_ids", validated.get("thread_ids"))),
                top_terms=tuple(_normalize_term_counts(validated.get("top_terms"))),
                evidence_titles=tuple(
                    _normalize_string_list("evidence_titles", validated.get("evidence_titles"))
                ),
                representative_thread_ids=tuple(
                    _normalize_string_list(
                        "representative_thread_ids", validated.get("representative_thread_ids")
                    )
                ),
                representative_excerpts=tuple(
                    _normalize_string_list(
                        "representative_excerpts", validated.get("representative_excerpts")
                    )
                ),
                mixed_reasons=tuple(
                    _normalize_string_list("mixed_reasons", validated.get("mixed_reasons"))
                ),
            )
        )

    if atlas_run_id is not None:
        resolved_atlas_run_id = atlas_run_id
    elif not seen_run_ids:
        raise ValueError("atlas_run_id is required when topic_cluster_rows is empty")
    elif len(seen_run_ids) != 1:
        raise ValueError("topic_cluster_rows must belong to exactly one atlas run_id")
    else:
        resolved_atlas_run_id = next(iter(seen_run_ids))

    for record in records:
        if record.atlas_run_id != resolved_atlas_run_id:
            raise ValueError("topic_cluster_rows run_id does not match atlas_run_id")
    return tuple(records), resolved_atlas_run_id


def _build_bridge_draft(record: _AtlasClusterRecord) -> _BridgeDraft:
    if record.status == "noise":
        return _BridgeDraft(record=record, identity=None)

    identity = _derive_candidate_identity(record)
    if record.status == "mixed" and (
        identity is None
        or not identity.safe_for_mixed
        or identity.wing_conflict
        or any(reason in _BLOCKING_MIXED_REASONS for reason in record.mixed_reasons)
    ):
        return _BridgeDraft(record=record, identity=None)

    return _BridgeDraft(record=record, identity=identity)


def _derive_candidate_identity(record: _AtlasClusterRecord) -> _CandidateIdentity | None:
    source_tokens = _source_tokens(record)
    room_tokens = _derive_room_tokens(record)
    if not room_tokens:
        return None

    wing_counter = _wing_scores(source_tokens)
    wing_conflict = _has_wing_conflict(wing_counter)
    canonical_wing = _select_wing(wing_counter)
    canonical_room = _fit_slug("_".join(room_tokens), semantic_seed=record.cluster_id)
    label = record.topic_label or _display_label(room_tokens)
    definition = _build_definition(record)
    safe_for_mixed = (
        canonical_wing != "general" and len(room_tokens) >= 2 and not _label_has_split_signal(record)
    )
    semantic_seed = _semantic_seed(record, canonical_wing, canonical_room)
    return _CandidateIdentity(
        canonical_wing=canonical_wing,
        canonical_room=canonical_room,
        label=label,
        definition=definition,
        safe_for_mixed=safe_for_mixed,
        wing_conflict=wing_conflict,
        semantic_seed=semantic_seed,
    )


def _resolve_duplicate_keys(
    drafts: Sequence[_BridgeDraft],
    warnings: list[str],
) -> dict[str, _CandidateIdentity | None]:
    identities_by_cluster = {draft.record.cluster_id: draft.identity for draft in drafts}
    collisions: dict[tuple[str, str], list[_BridgeDraft]] = defaultdict(list)
    for draft in drafts:
        if draft.identity is None:
            continue
        key = (draft.identity.canonical_wing, draft.identity.canonical_room)
        collisions[key].append(draft)

    for (canonical_wing, canonical_room), items in collisions.items():
        if len(items) <= 1:
            continue
        for draft in items:
            identity = draft.identity
            if identity is None:
                continue
            suffix = hashlib.sha256(identity.semantic_seed.encode("utf-8")).hexdigest()[:10]
            resolved_room = _fit_slug(
                f"{canonical_room}_{suffix}",
                semantic_seed=identity.semantic_seed,
            )
            identities_by_cluster[draft.record.cluster_id] = _CandidateIdentity(
                canonical_wing=canonical_wing,
                canonical_room=resolved_room,
                label=identity.label,
                definition=identity.definition,
                safe_for_mixed=identity.safe_for_mixed,
                wing_conflict=identity.wing_conflict,
                semantic_seed=identity.semantic_seed,
            )
            warnings.append(
                "disambiguated duplicate candidate_key for "
                f"{draft.record.cluster_id!r} as {canonical_wing}:{resolved_room}"
            )
    return identities_by_cluster


def _materialize_bridge_row(
    draft: _BridgeDraft,
    *,
    run_id: str,
    atlas_run_id: str,
    identity: _CandidateIdentity | None,
) -> dict[str, Any]:
    candidate_id = None
    candidate_key = None
    label = draft.record.topic_label or None
    definition = None
    if identity is not None:
        candidate_id = build_candidate_id(identity.canonical_wing, identity.canonical_room)
        candidate_key = f"{identity.canonical_wing}:{identity.canonical_room}"
        label = identity.label
        definition = identity.definition

    return guided_contract.build_candidate_bridge_record(
        run_id=run_id,
        atlas_run_id=atlas_run_id,
        candidate_id=candidate_id,
        candidate_key=candidate_key,
        bridge_status=draft.record.status,
        atlas_cluster_id=draft.record.cluster_id,
        atlas_cluster_status=draft.record.status,
        topic_label=draft.record.topic_label,
        label=label,
        definition=definition,
        thread_ids=list(draft.record.thread_ids),
        top_terms=list(draft.record.top_terms),
        evidence_titles=list(draft.record.evidence_titles),
        representative_thread_ids=list(draft.record.representative_thread_ids),
        representative_excerpts=list(draft.record.representative_excerpts),
        mixed_reasons=list(draft.record.mixed_reasons),
    )


def _source_tokens(record: _AtlasClusterRecord) -> list[str]:
    tokens: list[str] = []
    if record.topic_label:
        tokens.extend(_tokenize(record.topic_label))
    for term in record.top_terms:
        tokens.extend(_tokenize(str(term["term"])))
    for title in record.evidence_titles:
        tokens.extend(_tokenize(title))
    return tokens


def _derive_room_tokens(record: _AtlasClusterRecord) -> list[str]:
    if record.topic_label:
        label_tokens = _candidate_label_tokens(record.topic_label)
        if (
            label_tokens
            and len(label_tokens) <= _MAX_DIRECT_LABEL_TOKENS
            and not _label_has_split_signal(record)
        ):
            return label_tokens[:_MAX_ROOM_TOKENS]

    room_tokens: list[str] = []
    for term in record.top_terms:
        count = int(term["count"])
        if room_tokens and len(room_tokens) >= 2 and count <= 1:
            break
        term_tokens = _candidate_label_tokens(str(term["term"]))
        if not term_tokens:
            continue
        room_tokens.extend(token for token in term_tokens if token not in room_tokens)
        if len(room_tokens) >= _MAX_TOP_TERM_TOKENS:
            return room_tokens[:_MAX_TOP_TERM_TOKENS]

    if room_tokens:
        return room_tokens[:_MAX_TOP_TERM_TOKENS]
    if record.topic_label:
        return _tokenize_to_slug_parts(record.topic_label)[:_MAX_ROOM_TOKENS]
    return []


def _candidate_label_tokens(text: str) -> list[str]:
    tokens = [token for token in _tokenize_to_slug_parts(text) if token not in _GENERIC_TOKENS]
    return tokens


def _wing_scores(tokens: Sequence[str]) -> Counter[str]:
    scores: Counter[str] = Counter()
    for token in tokens:
        for wing, hints in _WING_HINTS.items():
            if token in hints:
                scores[wing] += 1
    return scores


def _has_wing_conflict(scores: Counter[str]) -> bool:
    if not scores:
        return False
    ranked = scores.most_common()
    if len(ranked) < 2:
        return False
    return ranked[0][1] == ranked[1][1]


def _select_wing(scores: Counter[str]) -> str:
    if not scores:
        return "general"
    ranked = sorted(scores.items(), key=lambda item: (-item[1], _WING_PRIORITY.index(item[0])))
    return ranked[0][0]


def _display_label(room_tokens: Sequence[str]) -> str:
    return " ".join(token.capitalize() for token in room_tokens)


def _build_definition(record: _AtlasClusterRecord) -> str | None:
    top_terms = [str(item["term"]) for item in record.top_terms[:3]]
    if record.topic_label and top_terms:
        return (
            f"Atlas-guided candidate scaffold for {record.topic_label}. "
            f"Top terms: {', '.join(top_terms)}."
        )
    if record.topic_label:
        return f"Atlas-guided candidate scaffold for {record.topic_label}."
    if top_terms:
        return f"Atlas-guided candidate scaffold from top terms: {', '.join(top_terms)}."
    return None


def _semantic_seed(record: _AtlasClusterRecord, canonical_wing: str, canonical_room: str) -> str:
    top_terms = ",".join(f"{item['term']}:{item['count']}" for item in record.top_terms)
    label = record.topic_label or ""
    return (
        f"{record.cluster_id}|{canonical_wing}|{canonical_room}|{label}|"
        f"{top_terms}|{','.join(record.thread_ids)}"
    )


def _label_has_split_signal(record: _AtlasClusterRecord) -> bool:
    label = (record.topic_label or "").lower()
    return " and " in label or " / " in label or " or " in label


def _fit_slug(value: str, *, semantic_seed: str) -> str:
    slug = "_".join(part for part in _tokenize_to_slug_parts(value) if part)
    if not slug:
        slug = "topic"
    if len(slug) <= _MAX_SLUG_LENGTH:
        return slug
    digest = hashlib.sha256(semantic_seed.encode("utf-8")).hexdigest()[:10]
    budget = _MAX_SLUG_LENGTH - len(digest) - 1
    return f"{slug[:budget].rstrip('_')}_{digest}"


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN_RE.findall(text)]


def _tokenize_to_slug_parts(text: str) -> list[str]:
    return [token for token in _tokenize(text) if token]


def _normalize_term_counts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError("top_terms must be a sequence of term-count mappings")
    normalized: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError("top_terms entries must be mappings")
        term = _require_nonempty_str("top_terms[].term", item.get("term"))
        count = item.get("count")
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise ValueError("top_terms[].count must be a non-negative integer")
        normalized.append({"term": term, "count": count})
    return normalized


def _normalize_string_list(field_name: str, value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a sequence of strings")
    result: list[str] = []
    for item in value:
        result.append(_require_nonempty_str(field_name, item))
    return result


def _require_nonempty_str(field_name: str, value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{field_name} must be non-empty")
    return stripped


def _optional_nonempty_str(value: Any) -> str | None:
    if value is None:
        return None
    return _require_nonempty_str("value", value)


def _require_choice(field_name: str, value: Any, allowed: Sequence[str] | set[str] | frozenset[str]) -> str:
    normalized = _require_nonempty_str(field_name, value)
    if normalized not in allowed:
        raise ValueError(f"{field_name} must be one of {sorted(allowed)}")
    return normalized
