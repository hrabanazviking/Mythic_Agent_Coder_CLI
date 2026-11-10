"""M-193 Splash and Ceremony, Restrained - pure-layer tests.

TIER: integration

The pure layer is the ceremony, held as data:
one record per moment, held whole as a card -
under its occasion, its kind in the closed
vocabulary (wordmark, status, art, silence),
its duration and its budget held honestly
(unknown stays empty, never invented), the
text alternative it carries, named as data,
and its detail - the notes held as data beside
them, each naming its moment, its stance and
its target, and the ceremony index derived at
call time from the held moments alone, never
stored where it could drift. A moment naming
no text alternative stands unalternated, named
in its gaps; two moments standing for one
moment id refuse by name, and one stance
record stands per moment stance. A record
claiming a ceremony actually showed, played
or performed refuses by name, and a stored
index or verdict refuses by name. The panel
is derived for one held view and the verdict
is derived for the whole book under one view.
The shipped example book is held in a data
file, and a loader reads a book from any file.
The M-171 charter names this slice on screen
S-01 (the splash screen), and the tests pin
that ownership live. This layer shows no
splash, plays no ceremony, performs nothing
and opens no network: it holds the ceremony
as data and tells it.
"""


from pathlib import Path

import pytest
import yaml

from mythic_agent.core.splash_ceremony import (
    KINDS,
    EXAMPLE_ALTERNATIVE,
    STANCES,
    INDEX_ACTION,
    SPLASH_CEREMONY_RESOURCE,
    SPLASH_CEREMONY_SCHEMA,
    SPLASH_CEREMONY_SLICE,
    CEREMONY_RULE,
    PLAIN_EXPLANATION,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    ALTERN_WORDS,
    MomentCard,
    NoteRecord,
    MomentBook,
    MomentPanel,
    SplashCeremonyRegistry,
    MomentVerdict,
    MomentView,
    book_record,
    build_book,
    build_moment,
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
    format_moment,
    format_index,
    format_note,
    format_ceremony_screen,
    format_panel,
    format_alternative,
    format_verdict,
    format_view,
    moment_for_alternative,
    moment_gaps,
    moment_passes,
    moment_plain_words,
    moment_record,
    moments_for_kind,
    index_plain_words,
    index_record,
    inspect_moment_source,
    note_for_moment,
    note_plain_words,
    note_record,
    load_splash_ceremony,
    load_splash_ceremony_file,
    normalize_kind,
    normalize_stance,
    normalize_view_filter,
    panel_plain_words,
    panel_record,
    parse_ceremony_args,
    passing_moments,
    plain_lines,
    plain_words,
    shown_moments,
    total_moments,
    validate_book,
    validate_moment,
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
EXAMPLE_TITLE = "Splash and ceremony at the M-192 slice boundary"


def _moment(**overrides):
    fields = {
        "moment_id": "moment-test",
        "seq": 1,
        "occasion": "A test moment",
        "kind": "wordmark",
        "duration": "3 seconds",
        "budget": "accent 5 percent",
        "text_alternative": "Mythic Agent Coder",
        "detail": "A test moment held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "moment-test",
    }
    fields.update(overrides)
    return build_moment(fields)


def _stored_moment(moment):
    return moment.to_record()


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "moment-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _stored_view(view):
    return view.to_record()


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "moment_id": "moment-test",
        "stance": "note",
        "target": "the user",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "moment-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _book(moments=None, views=None, notes=None, **overrides):
    fields = {
        "schema": SPLASH_CEREMONY_SCHEMA,
        "slice": "M-193",
        "splash_ceremony": {"title": "A test moment book"},
        "moments": [_stored_moment(item) for item in (
            moments if moments is not None else [_moment()])],
        "views": [_stored_view(item) for item in (
            views if views is not None else [_view()])],
        "notes": [item.to_record() for item in (notes or [])],
        "panels": [],
    }
    fields.update(overrides)
    return build_book(fields)


def _mixed_book():
    return _book(moments=[
        _moment(),
        _moment(moment_id="moment-silence-only", seq=2,
              occasion="A silence moment", kind="silence",
              duration="", budget="", text_alternative=""),
    ])


def test_shipped_book_loads_with_pinned_shape():
    book = load_splash_ceremony()
    assert book.title == EXAMPLE_TITLE
    assert book.moment_ids() == (
        "moment-wordmark-start", "moment-status-loading",
        "moment-art-longship", "moment-status-ready",
        "moment-silence-work", "moment-wordmark-complete")
    assert [v.view_id for v in book.views] == [
        "view-ceremony", "view-alternated"]
    assert [m.moment_id for m in book.notes] == [
        "moment-wordmark-start",
        "moment-status-loading"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m192-boundary"
    assert panel.as_of == "2026-11-10"
    assert [row.item_id for row in panel.rows] == list(book.moment_ids())
    derived = derive_panel(book, "view-ceremony")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 6
    assert panel.total_shown == derived.total_shown == 6
    assert {c.standing: c.items for c in panel.target_counts} == {
        "alternated": 5, "unalternated": 1}
    assert derive_verdict(book, "view-ceremony").verdict == "strained"
    assert derive_verdict(book, "view-ceremony").passing_shown == 5
    assert derive_verdict(book, "view-alternated").verdict == "open"
    assert derive_verdict(book, "view-alternated").passing_shown == 5
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / SPLASH_CEREMONY_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == SPLASH_CEREMONY_SCHEMA
    assert raw["slice"] == "M-193"
    assert "verdict" not in raw
    assert "ceremony_index" not in raw


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-193")]
    assert slice_.title == "Splash and ceremony, restrained"
    assert slice_.part == 8
    assert "keeps its beauty" in slice_.summary
    assert "ceremony at start" in slice_.summary
    assert "quiet the rest of the time" in slice_.summary
    assert SPLASH_CEREMONY_SLICE == "M-193"


def test_charter_names_m193_on_the_splash_screen():
    charter = load_charter()
    screen = charter.screen("splash")
    assert screen.id == "S-01"
    assert screen.verdict == "rebuild"
    assert "M-193" in screen.owning_slices
    assert "M-184" in screen.owning_slices
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners.count("M-193") == 1
    assert "text alternative" in screen.direction


def test_closed_vocabularies():
    assert ALTERN_WORDS == ("alternated", "unalternated")
    assert KINDS == ("wordmark", "status", "art", "silence")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "alternated", "unalternated")
    assert VERDICT_WORDS == ("open", "strained", "shut")
    assert INDEX_ACTION == "index"
    assert EXAMPLE_ALTERNATIVE == "Mythic Agent Coder"
    assert normalize_kind("WORDMARK") == "wordmark"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    with pytest.raises(ValueError):
        normalize_kind("the void")
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    assert "held as data alone" in CEREMONY_RULE
    assert "shows no splash" in CEREMONY_RULE
    assert "M-193" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /ceremony")


def test_shipped_book_judged_honestly_as_data():
    book = load_splash_ceremony()
    wordmark = book.moment_for("moment-wordmark-start")
    assert moment_passes(wordmark) is True
    assert moment_gaps(wordmark) == ()
    assert plain_lines(wordmark) == (
        "Moment: Wordmark at start",
        "Kind: wordmark",
        "Duration: 2 seconds",
        "Budget: accent 8 percent",
        "Alternative: Mythic Agent Coder")
    loading = book.moment_for("moment-status-loading")
    assert loading.duration == ""
    assert "Duration: unknown" in plain_lines(loading)
    art = book.moment_for("moment-art-longship")
    assert art.budget == ""
    assert "Budget: unknown" in plain_lines(art)
    sweep = book.moment_for("moment-silence-work")
    assert moment_gaps(sweep) == ("no text alternative",)
    assert moment_passes(sweep) is False
    assert [g.moment_id for g in passing_moments(book)] == [
        "moment-wordmark-start", "moment-status-loading",
        "moment-art-longship", "moment-status-ready",
        "moment-wordmark-complete"]
    assert total_moments(book) == 6
    index = derive_index(book)
    assert [e.alternative for e in index.entries] == [
        "Mythic Agent Coder", "Loading the forge: provider, model and tools.",
        "A longship under sail, drawn in line art.", "Ready - the chat stands open.",
        "Roadmap complete - all 272 slices stand banked."]
    assert index.gaps == ("moment-silence-work",)
    assert moment_for_alternative(book, "Mythic Agent Coder").moment_id == (
        "moment-wordmark-start")
    assert moment_for_alternative(book, "triple resume") is None
    assert first_note(book).note_id == "note-note-wordmark"
    assert note_for_moment(
        book, "moment-wordmark-start", "note").note_id == (
            "note-note-wordmark")
    assert note_for_moment(book, "moment-nope") is None


# ---------------------------------------------------------------------
# The held moment: judged whole, its telling derived.
# ---------------------------------------------------------------------


def test_moment_record_round_trips():
    moment = _moment()
    assert validate_moment(moment) is moment
    rebuilt = build_moment(_stored_moment(moment))
    assert rebuilt == moment
    assert rebuilt.item_id == "moment-test"
    assert rebuilt.text_alternative == "Mythic Agent Coder"
    record = moment_record(moment)
    assert record["type"] == "ceremony_moment"
    assert record["passes"] is True
    assert record["gaps"] == []


def test_moment_refuses_stored_judgements():
    for key in ("standing", "alternated", "gaps", "segment", "verdict",
                "index", "entries", "coverage"):
        fields = _stored_moment(_moment())
        fields[key] = "stored"
        with pytest.raises(ValueError):
            build_moment(fields)
    fields = _stored_moment(_moment())
    fields["surprise"] = "stored"
    with pytest.raises(ValueError):
        build_moment(fields)


def test_moment_refuses_a_live_session_claim():
    for key in ("shows_moment", "shown_moment", "plays_moment",
                "performed_moment", "posted_note"):
        fields = _stored_moment(_moment())
        fields[key] = True
        with pytest.raises(ValueError) as caught:
            build_moment(fields)
        assert "held as data alone" in str(caught.value)
    for key in ("posts_note", "shown_moment"):
        fields = _note().to_record()
        fields[key] = True
        with pytest.raises(ValueError) as caught:
            build_note(fields)
        assert "held as data alone" in str(caught.value)
    record = _note(moment_id="moment-test")
    assert validate_note(record) is record
    assert record.moment_id == "moment-test"
    assert note_record(record)["type"] == "ceremony_note"


def test_moment_vocabularies_are_closed():
    assert _moment(kind="WORDMARK").kind == "wordmark"
    assert _moment(duration="").duration == ""
    assert _moment(budget=None).budget == ""
    with pytest.raises(ValueError):
        _moment(kind="a hunch")
    with pytest.raises(ValueError):
        _moment(occasion="   ")
    with pytest.raises(ValueError):
        _moment(seq=0)
    with pytest.raises(ValueError):
        _moment(text_alternative=5)
    with pytest.raises(ValueError):
        _moment(duration=5)
    with pytest.raises(ValueError):
        _moment(budget=5)
    with pytest.raises(ValueError):
        _moment(detail="   ")


def test_plain_telling_derives_from_the_moments_own_fields():
    moment = _moment(
        occasion="Test Moment", kind="status", duration="", budget="",
        text_alternative="", detail="The alternative waits on a held moment.")
    lines = plain_lines(moment)
    assert lines[0] == "Moment: Test Moment"
    assert lines[1] == "Kind: status"
    assert lines[2] == "Duration: unknown"
    assert lines[3] == "Budget: unknown"
    assert lines[4] == "Alternative: none"
    assert plain_words(moment) == moment_plain_words(moment)
    assert "Test Moment" in plain_words(moment)
    assert "held moment" in plain_words(moment)


def test_unalternated_moment_stands_named_in_its_gaps():
    moment = _moment(text_alternative="")
    assert moment_gaps(moment) == ("no text alternative",)
    assert moment_passes(moment) is False
    text = format_moment(moment)
    assert "stands unalternated" in text
    current_text = format_moment(_moment())
    assert "stands alternated" in current_text


def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(_stored_view(view)) == view
    record = view_record(view)
    assert record["type"] == "ceremony_view"
    assert record["view_filter"] == "all"
    assert "shows all moments" in view_plain_words(view)
    assert "filter all" in format_view(view)
    with pytest.raises(ValueError):
        _view(view_filter="some")
    stance = _note()
    assert build_note(stance.to_record()) == stance
    assert "Moment note note moment-test" in format_note(stance)
    assert "shows no splash" in format_note(stance)
    assert "toward the user" in note_plain_words(stance)
    with pytest.raises(ValueError):
        _note(stance="dance")


# ---------------------------------------------------------------------
# The index and the stance targets: derived at call time, never held.
# ---------------------------------------------------------------------


def test_index_is_derived_from_the_held_moments_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.moment_id for e in index.entries] == ["moment-test"]
    assert index.entries[0].alternative == "Mythic Agent Coder"
    assert index.gaps == ("moment-silence-only",)
    assert index_record(index)["type"] == "ceremony_index"
    assert index_record(book)["gaps"] == ["moment-silence-only"]
    assert "1 alternatives" in index_plain_words(book)
    text = format_index(book)
    assert "Moment index" in text
    assert "Mythic Agent Coder - A test moment (moment-test)" in text
    assert "moment-silence-only" in text
    assert "shows no splash" in text


