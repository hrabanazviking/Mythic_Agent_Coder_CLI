"""M-240 Cross-app method - pure-layer tests.

TIER: integration

The pure layer is the tracker, held as data: one
record per endpoint, held whole - the host it
answers for, declared by host id, its title, the
steps it walked in walk endpoint and the evidence
it carries, held by host. The question walk is
explicit - declared, negotiated, bound, exchanged,
held, with their legal steps held as data -
and a endpoint's standing is derived at call
time: a endpoint that opens anywhere but declared, steps where the sequence does not allow,
carries a bare claim in place of held evidence,
or has not yet declared held stands open,
declared in its gaps. A endpoint stands only for
an active host: a endpoint naming no held
host, or one that is not active, refuses by
name. The endpoint's trace - its walked steps
as one line - is derived at call time, and a held
trace record stands current only while it agrees
with the derived trace. The index, panel,
verdict, ledger, trace, endpoint and current
endpoint are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
question was actually answered, exchanged or
held live. The shipped example book is held
in a data file, and a loader reads a book from
any file. No charter row names this host: the
M-171 TUI charter binds Part VIII alone, and the
M-005 method charter names the whole of Part X
as the part that executes it, both pinned live
below.
"""


from pathlib import Path

import pytest
import yaml

from mythic_agent.core.ide_companions import (
    EXAMPLE_STAGE,
    BARE_CLAIMS,
    HELD_EVIDENCE,
    INDEX_ACTION,
    STAGES,
    CLAIM_KINDS,
    TRANSITIONS,
    HOST_STATES,
    STAGE_FIELDS,
    PLAIN_EXPLANATION,
    ENDPOINT_RESOURCE,
    ENDPOINT_RULE,
    ENDPOINT_SCHEMA,
    ENDPOINT_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    EndpointRecord,
    IndexEndpoint,
    HostRef,
    NoteRecord,
    EndpointBook,
    EndpointIndex,
    EndpointPanel,
    EndpointRegistry,
    EndpointVerdict,
    EndpointView,
    trace_for_endpoint,
    ledger_record,
    book_record,
    build_trace,
    build_book,
    build_endpoint,
    build_host_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_endpoint,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    endpoint_for_check,
    endpoint_gaps,
    endpoint_endpoint,
    endpoint_record,
    endpoint_green,
    endpoints_for_host,
    first_note,
    format_book,
    format_endpoint,
    format_index,
    format_note,
    format_stage,
    format_panel,
    format_endpoint_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    host_record,
    load_endpoint,
    legal_step,
    load_endpoint_file,
    next_stage,
    normalize_stage,
    normalize_claim_kind,
    normalize_host_state,
    normalize_stance,
    normalize_view_filter,
    note_for_endpoint,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_endpoint_args,
    green_endpoints,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_endpoints,
    validate_book,
    validate_endpoint,
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
EXAMPLE_TITLE = "IDE companions at the M-240 slice run"
EXAMPLE_STAGES = ["held", "held", "held"]
EXAMPLE_RUN_IDS = (
    "endpoint-held-endpoint", "endpoint-retried-endpoint",
    "endpoint-own-endpoint", "endpoint-bare-endpoint",
    "endpoint-leaping-endpoint")
EXAMPLE_TRACE = "declared > negotiated > bound > exchanged > held"


def _ref(**overrides):
    fields = {
        "host_id": "host-test",
        "seq": 1,
        "title": "A test host",
        "state": "live",
        "detail": "A test host reference held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "endpoint-test",
    }
    fields.update(overrides)
    return build_host_ref(fields)


def _endpoint(**overrides):
    fields = {
        "endpoint_id": "endpoint-test",
        "seq": 1,
        "host_id": "host-test",
        "title": "A test endpoint",
        "stages": ["declared", "negotiated", "bound", "exchanged", "held"],
        "claims": [],
        "detail": "A test endpoint held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "endpoint-test",
    }
    fields.update(overrides)
    return build_endpoint(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "endpoint-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "endpoint_id": "endpoint-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "endpoint-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "endpoint_id": "endpoint-test",
        "trace": "declared > negotiated > bound > exchanged > held",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "endpoint-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(hosts=None, endpoints=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": ENDPOINT_SCHEMA,
        "host": "M-240",
        "ide_companions": {"title": "A test endpoint book"},
        "hosts": [item.to_record() for item in (
            hosts if hosts is not None else [_ref()])],
        "endpoint_records": [item.to_record() for item in (
            endpoints if endpoints is not None else [_endpoint()])],
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
    return _book(endpoints=[
        _endpoint(),
        _endpoint(endpoint_id="endpoint-hidden", seq=2,
               title="A hidden endpoint", stages=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_endpoint()
    assert book.title == EXAMPLE_TITLE
    assert book.endpoint_ids() == EXAMPLE_RUN_IDS
    assert book.host_ids() == (
        "ide-intellij", "ide-pycharm",
        "ide-generic")
    assert [v.view_id for v in book.views] == [
        "view-endpoints", "view-held"]
    assert [m.endpoint_id for m in book.notes] == [
        "endpoint-held-endpoint", "endpoint-bare-endpoint"]
    assert [a.endpoint_id for a in book.traces] == ["endpoint-held-endpoint"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-ide"
    assert panel.as_of == "2026-11-11"
    assert [row.item_id for row in panel.rows] == list(book.endpoint_ids())
    derived = derive_panel(book, "view-endpoints")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-endpoints").verdict == "held"
    assert derive_verdict(book, "view-endpoints").green_shown == 3
    assert derive_verdict(book, "view-held").verdict == "held"
    assert derive_verdict(book, "view-held").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / ENDPOINT_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == ENDPOINT_SCHEMA
    assert raw["host"] == "M-240"
    assert "verdict" not in raw
    assert "endpoint_index" not in raw
    assert "ledger" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-240")]
    assert slice_.title == "IDE companions II — JetBrains and the generic road"
    assert slice_.part == 10
    assert "an editor-agnostic protocol any IDE plugin can speak" in slice_.summary
    assert "terminal-first remains complete without" in slice_.summary
    assert ENDPOINT_SLICE == "M-240"

def test_charter_rows_do_not_name_m240():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-240" not in owners
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
    assert HOST_STATES == ("live", "dormant")
    assert STAGES == ("declared", "negotiated", "bound", "exchanged", "held")
    assert HELD_EVIDENCE == ("capability_ref", "message_ref", "request_ref", "response_ref", "session_ref", "channel_ref")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_KINDS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["exchanged"] == ("declared", "held")
    assert TRANSITIONS["held"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_STAGE == "held"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_host_state("LIVE") == "live"
    assert normalize_stage("BOUND") == "bound"
    assert normalize_claim_kind("FEELING") == "feeling"
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    with pytest.raises(ValueError):
        normalize_host_state("blessed")
    with pytest.raises(ValueError):
        normalize_stage("polish")
    with pytest.raises(ValueError):
        normalize_claim_kind("weather")
    assert legal_step("bound", "exchanged") is True
    assert legal_step("negotiated", "held") is False
    assert legal_step("held", "declared") is False
    assert next_stage("declared") == "negotiated"
    assert next_stage("bound") == "exchanged"
    assert next_stage("exchanged", failed=True) == "declared"
    assert next_stage("exchanged") == "held"
    assert next_stage("held") is None
    assert "held as data alone" in ENDPOINT_RULE
    assert "endpoint sequence" in ENDPOINT_RULE
    assert "M-240" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /idecompanions")

def test_shipped_book_judged_honestly_as_data():
    book = load_endpoint()
    opening = book.endpoint_for("endpoint-held-endpoint")
    assert endpoint_green(opening, book) is True
    assert endpoint_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Endpoint: The held endpoint",
        "Host: ide-intellij",
        "Stage: held",
        "Claims: capability_ref")
    asking = book.endpoint_for("endpoint-bare-endpoint")
    assert endpoint_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert endpoint_green(asking, book) is False
    skipping = book.endpoint_for("endpoint-leaping-endpoint")
    assert endpoint_gaps(skipping, book) == (
        "steps from negotiated to held, which the endpoint sequence "
        "does not allow",)
    assert [g.endpoint_id for g in green_endpoints(book)] == [
        "endpoint-held-endpoint", "endpoint-retried-endpoint", "endpoint-own-endpoint"]
    index = derive_index(book)
    assert [e.stage for e in index.endpoints] == EXAMPLE_STAGES
    assert index.gaps == ("endpoint-bare-endpoint", "endpoint-leaping-endpoint")
    assert endpoint_for_check(book, EXAMPLE_STAGE).endpoint_id == (
        "endpoint-held-endpoint")
    assert endpoint_for_check(book, "triple endpoint") is None
    assert transition_breaks(book) == (
        "endpoint-leaping-endpoint: negotiated > held",)
    assert [g.endpoint_id for g in endpoint_endpoint(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "endpoint-held-endpoint") == EXAMPLE_TRACE
    assert trace_current(book, "endpoint-held-endpoint") is True
    assert trace_current(book, "endpoint-retried-endpoint") is False
    assert trace_for_endpoint(
        book, "endpoint-held-endpoint").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_endpoint(
        book, "endpoint-held-endpoint", "note").note_id == (
            "note-note-first")
    assert note_for_endpoint(book, "endpoint-nope") is None
    assert current_endpoint(book).endpoint_id == "endpoint-bare-endpoint"
    ledger = ledger_record(book)
    assert ledger["standings"] == [
        {"standing": "complete", "endpoint_records": 3},
        {"standing": "open", "endpoint_records": 2}]
    assert ledger["total"] == 5
    assert ledger["current_endpoint"] == "endpoint-bare-endpoint"
    assert ledger["traces"] == [
        {"endpoint_id": "endpoint-held-endpoint", "trace": "current"},
        {"endpoint_id": "endpoint-retried-endpoint", "trace": "unheld"},
        {"endpoint_id": "endpoint-own-endpoint", "trace": "unheld"},
        {"endpoint_id": "endpoint-bare-endpoint", "trace": "unheld"},
        {"endpoint_id": "endpoint-leaping-endpoint", "trace": "unheld"}]
    assert ledger["breaks"] == ["endpoint-leaping-endpoint: negotiated > held"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 263
    assert citizen["next_slice"] == "M-264"
    assert citizen["m240_title"] == "IDE companions II — JetBrains and the generic road"
    assert citizen["m240_part"] == 10
    assert citizen["m240_status"] == "done"

def test_endpoint_record_round_trips():
    endpoint = _endpoint()
    assert validate_endpoint(endpoint) is endpoint
    rebuilt = build_endpoint(endpoint.to_record())
    assert rebuilt == endpoint
    assert rebuilt.item_id == "endpoint-test"
    assert rebuilt.stage == "held"
    record = endpoint_record(endpoint)
    assert record["type"] == "endpoint_endpoint"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert host_record(ref)["type"] == "endpoint_run"
    assert host_record(ref)["state"] == "live"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _endpoint(stages=[])
    assert endpoint_gaps(silent) == (
        "has passed through no step: the endpoint has not started",)
    assert endpoint_green(silent) is False
    walking = _endpoint(stages=["declared", "negotiated"])
    assert endpoint_gaps(walking) == (
        "has not reached held: the endpoint stands at negotiated",)
    assert walking.stage == "negotiated"
    sideways = _endpoint(stages=["negotiated", "bound", "exchanged", "held"])
    assert endpoint_gaps(sideways) == (
        "opens at negotiated, not at declared: the endpoint opens "
        "with the reflection",)
    repaired = _endpoint(stages=["declared", "negotiated", "bound", "exchanged", "declared", "negotiated", "bound", "exchanged", "held"])
    assert endpoint_gaps(repaired) == ()
    assert endpoint_green(repaired) is True
    with pytest.raises(ValueError):
        _endpoint(stages=[42])
    with pytest.raises(ValueError):
        _endpoint(stages="inspect as a bare string")
    with pytest.raises(ValueError):
        _endpoint(stages=["declared", "polish"])
    with pytest.raises(ValueError):
        _endpoint(claims=["weather"])
    with pytest.raises(ValueError):
        _endpoint(claims="capability_ref")
    none_endpoint = _endpoint(stages=None, claims=None)
    assert none_endpoint.stages == ()
    assert none_endpoint.claims == ()

def test_channel_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "endpoints", "coverage", "current_endpoint",
                "ledger", "endpoint"):
        fields = _endpoint().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_endpoint(fields)
    fields = _endpoint().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_endpoint(fields)


def test_channel_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _endpoint().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_endpoint(fields)


def test_endpoint_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _endpoint(title="")
    with pytest.raises(ValueError):
        _endpoint(host_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "declared > negotiated > bound > exchanged > held"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_endpoints_own_fields():
    endpoint = _endpoint(claims=["capability_ref"])
    assert plain_lines(endpoint) == (
        "Endpoint: A test endpoint",
        "Host: host-test",
        "Stage: held",
        "Claims: capability_ref")
    segment = segment_of(endpoint)
    assert segment.startswith("endpoint-test: A test endpoint")
    assert "stage: 'held'" in segment
    assert "gaps: none" in segment
    assert plain_words(endpoint).startswith(
        "A test endpoint - from host-test")

def test_red_endpoints_stand_named_in_their_gaps():
    asking = _endpoint(claims=["feeling", "capability_ref", "summary"])
    assert endpoint_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert endpoint_green(asking) is False
    skipping = _endpoint(stages=["declared", "negotiated", "held"])
    assert endpoint_gaps(skipping) == (
        "steps from negotiated to held, which the endpoint sequence "
        "does not allow",)
    book = _book(endpoints=[
        _endpoint(),
        _endpoint(endpoint_id="endpoint-skipping", seq=2,
             stages=["declared", "negotiated", "held"]),
    ])
    assert transition_breaks(book) == (
        "endpoint-skipping: negotiated > held",)
    assert current_endpoint(book).endpoint_id == "endpoint-skipping"
    assert [g.endpoint_id for g in endpoint_endpoint(book)] == [
        "endpoint-test", "endpoint-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "endpoint_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "endpoint_note"
    assert record["endpoint_id"] == "endpoint-test"
    assert view_plain_words(view) == "View view-test: shows all endpoints."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_endpoints_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.stage for e in index.endpoints] == ["held"]
    assert index.endpoints[0] == IndexEndpoint(
        stage="held",
        endpoint_id="endpoint-test", title="A test endpoint")
    assert index.gaps == ("endpoint-hidden",)
    record = index_record(book)
    assert record["type"] == "endpoint_index"
    assert record["gaps"] == ["endpoint-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "endpoint_book"

def test_check_target_reaches_its_endpoint_and_an_unheld_target_reaches_nothing():
    book = load_endpoint()
    assert endpoint_for_check(book, "held").endpoint_id == (
        "endpoint-held-endpoint")
    assert endpoint_for_check(book, "") is None
    assert endpoint_for_check(book, None) is None
    assert endpoint_for_check(book, "not held at all") is None
    text = format_stage(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_endpoint()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Endpoint note note endpoint-held-endpoint" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").endpoint_id == "endpoint-test"
    assert note_for_endpoint(book, "endpoint-test").note_id == "note-test"
    assert note_for_endpoint(book, "endpoint-test", "praise") is None
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
    row = build_row(None, _endpoint(), book)
    assert row.standing == "complete"
    assert validate_row(row, _endpoint(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_endpoints():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "endpoint_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "held"
    empty_book = _book(endpoints=[_endpoint(stages=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(EndpointVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_endpoints():
    book = load_endpoint()
    assert [g.endpoint_id for g in shown_endpoints(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.endpoint_id for g in shown_endpoints(book, "view-held")] == [
        "endpoint-held-endpoint", "endpoint-retried-endpoint", "endpoint-own-endpoint"]
    assert [g.endpoint_id for g in endpoints_for_host(
        book, "ide-pycharm")] == [
            "endpoint-own-endpoint", "endpoint-bare-endpoint",
            "endpoint-leaping-endpoint"]
    assert endpoints_for_host(book, "host-nope") == ()
    assert current_endpoint(_mixed_book()).endpoint_id == "endpoint-hidden"
    assert current_endpoint(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "endpoint-test") == (
        "declared > negotiated > bound > exchanged > held")
    assert trace_current(stale, "endpoint-test") is False
    assert ledger_record(stale)["traces"] == [
        {"endpoint_id": "endpoint-test", "trace": "stale"}]

def test_message_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(endpoints=[_endpoint(), _endpoint(seq=2)])
    with pytest.raises(ValueError):
        _book(endpoints=[_endpoint(), _endpoint(endpoint_id="endpoint-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(endpoints=[_endpoint(host_id="host-nope")])
    with pytest.raises(ValueError):
        _book(hosts=[_ref(), _ref(
            host_id="host-cold", seq=2, state="dormant")],
            endpoints=[_endpoint(host_id="host-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(host_id="host-nope")])
    fields = {
        "schema": ENDPOINT_SCHEMA, "host": "M-240",
        "ide_companions": {"title": "A bound book"},
        "hosts": [_ref().to_record()],
        "endpoint_records": [_endpoint().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "held"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_endpoint"] = "endpoint-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_endpoint")
    fields["trace"] = "endpoint-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / ENDPOINT_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "ide_companions.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_endpoint_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.endpoint_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = EndpointRegistry()
    assert registry.title() is None
    registry.register_host_ref(_ref())
    registry.register_endpoint(_endpoint())
    registry.register_view(_view())
    assert [g.endpoint_id for g in registry.list_endpoints()] == ["endpoint-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_endpoint("endpoint-test").title == "A test endpoint"
    assert registry.get_slice("host-test").state == "live"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("endpoint-test").endpoint_id == "endpoint-test"
    with pytest.raises(ValueError):
        registry.register_endpoint(_endpoint(seq=9))
    with pytest.raises(ValueError):
        registry.register_endpoint(_endpoint(endpoint_id="endpoint-two"))
    with pytest.raises(KeyError):
        registry.get_endpoint("endpoint-nope")
    assert registry.book().title == "An unheld endpoint book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = EndpointRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test endpoint book"
    assert registry.title() == "A test endpoint book"
    assert len(registry.list_endpoints()) == 2
    other = EndpointRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    endpoint = _endpoint()
    assert "A test endpoint" in plain_words(endpoint)
    assert panel_plain_words(_mixed_book()).startswith(
        "The endpoint book holds 2 endpoints")
    assert verdict_plain_words(_mixed_book()) == (
        "The endpoints stand held: 1 of 2 shown endpoints stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green endpoints; red, "
        "declared in its gaps: endpoint-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_endpoint(endpoint)
    assert "Endpoint: A test endpoint" in text
    assert "stands complete" in text
    text = format_endpoint(_endpoint(stages=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The IDE Companions (M-240) - A test endpoint book" in book_text
    assert "endpoint-hidden" in format_book(_mixed_book(), "host-test")
    assert "Endpoint panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "held - A test endpoint (endpoint-test)" in index_text
    assert "endpoint-hidden" in index_text
    screen = format_endpoint_screen()
    assert "The IDE Companions (M-240)" in screen
    assert "endpoint-bare-endpoint" in screen

def test_parse_args_well_and_loader_targets():
    assert parse_endpoint_args("") == ("show", None)
    assert parse_endpoint_args(None) == ("show", None)
    assert parse_endpoint_args("show") == ("show", None)
    assert parse_endpoint_args("endpoint endpoint-test") == (
        "endpoint", "endpoint-test")
    assert parse_endpoint_args("stage held") == (
        "stage", "held")
    assert parse_endpoint_args("host host-test") == (
        "host", "host-test")
    assert parse_endpoint_args("view view-test") == ("view", "view-test")
    assert parse_endpoint_args("note note-test") == ("note", "note-test")
    assert parse_endpoint_args("index") == ("index", None)
    assert parse_endpoint_args("panel") == ("panel", None)
    assert parse_endpoint_args("verdict") == ("verdict", None)
    for bad in ("dance", "endpoint", "stage", "host", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_endpoint_args(bad)
    ledger = ledger_record()
    assert ledger["type"] == "endpoint_well"
    assert ledger["total"] == 5
    assert ledger["current_endpoint"] == "endpoint-bare-endpoint"
    book = load_endpoint({
        "schema": ENDPOINT_SCHEMA, "host": "M-240",
        "ide_companions": {"title": "A bound book"},
        "hosts": [_ref().to_record()],
        "endpoint_records": [_endpoint().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, EndpointBook)
    assert book.title == "A bound book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_endpoint({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_endpoint({"host": "M-999"})
    built = build_endpoint(
        endpoint_id="endpoint-kw", seq=3, host_id="host-test",
        title="Kw Endpoint", stages=["declared", "negotiated", "bound", "exchanged", "held"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="endpoint-test")
    assert built.endpoint_id == "endpoint-kw"
    assert endpoint_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-240 agent layer: the agent holds a endpoint
# book for the session, endpoints and views are
# published as session news through the
# checkpoint target (ledger first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held endpoints, the ledger is derived from
# the held endpoints' completeness, the roadmap standing
# is exchanged from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no host. This layer endpoints
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session ledger news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_ENDPOINT_EVENT_TYPES = (
    "endpoint_endpoint", "endpoint_run", "endpoint_view",
    "endpoint_panel", "endpoint_verdict")


def _endpoint_events(store, session_id, host):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == host]


def _write_idecompanions_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / ENDPOINT_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "ide_companions.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestEndpointAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.idecompanions_status()
        assert status["endpoint_records"] == []
        assert status["hosts"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["idecompanions_book"]["title"] == EXAMPLE_TITLE
        assert len(status["idecompanions_book"]["hosts"]) == 3
        assert len(status["idecompanions_book"]["endpoint_records"]) == 5
        assert len(status["idecompanions_book"]["views"]) == 2
        assert len(status["idecompanions_book"]["notes"]) == 2
        assert len(status["idecompanions_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-ide"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["stage"] for e in status["index"]["endpoints"]] == (
            EXAMPLE_STAGES)
        assert status["index"]["gaps"] == [
            "endpoint-bare-endpoint", "endpoint-leaping-endpoint"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["ledger"]["total"] == 5
        assert status["ledger"]["current_endpoint"] == "endpoint-bare-endpoint"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 263
        assert status["roadmap"]["next_slice"] == "M-264"
        assert status["roadmap"]["m240_title"] == "IDE companions II — JetBrains and the generic road"
        assert "held as data alone" in status["rule"]
        assert "endpoint-bare-endpoint" in status["plain_words"]
        assert "The IDE Companions (M-240)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._idecompanions_registry()
        assert agent._idecompanions_registry() is first
        assert agent._idecompanions_store is first
        for name in ("idecompanions_book", "idecompanions_status", "idecompanions_panel",
                     "idecompanions_verdict", "idecompanions_index", "report_idecompanions"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_idecompanions_registry", "idecompanions_book", "idecompanions_status",
            "get_idecompanions_endpoint", "get_idecompanions_view", "get_idecompanions_note",
            "endpoints_for_host", "idecompanions_green",
            "idecompanions_panel", "idecompanions_verdict", "idecompanions_index",
            "register_idecompanions_endpoint", "register_idecompanions_view",
            "view_idecompanions", "register_idecompanions_book",
            "record_idecompanions_book", "report_idecompanions",
            "_publish_idecompanions_record", "_idecompanions_screen",
            "_idecompanions_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.idecompanions_status()
        assert agent.get_idecompanions_endpoint(
            "endpoint-held-endpoint").title == "The held endpoint"
        assert agent.get_idecompanions_view(
            "view-endpoints").view_filter == "all"
        assert agent.get_idecompanions_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.endpoint_id for d in agent.endpoints_for_host(
            "ide-pycharm")] == [
            "endpoint-own-endpoint", "endpoint-bare-endpoint",
            "endpoint-leaping-endpoint"]
        assert [d.endpoint_id for d in agent.idecompanions_green()] == [
            "endpoint-held-endpoint", "endpoint-retried-endpoint", "endpoint-own-endpoint"]
        agent.idecompanions_panel()
        agent.idecompanions_verdict()
        agent.idecompanions_index()
        agent.report_idecompanions()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _ENDPOINT_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_idecompanions_endpoint("endpoint-nope")
        with pytest.raises(KeyError):
            agent.get_idecompanions_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_idecompanions_note("note-nope")
        with pytest.raises(ValueError):
            agent.endpoints_for_host("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_idecompanions_endpoint(_endpoint())
        status = agent.idecompanions_status()
        assert [d["endpoint_id"] for d in status["endpoint_records"]] == ["endpoint-test"]
        assert status["book"]["title"] == "An unheld endpoint book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["stage"] for e in status["index"]["endpoints"]] == [
            "held"]
        assert status["first_note"] is None
        assert "endpoint-test" in status["screen"]
    def test_held_endpoint_never_falls_back_to_the_example(
            self, agent):
        agent.register_idecompanions_endpoint(_endpoint())
        with pytest.raises(KeyError):
            agent.get_idecompanions_endpoint("endpoint-held-endpoint")
        with pytest.raises(KeyError):
            agent.get_idecompanions_view("view-endpoints")
        with pytest.raises(KeyError):
            agent.get_idecompanions_note("note-note-first")
        endpoint = agent.get_idecompanions_endpoint("endpoint-test")
        assert endpoint.title == "A test endpoint"
        assert agent.idecompanions_book().title == (
            "An unheld endpoint book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_idecompanions_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.endpoint_id == "endpoint-held-endpoint"
        status = agent.idecompanions_status()
        assert status["index"]["gaps"] == [
            "endpoint-bare-endpoint", "endpoint-leaping-endpoint"]
        assert status["first_note"]["endpoint_id"] == (
            "endpoint-held-endpoint")
        assert status["first_note"]["stance"] == "note"

class TestEndpointAgentHolding:
    def test_register_endpoint_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_idecompanions_endpoint(_endpoint())
        assert result["endpoint"]["endpoint_id"] == "endpoint-test"
        assert result["record_news"]["type"] == "endpoint_endpoint"
        assert "endpoint-test" in result["screen"]
        events = _endpoint_events(store, session_id, "endpoint_endpoint")
        assert len(events) == 1
        agent.close()

    def test_duplicate_channel_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_idecompanions_endpoint(_endpoint())
        with pytest.raises(ValueError):
            agent.register_idecompanions_endpoint(_endpoint(seq=9))
        with pytest.raises(ValueError):
            agent.register_idecompanions_endpoint(_endpoint(endpoint_id="endpoint-two"))
        events = _endpoint_events(store, session_id, "endpoint_endpoint")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_idecompanions_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_endpoint_events(
            store, session_id, "endpoint_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_idecompanions_endpoint(_endpoint())
        result = agent.view_idecompanions("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "endpoint_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "held"
        assert len(_endpoint_events(
            store, session_id, "endpoint_view")) == 1
        assert len(_endpoint_events(
            store, session_id, "endpoint_panel")) == 1
        assert len(_endpoint_events(
            store, session_id, "endpoint_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_endpoint(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_idecompanions_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "endpoint_run", "endpoint_endpoint", "endpoint_view"]
        assert len(_endpoint_events(
            store, session_id, "endpoint_endpoint")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_idecompanions_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "endpoint_panel"
        assert result["index_record"]["gaps"] == [
            "endpoint-bare-endpoint", "endpoint-leaping-endpoint"]
        with pytest.raises(ValueError):
            agent.record_idecompanions_book()
        assert len(_endpoint_events(
            store, session_id, "endpoint_run")) == 3
        assert len(_endpoint_events(
            store, session_id, "endpoint_endpoint")) == 5
        assert len(_endpoint_events(
            store, session_id, "endpoint_view")) == 2
        agent.close()

    def test_book_from_a_file_is_linked_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_idecompanions_book_file(tmp_path)
        book = load_endpoint_file(path)
        result = agent.record_idecompanions_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_runrt_renders_example_then_held_book_only(self, agent):
        endpoint = agent.report_idecompanions()
        assert endpoint["book"]["title"] == EXAMPLE_TITLE
        assert endpoint["verdict"]["verdict"] == "held"
        assert endpoint["index"]["gaps"] == [
            "endpoint-bare-endpoint", "endpoint-leaping-endpoint"]
        assert "endpoint-held-endpoint" in endpoint["book_text"]
        assert "held - The held endpoint (endpoint-held-endpoint)" in endpoint["index_text"]
        agent.register_idecompanions_endpoint(_endpoint())
        endpoint = agent.report_idecompanions()
        assert endpoint["book"]["title"] == "An unheld endpoint book"
        assert endpoint["panel"] is None
        assert endpoint["verdict"] is None

class TestEndpointTerminalHeading:
    def test_show_endpoint_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/idecompanions")
        assert "The IDE Companions (M-240)" in text
        _, _, text = _slash(agent, "/idecompanions endpoint endpoint-held-endpoint")
        assert "Endpoint: The held endpoint" in text
        _, _, text = _slash(
            agent, "/idecompanions stage held")
        assert "Endpoint: The held endpoint" in text
        _, _, text = _slash(agent, "/idecompanions stage triple endpoint")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/idecompanions host ide-pycharm")
        assert "endpoint-bare-endpoint" in text
        assert "endpoint-held-endpoint" not in text
        _, _, text = _slash(agent, "/idecompanions view view-endpoints")
        assert "filter all" in text
        _, _, text = _slash(agent, "/idecompanions note note-note-first")
        assert "Endpoint note note endpoint-held-endpoint" in text
        _, _, text = _slash(agent, "/idecompanions index")
        assert "Endpoint index" in text
        assert "endpoint-bare-endpoint" in text
        _, _, text = _slash(agent, "/idecompanions panel")
        assert "Endpoint panel under view view-endpoints" in text
        _, _, text = _slash(agent, "/idecompanions verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/idecompanions [show|endpoint <endpoint-id>"
                "|stage <stage>|host <host-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/idecompanions dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/idecompanions endpoint endpoint-nope")
        assert "no endpoint declared" in text
@pytest.fixture()
def endpoint_handler(agent, monkeypatch):
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


def _endpoint_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestEndpointHost:
    def test_show_is_default(self, endpoint_handler, agent):
        endpoint_handler._handle_idecompanions("")
        assert "The IDE Companions (M-240)" in (
            _endpoint_published_text(endpoint_handler))

    def test_endpoint_check_slice_view_note_index_panel_verdict(
            self, endpoint_handler, agent):
        endpoint_handler._handle_idecompanions("endpoint endpoint-held-endpoint")
        assert "Endpoint: The held endpoint" in _endpoint_published_text(
            endpoint_handler)
        endpoint_handler._handle_idecompanions(
            "stage held")
        assert "Endpoint: The held endpoint" in _endpoint_published_text(
            endpoint_handler)
        endpoint_handler._handle_idecompanions("host ide-pycharm")
        assert "endpoint-bare-endpoint" in _endpoint_published_text(
            endpoint_handler)
        endpoint_handler._handle_idecompanions("view view-endpoints")
        assert "filter all" in _endpoint_published_text(endpoint_handler)
        endpoint_handler._handle_idecompanions("note note-note-first")
        assert "Endpoint note note endpoint-held-endpoint" in (
            _endpoint_published_text(endpoint_handler))
        endpoint_handler._handle_idecompanions("index")
        assert "Endpoint index" in _endpoint_published_text(endpoint_handler)
        endpoint_handler._handle_idecompanions("panel")
        assert "Endpoint panel under view" in _endpoint_published_text(
            endpoint_handler)
        endpoint_handler._handle_idecompanions("verdict")
        assert "held" in _endpoint_published_text(endpoint_handler)
    def test_bad_grammar_is_published(
            self, endpoint_handler, agent):
        endpoint_handler._handle_idecompanions("dance party")
        assert USAGE in _endpoint_published_text(endpoint_handler)
        endpoint_handler._handle_idecompanions("endpoint endpoint-nope")
        assert "no endpoint declared" in _endpoint_published_text(
            endpoint_handler)


class TestChatScreenRoutingEndpoint:
    def test_onwell_routes_as_system_host(self, monkeypatch):
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
        screen.handle_command("/idecompanions panel", _FakeLog())
        assert calls == [("/idecompanions", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/idecompanions[/green] - show the IDE companions (M-240)" in (
            text)
        assert ('"/idecompanions": "Usage: /idecompanions | '
                '/idecompanions endpoint <endpoint-id>') in text

class TestEndpointDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.idecompanions_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-endpoints"
        verdict = agent.idecompanions_verdict()
        assert verdict.verdict == "held"
        declared = agent.idecompanions_verdict("view-held")
        assert declared.verdict == "held"
        assert declared.green_shown == 3
        agent.register_idecompanions_endpoint(_endpoint())
        with pytest.raises(ValueError):
            agent.idecompanions_panel()
        with pytest.raises(ValueError):
            agent.idecompanions_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_idecompanions_endpoint(_endpoint(stages=[]))
        result = agent.view_idecompanions("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.idecompanions_index()
        assert [e["stage"] for e in result["index"]["endpoints"]] == (
            EXAMPLE_STAGES)
        assert result["index"]["gaps"] == [
            "endpoint-bare-endpoint", "endpoint-leaping-endpoint"]
        assert "held - The held endpoint (endpoint-held-endpoint)" in (
            result["index_text"])
        endpoint = agent.get_idecompanions_endpoint("endpoint-leaping-endpoint")
        assert endpoint_gaps(endpoint, agent.idecompanions_book()) == (
            "steps from negotiated to held, which the endpoint sequence "
            "does not allow",)
        assert endpoint_green(endpoint, agent.idecompanions_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _ENDPOINT_EVENT_TYPES] == []
        agent.close()
