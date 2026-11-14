"""M-231 Cross-app method - pure-layer tests.

TIER: integration

The pure layer is the tracker, held as data: one
record per external, held whole - the campaign it
answers for, named by campaign id, its title, the
steps it walked in walk external and the evidence
it carries, held by campaign. The question walk is
explicit - named, linked, verified, tracked,
held, with their legal steps held as data -
and a external's standing is derived at call
time: a external that opens anywhere but named, steps where the sequence does not allow,
carries a bare claim in place of held evidence,
or has not yet named held stands open,
named in its gaps. A external stands only for
an active campaign: a external naming no held
campaign, or one that is not active, refuses by
name. The external's trace - its walked steps
as one line - is derived at call time, and a held
trace record stands current only while it agrees
with the derived trace. The index, panel,
verdict, ledger, trace, external and current
external are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
question was actually answered, tracked or
held live. The shipped example book is held
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

from mythic_agent.core.cross_app_method import (
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
    EXTERNAL_RESOURCE,
    EXTERNAL_RULE,
    EXTERNAL_SCHEMA,
    EXTERNAL_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    ExternalRecord,
    IndexExternal,
    CampaignRef,
    NoteRecord,
    ExternalBook,
    ExternalIndex,
    ExternalPanel,
    ExternalRegistry,
    ExternalVerdict,
    ExternalView,
    trace_for_external,
    ledger_record,
    book_record,
    build_trace,
    build_book,
    build_external,
    build_campaign_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_external,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    external_for_check,
    external_gaps,
    external_external,
    external_record,
    external_green,
    externals_for_campaign,
    first_note,
    format_book,
    format_external,
    format_index,
    format_note,
    format_stage,
    format_panel,
    format_external_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    campaign_record,
    load_external,
    legal_step,
    load_external_file,
    next_stage,
    normalize_stage,
    normalize_claim_kind,
    normalize_campaign_state,
    normalize_stance,
    normalize_view_filter,
    note_for_external,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_external_args,
    green_externals,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_externals,
    validate_book,
    validate_external,
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
EXAMPLE_TITLE = "Cross-app method at the M-231 slice run"
EXAMPLE_STAGES = ["held", "held", "held"]
EXAMPLE_RUN_IDS = (
    "external-held-external", "external-retried-external",
    "external-own-external", "external-bare-external",
    "external-leaping-external")
EXAMPLE_TRACE = "named > linked > verified > tracked > held"


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
        "origin_session": "external-test",
    }
    fields.update(overrides)
    return build_campaign_ref(fields)


def _external(**overrides):
    fields = {
        "external_id": "external-test",
        "seq": 1,
        "campaign_id": "campaign-test",
        "title": "A test external",
        "stages": ["named", "linked", "verified", "tracked", "held"],
        "claims": [],
        "detail": "A test external held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "external-test",
    }
    fields.update(overrides)
    return build_external(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "external-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "external_id": "external-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "external-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "external_id": "external-test",
        "trace": "named > linked > verified > tracked > held",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "external-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(campaigns=None, externals=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": EXTERNAL_SCHEMA,
        "campaign": "M-231",
        "cross_app_method": {"title": "A test external book"},
        "campaigns": [item.to_record() for item in (
            campaigns if campaigns is not None else [_ref()])],
        "external_records": [item.to_record() for item in (
            externals if externals is not None else [_external()])],
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
    return _book(externals=[
        _external(),
        _external(external_id="external-hidden", seq=2,
               title="A hidden external", stages=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_external()
    assert book.title == EXAMPLE_TITLE
    assert book.external_ids() == EXAMPLE_RUN_IDS
    assert book.campaign_ids() == (
        "campaign-m230-metrics", "campaign-m231-crossapp",
        "campaign-m232-gate")
    assert [v.view_id for v in book.views] == [
        "view-externals", "view-held"]
    assert [m.external_id for m in book.notes] == [
        "external-held-external", "external-bare-external"]
    assert [a.external_id for a in book.traces] == ["external-held-external"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m230-campaign"
    assert panel.as_of == "2026-11-11"
    assert [row.item_id for row in panel.rows] == list(book.external_ids())
    derived = derive_panel(book, "view-externals")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-externals").verdict == "held"
    assert derive_verdict(book, "view-externals").green_shown == 3
    assert derive_verdict(book, "view-held").verdict == "held"
    assert derive_verdict(book, "view-held").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / EXTERNAL_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == EXTERNAL_SCHEMA
    assert raw["campaign"] == "M-231"
    assert "verdict" not in raw
    assert "external_index" not in raw
    assert "ledger" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-231")]
    assert slice_.title == "Cross-app method"
    assert slice_.part == 9
    assert "campaigns can name slices that live in other tools (a Samtal slice, a Sagnaskemma slice) as" in slice_.summary
    assert "the forge sees Volmarr's whole workshop" in slice_.summary
    assert EXTERNAL_SLICE == "M-231"

def test_charter_rows_do_not_name_m231():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-231" not in owners
    method = load_method_charter()
    assert "M-201" in method.source_note
    assert "M-232" in method.source_note
    assert "YRSA_CODING_JUGGERNAUT" in method.source_note

def test_closed_vocabularies():
    assert COMPLETE_WORDS == ("complete", "open")
    assert STAGE_FIELDS == ("stages", "claims")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "complete", "open")
    assert VERDICT_WORDS == ("held", "held", "blocked")
    assert CAMPAIGN_STATES == ("live", "dormant")
    assert STAGES == ("named", "linked", "verified", "tracked", "held")
    assert HELD_EVIDENCE == ("tool_ref", "slice_ref", "link_ref", "status_ref", "external_ref")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_KINDS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["tracked"] == ("named", "held")
    assert TRANSITIONS["held"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_STAGE == "held"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_campaign_state("LIVE") == "live"
    assert normalize_stage("VERIFIED") == "verified"
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
    assert legal_step("verified", "tracked") is True
    assert legal_step("linked", "held") is False
    assert legal_step("held", "named") is False
    assert next_stage("named") == "linked"
    assert next_stage("verified") == "tracked"
    assert next_stage("tracked", failed=True) == "named"
    assert next_stage("tracked") == "held"
    assert next_stage("held") is None
    assert "held as data alone" in EXTERNAL_RULE
    assert "external sequence" in EXTERNAL_RULE
    assert "M-231" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /crossapp")

def test_shipped_book_judged_honestly_as_data():
    book = load_external()
    opening = book.external_for("external-held-external")
    assert external_green(opening, book) is True
    assert external_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "External: The held external",
        "Campaign: campaign-m230-metrics",
        "Stage: held",
        "Claims: tool_ref")
    asking = book.external_for("external-bare-external")
    assert external_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert external_green(asking, book) is False
    skipping = book.external_for("external-leaping-external")
    assert external_gaps(skipping, book) == (
        "steps from linked to held, which the external sequence "
        "does not allow",)
    assert [g.external_id for g in green_externals(book)] == [
        "external-held-external", "external-retried-external", "external-own-external"]
    index = derive_index(book)
    assert [e.stage for e in index.externals] == EXAMPLE_STAGES
    assert index.gaps == ("external-bare-external", "external-leaping-external")
    assert external_for_check(book, EXAMPLE_STAGE).external_id == (
        "external-held-external")
    assert external_for_check(book, "triple external") is None
    assert transition_breaks(book) == (
        "external-leaping-external: linked > held",)
    assert [g.external_id for g in external_external(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "external-held-external") == EXAMPLE_TRACE
    assert trace_current(book, "external-held-external") is True
    assert trace_current(book, "external-retried-external") is False
    assert trace_for_external(
        book, "external-held-external").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_external(
        book, "external-held-external", "note").note_id == (
            "note-note-first")
    assert note_for_external(book, "external-nope") is None
    assert current_external(book).external_id == "external-bare-external"
    ledger = ledger_record(book)
    assert ledger["standings"] == [
        {"standing": "complete", "external_records": 3},
        {"standing": "open", "external_records": 2}]
    assert ledger["total"] == 5
    assert ledger["current_external"] == "external-bare-external"
    assert ledger["traces"] == [
        {"external_id": "external-held-external", "trace": "current"},
        {"external_id": "external-retried-external", "trace": "unheld"},
        {"external_id": "external-own-external", "trace": "unheld"},
        {"external_id": "external-bare-external", "trace": "unheld"},
        {"external_id": "external-leaping-external", "trace": "unheld"}]
    assert ledger["breaks"] == ["external-leaping-external: linked > held"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 270
    assert citizen["next_slice"] == "M-271"
    assert citizen["m231_title"] == "Cross-app method"
    assert citizen["m231_part"] == 9
    assert citizen["m231_status"] == "done"

def test_external_record_round_trips():
    external = _external()
    assert validate_external(external) is external
    rebuilt = build_external(external.to_record())
    assert rebuilt == external
    assert rebuilt.item_id == "external-test"
    assert rebuilt.stage == "held"
    record = external_record(external)
    assert record["type"] == "external_external"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert campaign_record(ref)["type"] == "external_run"
    assert campaign_record(ref)["state"] == "live"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _external(stages=[])
    assert external_gaps(silent) == (
        "has passed through no step: the external has not started",)
    assert external_green(silent) is False
    walking = _external(stages=["named", "linked"])
    assert external_gaps(walking) == (
        "has not reached held: the external stands at linked",)
    assert walking.stage == "linked"
    sideways = _external(stages=["linked", "verified", "tracked", "held"])
    assert external_gaps(sideways) == (
        "opens at linked, not at named: the external opens "
        "with the reflection",)
    repaired = _external(stages=["named", "linked", "verified", "tracked", "named", "linked", "verified", "tracked", "held"])
    assert external_gaps(repaired) == ()
    assert external_green(repaired) is True
    with pytest.raises(ValueError):
        _external(stages=[42])
    with pytest.raises(ValueError):
        _external(stages="inspect as a bare string")
    with pytest.raises(ValueError):
        _external(stages=["named", "polish"])
    with pytest.raises(ValueError):
        _external(claims=["weather"])
    with pytest.raises(ValueError):
        _external(claims="tool_ref")
    none_external = _external(stages=None, claims=None)
    assert none_external.stages == ()
    assert none_external.claims == ()

def test_external_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "externals", "coverage", "current_external",
                "ledger", "external"):
        fields = _external().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_external(fields)
    fields = _external().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_external(fields)


def test_external_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _external().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_external(fields)


def test_external_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _external(title="")
    with pytest.raises(ValueError):
        _external(campaign_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "named > linked > verified > tracked > held"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_externals_own_fields():
    external = _external(claims=["tool_ref"])
    assert plain_lines(external) == (
        "External: A test external",
        "Campaign: campaign-test",
        "Stage: held",
        "Claims: tool_ref")
    segment = segment_of(external)
    assert segment.startswith("external-test: A test external")
    assert "stage: 'held'" in segment
    assert "gaps: none" in segment
    assert plain_words(external).startswith(
        "A test external - from campaign-test")

def test_red_externals_stand_named_in_their_gaps():
    asking = _external(claims=["feeling", "tool_ref", "summary"])
    assert external_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert external_green(asking) is False
    skipping = _external(stages=["named", "linked", "held"])
    assert external_gaps(skipping) == (
        "steps from linked to held, which the external sequence "
        "does not allow",)
    book = _book(externals=[
        _external(),
        _external(external_id="external-skipping", seq=2,
             stages=["named", "linked", "held"]),
    ])
    assert transition_breaks(book) == (
        "external-skipping: linked > held",)
    assert current_external(book).external_id == "external-skipping"
    assert [g.external_id for g in external_external(book)] == [
        "external-test", "external-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "external_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "external_note"
    assert record["external_id"] == "external-test"
    assert view_plain_words(view) == "View view-test: shows all externals."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_externals_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.stage for e in index.externals] == ["held"]
    assert index.externals[0] == IndexExternal(
        stage="held",
        external_id="external-test", title="A test external")
    assert index.gaps == ("external-hidden",)
    record = index_record(book)
    assert record["type"] == "external_index"
    assert record["gaps"] == ["external-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "external_book"

def test_check_target_reaches_its_external_and_an_unheld_target_reaches_nothing():
    book = load_external()
    assert external_for_check(book, "held").external_id == (
        "external-held-external")
    assert external_for_check(book, "") is None
    assert external_for_check(book, None) is None
    assert external_for_check(book, "not held at all") is None
    text = format_stage(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_external()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "External note note external-held-external" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").external_id == "external-test"
    assert note_for_external(book, "external-test").note_id == "note-test"
    assert note_for_external(book, "external-test", "praise") is None
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
    row = build_row(None, _external(), book)
    assert row.standing == "complete"
    assert validate_row(row, _external(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_externals():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "external_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "held"
    empty_book = _book(externals=[_external(stages=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(ExternalVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_externals():
    book = load_external()
    assert [g.external_id for g in shown_externals(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.external_id for g in shown_externals(book, "view-held")] == [
        "external-held-external", "external-retried-external", "external-own-external"]
    assert [g.external_id for g in externals_for_campaign(
        book, "campaign-m231-crossapp")] == [
            "external-own-external", "external-bare-external",
            "external-leaping-external"]
    assert externals_for_campaign(book, "campaign-nope") == ()
    assert current_external(_mixed_book()).external_id == "external-hidden"
    assert current_external(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "external-test") == (
        "named > linked > verified > tracked > held")
    assert trace_current(stale, "external-test") is False
    assert ledger_record(stale)["traces"] == [
        {"external_id": "external-test", "trace": "stale"}]

def test_slice_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(externals=[_external(), _external(seq=2)])
    with pytest.raises(ValueError):
        _book(externals=[_external(), _external(external_id="external-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(externals=[_external(campaign_id="campaign-nope")])
    with pytest.raises(ValueError):
        _book(campaigns=[_ref(), _ref(
            campaign_id="campaign-cold", seq=2, state="dormant")],
            externals=[_external(campaign_id="campaign-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(campaign_id="campaign-nope")])
    fields = {
        "schema": EXTERNAL_SCHEMA, "campaign": "M-231",
        "cross_app_method": {"title": "A verified book"},
        "campaigns": [_ref().to_record()],
        "external_records": [_external().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "held"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_external"] = "external-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_external")
    fields["trace"] = "external-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / EXTERNAL_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "cross_app_method.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_external_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.external_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = ExternalRegistry()
    assert registry.title() is None
    registry.register_campaign_ref(_ref())
    registry.register_external(_external())
    registry.register_view(_view())
    assert [g.external_id for g in registry.list_externals()] == ["external-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_external("external-test").title == "A test external"
    assert registry.get_slice("campaign-test").state == "live"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("external-test").external_id == "external-test"
    with pytest.raises(ValueError):
        registry.register_external(_external(seq=9))
    with pytest.raises(ValueError):
        registry.register_external(_external(external_id="external-two"))
    with pytest.raises(KeyError):
        registry.get_external("external-nope")
    assert registry.book().title == "An unheld external book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = ExternalRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test external book"
    assert registry.title() == "A test external book"
    assert len(registry.list_externals()) == 2
    other = ExternalRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    external = _external()
    assert "A test external" in plain_words(external)
    assert panel_plain_words(_mixed_book()).startswith(
        "The external book holds 2 externals")
    assert verdict_plain_words(_mixed_book()) == (
        "The externals stand held: 1 of 2 shown externals stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green externals; red, "
        "named in its gaps: external-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_external(external)
    assert "External: A test external" in text
    assert "stands complete" in text
    text = format_external(_external(stages=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The External Gate (M-231) - A test external book" in book_text
    assert "external-hidden" in format_book(_mixed_book(), "campaign-test")
    assert "External panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "held - A test external (external-test)" in index_text
    assert "external-hidden" in index_text
    screen = format_external_screen()
    assert "The External Gate (M-231)" in screen
    assert "external-bare-external" in screen

def test_parse_args_well_and_loader_targets():
    assert parse_external_args("") == ("show", None)
    assert parse_external_args(None) == ("show", None)
    assert parse_external_args("show") == ("show", None)
    assert parse_external_args("external external-test") == (
        "external", "external-test")
    assert parse_external_args("stage held") == (
        "stage", "held")
    assert parse_external_args("campaign campaign-test") == (
        "campaign", "campaign-test")
    assert parse_external_args("view view-test") == ("view", "view-test")
    assert parse_external_args("note note-test") == ("note", "note-test")
    assert parse_external_args("index") == ("index", None)
    assert parse_external_args("panel") == ("panel", None)
    assert parse_external_args("verdict") == ("verdict", None)
    for bad in ("dance", "external", "stage", "campaign", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_external_args(bad)
    ledger = ledger_record()
    assert ledger["type"] == "external_well"
    assert ledger["total"] == 5
    assert ledger["current_external"] == "external-bare-external"
    book = load_external({
        "schema": EXTERNAL_SCHEMA, "campaign": "M-231",
        "cross_app_method": {"title": "A verified book"},
        "campaigns": [_ref().to_record()],
        "external_records": [_external().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, ExternalBook)
    assert book.title == "A verified book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_external({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_external({"campaign": "M-999"})
    built = build_external(
        external_id="external-kw", seq=3, campaign_id="campaign-test",
        title="Kw External", stages=["named", "linked", "verified", "tracked", "held"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="external-test")
    assert built.external_id == "external-kw"
    assert external_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-231 agent layer: the agent holds a external
# book for the session, externals and views are
# published as session news through the
# checkpoint target (ledger first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held externals, the ledger is derived from
# the held externals' completeness, the roadmap standing
# is tracked from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no campaign. This layer externals
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session ledger news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_EXTERNAL_EVENT_TYPES = (
    "external_external", "external_run", "external_view",
    "external_panel", "external_verdict")


def _external_events(store, session_id, campaign):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == campaign]


def _write_crossapp_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / EXTERNAL_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "cross_app_method.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestExternalAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.crossapp_status()
        assert status["external_records"] == []
        assert status["campaigns"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["crossapp_book"]["title"] == EXAMPLE_TITLE
        assert len(status["crossapp_book"]["campaigns"]) == 3
        assert len(status["crossapp_book"]["external_records"]) == 5
        assert len(status["crossapp_book"]["views"]) == 2
        assert len(status["crossapp_book"]["notes"]) == 2
        assert len(status["crossapp_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-m230-campaign"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["stage"] for e in status["index"]["externals"]] == (
            EXAMPLE_STAGES)
        assert status["index"]["gaps"] == [
            "external-bare-external", "external-leaping-external"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["ledger"]["total"] == 5
        assert status["ledger"]["current_external"] == "external-bare-external"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 270
        assert status["roadmap"]["next_slice"] == "M-271"
        assert status["roadmap"]["m231_title"] == "Cross-app method"
        assert "held as data alone" in status["rule"]
        assert "external-bare-external" in status["plain_words"]
        assert "The External Gate (M-231)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._crossapp_registry()
        assert agent._crossapp_registry() is first
        assert agent._crossapp_store is first
        for name in ("crossapp_book", "crossapp_status", "crossapp_panel",
                     "crossapp_verdict", "crossapp_index", "report_crossapp"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_crossapp_registry", "crossapp_book", "crossapp_status",
            "get_crossapp_external", "get_crossapp_view", "get_crossapp_note",
            "externals_for_campaign", "crossapp_green",
            "crossapp_panel", "crossapp_verdict", "crossapp_index",
            "register_crossapp_external", "register_crossapp_view",
            "view_crossapp", "register_crossapp_book",
            "record_crossapp_book", "report_crossapp",
            "_publish_crossapp_record", "_crossapp_screen",
            "_crossapp_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.crossapp_status()
        assert agent.get_crossapp_external(
            "external-held-external").title == "The held external"
        assert agent.get_crossapp_view(
            "view-externals").view_filter == "all"
        assert agent.get_crossapp_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.external_id for d in agent.externals_for_campaign(
            "campaign-m231-crossapp")] == [
            "external-own-external", "external-bare-external",
            "external-leaping-external"]
        assert [d.external_id for d in agent.crossapp_green()] == [
            "external-held-external", "external-retried-external", "external-own-external"]
        agent.crossapp_panel()
        agent.crossapp_verdict()
        agent.crossapp_index()
        agent.report_crossapp()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _EXTERNAL_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_crossapp_external("external-nope")
        with pytest.raises(KeyError):
            agent.get_crossapp_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_crossapp_note("note-nope")
        with pytest.raises(ValueError):
            agent.externals_for_campaign("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_crossapp_external(_external())
        status = agent.crossapp_status()
        assert [d["external_id"] for d in status["external_records"]] == ["external-test"]
        assert status["book"]["title"] == "An unheld external book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["stage"] for e in status["index"]["externals"]] == [
            "held"]
        assert status["first_note"] is None
        assert "external-test" in status["screen"]
    def test_held_external_never_falls_back_to_the_example(
            self, agent):
        agent.register_crossapp_external(_external())
        with pytest.raises(KeyError):
            agent.get_crossapp_external("external-held-external")
        with pytest.raises(KeyError):
            agent.get_crossapp_view("view-externals")
        with pytest.raises(KeyError):
            agent.get_crossapp_note("note-note-first")
        external = agent.get_crossapp_external("external-test")
        assert external.title == "A test external"
        assert agent.crossapp_book().title == (
            "An unheld external book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_crossapp_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.external_id == "external-held-external"
        status = agent.crossapp_status()
        assert status["index"]["gaps"] == [
            "external-bare-external", "external-leaping-external"]
        assert status["first_note"]["external_id"] == (
            "external-held-external")
        assert status["first_note"]["stance"] == "note"

class TestExternalAgentHolding:
    def test_register_external_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_crossapp_external(_external())
        assert result["external"]["external_id"] == "external-test"
        assert result["record_news"]["type"] == "external_external"
        assert "external-test" in result["screen"]
        events = _external_events(store, session_id, "external_external")
        assert len(events) == 1
        agent.close()

    def test_duplicate_external_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_crossapp_external(_external())
        with pytest.raises(ValueError):
            agent.register_crossapp_external(_external(seq=9))
        with pytest.raises(ValueError):
            agent.register_crossapp_external(_external(external_id="external-two"))
        events = _external_events(store, session_id, "external_external")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_crossapp_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_external_events(
            store, session_id, "external_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_crossapp_external(_external())
        result = agent.view_crossapp("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "external_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "held"
        assert len(_external_events(
            store, session_id, "external_view")) == 1
        assert len(_external_events(
            store, session_id, "external_panel")) == 1
        assert len(_external_events(
            store, session_id, "external_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_external(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_crossapp_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "external_run", "external_external", "external_view"]
        assert len(_external_events(
            store, session_id, "external_external")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_crossapp_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "external_panel"
        assert result["index_record"]["gaps"] == [
            "external-bare-external", "external-leaping-external"]
        with pytest.raises(ValueError):
            agent.record_crossapp_book()
        assert len(_external_events(
            store, session_id, "external_run")) == 3
        assert len(_external_events(
            store, session_id, "external_external")) == 5
        assert len(_external_events(
            store, session_id, "external_view")) == 2
        agent.close()

    def test_book_from_a_file_is_linked_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_crossapp_book_file(tmp_path)
        book = load_external_file(path)
        result = agent.record_crossapp_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_runrt_renders_example_then_held_book_only(self, agent):
        external = agent.report_crossapp()
        assert external["book"]["title"] == EXAMPLE_TITLE
        assert external["verdict"]["verdict"] == "held"
        assert external["index"]["gaps"] == [
            "external-bare-external", "external-leaping-external"]
        assert "external-held-external" in external["book_text"]
        assert "held - The held external (external-held-external)" in external["index_text"]
        agent.register_crossapp_external(_external())
        external = agent.report_crossapp()
        assert external["book"]["title"] == "An unheld external book"
        assert external["panel"] is None
        assert external["verdict"] is None

class TestExternalTerminalHeading:
    def test_show_external_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/crossapp")
        assert "The External Gate (M-231)" in text
        _, _, text = _slash(agent, "/crossapp external external-held-external")
        assert "External: The held external" in text
        _, _, text = _slash(
            agent, "/crossapp stage held")
        assert "External: The held external" in text
        _, _, text = _slash(agent, "/crossapp stage triple external")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/crossapp campaign campaign-m231-crossapp")
        assert "external-bare-external" in text
        assert "external-held-external" not in text
        _, _, text = _slash(agent, "/crossapp view view-externals")
        assert "filter all" in text
        _, _, text = _slash(agent, "/crossapp note note-note-first")
        assert "External note note external-held-external" in text
        _, _, text = _slash(agent, "/crossapp index")
        assert "External index" in text
        assert "external-bare-external" in text
        _, _, text = _slash(agent, "/crossapp panel")
        assert "External panel under view view-externals" in text
        _, _, text = _slash(agent, "/crossapp verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/crossapp [show|external <external-id>"
                "|stage <stage>|campaign <campaign-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/crossapp dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/crossapp external external-nope")
        assert "no external named" in text
@pytest.fixture()
def external_handler(agent, monkeypatch):
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


def _external_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestExternalCommand:
    def test_show_is_default(self, external_handler, agent):
        external_handler._handle_crossapp("")
        assert "The External Gate (M-231)" in (
            _external_published_text(external_handler))

    def test_external_check_slice_view_note_index_panel_verdict(
            self, external_handler, agent):
        external_handler._handle_crossapp("external external-held-external")
        assert "External: The held external" in _external_published_text(
            external_handler)
        external_handler._handle_crossapp(
            "stage held")
        assert "External: The held external" in _external_published_text(
            external_handler)
        external_handler._handle_crossapp("campaign campaign-m231-crossapp")
        assert "external-bare-external" in _external_published_text(
            external_handler)
        external_handler._handle_crossapp("view view-externals")
        assert "filter all" in _external_published_text(external_handler)
        external_handler._handle_crossapp("note note-note-first")
        assert "External note note external-held-external" in (
            _external_published_text(external_handler))
        external_handler._handle_crossapp("index")
        assert "External index" in _external_published_text(external_handler)
        external_handler._handle_crossapp("panel")
        assert "External panel under view" in _external_published_text(
            external_handler)
        external_handler._handle_crossapp("verdict")
        assert "held" in _external_published_text(external_handler)
    def test_bad_grammar_is_published(
            self, external_handler, agent):
        external_handler._handle_crossapp("dance party")
        assert USAGE in _external_published_text(external_handler)
        external_handler._handle_crossapp("external external-nope")
        assert "no external named" in _external_published_text(
            external_handler)


class TestChatScreenRoutingExternal:
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
        screen.handle_command("/crossapp panel", _FakeLog())
        assert calls == [("/crossapp", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/crossapp[/green] - show the External gate (M-231)" in (
            text)
        assert ('"/crossapp": "Usage: /crossapp | '
                '/crossapp external <external-id>') in text

class TestExternalDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.crossapp_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-externals"
        verdict = agent.crossapp_verdict()
        assert verdict.verdict == "held"
        found = agent.crossapp_verdict("view-held")
        assert found.verdict == "held"
        assert found.green_shown == 3
        agent.register_crossapp_external(_external())
        with pytest.raises(ValueError):
            agent.crossapp_panel()
        with pytest.raises(ValueError):
            agent.crossapp_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_crossapp_external(_external(stages=[]))
        result = agent.view_crossapp("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.crossapp_index()
        assert [e["stage"] for e in result["index"]["externals"]] == (
            EXAMPLE_STAGES)
        assert result["index"]["gaps"] == [
            "external-bare-external", "external-leaping-external"]
        assert "held - The held external (external-held-external)" in (
            result["index_text"])
        external = agent.get_crossapp_external("external-leaping-external")
        assert external_gaps(external, agent.crossapp_book()) == (
            "steps from linked to held, which the external sequence "
            "does not allow",)
        assert external_green(external, agent.crossapp_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _EXTERNAL_EVENT_TYPES] == []
        agent.close()