def test_target_reaches_its_moment_and_an_unheld_target_reaches_nothing():
    book = _mixed_book()
    assert moment_for_alternative(book, "Mythic Agent Coder").moment_id == "moment-test"
    assert moment_for_alternative(book, "triple resume") is None
    assert moment_for_alternative(book, "") is None
    assert "A test moment" in format_alternative(book, "Mythic Agent Coder")
    assert "reaches nothing in this book" in format_alternative(
        book, "triple resume")


def test_first_note_is_held_as_data():
    book = _book(notes=[_note(), _note(
        note_id="note-two", seq=2, moment_id="moment-other",
        stance="question", title="The second stance")])
    assert first_note(book).note_id == "note-test"
    assert note_for_moment(book, "moment-other").note_id == (
        "note-two")
    assert note_for_moment(
        book, "moment-other", "question").note_id == "note-two"
    assert note_for_moment(book, "moment-other", "praise") is None
    bare = _book()
    assert first_note(bare) is None
    assert note_for_moment(bare, "moment-other") is None
    text = format_note(first_note(book))
    assert "held as data alone" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    stance = _note(
        moment_id="moment-x", stance="concern",
        target="a branched session")
    assert stance.stance == "concern"
    rebuilt = build_note(stance.to_record())
    assert rebuilt == stance
    assert rebuilt.moment_id == "moment-x"
    assert rebuilt.target == "a branched session"
    with pytest.raises(ValueError):
        _note(moment_id="   ")
    with pytest.raises(ValueError):
        _note(target="   ")
    with pytest.raises(ValueError):
        _note(stance="teleport")


