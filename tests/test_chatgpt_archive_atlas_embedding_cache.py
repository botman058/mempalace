from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any

import pytest

from mempalace import chatgpt_archive_atlas_contract as contract

_embedding_cache_module = pytest.importorskip(
    "mempalace.chatgpt_archive_atlas_embedding_cache",
    reason="embedding cache implementation is not present yet",
)
ChatGPTAtlasEmbeddingCacheResult = _embedding_cache_module.ChatGPTAtlasEmbeddingCacheResult
build_embedding_source_text = _embedding_cache_module.build_embedding_source_text
materialize_chatgpt_thread_embedding_cache = (
    _embedding_cache_module.materialize_chatgpt_thread_embedding_cache
)


def _make_lexical_row(thread_id: str, *, keyphrase: str, excerpt: str) -> dict[str, Any]:
    return contract.build_lexical_sketch_row(
        run_id="run-wp08",
        thread_id=thread_id,
        logical_source_id=f"chatgpt:source:{thread_id}",
        top_terms=[{"term": "cache", "count": 3}, {"term": "embed", "count": 2}],
        keyphrases=[keyphrase],
        domains=["example.com"],
        paths=["/tmp/example.txt"],
        commands=["echo cache"],
        package_names=["numpy"],
        model_names=["all-MiniLM-L6-v2"],
        legal_citations=["17 USC 512"],
        capitalized_phrases=["ChatGPT"],
        representative_excerpts=[excerpt],
        noise_terms_rejected=["the"],
    )


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class RecordingFakeEmbedder:
    def __init__(self, *, dimensions: int = 3) -> None:
        self.calls: list[list[str]] = []
        self.dimensions = dimensions

    def __call__(self, texts: list[str], *args: Any, **kwargs: Any) -> list[list[float]]:
        batch = [str(item) for item in texts]
        self.calls.append(batch)
        vectors: list[list[float]] = []
        for text in batch:
            base = float(len(text))
            vectors.append([base + float(i) for i in range(self.dimensions)])
        return vectors

    @property
    def batch_sizes(self) -> list[int]:
        return [len(batch) for batch in self.calls]


def test_public_api_dataclass_is_frozen_and_tuple_backed() -> None:
    assert dataclasses.is_dataclass(ChatGPTAtlasEmbeddingCacheResult)
    result = ChatGPTAtlasEmbeddingCacheResult(
        metadata_rows=(),
        vector_rows=(),
        metadata_path=Path("thread_embeddings.jsonl"),
        vectors_path=Path("thread_embedding_vectors.jsonl"),
        effective_device="cpu",
        embedded_count=0,
        skipped_count=0,
        source_errors=(),
    )
    assert isinstance(result.metadata_rows, tuple)
    assert isinstance(result.vector_rows, tuple)
    assert isinstance(result.source_errors, tuple)
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.metadata_rows = ()


