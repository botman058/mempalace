import os
import tempfile
import shutil
import json
from pathlib import Path

import chromadb

from mempalace.convo_miner import (
    _split_normalized_transcripts,
    detect_convo_room,
    mine_convos,
    wing_from_codex_cwd,
)
from mempalace.normalize import TRANSCRIPT_SEPARATOR
from mempalace.palace import file_already_mined


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


def test_codex_wing_from_cwd():
    tmpdir = tempfile.mkdtemp()
    try:
        transcript = Path(tmpdir) / "rollout.jsonl"
        transcript.write_text(
            json.dumps(
                {
                    "type": "session_meta",
                    "payload": {"cwd": "/home/app/repos/mempalace"},
                }
            )
            + "\n",
            encoding="utf-8",
        )

        assert wing_from_codex_cwd(transcript, fallback="sessions") == "mempalace"
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_detect_convo_room_prefers_specific_rooms():
    assert detect_convo_room("pytest fixture assertion coverage smoke") == "tests"
    assert detect_convo_room("commit branch push pull request diff") == "git"
    assert detect_convo_room("README docs devlog handoff markdown") == "docs"


def test_mine_codex_convos_can_use_cwd_wings_and_chunk_rooms():
    tmpdir = tempfile.mkdtemp()
    try:
        transcript = Path(tmpdir) / "rollout.jsonl"
        lines = [
            {"type": "session_meta", "payload": {"cwd": "/home/app/repos/tako"}},
            {
                "type": "event_msg",
                "payload": {"type": "user_message", "message": "Please update pytest fixtures"},
            },
            {
                "type": "event_msg",
                "payload": {
                    "type": "agent_message",
                    "message": "I added a pytest fixture and assertion coverage.",
                },
            },
            {
                "type": "event_msg",
                "payload": {"type": "user_message", "message": "Now commit and push the branch"},
            },
            {
                "type": "event_msg",
                "payload": {
                    "type": "agent_message",
                    "message": "I checked git diff, committed, and pushed the branch.",
                },
            },
        ]
        transcript.write_text("\n".join(json.dumps(line) for line in lines), encoding="utf-8")

        palace_path = os.path.join(tmpdir, "palace")
        mine_convos(tmpdir, palace_path, wing_by_cwd=True)

        client = chromadb.PersistentClient(path=palace_path)
        col = client.get_collection("mempalace_drawers")
        result = col.get()
        metas = result["metadatas"]
        assert {m["wing"] for m in metas} == {"tako"}
        assert {"tests", "git"}.issubset({m["room"] for m in metas})
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_split_normalized_transcripts():
    one = "just one thread"
    assert _split_normalized_transcripts(one) == [one]

    joined = f"thread A{TRANSCRIPT_SEPARATOR}thread B{TRANSCRIPT_SEPARATOR}  "
    assert _split_normalized_transcripts(joined) == ["thread A", "thread B"]


def test_mine_chatgpt_multi_conversation_export_does_not_collapse_rooms():
    """A conversations.json list is split per thread, not filed as one room."""
    tmpdir = tempfile.mkdtemp()
    try:

        def convo(node, user_text, asst_text):
            return {
                "current_node": node,
                "mapping": {
                    "root": {"parent": None, "message": None, "children": ["u"]},
                    "u": {
                        "parent": "root",
                        "message": {
                            "author": {"role": "user"},
                            "content": {"parts": [user_text]},
                        },
                        "children": [node],
                    },
                    node: {
                        "parent": "u",
                        "message": {
                            "author": {"role": "assistant"},
                            "content": {"parts": [asst_text]},
                        },
                        "children": [],
                    },
                },
            }

        export = Path(tmpdir) / "conversations.json"
        export.write_text(
            json.dumps(
                [
                    convo(
                        "a1",
                        "How do I write a pytest fixture with assertion coverage?",
                        "Use a pytest fixture and assert on the result for coverage.",
                    ),
                    convo(
                        "a2",
                        "How do I commit and push this branch as a pull request?",
                        "Run git commit, then git push the branch and open the diff PR.",
                    ),
                ]
            ),
            encoding="utf-8",
        )

        palace_path = os.path.join(tmpdir, "palace")
        mine_convos(tmpdir, palace_path)

        client = chromadb.PersistentClient(path=palace_path)
        col = client.get_collection("mempalace_drawers")
        result = col.get()
        rooms = {m["room"] for m in result["metadatas"]}
        # Two distinct-topic threads must not collapse into one room.
        assert len(rooms) >= 2
        assert {"tests", "git"}.issubset(rooms)
    finally:
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


def test_mine_convos_allows_general_after_exchange(capsys):
    """A transcript mined as exchange can later be mined as general memories."""
    tmpdir = tempfile.mkdtemp()
    try:
        convo_path = Path(tmpdir) / "chat.txt"
        convo_path.write_text(
            "> What did we decide?\n"
            "We decided to use SQLite because it keeps the local setup simple.\n\n"
            "> What broke?\n"
            "The search failed because the old index was stale, and the fix was rebuild.\n"
        )
        palace_path = os.path.join(tmpdir, "palace")

        mine_convos(tmpdir, palace_path, wing="test", extract_mode="exchange")
        capsys.readouterr()
        mine_convos(tmpdir, palace_path, wing="test", extract_mode="general")
        out = capsys.readouterr().out

        assert "Files skipped (already filed): 0" in out

        client = chromadb.PersistentClient(path=palace_path)
        col = client.get_collection("mempalace_drawers")
        resolved = str(Path(tmpdir).resolve() / "chat.txt")
        rows = col.get(where={"source_file": resolved}, include=["metadatas"])
        modes = {meta.get("extract_mode") for meta in rows["metadatas"]}
        assert {"exchange", "general"} <= modes
        assert any(drawer_id.startswith("drawer_test_decision_") for drawer_id in rows["ids"])
        del col, client
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
        assert "Files skipped (already filed): 0" in out, (
            "stale drawers should force a rebuild, not a skip"
        )

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
