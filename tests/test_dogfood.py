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

# -- agent layer -----------------------------------------------------------
#
# M-141 agent layer: the agent holds a
# DogfoodRegistry for the session (session state
# only, no new setting), build records are held by
# being registered - published as their
# entry_record session news through the checkpoint
# road, deduped per entry id - the report road
# renders the held book (or the shipped example
# when unheld) through the pure formatters, and
# the /dogfood surface rides both roads on the
# pure parser + formatters. Status, get, report
# and ledger reads register and publish nothing,
# answer from the held registry first and from the
# shipped example only while nothing is held - a
# held session never falls back to the example.
# Reports and the CoordinatorLedger derive at call
# time from the held records, never held. This
# layer builds nothing live, runs no crew, calls
# no model, spawns no agent, merges or banks
# nothing, persists nothing and claims no build
# happened live - and there is no Part VIII board
# yet, so the screen is where the dogfood is
# visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _dogfood_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _entry_dict(e):
    return {
        "entry_id": e.entry_id, "member": e.member,
        "slice_id": e.slice_id, "title": e.title}


def _book_dict(**overrides):
    data = {
        "schema": DOGFOOD_SCHEMA,
        "guide": {"title": "A small dogfood book"},
        "entries": [_entry_dict(e) for e in _entries()],
    }
    data.update(overrides)
    return data


def _write_dogfood_book(tmp_path, data):
    path = tmp_path / "dogfood.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


class TestDogfoodAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.dogfood_status()
        assert status["entries"] == []
        assert status["book"] is None
        assert status["dogfood"]["title"] == (
            "Dogfood book at the M-140 slice boundary")
        assert [e["entry_id"] for e in status["dogfood"]["entries"]] == [
            "entry-m120-forge", "entry-m121-architect",
            "entry-m138-scribe", "entry-m139-forge",
            "entry-m140-forge", "entry-m140-auditor"]
        assert status["book_record"]["type"] == "dogfood_book"
        assert status["book_record"]["entry_count"] == 6
        assert status["book_record"]["ledger_count"] == 1
        assert [r["part"] for r in status["reports"]] == [5, 6]
        assert status["reports"][0]["builds"] == 1
        assert status["reports"][1]["builds"] == 5
        assert [led["ledger_id"] for led in status["ledgers"]] == [
            "ledger-m140-boundary"]
        assert status["ledger"]["keeper"] == "coordinator"
        assert status["ledger"]["total_builds"] == 6
        assert status["ledger"]["total_slices"] == 5
        assert status["ledger"]["total_parts"] == 2
        assert "forge_worker built M-120" in status["plain_words"][0]
        assert "Part 6 (The Crew) was built" in status["report_plain_words"]
        assert "Ledger kept by coordinator" in status["ledger_plain_words"]
        assert "The Mythic Coder building itself (M-141)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        assert agent._dogfood_registry() is agent._dogfood_registry()
        assert agent._dogfood_store is agent._dogfood_registry()

    def test_reads_register_and_publish_nothing(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.dogfood_status()
        entry = agent.get_dogfood_entry("entry-m139-forge")
        assert entry.member == "forge_worker"
        assert entry.part == 6
        report = agent.dogfood_report(6)
        assert report.builds == 5
        assert agent.dogfood_report(5).builds == 1
        ledger = agent.coordinator_ledger()
        assert ledger.keeper == "coordinator"
        assert ledger.total_builds == 6
        assert agent.dogfood().title == (
            "Dogfood book at the M-140 slice boundary")
        registry = agent._dogfood_registry()
        assert registry.list_entries() == ()
        assert _dogfood_events(store, session_id, "dogfood_entry") == []
        agent.close()

    def test_unheld_reads_raise(self, agent):
        with pytest.raises(KeyError):
            agent.get_dogfood_entry("no-such-entry")
        with pytest.raises(KeyError):
            agent.dogfood_report(3)

    def test_status_after_register_shows_the_held_pieces(self, agent):
        agent.register_dogfood_entry(_entry())
        status = agent.dogfood_status()
        assert [e["entry_id"] for e in status["entries"]] == [
            "entry-m139-forge"]
        assert status["book"]["entry_count"] == 1
        # The held book answers now, not the example:
        # records held one by one stand under a session
        # dogfood book, and it holds no ledgers - the
        # ledger stays a derivation.
        assert status["dogfood"]["title"] == "Session dogfood book"
        assert status["ledgers"] == []
        assert status["ledger"]["total_builds"] == 1
        assert "entry-m139-forge" in status["screen"]

    def test_held_session_never_falls_back_to_the_example(self, agent):
        agent.register_dogfood_entry(_entry())
        with pytest.raises(KeyError):
            agent.get_dogfood_entry("entry-m140-forge")
        with pytest.raises(KeyError):
            agent.dogfood_report(5)
        assert agent.dogfood().entry_ids() == ("entry-m139-forge",)
        assert agent.get_dogfood_entry(
            "entry-m139-forge").member == "forge_worker"
        report = agent.dogfood_report(6)
        assert report.builds == 1
        assert agent.coordinator_ledger().total_builds == 1


class TestDogfoodAgentRegister:
    def test_register_entry_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_dogfood_entry(_entry())
        assert outcome["entry"]["entry_id"] == "entry-m139-forge"
        assert outcome["record"]["type"] == "dogfood_entry"
        events = _dogfood_events(store, session_id, "dogfood_entry")
        assert len(events) == 1
        assert events[0]["entry_id"] == "entry-m139-forge"
        # The same record is never published twice.
        agent._publish_dogfood_record(outcome["record"])
        assert len(_dogfood_events(
            store, session_id, "dogfood_entry")) == 1
        # Foreign record types are refused on this road.
        from mythic_agent.core.character_voices import (
            load_character_voices,
            profile_record,
        )
        from mythic_agent.core.cost_court import (
            entry_record as _court_entry_record,
            load_cost_court,
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
        agent._publish_dogfood_record(report_record(
            derive_report(entries, 6), entries))
        agent._publish_dogfood_record(ledger_record(
            derive_ledger(entries), entries))
        agent._publish_dogfood_record(book_record(load_dogfood()))
        agent._publish_dogfood_record(_court_entry_record(
            load_cost_court().entries[0]))
        agent._publish_dogfood_record(_foster_report_record(
            load_failure_fostering().reports[0]))
        agent._publish_dogfood_record(_replay_step_record(
            load_crew_replay().steps[0]))
        agent._publish_dogfood_record(profile_record(
            load_character_voices().profiles[0]))
        agent._publish_dogfood_record(_sizing_case_record(
            load_crew_sizing().cases[0]))
        agent._publish_dogfood_record(_stand_up_entry_record(
            load_stand_up().entries[0]))
        memory = load_crew_memory()
        agent._publish_dogfood_record(_memory_entry_record(
            memory.entry_for("broken-checkpoint-chain")))
        panel = load_review_panel()
        agent._publish_dogfood_record(review_record(panel.reviews[0]))
        agent._publish_dogfood_record(casting_record(
            load_casting().members[0]))
        agent._publish_dogfood_record(_external_seat_record(
            load_external_agents().seats[0]))
        for kind in ("dogfood_report", "dogfood_ledger",
                     "dogfood_book", "cost_court_entry",
                     "failure_report", "crew_replay_step",
                     "character_voice_profile", "crew_sizing_case",
                     "stand_up_entry", "crew_memory_entry",
                     "panel_review", "crew_member", "external_seat"):
            assert _dogfood_events(store, session_id, kind) == []
        assert len(_dogfood_events(
            store, session_id, "dogfood_entry")) == 1
        agent.close()

    def test_duplicate_entry_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_dogfood_entry(_entry())
        with pytest.raises(ValueError):
            agent.register_dogfood_entry(_entry())
        assert len(_dogfood_events(
            store, session_id, "dogfood_entry")) == 1
        agent.close()

    def test_register_entry_without_id_gets_a_dogfood_id(self, agent):
        outcome = agent.register_dogfood_entry({
            "member": "auditor", "slice_id": "M-140",
            "title": "Cost court"})
        assert outcome["entry"]["entry_id"] == "dogfood-1"
        assert agent.get_dogfood_entry("dogfood-1").member == "auditor"

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_dogfood_book(load_dogfood())
        assert outcome["count"] == 6
        assert outcome["book"]["entry_count"] == 6
        events = _dogfood_events(store, session_id, "dogfood_entry")
        assert [e["entry_id"] for e in events] == [
            "entry-m120-forge", "entry-m121-architect",
            "entry-m138-scribe", "entry-m139-forge",
            "entry-m140-forge", "entry-m140-auditor"]
        assert agent.dogfood().title == (
            "Dogfood book at the M-140 slice boundary")
        assert agent.get_dogfood_entry(
            "entry-m121-architect").member == "architect"
        # The registry holds records, never reports or
        # ledgers: both are derived at call time.
        assert agent.dogfood().ledgers == ()
        assert agent.dogfood_report(6).builds == 5
        assert agent.dogfood_report(5).builds == 1
        assert agent.coordinator_ledger().total_builds == 6
        agent.close()

    def test_register_book_twice_refuses(self, agent):
        agent.register_dogfood_book(load_dogfood())
        with pytest.raises(ValueError):
            agent.register_dogfood_book(load_dogfood())

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_dogfood_book()
        assert outcome["count"] == 6
        assert outcome["book"]["entry_count"] == 6
        events = _dogfood_events(store, session_id, "dogfood_entry")
        assert [e["entry_id"] for e in events] == [
            "entry-m120-forge", "entry-m121-architect",
            "entry-m138-scribe", "entry-m139-forge",
            "entry-m140-forge", "entry-m140-auditor"]
        assert agent.dogfood().title == (
            "Dogfood book at the M-140 slice boundary")
        # The recorded book stands whole: its held
        # ledger still answers.
        assert agent.dogfood().ledgers[0].ledger_id == (
            "ledger-m140-boundary")
        assert agent.coordinator_ledger().total_builds == 6
        agent.close()

    def test_record_same_book_twice_refuses(self, agent):
        agent.record_dogfood_book()
        with pytest.raises(ValueError):
            agent.record_dogfood_book()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_dogfood_book(tmp_path, _book_dict())
        book = load_dogfood_file(path)
        outcome = agent.record_dogfood_book(book)
        assert outcome["count"] == 4
        assert agent.dogfood().title == "A small dogfood book"
        assert agent.get_dogfood_entry(
            "entry-m140-auditor").member == "auditor"
        assert agent.dogfood_report(6).builds == 4

    def test_one_by_one_holdings_stand_under_a_session_book(self, agent):
        agent.register_dogfood_entry(_entry())
        # Held one by one, the records stand under a
        # session dogfood book composed in the agent
        # layer - never under a recorded book title.
        assert agent.dogfood().title == "Session dogfood book"
        agent.register_dogfood_entry(_entries()[2])
        assert [e.entry_id for e in agent.dogfood().entries] == [
            "entry-m139-forge", "entry-m140-auditor"]
        # A whole book recorded now would re-hold the
        # same entry ids: the registry refuses it, as
        # it refuses any duplicate.
        with pytest.raises(ValueError):
            agent.record_dogfood_book()


class TestDogfoodAgentReport:
    def test_report_renders_the_example_when_unheld(self, agent):
        outcome = agent.report_dogfood()
        assert outcome["book"]["title"] == (
            "Dogfood book at the M-140 slice boundary")
        assert outcome["book"]["entry_count"] == 6
        assert "entry-m140-auditor" in outcome["entries_text"]
        assert "Part 6 (The Crew)" in outcome["report_text"]
        assert "Kept by coordinator:" in outcome["ledger_text"]
        assert "The Mythic Coder building itself (M-141)" in outcome["screen"]
        assert outcome["explanation"] == PLAIN_EXPLANATION

    def test_report_renders_the_held_book_only(self, agent):
        agent.register_dogfood_entry(_entry())
        outcome = agent.report_dogfood()
        assert outcome["book"]["entry_count"] == 1
        assert "entry-m139-forge" in outcome["entries_text"]
        assert "entry-m140-forge" not in outcome["entries_text"]
        assert "Part 5" not in outcome["report_text"]

    def test_report_registers_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.report_dogfood()
        registry = agent._dogfood_registry()
        assert registry.list_entries() == ()
        assert _dogfood_events(store, session_id, "dogfood_entry") == []
        agent.close()

    def test_no_live_build_crew_or_model_road(self, agent):
        # This layer holds the dogfood as data: it
        # builds nothing live, runs no crew, calls no
        # model, spawns no agent, merges or banks
        # nothing, persists nothing - and there is no
        # Part VIII board yet.
        assert not hasattr(agent, "generate_dogfood")
        assert not hasattr(agent, "persist_dogfood")
        assert not hasattr(agent, "spawn_dogfood_crew")
        assert not hasattr(agent, "run_live_crew")
        assert not hasattr(agent, "merge_dogfood")
        assert not hasattr(agent, "bank_dogfood")
        assert not hasattr(agent, "dogfood_board")


class TestDogfoodTerminalSurface:
    def test_show_entry_member_slice_part_and_ledger(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/dogfood")
        assert "The Mythic Coder building itself (M-141)" in text
        _, _, text = _slash(agent, "/dogfood entry entry-m139-forge")
        assert "entry-m139-forge: forge_worker" in text
        _, _, text = _slash(agent, "/dogfood member forge_worker")
        assert "entry-m120-forge" in text
        assert "entry-m139-forge" in text
        assert "entry-m140-auditor" not in text
        _, _, text = _slash(agent, "/dogfood slice M-140")
        assert "entry-m140-forge" in text
        assert "entry-m140-auditor" in text
        assert "entry-m139-forge" not in text
        _, _, text = _slash(agent, "/dogfood part 6")
        assert "Part 6 (The Crew) - 5 build(s)" in text
        _, _, text = _slash(agent, "/dogfood ledger")
        assert "Kept by coordinator:" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/dogfood [show|entry <entry-id>|member <member-id>|"
                "slice <slice-id>|part <part-number>|ledger]") in text
        _, _, text = _slash(agent, "/dogfood dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/dogfood entry missing-entry")
        assert "no build record in the book" in text


@pytest.fixture()
def dogfood_handler(agent, monkeypatch):
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


def _dogfood_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestDogfoodCommand:
    def test_show_is_default(self, dogfood_handler, agent):
        dogfood_handler._handle_dogfood("")
        assert "The Mythic Coder building itself (M-141)" in _dogfood_published_text(dogfood_handler)

    def test_entry_member_slice_part_and_ledger(self, dogfood_handler, agent):
        dogfood_handler._handle_dogfood("entry entry-m139-forge")
        assert "forge_worker" in _dogfood_published_text(dogfood_handler)
        dogfood_handler._handle_dogfood("member scribe")
        assert "entry-m138-scribe" in _dogfood_published_text(dogfood_handler)
        dogfood_handler._handle_dogfood("slice M-139")
        assert "entry-m139-forge" in _dogfood_published_text(dogfood_handler)
        dogfood_handler._handle_dogfood("part 5")
        assert "Part 5" in _dogfood_published_text(dogfood_handler)
        dogfood_handler._handle_dogfood("ledger")
        assert "Kept by coordinator:" in _dogfood_published_text(dogfood_handler)

    def test_bad_grammar_is_published(self, dogfood_handler, agent):
        dogfood_handler._handle_dogfood("dance party")
        assert USAGE in _dogfood_published_text(dogfood_handler)


class TestChatScreenRoutingDogfood:
    def test_dogfood_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/dogfood entry entry-m139-forge", _FakeLog())
        assert calls == [("/dogfood", "entry entry-m139-forge")]