def test_fake_embedder_materializes_cache_files_with_contract_rows(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    rows = (
        _make_lexical_row("thread-001", keyphrase="alpha keyphrase", excerpt="excerpt alpha"),
        _make_lexical_row("thread-002", keyphrase="beta keyphrase", excerpt="excerpt beta"),
    )
    embedder = RecordingFakeEmbedder(dimensions=4)

    result = materialize_chatgpt_thread_embedding_cache(
        rows,
        run_dir,
        run_id="run-wp08",
        embedding_function=embedder,
        effective_device="cuda",
        batch_size=2,
    )

    assert result.metadata_path == run_dir / "thread_embeddings.jsonl"
    assert result.vectors_path == run_dir / "thread_embedding_vectors.jsonl"
    assert result.metadata_path.exists()
    assert result.vectors_path.exists()
    assert result.embedded_count == 2
    assert result.skipped_count == 0
    assert result.source_errors == ()
    assert result.effective_device == "cuda"

    metadata_rows = _read_jsonl(result.metadata_path)
    vector_rows = _read_jsonl(result.vectors_path)
    assert len(metadata_rows) == len(rows) == len(vector_rows)
    for metadata_row in metadata_rows:
        assert contract.validate_row(contract.THREAD_EMBEDDING_METADATA_SCHEMA, metadata_row) == metadata_row
        assert metadata_row["safety_contract"] == contract.safety_contract()
        assert metadata_row["effective_device"] == "cuda"
        assert metadata_row["vector_dimensions"] == 4
    for vector_row in vector_rows:
        assert len(vector_row["vector"]) == 4


def test_resume_idempotency_does_not_reembed_existing_rows(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    rows = (
        _make_lexical_row("thread-001", keyphrase="alpha keyphrase", excerpt="excerpt alpha"),
        _make_lexical_row("thread-002", keyphrase="beta keyphrase", excerpt="excerpt beta"),
    )
    embedder = RecordingFakeEmbedder()

    first = materialize_chatgpt_thread_embedding_cache(
        rows,
        run_dir,
        run_id="run-wp08",
        embedding_function=embedder,
        batch_size=2,
        force=False,
    )
    calls_after_first = len(embedder.calls)
    second = materialize_chatgpt_thread_embedding_cache(
        rows,
        run_dir,
        run_id="run-wp08",
        embedding_function=embedder,
        batch_size=2,
        force=False,
    )

    assert calls_after_first > 0
    assert len(embedder.calls) == calls_after_first
    assert first.metadata_rows == second.metadata_rows
    assert first.vector_rows == second.vector_rows
    assert second.embedded_count == 0
    assert second.skipped_count == len(rows)


def test_partial_resume_embeds_only_missing_rows(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    row_a = _make_lexical_row("thread-001", keyphrase="alpha keyphrase", excerpt="excerpt alpha")
    row_b = _make_lexical_row("thread-002", keyphrase="beta keyphrase", excerpt="excerpt beta")
    row_c = _make_lexical_row("thread-003", keyphrase="gamma keyphrase", excerpt="excerpt gamma")
    embedder = RecordingFakeEmbedder()

    materialize_chatgpt_thread_embedding_cache(
        (row_a, row_b),
        run_dir,
        run_id="run-wp08",
        embedding_function=embedder,
        batch_size=2,
        force=False,
    )
    calls_after_seed = len(embedder.calls)

    result = materialize_chatgpt_thread_embedding_cache(
        (row_a, row_b, row_c),
        run_dir,
        run_id="run-wp08",
        embedding_function=embedder,
        batch_size=2,
        force=False,
    )

    assert len(embedder.calls) == calls_after_seed + 1
    assert embedder.calls[-1] == [build_embedding_source_text(row_c)]
    assert result.embedded_count == 1
    assert result.skipped_count == 2


def test_batch_sizes_never_exceed_batch_size(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    rows = tuple(
        _make_lexical_row(
            f"thread-{index:03d}",
            keyphrase=f"keyphrase {index}",
            excerpt=f"excerpt {index}",
        )
        for index in range(7)
    )
    embedder = RecordingFakeEmbedder()

    materialize_chatgpt_thread_embedding_cache(
        rows,
        run_dir,
        run_id="run-wp08",
        embedding_function=embedder,
        batch_size=3,
    )

    assert embedder.batch_sizes
    assert max(embedder.batch_sizes) <= 3
    assert sum(embedder.batch_sizes) == len(rows)


def test_source_text_and_hash_are_deterministic_and_change_with_source_text(tmp_path: Path) -> None:
    base = _make_lexical_row("thread-001", keyphrase="alpha keyphrase", excerpt="excerpt alpha")
    same_content = _make_lexical_row("thread-001", keyphrase="alpha keyphrase", excerpt="excerpt alpha")
    changed_content = _make_lexical_row("thread-001", keyphrase="changed keyphrase", excerpt="excerpt alpha")

    assert build_embedding_source_text(base) == build_embedding_source_text(same_content)
    assert build_embedding_source_text(base) != build_embedding_source_text(changed_content)

    run_a = tmp_path / "run-a"
    run_b = tmp_path / "run-b"
    embedder = RecordingFakeEmbedder()

    result_a = materialize_chatgpt_thread_embedding_cache(
        (base,),
        run_a,
        run_id="run-wp08-a",
        embedding_function=embedder,
        force=True,
    )
    result_b = materialize_chatgpt_thread_embedding_cache(
        (changed_content,),
        run_b,
        run_id="run-wp08-b",
        embedding_function=embedder,
        force=True,
    )

    meta_a = result_a.metadata_rows[0]
    meta_b = result_b.metadata_rows[0]
    assert meta_a["source_text_sha256"] != meta_b["source_text_sha256"]
    assert meta_a["embedding_id"] != meta_b["embedding_id"]
