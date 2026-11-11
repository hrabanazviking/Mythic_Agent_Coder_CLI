"""M-210 Question Law - pure-layer tests.

TIER: integration

The pure layer is the watcher, held as data: one
record per sentry, held whole - the slice it
answers for, named by slice id, its title, the
steps it walked in walk order and the evidence
it carries, held by kind. The question walk is
explicit - named, observed, judged, halted,
reported, with their legal steps held as data -
and a sentry's standing is derived at call
time: a sentry that opens anywhere but
named, steps where the sequence does not allow,
carries a bare claim in place of held evidence,
or has not yet reached reported stands open,
named in its gaps. A sentry stands only for
an active slice: a sentry naming no held
slice, or one that is not active, refuses by
name. The sentry's trace - its walked steps
as one line - is derived at call time, and a held
trace record stands current only while it agrees
with the derived trace. The index, panel,
verdict, board, trace, order and current
sentry are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
question was actually answered, halted or
reported live. The shipped example book is held
in a data file, and a loader reads a book from
any file. No charter row names this slice: the
M-171 TUI charter binds Part VIII alone, and the
M-005 method charter names the whole of Part IX
as the part that executes it, both pinned live
below.
"""


from pathlib import Path

import pytest
import yaml

from mythic_agent.core.scope_sentry import (
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
    SENTRY_RESOURCE,
    SENTRY_RULE,
    SENTRY_SCHEMA,
    SENTRY_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    SentryRecord,
    IndexEntry,
    SliceRef,
    NoteRecord,
    SentryBook,
    SentryIndex,
    SentryPanel,
    SentryRegistry,
    SentryVerdict,
    SentryView,
    trace_for_sentry,
    board_record,
    book_record,
    build_trace,
    build_book,
    build_sentry,
    build_slice_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_sentry,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    sentry_for_check,
    sentry_gaps,
    sentry_order,
    sentry_record,
    sentry_green,
    sentries_for_slice,
    first_note,
    format_book,
    format_sentry,
    format_index,
    format_note,
    format_check,
    format_panel,
    format_sentry_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    slice_record,
    load_sentry,
    legal_step,
    load_sentry_file,
    next_check,
    normalize_check,
    normalize_claim_kind,
    normalize_slice_state,
    normalize_stance,
    normalize_view_filter,
    note_for_sentry,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_sentry_args,
    green_sentries,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_sentries,
    validate_book,
    validate_sentry,
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
EXAMPLE_TITLE = "The scope sentry at the M-209 slice boundary"
EXAMPLE_CHECKS = ["reported", "reported", "reported"]
EXAMPLE_RUN_IDS = (
    "sentry-held-watch", "sentry-rechecked-watch",
    "sentry-own-watch", "sentry-bare-watch",
    "sentry-leaping-watch")
EXAMPLE_TRACE = "named > observed > judged > halted > reported"


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
        "origin_session": "sentry-test",
    }
    fields.update(overrides)
    return build_slice_ref(fields)


