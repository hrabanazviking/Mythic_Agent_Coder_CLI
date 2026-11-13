"""M-205 The Acceptance Gate As Audittime - pure-layer tests.

TIER: integration

The pure layer is the gate audit, held as data: one
record per audit, held whole - the slice it audits,
named by slice id, its title, the checks it
walked in walk order and the claims it asked,
held by kind. The gate sequence is explicit -
inspect, build, test, repair, continue, with its
legal steps held as data - and a audit's standing
is derived at call time: a audit that opens
anywhere but inspect, steps where the machine
does not allow, asks a file, framework, table or
function claim the Auditor can answer, or has
not yet reached evidence stands red, named
in its gaps. A audit stands only for an active
slice: a audit naming no held slice, or one that
is not active, refuses by name. The audit's trace
- its walked checks as one line - is derived at
call time, and a held trace record stands
current only while it agrees with the derived
trace. The index, panel, verdict, board, trace,
order and current audit are derived at call time,
never stored where they could drift, and a
stored one refuses by name, as does a record
claiming a gate was actually audit live, a slice
actually built, banked or pushed. The shipped
example book is held in a data file, and a
loader reads a book from any file. No charter
row names this slice: the M-171 TUI charter
binds Part VIII alone, and the M-005 method
charter names no slice row - its source note
names the whole Part IX range M-201-M-232 as
the part that executes it and names
YRSA_CODING_JUGGERNAUT itself among the six
plugs, and the tests pin both facts live. This
layer audits no gate, builds nothing, banks
nothing, pushes nothing and opens no network:
it holds gate audits as data and tells them.
"""


from pathlib import Path

import pytest
import yaml

