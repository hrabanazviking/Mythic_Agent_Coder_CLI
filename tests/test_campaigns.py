"""M-201 Campaigns as Data - pure-layer tests.

TIER: integration

The pure layer is the campaign, held as data:
one record per slice, held whole - under its
title, the part it stands in, its state in the
closed vocabulary the M-173 slice board itself
speaks (queued, building, verifying, banked),
its evidence held honestly (unknown stays
empty, never invented), the acceptance checks
it carries, named as data, and its detail - the
notes held as data beside them, each naming its
slice, its stance and its target, and the
campaign index derived at call time from the
held slices alone, never stored where it could
drift. A slice naming no acceptance checks
stands unready, named in its gaps, and a slice
claiming banked with no evidence stands named
in its gaps beside it; two slices standing for
one slice id refuse by name, and one stance
record stands per slice stance. A record
claiming a campaign was actually run, executed,
banked live, pushed or merged refuses by name,
and a stored index, verdict, board or current
slice refuses by name. The board display is
derived through the shipped M-173 slice-board
layer, never duplicated, and this repo's own
roadmap - the M-017 data file - stands proved
as the book's first citizen: 272 slices in 11
parts, with M-201 itself queued at build time.
The panel is derived for one held view and the
verdict is derived for the whole book under one
view. The shipped example book is held in a
data file, and a loader reads a book from any
file. No charter row names this slice: the
M-171 TUI charter binds Part VIII alone, and
the M-005 method charter names no slice row -
its source note names the whole Part IX range
M-201-M-232 as the part that executes it, and
the tests pin both facts live. This layer
executes nothing, runs no campaign, banks
nothing, pushes nothing and opens no network:
it holds campaigns as data and tells them.
"""


from pathlib import Path

import pytest
import yaml

from mythic_agent.core.campaigns import (
    STATES,
    EXAMPLE_CHECKS,
    STANCES,
    INDEX_ACTION,
    CAMPAIGNS_RESOURCE,
    CAMPAIGNS_SCHEMA,
    CAMPAIGNS_SLICE,
    CAMPAIGN_RULE,
    PLAIN_EXPLANATION,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    READY_WORDS,
    CampaignSlice,
    NoteRecord,
    CampaignBook,
    CampaignPanel,
    CampaignsRegistry,
    CampaignVerdict,
    CampaignView,
    board_record,
    book_record,
    build_book,
    build_note,
    build_panel,
    build_row,
    build_slice,
    build_verdict,
    build_view,
    current_slice,
    derive_index,
    derive_panel,
    derive_verdict,
    first_citizen_record,
    first_note,
    format_book,
    format_campaign_screen,
    format_checks,
    format_index,
    format_note,
    format_panel,
    format_slice,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    load_campaigns,
    load_campaigns_file,
    normalize_state,
    normalize_stance,
    normalize_view_filter,
    note_for_slice,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_campaign_args,
    passing_slices,
    plain_lines,
    plain_words,
    shown_slices,
    slice_for_checks,
    slice_gaps,
    slice_passes,
    slice_record,
    slices_for_state,
    validate_book,
    validate_note,
    validate_panel,
    validate_row,
    validate_slice,
    validate_verdict,
    validate_view,
    verdict_plain_words,
    verdict_record,
    view_plain_words,
    view_record,
)
from mythic_agent.core.method_charter import (
    load_charter as load_method_charter,
)
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.tui_redesign_charter import load_charter

ROOT = Path(__file__).resolve().parents[1]
ON = "2026-11-10"
BY = "the coordinator"
EXAMPLE_TITLE = "Campaigns as data at the M-200 slice boundary"
EXAMPLE_CHECKS_LIST = [
    "the part gate stands banked",
    "the campaign file loads, validates and displays",
    "the intent stands in the user's plain words",
    "each slice stands one verifiable outcome",
    "each slice carries its checks",
]
EXAMPLE_SLICE_IDS = (
    "slice-part9-open", "slice-campaigns-data",
    "slice-intent-capture", "slice-slicing-engine",
    "slice-juggernaut-loop", "slice-acceptance-gates")


def _slice(**overrides):
    fields = {
        "slice_id": "slice-test",
        "seq": 1,
        "title": "A test slice",
        "part": 9,
        "state": "queued",
        "evidence": "",
        "checks": "the test slice stands checked",
        "detail": "A test slice held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "slice-test",
    }
    fields.update(overrides)
    return build_slice(fields)


