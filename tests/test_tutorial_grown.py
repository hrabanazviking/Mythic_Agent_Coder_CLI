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


