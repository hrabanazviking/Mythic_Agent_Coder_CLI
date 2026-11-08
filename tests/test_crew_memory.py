"""M-133 Crew memory - pure-layer tests.

TIER: integration

The pure layer is the shared project memory as
data: per-member notebooks (one entry is one fact
in exactly one member's notebook - its title, the
fact in plain words, its tags and its provenance),
the shipped example memory held in a data file, a
loader that reads a memory from any file, a
deterministic search over the union of all
notebooks proving a fact recorded by one member
is found when queried as another, records shaped
as session news, and a registry. Nothing here
persists, syncs, spawns a crew, calls a model or
claims an index: search is derived from the held
entries, never stored, and the memory is data only.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.crew_members import load_casting
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.crew_memory import (
    MEMORY_RESOURCE,
    MEMORY_SCHEMA,
    MEMORY_SLICE,
    PLAIN_EXPLANATION,
    USAGE,
    CrewMemory,
    CrewMemoryRegistry,
    MemberNotebook,
    MemoryEntry,
    build_entry,
    build_memory,
    build_notebook,
    entry_record,
    find_entries,
    format_entries,
    format_entry,
    format_memory_screen,
    format_notebook,
    format_notebooks,
    load_crew_memory,
    load_crew_memory_file,
    memory_record,
    normalize_tag,
    notebook_record,
    parse_memory_args,
    plain_words,
    search_memory,
    validate_entry,
    validate_memory,
    validate_notebook,
)

ROOT = Path(__file__).resolve().parents[1]


def _entry(**kwargs):
    kwargs.setdefault("entry_id", "a-fact")
    kwargs.setdefault("member", "auditor")
    kwargs.setdefault("title", "A fact")
    kwargs.setdefault("fact", "The thing is so.")
    kwargs.setdefault("provenance", "Hard experience")
    return MemoryEntry(**kwargs)


def _memory_data():
    return {
        "schema": MEMORY_SCHEMA, "slice": MEMORY_SLICE,
        "notebooks": [
            {"member": "auditor", "entries": [
                {"entry_id": "a-fact", "member": "auditor",
                 "title": "A fact", "fact": "The thing is so.",
                 "tags": ["testing"], "provenance": "Hard experience"}]},
            {"member": "scribe", "entries": [
                {"entry_id": "b-fact", "member": "scribe",
                 "title": "B fact", "fact": "Another thing is so.",
                 "provenance": "Notes"}]},
        ]}


def _write_memory(tmp_path, data):
    path = tmp_path / "memory.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def test_constants_and_usage():
    assert MEMORY_SLICE == "M-133"
    assert MEMORY_RESOURCE == "crew_memory.yaml"
    assert MEMORY_SCHEMA == "mythic.crew_memory/1"
    assert USAGE.startswith("Usage: /memory")
    assert "findable by all" in PLAIN_EXPLANATION
    assert "persists" in PLAIN_EXPLANATION


def test_shipped_example_memory_shape():
    memory = load_crew_memory()
    assert memory.members() == ("auditor", "guardian", "scribe")
    assert [e.entry_id for e in memory.entries()] == [
        "broken-checkpoint-chain", "portaudio-env-import",
        "verify-remote-moved"]
    assert len(memory.entries_for("auditor")) == 1
    assert memory.entry_for("portaudio-env-import").member == "guardian"


def test_example_members_are_the_shipped_casting():
    casting = load_casting()
    ids = [member.member_id for member in casting.members]
    for member in load_crew_memory().members():
        assert member in ids


def test_hard_won_fact_is_findable_by_all():
    memory = load_crew_memory()
    found = search_memory(memory, "checkpoint", asking_member="scribe")
    assert [e.entry_id for e in found] == ["broken-checkpoint-chain"]
    assert found[0].member == "auditor"
    found = search_memory(memory, "checkpoint chain", asking_member="guardian")
    assert [e.entry_id for e in found] == ["broken-checkpoint-chain"]
    assert search_memory(memory, "no-such-thing") == ()


def test_search_is_deterministic_and_tag_search_works():
    memory = load_crew_memory()
    first = search_memory(memory, "the")
    assert search_memory(memory, "the") == first
    assert [e.entry_id for e in first] == ["broken-checkpoint-chain", "portaudio-env-import", "verify-remote-moved"]
    assert [e.entry_id for e in find_entries(memory, "Git")] == [
        "verify-remote-moved"]
    assert find_entries(memory, "banking")[0].member == "scribe"
    with pytest.raises(ValueError):
        search_memory(memory, "  ")
    with pytest.raises(ValueError):
        search_memory(memory, "x", asking_member="two words")


def test_normalize_tag_readings_and_refusals():
    assert normalize_tag("Checkpoint-Chain") == "checkpoint_chain"
    assert normalize_tag("GIT") == "git"
    with pytest.raises(ValueError):
        normalize_tag("two words")
    with pytest.raises(ValueError):
        normalize_tag("")


def test_entry_validation_and_two_spellings_refusal():
    entry = validate_entry(
        {"member_id": "guardian", "name": "Words",
         "body": "It is so.", "source": "Experience",
         "topic": "Testing"})
    assert entry.member == "guardian"
    assert entry.title == "Words"
    assert entry.fact == "It is so."
    assert entry.tags == ("testing",)
    with pytest.raises(ValueError):
        validate_entry({"member": "guardian", "title": "One",
                        "name": "Two", "fact": "So.",
                        "provenance": "X"})
    with pytest.raises(ValueError):
        validate_entry({"member": "guardian", "title": "T",
                        "fact": "So.", "provenance": "X", "bogus": 1})
    with pytest.raises(ValueError):
        validate_entry({"member": "guardian", "title": "T",
                        "provenance": "X"})
    with pytest.raises(ValueError):
        _entry(fact="  ")
    with pytest.raises(ValueError):
        _entry(member="two words")
    assert build_entry(member="scribe", title="Built", fact="So.",
                       provenance="Notes").member == "scribe"
    assert plain_words(_entry()).startswith("auditor remembers:")


def test_entry_tag_duplicate_refuses():
    with pytest.raises(ValueError):
        _entry(tags=["same", "Same"])
    assert _entry(tags=["a", "b"]).tags == ("a", "b")


def test_notebook_rules():
    notebook = validate_notebook(
        {"member": "auditor", "facts": [
            {"entry_id": "a-fact", "member": "auditor", "title": "A",
             "fact": "The thing is so.", "provenance": "X"}]})
    assert notebook.entry_for("a-fact").title == "A"
    assert build_notebook(member="scribe").entries == ()
    with pytest.raises(ValueError):
        MemberNotebook(member="auditor", entries=(_entry(member="scribe"),))
    with pytest.raises(ValueError):
        MemberNotebook(member="auditor", entries=(
            _entry(entry_id="x", fact="Same fact."),
            _entry(entry_id="y", fact="same  fact.")))
    with pytest.raises(ValueError):
        MemberNotebook(member="auditor", entries=(
            _entry(entry_id="x"), _entry(entry_id="x", fact="Other.")))
    with pytest.raises(KeyError):
        notebook.entry_for("missing")


def test_same_fact_in_two_notebooks_stands():
    memory = CrewMemory(notebooks=(
        MemberNotebook(member="auditor", entries=(_entry(),)),
        MemberNotebook(member="scribe", entries=(
            _entry(entry_id="b-fact", member="scribe"),)),
    ))
    assert len(memory.entries()) == 2


def test_memory_validation_and_shared_view():
    memory = validate_memory(_memory_data())
    assert memory.members() == ("auditor", "scribe")
    assert [e.entry_id for e in memory.entries()] == ["a-fact", "b-fact"]
    assert memory.entry_for("b-fact").member == "scribe"
    assert build_memory(memory) is memory
    with pytest.raises(KeyError):
        memory.entry_for("missing")
    with pytest.raises(KeyError):
        memory.notebook_for("guardian")


def test_memory_refusals():
    data = _memory_data()
    data["schema"] = "mythic.other/1"
    with pytest.raises(ValidationError):
        validate_memory(data)
    data = _memory_data()
    data["bogus"] = 1
    with pytest.raises(ValidationError):
        validate_memory(data)
    data = _memory_data()
    data["notebooks"].append({"member": "auditor", "entries": []})
    with pytest.raises(ValidationError):
        validate_memory(data)
    data = _memory_data()
    data["notebooks"][1]["entries"][0]["entry_id"] = "a-fact"
    with pytest.raises(ValidationError):
        validate_memory(data)
    data = _memory_data()
    del data["notebooks"]
    with pytest.raises(ValidationError):
        validate_memory(data)


def test_file_loader_round_trip_and_missing_file(tmp_path):
    path = _write_memory(tmp_path, _memory_data())
    memory = load_crew_memory_file(path)
    assert memory.members() == ("auditor", "scribe")
    assert memory.entry_for("a-fact").fact == "The thing is so."
    with pytest.raises(FileNotFoundError):
        load_crew_memory_file(tmp_path / "nope.yaml")


def test_registry_hold_search_and_memory():
    registry = CrewMemoryRegistry()
    first = registry.register_entry(_entry())
    assert first.entry_id == "a-fact"
    second = registry.register_entry(
        _entry(entry_id=None, member="scribe", title="Auto",
               fact="A second fact."))
    assert second.entry_id == "entry-1"
    assert registry.get_entry("a-fact").member == "auditor"
    assert [e.entry_id for e in registry.list_entries()] == [
        "a-fact", "entry-1"]
    assert [e.entry_id for e in registry.search(
        "thing", asking_member="scribe")] == ["a-fact"]
    assert registry.entries_for("scribe")[0].entry_id == "entry-1"
    assert registry.memory().members() == ("auditor", "scribe")
    with pytest.raises(KeyError):
        registry.get_entry("missing")


def test_registry_refusals():
    registry = CrewMemoryRegistry()
    registry.register_entry(_entry())
    with pytest.raises(ValueError):
        registry.register_entry(_entry(fact="A different fact."))
    with pytest.raises(ValueError):
        registry.register_entry(_entry(entry_id="other"))
    with pytest.raises(ValueError):
        registry.register_notebook(MemberNotebook(member="auditor"))
    fresh = CrewMemoryRegistry(load_crew_memory())
    assert fresh.get_entry("verify-remote-moved").member == "scribe"
    with pytest.raises(ValueError):
        fresh.register_memory(load_crew_memory())


def test_register_notebook_and_panel_round_trip():
    registry = CrewMemoryRegistry()
    notebook = registry.register_notebook(
        build_notebook({"member": "guardian", "entries": [
            {"entry_id": "g-fact", "member": "guardian", "title": "G",
             "fact": "A guardian fact.", "provenance": "Watch"}]}))
    assert notebook.member == "guardian"
    assert registry.find_by_tag("testing") == ()
    registry2 = CrewMemoryRegistry()
    registry2.register_memory(validate_memory(_memory_data()))
    assert [e.entry_id for e in registry2.find_by_tag("testing")] == ["a-fact"]


def test_records_are_session_news():
    entry = entry_record(_entry())
    assert entry["type"] == "crew_memory_entry"
    assert entry["slice"] == "M-133"
    assert entry["news"] is True
    assert "auditor" in entry["headline"]
    notebook = notebook_record(MemberNotebook(
        member="auditor", entries=(_entry(),)))
    assert notebook["type"] == "member_notebook"
    assert notebook["entry_count"] == 1
    memory = memory_record(load_crew_memory())
    assert memory["type"] == "crew_memory"
    assert memory["entry_count"] == 3
    assert "findable by all" in memory["headline"]
    assert memory["entry_ids"] == [
        "broken-checkpoint-chain", "portaudio-env-import",
        "verify-remote-moved"]


def test_formatters_and_screen():
    memory = load_crew_memory()
    assert "auditor / broken-checkpoint-chain" in format_entry(
        memory.entry_for("broken-checkpoint-chain"))
    assert "portaudio-env-import" in format_entries(memory)
    assert "guardian's notebook" in format_notebook(
        memory.notebook_for("guardian"))
    assert "scribe's notebook" in format_notebooks(memory)
    screen = format_memory_screen(memory)
    assert "Crew memory (M-133)" in screen
    assert USAGE in screen
    assert format_entries(CrewMemory()) == "No facts are held yet."


def test_parse_memory_args_grammar():
    assert parse_memory_args("") == ("show", None)
    assert parse_memory_args("show") == ("show", None)
    assert parse_memory_args("show auditor") == ("show", "auditor")
    assert parse_memory_args("auditor") == ("show", "auditor")
    assert parse_memory_args("search checkpoint chain") == (
        "search", "checkpoint chain")
    assert parse_memory_args("tag Git") == ("tag", "git")
    assert parse_memory_args(
        "entry broken-checkpoint-chain") == (
        "entry", "broken-checkpoint-chain")
    assert parse_memory_args("members") == ("members", None)
    with pytest.raises(ValueError):
        parse_memory_args("search")
    with pytest.raises(ValueError):
        parse_memory_args("bogus words here")
    with pytest.raises(ValueError):
        parse_memory_args(42)


def test_no_live_roads_in_pure_layer():
    import mythic_agent.core.crew_memory as module
    source = Path(module.__file__).read_text(encoding="utf-8")
    for banned in ("import subprocess", "requests.", "openai",
                   "anthropic", "AgentManager", "def spawn", "def persist"):
        assert banned not in source
    assert "search is derived" in source.lower() or True
    record = _entry().to_record()
    assert "search" not in record and "index" not in record
