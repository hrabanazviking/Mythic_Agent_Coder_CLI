"""M-162 Multi-session per project - pure-layer tests.

TIER: integration

The pure layer is the parallel session itself, held
as data: one session standing on one project, on
its own branch, under its own journal, carried with
its provenance whole (the project, the branch, the
session and journal it stands under, its state, the
journal entries that are its own, how many shared
memory-map entries it has read, who recorded it,
the day, and where it was read from), composed by
import from the shipped holdings it stands beside
(session memory, M-153, the project memory map,
M-150, cross-project memory, M-154, and long-session
endurance, M-161), each judged by its own layer's
validation, a multi-session panel derived from the
whole book in settled order, an isolation verdict
derived for the whole book - no journal crosstalk,
ever - the shipped example book held in a data
file, and a loader that reads a book from any file.
Nothing here spawns a live session, appends to a
live journal, calls a model or writes any project's
files: holding a session declares a standing, and
that is the whole road.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.cross_project_memory import load_cross_project_memory
from mythic_agent.core.long_session_endurance import load_long_session_endurance
from mythic_agent.core.project_memory_map import load_project_memory_map
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.session_memory import load_session_memory
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.multi_session_projects import (
    MULTI_SESSION_PROJECTS_RESOURCE,
    MULTI_SESSION_PROJECTS_SCHEMA,
    MULTI_SESSION_PROJECTS_SLICE,
    PLAIN_EXPLANATION,
    SESSION_STATES,
    USAGE,
    IsolationVerdict,
    MultiSessionBook,
    MultiSessionPanel,
    MultiSessionPanelRow,
    MultiSessionRegistry,
    ParallelSession,
    SessionStateCount,
    book_record,
    build_book,
    build_isolation,
    build_panel,
    build_row,
    build_session,
    derive_isolation,
    derive_panel,
    format_isolation,
    format_multi_session_projects_screen,
    format_panel,
    format_parallel_session,
    format_parallel_sessions,
    inspect_parallel_source,
    isolation_plain_words,
    isolation_record,
    load_multi_session_projects,
    load_multi_session_projects_file,
    multi_session_refs,
    normalize_session_state,
    panel_plain_words,
    panel_record,
    parallel_from_endurance_record,
    parallel_from_map_entry,
    parallel_from_session_situation,
    parallel_from_shared_lesson,
    parallel_record,
    parallel_sessions_from_session_memory,
    parse_multisession_args,
    plain_words,
    total_journal_entries,
    validate_book,
    validate_isolation,
    validate_panel,
    validate_row,
    validate_session,
)

ROOT = Path(__file__).resolve().parents[1]

EXAMPLE_TITLE = "Multi-session per project at the M-161 slice boundary"

BY = "Volmarr"
ON = "2026-11-08"


def _session(**overrides):
    fields = {
        "session_id": "multisession-test",
        "title": "the test session, wiring the parser",
        "project": "mythic-agent-coder",
        "branch": "work/parser-wiring",
        "session_ref": "session-test",
        "journal_ref": "journal-test",
        "state": "active",
        "journal_entries": ["entry-test-1", "entry-test-2"],
        "shared_reads": 3,
        "recorded_by": BY,
        "recorded_on": ON,
        "source": "test source",
    }
    fields.update(overrides)
    return build_session(fields)


def _stored_session(session):
    stored = session.to_record()
    for key in ("type", "slice", "journal_count"):
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


def _stored_isolation(verdict):
    stored = verdict.to_record()
    stored.pop("type")
    stored.pop("slice")
    return stored


def _book(sessions=None, **overrides):
    fields = {
        "title": "A test multi-session book",
        "sessions": [_stored_session(item) for item in (
            sessions if sessions is not None else [_session()])],
    }
    fields.update(overrides)
    return build_book(fields)


def _shipped_raw():
    path = ROOT / "mythic_agent" / "data" / "multi_session_projects.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_constants_and_usage():
    assert MULTI_SESSION_PROJECTS_SLICE == "M-162"
    assert MULTI_SESSION_PROJECTS_SCHEMA == "mythic.multi_session_projects/1"
    assert MULTI_SESSION_PROJECTS_RESOURCE == "multi_session_projects.yaml"
    assert SESSION_STATES == ("active", "paused", "done")
    assert "different branches" in PLAIN_EXPLANATION
    assert "shared memory map" in PLAIN_EXPLANATION
    assert "no journal crosstalk" in PLAIN_EXPLANATION
    assert "spawns no live session" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /multisession")
    assert "session <session-id>" in USAGE


def test_roadmap_boundary_is_derived_from_the_shipped_roadmap():
    road = load_roadmap()
    ids = [item.id for item in road.slices]
    assert "M-162" in ids
    mine = road.slices[ids.index("M-162")]
    assert mine.title == "Multi-session per project"
    assert mine.part == 7
    assert "parallel sessions on one repo" in mine.summary
    assert "shared memory map" in mine.summary
    assert "no journal crosstalk" in mine.summary
    for earlier in road.slices[:ids.index("M-162")]:
        assert earlier.status == "done", earlier.id


def test_shipped_example_shape():
    book = load_multi_session_projects()
    assert isinstance(book, MultiSessionBook)
    assert book.title == EXAMPLE_TITLE
    assert book.session_ids() == (
        "multisession-main", "multisession-memory",
        "multisession-graph", "multisession-thrift")
    assert book.total_sessions == 4
    assert book.project == "mythic-agent-coder"
    first = book.sessions[0]
    assert first.title == (
        "the endurance session, carried forward on the main line")
    assert first.branch == "main"
    assert first.state == "active"
    assert first.journal_count == 2
    assert first.recorded_by == "Volmarr"
    assert first.recorded_on == "2026-11-08"
    assert len(book.panels) == 1


def test_shipped_panel_is_pinned_and_derived():
    book = load_multi_session_projects()
    panel = book.panel_for("panel-m161-boundary")
    derived = derive_panel(book)
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert [row.session_id for row in panel.rows] == [
        "multisession-main", "multisession-memory",
        "multisession-graph", "multisession-thrift"]
    assert panel.total_sessions == 4
    assert panel.total_journal_entries == 8
    assert panel.total_shared_reads == 19


def test_shipped_isolation_proves_no_crosstalk():
    book = load_multi_session_projects()
    verdict = derive_isolation(book)
    assert verdict.verdict == "parallel-isolated"
    assert verdict.distinct_journals == 4
    assert verdict.distinct_branches == 4
    assert verdict.total_journal_entries == 8
    assert total_journal_entries(book) == 8
    entries = [entry for session in book.sessions
               for entry in session.journal_entries]
    assert len(entries) == len(set(entries))


def test_normalizers_and_aliases():
    assert normalize_session_state("Running") == "active"
    assert normalize_session_state("LIVE") == "active"
    assert normalize_session_state("held") == "paused"
    assert normalize_session_state("Waiting") == "paused"
    assert normalize_session_state("finished") == "done"
    assert normalize_session_state("CLOSED") == "done"
    with pytest.raises(ValueError):
        normalize_session_state("sleeping")
    with pytest.raises(ValueError):
        _session(branch="work/bad branch")
    with pytest.raises(ValueError):
        _session(branch="/leading-slash")
    with pytest.raises(ValueError):
        _session(branch="double//slash")


def test_session_validation_and_alias_spellings():
    session = _session()
    assert isinstance(session, ParallelSession)
    assert session.journal_count == 2
    aliased = build_session({
        "name": "the aliased session", "project": "other-project",
        "branch": "work/alias", "session": "session-alias",
        "journal": "journal-alias", "status": "held",
        "entries": ["entry-alias-1"], "reads": 1,
        "by": "Volmarr", "day": "2026-11-08",
        "source": "the alias test"})
    assert aliased.title == "the aliased session"
    assert aliased.state == "paused"
    assert aliased.session_ref == "session-alias"
    assert aliased.journal_entries == ("entry-alias-1",)
    with pytest.raises(ValueError):
        build_session({"title": "the bare standing"})
    with pytest.raises(ValueError):
        _session(recorded_on="08/11/2026")
    with pytest.raises(ValueError):
        _session(recorded_on="2026-13-01")
    with pytest.raises(ValueError):
        _session(state="sleeping")


def test_session_refuses_missing_provenance():
    fields = _stored_session(_session())
    fields.pop("recorded_by")
    with pytest.raises(ValueError, match="missing its"):
        build_session(fields)
    fields = _stored_session(_session())
    fields.pop("source")
    with pytest.raises(ValueError, match="missing its"):
        build_session(fields)
    fields = _stored_session(_session())
    fields["bogus"] = "nope"
    with pytest.raises(ValueError, match="unknown parallel-session keys"):
        build_session(fields)


def test_session_refuses_journal_problems():
    with pytest.raises(ValueError, match="at least one journal"):
        _session(journal_entries=[])
    with pytest.raises(ValueError, match="twice"):
        _session(journal_entries=["entry-test-1", "entry-test-1"])
    fields = _stored_session(_session())
    fields.pop("journal_entries")
    with pytest.raises(ValueError, match="missing its journal entries"):
        build_session(fields)
    fields = _stored_session(_session())
    fields.pop("branch")
    with pytest.raises(ValueError, match="missing its branch"):
        build_session(fields)


def test_book_refuses_duplicates_and_crosstalk():
    with pytest.raises(ValueError, match="already exists"):
        _book([_session(), _session(title="another title")])
    with pytest.raises(ValueError, match="already stands"):
        _book([_session(), _session(
            session_id="multisession-copy", title="the copy session",
            branch="work/copy", journal_ref="journal-copy",
            journal_entries=["entry-copy-1"])])
    # Different branches is the law: a second session
    # on a held branch refuses under any other id.
    with pytest.raises(ValueError, match="different branches"):
        _book([_session(), _session(
            session_id="multisession-copy", session_ref="session-copy",
            journal_ref="journal-copy",
            journal_entries=["entry-copy-1"])])
    # Every session stands under its own journal.
    with pytest.raises(ValueError, match="its own journal"):
        _book([_session(), _session(
            session_id="multisession-copy", session_ref="session-copy",
            branch="work/copy", journal_entries=["entry-copy-1"])])
    # No crosstalk: one entry in two sessions refuses.
    with pytest.raises(ValueError, match="crosstalk"):
        _book([_session(), _session(
            session_id="multisession-copy", session_ref="session-copy",
            branch="work/copy", journal_ref="journal-copy",
            journal_entries=["entry-test-1"])])
    # One project: a session of another project refuses.
    with pytest.raises(ValueError, match="one project"):
        _book([_session(), _session(
            session_id="multisession-copy", session_ref="session-copy",
            branch="work/copy", journal_ref="journal-copy",
            journal_entries=["entry-copy-1"], project="other-project")])
    # Distinct standings on distinct branches with
    # distinct journals and entries stand together.
    book = _book([_session(), _session(
        session_id="multisession-second", session_ref="session-second",
        branch="work/second", journal_ref="journal-second",
        journal_entries=["entry-second-1"], state="paused")])
    assert book.total_sessions == 2


def test_session_for_branch_in_book():
    book = load_multi_session_projects()
    session = book.session_for_branch("main")
    assert session.session_id == "multisession-main"
    assert isinstance(
        book.session_for("multisession-graph"), ParallelSession)
    with pytest.raises(KeyError):
        book.session_for_branch("work/nope")
    with pytest.raises(KeyError):
        book.session_for("multisession-nope")


def test_composition_from_session_situation():
    situation = load_session_memory().situations[0]
    session = parallel_from_session_situation(
        situation, project="mythic-agent-coder", branch="work/graph-care",
        journal_ref="journal-graph-care",
        journal_entries=["entry-graph-care-1"],
        recorded_by=BY, recorded_on=ON)
    assert session.session_ref == situation.session_ref
    assert session.shared_reads == situation.total_memory
    assert session.branch == "work/graph-care"
    blob = str(session.to_record())
    assert situation.title not in blob
    assert situation.workspace not in blob
    with pytest.raises(ValueError, match="branch"):
        parallel_from_session_situation(
            situation, project="mythic-agent-coder", branch=None,
            journal_ref="journal-x", journal_entries=["entry-x-1"],
            recorded_by=BY, recorded_on=ON)


def test_composition_from_map_entry():
    entry = load_project_memory_map().entries[0]
    session = parallel_from_map_entry(
        entry, project="mythic-agent-coder", branch="work/map-care",
        session_ref="session-map-care", journal_ref="journal-map-care",
        journal_entries=["entry-map-care-1"],
        recorded_by=BY, recorded_on=ON)
    assert session.shared_reads == 1
    assert session.session_ref == "session-map-care"
    blob = str(session.to_record())
    assert entry.title not in blob
    assert entry.detail not in blob


def test_composition_from_shared_lesson():
    lesson = load_cross_project_memory().lessons[0]
    session = parallel_from_shared_lesson(
        lesson, branch="work/lesson-care", session_ref="session-lesson",
        journal_ref="journal-lesson", journal_entries=["entry-lesson-1"],
        recorded_by=BY, recorded_on=ON)
    assert session.project == lesson.source_project
    assert session.shared_reads == 1
    blob = str(session.to_record())
    assert lesson.title not in blob
    assert lesson.detail not in blob
    assert lesson.context not in blob


def test_composition_from_endurance_record():
    record = load_long_session_endurance().records[0]
    session = parallel_from_endurance_record(
        record, project="mythic-agent-coder", branch="work/endurance-care",
        journal_ref="journal-endurance-care",
        journal_entries=["entry-endurance-care-1"])
    assert session.session_ref == record.ref
    assert session.recorded_by == record.recorded_by
    assert session.recorded_on == record.recorded_on
    blob = str(session.to_record())
    assert record.subject not in blob
    with pytest.raises(ValueError, match="journal"):
        parallel_from_endurance_record(
            record, project="mythic-agent-coder", branch="work/x",
            journal_ref=None, journal_entries=["entry-x-1"])


def test_inspect_parallel_source():
    situation = load_session_memory().situations[0]
    seen = inspect_parallel_source(situation)
    assert seen == {"session_ref": situation.session_ref,
                    "journal_count": None,
                    "shared_reads": situation.total_memory}
    entry = load_project_memory_map().entries[0]
    seen = inspect_parallel_source(entry)
    assert seen == {"entry_ref": entry.ref, "shared_reads": 1}
    seen = inspect_parallel_source(_session())
    assert seen == {"session_ref": "session-test", "journal_count": 2,
                    "shared_reads": 3}
    with pytest.raises(ValueError, match="no shipped layer owns"):
        inspect_parallel_source(42)


def test_sessions_from_session_memory_plural_road():
    memory_book = load_session_memory()
    sessions = parallel_sessions_from_session_memory(
        memory_book, project="mythic-agent-coder",
        recorded_by=BY, recorded_on=ON)
    assert len(sessions) == len(memory_book.situations)
    assert sessions[0].session_ref == memory_book.situations[0].session_ref
    assert sessions[0].branch == (
        f"work/{memory_book.situations[0].session_ref}")
    assert sessions[0].journal_ref == (
        f"journal-{memory_book.situations[0].session_ref}")
    assert sessions[0].shared_reads == (
        memory_book.situations[0].total_memory)
    with pytest.raises(ValueError, match="project"):
        parallel_sessions_from_session_memory(
            memory_book, project=None, recorded_by=BY, recorded_on=ON)


def test_panel_derivation_and_order():
    book = _book([
        _session(session_id="multisession-b", title="b session",
                 branch="work/b", session_ref="session-b",
                 journal_ref="journal-b",
                 journal_entries=["entry-b-1"]),
        _session(session_id="multisession-a", title="a session",
                 branch="work/a", session_ref="session-a",
                 journal_ref="journal-a",
                 journal_entries=["entry-a-1"]),
        _session(session_id="multisession-d", title="the done session",
                 branch="work/d", session_ref="session-d",
                 journal_ref="journal-d", state="done",
                 journal_entries=["entry-d-1", "entry-d-2"]),
    ])
    panel = derive_panel(book)
    assert isinstance(panel, MultiSessionPanel)
    # State order first (active before done), then
    # branch, then title, then session id.
    assert [r.session_id for r in panel.rows] == [
        "multisession-a", "multisession-b", "multisession-d"]
    assert panel.total_sessions == 3
    assert panel.total_journal_entries == 4
    counts = {c.state: c for c in panel.state_counts}
    assert counts["active"].sessions == 2
    assert counts["done"].sessions == 1
    assert isinstance(counts["done"], SessionStateCount)
    assert panel.row_for("multisession-d").journal_count == 2
    with pytest.raises(KeyError):
        panel.row_for("multisession-nope")


def test_panel_refuses_disagreement_and_bad_rows():
    book = load_multi_session_projects()
    panel = derive_panel(book)
    stored = _stored_panel(panel)
    assert validate_panel(stored, book) == panel
    bad = _stored_panel(panel)
    bad["total_sessions"] = 3
    with pytest.raises(ValueError):
        validate_panel(bad, book)
    bad = _stored_panel(panel)
    bad["account"] = ["A different account."]
    with pytest.raises(ValueError, match="disagrees"):
        validate_panel(bad, book)
    good_row = build_row(_stored_panel(panel)["rows"][0])
    assert isinstance(good_row, MultiSessionPanelRow)
    assert validate_row(good_row, book.sessions[0]) == good_row
    bad_row = _stored_panel(panel)["rows"][0]
    bad_row["branch"] = "work/elsewhere"
    with pytest.raises(ValueError, match="disagrees"):
        validate_row(bad_row, book.sessions[0])


def test_isolation_derivation_and_validation():
    book = _book([_session(), _session(
        session_id="multisession-second", session_ref="session-second",
        branch="work/second", journal_ref="journal-second",
        journal_entries=["entry-second-1"])])
    verdict = derive_isolation(book)
    assert isinstance(verdict, IsolationVerdict)
    assert verdict.verdict == "parallel-isolated"
    assert verdict.distinct_journals == 2
    assert verdict.distinct_branches == 2
    assert validate_isolation(_stored_isolation(verdict), book) == verdict
    assert build_isolation(_stored_isolation(verdict)) == verdict
    solo = derive_isolation(_book([_session()]))
    assert solo.verdict == "single-session"
    with pytest.raises(ValueError, match="disagrees"):
        validate_isolation(_stored_isolation(solo), book)
    # A verdict claiming isolation its counts do not
    # prove refuses at construction.
    with pytest.raises(ValueError, match="isolation"):
        IsolationVerdict(
            total_sessions=2, total_journal_entries=3,
            distinct_journals=1, distinct_branches=2,
            shared_reads=3, verdict="parallel-isolated")
    with pytest.raises(ValueError, match="verdict"):
        IsolationVerdict(
            total_sessions=1, total_journal_entries=2,
            distinct_journals=1, distinct_branches=1,
            shared_reads=3, verdict="parallel-isolated")


def test_book_validation_and_loader_roads(tmp_path):
    raw = _shipped_raw()
    assert validate_book(raw).title == EXAMPLE_TITLE
    assert build_book(raw).session_ids()[0] == "multisession-main"
    bad = dict(raw)
    bad["schema"] = "mythic.other/1"
    with pytest.raises(ValidationError):
        validate_book(bad)
    path = tmp_path / "multi_session.yaml"
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    loaded = load_multi_session_projects_file(path)
    assert loaded.title == EXAMPLE_TITLE
    with pytest.raises(FileNotFoundError):
        load_multi_session_projects_file(tmp_path / "nope.yaml")
    assert _shipped_raw()["schema"] == MULTI_SESSION_PROJECTS_SCHEMA


def test_registry_holds_sessions_one_by_one():
    registry = MultiSessionRegistry()
    held = registry.register_session(_session(session_id=None))
    assert held.session_id == "multisession-1"
    assert registry.latest_session() == held
    assert registry.get_session("multisession-1") == held
    assert registry.session_for_branch("work/parser-wiring") == held
    with pytest.raises(ValueError, match="already exists"):
        registry.register_session(held)
    with pytest.raises(ValueError, match="different branches"):
        registry.register_session(_session(
            session_id="multisession-copy", session_ref="session-copy",
            journal_ref="journal-copy",
            journal_entries=["entry-copy-1"]))
    with pytest.raises(ValueError, match="crosstalk"):
        registry.register_session(_session(
            session_id="multisession-copy", session_ref="session-copy",
            branch="work/copy", journal_ref="journal-copy"))
    with pytest.raises(ValueError, match="no multi-session book is held"):
        registry.book()
    assert registry.panel().total_sessions == 1
    assert registry.isolation().verdict == "single-session"
    with pytest.raises(KeyError):
        registry.get_session("multisession-nope")


def test_registry_register_book_and_title_law():
    registry = MultiSessionRegistry()
    book = _book()
    held_book = registry.register_book(book)
    assert held_book.title == "A test multi-session book"
    assert registry.list_sessions()[0].session_id == "multisession-test"
    with pytest.raises(ValueError):
        registry.register_book(book)
    other = _book([_session(
        session_id="multisession-z", session_ref="session-z",
        branch="work/z", journal_ref="journal-z",
        journal_entries=["entry-z-1"])], title="Another title")
    with pytest.raises(ValueError, match="different title"):
        registry.register_book(other)
    fresh = MultiSessionRegistry(load_multi_session_projects())
    assert fresh.book().total_sessions == 4


def test_news_records_and_plain_words():
    session = _session()
    news = parallel_record(session)
    assert news["type"] == "multi_session_projects_session"
    assert news["news"] is True
    assert "work/parser-wiring" in news["headline"]
    book = load_multi_session_projects()
    panel_news = panel_record(derive_panel(book), book)
    assert panel_news["type"] == "multi_session_projects_panel"
    assert "4 sessions" in panel_news["headline"]
    verdict_news = isolation_record(derive_isolation(book), book)
    assert verdict_news["type"] == "multi_session_projects_isolation"
    assert "parallel-isolated" in verdict_news["headline"]
    whole = book_record(book)
    assert whole["type"] == "multi_session_projects_book"
    assert whole["session_count"] == 4
    words = plain_words(book.sessions[0])
    assert "main" in words
    assert "Volmarr" in words
    panel_words = panel_plain_words(book)
    assert "multisession-graph" in panel_words
    assert "no crosstalk" in panel_words
    verdict_words = isolation_plain_words(book)
    assert "parallel-isolated" in verdict_words
    assert "no crosstalk" in verdict_words


def test_refs_and_totals_surface():
    book = load_multi_session_projects()
    refs = multi_session_refs(book)
    assert refs[0] == ("main", "session-m161-endurance")
    assert ("work/graph-retrieval-care", "session-m152-graph") in refs
    assert len(refs) == 4
    assert validate_session(_stored_session(_session())) == _session()


def test_formatters_and_screen():
    book = load_multi_session_projects()
    block = format_parallel_session(book.sessions[2])
    assert "journal-graph" in block
    assert "spawns no live session" in block
    listing = format_parallel_sessions(book)
    assert "multisession-main" in listing
    only = format_parallel_sessions(book, "main")
    assert "multisession-main" in only
    assert "multisession-graph" not in only
    panel_text = format_panel(book)
    assert "Multi-session panel in" in panel_text
    assert "no crosstalk" in panel_text
    isolation_text = format_isolation(book)
    assert "parallel-isolated" in isolation_text
    screen = format_multi_session_projects_screen(book)
    assert "Multi-Session Per Project (M-162)" in screen
    assert USAGE in screen
    default_screen = format_multi_session_projects_screen()
    assert "multisession-main" in default_screen


def test_parse_multisession_args():
    assert parse_multisession_args("") == ("show", None)
    assert parse_multisession_args("show") == ("show", None)
    assert parse_multisession_args("list") == ("show", None)
    assert parse_multisession_args(
        "session multisession-main") == ("session", "multisession-main")
    assert parse_multisession_args("branch work/graph-care") == (
        "branch", "work/graph-care")
    assert parse_multisession_args("panel") == ("panel", None)
    assert parse_multisession_args("isolation") == ("isolation", None)
    with pytest.raises(ValueError, match="Usage"):
        parse_multisession_args("dance party")
    with pytest.raises(ValueError):
        parse_multisession_args("branch bad branch")
    with pytest.raises(ValueError):
        parse_multisession_args(42)
