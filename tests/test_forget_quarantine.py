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
