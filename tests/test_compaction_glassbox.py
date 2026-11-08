"""M-151 Compaction v2, glass-box - pure-layer tests.

TIER: integration

The pure layer is the compaction as data: one book
of compaction records (what each compaction
replaced - the material kept whole or by journal
reference - the summary that replaced it, held as
its versions in order, and the record's journal
position, beside what it replaced), the shipped
example book held in a data file, a loader that
reads a book from any file, a panel derived from
the whole book in journal order, an edit road that
appends a new summary version and keeps every
earlier one, and a registry. A stored panel
disagreeing with the panel derived from its book
is refused, and a stored summary disagreeing with
its record's versions is refused. Nothing here
compacts live context: holding a record changes
no context, calls no model and archives nothing.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.validation import ValidationError
from mythic_agent.core.compaction_glassbox import (
    PLAIN_EXPLANATION,
    COMPACTION_GLASSBOX_RESOURCE,
    COMPACTION_GLASSBOX_SCHEMA,
    COMPACTION_GLASSBOX_SLICE,
    USAGE,
    CompactionBook,
    CompactionPanel,
    CompactionPanelRow,
    CompactionRecord,
    CompactionRegistry,
    CompactionSourceCount,
    book_record,
    build_book,
    build_panel,
    build_record,
    build_row,
    derive_panel,
    edit_record,
    format_compaction_glassbox_screen,
    format_panel,
    format_record,
    format_records,
    format_versions,
    load_compaction_glassbox,
    load_compaction_glassbox_file,
    panel_plain_words,
    panel_record,
    parse_glassbox_args,
    plain_words,
    record_from_archived,
    record_record,
    validate_book,
    validate_panel,
    validate_record,
    validate_row,
)

ROOT = Path(__file__).resolve().parents[1]


def _record(**overrides):
    fields = {
        "title": "A test compaction",
        "source": "context-pruner",
        "journal_ref": "journal/test#3",
        "journal_position": 3,
        "replaced": ["user: A first turn.", "assistant: A first answer."],
        "summary_versions": ["The first two turns stand archived."],
        "record_id": "compact-test",
    }
    fields.update(overrides)
    return build_record(fields)


def test_constants_and_usage():
    assert COMPACTION_GLASSBOX_SLICE == "M-151"
    assert COMPACTION_GLASSBOX_SCHEMA == "mythic.compaction_glassbox/1"
    assert COMPACTION_GLASSBOX_RESOURCE.endswith("compaction_glassbox.yaml")
    assert "/glassbox record <record-id>" in USAGE
    assert "/glassbox versions <record-id>" in USAGE
    assert "unrecoverable" in PLAIN_EXPLANATION
    raw = yaml.safe_load(
        (ROOT / "mythic_agent" / "data"
         / "compaction_glassbox.yaml").read_text(encoding="utf-8"))
    assert raw["schema"] == COMPACTION_GLASSBOX_SCHEMA
    assert raw["slice"] == "M-151"


def test_shipped_example_shape():
    book = load_compaction_glassbox()
    assert book.title == "Compaction glass-box at the M-150 slice boundary"
    assert book.record_ids() == (
        "compact-pruner-boundary", "compact-archiver-boundary",
        "compact-summarizer-boundary")
    assert book.positions() == (12, 27, 41)
    pruner = book.record_for("compact-pruner-boundary")
    assert pruner.source == "context-pruner"
    assert pruner.replaced_count == 3
    assert pruner.version_count == 1
    assert pruner.edited is False
    archiver = book.record_for("compact-archiver-boundary")
    # The archiver's material stands whole at its journal
    # reference - held by reference, never dropped.
    assert archiver.replaced == ()
    assert archiver.replaced_ref == "journal/session-boundary#27-archive"
    summarizer = book.record_for("compact-summarizer-boundary")
    # The summarizer's summary was edited: both versions
    # stand, in order, and the current one is the last.
    assert summarizer.version_count == 2
    assert summarizer.edited is True
    assert summarizer.summary_versions[0] == (
        "Two low-priority turns condensed into a recap.")
    assert summarizer.summary == summarizer.summary_versions[-1]
    assert len(book.panels) == 1
    assert book.panels[0].panel_id == "panel-m150-boundary"


def test_shipped_panel_is_pinned_and_derived():
    book = load_compaction_glassbox()
    panel = book.panels[0]
    assert validate_panel(panel, book) is panel
    derived = derive_panel(book)
    assert derived.rows == panel.rows
    assert derived.total_records == 3
    assert derived.total_replaced == 5
    assert derived.total_versions == 4
    assert [c.source for c in derived.source_counts] == [
        "context-pruner", "history-archiver", "context-summarizer"]
    assert panel.account[0] == (
        "The panel holds 3 compaction records: "
        "context-pruner 1, history-archiver 1, "
        "context-summarizer 1.")
    assert panel.account == derived.account


def test_record_validation_and_aliases():
    record = validate_record({
        "name": "Aliased compaction", "source": "history-archiver",
        "journal_ref": "journal/alias#1", "position": 1,
        "archived": ["user: One turn."],
        "summary": "One turn stands archived."})
    assert record.title == "Aliased compaction"
    assert record.journal_position == 1
    assert record.summary_versions == ("One turn stands archived.",)
    assert record.summary == "One turn stands archived."
    # A stored summary must be the versions' last.
    with pytest.raises(ValueError):
        validate_record({
            "title": "Judged", "source": "context-pruner",
            "journal_ref": "journal/j#2", "journal_position": 2,
            "replaced": ["user: One turn."],
            "summary_versions": ["First.", "Second."],
            "summary": "First."})
    # Named counts are judged against the record itself.
    with pytest.raises(ValueError):
        validate_record({
            "title": "Judged", "source": "context-pruner",
            "journal_ref": "journal/j#2", "journal_position": 2,
            "replaced": ["user: One turn."],
            "summary_versions": ["Only."], "version_count": 3})
    with pytest.raises(ValueError):
        validate_record({
            "title": "Judged", "source": "context-pruner",
            "journal_ref": "journal/j#2", "journal_position": 2,
            "replaced": ["user: One turn."],
            "summary_versions": ["Only."], "replaced_count": 9})
    # Unknown keys and missing pieces refuse.
    with pytest.raises(ValueError):
        _record(bogus_key="nope")
    with pytest.raises(ValueError):
        validate_record({
            "title": "No journal", "source": "context-pruner",
            "journal_position": 2, "replaced": ["user: One."],
            "summary_versions": ["Only."]})


def test_nothing_unrecoverable_refuses():
    # Neither the material whole nor a reference to it:
    # that forgets unrecoverably, and refuses.
    with pytest.raises(ValueError):
        build_record({
            "title": "Unrecoverable", "source": "context-pruner",
            "journal_ref": "journal/u#1", "journal_position": 1,
            "summary_versions": ["Gone."]})
    # By journal reference alone stands.
    by_ref = build_record({
        "title": "By reference", "source": "history-archiver",
        "journal_ref": "journal/u#2", "journal_position": 2,
        "replaced_ref": "journal/u#2-archive",
        "summary_versions": ["Kept at the reference."]})
    assert by_ref.replaced == ()
    assert by_ref.replaced_ref == "journal/u#2-archive"


def test_edit_record_appends_and_keeps_every_version():
    record = _record()
    edited = edit_record(record, "A sharper summary of the first turns.")
    assert edited.summary_versions == (
        "The first two turns stand archived.",
        "A sharper summary of the first turns.")
    assert edited.summary == "A sharper summary of the first turns."
    assert edited.record_id == record.record_id
    # The record itself is frozen data: untouched.
    assert record.version_count == 1
    edited_twice = edit_record(edited, "A third telling of the first turns.")
    assert edited_twice.version_count == 3
    assert edited_twice.summary_versions[0] == (
        "The first two turns stand archived.")
    # An edit that changes nothing is no version.
    with pytest.raises(ValueError):
        edit_record(record, "The first two turns stand archived.")
    # A repeated consecutive version refuses at construction.
    with pytest.raises(ValueError):
        _record(summary_versions=["Same.", "Same."])


def test_row_is_derived_and_judged():
    record = _record()
    row = build_row(record)
    assert row.record_id == "compact-test"
    assert row.replaced_count == 2
    assert row.version_count == 1
    assert row.summary == record.summary
    assert validate_row(row, record) is row
    tampered = build_row({
        "record_id": "compact-test", "title": record.title,
        "source": record.source, "journal_ref": record.journal_ref,
        "journal_position": record.journal_position,
        "replaced_count": 2, "version_count": 1,
        "summary": "A summary the record never held."})
    with pytest.raises(ValueError):
        validate_row(tampered, record)


def test_derive_panel_orders_by_journal_and_counts():
    later = _record(
        record_id="compact-later", journal_position=9,
        journal_ref="journal/test#9")
    earlier = _record(
        record_id="compact-earlier", journal_position=4,
        journal_ref="journal/test#4",
        summary_versions=["First telling.", "Edited telling."])
    panel = derive_panel([later, earlier])
    # Journal order, not held order.
    assert [r.record_id for r in panel.rows] == [
        "compact-earlier", "compact-later"]
    assert panel.total_records == 2
    assert panel.total_replaced == 4
    assert panel.total_versions == 3
    assert "1 of them carries an edited summary" in panel.account[2]


def test_panel_internal_inconsistency_refuses():
    record = _record()
    row = build_row(record)
    later = _record(
        record_id="compact-later", journal_position=9,
        journal_ref="journal/test#9")
    later_row = build_row(later)
    account = derive_panel([record, later]).account
    counts = [CompactionSourceCount(source="context-pruner", records=2)]
    # Rows out of journal order refuse.
    with pytest.raises(ValueError):
        CompactionPanel(
            rows=(later_row, row), total_records=2, total_replaced=4,
            total_versions=2, source_counts=counts, account=account)
    # A total that is not the rows' own refuses.
    with pytest.raises(ValueError):
        CompactionPanel(
            rows=(row, later_row), total_records=2, total_replaced=99,
            total_versions=2, source_counts=counts, account=account)
    # Two rows at one journal position refuse.
    clash = _record(
        record_id="compact-clash", journal_position=3,
        journal_ref="journal/test#3b")
    with pytest.raises(ValueError):
        derive_panel([record, clash])


def test_validate_panel_judged_against_its_source():
    book = load_compaction_glassbox()
    panel = derive_panel(book)
    assert validate_panel(panel, book) is panel
    def _stored_row(row):
        stored = row.to_record()
        stored.pop("type")
        stored.pop("slice")
        return stored

    stale = build_panel({
        "rows": [_stored_row(r) for r in panel.rows],
        "total_records": 3, "total_replaced": 5, "total_versions": 4,
        "source_counts": [c.to_record() for c in panel.source_counts],
        "account": list(panel.account)})
    assert validate_panel(stale, book) == stale
    tampered_rows = [_stored_row(r) for r in panel.rows]
    tampered_rows[0]["summary"] = "A summary no record holds."
    with pytest.raises(ValueError):
        validate_panel({
            "rows": tampered_rows, "total_records": 3,
            "total_replaced": 5, "total_versions": 4,
            "source_counts": [c.to_record() for c in panel.source_counts],
            "account": list(panel.account)}, book)


def test_book_validation_refusals():
    with pytest.raises(ValidationError):
        validate_book({"schema": "mythic.other/1", "guide": {"title": "T"},
                       "records": [_record().to_record()]})
    base = _record()
    dupe_id = _record(journal_position=8, journal_ref="journal/test#8")
    with pytest.raises((ValidationError, ValueError)):
        build_book({"title": "Dupes", "records": [base, dupe_id]})
    dupe_position = _record(
        record_id="compact-other", journal_ref="journal/test#3b")
    with pytest.raises((ValidationError, ValueError)):
        build_book({"title": "Dupes", "records": [base, dupe_position]})
    with pytest.raises(ValidationError):
        validate_book({
            "schema": COMPACTION_GLASSBOX_SCHEMA,
            "guide": {"title": "T"}, "records": [], "bogus": 1})


def test_load_compaction_glassbox_file_roundtrip(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "compaction_glassbox.yaml").read_text(encoding="utf-8")
    path = tmp_path / "compaction_glassbox.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_compaction_glassbox_file(path)
    assert book.title == "Compaction glass-box at the M-150 slice boundary"
    assert book.record_ids()[0] == "compact-pruner-boundary"
    with pytest.raises(FileNotFoundError):
        load_compaction_glassbox_file(tmp_path / "nope.yaml")


def test_registry_holds_records_one_by_one():
    registry = CompactionRegistry()
    held = registry.register_record({
        "title": "Held one", "source": "context-pruner",
        "journal_ref": "journal/held#1", "journal_position": 1,
        "replaced": ["user: One."], "summary_versions": ["One held."]})
    assert held.record_id == "compact-1"
    with pytest.raises(ValueError):
        registry.register_record(held)
    with pytest.raises(ValueError):
        registry.register_record({
            "title": "Same place", "source": "context-pruner",
            "journal_ref": "journal/held#1b", "journal_position": 1,
            "replaced": ["user: Two."], "summary_versions": ["Two."]})
    with pytest.raises(KeyError):
        registry.get_record("compact-nope")


def test_registry_book_title_panel_and_edit():
    registry = CompactionRegistry()
    book = registry.register_book(load_compaction_glassbox())
    assert book.title == "Compaction glass-box at the M-150 slice boundary"
    assert registry.panel().total_records == 3
    edited = registry.edit_summary(
        "compact-pruner-boundary", "An edited telling of the first pass.")
    assert edited.version_count == 2
    assert edited.summary_versions[0].startswith("The opening turns")
    # The edit keeps the record's held place and id.
    assert [r.record_id for r in registry.list_records()] == [
        "compact-pruner-boundary", "compact-archiver-boundary",
        "compact-summarizer-boundary"]
    assert registry.panel().total_versions == 5
    with pytest.raises(KeyError):
        registry.edit_summary("compact-nope", "Nothing.")
    with pytest.raises(ValueError):
        registry.register_book(build_book({
            "title": "Another book",
            "records": [_record(record_id="compact-fresh",
                                 journal_position=99,
                                 journal_ref="journal/test#99")]}))


def test_record_from_archived_live_shape():
    record = record_from_archived(
        [{"role": "user", "content": "Name the task."},
         {"role": "assistant", "content": "The task is named."},
         "a bare note"],
        title="From the pruner", source="context-pruner",
        journal_ref="journal/live#5", journal_position=5,
        record_id="compact-live")
    assert record.replaced == (
        "user: Name the task.", "assistant: The task is named.",
        "a bare note")
    assert record.summary == "Archived 3 earlier messages beside journal/live#5."
    with pytest.raises(ValueError):
        record_from_archived(
            [{"role": "user"}],
            title="Broken", source="context-pruner",
            journal_ref="journal/live#6", journal_position=6)


def test_token_figures_are_derived():
    from mythic_agent.context.budget import TokenEstimator
    estimator = TokenEstimator(prefer_tiktoken=False)
    record = _record()
    assert record.replaced_tokens == sum(
        estimator.count(piece) for piece in record.replaced)
    assert record.summary_tokens == estimator.count(record.summary)
    by_ref = build_record({
        "title": "By reference", "source": "history-archiver",
        "journal_ref": "journal/t#1", "journal_position": 1,
        "replaced_ref": "journal/t#1-archive",
        "summary_versions": ["Kept elsewhere."]})
    # Held by reference: the material stands in the journal,
    # so this record itself counts no replaced tokens.
    assert by_ref.replaced_tokens == 0


def test_records_and_plain_words():
    record = _record()
    news = record_record(record)
    assert news["type"] == "compaction_glassbox_record"
    assert news["news"] is True
    assert "summary version 1 shown" in news["headline"]
    panel_news = panel_record(derive_panel([record]))
    assert panel_news["type"] == "compaction_glassbox_panel"
    assert "all recoverable" in panel_news["headline"]
    book_news = book_record(load_compaction_glassbox())
    assert book_news["type"] == "compaction_glassbox_book"
    assert book_news["record_count"] == 3
    assert "2 pieces kept whole" in plain_words(record)
    by_ref = build_record({
        "title": "By reference", "source": "history-archiver",
        "journal_ref": "journal/t#1", "journal_position": 1,
        "replaced_ref": "journal/t#1-archive",
        "summary_versions": ["Kept elsewhere."]})
    assert "kept at journal/t#1-archive" in plain_words(by_ref)
    told = panel_plain_words(load_compaction_glassbox())
    assert "in journal order" in told
    assert "nothing the coder forgets is unrecoverable" in told


def test_formatters_and_screen():
    book = load_compaction_glassbox()
    line = format_record(book.records[0])
    assert line.startswith("compact-pruner-boundary: The pruner's first pass")
    all_lines = format_records(book)
    assert "compact-summarizer-boundary" in all_lines
    only_archiver = format_records(book, "history-archiver")
    assert "compact-archiver-boundary" in only_archiver
    assert "compact-pruner-boundary" not in only_archiver
    versions = format_versions(book.record_for("compact-summarizer-boundary"))
    assert "v1: Two low-priority turns condensed into a recap." in versions
    assert "v2 (current):" in versions
    panel_text = format_panel(book)
    assert "Panel in Compaction glass-box" in panel_text
    screen = format_compaction_glassbox_screen(book)
    assert "Compaction Glass-Box (M-151)" in screen
    assert USAGE in screen


def test_parse_glassbox_args_grammar():
    assert parse_glassbox_args("") == ("show", None)
    assert parse_glassbox_args("show") == ("show", None)
    assert parse_glassbox_args("list") == ("show", None)
    assert parse_glassbox_args("panel") == ("panel", None)
    assert parse_glassbox_args("record compact-x") == ("record", "compact-x")
    assert parse_glassbox_args("versions compact-x") == (
        "versions", "compact-x")
    for bad in ("dance", "record", "versions a b", "panel now", "record "):
        with pytest.raises(ValueError):
            parse_glassbox_args(bad)
    with pytest.raises(ValueError):
        parse_glassbox_args(None if False else 42)


def test_honest_boundary_module_imports_no_live_roads():
    source = (ROOT / "mythic_agent" / "core"
              / "compaction_glassbox.py").read_text(encoding="utf-8")
    # The pure layer composes the shipped context
    # budget road by import, and imports no agent,
    # ui or terminal code: holding a record can
    # compact no live context from here.
    assert "from ..context.budget import TokenEstimator" in source
    assert "from ..agents" not in source
    assert "from ..ui" not in source
    assert "from ..terminal" not in source
    assert "import agents" not in source


# -- agent layer -----------------------------------------------------------
#
# M-151 agent layer: the agent holds a
# CompactionRegistry for the session (session state
# only, no new setting), records are held by being
# registered - published as their record_record
# session news with the derived panel_record,
# through the checkpoint road, deduped per shape,
# with an edited summary announcing again under its
# new version count - the report road renders the
# held book (or the shipped example when unheld)
# through the pure formatters, and the /glassbox
# surface rides both roads on the pure parser +
# formatters. Status, get, source and panel reads
# register and publish nothing, answer from the held
# registry first and from the shipped example only
# while nothing is held - a held session never falls
# back to the example. The panel derives at call
# time from the held records, never held. This layer
# compacts no live context, and there is no Part
# VIII board yet, so the screen is where the glass
# box is visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _glassbox_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_glassbox_book(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "compaction_glassbox.yaml").read_text(encoding="utf-8")
    path = tmp_path / "compaction_glassbox.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestCompactionGlassboxAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.compaction_glassbox_status()
        assert status["records"] == []
        assert status["book"] is None
        assert status["compaction_glassbox"]["title"] == (
            "Compaction glass-box at the M-150 slice boundary")
        assert len(status["compaction_glassbox"]["records"]) == 3
        assert status["panel"]["total_records"] == 3
        assert status["panel"]["total_replaced"] == 5
        assert status["book_record"]["record_count"] == 3
        assert "Compaction Glass-Box (M-151)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._compaction_glassbox_registry()
        assert agent._compaction_glassbox_registry() is first
        assert agent._compaction_glassbox_store is first

    def test_reads_register_and_publish_nothing(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.compaction_glassbox_status()
        agent.get_compaction_record("compact-pruner-boundary")
        agent.compaction_records_for_source("context-pruner")
        agent.compaction_glassbox_panel()
        agent.report_compaction_glassbox()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("compaction_glassbox")] == []
        agent.close()

    def test_unheld_reads_raise(self, agent):
        with pytest.raises(KeyError):
            agent.get_compaction_record("compact-nope")

    def test_status_after_register_shows_the_held_pieces(self, agent):
        agent.register_compaction_record(_record())
        status = agent.compaction_glassbox_status()
        assert [r["record_id"] for r in status["records"]] == ["compact-test"]
        assert status["book"]["title"] == "Session compaction glass-box"
        assert status["panel"]["total_records"] == 1
        assert status["panel"]["rows"][0]["source"] == "context-pruner"

    def test_held_session_never_falls_back_to_the_example(self, agent):
        agent.register_compaction_record(_record())
        with pytest.raises(KeyError):
            agent.get_compaction_record("compact-pruner-boundary")
        assert agent.compaction_records_for_source("history-archiver") == ()
        assert [r.record_id for r in
                agent.compaction_records_for_source("context-pruner")] == [
                    "compact-test"]
        assert agent.compaction_glassbox_book().title == (
            "Session compaction glass-box")


class TestCompactionGlassboxAgentHolding:
    def test_register_record_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_compaction_record(_record())
        assert outcome["record"]["record_id"] == "compact-test"
        assert outcome["record_news"]["type"] == "compaction_glassbox_record"
        assert outcome["panel_record"]["type"] == (
            "compaction_glassbox_panel")
        events = _glassbox_events(
            store, session_id, "compaction_glassbox_record")
        assert len(events) == 1
        assert events[0]["record_id"] == "compact-test"
        panels = _glassbox_events(
            store, session_id, "compaction_glassbox_panel")
        assert len(panels) == 1
        assert panels[0]["total_records"] == 1
        agent._publish_compaction_glassbox_record(outcome["record_news"])
        agent._publish_compaction_glassbox_record(outcome["panel_record"])
        assert len(_glassbox_events(
            store, session_id, "compaction_glassbox_record")) == 1
        assert len(_glassbox_events(
            store, session_id, "compaction_glassbox_panel")) == 1
        from mythic_agent.core.context_budget import (
            book_record as _budget_book_record, load_context_budget)
        agent._publish_compaction_glassbox_record(
            {"type": "mentions_mention", "mention_id": "mention-x"})
        agent._publish_compaction_glassbox_record(
            _budget_book_record(load_context_budget()))
        agent._publish_compaction_glassbox_record(
            book_record(load_compaction_glassbox()))
        for kind in ("mentions_mention", "context_budget_book",
                     "compaction_glassbox_book"):
            assert _glassbox_events(store, session_id, kind) == []
        agent.close()

    def test_register_record_without_id_gets_a_compact_id(self, agent):
        outcome = agent.register_compaction_record({
            "title": "Unnamed compaction", "source": "context-pruner",
            "journal_ref": "journal/auto#1", "journal_position": 1,
            "replaced": ["user: One."],
            "summary_versions": ["One archived."]})
        assert outcome["record"]["record_id"] == "compact-1"

    def test_duplicate_record_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_compaction_record(_record())
        with pytest.raises(ValueError):
            agent.register_compaction_record(_record())
        assert len(_glassbox_events(
            store, session_id, "compaction_glassbox_record")) == 1
        agent.close()

    def test_edit_summary_holds_every_version_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_compaction_record(_record())
        outcome = agent.edit_compaction_summary(
            "compact-test", "A sharper summary of the first turns.")
        assert outcome["record"]["version_count"] == 2
        assert outcome["record"]["summary_versions"][0] == (
            "The first two turns stand archived.")
        assert outcome["record"]["summary"] == (
            "A sharper summary of the first turns.")
        # The edit is a new version of the record, and
        # announces again under its new version count.
        events = _glassbox_events(
            store, session_id, "compaction_glassbox_record")
        assert len(events) == 2
        assert events[-1]["version_count"] == 2
        held = agent.get_compaction_record("compact-test")
        assert held.version_count == 2
        with pytest.raises(KeyError):
            agent.edit_compaction_summary("compact-nope", "Nothing.")
        with pytest.raises(ValueError):
            agent.edit_compaction_summary(
                "compact-test", "A sharper summary of the first turns.")
        agent.close()

    def test_register_book_holds_and_publishes_in_order(self, agent):
        book = build_book({
            "title": "A held glass box",
            "records": [
                {"title": "First held", "source": "context-pruner",
                 "journal_ref": "journal/held#1", "journal_position": 1,
                 "replaced": ["user: One."],
                 "summary_versions": ["One archived."],
                 "record_id": "held-first"},
                {"title": "Second held", "source": "history-archiver",
                 "journal_ref": "journal/held#2", "journal_position": 2,
                 "replaced_ref": "journal/held#2-archive",
                 "summary_versions": ["Two archived."],
                 "record_id": "held-second"}]})
        outcome = agent.register_compaction_glassbox_book(book)
        assert outcome["count"] == 2
        assert [r["record_id"] for r in outcome["records_news"]] == [
            "held-first", "held-second"]
        assert agent.compaction_glassbox_book().title == "A held glass box"

    def test_register_book_twice_refuses(self, agent):
        agent.register_compaction_glassbox_book(load_compaction_glassbox())
        with pytest.raises(ValueError):
            agent.register_compaction_glassbox_book(
                load_compaction_glassbox())

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_compaction_glassbox_book()
        assert outcome["count"] == 3
        assert outcome["book"]["title"] == (
            "Compaction glass-box at the M-150 slice boundary")
        assert len(_glassbox_events(
            store, session_id, "compaction_glassbox_record")) == 3
        assert agent.compaction_glassbox_book().panels[0].panel_id == (
            "panel-m150-boundary")
        agent.close()

    def test_record_same_book_twice_refuses(self, agent):
        agent.record_compaction_glassbox_book()
        with pytest.raises(ValueError):
            agent.record_compaction_glassbox_book()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_glassbox_book(tmp_path)
        book = load_compaction_glassbox_file(path)
        outcome = agent.record_compaction_glassbox_book(book)
        assert outcome["count"] == 3
        assert agent.get_compaction_record(
            "compact-archiver-boundary").replaced_ref == (
                "journal/session-boundary#27-archive")

    def test_one_by_one_holdings_stand_under_a_session_book(self, agent):
        agent.register_compaction_record(_record())
        agent.register_compaction_record({
            "title": "Another compaction", "source": "context-summarizer",
            "journal_ref": "journal/test#7", "journal_position": 7,
            "replaced": ["user: An aside."],
            "summary_versions": ["An aside condensed."],
            "record_id": "compact-test-two"})
        book = agent.compaction_glassbox_book()
        assert book.title == "Session compaction glass-box"
        assert [r.record_id for r in book.records] == [
            "compact-test", "compact-test-two"]
        panel = agent.compaction_glassbox_panel()
        # Journal order: position 3 before position 7.
        assert [r.record_id for r in panel.rows] == [
            "compact-test", "compact-test-two"]

    def test_report_renders_the_example_when_unheld(self, agent):
        report = agent.report_compaction_glassbox()
        assert report["book"]["record_count"] == 3
        assert "compact-pruner-boundary" in report["records_text"]
        assert "Panel in Compaction glass-box" in report["panel_text"]

    def test_report_renders_the_held_book_only(self, agent):
        agent.register_compaction_record(_record())
        report = agent.report_compaction_glassbox()
        assert report["book"]["title"] == "Session compaction glass-box"
        assert "compact-pruner-boundary" not in report["records_text"]
        assert "compact-test" in report["records_text"]

    def test_report_registers_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.report_compaction_glassbox()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("compaction_glassbox")] == []
        agent.close()

    def test_no_live_compact_or_persist_road(self, agent):
        # This layer holds compactions as data: it
        # compacts no live context, calls no model,
        # archives no message and persists nothing -
        # and there is no Part VIII board yet. Holding
        # or editing a record changes no live context:
        # the agent's own messages and a
        # ContextBuilder's built messages are the same
        # before and after.
        assert not hasattr(agent, "apply_compaction_glassbox")
        assert not hasattr(agent, "compact_compaction_glassbox")
        assert not hasattr(agent, "persist_compaction_glassbox")
        assert not hasattr(agent, "compaction_glassbox_board")
        messages_before = list(agent.messages)
        from mythic_agent.agents.context import ContextBuilder
        builder = ContextBuilder(max_tokens=4000)
        builder.add_system("You are the coder.")
        builder.add_turn("user", "Build the slice.")
        before = builder.build()
        agent.record_compaction_glassbox_book()
        agent.edit_compaction_summary(
            "compact-pruner-boundary", "An edited first-pass summary.")
        assert builder.build() == before
        assert list(agent.messages) == messages_before


class TestCompactionGlassboxTerminalSurface:
    def test_show_record_versions_and_panel(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/glassbox")
        assert "Compaction Glass-Box (M-151)" in text
        _, _, text = _slash(agent, "/glassbox record compact-pruner-boundary")
        assert "compact-pruner-boundary: The pruner's first pass" in text
        _, _, text = _slash(
            agent, "/glassbox versions compact-summarizer-boundary")
        assert "v1: Two low-priority turns condensed into a recap." in text
        assert "v2 (current):" in text
        _, _, text = _slash(agent, "/glassbox panel")
        assert "Panel in Compaction glass-box" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/glassbox [show|record <record-id>|"
                "versions <record-id>|panel]") in text
        _, _, text = _slash(agent, "/glassbox dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/glassbox record compact-nope")
        assert "no record in the book" in text


@pytest.fixture()
def glassbox_handler(agent, monkeypatch):
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


def _glassbox_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestCompactionGlassboxCommand:
    def test_show_is_default(self, glassbox_handler, agent):
        glassbox_handler._handle_glassbox("")
        assert "Compaction Glass-Box (M-151)" in (
            _glassbox_published_text(glassbox_handler))

    def test_record_versions_and_panel(self, glassbox_handler, agent):
        glassbox_handler._handle_glassbox("record compact-pruner-boundary")
        assert "The pruner's first pass" in _glassbox_published_text(
            glassbox_handler)
        glassbox_handler._handle_glassbox(
            "versions compact-summarizer-boundary")
        text = _glassbox_published_text(glassbox_handler)
        assert "v2 (current):" in text
        glassbox_handler._handle_glassbox("panel")
        assert "Panel in Compaction glass-box" in _glassbox_published_text(
            glassbox_handler)

    def test_bad_grammar_is_published(self, glassbox_handler, agent):
        glassbox_handler._handle_glassbox("dance party")
        assert USAGE in _glassbox_published_text(glassbox_handler)


class TestChatScreenRoutingCompactionGlassbox:
    def test_glassbox_routes_as_system_command(self, monkeypatch):
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
            "/glassbox record compact-pruner-boundary", _FakeLog())
        assert calls == [("/glassbox", "record compact-pruner-boundary")]
