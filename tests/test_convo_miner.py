import json
import os
import shutil
import tempfile
from copy import deepcopy
from pathlib import Path

import chromadb

from mempalace.chatgpt_identity import extract_chatgpt_identity
from mempalace.convo_miner import mine_convos
from mempalace.palace import file_already_mined, get_collection


def _chatgpt_conversation(title: str, node_prefix: str, turns: list[tuple[str, str]]) -> dict:
    mapping = {"root": {"parent": None, "message": None, "children": []}}
    parent = "root"
    for idx, (question, answer) in enumerate(turns, 1):
        user_id = f"{node_prefix}_u{idx}"
        assistant_id = f"{node_prefix}_a{idx}"
        mapping[parent]["children"] = [user_id]
        mapping[user_id] = {
            "parent": parent,
            "message": {"author": {"role": "user"}, "content": {"parts": [question]}},
            "children": [assistant_id],
        }
        mapping[assistant_id] = {
            "parent": user_id,
            "message": {"author": {"role": "assistant"}, "content": {"parts": [answer]}},
            "children": [],
        }
        parent = assistant_id
    return {"title": title, "current_node": parent, "mapping": mapping}


def _write_conversations_json(directory: Path, conversations: list[dict]) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    export_path = directory / "conversations.json"
    export_path.write_text(json.dumps(conversations), encoding="utf-8")
    return export_path


def _load_drawers_by_source(palace_path: Path, source_file: str) -> dict:
    client = chromadb.PersistentClient(path=str(palace_path))
    col = client.get_collection("mempalace_drawers")
    return col.get(where={"source_file": source_file}, include=["documents", "metadatas"])


def test_convo_mining():
    tmpdir = tempfile.mkdtemp()
    with open(os.path.join(tmpdir, "chat.txt"), "w") as f:
        f.write(
            "> What is memory?\nMemory is persistence.\n\n> Why does it matter?\nIt enables continuity.\n\n> How do we build it?\nWith structured storage.\n"
        )

    palace_path = os.path.join(tmpdir, "palace")
    mine_convos(tmpdir, palace_path, wing="test_convos")

    client = chromadb.PersistentClient(path=palace_path)
    col = client.get_collection("mempalace_drawers")
    assert col.count() >= 2

    # Verify search works
    results = col.query(query_texts=["memory persistence"], n_results=1)
    assert len(results["documents"][0]) > 0

    shutil.rmtree(tmpdir, ignore_errors=True)