def _stored_slice(slice_):
    return slice_.to_record()


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "slice-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _stored_view(view):
    return view.to_record()


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "slice_id": "slice-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "slice-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _book(slices=None, views=None, notes=None, **overrides):
    fields = {
        "schema": CAMPAIGNS_SCHEMA,
        "slice": "M-201",
        "campaigns": {"title": "A test campaign book"},
        "slices": [_stored_slice(item) for item in (
            slices if slices is not None else [_slice()])],
        "views": [_stored_view(item) for item in (
            views if views is not None else [_view()])],
        "notes": [item.to_record() for item in (notes or [])],
        "panels": [],
    }
    fields.update(overrides)
    return build_book(fields)


def _mixed_book():
    return _book(slices=[
        _slice(),
        _slice(slice_id="slice-hidden", seq=2,
               title="A hidden slice", state="banked",
               evidence="",
               checks="the hidden slice stands checked"),
    ])


def test_shipped_book_loads_with_pinned_shape():
    book = load_campaigns()
    assert book.title == EXAMPLE_TITLE
    assert book.slice_ids() == EXAMPLE_SLICE_IDS
    assert [v.view_id for v in book.views] == [
        "view-campaign", "view-ready"]
    assert [m.slice_id for m in book.notes] == [
        "slice-part9-open",
        "slice-campaigns-data"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m200-boundary"
    assert panel.as_of == "2026-11-10"
    assert [row.item_id for row in panel.rows] == list(book.slice_ids())
    derived = derive_panel(book, "view-campaign")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 6
    assert panel.total_shown == derived.total_shown == 6
    assert {c.standing: c.items for c in panel.target_counts} == {
        "ready": 5, "unready": 1}
    assert derive_verdict(book, "view-campaign").verdict == "strained"
    assert derive_verdict(book, "view-campaign").passing_shown == 5
    assert derive_verdict(book, "view-ready").verdict == "open"
    assert derive_verdict(book, "view-ready").passing_shown == 5
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / CAMPAIGNS_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == CAMPAIGNS_SCHEMA
    assert raw["slice"] == "M-201"
    assert "verdict" not in raw
    assert "campaign_index" not in raw
    assert "board" not in raw


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-201")]
    assert slice_.title == "Campaigns as data"
    assert slice_.part == 9
    assert "acceptance checks" in slice_.summary
    assert "displays (M-173)" in slice_.summary
    assert "first citizen" in slice_.summary
    assert CAMPAIGNS_SLICE == "M-201"


def test_charter_rows_do_not_name_m201():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-201" not in owners
    method = load_method_charter()
    assert "M-201" in method.source_note
    assert "M-232" in method.source_note


def test_closed_vocabularies():
    assert READY_WORDS == ("ready", "unready")
    assert STATES == ("queued", "building", "verifying", "banked")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "ready", "unready")
    assert VERDICT_WORDS == ("open", "strained", "shut")
    assert INDEX_ACTION == "index"
    assert EXAMPLE_CHECKS == (
        "the campaign file loads, validates and displays")
    assert normalize_state("BANKED") == "banked"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    with pytest.raises(ValueError):
        normalize_state("the void")
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    assert "held as data alone" in CAMPAIGN_RULE
    assert "executes nothing" in CAMPAIGN_RULE
    assert "M-201" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /campaigns")


