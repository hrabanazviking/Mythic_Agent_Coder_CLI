"""M-206 Banking Discipline - pure-layer tests.

TIER: integration

The pure layer is the banking, held as data: one
record per banking, held whole - the slice it
banks, named by slice id, its title, the laws it
walked in walk order and the proofs it carries,
held by kind. The house git laws are explicit -
suite_green, commit, push, rework, verify, with
their legal steps held as data - and a banking's
standing is derived at call time: a banking that
opens anywhere but suite_green, steps where the
sequence does not allow, carries a bare claim in
place of held proof, or has not yet reached
verify stands unbanked, named in its gaps. A
banking stands only for an active slice: a
banking naming no held slice, or one that is not
active, refuses by name. The banking's trace -
its walked laws as one line - is derived at call
time, and a held trace record stands current
only while it agrees with the derived trace. The
index, panel, verdict, board, trace, order and
current banking are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
banking was actually banked, merged or pushed
live. The shipped example book is held in a data
file, and a loader reads a book from any file.
No charter row names this slice: the M-171 TUI
charter binds Part VIII alone, and the M-005
method charter names the whole of Part IX as the
part that executes it, both pinned live below.
"""


from pathlib import Path

import pytest
import yaml

from mythic_agent.core.banking_discipline import (
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
    BANKING_RESOURCE,
    BANKING_RULE,
    BANKING_SCHEMA,
    BANKING_SLICE,
    BANKED_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    BankingRecord,
    IndexEntry,
    SliceRef,
    NoteRecord,
    BankingBook,
    BankingIndex,
    BankingPanel,
    BankingRegistry,
    BankingVerdict,
    BankingView,
    trace_for_banking,
    board_record,
    book_record,
    build_trace,
    build_book,
    build_banking,
    build_slice_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_banking,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    banking_for_check,
    banking_gaps,
    banking_order,
    banking_record,
    banking_green,
    bankings_for_slice,
    first_note,
    format_book,
    format_banking,
    format_index,
    format_note,
    format_check,
    format_panel,
    format_banking_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    slice_record,
    load_banking,
    legal_step,
    load_banking_file,
    next_check,
    normalize_check,
    normalize_claim_kind,
    normalize_slice_state,
    normalize_stance,
    normalize_view_filter,
    note_for_banking,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_banking_args,
    green_bankings,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_bankings,
    validate_book,
    validate_banking,
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
EXAMPLE_TITLE = "The Banking discipline at the M-205 slice boundary"
EXAMPLE_CHECKS = ["verify", "verify", "verify"]
EXAMPLE_RUN_IDS = (
    "banking-acceptance-gate", "banking-rework-gate",
    "banking-discipline-gate", "banking-bare-gate",
    "banking-leaping-gate")
EXAMPLE_TRACE = "suite_green > commit > push > verify"


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
        "origin_session": "banking-test",
    }
    fields.update(overrides)
    return build_slice_ref(fields)