def test_mine_convos_does_not_reprocess_short_files(capsys):
    """Files below MIN_CHUNK_SIZE get a sentinel so they are skipped on re-run."""
    tmpdir = tempfile.mkdtemp()
    try:
        # A file too short to produce any chunks
        with open(os.path.join(tmpdir, "tiny.txt"), "w") as f:
            f.write("hi")

        palace_path = os.path.join(tmpdir, "palace")

        # First run -- file is processed (sentinel written)
        mine_convos(tmpdir, palace_path, wing="test")
        capsys.readouterr()  # drain output

        # Verify sentinel was written (resolve path -- macOS /var -> /private/var)
        resolved_file = str(Path(tmpdir).resolve() / "tiny.txt")
        client = chromadb.PersistentClient(path=palace_path)
        col = client.get_collection("mempalace_drawers")
        assert file_already_mined(col, resolved_file)

        # Second run -- file should be skipped
        mine_convos(tmpdir, palace_path, wing="test")
        out2 = capsys.readouterr().out
        assert "Files skipped (already filed): 1" in out2
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_mine_convos_does_not_reprocess_empty_chunk_files(capsys):
    """Files that normalize but produce 0 exchange chunks get a sentinel."""
    tmpdir = tempfile.mkdtemp()
    try:
        # Content long enough to pass MIN_CHUNK_SIZE but with no exchange markers
        # (no "> " lines), so chunk_exchanges returns []
        with open(os.path.join(tmpdir, "no_exchanges.txt"), "w") as f:
            f.write("This is a plain paragraph without any exchange markers. " * 5)

        palace_path = os.path.join(tmpdir, "palace")

        mine_convos(tmpdir, palace_path, wing="test")
        mine_convos(tmpdir, palace_path, wing="test")
        out2 = capsys.readouterr().out
        assert "Files skipped (already filed): 1" in out2
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_mine_convos_rebuilds_stale_drawers_after_schema_bump(capsys):
    """When stored drawers have an older normalize_version, the next mine
    silently purges them and refiles — no manual erase required.

    This is what makes the strip_noise upgrade apply to existing corpora:
    users just run `mempalace mine` again and old noise-filled drawers get
    replaced with clean ones."""
    from mempalace.palace import NORMALIZE_VERSION

    tmpdir = tempfile.mkdtemp()
    try:
        convo_path = Path(tmpdir) / "chat.txt"
        convo_path.write_text(
            "> What is memory?\nMemory is persistence.\n\n"
            "> Why does it matter?\nIt enables continuity.\n\n"
            "> How do we build it?\nWith structured storage.\n"
        )
        palace_path = os.path.join(tmpdir, "palace")

        # First mine — stamps drawers with NORMALIZE_VERSION
        mine_convos(tmpdir, palace_path, wing="test")
        capsys.readouterr()

        client = chromadb.PersistentClient(path=palace_path)
        col = client.get_collection("mempalace_drawers")
        resolved = str(Path(tmpdir).resolve() / "chat.txt")
        first_pass = col.get(where={"source_file": resolved})
        first_ids = set(first_pass["ids"])
        assert first_ids, "first mine should produce drawers"
        for meta in first_pass["metadatas"]:
            assert meta.get("normalize_version") == NORMALIZE_VERSION

        # Simulate pre-v2 drawers: rewrite metadata to an older version,
        # and replace content with "noise" so we can see it get cleaned up.
        stale_metas = []
        for meta in first_pass["metadatas"]:
            stale = dict(meta)
            stale["normalize_version"] = 1
            stale_metas.append(stale)
        col.update(
            ids=list(first_pass["ids"]),
            documents=["STALE NOISE"] * len(first_pass["ids"]),
            metadatas=stale_metas,
        )
        # Add an extra orphan drawer that should also be purged.
        col.add(
            ids=["orphan_drawer"],
            documents=["OLD ORPHAN"],
            metadatas=[
                {
                    "wing": "test",
                    "room": "default",
                    "source_file": resolved,
                    "chunk_index": 999,
                    "normalize_version": 1,
                }
            ],
        )
        del col, client

        # Second mine — version gate should trigger rebuild
        mine_convos(tmpdir, palace_path, wing="test")
        out = capsys.readouterr().out
        assert (
            "Files skipped (already filed): 0" in out
        ), "stale drawers should force a rebuild, not a skip"

        client = chromadb.PersistentClient(path=palace_path)
        col = client.get_collection("mempalace_drawers")
        rebuilt = col.get(where={"source_file": resolved})
        # Orphan is gone
        assert "orphan_drawer" not in rebuilt["ids"]
        # No stale content survived
        assert all("STALE NOISE" not in d for d in rebuilt["documents"])
        assert all("OLD ORPHAN" not in d for d in rebuilt["documents"])
        # All rebuilt drawers carry the current version
        for meta in rebuilt["metadatas"]:
            assert meta.get("normalize_version") == NORMALIZE_VERSION
        del col, client
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_mine_convos_rooms_chatgpt_privacy_export_per_thread(capsys):
    """A single conversations.json file can contain threads from different rooms."""
    tmpdir = tempfile.mkdtemp()
    try:
        export_path = Path(tmpdir) / "conversations.json"
        technical = _chatgpt_conversation(
            "Technical thread",
            "tech",
            [
                (
                    "Can you debug this Python API server error?",
                    "The bug is in the database function; add a test before refactor.",
                ),
                (
                    "What should the function do when the API fails?",
                    "Return a typed error and log the failing server response.",
                ),
                (
                    "How do we deploy the fix?",
                    "Run the test suite, commit the code, then deploy the patched server.",
                ),
            ],
        )
        technical["id"] = "technical-thread"
        planning = _chatgpt_conversation(
            "Planning thread",
            "plan",
            [
                (
                    "Can you help shape the roadmap and milestone plan?",
                    "Set the deadline, scope the backlog, and pick sprint priorities.",
                ),
                (
                    "What is the next requirement?",
                    "Define the launch milestone and keep one planning owner.",
                ),
                (
                    "How should we sequence the deadline work?",
                    "Prioritize the roadmap items before adding optional backlog scope.",
                ),
            ],
        )
        planning["id"] = "planning-thread"
        export_path.write_text(
            json.dumps([technical, planning])
        )
        palace_path = os.path.join(tmpdir, "palace")

        mine_convos(tmpdir, palace_path, wing="chatgpt")
        capsys.readouterr()

        technical_result = _load_drawers_by_source(Path(palace_path), "chatgpt:technical-thread")
        planning_result = _load_drawers_by_source(Path(palace_path), "chatgpt:planning-thread")
        rooms = {
            *(meta.get("room") for meta in technical_result["metadatas"]),
            *(meta.get("room") for meta in planning_result["metadatas"]),
        }

        assert "technical" in rooms
        assert "planning" in rooms
        assert all(
            meta.get("source_path") == str(export_path.resolve())
            for meta in technical_result["metadatas"] + planning_result["metadatas"]
        )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_mine_convos_chatgpt_overlap_dedupes_across_export_paths(tmp_path):
    export_a = tmp_path / "export-a"
    export_b = tmp_path / "export-b"
    palace_path = tmp_path / "palace"

    conversation = _chatgpt_conversation(
        "Overlap thread",
        "alpha",
        [
            (
                "Can you debug this Python API server error and keep the response structured?",
                "The bug is in the database function; add a test before refactor.",
            ),
            (
                "What should the function do when the API fails in production?",
                "Return a typed error and log the failing server response.",
            ),
            (
                "How do we deploy the fix without losing the old behavior?",
                "Run the test suite, commit the code, then deploy the patched server.",
            ),
        ],
    )
    conversation["id"] = "convo-123"

    _write_conversations_json(export_a, [conversation])
    mine_convos(str(export_a), str(palace_path), wing="chatgpt")

    logical_source = "chatgpt:convo-123"
    export_a_path = str((export_a / "conversations.json").resolve())
    first = _load_drawers_by_source(palace_path, logical_source)
    first_count = len(first["ids"])
    assert first_count > 0
    assert all(meta.get("source_file") == logical_source for meta in first["metadatas"])
    assert all(meta.get("logical_source_id") == logical_source for meta in first["metadatas"])
    assert all(meta.get("source_format") == "chatgpt" for meta in first["metadatas"])
    assert all(meta.get("source_path") == export_a_path for meta in first["metadatas"])

    _write_conversations_json(export_b, [conversation])
    mine_convos(str(export_b), str(palace_path), wing="chatgpt")

    second = _load_drawers_by_source(palace_path, logical_source)
    assert len(second["ids"]) == first_count
    assert all(meta.get("source_file") == logical_source for meta in second["metadatas"])
    assert all(meta.get("source_path") == export_a_path for meta in second["metadatas"])


