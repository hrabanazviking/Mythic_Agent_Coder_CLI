"""M-235 Cross-app method - pure-layer tests.

TIER: integration

The pure layer is the tracker, held as data: one
record per listing, held whole - the entry it
answers for, listed by entry id, its title, the
steps it walked in walk listing and the evidence
it carries, held by entry. The question walk is
explicit - listed, browsed, reviewed, decided,
held, with their legal steps held as data -
and a listing's standing is derived at call
time: a listing that opens anywhere but listed, steps where the sequence does not allow,
carries a bare claim in place of held evidence,
or has not yet listed held stands open,
listed in its gaps. A listing stands only for
an active entry: a listing naming no held
entry, or one that is not active, refuses by
name. The listing's trace - its walked steps
as one line - is derived at call time, and a held
trace record stands current only while it agrees
with the derived trace. The index, panel,
verdict, ledger, trace, listing and current
listing are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
question was actually answered, decided or
held live. The shipped example book is held
in a data file, and a loader reads a book from
any file. No charter row names this entry: the
M-171 TUI charter binds Part VIII alone, and the
M-005 method charter names the whole of Part X
as the part that executes it, both pinned live
below.
"""


from pathlib import Path

import pytest
import yaml

from mythic_agent.core.mcp_registry import (
    EXAMPLE_STAGE,
    BARE_CLAIMS,
    HELD_EVIDENCE,
    INDEX_ACTION,
    STAGES,
    CLAIM_KINDS,
    TRANSITIONS,
    ENTRY_STATES,
    STAGE_FIELDS,
    PLAIN_EXPLANATION,
    LISTING_RESOURCE,
    LISTING_RULE,
    LISTING_SCHEMA,
    LISTING_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    ListingRecord,
    IndexListing,
    EntryRef,
    NoteRecord,
    ListingBook,
    ListingIndex,
    ListingPanel,
    ListingRegistry,
    ListingVerdict,
    ListingView,
    trace_for_listing,
    ledger_record,
    book_record,
    build_trace,
    build_book,
    build_listing,
    build_entry_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_listing,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    listing_for_check,
    listing_gaps,
    listing_listing,
    listing_record,
    listing_green,
    listings_for_entry,
    first_note,
    format_book,
    format_listing,
    format_index,
    format_note,
    format_stage,
    format_panel,
    format_listing_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    entry_record,
    load_listing,
    legal_step,
    load_listing_file,
    next_stage,
    normalize_stage,
    normalize_claim_kind,
    normalize_entry_state,
    normalize_stance,
    normalize_view_filter,
    note_for_listing,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_listing_args,
    green_listings,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_listings,
    validate_book,
    validate_listing,
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
EXAMPLE_TITLE = "MCP registry at the M-235 slice run"
EXAMPLE_STAGES = ["held", "held", "held"]
EXAMPLE_RUN_IDS = (
    "listing-held-listing", "listing-retried-listing",
    "listing-own-listing", "listing-bare-listing",
    "listing-leaping-listing")
EXAMPLE_TRACE = "listed > browsed > reviewed > decided > held"


def _ref(**overrides):
    fields = {
        "entry_id": "entry-test",
        "seq": 1,
        "title": "A test entry",
        "state": "live",
        "detail": "A test entry reference held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "listing-test",
    }
    fields.update(overrides)
    return build_entry_ref(fields)


def _listing(**overrides):
    fields = {
        "listing_id": "listing-test",
        "seq": 1,
        "entry_id": "entry-test",
        "title": "A test listing",
        "stages": ["listed", "browsed", "reviewed", "decided", "held"],
        "claims": [],
        "detail": "A test listing held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "listing-test",
    }
    fields.update(overrides)
    return build_listing(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "listing-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "listing_id": "listing-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "listing-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "listing_id": "listing-test",
        "trace": "listed > browsed > reviewed > decided > held",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "listing-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(entrys=None, listings=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": LISTING_SCHEMA,
        "entry": "M-235",
        "mcp_registry": {"title": "A test listing book"},
        "entrys": [item.to_record() for item in (
            entrys if entrys is not None else [_ref()])],
        "listing_records": [item.to_record() for item in (
            listings if listings is not None else [_listing()])],
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
    return _book(listings=[
        _listing(),
        _listing(listing_id="listing-hidden", seq=2,
               title="A hidden listing", stages=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_listing()
    assert book.title == EXAMPLE_TITLE
    assert book.listing_ids() == EXAMPLE_RUN_IDS
    assert book.entry_ids() == (
        "entry-filesystem", "entry-search",
        "entry-remote")
    assert [v.view_id for v in book.views] == [
        "view-listings", "view-held"]
    assert [m.listing_id for m in book.notes] == [
        "listing-held-listing", "listing-bare-listing"]
    assert [a.listing_id for a in book.traces] == ["listing-held-listing"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-entry"
    assert panel.as_of == "2026-11-11"
    assert [row.item_id for row in panel.rows] == list(book.listing_ids())
    derived = derive_panel(book, "view-listings")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-listings").verdict == "held"
    assert derive_verdict(book, "view-listings").green_shown == 3
    assert derive_verdict(book, "view-held").verdict == "held"
    assert derive_verdict(book, "view-held").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / LISTING_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == LISTING_SCHEMA
    assert raw["entry"] == "M-235"
    assert "verdict" not in raw
    assert "listing_index" not in raw
    assert "ledger" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-235")]
    assert slice_.title == "MCP registry kindness"
    assert slice_.part == 10
    assert "known servers browsable and addable from the TUI with their tools listed" in slice_.summary
    assert "before trust is granted" in slice_.summary
    assert LISTING_SLICE == "M-235"

def test_charter_rows_do_not_name_m235():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-235" not in owners
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
    assert ENTRY_STATES == ("live", "dormant")
    assert STAGES == ("listed", "browsed", "reviewed", "decided", "held")
    assert HELD_EVIDENCE == ("tools_ref", "origin_ref", "detail_ref", "manifest_ref", "decision_ref")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_KINDS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["decided"] == ("listed", "held")
    assert TRANSITIONS["held"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_STAGE == "held"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_entry_state("LIVE") == "live"
    assert normalize_stage("REVIEWED") == "reviewed"
    assert normalize_claim_kind("FEELING") == "feeling"
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    with pytest.raises(ValueError):
        normalize_entry_state("blessed")
    with pytest.raises(ValueError):
        normalize_stage("polish")
    with pytest.raises(ValueError):
        normalize_claim_kind("weather")
    assert legal_step("reviewed", "decided") is True
    assert legal_step("browsed", "held") is False
    assert legal_step("held", "listed") is False
    assert next_stage("listed") == "browsed"
    assert next_stage("reviewed") == "decided"
    assert next_stage("decided", failed=True) == "listed"
    assert next_stage("decided") == "held"
    assert next_stage("held") is None
    assert "held as data alone" in LISTING_RULE
    assert "listing sequence" in LISTING_RULE
    assert "M-235" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /mcpregistry")

def test_shipped_book_judged_honestly_as_data():
    book = load_listing()
    opening = book.listing_for("listing-held-listing")
    assert listing_green(opening, book) is True
    assert listing_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Listing: The held listing",
        "Entry: entry-filesystem",
        "Stage: held",
        "Claims: tools_ref")
    asking = book.listing_for("listing-bare-listing")
    assert listing_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert listing_green(asking, book) is False
    skipping = book.listing_for("listing-leaping-listing")
    assert listing_gaps(skipping, book) == (
        "steps from browsed to held, which the listing sequence "
        "does not allow",)
    assert [g.listing_id for g in green_listings(book)] == [
        "listing-held-listing", "listing-retried-listing", "listing-own-listing"]
    index = derive_index(book)
    assert [e.stage for e in index.listings] == EXAMPLE_STAGES
    assert index.gaps == ("listing-bare-listing", "listing-leaping-listing")
    assert listing_for_check(book, EXAMPLE_STAGE).listing_id == (
        "listing-held-listing")
    assert listing_for_check(book, "triple listing") is None
    assert transition_breaks(book) == (
        "listing-leaping-listing: browsed > held",)
    assert [g.listing_id for g in listing_listing(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "listing-held-listing") == EXAMPLE_TRACE
    assert trace_current(book, "listing-held-listing") is True
    assert trace_current(book, "listing-retried-listing") is False
    assert trace_for_listing(
        book, "listing-held-listing").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_listing(
        book, "listing-held-listing", "note").note_id == (
            "note-note-first")
    assert note_for_listing(book, "listing-nope") is None
    assert current_listing(book).listing_id == "listing-bare-listing"
    ledger = ledger_record(book)
    assert ledger["standings"] == [
        {"standing": "complete", "listing_records": 3},
        {"standing": "open", "listing_records": 2}]
    assert ledger["total"] == 5
    assert ledger["current_listing"] == "listing-bare-listing"
    assert ledger["traces"] == [
        {"listing_id": "listing-held-listing", "trace": "current"},
        {"listing_id": "listing-retried-listing", "trace": "unheld"},
        {"listing_id": "listing-own-listing", "trace": "unheld"},
        {"listing_id": "listing-bare-listing", "trace": "unheld"},
        {"listing_id": "listing-leaping-listing", "trace": "unheld"}]
    assert ledger["breaks"] == ["listing-leaping-listing: browsed > held"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 241
    assert citizen["next_slice"] == "M-242"
    assert citizen["m235_title"] == "MCP registry kindness"
    assert citizen["m235_part"] == 10
    assert citizen["m235_status"] == "done"

def test_listing_record_round_trips():
    listing = _listing()
    assert validate_listing(listing) is listing
    rebuilt = build_listing(listing.to_record())
    assert rebuilt == listing
    assert rebuilt.item_id == "listing-test"
    assert rebuilt.stage == "held"
    record = listing_record(listing)
    assert record["type"] == "listing_listing"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert entry_record(ref)["type"] == "listing_run"
    assert entry_record(ref)["state"] == "live"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _listing(stages=[])
    assert listing_gaps(silent) == (
        "has passed through no step: the listing has not started",)
    assert listing_green(silent) is False
    walking = _listing(stages=["listed", "browsed"])
    assert listing_gaps(walking) == (
        "has not reached held: the listing stands at browsed",)
    assert walking.stage == "browsed"
    sideways = _listing(stages=["browsed", "reviewed", "decided", "held"])
    assert listing_gaps(sideways) == (
        "opens at browsed, not at listed: the listing opens "
        "with the reflection",)
    repaired = _listing(stages=["listed", "browsed", "reviewed", "decided", "listed", "browsed", "reviewed", "decided", "held"])
    assert listing_gaps(repaired) == ()
    assert listing_green(repaired) is True
    with pytest.raises(ValueError):
        _listing(stages=[42])
    with pytest.raises(ValueError):
        _listing(stages="inspect as a bare string")
    with pytest.raises(ValueError):
        _listing(stages=["listed", "polish"])
    with pytest.raises(ValueError):
        _listing(claims=["weather"])
    with pytest.raises(ValueError):
        _listing(claims="tools_ref")
    none_listing = _listing(stages=None, claims=None)
    assert none_listing.stages == ()
    assert none_listing.claims == ()

def test_decision_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "listings", "coverage", "current_listing",
                "ledger", "listing"):
        fields = _listing().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_listing(fields)
    fields = _listing().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_listing(fields)


def test_decision_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _listing().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_listing(fields)


def test_listing_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _listing(title="")
    with pytest.raises(ValueError):
        _listing(entry_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "listed > browsed > reviewed > decided > held"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_listings_own_fields():
    listing = _listing(claims=["tools_ref"])
    assert plain_lines(listing) == (
        "Listing: A test listing",
        "Entry: entry-test",
        "Stage: held",
        "Claims: tools_ref")
    segment = segment_of(listing)
    assert segment.startswith("listing-test: A test listing")
    assert "stage: 'held'" in segment
    assert "gaps: none" in segment
    assert plain_words(listing).startswith(
        "A test listing - from entry-test")

def test_red_listings_stand_named_in_their_gaps():
    asking = _listing(claims=["feeling", "tools_ref", "summary"])
    assert listing_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert listing_green(asking) is False
    skipping = _listing(stages=["listed", "browsed", "held"])
    assert listing_gaps(skipping) == (
        "steps from browsed to held, which the listing sequence "
        "does not allow",)
    book = _book(listings=[
        _listing(),
        _listing(listing_id="listing-skipping", seq=2,
             stages=["listed", "browsed", "held"]),
    ])
    assert transition_breaks(book) == (
        "listing-skipping: browsed > held",)
    assert current_listing(book).listing_id == "listing-skipping"
    assert [g.listing_id for g in listing_listing(book)] == [
        "listing-test", "listing-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "listing_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "listing_note"
    assert record["listing_id"] == "listing-test"
    assert view_plain_words(view) == "View view-test: shows all listings."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_listings_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.stage for e in index.listings] == ["held"]
    assert index.listings[0] == IndexListing(
        stage="held",
        listing_id="listing-test", title="A test listing")
    assert index.gaps == ("listing-hidden",)
    record = index_record(book)
    assert record["type"] == "listing_index"
    assert record["gaps"] == ["listing-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "listing_book"

def test_check_target_reaches_its_listing_and_an_unheld_target_reaches_nothing():
    book = load_listing()
    assert listing_for_check(book, "held").listing_id == (
        "listing-held-listing")
    assert listing_for_check(book, "") is None
    assert listing_for_check(book, None) is None
    assert listing_for_check(book, "not held at all") is None
    text = format_stage(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_listing()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Listing note note listing-held-listing" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").listing_id == "listing-test"
    assert note_for_listing(book, "listing-test").note_id == "note-test"
    assert note_for_listing(book, "listing-test", "praise") is None
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
    row = build_row(None, _listing(), book)
    assert row.standing == "complete"
    assert validate_row(row, _listing(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_listings():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "listing_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "held"
    empty_book = _book(listings=[_listing(stages=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(ListingVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_listings():
    book = load_listing()
    assert [g.listing_id for g in shown_listings(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.listing_id for g in shown_listings(book, "view-held")] == [
        "listing-held-listing", "listing-retried-listing", "listing-own-listing"]
    assert [g.listing_id for g in listings_for_entry(
        book, "entry-search")] == [
            "listing-own-listing", "listing-bare-listing",
            "listing-leaping-listing"]
    assert listings_for_entry(book, "entry-nope") == ()
    assert current_listing(_mixed_book()).listing_id == "listing-hidden"
    assert current_listing(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "listing-test") == (
        "listed > browsed > reviewed > decided > held")
    assert trace_current(stale, "listing-test") is False
    assert ledger_record(stale)["traces"] == [
        {"listing_id": "listing-test", "trace": "stale"}]

def test_origin_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(listings=[_listing(), _listing(seq=2)])
    with pytest.raises(ValueError):
        _book(listings=[_listing(), _listing(listing_id="listing-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(listings=[_listing(entry_id="entry-nope")])
    with pytest.raises(ValueError):
        _book(entrys=[_ref(), _ref(
            entry_id="entry-cold", seq=2, state="dormant")],
            listings=[_listing(entry_id="entry-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(entry_id="entry-nope")])
    fields = {
        "schema": LISTING_SCHEMA, "entry": "M-235",
        "mcp_registry": {"title": "A reviewed book"},
        "entrys": [_ref().to_record()],
        "listing_records": [_listing().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "held"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_listing"] = "listing-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_listing")
    fields["trace"] = "listing-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / LISTING_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "mcp_registry.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_listing_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.listing_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = ListingRegistry()
    assert registry.title() is None
    registry.register_entry_ref(_ref())
    registry.register_listing(_listing())
    registry.register_view(_view())
    assert [g.listing_id for g in registry.list_listings()] == ["listing-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_listing("listing-test").title == "A test listing"
    assert registry.get_slice("entry-test").state == "live"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("listing-test").listing_id == "listing-test"
    with pytest.raises(ValueError):
        registry.register_listing(_listing(seq=9))
    with pytest.raises(ValueError):
        registry.register_listing(_listing(listing_id="listing-two"))
    with pytest.raises(KeyError):
        registry.get_listing("listing-nope")
    assert registry.book().title == "An unheld listing book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = ListingRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test listing book"
    assert registry.title() == "A test listing book"
    assert len(registry.list_listings()) == 2
    other = ListingRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    listing = _listing()
    assert "A test listing" in plain_words(listing)
    assert panel_plain_words(_mixed_book()).startswith(
        "The listing book holds 2 listings")
    assert verdict_plain_words(_mixed_book()) == (
        "The listings stand held: 1 of 2 shown listings stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green listings; red, "
        "listed in its gaps: listing-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_listing(listing)
    assert "Listing: A test listing" in text
    assert "stands complete" in text
    text = format_listing(_listing(stages=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The MCP Registry (M-235) - A test listing book" in book_text
    assert "listing-hidden" in format_book(_mixed_book(), "entry-test")
    assert "Listing panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "held - A test listing (listing-test)" in index_text
    assert "listing-hidden" in index_text
    screen = format_listing_screen()
    assert "The MCP Registry (M-235)" in screen
    assert "listing-bare-listing" in screen

def test_parse_args_well_and_loader_targets():
    assert parse_listing_args("") == ("show", None)
    assert parse_listing_args(None) == ("show", None)
    assert parse_listing_args("show") == ("show", None)
    assert parse_listing_args("listing listing-test") == (
        "listing", "listing-test")
    assert parse_listing_args("stage held") == (
        "stage", "held")
    assert parse_listing_args("entry entry-test") == (
        "entry", "entry-test")
    assert parse_listing_args("view view-test") == ("view", "view-test")
    assert parse_listing_args("note note-test") == ("note", "note-test")
    assert parse_listing_args("index") == ("index", None)
    assert parse_listing_args("panel") == ("panel", None)
    assert parse_listing_args("verdict") == ("verdict", None)
    for bad in ("dance", "listing", "stage", "entry", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_listing_args(bad)
    ledger = ledger_record()
    assert ledger["type"] == "listing_well"
    assert ledger["total"] == 5
    assert ledger["current_listing"] == "listing-bare-listing"
    book = load_listing({
        "schema": LISTING_SCHEMA, "entry": "M-235",
        "mcp_registry": {"title": "A reviewed book"},
        "entrys": [_ref().to_record()],
        "listing_records": [_listing().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, ListingBook)
    assert book.title == "A reviewed book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_listing({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_listing({"entry": "M-999"})
    built = build_listing(
        listing_id="listing-kw", seq=3, entry_id="entry-test",
        title="Kw Listing", stages=["listed", "browsed", "reviewed", "decided", "held"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="listing-test")
    assert built.listing_id == "listing-kw"
    assert listing_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-235 agent layer: the agent holds a listing
# book for the session, listings and views are
# published as session news through the
# checkpoint target (ledger first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held listings, the ledger is derived from
# the held listings' completeness, the roadmap standing
# is decided from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no entry. This layer listings
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session ledger news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_LISTING_EVENT_TYPES = (
    "listing_listing", "listing_run", "listing_view",
    "listing_panel", "listing_verdict")


def _listing_events(store, session_id, entry):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == entry]


def _write_mcpregistry_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / LISTING_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "mcp_registry.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestListingAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.mcpregistry_status()
        assert status["listing_records"] == []
        assert status["entrys"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["mcpregistry_book"]["title"] == EXAMPLE_TITLE
        assert len(status["mcpregistry_book"]["entrys"]) == 3
        assert len(status["mcpregistry_book"]["listing_records"]) == 5
        assert len(status["mcpregistry_book"]["views"]) == 2
        assert len(status["mcpregistry_book"]["notes"]) == 2
        assert len(status["mcpregistry_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-entry"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["stage"] for e in status["index"]["listings"]] == (
            EXAMPLE_STAGES)
        assert status["index"]["gaps"] == [
            "listing-bare-listing", "listing-leaping-listing"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["ledger"]["total"] == 5
        assert status["ledger"]["current_listing"] == "listing-bare-listing"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 241
        assert status["roadmap"]["next_slice"] == "M-242"
        assert status["roadmap"]["m235_title"] == "MCP registry kindness"
        assert "held as data alone" in status["rule"]
        assert "listing-bare-listing" in status["plain_words"]
        assert "The MCP Registry (M-235)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._mcpregistry_registry()
        assert agent._mcpregistry_registry() is first
        assert agent._mcpregistry_store is first
        for name in ("mcpregistry_book", "mcpregistry_status", "mcpregistry_panel",
                     "mcpregistry_verdict", "mcpregistry_index", "report_mcpregistry"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_mcpregistry_registry", "mcpregistry_book", "mcpregistry_status",
            "get_mcpregistry_listing", "get_mcpregistry_view", "get_mcpregistry_note",
            "listings_for_entry", "mcpregistry_green",
            "mcpregistry_panel", "mcpregistry_verdict", "mcpregistry_index",
            "register_mcpregistry_listing", "register_mcpregistry_view",
            "view_mcpregistry", "register_mcpregistry_book",
            "record_mcpregistry_book", "report_mcpregistry",
            "_publish_mcpregistry_record", "_mcpregistry_screen",
            "_mcpregistry_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.mcpregistry_status()
        assert agent.get_mcpregistry_listing(
            "listing-held-listing").title == "The held listing"
        assert agent.get_mcpregistry_view(
            "view-listings").view_filter == "all"
        assert agent.get_mcpregistry_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.listing_id for d in agent.listings_for_entry(
            "entry-search")] == [
            "listing-own-listing", "listing-bare-listing",
            "listing-leaping-listing"]
        assert [d.listing_id for d in agent.mcpregistry_green()] == [
            "listing-held-listing", "listing-retried-listing", "listing-own-listing"]
        agent.mcpregistry_panel()
        agent.mcpregistry_verdict()
        agent.mcpregistry_index()
        agent.report_mcpregistry()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _LISTING_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_mcpregistry_listing("listing-nope")
        with pytest.raises(KeyError):
            agent.get_mcpregistry_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_mcpregistry_note("note-nope")
        with pytest.raises(ValueError):
            agent.listings_for_entry("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_mcpregistry_listing(_listing())
        status = agent.mcpregistry_status()
        assert [d["listing_id"] for d in status["listing_records"]] == ["listing-test"]
        assert status["book"]["title"] == "An unheld listing book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["stage"] for e in status["index"]["listings"]] == [
            "held"]
        assert status["first_note"] is None
        assert "listing-test" in status["screen"]
    def test_held_listing_never_falls_back_to_the_example(
            self, agent):
        agent.register_mcpregistry_listing(_listing())
        with pytest.raises(KeyError):
            agent.get_mcpregistry_listing("listing-held-listing")
        with pytest.raises(KeyError):
            agent.get_mcpregistry_view("view-listings")
        with pytest.raises(KeyError):
            agent.get_mcpregistry_note("note-note-first")
        listing = agent.get_mcpregistry_listing("listing-test")
        assert listing.title == "A test listing"
        assert agent.mcpregistry_book().title == (
            "An unheld listing book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_mcpregistry_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.listing_id == "listing-held-listing"
        status = agent.mcpregistry_status()
        assert status["index"]["gaps"] == [
            "listing-bare-listing", "listing-leaping-listing"]
        assert status["first_note"]["listing_id"] == (
            "listing-held-listing")
        assert status["first_note"]["stance"] == "note"

class TestListingAgentHolding:
    def test_register_listing_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_mcpregistry_listing(_listing())
        assert result["listing"]["listing_id"] == "listing-test"
        assert result["record_news"]["type"] == "listing_listing"
        assert "listing-test" in result["screen"]
        events = _listing_events(store, session_id, "listing_listing")
        assert len(events) == 1
        agent.close()

    def test_duplicate_decision_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_mcpregistry_listing(_listing())
        with pytest.raises(ValueError):
            agent.register_mcpregistry_listing(_listing(seq=9))
        with pytest.raises(ValueError):
            agent.register_mcpregistry_listing(_listing(listing_id="listing-two"))
        events = _listing_events(store, session_id, "listing_listing")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_mcpregistry_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_listing_events(
            store, session_id, "listing_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_mcpregistry_listing(_listing())
        result = agent.view_mcpregistry("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "listing_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "held"
        assert len(_listing_events(
            store, session_id, "listing_view")) == 1
        assert len(_listing_events(
            store, session_id, "listing_panel")) == 1
        assert len(_listing_events(
            store, session_id, "listing_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_listing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_mcpregistry_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "listing_run", "listing_listing", "listing_view"]
        assert len(_listing_events(
            store, session_id, "listing_listing")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_mcpregistry_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "listing_panel"
        assert result["index_record"]["gaps"] == [
            "listing-bare-listing", "listing-leaping-listing"]
        with pytest.raises(ValueError):
            agent.record_mcpregistry_book()
        assert len(_listing_events(
            store, session_id, "listing_run")) == 3
        assert len(_listing_events(
            store, session_id, "listing_listing")) == 5
        assert len(_listing_events(
            store, session_id, "listing_view")) == 2
        agent.close()

    def test_book_from_a_file_is_linked_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_mcpregistry_book_file(tmp_path)
        book = load_listing_file(path)
        result = agent.record_mcpregistry_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_runrt_renders_example_then_held_book_only(self, agent):
        listing = agent.report_mcpregistry()
        assert listing["book"]["title"] == EXAMPLE_TITLE
        assert listing["verdict"]["verdict"] == "held"
        assert listing["index"]["gaps"] == [
            "listing-bare-listing", "listing-leaping-listing"]
        assert "listing-held-listing" in listing["book_text"]
        assert "held - The held listing (listing-held-listing)" in listing["index_text"]
        agent.register_mcpregistry_listing(_listing())
        listing = agent.report_mcpregistry()
        assert listing["book"]["title"] == "An unheld listing book"
        assert listing["panel"] is None
        assert listing["verdict"] is None

class TestListingTerminalHeading:
    def test_show_listing_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/mcpregistry")
        assert "The MCP Registry (M-235)" in text
        _, _, text = _slash(agent, "/mcpregistry listing listing-held-listing")
        assert "Listing: The held listing" in text
        _, _, text = _slash(
            agent, "/mcpregistry stage held")
        assert "Listing: The held listing" in text
        _, _, text = _slash(agent, "/mcpregistry stage triple listing")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/mcpregistry entry entry-search")
        assert "listing-bare-listing" in text
        assert "listing-held-listing" not in text
        _, _, text = _slash(agent, "/mcpregistry view view-listings")
        assert "filter all" in text
        _, _, text = _slash(agent, "/mcpregistry note note-note-first")
        assert "Listing note note listing-held-listing" in text
        _, _, text = _slash(agent, "/mcpregistry index")
        assert "Listing index" in text
        assert "listing-bare-listing" in text
        _, _, text = _slash(agent, "/mcpregistry panel")
        assert "Listing panel under view view-listings" in text
        _, _, text = _slash(agent, "/mcpregistry verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/mcpregistry [show|listing <listing-id>"
                "|stage <stage>|entry <entry-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/mcpregistry dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/mcpregistry listing listing-nope")
        assert "no listing listed" in text
@pytest.fixture()
def listing_handler(agent, monkeypatch):
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


def _listing_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestListingCommand:
    def test_show_is_default(self, listing_handler, agent):
        listing_handler._handle_mcpregistry("")
        assert "The MCP Registry (M-235)" in (
            _listing_published_text(listing_handler))

    def test_listing_check_slice_view_note_index_panel_verdict(
            self, listing_handler, agent):
        listing_handler._handle_mcpregistry("listing listing-held-listing")
        assert "Listing: The held listing" in _listing_published_text(
            listing_handler)
        listing_handler._handle_mcpregistry(
            "stage held")
        assert "Listing: The held listing" in _listing_published_text(
            listing_handler)
        listing_handler._handle_mcpregistry("entry entry-search")
        assert "listing-bare-listing" in _listing_published_text(
            listing_handler)
        listing_handler._handle_mcpregistry("view view-listings")
        assert "filter all" in _listing_published_text(listing_handler)
        listing_handler._handle_mcpregistry("note note-note-first")
        assert "Listing note note listing-held-listing" in (
            _listing_published_text(listing_handler))
        listing_handler._handle_mcpregistry("index")
        assert "Listing index" in _listing_published_text(listing_handler)
        listing_handler._handle_mcpregistry("panel")
        assert "Listing panel under view" in _listing_published_text(
            listing_handler)
        listing_handler._handle_mcpregistry("verdict")
        assert "held" in _listing_published_text(listing_handler)
    def test_bad_grammar_is_published(
            self, listing_handler, agent):
        listing_handler._handle_mcpregistry("dance party")
        assert USAGE in _listing_published_text(listing_handler)
        listing_handler._handle_mcpregistry("listing listing-nope")
        assert "no listing listed" in _listing_published_text(
            listing_handler)


class TestChatScreenRoutingListing:
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
        screen.handle_command("/mcpregistry panel", _FakeLog())
        assert calls == [("/mcpregistry", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/mcpregistry[/green] - show the MCP registry (M-235)" in (
            text)
        assert ('"/mcpregistry": "Usage: /mcpregistry | '
                '/mcpregistry listing <listing-id>') in text

class TestListingDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.mcpregistry_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-listings"
        verdict = agent.mcpregistry_verdict()
        assert verdict.verdict == "held"
        found = agent.mcpregistry_verdict("view-held")
        assert found.verdict == "held"
        assert found.green_shown == 3
        agent.register_mcpregistry_listing(_listing())
        with pytest.raises(ValueError):
            agent.mcpregistry_panel()
        with pytest.raises(ValueError):
            agent.mcpregistry_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_mcpregistry_listing(_listing(stages=[]))
        result = agent.view_mcpregistry("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.mcpregistry_index()
        assert [e["stage"] for e in result["index"]["listings"]] == (
            EXAMPLE_STAGES)
        assert result["index"]["gaps"] == [
            "listing-bare-listing", "listing-leaping-listing"]
        assert "held - The held listing (listing-held-listing)" in (
            result["index_text"])
        listing = agent.get_mcpregistry_listing("listing-leaping-listing")
        assert listing_gaps(listing, agent.mcpregistry_book()) == (
            "steps from browsed to held, which the listing sequence "
            "does not allow",)
        assert listing_green(listing, agent.mcpregistry_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _LISTING_EVENT_TYPES] == []
        agent.close()
