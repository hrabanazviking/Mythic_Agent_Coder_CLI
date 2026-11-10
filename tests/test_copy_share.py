"""M-195 Copy and Share - pure-layer tests.

TIER: integration

The pure layer is the copying and sharing, held
as data: one record per clip, held whole as a
card - under its heading, its kind in the closed
vocabulary (answer, diff, report, code, summary),
its format and its origin held honestly (unknown
stays empty, never invented), the clean markdown
it carries, named as data, and its detail - the
notes held as data beside them, each naming its
clip, its stance and its target, and the clip
index derived at call time from the held clips
alone, never stored where it could drift. A clip
naming no markdown body stands unready, named in
its gaps; two clips standing for one clip id
refuse by name, and one stance record stands per
clip stance. A record claiming a clip was
actually copied to a clipboard, actually shared,
sent or posted refuses by name, and a stored
index or verdict refuses by name. The panel is
derived for one held view and the verdict is
derived for the whole book under one view. The
shipped example book is held in a data file, and
a loader reads a book from any file. The M-171
charter names this slice on NO row, and the tests
pin that absence live. This layer copies nothing
to any clipboard, shares nothing, sends nothing,
posts nothing and opens no network: it holds the
copying and sharing as data and tells it.
"""


from pathlib import Path

import pytest
import yaml

