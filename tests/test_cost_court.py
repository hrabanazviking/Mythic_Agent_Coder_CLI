"""M-140 Cost court - pure-layer tests.

TIER: integration

The pure layer is the cost court as data: a court
book of run records (the member who ran, the
slice, the model and the tokens - a record's cost
derived from the shipped shared rate table,
composed by import from the costs layer, never
stored on the record), the shipped example court
book held in a data file, a loader that reads a
court book from any file, per-member-per-slice
reports whose totals and account are derived from
the run records they report, the Scribe's ledger
whose rows and account are derived from the whole
book, records shaped as session news, and a
registry. Nothing here calls a model, bills
anyone, charges anything or spawns an agent: a
stored report disagreeing with the report derived
from its own records is refused, and a stored
ledger disagreeing with the ledger derived from
its book is refused.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.costs import price
from mythic_agent.core.crew_members import load_casting
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.cost_court import (
    COST_COURT_RESOURCE,
    COST_COURT_SCHEMA,
    COST_COURT_SLICE,
    PLAIN_EXPLANATION,
    SCRIBE_MEMBER,
    USAGE,
    CostBook,
    CostEntry,
    CostReport,
    CourtRegistry,
    ScribeLedger,
    book_record,
    build_book,
    build_entry,
    build_ledger,
    build_report,
    derive_ledger,
    derive_report,
    entry_record,
    format_cost_court_screen,
    format_entries,
    format_entry,
    format_ledger,
    format_report,
    ledger_plain_words,
    ledger_record,
    load_cost_court,
    load_cost_court_file,
    parse_cost_court_args,
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
    kwargs.setdefault("entry_id", "entry-m139-forge-a")
    kwargs.setdefault("member", "forge_worker")
    kwargs.setdefault("slice_id", "M-139")
    kwargs.setdefault("model", "claude-3-5-sonnet")
    kwargs.setdefault("input_tokens", 12000)
    kwargs.setdefault("output_tokens", 3000)
    return CostEntry(**kwargs)


def _entries():
    return [
        _entry(),
        CostEntry(
            entry_id="entry-m139-forge-b", member="forge_worker",
            slice_id="M-139", model="claude-3-5-sonnet",
            input_tokens=8000, output_tokens=2000),
        CostEntry(
            entry_id="entry-m139-auditor", member="auditor",
            slice_id="M-139", model="gpt-4o-mini",
            input_tokens=5000, output_tokens=1000),
        CostEntry(
            entry_id="entry-m138-scribe-a", member="scribe",
            slice_id="M-138", model="qwen-2.5-72b",
            input_tokens=10000, output_tokens=4000),
        CostEntry(
            entry_id="entry-m138-scribe-b", member="scribe",
            slice_id="M-138", model="mystery-model",
            input_tokens=2000, output_tokens=500),
    ]


def _entry_dict(e):
    return {
        "entry_id": e.entry_id, "member": e.member,
        "slice_id": e.slice_id, "model": e.model,
        "input_tokens": e.input_tokens,
        "output_tokens": e.output_tokens}


def _report_dict(r):
    return {
        "report_id": r.report_id, "member": r.member,
        "slice_id": r.slice_id, "entry_ids": list(r.entry_ids),
        "calls": r.calls, "input_tokens": r.input_tokens,
        "output_tokens": r.output_tokens, "cost_usd": r.cost_usd,
        "unpriced_calls": r.unpriced_calls,
        "account": list(r.account)}


def _ledger_dict(led):
    return {
        "ledger_id": led.ledger_id, "keeper": led.keeper,
        "rows": [_report_dict(r) for r in led.rows],
        "total_calls": led.total_calls,
        "total_input_tokens": led.total_input_tokens,
        "total_output_tokens": led.total_output_tokens,
        "total_cost_usd": led.total_cost_usd,
        "account": list(led.account)}


def _book_dict(**overrides):
    data = {
        "schema": COST_COURT_SCHEMA,
        "guide": {"title": "A small court book"},
        "entries": [_entry_dict(e) for e in _entries()],
    }
    data.update(overrides)
    return data


# ---------------------------------------------------------------------
# Constants, the shipped example, and its pinned shape.
# ---------------------------------------------------------------------


def test_constants_and_usage():
    assert COST_COURT_SLICE == "M-140"
    assert COST_COURT_RESOURCE == "cost_court.yaml"
    assert COST_COURT_SCHEMA == "mythic.cost_court/1"
    assert SCRIBE_MEMBER == "scribe"
    assert "cost court" in PLAIN_EXPLANATION.lower()
    assert "/costcourt" in USAGE
    assert "ledger" in USAGE


def test_shipped_example_shape():
    book = load_cost_court()
    assert book.title == "Cost court at the M-139 slice boundary"
    assert book.entry_ids() == (
        "entry-m139-forge-a", "entry-m139-forge-b",
        "entry-m139-auditor", "entry-m138-scribe-a",
        "entry-m138-scribe-b")
    ledger = book.ledger_for("ledger-m139-boundary")
    assert ledger.keeper == "scribe"
    assert [(r.slice_id, r.member) for r in ledger.rows] == [
        ("M-139", "forge_worker"), ("M-139", "auditor"),
        ("M-138", "scribe")]
    assert (ledger.total_calls, ledger.total_input_tokens,
            ledger.total_output_tokens) == (5, 37000, 10500)
    assert ledger.total_cost_usd == pytest.approx(0.14145)
    first = derive_report(book.entries, "forge_worker", "M-139")
    assert first.calls == 2
    assert first.cost_usd == pytest.approx(0.135)
    assert first.account[0] == (
        "Member forge_worker spent $0.135000 on slice M-139.")
    scribe = derive_report(book.entries, "scribe", "M-138")
    assert scribe.unpriced_calls == 1
    assert scribe.cost_usd == pytest.approx(0.0051)


def test_example_members_are_shipped_casting_members():
    casting = load_casting()
    ids = {m.member_id for m in casting.members}
    book = load_cost_court()
    for entry in book.entries:
        assert entry.member in ids
    assert SCRIBE_MEMBER in ids


def test_example_costs_are_the_shared_tables_own_prices():
    book = load_cost_court()
    for entry in book.entries:
        expected, known = price(
            entry.model, entry.input_tokens, entry.output_tokens)
        assert entry.cost_usd == expected
        assert entry.priced is known
    unknown = book.entry_for("entry-m138-scribe-b")
    assert unknown.priced is False
    assert unknown.cost_usd == 0.0


# ---------------------------------------------------------------------
# Run records: validation, aliases, refusals.
# ---------------------------------------------------------------------


def test_entry_validation_with_alias_spellings():
    entry = validate_entry({
        "id": "entry-x", "member_id": "auditor", "slice": "m-140",
        "model": "gpt-4o", "input": 100, "completion_tokens": 25})
    assert entry.entry_id == "entry-x"
    assert entry.member == "auditor"
    assert entry.slice_id == "M-140"
    assert entry.input_tokens == 100
    assert entry.output_tokens == 25
    built = build_entry(member="scribe", slice_id="M-138",
                        model="gpt-4o-mini", input_tokens=10,
                        output_tokens=5)
    assert built.member == "scribe"
    assert build_entry(entry) is entry


def test_entry_refusals():
    with pytest.raises(ValueError):
        validate_entry({"member": "auditor", "slice_id": "M-140",
                        "model": "gpt-4o", "input_tokens": 1,
                        "output_tokens": 1, "cost_usd": 0.5})
    with pytest.raises(ValueError):
        validate_entry({"member": "auditor", "slice_id": "M-140",
                        "model": "gpt-4o", "input_tokens": 1,
                        "output_tokens": 1, "bogus": 1})
    with pytest.raises(ValueError):
        validate_entry({"member": "two words", "slice_id": "M-140",
                        "model": "gpt-4o", "input_tokens": 1,
                        "output_tokens": 1})
    with pytest.raises(ValueError):
        validate_entry({"member": "auditor", "slice_id": "M-999",
                        "model": "gpt-4o", "input_tokens": 1,
                        "output_tokens": 1})
    with pytest.raises(ValueError):
        validate_entry({"member": "auditor", "slice_id": "M-140",
                        "model": "gpt-4o", "input_tokens": -1,
                        "output_tokens": 1})
    with pytest.raises(ValueError):
        validate_entry({"member": "auditor", "slice_id": "M-140",
                        "model": "gpt-4o", "input_tokens": True,
                        "output_tokens": 1})
    with pytest.raises(ValueError):
        validate_entry({"member": "auditor", "slice_id": "M-140",
                        "model": "gpt-4o", "input_tokens": 1})
    with pytest.raises(ValueError):
        validate_entry({"member": "auditor", "member_id": "scribe",
                        "slice_id": "M-140", "model": "gpt-4o",
                        "input_tokens": 1, "output_tokens": 1})
    with pytest.raises(ValueError):
        validate_entry("not a mapping")


# ---------------------------------------------------------------------
# Reports: derivation and the stored-report judgement.
# ---------------------------------------------------------------------


def test_report_derivation_is_deterministic():
    entries = _entries()
    one = derive_report(entries, "forge_worker", "M-139")
    two = derive_report(entries, "forge_worker", "M-139")
    assert one == two
    assert one.entry_ids == (
        "entry-m139-forge-a", "entry-m139-forge-b")
    assert (one.calls, one.input_tokens, one.output_tokens) == (
        2, 20000, 5000)
    assert one.cost_usd == pytest.approx(0.135)
    assert one.unpriced_calls == 0
    by_book = derive_report(
        CostBook(title="T", entries=entries), "auditor", "M-139")
    assert by_book.calls == 1
    with pytest.raises(KeyError):
        derive_report(entries, "skald", "M-139")


def test_stored_reports_judged_against_their_records():
    entries = _entries()
    derived = derive_report(entries, "scribe", "M-138")
    stored = _report_dict(derived)
    assert validate_report(stored, entries) == derived
    assert build_report(stored, entries) == derived
    tampered = dict(stored, cost_usd=9.99)
    with pytest.raises(ValueError):
        validate_report(tampered, entries)
    tampered = dict(stored, account=[
        "Member scribe spent $0.005100 on slice M-138."])
    with pytest.raises(ValueError):
        validate_report(tampered, entries)
    no_account = dict(stored)
    del no_account["account"]
    with pytest.raises(ValueError):
        validate_report(no_account, entries)
    bad_key = dict(stored, bogus=1)
    with pytest.raises(ValueError):
        validate_report(bad_key, entries)
    with pytest.raises(ValueError):
        CostReport(
            member="scribe", slice_id="M-138",
            entry_ids=("entry-m138-scribe-a",), calls=2,
            input_tokens=10000, output_tokens=4000,
            cost_usd=0.0051, unpriced_calls=0,
            account=("One statement.",))


# ---------------------------------------------------------------------
# The Scribe's ledger: derivation and the stored-ledger judgement.
# ---------------------------------------------------------------------


def test_ledger_derivation_is_deterministic():
    entries = _entries()
    one = derive_ledger(entries)
    two = derive_ledger(entries)
    assert one == two
    assert one.keeper == SCRIBE_MEMBER
    assert [(r.slice_id, r.member) for r in one.rows] == [
        ("M-139", "forge_worker"), ("M-139", "auditor"),
        ("M-138", "scribe")]
    assert one.total_cost_usd == pytest.approx(0.14145)
    assert one.row_for("scribe", "M-138").unpriced_calls == 1
    with pytest.raises(KeyError):
        one.row_for("skald", "M-139")
    with pytest.raises(ValueError):
        derive_ledger([])


def test_stored_ledgers_judged_against_their_book():
    entries = _entries()
    derived = derive_ledger(entries)
    stored = _ledger_dict(derived)
    assert validate_ledger(stored, entries) == derived
    assert build_ledger(stored, entries) == derived
    tampered = dict(stored, total_cost_usd=1.0,
                    rows=stored["rows"])
    with pytest.raises(ValueError):
        validate_ledger(tampered, entries)
    wrong_keeper = dict(stored, keeper="auditor")
    with pytest.raises(ValueError):
        validate_ledger(wrong_keeper, entries)
    no_account = dict(stored)
    del no_account["account"]
    with pytest.raises(ValueError):
        validate_ledger(no_account, entries)
    bad_key = dict(stored, bogus=1)
    with pytest.raises(ValueError):
        validate_ledger(bad_key, entries)
    with pytest.raises(ValueError):
        ScribeLedger(
            ledger_id="ledger-x", keeper="scribe",
            rows=derived.rows, total_calls=99,
            total_input_tokens=derived.total_input_tokens,
            total_output_tokens=derived.total_output_tokens,
            total_cost_usd=derived.total_cost_usd,
            account=derived.account)


# ---------------------------------------------------------------------
# Books: validation, views, refusals, and the file loader.
# ---------------------------------------------------------------------


def test_book_validation_and_views():
    ledger = _ledger_dict(derive_ledger(_entries()))
    ledger["ledger_id"] = "ledger-test"
    book = validate_book(_book_dict(ledgers=[ledger]))
    assert book.title == "A small court book"
    assert book.entry_for("entry-m139-auditor").member == "auditor"
    assert [e.entry_id for e in book.entries_for("scribe")] == [
        "entry-m138-scribe-a", "entry-m138-scribe-b"]
    assert [e.entry_id for e in book.entries_on("M-139")] == [
        "entry-m139-forge-a", "entry-m139-forge-b",
        "entry-m139-auditor"]
    assert book.ledger_for("ledger-test").keeper == "scribe"
    with pytest.raises(KeyError):
        book.entry_for("entry-nope")
    with pytest.raises(KeyError):
        book.ledger_for("ledger-nope")
    built = build_book(_book_dict())
    assert built.entry_ids() == tuple(
        e.entry_id for e in _entries())
    assert build_book(built) is built


def test_book_refusals():
    entries = _entries()
    dup = _book_dict()
    dup["entries"] = [_entry_dict(entries[0]),
                      _entry_dict(entries[0])]
    with pytest.raises(ValidationError):
        validate_book(dup)
    ledger = _ledger_dict(derive_ledger(entries))
    ledger["total_cost_usd"] = 3.25
    ledger["rows"] = [
        dict(r, cost_usd=r["cost_usd"]) for r in ledger["rows"]]
    with pytest.raises(ValidationError):
        validate_book(_book_dict(ledgers=[ledger]))
    with pytest.raises(ValidationError):
        validate_book(_book_dict(schema="mythic.other/1"))
    with pytest.raises(ValidationError):
        validate_book(_book_dict(bogus=1))
    no_entries = _book_dict()
    del no_entries["entries"]
    with pytest.raises(ValidationError):
        validate_book(no_entries)
    with pytest.raises(ValidationError):
        validate_book("not a mapping")
    with pytest.raises(ValidationError):
        validate_book(_book_dict(), require_example=True)


def test_file_loader_round_trip(tmp_path):
    data = _book_dict(
        ledgers=[_ledger_dict(derive_ledger(_entries()))])
    path = tmp_path / "court.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    book = load_cost_court_file(path)
    assert book.title == "A small court book"
    assert book.entry_ids() == tuple(e.entry_id for e in _entries())
    with pytest.raises(FileNotFoundError):
        load_cost_court_file(tmp_path / "missing.yaml")
    bad = tmp_path / "bad.yaml"
    bad.write_text("schema: mythic.cost_court/1\nentries: 5\n",
                   encoding="utf-8")
    with pytest.raises(ValidationError):
        load_cost_court_file(bad)


# ---------------------------------------------------------------------
# The registry: records held, reports and ledger derived.
# ---------------------------------------------------------------------


def test_registry_holds_records_and_derives():
    registry = CourtRegistry(load_cost_court())
    assert registry.get_entry("entry-m139-forge-a").member == \
        "forge_worker"
    report = registry.report_for("forge_worker", "M-139")
    assert report.cost_usd == pytest.approx(0.135)
    ledger = registry.ledger()
    assert ledger.total_calls == 5
    held = registry.book()
    assert held.ledgers == ()
    assert held.entry_ids() == load_cost_court().entry_ids()
    with pytest.raises(KeyError):
        registry.get_entry("entry-nope")
    with pytest.raises(KeyError):
        registry.report_for("skald", "M-139")


def test_registry_auto_ids_and_refusals():
    registry = CourtRegistry()
    first = registry.register_entry({
        "member": "auditor", "slice_id": "M-140",
        "model": "gpt-4o", "input_tokens": 10, "output_tokens": 2})
    second = registry.register_entry({
        "member": "auditor", "slice_id": "M-140",
        "model": "gpt-4o", "input_tokens": 5, "output_tokens": 1})
    assert (first.entry_id, second.entry_id) == ("court-1", "court-2")
    with pytest.raises(ValueError):
        registry.register_entry(first)
    with pytest.raises(ValueError):
        CourtRegistry().book()
    titled = CourtRegistry(load_cost_court())
    other = CostBook(
        title="Another book", entries=_entries())
    with pytest.raises(ValueError):
        titled.register_book(other)


# ---------------------------------------------------------------------
# Session-news records, plain words, screens, and the parser.
# ---------------------------------------------------------------------


def test_session_news_records():
    entries = _entries()
    entry = entry_record(entries[0])
    assert entry["type"] == "cost_court_entry"
    assert entry["slice"] == "M-140"
    assert entry["news"] is True
    assert "forge_worker" in entry["headline"]
    assert entry["cost_usd"] == pytest.approx(0.081)
    report = report_record(
        derive_report(entries, "forge_worker", "M-139"), entries)
    assert report["type"] == "cost_court_report"
    assert report["news"] is True
    ledger = ledger_record(derive_ledger(entries), entries)
    assert ledger["type"] == "cost_court_ledger"
    assert ledger["keeper"] == "scribe"
    book = book_record(load_cost_court())
    assert book["type"] == "cost_court_book"
    assert book["entry_count"] == 5
    assert book["ledger_count"] == 1


def test_plain_words():
    entries = _entries()
    words = plain_words(entries[0])
    assert "forge_worker" in words
    assert "priced" in words
    unknown = plain_words(entries[-1])
    assert "unpriced" in unknown
    book = CostBook(title="T", entries=entries)
    reports = report_plain_words(book)
    assert "forge_worker on M-139" in reports
    single = report_plain_words(
        derive_report(entries, "auditor", "M-139"))
    assert "auditor on M-139" in single
    ledger_words = ledger_plain_words(book)
    assert "Ledger kept by scribe" in ledger_words
    assert "Part XI" in ledger_words
    with pytest.raises(ValueError):
        report_plain_words("nope")
    with pytest.raises(ValueError):
        ledger_plain_words(42)


def test_formatters_and_screen():
    assert format_entry(_entries()[0]).startswith(
        "entry-m139-forge-a: forge_worker")
    book = load_cost_court()
    lines = format_entries(book)
    assert "entry-m138-scribe-b" in lines
    assert format_entries(book, member="skald") == \
        "No run records are held."
    reports = format_report(book)
    assert "Reports in Cost court at the M-139 slice boundary:" \
        in reports
    assert "scribe on M-138" in reports
    ledger = format_ledger(book)
    assert "Kept by scribe:" in ledger
    screen = format_cost_court_screen()
    assert "Cost court (M-140)" in screen
    assert USAGE in screen
    assert "ledger-m139-boundary" not in screen


def test_parser_grammar():
    assert parse_cost_court_args("") == ("show", None)
    assert parse_cost_court_args("show") == ("show", None)
    assert parse_cost_court_args("list") == ("show", None)
    assert parse_cost_court_args("ledger") == ("ledger", None)
    assert parse_cost_court_args("entry entry-m139-forge-a") == (
        "entry", "entry-m139-forge-a")
    assert parse_cost_court_args("member forge_worker") == (
        "member", "forge_worker")
    assert parse_cost_court_args("slice m-139") == (
        "slice", "M-139")
    for bad in ("bogus", "entry", "member two words",
                "slice M-999", "ledger now", 42):
        with pytest.raises(ValueError):
            parse_cost_court_args(bad)


# ---------------------------------------------------------------------
# The honest boundary: data and contracts only.
# ---------------------------------------------------------------------


def test_no_live_roads():
    source = (
        ROOT / "mythic_agent" / "core" / "cost_court.py"
    ).read_text(encoding="utf-8")
    for banned in ("subprocess", "socket", "requests",
                   "mythic_agent.agents", "mythic_agent.ui",
                   "import journal", "from .journal"):
        assert banned not in source
    for name in ("spawn", "persist", "execute", "deliver",
                 "send", "charge", "bill"):
        assert f"def {name}" not in source
    module = __import__("mythic_agent.core.cost_court",
                        fromlist=["x"])
    assert not hasattr(module, "charge")
    assert not hasattr(module, "bill")