def test_panel_is_derived_and_a_stored_panel_must_agree():
    book = _mixed_book()
    panel = derive_panel(book)
    assert isinstance(panel, MomentPanel)
    assert panel.total_items == 2
    assert panel.total_shown == 2
    assert validate_panel(panel, book) is panel
    assert build_panel(panel.to_record(), book).rows == panel.rows
    assert build_row(panel.rows[0], book.moments[0]) == panel.rows[0]
    assert validate_row(panel.rows[0], book.moments[0]) == panel.rows[0]
    tampered = dict(panel.to_record())
    tampered["total_shown"] = 99
    with pytest.raises(ValueError):
        build_panel(tampered, book)
    renamed = dict(panel.to_record())
    renamed["panel_id"] = "panel-renamed"
    assert build_panel(renamed, book).panel_id == "panel-renamed"
    record = panel_record(panel, book)
    assert record["type"] == "ceremony_panel"
    assert record["panel_id"] == panel.panel_id


def test_verdict_is_derived_from_the_shown_moments():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert isinstance(verdict, MomentVerdict)
    assert verdict.verdict == "strained"
    assert verdict.total_shown == 2
    assert verdict.passing_shown == 1
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    record = verdict_record(verdict, book)
    assert record["type"] == "ceremony_verdict"
    assert "strained" in verdict_plain_words(book)
    assert "strained" in format_verdict(book)


