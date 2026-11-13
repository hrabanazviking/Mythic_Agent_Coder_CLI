"""M-244 Cross-app method - pure-layer tests.

TIER: integration

The pure layer is the tracker, held as data: one
record per resolution, held whole - the bridge it
answers for, named by bridge id, its title, the
steps it walked in walk resolution and the evidence
it carries, held by bridge. The question walk is
explicit - named, sought, resolved, confirmed,
held, with their legal steps held as data -
and a resolution's standing is derived at call
time: a resolution that opens anywhere but named, steps where the sequence does not allow,
carries a bare claim in place of held evidence,
or has not yet named held stands open,
named in its gaps. A resolution stands only for
an active bridge: a resolution naming no held
bridge, or one that is not active, refuses by
name. The resolution's trace - its walked steps
as one line - is derived at call time, and a held
trace record stands current only while it agrees
with the derived trace. The index, panel,
verdict, ledger, trace, resolution and current
resolution are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
question was actually resolved, confirmed or
held live. The shipped example book is held
in a data file, and a loader reads a book from
any file. No charter row names this bridge: the
M-171 TUI charter binds Part VIII alone, and the
M-005 method charter names the whole of Part X
as the part that executes it, both pinned live
below.
"""


from pathlib import Path

import pytest
import yaml