def test_mine_convos_chatgpt_replace_updates_only_one_logical_source(tmp_path):
    export_a = tmp_path / "export-a"
    export_b = tmp_path / "export-b"
    palace_path = tmp_path / "palace"

    sibling = _chatgpt_conversation(
        "Sibling thread",
        "sibling",
        [
            (
                "Can you help shape the roadmap and milestone plan?",
                "Set the deadline, scope the backlog, and pick sprint priorities.",
            ),
            (
                "What is the next requirement?",
                "Define the launch milestone and keep one planning owner.",
            ),
            (
                "How should we sequence the deadline work?",
                "Prioritize the roadmap items before adding optional backlog scope.",
            ),
        ],
    )
    sibling["id"] = "sibling-456"

    original = _chatgpt_conversation(
        "Replaceable thread",
        "replace",
        [
            (
                "Can you debug this Python API server error and keep the response structured?",
                "The bug is in the database function; add a test before refactor.",
            ),
            (
                "What should the function do when the API fails in production?",
                "Return a typed error and log the failing server response.",
            ),
            (
                "How do we deploy the fix without losing the old behavior?",
                "Run the test suite, commit the code, then deploy the patched server.",
            ),
        ],
    )
    original["id"] = "replace-123"

    updated = deepcopy(original)
    updated["mapping"]["replace_a3"]["message"]["content"]["parts"] = [
        "Deploy the fix behind a feature flag and keep the old path as fallback."
    ]

    _write_conversations_json(export_a, [original, sibling])
    mine_convos(str(export_a), str(palace_path), wing="chatgpt")

    replaced_source = "chatgpt:replace-123"
    sibling_source = "chatgpt:sibling-456"
    export_a_path = str((export_a / "conversations.json").resolve())

    first_replaced = _load_drawers_by_source(palace_path, replaced_source)
    first_sibling = _load_drawers_by_source(palace_path, sibling_source)
    assert first_replaced["ids"]
    assert first_sibling["ids"]

    _write_conversations_json(export_b, [updated, sibling])
    mine_convos(str(export_b), str(palace_path), wing="chatgpt")

    second_replaced = _load_drawers_by_source(palace_path, replaced_source)
    second_sibling = _load_drawers_by_source(palace_path, sibling_source)

    replaced_docs = second_replaced["documents"]
    sibling_docs = second_sibling["documents"]
    assert any("feature flag" in doc for doc in replaced_docs)
    assert not any("patched server" in doc for doc in replaced_docs)
    assert any("patched server" in doc for doc in sibling_docs)
    assert not any("feature flag" in doc for doc in sibling_docs)
    assert all(meta.get("source_file") == replaced_source for meta in second_replaced["metadatas"])
    assert all(meta.get("source_path") == str((export_b / "conversations.json").resolve()) for meta in second_replaced["metadatas"])
    assert all(meta.get("source_file") == sibling_source for meta in second_sibling["metadatas"])
    assert all(meta.get("source_path") == export_a_path for meta in second_sibling["metadatas"])
    assert len(second_replaced["ids"]) == len(first_replaced["ids"])
    assert len(second_sibling["ids"]) == len(first_sibling["ids"])


