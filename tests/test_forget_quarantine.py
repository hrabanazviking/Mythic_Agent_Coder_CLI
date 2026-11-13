"""M-157 Forget and quarantine - pure-layer tests.

TIER: integration

The pure layer is the forgetting itself, journaled
as data: one act of forgetting, quarantining or
restoring a memory, carried with the class of thing
it names (a shipped holding's own name) and the
reference the thing stood under - never its content -
with its provenance whole (the word it was done on,
the day, and where the memory stood), composed by
import from the shipped memory layers (M-150, M-153,
M-154, M-155, M-156, M-133) by class and reference
alone, a forget panel derived from the whole book in
settled order, the shipped example book held in a
data file, and a loader that reads a book from any
file. Nothing here calls a model, mutates any live
memory or writes any project's files: journaling the
act is the whole road.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.cross_project_memory import (
    load_cross_project_memory,
)
from mythic_agent.core.decision_records import load_decision_records
from mythic_agent.core.project_memory_map import (
    build_entry as build_map_entry,
    load_project_memory_map,
)
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.self_improving_ledger import (
    load_self_improving_ledger,
)
from mythic_agent.core.session_memory import load_session_memory
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.forget_quarantine import (
    FORGET_ACTIONS,
    FORGET_QUARANTINE_RESOURCE,
    FORGET_QUARANTINE_SCHEMA,
    FORGET_QUARANTINE_SLICE,
    MEMORY_CLASSES,
    PLAIN_EXPLANATION,
    USAGE,
    ForgetActionCount,
    ForgetBook,
    ForgetEntry,
    ForgetPanel,
    ForgetPanelRow,
    ForgetRegistry,
    book_record,
    build_book,
    build_entry,
    build_panel,
    build_row,
    derive_panel,
    entries_from_memory_map,
    entries_from_session_memory,
    entry_from_cross_project,
    entry_from_decision_record,
    entry_from_ledger_candidate,
    entry_from_memory_map,
    entry_from_session_memory,
    entry_record,
    forgotten_entries,
    format_entries,
    format_entry,
    format_forget_quarantine_screen,
    format_forgotten,
    format_panel,
    format_quarantined,
    inspect_memory,
    load_forget_quarantine,
    load_forget_quarantine_file,
    normalize_forget_action,
    normalize_memory_class,
    panel_plain_words,
    panel_record,
    parse_forget_args,
    plain_words,
    validate_book,
    validate_entry,
    validate_panel,
    validate_row,
)

ROOT = Path(__file__).resolve().parents[1]

EXAMPLE_TITLE = "Forget and quarantine at the M-156 slice boundary"

FRAME = {
    "requested_by": "user",
    "acted_on": "2026-11-08",
    "reason": "The user asked for this memory to be forgotten.",
}

SECRET_WORDS = (
    "Call providers through httpx",
    "Provider calls go through httpx",
)


def _entry(**overrides):
    fields = {
        "entry_id": "entry-test",
        "action": "forgotten",
        "memory_class": "session-memory",
        "memory_ref": "note-test",
        "reason": "The user asked for this memory to be forgotten.",
        "requested_by": "user",
        "acted_on": "2026-11-08",
        "source": "test source",
    }
    fields.update(overrides)
    return build_entry(fields)


def _stored_entry(entry):
    stored = entry.to_record()
    stored.pop("type")
    stored.pop("slice")
    return stored


def _stored_panel(panel):
    stored = panel.to_record()
    stored.pop("type")
    stored.pop("slice")
    for row in stored["rows"]:
        row.pop("type")
        row.pop("slice")
    return stored


def _book(entries=None, **overrides):
    fields = {
        "title": "A test forget book",
        "entries": [_stored_entry(item) for item in (
            entries if entries is not None else [_entry()])],
    }
    fields.update(overrides)
    return build_book(fields)


def _shipped_raw():
    path = ROOT / "mythic_agent" / "data" / "forget_quarantine.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_constants_and_usage():
    assert FORGET_QUARANTINE_SLICE == "M-157"
    assert FORGET_QUARANTINE_SCHEMA == "mythic.forget_quarantine/1"
    assert FORGET_QUARANTINE_RESOURCE == "forget_quarantine.yaml"
    assert FORGET_ACTIONS == ("forgotten", "quarantined", "restored")
    assert MEMORY_CLASSES == (
        "session-memory", "cross-project", "ledger-candidate",
        "decision-record", "memory-map", "crew-memory")
    assert "never its content" in PLAIN_EXPLANATION
    assert "mutates no live memory" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /forget")
    assert "entry <entry-id>" in USAGE


def test_roadmap_boundary_is_derived_from_the_shipped_roadmap():
    road = load_roadmap()
    ids = [item.id for item in road.slices]
    assert "M-157" in ids
    mine = road.slices[ids.index("M-157")]
    assert mine.title == "Forget and quarantine"
    assert mine.part == 7
    assert "never its content" in mine.summary
    for earlier in road.slices[:ids.index("M-157")]:
        assert earlier.status == "done", earlier.id


def test_shipped_example_shape():
    book = load_forget_quarantine()
    assert isinstance(book, ForgetBook)
    assert book.title == EXAMPLE_TITLE
    assert book.entry_ids() == (
        "entry-lesson-forgotten", "entry-note-quarantined",
        "entry-note-restored", "entry-record-forgotten")
    assert book.total_entries == 4
    first = book.entries[0]
    assert first.memory_class == "cross-project"
    assert first.action == "forgotten"
    assert first.requested_by == "user"
    assert first.acted_on == "2026-11-08"
    assert len(book.panels) == 1


def test_shipped_panel_is_pinned_and_derived():
    book = load_forget_quarantine()
    panel = book.panel_for("panel-m156-boundary")
    derived = derive_panel(book)
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert [row.entry_id for row in panel.rows] == [
        "entry-lesson-forgotten", "entry-record-forgotten",
        "entry-note-quarantined", "entry-note-restored"]
    assert panel.total_forgotten == 2
    assert panel.total_quarantined == 1
    assert panel.total_restored == 1


def test_normalizers_and_aliases():
    assert normalize_memory_class("Session") == "session-memory"
    assert normalize_memory_class("crossmemory") == "cross-project"
    assert normalize_memory_class("ledger") == "ledger-candidate"
    assert normalize_memory_class("DECISIONS") == "decision-record"
    assert normalize_memory_class("map") == "memory-map"
    assert normalize_memory_class("crew") == "crew-memory"
    assert normalize_forget_action("Forget") == "forgotten"
    assert normalize_forget_action("held") == "quarantined"
    assert normalize_forget_action("restore") == "restored"
    with pytest.raises(ValueError):
        normalize_memory_class("vault")
    with pytest.raises(ValueError):
        normalize_forget_action("edited")


def test_entry_validation_and_alias_spellings():
    entry = _entry()
    assert isinstance(entry, ForgetEntry)
    assert entry.action == "forgotten"
    aliased = build_entry({
        "state": "quarantine", "kind": "map", "ref": "entry-x",
        "why": "Held apart at the user's word.",
        "by": "user", "day": "2026-11-08", "source": "the map"})
    assert aliased.action == "quarantined"
    assert aliased.memory_class == "memory-map"
    assert aliased.memory_ref == "entry-x"
    with pytest.raises(ValueError):
        build_entry({"action": "forgotten"})
    with pytest.raises(ValueError):
        _entry(acted_on="08/11/2026")
    with pytest.raises(ValueError):
        _entry(action="forgotten", acted_on="2026-13-01")


def test_entry_refuses_content_keys_by_name():
    # The honesty heart of the slice: a mapping that
    # tries to journal the forgotten thing's own words
    # refuses, naming the road it broke.
    for key in ("title", "detail", "content", "fact", "decision"):
        fields = _stored_entry(_entry())
        fields[key] = "The forgotten thing's own words."
        with pytest.raises(ValueError, match="never carries"):
            build_entry(fields)
    fields = _stored_entry(_entry())
    fields["surprise"] = "x"
    with pytest.raises(ValueError, match="unknown entry keys"):
        build_entry(fields)
    fields = _stored_entry(_entry())
    fields["class"] = "session-memory"
    fields["memory_class"] = "memory-map"
    with pytest.raises(ValueError, match="two different"):
        build_entry(fields)


def test_entry_refuses_missing_word():
    with pytest.raises(ValueError, match="missing its"):
        build_entry({"action": "forgotten", "memory_class": "map",
                     "memory_ref": "entry-x", "reason": "r",
                     "acted_on": "2026-11-08", "source": "the map"})


def test_composition_from_session_memory_carries_no_content():
    book = load_session_memory()
    notes = [n for s in book.situations for n in s.memory if n.note_id]
    assert notes
    entry = entry_from_session_memory(notes[0], **FRAME)
    assert entry.memory_class == "session-memory"
    assert entry.memory_ref == notes[0].note_id
    assert notes[0].title not in entry_record(entry)["headline"]
    assert notes[0].detail not in str(entry.to_record())
    assert notes[0].title not in plain_words(entry)
    entries = entries_from_session_memory(book, **FRAME)
    assert len(entries) == len(notes)
    assert {e.memory_class for e in entries} == {"session-memory"}


def test_composition_from_cross_project_and_ledger():
    lessons = [item for item in load_cross_project_memory().lessons
               if item.lesson_id]
    assert lessons
    entry = entry_from_cross_project(lessons[0], **FRAME)
    assert entry.memory_class == "cross-project"
    assert entry.memory_ref == lessons[0].lesson_id
    assert lessons[0].detail not in str(entry.to_record())
    candidates = [c for c in load_self_improving_ledger().candidates
                  if c.candidate_id]
    assert candidates
    entry = entry_from_ledger_candidate(
        candidates[0], action="quarantined", **FRAME)
    assert entry.memory_class == "ledger-candidate"
    assert entry.action == "quarantined"
    assert candidates[0].detail not in str(entry.to_record())


def test_composition_from_decision_record_carries_no_content():
    record = load_decision_records().record_for("record-httpx-client")
    entry = entry_from_decision_record(record, **FRAME)
    assert entry.memory_class == "decision-record"
    assert entry.memory_ref == "record-httpx-client"
    for surface in (str(entry.to_record()), plain_words(entry),
                    format_entry(entry), entry_record(entry)["headline"]):
        for secret in SECRET_WORDS:
            assert secret not in surface


def test_composition_from_memory_map_and_inspection():
    shipped = load_project_memory_map()
    first = shipped.entries[0]
    entry = entry_from_memory_map(first, **FRAME)
    assert entry.memory_class == "memory-map"
    assert entry.memory_ref == first.entry_id
    assert first.detail not in str(entry.to_record())
    entries = entries_from_memory_map(shipped, **FRAME)
    assert len(entries) == len(shipped.entries)
    seen = inspect_memory(first)
    assert seen == {"memory_class": "memory-map",
                    "memory_ref": first.entry_id}
    seen = inspect_memory(load_decision_records().records[0])
    assert seen["memory_class"] == "decision-record"
    with pytest.raises(ValueError):
        inspect_memory(object())
    bare = build_map_entry({
        "section": "gotcha", "title": "A bare fact",
        "detail": "A fact with no standing reference.",
        "source": "test", "ref": "nowhere"})
    with pytest.raises(ValueError):
        entry_from_memory_map(bare, **FRAME)


def test_composition_requires_the_frame_words():
    note_book = load_session_memory()
    note = [n for s in note_book.situations for n in s.memory][0]
    with pytest.raises(ValueError, match="frame"):
        entry_from_session_memory(
            note, requested_by=None, acted_on="2026-11-08",
            reason="A reason.")
    with pytest.raises(ValueError, match="frame"):
        validate_entry(note)


def test_restore_law_in_book_and_registry():
    quarantined = _entry(
        entry_id="entry-q", action="quarantined")
    restored = _entry(entry_id="entry-r", action="restored")
    book = _book([quarantined, restored])
    assert book.total_entries == 2
    with pytest.raises(ValueError, match="quarantined"):
        _book([restored])
    with pytest.raises(ValueError, match="quarantined"):
        _book([_entry(entry_id="entry-f"), restored])
    registry = ForgetRegistry()
    with pytest.raises(ValueError, match="quarantined"):
        registry.register_entry(restored)
    registry.register_entry(quarantined)
    assert registry.register_entry(restored).action == "restored"
    # A whole book is judged whole: a restored entry
    # may answer a quarantined entry held later in
    # the same book (the M-156 lesson).
    registry2 = ForgetRegistry()
    held = registry2.register_book(_book(
        [restored, quarantined], title="Reversed book"))
    assert held.total_entries == 2


def test_book_validation_refusals():
    with pytest.raises(ValueError):
        _book([_entry(), _entry()])
    with pytest.raises(ValueError):
        _book([_entry(), _entry(entry_id="entry-other")])
    raw = _shipped_raw()
    raw["schema"] = "mythic.other/1"
    with pytest.raises(ValidationError):
        validate_book(raw)
    raw = _shipped_raw()
    raw["panels"][0]["total_forgotten"] = 3
    with pytest.raises(ValidationError):
        validate_book(raw)
    raw = _shipped_raw()
    raw["entries"][0]["detail"] = "Smuggled content."
    with pytest.raises(ValidationError):
        validate_book(raw)
    raw = _shipped_raw()
    raw["guide"]["title"] = "A different title"
    with pytest.raises(ValidationError):
        validate_book(raw, require_example=True)


def test_load_forget_quarantine_file_roundtrip(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "forget_quarantine.yaml").read_text(encoding="utf-8")
    path = tmp_path / "forget_quarantine.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_forget_quarantine_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.entry_ids()[0] == "entry-lesson-forgotten"
    with pytest.raises(FileNotFoundError):
        load_forget_quarantine_file(tmp_path / "nope.yaml")


def test_registry_holds_entries_one_by_one():
    registry = ForgetRegistry()
    held = registry.register_entry({
        "action": "forgotten", "memory_class": "map",
        "memory_ref": "entry-x", "reason": "At the user's word.",
        "requested_by": "user", "acted_on": "2026-11-08",
        "source": "the map"})
    assert held.entry_id == "entry-1"
    second = registry.register_entry(_entry(entry_id="entry-named"))
    assert second.entry_id == "entry-named"
    assert registry.latest_entry().entry_id == "entry-named"
    assert [e.entry_id for e in registry.list_entries()] == [
        "entry-1", "entry-named"]
    with pytest.raises(ValueError):
        registry.register_entry(_entry(entry_id="entry-named"))
    with pytest.raises(KeyError):
        registry.get_entry("entry-nope")
    named = ForgetRegistry()
    named.register_book(_book())
    assert named.book().title == "A test forget book"
    assert named.panel().total_items == 1
    assert named.forgotten_entries()[0].entry_id == "entry-test"
    with pytest.raises(ValueError):
        named.register_book(_book(title="Another title"))


def test_panel_row_judged_against_its_entry():
    entry = _entry()
    panel = derive_panel(_book([entry]))
    row = panel.rows[0]
    assert isinstance(row, ForgetPanelRow)
    assert validate_row(row, entry) == row
    bad = build_row({
        "action": "forgotten", "entry_id": "entry-test",
        "memory_class": "memory-map", "memory_ref": "note-test",
        "requested_by": "user"})
    with pytest.raises(ValueError, match="disagrees"):
        validate_row(bad, entry)
    with pytest.raises(ValueError, match="never carries"):
        build_row({"action": "forgotten", "entry_id": "entry-test",
                   "memory_class": "session-memory",
                   "memory_ref": "note-test", "requested_by": "user",
                   "title": "Smuggled."})
    counts = panel.action_counts
    assert counts == (ForgetActionCount(action="forgotten", items=1),)


def test_forgotten_entries_only_through_forgetting():
    book = load_forget_quarantine()
    standing = forgotten_entries(book)
    assert [e.entry_id for e in standing] == [
        "entry-lesson-forgotten", "entry-record-forgotten"]
    assert all(e.action == "forgotten" for e in standing)


def test_panel_validation_refusals():
    book = _book()
    panel = derive_panel(book)
    stored = _stored_panel(panel)
    assert validate_panel(stored, book) == panel
    bad = _stored_panel(panel)
    bad["total_items"] = 9
    with pytest.raises(ValueError):
        validate_panel(bad)
    bad = _stored_panel(panel)
    bad["account"] = ["A different account."]
    with pytest.raises(ValueError, match="disagrees"):
        validate_panel(bad, book)
    built = build_panel(_stored_panel(panel))
    assert built == panel


def test_records_and_plain_words_carry_no_content():
    entry = _entry()
    record = entry_record(entry)
    assert record["type"] == "forget_entry"
    assert record["news"] is True
    assert "note-test" in record["headline"]
    assert set(record) == {
        "type", "slice", "entry_id", "action", "memory_class",
        "memory_ref", "reason", "requested_by", "acted_on",
        "source", "news", "headline"}
    words = plain_words(entry)
    assert "session-memory" in words and "not kept here" in words
    book = load_forget_quarantine()
    panel_rec = panel_record(derive_panel(book), book)
    assert panel_rec["headline"].startswith("Forget panel: 4 entries")
    book_rec = book_record(book)
    assert book_rec["entry_count"] == 4
    told = panel_plain_words(book)
    assert "entry-note-restored" in told
    assert "never its content" in told


def test_formatters_and_screen():
    book = load_forget_quarantine()
    text = format_entry(book.entries[0])
    assert "entry-lesson-forgotten" in text
    assert "Content: not kept" in text
    assert "lesson-flaky-test" in format_entries(book)
    assert "entry-record-forgotten" in format_forgotten(book)
    # The restored note stands again: its quarantine
    # is answered, so no memory stands quarantined
    # in the shipped book's net account.
    assert format_quarantined(book) == "No memories stand quarantined."
    panel_text = format_panel(book)
    assert "Forget panel in Forget and quarantine" in panel_text
    screen = format_forget_quarantine_screen()
    assert "Forget and Quarantine (M-157)" in screen
    assert USAGE in screen


def test_parse_forget_args_grammar():
    assert parse_forget_args("") == ("show", None)
    assert parse_forget_args("show") == ("show", None)
    assert parse_forget_args("list") == ("show", None)
    assert parse_forget_args("entry entry-test") == ("entry", "entry-test")
    assert parse_forget_args("forgotten") == ("forgotten", None)
    assert parse_forget_args("quarantined") == ("quarantined", None)
    assert parse_forget_args("panel") == ("panel", None)
    for bad in ("dance", "entry", "entry a b", "forgotten now", 5):
        with pytest.raises(ValueError):
            parse_forget_args(bad)


def test_honest_boundary_module_imports_no_live_roads():
    source = (ROOT / "mythic_agent" / "core"
              / "forget_quarantine.py").read_text(encoding="utf-8")
    assert "from .session_memory import" in source
    assert "from .cross_project_memory import" in source
    assert "from .self_improving_ledger import" in source
    assert "from .decision_records import" in source
    assert "from .project_memory_map import" in source
    assert "from ..agents" not in source
    assert "from ..ui" not in source
    assert "from ..terminal" not in source
    assert "import agents" not in source


def test_composition_from_crew_memory_and_direct_validate():
    from mythic_agent.core.crew_memory import (
        build_entry as build_crew_entry,
    )
    crew_entry = build_crew_entry({
        "entry_id": "crew-note-1", "member": "cartographer",
        "title": "A crew fact held in a notebook",
        "fact": "The crew fact's own words, never journaled.",
        "tags": ["roads"], "provenance": "test source"})
    seen = inspect_memory(crew_entry)
    assert seen == {"memory_class": "crew-memory",
                    "memory_ref": "crew-note-1"}
    entry = validate_entry(crew_entry, **FRAME)
    assert entry.memory_class == "crew-memory"
    assert entry.memory_ref == "crew-note-1"
    assert crew_entry.fact not in str(entry.to_record())
    assert crew_entry.title not in plain_words(entry)
    direct = validate_entry(_stored_entry(_entry()))
    assert direct == _entry()


def test_registry_constructor_and_titleless_book_refusal():
    registry = ForgetRegistry(load_forget_quarantine())
    assert registry.book().title == EXAMPLE_TITLE
    assert registry.panel().total_items == 4
    bare = ForgetRegistry()
    bare.register_entry(_entry(entry_id="entry-solo"))
    with pytest.raises(ValueError, match="no forget book is held"):
        bare.book()
    # The panel still derives from what stands held,
    # title or no title: derivation needs no book.
    assert bare.panel().total_items == 1


# -- agent layer -----------------------------------------------------------
#
# M-157 agent layer: the agent holds a ForgetRegistry
# for the session (session state only, no new setting),
# entries are held by being registered - published as
# their entry_record session news with the derived
# panel_record, through the checkpoint road, deduped
# per shape - the report road renders the held book (or
# the shipped example when unheld) through the pure
# formatters, a journal road reads the session's carried
# memory onto entries and holds them (mutating no live
# memory), and the /forget surface rides both roads on
# the pure parser + formatters. Status, get, panel and
# forgotten reads register and publish nothing, answer
# from the held registry first and from the shipped
# example only while nothing is held - a held session
# never falls back to the example. The panel derives at
# call time from the whole book, never held. This layer
# calls no model, deletes nothing from any holding and
# persists nothing beyond the session journal news, and
# there is no Part VIII board yet, so the screen is
# where the journal is visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _forget_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_forget_book(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "forget_quarantine.yaml").read_text(encoding="utf-8")
    path = tmp_path / "forget_quarantine.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestForgetQuarantineAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.forget_quarantine_status()
        assert status["entries"] == []
        assert status["book"] is None
        assert status["forgetting"]["title"] == EXAMPLE_TITLE
        assert len(status["forgetting"]["entries"]) == 4
        assert status["panel"]["total_items"] == 4
        assert status["panel"]["total_forgotten"] == 2
        assert status["panels"][0]["panel_id"] == "panel-m156-boundary"
        assert status["book_record"]["entry_count"] == 4
        assert "Forget and Quarantine (M-157)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._forget_quarantine_registry()
        assert agent._forget_quarantine_registry() is first
        assert agent._forget_quarantine_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.forget_quarantine_status()
        agent.get_forget_entry("entry-lesson-forgotten")
        agent.forget_quarantine_panel()
        agent.forgotten_memories()
        agent.report_forget_quarantine()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("forget_")] == []
        agent.close()

    def test_unheld_reads_raise(self, agent):
        with pytest.raises(KeyError):
            agent.get_forget_entry("entry-nope")

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_forget_entry(_entry())
        status = agent.forget_quarantine_status()
        assert [item["entry_id"] for item in status["entries"]] == [
            "entry-test"]
        assert status["book"]["title"] == "Forget and quarantine"

    def test_held_session_never_falls_back_to_the_example(
            self, agent):
        agent.register_forget_entry(_entry())
        with pytest.raises(KeyError):
            agent.get_forget_entry("entry-lesson-forgotten")
        entry = agent.get_forget_entry("entry-test")
        assert entry.memory_ref == "note-test"
        assert agent.forget_quarantine_book().title == (
            "Forget and quarantine")


class TestForgetQuarantineAgentHolding:
    def test_register_entry_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_forget_entry(_entry())
        assert outcome["entry"]["entry_id"] == "entry-test"
        assert outcome["entry_news"]["type"] == "forget_entry"
        events = _forget_events(store, session_id, "forget_entry")
        assert len(events) == 1
        assert events[0]["entry_id"] == "entry-test"
        agent._publish_forget_record(outcome["entry_news"])
        assert len(_forget_events(
            store, session_id, "forget_entry")) == 1
        agent._publish_forget_record(
            {"type": "mentions_mention", "mention_id": "mention-x"})
        agent._publish_forget_record(book_record(load_forget_quarantine()))
        for kind in ("mentions_mention", "forget_book"):
            assert _forget_events(store, session_id, kind) == []
        agent.close()

    def test_duplicate_entry_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_forget_entry(_entry())
        with pytest.raises(ValueError):
            agent.register_forget_entry(_entry())
        assert len(_forget_events(
            store, session_id, "forget_entry")) == 1
        agent.close()

    def test_journal_from_session_memory_carries_no_content(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        memory_book = load_session_memory()
        notes = [n for s in memory_book.situations for n in s.memory
                 if n.note_id]
        expected = len(notes)
        outcome = agent.journal_forgetting_from_session_memory(**FRAME)
        assert outcome["count"] == expected
        events = _forget_events(store, session_id, "forget_entry")
        assert len(events) == expected
        # The honesty heart at the agent layer: no
        # carried note's title or detail stands in any
        # journaled event, entry or headline.
        blob = str(events) + str(outcome["entries"])
        for note in notes:
            assert note.title not in blob
            assert note.detail not in blob
        # Journaling mutated no live memory: the
        # session's carried memory stands whole.
        assert agent.session_memory_book().situations == (
            memory_book.situations)
        assert agent.forget_quarantine_panel().total_forgotten == expected
        with pytest.raises(ValueError):
            agent.journal_forgetting_from_session_memory(**FRAME)
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent):
        book = _book()
        outcome = agent.register_forget_book(book)
        assert outcome["count"] == 1
        assert [item["type"] for item in outcome["entries_news"]] == [
            "forget_entry"]
        assert agent.forget_quarantine_book().title == (
            "A test forget book")

    def test_register_book_twice_refuses(self, agent):
        agent.register_forget_book(load_forget_quarantine())
        with pytest.raises(ValueError):
            agent.register_forget_book(load_forget_quarantine())

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_forget_book()
        assert outcome["count"] == 4
        assert outcome["book"]["title"] == EXAMPLE_TITLE
        assert len(_forget_events(
            store, session_id, "forget_entry")) == 4
        assert agent.forget_quarantine_book().panels[0].panel_id == (
            "panel-m156-boundary")
        agent.close()

    def test_record_same_book_twice_refuses(self, agent):
        agent.record_forget_book()
        with pytest.raises(ValueError):
            agent.record_forget_book()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_forget_book(tmp_path)
        book = load_forget_quarantine_file(path)
        outcome = agent.record_forget_book(book)
        assert outcome["count"] == 4
        assert agent.get_forget_entry(
            "entry-record-forgotten").memory_ref == "record-stdlib-http"

    def test_report_renders_the_example_when_unheld(self, agent):
        report = agent.report_forget_quarantine()
        assert report["book"]["entry_count"] == 4
        assert "entry-lesson-forgotten" in report["entries_text"]
        assert "Forget panel in Forget and quarantine" in (
            report["panel_text"])
        assert "entry-note-quarantined" not in report["quarantined_text"]
        assert "No memories stand quarantined." in (
            report["quarantined_text"])

    def test_report_renders_the_held_book_only(self, agent):
        agent.register_forget_entry(_entry())
        report = agent.report_forget_quarantine()
        assert report["book"]["title"] == "Forget and quarantine"
        assert "entry-lesson-forgotten" not in report["entries_text"]
        assert "entry-test" in report["entries_text"]

    def test_report_registers_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.report_forget_quarantine()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("forget_")] == []
        agent.close()

    def test_no_live_delete_or_persist_road(
            self, agent, tmp_path):
        # This layer journals acts of forgetting as
        # data: it calls no model, deletes nothing from
        # any live holding, writes no project files and
        # persists nothing - and there is no Part VIII
        # board yet. Holding, recording or journaling
        # changes no workspace file and no live context.
        assert not hasattr(agent, "apply_forget_quarantine")
        assert not hasattr(agent, "delete_forget_quarantine")
        assert not hasattr(agent, "persist_forget_quarantine")
        assert not hasattr(agent, "forget_quarantine_board")
        (tmp_path / "alpha.py").write_text(
            "def greet(name):\n    return name\n", encoding="utf-8")
        before = {
            p.name: p.read_bytes()
            for p in tmp_path.glob("*.py")}
        from mythic_agent.agents.context import ContextBuilder
        builder = ContextBuilder(max_tokens=4000)
        builder.add_system("You are the coder.")
        builder.add_turn("user", "Build the slice.")
        built_before = builder.build()
        agent.register_forget_entry(_entry())
        agent.record_forget_book()
        assert builder.build() == built_before
        assert {
            p.name: p.read_bytes()
            for p in tmp_path.glob("*.py")} == before


class TestForgetQuarantineTerminalSurface:
    def test_show_entry_forgotten_quarantined_panel(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/forget")
        assert "Forget and Quarantine (M-157)" in text
        _, _, text = _slash(agent, "/forget entry entry-lesson-forgotten")
        assert "lesson-flaky-test" in text
        assert "Content: not kept" in text
        _, _, text = _slash(agent, "/forget forgotten")
        assert "entry-record-forgotten" in text
        _, _, text = _slash(agent, "/forget quarantined")
        assert "No memories stand quarantined." in text
        _, _, text = _slash(agent, "/forget panel")
        assert "Forget panel in Forget and quarantine" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/forget [show|entry <entry-id>"
                "|forgotten|quarantined|panel]") in text
        _, _, text = _slash(agent, "/forget dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/forget entry entry-nope")
        assert "no entry in the book" in text


@pytest.fixture()
def forget_handler(agent, monkeypatch):
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


def _forget_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestForgetQuarantineCommand:
    def test_show_is_default(self, forget_handler, agent):
        forget_handler._handle_forget("")
        assert "Forget and Quarantine (M-157)" in (
            _forget_published_text(forget_handler))

    def test_entry_forgotten_quarantined_panel(
            self, forget_handler, agent):
        forget_handler._handle_forget("entry entry-lesson-forgotten")
        assert "lesson-flaky-test" in (
            _forget_published_text(forget_handler))
        forget_handler._handle_forget("forgotten")
        assert "entry-record-forgotten" in (
            _forget_published_text(forget_handler))
        forget_handler._handle_forget("quarantined")
        assert "No memories stand quarantined." in (
            _forget_published_text(forget_handler))
        forget_handler._handle_forget("panel")
        assert "Forget panel in Forget and quarantine" in (
            _forget_published_text(forget_handler))

    def test_bad_grammar_is_published(self, forget_handler, agent):
        forget_handler._handle_forget("dance party")
        assert USAGE in _forget_published_text(forget_handler)


class TestChatScreenRoutingForget:
    def test_forget_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command(
            "/forget entry entry-lesson-forgotten", _FakeLog())
        assert calls == [("/forget", "entry entry-lesson-forgotten")]
