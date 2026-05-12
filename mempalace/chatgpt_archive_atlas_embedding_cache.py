from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from . import chatgpt_archive_atlas_contract as contract

_METADATA_FILENAME = "thread_embeddings.jsonl"
_VECTORS_FILENAME = "thread_embedding_vectors.jsonl"
_SOURCE_ERROR_SCHEMA = "chatgpt_archive_atlas.embedding_cache_error.v1"
_CHROMA_ONNX_MODEL_NAME = "all-MiniLM-L6-v2"
_CHROMA_ONNX_REQUIRED_FILES = (
    "config.json",
    "model.onnx",
    "special_tokens_map.json",
    "tokenizer_config.json",
    "tokenizer.json",
    "vocab.txt",
)


@dataclass(frozen=True)
class ChatGPTAtlasEmbeddingCacheResult:
    metadata_rows: tuple[dict[str, Any], ...]
    vector_rows: tuple[dict[str, Any], ...]
    metadata_path: Path
    vectors_path: Path
    effective_device: str
    embedded_count: int
    skipped_count: int
    source_errors: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class _EmbeddingRequest:
    order_index: int
    thread_id: str
    embedding_id: str
    source_text: str
    source_text_sha256: str
    source_text_chars: int


def build_embedding_source_text(lexical_row) -> str:
    if not isinstance(lexical_row, Mapping):
        raise ValueError("lexical_row must be a mapping")

    sections: list[tuple[str, str]] = []

    title = _first_nonempty_str(
        lexical_row.get("conversation_title"),
        lexical_row.get("title_hint"),
    )
    if title is not None:
        sections.append(("Title", title))

    sections.extend(
        (
            ("Keyphrases", _join_list(_normalize_string_list(lexical_row.get("keyphrases")))),
            ("Top terms", _format_top_terms(lexical_row.get("top_terms"))),
            ("Project terms", _join_list(_normalize_string_list(lexical_row.get("project_terms")))),
            ("Domains", _join_list(_normalize_string_list(lexical_row.get("domains")))),
            ("Paths", _join_list(_normalize_string_list(lexical_row.get("paths")))),
            ("Commands", _join_list(_normalize_string_list(lexical_row.get("commands")))),
            ("Packages", _join_list(_normalize_string_list(lexical_row.get("package_names")))),
            ("Models", _join_list(_normalize_string_list(lexical_row.get("model_names")))),
            (
                "Legal citations",
                _join_list(_normalize_string_list(lexical_row.get("legal_citations"))),
            ),
            (
                "Named entities",
                _join_list(_normalize_string_list(lexical_row.get("person_org_candidates"))),
            ),
            ("Dates", _join_list(_normalize_string_list(lexical_row.get("dates")))),
            (
                "Capitalized phrases",
                _join_list(_normalize_string_list(lexical_row.get("capitalized_phrases"))),
            ),
        )
    )

    excerpts = _normalize_string_list(lexical_row.get("representative_excerpts"))
    if excerpts:
        sections.append(("Representative excerpts", "\n".join(f"- {item}" for item in excerpts)))

    rendered = [f"{label}: {value}" for label, value in sections if value]
    if not rendered:
        fallback = _first_nonempty_str(
            lexical_row.get("thread_id"),
            lexical_row.get("logical_source_id"),
        )
        if fallback is not None:
            rendered.append(f"Thread: {fallback}")
    return "\n".join(rendered).strip()


