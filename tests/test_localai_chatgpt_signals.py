from types import SimpleNamespace

from scripts.localai_chatgpt_signals import legacy_checkpoint_key, seen_checkpoint_key


def test_seen_checkpoint_key_accepts_legacy_chatgpt_rows(tmp_path):
    source_file = tmp_path / "nested" / "conversations.json"
    identity = SimpleNamespace(
        logical_source_id="chatgpt:convo-123",
        conversation_id="convo-123",
    )

    seen = {legacy_checkpoint_key(source_file, "convo-123")}

    assert seen_checkpoint_key(seen, source_file, identity) is True
    assert seen_checkpoint_key({"chatgpt:convo-123"}, source_file, identity) is True
    assert seen_checkpoint_key(set(), source_file, identity) is False


def test_seen_checkpoint_key_ignores_legacy_skipped_empty_rows(tmp_path):
    source_file = tmp_path / "nested" / "conversations.json"
    identity = SimpleNamespace(
        logical_source_id="chatgpt:convo-123",
        conversation_id="convo-123",
    )

    seen = {legacy_checkpoint_key(source_file, "convo-123"): "skipped_empty"}

    assert seen_checkpoint_key(seen, source_file, identity) is False
