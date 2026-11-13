"""M-241 Cross-app method - pure-layer tests.

TIER: integration

The pure layer is the tracker, held as data: one
record per importer, held whole - the source it
answers for, detected by source id, its title, the
steps it walked in walk importer and the evidence
it carries, held by source. The question walk is
explicit - detected, mapped, converted, imported,
held, with their legal steps held as data -
and a importer's standing is derived at call
time: a importer that opens anywhere but detected, steps where the sequence does not allow,
carries a bare claim in place of held evidence,
or has not yet detected held stands open,
detected in its gaps. A importer stands only for
an active source: a importer naming no held
source, or one that is not active, refuses by
name. The importer's trace - its walked steps
as one line - is derived at call time, and a held
trace record stands current only while it agrees
with the derived trace. The index, panel,
verdict, ledger, trace, importer and current
importer are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
question was actually answered, imported or
held live. The shipped example book is held
in a data file, and a loader reads a book from
any file. No charter row names this source: the
M-171 TUI charter binds Part VIII alone, and the
M-005 method charter names the whole of Part X
as the part that executes it, both pinned live
below.
"""


from pathlib import Path

import pytest
import yaml

from mythic_agent.core.rival_importers import (
    EXAMPLE_STAGE,
    BARE_CLAIMS,
    HELD_EVIDENCE,
    INDEX_ACTION,
    STAGES,
    CLAIM_KINDS,
    TRANSITIONS,
    SOURCE_STATES,
    STAGE_FIELDS,
    PLAIN_EXPLANATION,
    IMPORTER_RESOURCE,
    IMPORTER_RULE,
    IMPORTER_SCHEMA,
    IMPORTER_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    ImporterRecord,
    IndexImporter,
    SourceRef,
    NoteRecord,
    ImporterBook,
    ImporterIndex,
    ImporterPanel,
    ImporterRegistry,
    ImporterVerdict,
    ImporterView,
    trace_for_importer,
    ledger_record,
    book_record,
    build_trace,
    build_book,
    build_importer,
    build_source_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_importer,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    importer_for_check,
    importer_gaps,
    importer_importer,
    importer_record,
    importer_green,
    importers_for_source,
    first_note,
    format_book,
    format_importer,
    format_index,
    format_note,
    format_stage,
    format_panel,
    format_importer_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    source_record,
    load_importer,
    legal_step,
    load_importer_file,
    next_stage,
    normalize_stage,
    normalize_claim_kind,
    normalize_source_state,
    normalize_stance,
    normalize_view_filter,
    note_for_importer,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_importer_args,
    green_importers,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_importers,
    validate_book,
    validate_importer,
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
EXAMPLE_TITLE = "Rival importers at the M-241 slice run"
EXAMPLE_STAGES = ["held", "held", "held"]
EXAMPLE_RUN_IDS = (
    "importer-held-importer", "importer-retried-importer",
    "importer-own-importer", "importer-bare-importer",
    "importer-leaping-importer")
EXAMPLE_TRACE = "detected > mapped > converted > imported > held"


def _ref(**overrides):
    fields = {
        "source_id": "source-test",
        "seq": 1,
        "title": "A test source",
        "state": "live",
        "detail": "A test source reference held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "importer-test",
    }
    fields.update(overrides)
    return build_source_ref(fields)


def _importer(**overrides):
    fields = {
        "importer_id": "importer-test",
        "seq": 1,
        "source_id": "source-test",
        "title": "A test importer",
        "stages": ["detected", "mapped", "converted", "imported", "held"],
        "claims": [],
        "detail": "A test importer held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "importer-test",
    }
    fields.update(overrides)
    return build_importer(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "importer-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "importer_id": "importer-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "importer-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "importer_id": "importer-test",
        "trace": "detected > mapped > converted > imported > held",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "importer-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(sources=None, importers=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": IMPORTER_SCHEMA,
        "source": "M-241",
        "rival_importers": {"title": "A test importer book"},
        "sources": [item.to_record() for item in (
            sources if sources is not None else [_ref()])],
        "importer_records": [item.to_record() for item in (
            importers if importers is not None else [_importer()])],
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
    return _book(importers=[
        _importer(),
        _importer(importer_id="importer-hidden", seq=2,
               title="A hidden importer", stages=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_importer()
    assert book.title == EXAMPLE_TITLE
    assert book.importer_ids() == EXAMPLE_RUN_IDS
    assert book.source_ids() == (
        "rival-claude", "rival-codex",
        "rival-opencode")
    assert [v.view_id for v in book.views] == [
        "view-importers", "view-held"]
    assert [m.importer_id for m in book.notes] == [
        "importer-held-importer", "importer-bare-importer"]
    assert [a.importer_id for a in book.traces] == ["importer-held-importer"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-rival"
    assert panel.as_of == "2026-11-11"
    assert [row.item_id for row in panel.rows] == list(book.importer_ids())
    derived = derive_panel(book, "view-importers")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-importers").verdict == "held"
    assert derive_verdict(book, "view-importers").green_shown == 3
    assert derive_verdict(book, "view-held").verdict == "held"
    assert derive_verdict(book, "view-held").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / IMPORTER_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == IMPORTER_SCHEMA
    assert raw["source"] == "M-241"
    assert "verdict" not in raw
    assert "importer_index" not in raw
    assert "ledger" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-241")]
    assert slice_.title == "Rival importers"
    assert slice_.part == 10
    assert "settings, commands, instruction files, and MCP configs imported from" in slice_.summary
    assert "arriving users keep their habits" in slice_.summary
    assert IMPORTER_SLICE == "M-241"

def test_charter_rows_do_not_name_m241():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-241" not in owners
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
    assert SOURCE_STATES == ("live", "dormant")
    assert STAGES == ("detected", "mapped", "converted", "imported", "held")
    assert HELD_EVIDENCE == ("settings_ref", "commands_ref", "instructions_ref", "mcp_ref", "habits_ref", "layout_ref")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_KINDS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["imported"] == ("detected", "held")
    assert TRANSITIONS["held"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_STAGE == "held"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_source_state("LIVE") == "live"
    assert normalize_stage("CONVERTED") == "converted"
    assert normalize_claim_kind("FEELING") == "feeling"
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    with pytest.raises(ValueError):
        normalize_source_state("blessed")
    with pytest.raises(ValueError):
        normalize_stage("polish")
    with pytest.raises(ValueError):
        normalize_claim_kind("weather")
    assert legal_step("converted", "imported") is True
    assert legal_step("mapped", "held") is False
    assert legal_step("held", "detected") is False
    assert next_stage("detected") == "mapped"
    assert next_stage("converted") == "imported"
    assert next_stage("imported", failed=True) == "detected"
    assert next_stage("imported") == "held"
    assert next_stage("held") is None
    assert "held as data alone" in IMPORTER_RULE
    assert "importer sequence" in IMPORTER_RULE
    assert "M-241" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /rivalimporters")

def test_shipped_book_judged_honestly_as_data():
    book = load_importer()
    opening = book.importer_for("importer-held-importer")
    assert importer_green(opening, book) is True
    assert importer_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Importer: The held importer",
        "Source: rival-claude",
        "Stage: held",
        "Claims: settings_ref")
    asking = book.importer_for("importer-bare-importer")
    assert importer_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert importer_green(asking, book) is False
    skipping = book.importer_for("importer-leaping-importer")
    assert importer_gaps(skipping, book) == (
        "steps from mapped to held, which the importer sequence "
        "does not allow",)
    assert [g.importer_id for g in green_importers(book)] == [
        "importer-held-importer", "importer-retried-importer", "importer-own-importer"]
    index = derive_index(book)
    assert [e.stage for e in index.importers] == EXAMPLE_STAGES
    assert index.gaps == ("importer-bare-importer", "importer-leaping-importer")
    assert importer_for_check(book, EXAMPLE_STAGE).importer_id == (
        "importer-held-importer")
    assert importer_for_check(book, "triple importer") is None
    assert transition_breaks(book) == (
        "importer-leaping-importer: mapped > held",)
    assert [g.importer_id for g in importer_importer(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "importer-held-importer") == EXAMPLE_TRACE
    assert trace_current(book, "importer-held-importer") is True
    assert trace_current(book, "importer-retried-importer") is False
    assert trace_for_importer(
        book, "importer-held-importer").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_importer(
        book, "importer-held-importer", "note").note_id == (
            "note-note-first")
    assert note_for_importer(book, "importer-nope") is None
    assert current_importer(book).importer_id == "importer-bare-importer"
    ledger = ledger_record(book)
    assert ledger["standings"] == [
        {"standing": "complete", "importer_records": 3},
        {"standing": "open", "importer_records": 2}]
    assert ledger["total"] == 5
    assert ledger["current_importer"] == "importer-bare-importer"
    assert ledger["traces"] == [
        {"importer_id": "importer-held-importer", "trace": "current"},
        {"importer_id": "importer-retried-importer", "trace": "unheld"},
        {"importer_id": "importer-own-importer", "trace": "unheld"},
        {"importer_id": "importer-bare-importer", "trace": "unheld"},
        {"importer_id": "importer-leaping-importer", "trace": "unheld"}]
    assert ledger["breaks"] == ["importer-leaping-importer: mapped > held"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 265
    assert citizen["next_slice"] == "M-266"
    assert citizen["m241_title"] == "Rival importers"
    assert citizen["m241_part"] == 10
    assert citizen["m241_status"] == "done"

def test_importer_record_round_trips():
    importer = _importer()
    assert validate_importer(importer) is importer
    rebuilt = build_importer(importer.to_record())
    assert rebuilt == importer
    assert rebuilt.item_id == "importer-test"
    assert rebuilt.stage == "held"
    record = importer_record(importer)
    assert record["type"] == "importer_importer"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert source_record(ref)["type"] == "importer_run"
    assert source_record(ref)["state"] == "live"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _importer(stages=[])
    assert importer_gaps(silent) == (
        "has passed through no step: the importer has not started",)
    assert importer_green(silent) is False
    walking = _importer(stages=["detected", "mapped"])
    assert importer_gaps(walking) == (
        "has not reached held: the importer stands at mapped",)
    assert walking.stage == "mapped"
    sideways = _importer(stages=["mapped", "converted", "imported", "held"])
    assert importer_gaps(sideways) == (
        "opens at mapped, not at detected: the importer opens "
        "with the reflection",)
    repaired = _importer(stages=["detected", "mapped", "converted", "imported", "detected", "mapped", "converted", "imported", "held"])
    assert importer_gaps(repaired) == ()
    assert importer_green(repaired) is True
    with pytest.raises(ValueError):
        _importer(stages=[42])
    with pytest.raises(ValueError):
        _importer(stages="inspect as a bare string")
    with pytest.raises(ValueError):
        _importer(stages=["detected", "polish"])
    with pytest.raises(ValueError):
        _importer(claims=["weather"])
    with pytest.raises(ValueError):
        _importer(claims="settings_ref")
    none_importer = _importer(stages=None, claims=None)
    assert none_importer.stages == ()
    assert none_importer.claims == ()

def test_layout_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "importers", "coverage", "current_importer",
                "ledger", "importer"):
        fields = _importer().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_importer(fields)
    fields = _importer().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_importer(fields)


def test_layout_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _importer().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_importer(fields)


def test_importer_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _importer(title="")
    with pytest.raises(ValueError):
        _importer(source_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "detected > mapped > converted > imported > held"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_importers_own_fields():
    importer = _importer(claims=["settings_ref"])
    assert plain_lines(importer) == (
        "Importer: A test importer",
        "Source: source-test",
        "Stage: held",
        "Claims: settings_ref")
    segment = segment_of(importer)
    assert segment.startswith("importer-test: A test importer")
    assert "stage: 'held'" in segment
    assert "gaps: none" in segment
    assert plain_words(importer).startswith(
        "A test importer - from source-test")

def test_red_importers_stand_named_in_their_gaps():
    asking = _importer(claims=["feeling", "settings_ref", "summary"])
    assert importer_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert importer_green(asking) is False
    skipping = _importer(stages=["detected", "mapped", "held"])
    assert importer_gaps(skipping) == (
        "steps from mapped to held, which the importer sequence "
        "does not allow",)
    book = _book(importers=[
        _importer(),
        _importer(importer_id="importer-skipping", seq=2,
             stages=["detected", "mapped", "held"]),
    ])
    assert transition_breaks(book) == (
        "importer-skipping: mapped > held",)
    assert current_importer(book).importer_id == "importer-skipping"
    assert [g.importer_id for g in importer_importer(book)] == [
        "importer-test", "importer-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "importer_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "importer_note"
    assert record["importer_id"] == "importer-test"
    assert view_plain_words(view) == "View view-test: shows all importers."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_importers_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.stage for e in index.importers] == ["held"]
    assert index.importers[0] == IndexImporter(
        stage="held",
        importer_id="importer-test", title="A test importer")
    assert index.gaps == ("importer-hidden",)
    record = index_record(book)
    assert record["type"] == "importer_index"
    assert record["gaps"] == ["importer-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "importer_book"

def test_check_target_reaches_its_importer_and_an_unheld_target_reaches_nothing():
    book = load_importer()
    assert importer_for_check(book, "held").importer_id == (
        "importer-held-importer")
    assert importer_for_check(book, "") is None
    assert importer_for_check(book, None) is None
    assert importer_for_check(book, "not held at all") is None
    text = format_stage(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_importer()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Importer note note importer-held-importer" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").importer_id == "importer-test"
    assert note_for_importer(book, "importer-test").note_id == "note-test"
    assert note_for_importer(book, "importer-test", "praise") is None
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
    row = build_row(None, _importer(), book)
    assert row.standing == "complete"
    assert validate_row(row, _importer(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_importers():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "importer_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "held"
    empty_book = _book(importers=[_importer(stages=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(ImporterVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_importers():
    book = load_importer()
    assert [g.importer_id for g in shown_importers(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.importer_id for g in shown_importers(book, "view-held")] == [
        "importer-held-importer", "importer-retried-importer", "importer-own-importer"]
    assert [g.importer_id for g in importers_for_source(
        book, "rival-codex")] == [
            "importer-own-importer", "importer-bare-importer",
            "importer-leaping-importer"]
    assert importers_for_source(book, "source-nope") == ()
    assert current_importer(_mixed_book()).importer_id == "importer-hidden"
    assert current_importer(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "importer-test") == (
        "detected > mapped > converted > imported > held")
    assert trace_current(stale, "importer-test") is False
    assert ledger_record(stale)["traces"] == [
        {"importer_id": "importer-test", "trace": "stale"}]

def test_commands_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(importers=[_importer(), _importer(seq=2)])
    with pytest.raises(ValueError):
        _book(importers=[_importer(), _importer(importer_id="importer-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(importers=[_importer(source_id="source-nope")])
    with pytest.raises(ValueError):
        _book(sources=[_ref(), _ref(
            source_id="source-cold", seq=2, state="dormant")],
            importers=[_importer(source_id="source-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(source_id="source-nope")])
    fields = {
        "schema": IMPORTER_SCHEMA, "source": "M-241",
        "rival_importers": {"title": "A converted book"},
        "sources": [_ref().to_record()],
        "importer_records": [_importer().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "held"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_importer"] = "importer-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_importer")
    fields["trace"] = "importer-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / IMPORTER_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "rival_importers.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_importer_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.importer_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = ImporterRegistry()
    assert registry.title() is None
    registry.register_source_ref(_ref())
    registry.register_importer(_importer())
    registry.register_view(_view())
    assert [g.importer_id for g in registry.list_importers()] == ["importer-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_importer("importer-test").title == "A test importer"
    assert registry.get_slice("source-test").state == "live"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("importer-test").importer_id == "importer-test"
    with pytest.raises(ValueError):
        registry.register_importer(_importer(seq=9))
    with pytest.raises(ValueError):
        registry.register_importer(_importer(importer_id="importer-two"))
    with pytest.raises(KeyError):
        registry.get_importer("importer-nope")
    assert registry.book().title == "An unheld importer book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = ImporterRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test importer book"
    assert registry.title() == "A test importer book"
    assert len(registry.list_importers()) == 2
    other = ImporterRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    importer = _importer()
    assert "A test importer" in plain_words(importer)
    assert panel_plain_words(_mixed_book()).startswith(
        "The importer book holds 2 importers")
    assert verdict_plain_words(_mixed_book()) == (
        "The importers stand held: 1 of 2 shown importers stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green importers; red, "
        "detected in its gaps: importer-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_importer(importer)
    assert "Importer: A test importer" in text
    assert "stands complete" in text
    text = format_importer(_importer(stages=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The Rival Importers (M-241) - A test importer book" in book_text
    assert "importer-hidden" in format_book(_mixed_book(), "source-test")
    assert "Importer panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "held - A test importer (importer-test)" in index_text
    assert "importer-hidden" in index_text
    screen = format_importer_screen()
    assert "The Rival Importers (M-241)" in screen
    assert "importer-bare-importer" in screen

def test_parse_args_well_and_loader_targets():
    assert parse_importer_args("") == ("show", None)
    assert parse_importer_args(None) == ("show", None)
    assert parse_importer_args("show") == ("show", None)
    assert parse_importer_args("importer importer-test") == (
        "importer", "importer-test")
    assert parse_importer_args("stage held") == (
        "stage", "held")
    assert parse_importer_args("source source-test") == (
        "source", "source-test")
    assert parse_importer_args("view view-test") == ("view", "view-test")
    assert parse_importer_args("note note-test") == ("note", "note-test")
    assert parse_importer_args("index") == ("index", None)
    assert parse_importer_args("panel") == ("panel", None)
    assert parse_importer_args("verdict") == ("verdict", None)
    for bad in ("dance", "importer", "stage", "source", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_importer_args(bad)
    ledger = ledger_record()
    assert ledger["type"] == "importer_well"
    assert ledger["total"] == 5
    assert ledger["current_importer"] == "importer-bare-importer"
    book = load_importer({
        "schema": IMPORTER_SCHEMA, "source": "M-241",
        "rival_importers": {"title": "A converted book"},
        "sources": [_ref().to_record()],
        "importer_records": [_importer().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, ImporterBook)
    assert book.title == "A converted book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_importer({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_importer({"source": "M-999"})
    built = build_importer(
        importer_id="importer-kw", seq=3, source_id="source-test",
        title="Kw Importer", stages=["detected", "mapped", "converted", "imported", "held"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="importer-test")
    assert built.importer_id == "importer-kw"
    assert importer_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-241 agent layer: the agent holds a importer
# book for the session, importers and views are
# published as session news through the
# checkpoint target (ledger first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held importers, the ledger is derived from
# the held importers' completeness, the roadmap standing
# is imported from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no source. This layer importers
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session ledger news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_IMPORTER_EVENT_TYPES = (
    "importer_importer", "importer_run", "importer_view",
    "importer_panel", "importer_verdict")


def _importer_events(store, session_id, source):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == source]


def _write_rivalimporters_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / IMPORTER_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "rival_importers.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestImporterAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.rivalimporters_status()
        assert status["importer_records"] == []
        assert status["sources"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["rivalimporters_book"]["title"] == EXAMPLE_TITLE
        assert len(status["rivalimporters_book"]["sources"]) == 3
        assert len(status["rivalimporters_book"]["importer_records"]) == 5
        assert len(status["rivalimporters_book"]["views"]) == 2
        assert len(status["rivalimporters_book"]["notes"]) == 2
        assert len(status["rivalimporters_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-rival"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["stage"] for e in status["index"]["importers"]] == (
            EXAMPLE_STAGES)
        assert status["index"]["gaps"] == [
            "importer-bare-importer", "importer-leaping-importer"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["ledger"]["total"] == 5
        assert status["ledger"]["current_importer"] == "importer-bare-importer"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 265
        assert status["roadmap"]["next_slice"] == "M-266"
        assert status["roadmap"]["m241_title"] == "Rival importers"
        assert "held as data alone" in status["rule"]
        assert "importer-bare-importer" in status["plain_words"]
        assert "The Rival Importers (M-241)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._rivalimporters_registry()
        assert agent._rivalimporters_registry() is first
        assert agent._rivalimporters_store is first
        for name in ("rivalimporters_book", "rivalimporters_status", "rivalimporters_panel",
                     "rivalimporters_verdict", "rivalimporters_index", "report_rivalimporters"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_rivalimporters_registry", "rivalimporters_book", "rivalimporters_status",
            "get_rivalimporters_importer", "get_rivalimporters_view", "get_rivalimporters_note",
            "importers_for_source", "rivalimporters_green",
            "rivalimporters_panel", "rivalimporters_verdict", "rivalimporters_index",
            "register_rivalimporters_importer", "register_rivalimporters_view",
            "view_rivalimporters", "register_rivalimporters_book",
            "record_rivalimporters_book", "report_rivalimporters",
            "_publish_rivalimporters_record", "_rivalimporters_screen",
            "_rivalimporters_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.rivalimporters_status()
        assert agent.get_rivalimporters_importer(
            "importer-held-importer").title == "The held importer"
        assert agent.get_rivalimporters_view(
            "view-importers").view_filter == "all"
        assert agent.get_rivalimporters_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.importer_id for d in agent.importers_for_source(
            "rival-codex")] == [
            "importer-own-importer", "importer-bare-importer",
            "importer-leaping-importer"]
        assert [d.importer_id for d in agent.rivalimporters_green()] == [
            "importer-held-importer", "importer-retried-importer", "importer-own-importer"]
        agent.rivalimporters_panel()
        agent.rivalimporters_verdict()
        agent.rivalimporters_index()
        agent.report_rivalimporters()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _IMPORTER_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_rivalimporters_importer("importer-nope")
        with pytest.raises(KeyError):
            agent.get_rivalimporters_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_rivalimporters_note("note-nope")
        with pytest.raises(ValueError):
            agent.importers_for_source("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_rivalimporters_importer(_importer())
        status = agent.rivalimporters_status()
        assert [d["importer_id"] for d in status["importer_records"]] == ["importer-test"]
        assert status["book"]["title"] == "An unheld importer book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["stage"] for e in status["index"]["importers"]] == [
            "held"]
        assert status["first_note"] is None
        assert "importer-test" in status["screen"]
    def test_held_importer_never_falls_back_to_the_example(
            self, agent):
        agent.register_rivalimporters_importer(_importer())
        with pytest.raises(KeyError):
            agent.get_rivalimporters_importer("importer-held-importer")
        with pytest.raises(KeyError):
            agent.get_rivalimporters_view("view-importers")
        with pytest.raises(KeyError):
            agent.get_rivalimporters_note("note-note-first")
        importer = agent.get_rivalimporters_importer("importer-test")
        assert importer.title == "A test importer"
        assert agent.rivalimporters_book().title == (
            "An unheld importer book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_rivalimporters_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.importer_id == "importer-held-importer"
        status = agent.rivalimporters_status()
        assert status["index"]["gaps"] == [
            "importer-bare-importer", "importer-leaping-importer"]
        assert status["first_note"]["importer_id"] == (
            "importer-held-importer")
        assert status["first_note"]["stance"] == "note"

class TestImporterAgentHolding:
    def test_register_importer_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_rivalimporters_importer(_importer())
        assert result["importer"]["importer_id"] == "importer-test"
        assert result["record_news"]["type"] == "importer_importer"
        assert "importer-test" in result["screen"]
        events = _importer_events(store, session_id, "importer_importer")
        assert len(events) == 1
        agent.close()

    def test_duplicate_layout_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_rivalimporters_importer(_importer())
        with pytest.raises(ValueError):
            agent.register_rivalimporters_importer(_importer(seq=9))
        with pytest.raises(ValueError):
            agent.register_rivalimporters_importer(_importer(importer_id="importer-two"))
        events = _importer_events(store, session_id, "importer_importer")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_rivalimporters_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_importer_events(
            store, session_id, "importer_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_rivalimporters_importer(_importer())
        result = agent.view_rivalimporters("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "importer_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "held"
        assert len(_importer_events(
            store, session_id, "importer_view")) == 1
        assert len(_importer_events(
            store, session_id, "importer_panel")) == 1
        assert len(_importer_events(
            store, session_id, "importer_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_importer(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_rivalimporters_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "importer_run", "importer_importer", "importer_view"]
        assert len(_importer_events(
            store, session_id, "importer_importer")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_rivalimporters_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "importer_panel"
        assert result["index_record"]["gaps"] == [
            "importer-bare-importer", "importer-leaping-importer"]
        with pytest.raises(ValueError):
            agent.record_rivalimporters_book()
        assert len(_importer_events(
            store, session_id, "importer_run")) == 3
        assert len(_importer_events(
            store, session_id, "importer_importer")) == 5
        assert len(_importer_events(
            store, session_id, "importer_view")) == 2
        agent.close()

    def test_book_from_a_file_is_linked_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_rivalimporters_book_file(tmp_path)
        book = load_importer_file(path)
        result = agent.record_rivalimporters_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_runrt_renders_example_then_held_book_only(self, agent):
        importer = agent.report_rivalimporters()
        assert importer["book"]["title"] == EXAMPLE_TITLE
        assert importer["verdict"]["verdict"] == "held"
        assert importer["index"]["gaps"] == [
            "importer-bare-importer", "importer-leaping-importer"]
        assert "importer-held-importer" in importer["book_text"]
        assert "held - The held importer (importer-held-importer)" in importer["index_text"]
        agent.register_rivalimporters_importer(_importer())
        importer = agent.report_rivalimporters()
        assert importer["book"]["title"] == "An unheld importer book"
        assert importer["panel"] is None
        assert importer["verdict"] is None

class TestImporterTerminalHeading:
    def test_show_importer_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/rivalimporters")
        assert "The Rival Importers (M-241)" in text
        _, _, text = _slash(agent, "/rivalimporters importer importer-held-importer")
        assert "Importer: The held importer" in text
        _, _, text = _slash(
            agent, "/rivalimporters stage held")
        assert "Importer: The held importer" in text
        _, _, text = _slash(agent, "/rivalimporters stage triple importer")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/rivalimporters source rival-codex")
        assert "importer-bare-importer" in text
        assert "importer-held-importer" not in text
        _, _, text = _slash(agent, "/rivalimporters view view-importers")
        assert "filter all" in text
        _, _, text = _slash(agent, "/rivalimporters note note-note-first")
        assert "Importer note note importer-held-importer" in text
        _, _, text = _slash(agent, "/rivalimporters index")
        assert "Importer index" in text
        assert "importer-bare-importer" in text
        _, _, text = _slash(agent, "/rivalimporters panel")
        assert "Importer panel under view view-importers" in text
        _, _, text = _slash(agent, "/rivalimporters verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/rivalimporters [show|importer <importer-id>"
                "|stage <stage>|source <source-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/rivalimporters dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/rivalimporters importer importer-nope")
        assert "no importer detected" in text
@pytest.fixture()
def importer_handler(agent, monkeypatch):
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


def _importer_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestImporterSource:
    def test_show_is_default(self, importer_handler, agent):
        importer_handler._handle_rivalimporters("")
        assert "The Rival Importers (M-241)" in (
            _importer_published_text(importer_handler))

    def test_importer_check_slice_view_note_index_panel_verdict(
            self, importer_handler, agent):
        importer_handler._handle_rivalimporters("importer importer-held-importer")
        assert "Importer: The held importer" in _importer_published_text(
            importer_handler)
        importer_handler._handle_rivalimporters(
            "stage held")
        assert "Importer: The held importer" in _importer_published_text(
            importer_handler)
        importer_handler._handle_rivalimporters("source rival-codex")
        assert "importer-bare-importer" in _importer_published_text(
            importer_handler)
        importer_handler._handle_rivalimporters("view view-importers")
        assert "filter all" in _importer_published_text(importer_handler)
        importer_handler._handle_rivalimporters("note note-note-first")
        assert "Importer note note importer-held-importer" in (
            _importer_published_text(importer_handler))
        importer_handler._handle_rivalimporters("index")
        assert "Importer index" in _importer_published_text(importer_handler)
        importer_handler._handle_rivalimporters("panel")
        assert "Importer panel under view" in _importer_published_text(
            importer_handler)
        importer_handler._handle_rivalimporters("verdict")
        assert "held" in _importer_published_text(importer_handler)
    def test_bad_grammar_is_published(
            self, importer_handler, agent):
        importer_handler._handle_rivalimporters("dance party")
        assert USAGE in _importer_published_text(importer_handler)
        importer_handler._handle_rivalimporters("importer importer-nope")
        assert "no importer detected" in _importer_published_text(
            importer_handler)


class TestChatScreenRoutingImporter:
    def test_onwell_routes_as_system_source(self, monkeypatch):
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
        screen.handle_command("/rivalimporters panel", _FakeLog())
        assert calls == [("/rivalimporters", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/rivalimporters[/green] - show the Rival importers (M-241)" in (
            text)
        assert ('"/rivalimporters": "Usage: /rivalimporters | '
                '/rivalimporters importer <importer-id>') in text

class TestImporterDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.rivalimporters_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-importers"
        verdict = agent.rivalimporters_verdict()
        assert verdict.verdict == "held"
        detected = agent.rivalimporters_verdict("view-held")
        assert detected.verdict == "held"
        assert detected.green_shown == 3
        agent.register_rivalimporters_importer(_importer())
        with pytest.raises(ValueError):
            agent.rivalimporters_panel()
        with pytest.raises(ValueError):
            agent.rivalimporters_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_rivalimporters_importer(_importer(stages=[]))
        result = agent.view_rivalimporters("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.rivalimporters_index()
        assert [e["stage"] for e in result["index"]["importers"]] == (
            EXAMPLE_STAGES)
        assert result["index"]["gaps"] == [
            "importer-bare-importer", "importer-leaping-importer"]
        assert "held - The held importer (importer-held-importer)" in (
            result["index_text"])
        importer = agent.get_rivalimporters_importer("importer-leaping-importer")
        assert importer_gaps(importer, agent.rivalimporters_book()) == (
            "steps from mapped to held, which the importer sequence "
            "does not allow",)
        assert importer_green(importer, agent.rivalimporters_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _IMPORTER_EVENT_TYPES] == []
        agent.close()