def materialize_chatgpt_thread_embedding_cache(
    lexical_rows,
    run_dir,
    *,
    run_id: str,
    embedding_function=None,
    embedding_model: str = "all-MiniLM-L6-v2",
    requested_device: str | None = None,
    effective_device: str | None = None,
    batch_size: int = 32,
    force: bool = False,
) -> ChatGPTAtlasEmbeddingCacheResult:
    contract.build_progress(run_id=run_id, phase="thread_embeddings", status="pending")
    batch_limit = _validate_batch_size(batch_size)
    resolved_device = _resolve_effective_device(
        embedding_function=embedding_function,
        requested_device=requested_device,
        effective_device=effective_device,
    )

    output_dir = Path(run_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = output_dir / _METADATA_FILENAME
    vectors_path = output_dir / _VECTORS_FILENAME

    requests, source_errors, duplicate_count = _build_embedding_requests(lexical_rows)
    if not requests:
        return ChatGPTAtlasEmbeddingCacheResult(
            metadata_rows=(),
            vector_rows=(),
            metadata_path=metadata_path,
            vectors_path=vectors_path,
            effective_device=resolved_device,
            embedded_count=0,
            skipped_count=0,
            source_errors=tuple(source_errors),
        )

    _, metadata_by_key, metadata_errors = _load_existing_metadata_rows(metadata_path)
    _, vector_by_key, vector_errors = _load_existing_vector_rows(vectors_path)
    source_errors.extend(metadata_errors)
    source_errors.extend(vector_errors)

    covered_keys = _covered_request_keys(requests, metadata_by_key, vector_by_key)
    if covered_keys == {request.embedding_id for request in requests} and not force:
        metadata_rows, vector_rows = _collect_result_rows(requests, metadata_by_key, vector_by_key)
        return ChatGPTAtlasEmbeddingCacheResult(
            metadata_rows=metadata_rows,
            vector_rows=vector_rows,
            metadata_path=metadata_path,
            vectors_path=vectors_path,
            effective_device=resolved_device,
            embedded_count=0,
            skipped_count=len(requests) + duplicate_count,
            source_errors=tuple(source_errors),
        )

    pending = [
        request
        for request in requests
        if force or request.embedding_id not in covered_keys
    ]

    if pending:
        embedder = _resolve_embedder(
            embedding_function=embedding_function,
            embedding_model=embedding_model,
            requested_device=requested_device,
        )
        for batch_index, start in enumerate(range(0, len(pending), batch_limit)):
            batch = pending[start : start + batch_limit]
            texts = [request.source_text for request in batch]
            embeddings = _call_embedding_function(embedder, texts)
            if len(embeddings) != len(batch):
                raise ValueError(
                    "embedding_function returned a different number of vectors than source texts"
                )

            new_metadata_rows: list[dict[str, Any]] = []
            new_vector_rows: list[dict[str, Any]] = []
            for request, raw_vector in zip(batch, embeddings):
                vector = _normalize_vector(raw_vector)
                vector_dimensions = len(vector)
                metadata_row = contract.build_thread_embedding_metadata_row(
                    run_id=run_id,
                    thread_id=request.thread_id,
                    embedding_id=request.embedding_id,
                    embedding_model=embedding_model,
                    effective_device=resolved_device,
                    vector_dimensions=vector_dimensions,
                    source_text_sha256=request.source_text_sha256,
                    source_text_chars=request.source_text_chars,
                    batch_index=batch_index,
                    status="embedded",
                )
                vector_row = _build_vector_row(
                    run_id=run_id,
                    thread_id=request.thread_id,
                    embedding_id=request.embedding_id,
                    embedding_model=embedding_model,
                    effective_device=resolved_device,
                    source_text_sha256=request.source_text_sha256,
                    source_text_chars=request.source_text_chars,
                    vector_dimensions=vector_dimensions,
                    batch_index=batch_index,
                    status="embedded",
                    vector=vector,
                )
                new_metadata_rows.append(metadata_row)
                new_vector_rows.append(vector_row)
                metadata_by_key[request.embedding_id] = metadata_row
                vector_by_key[request.embedding_id] = vector_row

            _append_metadata_rows(metadata_path, new_metadata_rows)
            _append_vector_rows(vectors_path, new_vector_rows)

    metadata_rows, vector_rows = _collect_result_rows(requests, metadata_by_key, vector_by_key)
    return ChatGPTAtlasEmbeddingCacheResult(
        metadata_rows=metadata_rows,
        vector_rows=vector_rows,
        metadata_path=metadata_path,
        vectors_path=vectors_path,
        effective_device=resolved_device,
        embedded_count=len(pending),
        skipped_count=(len(requests) - len(pending)) + duplicate_count,
        source_errors=tuple(source_errors),
    )


def _build_embedding_requests(
    lexical_rows: Iterable[Mapping[str, Any]],
) -> tuple[list[_EmbeddingRequest], list[dict[str, Any]], int]:
    requests: list[_EmbeddingRequest] = []
    source_errors: list[dict[str, Any]] = []
    seen_embedding_ids: set[str] = set()
    duplicate_count = 0

    for index, lexical_row in enumerate(lexical_rows):
        if not isinstance(lexical_row, Mapping):
            source_errors.append(
                _build_source_error(
                    index=index,
                    thread_id=None,
                    error_code="lexical_row_type_error",
                    error_detail=f"lexical row must be a mapping, got {type(lexical_row).__name__}",
                )
            )
            continue

        try:
            contract.validate_row(contract.LEXICAL_SKETCH_SCHEMA, lexical_row)
            thread_id = _require_nonempty_str("thread_id", lexical_row.get("thread_id"))
            source_text = build_embedding_source_text(lexical_row)
            if not source_text:
                raise ValueError("embedding source text is empty")
            source_text_sha256 = _sha256_text(source_text)
            embedding_id = _build_embedding_id(thread_id, source_text_sha256)
        except (TypeError, ValueError) as exc:
            source_errors.append(
                _build_source_error(
                    index=index,
                    thread_id=_safe_nonempty_str(lexical_row.get("thread_id")),
                    error_code="lexical_row_validation_error",
                    error_detail=str(exc),
                )
            )
            continue

        if embedding_id in seen_embedding_ids:
            duplicate_count += 1
            continue
        seen_embedding_ids.add(embedding_id)
        requests.append(
            _EmbeddingRequest(
                order_index=index,
                thread_id=thread_id,
                embedding_id=embedding_id,
                source_text=source_text,
                source_text_sha256=source_text_sha256,
                source_text_chars=len(source_text),
            )
        )

    return requests, source_errors, duplicate_count


def _resolve_effective_device(
    *,
    embedding_function,
    requested_device: str | None,
    effective_device: str | None,
) -> str:
    if embedding_function is None:
        from . import embedding

        return embedding.describe_device(requested_device)

    return _normalize_effective_device(effective_device, requested_device)


def _resolve_embedder(
    *,
    embedding_function,
    embedding_model: str,
    requested_device: str | None,
):
    if embedding_function is None:
        _ensure_local_embedding_model_cache_ready(embedding_model)
        from . import embedding

        return embedding.get_embedding_function(requested_device)

    return embedding_function


def _normalize_effective_device(
    effective_device: str | None,
    requested_device: str | None,
) -> str:
    device = _first_nonempty_str(effective_device, requested_device)
    if device is None:
        return "injected"
    return device


def _ensure_local_embedding_model_cache_ready(embedding_model: str) -> Path:
    if embedding_model != _CHROMA_ONNX_MODEL_NAME:
        raise RuntimeError(
            "embedding_function=None only supports the pre-warmed local Chroma ONNX model "
            f"{_CHROMA_ONNX_MODEL_NAME!r}; inject an embedding function for "
            f"{embedding_model!r}."
        )

    extracted_dir = _local_chroma_onnx_model_dir(embedding_model)
    missing_files = [
        filename
        for filename in _CHROMA_ONNX_REQUIRED_FILES
        if not (extracted_dir / filename).is_file()
    ]
    if missing_files:
        missing = ", ".join(missing_files)
        raise RuntimeError(
            "Local embedding model cache is incomplete. Pre-warm the Chroma ONNX model "
            f"{embedding_model!r} under {extracted_dir} with files: {missing}; "
            "or inject an embedding_function."
        )
    return extracted_dir


def _assert_local_embedding_model_cache_available(embedding_model: str) -> Path:
    return _ensure_local_embedding_model_cache_ready(embedding_model)


def _local_chroma_onnx_model_dir(embedding_model: str) -> Path:
    return Path.home() / ".cache" / "chroma" / "onnx_models" / embedding_model / "onnx"


def _covered_request_keys(
    requests: Sequence[_EmbeddingRequest],
    metadata_by_key: Mapping[str, dict[str, Any]],
    vector_by_key: Mapping[str, dict[str, Any]],
) -> set[str]:
    covered: set[str] = set()
    for request in requests:
        metadata_row = metadata_by_key.get(request.embedding_id)
        vector_row = vector_by_key.get(request.embedding_id)
        if metadata_row is None or vector_row is None:
            continue
        if metadata_row.get("status") not in {"embedded", "skipped"}:
            continue
        if metadata_row.get("thread_id") != request.thread_id:
            continue
        if metadata_row.get("source_text_sha256") != request.source_text_sha256:
            continue
        if vector_row.get("thread_id") != request.thread_id:
            continue
        if vector_row.get("source_text_sha256") != request.source_text_sha256:
            continue
        if vector_row.get("status") not in {"embedded", "skipped"}:
            continue
        vector = vector_row.get("vector")
        if not isinstance(vector, list) or len(vector) != metadata_row.get("vector_dimensions"):
            continue
        covered.add(request.embedding_id)
    return covered


def _collect_result_rows(
    requests: Sequence[_EmbeddingRequest],
    metadata_by_key: Mapping[str, dict[str, Any]],
    vector_by_key: Mapping[str, dict[str, Any]],
) -> tuple[tuple[dict[str, Any], ...], tuple[dict[str, Any], ...]]:
    metadata_rows: list[dict[str, Any]] = []
    vector_rows: list[dict[str, Any]] = []
    for request in requests:
        metadata_row = metadata_by_key.get(request.embedding_id)
        vector_row = vector_by_key.get(request.embedding_id)
        if metadata_row is not None:
            metadata_rows.append(dict(metadata_row))
        if vector_row is not None:
            vector_rows.append(dict(vector_row))
    return tuple(metadata_rows), tuple(vector_rows)


def _load_existing_metadata_rows(
    path: Path,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    by_key: dict[str, dict[str, Any]] = {}
    errors: list[dict[str, Any]] = []

    for line_number, row, parse_error in _iter_jsonl_rows(path):
        if parse_error is not None:
            errors.append(
                _build_source_error(
                    index=line_number - 1,
                    thread_id=None,
                    error_code="metadata_cache_parse_error",
                    error_detail=parse_error,
                    relative_path=path.name,
                )
            )
            continue
        if row is None:
            continue
        try:
            normalized = contract.validate_row(contract.THREAD_EMBEDDING_METADATA_SCHEMA, row)
        except ValueError as exc:
            errors.append(
                _build_source_error(
                    index=line_number - 1,
                    thread_id=_safe_nonempty_str(row.get("thread_id")),
                    error_code="metadata_cache_validation_error",
                    error_detail=str(exc),
                    relative_path=path.name,
                )
            )
            continue
        rows.append(normalized)
        embedding_id = normalized.get("embedding_id")
        if isinstance(embedding_id, str) and embedding_id:
            by_key[embedding_id] = normalized

    return rows, by_key, errors


def _load_existing_vector_rows(
    path: Path,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    by_key: dict[str, dict[str, Any]] = {}
    errors: list[dict[str, Any]] = []

    for line_number, row, parse_error in _iter_jsonl_rows(path):
        if parse_error is not None:
            errors.append(
                _build_source_error(
                    index=line_number - 1,
                    thread_id=None,
                    error_code="vector_cache_parse_error",
                    error_detail=parse_error,
                    relative_path=path.name,
                )
            )
            continue
        if row is None:
            continue
        try:
            normalized = _validate_vector_row(row)
        except ValueError as exc:
            errors.append(
                _build_source_error(
                    index=line_number - 1,
                    thread_id=_safe_nonempty_str(row.get("thread_id")),
                    error_code="vector_cache_validation_error",
                    error_detail=str(exc),
                    relative_path=path.name,
                )
            )
            continue
        rows.append(normalized)
        by_key[normalized["embedding_id"]] = normalized

    return rows, by_key, errors


def _iter_jsonl_rows(path: Path):
    if not path.exists():
        return
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                yield line_number, None, str(exc)
                continue
            if not isinstance(payload, dict):
                yield line_number, None, "JSONL row must be an object"
                continue
            yield line_number, payload, None


def _append_metadata_rows(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        return
    with path.open("a", encoding="utf-8", newline="") as handle:
        for row in rows:
            handle.write(contract.canonical_json_line(row))


def _append_vector_rows(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        return
    with path.open("a", encoding="utf-8", newline="") as handle:
        for row in rows:
            contract.validate_json_safe(row)
            handle.write(json.dumps(row, ensure_ascii=True, separators=(",", ":"), sort_keys=True))
            handle.write("\n")


def _build_vector_row(
    *,
    run_id: str,
    thread_id: str,
    embedding_id: str,
    embedding_model: str,
    effective_device: str,
    source_text_sha256: str,
    source_text_chars: int,
    vector_dimensions: int,
    batch_index: int,
    status: str,
    vector: Sequence[float],
) -> dict[str, Any]:
    row = {
        "run_id": run_id,
        "thread_id": thread_id,
        "embedding_id": embedding_id,
        "embedding_model": embedding_model,
        "effective_device": effective_device,
        "source_text_sha256": source_text_sha256,
        "source_text_chars": source_text_chars,
        "vector_dimensions": vector_dimensions,
        "batch_index": batch_index,
        "status": status,
        "vector": list(vector),
    }
    contract.validate_json_safe(row)
    return row


def _validate_vector_row(row: Mapping[str, Any]) -> dict[str, Any]:
    embedding_id = _require_nonempty_str("embedding_id", row.get("embedding_id"))
    thread_id = _require_nonempty_str("thread_id", row.get("thread_id"))
    embedding_model = _require_nonempty_str("embedding_model", row.get("embedding_model"))
    effective_device = _require_nonempty_str("effective_device", row.get("effective_device"))
    source_text_sha256 = _require_nonempty_str("source_text_sha256", row.get("source_text_sha256"))
    source_text_chars = _require_nonnegative_int("source_text_chars", row.get("source_text_chars"))
    vector_dimensions = _require_nonnegative_int("vector_dimensions", row.get("vector_dimensions"))
    batch_index = _require_nonnegative_int("batch_index", row.get("batch_index"))
    status = _require_nonempty_str("status", row.get("status"))
    if status not in {"embedded", "skipped"}:
        raise ValueError("status must be 'embedded' or 'skipped'")
    vector = _normalize_vector(row.get("vector"))
    if len(vector) != vector_dimensions:
        raise ValueError("vector_dimensions must match the vector length")
    normalized = {
        "run_id": row.get("run_id"),
        "thread_id": thread_id,
        "embedding_id": embedding_id,
        "embedding_model": embedding_model,
        "effective_device": effective_device,
        "source_text_sha256": source_text_sha256,
        "source_text_chars": source_text_chars,
        "vector_dimensions": vector_dimensions,
        "batch_index": batch_index,
        "status": status,
        "vector": vector,
    }
    contract.validate_json_safe(normalized)
    return normalized


def _call_embedding_function(embedding_function, texts: Sequence[str]) -> Sequence[Any]:
    if callable(embedding_function):
        return embedding_function(list(texts))
    embed_documents = getattr(embedding_function, "embed_documents", None)
    if callable(embed_documents):
        return embed_documents(list(texts))
    raise ValueError("embedding_function must be callable or expose embed_documents(texts)")


def _normalize_vector(raw_vector: Any) -> list[float]:
    if hasattr(raw_vector, "tolist"):
        raw_vector = raw_vector.tolist()
    if not isinstance(raw_vector, Sequence) or isinstance(raw_vector, (str, bytes, bytearray)):
        raise ValueError("embedding vector must be a numeric sequence")
    vector: list[float] = []
    for index, value in enumerate(raw_vector):
        if isinstance(value, bool):
            raise ValueError(f"embedding vector item {index} must be numeric")
        if isinstance(value, int):
            vector.append(float(value))
            continue
        if isinstance(value, float):
            if not math.isfinite(value):
                raise ValueError(f"embedding vector item {index} must be finite")
            vector.append(value)
            continue
        raise ValueError(f"embedding vector item {index} must be numeric")
    return vector


def _validate_batch_size(batch_size: int) -> int:
    if not isinstance(batch_size, int) or isinstance(batch_size, bool) or batch_size <= 0:
        raise ValueError("batch_size must be a positive integer")
    return batch_size


def _sha256_text(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def _build_embedding_id(thread_id: str, source_text_sha256: str) -> str:
    return f"{thread_id}:{source_text_sha256}"


def _build_source_error(
    *,
    index: int,
    thread_id: str | None,
    error_code: str,
    error_detail: str,
    relative_path: str | None = None,
) -> dict[str, Any]:
    row = {
        "schema": _SOURCE_ERROR_SCHEMA,
        "source_index": index,
        "thread_id": thread_id,
        "relative_path": relative_path,
        "error_code": error_code,
        "error_detail": error_detail,
    }
    contract.validate_json_safe(row)
    return row


def _normalize_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ValueError("expected a sequence of strings")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError("expected a sequence of strings")
        if item:
            result.append(item)
    return result


def _format_top_terms(value: Any) -> str:
    if value is None:
        return ""
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ValueError("top_terms must be a sequence")
    items: list[str] = []
    for entry in value:
        if not isinstance(entry, Mapping):
            raise ValueError("top_terms entries must be mappings")
        term = _require_nonempty_str("top_terms.term", entry.get("term"))
        count = _require_nonnegative_int("top_terms.count", entry.get("count"))
        items.append(f"{term} ({count})")
    return _join_list(items)


def _join_list(items: Sequence[str]) -> str:
    return ", ".join(item for item in items if item)


def _first_nonempty_str(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _safe_nonempty_str(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value
    return None


def _require_nonempty_str(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _require_nonnegative_int(name: str, value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value