def test_shipped_book_judged_honestly_as_data():
    book = load_campaigns()
    gate = book.slice_for("slice-part9-open")
    assert slice_passes(gate) is True
    assert slice_gaps(gate) == ()
    assert plain_lines(gate) == (
        "Slice: Part IX opens",
        "Part: 9",
        "State: banked",
        "Evidence: the part VIII gate, banked at M-200",
        "Checks: the part gate stands banked")
    work = book.slice_for("slice-campaigns-data")
    assert work.state == "building"
    assert work.evidence == ""
    assert "Evidence: unknown" in plain_lines(work)
    juggernaut = book.slice_for("slice-juggernaut-loop")
    assert slice_gaps(juggernaut) == ("no acceptance checks",)
    assert slice_passes(juggernaut) is False
    assert [g.slice_id for g in passing_slices(book)] == [
        "slice-part9-open", "slice-campaigns-data",
        "slice-intent-capture", "slice-slicing-engine",
        "slice-acceptance-gates"]
    index = derive_index(book)
    assert [e.checks for e in index.entries] == EXAMPLE_CHECKS_LIST
    assert index.gaps == ("slice-juggernaut-loop",)
    assert slice_for_checks(book, EXAMPLE_CHECKS).slice_id == (
        "slice-campaigns-data")
    assert slice_for_checks(book, "triple resume") is None
    assert first_note(book).note_id == "note-note-open"
    assert note_for_slice(
        book, "slice-part9-open", "note").note_id == (
            "note-note-open")
    assert note_for_slice(book, "slice-nope") is None
    assert current_slice(book).slice_id == "slice-campaigns-data"
    board = board_record(book)
    assert board["board_slice"] == "M-173"
    assert board["columns"] == [
        {"column": "queued", "slices": 4},
        {"column": "building", "slices": 1},
        {"column": "verifying", "slices": 0},
        {"column": "banked", "slices": 1}]
    assert board["total"] == 6
    assert board["current_slice"] == "slice-campaigns-data"
    citizen = first_citizen_record()
    assert citizen["campaign_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["next_slice"] == "M-204"
    assert citizen["m201_title"] == "Campaigns as data"
    assert citizen["m201_part"] == 9
    assert citizen["m201_status"] == "done"


# ---------------------------------------------------------------------
# The held slice: judged whole, its telling derived.
# ---------------------------------------------------------------------


def test_slice_record_round_trips():
    slice_ = _slice()
    assert validate_slice(slice_) is slice_
    rebuilt = build_slice(_stored_slice(slice_))
    assert rebuilt == slice_
    assert rebuilt.item_id == "slice-test"
    assert rebuilt.checks == "the test slice stands checked"
    record = slice_record(slice_)
    assert record["type"] == "campaign_slice"
    assert record["passes"] is True
    assert record["gaps"] == []


def test_slice_refuses_stored_judgements():
    for key in ("standing", "ready", "gaps", "segment", "verdict",
                "index", "entries", "coverage", "current_slice",
                "board"):
        fields = _stored_slice(_slice())
        fields[key] = "stored"
        with pytest.raises(ValueError):
            build_slice(fields)
    fields = _stored_slice(_slice())
    fields["surprise"] = "stored"
    with pytest.raises(ValueError):
        build_slice(fields)


def test_slice_refuses_a_live_campaign_claim():
    for key in ("runs_campaign", "executed_campaign",
                "banked_live", "pushed_campaign",
                "executes_slice", "opens_network"):
        fields = _stored_slice(_slice())
        fields[key] = True
        with pytest.raises(ValueError) as caught:
            build_slice(fields)
        assert "held as data alone" in str(caught.value)
    for key in ("posts_note", "posted_note"):
        fields = _note().to_record()
        fields[key] = True
        with pytest.raises(ValueError) as caught:
            build_note(fields)
        assert "held as data alone" in str(caught.value)
    record = _note(slice_id="slice-test")
    assert validate_note(record) is record
    assert record.slice_id == "slice-test"
    assert note_record(record)["type"] == "campaign_note"


def test_slice_vocabularies_are_closed():
    assert _slice(state="BANKED").state == "banked"
    assert _slice(checks="").checks == ""
    assert _slice(evidence=None).evidence == ""
    with pytest.raises(ValueError):
        _slice(state="a hunch")
    with pytest.raises(ValueError):
        _slice(title="   ")
    with pytest.raises(ValueError):
        _slice(seq=0)
    with pytest.raises(ValueError):
        _slice(part=0)
    with pytest.raises(ValueError):
        _slice(checks=5)
    with pytest.raises(ValueError):
        _slice(evidence=5)
    with pytest.raises(ValueError):
        _slice(detail="   ")


def test_plain_telling_derives_from_the_slices_own_fields():
    slice_ = _slice(
        title="Test Slice", state="banked", evidence="",
        checks="", detail="The checks wait on a held slice.")
    lines = plain_lines(slice_)
    assert lines[0] == "Slice: Test Slice"
    assert lines[1] == "Part: 9"
    assert lines[2] == "State: banked"
    assert lines[3] == "Evidence: unknown"
    assert lines[4] == "Checks: none"
    assert "Test Slice" in plain_words(slice_)
    assert "part 9, state banked" in plain_words(slice_)
    from mythic_agent.core.campaigns import segment_of
    assert "gaps: no acceptance checks, banked without evidence" in (
        segment_of(slice_))


def test_unready_slice_stands_named_in_its_gaps():
    slice_ = _slice(checks="")
    assert slice_gaps(slice_) == ("no acceptance checks",)
    assert slice_passes(slice_) is False
    text = format_slice(slice_)
    assert "stands unready" in text
    assert "no acceptance checks" in text
    banked = _slice(state="banked", evidence="")
    assert slice_gaps(banked) == ("banked without evidence",)
    assert "banked without evidence" in format_slice(banked)
    current_text = format_slice(_slice())
    assert "stands ready" in current_text


def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(_stored_view(view)) == view
    record = view_record(view)
    assert record["type"] == "campaign_view"
    assert record["view_filter"] == "all"
    assert "shows all slices" in view_plain_words(view)
    assert "filter all" in format_view(view)
    with pytest.raises(ValueError):
        _view(view_filter="some")
    stance = _note()
    assert build_note(stance.to_record()) == stance
    assert "Slice note note slice-test" in format_note(stance)
    assert "executes nothing" in format_note(stance)
    assert "toward the work ahead" in note_plain_words(stance)
    with pytest.raises(ValueError):
        _note(stance="dance")


# ---------------------------------------------------------------------
# The index and the stance targets: derived at call time, never held.
# ---------------------------------------------------------------------


def test_index_is_derived_from_the_held_slices_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.slice_id for e in index.entries] == ["slice-test"]
    assert index.entries[0].checks == "the test slice stands checked"
    assert index.gaps == ("slice-hidden",)
    assert index_record(index)["type"] == "campaign_index"
    assert index_record(book)["gaps"] == ["slice-hidden"]
    assert "1 ready works" in index_plain_words(book)
    text = format_index(book)
    assert "Campaign index" in text
    assert "the test slice stands checked - A test slice (slice-test)" in text
    assert "slice-hidden" in text
    assert "executes nothing" in text


