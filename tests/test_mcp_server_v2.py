"""M-234 Cross-app method - pure-layer tests.

TIER: integration

The pure layer is the tracker, held as data: one
record per exposure, held whole - the service it
answers for, declared by service id, its title, the
steps it walked in walk exposure and the evidence
it carries, held by service. The question walk is
explicit - declared, contracted, authorised, served,
held, with their legal steps held as data -
and a exposure's standing is derived at call
time: a exposure that opens anywhere but declared, steps where the sequence does not allow,
carries a bare claim in place of held evidence,
or has not yet declared held stands open,
declared in its gaps. A exposure stands only for
an active service: a exposure naming no held
service, or one that is not active, refuses by
name. The exposure's trace - its walked steps
as one line - is derived at call time, and a held
trace record stands current only while it agrees
with the derived trace. The index, panel,
verdict, ledger, trace, exposure and current
exposure are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
question was actually answered, served or
held live. The shipped example book is held
in a data file, and a loader reads a book from
any file. No charter row names this service: the
M-171 TUI charter binds Part VIII alone, and the
M-005 method charter names the whole of Part X
as the part that executes it, both pinned live
below.
"""


from pathlib import Path

import pytest
import yaml

from mythic_agent.core.mcp_server_v2 import (
    EXAMPLE_STAGE,
    BARE_CLAIMS,
    HELD_EVIDENCE,
    INDEX_ACTION,
    STAGES,
    CLAIM_KINDS,
    TRANSITIONS,
    SERVICE_STATES,
    STAGE_FIELDS,
    PLAIN_EXPLANATION,
    EXPOSURE_RESOURCE,
    EXPOSURE_RULE,
    EXPOSURE_SCHEMA,
    EXPOSURE_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    ExposureRecord,
    IndexExposure,
    ServiceRef,
    NoteRecord,
    ExposureBook,
    ExposureIndex,
    ExposurePanel,
    ExposureRegistry,
    ExposureVerdict,
    ExposureView,
    trace_for_exposure,
    ledger_record,
    book_record,
    build_trace,
    build_book,
    build_exposure,
    build_service_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_exposure,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    exposure_for_check,
    exposure_gaps,
    exposure_exposure,
    exposure_record,
    exposure_green,
    exposures_for_service,
    first_note,
    format_book,
    format_exposure,
    format_index,
    format_note,
    format_stage,
    format_panel,
    format_exposure_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    service_record,
    load_exposure,
    legal_step,
    load_exposure_file,
    next_stage,
    normalize_stage,
    normalize_claim_kind,
    normalize_service_state,
    normalize_stance,
    normalize_view_filter,
    note_for_exposure,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_exposure_args,
    green_exposures,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_exposures,
    validate_book,
    validate_exposure,
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
EXAMPLE_TITLE = "MCP service v2 at the M-234 slice run"
EXAMPLE_STAGES = ["held", "held", "held"]
EXAMPLE_RUN_IDS = (
    "exposure-held-exposure", "exposure-retried-exposure",
    "exposure-own-exposure", "exposure-bare-exposure",
    "exposure-leaping-exposure")
EXAMPLE_TRACE = "declared > contracted > authorised > served > held"


def _ref(**overrides):
    fields = {
        "service_id": "service-test",
        "seq": 1,
        "title": "A test service",
        "state": "live",
        "detail": "A test service reference held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "exposure-test",
    }
    fields.update(overrides)
    return build_service_ref(fields)


def _exposure(**overrides):
    fields = {
        "exposure_id": "exposure-test",
        "seq": 1,
        "service_id": "service-test",
        "title": "A test exposure",
        "stages": ["declared", "contracted", "authorised", "served", "held"],
        "claims": [],
        "detail": "A test exposure held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "exposure-test",
    }
    fields.update(overrides)
    return build_exposure(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "exposure-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "exposure_id": "exposure-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "exposure-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "exposure_id": "exposure-test",
        "trace": "declared > contracted > authorised > served > held",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "exposure-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(services=None, exposures=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": EXPOSURE_SCHEMA,
        "service": "M-234",
        "mcp_server_v2": {"title": "A test exposure book"},
        "services": [item.to_record() for item in (
            services if services is not None else [_ref()])],
        "exposure_records": [item.to_record() for item in (
            exposures if exposures is not None else [_exposure()])],
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
    return _book(exposures=[
        _exposure(),
        _exposure(exposure_id="exposure-hidden", seq=2,
               title="A hidden exposure", stages=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_exposure()
    assert book.title == EXAMPLE_TITLE
    assert book.exposure_ids() == EXAMPLE_RUN_IDS
    assert book.service_ids() == (
        "service-campaign", "service-board",
        "service-memorymap")
    assert [v.view_id for v in book.views] == [
        "view-exposures", "view-held"]
    assert [m.exposure_id for m in book.notes] == [
        "exposure-held-exposure", "exposure-bare-exposure"]
    assert [a.exposure_id for a in book.traces] == ["exposure-held-exposure"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-campaign"
    assert panel.as_of == "2026-11-11"
    assert [row.item_id for row in panel.rows] == list(book.exposure_ids())
    derived = derive_panel(book, "view-exposures")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-exposures").verdict == "held"
    assert derive_verdict(book, "view-exposures").green_shown == 3
    assert derive_verdict(book, "view-held").verdict == "held"
    assert derive_verdict(book, "view-held").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / EXPOSURE_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == EXPOSURE_SCHEMA
    assert raw["service"] == "M-234"
    assert "verdict" not in raw
    assert "exposure_index" not in raw
    assert "ledger" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-234")]
    assert slice_.title == "MCP server v2"
    assert slice_.part == 10
    assert "the existing `mythic-mcp` gains campaign, board, and memory-map services with versioned contracts" in slice_.summary
    assert "external agents (Hermes-class) can be dealt slices" in slice_.summary
    assert EXPOSURE_SLICE == "M-234"

def test_charter_rows_do_not_name_m234():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-234" not in owners
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
    assert SERVICE_STATES == ("live", "dormant")
    assert STAGES == ("declared", "contracted", "authorised", "served", "held")
    assert HELD_EVIDENCE == ("campaign_ref", "board_ref", "memorymap_ref", "contract_ref", "policy_ref")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_KINDS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["served"] == ("declared", "held")
    assert TRANSITIONS["held"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_STAGE == "held"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_service_state("LIVE") == "live"
    assert normalize_stage("AUTHORISED") == "authorised"
    assert normalize_claim_kind("FEELING") == "feeling"
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    with pytest.raises(ValueError):
        normalize_service_state("blessed")
    with pytest.raises(ValueError):
        normalize_stage("polish")
    with pytest.raises(ValueError):
        normalize_claim_kind("weather")
    assert legal_step("authorised", "served") is True
    assert legal_step("contracted", "held") is False
    assert legal_step("held", "declared") is False
    assert next_stage("declared") == "contracted"
    assert next_stage("authorised") == "served"
    assert next_stage("served", failed=True) == "declared"
    assert next_stage("served") == "held"
    assert next_stage("held") is None
    assert "held as data alone" in EXPOSURE_RULE
    assert "exposure sequence" in EXPOSURE_RULE
    assert "M-234" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /mcpserver")

def test_shipped_book_judged_honestly_as_data():
    book = load_exposure()
    opening = book.exposure_for("exposure-held-exposure")
    assert exposure_green(opening, book) is True
    assert exposure_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Exposure: The held exposure",
        "Service: service-campaign",
        "Stage: held",
        "Claims: campaign_ref")
    asking = book.exposure_for("exposure-bare-exposure")
    assert exposure_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert exposure_green(asking, book) is False
    skipping = book.exposure_for("exposure-leaping-exposure")
    assert exposure_gaps(skipping, book) == (
        "steps from contracted to held, which the exposure sequence "
        "does not allow",)
    assert [g.exposure_id for g in green_exposures(book)] == [
        "exposure-held-exposure", "exposure-retried-exposure", "exposure-own-exposure"]
    index = derive_index(book)
    assert [e.stage for e in index.exposures] == EXAMPLE_STAGES
    assert index.gaps == ("exposure-bare-exposure", "exposure-leaping-exposure")
    assert exposure_for_check(book, EXAMPLE_STAGE).exposure_id == (
        "exposure-held-exposure")
    assert exposure_for_check(book, "triple exposure") is None
    assert transition_breaks(book) == (
        "exposure-leaping-exposure: contracted > held",)
    assert [g.exposure_id for g in exposure_exposure(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "exposure-held-exposure") == EXAMPLE_TRACE
    assert trace_current(book, "exposure-held-exposure") is True
    assert trace_current(book, "exposure-retried-exposure") is False
    assert trace_for_exposure(
        book, "exposure-held-exposure").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_exposure(
        book, "exposure-held-exposure", "note").note_id == (
            "note-note-first")
    assert note_for_exposure(book, "exposure-nope") is None
    assert current_exposure(book).exposure_id == "exposure-bare-exposure"
    ledger = ledger_record(book)
    assert ledger["standings"] == [
        {"standing": "complete", "exposure_records": 3},
        {"standing": "open", "exposure_records": 2}]
    assert ledger["total"] == 5
    assert ledger["current_exposure"] == "exposure-bare-exposure"
    assert ledger["traces"] == [
        {"exposure_id": "exposure-held-exposure", "trace": "current"},
        {"exposure_id": "exposure-retried-exposure", "trace": "unheld"},
        {"exposure_id": "exposure-own-exposure", "trace": "unheld"},
        {"exposure_id": "exposure-bare-exposure", "trace": "unheld"},
        {"exposure_id": "exposure-leaping-exposure", "trace": "unheld"}]
    assert ledger["breaks"] == ["exposure-leaping-exposure: contracted > held"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 267
    assert citizen["next_slice"] == "M-268"
    assert citizen["m234_title"] == "MCP server v2"
    assert citizen["m234_part"] == 10
    assert citizen["m234_status"] == "done"

def test_exposure_record_round_trips():
    exposure = _exposure()
    assert validate_exposure(exposure) is exposure
    rebuilt = build_exposure(exposure.to_record())
    assert rebuilt == exposure
    assert rebuilt.item_id == "exposure-test"
    assert rebuilt.stage == "held"
    record = exposure_record(exposure)
    assert record["type"] == "exposure_exposure"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert service_record(ref)["type"] == "exposure_run"
    assert service_record(ref)["state"] == "live"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _exposure(stages=[])
    assert exposure_gaps(silent) == (
        "has passed through no step: the exposure has not started",)
    assert exposure_green(silent) is False
    walking = _exposure(stages=["declared", "contracted"])
    assert exposure_gaps(walking) == (
        "has not reached held: the exposure stands at contracted",)
    assert walking.stage == "contracted"
    sideways = _exposure(stages=["contracted", "authorised", "served", "held"])
    assert exposure_gaps(sideways) == (
        "opens at contracted, not at declared: the exposure opens "
        "with the reflection",)
    repaired = _exposure(stages=["declared", "contracted", "authorised", "served", "declared", "contracted", "authorised", "served", "held"])
    assert exposure_gaps(repaired) == ()
    assert exposure_green(repaired) is True
    with pytest.raises(ValueError):
        _exposure(stages=[42])
    with pytest.raises(ValueError):
        _exposure(stages="inspect as a bare string")
    with pytest.raises(ValueError):
        _exposure(stages=["declared", "polish"])
    with pytest.raises(ValueError):
        _exposure(claims=["weather"])
    with pytest.raises(ValueError):
        _exposure(claims="campaign_ref")
    none_exposure = _exposure(stages=None, claims=None)
    assert none_exposure.stages == ()
    assert none_exposure.claims == ()

def test_policy_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "exposures", "coverage", "current_exposure",
                "ledger", "exposure"):
        fields = _exposure().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_exposure(fields)
    fields = _exposure().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_exposure(fields)


def test_policy_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _exposure().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_exposure(fields)


def test_exposure_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _exposure(title="")
    with pytest.raises(ValueError):
        _exposure(service_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "declared > contracted > authorised > served > held"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_exposures_own_fields():
    exposure = _exposure(claims=["campaign_ref"])
    assert plain_lines(exposure) == (
        "Exposure: A test exposure",
        "Service: service-test",
        "Stage: held",
        "Claims: campaign_ref")
    segment = segment_of(exposure)
    assert segment.startswith("exposure-test: A test exposure")
    assert "stage: 'held'" in segment
    assert "gaps: none" in segment
    assert plain_words(exposure).startswith(
        "A test exposure - from service-test")

def test_red_exposures_stand_named_in_their_gaps():
    asking = _exposure(claims=["feeling", "campaign_ref", "summary"])
    assert exposure_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert exposure_green(asking) is False
    skipping = _exposure(stages=["declared", "contracted", "held"])
    assert exposure_gaps(skipping) == (
        "steps from contracted to held, which the exposure sequence "
        "does not allow",)
    book = _book(exposures=[
        _exposure(),
        _exposure(exposure_id="exposure-skipping", seq=2,
             stages=["declared", "contracted", "held"]),
    ])
    assert transition_breaks(book) == (
        "exposure-skipping: contracted > held",)
    assert current_exposure(book).exposure_id == "exposure-skipping"
    assert [g.exposure_id for g in exposure_exposure(book)] == [
        "exposure-test", "exposure-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "exposure_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "exposure_note"
    assert record["exposure_id"] == "exposure-test"
    assert view_plain_words(view) == "View view-test: shows all exposures."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_exposures_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.stage for e in index.exposures] == ["held"]
    assert index.exposures[0] == IndexExposure(
        stage="held",
        exposure_id="exposure-test", title="A test exposure")
    assert index.gaps == ("exposure-hidden",)
    record = index_record(book)
    assert record["type"] == "exposure_index"
    assert record["gaps"] == ["exposure-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "exposure_book"

def test_check_target_reaches_its_exposure_and_an_unheld_target_reaches_nothing():
    book = load_exposure()
    assert exposure_for_check(book, "held").exposure_id == (
        "exposure-held-exposure")
    assert exposure_for_check(book, "") is None
    assert exposure_for_check(book, None) is None
    assert exposure_for_check(book, "not held at all") is None
    text = format_stage(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_exposure()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Exposure note note exposure-held-exposure" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").exposure_id == "exposure-test"
    assert note_for_exposure(book, "exposure-test").note_id == "note-test"
    assert note_for_exposure(book, "exposure-test", "praise") is None
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
    row = build_row(None, _exposure(), book)
    assert row.standing == "complete"
    assert validate_row(row, _exposure(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_exposures():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "exposure_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "held"
    empty_book = _book(exposures=[_exposure(stages=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(ExposureVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_exposures():
    book = load_exposure()
    assert [g.exposure_id for g in shown_exposures(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.exposure_id for g in shown_exposures(book, "view-held")] == [
        "exposure-held-exposure", "exposure-retried-exposure", "exposure-own-exposure"]
    assert [g.exposure_id for g in exposures_for_service(
        book, "service-board")] == [
            "exposure-own-exposure", "exposure-bare-exposure",
            "exposure-leaping-exposure"]
    assert exposures_for_service(book, "service-nope") == ()
    assert current_exposure(_mixed_book()).exposure_id == "exposure-hidden"
    assert current_exposure(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "exposure-test") == (
        "declared > contracted > authorised > served > held")
    assert trace_current(stale, "exposure-test") is False
    assert ledger_record(stale)["traces"] == [
        {"exposure_id": "exposure-test", "trace": "stale"}]

def test_board_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(exposures=[_exposure(), _exposure(seq=2)])
    with pytest.raises(ValueError):
        _book(exposures=[_exposure(), _exposure(exposure_id="exposure-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(exposures=[_exposure(service_id="service-nope")])
    with pytest.raises(ValueError):
        _book(services=[_ref(), _ref(
            service_id="service-cold", seq=2, state="dormant")],
            exposures=[_exposure(service_id="service-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(service_id="service-nope")])
    fields = {
        "schema": EXPOSURE_SCHEMA, "service": "M-234",
        "mcp_server_v2": {"title": "A authorised book"},
        "services": [_ref().to_record()],
        "exposure_records": [_exposure().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "held"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_exposure"] = "exposure-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_exposure")
    fields["trace"] = "exposure-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / EXPOSURE_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "mcp_server_v2.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_exposure_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.exposure_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = ExposureRegistry()
    assert registry.title() is None
    registry.register_service_ref(_ref())
    registry.register_exposure(_exposure())
    registry.register_view(_view())
    assert [g.exposure_id for g in registry.list_exposures()] == ["exposure-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_exposure("exposure-test").title == "A test exposure"
    assert registry.get_slice("service-test").state == "live"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("exposure-test").exposure_id == "exposure-test"
    with pytest.raises(ValueError):
        registry.register_exposure(_exposure(seq=9))
    with pytest.raises(ValueError):
        registry.register_exposure(_exposure(exposure_id="exposure-two"))
    with pytest.raises(KeyError):
        registry.get_exposure("exposure-nope")
    assert registry.book().title == "An unheld exposure book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = ExposureRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test exposure book"
    assert registry.title() == "A test exposure book"
    assert len(registry.list_exposures()) == 2
    other = ExposureRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    exposure = _exposure()
    assert "A test exposure" in plain_words(exposure)
    assert panel_plain_words(_mixed_book()).startswith(
        "The exposure book holds 2 exposures")
    assert verdict_plain_words(_mixed_book()) == (
        "The exposures stand held: 1 of 2 shown exposures stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green exposures; red, "
        "declared in its gaps: exposure-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_exposure(exposure)
    assert "Exposure: A test exposure" in text
    assert "stands complete" in text
    text = format_exposure(_exposure(stages=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The MCP Server v2 (M-234) - A test exposure book" in book_text
    assert "exposure-hidden" in format_book(_mixed_book(), "service-test")
    assert "Exposure panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "held - A test exposure (exposure-test)" in index_text
    assert "exposure-hidden" in index_text
    screen = format_exposure_screen()
    assert "The MCP Server v2 (M-234)" in screen
    assert "exposure-bare-exposure" in screen

def test_parse_args_well_and_loader_targets():
    assert parse_exposure_args("") == ("show", None)
    assert parse_exposure_args(None) == ("show", None)
    assert parse_exposure_args("show") == ("show", None)
    assert parse_exposure_args("exposure exposure-test") == (
        "exposure", "exposure-test")
    assert parse_exposure_args("stage held") == (
        "stage", "held")
    assert parse_exposure_args("service service-test") == (
        "service", "service-test")
    assert parse_exposure_args("view view-test") == ("view", "view-test")
    assert parse_exposure_args("note note-test") == ("note", "note-test")
    assert parse_exposure_args("index") == ("index", None)
    assert parse_exposure_args("panel") == ("panel", None)
    assert parse_exposure_args("verdict") == ("verdict", None)
    for bad in ("dance", "exposure", "stage", "service", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_exposure_args(bad)
    ledger = ledger_record()
    assert ledger["type"] == "exposure_well"
    assert ledger["total"] == 5
    assert ledger["current_exposure"] == "exposure-bare-exposure"
    book = load_exposure({
        "schema": EXPOSURE_SCHEMA, "service": "M-234",
        "mcp_server_v2": {"title": "A authorised book"},
        "services": [_ref().to_record()],
        "exposure_records": [_exposure().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, ExposureBook)
    assert book.title == "A authorised book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_exposure({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_exposure({"service": "M-999"})
    built = build_exposure(
        exposure_id="exposure-kw", seq=3, service_id="service-test",
        title="Kw Exposure", stages=["declared", "contracted", "authorised", "served", "held"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="exposure-test")
    assert built.exposure_id == "exposure-kw"
    assert exposure_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-234 agent layer: the agent holds a exposure
# book for the session, exposures and views are
# published as session news through the
# checkpoint target (ledger first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held exposures, the ledger is derived from
# the held exposures' completeness, the roadmap standing
# is served from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no service. This layer exposures
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session ledger news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_EXPOSURE_EVENT_TYPES = (
    "exposure_exposure", "exposure_run", "exposure_view",
    "exposure_panel", "exposure_verdict")


def _exposure_events(store, session_id, service):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == service]


def _write_mcpserver_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / EXPOSURE_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "mcp_server_v2.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestExposureAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.mcpserver_status()
        assert status["exposure_records"] == []
        assert status["services"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["mcpserver_book"]["title"] == EXAMPLE_TITLE
        assert len(status["mcpserver_book"]["services"]) == 3
        assert len(status["mcpserver_book"]["exposure_records"]) == 5
        assert len(status["mcpserver_book"]["views"]) == 2
        assert len(status["mcpserver_book"]["notes"]) == 2
        assert len(status["mcpserver_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-campaign"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["stage"] for e in status["index"]["exposures"]] == (
            EXAMPLE_STAGES)
        assert status["index"]["gaps"] == [
            "exposure-bare-exposure", "exposure-leaping-exposure"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["ledger"]["total"] == 5
        assert status["ledger"]["current_exposure"] == "exposure-bare-exposure"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 267
        assert status["roadmap"]["next_slice"] == "M-268"
        assert status["roadmap"]["m234_title"] == "MCP server v2"
        assert "held as data alone" in status["rule"]
        assert "exposure-bare-exposure" in status["plain_words"]
        assert "The MCP Server v2 (M-234)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._mcpserver_registry()
        assert agent._mcpserver_registry() is first
        assert agent._mcpserver_store is first
        for name in ("mcpserver_book", "mcpserver_status", "mcpserver_panel",
                     "mcpserver_verdict", "mcpserver_index", "report_mcpserver"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_mcpserver_registry", "mcpserver_book", "mcpserver_status",
            "get_mcpserver_exposure", "get_mcpserver_view", "get_mcpserver_note",
            "exposures_for_service", "mcpserver_green",
            "mcpserver_panel", "mcpserver_verdict", "mcpserver_index",
            "register_mcpserver_exposure", "register_mcpserver_view",
            "view_mcpserver", "register_mcpserver_book",
            "record_mcpserver_book", "report_mcpserver",
            "_publish_mcpserver_record", "_mcpserver_screen",
            "_mcpserver_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.mcpserver_status()
        assert agent.get_mcpserver_exposure(
            "exposure-held-exposure").title == "The held exposure"
        assert agent.get_mcpserver_view(
            "view-exposures").view_filter == "all"
        assert agent.get_mcpserver_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.exposure_id for d in agent.exposures_for_service(
            "service-board")] == [
            "exposure-own-exposure", "exposure-bare-exposure",
            "exposure-leaping-exposure"]
        assert [d.exposure_id for d in agent.mcpserver_green()] == [
            "exposure-held-exposure", "exposure-retried-exposure", "exposure-own-exposure"]
        agent.mcpserver_panel()
        agent.mcpserver_verdict()
        agent.mcpserver_index()
        agent.report_mcpserver()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _EXPOSURE_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_mcpserver_exposure("exposure-nope")
        with pytest.raises(KeyError):
            agent.get_mcpserver_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_mcpserver_note("note-nope")
        with pytest.raises(ValueError):
            agent.exposures_for_service("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_mcpserver_exposure(_exposure())
        status = agent.mcpserver_status()
        assert [d["exposure_id"] for d in status["exposure_records"]] == ["exposure-test"]
        assert status["book"]["title"] == "An unheld exposure book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["stage"] for e in status["index"]["exposures"]] == [
            "held"]
        assert status["first_note"] is None
        assert "exposure-test" in status["screen"]
    def test_held_exposure_never_falls_back_to_the_example(
            self, agent):
        agent.register_mcpserver_exposure(_exposure())
        with pytest.raises(KeyError):
            agent.get_mcpserver_exposure("exposure-held-exposure")
        with pytest.raises(KeyError):
            agent.get_mcpserver_view("view-exposures")
        with pytest.raises(KeyError):
            agent.get_mcpserver_note("note-note-first")
        exposure = agent.get_mcpserver_exposure("exposure-test")
        assert exposure.title == "A test exposure"
        assert agent.mcpserver_book().title == (
            "An unheld exposure book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_mcpserver_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.exposure_id == "exposure-held-exposure"
        status = agent.mcpserver_status()
        assert status["index"]["gaps"] == [
            "exposure-bare-exposure", "exposure-leaping-exposure"]
        assert status["first_note"]["exposure_id"] == (
            "exposure-held-exposure")
        assert status["first_note"]["stance"] == "note"

class TestExposureAgentHolding:
    def test_register_exposure_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_mcpserver_exposure(_exposure())
        assert result["exposure"]["exposure_id"] == "exposure-test"
        assert result["record_news"]["type"] == "exposure_exposure"
        assert "exposure-test" in result["screen"]
        events = _exposure_events(store, session_id, "exposure_exposure")
        assert len(events) == 1
        agent.close()

    def test_duplicate_policy_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_mcpserver_exposure(_exposure())
        with pytest.raises(ValueError):
            agent.register_mcpserver_exposure(_exposure(seq=9))
        with pytest.raises(ValueError):
            agent.register_mcpserver_exposure(_exposure(exposure_id="exposure-two"))
        events = _exposure_events(store, session_id, "exposure_exposure")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_mcpserver_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_exposure_events(
            store, session_id, "exposure_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_mcpserver_exposure(_exposure())
        result = agent.view_mcpserver("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "exposure_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "held"
        assert len(_exposure_events(
            store, session_id, "exposure_view")) == 1
        assert len(_exposure_events(
            store, session_id, "exposure_panel")) == 1
        assert len(_exposure_events(
            store, session_id, "exposure_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_exposure(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_mcpserver_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "exposure_run", "exposure_exposure", "exposure_view"]
        assert len(_exposure_events(
            store, session_id, "exposure_exposure")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_mcpserver_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "exposure_panel"
        assert result["index_record"]["gaps"] == [
            "exposure-bare-exposure", "exposure-leaping-exposure"]
        with pytest.raises(ValueError):
            agent.record_mcpserver_book()
        assert len(_exposure_events(
            store, session_id, "exposure_run")) == 3
        assert len(_exposure_events(
            store, session_id, "exposure_exposure")) == 5
        assert len(_exposure_events(
            store, session_id, "exposure_view")) == 2
        agent.close()

    def test_book_from_a_file_is_linked_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_mcpserver_book_file(tmp_path)
        book = load_exposure_file(path)
        result = agent.record_mcpserver_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_runrt_renders_example_then_held_book_only(self, agent):
        exposure = agent.report_mcpserver()
        assert exposure["book"]["title"] == EXAMPLE_TITLE
        assert exposure["verdict"]["verdict"] == "held"
        assert exposure["index"]["gaps"] == [
            "exposure-bare-exposure", "exposure-leaping-exposure"]
        assert "exposure-held-exposure" in exposure["book_text"]
        assert "held - The held exposure (exposure-held-exposure)" in exposure["index_text"]
        agent.register_mcpserver_exposure(_exposure())
        exposure = agent.report_mcpserver()
        assert exposure["book"]["title"] == "An unheld exposure book"
        assert exposure["panel"] is None
        assert exposure["verdict"] is None

class TestExposureTerminalHeading:
    def test_show_exposure_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/mcpserver")
        assert "The MCP Server v2 (M-234)" in text
        _, _, text = _slash(agent, "/mcpserver exposure exposure-held-exposure")
        assert "Exposure: The held exposure" in text
        _, _, text = _slash(
            agent, "/mcpserver stage held")
        assert "Exposure: The held exposure" in text
        _, _, text = _slash(agent, "/mcpserver stage triple exposure")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/mcpserver service service-board")
        assert "exposure-bare-exposure" in text
        assert "exposure-held-exposure" not in text
        _, _, text = _slash(agent, "/mcpserver view view-exposures")
        assert "filter all" in text
        _, _, text = _slash(agent, "/mcpserver note note-note-first")
        assert "Exposure note note exposure-held-exposure" in text
        _, _, text = _slash(agent, "/mcpserver index")
        assert "Exposure index" in text
        assert "exposure-bare-exposure" in text
        _, _, text = _slash(agent, "/mcpserver panel")
        assert "Exposure panel under view view-exposures" in text
        _, _, text = _slash(agent, "/mcpserver verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/mcpserver [show|exposure <exposure-id>"
                "|stage <stage>|service <service-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/mcpserver dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/mcpserver exposure exposure-nope")
        assert "no exposure declared" in text
@pytest.fixture()
def exposure_handler(agent, monkeypatch):
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


def _exposure_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestExposureCommand:
    def test_show_is_default(self, exposure_handler, agent):
        exposure_handler._handle_mcpserver("")
        assert "The MCP Server v2 (M-234)" in (
            _exposure_published_text(exposure_handler))

    def test_exposure_check_slice_view_note_index_panel_verdict(
            self, exposure_handler, agent):
        exposure_handler._handle_mcpserver("exposure exposure-held-exposure")
        assert "Exposure: The held exposure" in _exposure_published_text(
            exposure_handler)
        exposure_handler._handle_mcpserver(
            "stage held")
        assert "Exposure: The held exposure" in _exposure_published_text(
            exposure_handler)
        exposure_handler._handle_mcpserver("service service-board")
        assert "exposure-bare-exposure" in _exposure_published_text(
            exposure_handler)
        exposure_handler._handle_mcpserver("view view-exposures")
        assert "filter all" in _exposure_published_text(exposure_handler)
        exposure_handler._handle_mcpserver("note note-note-first")
        assert "Exposure note note exposure-held-exposure" in (
            _exposure_published_text(exposure_handler))
        exposure_handler._handle_mcpserver("index")
        assert "Exposure index" in _exposure_published_text(exposure_handler)
        exposure_handler._handle_mcpserver("panel")
        assert "Exposure panel under view" in _exposure_published_text(
            exposure_handler)
        exposure_handler._handle_mcpserver("verdict")
        assert "held" in _exposure_published_text(exposure_handler)
    def test_bad_grammar_is_published(
            self, exposure_handler, agent):
        exposure_handler._handle_mcpserver("dance party")
        assert USAGE in _exposure_published_text(exposure_handler)
        exposure_handler._handle_mcpserver("exposure exposure-nope")
        assert "no exposure declared" in _exposure_published_text(
            exposure_handler)


class TestChatScreenRoutingExposure:
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
        screen.handle_command("/mcpserver panel", _FakeLog())
        assert calls == [("/mcpserver", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/mcpserver[/green] - show the MCP server v2 (M-234)" in (
            text)
        assert ('"/mcpserver": "Usage: /mcpserver | '
                '/mcpserver exposure <exposure-id>') in text

class TestExposureDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.mcpserver_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-exposures"
        verdict = agent.mcpserver_verdict()
        assert verdict.verdict == "held"
        found = agent.mcpserver_verdict("view-held")
        assert found.verdict == "held"
        assert found.green_shown == 3
        agent.register_mcpserver_exposure(_exposure())
        with pytest.raises(ValueError):
            agent.mcpserver_panel()
        with pytest.raises(ValueError):
            agent.mcpserver_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_mcpserver_exposure(_exposure(stages=[]))
        result = agent.view_mcpserver("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.mcpserver_index()
        assert [e["stage"] for e in result["index"]["exposures"]] == (
            EXAMPLE_STAGES)
        assert result["index"]["gaps"] == [
            "exposure-bare-exposure", "exposure-leaping-exposure"]
        assert "held - The held exposure (exposure-held-exposure)" in (
            result["index_text"])
        exposure = agent.get_mcpserver_exposure("exposure-leaping-exposure")
        assert exposure_gaps(exposure, agent.mcpserver_book()) == (
            "steps from contracted to held, which the exposure sequence "
            "does not allow",)
        assert exposure_green(exposure, agent.mcpserver_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _EXPOSURE_EVENT_TYPES] == []
        agent.close()
