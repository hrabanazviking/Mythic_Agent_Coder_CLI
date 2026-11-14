"""M-230 Method metrics - pure-layer tests.

TIER: integration

The pure layer is the watcher, held as data: one
record per reading, held whole - the campaign it
answers for, named by campaign id, its title, the
steps it walked in walk reading and the evidence
it carries, held by campaign. The question walk is
explicit - named, checked, weighed, calibrated,
posted, with their legal steps held as data -
and a reading's standing is derived at call
time: a reading that opens anywhere but taken, steps where the sequence does not allow,
carries a bare claim in place of held evidence,
or has not yet taken posted stands open,
named in its gaps. A reading stands only for
an active campaign: a reading naming no held
campaign, or one that is not active, refuses by
name. The reading's trace - its walked steps
as one line - is derived at call time, and a held
trace record stands current only while it agrees
with the derived trace. The index, panel,
verdict, ledger, trace, reading and current
reading are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
question was actually answered, calibrated or
posted live. The shipped example book is held
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

from mythic_agent.core.method_metrics import (
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
    READING_RESOURCE,
    READING_RULE,
    READING_SCHEMA,
    READING_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    ReadingRecord,
    IndexReading,
    CampaignRef,
    NoteRecord,
    ReadingBook,
    ReadingIndex,
    ReadingPanel,
    ReadingRegistry,
    ReadingVerdict,
    ReadingView,
    trace_for_reading,
    ledger_record,
    book_record,
    build_trace,
    build_book,
    build_reading,
    build_campaign_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_reading,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    reading_for_check,
    reading_gaps,
    reading_reading,
    reading_record,
    reading_green,
    readings_for_campaign,
    first_note,
    format_book,
    format_reading,
    format_index,
    format_note,
    format_stage,
    format_panel,
    format_reading_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    campaign_record,
    load_reading,
    legal_step,
    load_reading_file,
    next_stage,
    normalize_stage,
    normalize_claim_kind,
    normalize_campaign_state,
    normalize_stance,
    normalize_view_filter,
    note_for_reading,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_reading_args,
    green_readings,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_readings,
    validate_book,
    validate_reading,
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
EXAMPLE_TITLE = "Method metrics at the M-230 slice run"
EXAMPLE_STAGES = ["posted", "posted", "posted"]
EXAMPLE_RUN_IDS = (
    "reading-held-reading", "reading-retried-reading",
    "reading-own-reading", "reading-bare-reading",
    "reading-leaping-reading")
EXAMPLE_TRACE = "taken > checked > weighed > calibrated > posted"


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
        "origin_session": "reading-test",
    }
    fields.update(overrides)
    return build_campaign_ref(fields)


def _reading(**overrides):
    fields = {
        "reading_id": "reading-test",
        "seq": 1,
        "campaign_id": "campaign-test",
        "title": "A test reading",
        "stages": ["taken", "checked", "weighed", "calibrated", "posted"],
        "claims": [],
        "detail": "A test reading held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "reading-test",
    }
    fields.update(overrides)
    return build_reading(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "reading-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "reading_id": "reading-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "reading-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "reading_id": "reading-test",
        "trace": "taken > checked > weighed > calibrated > posted",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "reading-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(campaigns=None, readings=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": READING_SCHEMA,
        "campaign": "M-230",
        "method_metrics": {"title": "A test reading book"},
        "campaigns": [item.to_record() for item in (
            campaigns if campaigns is not None else [_ref()])],
        "reading_records": [item.to_record() for item in (
            readings if readings is not None else [_reading()])],
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
    return _book(readings=[
        _reading(),
        _reading(reading_id="reading-hidden", seq=2,
               title="A hidden reading", stages=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_reading()
    assert book.title == EXAMPLE_TITLE
    assert book.reading_ids() == EXAMPLE_RUN_IDS
    assert book.campaign_ids() == (
        "campaign-m229-teachable", "campaign-m230-metrics",
        "campaign-m231-crossapp")
    assert [v.view_id for v in book.views] == [
        "view-readings", "view-posted"]
    assert [m.reading_id for m in book.notes] == [
        "reading-held-reading", "reading-bare-reading"]
    assert [a.reading_id for a in book.traces] == ["reading-held-reading"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m229-campaign"
    assert panel.as_of == "2026-11-11"
    assert [row.item_id for row in panel.rows] == list(book.reading_ids())
    derived = derive_panel(book, "view-readings")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-readings").verdict == "held"
    assert derive_verdict(book, "view-readings").green_shown == 3
    assert derive_verdict(book, "view-posted").verdict == "posted"
    assert derive_verdict(book, "view-posted").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / READING_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == READING_SCHEMA
    assert raw["campaign"] == "M-230"
    assert "verdict" not in raw
    assert "reading_index" not in raw
    assert "ledger" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-230")]
    assert slice_.title == "Method metrics"
    assert slice_.part == 9
    assert "slices banked, gate pass rate, repair rounds, calibration" in slice_.summary
    assert "the method's own health on the metrics board" in slice_.summary
    assert READING_SLICE == "M-230"

def test_charter_rows_do_not_name_m230():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-230" not in owners
    method = load_method_charter()
    assert "M-201" in method.source_note
    assert "M-232" in method.source_note
    assert "YRSA_CODING_JUGGERNAUT" in method.source_note

def test_closed_vocabularies():
    assert COMPLETE_WORDS == ("complete", "open")
    assert STAGE_FIELDS == ("stages", "claims")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "complete", "open")
    assert VERDICT_WORDS == ("posted", "held", "blocked")
    assert CAMPAIGN_STATES == ("live", "dormant")
    assert STAGES == ("taken", "checked", "weighed", "calibrated", "posted")
    assert HELD_EVIDENCE == ("metrics_ref", "count_ref", "gate_ref", "repair_ref", "reading_ref")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_KINDS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["calibrated"] == ("taken", "posted")
    assert TRANSITIONS["posted"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_STAGE == "posted"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_campaign_state("LIVE") == "live"
    assert normalize_stage("WEIGHED") == "weighed"
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
    assert legal_step("weighed", "calibrated") is True
    assert legal_step("checked", "posted") is False
    assert legal_step("posted", "taken") is False
    assert next_stage("taken") == "checked"
    assert next_stage("weighed") == "calibrated"
    assert next_stage("calibrated", failed=True) == "taken"
    assert next_stage("calibrated") == "posted"
    assert next_stage("posted") is None
    assert "held as data alone" in READING_RULE
    assert "reading sequence" in READING_RULE
    assert "M-230" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /metrics")

def test_shipped_book_judged_honestly_as_data():
    book = load_reading()
    opening = book.reading_for("reading-held-reading")
    assert reading_green(opening, book) is True
    assert reading_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Reading: The held reading",
        "Campaign: campaign-m229-teachable",
        "Stage: posted",
        "Claims: metrics_ref")
    asking = book.reading_for("reading-bare-reading")
    assert reading_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert reading_green(asking, book) is False
    skipping = book.reading_for("reading-leaping-reading")
    assert reading_gaps(skipping, book) == (
        "steps from checked to posted, which the reading sequence "
        "does not allow",)
    assert [g.reading_id for g in green_readings(book)] == [
        "reading-held-reading", "reading-retried-reading", "reading-own-reading"]
    index = derive_index(book)
    assert [e.stage for e in index.readings] == EXAMPLE_STAGES
    assert index.gaps == ("reading-bare-reading", "reading-leaping-reading")
    assert reading_for_check(book, EXAMPLE_STAGE).reading_id == (
        "reading-held-reading")
    assert reading_for_check(book, "triple reading") is None
    assert transition_breaks(book) == (
        "reading-leaping-reading: checked > posted",)
    assert [g.reading_id for g in reading_reading(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "reading-held-reading") == EXAMPLE_TRACE
    assert trace_current(book, "reading-held-reading") is True
    assert trace_current(book, "reading-retried-reading") is False
    assert trace_for_reading(
        book, "reading-held-reading").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_reading(
        book, "reading-held-reading", "note").note_id == (
            "note-note-first")
    assert note_for_reading(book, "reading-nope") is None
    assert current_reading(book).reading_id == "reading-bare-reading"
    ledger = ledger_record(book)
    assert ledger["standings"] == [
        {"standing": "complete", "reading_records": 3},
        {"standing": "open", "reading_records": 2}]
    assert ledger["total"] == 5
    assert ledger["current_reading"] == "reading-bare-reading"
    assert ledger["traces"] == [
        {"reading_id": "reading-held-reading", "trace": "current"},
        {"reading_id": "reading-retried-reading", "trace": "unheld"},
        {"reading_id": "reading-own-reading", "trace": "unheld"},
        {"reading_id": "reading-bare-reading", "trace": "unheld"},
        {"reading_id": "reading-leaping-reading", "trace": "unheld"}]
    assert ledger["breaks"] == ["reading-leaping-reading: checked > posted"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 271
    assert citizen["next_slice"] == "M-272"
    assert citizen["m230_title"] == "Method metrics"
    assert citizen["m230_part"] == 9
    assert citizen["m230_status"] == "done"

def test_reading_record_round_trips():
    reading = _reading()
    assert validate_reading(reading) is reading
    rebuilt = build_reading(reading.to_record())
    assert rebuilt == reading
    assert rebuilt.item_id == "reading-test"
    assert rebuilt.stage == "posted"
    record = reading_record(reading)
    assert record["type"] == "reading_reading"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert campaign_record(ref)["type"] == "reading_run"
    assert campaign_record(ref)["state"] == "live"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _reading(stages=[])
    assert reading_gaps(silent) == (
        "has passed through no step: the reading has not started",)
    assert reading_green(silent) is False
    walking = _reading(stages=["taken", "checked"])
    assert reading_gaps(walking) == (
        "has not reached posted: the reading stands at checked",)
    assert walking.stage == "checked"
    sideways = _reading(stages=["checked", "weighed", "calibrated", "posted"])
    assert reading_gaps(sideways) == (
        "opens at checked, not at taken: the reading opens "
        "with the reflection",)
    repaired = _reading(stages=["taken", "checked", "weighed", "calibrated", "taken", "checked", "weighed", "calibrated", "posted"])
    assert reading_gaps(repaired) == ()
    assert reading_green(repaired) is True
    with pytest.raises(ValueError):
        _reading(stages=[42])
    with pytest.raises(ValueError):
        _reading(stages="inspect as a bare string")
    with pytest.raises(ValueError):
        _reading(stages=["taken", "polish"])
    with pytest.raises(ValueError):
        _reading(claims=["weather"])
    with pytest.raises(ValueError):
        _reading(claims="metrics_ref")
    none_reading = _reading(stages=None, claims=None)
    assert none_reading.stages == ()
    assert none_reading.claims == ()

def test_reading_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "readings", "coverage", "current_reading",
                "ledger", "reading"):
        fields = _reading().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_reading(fields)
    fields = _reading().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_reading(fields)


def test_reading_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _reading().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_reading(fields)


def test_reading_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _reading(title="")
    with pytest.raises(ValueError):
        _reading(campaign_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "taken > checked > weighed > calibrated > posted"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_readings_own_fields():
    reading = _reading(claims=["metrics_ref"])
    assert plain_lines(reading) == (
        "Reading: A test reading",
        "Campaign: campaign-test",
        "Stage: posted",
        "Claims: metrics_ref")
    segment = segment_of(reading)
    assert segment.startswith("reading-test: A test reading")
    assert "stage: 'posted'" in segment
    assert "gaps: none" in segment
    assert plain_words(reading).startswith(
        "A test reading - from campaign-test")

def test_red_readings_stand_named_in_their_gaps():
    asking = _reading(claims=["feeling", "metrics_ref", "summary"])
    assert reading_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert reading_green(asking) is False
    skipping = _reading(stages=["taken", "checked", "posted"])
    assert reading_gaps(skipping) == (
        "steps from checked to posted, which the reading sequence "
        "does not allow",)
    book = _book(readings=[
        _reading(),
        _reading(reading_id="reading-skipping", seq=2,
             stages=["taken", "checked", "posted"]),
    ])
    assert transition_breaks(book) == (
        "reading-skipping: checked > posted",)
    assert current_reading(book).reading_id == "reading-skipping"
    assert [g.reading_id for g in reading_reading(book)] == [
        "reading-test", "reading-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "reading_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "reading_note"
    assert record["reading_id"] == "reading-test"
    assert view_plain_words(view) == "View view-test: shows all readings."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_readings_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.stage for e in index.readings] == ["posted"]
    assert index.readings[0] == IndexReading(
        stage="posted",
        reading_id="reading-test", title="A test reading")
    assert index.gaps == ("reading-hidden",)
    record = index_record(book)
    assert record["type"] == "reading_index"
    assert record["gaps"] == ["reading-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "reading_book"

def test_check_target_reaches_its_reading_and_an_unheld_target_reaches_nothing():
    book = load_reading()
    assert reading_for_check(book, "posted").reading_id == (
        "reading-held-reading")
    assert reading_for_check(book, "") is None
    assert reading_for_check(book, None) is None
    assert reading_for_check(book, "not held at all") is None
    text = format_stage(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_reading()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Reading note note reading-held-reading" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").reading_id == "reading-test"
    assert note_for_reading(book, "reading-test").note_id == "note-test"
    assert note_for_reading(book, "reading-test", "praise") is None
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
    row = build_row(None, _reading(), book)
    assert row.standing == "complete"
    assert validate_row(row, _reading(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_readings():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "reading_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "posted"
    empty_book = _book(readings=[_reading(stages=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(ReadingVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_readings():
    book = load_reading()
    assert [g.reading_id for g in shown_readings(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.reading_id for g in shown_readings(book, "view-posted")] == [
        "reading-held-reading", "reading-retried-reading", "reading-own-reading"]
    assert [g.reading_id for g in readings_for_campaign(
        book, "campaign-m230-metrics")] == [
            "reading-own-reading", "reading-bare-reading",
            "reading-leaping-reading"]
    assert readings_for_campaign(book, "campaign-nope") == ()
    assert current_reading(_mixed_book()).reading_id == "reading-hidden"
    assert current_reading(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "reading-test") == (
        "taken > checked > weighed > calibrated > posted")
    assert trace_current(stale, "reading-test") is False
    assert ledger_record(stale)["traces"] == [
        {"reading_id": "reading-test", "trace": "stale"}]

def test_count_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(readings=[_reading(), _reading(seq=2)])
    with pytest.raises(ValueError):
        _book(readings=[_reading(), _reading(reading_id="reading-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(readings=[_reading(campaign_id="campaign-nope")])
    with pytest.raises(ValueError):
        _book(campaigns=[_ref(), _ref(
            campaign_id="campaign-cold", seq=2, state="dormant")],
            readings=[_reading(campaign_id="campaign-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(campaign_id="campaign-nope")])
    fields = {
        "schema": READING_SCHEMA, "campaign": "M-230",
        "method_metrics": {"title": "A weighed book"},
        "campaigns": [_ref().to_record()],
        "reading_records": [_reading().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "posted"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_reading"] = "reading-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_reading")
    fields["trace"] = "reading-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / READING_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "method_metrics.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_reading_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.reading_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = ReadingRegistry()
    assert registry.title() is None
    registry.register_campaign_ref(_ref())
    registry.register_reading(_reading())
    registry.register_view(_view())
    assert [g.reading_id for g in registry.list_readings()] == ["reading-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_reading("reading-test").title == "A test reading"
    assert registry.get_slice("campaign-test").state == "live"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("reading-test").reading_id == "reading-test"
    with pytest.raises(ValueError):
        registry.register_reading(_reading(seq=9))
    with pytest.raises(ValueError):
        registry.register_reading(_reading(reading_id="reading-two"))
    with pytest.raises(KeyError):
        registry.get_reading("reading-nope")
    assert registry.book().title == "An unheld reading book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = ReadingRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test reading book"
    assert registry.title() == "A test reading book"
    assert len(registry.list_readings()) == 2
    other = ReadingRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    reading = _reading()
    assert "A test reading" in plain_words(reading)
    assert panel_plain_words(_mixed_book()).startswith(
        "The reading book holds 2 readings")
    assert verdict_plain_words(_mixed_book()) == (
        "The readings stand held: 1 of 2 shown readings stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green readings; red, "
        "named in its gaps: reading-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_reading(reading)
    assert "Reading: A test reading" in text
    assert "stands complete" in text
    text = format_reading(_reading(stages=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The Reading Gate (M-230) - A test reading book" in book_text
    assert "reading-hidden" in format_book(_mixed_book(), "campaign-test")
    assert "Reading panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "posted - A test reading (reading-test)" in index_text
    assert "reading-hidden" in index_text
    screen = format_reading_screen()
    assert "The Reading Gate (M-230)" in screen
    assert "reading-bare-reading" in screen

def test_parse_args_well_and_loader_targets():
    assert parse_reading_args("") == ("show", None)
    assert parse_reading_args(None) == ("show", None)
    assert parse_reading_args("show") == ("show", None)
    assert parse_reading_args("reading reading-test") == (
        "reading", "reading-test")
    assert parse_reading_args("stage posted") == (
        "stage", "posted")
    assert parse_reading_args("campaign campaign-test") == (
        "campaign", "campaign-test")
    assert parse_reading_args("view view-test") == ("view", "view-test")
    assert parse_reading_args("note note-test") == ("note", "note-test")
    assert parse_reading_args("index") == ("index", None)
    assert parse_reading_args("panel") == ("panel", None)
    assert parse_reading_args("verdict") == ("verdict", None)
    for bad in ("dance", "reading", "stage", "campaign", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_reading_args(bad)
    ledger = ledger_record()
    assert ledger["type"] == "reading_well"
    assert ledger["total"] == 5
    assert ledger["current_reading"] == "reading-bare-reading"
    book = load_reading({
        "schema": READING_SCHEMA, "campaign": "M-230",
        "method_metrics": {"title": "A weighed book"},
        "campaigns": [_ref().to_record()],
        "reading_records": [_reading().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, ReadingBook)
    assert book.title == "A weighed book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_reading({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_reading({"campaign": "M-999"})
    built = build_reading(
        reading_id="reading-kw", seq=3, campaign_id="campaign-test",
        title="Kw Reading", stages=["taken", "checked", "weighed", "calibrated", "posted"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="reading-test")
    assert built.reading_id == "reading-kw"
    assert reading_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-230 agent layer: the agent holds a reading
# book for the session, readings and views are
# published as session news through the
# checkpoint target (ledger first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held readings, the ledger is derived from
# the held readings' completeness, the roadmap standing
# is calibrated from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no campaign. This layer readings
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session ledger news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_READING_EVENT_TYPES = (
    "reading_reading", "reading_run", "reading_view",
    "reading_panel", "reading_verdict")


def _reading_events(store, session_id, campaign):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == campaign]


def _write_metrics_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / READING_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "method_metrics.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestReadingAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.metrics_status()
        assert status["reading_records"] == []
        assert status["campaigns"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["metrics_book"]["title"] == EXAMPLE_TITLE
        assert len(status["metrics_book"]["campaigns"]) == 3
        assert len(status["metrics_book"]["reading_records"]) == 5
        assert len(status["metrics_book"]["views"]) == 2
        assert len(status["metrics_book"]["notes"]) == 2
        assert len(status["metrics_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-m229-campaign"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["stage"] for e in status["index"]["readings"]] == (
            EXAMPLE_STAGES)
        assert status["index"]["gaps"] == [
            "reading-bare-reading", "reading-leaping-reading"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["ledger"]["total"] == 5
        assert status["ledger"]["current_reading"] == "reading-bare-reading"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 271
        assert status["roadmap"]["next_slice"] == "M-272"
        assert status["roadmap"]["m230_title"] == "Method metrics"
        assert "held as data alone" in status["rule"]
        assert "reading-bare-reading" in status["plain_words"]
        assert "The Reading Gate (M-230)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._metrics_registry()
        assert agent._metrics_registry() is first
        assert agent._metrics_store is first
        for name in ("metrics_book", "metrics_status", "metrics_panel",
                     "metrics_verdict", "metrics_index", "report_metrics"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_metrics_registry", "metrics_book", "metrics_status",
            "get_metrics_reading", "get_metrics_view", "get_metrics_note",
            "readings_for_campaign", "metrics_green",
            "metrics_panel", "metrics_verdict", "metrics_index",
            "register_metrics_reading", "register_metrics_view",
            "view_metrics", "register_metrics_book",
            "record_metrics_book", "report_metrics",
            "_publish_metrics_record", "_metrics_screen",
            "_metrics_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.metrics_status()
        assert agent.get_metrics_reading(
            "reading-held-reading").title == "The held reading"
        assert agent.get_metrics_view(
            "view-readings").view_filter == "all"
        assert agent.get_metrics_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.reading_id for d in agent.readings_for_campaign(
            "campaign-m230-metrics")] == [
            "reading-own-reading", "reading-bare-reading",
            "reading-leaping-reading"]
        assert [d.reading_id for d in agent.metrics_green()] == [
            "reading-held-reading", "reading-retried-reading", "reading-own-reading"]
        agent.metrics_panel()
        agent.metrics_verdict()
        agent.metrics_index()
        agent.report_metrics()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _READING_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_metrics_reading("reading-nope")
        with pytest.raises(KeyError):
            agent.get_metrics_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_metrics_note("note-nope")
        with pytest.raises(ValueError):
            agent.readings_for_campaign("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_metrics_reading(_reading())
        status = agent.metrics_status()
        assert [d["reading_id"] for d in status["reading_records"]] == ["reading-test"]
        assert status["book"]["title"] == "An unheld reading book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["stage"] for e in status["index"]["readings"]] == [
            "posted"]
        assert status["first_note"] is None
        assert "reading-test" in status["screen"]
    def test_held_reading_never_falls_back_to_the_example(
            self, agent):
        agent.register_metrics_reading(_reading())
        with pytest.raises(KeyError):
            agent.get_metrics_reading("reading-held-reading")
        with pytest.raises(KeyError):
            agent.get_metrics_view("view-readings")
        with pytest.raises(KeyError):
            agent.get_metrics_note("note-note-first")
        reading = agent.get_metrics_reading("reading-test")
        assert reading.title == "A test reading"
        assert agent.metrics_book().title == (
            "An unheld reading book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_metrics_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.reading_id == "reading-held-reading"
        status = agent.metrics_status()
        assert status["index"]["gaps"] == [
            "reading-bare-reading", "reading-leaping-reading"]
        assert status["first_note"]["reading_id"] == (
            "reading-held-reading")
        assert status["first_note"]["stance"] == "note"

class TestReadingAgentHolding:
    def test_register_reading_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_metrics_reading(_reading())
        assert result["reading"]["reading_id"] == "reading-test"
        assert result["record_news"]["type"] == "reading_reading"
        assert "reading-test" in result["screen"]
        events = _reading_events(store, session_id, "reading_reading")
        assert len(events) == 1
        agent.close()

    def test_duplicate_reading_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_metrics_reading(_reading())
        with pytest.raises(ValueError):
            agent.register_metrics_reading(_reading(seq=9))
        with pytest.raises(ValueError):
            agent.register_metrics_reading(_reading(reading_id="reading-two"))
        events = _reading_events(store, session_id, "reading_reading")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_metrics_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_reading_events(
            store, session_id, "reading_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_metrics_reading(_reading())
        result = agent.view_metrics("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "reading_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "posted"
        assert len(_reading_events(
            store, session_id, "reading_view")) == 1
        assert len(_reading_events(
            store, session_id, "reading_panel")) == 1
        assert len(_reading_events(
            store, session_id, "reading_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_reading(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_metrics_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "reading_run", "reading_reading", "reading_view"]
        assert len(_reading_events(
            store, session_id, "reading_reading")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_metrics_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "reading_panel"
        assert result["index_record"]["gaps"] == [
            "reading-bare-reading", "reading-leaping-reading"]
        with pytest.raises(ValueError):
            agent.record_metrics_book()
        assert len(_reading_events(
            store, session_id, "reading_run")) == 3
        assert len(_reading_events(
            store, session_id, "reading_reading")) == 5
        assert len(_reading_events(
            store, session_id, "reading_view")) == 2
        agent.close()

    def test_book_from_a_file_is_checked_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_metrics_book_file(tmp_path)
        book = load_reading_file(path)
        result = agent.record_metrics_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_runrt_renders_example_then_held_book_only(self, agent):
        reading = agent.report_metrics()
        assert reading["book"]["title"] == EXAMPLE_TITLE
        assert reading["verdict"]["verdict"] == "held"
        assert reading["index"]["gaps"] == [
            "reading-bare-reading", "reading-leaping-reading"]
        assert "reading-held-reading" in reading["book_text"]
        assert "posted - The held reading (reading-held-reading)" in reading["index_text"]
        agent.register_metrics_reading(_reading())
        reading = agent.report_metrics()
        assert reading["book"]["title"] == "An unheld reading book"
        assert reading["panel"] is None
        assert reading["verdict"] is None

class TestReadingTerminalHeading:
    def test_show_reading_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/metrics")
        assert "The Reading Gate (M-230)" in text
        _, _, text = _slash(agent, "/metrics reading reading-held-reading")
        assert "Reading: The held reading" in text
        _, _, text = _slash(
            agent, "/metrics stage posted")
        assert "Reading: The held reading" in text
        _, _, text = _slash(agent, "/metrics stage triple reading")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/metrics campaign campaign-m230-metrics")
        assert "reading-bare-reading" in text
        assert "reading-held-reading" not in text
        _, _, text = _slash(agent, "/metrics view view-readings")
        assert "filter all" in text
        _, _, text = _slash(agent, "/metrics note note-note-first")
        assert "Reading note note reading-held-reading" in text
        _, _, text = _slash(agent, "/metrics index")
        assert "Reading index" in text
        assert "reading-bare-reading" in text
        _, _, text = _slash(agent, "/metrics panel")
        assert "Reading panel under view view-readings" in text
        _, _, text = _slash(agent, "/metrics verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/metrics [show|reading <reading-id>"
                "|stage <stage>|campaign <campaign-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/metrics dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/metrics reading reading-nope")
        assert "no reading named" in text
@pytest.fixture()
def reading_handler(agent, monkeypatch):
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


def _reading_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestReadingCommand:
    def test_show_is_default(self, reading_handler, agent):
        reading_handler._handle_metrics("")
        assert "The Reading Gate (M-230)" in (
            _reading_published_text(reading_handler))

    def test_reading_check_slice_view_note_index_panel_verdict(
            self, reading_handler, agent):
        reading_handler._handle_metrics("reading reading-held-reading")
        assert "Reading: The held reading" in _reading_published_text(
            reading_handler)
        reading_handler._handle_metrics(
            "stage posted")
        assert "Reading: The held reading" in _reading_published_text(
            reading_handler)
        reading_handler._handle_metrics("campaign campaign-m230-metrics")
        assert "reading-bare-reading" in _reading_published_text(
            reading_handler)
        reading_handler._handle_metrics("view view-readings")
        assert "filter all" in _reading_published_text(reading_handler)
        reading_handler._handle_metrics("note note-note-first")
        assert "Reading note note reading-held-reading" in (
            _reading_published_text(reading_handler))
        reading_handler._handle_metrics("index")
        assert "Reading index" in _reading_published_text(reading_handler)
        reading_handler._handle_metrics("panel")
        assert "Reading panel under view" in _reading_published_text(
            reading_handler)
        reading_handler._handle_metrics("verdict")
        assert "held" in _reading_published_text(reading_handler)
    def test_bad_grammar_is_published(
            self, reading_handler, agent):
        reading_handler._handle_metrics("dance party")
        assert USAGE in _reading_published_text(reading_handler)
        reading_handler._handle_metrics("reading reading-nope")
        assert "no reading named" in _reading_published_text(
            reading_handler)


class TestChatScreenRoutingReading:
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
        screen.handle_command("/metrics panel", _FakeLog())
        assert calls == [("/metrics", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/metrics[/green] - show the Reading gate (M-230)" in (
            text)
        assert ('"/metrics": "Usage: /metrics | '
                '/metrics reading <reading-id>') in text

class TestReadingDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.metrics_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-readings"
        verdict = agent.metrics_verdict()
        assert verdict.verdict == "held"
        found = agent.metrics_verdict("view-posted")
        assert found.verdict == "posted"
        assert found.green_shown == 3
        agent.register_metrics_reading(_reading())
        with pytest.raises(ValueError):
            agent.metrics_panel()
        with pytest.raises(ValueError):
            agent.metrics_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_metrics_reading(_reading(stages=[]))
        result = agent.view_metrics("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.metrics_index()
        assert [e["stage"] for e in result["index"]["readings"]] == (
            EXAMPLE_STAGES)
        assert result["index"]["gaps"] == [
            "reading-bare-reading", "reading-leaping-reading"]
        assert "posted - The held reading (reading-held-reading)" in (
            result["index_text"])
        reading = agent.get_metrics_reading("reading-leaping-reading")
        assert reading_gaps(reading, agent.metrics_book()) == (
            "steps from checked to posted, which the reading sequence "
            "does not allow",)
        assert reading_green(reading, agent.metrics_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _READING_EVENT_TYPES] == []
        agent.close()
