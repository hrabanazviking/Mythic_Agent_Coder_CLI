"""M-228 Team-of-one scaling - pure-layer tests.

TIER: integration

The pure layer is the steward, held as data: one
record per endeavour, held whole - the campaign it
answers for, named by campaign id, its title, the
steps it walked in walk endeavour and the evidence
it carries, held by campaign. The question walk is
explicit - named, sized, grained, matched,
served, with their legal steps held as data -
and a endeavour's standing is derived at call
time: a endeavour that opens anywhere but scoped, steps where the sequence does not allow,
carries a bare claim in place of held evidence,
or has not yet scoped served stands open,
named in its gaps. A endeavour stands only for
an active campaign: a endeavour naming no held
campaign, or one that is not active, refuses by
name. The endeavour's trace - its walked steps
as one line - is derived at call time, and a held
trace record stands current only while it agrees
with the derived trace. The index, panel,
verdict, ledger, trace, endeavour and current
endeavour are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
question was actually answered, matched or
served live. The shipped example book is held
in a data file, and a loader reads a book from
any file. No charter row names this campaign: the
M-171 TUI charter binds Part VIII alone, and the
M-005 method charter names the whole of Part IX
as the part that executes it, both pinned live
below.
"""


from pathlib import Path

import pytest
import yaml

