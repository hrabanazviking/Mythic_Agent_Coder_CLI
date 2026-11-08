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


# -- agent layer -----------------------------------------------------------
#
# M-140 agent layer: the agent holds a
# CourtRegistry for the session (session state
# only, no new setting), run records are held by
# being registered - published as their
# entry_record session news through the checkpoint
# road, deduped per entry id - the report road
# renders the held book (or the shipped example
# when unheld) through the pure formatters, and
# the /costcourt surface rides both roads on the
# pure parser + formatters. Status, get, report
# and ledger reads register and publish nothing,
# answer from the held registry first and from the
# shipped example only while nothing is held - a
# held session never falls back to the example.
# Reports and the ledger are derived at call time
# from the held records, never held. This layer
# calls no model, bills no one, charges nothing,
# persists nothing and claims no live crew run -
# and there is no Part VIII board yet, so the
# screen is where the court is visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _court_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_court_book(tmp_path, data):
    path = tmp_path / "court.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


class TestCostCourtAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.cost_court_status()
        assert status["entries"] == []
        assert status["book"] is None
        assert status["court"]["title"] == (
            "Cost court at the M-139 slice boundary")
        assert [e["entry_id"] for e in status["court"]["entries"]] == [
            "entry-m139-forge-a", "entry-m139-forge-b",
            "entry-m139-auditor", "entry-m138-scribe-a",
            "entry-m138-scribe-b"]
        assert status["book_record"]["type"] == "cost_court_book"
        assert status["book_record"]["entry_count"] == 5
        assert status["book_record"]["ledger_count"] == 1
        assert [(r["member"], r["slice_id"]) for r in status["reports"]] == [
            ("forge_worker", "M-139"), ("auditor", "M-139"),
            ("scribe", "M-138")]
        assert status["reports"][0]["cost_usd"] == pytest.approx(0.135)
        assert [led["ledger_id"] for led in status["ledgers"]] == [
            "ledger-m139-boundary"]
        assert status["ledger"]["keeper"] == "scribe"
        assert status["ledger"]["total_calls"] == 5
        assert status["ledger"]["total_cost_usd"] == pytest.approx(0.14145)
        assert "forge_worker ran claude-3-5-sonnet" in status["plain_words"][0]
        assert "forge_worker on M-139" in status["report_plain_words"]
        assert "Ledger kept by scribe" in status["ledger_plain_words"]
        assert "Cost court (M-140)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        assert agent._cost_court_registry() is agent._cost_court_registry()
        assert agent._cost_court_store is agent._cost_court_registry()

    def test_reads_register_and_publish_nothing(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.cost_court_status()
        entry = agent.get_cost_entry("entry-m139-forge-a")
        assert entry.member == "forge_worker"
        assert entry.cost_usd == pytest.approx(0.081)
        report = agent.cost_report("forge_worker", "M-139")
        assert report.calls == 2
        assert report.cost_usd == pytest.approx(0.135)
        ledger = agent.scribe_ledger()
        assert ledger.keeper == "scribe"
        assert ledger.total_calls == 5
        assert agent.cost_court().title == (
            "Cost court at the M-139 slice boundary")
        registry = agent._cost_court_registry()
        assert registry.list_entries() == ()
        assert _court_events(store, session_id, "cost_court_entry") == []
        agent.close()

    def test_unheld_reads_raise(self, agent):
        with pytest.raises(KeyError):
            agent.get_cost_entry("no-such-entry")
        with pytest.raises(KeyError):
            agent.cost_report("skald", "M-139")
        with pytest.raises(KeyError):
            agent.cost_report("forge_worker", "M-200")

    def test_status_after_register_shows_the_held_pieces(self, agent):
        agent.register_cost_entry(_entry())
        status = agent.cost_court_status()
        assert [e["entry_id"] for e in status["entries"]] == [
            "entry-m139-forge-a"]
        assert status["book"]["entry_count"] == 1
        # The held book answers now, not the example:
        # records held one by one stand under a session
        # cost court book, and it holds no ledgers -
        # the ledger stays a derivation.
        assert status["court"]["title"] == "Session cost court book"
        assert status["ledgers"] == []
        assert status["ledger"]["total_calls"] == 1
        assert "entry-m139-forge-a" in status["screen"]

    def test_held_session_never_falls_back_to_the_example(self, agent):
        agent.register_cost_entry(_entry())
        with pytest.raises(KeyError):
            agent.get_cost_entry("entry-m139-forge-b")
        with pytest.raises(KeyError):
            agent.cost_report("auditor", "M-139")
        assert agent.cost_court().entry_ids() == ("entry-m139-forge-a",)
        assert agent.get_cost_entry(
            "entry-m139-forge-a").member == "forge_worker"
        report = agent.cost_report("forge_worker", "M-139")
        assert report.calls == 1
        assert agent.scribe_ledger().total_calls == 1


class TestCostCourtAgentRegister:
    def test_register_entry_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_cost_entry(_entry())
        assert outcome["entry"]["entry_id"] == "entry-m139-forge-a"
        assert outcome["record"]["type"] == "cost_court_entry"
        events = _court_events(store, session_id, "cost_court_entry")
        assert len(events) == 1
        assert events[0]["entry_id"] == "entry-m139-forge-a"
        # The same record is never published twice.
        agent._publish_cost_court_record(outcome["record"])
        assert len(_court_events(
            store, session_id, "cost_court_entry")) == 1
        # Foreign record types are refused on this road.
        from mythic_agent.core.character_voices import (
            load_character_voices,
            profile_record,
        )
        from mythic_agent.core.crew_members import (
            casting_record,
            load_casting,
        )
        from mythic_agent.core.crew_memory import (
            entry_record as _memory_entry_record,
            load_crew_memory,
        )
        from mythic_agent.core.crew_replay import (
            load_crew_replay,
            step_record as _replay_step_record,
        )
        from mythic_agent.core.crew_sizing import (
            case_record as _sizing_case_record,
            load_crew_sizing,
        )
        from mythic_agent.core.external_agents import (
            load_external_agents,
            seat_record as _external_seat_record,
        )
        from mythic_agent.core.failure_fostering import (
            load_failure_fostering,
            report_record as _foster_report_record,
        )
        from mythic_agent.core.review_panels import (
            load_review_panel,
            review_record,
        )
        from mythic_agent.core.stand_ups import (
            entry_record as _stand_up_entry_record,
            load_stand_up,
        )
        entries = _entries()
        agent._publish_cost_court_record(report_record(
            derive_report(entries, "forge_worker", "M-139"), entries))
        agent._publish_cost_court_record(ledger_record(
            derive_ledger(entries), entries))
        agent._publish_cost_court_record(book_record(load_cost_court()))
        agent._publish_cost_court_record(_foster_report_record(
            load_failure_fostering().reports[0]))
        agent._publish_cost_court_record(_replay_step_record(
            load_crew_replay().steps[0]))
        agent._publish_cost_court_record(profile_record(
            load_character_voices().profiles[0]))
        agent._publish_cost_court_record(_sizing_case_record(
            load_crew_sizing().cases[0]))
        agent._publish_cost_court_record(_stand_up_entry_record(
            load_stand_up().entries[0]))
        memory = load_crew_memory()
        agent._publish_cost_court_record(_memory_entry_record(
            memory.entry_for("broken-checkpoint-chain")))
        panel = load_review_panel()
        agent._publish_cost_court_record(review_record(panel.reviews[0]))
        agent._publish_cost_court_record(casting_record(
            load_casting().members[0]))
        agent._publish_cost_court_record(_external_seat_record(
            load_external_agents().seats[0]))
        for kind in ("cost_court_report", "cost_court_ledger",
                     "cost_court_book", "failure_report",
                     "crew_replay_step", "character_voice_profile",
                     "crew_sizing_case", "stand_up_entry",
                     "crew_memory_entry", "panel_review", "crew_member",
                     "external_seat"):
            assert _court_events(store, session_id, kind) == []
        assert len(_court_events(
            store, session_id, "cost_court_entry")) == 1
        agent.close()

    def test_duplicate_entry_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_cost_entry(_entry())
        with pytest.raises(ValueError):
            agent.register_cost_entry(_entry())
        assert len(_court_events(
            store, session_id, "cost_court_entry")) == 1
        agent.close()

    def test_register_entry_without_id_gets_a_court_id(self, agent):
        outcome = agent.register_cost_entry({
            "member": "auditor", "slice_id": "M-140",
            "model": "gpt-4o", "input_tokens": 10, "output_tokens": 2})
        assert outcome["entry"]["entry_id"] == "court-1"
        assert agent.get_cost_entry("court-1").member == "auditor"

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_cost_book(load_cost_court())
        assert outcome["count"] == 5
        assert outcome["book"]["entry_count"] == 5
        events = _court_events(store, session_id, "cost_court_entry")
        assert [e["entry_id"] for e in events] == [
            "entry-m139-forge-a", "entry-m139-forge-b",
            "entry-m139-auditor", "entry-m138-scribe-a",
            "entry-m138-scribe-b"]
        assert agent.cost_court().title == (
            "Cost court at the M-139 slice boundary")
        assert agent.get_cost_entry("entry-m138-scribe-b").priced is False
        # The registry holds records, never reports or
        # ledgers: both are derived at call time.
        assert agent.cost_court().ledgers == ()
        assert agent.cost_report("scribe", "M-138").unpriced_calls == 1
        assert agent.scribe_ledger().total_calls == 5
        agent.close()

    def test_register_book_twice_refuses(self, agent):
        agent.register_cost_book(load_cost_court())
        with pytest.raises(ValueError):
            agent.register_cost_book(load_cost_court())

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_cost_book()
        assert outcome["count"] == 5
        assert outcome["book"]["entry_count"] == 5
        events = _court_events(store, session_id, "cost_court_entry")
        assert [e["entry_id"] for e in events] == [
            "entry-m139-forge-a", "entry-m139-forge-b",
            "entry-m139-auditor", "entry-m138-scribe-a",
            "entry-m138-scribe-b"]
        assert agent.cost_court().title == (
            "Cost court at the M-139 slice boundary")
        # The recorded book stands whole: its held
        # ledger still answers.
        assert agent.cost_court().ledgers[0].ledger_id == (
            "ledger-m139-boundary")
        assert agent.scribe_ledger().total_cost_usd == pytest.approx(0.14145)
        agent.close()

    def test_record_same_book_twice_refuses(self, agent):
        agent.record_cost_book()
        with pytest.raises(ValueError):
            agent.record_cost_book()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_court_book(tmp_path, _book_dict())
        book = load_cost_court_file(path)
        outcome = agent.record_cost_book(book)
        assert outcome["count"] == 5
        assert agent.cost_court().title == "A small court book"
        assert agent.get_cost_entry("entry-m139-auditor").member == "auditor"
        assert agent.cost_report(
            "forge_worker", "M-139").cost_usd == pytest.approx(0.135)

    def test_one_by_one_holdings_stand_under_a_session_book(self, agent):
        agent.register_cost_entry(_entry())
        # Held one by one, the records stand under a
        # session cost court book composed in the agent
        # layer - never under a recorded book title.
        assert agent.cost_court().title == "Session cost court book"
        agent.register_cost_entry(_entries()[2])
        assert [e.entry_id for e in agent.cost_court().entries] == [
            "entry-m139-forge-a", "entry-m139-auditor"]
        # A whole book recorded now would re-hold the
        # same entry ids: the registry refuses it, as
        # it refuses any duplicate.
        with pytest.raises(ValueError):
            agent.record_cost_book()


class TestCostCourtAgentReport:
    def test_report_renders_the_example_when_unheld(self, agent):
        outcome = agent.report_cost_court()
        assert outcome["book"]["title"] == (
            "Cost court at the M-139 slice boundary")
        assert outcome["book"]["entry_count"] == 5
        assert "entry-m138-scribe-b" in outcome["entries_text"]
        assert "scribe on M-138" in outcome["report_text"]
        assert "Kept by scribe:" in outcome["ledger_text"]
        assert "Cost court (M-140)" in outcome["screen"]
        assert outcome["explanation"] == PLAIN_EXPLANATION

    def test_report_renders_the_held_book_only(self, agent):
        agent.register_cost_entry(_entry())
        outcome = agent.report_cost_court()
        assert outcome["book"]["entry_count"] == 1
        assert "entry-m139-forge-a" in outcome["entries_text"]
        assert "entry-m139-forge-b" not in outcome["entries_text"]
        assert "auditor" not in outcome["report_text"]

    def test_report_registers_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.report_cost_court()
        registry = agent._cost_court_registry()
        assert registry.list_entries() == ()
        assert _court_events(store, session_id, "cost_court_entry") == []
        agent.close()

    def test_no_live_bill_charge_or_model_road(self, agent):
        # This layer holds the court as data: it calls
        # no model, bills no one, charges nothing,
        # runs no live crew, persists nothing - and
        # there is no Part VIII board yet.
        assert not hasattr(agent, "generate_cost_court")
        assert not hasattr(agent, "persist_cost_court")
        assert not hasattr(agent, "bill_cost_court")
        assert not hasattr(agent, "charge_cost_court")
        assert not hasattr(agent, "issue_bill")
        assert not hasattr(agent, "run_live_crew")
        assert not hasattr(agent, "cost_court_board")


class TestCostCourtTerminalSurface:
    def test_show_entry_member_slice_and_ledger(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/costcourt")
        assert "Cost court (M-140)" in text
        _, _, text = _slash(agent, "/costcourt entry entry-m139-forge-a")
        assert "entry-m139-forge-a: forge_worker" in text
        _, _, text = _slash(agent, "/costcourt member forge_worker")
        assert "entry-m139-forge-a" in text
        assert "entry-m139-forge-b" in text
        assert "entry-m139-auditor" not in text
        _, _, text = _slash(agent, "/costcourt slice M-138")
        assert "entry-m138-scribe-a" in text
        assert "entry-m139-forge-a" not in text
        _, _, text = _slash(agent, "/costcourt ledger")
        assert "Kept by scribe:" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/costcourt [show|entry <entry-id>|member <member-id>|"
                "slice <slice-id>|ledger]") in text
        _, _, text = _slash(agent, "/costcourt dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/costcourt entry missing-entry")
        assert "no run record in the book" in text


@pytest.fixture()
def court_handler(agent, monkeypatch):
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


def _court_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestCostCourtCommand:
    def test_show_is_default(self, court_handler, agent):
        court_handler._handle_costcourt("")
        assert "Cost court (M-140)" in _court_published_text(court_handler)

    def test_entry_member_slice_and_ledger(self, court_handler, agent):
        court_handler._handle_costcourt("entry entry-m139-forge-a")
        assert "forge_worker" in _court_published_text(court_handler)
        court_handler._handle_costcourt("member scribe")
        assert "entry-m138-scribe-a" in _court_published_text(court_handler)
        court_handler._handle_costcourt("slice M-139")
        assert "entry-m139-auditor" in _court_published_text(court_handler)
        court_handler._handle_costcourt("ledger")
        assert "Kept by scribe:" in _court_published_text(court_handler)

    def test_bad_grammar_is_published(self, court_handler, agent):
        court_handler._handle_costcourt("dance party")
        assert USAGE in _court_published_text(court_handler)


class TestChatScreenRoutingCostCourt:
    def test_costcourt_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/costcourt entry entry-m139-forge-a", _FakeLog())
        assert calls == [("/costcourt", "entry entry-m139-forge-a")]
