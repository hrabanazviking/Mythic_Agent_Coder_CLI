"""Tests for the user preference store (Slice 21)."""

import json

import pytest

from mythic_agent.memory.preferences import PreferenceStore


@pytest.fixture
def store(tmp_path):
    return PreferenceStore(tmp_path / "project")


def test_record_and_get(store):
    store.record("test_runner", "pytest")
    assert store.get("test_runner") == "pytest"


def test_get_missing_returns_default(store):
    assert store.get("nope") is None
    assert store.get("nope", "fallback") == "fallback"


def test_persists_across_instances(tmp_path):
    first = PreferenceStore(tmp_path / "project")
    first.record("editor", "vim")
    second = PreferenceStore(tmp_path / "project")
    assert second.get("editor") == "vim"


def test_persistence_file_layout(tmp_path):
    PreferenceStore(tmp_path / "project").record("x", "y")
    path = tmp_path / "project" / ".mythic" / "preferences.json"
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["x"]["value"] == "y"
    assert data["x"]["count"] == 1


def test_record_strengthens_count(store):
    store.record("tool", "grep")
    store.record("tool", "grep")
    store.record("tool", "rg")
    assert store.get("tool") == "rg"
    assert store.suggest().startswith("You usually prefer 'rg' for tool.")


def test_suggest_empty_when_nothing_recorded(store):
    assert store.suggest() == ""


def test_suggest_formatting(store):
    store.record("test_runner", "pytest")
    store.record("test_runner", "pytest")
    store.record("editor", "vim")
    text = store.suggest()
    assert "You usually prefer 'pytest' for test runner." in text
    assert "You usually prefer 'vim' for editor." in text
    # Highest count ranks first.
    assert text.index("pytest") < text.index("vim")


def test_suggest_respects_top_n(store):
    store.record("a", "1")
    store.record("b", "2")
    store.record("c", "3")
    lines = store.suggest(top_n=2).splitlines()
    assert len(lines) == 2


def test_forget(store):
    store.record("tool", "grep")
    assert store.forget("tool") is True
    assert store.get("tool") is None
    assert store.forget("tool") is False


def test_all(store):
    store.record("a", "1")
    store.record("b", "2")
    assert store.all() == {"a": "1", "b": "2"}


def test_learn_from_turn_always_use(store):
    extracted = store.learn_from_turn("Please always use pytest.")
    assert extracted == [("tool", "pytest")]
    assert store.get("tool") == "pytest"


def test_learn_from_turn_never_use(store):
    extracted = store.learn_from_turn("Never use vi again.")
    assert ("avoid_tool", "vi again") in extracted
    assert store.get("avoid_tool") == "vi again"


def test_learn_from_turn_prefer_over(store):
    extracted = store.learn_from_turn("I prefer rg over grep.")
    assert ("preference", "rg over grep") in extracted or any(
        pref == "preference" for pref, _ in extracted
    )


def test_learn_from_turn_no_match(store):
    extracted = store.learn_from_turn("Hello, how are you today?")
    assert extracted == []
    assert store.suggest() == ""


def test_corrupted_store_self_heals(tmp_path):
    project = tmp_path / "project"
    bad = project / ".mythic" / "preferences.json"
    bad.parent.mkdir(parents=True)
    bad.write_text("{ not valid json", encoding="utf-8")
    store = PreferenceStore(project)
    assert store.get("anything") is None
    store.record("fresh", "start")
    assert store.get("fresh") == "start"
    assert bad.with_suffix(".json.corrupted").exists()


def test_workspaces_are_isolated(tmp_path):
    a = PreferenceStore(tmp_path / "proj-a")
    b = PreferenceStore(tmp_path / "proj-b")
    a.record("tool", "grep")
    assert b.get("tool") is None
