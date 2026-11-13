"""M-150 Project Memory Map (Mythic law) - pure-layer tests.

TIER: integration

The pure layer is the project memory map as data:
one book of entry records (one fact of the living
map - its section in the closed set this slice
names, its title, the fact itself in plain words,
its source, and the reference where the thing it
names lives), the shipped example book held in a
data file, a loader that reads a book from any
file, a panel derived from the whole book in map
order (section first, then title - so two panels
diff cleanly), kept by the Scribe, a scan road that
reads a real workspace's PROJECT_MEMORY_MAP.md
convention file, the Scribe's directives read off
the shipped method charter by import, records
shaped as session news, and a registry. A stored
panel disagreeing with the panel derived from its
book is refused. Nothing here writes or edits a
project file: holding the map changes no file, and
a scan leaves every workspace file byte-identical.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.validation import ValidationError
from mythic_agent.core.project_memory_map import (
    PLAIN_EXPLANATION,
    PROJECT_MEMORY_MAP_RESOURCE,
    PROJECT_MEMORY_MAP_SCHEMA,
    PROJECT_MEMORY_MAP_SLICE,
    MAP_KEEPER,
    MAP_SECTIONS,
    MAP_SECTION_HEADINGS,
    USAGE,
    MemoryMapBook,
    MemoryMapEntry,
    MemoryMapPanel,
    MemoryMapPanelRow,
    MemoryMapRegistry,
    MemoryMapSectionCount,
    book_record,
    build_book,
    build_entry,
    build_panel,
    build_row,
    derive_panel,
    entry_record,
    format_entries,
    format_entry,
    format_panel,
    format_project_memory_map_screen,
    load_project_memory_map,
    load_project_memory_map_file,
    normalize_section,
    panel_plain_words,
    panel_record,
    parse_memory_map_args,
    plain_words,
    scan_workspace,
    scribe_directives,
    validate_book,
    validate_entry,
    validate_panel,
    validate_row,
)

ROOT = Path(__file__).resolve().parents[1]


def _entry(**overrides):
    fields = {
        "section": "gotcha", "title": "A test gotcha",
        "detail": "A fact won the hard way in tests.",
        "source": "test suite",
        "ref": "tests/test_project_memory_map.py",
        "entry_id": "map-test-gotcha",
    }
    fields.update(overrides)
    return build_entry(fields)


def test_constants_and_usage():
    assert PROJECT_MEMORY_MAP_SLICE == "M-150"
    assert PROJECT_MEMORY_MAP_SCHEMA == "mythic.project_memory_map/1"
    assert PROJECT_MEMORY_MAP_RESOURCE.endswith("project_memory_map.yaml")
    assert MAP_SECTIONS == ("architecture", "decision", "gotcha", "location")
    assert MAP_KEEPER == "Scribe"
    assert "/memorymap" in USAGE
    assert "Scribe" in PLAIN_EXPLANATION


def test_headings_compose_onto_the_closed_sections():
    # The shipped markdown map's own headings are the
    # sections' faces - never a second taxonomy.
    assert set(MAP_SECTION_HEADINGS.values()) == set(MAP_SECTIONS)
    assert MAP_SECTION_HEADINGS["Where things live"] == "location"
    assert MAP_SECTION_HEADINGS["Working facts & gotchas"] == "gotcha"
    assert MAP_SECTION_HEADINGS["Campaign state"] == "decision"
    assert MAP_SECTION_HEADINGS["What this is"] == "architecture"


def test_scribe_directives_come_from_the_charter():
    # The Scribe's law is the shipped method charter's
    # PROJECT_MEMORY_MAP plug (F-03), composed by
    # import - never a second copy in this module.
    directives = scribe_directives()
    assert len(directives) == 4
    assert directives[0].startswith("Keep the project's memory map current")
    assert "same session" in directives[1]
    source = (ROOT / "mythic_agent" / "core"
              / "project_memory_map.py").read_text(encoding="utf-8")
    assert "from .method_charter import load_charter" in source


def test_shipped_example_shape():
    book = load_project_memory_map()
    assert book.title == "Project memory map at the M-149 slice boundary"
    assert [e.entry_id for e in book.entries] == [
        "map-package", "map-agents", "map-tests",
        "map-two-roads", "map-offices", "map-ci-manual",
        "map-scribe-law", "map-no-docker", "map-suite-extras"]
    assert [e.section for e in book.entries] == [
        "location", "location", "location",
        "architecture", "architecture", "decision",
        "decision", "gotcha", "gotcha"]
    assert book.entry_for("map-package").title == "The package"
    with pytest.raises(KeyError):
        book.entry_for("map-nope")
    assert [e.entry_id for e in book.entries_for_section("gotcha")] == [
        "map-no-docker", "map-suite-extras"]
    assert [e.entry_id for e in book.entries_for_section("locations")] == [
        "map-package", "map-agents", "map-tests"]


def test_shipped_panel_is_pinned_and_derived():
    book = load_project_memory_map()
    assert len(book.panels) == 1
    stored = book.panels[0]
    assert stored.panel_id == "panel-m149-boundary"
    assert stored.keeper == "Scribe"
    assert [r.entry_id for r in stored.rows] == [
        "map-offices", "map-two-roads", "map-ci-manual",
        "map-scribe-law", "map-no-docker", "map-suite-extras",
        "map-agents", "map-package", "map-tests"]
    assert stored.total_entries == 9
    assert [(c.section, c.entries) for c in stored.section_counts] == [
        ("architecture", 2), ("decision", 2),
        ("gotcha", 2), ("location", 3)]
    assert stored.account[0] == (
        "The panel holds 9 project memory map entries: "
        "architecture 2, decision 2, gotcha 2, location 3.")
    derived = derive_panel(book)
    assert derived.rows == stored.rows
    assert derived.section_counts == stored.section_counts
    assert derived.account == stored.account
    assert validate_panel(stored, book) == stored


def test_normalize_section_reads_the_roadmap_faces():
    assert normalize_section("architecture") == "architecture"
    assert normalize_section("Decisions") == "decision"
    assert normalize_section("gotchas") == "gotcha"
    assert normalize_section("locations") == "location"
    assert normalize_section("where-things-live") == "location"
    with pytest.raises(ValueError):
        normalize_section("rumours")


def test_entry_validation_and_aliases():
    entry = build_entry({
        "kind": "decisions", "name": "An aliased decision",
        "body": "Named through the alias spellings.",
        "source": "test suite", "path": "tests/",
        "id": "map-alias-decision"})
    assert entry.entry_id == "map-alias-decision"
    assert entry.section == "decision"
    assert entry.title == "An aliased decision"
    assert entry.detail == "Named through the alias spellings."
    assert entry.ref == "tests/"
    with pytest.raises(ValueError):
        build_entry({"section": "gotcha", "title": "x",
                     "detail": "y", "source": "z",
                     "ref": "tests/", "bogus": 1})
    with pytest.raises(ValueError):
        build_entry({"title": "No section named.",
                     "detail": "y", "source": "z", "ref": "tests/"})
    with pytest.raises(ValueError):
        build_entry({"section": "gotcha", "kind": "decision",
                     "title": "Two spellings disagree.",
                     "detail": "y", "source": "z", "ref": "tests/"})
    with pytest.raises(ValueError):
        _entry(ref="a ref with spaces")
    with pytest.raises(ValueError):
        _entry(ref="x" * 301)
    with pytest.raises(ValueError):
        _entry(section="rumours")


def test_row_is_derived_and_judged():
    entry = _entry()
    row = build_row(entry)
    assert row.section == "gotcha"
    assert row.entry_id == "map-test-gotcha"
    assert validate_row(row, entry) == row
    with pytest.raises(ValueError):
        validate_row(build_row({
            "section": "location", "title": "Somewhere else",
            "source": "test suite", "ref": "elsewhere/",
            "entry_id": "map-other"}), entry)


def test_derive_panel_orders_and_counts():
    book = build_book({
        "title": "A small map",
        "entries": [
            {"section": "location", "title": "The package",
             "detail": "Where the package lives.",
             "source": "test suite", "ref": "pkg/",
             "entry_id": "e-package"},
            {"section": "architecture", "title": "The two roads",
             "detail": "How the roads bind.",
             "source": "test suite", "ref": "docs/",
             "entry_id": "e-roads"},
            {"section": "gotcha", "title": "No Docker, anywhere",
             "detail": "A standing law.",
             "source": "test suite", "ref": "laws.md",
             "entry_id": "e-docker"},
        ]})
    panel = derive_panel(book)
    assert [r.entry_id for r in panel.rows] == [
        "e-roads", "e-docker", "e-package"]
    assert panel.total_entries == 3
    assert panel.keeper == "Scribe"
    assert [(c.section, c.entries) for c in panel.section_counts] == [
        ("architecture", 1), ("gotcha", 1), ("location", 1)]
    assert panel.account[0] == (
        "The panel holds 3 project memory map entries: "
        "architecture 1, gotcha 1, location 1.")
    assert panel.row_for("e-docker").title == "No Docker, anywhere"
    with pytest.raises(KeyError):
        panel.row_for("e-nope")
    with pytest.raises(ValueError):
        derive_panel([])


def test_panel_internal_inconsistency_refuses():
    row = build_row(_entry())
    with pytest.raises(ValueError):
        MemoryMapPanel(
            rows=[row], total_entries=5,
            section_counts=[MemoryMapSectionCount(
                section="gotcha", entries=1)],
            account=["A lying total."])
    earlier = build_row(_entry(
        section="architecture", title="An earlier section",
        entry_id="map-earlier"))
    with pytest.raises(ValueError):
        MemoryMapPanel(
            rows=[row, earlier], total_entries=2,
            section_counts=[
                MemoryMapSectionCount(section="gotcha", entries=1),
                MemoryMapSectionCount(section="architecture", entries=1)],
            account=["Rows out of order."])
    with pytest.raises(ValueError) as caught:
        MemoryMapPanel(
            rows=[row], total_entries=1,
            section_counts=[MemoryMapSectionCount(
                section="gotcha", entries=1)],
            account=["Kept by someone else."], keeper="Cartographer")
    assert "kept by the Scribe" in str(caught.value)


def test_validate_panel_judged_against_its_source():
    book = load_project_memory_map()
    panel = derive_panel(book)
    smaller = build_book({
        "title": "A smaller map",
        "entries": [
            {"section": "location", "title": "The package",
             "detail": "Where the package lives.",
             "source": "test suite", "ref": "pkg/",
             "entry_id": "e-package"}]})
    with pytest.raises(ValueError):
        validate_panel(panel, smaller)
    assert validate_panel(panel, book).rows == panel.rows


def test_book_validation_refusals():
    with pytest.raises(ValueError):
        build_book({"title": "Empty", "entries": []})
    with pytest.raises(ValueError):
        build_book({"title": "Twins", "entries": [
            {"section": "gotcha", "title": "One",
             "detail": "One.", "source": "s", "ref": "a/",
             "entry_id": "e-same"},
            {"section": "gotcha", "title": "Two",
             "detail": "Two.", "source": "s", "ref": "b/",
             "entry_id": "e-same"}]})
    with pytest.raises(ValueError):
        build_book({"title": "Same fact twice", "entries": [
            {"section": "gotcha", "title": "Same title",
             "detail": "One.", "source": "s", "ref": "a/",
             "entry_id": "e-one"},
            {"section": "gotcha", "title": "Same title",
             "detail": "Two.", "source": "s", "ref": "b/",
             "entry_id": "e-two"}]})
    with pytest.raises(ValueError):
        validate_book({"title": "No entries at all"})


def test_load_project_memory_map_file_roundtrip(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "project_memory_map.yaml").read_text(encoding="utf-8")
    path = tmp_path / "project_memory_map.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_project_memory_map_file(path)
    assert book.title == load_project_memory_map().title
    assert book.entry_ids() == load_project_memory_map().entry_ids()
    bad = tmp_path / "bad.yaml"
    bad.write_text("schema: mythic.other/9\nentries: []\n",
                   encoding="utf-8")
    with pytest.raises((ValueError, ValidationError)):
        load_project_memory_map_file(bad)


def test_registry_holds_entries_one_by_one():
    registry = MemoryMapRegistry()
    first = registry.register_entry({
        "section": "location", "title": "The package",
        "detail": "Where the package lives.",
        "source": "test suite", "ref": "pkg/"})
    second = registry.register_entry(_entry())
    assert first.entry_id == "map-1"
    assert second.entry_id == "map-test-gotcha"
    assert [e.entry_id for e in registry.list_entries()] == [
        "map-1", "map-test-gotcha"]
    with pytest.raises(ValueError):
        registry.register_entry(_entry())
    with pytest.raises(ValueError):
        registry.register_entry({
            "section": "gotcha", "title": "A test gotcha",
            "detail": "The same fact again.",
            "source": "test suite", "ref": "elsewhere/",
            "entry_id": "map-other-id"})
    assert registry.get_entry("map-1").title == "The package"
    with pytest.raises(KeyError):
        registry.get_entry("map-99")


def test_registry_book_title_and_panel():
    registry = MemoryMapRegistry()
    registry.register_book(load_project_memory_map())
    assert registry.book().title == (
        "Project memory map at the M-149 slice boundary")
    assert registry.panel().total_entries == 9
    assert registry.panel().keeper == "Scribe"
    other = build_book({
        "title": "Another map",
        "entries": [
            {"section": "location", "title": "The package",
             "detail": "Where the package lives.",
             "source": "test suite", "ref": "pkg/",
             "entry_id": "e-fresh"}]})
    with pytest.raises(ValueError):
        registry.register_book(other)
    fresh = MemoryMapRegistry()
    with pytest.raises(ValueError):
        fresh.book()


def test_records_and_plain_words():
    book = load_project_memory_map()
    entry = book.entry_for("map-package")
    record = entry_record(entry)
    assert record["type"] == "project_memory_map_entry"
    assert record["news"] is True
    assert record["entry_id"] == "map-package"
    assert record["section"] == "location"
    assert "The package (location)" in record["headline"]
    panel_rec = panel_record(derive_panel(book))
    assert panel_rec["type"] == "project_memory_map_panel"
    assert panel_rec["total_entries"] == 9
    assert panel_rec["keeper"] == "Scribe"
    book_rec = book_record(book)
    assert book_rec["type"] == "project_memory_map_book"
    assert book_rec["entry_count"] == 9
    assert book_rec["panel_count"] == 1
    assert plain_words(entry) == (
        "The package - location, at mythic_agent/ "
        "from PROJECT_MEMORY_MAP.md: mythic_agent/ is the "
        "package; entry points mythic (mythic_agent.cli:main) "
        "and mythic-mcp (mythic_agent.mcp_server:main).")
    told = panel_plain_words(book)
    assert "location: The package" in told
    assert "The panel holds 9 project memory map entries" in told


def test_formatters_and_screen():
    book = load_project_memory_map()
    entry = book.entry_for("map-agents")
    assert format_entry(entry) == (
        "map-agents: The agent loop - location "
        "(mythic_agent/agents/ from PROJECT_MEMORY_MAP.md)")
    whole = format_entries(book)
    assert whole.count("\n") == 8
    gotchas = format_entries(book, "gotcha")
    assert "map-no-docker" in gotchas
    assert "map-package" not in gotchas
    panel_text = format_panel(book)
    assert panel_text.startswith(
        "Panel in Project memory map at the M-149 slice boundary:")
    assert "map-tests: location" in panel_text
    screen = format_project_memory_map_screen()
    assert screen.startswith("Project Memory Map (M-150) - ")
    assert "panel-m149-boundary" not in screen
    assert USAGE in screen


def test_parse_memory_map_args_grammar():
    assert parse_memory_map_args("") == ("show", None)
    assert parse_memory_map_args("show") == ("show", None)
    assert parse_memory_map_args("list") == ("show", None)
    assert parse_memory_map_args("panel") == ("panel", None)
    assert parse_memory_map_args(
        "entry map-package") == ("entry", "map-package")
    assert parse_memory_map_args(
        "section gotchas") == ("section", "gotcha")
    assert parse_memory_map_args(
        "section locations") == ("section", "location")
    for bad in ("dance party", "entry", "section rumours",
                "panel now", "entry a b"):
        with pytest.raises(ValueError) as caught:
            parse_memory_map_args(bad)
        assert str(caught.value) == USAGE
    with pytest.raises(ValueError):
        parse_memory_map_args(42)


def _write_convention_map(root):
    (root / "PROJECT_MEMORY_MAP.md").write_text(
        "# Project Memory Map\n\n"
        "## Where things live\n\n"
        "- `pkg/` - the package lives here.\n\n"
        "## Working facts & gotchas\n\n"
        "Never feed the gremlins after midnight.\n\n"
        "## Campaign state\n\n"
        "The campaign stands at the test boundary.\n",
        encoding="utf-8")
    return root


def _snapshot_bytes(root):
    return {str(p.relative_to(root)): p.read_bytes()
            for p in sorted(root.rglob("*")) if p.is_file()}


def test_scan_workspace_reads_the_convention_file(tmp_path):
    _write_convention_map(tmp_path)
    entries = scan_workspace(tmp_path)
    by_id = {e.entry_id: e for e in entries}
    assert set(by_id) == {
        "scan-where-things-live", "scan-working-facts-gotchas",
        "scan-campaign-state"}
    assert by_id["scan-where-things-live"].section == "location"
    assert by_id["scan-where-things-live"].detail == (
        "`pkg/` - the package lives here.")
    assert by_id["scan-working-facts-gotchas"].section == "gotcha"
    assert by_id["scan-campaign-state"].section == "decision"
    panel = derive_panel(entries)
    assert [r.section for r in panel.rows] == [
        "decision", "gotcha", "location"]


def test_scan_workspace_without_a_convention_file_is_empty(tmp_path):
    assert scan_workspace(tmp_path) == ()


def test_honest_boundary_scan_mutates_nothing(tmp_path):
    _write_convention_map(tmp_path)
    before = _snapshot_bytes(tmp_path)
    entries = scan_workspace(tmp_path)
    derive_panel(entries)
    assert _snapshot_bytes(tmp_path) == before


def test_honest_boundary_module_imports_no_live_roads():
    source = (ROOT / "mythic_agent" / "core"
              / "project_memory_map.py").read_text(encoding="utf-8")
    for forbidden in ("from ..agents", "from ..ui",
                      "from ..terminal", "import requests",
                      "urlopen"):
        assert forbidden not in source
    # The shipped roads it does compose are the
    # convention file it reads and the method
    # charter it imports.
    assert "from .method_charter import load_charter" in source
    assert "PROJECT_MEMORY_MAP.md" in source


# -- agent layer -----------------------------------------------------------
#
# M-150 agent layer: the agent holds a
# MemoryMapRegistry for the session (session state
# only, no new setting), entries are held by being
# registered - published as their entry_record
# session news with the derived panel_record,
# through the checkpoint road, deduped per shape -
# the report road renders the held book (or the
# shipped example when unheld) through the pure
# formatters, and the /memorymap surface rides both
# roads on the pure parser + formatters. Status,
# get, section and panel reads register and publish
# nothing, answer from the held registry first and
# from the shipped example only while nothing is
# held - a held session never falls back to the
# example. The panel derives at call time from the
# held entries, never held. This layer writes and
# edits no project file, and there is no Part VIII
# board yet, so the screen is where the map is
# visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _map_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_map_book(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "project_memory_map.yaml").read_text(encoding="utf-8")
    path = tmp_path / "project_memory_map.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestProjectMemoryMapAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.project_memory_map_status()
        assert status["entries"] == []
        assert status["book"] is None
        assert status["project_memory_map"]["title"] == (
            "Project memory map at the M-149 slice boundary")
        assert len(status["project_memory_map"]["entries"]) == 9
        assert status["panel"]["total_entries"] == 9
        assert status["panel"]["keeper"] == "Scribe"
        assert status["book_record"]["entry_count"] == 9
        assert "Project Memory Map (M-150)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._project_memory_map_registry()
        assert agent._project_memory_map_registry() is first
        assert agent._project_memory_map_store is first

    def test_reads_register_and_publish_nothing(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.project_memory_map_status()
        agent.get_memory_map_entry("map-package")
        agent.project_memory_map_for_section("gotcha")
        agent.project_memory_map_panel()
        agent.report_project_memory_map()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("project_memory_map")] == []
        agent.close()

    def test_unheld_reads_raise(self, agent):
        with pytest.raises(KeyError):
            agent.get_memory_map_entry("map-nope")

    def test_status_after_register_shows_the_held_pieces(self, agent):
        agent.register_memory_map_entry(_entry())
        status = agent.project_memory_map_status()
        assert [e["entry_id"] for e in status["entries"]] == [
            "map-test-gotcha"]
        assert status["book"]["title"] == "Session project memory map"
        assert status["panel"]["total_entries"] == 1
        assert status["panel"]["rows"][0]["section"] == "gotcha"

    def test_held_session_never_falls_back_to_the_example(self, agent):
        agent.register_memory_map_entry(_entry())
        with pytest.raises(KeyError):
            agent.get_memory_map_entry("map-package")
        assert agent.project_memory_map_for_section("location") == ()
        assert [e.entry_id for e in
                agent.project_memory_map_for_section("gotcha")] == [
                    "map-test-gotcha"]
        assert agent.project_memory_map_book().title == (
            "Session project memory map")


class TestProjectMemoryMapAgentHolding:
    def test_register_entry_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_memory_map_entry(_entry())
        assert outcome["entry"]["entry_id"] == "map-test-gotcha"
        assert outcome["record"]["type"] == "project_memory_map_entry"
        assert outcome["panel_record"]["type"] == (
            "project_memory_map_panel")
        events = _map_events(
            store, session_id, "project_memory_map_entry")
        assert len(events) == 1
        assert events[0]["entry_id"] == "map-test-gotcha"
        panels = _map_events(
            store, session_id, "project_memory_map_panel")
        assert len(panels) == 1
        assert panels[0]["total_entries"] == 1
        agent._publish_project_memory_map_record(outcome["record"])
        agent._publish_project_memory_map_record(outcome["panel_record"])
        assert len(_map_events(
            store, session_id, "project_memory_map_entry")) == 1
        assert len(_map_events(
            store, session_id, "project_memory_map_panel")) == 1
        from mythic_agent.core.context_budget import (
            book_record as _budget_book_record, load_context_budget)
        agent._publish_project_memory_map_record(
            {"type": "mentions_mention", "mention_id": "mention-x"})
        agent._publish_project_memory_map_record(
            _budget_book_record(load_context_budget()))
        agent._publish_project_memory_map_record(
            book_record(load_project_memory_map()))
        for kind in ("mentions_mention", "context_budget_book",
                     "project_memory_map_book"):
            assert _map_events(store, session_id, kind) == []
        agent.close()

    def test_register_entry_without_id_gets_a_map_id(self, agent):
        outcome = agent.register_memory_map_entry({
            "section": "location", "title": "The package",
            "detail": "Where the package lives.",
            "source": "test suite", "ref": "pkg/"})
        assert outcome["entry"]["entry_id"] == "map-1"

    def test_duplicate_entry_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_memory_map_entry(_entry())
        with pytest.raises(ValueError):
            agent.register_memory_map_entry(_entry())
        assert len(_map_events(
            store, session_id, "project_memory_map_entry")) == 1
        agent.close()

    def test_scan_and_register_holds_the_convention_map(
            self, agent, tmp_path):
        workspace = tmp_path / "ws"
        workspace.mkdir()
        _write_convention_map(workspace)
        before = _snapshot_bytes(workspace)
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.scan_and_register_project_memory_map(workspace)
        assert outcome["count"] == 3
        assert [e["entry_id"] for e in outcome["entries"]] == [
            "scan-where-things-live", "scan-working-facts-gotchas",
            "scan-campaign-state"]
        assert len(_map_events(
            store, session_id, "project_memory_map_entry")) == 3
        assert agent.project_memory_map_panel().total_entries == 3
        # Scanning and holding changed no file.
        assert _snapshot_bytes(workspace) == before
        agent.close()

    def test_register_book_holds_and_publishes_in_order(self, agent):
        book = build_book({
            "title": "A held map",
            "entries": [
                {"section": "location", "title": "The package",
                 "detail": "Where the package lives.",
                 "source": "test suite", "ref": "pkg/",
                 "entry_id": "held-package"},
                {"section": "gotcha", "title": "No Docker, anywhere",
                 "detail": "A standing law.",
                 "source": "test suite", "ref": "laws.md",
                 "entry_id": "held-docker"}]})
        outcome = agent.register_project_memory_map_book(book)
        assert outcome["count"] == 2
        assert [r["entry_id"] for r in outcome["records"]] == [
            "held-package", "held-docker"]
        assert agent.project_memory_map_book().title == "A held map"

    def test_register_book_twice_refuses(self, agent):
        agent.register_project_memory_map_book(load_project_memory_map())
        with pytest.raises(ValueError):
            agent.register_project_memory_map_book(
                load_project_memory_map())

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_project_memory_map_book()
        assert outcome["count"] == 9
        assert outcome["book"]["title"] == (
            "Project memory map at the M-149 slice boundary")
        assert len(_map_events(
            store, session_id, "project_memory_map_entry")) == 9
        assert agent.project_memory_map_book().panels[0].panel_id == (
            "panel-m149-boundary")
        agent.close()

    def test_record_same_book_twice_refuses(self, agent):
        agent.record_project_memory_map_book()
        with pytest.raises(ValueError):
            agent.record_project_memory_map_book()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_map_book(tmp_path)
        book = load_project_memory_map_file(path)
        outcome = agent.record_project_memory_map_book(book)
        assert outcome["count"] == 9
        assert agent.get_memory_map_entry(
            "map-no-docker").section == "gotcha"

    def test_one_by_one_holdings_stand_under_a_session_book(self, agent):
        agent.register_memory_map_entry(_entry())
        agent.register_memory_map_entry({
            "section": "location", "title": "The package",
            "detail": "Where the package lives.",
            "source": "test suite", "ref": "pkg/",
            "entry_id": "map-test-package"})
        book = agent.project_memory_map_book()
        assert book.title == "Session project memory map"
        assert [e.entry_id for e in book.entries] == [
            "map-test-gotcha", "map-test-package"]
        panel = agent.project_memory_map_panel()
        assert [r.entry_id for r in panel.rows] == [
            "map-test-gotcha", "map-test-package"]

    def test_report_renders_the_example_when_unheld(self, agent):
        report = agent.report_project_memory_map()
        assert report["book"]["entry_count"] == 9
        assert "map-package" in report["entries_text"]
        assert "Panel in Project memory map" in report["panel_text"]

    def test_report_renders_the_held_book_only(self, agent):
        agent.register_memory_map_entry(_entry())
        report = agent.report_project_memory_map()
        assert report["book"]["title"] == "Session project memory map"
        assert "map-package" not in report["entries_text"]
        assert "map-test-gotcha" in report["entries_text"]

    def test_report_registers_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.report_project_memory_map()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("project_memory_map")] == []
        agent.close()

    def test_no_live_write_edit_or_persist_road(self, agent):
        # This layer holds the map as data: it writes
        # and edits no project file, applies nothing
        # the map describes, persists nothing - and
        # there is no Part VIII board yet. Holding a
        # book changes no live context assembly: a
        # ContextBuilder's built messages are the same
        # before and after a book is held.
        assert not hasattr(agent, "apply_project_memory_map")
        assert not hasattr(agent, "write_project_memory_map")
        assert not hasattr(agent, "edit_project_memory_map")
        assert not hasattr(agent, "persist_project_memory_map")
        assert not hasattr(agent, "project_memory_map_board")
        from mythic_agent.agents.context import ContextBuilder
        builder = ContextBuilder(max_tokens=4000)
        builder.add_system("You are the coder.")
        builder.add_turn("user", "Build the slice.")
        before = builder.build()
        agent.record_project_memory_map_book()
        assert builder.build() == before


class TestProjectMemoryMapTerminalSurface:
    def test_show_entry_section_and_panel(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/memorymap")
        assert "Project Memory Map (M-150)" in text
        _, _, text = _slash(agent, "/memorymap entry map-package")
        assert "map-package: The package" in text
        _, _, text = _slash(agent, "/memorymap section location")
        assert "map-package" in text
        assert "map-offices" not in text
        _, _, text = _slash(agent, "/memorymap panel")
        assert "Panel in Project memory map" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/memorymap [show|entry <entry-id>|"
                "section <section>|panel]") in text
        _, _, text = _slash(agent, "/memorymap dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/memorymap entry map-nope")
        assert "no entry in the book" in text


@pytest.fixture()
def map_handler(agent, monkeypatch):
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


def _map_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestProjectMemoryMapCommand:
    def test_show_is_default(self, map_handler, agent):
        map_handler._handle_memory_map("")
        assert "Project Memory Map (M-150)" in (
            _map_published_text(map_handler))

    def test_entry_section_and_panel(self, map_handler, agent):
        map_handler._handle_memory_map("entry map-package")
        assert "The package" in _map_published_text(map_handler)
        map_handler._handle_memory_map("section gotcha")
        text = _map_published_text(map_handler)
        assert "map-no-docker" in text
        map_handler._handle_memory_map("panel")
        assert "Panel in Project memory map" in _map_published_text(
            map_handler)

    def test_bad_grammar_is_published(self, map_handler, agent):
        map_handler._handle_memory_map("dance party")
        assert USAGE in _map_published_text(map_handler)


class TestChatScreenRoutingProjectMemoryMap:
    def test_memory_map_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/memorymap entry map-package", _FakeLog())
        assert calls == [("/memorymap", "entry map-package")]