def _sentry(**overrides):
    fields = {
        "sentry_id": "sentry-test",
        "seq": 1,
        "slice_id": "slice-test",
        "title": "A test sentry",
        "checks": ["named", "observed", "judged", "halted", "reported"],
        "claims": [],
        "detail": "A test sentry held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "sentry-test",
    }
    fields.update(overrides)
    return build_sentry(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "sentry-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "sentry_id": "sentry-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "sentry-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "sentry_id": "sentry-test",
        "trace": "named > observed > judged > halted > reported",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "sentry-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(slices=None, sentries=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": SENTRY_SCHEMA,
        "slice": "M-210",
        "scope_sentry": {"title": "A test sentry book"},
        "slices": [item.to_record() for item in (
            slices if slices is not None else [_ref()])],
        "sentries": [item.to_record() for item in (
            sentries if sentries is not None else [_sentry()])],
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
    return _book(sentries=[
        _sentry(),
        _sentry(sentry_id="sentry-hidden", seq=2,
               title="A hidden sentry", checks=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_sentry()
    assert book.title == EXAMPLE_TITLE
    assert book.sentry_ids() == EXAMPLE_RUN_IDS
    assert book.slice_ids() == (
        "slice-m209-question", "slice-m210-scope",
        "slice-m211-memory")
    assert [v.view_id for v in book.views] == [
        "view-sentries", "view-reported"]
    assert [m.sentry_id for m in book.notes] == [
        "sentry-held-watch", "sentry-bare-watch"]
    assert [a.sentry_id for a in book.traces] == ["sentry-held-watch"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m209-boundary"
    assert panel.as_of == "2026-11-10"
    assert [row.item_id for row in panel.rows] == list(book.sentry_ids())
    derived = derive_panel(book, "view-sentries")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-sentries").verdict == "held"
    assert derive_verdict(book, "view-sentries").green_shown == 3
    assert derive_verdict(book, "view-reported").verdict == "reported"
    assert derive_verdict(book, "view-reported").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / SENTRY_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == SENTRY_SCHEMA
    assert raw["slice"] == "M-210"
    assert "verdict" not in raw
    assert "sentry_index" not in raw
    assert "board" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-210")]
    assert slice_.title == "Scope sentry"
    assert slice_.part == 9
    assert "work drifting beyond the named target" in slice_.summary
    assert "wrong repo, wrong branch, extra features unasked" in slice_.summary
    assert "caught against the campaign file" in slice_.summary
    assert "stopped with a report" in slice_.summary
    assert SENTRY_SLICE == "M-210"

def test_charter_rows_do_not_name_m210():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-210" not in owners
    method = load_method_charter()
    assert "M-201" in method.source_note
    assert "M-232" in method.source_note
    assert "YRSA_CODING_JUGGERNAUT" in method.source_note

def test_closed_vocabularies():
    assert COMPLETE_WORDS == ("complete", "open")
    assert CHECK_FIELDS == ("checks", "claims")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "complete", "open")
    assert VERDICT_WORDS == ("reported", "held", "blocked")
    assert SLICE_STATES == ("active", "queued")
    assert CHECKS == ("named", "observed", "judged", "halted", "reported")
    assert HELD_EVIDENCE == ("campaign_ref", "target_ref", "drift_report", "ledger_row")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_KINDS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["halted"] == ("named", "reported")
    assert TRANSITIONS["reported"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_CHECK == "reported"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_slice_state("ACTIVE") == "active"
    assert normalize_check("JUDGED") == "judged"
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
    assert legal_step("judged", "halted") is True
    assert legal_step("observed", "reported") is False
    assert legal_step("reported", "named") is False
    assert next_check("named") == "observed"
    assert next_check("judged") == "halted"
    assert next_check("halted", failed=True) == "named"
    assert next_check("halted") == "reported"
    assert next_check("reported") is None
    assert "held as data alone" in SENTRY_RULE
    assert "sentry sequence" in SENTRY_RULE
    assert "M-210" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /scopesentry")

def test_shipped_book_judged_honestly_as_data():
    book = load_sentry()
    opening = book.sentry_for("sentry-held-watch")
    assert sentry_green(opening, book) is True
    assert sentry_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Sentry: The held watch",
        "Slice: slice-m209-question",
        "Check: reported",
        "Claims: campaign_ref")
    asking = book.sentry_for("sentry-bare-watch")
    assert sentry_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert sentry_green(asking, book) is False
    skipping = book.sentry_for("sentry-leaping-watch")
    assert sentry_gaps(skipping, book) == (
        "steps from observed to reported, which the sentry sequence "
        "does not allow",)
    assert [g.sentry_id for g in green_sentries(book)] == [
        "sentry-held-watch", "sentry-rechecked-watch", "sentry-own-watch"]
    index = derive_index(book)
    assert [e.check for e in index.entries] == EXAMPLE_CHECKS
    assert index.gaps == ("sentry-bare-watch", "sentry-leaping-watch")
    assert sentry_for_check(book, EXAMPLE_CHECK).sentry_id == (
        "sentry-held-watch")
    assert sentry_for_check(book, "triple resume") is None
    assert transition_breaks(book) == (
        "sentry-leaping-watch: observed > reported",)
    assert [g.sentry_id for g in sentry_order(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "sentry-held-watch") == EXAMPLE_TRACE
    assert trace_current(book, "sentry-held-watch") is True
    assert trace_current(book, "sentry-rechecked-watch") is False
    assert trace_for_sentry(
        book, "sentry-held-watch").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_sentry(
        book, "sentry-held-watch", "note").note_id == (
            "note-note-first")
    assert note_for_sentry(book, "sentry-nope") is None
    assert current_sentry(book).sentry_id == "sentry-bare-watch"
    board = board_record(book)
    assert board["standings"] == [
        {"standing": "complete", "sentries": 3},
        {"standing": "open", "sentries": 2}]
    assert board["total"] == 5
    assert board["current_sentry"] == "sentry-bare-watch"
    assert board["traces"] == [
        {"sentry_id": "sentry-held-watch", "trace": "current"},
        {"sentry_id": "sentry-rechecked-watch", "trace": "unheld"},
        {"sentry_id": "sentry-own-watch", "trace": "unheld"},
        {"sentry_id": "sentry-bare-watch", "trace": "unheld"},
        {"sentry_id": "sentry-leaping-watch", "trace": "unheld"}]
    assert board["breaks"] == ["sentry-leaping-watch: observed > reported"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 220
    assert citizen["next_slice"] == "M-221"
    assert citizen["m210_title"] == "Scope sentry"
    assert citizen["m210_part"] == 9
    assert citizen["m210_status"] == "done"

def test_sentry_record_round_trips():
    sentry = _sentry()
    assert validate_sentry(sentry) is sentry
    rebuilt = build_sentry(sentry.to_record())
    assert rebuilt == sentry
    assert rebuilt.item_id == "sentry-test"
    assert rebuilt.check == "reported"
    record = sentry_record(sentry)
    assert record["type"] == "sentry_sentry"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert slice_record(ref)["type"] == "sentry_slice"
    assert slice_record(ref)["state"] == "active"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _sentry(checks=[])
    assert sentry_gaps(silent) == (
        "has passed through no step: the sentry has not started",)
    assert sentry_green(silent) is False
    walking = _sentry(checks=["named", "observed"])
    assert sentry_gaps(walking) == (
        "has not reached reported: the sentry stands at observed",)
    assert walking.check == "observed"
    sideways = _sentry(checks=["observed", "judged", "halted", "reported"])
    assert sentry_gaps(sideways) == (
        "opens at observed, not at named: the sentry opens "
        "with the question",)
    repaired = _sentry(checks=["named", "observed", "judged", "halted", "named", "observed", "judged", "halted", "reported"])
    assert sentry_gaps(repaired) == ()
    assert sentry_green(repaired) is True
    with pytest.raises(ValueError):
        _sentry(checks=[42])
    with pytest.raises(ValueError):
        _sentry(checks="inspect as a bare string")
    with pytest.raises(ValueError):
        _sentry(checks=["named", "polish"])
    with pytest.raises(ValueError):
        _sentry(claims=["weather"])
    with pytest.raises(ValueError):
        _sentry(claims="campaign_ref")
    none_sentry = _sentry(checks=None, claims=None)
    assert none_sentry.checks == ()
    assert none_sentry.claims == ()

def test_sentry_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "entries", "coverage", "current_sentry",
                "board", "order"):
        fields = _sentry().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_sentry(fields)
    fields = _sentry().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_sentry(fields)


def test_sentry_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _sentry().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_sentry(fields)


def test_sentry_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _sentry(title="")
    with pytest.raises(ValueError):
        _sentry(slice_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "named > observed > judged > halted > reported"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_sentries_own_fields():
    sentry = _sentry(claims=["campaign_ref"])
    assert plain_lines(sentry) == (
        "Sentry: A test sentry",
        "Slice: slice-test",
        "Check: reported",
        "Claims: campaign_ref")
    segment = segment_of(sentry)
    assert segment.startswith("sentry-test: A test sentry")
    assert "check: 'reported'" in segment
    assert "gaps: none" in segment
    assert plain_words(sentry).startswith(
        "A test sentry - from slice-test")

def test_red_sentries_stand_named_in_their_gaps():
    asking = _sentry(claims=["feeling", "campaign_ref", "summary"])
    assert sentry_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert sentry_green(asking) is False
    skipping = _sentry(checks=["named", "observed", "reported"])
    assert sentry_gaps(skipping) == (
        "steps from observed to reported, which the sentry sequence "
        "does not allow",)
    book = _book(sentries=[
        _sentry(),
        _sentry(sentry_id="sentry-skipping", seq=2,
             checks=["named", "observed", "reported"]),
    ])
    assert transition_breaks(book) == (
        "sentry-skipping: observed > reported",)
    assert current_sentry(book).sentry_id == "sentry-skipping"
    assert [g.sentry_id for g in sentry_order(book)] == [
        "sentry-test", "sentry-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "sentry_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "sentry_note"
    assert record["sentry_id"] == "sentry-test"
    assert view_plain_words(view) == "View view-test: shows all sentries."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_sentries_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.check for e in index.entries] == ["reported"]
    assert index.entries[0] == IndexEntry(
        check="reported",
        sentry_id="sentry-test", title="A test sentry")
    assert index.gaps == ("sentry-hidden",)
    record = index_record(book)
    assert record["type"] == "sentry_index"
    assert record["gaps"] == ["sentry-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "sentry_book"

def test_check_target_reaches_its_sentry_and_an_unheld_target_reaches_nothing():
    book = load_sentry()
    assert sentry_for_check(book, "reported").sentry_id == (
        "sentry-held-watch")
    assert sentry_for_check(book, "") is None
    assert sentry_for_check(book, None) is None
    assert sentry_for_check(book, "not held at all") is None
    text = format_check(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_sentry()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Sentry note note sentry-held-watch" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").sentry_id == "sentry-test"
    assert note_for_sentry(book, "sentry-test").note_id == "note-test"
    assert note_for_sentry(book, "sentry-test", "praise") is None
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
    row = build_row(None, _sentry(), book)
    assert row.standing == "complete"
    assert validate_row(row, _sentry(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_sentries():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "sentry_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "reported"
    empty_book = _book(sentries=[_sentry(checks=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(SentryVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_readings():
    book = load_sentry()
    assert [g.sentry_id for g in shown_sentries(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.sentry_id for g in shown_sentries(book, "view-reported")] == [
        "sentry-held-watch", "sentry-rechecked-watch", "sentry-own-watch"]
    assert [g.sentry_id for g in sentries_for_slice(
        book, "slice-m210-scope")] == [
            "sentry-own-watch", "sentry-bare-watch",
            "sentry-leaping-watch"]
    assert sentries_for_slice(book, "slice-nope") == ()
    assert current_sentry(_mixed_book()).sentry_id == "sentry-hidden"
    assert current_sentry(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "sentry-test") == (
        "named > observed > judged > halted > reported")
    assert trace_current(stale, "sentry-test") is False
    assert board_record(stale)["traces"] == [
        {"sentry_id": "sentry-test", "trace": "stale"}]

def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(sentries=[_sentry(), _sentry(seq=2)])
    with pytest.raises(ValueError):
        _book(sentries=[_sentry(), _sentry(sentry_id="sentry-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(sentries=[_sentry(slice_id="slice-nope")])
    with pytest.raises(ValueError):
        _book(slices=[_ref(), _ref(
            slice_id="slice-cold", seq=2, state="queued")],
            sentries=[_sentry(slice_id="slice-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(slice_id="slice-nope")])
    fields = {
        "schema": SENTRY_SCHEMA, "slice": "M-210",
        "scope_sentry": {"title": "A judged book"},
        "slices": [_ref().to_record()],
        "sentries": [_sentry().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "reported"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_sentry"] = "sentry-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_sentry")
    fields["trace"] = "sentry-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / SENTRY_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "scope_sentry.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_sentry_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.sentry_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = SentryRegistry()
    assert registry.title() is None
    registry.register_slice_ref(_ref())
    registry.register_sentry(_sentry())
    registry.register_view(_view())
    assert [g.sentry_id for g in registry.list_sentries()] == ["sentry-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_sentry("sentry-test").title == "A test sentry"
    assert registry.get_slice("slice-test").state == "active"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("sentry-test").sentry_id == "sentry-test"
    with pytest.raises(ValueError):
        registry.register_sentry(_sentry(seq=9))
    with pytest.raises(ValueError):
        registry.register_sentry(_sentry(sentry_id="sentry-two"))
    with pytest.raises(KeyError):
        registry.get_sentry("sentry-nope")
    assert registry.book().title == "An unheld sentry book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = SentryRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test sentry book"
    assert registry.title() == "A test sentry book"
    assert len(registry.list_sentries()) == 2
    other = SentryRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    sentry = _sentry()
    assert "A test sentry" in plain_words(sentry)
    assert panel_plain_words(_mixed_book()).startswith(
        "The sentry book holds 2 sentries")
    assert verdict_plain_words(_mixed_book()) == (
        "The sentries stand held: 1 of 2 shown sentries stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green sentries; red, "
        "named in its gaps: sentry-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_sentry(sentry)
    assert "Sentry: A test sentry" in text
    assert "stands complete" in text
    text = format_sentry(_sentry(checks=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The Scope Gate (M-210) - A test sentry book" in book_text
    assert "sentry-hidden" in format_book(_mixed_book(), "slice-test")
    assert "Sentry panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "reported - A test sentry (sentry-test)" in index_text
    assert "sentry-hidden" in index_text
    screen = format_sentry_screen()
    assert "The Scope Gate (M-210)" in screen
    assert "sentry-bare-watch" in screen

def test_parse_args_board_and_loader_targets():
    assert parse_sentry_args("") == ("show", None)
    assert parse_sentry_args(None) == ("show", None)
    assert parse_sentry_args("show") == ("show", None)
    assert parse_sentry_args("sentry sentry-test") == (
        "sentry", "sentry-test")
    assert parse_sentry_args("check reported") == (
        "check", "reported")
    assert parse_sentry_args("slice slice-test") == (
        "slice", "slice-test")
    assert parse_sentry_args("view view-test") == ("view", "view-test")
    assert parse_sentry_args("note note-test") == ("note", "note-test")
    assert parse_sentry_args("index") == ("index", None)
    assert parse_sentry_args("panel") == ("panel", None)
    assert parse_sentry_args("verdict") == ("verdict", None)
    for bad in ("dance", "sentry", "check", "slice", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_sentry_args(bad)
    board = board_record()
    assert board["type"] == "sentry_board"
    assert board["total"] == 5
    assert board["current_sentry"] == "sentry-bare-watch"
    book = load_sentry({
        "schema": SENTRY_SCHEMA, "slice": "M-210",
        "scope_sentry": {"title": "A judged book"},
        "slices": [_ref().to_record()],
        "sentries": [_sentry().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, SentryBook)
    assert book.title == "A judged book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_sentry({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_sentry({"slice": "M-999"})
    built = build_sentry(
        sentry_id="sentry-kw", seq=3, slice_id="slice-test",
        title="Kw Sentry", checks=["named", "observed", "judged", "halted", "reported"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="sentry-test")
    assert built.sentry_id == "sentry-kw"
    assert sentry_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-210 agent layer: the agent holds a sentry
# book for the session, sentries and views are
# published as session news through the
# checkpoint target (journal first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held sentries, the board is derived from
# the held sentries' completeness, the roadmap standing
# is read from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no slice. This layer sentries
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session journal news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_SENTRY_EVENT_TYPES = (
    "sentry_sentry", "sentry_slice", "sentry_view",
    "sentry_panel", "sentry_verdict")


def _sentry_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_sentry_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / SENTRY_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "scope_sentry.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestSentryAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.sentry_status()
        assert status["sentries"] == []
        assert status["slices"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["sentry_book"]["title"] == EXAMPLE_TITLE
        assert len(status["sentry_book"]["slices"]) == 3
        assert len(status["sentry_book"]["sentries"]) == 5
        assert len(status["sentry_book"]["views"]) == 2
        assert len(status["sentry_book"]["notes"]) == 2
        assert len(status["sentry_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-m209-boundary"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["check"] for e in status["index"]["entries"]] == (
            EXAMPLE_CHECKS)
        assert status["index"]["gaps"] == [
            "sentry-bare-watch", "sentry-leaping-watch"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["board"]["total"] == 5
        assert status["board"]["current_sentry"] == "sentry-bare-watch"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 220
        assert status["roadmap"]["next_slice"] == "M-221"
        assert status["roadmap"]["m210_title"] == "Scope sentry"
        assert "held as data alone" in status["rule"]
        assert "sentry-bare-watch" in status["plain_words"]
        assert "The Scope Gate (M-210)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._sentry_registry()
        assert agent._sentry_registry() is first
        assert agent._sentry_store is first
        for name in ("sentry_book", "sentry_status", "sentry_panel",
                     "sentry_verdict", "sentry_index", "report_sentry"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_sentry_registry", "sentry_book", "sentry_status",
            "get_sentry_sentry", "get_sentry_view", "get_sentry_note",
            "sentry_sentries_for_slice", "sentry_sentries_green",
            "sentry_panel", "sentry_verdict", "sentry_index",
            "register_sentry_sentry", "register_sentry_view",
            "view_sentry", "register_sentry_book",
            "record_sentry_book", "report_sentry",
            "_publish_sentry_record", "_sentry_screen",
            "_sentry_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.sentry_status()
        assert agent.get_sentry_sentry(
            "sentry-held-watch").title == "The held watch"
        assert agent.get_sentry_view(
            "view-sentries").view_filter == "all"
        assert agent.get_sentry_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.sentry_id for d in agent.sentry_sentries_for_slice(
            "slice-m210-scope")] == [
            "sentry-own-watch", "sentry-bare-watch",
            "sentry-leaping-watch"]
        assert [d.sentry_id for d in agent.sentry_sentries_green()] == [
            "sentry-held-watch", "sentry-rechecked-watch", "sentry-own-watch"]
        agent.sentry_panel()
        agent.sentry_verdict()
        agent.sentry_index()
        agent.report_sentry()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _SENTRY_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_sentry_sentry("sentry-nope")
        with pytest.raises(KeyError):
            agent.get_sentry_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_sentry_note("note-nope")
        with pytest.raises(ValueError):
            agent.sentry_sentries_for_slice("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_sentry_sentry(_sentry())
        status = agent.sentry_status()
        assert [d["sentry_id"] for d in status["sentries"]] == ["sentry-test"]
        assert status["book"]["title"] == "An unheld sentry book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["check"] for e in status["index"]["entries"]] == [
            "reported"]
        assert status["first_note"] is None
        assert "sentry-test" in status["screen"]
    def test_held_sentry_never_falls_back_to_the_example(
            self, agent):
        agent.register_sentry_sentry(_sentry())
        with pytest.raises(KeyError):
            agent.get_sentry_sentry("sentry-held-watch")
        with pytest.raises(KeyError):
            agent.get_sentry_view("view-sentries")
        with pytest.raises(KeyError):
            agent.get_sentry_note("note-note-first")
        sentry = agent.get_sentry_sentry("sentry-test")
        assert sentry.title == "A test sentry"
        assert agent.sentry_book().title == (
            "An unheld sentry book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_sentry_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.sentry_id == "sentry-held-watch"
        status = agent.sentry_status()
        assert status["index"]["gaps"] == [
            "sentry-bare-watch", "sentry-leaping-watch"]
        assert status["first_note"]["sentry_id"] == (
            "sentry-held-watch")
        assert status["first_note"]["stance"] == "note"

class TestSentryAgentHolding:
    def test_register_sentry_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_sentry_sentry(_sentry())
        assert result["sentry"]["sentry_id"] == "sentry-test"
        assert result["record_news"]["type"] == "sentry_sentry"
        assert "sentry-test" in result["screen"]
        events = _sentry_events(store, session_id, "sentry_sentry")
        assert len(events) == 1
        agent.close()

    def test_duplicate_sentry_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_sentry_sentry(_sentry())
        with pytest.raises(ValueError):
            agent.register_sentry_sentry(_sentry(seq=9))
        with pytest.raises(ValueError):
            agent.register_sentry_sentry(_sentry(sentry_id="sentry-two"))
        events = _sentry_events(store, session_id, "sentry_sentry")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_sentry_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_sentry_events(
            store, session_id, "sentry_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_sentry_sentry(_sentry())
        result = agent.view_sentry("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "sentry_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "reported"
        assert len(_sentry_events(
            store, session_id, "sentry_view")) == 1
        assert len(_sentry_events(
            store, session_id, "sentry_panel")) == 1
        assert len(_sentry_events(
            store, session_id, "sentry_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_sentry_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "sentry_slice", "sentry_sentry", "sentry_view"]
        assert len(_sentry_events(
            store, session_id, "sentry_sentry")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_sentry_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "sentry_panel"
        assert result["index_record"]["gaps"] == [
            "sentry-bare-watch", "sentry-leaping-watch"]
        with pytest.raises(ValueError):
            agent.record_sentry_book()
        assert len(_sentry_events(
            store, session_id, "sentry_slice")) == 3
        assert len(_sentry_events(
            store, session_id, "sentry_sentry")) == 5
        assert len(_sentry_events(
            store, session_id, "sentry_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_sentry_book_file(tmp_path)
        book = load_sentry_file(path)
        result = agent.record_sentry_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_sentry()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "held"
        assert report["index"]["gaps"] == [
            "sentry-bare-watch", "sentry-leaping-watch"]
        assert "sentry-held-watch" in report["book_text"]
        assert "reported - The held watch (sentry-held-watch)" in report["index_text"]
        agent.register_sentry_sentry(_sentry())
        report = agent.report_sentry()
        assert report["book"]["title"] == "An unheld sentry book"
        assert report["panel"] is None
        assert report["verdict"] is None

class TestSentryTerminalHeading:
    def test_show_sentry_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/scopesentry")
        assert "The Scope Gate (M-210)" in text
        _, _, text = _slash(agent, "/scopesentry sentry sentry-held-watch")
        assert "Sentry: The held watch" in text
        _, _, text = _slash(
            agent, "/scopesentry check reported")
        assert "Sentry: The held watch" in text
        _, _, text = _slash(agent, "/scopesentry check triple resume")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/scopesentry slice slice-m210-scope")
        assert "sentry-bare-watch" in text
        assert "sentry-held-watch" not in text
        _, _, text = _slash(agent, "/scopesentry view view-sentries")
        assert "filter all" in text
        _, _, text = _slash(agent, "/scopesentry note note-note-first")
        assert "Sentry note note sentry-held-watch" in text
        _, _, text = _slash(agent, "/scopesentry index")
        assert "Sentry index" in text
        assert "sentry-bare-watch" in text
        _, _, text = _slash(agent, "/scopesentry panel")
        assert "Sentry panel under view view-sentries" in text
        _, _, text = _slash(agent, "/scopesentry verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/scopesentry [show|sentry <sentry-id>"
                "|check <check>|slice <slice-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/scopesentry dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/scopesentry sentry sentry-nope")
        assert "no sentry named" in text
@pytest.fixture()
def sentry_handler(agent, monkeypatch):
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


def _sentry_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestSentryCommand:
    def test_show_is_default(self, sentry_handler, agent):
        sentry_handler._handle_sentry("")
        assert "The Scope Gate (M-210)" in (
            _sentry_published_text(sentry_handler))

    def test_sentry_check_slice_view_note_index_panel_verdict(
            self, sentry_handler, agent):
        sentry_handler._handle_sentry("sentry sentry-held-watch")
        assert "Sentry: The held watch" in _sentry_published_text(
            sentry_handler)
        sentry_handler._handle_sentry(
            "check reported")
        assert "Sentry: The held watch" in _sentry_published_text(
            sentry_handler)
        sentry_handler._handle_sentry("slice slice-m210-scope")
        assert "sentry-bare-watch" in _sentry_published_text(
            sentry_handler)
        sentry_handler._handle_sentry("view view-sentries")
        assert "filter all" in _sentry_published_text(sentry_handler)
        sentry_handler._handle_sentry("note note-note-first")
        assert "Sentry note note sentry-held-watch" in (
            _sentry_published_text(sentry_handler))
        sentry_handler._handle_sentry("index")
        assert "Sentry index" in _sentry_published_text(sentry_handler)
        sentry_handler._handle_sentry("panel")
        assert "Sentry panel under view" in _sentry_published_text(
            sentry_handler)
        sentry_handler._handle_sentry("verdict")
        assert "held" in _sentry_published_text(sentry_handler)
    def test_bad_grammar_is_published(
            self, sentry_handler, agent):
        sentry_handler._handle_sentry("dance party")
        assert USAGE in _sentry_published_text(sentry_handler)
        sentry_handler._handle_sentry("sentry sentry-nope")
        assert "no sentry named" in _sentry_published_text(
            sentry_handler)


class TestChatScreenRoutingSentry:
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
        screen.handle_command("/scopesentry panel", _FakeLog())
        assert calls == [("/scopesentry", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/scopesentry[/green] - show the Scope gate (M-210)" in (
            text)
        assert ('"/scopesentry": "Usage: /scopesentry | '
                '/scopesentry sentry <sentry-id>') in text

class TestSentryDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.sentry_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-sentries"
        verdict = agent.sentry_verdict()
        assert verdict.verdict == "held"
        found = agent.sentry_verdict("view-reported")
        assert found.verdict == "reported"
        assert found.green_shown == 3
        agent.register_sentry_sentry(_sentry())
        with pytest.raises(ValueError):
            agent.sentry_panel()
        with pytest.raises(ValueError):
            agent.sentry_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_sentry_sentry(_sentry(checks=[]))
        result = agent.view_sentry("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.sentry_index()
        assert [e["check"] for e in result["index"]["entries"]] == (
            EXAMPLE_CHECKS)
        assert result["index"]["gaps"] == [
            "sentry-bare-watch", "sentry-leaping-watch"]
        assert "reported - The held watch (sentry-held-watch)" in (
            result["index_text"])
        sentry = agent.get_sentry_sentry("sentry-leaping-watch")
        assert sentry_gaps(sentry, agent.sentry_book()) == (
            "steps from observed to reported, which the sentry sequence "
            "does not allow",)
        assert sentry_green(sentry, agent.sentry_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _SENTRY_EVENT_TYPES] == []
        agent.close()
