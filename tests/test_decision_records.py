"""M-156 Decision records - pure-layer tests.

TIER: integration

The pure layer is the session's choices as data:
one choice made in session (what was chosen, the
roads not taken, why), carried with its provenance
whole (the session it was decided in, the day, and
where it was read from), standing proposed,
accepted or superseded - a superseded record
naming the record that superseded it - composed by
import from the shipped project memory map's
decision section (M-150) and the shipped session
memory's standing decisions (M-153), with the
Scribe's doctrine read off the shipped method
charter's Project Memory Map tenet, a decision
panel derived from the whole book in settled
order, every record rendered as a small ADR in a
deterministic markdown form, the shipped example
book held in a data file, and a loader that reads
a book from any file. Nothing here calls a model
or writes any project's docs: rendering the ADR
text is the whole road.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.project_memory_map import (
    build_entry as build_map_entry,
    load_project_memory_map,
)
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.session_memory import (
    build_decision as build_standing_decision,
    load_session_memory,
)
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.decision_records import (
    DECISION_RECORDS_RESOURCE,
    DECISION_RECORDS_SCHEMA,
    DECISION_RECORDS_SLICE,
    DECISION_SCRIBE_TENET,
    DECISION_STATUSES,
    PLAIN_EXPLANATION,
    USAGE,
    DecisionBook,
    DecisionPanel,
    DecisionPanelRow,
    DecisionRecord,
    DecisionRegistry,
    DecisionStatusCount,
    accepted_records,
    book_record,
    build_book,
    build_panel,
    build_record,
    build_row,
    derive_panel,
    format_accepted,
    format_adr,
    format_adrs,
    format_decision_records_screen,
    format_panel,
    format_record,
    format_records,
    load_decision_records,
    load_decision_records_file,
    normalize_decision_status,
    panel_plain_words,
    panel_record,
    parse_decision_records_args,
    plain_words,
    record_from_map_entry,
    record_from_standing_decision,
    record_record,
    records_from_memory_map,
    records_from_session_memory,
    scribe_directives,
    validate_book,
    validate_panel,
    validate_record,
    validate_row,
)

ROOT = Path(__file__).resolve().parents[1]

EXAMPLE_TITLE = "Decision records at the M-155 slice boundary"

FRAME = {
    "session_ref": "session-alpha",
    "decided_on": "2026-11-08",
    "alternatives": ["The road not taken, named plainly."],
    "rationale": "The reason the chosen road won.",
    "context": "The situation the choice was made in.",
    "consequences": "What follows from the choice.",
}


def _record(**overrides):
    fields = {
        "record_id": "record-test",
        "status": "accepted",
        "title": "A test choice",
        "decision": "The chosen road, in plain words.",
        "alternatives": ["The other road, named."],
        "rationale": "Why the chosen road won.",
        "context": "Decided while the alpha suite was red.",
        "consequences": "The alpha suite follows the chosen road.",
        "session_ref": "session-alpha",
        "decided_on": "2026-11-08",
        "source": "test source",
    }
    fields.update(overrides)
    return build_record(fields)


def _stored_record(record):
    stored = record.to_record()
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


def _book(records=None, **overrides):
    fields = {
        "title": "A test decision book",
        "records": [_stored_record(item) for item in (
            records if records is not None else [_record()])],
    }
    fields.update(overrides)
    return build_book(fields)


def _shipped_raw():
    path = ROOT / "mythic_agent" / "data" / "decision_records.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_constants_and_usage():
    assert DECISION_RECORDS_SLICE == "M-156"
    assert DECISION_RECORDS_SCHEMA == "mythic.decision_records/1"
    assert DECISION_RECORDS_RESOURCE == "decision_records.yaml"
    assert DECISION_SCRIBE_TENET == "project-memory-map"
    assert DECISION_STATUSES == ("proposed", "accepted", "superseded")
    assert "provenance" in PLAIN_EXPLANATION
    assert "writes no project docs" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /decisions")
    assert "adr <record-id>" in USAGE


def test_roadmap_boundary_is_derived_from_the_shipped_roadmap():
    # The M-153 lesson: expectations come off the
    # shipped roadmap itself, never a hard pin of
    # this slice as the first queued slice.
    road = load_roadmap()
    ids = [item.id for item in road.slices]
    assert "M-156" in ids
    mine = road.slices[ids.index("M-156")]
    assert mine.title == "Decision records"
    assert mine.part == 7
    assert "ADR" in mine.summary
    for earlier in road.slices[:ids.index("M-156")]:
        assert earlier.status == "done", earlier.id


def test_shipped_example_shape():
    book = load_decision_records()
    assert isinstance(book, DecisionBook)
    assert book.title == EXAMPLE_TITLE
    assert book.record_ids() == (
        "record-stdlib-http", "record-httpx-client",
        "record-rune-index")
    assert book.total_records == 3
    first = book.records[0]
    # The first record stands with its provenance
    # whole and its supersession explicit.
    assert first.session_ref == "session-provider-ocean"
    assert first.status == "superseded"
    assert first.superseded_by == "record-httpx-client"
    assert first.decided_on == "2026-11-02"
    assert len(book.panels) == 1


def test_shipped_panel_is_pinned_and_derived():
    book = load_decision_records()
    panel = book.panel_for("panel-m155-boundary")
    derived = derive_panel(book)
    assert validate_panel(panel, book) == panel
    assert panel.rows == derived.rows
    assert [row.record_id for row in panel.rows] == [
        "record-httpx-client", "record-rune-index",
        "record-stdlib-http"]
    assert [row.status for row in panel.rows] == [
        "accepted", "proposed", "superseded"]
    assert panel.total_items == 3
    assert panel.total_accepted == 1
    assert panel.total_proposed == 1
    assert panel.total_superseded == 1
    assert panel.account[0] == (
        "The decision panel holds 3 records: accepted 1, "
        "proposed 1, superseded 1.")


def test_record_validation_and_aliases():
    record = build_record({
        "id": "record-alias", "state": "decided",
        "name": "An aliased choice", "choice": "The choice stands.",
        "roads_not_taken": ["The other road."],
        "why": "The reason.", "context": "A context.",
        "effects": "What follows.", "session": "session-alpha",
        "day": "2026-11-08", "source": "a source"})
    assert record.record_id == "record-alias"
    assert record.status == "accepted"
    assert record.title == "An aliased choice"
    assert record.decision == "The choice stands."
    assert record.alternatives == ("The other road.",)
    assert record.rationale == "The reason."
    assert record.consequences == "What follows."
    assert record.session_ref == "session-alpha"
    assert record.decided_on == "2026-11-08"
    assert normalize_decision_status("Draft") == "proposed"
    assert normalize_decision_status("AGREED") == "accepted"
    assert normalize_decision_status("replaced") == "superseded"
    with pytest.raises(ValueError):
        normalize_decision_status("forgotten")
    with pytest.raises(ValueError):
        build_record({
            "status": "accepted", "title": "Two titles",
            "name": "A different title", "decision": "D.",
            "alternatives": ["A."], "rationale": "R.",
            "context": "C.", "consequences": "F.",
            "session_ref": "session-alpha",
            "decided_on": "2026-11-08", "source": "S"})


def test_record_without_provenance_refuses():
    stored = _stored_record(_record())
    for field in ("session_ref", "decided_on", "source",
                  "alternatives", "rationale", "context",
                  "consequences", "decision", "status"):
        broken = dict(stored)
        broken.pop(field)
        with pytest.raises(ValueError):
            build_record(broken)
    with pytest.raises(ValueError):
        _record(decided_on="November 8")
    with pytest.raises(ValueError):
        _record(decided_on="2026-13-40")
    with pytest.raises(ValueError):
        _record(session_ref="two words")
    with pytest.raises(ValueError):
        _record(alternatives=[])
    with pytest.raises(ValueError):
        _record(alternatives=["Same road.", "Same road."])


def test_supersession_law():
    # A superseded record names its superseder.
    with pytest.raises(ValueError):
        _record(status="superseded")
    # No other state names one.
    with pytest.raises(ValueError):
        _record(status="accepted", superseded_by="record-other")
    with pytest.raises(ValueError):
        _record(status="proposed", superseded_by="record-other")
    # A record cannot supersede itself.
    with pytest.raises(ValueError):
        _record(status="superseded", superseded_by="record-test")
    old = _record(record_id="record-old", title="The old road")
    new = _record(record_id="record-new", title="The new road")
    gone = _record(
        record_id="record-gone", title="The gone road",
        status="superseded", superseded_by="record-new")
    book = _book(records=[old, new, gone])
    assert book.record_for("record-gone").superseded_by == "record-new"
    # A superseder the book does not hold refuses the book.
    orphan = _record(
        record_id="record-orphan", title="The orphan road",
        status="superseded", superseded_by="record-missing")
    with pytest.raises(ValueError):
        _book(records=[old, orphan])


def test_record_composes_the_shipped_map_decision_entry():
    entry = build_map_entry({
        "entry_id": "map-test-choice", "section": "decision",
        "title": "A mapped choice",
        "detail": "The mapped decision itself.",
        "source": "the map", "ref": "alpha/lib.py"})
    record = record_from_map_entry(entry, **FRAME)
    assert isinstance(record, DecisionRecord)
    assert record.record_id == "map-test-choice"
    assert record.status == "proposed"
    assert record.title == "A mapped choice"
    assert record.decision == entry.detail
    assert record.source == entry.source
    assert record.session_ref == "session-alpha"
    # An entry of any other section is no choice.
    fact = build_map_entry({
        "entry_id": "map-test-fact", "section": "gotcha",
        "title": "A mapped fact", "detail": "It stays a fact.",
        "source": "the map", "ref": "alpha/lib.py"})
    with pytest.raises(ValueError):
        record_from_map_entry(fact, **FRAME)
    # A bare entry names no frame: it is not recorded.
    with pytest.raises(TypeError):
        record_from_map_entry(entry)
    with pytest.raises(ValueError):
        validate_record(entry, session_ref="session-alpha")


def test_record_composes_a_standing_decision():
    standing = build_standing_decision({
        "decision_id": "standing-test", "title": "A settled choice",
        "decision": "The settled words.", "source": "the day book"})
    record = record_from_standing_decision(standing, **FRAME)
    assert record.record_id == "standing-test"
    assert record.title == "A settled choice"
    assert record.decision == "The settled words."
    assert record.source == "the day book"
    assert record.status == "proposed"


def test_records_from_the_shipped_map():
    map_book = load_project_memory_map()
    records = records_from_memory_map(map_book, **FRAME)
    decision_entries = [
        entry for entry in map_book.entries
        if entry.section == "decision"]
    assert len(records) == len(decision_entries)
    assert [item.record_id for item in records] == [
        entry.entry_id for entry in decision_entries]
    # Drafting accepts nothing: every drafted record
    # stands proposed.
    assert all(item.status == "proposed" for item in records)
    book = _book(records=list(records))
    assert accepted_records(book) == ()
    assert derive_panel(book).total_proposed == len(decision_entries)


def test_records_from_session_memory():
    memory_book = load_session_memory()
    records = records_from_session_memory(memory_book, **FRAME)
    expected = [
        decision for situation in memory_book.situations
        for decision in situation.decisions]
    assert [item.record_id for item in records] == [
        item.decision_id for item in expected]
    assert all(
        item.session_ref == "session-alpha" for item in records)


def test_scribe_directives_are_composed_by_import():
    directives = scribe_directives()
    assert directives
    assert any("decisions" in item for item in directives)
    assert any("same session" in item for item in directives)


def test_book_refusals():
    with pytest.raises(ValueError):
        _book(records=[_record(), _record(
            title="Another title")])
    with pytest.raises(ValueError):
        _book(records=[_record(), _record(
            record_id="record-two")])
    with pytest.raises(ValueError):
        _book(total_records=7)
    book = _book()
    assert book.record_for("record-test").title == "A test choice"
    with pytest.raises(KeyError):
        book.record_for("record-nope")
    with pytest.raises(KeyError):
        book.panel_for("panel-nope")


def test_panel_is_derived_in_settled_order():
    records = [
        _record(record_id="record-zed", title="Zed's choice",
                status="proposed", session_ref="session-zed"),
        _record(record_id="record-alpha", title="Alpha's choice",
                session_ref="session-alpha"),
        _record(record_id="record-gone", title="Gone's choice",
                status="superseded", superseded_by="record-alpha",
                session_ref="session-gone"),
    ]
    book = _book(records=records)
    panel = derive_panel(book)
    assert [row.status for row in panel.rows] == [
        "accepted", "proposed", "superseded"]
    assert [row.record_id for row in panel.rows] == [
        "record-alpha", "record-zed", "record-gone"]
    assert panel.total_items == 3
    assert panel.status_counts == tuple(
        DecisionStatusCount(status=status, items=1)
        for status in ("accepted", "proposed", "superseded"))
    row = panel.row_for("record-alpha")
    assert row.session_ref == "session-alpha"
    with pytest.raises(KeyError):
        panel.row_for("record-nope")


def test_panel_judgement_against_its_book():
    book = _book()
    panel = derive_panel(book)
    assert validate_panel(_stored_panel(panel), book) == panel
    tampered = _stored_panel(panel)
    tampered["rows"][0]["title"] = "A softened title"
    with pytest.raises(ValueError):
        validate_panel(tampered, book)
    tampered = _stored_panel(panel)
    tampered["rows"][0]["status"] = "proposed"
    with pytest.raises(ValueError):
        validate_panel(tampered, book)


def test_panel_construction_refusals():
    records = [
        _record(),
        _record(record_id="record-two", title="Second choice",
                status="proposed", session_ref="session-beta"),
    ]
    book = _book(records=records)
    panel = derive_panel(book)
    rows = list(panel.rows)
    with pytest.raises(ValueError):
        DecisionPanel(
            rows=list(reversed(rows)), total_items=2,
            total_accepted=1, total_proposed=1, total_superseded=0,
            status_counts=panel.status_counts,
            account=panel.account)
    with pytest.raises(ValueError):
        DecisionPanel(
            rows=rows, total_items=3,
            total_accepted=1, total_proposed=1, total_superseded=0,
            status_counts=panel.status_counts,
            account=panel.account)
    with pytest.raises(ValueError):
        build_panel({
            "rows": [_stored_panel(panel)["rows"][0]],
            "total_items": 1, "total_accepted": 1,
            "total_proposed": 0, "total_superseded": 0,
            "status_counts": [{"status": "accepted", "items": 1}]})


def test_panel_row_judged_against_its_record():
    record = _record()
    row = build_row({
        "status": "accepted", "record_id": "record-test",
        "title": record.title, "decision": record.decision,
        "session_ref": "session-alpha"}, record)
    assert isinstance(row, DecisionPanelRow)
    with pytest.raises(ValueError):
        validate_row({
            "status": "proposed", "record_id": "record-test",
            "title": record.title, "decision": record.decision,
            "session_ref": "session-alpha"}, record)


def test_accepted_records_only_through_acceptance():
    book = load_decision_records()
    standing = accepted_records(book)
    assert [item.record_id for item in standing] == [
        "record-httpx-client"]
    assert standing[0].session_ref == "session-provider-ocean"
    fresh = _book(records=[_record(status="proposed")])
    assert accepted_records(fresh) == ()


def test_book_validation_refusals():
    raw = _shipped_raw()
    with pytest.raises(ValidationError):
        validate_book({**raw, "schema": "mythic.other/9"})
    with pytest.raises(ValidationError):
        validate_book({**raw, "bogus": 1})
    broken = {**raw, "records": []}
    with pytest.raises(ValidationError):
        validate_book(broken)
    broken = {**raw, "guide": {"title": "T", "bogus": 1}}
    with pytest.raises(ValidationError):
        validate_book(broken)
    import copy
    broken = copy.deepcopy(raw)
    broken["panels"][0]["rows"][0]["title"] = "A rewritten choice"
    with pytest.raises(ValidationError):
        validate_book(broken)
    with pytest.raises(ValidationError):
        validate_book(
            {**raw, "guide": {"title": "Another title"}},
            require_example=True)


def test_load_decision_records_file_roundtrip(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "decision_records.yaml").read_text(encoding="utf-8")
    path = tmp_path / "decision_records.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_decision_records_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.record_ids()[0] == "record-stdlib-http"
    with pytest.raises(FileNotFoundError):
        load_decision_records_file(tmp_path / "missing.yaml")


def test_registry_holds_records_one_by_one():
    registry = DecisionRegistry()
    record = registry.register_record({
        "status": "proposed", "title": "Held choice",
        "decision": "Held one by one.",
        "alternatives": ["The other road."],
        "rationale": "A registry test.", "context": "A test.",
        "consequences": "Held.", "session_ref": "session-alpha",
        "decided_on": "2026-11-08", "source": "test"})
    assert record.record_id == "record-1"
    # A superseded record naming an unheld superseder
    # refuses, exactly as a book judges it.
    with pytest.raises(ValueError):
        registry.register_record({
            "status": "superseded", "title": "Gone choice",
            "decision": "Gone.", "alternatives": ["The other road."],
            "rationale": "A registry test.", "context": "A test.",
            "consequences": "Gone.", "session_ref": "session-alpha",
            "decided_on": "2026-11-08", "source": "test",
            "superseded_by": "record-missing"})
    newer = registry.register_record({
        "status": "accepted", "title": "Newer choice",
        "decision": "The newer road.",
        "alternatives": ["The held road."],
        "rationale": "A registry test.", "context": "A test.",
        "consequences": "Stands.", "session_ref": "session-alpha",
        "decided_on": "2026-11-08", "source": "test"})
    gone = registry.register_record({
        "status": "superseded", "title": "Gone choice",
        "decision": "Gone.", "alternatives": ["The newer road."],
        "rationale": "A registry test.", "context": "A test.",
        "consequences": "Replaced.", "session_ref": "session-alpha",
        "decided_on": "2026-11-08", "source": "test",
        "superseded_by": newer.record_id})
    assert gone.superseded_by == newer.record_id
    panel = registry.panel()
    assert panel.total_items == 3
    assert panel.total_accepted == 1
    assert [item.record_id for item in registry.accepted_records()] == [
        newer.record_id]
    with pytest.raises(KeyError):
        registry.get_record("record-nope")


def test_registry_register_book_titles():
    registry = DecisionRegistry()
    registry.register_book(load_decision_records())
    assert registry.book().title == EXAMPLE_TITLE
    with pytest.raises(ValueError):
        registry.register_book(load_decision_records())
    other = DecisionRegistry()
    other.register_record(_record())
    with pytest.raises(ValueError):
        other.register_book(_book(title="Another title"))


def test_records_and_plain_words():
    record = _record()
    news = record_record(record)
    assert news["type"] == "decision_record"
    assert news["news"] is True
    assert "session-alpha" in news["headline"]
    book = _book()
    panel_news = panel_record(derive_panel(book), book)
    assert panel_news["type"] == "decision_panel"
    book_news = book_record(book)
    assert book_news["type"] == "decision_book"
    assert book_news["record_count"] == 1
    words = plain_words(record)
    assert "from session-alpha" in words
    told = panel_plain_words(book)
    assert "A test decision book" in told
    assert "record-test: accepted" in told


def test_adr_rendering_is_exact_and_deterministic():
    record = _record()
    expected = "\n".join([
        "# ADR record-test: A test choice",
        "",
        "- Status: accepted",
        "- Session: session-alpha",
        "- Date: 2026-11-08",
        "- Source: test source",
        "",
        "## Context",
        "",
        "Decided while the alpha suite was red.",
        "",
        "## Decision",
        "",
        "The chosen road, in plain words.",
        "",
        "## Alternatives considered",
        "",
        "- The other road, named.",
        "",
        "## Rationale",
        "",
        "Why the chosen road won.",
        "",
        "## Consequences",
        "",
        "The alpha suite follows the chosen road.",
    ])
    assert format_adr(record) == expected
    # Rendering is deterministic: the same record
    # renders the same ADR, byte for byte.
    assert format_adr(record) == format_adr(_record())
    gone = _record(
        record_id="record-gone", title="The gone road",
        status="superseded", superseded_by="record-test")
    assert "- Superseded by: record-test" in format_adr(gone)
    book = load_decision_records()
    adrs = format_adrs(book)
    assert "# ADR record-httpx-client" in adrs
    assert adrs.count("# ADR ") == 3


def test_formatters_and_screen():
    book = load_decision_records()
    assert "record-httpx-client" in format_record(
        book.record_for("record-httpx-client"))
    assert "decided in session-provider-ocean" in format_record(
        book.record_for("record-stdlib-http"))
    assert "record-rune-index" in format_records(book)
    accepted_text = format_accepted(book)
    assert "record-httpx-client" in accepted_text
    empty = _book(records=[_record(status="proposed")])
    assert format_accepted(empty) == "No decisions stand accepted yet."
    panel_text = format_panel(book)
    assert "Decision panel in Decision records" in panel_text
    screen = format_decision_records_screen()
    assert "Decision Records (M-156)" in screen
    assert "record-stdlib-http" in screen
    assert USAGE in screen


def test_parse_decision_records_args_grammar():
    assert parse_decision_records_args("") == ("show", None)
    assert parse_decision_records_args("show") == ("show", None)
    assert parse_decision_records_args("list") == ("show", None)
    assert parse_decision_records_args(
        "record record-test") == ("record", "record-test")
    assert parse_decision_records_args(
        "adr record-test") == ("adr", "record-test")
    assert parse_decision_records_args("accepted") == ("accepted", None)
    assert parse_decision_records_args("panel") == ("panel", None)
    for bad in ("dance", "record", "accepted now",
                "record two words", "panel now"):
        with pytest.raises(ValueError):
            parse_decision_records_args(bad)


def test_honest_boundary_module_imports_no_live_roads():
    source = (ROOT / "mythic_agent" / "core"
              / "decision_records.py").read_text(encoding="utf-8")
    # The pure layer composes the shipped project
    # memory map, session memory and method charter
    # by import, and imports no agent, ui or
    # terminal code: holding or rendering a record
    # can call no model and write no project docs.
    assert "from .project_memory_map import" in source
    assert "from .session_memory import" in source
    assert "from .method_charter import" in source
    assert "from ..agents" not in source
    assert "from ..ui" not in source
    assert "from ..terminal" not in source
    assert "import agents" not in source


# -- agent layer -----------------------------------------------------------
#
# M-156 agent layer: the agent holds a
# DecisionRegistry for the session (session state
# only, no new setting), records are held by being
# registered - published as their record_record
# session news with the derived panel_record,
# through the checkpoint road, deduped per shape -
# the report road renders the held book (or the
# shipped example when unheld) through the pure
# formatters, a draft road reads the session's
# standing decisions onto records and holds them
# (accepting nothing), and the /decisions surface
# rides both roads on the pure parser +
# formatters. Status, get, panel and accepted
# reads register and publish nothing, answer from
# the held registry first and from the shipped
# example only while nothing is held - a held
# session never falls back to the example. The
# panel derives at call time from the whole book,
# never held. This layer calls no model, writes
# no project docs and persists nothing beyond the
# session journal news, and there is no Part VIII
# board yet, so the screen is where the records
# are visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _decision_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_decision_book(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "decision_records.yaml").read_text(encoding="utf-8")
    path = tmp_path / "decision_records.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestDecisionRecordsAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.decision_records_status()
        assert status["records"] == []
        assert status["book"] is None
        assert status["decisions"]["title"] == EXAMPLE_TITLE
        assert len(status["decisions"]["records"]) == 3
        assert status["panel"]["total_items"] == 3
        assert status["panel"]["total_accepted"] == 1
        assert status["panels"][0]["panel_id"] == (
            "panel-m155-boundary")
        assert status["book_record"]["record_count"] == 3
        assert "Decision Records (M-156)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._decision_records_registry()
        assert agent._decision_records_registry() is first
        assert agent._decision_records_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.decision_records_status()
        agent.get_decision_record("record-httpx-client")
        agent.decision_records_panel()
        agent.accepted_decision_records()
        agent.report_decision_records()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("decision_")] == []
        agent.close()

    def test_unheld_reads_raise(self, agent):
        with pytest.raises(KeyError):
            agent.get_decision_record("record-nope")

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_decision_record(_record())
        status = agent.decision_records_status()
        assert [item["record_id"] for item in status["records"]] == [
            "record-test"]
        assert status["book"]["title"] == "Decision records"

    def test_held_session_never_falls_back_to_the_example(
            self, agent):
        agent.register_decision_record(_record())
        with pytest.raises(KeyError):
            agent.get_decision_record("record-httpx-client")
        record = agent.get_decision_record("record-test")
        assert record.title == "A test choice"
        assert agent.decision_records_book().title == (
            "Decision records")


class TestDecisionRecordsAgentHolding:
    def test_register_record_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_decision_record(_record())
        assert outcome["record"]["record_id"] == "record-test"
        assert outcome["record_news"]["type"] == "decision_record"
        events = _decision_events(
            store, session_id, "decision_record")
        assert len(events) == 1
        assert events[0]["record_id"] == "record-test"
        agent._publish_decision_record(outcome["record_news"])
        assert len(_decision_events(
            store, session_id, "decision_record")) == 1
        agent._publish_decision_record(
            {"type": "mentions_mention", "mention_id": "mention-x"})
        agent._publish_decision_record(
            book_record(load_decision_records()))
        for kind in ("mentions_mention", "decision_book"):
            assert _decision_events(store, session_id, kind) == []
        agent.close()

    def test_duplicate_record_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_decision_record(_record())
        with pytest.raises(ValueError):
            agent.register_decision_record(_record())
        assert len(_decision_events(
            store, session_id, "decision_record")) == 1
        agent.close()

    def test_draft_from_session_memory_composes_standing_decisions(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        memory_book = load_session_memory()
        expected = sum(
            len(situation.decisions)
            for situation in memory_book.situations)
        outcome = agent.draft_decision_records_from_session_memory(
            **FRAME)
        assert outcome["count"] == expected
        assert len(_decision_events(
            store, session_id, "decision_record")) == expected
        # Every drafted record stands proposed:
        # drafting accepted nothing, silently or
        # otherwise.
        book = agent.decision_records_book()
        assert agent.accepted_decision_records() == ()
        assert agent.decision_records_panel().total_proposed == expected
        assert {item.session_ref for item in book.records} == {
            "session-alpha"}
        with pytest.raises(ValueError):
            agent.draft_decision_records_from_session_memory(**FRAME)
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent):
        book = _book()
        outcome = agent.register_decision_book(book)
        assert outcome["count"] == 1
        assert [item["type"] for item in outcome["records_news"]] == [
            "decision_record"]
        assert agent.decision_records_book().title == (
            "A test decision book")

    def test_register_book_twice_refuses(self, agent):
        agent.register_decision_book(load_decision_records())
        with pytest.raises(ValueError):
            agent.register_decision_book(load_decision_records())

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_decision_book()
        assert outcome["count"] == 3
        assert outcome["book"]["title"] == EXAMPLE_TITLE
        assert len(_decision_events(
            store, session_id, "decision_record")) == 3
        assert agent.decision_records_book().panels[0].panel_id == (
            "panel-m155-boundary")
        agent.close()

    def test_record_same_book_twice_refuses(self, agent):
        agent.record_decision_book()
        with pytest.raises(ValueError):
            agent.record_decision_book()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_decision_book(tmp_path)
        book = load_decision_records_file(path)
        outcome = agent.record_decision_book(book)
        assert outcome["count"] == 3
        assert agent.get_decision_record(
            "record-httpx-client").title == (
                "Call providers through httpx")

    def test_report_renders_the_example_when_unheld(self, agent):
        report = agent.report_decision_records()
        assert report["book"]["record_count"] == 3
        assert "record-httpx-client" in report["records_text"]
        assert "Decision panel in Decision records" in (
            report["panel_text"])
        assert "# ADR record-httpx-client" in report["adrs_text"]

    def test_report_renders_the_held_book_only(self, agent):
        agent.register_decision_record(_record())
        report = agent.report_decision_records()
        assert report["book"]["title"] == "Decision records"
        assert "record-httpx-client" not in report["records_text"]
        assert "record-test" in report["records_text"]

    def test_report_registers_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.report_decision_records()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("decision_")] == []
        agent.close()

    def test_no_live_write_or_persist_road(
            self, agent, tmp_path):
        # This layer holds and renders records as
        # data: it calls no model, writes no project
        # docs and persists nothing - and there is
        # no Part VIII board yet. Holding, recording
        # or drafting changes no workspace file and
        # no live context.
        assert not hasattr(agent, "apply_decision_records")
        assert not hasattr(agent, "write_decision_records")
        assert not hasattr(agent, "persist_decision_records")
        assert not hasattr(agent, "decision_records_board")
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
        agent.register_decision_record(_record())
        agent.record_decision_book()
        assert builder.build() == built_before
        assert {
            p.name: p.read_bytes()
            for p in tmp_path.glob("*.py")} == before


class TestDecisionRecordsTerminalSurface:
    def test_show_record_adr_accepted_panel(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/decisions")
        assert "Decision Records (M-156)" in text
        _, _, text = _slash(
            agent, "/decisions record record-httpx-client")
        assert "Call providers through httpx" in text
        _, _, text = _slash(agent, "/decisions adr record-httpx-client")
        assert "# ADR record-httpx-client" in text
        assert "## Alternatives considered" in text
        _, _, text = _slash(agent, "/decisions accepted")
        assert "record-httpx-client" in text
        _, _, text = _slash(agent, "/decisions panel")
        assert "Decision panel in Decision records" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/decisions [show|record <record-id>"
                "|adr <record-id>|accepted|panel]") in text
        _, _, text = _slash(agent, "/decisions dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/decisions record record-nope")
        assert "no record in the book" in text


@pytest.fixture()
def decisions_handler(agent, monkeypatch):
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


def _decisions_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestDecisionRecordsCommand:
    def test_show_is_default(self, decisions_handler, agent):
        decisions_handler._handle_decisions("")
        assert "Decision Records (M-156)" in (
            _decisions_published_text(decisions_handler))

    def test_record_adr_accepted_panel(
            self, decisions_handler, agent):
        decisions_handler._handle_decisions(
            "record record-httpx-client")
        assert "Call providers through httpx" in (
            _decisions_published_text(decisions_handler))
        decisions_handler._handle_decisions("adr record-httpx-client")
        assert "# ADR record-httpx-client" in (
            _decisions_published_text(decisions_handler))
        decisions_handler._handle_decisions("accepted")
        assert "record-httpx-client" in (
            _decisions_published_text(decisions_handler))
        decisions_handler._handle_decisions("panel")
        assert "Decision panel in Decision records" in (
            _decisions_published_text(decisions_handler))

    def test_bad_grammar_is_published(self, decisions_handler, agent):
        decisions_handler._handle_decisions("dance party")
        assert USAGE in _decisions_published_text(decisions_handler)


class TestChatScreenRoutingDecisionRecords:
    def test_decisions_routes_as_system_command(self, monkeypatch):
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
            "/decisions record record-httpx-client",
            _FakeLog())
        assert calls == [(
            "/decisions", "record record-httpx-client")]
