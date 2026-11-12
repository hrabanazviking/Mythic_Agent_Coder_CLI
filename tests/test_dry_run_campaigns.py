"""M-224 Dry-run campaigns - pure-layer tests.

TIER: integration

The pure layer is the taxonomist, held as data: one
record per rehearsal, held whole - the campaign it
answers for, named by campaign id, its title, the
steps it walked in walk order and the evidence
it carries, held by campaign. The question walk is
explicit - named, dealt, gated, mocked,
proven, with their legal steps held as data -
and a rehearsal's standing is derived at call
time: a rehearsal that opens anywhere but planned, steps where the sequence does not allow,
carries a bare claim in place of held evidence,
or has not yet planned proven stands open,
named in its gaps. A rehearsal stands only for
an active campaign: a rehearsal naming no held
campaign, or one that is not active, refuses by
name. The rehearsal's trace - its walked steps
as one line - is derived at call time, and a held
trace record stands current only while it agrees
with the derived trace. The index, panel,
verdict, ledger, trace, order and current
rehearsal are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
question was actually answered, mocked or
proven live. The shipped example book is held
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

from mythic_agent.core.dry_run_campaigns import (
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
    REHEARSAL_RESOURCE,
    REHEARSAL_RULE,
    REHEARSAL_SCHEMA,
    REHEARSAL_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    RehearsalRecord,
    IndexRehearsal,
    CampaignRef,
    NoteRecord,
    RehearsalBook,
    RehearsalIndex,
    RehearsalPanel,
    RehearsalRegistry,
    RehearsalVerdict,
    RehearsalView,
    trace_for_rehearsal,
    ledger_record,
    book_record,
    build_trace,
    build_book,
    build_rehearsal,
    build_campaign_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_rehearsal,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    rehearsal_for_check,
    rehearsal_gaps,
    rehearsal_order,
    rehearsal_record,
    rehearsal_green,
    rehearsals_for_campaign,
    first_note,
    format_book,
    format_rehearsal,
    format_index,
    format_note,
    format_stage,
    format_panel,
    format_rehearsal_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    campaign_record,
    load_rehearsal,
    legal_step,
    load_rehearsal_file,
    next_stage,
    normalize_stage,
    normalize_claim_kind,
    normalize_campaign_state,
    normalize_stance,
    normalize_view_filter,
    note_for_rehearsal,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_rehearsal_args,
    green_rehearsals,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_rehearsals,
    validate_book,
    validate_rehearsal,
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
EXAMPLE_TITLE = "Dry-run campaigns at the M-224 slice run"
EXAMPLE_STAGES = ["proven", "proven", "proven"]
EXAMPLE_RUN_IDS = (
    "rehearsal-held-rehearsal", "rehearsal-retried-rehearsal",
    "rehearsal-own-rehearsal", "rehearsal-bare-rehearsal",
    "rehearsal-leaping-rehearsal")
EXAMPLE_TRACE = "planned > dealt > gated > mocked > proven"


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
        "origin_session": "rehearsal-test",
    }
    fields.update(overrides)
    return build_campaign_ref(fields)


def _rehearsal(**overrides):
    fields = {
        "rehearsal_id": "rehearsal-test",
        "seq": 1,
        "campaign_id": "campaign-test",
        "title": "A test rehearsal",
        "stages": ["planned", "dealt", "gated", "mocked", "proven"],
        "claims": [],
        "detail": "A test rehearsal held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "rehearsal-test",
    }
    fields.update(overrides)
    return build_rehearsal(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "rehearsal-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "rehearsal_id": "rehearsal-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "rehearsal-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "rehearsal_id": "rehearsal-test",
        "trace": "planned > dealt > gated > mocked > proven",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "rehearsal-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(campaigns=None, rehearsals=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": REHEARSAL_SCHEMA,
        "campaign": "M-224",
        "dry_run_campaigns": {"title": "A test rehearsal book"},
        "campaigns": [item.to_record() for item in (
            campaigns if campaigns is not None else [_ref()])],
        "rehearsal_records": [item.to_record() for item in (
            rehearsals if rehearsals is not None else [_rehearsal()])],
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
    return _book(rehearsals=[
        _rehearsal(),
        _rehearsal(rehearsal_id="rehearsal-hidden", seq=2,
               title="A hidden rehearsal", stages=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_rehearsal()
    assert book.title == EXAMPLE_TITLE
    assert book.rehearsal_ids() == EXAMPLE_RUN_IDS
    assert book.campaign_ids() == (
        "campaign-m223-failtax", "campaign-m224-dryrun",
        "campaign-m225-export")
    assert [v.view_id for v in book.views] == [
        "view-rehearsals", "view-proven"]
    assert [m.rehearsal_id for m in book.notes] == [
        "rehearsal-held-rehearsal", "rehearsal-bare-rehearsal"]
    assert [a.rehearsal_id for a in book.traces] == ["rehearsal-held-rehearsal"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m223-campaign"
    assert panel.as_of == "2026-11-11"
    assert [row.item_id for row in panel.rows] == list(book.rehearsal_ids())
    derived = derive_panel(book, "view-rehearsals")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-rehearsals").verdict == "held"
    assert derive_verdict(book, "view-rehearsals").green_shown == 3
    assert derive_verdict(book, "view-proven").verdict == "proven"
    assert derive_verdict(book, "view-proven").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / REHEARSAL_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == REHEARSAL_SCHEMA
    assert raw["campaign"] == "M-224"
    assert "verdict" not in raw
    assert "rehearsal_index" not in raw
    assert "ledger" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-224")]
    assert slice_.title == "Dry-run campaigns"
    assert slice_.part == 9
    assert "a campaign can be rehearsed (plan, dealing, gates) with models mocked" in slice_.summary
    assert "the shape proven before" in slice_.summary
    assert REHEARSAL_SLICE == "M-224"

def test_charter_rows_do_not_name_m224():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-224" not in owners
    method = load_method_charter()
    assert "M-201" in method.source_note
    assert "M-232" in method.source_note
    assert "YRSA_CODING_JUGGERNAUT" in method.source_note

def test_closed_vocabularies():
    assert COMPLETE_WORDS == ("complete", "open")
    assert STAGE_FIELDS == ("stages", "claims")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "complete", "open")
    assert VERDICT_WORDS == ("proven", "held", "blocked")
    assert CAMPAIGN_STATES == ("live", "dormant")
    assert STAGES == ("planned", "dealt", "gated", "mocked", "proven")
    assert HELD_EVIDENCE == ("plan_ref", "dealing_ref", "gate_ref", "mock_ref", "proof_ref")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_KINDS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["mocked"] == ("planned", "proven")
    assert TRANSITIONS["proven"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_STAGE == "proven"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_campaign_state("LIVE") == "live"
    assert normalize_stage("GATED") == "gated"
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
    assert legal_step("gated", "mocked") is True
    assert legal_step("dealt", "proven") is False
    assert legal_step("proven", "planned") is False
    assert next_stage("planned") == "dealt"
    assert next_stage("gated") == "mocked"
    assert next_stage("mocked", failed=True) == "planned"
    assert next_stage("mocked") == "proven"
    assert next_stage("proven") is None
    assert "held as data alone" in REHEARSAL_RULE
    assert "rehearsal sequence" in REHEARSAL_RULE
    assert "M-224" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /dryrun")

def test_shipped_book_judged_honestly_as_data():
    book = load_rehearsal()
    opening = book.rehearsal_for("rehearsal-held-rehearsal")
    assert rehearsal_green(opening, book) is True
    assert rehearsal_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Rehearsal: The held rehearsal",
        "Campaign: campaign-m223-failtax",
        "Stage: proven",
        "Claims: plan_ref")
    asking = book.rehearsal_for("rehearsal-bare-rehearsal")
    assert rehearsal_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert rehearsal_green(asking, book) is False
    skipping = book.rehearsal_for("rehearsal-leaping-rehearsal")
    assert rehearsal_gaps(skipping, book) == (
        "steps from dealt to proven, which the rehearsal sequence "
        "does not allow",)
    assert [g.rehearsal_id for g in green_rehearsals(book)] == [
        "rehearsal-held-rehearsal", "rehearsal-retried-rehearsal", "rehearsal-own-rehearsal"]
    index = derive_index(book)
    assert [e.stage for e in index.rehearsals] == EXAMPLE_STAGES
    assert index.gaps == ("rehearsal-bare-rehearsal", "rehearsal-leaping-rehearsal")
    assert rehearsal_for_check(book, EXAMPLE_STAGE).rehearsal_id == (
        "rehearsal-held-rehearsal")
    assert rehearsal_for_check(book, "triple rehearsal") is None
    assert transition_breaks(book) == (
        "rehearsal-leaping-rehearsal: dealt > proven",)
    assert [g.rehearsal_id for g in rehearsal_order(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "rehearsal-held-rehearsal") == EXAMPLE_TRACE
    assert trace_current(book, "rehearsal-held-rehearsal") is True
    assert trace_current(book, "rehearsal-retried-rehearsal") is False
    assert trace_for_rehearsal(
        book, "rehearsal-held-rehearsal").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_rehearsal(
        book, "rehearsal-held-rehearsal", "note").note_id == (
            "note-note-first")
    assert note_for_rehearsal(book, "rehearsal-nope") is None
    assert current_rehearsal(book).rehearsal_id == "rehearsal-bare-rehearsal"
    ledger = ledger_record(book)
    assert ledger["standings"] == [
        {"standing": "complete", "rehearsal_records": 3},
        {"standing": "open", "rehearsal_records": 2}]
    assert ledger["total"] == 5
    assert ledger["current_rehearsal"] == "rehearsal-bare-rehearsal"
    assert ledger["traces"] == [
        {"rehearsal_id": "rehearsal-held-rehearsal", "trace": "current"},
        {"rehearsal_id": "rehearsal-retried-rehearsal", "trace": "unheld"},
        {"rehearsal_id": "rehearsal-own-rehearsal", "trace": "unheld"},
        {"rehearsal_id": "rehearsal-bare-rehearsal", "trace": "unheld"},
        {"rehearsal_id": "rehearsal-leaping-rehearsal", "trace": "unheld"}]
    assert ledger["breaks"] == ["rehearsal-leaping-rehearsal: dealt > proven"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 251
    assert citizen["next_slice"] == "M-252"
    assert citizen["m224_title"] == "Dry-run campaigns"
    assert citizen["m224_part"] == 9
    assert citizen["m224_status"] == "done"

def test_rehearsal_record_round_trips():
    rehearsal = _rehearsal()
    assert validate_rehearsal(rehearsal) is rehearsal
    rebuilt = build_rehearsal(rehearsal.to_record())
    assert rebuilt == rehearsal
    assert rebuilt.item_id == "rehearsal-test"
    assert rebuilt.stage == "proven"
    record = rehearsal_record(rehearsal)
    assert record["type"] == "rehearsal_rehearsal"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert campaign_record(ref)["type"] == "rehearsal_run"
    assert campaign_record(ref)["state"] == "live"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _rehearsal(stages=[])
    assert rehearsal_gaps(silent) == (
        "has passed through no step: the rehearsal has not started",)
    assert rehearsal_green(silent) is False
    walking = _rehearsal(stages=["planned", "dealt"])
    assert rehearsal_gaps(walking) == (
        "has not reached proven: the rehearsal stands at dealt",)
    assert walking.stage == "dealt"
    sideways = _rehearsal(stages=["dealt", "gated", "mocked", "proven"])
    assert rehearsal_gaps(sideways) == (
        "opens at dealt, not at planned: the rehearsal opens "
        "with the reflection",)
    repaired = _rehearsal(stages=["planned", "dealt", "gated", "mocked", "planned", "dealt", "gated", "mocked", "proven"])
    assert rehearsal_gaps(repaired) == ()
    assert rehearsal_green(repaired) is True
    with pytest.raises(ValueError):
        _rehearsal(stages=[42])
    with pytest.raises(ValueError):
        _rehearsal(stages="inspect as a bare string")
    with pytest.raises(ValueError):
        _rehearsal(stages=["planned", "polish"])
    with pytest.raises(ValueError):
        _rehearsal(claims=["weather"])
    with pytest.raises(ValueError):
        _rehearsal(claims="plan_ref")
    none_rehearsal = _rehearsal(stages=None, claims=None)
    assert none_rehearsal.stages == ()
    assert none_rehearsal.claims == ()

def test_rehearsal_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "rehearsals", "coverage", "current_rehearsal",
                "ledger", "order"):
        fields = _rehearsal().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_rehearsal(fields)
    fields = _rehearsal().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_rehearsal(fields)


def test_rehearsal_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _rehearsal().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_rehearsal(fields)


def test_rehearsal_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _rehearsal(title="")
    with pytest.raises(ValueError):
        _rehearsal(campaign_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "planned > dealt > gated > mocked > proven"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_rehearsals_own_fields():
    rehearsal = _rehearsal(claims=["plan_ref"])
    assert plain_lines(rehearsal) == (
        "Rehearsal: A test rehearsal",
        "Campaign: campaign-test",
        "Stage: proven",
        "Claims: plan_ref")
    segment = segment_of(rehearsal)
    assert segment.startswith("rehearsal-test: A test rehearsal")
    assert "stage: 'proven'" in segment
    assert "gaps: none" in segment
    assert plain_words(rehearsal).startswith(
        "A test rehearsal - from campaign-test")

def test_red_rehearsals_stand_named_in_their_gaps():
    asking = _rehearsal(claims=["feeling", "plan_ref", "summary"])
    assert rehearsal_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert rehearsal_green(asking) is False
    skipping = _rehearsal(stages=["planned", "dealt", "proven"])
    assert rehearsal_gaps(skipping) == (
        "steps from dealt to proven, which the rehearsal sequence "
        "does not allow",)
    book = _book(rehearsals=[
        _rehearsal(),
        _rehearsal(rehearsal_id="rehearsal-skipping", seq=2,
             stages=["planned", "dealt", "proven"]),
    ])
    assert transition_breaks(book) == (
        "rehearsal-skipping: dealt > proven",)
    assert current_rehearsal(book).rehearsal_id == "rehearsal-skipping"
    assert [g.rehearsal_id for g in rehearsal_order(book)] == [
        "rehearsal-test", "rehearsal-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "rehearsal_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "rehearsal_note"
    assert record["rehearsal_id"] == "rehearsal-test"
    assert view_plain_words(view) == "View view-test: shows all rehearsals."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_rehearsals_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.stage for e in index.rehearsals] == ["proven"]
    assert index.rehearsals[0] == IndexRehearsal(
        stage="proven",
        rehearsal_id="rehearsal-test", title="A test rehearsal")
    assert index.gaps == ("rehearsal-hidden",)
    record = index_record(book)
    assert record["type"] == "rehearsal_index"
    assert record["gaps"] == ["rehearsal-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "rehearsal_book"

def test_check_target_reaches_its_rehearsal_and_an_unheld_target_reaches_nothing():
    book = load_rehearsal()
    assert rehearsal_for_check(book, "proven").rehearsal_id == (
        "rehearsal-held-rehearsal")
    assert rehearsal_for_check(book, "") is None
    assert rehearsal_for_check(book, None) is None
    assert rehearsal_for_check(book, "not held at all") is None
    text = format_stage(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_rehearsal()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Rehearsal note note rehearsal-held-rehearsal" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").rehearsal_id == "rehearsal-test"
    assert note_for_rehearsal(book, "rehearsal-test").note_id == "note-test"
    assert note_for_rehearsal(book, "rehearsal-test", "praise") is None
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
    row = build_row(None, _rehearsal(), book)
    assert row.standing == "complete"
    assert validate_row(row, _rehearsal(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_rehearsals():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "rehearsal_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "proven"
    empty_book = _book(rehearsals=[_rehearsal(stages=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(RehearsalVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_readings():
    book = load_rehearsal()
    assert [g.rehearsal_id for g in shown_rehearsals(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.rehearsal_id for g in shown_rehearsals(book, "view-proven")] == [
        "rehearsal-held-rehearsal", "rehearsal-retried-rehearsal", "rehearsal-own-rehearsal"]
    assert [g.rehearsal_id for g in rehearsals_for_campaign(
        book, "campaign-m224-dryrun")] == [
            "rehearsal-own-rehearsal", "rehearsal-bare-rehearsal",
            "rehearsal-leaping-rehearsal"]
    assert rehearsals_for_campaign(book, "campaign-nope") == ()
    assert current_rehearsal(_mixed_book()).rehearsal_id == "rehearsal-hidden"
    assert current_rehearsal(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "rehearsal-test") == (
        "planned > dealt > gated > mocked > proven")
    assert trace_current(stale, "rehearsal-test") is False
    assert ledger_record(stale)["traces"] == [
        {"rehearsal_id": "rehearsal-test", "trace": "stale"}]

def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(rehearsals=[_rehearsal(), _rehearsal(seq=2)])
    with pytest.raises(ValueError):
        _book(rehearsals=[_rehearsal(), _rehearsal(rehearsal_id="rehearsal-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(rehearsals=[_rehearsal(campaign_id="campaign-nope")])
    with pytest.raises(ValueError):
        _book(campaigns=[_ref(), _ref(
            campaign_id="campaign-cold", seq=2, state="dormant")],
            rehearsals=[_rehearsal(campaign_id="campaign-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(campaign_id="campaign-nope")])
    fields = {
        "schema": REHEARSAL_SCHEMA, "campaign": "M-224",
        "dry_run_campaigns": {"title": "A gated book"},
        "campaigns": [_ref().to_record()],
        "rehearsal_records": [_rehearsal().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "proven"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_rehearsal"] = "rehearsal-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_rehearsal")
    fields["trace"] = "rehearsal-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / REHEARSAL_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "dry_run_campaigns.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_rehearsal_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.rehearsal_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = RehearsalRegistry()
    assert registry.title() is None
    registry.register_campaign_ref(_ref())
    registry.register_rehearsal(_rehearsal())
    registry.register_view(_view())
    assert [g.rehearsal_id for g in registry.list_rehearsals()] == ["rehearsal-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_rehearsal("rehearsal-test").title == "A test rehearsal"
    assert registry.get_slice("campaign-test").state == "live"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("rehearsal-test").rehearsal_id == "rehearsal-test"
    with pytest.raises(ValueError):
        registry.register_rehearsal(_rehearsal(seq=9))
    with pytest.raises(ValueError):
        registry.register_rehearsal(_rehearsal(rehearsal_id="rehearsal-two"))
    with pytest.raises(KeyError):
        registry.get_rehearsal("rehearsal-nope")
    assert registry.book().title == "An unheld rehearsal book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = RehearsalRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test rehearsal book"
    assert registry.title() == "A test rehearsal book"
    assert len(registry.list_rehearsals()) == 2
    other = RehearsalRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    rehearsal = _rehearsal()
    assert "A test rehearsal" in plain_words(rehearsal)
    assert panel_plain_words(_mixed_book()).startswith(
        "The rehearsal book holds 2 rehearsals")
    assert verdict_plain_words(_mixed_book()) == (
        "The rehearsals stand held: 1 of 2 shown rehearsals stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green rehearsals; red, "
        "named in its gaps: rehearsal-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_rehearsal(rehearsal)
    assert "Rehearsal: A test rehearsal" in text
    assert "stands complete" in text
    text = format_rehearsal(_rehearsal(stages=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The Rehearsal Gate (M-224) - A test rehearsal book" in book_text
    assert "rehearsal-hidden" in format_book(_mixed_book(), "campaign-test")
    assert "Rehearsal panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "proven - A test rehearsal (rehearsal-test)" in index_text
    assert "rehearsal-hidden" in index_text
    screen = format_rehearsal_screen()
    assert "The Rehearsal Gate (M-224)" in screen
    assert "rehearsal-bare-rehearsal" in screen

def test_parse_args_well_and_loader_targets():
    assert parse_rehearsal_args("") == ("show", None)
    assert parse_rehearsal_args(None) == ("show", None)
    assert parse_rehearsal_args("show") == ("show", None)
    assert parse_rehearsal_args("rehearsal rehearsal-test") == (
        "rehearsal", "rehearsal-test")
    assert parse_rehearsal_args("stage proven") == (
        "stage", "proven")
    assert parse_rehearsal_args("campaign campaign-test") == (
        "campaign", "campaign-test")
    assert parse_rehearsal_args("view view-test") == ("view", "view-test")
    assert parse_rehearsal_args("note note-test") == ("note", "note-test")
    assert parse_rehearsal_args("index") == ("index", None)
    assert parse_rehearsal_args("panel") == ("panel", None)
    assert parse_rehearsal_args("verdict") == ("verdict", None)
    for bad in ("dance", "rehearsal", "stage", "campaign", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_rehearsal_args(bad)
    ledger = ledger_record()
    assert ledger["type"] == "rehearsal_well"
    assert ledger["total"] == 5
    assert ledger["current_rehearsal"] == "rehearsal-bare-rehearsal"
    book = load_rehearsal({
        "schema": REHEARSAL_SCHEMA, "campaign": "M-224",
        "dry_run_campaigns": {"title": "A gated book"},
        "campaigns": [_ref().to_record()],
        "rehearsal_records": [_rehearsal().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, RehearsalBook)
    assert book.title == "A gated book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_rehearsal({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_rehearsal({"campaign": "M-999"})
    built = build_rehearsal(
        rehearsal_id="rehearsal-kw", seq=3, campaign_id="campaign-test",
        title="Kw Rehearsal", stages=["planned", "dealt", "gated", "mocked", "proven"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="rehearsal-test")
    assert built.rehearsal_id == "rehearsal-kw"
    assert rehearsal_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-224 agent layer: the agent holds a rehearsal
# book for the session, rehearsals and views are
# published as session news through the
# checkpoint target (ledger first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held rehearsals, the ledger is derived from
# the held rehearsals' completeness, the roadmap standing
# is mocked from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no campaign. This layer rehearsals
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session ledger news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_REHEARSAL_EVENT_TYPES = (
    "rehearsal_rehearsal", "rehearsal_run", "rehearsal_view",
    "rehearsal_panel", "rehearsal_verdict")


def _rehearsal_events(store, session_id, campaign):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == campaign]


def _write_dryrun_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / REHEARSAL_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "dry_run_campaigns.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestRehearsalAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.dryrun_status()
        assert status["rehearsal_records"] == []
        assert status["campaigns"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["dryrun_book"]["title"] == EXAMPLE_TITLE
        assert len(status["dryrun_book"]["campaigns"]) == 3
        assert len(status["dryrun_book"]["rehearsal_records"]) == 5
        assert len(status["dryrun_book"]["views"]) == 2
        assert len(status["dryrun_book"]["notes"]) == 2
        assert len(status["dryrun_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-m223-campaign"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["stage"] for e in status["index"]["rehearsals"]] == (
            EXAMPLE_STAGES)
        assert status["index"]["gaps"] == [
            "rehearsal-bare-rehearsal", "rehearsal-leaping-rehearsal"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["ledger"]["total"] == 5
        assert status["ledger"]["current_rehearsal"] == "rehearsal-bare-rehearsal"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 251
        assert status["roadmap"]["next_slice"] == "M-252"
        assert status["roadmap"]["m224_title"] == "Dry-run campaigns"
        assert "held as data alone" in status["rule"]
        assert "rehearsal-bare-rehearsal" in status["plain_words"]
        assert "The Rehearsal Gate (M-224)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._dryrun_registry()
        assert agent._dryrun_registry() is first
        assert agent._dryrun_store is first
        for name in ("dryrun_book", "dryrun_status", "dryrun_panel",
                     "dryrun_verdict", "dryrun_index", "report_dryrun"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_dryrun_registry", "dryrun_book", "dryrun_status",
            "get_dryrun_rehearsal", "get_dryrun_view", "get_dryrun_note",
            "rehearsals_for_campaign", "rehearsals_green",
            "dryrun_panel", "dryrun_verdict", "dryrun_index",
            "register_dryrun_rehearsal", "register_dryrun_view",
            "view_dryrun", "register_dryrun_book",
            "record_dryrun_book", "report_dryrun",
            "_publish_dryrun_record", "_dryrun_screen",
            "_dryrun_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.dryrun_status()
        assert agent.get_dryrun_rehearsal(
            "rehearsal-held-rehearsal").title == "The held rehearsal"
        assert agent.get_dryrun_view(
            "view-rehearsals").view_filter == "all"
        assert agent.get_dryrun_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.rehearsal_id for d in agent.rehearsals_for_campaign(
            "campaign-m224-dryrun")] == [
            "rehearsal-own-rehearsal", "rehearsal-bare-rehearsal",
            "rehearsal-leaping-rehearsal"]
        assert [d.rehearsal_id for d in agent.rehearsals_green()] == [
            "rehearsal-held-rehearsal", "rehearsal-retried-rehearsal", "rehearsal-own-rehearsal"]
        agent.dryrun_panel()
        agent.dryrun_verdict()
        agent.dryrun_index()
        agent.report_dryrun()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _REHEARSAL_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_dryrun_rehearsal("rehearsal-nope")
        with pytest.raises(KeyError):
            agent.get_dryrun_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_dryrun_note("note-nope")
        with pytest.raises(ValueError):
            agent.rehearsals_for_campaign("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_dryrun_rehearsal(_rehearsal())
        status = agent.dryrun_status()
        assert [d["rehearsal_id"] for d in status["rehearsal_records"]] == ["rehearsal-test"]
        assert status["book"]["title"] == "An unheld rehearsal book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["stage"] for e in status["index"]["rehearsals"]] == [
            "proven"]
        assert status["first_note"] is None
        assert "rehearsal-test" in status["screen"]
    def test_held_rehearsal_never_falls_back_to_the_example(
            self, agent):
        agent.register_dryrun_rehearsal(_rehearsal())
        with pytest.raises(KeyError):
            agent.get_dryrun_rehearsal("rehearsal-held-rehearsal")
        with pytest.raises(KeyError):
            agent.get_dryrun_view("view-rehearsals")
        with pytest.raises(KeyError):
            agent.get_dryrun_note("note-note-first")
        rehearsal = agent.get_dryrun_rehearsal("rehearsal-test")
        assert rehearsal.title == "A test rehearsal"
        assert agent.dryrun_book().title == (
            "An unheld rehearsal book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_dryrun_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.rehearsal_id == "rehearsal-held-rehearsal"
        status = agent.dryrun_status()
        assert status["index"]["gaps"] == [
            "rehearsal-bare-rehearsal", "rehearsal-leaping-rehearsal"]
        assert status["first_note"]["rehearsal_id"] == (
            "rehearsal-held-rehearsal")
        assert status["first_note"]["stance"] == "note"

class TestRehearsalAgentHolding:
    def test_register_rehearsal_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_dryrun_rehearsal(_rehearsal())
        assert result["rehearsal"]["rehearsal_id"] == "rehearsal-test"
        assert result["record_news"]["type"] == "rehearsal_rehearsal"
        assert "rehearsal-test" in result["screen"]
        events = _rehearsal_events(store, session_id, "rehearsal_rehearsal")
        assert len(events) == 1
        agent.close()

    def test_duplicate_rehearsal_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_dryrun_rehearsal(_rehearsal())
        with pytest.raises(ValueError):
            agent.register_dryrun_rehearsal(_rehearsal(seq=9))
        with pytest.raises(ValueError):
            agent.register_dryrun_rehearsal(_rehearsal(rehearsal_id="rehearsal-two"))
        events = _rehearsal_events(store, session_id, "rehearsal_rehearsal")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_dryrun_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_rehearsal_events(
            store, session_id, "rehearsal_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_dryrun_rehearsal(_rehearsal())
        result = agent.view_dryrun("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "rehearsal_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "proven"
        assert len(_rehearsal_events(
            store, session_id, "rehearsal_view")) == 1
        assert len(_rehearsal_events(
            store, session_id, "rehearsal_panel")) == 1
        assert len(_rehearsal_events(
            store, session_id, "rehearsal_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_dryrun_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "rehearsal_run", "rehearsal_rehearsal", "rehearsal_view"]
        assert len(_rehearsal_events(
            store, session_id, "rehearsal_rehearsal")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_dryrun_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "rehearsal_panel"
        assert result["index_record"]["gaps"] == [
            "rehearsal-bare-rehearsal", "rehearsal-leaping-rehearsal"]
        with pytest.raises(ValueError):
            agent.record_dryrun_book()
        assert len(_rehearsal_events(
            store, session_id, "rehearsal_run")) == 3
        assert len(_rehearsal_events(
            store, session_id, "rehearsal_rehearsal")) == 5
        assert len(_rehearsal_events(
            store, session_id, "rehearsal_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_dryrun_book_file(tmp_path)
        book = load_rehearsal_file(path)
        result = agent.record_dryrun_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_runrt_renders_example_then_held_book_only(self, agent):
        rehearsal = agent.report_dryrun()
        assert rehearsal["book"]["title"] == EXAMPLE_TITLE
        assert rehearsal["verdict"]["verdict"] == "held"
        assert rehearsal["index"]["gaps"] == [
            "rehearsal-bare-rehearsal", "rehearsal-leaping-rehearsal"]
        assert "rehearsal-held-rehearsal" in rehearsal["book_text"]
        assert "proven - The held rehearsal (rehearsal-held-rehearsal)" in rehearsal["index_text"]
        agent.register_dryrun_rehearsal(_rehearsal())
        rehearsal = agent.report_dryrun()
        assert rehearsal["book"]["title"] == "An unheld rehearsal book"
        assert rehearsal["panel"] is None
        assert rehearsal["verdict"] is None

class TestRehearsalTerminalHeading:
    def test_show_rehearsal_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/dryrun")
        assert "The Rehearsal Gate (M-224)" in text
        _, _, text = _slash(agent, "/dryrun rehearsal rehearsal-held-rehearsal")
        assert "Rehearsal: The held rehearsal" in text
        _, _, text = _slash(
            agent, "/dryrun stage proven")
        assert "Rehearsal: The held rehearsal" in text
        _, _, text = _slash(agent, "/dryrun stage triple rehearsal")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/dryrun campaign campaign-m224-dryrun")
        assert "rehearsal-bare-rehearsal" in text
        assert "rehearsal-held-rehearsal" not in text
        _, _, text = _slash(agent, "/dryrun view view-rehearsals")
        assert "filter all" in text
        _, _, text = _slash(agent, "/dryrun note note-note-first")
        assert "Rehearsal note note rehearsal-held-rehearsal" in text
        _, _, text = _slash(agent, "/dryrun index")
        assert "Rehearsal index" in text
        assert "rehearsal-bare-rehearsal" in text
        _, _, text = _slash(agent, "/dryrun panel")
        assert "Rehearsal panel under view view-rehearsals" in text
        _, _, text = _slash(agent, "/dryrun verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/dryrun [show|rehearsal <rehearsal-id>"
                "|stage <stage>|campaign <campaign-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/dryrun dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/dryrun rehearsal rehearsal-nope")
        assert "no rehearsal named" in text
@pytest.fixture()
def rehearsal_handler(agent, monkeypatch):
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


def _rehearsal_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestRehearsalCommand:
    def test_show_is_default(self, rehearsal_handler, agent):
        rehearsal_handler._handle_dryrun("")
        assert "The Rehearsal Gate (M-224)" in (
            _rehearsal_published_text(rehearsal_handler))

    def test_rehearsal_check_slice_view_note_index_panel_verdict(
            self, rehearsal_handler, agent):
        rehearsal_handler._handle_dryrun("rehearsal rehearsal-held-rehearsal")
        assert "Rehearsal: The held rehearsal" in _rehearsal_published_text(
            rehearsal_handler)
        rehearsal_handler._handle_dryrun(
            "stage proven")
        assert "Rehearsal: The held rehearsal" in _rehearsal_published_text(
            rehearsal_handler)
        rehearsal_handler._handle_dryrun("campaign campaign-m224-dryrun")
        assert "rehearsal-bare-rehearsal" in _rehearsal_published_text(
            rehearsal_handler)
        rehearsal_handler._handle_dryrun("view view-rehearsals")
        assert "filter all" in _rehearsal_published_text(rehearsal_handler)
        rehearsal_handler._handle_dryrun("note note-note-first")
        assert "Rehearsal note note rehearsal-held-rehearsal" in (
            _rehearsal_published_text(rehearsal_handler))
        rehearsal_handler._handle_dryrun("index")
        assert "Rehearsal index" in _rehearsal_published_text(rehearsal_handler)
        rehearsal_handler._handle_dryrun("panel")
        assert "Rehearsal panel under view" in _rehearsal_published_text(
            rehearsal_handler)
        rehearsal_handler._handle_dryrun("verdict")
        assert "held" in _rehearsal_published_text(rehearsal_handler)
    def test_bad_grammar_is_published(
            self, rehearsal_handler, agent):
        rehearsal_handler._handle_dryrun("dance party")
        assert USAGE in _rehearsal_published_text(rehearsal_handler)
        rehearsal_handler._handle_dryrun("rehearsal rehearsal-nope")
        assert "no rehearsal named" in _rehearsal_published_text(
            rehearsal_handler)


class TestChatScreenRoutingRehearsal:
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
        screen.handle_command("/dryrun panel", _FakeLog())
        assert calls == [("/dryrun", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/dryrun[/green] - show the Rehearsal gate (M-224)" in (
            text)
        assert ('"/dryrun": "Usage: /dryrun | '
                '/dryrun rehearsal <rehearsal-id>') in text

class TestRehearsalDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.dryrun_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-rehearsals"
        verdict = agent.dryrun_verdict()
        assert verdict.verdict == "held"
        found = agent.dryrun_verdict("view-proven")
        assert found.verdict == "proven"
        assert found.green_shown == 3
        agent.register_dryrun_rehearsal(_rehearsal())
        with pytest.raises(ValueError):
            agent.dryrun_panel()
        with pytest.raises(ValueError):
            agent.dryrun_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_dryrun_rehearsal(_rehearsal(stages=[]))
        result = agent.view_dryrun("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.dryrun_index()
        assert [e["stage"] for e in result["index"]["rehearsals"]] == (
            EXAMPLE_STAGES)
        assert result["index"]["gaps"] == [
            "rehearsal-bare-rehearsal", "rehearsal-leaping-rehearsal"]
        assert "proven - The held rehearsal (rehearsal-held-rehearsal)" in (
            result["index_text"])
        rehearsal = agent.get_dryrun_rehearsal("rehearsal-leaping-rehearsal")
        assert rehearsal_gaps(rehearsal, agent.dryrun_book()) == (
            "steps from dealt to proven, which the rehearsal sequence "
            "does not allow",)
        assert rehearsal_green(rehearsal, agent.dryrun_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _REHEARSAL_EVENT_TYPES] == []
        agent.close()
