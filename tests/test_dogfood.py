"""M-141 The Mythic Coder building itself - pure-layer tests.

TIER: integration

The pure layer is the dogfood as data: a dogfood
book of build records (the member who built, the
slice built and a title - a record's part derived
from the shipped roadmap, composed by import from
the roadmap layer, never stored on the record), the
shipped example dogfood book held in a data file, a
loader that reads a dogfood book from any file,
per-part reports whose counts and account are
derived from the build records they report, the
coordinator's ledger whose rows and account are
derived from the whole book, records shaped as
session news, and a registry. Nothing here builds
a slice live, runs a crew, calls a model or spawns
an agent: a stored report disagreeing with the
report derived from its own records is refused, and
a stored ledger disagreeing with the ledger derived
from its book is refused.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.crew_members import load_casting
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.dogfood import (
    COORDINATOR_KEEPER,
    DOGFOOD_RESOURCE,
    DOGFOOD_SCHEMA,
    DOGFOOD_SLICE,
    PLAIN_EXPLANATION,
    USAGE,
    CoordinatorLedger,
    DogfoodBook,
    DogfoodEntry,
    DogfoodRegistry,
    DogfoodReport,
    book_record,
    build_book,
    build_entry,
    build_ledger,
    build_report,
    derive_ledger,
    derive_report,
    entry_record,
    format_dogfood_screen,
    format_entries,
    format_entry,
    format_ledger,
    format_report,
    ledger_plain_words,
    ledger_record,
    load_dogfood,
    load_dogfood_file,
    parse_dogfood_args,
    plain_words,
    report_plain_words,
    report_record,
    validate_book,
    validate_entry,
    validate_ledger,
    validate_report,
)

ROOT = Path(__file__).resolve().parents[1]


def _entry(**kwargs):
    kwargs.setdefault("entry_id", "entry-m139-forge")
    kwargs.setdefault("member", "forge_worker")
    kwargs.setdefault("slice_id", "M-139")
    kwargs.setdefault("title", "Failure fostering")
    return DogfoodEntry(**kwargs)


def _entries():
    return [
        _entry(),
        DogfoodEntry(
            entry_id="entry-m140-forge", member="forge_worker",
            slice_id="M-140", title="Cost court"),
        DogfoodEntry(
            entry_id="entry-m140-auditor", member="auditor",
            slice_id="M-140", title="Cost court"),
        DogfoodEntry(
            entry_id="entry-m121-architect", member="architect",
            slice_id="M-121", title="Agents as files"),
    ]


def test_constants_and_usage():
    assert DOGFOOD_SLICE == "M-141"
    assert DOGFOOD_SCHEMA == "mythic.dogfood/1"
    assert DOGFOOD_RESOURCE == "dogfood.yaml"
    assert COORDINATOR_KEEPER == "coordinator"
    assert "coordinator" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /dogfood")
    assert "/dogfood part <part-number>" in USAGE
    assert "/dogfood ledger" in USAGE


def test_shipped_example_shape():
    book = load_dogfood()
    assert book.title == "Dogfood book at the M-140 slice boundary"
    assert book.entry_ids() == (
        "entry-m120-forge", "entry-m121-architect",
        "entry-m138-scribe", "entry-m139-forge",
        "entry-m140-forge", "entry-m140-auditor")
    assert [e.part for e in book.entries] == [5, 6, 6, 6, 6, 6]
    ledger = book.ledger_for("ledger-m140-boundary")
    assert ledger.keeper == COORDINATOR_KEEPER
    assert [row.part for row in ledger.rows] == [5, 6]
    assert (ledger.total_builds, ledger.total_slices,
            ledger.total_parts) == (6, 5, 2)
    assert ledger.account == (
        "The coordinator keeps this ledger: 2 part row(s) "
        "across 2 part(s).",
        "Total: 6 build(s) across 5 slice(s).",
        "The standing dogfood: each part of this road is "
        "built by the crew it improves.")
    first = derive_report(book.entries, 5)
    assert first.account == (
        "Part 5 (Autonomy & Safety) was built by the crew "
        "it improves in 1 build(s) across 1 slice(s).",
        "Builders: forge_worker.",
        "Every build stands under the coordinator's "
        "discipline.")


def test_example_members_are_shipped_casting_members():
    casting_ids = {m.member_id for m in load_casting().members}
    book = load_dogfood()
    assert {e.member for e in book.entries} <= casting_ids
    assert COORDINATOR_KEEPER not in casting_ids


def test_example_parts_are_the_roadmaps_own_parts():
    road = load_roadmap()
    book = load_dogfood()
    for entry in book.entries:
        assert entry.part == road.slice(entry.slice_id).part
        assert entry.part_title == road.part(entry.part).title
    with pytest.raises(ValueError):
        build_entry({"member": "forge_worker", "slice_id": "M-140",
                     "title": "Cost court", "part": 6})


def test_entry_validation_with_alias_spellings():
    entry = validate_entry({
        "id": "entry-m139-forge", "member_id": "forge_worker",
        "slice": "M-139", "name": "Failure fostering"})
    assert entry == _entry()
    assert build_entry(member="auditor", slice_id="M-140",
                       title="Cost court") == DogfoodEntry(
        member="auditor", slice_id="M-140", title="Cost court")
    with pytest.raises(ValueError):
        validate_entry({"member": "forge_worker",
                        "member_id": "auditor",
                        "slice_id": "M-139", "title": "Failure fostering"})


def test_entry_refusals():
    with pytest.raises(ValueError):
        build_entry({"member": "forge_worker", "slice_id": "M-139",
                     "title": "Failure fostering", "part": 6})
    with pytest.raises(ValueError):
        build_entry({"member": "forge_worker", "slice_id": "M-139",
                     "title": "Failure fostering", "bogus": 1})
    with pytest.raises(ValueError):
        _entry(member="forge worker")
    with pytest.raises(ValueError):
        _entry(slice_id="139")
    with pytest.raises(ValueError):
        _entry(slice_id="M-999")
    with pytest.raises(ValueError):
        build_entry({"member": "forge_worker", "slice_id": "M-139"})
    with pytest.raises(ValueError):
        validate_entry("not a mapping")


def test_report_derivation_is_deterministic():
    entries = _entries()
    report = derive_report(entries, 6)
    assert report.entry_ids == (
        "entry-m139-forge", "entry-m140-forge",
        "entry-m140-auditor", "entry-m121-architect")
    assert report.builds == 4
    assert report.slices == ("M-139", "M-140", "M-121")
    assert report.members == ("forge_worker", "auditor", "architect")
    assert report.account[0] == (
        "Part 6 (The Crew) was built by the crew it improves "
        "in 4 build(s) across 3 slice(s).")
    assert derive_report(entries, 6) == report
    book = DogfoodBook(title="B", entries=entries)
    assert derive_report(book, 6) == report
    with pytest.raises(KeyError):
        derive_report(entries, 5)


def test_stored_reports_judged_against_their_records():
    entries = _entries()
    derived = derive_report(entries, 6)
    stored = {
        "part": 6, "entry_ids": list(derived.entry_ids),
        "builds": derived.builds, "slices": list(derived.slices),
        "members": list(derived.members),
        "account": list(derived.account)}
    assert validate_report(stored, entries) == derived
    assert build_report(stored, entries) == derived
    tampered = dict(stored, builds=9, entry_ids=list(derived.entry_ids) + ["x-1", "x-2", "x-3", "x-4", "x-5"])
    with pytest.raises(ValueError):
        validate_report(tampered, entries)
    with pytest.raises(ValueError):
        validate_report(dict(stored, account=["A different account."]), entries)
    no_account = {k: v for k, v in stored.items() if k != "account"}
    with pytest.raises(ValueError):
        validate_report(no_account, entries)
    with pytest.raises(ValueError):
        validate_report(dict(stored, bogus=1), entries)


def test_ledger_derivation_is_deterministic():
    entries = _entries() + [DogfoodEntry(
        entry_id="entry-m120-forge", member="forge_worker",
        slice_id="M-120", title="Part V gate")]
    ledger = derive_ledger(entries)
    assert ledger.keeper == COORDINATOR_KEEPER
    assert [row.part for row in ledger.rows] == [6, 5]
    assert (ledger.total_builds, ledger.total_slices,
            ledger.total_parts) == (5, 4, 2)
    assert derive_ledger(entries) == ledger
    with pytest.raises(ValueError):
        derive_ledger([])
    with pytest.raises(KeyError):
        ledger.row_for(7)


def test_stored_ledgers_judged_against_their_book():
    book = load_dogfood()
    derived = derive_ledger(book.entries)
    stored = {
        "keeper": "coordinator",
        "rows": [{"part": row.part,
                  "entry_ids": list(row.entry_ids),
                  "builds": row.builds,
                  "slices": list(row.slices),
                  "members": list(row.members),
                  "account": list(row.account)} for row in derived.rows],
        "total_builds": derived.total_builds,
        "total_slices": derived.total_slices,
        "total_parts": derived.total_parts,
        "account": list(derived.account)}
    assert validate_ledger(stored, book.entries) == derived
    assert build_ledger(stored, book.entries) == derived
    with pytest.raises(ValueError):
        validate_ledger(dict(stored, total_builds=99), book.entries)
    with pytest.raises(ValueError):
        validate_ledger(dict(stored, keeper="scribe"), book.entries)
    no_account = {k: v for k, v in stored.items() if k != "account"}
    with pytest.raises(ValueError):
        validate_ledger(no_account, book.entries)
    with pytest.raises(ValueError):
        validate_ledger(dict(stored, bogus=1), book.entries)


def test_book_validation_and_views():
    book = build_book(load_dogfood())
    assert book.entry_for("entry-m140-auditor").member == "auditor"
    assert [e.entry_id for e in book.entries_for("forge_worker")] == [
        "entry-m120-forge", "entry-m139-forge", "entry-m140-forge"]
    assert [e.entry_id for e in book.entries_on("M-140")] == [
        "entry-m140-forge", "entry-m140-auditor"]
    assert len(book.entries_in(6)) == 5
    assert len(book.entries_in(5)) == 1
    with pytest.raises(KeyError):
        book.entry_for("entry-nope")
    with pytest.raises(KeyError):
        book.ledger_for("ledger-nope")
    data = yaml.safe_load(
        (ROOT / "mythic_agent" / "data" / "dogfood.yaml").read_text(
            encoding="utf-8"))
    assert validate_book(data).title == book.title


def test_book_refusals():
    data = yaml.safe_load(
        (ROOT / "mythic_agent" / "data" / "dogfood.yaml").read_text(
            encoding="utf-8"))
    dup = dict(data, entries=data["entries"] + [data["entries"][0]])
    with pytest.raises(ValidationError):
        validate_book(dup)
    bad_ledger = yaml.safe_load(yaml.safe_dump(data))
    bad_ledger["ledgers"][0]["total_builds"] = 99
    with pytest.raises(ValidationError):
        validate_book(bad_ledger)
    with pytest.raises(ValidationError):
        validate_book(dict(data, schema="mythic.other/1"))
    with pytest.raises(ValidationError):
        validate_book(dict(data, bogus=1))
    no_entries = {k: v for k, v in data.items() if k != "entries"}
    with pytest.raises(ValidationError):
        validate_book(no_entries)
    with pytest.raises(ValidationError):
        validate_book("not a mapping")
    with pytest.raises(ValidationError):
        validate_book(data, require_example=True) if False else validate_book(
            dict(data, guide={"title": "Some other book"}),
            require_example=True)


def test_file_loader_round_trip(tmp_path):
    text = (ROOT / "mythic_agent" / "data" / "dogfood.yaml").read_text(
        encoding="utf-8")
    target = tmp_path / "my-dogfood.yaml"
    target.write_text(text, encoding="utf-8")
    book = load_dogfood_file(target)
    assert book.entry_ids() == load_dogfood().entry_ids()
    with pytest.raises(FileNotFoundError):
        load_dogfood_file(tmp_path / "missing.yaml")
    bad = tmp_path / "bad.yaml"
    bad.write_text("schema: mythic.dogfood/1\nentries: 42\n",
                   encoding="utf-8")
    with pytest.raises(ValidationError):
        load_dogfood_file(bad)


def test_registry_holds_records_and_derives():
    registry = DogfoodRegistry()
    held = registry.register_entry(_entry())
    assert held.entry_id == "entry-m139-forge"
    registry.register_entry(DogfoodEntry(
        entry_id="entry-m120-forge", member="forge_worker",
        slice_id="M-120", title="Part V gate"))
    assert [e.entry_id for e in registry.list_entries()] == [
        "entry-m139-forge", "entry-m120-forge"]
    book = registry.book() if registry._title else None
    assert book is None
    registry2 = DogfoodRegistry(load_dogfood())
    assert registry2.book().title == load_dogfood().title
    assert registry2.report_for(6).builds == 5
    assert registry2.ledger().total_builds == 6
    assert registry2.get_entry("entry-m138-scribe").member == "scribe"


def test_registry_auto_ids_and_refusals():
    registry = DogfoodRegistry()
    first = registry.register_entry(DogfoodEntry(
        member="forge_worker", slice_id="M-139",
        title="Failure fostering"))
    second = registry.register_entry(DogfoodEntry(
        member="auditor", slice_id="M-140", title="Cost court"))
    assert (first.entry_id, second.entry_id) == ("dogfood-1", "dogfood-2")
    with pytest.raises(ValueError):
        registry.register_entry(first)
    with pytest.raises(KeyError):
        registry.get_entry("entry-nope")
    registry2 = DogfoodRegistry(load_dogfood())
    other = DogfoodBook(title="Another book", entries=_entries())
    with pytest.raises(ValueError):
        registry2.register_book(other)


def test_session_news_records():
    book = load_dogfood()
    entry = book.entry_for("entry-m139-forge")
    record = entry_record(entry)
    assert record["type"] == "dogfood_entry"
    assert record["slice"] == "M-141"
    assert record["news"] is True
    assert record["part"] == 6
    assert "forge_worker built M-139" in record["headline"]
    report = derive_report(book.entries, 6)
    rrecord = report_record(report, book.entries)
    assert rrecord["type"] == "dogfood_report"
    assert rrecord["news"] is True
    ledger = book.ledger_for("ledger-m140-boundary")
    lrecord = ledger_record(ledger, book.entries)
    assert lrecord["type"] == "dogfood_ledger"
    assert lrecord["keeper"] == "coordinator"
    brecord = book_record(book)
    assert brecord["type"] == "dogfood_book"
    assert brecord["entry_count"] == 6
    assert brecord["ledger_count"] == 1


def test_plain_words():
    book = load_dogfood()
    entry = book.entry_for("entry-m121-architect")
    assert plain_words(entry) == (
        "architect built M-121 (Part 6, The Crew): Agents as files.")
    words = report_plain_words(book)
    assert "Part 5 (Autonomy & Safety)" in words
    assert "Part 6 (The Crew)" in words
    ledger_words = ledger_plain_words(book)
    assert "Ledger kept by coordinator:" in ledger_words
    assert "Total: 6 build(s) across 5 slice(s)." in ledger_words
    single = ledger_plain_words(book.ledger_for("ledger-m140-boundary"))
    assert single.startswith("Ledger kept by coordinator:")


def test_formatters_and_screen():
    book = load_dogfood()
    entry = book.entry_for("entry-m140-forge")
    assert format_entry(entry) == (
        "entry-m140-forge: forge_worker built M-140 "
        "(Part 6) - Cost court")
    all_lines = format_entries(book).splitlines()
    assert len(all_lines) == 6
    member_lines = format_entries(book, member="auditor").splitlines()
    assert member_lines == [
        "entry-m140-auditor: auditor built M-140 (Part 6) - Cost court"]
    empty = format_entries(book, member="skald")
    assert empty == "No build records are held."
    report_text = format_report(book)
    assert "Part 5 (Autonomy & Safety) - 1 build(s)" in report_text
    ledger_text = format_ledger(book)
    assert "Kept by coordinator:" in ledger_text
    screen = format_dogfood_screen()
    assert "The Mythic Coder building itself (M-141)" in screen
    assert "entry-m120-forge" in screen
    assert USAGE in screen


def test_parser_grammar():
    assert parse_dogfood_args("") == ("show", None)
    assert parse_dogfood_args("show") == ("show", None)
    assert parse_dogfood_args("list") == ("show", None)
    assert parse_dogfood_args("entry entry-m140-forge") == (
        "entry", "entry-m140-forge")
    assert parse_dogfood_args("member forge_worker") == (
        "member", "forge_worker")
    assert parse_dogfood_args("slice M-140") == ("slice", "M-140")
    assert parse_dogfood_args("part 6") == ("part", 6)
    assert parse_dogfood_args("ledger") == ("ledger", None)
    for bad in ("bogus", "entry", "part 0", "part 12", "part x",
                "slice 140", "ledger now", "member"):
        with pytest.raises(ValueError):
            parse_dogfood_args(bad)


def test_no_live_roads():
    source = (
        ROOT / "mythic_agent" / "core" / "dogfood.py"
    ).read_text(encoding="utf-8")
    for banned in ("subprocess", "socket", "requests",
                   "mythic_agent.agents", "mythic_agent.ui",
                   "import journal", "from .journal"):
        assert banned not in source
    for name in ("spawn", "persist", "execute", "deliver",
                 "send", "merge", "bank"):
        assert f"def {name}" not in source
    module = __import__("mythic_agent.core.dogfood",
                        fromlist=["x"])
    assert not hasattr(module, "spawn")
    assert not hasattr(module, "bank")