from mythic_agent.core.kista_keykeeper import (
    EXAMPLE_STAGE,
    BARE_CLAIMS,
    HELD_EVIDENCE,
    INDEX_ACTION,
    STAGES,
    CLAIM_KINDS,
    TRANSITIONS,
    BRIDGE_STATES,
    STAGE_FIELDS,
    PLAIN_EXPLANATION,
    RESOLUTION_RESOURCE,
    RESOLUTION_RULE,
    RESOLUTION_SCHEMA,
    RESOLUTION_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    ResolutionRecord,
    IndexResolution,
    BridgeRef,
    NoteRecord,
    ResolutionBook,
    ResolutionIndex,
    ResolutionPanel,
    ResolutionRegistry,
    ResolutionVerdict,
    ResolutionView,
    trace_for_resolution,
    ledger_record,
    book_record,
    build_trace,
    build_book,
    build_resolution,
    build_bridge_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_resolution,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    resolution_for_check,
    resolution_gaps,
    resolution_resolution,
    resolution_record,
    resolution_green,
    resolutions_for_bridge,
    first_note,
    format_book,
    format_resolution,
    format_index,
    format_note,
    format_stage,
    format_panel,
    format_resolution_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    bridge_record,
    load_resolution,
    legal_step,
    load_resolution_file,
    next_stage,
    normalize_stage,
    normalize_claim_kind,
    normalize_bridge_state,
    normalize_stance,
    normalize_view_filter,
    note_for_resolution,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_resolution_args,
    green_resolutions,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_resolutions,
    validate_book,
    validate_resolution,
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
EXAMPLE_TITLE = "Kista key-keeper at the M-244 slice run"
EXAMPLE_STAGES = ["held", "held", "held"]
EXAMPLE_RUN_IDS = (
    "resolution-held-resolution", "resolution-retried-resolution",
    "resolution-own-resolution", "resolution-bare-resolution",
    "resolution-leaping-resolution")
EXAMPLE_TRACE = "named > sought > resolved > confirmed > held"


def _ref(**overrides):
    fields = {
        "bridge_id": "bridge-test",
        "seq": 1,
        "title": "A test bridge",
        "state": "live",
        "detail": "A test bridge reference held as data.",
        "recorded_on": ON,
        "actor": BY,
        "repo": "test bridge",
        "origin_session": "resolution-test",
    }
    fields.update(overrides)
    return build_bridge_ref(fields)


def _resolution(**overrides):
    fields = {
        "resolution_id": "resolution-test",
        "seq": 1,
        "bridge_id": "bridge-test",
        "title": "A test resolution",
        "stages": ["named", "sought", "resolved", "confirmed", "held"],
        "claims": [],
        "detail": "A test resolution held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "repo": "test bridge",
        "origin_session": "resolution-test",
    }
    fields.update(overrides)
    return build_resolution(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "repo": "test bridge",
        "origin_session": "resolution-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "resolution_id": "resolution-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "repo": "test bridge",
        "origin_session": "resolution-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "resolution_id": "resolution-test",
        "trace": "named > sought > resolved > confirmed > held",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "repo": "test bridge",
        "origin_session": "resolution-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(bridges=None, resolutions=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": RESOLUTION_SCHEMA,
        "repo": "M-244",
        "kista_keykeeper": {"title": "A test resolution book"},
        "bridges": [item.to_record() for item in (
            bridges if bridges is not None else [_ref()])],
        "resolution_records": [item.to_record() for item in (
            resolutions if resolutions is not None else [_resolution()])],
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
    return _book(resolutions=[
        _resolution(),
        _resolution(resolution_id="resolution-hidden", seq=2,
               title="A hidden resolution", stages=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_resolution()
    assert book.title == EXAMPLE_TITLE
    assert book.resolution_ids() == EXAMPLE_RUN_IDS
    assert book.bridge_ids() == (
        "bridge-samverk", "bridge-samtal",
        "bridge-github")
    assert [v.view_id for v in book.views] == [
        "view-resolutions", "view-held"]
    assert [m.resolution_id for m in book.notes] == [
        "resolution-held-resolution", "resolution-bare-resolution"]
    assert [a.resolution_id for a in book.traces] == ["resolution-held-resolution"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-kista"
    assert panel.as_of == "2026-11-11"
    assert [row.item_id for row in panel.rows] == list(book.resolution_ids())
    derived = derive_panel(book, "view-resolutions")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-resolutions").verdict == "held"
    assert derive_verdict(book, "view-resolutions").green_shown == 3
    assert derive_verdict(book, "view-held").verdict == "held"
    assert derive_verdict(book, "view-held").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / RESOLUTION_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == RESOLUTION_SCHEMA
    assert raw["repo"] == "M-244"
    assert "verdict" not in raw
    assert "resolution_index" not in raw
    assert "ledger" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-244")]
    assert slice_.title == "Kista as the key-keeper (with M-032)"
    assert slice_.part == 10
    assert "every bridge's credential resolves through Kista" in slice_.summary
    assert "a bridge without a key asks once" in slice_.summary
    assert RESOLUTION_SLICE == "M-244"

def test_charter_rows_do_not_name_m244():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-244" not in owners
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
    assert BRIDGE_STATES == ("live", "dormant")
    assert STAGES == ("named", "sought", "resolved", "confirmed", "held")
    assert HELD_EVIDENCE == ("bridge_ref", "key_ref", "vault_ref", "grant_ref", "scope_ref", "custody_ref")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_KINDS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["confirmed"] == ("named", "held")
    assert TRANSITIONS["held"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_STAGE == "held"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_bridge_state("LIVE") == "live"
    assert normalize_stage("RESOLVED") == "resolved"
    assert normalize_claim_kind("FEELING") == "feeling"
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    with pytest.raises(ValueError):
        normalize_bridge_state("blessed")
    with pytest.raises(ValueError):
        normalize_stage("polish")
    with pytest.raises(ValueError):
        normalize_claim_kind("weather")
    assert legal_step("resolved", "confirmed") is True
    assert legal_step("sought", "held") is False
    assert legal_step("held", "named") is False
    assert next_stage("named") == "sought"
    assert next_stage("resolved") == "confirmed"
    assert next_stage("confirmed", failed=True) == "named"
    assert next_stage("confirmed") == "held"
    assert next_stage("held") is None
    assert "held as data alone" in RESOLUTION_RULE
    assert "resolution sequence" in RESOLUTION_RULE
    assert "M-244" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /kistakeykeeper")

def test_shipped_book_judged_honestly_as_data():
    book = load_resolution()
    opening = book.resolution_for("resolution-held-resolution")
    assert resolution_green(opening, book) is True
    assert resolution_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Resolution: The held resolution",
        "Bridge: bridge-samverk",
        "Stage: held",
        "Claims: bridge_ref")
    asking = book.resolution_for("resolution-bare-resolution")
    assert resolution_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert resolution_green(asking, book) is False
    skipping = book.resolution_for("resolution-leaping-resolution")
    assert resolution_gaps(skipping, book) == (
        "steps from sought to held, which the resolution sequence "
        "does not allow",)
    assert [g.resolution_id for g in green_resolutions(book)] == [
        "resolution-held-resolution", "resolution-retried-resolution", "resolution-own-resolution"]
    index = derive_index(book)
    assert [e.stage for e in index.resolutions] == EXAMPLE_STAGES
    assert index.gaps == ("resolution-bare-resolution", "resolution-leaping-resolution")
    assert resolution_for_check(book, EXAMPLE_STAGE).resolution_id == (
        "resolution-held-resolution")
    assert resolution_for_check(book, "triple resolution") is None
    assert transition_breaks(book) == (
        "resolution-leaping-resolution: sought > held",)
    assert [g.resolution_id for g in resolution_resolution(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "resolution-held-resolution") == EXAMPLE_TRACE
    assert trace_current(book, "resolution-held-resolution") is True
    assert trace_current(book, "resolution-retried-resolution") is False
    assert trace_for_resolution(
        book, "resolution-held-resolution").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_resolution(
        book, "resolution-held-resolution", "note").note_id == (
            "note-note-first")
    assert note_for_resolution(book, "resolution-nope") is None
    assert current_resolution(book).resolution_id == "resolution-bare-resolution"
    ledger = ledger_record(book)
    assert ledger["standings"] == [
        {"standing": "complete", "resolution_records": 3},
        {"standing": "open", "resolution_records": 2}]
    assert ledger["total"] == 5
    assert ledger["current_resolution"] == "resolution-bare-resolution"
    assert ledger["traces"] == [
        {"resolution_id": "resolution-held-resolution", "trace": "current"},
        {"resolution_id": "resolution-retried-resolution", "trace": "unheld"},
        {"resolution_id": "resolution-own-resolution", "trace": "unheld"},
        {"resolution_id": "resolution-bare-resolution", "trace": "unheld"},
        {"resolution_id": "resolution-leaping-resolution", "trace": "unheld"}]
    assert ledger["breaks"] == ["resolution-leaping-resolution: sought > held"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 261
    assert citizen["next_slice"] == "M-262"
    assert citizen["m244_title"] == "Kista as the key-keeper (with M-032)"
    assert citizen["m244_part"] == 10
    assert citizen["m244_status"] == "done"

def test_resolution_record_round_trips():
    resolution = _resolution()
    assert validate_resolution(resolution) is resolution
    rebuilt = build_resolution(resolution.to_record())
    assert rebuilt == resolution
    assert rebuilt.item_id == "resolution-test"
    assert rebuilt.stage == "held"
    record = resolution_record(resolution)
    assert record["type"] == "resolution_resolution"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert bridge_record(ref)["type"] == "resolution_run"
    assert bridge_record(ref)["state"] == "live"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _resolution(stages=[])
    assert resolution_gaps(silent) == (
        "has passed through no step: the resolution has not started",)
    assert resolution_green(silent) is False
    walking = _resolution(stages=["named", "sought"])
    assert resolution_gaps(walking) == (
        "has not reached held: the resolution stands at sought",)
    assert walking.stage == "sought"
    sideways = _resolution(stages=["sought", "resolved", "confirmed", "held"])
    assert resolution_gaps(sideways) == (
        "opens at sought, not at named: the resolution opens "
        "with the reflection",)
    repaired = _resolution(stages=["named", "sought", "resolved", "confirmed", "named", "sought", "resolved", "confirmed", "held"])
    assert resolution_gaps(repaired) == ()
    assert resolution_green(repaired) is True
    with pytest.raises(ValueError):
        _resolution(stages=[42])
    with pytest.raises(ValueError):
        _resolution(stages="inspect as a bare string")
    with pytest.raises(ValueError):
        _resolution(stages=["named", "polish"])
    with pytest.raises(ValueError):
        _resolution(claims=["weather"])
    with pytest.raises(ValueError):
        _resolution(claims="bridge_ref")
    none_resolution = _resolution(stages=None, claims=None)
    assert none_resolution.stages == ()
    assert none_resolution.claims == ()

def test_custody_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "resolutions", "coverage", "current_resolution",
                "ledger", "resolution"):
        fields = _resolution().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_resolution(fields)
    fields = _resolution().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_resolution(fields)


def test_custody_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _resolution().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_resolution(fields)


def test_resolution_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _resolution(title="")
    with pytest.raises(ValueError):
        _resolution(bridge_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "named > sought > resolved > confirmed > held"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_resolutions_own_fields():
    resolution = _resolution(claims=["bridge_ref"])
    assert plain_lines(resolution) == (
        "Resolution: A test resolution",
        "Bridge: bridge-test",
        "Stage: held",
        "Claims: bridge_ref")
    segment = segment_of(resolution)
    assert segment.startswith("resolution-test: A test resolution")
    assert "stage: 'held'" in segment
    assert "gaps: none" in segment
    assert plain_words(resolution).startswith(
        "A test resolution - from bridge-test")

def test_red_resolutions_stand_named_in_their_gaps():
    asking = _resolution(claims=["feeling", "bridge_ref", "summary"])
    assert resolution_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert resolution_green(asking) is False
    skipping = _resolution(stages=["named", "sought", "held"])
    assert resolution_gaps(skipping) == (
        "steps from sought to held, which the resolution sequence "
        "does not allow",)
    book = _book(resolutions=[
        _resolution(),
        _resolution(resolution_id="resolution-skipping", seq=2,
             stages=["named", "sought", "held"]),
    ])
    assert transition_breaks(book) == (
        "resolution-skipping: sought > held",)
    assert current_resolution(book).resolution_id == "resolution-skipping"
    assert [g.resolution_id for g in resolution_resolution(book)] == [
        "resolution-test", "resolution-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "resolution_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "resolution_note"
    assert record["resolution_id"] == "resolution-test"
    assert view_plain_words(view) == "View view-test: shows all resolutions."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_resolutions_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.stage for e in index.resolutions] == ["held"]
    assert index.resolutions[0] == IndexResolution(
        stage="held",
        resolution_id="resolution-test", title="A test resolution")
    assert index.gaps == ("resolution-hidden",)
    record = index_record(book)
    assert record["type"] == "resolution_index"
    assert record["gaps"] == ["resolution-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "resolution_book"

def test_check_target_reaches_its_resolution_and_an_unheld_target_reaches_nothing():
    book = load_resolution()
    assert resolution_for_check(book, "held").resolution_id == (
        "resolution-held-resolution")
    assert resolution_for_check(book, "") is None
    assert resolution_for_check(book, None) is None
    assert resolution_for_check(book, "not held at all") is None
    text = format_stage(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_resolution()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Resolution note note resolution-held-resolution" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").resolution_id == "resolution-test"
    assert note_for_resolution(book, "resolution-test").note_id == "note-test"
    assert note_for_resolution(book, "resolution-test", "praise") is None
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
    row = build_row(None, _resolution(), book)
    assert row.standing == "complete"
    assert validate_row(row, _resolution(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_resolutions():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "resolution_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "held"
    empty_book = _book(resolutions=[_resolution(stages=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(ResolutionVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_resolutions():
    book = load_resolution()
    assert [g.resolution_id for g in shown_resolutions(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.resolution_id for g in shown_resolutions(book, "view-held")] == [
        "resolution-held-resolution", "resolution-retried-resolution", "resolution-own-resolution"]
    assert [g.resolution_id for g in resolutions_for_bridge(
        book, "bridge-samtal")] == [
            "resolution-own-resolution", "resolution-bare-resolution",
            "resolution-leaping-resolution"]
    assert resolutions_for_bridge(book, "bridge-nope") == ()
    assert current_resolution(_mixed_book()).resolution_id == "resolution-hidden"
    assert current_resolution(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "resolution-test") == (
        "named > sought > resolved > confirmed > held")
    assert trace_current(stale, "resolution-test") is False
    assert ledger_record(stale)["traces"] == [
        {"resolution_id": "resolution-test", "trace": "stale"}]

def test_key_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(resolutions=[_resolution(), _resolution(seq=2)])
    with pytest.raises(ValueError):
        _book(resolutions=[_resolution(), _resolution(resolution_id="resolution-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(resolutions=[_resolution(bridge_id="bridge-nope")])
    with pytest.raises(ValueError):
        _book(bridges=[_ref(), _ref(
            bridge_id="bridge-cold", seq=2, state="dormant")],
            resolutions=[_resolution(bridge_id="bridge-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(bridge_id="bridge-nope")])
    fields = {
        "schema": RESOLUTION_SCHEMA, "repo": "M-244",
        "kista_keykeeper": {"title": "A resolved book"},
        "bridges": [_ref().to_record()],
        "resolution_records": [_resolution().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "held"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_resolution"] = "resolution-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_resolution")
    fields["trace"] = "resolution-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / RESOLUTION_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "kista_keykeeper.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_resolution_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.resolution_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = ResolutionRegistry()
    assert registry.title() is None
    registry.register_bridge_ref(_ref())
    registry.register_resolution(_resolution())
    registry.register_view(_view())
    assert [g.resolution_id for g in registry.list_resolutions()] == ["resolution-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_resolution("resolution-test").title == "A test resolution"
    assert registry.get_slice("bridge-test").state == "live"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("resolution-test").resolution_id == "resolution-test"
    with pytest.raises(ValueError):
        registry.register_resolution(_resolution(seq=9))
    with pytest.raises(ValueError):
        registry.register_resolution(_resolution(resolution_id="resolution-two"))
    with pytest.raises(KeyError):
        registry.get_resolution("resolution-nope")
    assert registry.book().title == "An unheld resolution book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = ResolutionRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test resolution book"
    assert registry.title() == "A test resolution book"
    assert len(registry.list_resolutions()) == 2
    other = ResolutionRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    resolution = _resolution()
    assert "A test resolution" in plain_words(resolution)
    assert panel_plain_words(_mixed_book()).startswith(
        "The resolution book holds 2 resolutions")
    assert verdict_plain_words(_mixed_book()) == (
        "The resolutions stand held: 1 of 2 shown resolutions stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green resolutions; red, "
        "named in its gaps: resolution-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_resolution(resolution)
    assert "Resolution: A test resolution" in text
    assert "stands complete" in text
    text = format_resolution(_resolution(stages=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The Kista Key-keeper (M-244) - A test resolution book" in book_text
    assert "resolution-hidden" in format_book(_mixed_book(), "bridge-test")
    assert "Resolution panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "held - A test resolution (resolution-test)" in index_text
    assert "resolution-hidden" in index_text
    screen = format_resolution_screen()
    assert "The Kista Key-keeper (M-244)" in screen
    assert "resolution-bare-resolution" in screen

def test_parse_args_well_and_loader_targets():
    assert parse_resolution_args("") == ("show", None)
    assert parse_resolution_args(None) == ("show", None)
    assert parse_resolution_args("show") == ("show", None)
    assert parse_resolution_args("resolution resolution-test") == (
        "resolution", "resolution-test")
    assert parse_resolution_args("stage held") == (
        "stage", "held")
    assert parse_resolution_args("bridge bridge-test") == (
        "bridge", "bridge-test")
    assert parse_resolution_args("view view-test") == ("view", "view-test")
    assert parse_resolution_args("note note-test") == ("note", "note-test")
    assert parse_resolution_args("index") == ("index", None)
    assert parse_resolution_args("panel") == ("panel", None)
    assert parse_resolution_args("verdict") == ("verdict", None)
    for bad in ("dance", "resolution", "stage", "bridge", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_resolution_args(bad)
    ledger = ledger_record()
    assert ledger["type"] == "resolution_well"
    assert ledger["total"] == 5
    assert ledger["current_resolution"] == "resolution-bare-resolution"
    book = load_resolution({
        "schema": RESOLUTION_SCHEMA, "repo": "M-244",
        "kista_keykeeper": {"title": "A resolved book"},
        "bridges": [_ref().to_record()],
        "resolution_records": [_resolution().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, ResolutionBook)
    assert book.title == "A resolved book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_resolution({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_resolution({"repo": "M-999"})
    built = build_resolution(
        resolution_id="resolution-kw", seq=3, bridge_id="bridge-test",
        title="Kw Resolution", stages=["named", "sought", "resolved", "confirmed", "held"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        repo="test bridge", origin_session="resolution-test")
    assert built.resolution_id == "resolution-kw"
    assert resolution_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-244 agent layer: the agent holds a resolution
# book for the session, resolutions and views are
# published as session news through the
# checkpoint target (ledger first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held resolutions, the ledger is derived from
# the held resolutions' completeness, the roadmap standing
# is confirmed from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no bridge. This layer resolutions
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session ledger news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_RESOLUTION_EVENT_TYPES = (
    "resolution_resolution", "resolution_run", "resolution_view",
    "resolution_panel", "resolution_verdict")


def _resolution_events(store, session_id, bridge):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == bridge]


def _write_kistakeykeeper_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / RESOLUTION_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "kista_keykeeper.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestResolutionAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.kistakeykeeper_status()
        assert status["resolution_records"] == []
        assert status["bridges"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["kistakeykeeper_book"]["title"] == EXAMPLE_TITLE
        assert len(status["kistakeykeeper_book"]["bridges"]) == 3
        assert len(status["kistakeykeeper_book"]["resolution_records"]) == 5
        assert len(status["kistakeykeeper_book"]["views"]) == 2
        assert len(status["kistakeykeeper_book"]["notes"]) == 2
        assert len(status["kistakeykeeper_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-kista"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["stage"] for e in status["index"]["resolutions"]] == (
            EXAMPLE_STAGES)
        assert status["index"]["gaps"] == [
            "resolution-bare-resolution", "resolution-leaping-resolution"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["ledger"]["total"] == 5
        assert status["ledger"]["current_resolution"] == "resolution-bare-resolution"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 261
        assert status["roadmap"]["next_slice"] == "M-262"
        assert status["roadmap"]["m244_title"] == "Kista as the key-keeper (with M-032)"
        assert "held as data alone" in status["rule"]
        assert "resolution-bare-resolution" in status["plain_words"]
        assert "The Kista Key-keeper (M-244)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._kistakeykeeper_registry()
        assert agent._kistakeykeeper_registry() is first
        assert agent._kistakeykeeper_store is first
        for name in ("kistakeykeeper_book", "kistakeykeeper_status", "kistakeykeeper_panel",
                     "kistakeykeeper_verdict", "kistakeykeeper_index", "report_kistakeykeeper"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_kistakeykeeper_registry", "kistakeykeeper_book", "kistakeykeeper_status",
            "get_kistakeykeeper_resolution", "get_kistakeykeeper_view", "get_kistakeykeeper_note",
            "resolutions_for_bridge", "kistakeykeeper_green",
            "kistakeykeeper_panel", "kistakeykeeper_verdict", "kistakeykeeper_index",
            "register_kistakeykeeper_resolution", "register_kistakeykeeper_view",
            "view_kistakeykeeper", "register_kistakeykeeper_book",
            "record_kistakeykeeper_book", "report_kistakeykeeper",
            "_publish_kistakeykeeper_record", "_kistakeykeeper_screen",
            "_kistakeykeeper_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.kistakeykeeper_status()
        assert agent.get_kistakeykeeper_resolution(
            "resolution-held-resolution").title == "The held resolution"
        assert agent.get_kistakeykeeper_view(
            "view-resolutions").view_filter == "all"
        assert agent.get_kistakeykeeper_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.resolution_id for d in agent.resolutions_for_bridge(
            "bridge-samtal")] == [
            "resolution-own-resolution", "resolution-bare-resolution",
            "resolution-leaping-resolution"]
        assert [d.resolution_id for d in agent.kistakeykeeper_green()] == [
            "resolution-held-resolution", "resolution-retried-resolution", "resolution-own-resolution"]
        agent.kistakeykeeper_panel()
        agent.kistakeykeeper_verdict()
        agent.kistakeykeeper_index()
        agent.report_kistakeykeeper()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _RESOLUTION_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_kistakeykeeper_resolution("resolution-nope")
        with pytest.raises(KeyError):
            agent.get_kistakeykeeper_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_kistakeykeeper_note("note-nope")
        with pytest.raises(ValueError):
            agent.resolutions_for_bridge("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_kistakeykeeper_resolution(_resolution())
        status = agent.kistakeykeeper_status()
        assert [d["resolution_id"] for d in status["resolution_records"]] == ["resolution-test"]
        assert status["book"]["title"] == "An unheld resolution book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["stage"] for e in status["index"]["resolutions"]] == [
            "held"]
        assert status["first_note"] is None
        assert "resolution-test" in status["screen"]
    def test_held_resolution_never_falls_back_to_the_example(
            self, agent):
        agent.register_kistakeykeeper_resolution(_resolution())
        with pytest.raises(KeyError):
            agent.get_kistakeykeeper_resolution("resolution-held-resolution")
        with pytest.raises(KeyError):
            agent.get_kistakeykeeper_view("view-resolutions")
        with pytest.raises(KeyError):
            agent.get_kistakeykeeper_note("note-note-first")
        resolution = agent.get_kistakeykeeper_resolution("resolution-test")
        assert resolution.title == "A test resolution"
        assert agent.kistakeykeeper_book().title == (
            "An unheld resolution book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_kistakeykeeper_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.resolution_id == "resolution-held-resolution"
        status = agent.kistakeykeeper_status()
        assert status["index"]["gaps"] == [
            "resolution-bare-resolution", "resolution-leaping-resolution"]
        assert status["first_note"]["resolution_id"] == (
            "resolution-held-resolution")
        assert status["first_note"]["stance"] == "note"

class TestResolutionAgentHolding:
    def test_register_resolution_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_kistakeykeeper_resolution(_resolution())
        assert result["resolution"]["resolution_id"] == "resolution-test"
        assert result["record_news"]["type"] == "resolution_resolution"
        assert "resolution-test" in result["screen"]
        events = _resolution_events(store, session_id, "resolution_resolution")
        assert len(events) == 1
        agent.close()

    def test_duplicate_custody_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_kistakeykeeper_resolution(_resolution())
        with pytest.raises(ValueError):
            agent.register_kistakeykeeper_resolution(_resolution(seq=9))
        with pytest.raises(ValueError):
            agent.register_kistakeykeeper_resolution(_resolution(resolution_id="resolution-two"))
        events = _resolution_events(store, session_id, "resolution_resolution")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_kistakeykeeper_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_resolution_events(
            store, session_id, "resolution_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_kistakeykeeper_resolution(_resolution())
        result = agent.view_kistakeykeeper("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "resolution_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "held"
        assert len(_resolution_events(
            store, session_id, "resolution_view")) == 1
        assert len(_resolution_events(
            store, session_id, "resolution_panel")) == 1
        assert len(_resolution_events(
            store, session_id, "resolution_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_resolution(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_kistakeykeeper_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "resolution_run", "resolution_resolution", "resolution_view"]
        assert len(_resolution_events(
            store, session_id, "resolution_resolution")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_kistakeykeeper_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "resolution_panel"
        assert result["index_record"]["gaps"] == [
            "resolution-bare-resolution", "resolution-leaping-resolution"]
        with pytest.raises(ValueError):
            agent.record_kistakeykeeper_book()
        assert len(_resolution_events(
            store, session_id, "resolution_run")) == 3
        assert len(_resolution_events(
            store, session_id, "resolution_resolution")) == 5
        assert len(_resolution_events(
            store, session_id, "resolution_view")) == 2
        agent.close()

    def test_book_from_a_file_is_reached_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_kistakeykeeper_book_file(tmp_path)
        book = load_resolution_file(path)
        result = agent.record_kistakeykeeper_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_runrt_renders_example_then_held_book_only(self, agent):
        resolution = agent.report_kistakeykeeper()
        assert resolution["book"]["title"] == EXAMPLE_TITLE
        assert resolution["verdict"]["verdict"] == "held"
        assert resolution["index"]["gaps"] == [
            "resolution-bare-resolution", "resolution-leaping-resolution"]
        assert "resolution-held-resolution" in resolution["book_text"]
        assert "held - The held resolution (resolution-held-resolution)" in resolution["index_text"]
        agent.register_kistakeykeeper_resolution(_resolution())
        resolution = agent.report_kistakeykeeper()
        assert resolution["book"]["title"] == "An unheld resolution book"
        assert resolution["panel"] is None
        assert resolution["verdict"] is None

class TestResolutionTerminalHeading:
    def test_show_resolution_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/kistakeykeeper")
        assert "The Kista Key-keeper (M-244)" in text
        _, _, text = _slash(agent, "/kistakeykeeper resolution resolution-held-resolution")
        assert "Resolution: The held resolution" in text
        _, _, text = _slash(
            agent, "/kistakeykeeper stage held")
        assert "Resolution: The held resolution" in text
        _, _, text = _slash(agent, "/kistakeykeeper stage triple resolution")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/kistakeykeeper bridge bridge-samtal")
        assert "resolution-bare-resolution" in text
        assert "resolution-held-resolution" not in text
        _, _, text = _slash(agent, "/kistakeykeeper view view-resolutions")
        assert "filter all" in text
        _, _, text = _slash(agent, "/kistakeykeeper note note-note-first")
        assert "Resolution note note resolution-held-resolution" in text
        _, _, text = _slash(agent, "/kistakeykeeper index")
        assert "Resolution index" in text
        assert "resolution-bare-resolution" in text
        _, _, text = _slash(agent, "/kistakeykeeper panel")
        assert "Resolution panel under view view-resolutions" in text
        _, _, text = _slash(agent, "/kistakeykeeper verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/kistakeykeeper [show|resolution <resolution-id>"
                "|stage <stage>|bridge <bridge-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/kistakeykeeper dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/kistakeykeeper resolution resolution-nope")
        assert "no resolution named" in text
@pytest.fixture()
def resolution_handler(agent, monkeypatch):
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


def _resolution_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestResolutionSource:
    def test_show_is_default(self, resolution_handler, agent):
        resolution_handler._handle_kistakeykeeper("")
        assert "The Kista Key-keeper (M-244)" in (
            _resolution_published_text(resolution_handler))

    def test_resolution_check_slice_view_note_index_panel_verdict(
            self, resolution_handler, agent):
        resolution_handler._handle_kistakeykeeper("resolution resolution-held-resolution")
        assert "Resolution: The held resolution" in _resolution_published_text(
            resolution_handler)
        resolution_handler._handle_kistakeykeeper(
            "stage held")
        assert "Resolution: The held resolution" in _resolution_published_text(
            resolution_handler)
        resolution_handler._handle_kistakeykeeper("bridge bridge-samtal")
        assert "resolution-bare-resolution" in _resolution_published_text(
            resolution_handler)
        resolution_handler._handle_kistakeykeeper("view view-resolutions")
        assert "filter all" in _resolution_published_text(resolution_handler)
        resolution_handler._handle_kistakeykeeper("note note-note-first")
        assert "Resolution note note resolution-held-resolution" in (
            _resolution_published_text(resolution_handler))
        resolution_handler._handle_kistakeykeeper("index")
        assert "Resolution index" in _resolution_published_text(resolution_handler)
        resolution_handler._handle_kistakeykeeper("panel")
        assert "Resolution panel under view" in _resolution_published_text(
            resolution_handler)
        resolution_handler._handle_kistakeykeeper("verdict")
        assert "held" in _resolution_published_text(resolution_handler)
    def test_bad_grammar_is_published(
            self, resolution_handler, agent):
        resolution_handler._handle_kistakeykeeper("dance party")
        assert USAGE in _resolution_published_text(resolution_handler)
        resolution_handler._handle_kistakeykeeper("resolution resolution-nope")
        assert "no resolution named" in _resolution_published_text(
            resolution_handler)


class TestChatScreenRoutingResolution:
    def test_onwell_routes_as_system_bridge(self, monkeypatch):
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
        screen.handle_command("/kistakeykeeper panel", _FakeLog())
        assert calls == [("/kistakeykeeper", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/kistakeykeeper[/green] - show the Kista key-keeper (M-244)" in (
            text)
        assert ('"/kistakeykeeper": "Usage: /kistakeykeeper | '
                '/kistakeykeeper resolution <resolution-id>') in text

class TestResolutionDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.kistakeykeeper_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-resolutions"
        verdict = agent.kistakeykeeper_verdict()
        assert verdict.verdict == "held"
        named = agent.kistakeykeeper_verdict("view-held")
        assert named.verdict == "held"
        assert named.green_shown == 3
        agent.register_kistakeykeeper_resolution(_resolution())
        with pytest.raises(ValueError):
            agent.kistakeykeeper_panel()
        with pytest.raises(ValueError):
            agent.kistakeykeeper_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_kistakeykeeper_resolution(_resolution(stages=[]))
        result = agent.view_kistakeykeeper("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.kistakeykeeper_index()
        assert [e["stage"] for e in result["index"]["resolutions"]] == (
            EXAMPLE_STAGES)
        assert result["index"]["gaps"] == [
            "resolution-bare-resolution", "resolution-leaping-resolution"]
        assert "held - The held resolution (resolution-held-resolution)" in (
            result["index_text"])
        resolution = agent.get_kistakeykeeper_resolution("resolution-leaping-resolution")
        assert resolution_gaps(resolution, agent.kistakeykeeper_book()) == (
            "steps from sought to held, which the resolution sequence "
            "does not allow",)
        assert resolution_green(resolution, agent.kistakeykeeper_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _RESOLUTION_EVENT_TYPES] == []
        agent.close()
