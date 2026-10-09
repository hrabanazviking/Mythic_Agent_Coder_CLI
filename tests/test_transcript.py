"""Slice 27: memory-bounded transcript (mythic_agent/core/transcript.py)."""

import tracemalloc

import pytest

from mythic_agent.core.transcript import BoundedTranscript


def turn(i, size=100):
    return {"role": "user" if i % 2 == 0 else "assistant", "content": f"turn-{i} " + "x" * size}


def test_add_get_preserves_order(tmp_path):
    t = BoundedTranscript(max_tokens=10**9, spill_dir=tmp_path)
    for i in range(5):
        t.add(turn(i))
    got = t.get()
    assert [g["content"] for g in got] == [f"turn-{i} " + "x" * 100 for i in range(5)]


def test_spill_triggers_over_budget_and_caps_memory(tmp_path):
    t = BoundedTranscript(max_tokens=200, spill_dir=tmp_path)
    for i in range(10):
        t.add(turn(i, size=793))  # 800 chars -> exactly 200 tokens
    stats = t.stats()
    assert stats["spilled_turns"] == 9
    assert stats["in_memory_tokens"] <= 200
    assert len(t.get()) == 1  # newest turn always kept
    assert stats["spill_file"] is not None


def test_get_all_reconstructs_full_order(tmp_path):
    t = BoundedTranscript(max_tokens=200, spill_dir=tmp_path)
    for i in range(10):
        t.add(turn(i, size=793))  # 800 chars -> exactly 200 tokens
    full = t.get_all()
    assert len(full) == 10
    assert [f["content"].startswith(f"turn-{i} ") for i, f in enumerate(full)] == [True] * 10


def test_no_spill_when_under_budget(tmp_path):
    t = BoundedTranscript(max_tokens=10**9, spill_dir=tmp_path)
    for i in range(3):
        t.add(turn(i))
    assert t.stats()["spilled_turns"] == 0
    assert t.stats()["spill_file"] is None
    assert len(t.get_all()) == 3


def test_tracemalloc_peak_memory_stays_bounded(tmp_path):
    turns = [turn(i, size=7_600) for i in range(60)]  # ~1.9k tokens each

    tracemalloc.start()
    bounded = BoundedTranscript(max_tokens=2_000, spill_dir=tmp_path)
    for x in turns:
        bounded.add(x)
    _, peak_bounded = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Same content held unbounded would keep all ~300k tokens in RAM.
    estimated_unbounded = sum(len(x["content"]) for x in turns)
    in_memory_chars = sum(len(g["content"]) for g in bounded.get())
    assert in_memory_chars < estimated_unbounded // 10  # at least 10x reduction
    assert bounded.stats()["in_memory_tokens"] <= 2_000
    assert peak_bounded < estimated_unbounded  # bounded below raw payload size


def test_invalid_max_tokens_rejected(tmp_path):
    with pytest.raises(ValueError):
        BoundedTranscript(max_tokens=0, spill_dir=tmp_path)


def test_malformed_turn_rejected(tmp_path):
    t = BoundedTranscript(max_tokens=1000, spill_dir=tmp_path)
    with pytest.raises(TypeError):
        t.add({"role": "user"})  # no content
    with pytest.raises(TypeError):
        t.add("not a dict")


def test_get_returns_copies(tmp_path):
    t = BoundedTranscript(max_tokens=10**9, spill_dir=tmp_path)
    t.add(turn(0))
    got = t.get()
    got[0]["content"] = "mutated"
    assert t.get()[0]["content"].startswith("turn-0 ")