def test_checks_target_reaches_its_slice_and_an_unheld_target_reaches_nothing():
    book = _mixed_book()
    assert slice_for_checks(
        book, "the test slice stands checked").slice_id == "slice-test"
    assert slice_for_checks(book, "triple resume") is None
    assert slice_for_checks(book, "") is None
    assert "A test slice" in format_checks(
        book, "the test slice stands checked")
    assert "reach nothing in this book" in format_checks(
        book, "triple resume")


def test_first_note_is_held_as_data():
    book = _book(notes=[_note(), _note(
        note_id="note-two", seq=2, slice_id="slice-other",
        stance="question", title="The second stance")])
    assert first_note(book).note_id == "note-test"
    assert note_for_slice(book, "slice-other").note_id == (
        "note-two")
    assert note_for_slice(
        book, "slice-other", "question").note_id == "note-two"
    assert note_for_slice(book, "slice-other", "praise") is None
    bare = _book()
    assert first_note(bare) is None
    assert note_for_slice(bare, "slice-other") is None
    text = format_note(first_note(book))
    assert "held as data alone" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    stance = _note(
        slice_id="slice-x", stance="concern",
        target="a branched campaign")
    assert stance.stance == "concern"
    rebuilt = build_note(stance.to_record())
    assert rebuilt == stance
    assert rebuilt.slice_id == "slice-x"
    assert rebuilt.target == "a branched campaign"
    with pytest.raises(ValueError):
        _note(slice_id="   ")
    with pytest.raises(ValueError):
        _note(target="   ")
    with pytest.raises(ValueError):
        _note(stance="teleport")


def test_panel_is_derived_and_a_stored_panel_must_agree():
    book = _mixed_book()
    panel = derive_panel(book)
    assert isinstance(panel, CampaignPanel)
    assert panel.total_items == 2
    assert panel.total_shown == 2
    assert validate_panel(panel, book) is panel
    assert build_panel(panel.to_record(), book).rows == panel.rows
    assert build_row(panel.rows[0], book.slices[0]) == panel.rows[0]
    assert validate_row(panel.rows[0], book.slices[0]) == panel.rows[0]
    tampered = dict(panel.to_record())
    tampered["total_shown"] = 99
    with pytest.raises(ValueError):
        build_panel(tampered, book)
    renamed = dict(panel.to_record())
    renamed["panel_id"] = "panel-renamed"
    assert build_panel(renamed, book).panel_id == "panel-renamed"
    record = panel_record(panel, book)
    assert record["type"] == "campaign_panel"
    assert record["panel_id"] == panel.panel_id


def test_verdict_is_derived_from_the_shown_slices():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert isinstance(verdict, CampaignVerdict)
    assert verdict.verdict == "strained"
    assert verdict.total_shown == 2
    assert verdict.passing_shown == 1
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    record = verdict_record(verdict, book)
    assert record["type"] == "campaign_verdict"
    assert "strained" in verdict_plain_words(book)
    assert "strained" in format_verdict(book)


def test_verdict_open_and_shut_edges():
    whole = _book(slices=[_slice()])
    assert derive_verdict(whole).verdict == "open"
    absent_book = _book(slices=[_slice(checks="")])
    assert derive_verdict(absent_book).verdict == "shut"
    none_shown = _book(
        slices=[_slice(checks="")],
        views=[_view(view_filter="ready")])
    verdict = derive_verdict(none_shown)
    assert verdict.total_shown == 0
    assert verdict.verdict == "shut"


