"""Slice 23: disk-backed LLM response cache (mythic_agent/core/cache.py)."""

import json
import time

import pytest

from mythic_agent.core.cache import ResponseCache, default_cache_dir


def make_cache(tmp_path, **kwargs):
    return ResponseCache(tmp_path / "cache", **kwargs)


def test_put_get_roundtrip(tmp_path):
    cache = make_cache(tmp_path)
    key = ResponseCache.hash_prompt("hello world")
    assert cache.get(key) is None  # miss before put
    cache.put(key, "response text")
    assert cache.get(key) == "response text"


def test_hash_prompt_deterministic_and_distinct():
    assert ResponseCache.hash_prompt("abc") == ResponseCache.hash_prompt("abc")
    assert len(ResponseCache.hash_prompt("abc")) == 64
    assert ResponseCache.hash_prompt("abc") != ResponseCache.hash_prompt("abd")


def test_expired_entry_is_miss_and_evicted(tmp_path):
    cache = make_cache(tmp_path, ttl_seconds=1)
    key = ResponseCache.hash_prompt("ttl test")
    cache.put(key, "stale")
    entry = next((tmp_path / "cache").glob("*.json"))
    data = json.loads(entry.read_text())
    data["created_at"] = time.time() - 3600  # force expiry
    entry.write_text(json.dumps(data))
    assert cache.get(key) is None
    assert not entry.exists()


def test_corrupt_entry_is_miss_and_evicted(tmp_path):
    cache = make_cache(tmp_path)
    key = ResponseCache.hash_prompt("corrupt")
    (tmp_path / "cache" / f"{key}.json").write_text("not-json{{{")
    assert cache.get(key) is None
    assert not (tmp_path / "cache" / f"{key}.json").exists()


def test_clear_removes_entries(tmp_path):
    cache = make_cache(tmp_path)
    for i in range(3):
        cache.put(ResponseCache.hash_prompt(f"p{i}"), f"r{i}")
    assert cache.stats()["entries"] == 3
    assert cache.clear() == 3
    assert cache.stats()["entries"] == 0


def test_stats_reports_hits_misses_and_size(tmp_path):
    cache = make_cache(tmp_path)
    key = ResponseCache.hash_prompt("stats")
    cache.get(key)  # miss
    cache.put(key, "x" * 100)
    cache.get(key)  # hit
    stats = cache.stats()
    assert stats["entries"] == 1
    assert stats["misses"] == 1
    assert stats["hits"] == 1
    assert stats["size_bytes"] > 0
    assert stats["ttl_seconds"] == 3600
    # A fresh instance against the same dir sees persisted counters.
    assert ResponseCache(tmp_path / "cache").stats()["hits"] == 1


def test_invalid_ttl_rejected(tmp_path):
    with pytest.raises(ValueError):
        ResponseCache(tmp_path / "cache", ttl_seconds=0)


def test_default_cache_dir_under_mythic_home(tmp_path, monkeypatch):
    monkeypatch.setenv("MYTHIC_HOME", str(tmp_path / "state"))
    assert default_cache_dir() == tmp_path / "state" / "cache"


def test_overwrite_updates_response(tmp_path):
    cache = make_cache(tmp_path)
    key = ResponseCache.hash_prompt("overwrite")
    cache.put(key, "first")
    cache.put(key, "second")
    assert cache.get(key) == "second"