from mythic_agent.core.copy_share import (
    KINDS,
    EXAMPLE_MARKDOWN,
    STANCES,
    INDEX_ACTION,
    COPY_SHARE_RESOURCE,
    COPY_SHARE_SCHEMA,
    COPY_SHARE_SLICE,
    SHARE_RULE,
    PLAIN_EXPLANATION,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    READY_WORDS,
    ClipCard,
    NoteRecord,
    ClipBook,
    ClipPanel,
    CopyShareRegistry,
    ClipVerdict,
    ClipView,
    book_record,
    build_book,
    build_clip,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    derive_index,
    derive_panel,
    derive_verdict,
    first_note,
    format_book,
    format_clip,
    format_index,
    format_note,
    format_share_screen,
    format_panel,
    format_markdown,
    format_verdict,
    format_view,
    clip_for_markdown,
    clip_gaps,
    clip_passes,
    clip_plain_words,
    clip_record,
    clips_for_kind,
    index_plain_words,
    index_record,
    inspect_clip_source,
    note_for_clip,
    note_plain_words,
    note_record,
    load_copy_share,
    load_copy_share_file,
    normalize_kind,
    normalize_stance,
    normalize_view_filter,
    panel_plain_words,
    panel_record,
    parse_share_args,
    passing_clips,
    plain_lines,
    plain_words,
    shown_clips,
    total_clips,
    validate_book,
    validate_clip,
    validate_note,
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
EXAMPLE_TITLE = "Copy and share at the M-194 slice boundary"


def _clip(**overrides):
    fields = {
        "clip_id": "clip-test",
        "seq": 1,
        "heading": "A test clip",
        "kind": "answer",
        "format": "80 columns",
        "origin": "24 rows",
        "markdown": "the answer in clean markdown",
        "detail": "A test clip held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "clip-test",
    }
    fields.update(overrides)
    return build_clip(fields)


def _stored_clip(clip):
    return clip.to_record()


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "clip-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _stored_view(view):
    return view.to_record()


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "clip_id": "clip-test",
        "stance": "note",
        "target": "the user",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "clip-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _book(clips=None, views=None, notes=None, **overrides):
    fields = {
        "schema": COPY_SHARE_SCHEMA,
        "slice": "M-195",
        "copy_share": {"title": "A test clip book"},
        "clips": [_stored_clip(item) for item in (
            clips if clips is not None else [_clip()])],
        "views": [_stored_view(item) for item in (
            views if views is not None else [_view()])],
        "notes": [item.to_record() for item in (notes or [])],
        "panels": [],
    }
    fields.update(overrides)
    return build_book(fields)


def _mixed_book():
    return _book(clips=[
        _clip(),
        _clip(clip_id="clip-code-only", seq=2,
              heading="A hidden clip", kind="code",
              format="", origin="", markdown=""),
    ])


def test_shipped_book_loads_with_pinned_shape():
    book = load_copy_share()
    assert book.title == EXAMPLE_TITLE
    assert book.clip_ids() == (
        "clip-answer-main", "clip-diff-main",
        "clip-report-main", "clip-summary-main",
        "clip-code-main", "clip-answer-chat")
    assert [v.view_id for v in book.views] == [
        "view-share", "view-ready"]
    assert [m.clip_id for m in book.notes] == [
        "clip-answer-main",
        "clip-diff-main"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m194-boundary"
    assert panel.as_of == "2026-11-10"
    assert [row.item_id for row in panel.rows] == list(book.clip_ids())
    derived = derive_panel(book, "view-share")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 6
    assert panel.total_shown == derived.total_shown == 6
    assert {c.standing: c.items for c in panel.target_counts} == {
        "ready": 5, "unready": 1}
    assert derive_verdict(book, "view-share").verdict == "strained"
    assert derive_verdict(book, "view-share").passing_shown == 5
    assert derive_verdict(book, "view-ready").verdict == "open"
    assert derive_verdict(book, "view-ready").passing_shown == 5
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / COPY_SHARE_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == COPY_SHARE_SCHEMA
    assert raw["slice"] == "M-195"
    assert "verdict" not in raw
    assert "share_index" not in raw


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-195")]
    assert slice_.title == "Copy and share"
    assert slice_.part == 8
    assert "copyable as clean markdown" in slice_.summary
    assert "shareable session summary" in slice_.summary
    assert "generated on command" in slice_.summary
    assert COPY_SHARE_SLICE == "M-195"


def test_charter_does_not_name_m195():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert owners.count("M-187") == 1
    assert "M-195" not in owners


def test_closed_vocabularies():
    assert READY_WORDS == ("ready", "unready")
    assert KINDS == ("answer", "diff", "report", "code", "summary")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "ready", "unready")
    assert VERDICT_WORDS == ("open", "strained", "shut")
    assert INDEX_ACTION == "index"
    assert EXAMPLE_MARKDOWN == "the answer in clean markdown"
    assert normalize_kind("ANSWER") == "answer"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    with pytest.raises(ValueError):
        normalize_kind("the void")
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    assert "held as data alone" in SHARE_RULE
    assert "copies nothing to any clipboard" in SHARE_RULE
    assert "M-195" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /copyshare")


def test_shipped_book_judged_honestly_as_data():
    book = load_copy_share()
    wordmark = book.clip_for("clip-answer-main")
    assert clip_passes(wordmark) is True
    assert clip_gaps(wordmark) == ()
    assert plain_lines(wordmark) == (
        "Clip: The last answer, ready to copy",
        "Kind: answer",
        "Format: markdown",
        "Origin: the last answer",
        "Markdown: the answer in clean markdown")
    loading = book.clip_for("clip-diff-main")
    assert loading.format == ""
    assert "Format: unknown" in plain_lines(loading)
    art = book.clip_for("clip-report-main")
    assert art.origin == ""
    assert "Origin: unknown" in plain_lines(art)
    sweep = book.clip_for("clip-code-main")
    assert clip_gaps(sweep) == ("no markdown body",)
    assert clip_passes(sweep) is False
    assert [g.clip_id for g in passing_clips(book)] == [
        "clip-answer-main", "clip-diff-main",
        "clip-report-main", "clip-summary-main",
        "clip-answer-chat"]
    assert total_clips(book) == 6
    index = derive_index(book)
    assert [e.markdown for e in index.entries] == [
        "the answer in clean markdown", "the diff in clean markdown",
        "the report in clean markdown", "the session summary in clean markdown",
        "the conversation and the question on the floor"]
    assert index.gaps == ("clip-code-main",)
    assert clip_for_markdown(book, "the answer in clean markdown").clip_id == (
        "clip-answer-main")
    assert clip_for_markdown(book, "triple resume") is None
    assert first_note(book).note_id == "note-note-answer"
    assert note_for_clip(
        book, "clip-answer-main", "note").note_id == (
            "note-note-answer")
    assert note_for_clip(book, "clip-nope") is None

# ---------------------------------------------------------------------
# The held clip: judged whole, its telling derived.
# ---------------------------------------------------------------------


def test_clip_record_round_trips():
    clip = _clip()
    assert validate_clip(clip) is clip
    rebuilt = build_clip(_stored_clip(clip))
    assert rebuilt == clip
    assert rebuilt.item_id == "clip-test"
    assert rebuilt.markdown == "the answer in clean markdown"
    record = clip_record(clip)
    assert record["type"] == "share_clip"
    assert record["passes"] is True
    assert record["gaps"] == []


def test_clip_refuses_stored_judgements():
    for key in ("standing", "ready", "gaps", "segment", "verdict",
                "index", "entries", "coverage"):
        fields = _stored_clip(_clip())
        fields[key] = "stored"
        with pytest.raises(ValueError):
            build_clip(fields)
    fields = _stored_clip(_clip())
    fields["surprise"] = "stored"
    with pytest.raises(ValueError):
        build_clip(fields)


def test_clip_refuses_a_live_session_claim():
    for key in ("shows_clip", "shown_clip", "plays_clip",
                "performed_clip", "posted_note", "copied_to_clipboard", "shared_live", "sent_clip"):
        fields = _stored_clip(_clip())
        fields[key] = True
        with pytest.raises(ValueError) as caught:
            build_clip(fields)
        assert "held as data alone" in str(caught.value)
    for key in ("posts_note", "shown_clip"):
        fields = _note().to_record()
        fields[key] = True
        with pytest.raises(ValueError) as caught:
            build_note(fields)
        assert "held as data alone" in str(caught.value)
    record = _note(clip_id="clip-test")
    assert validate_note(record) is record
    assert record.clip_id == "clip-test"
    assert note_record(record)["type"] == "share_note"


def test_clip_vocabularies_are_closed():
    assert _clip(kind="ANSWER").kind == "answer"
    assert _clip(format="").format == ""
    assert _clip(origin=None).origin == ""
    with pytest.raises(ValueError):
        _clip(kind="a hunch")
    with pytest.raises(ValueError):
        _clip(heading="   ")
    with pytest.raises(ValueError):
        _clip(seq=0)
    with pytest.raises(ValueError):
        _clip(markdown=5)
    with pytest.raises(ValueError):
        _clip(format=5)
    with pytest.raises(ValueError):
        _clip(origin=5)
    with pytest.raises(ValueError):
        _clip(detail="   ")


def test_plain_telling_derives_from_the_clips_own_fields():
    clip = _clip(
        heading="Test Clip", kind="diff", format="", origin="",
        markdown="", detail="The markdown waits on a held clip.")
    lines = plain_lines(clip)
    assert lines[0] == "Clip: Test Clip"
    assert lines[1] == "Kind: diff"
    assert lines[2] == "Format: unknown"
    assert lines[3] == "Origin: unknown"
    assert lines[4] == "Markdown: none"
    assert plain_words(clip) == clip_plain_words(clip)
    assert "Test Clip" in plain_words(clip)
    assert "held clip" in plain_words(clip)


def test_unready_clip_stands_named_in_its_gaps():
    clip = _clip(markdown="")
    assert clip_gaps(clip) == ("no markdown body",)
    assert clip_passes(clip) is False
    text = format_clip(clip)
    assert "stands unready" in text
    current_text = format_clip(_clip())
    assert "stands ready" in current_text


def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(_stored_view(view)) == view
    record = view_record(view)
    assert record["type"] == "share_view"
    assert record["view_filter"] == "all"
    assert "shows all clips" in view_plain_words(view)
    assert "filter all" in format_view(view)
    with pytest.raises(ValueError):
        _view(view_filter="some")
    stance = _note()
    assert build_note(stance.to_record()) == stance
    assert "Clip note note clip-test" in format_note(stance)
    assert "copies nothing to any clipboard" in format_note(stance)
    assert "toward the user" in note_plain_words(stance)
    with pytest.raises(ValueError):
        _note(stance="dance")


# ---------------------------------------------------------------------
# The index and the stance targets: derived at call time, never held.
# ---------------------------------------------------------------------


def test_index_is_derived_from_the_held_clips_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.clip_id for e in index.entries] == ["clip-test"]
    assert index.entries[0].markdown == "the answer in clean markdown"
    assert index.gaps == ("clip-code-only",)
    assert index_record(index)["type"] == "share_index"
    assert index_record(book)["gaps"] == ["clip-code-only"]
    assert "1 ready works" in index_plain_words(book)
    text = format_index(book)
    assert "Clip index" in text
    assert "the answer in clean markdown - A test clip (clip-test)" in text
    assert "clip-code-only" in text
    assert "copies nothing to any clipboard" in text