def test_shown_and_state_readings():
    book = _mixed_book()
    assert [g.slice_id for g in shown_slices(book)] == [
        "slice-test", "slice-hidden"]
    ready_view = _view(
        view_id="view-r", seq=2, view_filter="ready")
    book2 = _book(
        slices=[_slice(), _slice(
            slice_id="slice-hidden", seq=2, title="A hidden slice",
            state="banked", evidence="",
            checks="the hidden slice stands checked")],
        views=[_view(), ready_view])
    assert [g.slice_id for g in shown_slices(book2, ready_view)] == [
        "slice-test"]
    assert [g.slice_id for g in slices_for_state(book2, "banked")] == [
        "slice-hidden"]
    assert [g.slice_id for g in passing_slices(book2)] == [
        "slice-test"]
    assert current_slice(book2).slice_id == "slice-test"
    with pytest.raises(ValueError):
        slices_for_state(book2, "the void")


def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(slices=[_slice(), _slice(seq=2)])
    with pytest.raises(ValueError):
        _book(slices=[_slice(), _slice(slice_id="slice-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(view_filter="ready")])
    with pytest.raises(ValueError) as caught:
        _book(notes=[_note(), _note(note_id="note-two", seq=2)])
    assert "one stance stands per slice target" in str(caught.value)
    fields = {
        "schema": CAMPAIGNS_SCHEMA, "slice": "M-201",
        "campaigns": {"title": "A test campaign book"},
        "slices": [_stored_slice(_slice())],
        "views": [_stored_view(_view())], "notes": [],
        "panels": [], "verdict": "open",
    }
    with pytest.raises(ValueError):
        build_book(fields)
    del fields["verdict"]
    fields["campaign_index"] = "stored"
    with pytest.raises(ValueError):
        build_book(fields)
    del fields["campaign_index"]
    fields["board"] = "stored"
    with pytest.raises(ValueError):
        build_book(fields)
    raw = {
        "schema": CAMPAIGNS_SCHEMA, "slice": "M-201",
        "campaigns": {"title": "A test campaign book"},
        "slices": [], "views": [], "notes": [], "panels": [],
        "runs_campaign": True,
    }
    with pytest.raises(ValueError) as caught:
        build_book(raw)
    assert "held as data alone" in str(caught.value)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / CAMPAIGNS_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "campaigns.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_campaigns_file(path)
    assert book.title == EXAMPLE_TITLE
    assert len(book.slices) == 6


def test_registry_holds_slices_and_views_one_by_one():
    registry = CampaignsRegistry()
    assert registry.list_items() == ()
    held = registry.register_slice(_slice())
    assert held.slice_id == "slice-test"
    registry.register_view(_view())
    assert [i.item_id for i in registry.list_items()] == [
        "slice-test", "view-test"]
    assert registry.get_slice("slice-test").title == "A test slice"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.book().title == "An unheld campaign book"
    with pytest.raises(ValueError):
        registry.register_slice(_slice(seq=2))
    with pytest.raises(ValueError):
        registry.register_slice(_slice(slice_id="slice-two"))
    with pytest.raises(KeyError):
        registry.get_slice("slice-nope")


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = CampaignsRegistry()
    book = _mixed_book()
    held = registry.register_book(book)
    assert held.title == "A test campaign book"
    assert len(registry.list_slices()) == 2
    other = _book(slices=[_slice(
        slice_id="slice-x", seq=9, title="Other",
        checks="the other slice stands checked")],
        views=[_view(view_id="view-x", seq=9)])
    object.__setattr__(other, "title", "Another title")
    with pytest.raises(ValueError):
        registry.register_book(other)


def test_plain_words_and_formatters():
    book = _mixed_book()
    assert "state: 'banked'" in format_book(book)
    assert "slice-hidden" in format_book(book, "banked")
    assert "slice-test" not in format_book(book, "banked")
    assert "Campaign panel under view view-test" in format_panel(book)
    assert panel_plain_words(book).startswith(
        "The campaign book holds 2 slices")
    screen = format_campaign_screen(book)
    assert "Campaigns as Data (M-201)" in screen
    assert PLAIN_EXPLANATION in screen
    assert "slice-hidden" in screen
    record = book_record(book)
    assert record["type"] == "campaign_book"
    assert record["title"] == "A test campaign book"
    assert len(record["slices"]) == 2
    panel = derive_panel(book)
    assert panel_record(panel, book)["rows"][0]["item_id"] == "slice-test"
    assert verdict_record(derive_verdict(book), book)["verdict"] == (
        "strained")
    slice_text = format_slice(book.slices[0])
    assert "Slice: A test slice" in slice_text
    assert "Checks: the test slice stands checked" in slice_text


def test_parse_args_board_and_loader_targets():
    assert parse_campaign_args("") == ("show", None)
    assert parse_campaign_args("show") == ("show", None)
    assert parse_campaign_args(None) == ("show", None)
    assert parse_campaign_args("slice slice-test") == (
        "slice", "slice-test")
    assert parse_campaign_args(
        "checks the campaign file loads, validates and displays") == (
            "checks", "the campaign file loads, validates and displays")
    assert parse_campaign_args("state banked") == (
        "state", "banked")
    assert parse_campaign_args("view view-test") == ("view", "view-test")
    assert parse_campaign_args("note note-test") == (
        "note", "note-test")
    assert parse_campaign_args("index") == ("index", None)
    assert parse_campaign_args("panel") == ("panel", None)
    assert parse_campaign_args("verdict") == ("verdict", None)
    for bad in ("dance", "slice", "checks", "state", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_campaign_args(bad)
    board = board_record()
    assert board["type"] == "campaign_board"
    assert board["total"] == 6
    assert board["current_slice"] == "slice-campaigns-data"
    book = load_campaigns({
        "schema": CAMPAIGNS_SCHEMA, "slice": "M-201",
        "campaigns": {"title": "A judged book"},
        "slices": [_stored_slice(_slice())],
        "views": [_stored_view(_view())], "notes": [], "panels": []})
    assert isinstance(book, CampaignBook)
    assert book.title == "A judged book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_campaigns({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_campaigns({"slice": "M-999"})
    built = build_slice(
        slice_id="slice-kw", seq=3, title="Kw Slice",
        part=9, state="queued", evidence="",
        checks="the kw slice stands checked", detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="slice-test")
    assert built.slice_id == "slice-kw"
    assert slice_passes(built) is True


# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-201 agent layer: the agent holds a campaign
# book for the session, slices and views are
# published as session news through the
# checkpoint target (journal first, deduped per
# shape), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held slices, the board is derived
# through the M-173 layer, the first citizen is
# read from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one executes no campaign. This layer
# runs nothing, banks nothing, pushes nothing
# and persists nothing beyond the session
# journal news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _campaign_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_campaign_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / CAMPAIGNS_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "campaigns.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestCampaignAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.campaigns_status()
        assert status["slices"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["campaigns"]["title"] == EXAMPLE_TITLE
        assert len(status["campaigns"]["slices"]) == 6
        assert len(status["campaigns"]["views"]) == 2
        assert len(status["campaigns"]["notes"]) == 2
        assert status["panel"]["total_items"] == 6
        assert status["panel"]["total_shown"] == 6
        assert status["panels"][0]["panel_id"] == "panel-m200-boundary"
        assert status["verdict"]["verdict"] == "strained"
        assert status["verdict"]["passing_shown"] == 5
        assert [e["checks"] for e in status["index"]["entries"]] == (
            EXAMPLE_CHECKS_LIST)
        assert status["index"]["gaps"] == ["slice-juggernaut-loop"]
        assert status["first_note"]["note_id"] == "note-note-open"
        assert status["board"]["total"] == 6
        assert status["board"]["current_slice"] == "slice-campaigns-data"
        assert status["first_citizen"]["slices"] == 272
        assert status["first_citizen"]["parts"] == 11
        assert "held as data alone" in status["rule"]
        assert "slice-juggernaut-loop" in status["plain_words"]
        assert "Campaigns as Data (M-201)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._campaigns_registry()
        assert agent._campaigns_registry() is first
        assert agent._campaigns_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.campaigns_status()
        assert agent.get_campaign_slice(
            "slice-part9-open").title == "Part IX opens"
        assert agent.get_campaign_view(
            "view-campaign").view_filter == "all"
        assert agent.get_campaign_note(
            "note-note-open").note_id == "note-note-open"
        assert [a.slice_id for a in agent.campaign_slices_for_state(
            "banked")] == ["slice-part9-open"]
        assert [a.slice_id for a in agent.campaign_slices_for_state(
            "queued")] == [
                "slice-intent-capture", "slice-slicing-engine",
                "slice-juggernaut-loop", "slice-acceptance-gates"]
        assert [a.slice_id for a in agent.campaign_slices_passing()] == [
            "slice-part9-open", "slice-campaigns-data",
            "slice-intent-capture", "slice-slicing-engine",
            "slice-acceptance-gates"]
        agent.campaigns_panel()
        agent.campaigns_verdict()
        agent.campaign_index()
        agent.report_campaigns()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("campaign")] == []
        with pytest.raises(KeyError):
            agent.get_campaign_slice("slice-nope")
        with pytest.raises(KeyError):
            agent.get_campaign_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_campaign_note("note-nope")
        with pytest.raises(ValueError):
            agent.campaign_slices_for_state("the void")
        agent.close()

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_campaign_slice(_slice())
        status = agent.campaigns_status()
        assert [a["slice_id"] for a in status["slices"]] == ["slice-test"]
        assert status["book"]["title"] == "An unheld campaign book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["checks"] for e in status["index"]["entries"]] == [
            "the test slice stands checked"]
        assert status["first_note"] is None
        assert "slice-test" in status["screen"]

    def test_held_slice_never_falls_back_to_the_example(
            self, agent):
        agent.register_campaign_slice(_slice())
        with pytest.raises(KeyError):
            agent.get_campaign_slice("slice-part9-open")
        with pytest.raises(KeyError):
            agent.get_campaign_view("view-campaign")
        with pytest.raises(KeyError):
            agent.get_campaign_note("note-note-open")
        slice_ = agent.get_campaign_slice("slice-test")
        assert slice_.title == "A test slice"
        assert agent.campaigns_book().title == (
            "An unheld campaign book")

    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_campaign_note("note-note-open")
        assert first.note_id == "note-note-open"
        assert first.slice_id == "slice-part9-open"
        status = agent.campaigns_status()
        assert status["index"]["gaps"] == ["slice-juggernaut-loop"]
        assert status["first_note"]["slice_id"] == (
            "slice-part9-open")
        assert status["first_note"]["stance"] == "note"


class TestCampaignAgentHolding:
    def test_register_slice_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_campaign_slice(_slice())
        assert result["slice"]["slice_id"] == "slice-test"
        assert result["record_news"]["type"] == "campaign_slice"
        assert "slice-test" in result["screen"]
        events = _campaign_events(store, session_id, "campaign_slice")
        assert len(events) == 1
        agent.close()

    def test_duplicate_slice_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_campaign_slice(_slice())
        with pytest.raises(ValueError):
            agent.register_campaign_slice(_slice(seq=9))
        with pytest.raises(ValueError):
            agent.register_campaign_slice(_slice(slice_id="slice-two"))
        events = _campaign_events(store, session_id, "campaign_slice")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_campaign_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_campaign_events(
            store, session_id, "campaign_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_campaign_slice(_slice())
        result = agent.view_campaign("ready")
        assert result["view"]["view_filter"] == "ready"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "campaign_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "open"
        assert len(_campaign_events(
            store, session_id, "campaign_view")) == 1
        assert len(_campaign_events(
            store, session_id, "campaign_panel")) == 1
        assert len(_campaign_events(
            store, session_id, "campaign_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_campaign_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "campaign_slice", "campaign_view"]
        assert len(_campaign_events(
            store, session_id, "campaign_slice")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_campaign_book()
        assert result["count"] == 6
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "campaign_panel"
        assert result["index_record"]["gaps"] == [
            "slice-juggernaut-loop"]
        with pytest.raises(ValueError):
            agent.record_campaign_book()
        assert len(_campaign_events(
            store, session_id, "campaign_slice")) == 6
        assert len(_campaign_events(
            store, session_id, "campaign_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_campaign_book_file(tmp_path)
        book = load_campaigns_file(path)
        result = agent.record_campaign_book(book)
        assert result["count"] == 6
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_campaigns()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "strained"
        assert report["index"]["gaps"] == ["slice-juggernaut-loop"]
        assert "slice-part9-open" in report["book_text"]
        assert "the part gate stands banked - Part IX opens (slice-part9-open)" in report["index_text"]
        agent.register_campaign_slice(_slice())
        report = agent.report_campaigns()
        assert report["book"]["title"] == "An unheld campaign book"
        assert report["panel"] is None
        assert report["verdict"] is None


class TestCampaignTerminalHeading:
    def test_show_slice_target_checks_state_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/campaigns")
        assert "Campaigns as Data (M-201)" in text
        _, _, text = _slash(agent, "/campaigns slice slice-part9-open")
        assert "Slice: Part IX opens" in text
        _, _, text = _slash(
            agent,
            "/campaigns checks the campaign file loads, validates and displays")
        assert "Slice: Campaigns as data" in text
        _, _, text = _slash(agent, "/campaigns checks triple resume")
        assert "reach nothing in this book" in text
        _, _, text = _slash(agent, "/campaigns state queued")
        assert "slice-intent-capture" in text
        assert "slice-part9-open" not in text
        _, _, text = _slash(agent, "/campaigns view view-campaign")
        assert "filter all" in text
        _, _, text = _slash(agent, "/campaigns note note-note-open")
        assert "Slice note note slice-part9-open" in text
        _, _, text = _slash(agent, "/campaigns index")
        assert "Campaign index" in text
        assert "slice-acceptance-gates" in text
        _, _, text = _slash(agent, "/campaigns panel")
        assert "Campaign panel under view view-campaign" in text
        _, _, text = _slash(agent, "/campaigns verdict")
        assert "strained" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/campaigns [show|slice <slice-id>"
                "|checks <checks>|state <state>|view <view-id>"
                "|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/campaigns dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/campaigns slice slice-nope")
        assert "no slice named" in text


@pytest.fixture()
def campaigns_handler(agent, monkeypatch):
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


def _campaign_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestCampaignCommand:
    def test_show_is_default(self, campaigns_handler, agent):
        campaigns_handler._handle_campaigns("")
        assert "Campaigns as Data (M-201)" in (
            _campaign_published_text(campaigns_handler))

    def test_slice_target_checks_state_view_note_index_panel_verdict(
            self, campaigns_handler, agent):
        campaigns_handler._handle_campaigns("slice slice-part9-open")
        assert "Slice: Part IX opens" in _campaign_published_text(
            campaigns_handler)
        campaigns_handler._handle_campaigns(
            "checks the campaign file loads, validates and displays")
        assert "Slice: Campaigns as data" in _campaign_published_text(
            campaigns_handler)
        campaigns_handler._handle_campaigns("state queued")
        assert "slice-intent-capture" in _campaign_published_text(
            campaigns_handler)
        campaigns_handler._handle_campaigns("view view-campaign")
        assert "filter all" in _campaign_published_text(campaigns_handler)
        campaigns_handler._handle_campaigns("note note-note-open")
        assert "Slice note note slice-part9-open" in (
            _campaign_published_text(campaigns_handler))
        campaigns_handler._handle_campaigns("index")
        assert "Campaign index" in _campaign_published_text(
            campaigns_handler)
        campaigns_handler._handle_campaigns("panel")
        assert "Campaign panel under view" in _campaign_published_text(
            campaigns_handler)
        campaigns_handler._handle_campaigns("verdict")
        assert "strained" in _campaign_published_text(campaigns_handler)

    def test_bad_grammar_is_published(
            self, campaigns_handler, agent):
        campaigns_handler._handle_campaigns("dance party")
        assert USAGE in _campaign_published_text(campaigns_handler)
        campaigns_handler._handle_campaigns("slice slice-nope")
        assert "no slice named" in _campaign_published_text(
            campaigns_handler)


class TestChatScreenRoutingCampaigns:
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
        screen.handle_command("/campaigns panel", _FakeLog())
        assert calls == [("/campaigns", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/campaigns[/green] - show campaigns as data (M-201)" in (
            text)
        assert ('"/campaigns": "Usage: /campaigns | '
                '/campaigns slice <slice-id>') in text


class TestCampaignDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.campaigns_panel()
        assert panel.total_shown == 6
        assert panel.panel_id == "panel-view-campaign"
        verdict = agent.campaigns_verdict()
        assert verdict.verdict == "strained"
        found = agent.campaigns_verdict("view-ready")
        assert found.verdict == "open"
        assert found.passing_shown == 5
        agent.register_campaign_slice(_slice())
        with pytest.raises(ValueError):
            agent.campaigns_panel()
        with pytest.raises(ValueError):
            agent.campaigns_verdict()

    def test_view_target_over_an_unshown_filter_is_shut(self, agent):
        agent.register_campaign_slice(_slice(checks=""))
        result = agent.view_campaign("ready")
        assert result["verdict_record"]["verdict"] == "shut"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.campaign_index()
        assert [e["checks"] for e in result["index"]["entries"]] == (
            EXAMPLE_CHECKS_LIST)
        assert result["index"]["gaps"] == ["slice-juggernaut-loop"]
        assert "the part gate stands banked - Part IX opens (slice-part9-open)" in (
            result["index_text"])
        slice_ = agent.get_campaign_slice("slice-juggernaut-loop")
        assert slice_gaps(slice_) == ("no acceptance checks",)
        assert slice_passes(slice_) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("campaign")] == []
        agent.close()
