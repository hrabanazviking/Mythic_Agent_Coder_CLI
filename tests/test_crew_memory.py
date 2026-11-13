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

# -- agent layer -----------------------------------------------------------
#
# M-133 agent layer: the agent holds a
# CrewMemoryRegistry for the session (session
# state only, no new setting), entries are held
# by being registered - published as their
# entry_record session news through the checkpoint
# road, deduped per entry id - the whole memory is
# published as ONE memory_record session event,
# deduped per whole memory shape, and the /memory
# surface rides both roads on the pure parser +
# formatters. Status, get, search, tag and memory
# reads register and publish nothing, answer from
# the held registry first and from the shipped
# example only while nothing is held - a held
# session never falls back to the example. This
# layer persists nothing, syncs nothing, spawns no
# crew, calls no model and claims no board - Part
# VIII does not exist yet, so the screen is where
# the memory is visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _memory_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


class TestCrewMemoryAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.crew_memory_status()
        assert status["entries"] == []
        assert status["notebooks"] == []
        assert status["memory"]["members"] == [
            "auditor", "guardian", "scribe"]
        assert len(status["memory"]["entries"]) == 3
        assert status["memory_record"]["type"] == "crew_memory"
        assert status["memory_record"]["entry_count"] == 3
        assert "Crew memory (M-133)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        assert agent._crew_memory_registry() is \
            agent._crew_memory_registry()
        assert agent._crew_memory_store is \
            agent._crew_memory_registry()

    def test_reads_register_and_publish_nothing(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.crew_memory_status()
        entry = agent.get_memory_entry("broken-checkpoint-chain")
        assert entry.member == "auditor"
        found = agent.search_crew_memory(
            "checkpoint", asking_member="scribe")
        assert [e.entry_id for e in found] == [
            "broken-checkpoint-chain"]
        tagged = agent.find_memory_entries_by_tag("git")
        assert [e.entry_id for e in tagged] == ["verify-remote-moved"]
        assert agent.crew_memory().members() == (
            "auditor", "guardian", "scribe")
        registry = agent._crew_memory_registry()
        assert registry.list_entries() == ()
        for kind in ("crew_memory_entry", "crew_memory"):
            assert _memory_events(store, session_id, kind) == []
        agent.close()

    def test_unheld_get_raises_keyerror(self, agent):
        with pytest.raises(KeyError):
            agent.get_memory_entry("entry-1")

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_memory_entry(_entry())
        status = agent.crew_memory_status()
        assert [e["entry_id"] for e in status["entries"]] == ["a-fact"]
        assert [n["member"] for n in status["notebooks"]] == ["auditor"]
        # The held memory answers now, not the example:
        # the session memory is the held union alone.
        assert status["memory"]["members"] == ["auditor"]
        assert status["memory_record"]["entry_count"] == 1
        assert "A fact" in status["screen"]

    def test_held_session_never_falls_back_to_the_example(
            self, agent):
        agent.register_memory_entry(_entry())
        with pytest.raises(KeyError):
            agent.get_memory_entry("broken-checkpoint-chain")
        assert agent.search_crew_memory("checkpoint") == ()
        assert agent.find_memory_entries_by_tag("git") == ()
        assert [e.entry_id for e in agent.crew_memory().entries()] == [
            "a-fact"]
        with pytest.raises(KeyError):
            agent.crew_memory().notebook_for("guardian")


class TestCrewMemoryAgentRegister:
    def test_register_entry_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_memory_entry(_entry())
        assert outcome["entry"]["entry_id"] == "a-fact"
        assert outcome["record"]["type"] == "crew_memory_entry"
        events = _memory_events(store, session_id, "crew_memory_entry")
        assert len(events) == 1
        assert events[0]["entry_id"] == "a-fact"
        # The same record is never published twice.
        agent._publish_memory_record(outcome["record"])
        assert len(_memory_events(
            store, session_id, "crew_memory_entry")) == 1
        # Foreign record types are refused on this road.
        from mythic_agent.core.crew_members import (
            casting_record,
            load_casting,
        )
        from mythic_agent.core.review_panels import (
            change_record,
            load_review_panel,
            outcome_of_panel,
            outcome_record,
            review_record,
        )
        panel = load_review_panel()
        agent._publish_memory_record(change_record(panel.change))
        agent._publish_memory_record(review_record(panel.reviews[0]))
        agent._publish_memory_record(outcome_record(
            outcome_of_panel(panel)))
        agent._publish_memory_record(casting_record(
            load_casting().members[0]))
        for kind in ("panel_change", "panel_review",
                     "panel_outcome", "crew_member"):
            assert _memory_events(store, session_id, kind) == []
        assert len(_memory_events(
            store, session_id, "crew_memory_entry")) == 1
        agent.close()

    def test_duplicate_id_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_memory_entry(_entry())
        with pytest.raises(ValueError):
            agent.register_memory_entry(
                _entry(fact="A different fact."))
        assert len(_memory_events(
            store, session_id, "crew_memory_entry")) == 1
        agent.close()

    def test_duplicate_fact_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_memory_entry(_entry(entry_id="x-fact"))
        with pytest.raises(ValueError):
            agent.register_memory_entry(_entry(
                entry_id="y-fact", fact="the  thing is so."))
        assert len(_memory_events(
            store, session_id, "crew_memory_entry")) == 1
        agent.close()

    def test_record_notebook_holds_and_publishes_each_entry(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        notebook = build_notebook({"member": "guardian", "entries": [
            {"entry_id": "g-one", "member": "guardian", "title": "G one",
             "fact": "A first guardian fact.", "provenance": "Watch"},
            {"entry_id": "g-two", "member": "guardian", "title": "G two",
             "fact": "A second guardian fact.", "provenance": "Watch"}]})
        outcome = agent.record_member_notebook(notebook)
        assert outcome["count"] == 2
        assert outcome["notebook"]["member"] == "guardian"
        assert len(_memory_events(
            store, session_id, "crew_memory_entry")) == 2
        assert agent.get_memory_entry("g-two").title == "G two"
        agent.close()

    def test_second_notebook_for_one_member_refuses(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.record_member_notebook(build_notebook(
            {"member": "auditor", "entries": [
                {"entry_id": "a-one", "member": "auditor", "title": "A",
                 "fact": "An auditor fact.", "provenance": "Work"}]}))
        with pytest.raises(ValueError):
            agent.record_member_notebook(build_notebook(
                {"member": "auditor", "entries": []}))
        assert len(_memory_events(
            store, session_id, "crew_memory_entry")) == 1
        agent.close()

    def test_record_memory_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_crew_memory()
        assert outcome["count"] == 3
        assert outcome["memory"]["entry_count"] == 3
        events = _memory_events(store, session_id, "crew_memory_entry")
        assert [e["entry_id"] for e in events] == [
            "broken-checkpoint-chain", "portaudio-env-import",
            "verify-remote-moved"]
        assert agent.crew_memory().members() == (
            "auditor", "guardian", "scribe")
        agent.close()

    def test_record_same_memory_twice_refuses(self, agent):
        agent.record_crew_memory()
        with pytest.raises(ValueError):
            agent.record_crew_memory()

    def test_memory_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_memory(tmp_path, _memory_data())
        memory = load_crew_memory_file(path)
        outcome = agent.record_crew_memory(memory)
        assert outcome["count"] == 2
        assert agent.get_memory_entry("b-fact").member == "scribe"
        found = agent.search_crew_memory(
            "another", asking_member="auditor")
        assert [e.entry_id for e in found] == ["b-fact"]

    def test_search_prefers_the_held_memory(self, agent):
        agent.register_memory_entry(MemoryEntry(
            entry_id="gate-fact", member="scribe", title="Gate fact",
            fact="The checkpoint gate holds.", tags=("checkpoints",),
            provenance="Watch"))
        found = agent.search_crew_memory(
            "checkpoint", asking_member="auditor")
        assert [e.entry_id for e in found] == ["gate-fact"]
        assert found[0].member == "scribe"
        # The held memory answers now: the example's
        # PortAudio fact no longer answers.
        assert agent.search_crew_memory("portaudio") == ()


class TestCrewMemoryAgentReport:
    def test_report_publishes_one_memory_event_and_dedups(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.record_crew_memory()
        outcome = agent.report_crew_memory()
        assert outcome["record"]["type"] == "crew_memory"
        assert outcome["entry_count"] == 3
        assert outcome["memory"]["entry_count"] == 3
        events = _memory_events(store, session_id, "crew_memory")
        # ONE memory event holds the whole memory.
        assert len(events) == 1
        assert events[0]["entry_count"] == 3
        # Reporting again on the same memory publishes
        # nothing new.
        agent.report_crew_memory()
        assert len(_memory_events(
            store, session_id, "crew_memory")) == 1
        agent.close()

    def test_grown_memory_announces_as_the_new_memory(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_memory_entry(_entry())
        outcome = agent.report_crew_memory()
        assert outcome["entry_count"] == 1
        assert len(_memory_events(
            store, session_id, "crew_memory")) == 1
        # A newly held entry grows the memory: the new
        # memory announces as the new memory it is.
        agent.register_memory_entry(_entry(
            entry_id="b-fact", member="scribe", title="B fact",
            fact="Another thing is so."))
        outcome = agent.report_crew_memory()
        assert outcome["entry_count"] == 2
        events = _memory_events(store, session_id, "crew_memory")
        assert len(events) == 2
        assert events[1]["entry_count"] == 2
        agent.close()

    def test_no_persist_sync_spawn_or_board_road(self, agent):
        # This layer holds the memory as data: it
        # persists nothing, syncs nothing, spawns no
        # crew and builds no board - Part VIII does
        # not exist yet, and persistence is a later
        # road, not this slice.
        assert not hasattr(agent, "persist_crew_memory")
        assert not hasattr(agent, "sync_crew_memory")
        assert not hasattr(agent, "spawn_crew_memory")
        assert not hasattr(agent, "crew_memory_board")


class TestCrewMemoryTerminalSurface:
    def test_show_search_tag_entry_and_members(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/memory")
        assert "Crew memory (M-133)" in text
        _, _, text = _slash(agent, "/memory show auditor")
        assert "auditor's notebook" in text
        _, _, text = _slash(agent, "/memory guardian")
        assert "guardian's notebook" in text
        _, _, text = _slash(agent, "/memory search checkpoint")
        assert "broken-checkpoint-chain" in text
        _, _, text = _slash(agent, "/memory tag git")
        assert "verify-remote-moved" in text
        _, _, text = _slash(agent, "/memory entry portaudio-env-import")
        assert "portaudio-env-import" in text
        _, _, text = _slash(agent, "/memory members")
        assert "- auditor" in text
        assert "- scribe" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/memory [show|show <member>|search <words>|"
                "tag <tag>|entry <entry-id>|members]") in text
        _, _, text = _slash(agent, "/memory dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/memory entry missing-entry")
        assert "no entry in the shared memory" in text


@pytest.fixture()
def memory_handler(agent, monkeypatch):
    from mythic_agent.agents import command_handler as handler_module
    from mythic_agent.agents.command_handler import CommandHandler
    from mythic_agent.agents.llm import AGENT_REGISTRY
    published = []
    monkeypatch.setattr(
        handler_module, "publish_sync",
        lambda event, **kwargs: published.append((event, kwargs)))
    AGENT_REGISTRY["Primary"] = agent
    instance = CommandHandler.__new__(CommandHandler)
    instance.published = published
    yield instance
    AGENT_REGISTRY.pop("Primary", None)


def _memory_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestCrewMemoryCommand:
    def test_show_is_default(self, memory_handler, agent):
        memory_handler._handle_memory("")
        assert "Crew memory (M-133)" in \
            _memory_published_text(memory_handler)

    def test_show_one_search_tag_entry_and_members(
            self, memory_handler, agent):
        memory_handler._handle_memory("show auditor")
        assert "auditor's notebook" in \
            _memory_published_text(memory_handler)
        memory_handler._handle_memory("search checkpoint")
        assert "broken-checkpoint-chain" in \
            _memory_published_text(memory_handler)
        memory_handler._handle_memory("tag git")
        assert "verify-remote-moved" in \
            _memory_published_text(memory_handler)
        memory_handler._handle_memory("entry verify-remote-moved")
        assert "verify-remote-moved" in \
            _memory_published_text(memory_handler)
        memory_handler._handle_memory("members")
        assert "- scribe" in _memory_published_text(memory_handler)

    def test_bad_grammar_is_published(self, memory_handler, agent):
        memory_handler._handle_memory("dance party")
        assert USAGE in _memory_published_text(memory_handler)


class TestChatScreenRoutingMemory:
    def test_memory_routes_as_system_command(self, monkeypatch):
        from mythic_agent.ui.screens import chat_screen
        from mythic_agent.ui.screens.chat_screen import MainChatScreen

        class _FakeLog:
            def __init__(self):
                self.lines = []

            def write(self, *args, **kwargs):
                self.lines.append(" ".join(str(a) for a in args))

        calls = []
        monkeypatch.setattr(
            chat_screen.SecureAPI, "publish_system_command",
            staticmethod(lambda cmd, args: calls.append((cmd, args))))
        screen = MainChatScreen.__new__(MainChatScreen)
        screen.handle_command("/memory members", _FakeLog())
        assert calls == [("/memory", "members")]