def _banking(**overrides):
    fields = {
        "banking_id": "banking-test",
        "seq": 1,
        "slice_id": "slice-test",
        "title": "A test banking",
        "checks": ["suite_green", "commit", "push", "verify"],
        "claims": [],
        "detail": "A test banking held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "banking-test",
    }
    fields.update(overrides)
    return build_banking(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "banking-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "banking_id": "banking-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "banking-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "banking_id": "banking-test",
        "trace": "suite_green > commit > push > verify",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "banking-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(slices=None, bankings=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": BANKING_SCHEMA,
        "slice": "M-206",
        "banking_discipline": {"title": "A test banking book"},
        "slices": [item.to_record() for item in (
            slices if slices is not None else [_ref()])],
        "bankings": [item.to_record() for item in (
            bankings if bankings is not None else [_banking()])],
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
    return _book(bankings=[
        _banking(),
        _banking(banking_id="banking-hidden", seq=2,
               title="A hidden banking", checks=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_banking()
    assert book.title == EXAMPLE_TITLE
    assert book.banking_ids() == EXAMPLE_RUN_IDS
    assert book.slice_ids() == (
        "slice-m205-gates", "slice-m206-banking",
        "slice-m207-keeper")
    assert [v.view_id for v in book.views] == [
        "view-bankings", "view-banked"]
    assert [m.banking_id for m in book.notes] == [
        "banking-acceptance-gate", "banking-bare-gate"]
    assert [a.banking_id for a in book.traces] == ["banking-acceptance-gate"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m205-boundary"
    assert panel.as_of == "2026-11-10"
    assert [row.item_id for row in panel.rows] == list(book.banking_ids())
    derived = derive_panel(book, "view-bankings")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "banked": 3, "unbanked": 2}
    assert derive_verdict(book, "view-bankings").verdict == "held"
    assert derive_verdict(book, "view-bankings").green_shown == 3
    assert derive_verdict(book, "view-banked").verdict == "verified"
    assert derive_verdict(book, "view-banked").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / BANKING_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == BANKING_SCHEMA
    assert raw["slice"] == "M-206"
    assert "verdict" not in raw
    assert "banking_index" not in raw
    assert "board" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-206")]
    assert slice_.title == "Banking discipline"
    assert slice_.part == 9
    assert "banked slices commit (M-078)" in slice_.summary
    assert "house git laws" in slice_.summary
    assert "push with remote verification" in slice_.summary
    assert "recites them in its plan" in slice_.summary
    assert "where the user has so ruled" in slice_.summary
    assert BANKING_SLICE == "M-206"

def test_charter_rows_do_not_name_m206():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-206" not in owners
    method = load_method_charter()
    assert "M-201" in method.source_note
    assert "M-232" in method.source_note
    assert "YRSA_CODING_JUGGERNAUT" in method.source_note

def test_closed_vocabularies():
    assert BANKED_WORDS == ("banked", "unbanked")
    assert CHECK_FIELDS == ("checks", "claims")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "banked", "unbanked")
    assert VERDICT_WORDS == ("verified", "held", "blocked")
    assert SLICE_STATES == ("active", "queued")
    assert CHECKS == ("suite_green", "commit", "push", "rework", "verify")
    assert HELD_EVIDENCE == ("suite_log", "commit_ref", "remote_hash", "ledger_row")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_KINDS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["push"] == ("rework", "verify")
    assert TRANSITIONS["verify"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_CHECK == "verify"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_slice_state("ACTIVE") == "active"
    assert normalize_check("PUSH") == "push"
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
    assert legal_step("push", "rework") is True
    assert legal_step("commit", "verify") is False
    assert legal_step("verify", "suite_green") is False
    assert next_check("suite_green") == "commit"
    assert next_check("push") == "verify"
    assert next_check("push", failed=True) == "rework"
    assert next_check("rework") == "push"
    assert next_check("verify") is None
    assert "held as data alone" in BANKING_RULE
    assert "house sequence" in BANKING_RULE
    assert "M-206" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /banking")

def test_shipped_book_judged_honestly_as_data():
    book = load_banking()
    opening = book.banking_for("banking-acceptance-gate")
    assert banking_green(opening, book) is True
    assert banking_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Banking: The acceptance gate banking",
        "Slice: slice-m205-gates",
        "Check: verify",
        "Claims: suite_log")
    asking = book.banking_for("banking-bare-gate")
    assert banking_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: banked stands on held proof alone",)
    assert banking_green(asking, book) is False
    skipping = book.banking_for("banking-leaping-gate")
    assert banking_gaps(skipping, book) == (
        "steps from commit to verify, which the house sequence "
        "does not allow",)
    assert [g.banking_id for g in green_bankings(book)] == [
        "banking-acceptance-gate", "banking-rework-gate", "banking-discipline-gate"]
    index = derive_index(book)
    assert [e.check for e in index.entries] == EXAMPLE_CHECKS
    assert index.gaps == ("banking-bare-gate", "banking-leaping-gate")
    assert banking_for_check(book, EXAMPLE_CHECK).banking_id == (
        "banking-acceptance-gate")
    assert banking_for_check(book, "triple resume") is None
    assert transition_breaks(book) == (
        "banking-leaping-gate: commit > verify",)
    assert [g.banking_id for g in banking_order(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "banking-acceptance-gate") == EXAMPLE_TRACE
    assert trace_current(book, "banking-acceptance-gate") is True
    assert trace_current(book, "banking-rework-gate") is False
    assert trace_for_banking(
        book, "banking-acceptance-gate").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_banking(
        book, "banking-acceptance-gate", "note").note_id == (
            "note-note-first")
    assert note_for_banking(book, "banking-nope") is None
    assert current_banking(book).banking_id == "banking-bare-gate"
    board = board_record(book)
    assert board["standings"] == [
        {"standing": "banked", "bankings": 3},
        {"standing": "unbanked", "bankings": 2}]
    assert board["total"] == 5
    assert board["current_banking"] == "banking-bare-gate"
    assert board["traces"] == [
        {"banking_id": "banking-acceptance-gate", "trace": "current"},
        {"banking_id": "banking-rework-gate", "trace": "unheld"},
        {"banking_id": "banking-discipline-gate", "trace": "unheld"},
        {"banking_id": "banking-bare-gate", "trace": "unheld"},
        {"banking_id": "banking-leaping-gate", "trace": "unheld"}]
    assert board["breaks"] == ["banking-leaping-gate: commit > verify"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 272
    assert citizen["next_slice"] is None
    assert citizen["m206_title"] == "Banking discipline"
    assert citizen["m206_part"] == 9
    assert citizen["m206_status"] == "done"

def test_banking_record_round_trips():
    banking = _banking()
    assert validate_banking(banking) is banking
    rebuilt = build_banking(banking.to_record())
    assert rebuilt == banking
    assert rebuilt.item_id == "banking-test"
    assert rebuilt.check == "verify"
    record = banking_record(banking)
    assert record["type"] == "banking_banking"
    assert record["banked"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert slice_record(ref)["type"] == "banking_slice"
    assert slice_record(ref)["state"] == "active"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _banking(checks=[])
    assert banking_gaps(silent) == (
        "has passed through no law: the banking has not started",)
    assert banking_green(silent) is False
    walking = _banking(checks=["suite_green", "commit"])
    assert banking_gaps(walking) == (
        "has not reached verify: the banking stands at commit",)
    assert walking.check == "commit"
    sideways = _banking(checks=["commit", "push", "verify"])
    assert banking_gaps(sideways) == (
        "opens at commit, not at suite_green: the banking opens "
        "with the suite green",)
    repaired = _banking(checks=[
        "suite_green", "commit", "push", "rework", "push", "verify"])
    assert banking_gaps(repaired) == ()
    assert banking_green(repaired) is True
    with pytest.raises(ValueError):
        _banking(checks=[42])
    with pytest.raises(ValueError):
        _banking(checks="inspect as a bare string")
    with pytest.raises(ValueError):
        _banking(checks=["suite_green", "polish"])
    with pytest.raises(ValueError):
        _banking(claims=["weather"])
    with pytest.raises(ValueError):
        _banking(claims="suite_log")
    none_banking = _banking(checks=None, claims=None)
    assert none_banking.checks == ()
    assert none_banking.claims == ()

def test_banking_refuses_stored_judgements():
    for key in ("standing", "banked", "gaps", "segment", "verdict",
                "index", "entries", "coverage", "current_banking",
                "board", "order"):
        fields = _banking().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_banking(fields)
    fields = _banking().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_banking(fields)


def test_banking_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _banking().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_banking(fields)


def test_banking_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _banking(title="")
    with pytest.raises(ValueError):
        _banking(slice_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "suite_green > commit > push > verify"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_bankings_own_fields():
    banking = _banking(claims=["suite_log"])
    assert plain_lines(banking) == (
        "Banking: A test banking",
        "Slice: slice-test",
        "Check: verify",
        "Claims: suite_log")
    segment = segment_of(banking)
    assert segment.startswith("banking-test: A test banking")
    assert "check: 'verify'" in segment
    assert "gaps: none" in segment
    assert plain_words(banking).startswith(
        "A test banking - from slice-test")

def test_red_bankings_stand_named_in_their_gaps():
    asking = _banking(claims=["feeling", "suite_log", "summary"])
    assert banking_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: banked stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: banked stands on held proof alone")
    assert banking_green(asking) is False
    skipping = _banking(checks=["suite_green", "commit", "verify"])
    assert banking_gaps(skipping) == (
        "steps from commit to verify, which the house sequence "
        "does not allow",)
    book = _book(bankings=[
        _banking(),
        _banking(banking_id="banking-skipping", seq=2,
             checks=["suite_green", "commit", "verify"]),
    ])
    assert transition_breaks(book) == (
        "banking-skipping: commit > verify",)
    assert current_banking(book).banking_id == "banking-skipping"
    assert [g.banking_id for g in banking_order(book)] == [
        "banking-test", "banking-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "banking_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "banking_note"
    assert record["banking_id"] == "banking-test"
    assert view_plain_words(view) == "View view-test: shows all bankings."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_bankings_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.check for e in index.entries] == ["verify"]
    assert index.entries[0] == IndexEntry(
        check="verify",
        banking_id="banking-test", title="A test banking")
    assert index.gaps == ("banking-hidden",)
    record = index_record(book)
    assert record["type"] == "banking_index"
    assert record["gaps"] == ["banking-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "banking_book"

def test_check_target_reaches_its_banking_and_an_unheld_target_reaches_nothing():
    book = load_banking()
    assert banking_for_check(book, "verify").banking_id == (
        "banking-acceptance-gate")
    assert banking_for_check(book, "") is None
    assert banking_for_check(book, None) is None
    assert banking_for_check(book, "not held at all") is None
    text = format_check(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_banking()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Banking note note banking-acceptance-gate" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").banking_id == "banking-test"
    assert note_for_banking(book, "banking-test").note_id == "note-test"
    assert note_for_banking(book, "banking-test", "praise") is None
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
        "banked": 1, "unbanked": 1}
    assert validate_panel(panel, book) is panel
    assert build_panel(panel.to_record(), book) == panel
    row = build_row(None, _banking(), book)
    assert row.standing == "banked"
    assert validate_row(row, _banking(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_bankings():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "banking_verdict"
    green_book = _book(views=[_view(view_filter="banked")])
    assert derive_verdict(green_book).verdict == "verified"
    empty_book = _book(bankings=[_banking(checks=[])],
                       views=[_view(view_filter="banked")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(BankingVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_readings():
    book = load_banking()
    assert [g.banking_id for g in shown_bankings(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.banking_id for g in shown_bankings(book, "view-banked")] == [
        "banking-acceptance-gate", "banking-rework-gate", "banking-discipline-gate"]
    assert [g.banking_id for g in bankings_for_slice(
        book, "slice-m206-banking")] == [
            "banking-discipline-gate", "banking-bare-gate",
            "banking-leaping-gate"]
    assert bankings_for_slice(book, "slice-nope") == ()
    assert current_banking(_mixed_book()).banking_id == "banking-hidden"
    assert current_banking(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "banking-test") == (
        "suite_green > commit > push > verify")
    assert trace_current(stale, "banking-test") is False
    assert board_record(stale)["traces"] == [
        {"banking_id": "banking-test", "trace": "stale"}]

def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(bankings=[_banking(), _banking(seq=2)])
    with pytest.raises(ValueError):
        _book(bankings=[_banking(), _banking(banking_id="banking-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(bankings=[_banking(slice_id="slice-nope")])
    with pytest.raises(ValueError):
        _book(slices=[_ref(), _ref(
            slice_id="slice-cold", seq=2, state="queued")],
            bankings=[_banking(slice_id="slice-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(slice_id="slice-nope")])
    fields = {
        "schema": BANKING_SCHEMA, "slice": "M-206",
        "banking_discipline": {"title": "A judged book"},
        "slices": [_ref().to_record()],
        "bankings": [_banking().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "verified"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_banking"] = "banking-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_banking")
    fields["trace"] = "banking-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / BANKING_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "banking_discipline.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_banking_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.banking_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = BankingRegistry()
    assert registry.title() is None
    registry.register_slice_ref(_ref())
    registry.register_banking(_banking())
    registry.register_view(_view())
    assert [g.banking_id for g in registry.list_bankings()] == ["banking-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_banking("banking-test").title == "A test banking"
    assert registry.get_slice("slice-test").state == "active"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("banking-test").banking_id == "banking-test"
    with pytest.raises(ValueError):
        registry.register_banking(_banking(seq=9))
    with pytest.raises(ValueError):
        registry.register_banking(_banking(banking_id="banking-two"))
    with pytest.raises(KeyError):
        registry.get_banking("banking-nope")
    assert registry.book().title == "An unheld banking book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = BankingRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test banking book"
    assert registry.title() == "A test banking book"
    assert len(registry.list_bankings()) == 2
    other = BankingRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    banking = _banking()
    assert "A test banking" in plain_words(banking)
    assert panel_plain_words(_mixed_book()).startswith(
        "The banking book holds 2 bankings")
    assert verdict_plain_words(_mixed_book()) == (
        "The bankings stand held: 1 of 2 shown bankings stand banked.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green bankings; red, "
        "named in its gaps: banking-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_banking(banking)
    assert "Banking: A test banking" in text
    assert "stands banked" in text
    text = format_banking(_banking(checks=[]))
    assert "stands unbanked" in text
    assert "has passed through no law" in text
    book_text = format_book(_mixed_book())
    assert "The Banking Gate (M-206) - A test banking book" in book_text
    assert "banking-hidden" in format_book(_mixed_book(), "slice-test")
    assert "Banking panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "verify - A test banking (banking-test)" in index_text
    assert "banking-hidden" in index_text
    screen = format_banking_screen()
    assert "The Banking Gate (M-206)" in screen
    assert "banking-bare-gate" in screen

def test_parse_args_board_and_loader_targets():
    assert parse_banking_args("") == ("show", None)
    assert parse_banking_args(None) == ("show", None)
    assert parse_banking_args("show") == ("show", None)
    assert parse_banking_args("banking banking-test") == (
        "banking", "banking-test")
    assert parse_banking_args("check verify") == (
        "check", "verify")
    assert parse_banking_args("slice slice-test") == (
        "slice", "slice-test")
    assert parse_banking_args("view view-test") == ("view", "view-test")
    assert parse_banking_args("note note-test") == ("note", "note-test")
    assert parse_banking_args("index") == ("index", None)
    assert parse_banking_args("panel") == ("panel", None)
    assert parse_banking_args("verdict") == ("verdict", None)
    for bad in ("dance", "banking", "check", "slice", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_banking_args(bad)
    board = board_record()
    assert board["type"] == "banking_board"
    assert board["total"] == 5
    assert board["current_banking"] == "banking-bare-gate"
    book = load_banking({
        "schema": BANKING_SCHEMA, "slice": "M-206",
        "banking_discipline": {"title": "A judged book"},
        "slices": [_ref().to_record()],
        "bankings": [_banking().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, BankingBook)
    assert book.title == "A judged book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_banking({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_banking({"slice": "M-999"})
    built = build_banking(
        banking_id="banking-kw", seq=3, slice_id="slice-test",
        title="Kw Banking", checks=["suite_green", "commit", "push", "verify"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="banking-test")
    assert built.banking_id == "banking-kw"
    assert banking_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-206 agent layer: the agent holds a banking
# book for the session, bankings and views are
# published as session news through the
# checkpoint target (journal first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held bankings, the board is derived from
# the held bankings' bankedness, the roadmap standing
# is read from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no slice. This layer bankings
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session journal news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_BANKING_EVENT_TYPES = (
    "banking_banking", "banking_slice", "banking_view",
    "banking_panel", "banking_verdict")


def _banking_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_banking_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / BANKING_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "banking_discipline.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestBankingAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.banking_status()
        assert status["bankings"] == []
        assert status["slices"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["banking_book"]["title"] == EXAMPLE_TITLE
        assert len(status["banking_book"]["slices"]) == 3
        assert len(status["banking_book"]["bankings"]) == 5
        assert len(status["banking_book"]["views"]) == 2
        assert len(status["banking_book"]["notes"]) == 2
        assert len(status["banking_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-m205-boundary"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["check"] for e in status["index"]["entries"]] == (
            EXAMPLE_CHECKS)
        assert status["index"]["gaps"] == [
            "banking-bare-gate", "banking-leaping-gate"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["board"]["total"] == 5
        assert status["board"]["current_banking"] == "banking-bare-gate"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 272
        assert status["roadmap"]["next_slice"] is None
        assert status["roadmap"]["m206_title"] == "Banking discipline"
        assert "held as data alone" in status["rule"]
        assert "banking-bare-gate" in status["plain_words"]
        assert "The Banking Gate (M-206)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._banking_registry()
        assert agent._banking_registry() is first
        assert agent._banking_store is first
        for name in ("banking_book", "banking_status", "banking_panel",
                     "banking_verdict", "banking_index", "report_banking"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_banking_registry", "banking_book", "banking_status",
            "get_banking_banking", "get_banking_view", "get_banking_note",
            "banking_bankings_for_slice", "banking_bankings_green",
            "banking_panel", "banking_verdict", "banking_index",
            "register_banking_banking", "register_banking_view",
            "view_banking", "register_banking_book",
            "record_banking_book", "report_banking",
            "_publish_banking_record", "_banking_screen",
            "_banking_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.banking_status()
        assert agent.get_banking_banking(
            "banking-acceptance-gate").title == "The acceptance gate banking"
        assert agent.get_banking_view(
            "view-bankings").view_filter == "all"
        assert agent.get_banking_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.banking_id for d in agent.banking_bankings_for_slice(
            "slice-m206-banking")] == [
            "banking-discipline-gate", "banking-bare-gate",
            "banking-leaping-gate"]
        assert [d.banking_id for d in agent.banking_bankings_green()] == [
            "banking-acceptance-gate", "banking-rework-gate", "banking-discipline-gate"]
        agent.banking_panel()
        agent.banking_verdict()
        agent.banking_index()
        agent.report_banking()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _BANKING_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_banking_banking("banking-nope")
        with pytest.raises(KeyError):
            agent.get_banking_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_banking_note("note-nope")
        with pytest.raises(ValueError):
            agent.banking_bankings_for_slice("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_banking_banking(_banking())
        status = agent.banking_status()
        assert [d["banking_id"] for d in status["bankings"]] == ["banking-test"]
        assert status["book"]["title"] == "An unheld banking book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["check"] for e in status["index"]["entries"]] == [
            "verify"]
        assert status["first_note"] is None
        assert "banking-test" in status["screen"]
    def test_held_banking_never_falls_back_to_the_example(
            self, agent):
        agent.register_banking_banking(_banking())
        with pytest.raises(KeyError):
            agent.get_banking_banking("banking-acceptance-gate")
        with pytest.raises(KeyError):
            agent.get_banking_view("view-bankings")
        with pytest.raises(KeyError):
            agent.get_banking_note("note-note-first")
        banking = agent.get_banking_banking("banking-test")
        assert banking.title == "A test banking"
        assert agent.banking_book().title == (
            "An unheld banking book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_banking_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.banking_id == "banking-acceptance-gate"
        status = agent.banking_status()
        assert status["index"]["gaps"] == [
            "banking-bare-gate", "banking-leaping-gate"]
        assert status["first_note"]["banking_id"] == (
            "banking-acceptance-gate")
        assert status["first_note"]["stance"] == "note"

class TestBankingAgentHolding:
    def test_register_banking_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_banking_banking(_banking())
        assert result["banking"]["banking_id"] == "banking-test"
        assert result["record_news"]["type"] == "banking_banking"
        assert "banking-test" in result["screen"]
        events = _banking_events(store, session_id, "banking_banking")
        assert len(events) == 1
        agent.close()

    def test_duplicate_banking_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_banking_banking(_banking())
        with pytest.raises(ValueError):
            agent.register_banking_banking(_banking(seq=9))
        with pytest.raises(ValueError):
            agent.register_banking_banking(_banking(banking_id="banking-two"))
        events = _banking_events(store, session_id, "banking_banking")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_banking_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_banking_events(
            store, session_id, "banking_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_banking_banking(_banking())
        result = agent.view_banking("banked")
        assert result["view"]["view_filter"] == "banked"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "banking_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "verified"
        assert len(_banking_events(
            store, session_id, "banking_view")) == 1
        assert len(_banking_events(
            store, session_id, "banking_panel")) == 1
        assert len(_banking_events(
            store, session_id, "banking_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_banking_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "banking_slice", "banking_banking", "banking_view"]
        assert len(_banking_events(
            store, session_id, "banking_banking")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_banking_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "banking_panel"
        assert result["index_record"]["gaps"] == [
            "banking-bare-gate", "banking-leaping-gate"]
        with pytest.raises(ValueError):
            agent.record_banking_book()
        assert len(_banking_events(
            store, session_id, "banking_slice")) == 3
        assert len(_banking_events(
            store, session_id, "banking_banking")) == 5
        assert len(_banking_events(
            store, session_id, "banking_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_banking_book_file(tmp_path)
        book = load_banking_file(path)
        result = agent.record_banking_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_banking()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "held"
        assert report["index"]["gaps"] == [
            "banking-bare-gate", "banking-leaping-gate"]
        assert "banking-acceptance-gate" in report["book_text"]
        assert "verify - The acceptance gate banking (banking-acceptance-gate)" in report["index_text"]
        agent.register_banking_banking(_banking())
        report = agent.report_banking()
        assert report["book"]["title"] == "An unheld banking book"
        assert report["panel"] is None
        assert report["verdict"] is None

class TestBankingTerminalHeading:
    def test_show_banking_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/banking")
        assert "The Banking Gate (M-206)" in text
        _, _, text = _slash(agent, "/banking banking banking-acceptance-gate")
        assert "Banking: The acceptance gate banking" in text
        _, _, text = _slash(
            agent, "/banking check verify")
        assert "Banking: The acceptance gate banking" in text
        _, _, text = _slash(agent, "/banking check triple resume")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/banking slice slice-m206-banking")
        assert "banking-bare-gate" in text
        assert "banking-acceptance-gate" not in text
        _, _, text = _slash(agent, "/banking view view-bankings")
        assert "filter all" in text
        _, _, text = _slash(agent, "/banking note note-note-first")
        assert "Banking note note banking-acceptance-gate" in text
        _, _, text = _slash(agent, "/banking index")
        assert "Banking index" in text
        assert "banking-bare-gate" in text
        _, _, text = _slash(agent, "/banking panel")
        assert "Banking panel under view view-bankings" in text
        _, _, text = _slash(agent, "/banking verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/banking [show|banking <banking-id>"
                "|check <check>|slice <slice-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/banking dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/banking banking banking-nope")
        assert "no banking named" in text
@pytest.fixture()
def banking_handler(agent, monkeypatch):
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


def _banking_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestBankingCommand:
    def test_show_is_default(self, banking_handler, agent):
        banking_handler._handle_banking("")
        assert "The Banking Gate (M-206)" in (
            _banking_published_text(banking_handler))

    def test_banking_check_slice_view_note_index_panel_verdict(
            self, banking_handler, agent):
        banking_handler._handle_banking("banking banking-acceptance-gate")
        assert "Banking: The acceptance gate banking" in _banking_published_text(
            banking_handler)
        banking_handler._handle_banking(
            "check verify")
        assert "Banking: The acceptance gate banking" in _banking_published_text(
            banking_handler)
        banking_handler._handle_banking("slice slice-m206-banking")
        assert "banking-bare-gate" in _banking_published_text(
            banking_handler)
        banking_handler._handle_banking("view view-bankings")
        assert "filter all" in _banking_published_text(banking_handler)
        banking_handler._handle_banking("note note-note-first")
        assert "Banking note note banking-acceptance-gate" in (
            _banking_published_text(banking_handler))
        banking_handler._handle_banking("index")
        assert "Banking index" in _banking_published_text(banking_handler)
        banking_handler._handle_banking("panel")
        assert "Banking panel under view" in _banking_published_text(
            banking_handler)
        banking_handler._handle_banking("verdict")
        assert "held" in _banking_published_text(banking_handler)
    def test_bad_grammar_is_published(
            self, banking_handler, agent):
        banking_handler._handle_banking("dance party")
        assert USAGE in _banking_published_text(banking_handler)
        banking_handler._handle_banking("banking banking-nope")
        assert "no banking named" in _banking_published_text(
            banking_handler)


class TestChatScreenRoutingBanking:
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
        screen.handle_command("/banking panel", _FakeLog())
        assert calls == [("/banking", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/banking[/green] - show the Banking gate (M-206)" in (
            text)
        assert ('"/banking": "Usage: /banking | '
                '/banking banking <banking-id>') in text

class TestBankingDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.banking_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-bankings"
        verdict = agent.banking_verdict()
        assert verdict.verdict == "held"
        found = agent.banking_verdict("view-banked")
        assert found.verdict == "verified"
        assert found.green_shown == 3
        agent.register_banking_banking(_banking())
        with pytest.raises(ValueError):
            agent.banking_panel()
        with pytest.raises(ValueError):
            agent.banking_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_banking_banking(_banking(checks=[]))
        result = agent.view_banking("banked")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.banking_index()
        assert [e["check"] for e in result["index"]["entries"]] == (
            EXAMPLE_CHECKS)
        assert result["index"]["gaps"] == [
            "banking-bare-gate", "banking-leaping-gate"]
        assert "verify - The acceptance gate banking (banking-acceptance-gate)" in (
            result["index_text"])
        banking = agent.get_banking_banking("banking-leaping-gate")
        assert banking_gaps(banking, agent.banking_book()) == (
            "steps from commit to verify, which the house sequence "
            "does not allow",)
        assert banking_green(banking, agent.banking_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _BANKING_EVENT_TYPES] == []
        agent.close()