def test_verdict_open_and_shut_edges():
    whole = _book(moments=[_moment()])
    assert derive_verdict(whole).verdict == "open"
    absent_book = _book(moments=[_moment(text_alternative="")])
    assert derive_verdict(absent_book).verdict == "shut"
    none_shown = _book(
        moments=[_moment(text_alternative="")],
        views=[_view(view_filter="alternated")])
    verdict = derive_verdict(none_shown)
    assert verdict.total_shown == 0
    assert verdict.verdict == "shut"


def test_shown_and_kind_readings():
    book = _mixed_book()
    assert [g.moment_id for g in shown_moments(book)] == [
        "moment-test", "moment-silence-only"]
    alternated_view = _view(
        view_id="view-r", seq=2, view_filter="alternated")
    book2 = _book(
        moments=[_moment(), _moment(
            moment_id="moment-silence-only", seq=2, occasion="A silence moment",
            kind="silence", duration="", budget="", text_alternative="")],
        views=[_view(), alternated_view])
    assert [g.moment_id for g in shown_moments(book2, alternated_view)] == [
        "moment-test"]
    assert [g.moment_id for g in moments_for_kind(book2, "silence")] == [
        "moment-silence-only"]
    assert [g.moment_id for g in passing_moments(book2)] == [
        "moment-test"]
    assert total_moments(book2) == 2
    with pytest.raises(ValueError):
        moments_for_kind(book2, "the void")