def test_target_reaches_its_clip_and_an_unheld_target_reaches_nothing():
    book = _mixed_book()
    assert clip_for_markdown(book, "the answer in clean markdown").clip_id == "clip-test"
    assert clip_for_markdown(book, "triple resume") is None
    assert clip_for_markdown(book, "") is None
    assert "A test clip" in format_markdown(book, "the answer in clean markdown")
    assert "reaches nothing in this book" in format_markdown(
        book, "triple resume")


def test_first_note_is_held_as_data():
    book = _book(notes=[_note(), _note(
        note_id="note-two", seq=2, clip_id="clip-other",
        stance="question", title="The second stance")])
    assert first_note(book).note_id == "note-test"
    assert note_for_clip(book, "clip-other").note_id == (
        "note-two")
    assert note_for_clip(
        book, "clip-other", "question").note_id == "note-two"
    assert note_for_clip(book, "clip-other", "praise") is None
    bare = _book()
    assert first_note(bare) is None
    assert note_for_clip(bare, "clip-other") is None
    text = format_note(first_note(book))
    assert "held as data alone" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    stance = _note(
        clip_id="clip-x", stance="concern",
        target="a branched session")
    assert stance.stance == "concern"
    rebuilt = build_note(stance.to_record())
    assert rebuilt == stance
    assert rebuilt.clip_id == "clip-x"
    assert rebuilt.target == "a branched session"
    with pytest.raises(ValueError):
        _note(clip_id="   ")
    with pytest.raises(ValueError):
        _note(target="   ")
    with pytest.raises(ValueError):
        _note(stance="teleport")