from mythic_agent.core.team_scaling import (
    EXAMPLE_STAGE,
    BARE_CLAIMS,
    HELD_EVIDENCE,
    INDEX_ACTION,
    STAGES,
    CLAIM_KINDS,
    TRANSITIONS,
    CAMPAIGN_STATES,
    STAGE_FIELDS,
    PLAIN_EXPLANATION,
    ENDEAVOUR_RESOURCE,
    ENDEAVOUR_RULE,
    ENDEAVOUR_SCHEMA,
    ENDEAVOUR_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    EndeavourRecord,
    IndexEndeavour,
    CampaignRef,
    NoteRecord,
    EndeavourBook,
    EndeavourIndex,
    EndeavourPanel,
    EndeavourRegistry,
    EndeavourVerdict,
    EndeavourView,
    trace_for_endeavour,
    ledger_record,
    book_record,
    build_trace,
    build_book,
    build_endeavour,
    build_campaign_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_endeavour,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    endeavour_for_check,
    endeavour_gaps,
    endeavour_endeavour,
    endeavour_record,
    endeavour_green,
    endeavours_for_campaign,
    first_note,
    format_book,
    format_endeavour,
    format_index,
    format_note,
    format_stage,
    format_panel,
    format_endeavour_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    campaign_record,
    load_endeavour,
    legal_step,
    load_endeavour_file,
    next_stage,
    normalize_stage,
    normalize_claim_kind,
    normalize_campaign_state,
    normalize_stance,
    normalize_view_filter,
    note_for_endeavour,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_endeavour_args,
    green_endeavours,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_endeavours,
    validate_book,
    validate_endeavour,
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
from mythic_agent.core.method_charter import (
    load_charter as load_method_charter,
)
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.tui_redesign_charter import load_charter

ROOT = Path(__file__).resolve().parents[1]
ON = "2026-11-11"
BY = "the coordinator"
EXAMPLE_TITLE = "Team-of-one scaling at the M-228 slice run"
EXAMPLE_STAGES = ["served", "served", "served"]
EXAMPLE_RUN_IDS = (
    "endeavour-held-endeavour", "endeavour-retried-endeavour",
    "endeavour-own-endeavour", "endeavour-bare-endeavour",
    "endeavour-leaping-endeavour")
EXAMPLE_TRACE = "scoped > sized > grained > matched > served"


def _ref(**overrides):
    fields = {
        "campaign_id": "campaign-test",
        "seq": 1,
        "title": "A test campaign",
        "state": "live",
        "detail": "A test campaign reference held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "endeavour-test",
    }
    fields.update(overrides)
    return build_campaign_ref(fields)


def _endeavour(**overrides):
    fields = {
        "endeavour_id": "endeavour-test",
        "seq": 1,
        "campaign_id": "campaign-test",
        "title": "A test endeavour",
        "stages": ["scoped", "sized", "grained", "matched", "served"],
        "claims": [],
        "detail": "A test endeavour held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "endeavour-test",
    }
    fields.update(overrides)
    return build_endeavour(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "endeavour-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "endeavour_id": "endeavour-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "endeavour-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "endeavour_id": "endeavour-test",
        "trace": "scoped > sized > grained > matched > served",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "endeavour-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(campaigns=None, endeavours=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": ENDEAVOUR_SCHEMA,
        "campaign": "M-228",
        "team_scaling": {"title": "A test endeavour book"},
        "campaigns": [item.to_record() for item in (
            campaigns if campaigns is not None else [_ref()])],
        "endeavour_records": [item.to_record() for item in (
            endeavours if endeavours is not None else [_endeavour()])],
        "views": [item.to_record() for item in (
            views if views is not None else [_view()])],
        "notes": [item.to_record() for item in (notes or [])],
        "traces": [item.to_record() for item in (
            traces or [])],
        "panels": [],
    }
    fields.update(overrides)
    return build_book(fields)


def _mixed_book():
    return _book(endeavours=[
        _endeavour(),
        _endeavour(endeavour_id="endeavour-hidden", seq=2,
               title="A hidden endeavour", stages=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_endeavour()
    assert book.title == EXAMPLE_TITLE
    assert book.endeavour_ids() == EXAMPLE_RUN_IDS
    assert book.campaign_ids() == (
        "campaign-m227-workflow", "campaign-m228-scaling",
        "campaign-m229-teachable")
    assert [v.view_id for v in book.views] == [
        "view-endeavours", "view-served"]
    assert [m.endeavour_id for m in book.notes] == [
        "endeavour-held-endeavour", "endeavour-bare-endeavour"]
    assert [a.endeavour_id for a in book.traces] == ["endeavour-held-endeavour"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m227-campaign"
    assert panel.as_of == "2026-11-11"
    assert [row.item_id for row in panel.rows] == list(book.endeavour_ids())
    derived = derive_panel(book, "view-endeavours")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-endeavours").verdict == "held"
    assert derive_verdict(book, "view-endeavours").green_shown == 3
    assert derive_verdict(book, "view-served").verdict == "served"
    assert derive_verdict(book, "view-served").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / ENDEAVOUR_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == ENDEAVOUR_SCHEMA
    assert raw["campaign"] == "M-228"
    assert "verdict" not in raw
    assert "endeavour_index" not in raw
    assert "ledger" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-228")]
    assert slice_.title == "Team-of-one scaling"
    assert slice_.part == 9
    assert "the same machinery serves a hobby repo and a 500-slice epic without ceremony change" in slice_.summary
    assert "grain follows the work, not the tool's ego" in slice_.summary
    assert ENDEAVOUR_SLICE == "M-228"

def test_charter_rows_do_not_name_m228():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-228" not in owners
    method = load_method_charter()
    assert "M-201" in method.source_note
    assert "M-232" in method.source_note
    assert "YRSA_CODING_JUGGERNAUT" in method.source_note

def test_closed_vocabularies():
    assert COMPLETE_WORDS == ("complete", "open")
    assert STAGE_FIELDS == ("stages", "claims")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "complete", "open")
    assert VERDICT_WORDS == ("served", "held", "blocked")
    assert CAMPAIGN_STATES == ("live", "dormant")
    assert STAGES == ("scoped", "sized", "grained", "matched", "served")
    assert HELD_EVIDENCE == ("scope_ref", "size_ref", "grain_ref", "crew_ref", "endeavour_ref")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_KINDS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["matched"] == ("scoped", "served")
    assert TRANSITIONS["served"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_STAGE == "served"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_campaign_state("LIVE") == "live"
    assert normalize_stage("GRAINED") == "grained"
    assert normalize_claim_kind("FEELING") == "feeling"
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    with pytest.raises(ValueError):
        normalize_campaign_state("blessed")
    with pytest.raises(ValueError):
        normalize_stage("polish")
    with pytest.raises(ValueError):
        normalize_claim_kind("weather")
    assert legal_step("grained", "matched") is True
    assert legal_step("sized", "served") is False
    assert legal_step("served", "scoped") is False
    assert next_stage("scoped") == "sized"
    assert next_stage("grained") == "matched"
    assert next_stage("matched", failed=True) == "scoped"
    assert next_stage("matched") == "served"
    assert next_stage("served") is None
    assert "held as data alone" in ENDEAVOUR_RULE
    assert "endeavour sequence" in ENDEAVOUR_RULE
    assert "M-228" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /scaling")

def test_shipped_book_judged_honestly_as_data():
    book = load_endeavour()
    opening = book.endeavour_for("endeavour-held-endeavour")
    assert endeavour_green(opening, book) is True
    assert endeavour_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Endeavour: The held endeavour",
        "Campaign: campaign-m227-workflow",
        "Stage: served",
        "Claims: scope_ref")
    asking = book.endeavour_for("endeavour-bare-endeavour")
    assert endeavour_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert endeavour_green(asking, book) is False
    skipping = book.endeavour_for("endeavour-leaping-endeavour")
    assert endeavour_gaps(skipping, book) == (
        "steps from sized to served, which the endeavour sequence "
        "does not allow",)
    assert [g.endeavour_id for g in green_endeavours(book)] == [
        "endeavour-held-endeavour", "endeavour-retried-endeavour", "endeavour-own-endeavour"]
    index = derive_index(book)
    assert [e.stage for e in index.endeavours] == EXAMPLE_STAGES
    assert index.gaps == ("endeavour-bare-endeavour", "endeavour-leaping-endeavour")
    assert endeavour_for_check(book, EXAMPLE_STAGE).endeavour_id == (
        "endeavour-held-endeavour")
    assert endeavour_for_check(book, "triple endeavour") is None
    assert transition_breaks(book) == (
        "endeavour-leaping-endeavour: sized > served",)
    assert [g.endeavour_id for g in endeavour_endeavour(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "endeavour-held-endeavour") == EXAMPLE_TRACE
    assert trace_current(book, "endeavour-held-endeavour") is True
    assert trace_current(book, "endeavour-retried-endeavour") is False
    assert trace_for_endeavour(
        book, "endeavour-held-endeavour").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_endeavour(
        book, "endeavour-held-endeavour", "note").note_id == (
            "note-note-first")
    assert note_for_endeavour(book, "endeavour-nope") is None
    assert current_endeavour(book).endeavour_id == "endeavour-bare-endeavour"
    ledger = ledger_record(book)
    assert ledger["standings"] == [
        {"standing": "complete", "endeavour_records": 3},
        {"standing": "open", "endeavour_records": 2}]
    assert ledger["total"] == 5
    assert ledger["current_endeavour"] == "endeavour-bare-endeavour"
    assert ledger["traces"] == [
        {"endeavour_id": "endeavour-held-endeavour", "trace": "current"},
        {"endeavour_id": "endeavour-retried-endeavour", "trace": "unheld"},
        {"endeavour_id": "endeavour-own-endeavour", "trace": "unheld"},
        {"endeavour_id": "endeavour-bare-endeavour", "trace": "unheld"},
        {"endeavour_id": "endeavour-leaping-endeavour", "trace": "unheld"}]
    assert ledger["breaks"] == ["endeavour-leaping-endeavour: sized > served"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 244
    assert citizen["next_slice"] == "M-245"
    assert citizen["m228_title"] == "Team-of-one scaling"
    assert citizen["m228_part"] == 9
    assert citizen["m228_status"] == "done"

def test_endeavour_record_round_trips():
    endeavour = _endeavour()
    assert validate_endeavour(endeavour) is endeavour
    rebuilt = build_endeavour(endeavour.to_record())
    assert rebuilt == endeavour
    assert rebuilt.item_id == "endeavour-test"
    assert rebuilt.stage == "served"
    record = endeavour_record(endeavour)
    assert record["type"] == "endeavour_endeavour"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert campaign_record(ref)["type"] == "endeavour_run"
    assert campaign_record(ref)["state"] == "live"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _endeavour(stages=[])
    assert endeavour_gaps(silent) == (
        "has passed through no step: the endeavour has not started",)
    assert endeavour_green(silent) is False
    walking = _endeavour(stages=["scoped", "sized"])
    assert endeavour_gaps(walking) == (
        "has not reached served: the endeavour stands at sized",)
    assert walking.stage == "sized"
    sideways = _endeavour(stages=["sized", "grained", "matched", "served"])
    assert endeavour_gaps(sideways) == (
        "opens at sized, not at scoped: the endeavour opens "
        "with the reflection",)
    repaired = _endeavour(stages=["scoped", "sized", "grained", "matched", "scoped", "sized", "grained", "matched", "served"])
    assert endeavour_gaps(repaired) == ()
    assert endeavour_green(repaired) is True
    with pytest.raises(ValueError):
        _endeavour(stages=[42])
    with pytest.raises(ValueError):
        _endeavour(stages="inspect as a bare string")
    with pytest.raises(ValueError):
        _endeavour(stages=["scoped", "polish"])
    with pytest.raises(ValueError):
        _endeavour(claims=["weather"])
    with pytest.raises(ValueError):
        _endeavour(claims="scope_ref")
    none_endeavour = _endeavour(stages=None, claims=None)
    assert none_endeavour.stages == ()
    assert none_endeavour.claims == ()

def test_endeavour_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "endeavours", "coverage", "current_endeavour",
                "ledger", "endeavour"):
        fields = _endeavour().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_endeavour(fields)
    fields = _endeavour().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_endeavour(fields)


def test_endeavour_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _endeavour().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_endeavour(fields)


def test_endeavour_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _endeavour(title="")
    with pytest.raises(ValueError):
        _endeavour(campaign_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "scoped > sized > grained > matched > served"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_endeavours_own_fields():
    endeavour = _endeavour(claims=["scope_ref"])
    assert plain_lines(endeavour) == (
        "Endeavour: A test endeavour",
        "Campaign: campaign-test",
        "Stage: served",
        "Claims: scope_ref")
    segment = segment_of(endeavour)
    assert segment.startswith("endeavour-test: A test endeavour")
    assert "stage: 'served'" in segment
    assert "gaps: none" in segment
    assert plain_words(endeavour).startswith(
        "A test endeavour - from campaign-test")

def test_red_endeavours_stand_named_in_their_gaps():
    asking = _endeavour(claims=["feeling", "scope_ref", "summary"])
    assert endeavour_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert endeavour_green(asking) is False
    skipping = _endeavour(stages=["scoped", "sized", "served"])
    assert endeavour_gaps(skipping) == (
        "steps from sized to served, which the endeavour sequence "
        "does not allow",)
    book = _book(endeavours=[
        _endeavour(),
        _endeavour(endeavour_id="endeavour-skipping", seq=2,
             stages=["scoped", "sized", "served"]),
    ])
    assert transition_breaks(book) == (
        "endeavour-skipping: sized > served",)
    assert current_endeavour(book).endeavour_id == "endeavour-skipping"
    assert [g.endeavour_id for g in endeavour_endeavour(book)] == [
        "endeavour-test", "endeavour-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "endeavour_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "endeavour_note"
    assert record["endeavour_id"] == "endeavour-test"
    assert view_plain_words(view) == "View view-test: shows all endeavours."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_endeavours_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.stage for e in index.endeavours] == ["served"]
    assert index.endeavours[0] == IndexEndeavour(
        stage="served",
        endeavour_id="endeavour-test", title="A test endeavour")
    assert index.gaps == ("endeavour-hidden",)
    record = index_record(book)
    assert record["type"] == "endeavour_index"
    assert record["gaps"] == ["endeavour-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "endeavour_book"

def test_check_target_reaches_its_endeavour_and_an_unheld_target_reaches_nothing():
    book = load_endeavour()
    assert endeavour_for_check(book, "served").endeavour_id == (
        "endeavour-held-endeavour")
    assert endeavour_for_check(book, "") is None
    assert endeavour_for_check(book, None) is None
    assert endeavour_for_check(book, "not held at all") is None
    text = format_stage(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_endeavour()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Endeavour note note endeavour-held-endeavour" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").endeavour_id == "endeavour-test"
    assert note_for_endeavour(book, "endeavour-test").note_id == "note-test"
    assert note_for_endeavour(book, "endeavour-test", "praise") is None
    with pytest.raises(KeyError):
        book.note_for("note-nope")
    with pytest.raises(ValueError):
        _book(notes=[_note(), _note(note_id="note-two", seq=2)])


def test_panel_is_derived_and_a_stored_panel_must_agree():
    book = _mixed_book()
    panel = derive_panel(book)
    assert panel.panel_id == "panel-view-test"
    assert panel.total_items == 2
    assert panel.total_shown == 2
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 1, "open": 1}
    assert validate_panel(panel, book) is panel
    assert build_panel(panel.to_record(), book) == panel
    row = build_row(None, _endeavour(), book)
    assert row.standing == "complete"
    assert validate_row(row, _endeavour(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_endeavours():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "endeavour_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "served"
    empty_book = _book(endeavours=[_endeavour(stages=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(EndeavourVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_readings():
    book = load_endeavour()
    assert [g.endeavour_id for g in shown_endeavours(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.endeavour_id for g in shown_endeavours(book, "view-served")] == [
        "endeavour-held-endeavour", "endeavour-retried-endeavour", "endeavour-own-endeavour"]
    assert [g.endeavour_id for g in endeavours_for_campaign(
        book, "campaign-m228-scaling")] == [
            "endeavour-own-endeavour", "endeavour-bare-endeavour",
            "endeavour-leaping-endeavour"]
    assert endeavours_for_campaign(book, "campaign-nope") == ()
    assert current_endeavour(_mixed_book()).endeavour_id == "endeavour-hidden"
    assert current_endeavour(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "endeavour-test") == (
        "scoped > sized > grained > matched > served")
    assert trace_current(stale, "endeavour-test") is False
    assert ledger_record(stale)["traces"] == [
        {"endeavour_id": "endeavour-test", "trace": "stale"}]

def test_size_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(endeavours=[_endeavour(), _endeavour(seq=2)])
    with pytest.raises(ValueError):
        _book(endeavours=[_endeavour(), _endeavour(endeavour_id="endeavour-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(endeavours=[_endeavour(campaign_id="campaign-nope")])
    with pytest.raises(ValueError):
        _book(campaigns=[_ref(), _ref(
            campaign_id="campaign-cold", seq=2, state="dormant")],
            endeavours=[_endeavour(campaign_id="campaign-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(campaign_id="campaign-nope")])
    fields = {
        "schema": ENDEAVOUR_SCHEMA, "campaign": "M-228",
        "team_scaling": {"title": "A grained book"},
        "campaigns": [_ref().to_record()],
        "endeavour_records": [_endeavour().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "served"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_endeavour"] = "endeavour-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_endeavour")
    fields["trace"] = "endeavour-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / ENDEAVOUR_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "team_scaling.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_endeavour_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.endeavour_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = EndeavourRegistry()
    assert registry.title() is None
    registry.register_campaign_ref(_ref())
    registry.register_endeavour(_endeavour())
    registry.register_view(_view())
    assert [g.endeavour_id for g in registry.list_endeavours()] == ["endeavour-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_endeavour("endeavour-test").title == "A test endeavour"
    assert registry.get_slice("campaign-test").state == "live"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("endeavour-test").endeavour_id == "endeavour-test"
    with pytest.raises(ValueError):
        registry.register_endeavour(_endeavour(seq=9))
    with pytest.raises(ValueError):
        registry.register_endeavour(_endeavour(endeavour_id="endeavour-two"))
    with pytest.raises(KeyError):
        registry.get_endeavour("endeavour-nope")
    assert registry.book().title == "An unheld endeavour book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = EndeavourRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test endeavour book"
    assert registry.title() == "A test endeavour book"
    assert len(registry.list_endeavours()) == 2
    other = EndeavourRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    endeavour = _endeavour()
    assert "A test endeavour" in plain_words(endeavour)
    assert panel_plain_words(_mixed_book()).startswith(
        "The endeavour book holds 2 endeavours")
    assert verdict_plain_words(_mixed_book()) == (
        "The endeavours stand held: 1 of 2 shown endeavours stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green endeavours; red, "
        "named in its gaps: endeavour-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_endeavour(endeavour)
    assert "Endeavour: A test endeavour" in text
    assert "stands complete" in text
    text = format_endeavour(_endeavour(stages=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The Endeavour Gate (M-228) - A test endeavour book" in book_text
    assert "endeavour-hidden" in format_book(_mixed_book(), "campaign-test")
    assert "Endeavour panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "served - A test endeavour (endeavour-test)" in index_text
    assert "endeavour-hidden" in index_text
    screen = format_endeavour_screen()
    assert "The Endeavour Gate (M-228)" in screen
    assert "endeavour-bare-endeavour" in screen

def test_parse_args_well_and_loader_targets():
    assert parse_endeavour_args("") == ("show", None)
    assert parse_endeavour_args(None) == ("show", None)
    assert parse_endeavour_args("show") == ("show", None)
    assert parse_endeavour_args("endeavour endeavour-test") == (
        "endeavour", "endeavour-test")
    assert parse_endeavour_args("stage served") == (
        "stage", "served")
    assert parse_endeavour_args("campaign campaign-test") == (
        "campaign", "campaign-test")
    assert parse_endeavour_args("view view-test") == ("view", "view-test")
    assert parse_endeavour_args("note note-test") == ("note", "note-test")
    assert parse_endeavour_args("index") == ("index", None)
    assert parse_endeavour_args("panel") == ("panel", None)
    assert parse_endeavour_args("verdict") == ("verdict", None)
    for bad in ("dance", "endeavour", "stage", "campaign", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_endeavour_args(bad)
    ledger = ledger_record()
    assert ledger["type"] == "endeavour_well"
    assert ledger["total"] == 5
    assert ledger["current_endeavour"] == "endeavour-bare-endeavour"
    book = load_endeavour({
        "schema": ENDEAVOUR_SCHEMA, "campaign": "M-228",
        "team_scaling": {"title": "A grained book"},
        "campaigns": [_ref().to_record()],
        "endeavour_records": [_endeavour().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, EndeavourBook)
    assert book.title == "A grained book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_endeavour({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_endeavour({"campaign": "M-999"})
    built = build_endeavour(
        endeavour_id="endeavour-kw", seq=3, campaign_id="campaign-test",
        title="Kw Endeavour", stages=["scoped", "sized", "grained", "matched", "served"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="endeavour-test")
    assert built.endeavour_id == "endeavour-kw"
    assert endeavour_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-228 agent layer: the agent holds a endeavour
# book for the session, endeavours and views are
# published as session news through the
# checkpoint target (ledger first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held endeavours, the ledger is derived from
# the held endeavours' completeness, the roadmap standing
# is matched from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no campaign. This layer endeavours
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session ledger news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_ENDEAVOUR_EVENT_TYPES = (
    "endeavour_endeavour", "endeavour_run", "endeavour_view",
    "endeavour_panel", "endeavour_verdict")


def _endeavour_events(store, session_id, campaign):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == campaign]


def _write_scaling_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / ENDEAVOUR_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "team_scaling.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestEndeavourAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.scaling_status()
        assert status["endeavour_records"] == []
        assert status["campaigns"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["scaling_book"]["title"] == EXAMPLE_TITLE
        assert len(status["scaling_book"]["campaigns"]) == 3
        assert len(status["scaling_book"]["endeavour_records"]) == 5
        assert len(status["scaling_book"]["views"]) == 2
        assert len(status["scaling_book"]["notes"]) == 2
        assert len(status["scaling_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-m227-campaign"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["stage"] for e in status["index"]["endeavours"]] == (
            EXAMPLE_STAGES)
        assert status["index"]["gaps"] == [
            "endeavour-bare-endeavour", "endeavour-leaping-endeavour"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["ledger"]["total"] == 5
        assert status["ledger"]["current_endeavour"] == "endeavour-bare-endeavour"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 244
        assert status["roadmap"]["next_slice"] == "M-245"
        assert status["roadmap"]["m228_title"] == "Team-of-one scaling"
        assert "held as data alone" in status["rule"]
        assert "endeavour-bare-endeavour" in status["plain_words"]
        assert "The Endeavour Gate (M-228)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._scaling_registry()
        assert agent._scaling_registry() is first
        assert agent._scaling_store is first
        for name in ("scaling_book", "scaling_status", "scaling_panel",
                     "scaling_verdict", "scaling_index", "report_scaling"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_scaling_registry", "scaling_book", "scaling_status",
            "get_scaling_endeavour", "get_scaling_view", "get_scaling_note",
            "endeavours_for_campaign", "scaling_green",
            "scaling_panel", "scaling_verdict", "scaling_index",
            "register_scaling_endeavour", "register_scaling_view",
            "view_scaling", "register_scaling_book",
            "record_scaling_book", "report_scaling",
            "_publish_scaling_record", "_scaling_screen",
            "_scaling_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.scaling_status()
        assert agent.get_scaling_endeavour(
            "endeavour-held-endeavour").title == "The held endeavour"
        assert agent.get_scaling_view(
            "view-endeavours").view_filter == "all"
        assert agent.get_scaling_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.endeavour_id for d in agent.endeavours_for_campaign(
            "campaign-m228-scaling")] == [
            "endeavour-own-endeavour", "endeavour-bare-endeavour",
            "endeavour-leaping-endeavour"]
        assert [d.endeavour_id for d in agent.scaling_green()] == [
            "endeavour-held-endeavour", "endeavour-retried-endeavour", "endeavour-own-endeavour"]
        agent.scaling_panel()
        agent.scaling_verdict()
        agent.scaling_index()
        agent.report_scaling()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _ENDEAVOUR_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_scaling_endeavour("endeavour-nope")
        with pytest.raises(KeyError):
            agent.get_scaling_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_scaling_note("note-nope")
        with pytest.raises(ValueError):
            agent.endeavours_for_campaign("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_scaling_endeavour(_endeavour())
        status = agent.scaling_status()
        assert [d["endeavour_id"] for d in status["endeavour_records"]] == ["endeavour-test"]
        assert status["book"]["title"] == "An unheld endeavour book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["stage"] for e in status["index"]["endeavours"]] == [
            "served"]
        assert status["first_note"] is None
        assert "endeavour-test" in status["screen"]
    def test_held_endeavour_never_falls_back_to_the_example(
            self, agent):
        agent.register_scaling_endeavour(_endeavour())
        with pytest.raises(KeyError):
            agent.get_scaling_endeavour("endeavour-held-endeavour")
        with pytest.raises(KeyError):
            agent.get_scaling_view("view-endeavours")
        with pytest.raises(KeyError):
            agent.get_scaling_note("note-note-first")
        endeavour = agent.get_scaling_endeavour("endeavour-test")
        assert endeavour.title == "A test endeavour"
        assert agent.scaling_book().title == (
            "An unheld endeavour book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_scaling_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.endeavour_id == "endeavour-held-endeavour"
        status = agent.scaling_status()
        assert status["index"]["gaps"] == [
            "endeavour-bare-endeavour", "endeavour-leaping-endeavour"]
        assert status["first_note"]["endeavour_id"] == (
            "endeavour-held-endeavour")
        assert status["first_note"]["stance"] == "note"

class TestEndeavourAgentHolding:
    def test_register_endeavour_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_scaling_endeavour(_endeavour())
        assert result["endeavour"]["endeavour_id"] == "endeavour-test"
        assert result["record_news"]["type"] == "endeavour_endeavour"
        assert "endeavour-test" in result["screen"]
        events = _endeavour_events(store, session_id, "endeavour_endeavour")
        assert len(events) == 1
        agent.close()

    def test_duplicate_endeavour_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_scaling_endeavour(_endeavour())
        with pytest.raises(ValueError):
            agent.register_scaling_endeavour(_endeavour(seq=9))
        with pytest.raises(ValueError):
            agent.register_scaling_endeavour(_endeavour(endeavour_id="endeavour-two"))
        events = _endeavour_events(store, session_id, "endeavour_endeavour")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_scaling_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_endeavour_events(
            store, session_id, "endeavour_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_scaling_endeavour(_endeavour())
        result = agent.view_scaling("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "endeavour_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "served"
        assert len(_endeavour_events(
            store, session_id, "endeavour_view")) == 1
        assert len(_endeavour_events(
            store, session_id, "endeavour_panel")) == 1
        assert len(_endeavour_events(
            store, session_id, "endeavour_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_endeavour(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_scaling_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "endeavour_run", "endeavour_endeavour", "endeavour_view"]
        assert len(_endeavour_events(
            store, session_id, "endeavour_endeavour")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_scaling_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "endeavour_panel"
        assert result["index_record"]["gaps"] == [
            "endeavour-bare-endeavour", "endeavour-leaping-endeavour"]
        with pytest.raises(ValueError):
            agent.record_scaling_book()
        assert len(_endeavour_events(
            store, session_id, "endeavour_run")) == 3
        assert len(_endeavour_events(
            store, session_id, "endeavour_endeavour")) == 5
        assert len(_endeavour_events(
            store, session_id, "endeavour_view")) == 2
        agent.close()

    def test_book_from_a_file_is_sized_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_scaling_book_file(tmp_path)
        book = load_endeavour_file(path)
        result = agent.record_scaling_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_runrt_renders_example_then_held_book_only(self, agent):
        endeavour = agent.report_scaling()
        assert endeavour["book"]["title"] == EXAMPLE_TITLE
        assert endeavour["verdict"]["verdict"] == "held"
        assert endeavour["index"]["gaps"] == [
            "endeavour-bare-endeavour", "endeavour-leaping-endeavour"]
        assert "endeavour-held-endeavour" in endeavour["book_text"]
        assert "served - The held endeavour (endeavour-held-endeavour)" in endeavour["index_text"]
        agent.register_scaling_endeavour(_endeavour())
        endeavour = agent.report_scaling()
        assert endeavour["book"]["title"] == "An unheld endeavour book"
        assert endeavour["panel"] is None
        assert endeavour["verdict"] is None

class TestEndeavourTerminalHeading:
    def test_show_endeavour_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/scaling")
        assert "The Endeavour Gate (M-228)" in text
        _, _, text = _slash(agent, "/scaling endeavour endeavour-held-endeavour")
        assert "Endeavour: The held endeavour" in text
        _, _, text = _slash(
            agent, "/scaling stage served")
        assert "Endeavour: The held endeavour" in text
        _, _, text = _slash(agent, "/scaling stage triple endeavour")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/scaling campaign campaign-m228-scaling")
        assert "endeavour-bare-endeavour" in text
        assert "endeavour-held-endeavour" not in text
        _, _, text = _slash(agent, "/scaling view view-endeavours")
        assert "filter all" in text
        _, _, text = _slash(agent, "/scaling note note-note-first")
        assert "Endeavour note note endeavour-held-endeavour" in text
        _, _, text = _slash(agent, "/scaling index")
        assert "Endeavour index" in text
        assert "endeavour-bare-endeavour" in text
        _, _, text = _slash(agent, "/scaling panel")
        assert "Endeavour panel under view view-endeavours" in text
        _, _, text = _slash(agent, "/scaling verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/scaling [show|endeavour <endeavour-id>"
                "|stage <stage>|campaign <campaign-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/scaling dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/scaling endeavour endeavour-nope")
        assert "no endeavour named" in text
@pytest.fixture()
def endeavour_handler(agent, monkeypatch):
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


def _endeavour_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestEndeavourCommand:
    def test_show_is_default(self, endeavour_handler, agent):
        endeavour_handler._handle_scaling("")
        assert "The Endeavour Gate (M-228)" in (
            _endeavour_published_text(endeavour_handler))

    def test_endeavour_check_slice_view_note_index_panel_verdict(
            self, endeavour_handler, agent):
        endeavour_handler._handle_scaling("endeavour endeavour-held-endeavour")
        assert "Endeavour: The held endeavour" in _endeavour_published_text(
            endeavour_handler)
        endeavour_handler._handle_scaling(
            "stage served")
        assert "Endeavour: The held endeavour" in _endeavour_published_text(
            endeavour_handler)
        endeavour_handler._handle_scaling("campaign campaign-m228-scaling")
        assert "endeavour-bare-endeavour" in _endeavour_published_text(
            endeavour_handler)
        endeavour_handler._handle_scaling("view view-endeavours")
        assert "filter all" in _endeavour_published_text(endeavour_handler)
        endeavour_handler._handle_scaling("note note-note-first")
        assert "Endeavour note note endeavour-held-endeavour" in (
            _endeavour_published_text(endeavour_handler))
        endeavour_handler._handle_scaling("index")
        assert "Endeavour index" in _endeavour_published_text(endeavour_handler)
        endeavour_handler._handle_scaling("panel")
        assert "Endeavour panel under view" in _endeavour_published_text(
            endeavour_handler)
        endeavour_handler._handle_scaling("verdict")
        assert "held" in _endeavour_published_text(endeavour_handler)
    def test_bad_grammar_is_published(
            self, endeavour_handler, agent):
        endeavour_handler._handle_scaling("dance party")
        assert USAGE in _endeavour_published_text(endeavour_handler)
        endeavour_handler._handle_scaling("endeavour endeavour-nope")
        assert "no endeavour named" in _endeavour_published_text(
            endeavour_handler)


class TestChatScreenRoutingEndeavour:
    def test_onwell_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/scaling panel", _FakeLog())
        assert calls == [("/scaling", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/scaling[/green] - show the Endeavour gate (M-228)" in (
            text)
        assert ('"/scaling": "Usage: /scaling | '
                '/scaling endeavour <endeavour-id>') in text

class TestEndeavourDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.scaling_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-endeavours"
        verdict = agent.scaling_verdict()
        assert verdict.verdict == "held"
        found = agent.scaling_verdict("view-served")
        assert found.verdict == "served"
        assert found.green_shown == 3
        agent.register_scaling_endeavour(_endeavour())
        with pytest.raises(ValueError):
            agent.scaling_panel()
        with pytest.raises(ValueError):
            agent.scaling_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_scaling_endeavour(_endeavour(stages=[]))
        result = agent.view_scaling("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.scaling_index()
        assert [e["stage"] for e in result["index"]["endeavours"]] == (
            EXAMPLE_STAGES)
        assert result["index"]["gaps"] == [
            "endeavour-bare-endeavour", "endeavour-leaping-endeavour"]
        assert "served - The held endeavour (endeavour-held-endeavour)" in (
            result["index_text"])
        endeavour = agent.get_scaling_endeavour("endeavour-leaping-endeavour")
        assert endeavour_gaps(endeavour, agent.scaling_book()) == (
            "steps from sized to served, which the endeavour sequence "
            "does not allow",)
        assert endeavour_green(endeavour, agent.scaling_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _ENDEAVOUR_EVENT_TYPES] == []
        agent.close()