from mythic_agent.core.acceptance_gates import (
    EXAMPLE_CHECK,
    BARE_CLAIMS,
    HELD_EVIDENCE,
    INDEX_ACTION,
    CHECKS,
    CLAIM_KINDS,
    TRANSITIONS,
    SLICE_STATES,
    CHECK_FIELDS,
    PLAIN_EXPLANATION,
    ACCEPTANCE_RESOURCE,
    ACCEPTANCE_RULE,
    ACCEPTANCE_SCHEMA,
    ACCEPTANCE_SLICE,
    GREEN_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    AuditRecord,
    IndexEntry,
    SliceRef,
    NoteRecord,
    AcceptanceBook,
    AcceptanceIndex,
    AcceptancePanel,
    AcceptanceRegistry,
    AcceptanceVerdict,
    AcceptanceView,
    trace_for_audit,
    board_record,
    book_record,
    build_trace,
    build_book,
    build_audit,
    build_slice_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_audit,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    audit_for_check,
    audit_gaps,
    audit_order,
    audit_record,
    audit_green,
    audits_for_slice,
    first_note,
    format_book,
    format_audit,
    format_index,
    format_note,
    format_check,
    format_panel,
    format_acceptance_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    slice_record,
    load_acceptance,
    legal_step,
    load_acceptance_file,
    next_check,
    normalize_check,
    normalize_claim_kind,
    normalize_slice_state,
    normalize_stance,
    normalize_view_filter,
    note_for_audit,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_acceptance_args,
    green_audits,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_audits,
    validate_book,
    validate_audit,
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
ON = "2026-11-10"
BY = "the coordinator"
EXAMPLE_TITLE = "The Acceptance gate at the M-204 slice boundary"
EXAMPLE_CHECKS = ["evidence", "evidence", "evidence"]
EXAMPLE_RUN_IDS = (
    "audit-juggernaut-gate", "audit-repair-gate",
    "audit-acceptance-gate", "audit-feeling-gate",
    "audit-skipping-gate")
EXAMPLE_TRACE = "charter > build > test_suite > evidence"


def _ref(**overrides):
    fields = {
        "slice_id": "slice-test",
        "seq": 1,
        "title": "A test slice",
        "state": "active",
        "detail": "A test slice reference held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "acceptance-test",
    }
    fields.update(overrides)
    return build_slice_ref(fields)


def _audit(**overrides):
    fields = {
        "audit_id": "audit-test",
        "seq": 1,
        "slice_id": "slice-test",
        "title": "A test audit",
        "checks": ["charter", "build", "test_suite", "evidence"],
        "claims": [],
        "detail": "A test audit held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "acceptance-test",
    }
    fields.update(overrides)
    return build_audit(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "acceptance-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "audit_id": "audit-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "acceptance-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "audit_id": "audit-test",
        "trace": "charter > build > test_suite > evidence",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "acceptance-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(slices=None, audits=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": ACCEPTANCE_SCHEMA,
        "slice": "M-205",
        "acceptance_gates": {"title": "A test acceptance book"},
        "slices": [item.to_record() for item in (
            slices if slices is not None else [_ref()])],
        "audits": [item.to_record() for item in (
            audits if audits is not None else [_audit()])],
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
    return _book(audits=[
        _audit(),
        _audit(audit_id="audit-hidden", seq=2,
               title="A hidden audit", checks=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_acceptance()
    assert book.title == EXAMPLE_TITLE
    assert book.audit_ids() == EXAMPLE_RUN_IDS
    assert book.slice_ids() == (
        "slice-m204-juggernaut", "slice-m205-gates",
        "slice-m206-banking")
    assert [v.view_id for v in book.views] == [
        "view-gates", "view-green"]
    assert [m.audit_id for m in book.notes] == [
        "audit-juggernaut-gate", "audit-feeling-gate"]
    assert [a.audit_id for a in book.traces] == ["audit-juggernaut-gate"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m204-boundary"
    assert panel.as_of == "2026-11-10"
    assert [row.item_id for row in panel.rows] == list(book.audit_ids())
    derived = derive_panel(book, "view-gates")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "green": 3, "red": 2}
    assert derive_verdict(book, "view-gates").verdict == "held"
    assert derive_verdict(book, "view-gates").green_shown == 3
    assert derive_verdict(book, "view-green").verdict == "bankable"
    assert derive_verdict(book, "view-green").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / ACCEPTANCE_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == ACCEPTANCE_SCHEMA
    assert raw["slice"] == "M-205"
    assert "verdict" not in raw
    assert "acceptance_index" not in raw
    assert "board" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-205")]
    assert slice_.title == "Acceptance gates per slice"
    assert slice_.part == 9
    assert "each slice carries its checks" in slice_.summary
    assert "Auditor (M-130)" in slice_.summary
    assert "banks only green" in slice_.summary
    assert "evidence" in slice_.summary
    assert "not a feeling" in slice_.summary
    assert ACCEPTANCE_SLICE == "M-205"

def test_charter_rows_do_not_name_m205():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-205" not in owners
    method = load_method_charter()
    assert "M-201" in method.source_note
    assert "M-232" in method.source_note
    assert "YRSA_CODING_JUGGERNAUT" in method.source_note

def test_closed_vocabularies():
    assert GREEN_WORDS == ("green", "red")
    assert CHECK_FIELDS == ("checks", "claims")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "green", "red")
    assert VERDICT_WORDS == ("bankable", "held", "blocked")
    assert SLICE_STATES == ("active", "queued")
    assert CHECKS == ("charter", "build", "test_suite", "repair", "evidence")
    assert HELD_EVIDENCE == ("runner_output", "compile_log", "neighbour_log", "ledger_row")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_KINDS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["test_suite"] == ("repair", "evidence")
    assert TRANSITIONS["evidence"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_CHECK == "evidence"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_slice_state("ACTIVE") == "active"
    assert normalize_check("TEST_SUITE") == "test_suite"
    assert normalize_claim_kind("FEELING") == "feeling"
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    with pytest.raises(ValueError):
        normalize_slice_state("blessed")
    with pytest.raises(ValueError):
        normalize_check("polish")
    with pytest.raises(ValueError):
        normalize_claim_kind("weather")
    assert legal_step("test_suite", "repair") is True
    assert legal_step("build", "evidence") is False
    assert legal_step("evidence", "charter") is False
    assert next_check("charter") == "build"
    assert next_check("test_suite") == "evidence"
    assert next_check("test_suite", failed=True) == "repair"
    assert next_check("repair") == "test_suite"
    assert next_check("evidence") is None
    assert "held as data alone" in ACCEPTANCE_RULE
    assert "gate sequence" in ACCEPTANCE_RULE
    assert "M-205" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /acceptance")

def test_shipped_book_judged_honestly_as_data():
    book = load_acceptance()
    opening = book.audit_for("audit-juggernaut-gate")
    assert audit_green(opening, book) is True
    assert audit_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Audit: The Juggernaut loop gate audit",
        "Slice: slice-m204-juggernaut",
        "Check: evidence",
        "Claims: runner_output")
    asking = book.audit_for("audit-feeling-gate")
    assert audit_gaps(asking, book) == (
        "asked a feeling claim the Auditor can answer",)
    assert audit_green(asking, book) is False
    skipping = book.audit_for("audit-skipping-gate")
    assert audit_gaps(skipping, book) == (
        "steps from build to evidence, which the gate sequence "
        "does not allow",)
    assert [g.audit_id for g in green_audits(book)] == [
        "audit-juggernaut-gate", "audit-repair-gate", "audit-acceptance-gate"]
    index = derive_index(book)
    assert [e.check for e in index.entries] == EXAMPLE_CHECKS
    assert index.gaps == ("audit-feeling-gate", "audit-skipping-gate")
    assert audit_for_check(book, EXAMPLE_CHECK).audit_id == (
        "audit-juggernaut-gate")
    assert audit_for_check(book, "triple resume") is None
    assert transition_breaks(book) == (
        "audit-skipping-gate: build > evidence",)
    assert [g.audit_id for g in audit_order(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "audit-juggernaut-gate") == EXAMPLE_TRACE
    assert trace_current(book, "audit-juggernaut-gate") is True
    assert trace_current(book, "audit-repair-gate") is False
    assert trace_for_audit(
        book, "audit-juggernaut-gate").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_audit(
        book, "audit-juggernaut-gate", "note").note_id == (
            "note-note-first")
    assert note_for_audit(book, "audit-nope") is None
    assert current_audit(book).audit_id == "audit-feeling-gate"
    board = board_record(book)
    assert board["standings"] == [
        {"standing": "green", "audits": 3},
        {"standing": "red", "audits": 2}]
    assert board["total"] == 5
    assert board["current_audit"] == "audit-feeling-gate"
    assert board["traces"] == [
        {"audit_id": "audit-juggernaut-gate", "trace": "current"},
        {"audit_id": "audit-repair-gate", "trace": "unheld"},
        {"audit_id": "audit-acceptance-gate", "trace": "unheld"},
        {"audit_id": "audit-feeling-gate", "trace": "unheld"},
        {"audit_id": "audit-skipping-gate", "trace": "unheld"}]
    assert board["breaks"] == ["audit-skipping-gate: build > evidence"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 261
    assert citizen["next_slice"] == "M-262"
    assert citizen["m205_title"] == "Acceptance gates per slice"
    assert citizen["m205_part"] == 9
    assert citizen["m205_status"] == "done"

def test_audit_record_round_trips():
    audit = _audit()
    assert validate_audit(audit) is audit
    rebuilt = build_audit(audit.to_record())
    assert rebuilt == audit
    assert rebuilt.item_id == "audit-test"
    assert rebuilt.check == "evidence"
    record = audit_record(audit)
    assert record["type"] == "acceptance_audit"
    assert record["green"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert slice_record(ref)["type"] == "acceptance_slice"
    assert slice_record(ref)["state"] == "active"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _audit(checks=[])
    assert audit_gaps(silent) == (
        "has passed through no check: the gate has not started",)
    assert audit_green(silent) is False
    walking = _audit(checks=["charter", "build"])
    assert audit_gaps(walking) == (
        "has not reached evidence: the gate stands at build",)
    assert walking.check == "build"
    sideways = _audit(checks=["build", "test_suite", "evidence"])
    assert audit_gaps(sideways) == (
        "opens at build, not at charter: the gate opens "
        "by reading the charter",)
    repaired = _audit(checks=[
        "charter", "build", "test_suite", "repair", "test_suite", "evidence"])
    assert audit_gaps(repaired) == ()
    assert audit_green(repaired) is True
    with pytest.raises(ValueError):
        _audit(checks=[42])
    with pytest.raises(ValueError):
        _audit(checks="inspect as a bare string")
    with pytest.raises(ValueError):
        _audit(checks=["charter", "polish"])
    with pytest.raises(ValueError):
        _audit(claims=["weather"])
    with pytest.raises(ValueError):
        _audit(claims="runner_output")
    none_audit = _audit(checks=None, claims=None)
    assert none_audit.checks == ()
    assert none_audit.claims == ()

def test_audit_refuses_stored_judgements():
    for key in ("standing", "green", "gaps", "segment", "verdict",
                "index", "entries", "coverage", "current_audit",
                "board", "order"):
        fields = _audit().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_audit(fields)
    fields = _audit().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_audit(fields)


def test_audit_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _audit().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_audit(fields)


def test_audit_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _audit(title="")
    with pytest.raises(ValueError):
        _audit(slice_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "charter > build > test_suite > evidence"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_audits_own_fields():
    audit = _audit(claims=["runner_output"])
    assert plain_lines(audit) == (
        "Audit: A test audit",
        "Slice: slice-test",
        "Check: evidence",
        "Claims: runner_output")
    segment = segment_of(audit)
    assert segment.startswith("audit-test: A test audit")
    assert "check: 'evidence'" in segment
    assert "gaps: none" in segment
    assert plain_words(audit).startswith(
        "A test audit - from slice-test")

def test_red_audits_stand_named_in_their_gaps():
    asking = _audit(claims=["feeling", "runner_output", "summary"])
    assert audit_gaps(asking) == (
        "asked a feeling claim the Auditor can answer",
        "asked a summary claim the Auditor can answer")
    assert audit_green(asking) is False
    skipping = _audit(checks=["charter", "build", "evidence"])
    assert audit_gaps(skipping) == (
        "steps from build to evidence, which the gate sequence "
        "does not allow",)
    book = _book(audits=[
        _audit(),
        _audit(audit_id="audit-skipping", seq=2,
             checks=["charter", "build", "evidence"]),
    ])
    assert transition_breaks(book) == (
        "audit-skipping: build > evidence",)
    assert current_audit(book).audit_id == "audit-skipping"
    assert [g.audit_id for g in audit_order(book)] == [
        "audit-test", "audit-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "acceptance_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "acceptance_note"
    assert record["audit_id"] == "audit-test"
    assert view_plain_words(view) == "View view-test: shows all audits."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_audits_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.check for e in index.entries] == ["evidence"]
    assert index.entries[0] == IndexEntry(
        check="evidence",
        audit_id="audit-test", title="A test audit")
    assert index.gaps == ("audit-hidden",)
    record = index_record(book)
    assert record["type"] == "acceptance_index"
    assert record["gaps"] == ["audit-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "acceptance_book"

def test_check_target_reaches_its_audit_and_an_unheld_target_reaches_nothing():
    book = load_acceptance()
    assert audit_for_check(book, "evidence").audit_id == (
        "audit-juggernaut-gate")
    assert audit_for_check(book, "") is None
    assert audit_for_check(book, None) is None
    assert audit_for_check(book, "not held at all") is None
    text = format_check(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_acceptance()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Acceptance note note audit-juggernaut-gate" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").audit_id == "audit-test"
    assert note_for_audit(book, "audit-test").note_id == "note-test"
    assert note_for_audit(book, "audit-test", "praise") is None
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
        "green": 1, "red": 1}
    assert validate_panel(panel, book) is panel
    assert build_panel(panel.to_record(), book) == panel
    row = build_row(None, _audit(), book)
    assert row.standing == "green"
    assert validate_row(row, _audit(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_audits():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "acceptance_verdict"
    green_book = _book(views=[_view(view_filter="green")])
    assert derive_verdict(green_book).verdict == "bankable"
    empty_book = _book(audits=[_audit(checks=[])],
                       views=[_view(view_filter="green")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(AcceptanceVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_readings():
    book = load_acceptance()
    assert [g.audit_id for g in shown_audits(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.audit_id for g in shown_audits(book, "view-green")] == [
        "audit-juggernaut-gate", "audit-repair-gate", "audit-acceptance-gate"]
    assert [g.audit_id for g in audits_for_slice(
        book, "slice-m205-gates")] == [
            "audit-acceptance-gate", "audit-feeling-gate",
            "audit-skipping-gate"]
    assert audits_for_slice(book, "slice-nope") == ()
    assert current_audit(_mixed_book()).audit_id == "audit-hidden"
    assert current_audit(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "audit-test") == (
        "charter > build > test_suite > evidence")
    assert trace_current(stale, "audit-test") is False
    assert board_record(stale)["traces"] == [
        {"audit_id": "audit-test", "trace": "stale"}]

def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(audits=[_audit(), _audit(seq=2)])
    with pytest.raises(ValueError):
        _book(audits=[_audit(), _audit(audit_id="audit-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(audits=[_audit(slice_id="slice-nope")])
    with pytest.raises(ValueError):
        _book(slices=[_ref(), _ref(
            slice_id="slice-cold", seq=2, state="queued")],
            audits=[_audit(slice_id="slice-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(slice_id="slice-nope")])
    fields = {
        "schema": ACCEPTANCE_SCHEMA, "slice": "M-205",
        "acceptance_gates": {"title": "A judged book"},
        "slices": [_ref().to_record()],
        "audits": [_audit().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "bankable"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_audit"] = "audit-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_audit")
    fields["trace"] = "audit-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / ACCEPTANCE_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "acceptance_gates.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_acceptance_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.audit_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = AcceptanceRegistry()
    assert registry.title() is None
    registry.register_slice_ref(_ref())
    registry.register_audit(_audit())
    registry.register_view(_view())
    assert [g.audit_id for g in registry.list_audits()] == ["audit-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_audit("audit-test").title == "A test audit"
    assert registry.get_slice("slice-test").state == "active"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("audit-test").audit_id == "audit-test"
    with pytest.raises(ValueError):
        registry.register_audit(_audit(seq=9))
    with pytest.raises(ValueError):
        registry.register_audit(_audit(audit_id="audit-two"))
    with pytest.raises(KeyError):
        registry.get_audit("audit-nope")
    assert registry.book().title == "An unheld acceptance book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = AcceptanceRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test acceptance book"
    assert registry.title() == "A test acceptance book"
    assert len(registry.list_audits()) == 2
    other = AcceptanceRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    audit = _audit()
    assert "A test audit" in plain_words(audit)
    assert panel_plain_words(_mixed_book()).startswith(
        "The acceptance book holds 2 audits")
    assert verdict_plain_words(_mixed_book()) == (
        "The audits stand held: 1 of 2 shown audits stand green.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green audits; red, "
        "named in its gaps: audit-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_audit(audit)
    assert "Audit: A test audit" in text
    assert "stands green" in text
    text = format_audit(_audit(checks=[]))
    assert "stands red" in text
    assert "has passed through no check" in text
    book_text = format_book(_mixed_book())
    assert "The Acceptance Gate (M-205) - A test acceptance book" in book_text
    assert "audit-hidden" in format_book(_mixed_book(), "slice-test")
    assert "Acceptance panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "evidence - A test audit (audit-test)" in index_text
    assert "audit-hidden" in index_text
    screen = format_acceptance_screen()
    assert "The Acceptance Gate (M-205)" in screen
    assert "audit-feeling-gate" in screen

def test_parse_args_board_and_loader_targets():
    assert parse_acceptance_args("") == ("show", None)
    assert parse_acceptance_args(None) == ("show", None)
    assert parse_acceptance_args("show") == ("show", None)
    assert parse_acceptance_args("audit audit-test") == (
        "audit", "audit-test")
    assert parse_acceptance_args("check evidence") == (
        "check", "evidence")
    assert parse_acceptance_args("slice slice-test") == (
        "slice", "slice-test")
    assert parse_acceptance_args("view view-test") == ("view", "view-test")
    assert parse_acceptance_args("note note-test") == ("note", "note-test")
    assert parse_acceptance_args("index") == ("index", None)
    assert parse_acceptance_args("panel") == ("panel", None)
    assert parse_acceptance_args("verdict") == ("verdict", None)
    for bad in ("dance", "audit", "check", "slice", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_acceptance_args(bad)
    board = board_record()
    assert board["type"] == "acceptance_board"
    assert board["total"] == 5
    assert board["current_audit"] == "audit-feeling-gate"
    book = load_acceptance({
        "schema": ACCEPTANCE_SCHEMA, "slice": "M-205",
        "acceptance_gates": {"title": "A judged book"},
        "slices": [_ref().to_record()],
        "audits": [_audit().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, AcceptanceBook)
    assert book.title == "A judged book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_acceptance({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_acceptance({"slice": "M-999"})
    built = build_audit(
        audit_id="audit-kw", seq=3, slice_id="slice-test",
        title="Kw Audit", checks=["charter", "build", "test_suite", "evidence"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="acceptance-test")
    assert built.audit_id == "audit-kw"
    assert audit_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-205 agent layer: the agent holds a acceptance
# book for the session, audits and views are
# published as session news through the
# checkpoint target (journal first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held audits, the board is derived from
# the held audits' greenness, the roadmap standing
# is read from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no slice. This layer audits
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session journal news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_ACCEPTANCE_EVENT_TYPES = (
    "acceptance_audit", "acceptance_slice", "acceptance_view",
    "acceptance_panel", "acceptance_verdict")


def _acceptance_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_acceptance_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / ACCEPTANCE_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "acceptance_gates.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestAcceptanceAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.acceptance_status()
        assert status["audits"] == []
        assert status["slices"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["acceptance_book"]["title"] == EXAMPLE_TITLE
        assert len(status["acceptance_book"]["slices"]) == 3
        assert len(status["acceptance_book"]["audits"]) == 5
        assert len(status["acceptance_book"]["views"]) == 2
        assert len(status["acceptance_book"]["notes"]) == 2
        assert len(status["acceptance_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-m204-boundary"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["check"] for e in status["index"]["entries"]] == (
            EXAMPLE_CHECKS)
        assert status["index"]["gaps"] == [
            "audit-feeling-gate", "audit-skipping-gate"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["board"]["total"] == 5
        assert status["board"]["current_audit"] == "audit-feeling-gate"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 261
        assert status["roadmap"]["next_slice"] == "M-262"
        assert status["roadmap"]["m205_title"] == "Acceptance gates per slice"
        assert "held as data alone" in status["rule"]
        assert "audit-feeling-gate" in status["plain_words"]
        assert "The Acceptance Gate (M-205)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._acceptance_registry()
        assert agent._acceptance_registry() is first
        assert agent._acceptance_store is first
        for name in ("acceptance_book", "acceptance_status", "acceptance_panel",
                     "acceptance_verdict", "acceptance_index", "report_acceptance"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_acceptance_registry", "acceptance_book", "acceptance_status",
            "get_acceptance_audit", "get_acceptance_view", "get_acceptance_note",
            "acceptance_audits_for_slice", "acceptance_audits_green",
            "acceptance_panel", "acceptance_verdict", "acceptance_index",
            "register_acceptance_audit", "register_acceptance_view",
            "view_acceptance", "register_acceptance_book",
            "record_acceptance_book", "report_acceptance",
            "_publish_acceptance_record", "_acceptance_screen",
            "_acceptance_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.acceptance_status()
        assert agent.get_acceptance_audit(
            "audit-juggernaut-gate").title == "The Juggernaut loop gate audit"
        assert agent.get_acceptance_view(
            "view-gates").view_filter == "all"
        assert agent.get_acceptance_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.audit_id for d in agent.acceptance_audits_for_slice(
            "slice-m205-gates")] == [
            "audit-acceptance-gate", "audit-feeling-gate",
            "audit-skipping-gate"]
        assert [d.audit_id for d in agent.acceptance_audits_green()] == [
            "audit-juggernaut-gate", "audit-repair-gate", "audit-acceptance-gate"]
        agent.acceptance_panel()
        agent.acceptance_verdict()
        agent.acceptance_index()
        agent.report_acceptance()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _ACCEPTANCE_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_acceptance_audit("audit-nope")
        with pytest.raises(KeyError):
            agent.get_acceptance_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_acceptance_note("note-nope")
        with pytest.raises(ValueError):
            agent.acceptance_audits_for_slice("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_acceptance_audit(_audit())
        status = agent.acceptance_status()
        assert [d["audit_id"] for d in status["audits"]] == ["audit-test"]
        assert status["book"]["title"] == "An unheld acceptance book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["check"] for e in status["index"]["entries"]] == [
            "evidence"]
        assert status["first_note"] is None
        assert "audit-test" in status["screen"]
    def test_held_audit_never_falls_back_to_the_example(
            self, agent):
        agent.register_acceptance_audit(_audit())
        with pytest.raises(KeyError):
            agent.get_acceptance_audit("audit-juggernaut-gate")
        with pytest.raises(KeyError):
            agent.get_acceptance_view("view-gates")
        with pytest.raises(KeyError):
            agent.get_acceptance_note("note-note-first")
        audit = agent.get_acceptance_audit("audit-test")
        assert audit.title == "A test audit"
        assert agent.acceptance_book().title == (
            "An unheld acceptance book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_acceptance_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.audit_id == "audit-juggernaut-gate"
        status = agent.acceptance_status()
        assert status["index"]["gaps"] == [
            "audit-feeling-gate", "audit-skipping-gate"]
        assert status["first_note"]["audit_id"] == (
            "audit-juggernaut-gate")
        assert status["first_note"]["stance"] == "note"

class TestAcceptanceAgentHolding:
    def test_register_audit_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_acceptance_audit(_audit())
        assert result["audit"]["audit_id"] == "audit-test"
        assert result["record_news"]["type"] == "acceptance_audit"
        assert "audit-test" in result["screen"]
        events = _acceptance_events(store, session_id, "acceptance_audit")
        assert len(events) == 1
        agent.close()

    def test_duplicate_audit_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_acceptance_audit(_audit())
        with pytest.raises(ValueError):
            agent.register_acceptance_audit(_audit(seq=9))
        with pytest.raises(ValueError):
            agent.register_acceptance_audit(_audit(audit_id="audit-two"))
        events = _acceptance_events(store, session_id, "acceptance_audit")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_acceptance_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_acceptance_events(
            store, session_id, "acceptance_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_acceptance_audit(_audit())
        result = agent.view_acceptance("green")
        assert result["view"]["view_filter"] == "green"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "acceptance_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "bankable"
        assert len(_acceptance_events(
            store, session_id, "acceptance_view")) == 1
        assert len(_acceptance_events(
            store, session_id, "acceptance_panel")) == 1
        assert len(_acceptance_events(
            store, session_id, "acceptance_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_acceptance_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "acceptance_slice", "acceptance_audit", "acceptance_view"]
        assert len(_acceptance_events(
            store, session_id, "acceptance_audit")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_acceptance_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "acceptance_panel"
        assert result["index_record"]["gaps"] == [
            "audit-feeling-gate", "audit-skipping-gate"]
        with pytest.raises(ValueError):
            agent.record_acceptance_book()
        assert len(_acceptance_events(
            store, session_id, "acceptance_slice")) == 3
        assert len(_acceptance_events(
            store, session_id, "acceptance_audit")) == 5
        assert len(_acceptance_events(
            store, session_id, "acceptance_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_acceptance_book_file(tmp_path)
        book = load_acceptance_file(path)
        result = agent.record_acceptance_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_acceptance()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "held"
        assert report["index"]["gaps"] == [
            "audit-feeling-gate", "audit-skipping-gate"]
        assert "audit-juggernaut-gate" in report["book_text"]
        assert "evidence - The Juggernaut loop gate audit (audit-juggernaut-gate)" in report["index_text"]
        agent.register_acceptance_audit(_audit())
        report = agent.report_acceptance()
        assert report["book"]["title"] == "An unheld acceptance book"
        assert report["panel"] is None
        assert report["verdict"] is None

class TestAcceptanceTerminalHeading:
    def test_show_audit_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/acceptance")
        assert "The Acceptance Gate (M-205)" in text
        _, _, text = _slash(agent, "/acceptance audit audit-juggernaut-gate")
        assert "Audit: The Juggernaut loop gate audit" in text
        _, _, text = _slash(
            agent, "/acceptance check evidence")
        assert "Audit: The Juggernaut loop gate audit" in text
        _, _, text = _slash(agent, "/acceptance check triple resume")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/acceptance slice slice-m205-gates")
        assert "audit-feeling-gate" in text
        assert "audit-juggernaut-gate" not in text
        _, _, text = _slash(agent, "/acceptance view view-gates")
        assert "filter all" in text
        _, _, text = _slash(agent, "/acceptance note note-note-first")
        assert "Acceptance note note audit-juggernaut-gate" in text
        _, _, text = _slash(agent, "/acceptance index")
        assert "Acceptance index" in text
        assert "audit-feeling-gate" in text
        _, _, text = _slash(agent, "/acceptance panel")
        assert "Acceptance panel under view view-gates" in text
        _, _, text = _slash(agent, "/acceptance verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/acceptance [show|audit <audit-id>"
                "|check <check>|slice <slice-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/acceptance dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/acceptance audit audit-nope")
        assert "no audit named" in text
@pytest.fixture()
def acceptance_handler(agent, monkeypatch):
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


def _acceptance_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestAcceptanceCommand:
    def test_show_is_default(self, acceptance_handler, agent):
        acceptance_handler._handle_acceptance("")
        assert "The Acceptance Gate (M-205)" in (
            _acceptance_published_text(acceptance_handler))

    def test_audit_check_slice_view_note_index_panel_verdict(
            self, acceptance_handler, agent):
        acceptance_handler._handle_acceptance("audit audit-juggernaut-gate")
        assert "Audit: The Juggernaut loop gate audit" in _acceptance_published_text(
            acceptance_handler)
        acceptance_handler._handle_acceptance(
            "check evidence")
        assert "Audit: The Juggernaut loop gate audit" in _acceptance_published_text(
            acceptance_handler)
        acceptance_handler._handle_acceptance("slice slice-m205-gates")
        assert "audit-feeling-gate" in _acceptance_published_text(
            acceptance_handler)
        acceptance_handler._handle_acceptance("view view-gates")
        assert "filter all" in _acceptance_published_text(acceptance_handler)
        acceptance_handler._handle_acceptance("note note-note-first")
        assert "Acceptance note note audit-juggernaut-gate" in (
            _acceptance_published_text(acceptance_handler))
        acceptance_handler._handle_acceptance("index")
        assert "Acceptance index" in _acceptance_published_text(acceptance_handler)
        acceptance_handler._handle_acceptance("panel")
        assert "Acceptance panel under view" in _acceptance_published_text(
            acceptance_handler)
        acceptance_handler._handle_acceptance("verdict")
        assert "held" in _acceptance_published_text(acceptance_handler)
    def test_bad_grammar_is_published(
            self, acceptance_handler, agent):
        acceptance_handler._handle_acceptance("dance party")
        assert USAGE in _acceptance_published_text(acceptance_handler)
        acceptance_handler._handle_acceptance("audit audit-nope")
        assert "no audit named" in _acceptance_published_text(
            acceptance_handler)


class TestChatScreenRoutingAcceptance:
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
        screen.handle_command("/acceptance panel", _FakeLog())
        assert calls == [("/acceptance", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/acceptance[/green] - show the Acceptance gate (M-205)" in (
            text)
        assert ('"/acceptance": "Usage: /acceptance | '
                '/acceptance audit <audit-id>') in text

class TestAcceptanceDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.acceptance_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-gates"
        verdict = agent.acceptance_verdict()
        assert verdict.verdict == "held"
        found = agent.acceptance_verdict("view-green")
        assert found.verdict == "bankable"
        assert found.green_shown == 3
        agent.register_acceptance_audit(_audit())
        with pytest.raises(ValueError):
            agent.acceptance_panel()
        with pytest.raises(ValueError):
            agent.acceptance_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_acceptance_audit(_audit(checks=[]))
        result = agent.view_acceptance("green")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.acceptance_index()
        assert [e["check"] for e in result["index"]["entries"]] == (
            EXAMPLE_CHECKS)
        assert result["index"]["gaps"] == [
            "audit-feeling-gate", "audit-skipping-gate"]
        assert "evidence - The Juggernaut loop gate audit (audit-juggernaut-gate)" in (
            result["index_text"])
        audit = agent.get_acceptance_audit("audit-skipping-gate")
        assert audit_gaps(audit, agent.acceptance_book()) == (
            "steps from build to evidence, which the gate sequence "
            "does not allow",)
        assert audit_green(audit, agent.acceptance_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _ACCEPTANCE_EVENT_TYPES] == []
        agent.close()
