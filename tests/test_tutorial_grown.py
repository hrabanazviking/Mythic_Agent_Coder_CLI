"""M-185 The Tutorial Grown - pure-layer tests.

TIER: integration

The pure layer is the grown tutorial, held as
data: one interactive lesson held whole - under
its title, its feature family in the closed
vocabulary, and its readiness, ready or blocked -
the scratch repo a lesson runs inside, held as
data, and the play: the lesson steps held in
order under the one rule, lessons run inside a
scratch repo, never against the real workspace.
Readiness is never faked: a lesson whose exercise
does not stand ready stands blocked, named in its
gaps. A record claiming a run outside a scratch
repo refuses by name, and a play that cleans its
scratch repo away before its exercise stands tried
refuses by name. The panel is derived for one held
view and the verdict is derived for the whole book
under one view. The shipped example book is held
in a data file, and a loader reads a book from any
file. This layer runs no lesson, opens no repo and
writes nothing to any real workspace: it holds the
grown tutorial as data and tells it.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.tutorial_grown import (
    READINESS_WORDS,
    SCRATCH_STATES,
    TUTORIAL_GROWN_RESOURCE,
    TUTORIAL_GROWN_SCHEMA,
    TUTORIAL_GROWN_SLICE,
    PLAIN_EXPLANATION,
    FEATURE_FAMILIES,
    SCRATCH_REPO_RULE,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    PLAY_ACTION,
    PLAY_PHASES,
    LessonRecord,
    ScratchRecord,
    TutorialBook,
    TutorialPanel,
    TutorialRegistry,
    TutorialVerdict,
    TutorialView,
    PlayStep,
    book_record,
    build_book,
    build_lesson,
    build_scratch,
    build_panel,
    build_row,
    build_step,
    build_verdict,
    build_view,
    derive_panel,
    derive_verdict,
    derive_play,
    lesson_gaps,
    lesson_passes,
    lesson_plain_words,
    lesson_record,
    lessons_for_readiness,
    format_book,
    format_lesson,
    format_scratch,
    format_tutorial_grown_screen,
    format_panel,
    format_verdict,
    format_view,
    format_play,
    inspect_tutorial_source,
    load_tutorial_grown,
    load_tutorial_grown_file,
    normalize_state,
    normalize_readiness,
    normalize_phase,
    normalize_family,
    normalize_view_filter,
    scratch_record,
    panel_plain_words,
    panel_record,
    parse_tutorial_args,
    passing_lessons,
    plain_lines,
    plain_words,
    segment_of,
    shown_lessons,
    step_record,
    total_lessons,
    validate_book,
    validate_lesson,
    validate_scratch,
    validate_panel,
    validate_row,
    validate_step,
    validate_verdict,
    validate_view,
    verdict_plain_words,
    verdict_record,
    view_plain_words,
    view_record,
    play_plain_words,
    play_record,
    play_steps,
)
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.tui_redesign_charter import load_charter

ROOT = Path(__file__).resolve().parents[1]
ON = "2026-11-09"
BY = "the coordinator"
EXAMPLE_TITLE = "The tutorial grown at the M-184 slice boundary"


def _lesson(**overrides):
    fields = {
        "lesson_id": "les-test",
        "seq": 1,
        "title": "A test lesson",
        "family": "providers",
        "readiness": "ready",
        "detail": "A test lesson held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_lesson(fields)


def _stored_lesson(lesson):
    return lesson.to_record()


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _stored_view(view):
    return view.to_record()


def _step(**overrides):
    fields = {
        "step_id": "step-test",
        "seq": 1,
        "phase": "open",
        "title": "A test step",
        "detail": "A test play step held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_step(fields)


def _scratch(**overrides):
    fields = {
        "scratch_id": "scratch-test",
        "seq": 1,
        "repo": "test-playground",
        "state": "pending",
        "detail": "A test scratch held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_scratch(fields)


def _book(lessons=None, views=None, steps=None, scratches=None,
          **overrides):
    fields = {
        "schema": TUTORIAL_GROWN_SCHEMA,
        "slice": "M-185",
        "guide": {"title": "A test tutorial book"},
        "lessons": [_stored_lesson(item) for item in (
            lessons if lessons is not None else [_lesson()])],
        "views": [_stored_view(item) for item in (
            views if views is not None else [_view()])],
        "steps": [item.to_record() for item in (steps or [])],
        "scratches": [item.to_record() for item in (scratches or [])],
        "panels": [],
    }
    fields.update(overrides)
    return build_book(fields)


def _mixed_book():
    return _book(lessons=[
        _lesson(),
        _lesson(lesson_id="les-blocked", seq=2, title="Play inside the sandbox",
                   family="sandboxing", readiness="blocked"),
    ])


# ---------------------------------------------------------------------
# The shipped example book, the roadmap and the charter.
# ---------------------------------------------------------------------


def test_shipped_book_loads_with_pinned_shape():
    book = load_tutorial_grown()
    assert book.title == EXAMPLE_TITLE
    assert book.lesson_ids() == (
        "les-providers-first", "les-code-intelligence", "les-editors-hand",
        "les-sandboxing", "les-parallel-crews", "les-memory-context")
    assert [v.view_id for v in book.views] == ["view-all", "view-ready"]
    assert [s.phase for s in book.steps] == [
        "open", "read", "try", "check", "clean"]
    assert len(book.scratches) == 1
    assert book.scratches[0].state == "open"
    assert book.scratches[0].repo == "tutorial-playground"
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m184-boundary"
    assert panel.as_of == "2026-11-09"
    assert [row.item_id for row in panel.rows] == list(book.lesson_ids())
    derived = derive_panel(book, "view-all")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 6
    assert panel.total_shown == derived.total_shown == 6
    assert {c.readiness: c.items for c in panel.readiness_counts} == {
        "ready": 4, "blocked": 2}
    assert derive_verdict(book, "view-all").verdict == "strained"
    assert derive_verdict(book, "view-all").passing_shown == 4
    assert derive_verdict(book, "view-ready").verdict == "open"
    assert derive_verdict(book, "view-ready").passing_shown == 4
    assert derive_play(book).passes() is True
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / TUTORIAL_GROWN_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == TUTORIAL_GROWN_SCHEMA
    assert raw["slice"] == "M-185"
    assert "verdict" not in raw



def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-185")]
    assert slice_.title == "The tutorial grown"
    assert slice_.part == 8
    assert "interactive lessons per feature family" in slice_.summary
    assert "scratch repo" in slice_.summary
    assert "mythic tutorial" in slice_.summary
    assert "manual you play" in slice_.summary
    assert TUTORIAL_GROWN_SLICE == "M-185"



def test_charter_names_no_row_for_m185():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert owners.count("M-185") == 0



def test_closed_vocabularies():
    assert READINESS_WORDS == ("ready", "blocked")
    assert FEATURE_FAMILIES == (
        "providers", "code intelligence", "the editor's hand",
        "sandboxing", "parallel crews", "memory and context",
        "plain language", "bridges")
    assert VIEW_FILTERS == ("all", "ready", "blocked")
    assert PLAY_PHASES == ("open", "read", "try", "check", "clean")
    assert SCRATCH_STATES == ("open", "closed", "pending")
    assert VERDICT_WORDS == ("open", "strained", "shut")
    assert PLAY_ACTION == "play"
    assert normalize_readiness("READY") == "ready"
    assert normalize_family("Code Intelligence") == "code intelligence"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_phase("TRY") == "try"
    assert normalize_state("Closed") == "closed"
    with pytest.raises(ValueError):
        normalize_readiness("maybe")
    with pytest.raises(ValueError):
        normalize_family("a guess")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    with pytest.raises(ValueError):
        normalize_phase("tour")
    with pytest.raises(ValueError):
        normalize_state("later")
    assert "inside a scratch repo" in SCRATCH_REPO_RULE
    assert "M-185" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /lessons")



def test_shipped_book_judged_honestly_as_data():
    book = load_tutorial_grown()
    providers = book.lesson_for("les-providers-first")
    assert lesson_passes(providers) is True
    assert lesson_gaps(providers) == ()
    assert plain_lines(providers) == (
        "Lesson: Meet your providers",
        "Family: providers",
        "Readiness: ready")
    sandbox = book.lesson_for("les-sandboxing")
    assert lesson_gaps(sandbox) == ("exercise",)
    assert lesson_passes(sandbox) is False
    assert [d.lesson_id for d in passing_lessons(book)] == [
        "les-providers-first", "les-code-intelligence", "les-editors-hand",
        "les-parallel-crews"]
    assert total_lessons(book) == 6
    assert segment_of(sandbox) == (
        "les-sandboxing: Play inside the sandbox in family "
        "'sandboxing' - readiness: 'blocked' - detail: 'This "
        "lesson's exercise names a command the sandbox has not "
        "approved on this machine, so it stands blocked honestly "
        "- it is never run against the real workspace instead.' "
        "- gaps: exercise")
    play = derive_play(book)
    assert [s.step_id for s in play.steps] == [
        "step-open", "step-read", "step-try", "step-check", "step-clean"]
    assert play.try_seq == 3
    assert play.clean_seq == 5


# ---------------------------------------------------------------------
# The held lesson: judged whole, its telling derived.
# ---------------------------------------------------------------------


def test_lesson_record_round_trips():
    lesson = _lesson()
    assert validate_lesson(lesson) is lesson
    rebuilt = build_lesson(_stored_lesson(lesson))
    assert rebuilt == lesson
    assert rebuilt.item_id == "les-test"
    record = lesson_record(lesson)
    assert record["type"] == "tutorial_lesson"
    assert record["passes"] is True
    assert record["gaps"] == []


def test_lesson_refuses_stored_judgements():
    for key in ("passes", "gaps", "segment", "verdict", "play",
                "in_order"):
        fields = _stored_lesson(_lesson())
        fields[key] = "stored"
        with pytest.raises(ValueError):
            build_lesson(fields)
    fields = _stored_lesson(_lesson())
    fields["surprise"] = "stored"
    with pytest.raises(ValueError):
        build_lesson(fields)



def test_lesson_refuses_a_run_outside_a_scratch_repo():
    for key in ("real_workspace", "runs_in_real_workspace",
                "against_real_workspace", "outside_scratch_repo",
                "run_outside_scratch"):
        fields = _stored_lesson(_lesson())
        fields[key] = True
        with pytest.raises(ValueError) as caught:
            build_lesson(fields)
        assert "scratch repo" in str(caught.value)



def test_scratch_refuses_a_run_outside_a_scratch_repo():
    for key in ("real_workspace", "against_real_workspace"):
        fields = _scratch().to_record()
        fields[key] = True
        with pytest.raises(ValueError) as caught:
            build_scratch(fields)
        assert "scratch repo" in str(caught.value)
    scratch = _scratch(state="OPEN")
    assert validate_scratch(scratch) is scratch
    assert scratch.state == "open"
    assert scratch_record(scratch)["type"] == "tutorial_scratch"



def test_lesson_vocabularies_are_closed():
    assert _lesson(readiness="BLOCKED").readiness == "blocked"
    with pytest.raises(ValueError):
        _lesson(readiness="guessed")
    with pytest.raises(ValueError):
        _lesson(family="a hunch")
    with pytest.raises(ValueError):
        _lesson(title="   ")
    with pytest.raises(ValueError):
        _lesson(seq=0)



def test_plain_telling_derives_from_the_lessons_own_fields():
    lesson = _lesson(
        title="Test Lesson", family="code intelligence",
        readiness="blocked",
        detail="The exercise waits on an unapproved command.")
    lines = plain_lines(lesson)
    assert lines[0] == "Lesson: Test Lesson"
    assert lines[1] == "Family: code intelligence"
    assert lines[2] == "Readiness: blocked"
    assert plain_words(lesson) == lesson_plain_words(lesson)
    assert "Test Lesson" in plain_words(lesson)
    assert "unapproved command" in plain_words(lesson)



def test_blocked_lesson_stands_named_in_its_gaps():
    lesson = _lesson(readiness="blocked")
    assert lesson_gaps(lesson) == ("exercise",)
    assert lesson_passes(lesson) is False
    text = format_lesson(lesson)
    assert "stands blocked" in text
    ready_text = format_lesson(_lesson())
    assert "stands ready" in ready_text



def test_view_step_and_scratch_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(_stored_view(view)) == view
    record = view_record(view)
    assert record["type"] == "tutorial_view"
    assert record["view_filter"] == "all"
    assert "shows all lessons" in view_plain_words(view)
    assert "filter all" in format_view(view)
    with pytest.raises(ValueError):
        _view(view_filter="some")
    step = _step(phase="READ")
    assert validate_step(step) is step
    assert step.phase == "read"
    assert build_step(step.to_record()) == step
    assert step_record(step)["type"] == "tutorial_step"
    scratch = _scratch()
    assert build_scratch(scratch.to_record()) == scratch
    assert "scratch repo test-playground" in format_scratch(scratch)



def test_play_is_derived_in_held_order_and_stands_in_order():
    steps = [
        _step(step_id="step-o", seq=1, phase="open"),
        _step(step_id="step-r", seq=2, phase="read"),
        _step(step_id="step-t", seq=3, phase="try"),
        _step(step_id="step-c", seq=4, phase="clean"),
    ]
    book = _book(steps=steps)
    assert [s.step_id for s in play_steps(book)] == [
        "step-o", "step-r", "step-t", "step-c"]
    play = derive_play(book)
    assert play.passes() is True
    assert play.try_seq == 3
    assert play.clean_seq == 4
    assert play_record(book)["passes"] is True
    assert "scratch repo" in play_plain_words(book)
    assert "[try]" in format_play(book)
    no_try = _book(steps=[_step(step_id="step-o", seq=1)])
    assert derive_play(no_try).passes() is False



def test_play_cleaning_scratch_before_the_try_refuses_by_name():
    steps = [
        _step(step_id="step-c", seq=1, phase="clean"),
        _step(step_id="step-t", seq=2, phase="try"),
    ]
    with pytest.raises(ValueError) as caught:
        _book(steps=steps)
    assert "cleans its scratch repo" in str(caught.value)
    fields = _step().to_record()
    fields["real_workspace"] = True
    with pytest.raises(ValueError) as caught:
        build_step(fields)
    assert "outside a scratch repo" in str(caught.value)
    raw = {
        "schema": TUTORIAL_GROWN_SCHEMA, "slice": "M-185",
        "guide": {"title": "A test tutorial book"},
        "lessons": [], "views": [], "steps": [], "scratches": [],
        "panels": [], "runs_in_real_workspace": True,
    }
    with pytest.raises(ValueError) as caught:
        build_book(raw)
    assert "outside a scratch repo" in str(caught.value)


def test_panel_is_derived_and_a_stored_panel_must_agree():
    book = _mixed_book()
    panel = derive_panel(book)
    assert isinstance(panel, TutorialPanel)
    assert panel.total_items == 2
    assert panel.total_shown == 2
    assert validate_panel(panel, book) is panel
    assert build_panel(panel.to_record(), book).rows == panel.rows
    assert build_row(panel.rows[0], book.lessons[0]) == panel.rows[0]
    assert validate_row(panel.rows[0], book.lessons[0]) == panel.rows[0]
    tampered = dict(panel.to_record())
    tampered["total_shown"] = 99
    with pytest.raises(ValueError):
        build_panel(tampered, book)
    renamed = dict(panel.to_record())
    renamed["panel_id"] = "panel-renamed"
    assert build_panel(renamed, book).panel_id == "panel-renamed"
    record = panel_record(panel, book)
    assert record["type"] == "tutorial_panel"
    assert record["panel_id"] == panel.panel_id


def test_verdict_is_derived_from_the_shown_lessons():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert isinstance(verdict, TutorialVerdict)
    assert verdict.verdict == "strained"
    assert verdict.total_shown == 2
    assert verdict.passing_shown == 1
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    record = verdict_record(verdict, book)
    assert record["type"] == "tutorial_verdict"
    assert "strained" in verdict_plain_words(book)
    assert "strained" in format_verdict(book)


def test_verdict_open_and_shut_edges():
    whole = _book(lessons=[_lesson()])
    assert derive_verdict(whole).verdict == "open"
    absent_book = _book(lessons=[_lesson(readiness="blocked")])
    assert derive_verdict(absent_book).verdict == "shut"
    none_shown = _book(
        lessons=[_lesson(readiness="blocked")],
        views=[_view(view_filter="ready")])
    verdict = derive_verdict(none_shown)
    assert verdict.total_shown == 0
    assert verdict.verdict == "shut"



def test_shown_and_readiness_readings():
    book = _mixed_book()
    assert [d.lesson_id for d in shown_lessons(book)] == [
        "les-test", "les-blocked"]
    ready_view = _view(view_id="view-r", seq=2, view_filter="ready")
    book2 = _book(
        lessons=[_lesson(), _lesson(
            lesson_id="les-blocked", seq=2, title="Play inside the sandbox",
            family="sandboxing", readiness="blocked")],
        views=[_view(), ready_view])
    assert [d.lesson_id for d in shown_lessons(book2, ready_view)] == [
        "les-test"]
    assert [d.lesson_id for d in lessons_for_readiness(
        book2, "blocked")] == ["les-blocked"]
    assert [d.lesson_id for d in passing_lessons(book2)] == [
        "les-test"]
    assert total_lessons(book2) == 2
    with pytest.raises(ValueError):
        lessons_for_readiness(book2, "maybe")


def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(lessons=[_lesson(), _lesson(seq=2)])
    with pytest.raises(ValueError):
        _book(lessons=[_lesson(), _lesson(lesson_id="det-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(view_filter="ready")])
    with pytest.raises(ValueError):
        _book(steps=[_step(), _step(phase="play")])
    with pytest.raises(ValueError):
        _book(scratches=[_scratch(), _scratch(title="Other")])
    fields = {
        "schema": TUTORIAL_GROWN_SCHEMA, "slice": "M-185",
        "guide": {"title": "A test tutorial book"},
        "lessons": [_stored_lesson(_lesson())],
        "views": [_stored_view(_view())], "steps": [], "scratches": [],
        "panels": [], "verdict": "open",
    }
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / TUTORIAL_GROWN_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "tutorial_grown.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_tutorial_grown_file(path)
    assert book.title == EXAMPLE_TITLE
    assert total_lessons(book) == 6



def test_registry_holds_lessons_and_views_one_by_one():
    registry = TutorialRegistry()
    assert registry.list_items() == ()
    held = registry.register_lesson(_lesson())
    assert held.lesson_id == "les-test"
    registry.register_view(_view())
    assert [i.item_id if hasattr(i, "item_id") else i.view_id
            for i in registry.list_items()] == [
        "les-test", "view-test"]
    assert registry.get_lesson("les-test").title == "A test lesson"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.book().title == "An unheld tutorial book"
    with pytest.raises(ValueError):
        registry.register_lesson(_lesson(seq=2))
    with pytest.raises(ValueError):
        registry.register_lesson(_lesson(lesson_id="les-two"))
    with pytest.raises(KeyError):
        registry.get_lesson("les-nope")


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = TutorialRegistry()
    book = _mixed_book()
    held = registry.register_book(book)
    assert held.title == "A test tutorial book"
    assert len(registry.list_lessons()) == 2
    other = _book(lessons=[_lesson(
        lesson_id="det-x", seq=9, title="Other")],
        views=[_view(view_id="view-x", seq=9)])
    object.__setattr__(other, "title", "Another title")
    with pytest.raises(ValueError):
        registry.register_book(other)



def test_records_are_session_news():
    book = _mixed_book()
    record = book_record(book)
    assert record["type"] == "tutorial_book"
    assert record["title"] == "A test tutorial book"
    assert len(record["lessons"]) == 2
    panel = derive_panel(book)
    assert panel_record(panel, book)["rows"][0]["item_id"] == "les-test"
    assert verdict_record(derive_verdict(book), book)["verdict"] == (
        "strained")



def test_plain_words_and_formatters():
    book = _mixed_book()
    assert "in family 'providers'" in format_book(book)
    assert "les-blocked" in format_book(book, "blocked")
    assert "les-test" not in format_book(book, "blocked")
    assert "Tutorial panel under view view-test" in format_panel(book)
    assert panel_plain_words(book).startswith(
        "The tutorial book holds 2 lessons")
    screen = format_tutorial_grown_screen(book)
    assert "The Tutorial Grown (M-185)" in screen
    assert PLAIN_EXPLANATION in screen
    lesson_text = format_lesson(book.lessons[0])
    assert "Lesson: A test lesson" in lesson_text
    assert "Readiness: ready" in lesson_text



def test_parse_args_inspect_and_loader_roads():
    assert parse_tutorial_args("") == ("show", None)
    assert parse_tutorial_args("show") == ("show", None)
    assert parse_tutorial_args(None) == ("show", None)
    assert parse_tutorial_args("lesson les-test") == (
        "lesson", "les-test")
    assert parse_tutorial_args("play") == ("play", None)
    assert parse_tutorial_args("scratch scratch-test") == (
        "scratch", "scratch-test")
    assert parse_tutorial_args("view view-test") == (
        "view", "view-test")
    assert parse_tutorial_args("readiness blocked") == (
        "readiness", "blocked")
    assert parse_tutorial_args("panel") == ("panel", None)
    assert parse_tutorial_args("verdict") == ("verdict", None)
    for bad in ("dance", "lesson", "panel now", "play now",
                "readiness a b"):
        with pytest.raises(ValueError):
            parse_tutorial_args(bad)
    lesson = _lesson()
    assert inspect_tutorial_source(lesson) == {
        "kind": "lesson", "lesson_id": "les-test"}
    assert inspect_tutorial_source(
        _stored_lesson(lesson))["kind"] == "lesson"
    assert inspect_tutorial_source(
        _stored_view(_view()))["kind"] == "view"
    assert inspect_tutorial_source(
        _step().to_record())["kind"] == "step"
    assert inspect_tutorial_source(
        _scratch().to_record())["kind"] == "scratch"
    assert inspect_tutorial_source(42)["kind"] == "unknown"
    book = load_tutorial_grown({
        "schema": TUTORIAL_GROWN_SCHEMA, "slice": "M-185",
        "guide": {"title": "A judged book"},
        "lessons": [_stored_lesson(_lesson())],
        "views": [_stored_view(_view())], "steps": [], "scratches": [],
        "panels": []})
    assert isinstance(book, TutorialBook)
    assert book.title == "A judged book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_tutorial_grown({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_tutorial_grown({"slice": "M-999"})
    built = build_lesson(
        lesson_id="les-kw", seq=3, title="Kw Lesson",
        family="bridges", readiness="ready",
        detail="Built by fields.", recorded_on=ON, actor=BY,
        source="test source", origin_session="session-test")
    assert built.lesson_id == "les-kw"
    assert lesson_passes(built) is True


# ---------------------------------------------------------------------
# M-185 agent layer: the agent holds a tutorial
# book for the session, lessons and views are
# published as session news through the checkpoint
# road (journal first, deduped per shape), the
# panel and verdict are derived at call time from
# the whole book under a view, never held, and the
# play is derived at call time from the book's held
# steps under the scratch-repo rule - lessons run
# inside a scratch repo, never against the real
# workspace. This layer calls no model, runs no
# lesson, opens no repo and persists nothing beyond
# the session journal news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _tutorial_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_tutorial_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / TUTORIAL_GROWN_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "tutorial_grown.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestTutorialAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.tutorial_grown_status()
        assert status["lessons"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["tutorial"]["title"] == EXAMPLE_TITLE
        assert len(status["tutorial"]["lessons"]) == 6
        assert len(status["tutorial"]["views"]) == 2
        assert len(status["tutorial"]["steps"]) == 5
        assert len(status["tutorial"]["scratches"]) == 1
        assert status["panel"]["total_items"] == 6
        assert status["panel"]["total_shown"] == 6
        assert status["panels"][0]["panel_id"] == "panel-m184-boundary"
        assert status["verdict"]["verdict"] == "strained"
        assert status["verdict"]["passing_shown"] == 4
        assert status["play"]["passes"] is True
        assert "inside a scratch repo" in status["rule"]
        assert "Memory you can play with" in status["plain_words"]
        assert "The Tutorial Grown (M-185)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._tutorial_grown_registry()
        assert agent._tutorial_grown_registry() is first
        assert agent._tutorial_grown_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.tutorial_grown_status()
        assert agent.get_tutorial_lesson(
            "les-providers-first").title == "Meet your providers"
        assert agent.get_tutorial_view("view-all").view_filter == "all"
        assert agent.get_tutorial_scratch(
            "scratch-tutorial-playground").state == "open"
        assert [d.lesson_id for d in agent.tutorial_grown_with_readiness(
            "blocked")] == ["les-sandboxing", "les-memory-context"]
        assert [d.lesson_id for d in agent.tutorial_grown_passing()] == [
            "les-providers-first", "les-code-intelligence", "les-editors-hand",
            "les-parallel-crews"]
        agent.tutorial_grown_panel()
        agent.tutorial_grown_verdict()
        agent.tutorial_grown_play()
        agent.report_tutorial_grown()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("tutorial")] == []
        with pytest.raises(KeyError):
            agent.get_tutorial_lesson("les-nope")
        with pytest.raises(KeyError):
            agent.get_tutorial_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_tutorial_scratch("scratch-nope")
        with pytest.raises(ValueError):
            agent.tutorial_grown_with_readiness("maybe")
        agent.close()

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_tutorial_lesson(_lesson())
        status = agent.tutorial_grown_status()
        assert [d["lesson_id"] for d in status["lessons"]] == [
            "les-test"]
        assert status["book"]["title"] == "An unheld tutorial book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert status["play"]["passes"] is False
        assert "les-test" in status["screen"]

    def test_held_lesson_never_falls_back_to_the_example(
            self, agent):
        agent.register_tutorial_lesson(_lesson())
        with pytest.raises(KeyError):
            agent.get_tutorial_lesson("les-providers-first")
        with pytest.raises(KeyError):
            agent.get_tutorial_view("view-all")
        lesson = agent.get_tutorial_lesson("les-test")
        assert lesson.title == "A test lesson"
        assert agent.tutorial_grown_book().title == (
            "An unheld tutorial book")

    def test_play_and_scratch_stand_in_the_example(self, agent):
        play = agent.tutorial_grown_play()
        assert [s.phase for s in play.steps] == [
            "open", "read", "try", "check", "clean"]
        assert play.passes() is True
        scratch = agent.get_tutorial_scratch("scratch-tutorial-playground")
        assert scratch.repo == "tutorial-playground"
        assert scratch.state == "open"


class TestTutorialAgentHolding:
    def test_register_lesson_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_tutorial_lesson(_lesson())
        assert result["lesson"]["lesson_id"] == "les-test"
        assert result["record_news"]["type"] == "tutorial_lesson"
        assert "les-test" in result["screen"]
        events = _tutorial_events(
            store, session_id, "tutorial_lesson")
        assert len(events) == 1
        agent.close()

    def test_duplicate_lesson_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_tutorial_lesson(_lesson())
        with pytest.raises(ValueError):
            agent.register_tutorial_lesson(_lesson(seq=9))
        events = _tutorial_events(
            store, session_id, "tutorial_lesson")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_tutorial_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_tutorial_events(
            store, session_id, "tutorial_view")) == 1
        agent.close()

    def test_view_road_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_tutorial_lesson(_lesson())
        result = agent.view_tutorial("ready")
        assert result["view"]["view_filter"] == "ready"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "tutorial_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "open"
        assert len(_tutorial_events(
            store, session_id, "tutorial_view")) == 1
        assert len(_tutorial_events(
            store, session_id, "tutorial_panel")) == 1
        assert len(_tutorial_events(
            store, session_id, "tutorial_verdict")) == 1
        agent.close()

    def test_view_road_over_an_unshown_filter_is_shut(self, agent):
        agent.register_tutorial_lesson(_lesson(readiness="blocked"))
        result = agent.view_tutorial("ready")
        assert result["verdict_record"]["verdict"] == "shut"
        assert result["verdict_record"]["total_shown"] == 0

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_tutorial_book(
            _book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "tutorial_lesson", "tutorial_view"]
        assert len(_tutorial_events(
            store, session_id, "tutorial_lesson")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_tutorial_book()
        assert result["count"] == 6
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "tutorial_panel"
        assert result["play_record"]["passes"] is True
        with pytest.raises(ValueError):
            agent.record_tutorial_book()
        assert len(_tutorial_events(
            store, session_id, "tutorial_lesson")) == 6
        assert len(_tutorial_events(
            store, session_id, "tutorial_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_tutorial_book_file(tmp_path)
        book = load_tutorial_grown_file(path)
        result = agent.record_tutorial_book(book)
        assert result["count"] == 6
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_tutorial_grown()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "strained"
        assert "les-providers-first" in report["book_text"]
        assert "[try]" in report["play_text"]
        assert "scratch-tutorial-playground" in report["play_text"]
        agent.register_tutorial_lesson(_lesson())
        report = agent.report_tutorial_grown()
        assert report["book"]["title"] == "An unheld tutorial book"
        assert report["panel"] is None
        assert report["verdict"] is None


class TestTutorialTerminalSurface:
    def test_show_lesson_play_scratch_view_readiness_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/lessons")
        assert "The Tutorial Grown (M-185)" in text
        _, _, text = _slash(agent, "/lessons lesson les-providers-first")
        assert "Lesson: Meet your providers" in text
        _, _, text = _slash(agent, "/lessons play")
        assert "[try]" in text
        _, _, text = _slash(agent, "/lessons scratch scratch-tutorial-playground")
        assert "open" in text
        _, _, text = _slash(agent, "/lessons view view-all")
        assert "filter all" in text
        _, _, text = _slash(agent, "/lessons readiness blocked")
        assert "les-sandboxing" in text
        assert "les-providers-first" not in text
        _, _, text = _slash(agent, "/lessons panel")
        assert "Tutorial panel under view view-all" in text
        _, _, text = _slash(agent, "/lessons verdict")
        assert "strained" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/lessons [show|lesson <lesson-id>"
                "|play|scratch <scratch-id>|view <view-id>"
                "|readiness <readiness>|panel|verdict]") in text
        _, _, text = _slash(agent, "/lessons dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/lessons lesson les-nope")
        assert "no lesson named" in text


@pytest.fixture()
def lessons_handler(agent, monkeypatch):
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


def _lessons_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestTutorialCommand:
    def test_show_is_default(self, lessons_handler, agent):
        lessons_handler._handle_lessons("")
        assert "The Tutorial Grown (M-185)" in (
            _lessons_published_text(lessons_handler))

    def test_lesson_play_scratch_view_readiness_panel_verdict(
            self, lessons_handler, agent):
        lessons_handler._handle_lessons("lesson les-providers-first")
        assert "Lesson: Meet your providers" in _lessons_published_text(
            lessons_handler)
        lessons_handler._handle_lessons("play")
        assert "[try]" in _lessons_published_text(lessons_handler)
        lessons_handler._handle_lessons("scratch scratch-tutorial-playground")
        assert "open" in _lessons_published_text(lessons_handler)
        lessons_handler._handle_lessons("view view-all")
        assert "filter all" in _lessons_published_text(lessons_handler)
        lessons_handler._handle_lessons("readiness blocked")
        assert "les-sandboxing" in _lessons_published_text(
            lessons_handler)
        lessons_handler._handle_lessons("panel")
        assert "Tutorial panel under view" in _lessons_published_text(
            lessons_handler)
        lessons_handler._handle_lessons("verdict")
        assert "strained" in _lessons_published_text(lessons_handler)

    def test_bad_grammar_is_published(
            self, lessons_handler, agent):
        lessons_handler._handle_lessons("dance party")
        assert USAGE in _lessons_published_text(lessons_handler)
        lessons_handler._handle_lessons("lesson les-nope")
        assert "no lesson named" in _lessons_published_text(
            lessons_handler)


class TestChatScreenRoutingTutorial:
    def test_onboard_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/lessons panel", _FakeLog())
        assert calls == [("/lessons", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/lessons[/green] - show the tutorial grown (M-185)" in (
            text)
        assert ('"/lessons": "Usage: /lessons | '
                '/lessons lesson <lesson-id>') in text


class TestTutorialDerivedRoads:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.tutorial_grown_panel()
        assert panel.total_shown == 6
        assert panel.panel_id == "panel-view-all"
        verdict = agent.tutorial_grown_verdict()
        assert verdict.verdict == "strained"
        found = agent.tutorial_grown_verdict("view-ready")
        assert found.verdict == "open"
        assert found.passing_shown == 4
        agent.register_tutorial_lesson(_lesson())
        with pytest.raises(ValueError):
            agent.tutorial_grown_panel()
        with pytest.raises(ValueError):
            agent.tutorial_grown_verdict()

    def test_absent_lesson_stands_named_in_its_gaps(self, agent):
        lesson = agent.get_tutorial_lesson("les-sandboxing")
        assert lesson_gaps(lesson) == ("exercise",)
        assert lesson_passes(lesson) is False
        status = agent.tutorial_grown_status()
        assert status["verdict"]["passing_shown"] == 4
        assert status["play"]["steps"][2]["phase"] == "try"
        assert status["play"]["steps"][4]["phase"] == "clean"