def test_panel_is_derived_and_a_stored_panel_must_agree():
    book = _mixed_book()
    panel = derive_panel(book)
    assert isinstance(panel, ClipPanel)
    assert panel.total_items == 2
    assert panel.total_shown == 2
    assert validate_panel(panel, book) is panel
    assert build_panel(panel.to_record(), book).rows == panel.rows
    assert build_row(panel.rows[0], book.clips[0]) == panel.rows[0]
    assert validate_row(panel.rows[0], book.clips[0]) == panel.rows[0]
    tampered = dict(panel.to_record())
    tampered["total_shown"] = 99
    with pytest.raises(ValueError):
        build_panel(tampered, book)
    renamed = dict(panel.to_record())
    renamed["panel_id"] = "panel-renamed"
    assert build_panel(renamed, book).panel_id == "panel-renamed"
    record = panel_record(panel, book)
    assert record["type"] == "share_panel"
    assert record["panel_id"] == panel.panel_id


def test_verdict_is_derived_from_the_shown_clips():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert isinstance(verdict, ClipVerdict)
    assert verdict.verdict == "strained"
    assert verdict.total_shown == 2
    assert verdict.passing_shown == 1
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    record = verdict_record(verdict, book)
    assert record["type"] == "share_verdict"
    assert "strained" in verdict_plain_words(book)
    assert "strained" in format_verdict(book)


def test_verdict_open_and_shut_edges():
    whole = _book(clips=[_clip()])
    assert derive_verdict(whole).verdict == "open"
    absent_book = _book(clips=[_clip(markdown="")])
    assert derive_verdict(absent_book).verdict == "shut"
    none_shown = _book(
        clips=[_clip(markdown="")],
        views=[_view(view_filter="ready")])
    verdict = derive_verdict(none_shown)
    assert verdict.total_shown == 0
    assert verdict.verdict == "shut"


def test_shown_and_kind_readings():
    book = _mixed_book()
    assert [g.clip_id for g in shown_clips(book)] == [
        "clip-test", "clip-code-only"]
    ready_view = _view(
        view_id="view-r", seq=2, view_filter="ready")
    book2 = _book(
        clips=[_clip(), _clip(
            clip_id="clip-code-only", seq=2, heading="A hidden clip",
            kind="code", format="", origin="", markdown="")],
        views=[_view(), ready_view])
    assert [g.clip_id for g in shown_clips(book2, ready_view)] == [
        "clip-test"]
    assert [g.clip_id for g in clips_for_kind(book2, "code")] == [
        "clip-code-only"]
    assert [g.clip_id for g in passing_clips(book2)] == [
        "clip-test"]
    assert total_clips(book2) == 2
    with pytest.raises(ValueError):
        clips_for_kind(book2, "the void")


