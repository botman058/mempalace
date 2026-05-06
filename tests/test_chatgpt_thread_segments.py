from __future__ import annotations

from mempalace.chatgpt_thread_segments import build_chatgpt_thread_segments
from mempalace.normalize import _collect_chatgpt_messages, _messages_to_transcript


def _conversation_from_messages(messages: list[tuple[str, str]], conversation_id: str = "conv-1") -> dict:
    mapping: dict[str, dict] = {
        "root": {"id": "root", "parent": None, "children": ["n0"], "message": None}
    }
    prev = "root"
    for i, (role, text) in enumerate(messages):
        node_id = f"n{i}"
        next_id = f"n{i + 1}" if i + 1 < len(messages) else None
        mapping[node_id] = {
            "id": node_id,
            "parent": prev,
            "children": [next_id] if next_id else [],
            "message": {
                "author": {"role": role},
                "content": {"parts": [text]},
            },
        }
        if prev in mapping:
            mapping[prev]["children"] = [node_id]
        prev = node_id
    return {
        "id": conversation_id,
        "title": "Test Conversation",
        "mapping": mapping,
        "current_node": prev if prev != "root" else "root",
    }


def _rebuild_from_segments(segments):
    if not segments:
        return ""
    covered = [""] * segments[-1].char_end
    for seg in segments:
        for i, char in enumerate(seg.content, start=seg.char_start):
            if i < len(covered):
                covered[i] = char
    return "".join(covered)


def _normalize_transcript_shape(text: str) -> str:
    return text.replace("\n\n", "\n")


def test_short_conversation_single_segment():
    convo = _conversation_from_messages(
        [
            ("user", "hello"),
            ("assistant", "hi"),
            ("user", "can you summarize this"),
            ("assistant", "yes"),
        ]
    )
    segments = build_chatgpt_thread_segments(conversation=convo)
    assert len(segments) == 1
    assert segments[0].message_start_index == 0
    assert segments[0].message_end_index == 3
    assert "hello" in segments[0].content


def test_long_multi_turn_conversation_uses_turn_overlap():
    msgs = []
    for i in range(40):
        msgs.append(("user", f"user turn {i} " + ("x" * 220)))
        msgs.append(("assistant", f"assistant turn {i} " + ("y" * 220)))
    convo = _conversation_from_messages(msgs, conversation_id="conv-long")
    segments = build_chatgpt_thread_segments(conversation=convo, target_chars=10_000)
    assert len(segments) > 1
    for left, right in zip(segments, segments[1:]):
        assert left.message_end_index >= right.message_start_index
    rebuilt = _rebuild_from_segments(segments)
    transcript = _messages_to_transcript(_collect_chatgpt_messages(convo), spellcheck=False)
    assert _normalize_transcript_shape(transcript) in _normalize_transcript_shape(rebuilt)


def test_first_message_over_12k_is_split_and_later_turns_preserved():
    huge = "A" * 13_500 + "SUFFIX_MARKER"
    convo = _conversation_from_messages(
        [
            ("user", huge),
            ("assistant", "ack"),
            ("user", "later turn should remain"),
            ("assistant", "later reply should remain"),
        ],
        conversation_id="conv-huge",
    )
    segments = build_chatgpt_thread_segments(
        conversation=convo,
        target_chars=10_000,
        max_message_chars=12_000,
        message_overlap_chars=1_000,
    )
    assert len(segments) >= 3
    assert any(seg.message_start_index == 0 and seg.message_end_index == 0 for seg in segments)
    assert any("SUFFIX_MARKER" in seg.content for seg in segments)
    assert any("later turn should remain" in seg.content for seg in segments)
    assert any("later reply should remain" in seg.content for seg in segments)


def test_multiple_subthreads_in_one_conversation():
    convo = _conversation_from_messages(
        [
            ("user", "Let's debug postgres latency and index scans"),
            ("assistant", "Share your query plans."),
            ("user", "new topic: plan Italy train itinerary and hotels"),
            ("assistant", "What cities and dates?"),
            ("user", "separately, budget spreadsheet and exchange rates"),
            ("assistant", "I can help with formulas."),
        ],
        conversation_id="conv-subthreads",
    )
    segments = build_chatgpt_thread_segments(conversation=convo, target_chars=220)
    subthreads = {seg.subthread_id for seg in segments}
    assert len(subthreads) >= 2
    assert all(seg.subthread_label for seg in segments)


def test_deterministic_rerun_same_input():
    convo = _conversation_from_messages(
        [
            ("user", "alpha topic details"),
            ("assistant", "alpha response"),
            ("user", "new topic beta details"),
            ("assistant", "beta response"),
        ],
        conversation_id="conv-deterministic",
    )
    first = build_chatgpt_thread_segments(conversation=convo, target_chars=120)
    second = build_chatgpt_thread_segments(conversation=convo, target_chars=120)
    assert first == second
    assert [seg.segment_id for seg in first] == [seg.segment_id for seg in second]


def test_no_dropped_suffix_for_oversized_message():
    payload = "B" * 25_000 + "TAIL_END_MARKER"
    convo = _conversation_from_messages(
        [("user", payload), ("assistant", "tail reply")], conversation_id="conv-suffix"
    )
    segments = build_chatgpt_thread_segments(
        conversation=convo,
        target_chars=10_000,
        max_message_chars=12_000,
        message_overlap_chars=1_000,
    )
    rebuilt = _rebuild_from_segments(segments)
    transcript = _messages_to_transcript(_collect_chatgpt_messages(convo), spellcheck=False)
    assert "TAIL_END_MARKER" in rebuilt
    assert _normalize_transcript_shape(transcript) in _normalize_transcript_shape(rebuilt)