def test_mine_convos_chatgpt_without_id_uses_mapping_digest_fallback(tmp_path):
    export_a = tmp_path / "export-a"
    export_b = tmp_path / "export-b"
    palace_path = tmp_path / "palace"

    conversation = _chatgpt_conversation(
        "Fallback thread",
        "fallback",
        [
            (
                "Can you debug this Python API server error and keep the response structured?",
                "The bug is in the database function; add a test before refactor.",
            ),
            (
                "What should the function do when the API fails in production?",
                "Return a typed error and log the failing server response.",
            ),
            (
                "How do we deploy the fix without losing the old behavior?",
                "Run the test suite, commit the code, then deploy the patched server.",
            ),
        ],
    )

    expected = extract_chatgpt_identity(conversation)
    assert expected is not None
    logical_source = expected.logical_source_id

    _write_conversations_json(export_a, [conversation])
    mine_convos(str(export_a), str(palace_path), wing="chatgpt")

    export_a_path = str((export_a / "conversations.json").resolve())
    first = _load_drawers_by_source(palace_path, logical_source)
    first_count = len(first["ids"])
    assert first_count > 0
    assert all(meta.get("source_file") == logical_source for meta in first["metadatas"])
    assert all(meta.get("source_path") == export_a_path for meta in first["metadatas"])

    _write_conversations_json(export_b, [conversation])
    mine_convos(str(export_b), str(palace_path), wing="chatgpt")

    second = _load_drawers_by_source(palace_path, logical_source)
    assert len(second["ids"]) == first_count
    assert all(meta.get("source_file") == logical_source for meta in second["metadatas"])
    assert all(meta.get("source_path") == export_a_path for meta in second["metadatas"])


