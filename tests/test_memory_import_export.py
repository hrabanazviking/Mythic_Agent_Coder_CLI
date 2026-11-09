"""M-164 Memory import/export - pure-layer tests.

TIER: integration

The pure layer is the memory package itself, held
as data: one project's memory map + ledger exported
as one portable file record - they ride with the
repo if the user wishes - carried with its
provenance whole (the project it packs, the session
it was exported from and the day, what rides in it -
the map entry ids and their sections, the ledger
candidate ids and their promotion states - who
exported it, and where it was read from), composed
by import from the shipped holdings it packs (the
project memory map, M-150, and the self-improving
ledger, M-155), each judged by its own layer's
validation, an import judged whole before anything
is held, a memory panel derived from the whole book
in settled order, a portability verdict derived for
the whole book - a partial packing is never smoothed
into a whole one - the shipped example book held in
a data file, and a loader that reads a book from any
file. Nothing here sends, posts, schedules, calls a
model, writes any project's files or writes any live
memory: holding a package records a packing, and
that is the whole road.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.project_memory_map import load_project_memory_map
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.self_improving_ledger import load_self_improving_ledger
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.memory_import_export import (
    MEMORY_IMPORT_EXPORT_RESOURCE,
    MEMORY_IMPORT_EXPORT_SCHEMA,
    MEMORY_IMPORT_EXPORT_SLICE,
    PLAIN_EXPLANATION,
    RIDE_KINDS,
    USAGE,
    MemoryExportBook,
    MemoryPackage,
    MemoryPackageRegistry,
    PackagePanel,
    PackagePanelRow,
    PortabilityVerdict,
    RideCount,
    book_record,
    build_book,
    build_package,
    build_panel,
    build_row,
    build_verdict,
    derive_panel,
    derive_verdict,
    format_memory_import_export_screen,
    format_package,
    format_packages,
    format_panel,
    format_verdict,
    inspect_package_source,
    load_memory_import_export,
    load_memory_import_export_file,
    normalize_ride_kind,
    package_from_ledger,
    package_from_memory_books,
    package_from_memory_map,
    package_record,
    package_refs,
    panel_plain_words,
    panel_record,
    parse_memoryxport_args,
    plain_words,
    total_candidates,
    total_map_entries,
    total_pieces,
    validate_book,
    validate_package,
    validate_panel,
    validate_row,
    validate_verdict,
    verdict_plain_words,
    verdict_record,
)

ROOT = Path(__file__).resolve().parents[1]

EXAMPLE_TITLE = "Memory import/export at the M-163 slice boundary"

BY = "Volmarr"
ON = "2026-11-09"


def _package(**overrides):
    fields = {
        "package_id": "package-test",
        "title": "the test project memory, packed for the road",
        "project": "test-project",
        "source_session": "session-test",
        "map_entry_ids": ["map-alpha", "map-beta"],
        "candidate_ids": ["candidate-alpha"],
        "map_sections": ["architecture", "location"],
        "ledger_states": ["candidate"],
        "exported_by": BY,
        "exported_on": ON,
        "source": "test source",
    }
    fields.update(overrides)
    return build_package(fields)


def _stored_package(package):
    stored = package.to_record()
    for key in ("type", "slice", "map_count",
                "candidate_count", "piece_count"):
        stored.pop(key)
    return stored


def _stored_panel(panel):
    stored = panel.to_record()
    stored.pop("type")
    stored.pop("slice")
    for row in stored["rows"]:
        row.pop("type")
        row.pop("slice")
    return stored


def _stored_verdict(verdict):
    stored = verdict.to_record()
    stored.pop("type")
    stored.pop("slice")
    return stored


def _book(packages=None, **overrides):
    fields = {
        "title": "A test memory export book",
        "packages": [_stored_package(item) for item in (
            packages if packages is not None else [_package()])],
    }
    fields.update(overrides)
    return build_book(fields)


def _shipped_raw():
    path = ROOT / "mythic_agent" / "data" / "memory_import_export.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_constants_and_usage():
    assert MEMORY_IMPORT_EXPORT_SLICE == "M-164"
    assert MEMORY_IMPORT_EXPORT_SCHEMA == "mythic.memory_import_export/1"
    assert MEMORY_IMPORT_EXPORT_RESOURCE == "memory_import_export.yaml"
    assert RIDE_KINDS == ("map", "ledger")
    assert "memory map + ledger" in PLAIN_EXPLANATION
    assert "portable" in PLAIN_EXPLANATION
    assert "judged whole" in PLAIN_EXPLANATION
    assert "writes no live" in PLAIN_EXPLANATION
    assert "sends nothing" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /memoryxport")
    assert "package <package-id>" in USAGE


def test_roadmap_boundary_is_derived_from_the_shipped_roadmap():
    road = load_roadmap()
    ids = [item.id for item in road.slices]
    assert "M-164" in ids
    mine = road.slices[ids.index("M-164")]
    assert mine.title == "Memory import/export"
    assert mine.part == 7
    assert "memory map + ledger" in mine.summary
    assert "portable" in mine.summary
    assert "ride with the repo" in mine.summary
    for earlier in road.slices[:ids.index("M-164")]:
        assert earlier.status == "done", earlier.id


def test_shipped_example_shape():
    book = load_memory_import_export()
    assert isinstance(book, MemoryExportBook)
    assert book.title == EXAMPLE_TITLE
    assert book.package_ids() == (
        "package-coder-memory", "package-samtal-memory")
    assert book.total_packages == 2
    first = book.packages[0]
    assert first.title == (
        "the mythic-agent-coder memory, packed to ride with the repo")
    assert first.project == "mythic-agent-coder"
    assert first.source_session == "session-m163-handoff"
    assert first.map_count == 9
    assert first.candidate_count == 3
    assert first.piece_count == 12
    assert first.map_sections == (
        "architecture", "decision", "gotcha", "location")
    assert first.ledger_states == ("candidate", "promoted", "declined")
    assert first.exported_by == "Volmarr"
    assert first.exported_on == "2026-11-09"
    assert len(book.panels) == 1


def test_shipped_panel_is_pinned_and_derived():
    book = load_memory_import_export()
    panel = book.panel_for("panel-m163-boundary")
    derived = derive_panel(book)
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert [row.package_id for row in panel.rows] == [
        "package-coder-memory", "package-samtal-memory"]
    assert panel.total_packages == 2
    assert panel.total_map_entries == 11
    assert panel.total_candidates == 3
    assert panel.total_pieces == 14


def test_shipped_verdict_names_the_partial_packing():
    book = load_memory_import_export()
    verdict = derive_verdict(book)
    assert verdict.verdict == "partially-portable"
    assert verdict.total_complete == 1
    assert verdict.total_map_only == 1
    assert verdict.total_ledger_only == 0
    assert verdict.distinct_projects == 2
    assert total_map_entries(book) == 11
    assert total_candidates(book) == 3
    assert total_pieces(book) == 14
    pieces = [piece for package in book.packages
              for piece in tuple(package.map_entry_ids)
              + tuple(package.candidate_ids)]
    assert len(pieces) == len(set(pieces))


def test_normalizers_and_aliases():
    assert normalize_ride_kind("Map") == "map"
    assert normalize_ride_kind("memory-map") == "map"
    assert normalize_ride_kind("MEMORY_MAP") == "map"
    assert normalize_ride_kind("Ledger") == "ledger"
    assert normalize_ride_kind("self-improving-ledger") == "ledger"
    with pytest.raises(ValueError):
        normalize_ride_kind("scroll")
    with pytest.raises(ValueError):
        _package(exported_on="09/11/2026")
    with pytest.raises(ValueError):
        _package(source_session="bad session")
    # Sections and states are held in their own
    # layers' settled orders, however they arrive.
    packed = _package(
        map_sections=["location", "architecture"],
        ledger_states=["candidate"])
    assert packed.map_sections == ("architecture", "location")


def test_package_validation_and_alias_spellings():
    package = _package()
    assert isinstance(package, MemoryPackage)
    assert package.piece_count == 3
    assert package.counts() == {"map": 2, "ledger": 1}
    assert package.rides_both is True
    aliased = build_package({
        "name": "the aliased package", "project": "other-project",
        "session": "session-alias",
        "map_entries": ["map-gamma"], "candidates": [],
        "sections": ["gotcha"], "states": [],
        "exporter": "Volmarr", "day": "2026-11-09",
        "source": "the alias test"})
    assert aliased.title == "the aliased package"
    assert aliased.source_session == "session-alias"
    assert aliased.map_entry_ids == ("map-gamma",)
    assert aliased.candidate_ids == ()
    assert aliased.ledger_states == ()
    with pytest.raises(ValueError):
        build_package({"title": "the bare packing"})
    with pytest.raises(ValueError):
        _package(exported_on="2026-13-01")


def test_package_refuses_missing_provenance():
    fields = _stored_package(_package())
    fields.pop("exported_by")
    with pytest.raises(ValueError, match="missing its"):
        build_package(fields)
    fields = _stored_package(_package())
    fields.pop("source")
    with pytest.raises(ValueError, match="missing its"):
        build_package(fields)
    fields = _stored_package(_package())
    fields.pop("project")
    with pytest.raises(ValueError, match="missing its"):
        build_package(fields)
    fields = _stored_package(_package())
    fields["bogus"] = "nope"
    with pytest.raises(ValueError, match="unknown package keys"):
        build_package(fields)


def test_package_refuses_content_problems():
    with pytest.raises(ValueError, match="at least one piece"):
        _package(map_entry_ids=[], candidate_ids=[],
                 map_sections=[], ledger_states=[])
    with pytest.raises(ValueError, match="twice"):
        _package(map_entry_ids=["map-alpha", "map-alpha"])
    with pytest.raises(ValueError, match="rides once"):
        _package(candidate_ids=["map-alpha"])
    with pytest.raises(ValueError, match="sections ride exactly"):
        _package(map_sections=[])
    with pytest.raises(ValueError, match="sections ride exactly"):
        _package(map_entry_ids=[], map_sections=["gotcha"],
                 candidate_ids=["candidate-alpha"])
    with pytest.raises(ValueError, match="states ride exactly"):
        _package(ledger_states=[])
    with pytest.raises(ValueError, match="states ride exactly"):
        _package(candidate_ids=[], ledger_states=["promoted"],
                 map_entry_ids=["map-alpha"])
    fields = _stored_package(_package())
    fields.pop("map_entry_ids")
    with pytest.raises(ValueError, match="missing its map entries"):
        build_package(fields)


def test_book_refuses_duplicates_and_double_packing():
    with pytest.raises(ValueError, match="already exists"):
        _book([_package(), _package(title="another title")])
    # One package per project and session: a second
    # package packing a held project from a held
    # session refuses under any id.
    with pytest.raises(ValueError, match="stands once"):
        _book([_package(), _package(
            package_id="package-copy", title="the copy package",
            map_entry_ids=["map-gamma"], candidate_ids=[],
            map_sections=["gotcha"], ledger_states=[],
        )])
    # A piece is packed once: one piece in two
    # packages refuses, naming both sessions.
    with pytest.raises(ValueError, match="packed twice"):
        _book([_package(), _package(
            package_id="package-copy", project="other-project",
            source_session="session-copy",
            map_entry_ids=["map-alpha"], candidate_ids=[],
            map_sections=["architecture"], ledger_states=[],
        )])
    # Distinct projects with distinct pieces stand
    # together in one book.
    book = _book([_package(), _package(
        package_id="package-second", project="second-project",
        source_session="session-second",
        map_entry_ids=[], candidate_ids=["candidate-beta"],
        map_sections=[], ledger_states=["promoted"],
    )])
    assert book.total_packages == 2


def test_package_for_project_in_book():
    book = load_memory_import_export()
    package = book.package_for_project("samtal")
    assert package.package_id == "package-samtal-memory"
    assert isinstance(
        book.package_for("package-coder-memory"), MemoryPackage)
    with pytest.raises(KeyError):
        book.package_for_project("nope-project")
    with pytest.raises(KeyError):
        book.package_for("package-nope")


def test_composition_from_memory_map():
    map_book = load_project_memory_map()
    package = package_from_memory_map(
        map_book, project="mythic-agent-coder",
        source_session="session-m150-map",
        exported_by=BY, exported_on=ON)
    assert package.map_entry_ids == map_book.entry_ids()
    assert package.map_sections == (
        "architecture", "decision", "gotcha", "location")
    assert package.candidate_ids == ()
    assert package.title == (
        "memory of mythic-agent-coder, packed from its map")
    assert validate_package(package, map_book) == package
    blob = str(package.to_record())
    for entry in map_book.entries:
        assert entry.title not in blob
        assert entry.detail not in blob
        assert entry.ref not in blob
    with pytest.raises(ValueError, match="project"):
        package_from_memory_map(
            map_book, project=None,
            source_session="session-x",
            exported_by=BY, exported_on=ON)


def test_composition_from_ledger():
    ledger_book = load_self_improving_ledger()
    package = package_from_ledger(
        ledger_book, project="mythic-agent-coder",
        source_session="session-m155-ledger",
        exported_by=BY, exported_on=ON)
    assert package.candidate_ids == ledger_book.candidate_ids()
    # The standings are the ledger's own: one
    # promoted, one still a candidate, one declined.
    assert package.ledger_states == ("candidate", "promoted", "declined")
    assert package.map_entry_ids == ()
    assert validate_package(package, None, ledger_book) == package
    blob = str(package.to_record())
    for candidate in ledger_book.candidates:
        assert candidate.title not in blob
        assert candidate.detail not in blob
        assert candidate.context not in blob
    with pytest.raises(ValueError, match="session"):
        package_from_ledger(
            ledger_book, project="mythic-agent-coder",
            source_session=None, exported_by=BY, exported_on=ON)


def test_composition_from_memory_books():
    map_book = load_project_memory_map()
    ledger_book = load_self_improving_ledger()
    package = package_from_memory_books(
        map_book, ledger_book, project="mythic-agent-coder",
        source_session="session-m163-handoff",
        exported_by=BY, exported_on=ON)
    assert package.map_count == 9
    assert package.candidate_count == 3
    assert package.piece_count == 12
    assert package.rides_both is True
    # The shipped example's first package is exactly
    # this composition, provenance and all.
    shipped = load_memory_import_export().packages[0]
    assert package.map_entry_ids == shipped.map_entry_ids
    assert package.candidate_ids == shipped.candidate_ids
    assert package.map_sections == shipped.map_sections
    assert package.ledger_states == shipped.ledger_states
    with pytest.raises(ValueError, match="exported"):
        package_from_memory_books(
            map_book, ledger_book, project="mythic-agent-coder",
            source_session="session-x", exported_by=None,
            exported_on=ON)


def test_composition_refusals_name_the_missing_provenance():
    map_book = load_project_memory_map()
    with pytest.raises(ValueError, match="project"):
        package_from_memory_books(
            map_book, load_self_improving_ledger(), project=None,
            source_session="session-x", exported_by=BY, exported_on=ON)
    with pytest.raises(ValueError, match="session"):
        package_from_memory_map(
            map_book, project="p", source_session=None,
            exported_by=BY, exported_on=ON)
    with pytest.raises(ValueError, match="exported"):
        package_from_memory_map(
            map_book, project="p", source_session="session-x",
            exported_by=BY, exported_on=None)


def test_inspect_package_source():
    map_book = load_project_memory_map()
    seen = inspect_package_source(map_book)
    assert seen == {"map_count": 9, "candidate_count": None}
    ledger_book = load_self_improving_ledger()
    seen = inspect_package_source(ledger_book)
    assert seen == {"map_count": None, "candidate_count": 3}
    seen = inspect_package_source(map_book.entries[0])
    assert seen == {"map_count": 1, "candidate_count": None}
    seen = inspect_package_source(ledger_book.candidates[0])
    assert seen == {"map_count": None, "candidate_count": 1}
    seen = inspect_package_source(_package())
    assert seen == {"project": "test-project", "map_count": 2,
                    "candidate_count": 1}
    with pytest.raises(ValueError, match="no shipped layer owns"):
        inspect_package_source(42)


def test_validate_package_judged_against_sources():
    map_book = load_project_memory_map()
    ledger_book = load_self_improving_ledger()
    package = package_from_memory_books(
        map_book, ledger_book, project="mythic-agent-coder",
        source_session="session-x", exported_by=BY, exported_on=ON)
    assert validate_package(package, map_book, ledger_book) == package
    # A package naming a piece its map does not hold
    # refuses against that map - judged whole.
    tampered = _package(
        map_entry_ids=["map-alpha"], candidate_ids=[],
        map_sections=["architecture"], ledger_states=[])
    with pytest.raises(ValueError, match="disagree with the memory map"):
        validate_package(tampered, map_book)
    with pytest.raises(ValueError, match="disagree with the ledger"):
        validate_package(tampered, None, ledger_book)
    # A foreign record refuses by name before any
    # judging: unknown keys never ride.
    foreign = _stored_package(_package())
    foreign["payload"] = "run me"
    with pytest.raises(ValueError, match="unknown package keys"):
        validate_package(foreign)


def test_panel_derivation_and_order():
    book = _book([
        _package(package_id="package-b", title="b package",
                 project="beta-project", source_session="session-b",
                 map_entry_ids=["map-b1"], candidate_ids=[],
                 map_sections=["gotcha"], ledger_states=[]),
        _package(package_id="package-a", title="a package",
                 project="alpha-project", source_session="session-a",
                 map_entry_ids=["map-a1", "map-a2"],
                 candidate_ids=["candidate-a1"],
                 map_sections=["architecture"],
                 ledger_states=["promoted"]),
        _package(package_id="package-c", title="the c package",
                 project="alpha-project", source_session="session-c",
                 map_entry_ids=[], candidate_ids=["candidate-c1"],
                 map_sections=[], ledger_states=["candidate"]),
    ])
    panel = derive_panel(book)
    assert isinstance(panel, PackagePanel)
    # Panel order: project, then day, then title,
    # then package id.
    assert [r.package_id for r in panel.rows] == [
        "package-a", "package-c", "package-b"]
    assert panel.total_packages == 3
    assert panel.total_map_entries == 3
    assert panel.total_candidates == 2
    assert panel.total_pieces == 5
    counts = {c.kind: c for c in panel.ride_counts}
    assert counts["map"].items == 3
    assert counts["ledger"].items == 2
    assert isinstance(counts["map"], RideCount)
    assert panel.row_for("package-c").piece_count == 1
    with pytest.raises(KeyError):
        panel.row_for("package-nope")


def test_panel_refuses_disagreement_and_bad_rows():
    book = load_memory_import_export()
    panel = derive_panel(book)
    stored = _stored_panel(panel)
    assert validate_panel(stored, book) == panel
    bad = _stored_panel(panel)
    bad["total_packages"] = 1
    with pytest.raises(ValueError):
        validate_panel(bad, book)
    bad = _stored_panel(panel)
    bad["account"] = ["A different account."]
    with pytest.raises(ValueError, match="disagrees"):
        validate_panel(bad, book)
    good_row = build_row(_stored_panel(panel)["rows"][0])
    assert isinstance(good_row, PackagePanelRow)
    assert validate_row(good_row, book.packages[0]) == good_row
    bad_row = _stored_panel(panel)["rows"][0]
    bad_row["project"] = "elsewhere"
    with pytest.raises(ValueError, match="disagrees"):
        validate_row(bad_row, book.packages[0])


def test_verdict_derivation_and_validation():
    both = _book([_package(), _package(
        package_id="package-second", project="second-project",
        source_session="session-second",
        map_entry_ids=["map-gamma"], candidate_ids=["candidate-beta"],
        map_sections=["decision"], ledger_states=["promoted"])])
    verdict = derive_verdict(both)
    assert isinstance(verdict, PortabilityVerdict)
    assert verdict.verdict == "fully-portable"
    assert verdict.total_complete == 2
    assert verdict.distinct_projects == 2
    assert validate_verdict(_stored_verdict(verdict), both) == verdict
    assert build_verdict(_stored_verdict(verdict)) == verdict
    map_only = derive_verdict(_book([_package(
        candidate_ids=[], ledger_states=[])]))
    assert map_only.verdict == "map-only"
    ledger_only = derive_verdict(_book([_package(
        map_entry_ids=[], map_sections=[],
        candidate_ids=["candidate-alpha"]) ]))
    assert ledger_only.verdict == "ledger-only"
    partial = derive_verdict(load_memory_import_export())
    assert partial.verdict == "partially-portable"
    with pytest.raises(ValueError, match="disagrees"):
        validate_verdict(_stored_verdict(map_only), both)
    # A verdict whose word is not its own counts'
    # word refuses at construction.
    with pytest.raises(ValueError, match="verdict"):
        PortabilityVerdict(
            total_packages=1, total_map_entries=2, total_candidates=1,
            total_pieces=3, total_complete=1, total_map_only=0,
            total_ledger_only=0, distinct_projects=1,
            verdict="map-only")
    with pytest.raises(ValueError, match="verdict"):
        PortabilityVerdict(
            total_packages=2, total_map_entries=2, total_candidates=0,
            total_pieces=2, total_complete=0, total_map_only=2,
            total_ledger_only=0, distinct_projects=1,
            verdict="fully-portable")


def test_book_validation_and_loader_roads(tmp_path):
    raw = _shipped_raw()
    assert validate_book(raw).title == EXAMPLE_TITLE
    assert build_book(raw).package_ids()[0] == "package-coder-memory"
    bad = dict(raw)
    bad["schema"] = "mythic.other/1"
    with pytest.raises(ValidationError):
        validate_book(bad)
    path = tmp_path / "memory_import_export.yaml"
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    loaded = load_memory_import_export_file(path)
    assert loaded.title == EXAMPLE_TITLE
    with pytest.raises(FileNotFoundError):
        load_memory_import_export_file(tmp_path / "nope.yaml")
    assert _shipped_raw()["schema"] == MEMORY_IMPORT_EXPORT_SCHEMA


def test_registry_holds_packages_one_by_one():
    registry = MemoryPackageRegistry()
    held = registry.register_package(_package(package_id=None))
    assert held.package_id == "package-1"
    assert registry.latest_package() == held
    assert registry.get_package("package-1") == held
    assert registry.package_for_project("test-project") == held
    with pytest.raises(ValueError, match="already exists"):
        registry.register_package(held)
    with pytest.raises(ValueError, match="stands once"):
        registry.register_package(_package(
            package_id="package-copy",
            map_entry_ids=["map-gamma"], candidate_ids=[],
            map_sections=["gotcha"], ledger_states=[]))
    with pytest.raises(ValueError, match="packed twice"):
        registry.register_package(_package(
            package_id="package-copy", project="other-project",
            source_session="session-copy", candidate_ids=[],
            ledger_states=[]))
    with pytest.raises(ValueError, match="no memory export book is held"):
        registry.book()
    assert registry.panel().total_packages == 1
    assert registry.verdict().verdict == "fully-portable"
    with pytest.raises(KeyError):
        registry.get_package("package-nope")


def test_registry_register_book_and_title_law():
    registry = MemoryPackageRegistry()
    book = _book()
    held_book = registry.register_book(book)
    assert held_book.title == "A test memory export book"
    assert registry.list_packages()[0].package_id == "package-test"
    with pytest.raises(ValueError):
        registry.register_book(book)
    other = _book([_package(
        package_id="package-z", project="z-project",
        source_session="session-z",
        map_entry_ids=["map-z1"], candidate_ids=[],
        map_sections=["location"], ledger_states=[])],
        title="Another title")
    with pytest.raises(ValueError, match="different title"):
        registry.register_book(other)
    fresh = MemoryPackageRegistry(load_memory_import_export())
    assert fresh.book().total_packages == 2


def test_registry_book_judged_whole_before_holding():
    # A book whose second package breaks the book's
    # laws holds nothing at all - the import is
    # judged whole before anything is held.
    registry = MemoryPackageRegistry()
    registry.register_package(_package())
    clashing = _book([_package(
        package_id="package-new", project="new-project",
        source_session="session-new",
        map_entry_ids=["map-new"], candidate_ids=[],
        map_sections=["gotcha"], ledger_states=[]), _package(
        package_id="package-clash", project="clash-project",
        source_session="session-clash",
        map_entry_ids=["map-alpha"], candidate_ids=[],
        map_sections=["architecture"], ledger_states=[])],
        title="A clashing book")
    with pytest.raises(ValueError, match="packed twice"):
        registry.register_book(clashing)
    assert [p.package_id for p in registry.list_packages()] == [
        "package-test"]


def test_news_records_and_plain_words():
    package = _package()
    news = package_record(package)
    assert news["type"] == "memory_import_export_package"
    assert news["news"] is True
    assert "test-project" in news["headline"]
    book = load_memory_import_export()
    panel_news = panel_record(derive_panel(book), book)
    assert panel_news["type"] == "memory_import_export_panel"
    assert "2 packages" in panel_news["headline"]
    verdict_news = verdict_record(derive_verdict(book), book)
    assert verdict_news["type"] == "memory_import_export_verdict"
    assert "partially-portable" in verdict_news["headline"]
    whole = book_record(book)
    assert whole["type"] == "memory_import_export_book"
    assert whole["package_count"] == 2
    words = plain_words(book.packages[0])
    assert "mythic-agent-coder" in words
    assert "Volmarr" in words
    panel_words = panel_plain_words(book)
    assert "package-samtal-memory" in panel_words
    assert "derived, never stored loose" in panel_words
    verdict_words = verdict_plain_words(book)
    assert "partially-portable" in verdict_words
    assert "ride both" in verdict_words


def test_refs_and_totals_surface():
    book = load_memory_import_export()
    refs = package_refs(book)
    assert refs[0] == ("mythic-agent-coder", "session-m163-handoff")
    assert ("samtal", "session-samtal-gatekeeper") in refs
    assert len(refs) == 2
    assert validate_package(_stored_package(_package())) == _package()


def test_formatters_and_screen():
    book = load_memory_import_export()
    block = format_package(book.packages[0])
    assert "map-package" in block
    assert "writes no live memory" in block
    listing = format_packages(book)
    assert "package-coder-memory" in listing
    only = format_packages(book, "samtal")
    assert "package-samtal-memory" in only
    assert "package-coder-memory" not in only
    panel_text = format_panel(book)
    assert "Memory panel in" in panel_text
    assert "derived, never stored loose" in panel_text
    verdict_text = format_verdict(book)
    assert "partially-portable" in verdict_text
    screen = format_memory_import_export_screen(book)
    assert "Memory Import/Export (M-164)" in screen
    assert USAGE in screen
    default_screen = format_memory_import_export_screen()
    assert "package-coder-memory" in default_screen


def test_parse_memoryxport_args():
    assert parse_memoryxport_args("") == ("show", None)
    assert parse_memoryxport_args("show") == ("show", None)
    assert parse_memoryxport_args("list") == ("show", None)
    assert parse_memoryxport_args(
        "package package-coder-memory") == (
        "package", "package-coder-memory")
    assert parse_memoryxport_args(
        "project mythic-agent-coder") == (
        "project", "mythic-agent-coder")
    assert parse_memoryxport_args("panel") == ("panel", None)
    assert parse_memoryxport_args("verdict") == ("verdict", None)
    with pytest.raises(ValueError, match="Usage"):
        parse_memoryxport_args("dance party")
    with pytest.raises(ValueError):
        parse_memoryxport_args("project bad project")
    with pytest.raises(ValueError):
        parse_memoryxport_args(42)