def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(moments=[_moment(), _moment(seq=2)])
    with pytest.raises(ValueError):
        _book(moments=[_moment(), _moment(moment_id="moment-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(view_filter="alternated")])
    with pytest.raises(ValueError) as caught:
        _book(notes=[_note(), _note(note_id="note-two", seq=2)])
    assert "one stance stands per session target" in str(caught.value)
    fields = {
        "schema": SPLASH_CEREMONY_SCHEMA, "slice": "M-193",
        "splash_ceremony": {"title": "A test moment book"},
        "moments": [_stored_moment(_moment())],
        "views": [_stored_view(_view())], "notes": [],
        "panels": [], "verdict": "open",
    }
    with pytest.raises(ValueError):
        build_book(fields)
    del fields["verdict"]
    fields["ceremony_index"] = "stored"
    with pytest.raises(ValueError):
        build_book(fields)
    raw = {
        "schema": SPLASH_CEREMONY_SCHEMA, "slice": "M-193",
        "splash_ceremony": {"title": "A test moment book"},
        "moments": [], "views": [], "notes": [], "panels": [],
        "shows_moment": True,
    }
    with pytest.raises(ValueError) as caught:
        build_book(raw)
    assert "held as data alone" in str(caught.value)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / SPLASH_CEREMONY_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "splash_ceremony.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_splash_ceremony_file(path)
    assert book.title == EXAMPLE_TITLE
    assert total_moments(book) == 6


def test_registry_holds_moments_and_views_one_by_one():
    registry = SplashCeremonyRegistry()
    assert registry.list_items() == ()
    held = registry.register_moment(_moment())
    assert held.moment_id == "moment-test"
    registry.register_view(_view())
    assert [i.item_id if hasattr(i, "item_id") else i.view_id
            for i in registry.list_items()] == ["moment-test", "view-test"]
    assert registry.get_moment("moment-test").occasion == "A test moment"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.book().title == "An unheld moment book"
    with pytest.raises(ValueError):
        registry.register_moment(_moment(seq=2))
    with pytest.raises(ValueError):
        registry.register_moment(_moment(moment_id="moment-two"))
    with pytest.raises(KeyError):
        registry.get_moment("moment-nope")


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = SplashCeremonyRegistry()
    book = _mixed_book()
    held = registry.register_book(book)
    assert held.title == "A test moment book"
    assert len(registry.list_moments()) == 2
    other = _book(moments=[_moment(
        moment_id="moment-x", seq=9, occasion="Other", text_alternative="Mythic Agent Coder")],
        views=[_view(view_id="view-x", seq=9)])
    object.__setattr__(other, "title", "Another title")
    with pytest.raises(ValueError):
        registry.register_book(other)


def test_plain_words_and_formatters():
    book = _mixed_book()
    assert "kind: 'wordmark'" in format_book(book)
    assert "moment-silence-only" in format_book(book, "silence")
    assert "moment-test" not in format_book(book, "silence")
    assert "Ceremony panel under view view-test" in format_panel(book)
    assert panel_plain_words(book).startswith(
        "The ceremony book holds 2 moments")
    screen = format_ceremony_screen(book)
    assert "Splash and Ceremony (M-193)" in screen
    assert PLAIN_EXPLANATION in screen
    assert "moment-terminal-sweep" not in screen
    assert "moment-silence-only" in screen
    record = book_record(book)
    assert record["type"] == "ceremony_book"
    assert record["title"] == "A test moment book"
    assert len(record["moments"]) == 2
    panel = derive_panel(book)
    assert panel_record(panel, book)["rows"][0]["item_id"] == "moment-test"
    assert verdict_record(derive_verdict(book), book)["verdict"] == (
        "strained")
    moment_text = format_moment(book.moments[0])
    assert "Moment: A test moment" in moment_text
    assert "Alternative: Mythic Agent Coder" in moment_text


def test_parse_args_inspect_and_loader_targets():
    assert parse_ceremony_args("") == ("show", None)
    assert parse_ceremony_args("show") == ("show", None)
    assert parse_ceremony_args(None) == ("show", None)
    assert parse_ceremony_args("moment moment-test") == (
        "moment", "moment-test")
    assert parse_ceremony_args("alternative Mythic Agent Coder") == (
        "alternative", "Mythic Agent Coder")
    assert parse_ceremony_args("kind wordmark") == (
        "kind", "wordmark")
    assert parse_ceremony_args("view view-test") == ("view", "view-test")
    assert parse_ceremony_args("note note-test") == (
        "note", "note-test")
    assert parse_ceremony_args("index") == ("index", None)
    assert parse_ceremony_args("panel") == ("panel", None)
    assert parse_ceremony_args("verdict") == ("verdict", None)
    for bad in ("dance", "moment", "alternative", "kind", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_ceremony_args(bad)
    moment = _moment()
    assert inspect_moment_source(moment) == {
        "kind": "moment", "moment_id": "moment-test"}
    assert inspect_moment_source(_stored_moment(moment))["kind"] == (
        "moment")
    assert inspect_moment_source(_stored_view(_view()))["kind"] == (
        "view")
    assert inspect_moment_source(_note().to_record())["kind"] == (
        "note")
    assert inspect_moment_source(42)["kind"] == "unknown"
    book = load_splash_ceremony({
        "schema": SPLASH_CEREMONY_SCHEMA, "slice": "M-193",
        "splash_ceremony": {"title": "A judged book"},
        "moments": [_stored_moment(_moment())],
        "views": [_stored_view(_view())], "notes": [], "panels": []})
    assert isinstance(book, MomentBook)
    assert book.title == "A judged book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_splash_ceremony({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_splash_ceremony({"slice": "M-999"})
    built = build_moment(
        moment_id="moment-kw", seq=3, occasion="Kw Moment",
        kind="wordmark", duration="1 second", budget="accent 5 percent",
        text_alternative="Mythic Agent Coder", detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="moment-test")
    assert built.moment_id == "moment-kw"
    assert moment_passes(built) is True


# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-193 agent layer: the agent holds a moment book
# for the session, moments and views are published
# as session news through the checkpoint target
# (journal first, deduped per shape), the panel
# and verdict are derived at call time from the
# whole book under a view, never held, the index
# is derived from the book's held moments, and the
# stance targets are held as data beside them -
# holding one resumes no session. This layer
# resumes nothing, renders no live UI, exports
# nothing and persists nothing beyond the
# session journal news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _moment_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_moment_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / SPLASH_CEREMONY_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "splash_ceremony.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestCeremonyAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.splash_ceremony_status()
        assert status["moments"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["splash_ceremony"]["title"] == EXAMPLE_TITLE
        assert len(status["splash_ceremony"]["moments"]) == 6
        assert len(status["splash_ceremony"]["views"]) == 2
        assert len(status["splash_ceremony"]["notes"]) == 2
        assert status["panel"]["total_items"] == 6
        assert status["panel"]["total_shown"] == 6
        assert status["panels"][0]["panel_id"] == "panel-m192-boundary"
        assert status["verdict"]["verdict"] == "strained"
        assert status["verdict"]["passing_shown"] == 5
        assert [e["alternative"] for e in status["index"]["entries"]] == ["Mythic Agent Coder", "Loading the forge: provider, model and tools.", "A longship under sail, drawn in line art.", "Ready - the chat stands open.", "Roadmap complete - all 272 slices stand banked."]
        assert status["index"]["gaps"] == ["moment-silence-work"]
        assert status["first_note"]["note_id"] == "note-note-wordmark"
        assert "held as data alone" in status["rule"]
        assert "Roadmap complete - all 272 slices stand banked." in status["plain_words"]
        assert "Splash and Ceremony (M-193)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._splash_ceremony_registry()
        assert agent._splash_ceremony_registry() is first
        assert agent._splash_ceremony_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.splash_ceremony_status()
        assert agent.get_ceremony_moment(
            "moment-wordmark-start").occasion == "Wordmark at start"
        assert agent.get_ceremony_view("view-ceremony").view_filter == "all"
        assert agent.get_ceremony_note(
            "note-note-wordmark").note_id == "note-note-wordmark"
        assert [a.moment_id for a in agent.ceremony_moments_for_kind(
            "wordmark")] == ["moment-wordmark-start", "moment-wordmark-complete"]
        assert [a.moment_id for a in agent.ceremony_moments_for_kind(
            "status")] == ["moment-status-loading", "moment-status-ready"]
        assert [a.moment_id for a in agent.ceremony_moments_passing()] == [
            "moment-wordmark-start", "moment-status-loading",
            "moment-art-longship", "moment-status-ready",
            "moment-wordmark-complete"]
        agent.splash_ceremony_panel()
        agent.splash_ceremony_verdict()
        agent.ceremony_index()
        agent.report_splash_ceremony()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("ceremony")
                or e["type"] == "ceremony_moment"] == []
        with pytest.raises(KeyError):
            agent.get_ceremony_moment("moment-nope")
        with pytest.raises(KeyError):
            agent.get_ceremony_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_ceremony_note("note-nope")
        with pytest.raises(ValueError):
            agent.ceremony_moments_for_kind("the void")
        agent.close()

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_ceremony_moment(_moment())
        status = agent.splash_ceremony_status()
        assert [a["moment_id"] for a in status["moments"]] == ["moment-test"]
        assert status["book"]["title"] == "An unheld moment book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["alternative"] for e in status["index"]["entries"]] == [
            "Mythic Agent Coder"]
        assert status["first_note"] is None
        assert "moment-test" in status["screen"]

    def test_held_moment_never_falls_back_to_the_example(
            self, agent):
        agent.register_ceremony_moment(_moment())
        with pytest.raises(KeyError):
            agent.get_ceremony_moment("moment-wordmark-start")
        with pytest.raises(KeyError):
            agent.get_ceremony_view("view-ceremony")
        with pytest.raises(KeyError):
            agent.get_ceremony_note("modal")
        moment = agent.get_ceremony_moment("moment-test")
        assert moment.occasion == "A test moment"
        assert agent.splash_ceremony_book().title == (
            "An unheld moment book")

    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_ceremony_note("note-note-wordmark")
        assert first.note_id == "note-note-wordmark"
        assert first.moment_id == "moment-wordmark-start"
        status = agent.splash_ceremony_status()
        assert status["index"]["gaps"] == ["moment-silence-work"]
        assert status["first_note"]["moment_id"] == (
            "moment-wordmark-start")
        assert status["first_note"]["stance"] == "note"


class TestCeremonyAgentHolding:
    def test_register_moment_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_ceremony_moment(_moment())
        assert result["moment"]["moment_id"] == "moment-test"
        assert result["record_news"]["type"] == "ceremony_moment"
        assert "moment-test" in result["screen"]
        events = _moment_events(store, session_id, "ceremony_moment")
        assert len(events) == 1
        agent.close()

    def test_duplicate_moment_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_ceremony_moment(_moment())
        with pytest.raises(ValueError):
            agent.register_ceremony_moment(_moment(seq=9))
        with pytest.raises(ValueError):
            agent.register_ceremony_moment(_moment(moment_id="moment-two"))
        events = _moment_events(store, session_id, "ceremony_moment")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_ceremony_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_moment_events(
            store, session_id, "ceremony_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_ceremony_moment(_moment())
        result = agent.view_ceremony("alternated")
        assert result["view"]["view_filter"] == "alternated"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "ceremony_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "open"
        assert len(_moment_events(
            store, session_id, "ceremony_view")) == 1
        assert len(_moment_events(
            store, session_id, "ceremony_panel")) == 1
        assert len(_moment_events(
            store, session_id, "ceremony_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_ceremony_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "ceremony_moment", "ceremony_view"]
        assert len(_moment_events(
            store, session_id, "ceremony_moment")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_ceremony_book()
        assert result["count"] == 6
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "ceremony_panel"
        assert result["index_record"]["gaps"] == [
            "moment-silence-work"]
        with pytest.raises(ValueError):
            agent.record_ceremony_book()
        assert len(_moment_events(
            store, session_id, "ceremony_moment")) == 6
        assert len(_moment_events(
            store, session_id, "ceremony_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_moment_book_file(tmp_path)
        book = load_splash_ceremony_file(path)
        result = agent.record_ceremony_book(book)
        assert result["count"] == 6
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_splash_ceremony()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "strained"
        assert report["index"]["gaps"] == ["moment-silence-work"]
        assert "moment-wordmark-start" in report["book_text"]
        assert "Mythic Agent Coder - Wordmark at start (moment-wordmark-start)" in report["index_text"]
        agent.register_ceremony_moment(_moment())
        report = agent.report_splash_ceremony()
        assert report["book"]["title"] == "An unheld moment book"
        assert report["panel"] is None
        assert report["verdict"] is None


class TestCeremonyTerminalSurface:
    def test_show_moment_target_kind_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/ceremony")
        assert "Splash and Ceremony (M-193)" in text
        _, _, text = _slash(agent, "/ceremony moment moment-wordmark-start")
        assert "Moment: Wordmark at start" in text
        _, _, text = _slash(agent, "/ceremony alternative Mythic Agent Coder")
        assert "Mythic Agent Coder" in text
        _, _, text = _slash(agent, "/ceremony alternative triple resume")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/ceremony kind wordmark")
        assert "moment-wordmark-start" in text
        assert "moment-silence-work" not in text
        _, _, text = _slash(agent, "/ceremony view view-ceremony")
        assert "filter all" in text
        _, _, text = _slash(agent, "/ceremony note note-note-wordmark")
        assert "Moment note note moment-wordmark-start" in text
        _, _, text = _slash(agent, "/ceremony index")
        assert "Moment index" in text
        assert "moment-status-ready" in text
        _, _, text = _slash(agent, "/ceremony panel")
        assert "Ceremony panel under view view-ceremony" in text
        _, _, text = _slash(agent, "/ceremony verdict")
        assert "strained" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/ceremony [show|moment <moment-id>"
                "|alternative <alternative>|kind <kind>|view <view-id>"
                "|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/ceremony dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/ceremony moment moment-nope")
        assert "no moment named" in text


@pytest.fixture()
def ceremony_handler(agent, monkeypatch):
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


def _moment_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestCeremonyCommand:
    def test_show_is_default(self, ceremony_handler, agent):
        ceremony_handler._handle_ceremony("")
        assert "Splash and Ceremony (M-193)" in (
            _moment_published_text(ceremony_handler))

    def test_moment_target_kind_view_note_index_panel_verdict(
            self, ceremony_handler, agent):
        ceremony_handler._handle_ceremony("moment moment-wordmark-start")
        assert "Moment: Wordmark at start" in _moment_published_text(
            ceremony_handler)
        ceremony_handler._handle_ceremony("alternative Mythic Agent Coder")
        assert "Mythic Agent Coder" in _moment_published_text(
            ceremony_handler)
        ceremony_handler._handle_ceremony("kind wordmark")
        assert "moment-wordmark-start" in _moment_published_text(ceremony_handler)
        ceremony_handler._handle_ceremony("view view-ceremony")
        assert "filter all" in _moment_published_text(ceremony_handler)
        ceremony_handler._handle_ceremony("note note-note-wordmark")
        assert "Moment note note moment-wordmark-start" in _moment_published_text(ceremony_handler)
        ceremony_handler._handle_ceremony("index")
        assert "Moment index" in _moment_published_text(ceremony_handler)
        ceremony_handler._handle_ceremony("panel")
        assert "Ceremony panel under view" in _moment_published_text(
            ceremony_handler)
        ceremony_handler._handle_ceremony("verdict")
        assert "strained" in _moment_published_text(ceremony_handler)

    def test_bad_grammar_is_published(
            self, ceremony_handler, agent):
        ceremony_handler._handle_ceremony("dance party")
        assert USAGE in _moment_published_text(ceremony_handler)
        ceremony_handler._handle_ceremony("moment moment-nope")
        assert "no moment named" in _moment_published_text(ceremony_handler)


class TestChatScreenRoutingCeremony:
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
        screen.handle_command("/ceremony panel", _FakeLog())
        assert calls == [("/ceremony", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/ceremony[/green] - show splash and ceremony, restrained (M-193)" in (
            text)
        assert ('"/ceremony": "Usage: /ceremony | '
                '/ceremony moment <moment-id>') in text


class TestCeremonyDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.splash_ceremony_panel()
        assert panel.total_shown == 6
        assert panel.panel_id == "panel-view-ceremony"
        verdict = agent.splash_ceremony_verdict()
        assert verdict.verdict == "strained"
        found = agent.splash_ceremony_verdict("view-alternated")
        assert found.verdict == "open"
        assert found.passing_shown == 5
        agent.register_ceremony_moment(_moment())
        with pytest.raises(ValueError):
            agent.splash_ceremony_panel()
        with pytest.raises(ValueError):
            agent.splash_ceremony_verdict()

    def test_view_target_over_an_unshown_filter_is_shut(self, agent):
        agent.register_ceremony_moment(_moment(text_alternative=""))
        result = agent.view_ceremony("alternated")
        assert result["verdict_record"]["verdict"] == "shut"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.ceremony_index()
        assert [e["alternative"] for e in result["index"]["entries"]] == ["Mythic Agent Coder", "Loading the forge: provider, model and tools.", "A longship under sail, drawn in line art.", "Ready - the chat stands open.", "Roadmap complete - all 272 slices stand banked."]
        assert result["index"]["gaps"] == ["moment-silence-work"]
        assert "Mythic Agent Coder - Wordmark at start (moment-wordmark-start)" in (
            result["index_text"])
        moment = agent.get_ceremony_moment("moment-silence-work")
        assert moment_gaps(moment) == ("no text alternative",)
        assert moment_passes(moment) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("ceremony")
                or e["type"] == "ceremony_moment"] == []
        agent.close()