def test_mine_convos_chatgpt_shaped_non_export_json_remains_path_based(tmp_path):
    source_dir = tmp_path / "json"
    palace_path = tmp_path / "palace"
    source_dir.mkdir()
    source_path = source_dir / "chatgpt.json"
    conversation = _chatgpt_conversation(
        "Path based JSON",
        "pathjson",
        [
            (
                "Can you debug this Python API server error?",
                "Add a test and patch the API server.",
            ),
            (
                "How do we deploy the fix?",
                "Commit the code and deploy the patched server.",
            ),
            (
                "What should we preserve?",
                "Keep the old API behavior behind a fallback.",
            ),
        ],
    )
    conversation["id"] = "path-json-123"
    source_path.write_text(json.dumps([conversation]), encoding="utf-8")

    mine_convos(str(source_dir), str(palace_path), wing="chatgpt")

    resolved = str(source_path.resolve())
    path_drawers = _load_drawers_by_source(palace_path, resolved)
    logical_drawers = _load_drawers_by_source(palace_path, "chatgpt:path-json-123")
    assert path_drawers["ids"]
    assert logical_drawers["ids"] == []
    assert all(meta.get("source_file") == resolved for meta in path_drawers["metadatas"])


def test_mine_convos_chatgpt_grandfathers_path_keyed_drawers(tmp_path):
    source_dir = tmp_path / "export"
    palace_path = tmp_path / "palace"
    conversation = _chatgpt_conversation(
        "Grandfathered",
        "grandfather",
        [
            (
                "Can you debug this Python API server error?",
                "Add a test and patch the API server.",
            ),
            (
                "How do we deploy the fix?",
                "Commit the code and deploy the patched server.",
            ),
            (
                "What should we preserve?",
                "Keep the old API behavior behind a fallback.",
            ),
        ],
    )
    conversation["id"] = "grandfather-123"
    export_path = _write_conversations_json(source_dir, [conversation])

    col = get_collection(str(palace_path))
    old_source = str(export_path.resolve())
    col.add(
        ids=["legacy_path_drawer"],
        documents=["legacy path keyed drawer"],
        metadatas=[
            {
                "wing": "chatgpt",
                "room": "technical",
                "source_file": old_source,
                "chunk_index": 0,
                "normalize_version": 2,
            }
        ],
    )

    mine_convos(str(source_dir), str(palace_path), wing="chatgpt")

    legacy = _load_drawers_by_source(palace_path, old_source)
    logical = _load_drawers_by_source(palace_path, "chatgpt:grandfather-123")
    assert "legacy_path_drawer" in legacy["ids"]
    assert logical["ids"]


def test_mine_convos_non_chatgpt_remains_path_based(tmp_path):
    source_dir = tmp_path / "plain"
    palace_path = tmp_path / "palace"
    source_dir.mkdir()
    transcript = (
        "> What is memory?\n"
        "Memory is persistence of information over time.\n\n"
        "> Why does it matter?\n"
        "It enables continuity across sessions and conversations.\n\n"
        "> How do we build it?\n"
        "With structured storage and retrieval mechanisms.\n"
    )
    source_path = source_dir / "chat.txt"
    source_path.write_text(transcript, encoding="utf-8")

    mine_convos(str(source_dir), str(palace_path), wing="plain")

    resolved = str(source_path.resolve())
    drawers = _load_drawers_by_source(palace_path, resolved)
    assert drawers["ids"]
    assert all(meta.get("source_file") == resolved for meta in drawers["metadatas"])