def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(clips=[_clip(), _clip(seq=2)])
    with pytest.raises(ValueError):
        _book(clips=[_clip(), _clip(clip_id="clip-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(view_filter="ready")])
    with pytest.raises(ValueError) as caught:
        _book(notes=[_note(), _note(note_id="note-two", seq=2)])
    assert "one stance stands per session target" in str(caught.value)
    fields = {
        "schema": COPY_SHARE_SCHEMA, "slice": "M-195",
        "copy_share": {"title": "A test clip book"},
        "clips": [_stored_clip(_clip())],
        "views": [_stored_view(_view())], "notes": [],
        "panels": [], "verdict": "open",
    }
    with pytest.raises(ValueError):
        build_book(fields)
    del fields["verdict"]
    fields["share_index"] = "stored"
    with pytest.raises(ValueError):
        build_book(fields)
    raw = {
        "schema": COPY_SHARE_SCHEMA, "slice": "M-195",
        "copy_share": {"title": "A test clip book"},
        "clips": [], "views": [], "notes": [], "panels": [],
        "shows_clip": True,
    }
    with pytest.raises(ValueError) as caught:
        build_book(raw)
    assert "held as data alone" in str(caught.value)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / COPY_SHARE_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "copy_share.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_copy_share_file(path)
    assert book.title == EXAMPLE_TITLE
    assert total_clips(book) == 6


def test_registry_holds_clips_and_views_one_by_one():
    registry = CopyShareRegistry()
    assert registry.list_items() == ()
    held = registry.register_clip(_clip())
    assert held.clip_id == "clip-test"
    registry.register_view(_view())
    assert [i.item_id if hasattr(i, "item_id") else i.view_id
            for i in registry.list_items()] == ["clip-test", "view-test"]
    assert registry.get_clip("clip-test").heading == "A test clip"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.book().title == "An unheld clip book"
    with pytest.raises(ValueError):
        registry.register_clip(_clip(seq=2))
    with pytest.raises(ValueError):
        registry.register_clip(_clip(clip_id="clip-two"))
    with pytest.raises(KeyError):
        registry.get_clip("clip-nope")


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = CopyShareRegistry()
    book = _mixed_book()
    held = registry.register_book(book)
    assert held.title == "A test clip book"
    assert len(registry.list_clips()) == 2
    other = _book(clips=[_clip(
        clip_id="clip-x", seq=9, heading="Other", markdown="the answer in clean markdown")],
        views=[_view(view_id="view-x", seq=9)])
    object.__setattr__(other, "title", "Another title")
    with pytest.raises(ValueError):
        registry.register_book(other)


def test_plain_words_and_formatters():
    book = _mixed_book()
    assert "kind: 'answer'" in format_book(book)
    assert "clip-code-only" in format_book(book, "code")
    assert "clip-test" not in format_book(book, "code")
    assert "Share panel under view view-test" in format_panel(book)
    assert panel_plain_words(book).startswith(
        "The share book holds 2 clips")
    screen = format_share_screen(book)
    assert "Copy and Share (M-195)" in screen
    assert PLAIN_EXPLANATION in screen
    assert "clip-code-sweep" not in screen
    assert "clip-code-only" in screen
    record = book_record(book)
    assert record["type"] == "share_book"
    assert record["title"] == "A test clip book"
    assert len(record["clips"]) == 2
    panel = derive_panel(book)
    assert panel_record(panel, book)["rows"][0]["item_id"] == "clip-test"
    assert verdict_record(derive_verdict(book), book)["verdict"] == (
        "strained")
    clip_text = format_clip(book.clips[0])
    assert "Clip: A test clip" in clip_text
    assert "Markdown: the answer in clean markdown" in clip_text


def test_parse_args_inspect_and_loader_targets():
    assert parse_share_args("") == ("show", None)
    assert parse_share_args("show") == ("show", None)
    assert parse_share_args(None) == ("show", None)
    assert parse_share_args("clip clip-test") == (
        "clip", "clip-test")
    assert parse_share_args("markdown the answer in clean markdown") == (
        "markdown", "the answer in clean markdown")
    assert parse_share_args("kind answer") == (
        "kind", "answer")
    assert parse_share_args("view view-test") == ("view", "view-test")
    assert parse_share_args("note note-test") == (
        "note", "note-test")
    assert parse_share_args("index") == ("index", None)
    assert parse_share_args("panel") == ("panel", None)
    assert parse_share_args("verdict") == ("verdict", None)
    for bad in ("dance", "clip", "markdown", "kind", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_share_args(bad)
    clip = _clip()
    assert inspect_clip_source(clip) == {
        "kind": "clip", "clip_id": "clip-test"}
    assert inspect_clip_source(_stored_clip(clip))["kind"] == (
        "clip")
    assert inspect_clip_source(_stored_view(_view()))["kind"] == (
        "view")
    assert inspect_clip_source(_note().to_record())["kind"] == (
        "note")
    assert inspect_clip_source(42)["kind"] == "unknown"
    book = load_copy_share({
        "schema": COPY_SHARE_SCHEMA, "slice": "M-195",
        "copy_share": {"title": "A judged book"},
        "clips": [_stored_clip(_clip())],
        "views": [_stored_view(_view())], "notes": [], "panels": []})
    assert isinstance(book, ClipBook)
    assert book.title == "A judged book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_copy_share({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_copy_share({"slice": "M-999"})
    built = build_clip(
        clip_id="clip-kw", seq=3, heading="Kw Clip",
        kind="answer", format="80 columns", origin="24 rows",
        markdown="the answer in clean markdown", detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="clip-test")
    assert built.clip_id == "clip-kw"
    assert clip_passes(built) is True


# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-195 agent layer: the agent holds a clip book
# for the session, clips and views are published
# as session news through the checkpoint target
# (journal first, deduped per shape), the panel
# and verdict are derived at call time from the
# whole book under a view, never held, the index
# is derived from the book's held clips, and the
# stance targets are held as data beside them -
# holding one resumes no session. This layer
# resumes nothing, renders no live UI, exports
# nothing and persists nothing beyond the
# session journal news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _clip_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_clip_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / COPY_SHARE_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "copy_share.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestShareAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.copy_share_status()
        assert status["clips"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["copy_share"]["title"] == EXAMPLE_TITLE
        assert len(status["copy_share"]["clips"]) == 6
        assert len(status["copy_share"]["views"]) == 2
        assert len(status["copy_share"]["notes"]) == 2
        assert status["panel"]["total_items"] == 6
        assert status["panel"]["total_shown"] == 6
        assert status["panels"][0]["panel_id"] == "panel-m194-boundary"
        assert status["verdict"]["verdict"] == "strained"
        assert status["verdict"]["passing_shown"] == 5
        assert [e["markdown"] for e in status["index"]["entries"]] == ["the answer in clean markdown", "the diff in clean markdown", "the report in clean markdown", "the session summary in clean markdown", "the conversation and the question on the floor"]
        assert status["index"]["gaps"] == ["clip-code-main"]
        assert status["first_note"]["note_id"] == "note-note-answer"
        assert "held as data alone" in status["rule"]
        assert "the conversation and the question on the floor" in status["plain_words"]
        assert "Copy and Share (M-195)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._copy_share_registry()
        assert agent._copy_share_registry() is first
        assert agent._copy_share_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.copy_share_status()
        assert agent.get_share_clip(
            "clip-answer-main").heading == "The last answer, ready to copy"
        assert agent.get_share_view("view-share").view_filter == "all"
        assert agent.get_share_note(
            "note-note-answer").note_id == "note-note-answer"
        assert [a.clip_id for a in agent.share_clips_for_kind(
            "answer")] == ["clip-answer-main", "clip-answer-chat"]
        assert [a.clip_id for a in agent.share_clips_for_kind(
            "diff")] == ["clip-diff-main"]
        assert [a.clip_id for a in agent.share_clips_passing()] == [
            "clip-answer-main", "clip-diff-main",
            "clip-report-main", "clip-summary-main",
            "clip-answer-chat"]
        agent.copy_share_panel()
        agent.copy_share_verdict()
        agent.share_index()
        agent.report_copy_share()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("share")
                or e["type"] == "share_clip"] == []
        with pytest.raises(KeyError):
            agent.get_share_clip("clip-nope")
        with pytest.raises(KeyError):
            agent.get_share_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_share_note("note-nope")
        with pytest.raises(ValueError):
            agent.share_clips_for_kind("the void")
        agent.close()

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_share_clip(_clip())
        status = agent.copy_share_status()
        assert [a["clip_id"] for a in status["clips"]] == ["clip-test"]
        assert status["book"]["title"] == "An unheld clip book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["markdown"] for e in status["index"]["entries"]] == [
            "the answer in clean markdown"]
        assert status["first_note"] is None
        assert "clip-test" in status["screen"]

    def test_held_clip_never_falls_back_to_the_example(
            self, agent):
        agent.register_share_clip(_clip())
        with pytest.raises(KeyError):
            agent.get_share_clip("clip-answer-main")
        with pytest.raises(KeyError):
            agent.get_share_view("view-share")
        with pytest.raises(KeyError):
            agent.get_share_note("modal")
        clip = agent.get_share_clip("clip-test")
        assert clip.heading == "A test clip"
        assert agent.copy_share_book().title == (
            "An unheld clip book")

    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_share_note("note-note-answer")
        assert first.note_id == "note-note-answer"
        assert first.clip_id == "clip-answer-main"
        status = agent.copy_share_status()
        assert status["index"]["gaps"] == ["clip-code-main"]
        assert status["first_note"]["clip_id"] == (
            "clip-answer-main")
        assert status["first_note"]["stance"] == "note"


class TestShareAgentHolding:
    def test_register_clip_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_share_clip(_clip())
        assert result["clip"]["clip_id"] == "clip-test"
        assert result["record_news"]["type"] == "share_clip"
        assert "clip-test" in result["screen"]
        events = _clip_events(store, session_id, "share_clip")
        assert len(events) == 1
        agent.close()

    def test_duplicate_clip_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_share_clip(_clip())
        with pytest.raises(ValueError):
            agent.register_share_clip(_clip(seq=9))
        with pytest.raises(ValueError):
            agent.register_share_clip(_clip(clip_id="clip-two"))
        events = _clip_events(store, session_id, "share_clip")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_share_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_clip_events(
            store, session_id, "share_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_share_clip(_clip())
        result = agent.view_share("ready")
        assert result["view"]["view_filter"] == "ready"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "share_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "open"
        assert len(_clip_events(
            store, session_id, "share_view")) == 1
        assert len(_clip_events(
            store, session_id, "share_panel")) == 1
        assert len(_clip_events(
            store, session_id, "share_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_share_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "share_clip", "share_view"]
        assert len(_clip_events(
            store, session_id, "share_clip")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_share_book()
        assert result["count"] == 6
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "share_panel"
        assert result["index_record"]["gaps"] == [
            "clip-code-main"]
        with pytest.raises(ValueError):
            agent.record_share_book()
        assert len(_clip_events(
            store, session_id, "share_clip")) == 6
        assert len(_clip_events(
            store, session_id, "share_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_clip_book_file(tmp_path)
        book = load_copy_share_file(path)
        result = agent.record_share_book(book)
        assert result["count"] == 6
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_copy_share()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "strained"
        assert report["index"]["gaps"] == ["clip-code-main"]
        assert "clip-answer-main" in report["book_text"]
        assert "the answer in clean markdown - The last answer, ready to copy (clip-answer-main)" in report["index_text"]
        agent.register_share_clip(_clip())
        report = agent.report_copy_share()
        assert report["book"]["title"] == "An unheld clip book"
        assert report["panel"] is None
        assert report["verdict"] is None


class TestShareTerminalHeading:
    def test_show_clip_target_kind_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/copyshare")
        assert "Copy and Share (M-195)" in text
        _, _, text = _slash(agent, "/copyshare clip clip-answer-main")
        assert "Clip: The last answer, ready to copy" in text
        _, _, text = _slash(agent, "/copyshare markdown the answer in clean markdown")
        assert "the answer in clean markdown" in text
        _, _, text = _slash(agent, "/copyshare markdown triple resume")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/copyshare kind answer")
        assert "clip-answer-main" in text
        assert "clip-code-main" not in text
        _, _, text = _slash(agent, "/copyshare view view-share")
        assert "filter all" in text
        _, _, text = _slash(agent, "/copyshare note note-note-answer")
        assert "Clip note note clip-answer-main" in text
        _, _, text = _slash(agent, "/copyshare index")
        assert "Clip index" in text
        assert "clip-summary-main" in text
        _, _, text = _slash(agent, "/copyshare panel")
        assert "Share panel under view view-share" in text
        _, _, text = _slash(agent, "/copyshare verdict")
        assert "strained" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/copyshare [show|clip <clip-id>"
                "|markdown <markdown>|kind <kind>|view <view-id>"
                "|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/copyshare dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/copyshare clip clip-nope")
        assert "no clip named" in text


@pytest.fixture()
def share_handler(agent, monkeypatch):
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


def _clip_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestShareCommand:
    def test_show_is_default(self, share_handler, agent):
        share_handler._handle_copyshare("")
        assert "Copy and Share (M-195)" in (
            _clip_published_text(share_handler))

    def test_clip_target_kind_view_note_index_panel_verdict(
            self, share_handler, agent):
        share_handler._handle_copyshare("clip clip-answer-main")
        assert "Clip: The last answer, ready to copy" in _clip_published_text(
            share_handler)
        share_handler._handle_copyshare("markdown the answer in clean markdown")
        assert "the answer in clean markdown" in _clip_published_text(
            share_handler)
        share_handler._handle_copyshare("kind answer")
        assert "clip-answer-main" in _clip_published_text(share_handler)
        share_handler._handle_copyshare("view view-share")
        assert "filter all" in _clip_published_text(share_handler)
        share_handler._handle_copyshare("note note-note-answer")
        assert "Clip note note clip-answer-main" in _clip_published_text(share_handler)
        share_handler._handle_copyshare("index")
        assert "Clip index" in _clip_published_text(share_handler)
        share_handler._handle_copyshare("panel")
        assert "Share panel under view" in _clip_published_text(
            share_handler)
        share_handler._handle_copyshare("verdict")
        assert "strained" in _clip_published_text(share_handler)

    def test_bad_grammar_is_published(
            self, share_handler, agent):
        share_handler._handle_copyshare("dance party")
        assert USAGE in _clip_published_text(share_handler)
        share_handler._handle_copyshare("clip clip-nope")
        assert "no clip named" in _clip_published_text(share_handler)


class TestChatScreenRoutingShare:
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
        screen.handle_command("/copyshare panel", _FakeLog())
        assert calls == [("/copyshare", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/copyshare[/green] - show copy and share (M-195)" in (
            text)
        assert ('"/copyshare": "Usage: /copyshare | '
                '/copyshare clip <clip-id>') in text


class TestShareDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.copy_share_panel()
        assert panel.total_shown == 6
        assert panel.panel_id == "panel-view-share"
        verdict = agent.copy_share_verdict()
        assert verdict.verdict == "strained"
        found = agent.copy_share_verdict("view-ready")
        assert found.verdict == "open"
        assert found.passing_shown == 5
        agent.register_share_clip(_clip())
        with pytest.raises(ValueError):
            agent.copy_share_panel()
        with pytest.raises(ValueError):
            agent.copy_share_verdict()

    def test_view_target_over_an_unshown_filter_is_shut(self, agent):
        agent.register_share_clip(_clip(markdown=""))
        result = agent.view_share("ready")
        assert result["verdict_record"]["verdict"] == "shut"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.share_index()
        assert [e["markdown"] for e in result["index"]["entries"]] == ["the answer in clean markdown", "the diff in clean markdown", "the report in clean markdown", "the session summary in clean markdown", "the conversation and the question on the floor"]
        assert result["index"]["gaps"] == ["clip-code-main"]
        assert "the answer in clean markdown - The last answer, ready to copy (clip-answer-main)" in (
            result["index_text"])
        clip = agent.get_share_clip("clip-code-main")
        assert clip_gaps(clip) == ("no markdown body",)
        assert clip_passes(clip) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("share")
                or e["type"] == "share_clip"] == []
        agent.close()
