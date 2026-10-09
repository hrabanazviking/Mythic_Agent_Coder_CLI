"""Tests for mythic_agent.memory.long_term (Slice 42)."""

import json

import pytest

from mythic_agent.memory.long_term import LongTermMemory


@pytest.fixture()
def mem(tmp_path):
    return LongTermMemory(workspace=tmp_path)


def test_store_and_recall(mem):
    mem.store("Volmarr prefers two-space indentation in Python.")
    mem.store("The project uses pytest for testing.")
    results = mem.recall("indentation style")
    assert results and "two-space indentation" in results[0]


def test_recall_returns_list_of_strings_ranked(mem):
    mem.store("Python style: black formatter with line length 100.")
    mem.store("Formatter config lives in pyproject.toml.")
    mem.store("The sky is blue.")
    results = mem.recall("python formatter style", top_k=2)
    assert len(results) == 2
    assert all(isinstance(r, str) for r in results)
    assert "black formatter" in results[0]


def test_recall_no_match_returns_empty(mem):
    mem.store("Postgres connection pool size is 20.")
    assert mem.recall("quantum banana hammock") == []


def test_recall_empty_query(mem):
    mem.store("Something memorable.")
    assert mem.recall("") == []
    assert mem.recall("   ") == []


def test_forget(mem):
    mem.store("Temporary fact to forget.")
    assert len(mem) == 1
    assert mem.forget("Temporary fact to forget.") is True
    assert len(mem) == 0
    assert mem.forget("Temporary fact to forget.") is False
    assert mem.recall("temporary") == []


def test_store_deduplicates(mem):
    mem.store("Same fact twice.")
    mem.store("Same fact twice.", tags=["style"])
    assert len(mem) == 1
    assert mem.all()[0].tags == ["style"]


def test_store_empty_raises(mem):
    with pytest.raises(ValueError):
        mem.store("   ")


def test_persistence_roundtrip(mem, tmp_path):
    mem.store("Persistent fact about deploy.", tags=["ops"], source="standup")
    mem2 = LongTermMemory(workspace=tmp_path)
    assert len(mem2) == 1
    assert mem2.recall("deploy") == ["Persistent fact about deploy."]
    assert mem2.all()[0].tags == ["ops"]
    assert mem2.all()[0].source == "standup"
    store_file = tmp_path / ".mythic" / "long_term.json"
    assert store_file.exists()
    data = json.loads(store_file.read_text())
    assert data[0]["text"] == "Persistent fact about deploy."


def test_recall_with_scores_sorted(mem):
    mem.store("Alpha fact about caching redis.")
    mem.store("Beta fact about caching memcached.")
    scored = mem.recall_with_scores("caching redis", top_k=2)
    assert len(scored) == 2
    assert scored[0][1] >= scored[1][1]
    assert "redis" in scored[0][0]


def test_tag_match_boosts_recall(mem):
    mem.store("Unrelated words here entirely.", tags=["deployment"])
    mem.store("Some other fact about nothing much.")
    results = mem.recall("deployment")
    assert results and results[0] == "Unrelated words here entirely."


def test_clear_and_export_import(mem, tmp_path):
    mem.store("Fact one.")
    mem.store("Fact two.")
    export_path = tmp_path / "export.json"
    mem.export(export_path)
    assert mem.clear() == 2
    assert len(mem) == 0
    assert mem.import_facts(export_path) == 2
    assert sorted(mem.recall("fact", top_k=10)) == ["Fact one.", "Fact two."]
