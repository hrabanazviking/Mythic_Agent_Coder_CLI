"""M-191 Session Theatre - pure-layer tests.

TIER: integration

The pure layer is the session theatre, held as
data: one record per past session, held whole
as a browsable hunk - under its file, its
kind in the closed vocabulary, its added and
its removed held honestly (unknown stays
empty, never invented), the resume target that
reaches it, named as data, and its detail - the
resume, fork and export targets held as data
beside them, each naming its session, its
stance and its target, and the theatre index
derived at call time from the held hunks alone,
never stored where it could drift. A hunk
naming no jump target stands untargeted, named
in its gaps; two hunks standing for one session
id refuse by name, and one stance record stands
per session target. A record claiming a session
actually resumed, forked or exported refuses by
name, and a stored index or verdict refuses by
name. The panel is derived for one held view
and the verdict is derived for the whole book
under one view. The shipped example book is
held in a data file, and a loader reads a book
from any file. This layer resumes no session,
forks nothing, exports nothing and opens no
network: it holds the theatre as data and
tells it.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.diff_theatre_final import (
    KINDS,
    EXAMPLE_TARGET,
    STANCES,
    INDEX_ACTION,
    DIFF_THEATRE_FINAL_RESOURCE,
    DIFF_THEATRE_FINAL_SCHEMA,
    DIFF_THEATRE_FINAL_SLICE,
    THEATRE_RULE,
    PLAIN_EXPLANATION,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TARGET_WORDS,
    HunkCard,
    CommentRecord,
    TheatreBook,
    TheatrePanel,
    DiffTheatreFinalRegistry,
    TheatreVerdict,
    TheatreView,
    book_record,
    build_book,
    build_hunk,
    build_comment,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    derive_index,
    derive_panel,
    derive_verdict,
    first_comment,
    format_book,
    format_hunk,
    format_index,
    format_comment,
    format_theatre_screen,
    format_panel,
    format_target,
    format_verdict,
    format_view,
    hunk_for_target,
    hunk_gaps,
    hunk_passes,
    hunk_plain_words,
    hunk_record,
    hunks_for_kind,
    index_plain_words,
    index_record,
    inspect_theatre_source,
    comment_for_hunk,
    comment_plain_words,
    comment_record,
    load_diff_theatre_final,
    load_diff_theatre_final_file,
    normalize_kind,
    normalize_stance,
    normalize_view_filter,
    panel_plain_words,
    panel_record,
    parse_theatre_args,
    passing_hunks,
    plain_lines,
    plain_words,
    shown_hunks,
    total_hunks,
    validate_book,
    validate_hunk,
    validate_comment,
    validate_panel,
    validate_row,
    validate_verdict,
    validate_view,
    verdict_plain_words,
    verdict_record,
    view_plain_words,
    view_record,
)
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.tui_redesign_charter import load_charter

ROOT = Path(__file__).resolve().parents[1]
ON = "2026-11-09"
BY = "the coordinator"
EXAMPLE_TITLE = "Diff theatre final form at the M-190 slice boundary"


def _hunk(**overrides):
    fields = {
        "hunk_id": "hunk-test",
        "seq": 1,
        "file": "A test file",
        "kind": "changed",
        "added": "3 lines",
        "removed": "2 lines",
        "target": "mythic_agent/core/session.py:128",
        "detail": "A test hunk held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "hunk-test",
    }
    fields.update(overrides)
    return build_hunk(fields)


def _stored_hunk(hunk):
    return hunk.to_record()


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "hunk-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _stored_view(view):
    return view.to_record()


def _comment(**overrides):
    fields = {
        "comment_id": "comment-test",
        "seq": 1,
        "hunk_id": "hunk-test",
        "stance": "note",
        "target": "the coder",
        "title": "A test comment",
        "detail": "A test comment held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "hunk-test",
    }
    fields.update(overrides)
    return build_comment(fields)


def _book(hunks=None, views=None, comments=None, **overrides):
    fields = {
        "schema": DIFF_THEATRE_FINAL_SCHEMA,
        "slice": "M-191",
        "theatre": {"title": "A test theatre book"},
        "hunks": [_stored_hunk(item) for item in (
            hunks if hunks is not None else [_hunk()])],
        "views": [_stored_view(item) for item in (
            views if views is not None else [_view()])],
        "comments": [item.to_record() for item in (comments or [])],
        "panels": [],
    }
    fields.update(overrides)
    return build_book(fields)


def _mixed_book():
    return _book(hunks=[
        _hunk(),
        _hunk(hunk_id="hunk-removed", seq=2,
                 file="A removed file", kind="removed",
                 added="", removed="", target=""),
    ])


# ---------------------------------------------------------------------
# The shipped example book, the roadmap and the charter.
# ---------------------------------------------------------------------


def test_shipped_book_loads_with_pinned_shape():
    book = load_diff_theatre_final()
    assert book.title == EXAMPLE_TITLE
    assert book.hunk_ids() == (
        "hunk-login-redirect", "hunk-costs-face-view",
        "hunk-flaky-gate-test", "hunk-gallery-guide",
        "hunk-store-sweep", "hunk-bank-m190-wave")
    assert [v.view_id for v in book.views] == [
        "view-all", "view-targeted"]
    assert [m.hunk_id for m in book.comments] == [
        "hunk-login-redirect",
        "hunk-gallery-guide"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m190-boundary"
    assert panel.as_of == "2026-11-10"
    assert [row.item_id for row in panel.rows] == list(book.hunk_ids())
    derived = derive_panel(book, "view-all")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 6
    assert panel.total_shown == derived.total_shown == 6
    assert {c.standing: c.items for c in panel.target_counts} == {
        "targeted": 5, "untargeted": 1}
    assert derive_verdict(book, "view-all").verdict == "strained"
    assert derive_verdict(book, "view-all").passing_shown == 5
    assert derive_verdict(book, "view-targeted").verdict == "open"
    assert derive_verdict(book, "view-targeted").passing_shown == 5
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / DIFF_THEATRE_FINAL_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == DIFF_THEATRE_FINAL_SCHEMA
    assert raw["slice"] == "M-191"
    assert "verdict" not in raw
    assert "theatre_index" not in raw


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-191")]
    assert slice_.title == "Diff theatre final form (with M-091)"
    assert slice_.part == 8
    assert "the review screen a user would" in slice_.summary
    assert "jump-to-file" in slice_.summary
    assert "comment-on-hunk feeding back to the coder" in slice_.summary
    assert DIFF_THEATRE_FINAL_SLICE == "M-191"


def test_charter_does_not_name_m191():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert owners.count("M-187") == 1
    assert "M-191" not in owners


def test_closed_vocabularies():
    assert TARGET_WORDS == ("targeted", "untargeted")
    assert KINDS == ("added", "removed", "changed", "mixed")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "targeted", "untargeted")
    assert VERDICT_WORDS == ("open", "strained", "shut")
    assert INDEX_ACTION == "index"
    assert EXAMPLE_TARGET == "mythic_agent/core/session.py:128"
    assert normalize_kind("CHANGED") == "changed"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    with pytest.raises(ValueError):
        normalize_kind("the void")
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    assert "held as data alone" in THEATRE_RULE
    assert "jumps to no file" in THEATRE_RULE
    assert "M-191" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /theatre")


def test_shipped_book_judged_honestly_as_data():
    book = load_diff_theatre_final()
    login = book.hunk_for("hunk-login-redirect")
    assert hunk_passes(login) is True
    assert hunk_gaps(login) == ()
    assert plain_lines(login) == (
        "Hunk: mythic_agent/core/session.py",
        "Kind: changed",
        "Added: 12 lines",
        "Removed: 4 lines",
        "Target: mythic_agent/core/session.py:128")
    addeds = book.hunk_for("hunk-costs-face-view")
    assert addeds.added == ""
    assert "Added: unknown" in plain_lines(addeds)
    flaky = book.hunk_for("hunk-flaky-gate-test")
    assert flaky.removed == ""
    assert "Removed: unknown" in plain_lines(flaky)
    sweep = book.hunk_for("hunk-store-sweep")
    assert hunk_gaps(sweep) == ("no jump target",)
    assert hunk_passes(sweep) is False
    assert [g.hunk_id for g in passing_hunks(book)] == [
        "hunk-login-redirect", "hunk-costs-face-view",
        "hunk-flaky-gate-test", "hunk-gallery-guide",
        "hunk-bank-m190-wave"]
    assert total_hunks(book) == 6
    index = derive_index(book)
    assert [e.target for e in index.entries] == [
        "mythic_agent/core/session.py:128", "mythic_agent/core/costs_face.py:12", "tests/test_part7_gate.py:41",
            "docs/gallery_guide.md:1", "mythic_agent/data/roadmap_slices.yaml:1180"]
    assert index.gaps == ("hunk-store-sweep",)
    assert hunk_for_target(book, "mythic_agent/core/session.py:128").hunk_id == (
        "hunk-login-redirect")
    assert hunk_for_target(book, "triple resume") is None
    assert first_comment(book).comment_id == "comment-note-login"
    assert comment_for_hunk(
        book, "hunk-login-redirect", "note").comment_id == (
            "comment-note-login")
    assert comment_for_hunk(book, "hunk-nope") is None


# ---------------------------------------------------------------------
# The held hunk: judged whole, its telling derived.
# ---------------------------------------------------------------------


def test_hunk_record_round_trips():
    hunk = _hunk()
    assert validate_hunk(hunk) is hunk
    rebuilt = build_hunk(_stored_hunk(hunk))
    assert rebuilt == hunk
    assert rebuilt.item_id == "hunk-test"
    assert rebuilt.target == "mythic_agent/core/session.py:128"
    record = hunk_record(hunk)
    assert record["type"] == "diff_hunk"
    assert record["passes"] is True
    assert record["gaps"] == []


def test_hunk_refuses_stored_judgements():
    for key in ("standing", "targeted", "gaps", "segment", "verdict",
                "index", "entries", "coverage"):
        fields = _stored_hunk(_hunk())
        fields[key] = "stored"
        with pytest.raises(ValueError):
            build_hunk(fields)
    fields = _stored_hunk(_hunk())
    fields["surprise"] = "stored"
    with pytest.raises(ValueError):
        build_hunk(fields)


def test_hunk_refuses_a_live_session_claim():
    for key in ("jumps_to_file", "jumped_to_file", "applies_hunk",
                "posted_comment", "opens_file"):
        fields = _stored_hunk(_hunk())
        fields[key] = True
        with pytest.raises(ValueError) as caught:
            build_hunk(fields)
        assert "held as data alone" in str(caught.value)
    for key in ("posts_comment", "jumped_to_file"):
        fields = _comment().to_record()
        fields[key] = True
        with pytest.raises(ValueError) as caught:
            build_comment(fields)
        assert "held as data alone" in str(caught.value)
    record = _comment(hunk_id="hunk-test")
    assert validate_comment(record) is record
    assert record.hunk_id == "hunk-test"
    assert comment_record(record)["type"] == "theatre_comment"


def test_hunk_vocabularies_are_closed():
    assert _hunk(kind="CHANGED").kind == "changed"
    assert _hunk(added="").added == ""
    assert _hunk(removed=None).removed == ""
    with pytest.raises(ValueError):
        _hunk(kind="a hunch")
    with pytest.raises(ValueError):
        _hunk(file="   ")
    with pytest.raises(ValueError):
        _hunk(seq=0)
    with pytest.raises(ValueError):
        _hunk(target=5)
    with pytest.raises(ValueError):
        _hunk(added=5)
    with pytest.raises(ValueError):
        _hunk(removed=5)
    with pytest.raises(ValueError):
        _hunk(detail="   ")


def test_plain_telling_derives_from_the_hunks_own_fields():
    hunk = _hunk(
        file="Test Session", kind="removed", added="", removed="",
        target="", detail="The target waits on a held hunk.")
    lines = plain_lines(hunk)
    assert lines[0] == "Hunk: Test Session"
    assert lines[1] == "Kind: removed"
    assert lines[2] == "Added: unknown"
    assert lines[3] == "Removed: unknown"
    assert lines[4] == "Target: none"
    assert plain_words(hunk) == hunk_plain_words(hunk)
    assert "Test Session" in plain_words(hunk)
    assert "held hunk" in plain_words(hunk)


def test_untargeted_hunk_stands_named_in_its_gaps():
    hunk = _hunk(target="")
    assert hunk_gaps(hunk) == ("no jump target",)
    assert hunk_passes(hunk) is False
    text = format_hunk(hunk)
    assert "stands untargeted" in text
    current_text = format_hunk(_hunk())
    assert "stands targeted" in current_text


def test_view_and_comment_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(_stored_view(view)) == view
    record = view_record(view)
    assert record["type"] == "theatre_view"
    assert record["view_filter"] == "all"
    assert "shows all hunks" in view_plain_words(view)
    assert "filter all" in format_view(view)
    with pytest.raises(ValueError):
        _view(view_filter="some")
    stance = _comment()
    assert build_comment(stance.to_record()) == stance
    assert "Hunk comment note hunk-test" in format_comment(stance)
    assert "jumps to no file" in format_comment(stance)
    assert "toward the coder" in comment_plain_words(stance)
    with pytest.raises(ValueError):
        _comment(stance="dance")


# ---------------------------------------------------------------------
# The index and the stance targets: derived at call time, never held.
# ---------------------------------------------------------------------


def test_index_is_derived_from_the_held_hunks_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.hunk_id for e in index.entries] == ["hunk-test"]
    assert index.entries[0].target == "mythic_agent/core/session.py:128"
    assert index.gaps == ("hunk-removed",)
    assert index_record(index)["type"] == "theatre_index"
    assert index_record(book)["gaps"] == ["hunk-removed"]
    assert "1 targets" in index_plain_words(book)
    text = format_index(book)
    assert "Hunk index" in text
    assert "mythic_agent/core/session.py:128 - A test file (hunk-test)" in text
    assert "hunk-removed" in text
    assert "jumps to no file" in text


def test_target_reaches_its_hunk_and_an_unheld_target_reaches_nothing():
    book = _mixed_book()
    assert hunk_for_target(book, "mythic_agent/core/session.py:128").hunk_id == "hunk-test"
    assert hunk_for_target(book, "triple resume") is None
    assert hunk_for_target(book, "") is None
    assert "A test file" in format_target(book, "mythic_agent/core/session.py:128")
    assert "reaches nothing in this book" in format_target(
        book, "triple resume")


def test_first_comment_is_held_as_data():
    book = _book(comments=[_comment(), _comment(
        comment_id="comment-two", seq=2, hunk_id="hunk-other",
        stance="question", title="The second stance")])
    assert first_comment(book).comment_id == "comment-test"
    assert comment_for_hunk(book, "hunk-other").comment_id == (
        "comment-two")
    assert comment_for_hunk(
        book, "hunk-other", "question").comment_id == "comment-two"
    assert comment_for_hunk(book, "hunk-other", "praise") is None
    bare = _book()
    assert first_comment(bare) is None
    assert comment_for_hunk(bare, "hunk-other") is None
    text = format_comment(first_comment(book))
    assert "held as data alone" in text
    assert "posts no comment" in text


def test_comment_targets_stand_held_whole():
    stance = _comment(
        hunk_id="hunk-x", stance="concern",
        target="a branched session")
    assert stance.stance == "concern"
    rebuilt = build_comment(stance.to_record())
    assert rebuilt == stance
    assert rebuilt.hunk_id == "hunk-x"
    assert rebuilt.target == "a branched session"
    with pytest.raises(ValueError):
        _comment(hunk_id="   ")
    with pytest.raises(ValueError):
        _comment(target="   ")
    with pytest.raises(ValueError):
        _comment(stance="teleport")


def test_panel_is_derived_and_a_stored_panel_must_agree():
    book = _mixed_book()
    panel = derive_panel(book)
    assert isinstance(panel, TheatrePanel)
    assert panel.total_items == 2
    assert panel.total_shown == 2
    assert validate_panel(panel, book) is panel
    assert build_panel(panel.to_record(), book).rows == panel.rows
    assert build_row(panel.rows[0], book.hunks[0]) == panel.rows[0]
    assert validate_row(panel.rows[0], book.hunks[0]) == panel.rows[0]
    tampered = dict(panel.to_record())
    tampered["total_shown"] = 99
    with pytest.raises(ValueError):
        build_panel(tampered, book)
    renamed = dict(panel.to_record())
    renamed["panel_id"] = "panel-renamed"
    assert build_panel(renamed, book).panel_id == "panel-renamed"
    record = panel_record(panel, book)
    assert record["type"] == "theatre_panel"
    assert record["panel_id"] == panel.panel_id


def test_verdict_is_derived_from_the_shown_hunks():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert isinstance(verdict, TheatreVerdict)
    assert verdict.verdict == "strained"
    assert verdict.total_shown == 2
    assert verdict.passing_shown == 1
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    record = verdict_record(verdict, book)
    assert record["type"] == "theatre_verdict"
    assert "strained" in verdict_plain_words(book)
    assert "strained" in format_verdict(book)


def test_verdict_open_and_shut_edges():
    whole = _book(hunks=[_hunk()])
    assert derive_verdict(whole).verdict == "open"
    absent_book = _book(hunks=[_hunk(target="")])
    assert derive_verdict(absent_book).verdict == "shut"
    none_shown = _book(
        hunks=[_hunk(target="")],
        views=[_view(view_filter="targeted")])
    verdict = derive_verdict(none_shown)
    assert verdict.total_shown == 0
    assert verdict.verdict == "shut"


def test_shown_and_kind_readings():
    book = _mixed_book()
    assert [g.hunk_id for g in shown_hunks(book)] == [
        "hunk-test", "hunk-removed"]
    targeted_view = _view(
        view_id="view-r", seq=2, view_filter="targeted")
    book2 = _book(
        hunks=[_hunk(), _hunk(
            hunk_id="hunk-removed", seq=2, file="A removed file",
            kind="removed", added="", removed="", target="")],
        views=[_view(), targeted_view])
    assert [g.hunk_id for g in shown_hunks(book2, targeted_view)] == [
        "hunk-test"]
    assert [g.hunk_id for g in hunks_for_kind(book2, "removed")] == [
        "hunk-removed"]
    assert [g.hunk_id for g in passing_hunks(book2)] == [
        "hunk-test"]
    assert total_hunks(book2) == 2
    with pytest.raises(ValueError):
        hunks_for_kind(book2, "the void")


def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(hunks=[_hunk(), _hunk(seq=2)])
    with pytest.raises(ValueError):
        _book(hunks=[_hunk(), _hunk(hunk_id="hunk-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(view_filter="targeted")])
    with pytest.raises(ValueError) as caught:
        _book(comments=[_comment(), _comment(comment_id="comment-two", seq=2)])
    assert "one stance stands per session target" in str(caught.value)
    fields = {
        "schema": DIFF_THEATRE_FINAL_SCHEMA, "slice": "M-191",
        "theatre": {"title": "A test theatre book"},
        "hunks": [_stored_hunk(_hunk())],
        "views": [_stored_view(_view())], "comments": [],
        "panels": [], "verdict": "open",
    }
    with pytest.raises(ValueError):
        build_book(fields)
    del fields["verdict"]
    fields["theatre_index"] = "stored"
    with pytest.raises(ValueError):
        build_book(fields)
    raw = {
        "schema": DIFF_THEATRE_FINAL_SCHEMA, "slice": "M-191",
        "theatre": {"title": "A test theatre book"},
        "hunks": [], "views": [], "comments": [], "panels": [],
        "jumps_to_file": True,
    }
    with pytest.raises(ValueError) as caught:
        build_book(raw)
    assert "held as data alone" in str(caught.value)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / DIFF_THEATRE_FINAL_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "diff_theatre_final.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_diff_theatre_final_file(path)
    assert book.title == EXAMPLE_TITLE
    assert total_hunks(book) == 6


def test_registry_holds_hunks_and_views_one_by_one():
    registry = DiffTheatreFinalRegistry()
    assert registry.list_items() == ()
    held = registry.register_hunk(_hunk())
    assert held.hunk_id == "hunk-test"
    registry.register_view(_view())
    assert [i.item_id if hasattr(i, "item_id") else i.view_id
            for i in registry.list_items()] == ["hunk-test", "view-test"]
    assert registry.get_hunk("hunk-test").file == "A test file"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.book().title == "An unheld theatre book"
    with pytest.raises(ValueError):
        registry.register_hunk(_hunk(seq=2))
    with pytest.raises(ValueError):
        registry.register_hunk(_hunk(hunk_id="hunk-two"))
    with pytest.raises(KeyError):
        registry.get_hunk("hunk-nope")


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = DiffTheatreFinalRegistry()
    book = _mixed_book()
    held = registry.register_book(book)
    assert held.title == "A test theatre book"
    assert len(registry.list_hunks()) == 2
    other = _book(hunks=[_hunk(
        hunk_id="hunk-x", seq=9, file="Other", target="mythic_agent/core/session.py:128")],
        views=[_view(view_id="view-x", seq=9)])
    object.__setattr__(other, "title", "Another title")
    with pytest.raises(ValueError):
        registry.register_book(other)


def test_plain_words_and_formatters():
    book = _mixed_book()
    assert "kind: 'changed'" in format_book(book)
    assert "hunk-removed" in format_book(book, "removed")
    assert "hunk-test" not in format_book(book, "removed")
    assert "Theatre panel under view view-test" in format_panel(book)
    assert panel_plain_words(book).startswith(
        "The theatre book holds 2 hunks")
    screen = format_theatre_screen(book)
    assert "Diff Theatre Final Form (M-191)" in screen
    assert PLAIN_EXPLANATION in screen
    assert "hunk-store-sweep" not in screen
    assert "hunk-removed" in screen
    record = book_record(book)
    assert record["type"] == "theatre_book"
    assert record["title"] == "A test theatre book"
    assert len(record["hunks"]) == 2
    panel = derive_panel(book)
    assert panel_record(panel, book)["rows"][0]["item_id"] == "hunk-test"
    assert verdict_record(derive_verdict(book), book)["verdict"] == (
        "strained")
    hunk_text = format_hunk(book.hunks[0])
    assert "Hunk: A test file" in hunk_text
    assert "Target: mythic_agent/core/session.py:128" in hunk_text


def test_parse_args_inspect_and_loader_targets():
    assert parse_theatre_args("") == ("show", None)
    assert parse_theatre_args("show") == ("show", None)
    assert parse_theatre_args(None) == ("show", None)
    assert parse_theatre_args("hunk hunk-test") == (
        "hunk", "hunk-test")
    assert parse_theatre_args("target resume from checkpoint") == (
        "target", "resume from checkpoint")
    assert parse_theatre_args("kind changed") == (
        "kind", "changed")
    assert parse_theatre_args("view view-test") == ("view", "view-test")
    assert parse_theatre_args("comment comment-test") == (
        "comment", "comment-test")
    assert parse_theatre_args("index") == ("index", None)
    assert parse_theatre_args("panel") == ("panel", None)
    assert parse_theatre_args("verdict") == ("verdict", None)
    for bad in ("dance", "hunk", "target", "kind", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_theatre_args(bad)
    hunk = _hunk()
    assert inspect_theatre_source(hunk) == {
        "kind": "hunk", "hunk_id": "hunk-test"}
    assert inspect_theatre_source(_stored_hunk(hunk))["kind"] == (
        "hunk")
    assert inspect_theatre_source(_stored_view(_view()))["kind"] == (
        "view")
    assert inspect_theatre_source(_comment().to_record())["kind"] == (
        "comment")
    assert inspect_theatre_source(42)["kind"] == "unknown"
    book = load_diff_theatre_final({
        "schema": DIFF_THEATRE_FINAL_SCHEMA, "slice": "M-191",
        "theatre": {"title": "A judged book"},
        "hunks": [_stored_hunk(_hunk())],
        "views": [_stored_view(_view())], "comments": [], "panels": []})
    assert isinstance(book, TheatreBook)
    assert book.title == "A judged book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_diff_theatre_final({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_diff_theatre_final({"slice": "M-999"})
    built = build_hunk(
        hunk_id="hunk-kw", seq=3, file="Kw Session",
        kind="changed", added="1 line", removed="1 line",
        target="mythic_agent/core/session.py:128", detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="hunk-test")
    assert built.hunk_id == "hunk-kw"
    assert hunk_passes(built) is True


