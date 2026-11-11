"""M-226 Standing orders - pure-layer tests.

TIER: integration

The pure layer is the taxonomist, held as data: one
record per order, held whole - the campaign it
answers for, named by campaign id, its title, the
steps it walked in walk order and the evidence
it carries, held by campaign. The question walk is
explicit - named, recorded, bound, honoured,
kept, with their legal steps held as data -
and a order's standing is derived at call
time: a order that opens anywhere but stated, steps where the sequence does not allow,
carries a bare claim in place of held evidence,
or has not yet stated kept stands open,
named in its gaps. A order stands only for
an active campaign: a order naming no held
campaign, or one that is not active, refuses by
name. The order's trace - its walked steps
as one line - is derived at call time, and a held
trace record stands current only while it agrees
with the derived trace. The index, panel,
verdict, ledger, trace, order and current
order are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
question was actually answered, honoured or
kept live. The shipped example book is held
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

from mythic_agent.core.standing_orders import (
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
    ORDER_RESOURCE,
    ORDER_RULE,
    ORDER_SCHEMA,
    ORDER_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    OrderRecord,
    IndexOrder,
    CampaignRef,
    NoteRecord,
    OrderBook,
    OrderIndex,
    OrderPanel,
    OrderRegistry,
    OrderVerdict,
    OrderView,
    trace_for_order,
    ledger_record,
    book_record,
    build_trace,
    build_book,
    build_order,
    build_campaign_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_order,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    order_for_check,
    order_gaps,
    order_order,
    order_record,
    order_green,
    orders_for_campaign,
    first_note,
    format_book,
    format_order,
    format_index,
    format_note,
    format_stage,
    format_panel,
    format_order_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    campaign_record,
    load_order,
    legal_step,
    load_order_file,
    next_stage,
    normalize_stage,
    normalize_claim_kind,
    normalize_campaign_state,
    normalize_stance,
    normalize_view_filter,
    note_for_order,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_order_args,
    green_orders,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_orders,
    validate_book,
    validate_order,
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
EXAMPLE_TITLE = "Standing orders at the M-226 slice run"
EXAMPLE_STAGES = ["kept", "kept", "kept"]
EXAMPLE_RUN_IDS = (
    "order-held-order", "order-retried-order",
    "order-own-order", "order-bare-order",
    "order-leaping-order")
EXAMPLE_TRACE = "stated > recorded > bound > honoured > kept"


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
        "origin_session": "order-test",
    }
    fields.update(overrides)
    return build_campaign_ref(fields)


def _order(**overrides):
    fields = {
        "order_id": "order-test",
        "seq": 1,
        "campaign_id": "campaign-test",
        "title": "A test order",
        "stages": ["stated", "recorded", "bound", "honoured", "kept"],
        "claims": [],
        "detail": "A test order held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "order-test",
    }
    fields.update(overrides)
    return build_order(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "order-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "order_id": "order-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "order-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "order_id": "order-test",
        "trace": "stated > recorded > bound > honoured > kept",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "order-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(campaigns=None, orders=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": ORDER_SCHEMA,
        "campaign": "M-226",
        "standing_orders": {"title": "A test order book"},
        "campaigns": [item.to_record() for item in (
            campaigns if campaigns is not None else [_ref()])],
        "order_records": [item.to_record() for item in (
            orders if orders is not None else [_order()])],
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
    return _book(orders=[
        _order(),
        _order(order_id="order-hidden", seq=2,
               title="A hidden order", stages=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_order()
    assert book.title == EXAMPLE_TITLE
    assert book.order_ids() == EXAMPLE_RUN_IDS
    assert book.campaign_ids() == (
        "campaign-m225-export", "campaign-m226-orders",
        "campaign-m227-workflow")
    assert [v.view_id for v in book.views] == [
        "view-orders", "view-kept"]
    assert [m.order_id for m in book.notes] == [
        "order-held-order", "order-bare-order"]
    assert [a.order_id for a in book.traces] == ["order-held-order"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m225-campaign"
    assert panel.as_of == "2026-11-11"
    assert [row.item_id for row in panel.rows] == list(book.order_ids())
    derived = derive_panel(book, "view-orders")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-orders").verdict == "held"
    assert derive_verdict(book, "view-orders").green_shown == 3
    assert derive_verdict(book, "view-kept").verdict == "kept"
    assert derive_verdict(book, "view-kept").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / ORDER_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == ORDER_SCHEMA
    assert raw["campaign"] == "M-226"
    assert "verdict" not in raw
    assert "order_index" not in raw
    assert "ledger" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-226")]
    assert slice_.title == "Standing orders"
    assert slice_.part == 9
    assert "user-level laws (no-Docker, README guardian, manual-only workflows, keeper law) stored once" in slice_.summary
    assert "binding every campaign" in slice_.summary
    assert ORDER_SLICE == "M-226"

def test_charter_rows_do_not_name_m226():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-226" not in owners
    method = load_method_charter()
    assert "M-201" in method.source_note
    assert "M-232" in method.source_note
    assert "YRSA_CODING_JUGGERNAUT" in method.source_note

def test_closed_vocabularies():
    assert COMPLETE_WORDS == ("complete", "open")
    assert STAGE_FIELDS == ("stages", "claims")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "complete", "open")
    assert VERDICT_WORDS == ("kept", "held", "blocked")
    assert CAMPAIGN_STATES == ("live", "dormant")
    assert STAGES == ("stated", "recorded", "bound", "honoured", "kept")
    assert HELD_EVIDENCE == ("word_ref", "book_ref", "campaign_ref", "proof_ref", "order_ref")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_KINDS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["honoured"] == ("stated", "kept")
    assert TRANSITIONS["kept"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_STAGE == "kept"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_campaign_state("LIVE") == "live"
    assert normalize_stage("BOUND") == "bound"
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
    assert legal_step("bound", "honoured") is True
    assert legal_step("recorded", "kept") is False
    assert legal_step("kept", "stated") is False
    assert next_stage("stated") == "recorded"
    assert next_stage("bound") == "honoured"
    assert next_stage("honoured", failed=True) == "stated"
    assert next_stage("honoured") == "kept"
    assert next_stage("kept") is None
    assert "held as data alone" in ORDER_RULE
    assert "order sequence" in ORDER_RULE
    assert "M-226" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /orders")

def test_shipped_book_judged_honestly_as_data():
    book = load_order()
    opening = book.order_for("order-held-order")
    assert order_green(opening, book) is True
    assert order_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Order: The held order",
        "Campaign: campaign-m225-export",
        "Stage: kept",
        "Claims: word_ref")
    asking = book.order_for("order-bare-order")
    assert order_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert order_green(asking, book) is False
    skipping = book.order_for("order-leaping-order")
    assert order_gaps(skipping, book) == (
        "steps from recorded to kept, which the order sequence "
        "does not allow",)
    assert [g.order_id for g in green_orders(book)] == [
        "order-held-order", "order-retried-order", "order-own-order"]
    index = derive_index(book)
    assert [e.stage for e in index.orders] == EXAMPLE_STAGES
    assert index.gaps == ("order-bare-order", "order-leaping-order")
    assert order_for_check(book, EXAMPLE_STAGE).order_id == (
        "order-held-order")
    assert order_for_check(book, "triple order") is None
    assert transition_breaks(book) == (
        "order-leaping-order: recorded > kept",)
    assert [g.order_id for g in order_order(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "order-held-order") == EXAMPLE_TRACE
    assert trace_current(book, "order-held-order") is True
    assert trace_current(book, "order-retried-order") is False
    assert trace_for_order(
        book, "order-held-order").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_order(
        book, "order-held-order", "note").note_id == (
            "note-note-first")
    assert note_for_order(book, "order-nope") is None
    assert current_order(book).order_id == "order-bare-order"
    ledger = ledger_record(book)
    assert ledger["standings"] == [
        {"standing": "complete", "order_records": 3},
        {"standing": "open", "order_records": 2}]
    assert ledger["total"] == 5
    assert ledger["current_order"] == "order-bare-order"
    assert ledger["traces"] == [
        {"order_id": "order-held-order", "trace": "current"},
        {"order_id": "order-retried-order", "trace": "unheld"},
        {"order_id": "order-own-order", "trace": "unheld"},
        {"order_id": "order-bare-order", "trace": "unheld"},
        {"order_id": "order-leaping-order", "trace": "unheld"}]
    assert ledger["breaks"] == ["order-leaping-order: recorded > kept"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 231
    assert citizen["next_slice"] == "M-232"
    assert citizen["m226_title"] == "Standing orders"
    assert citizen["m226_part"] == 9
    assert citizen["m226_status"] == "done"

def test_order_record_round_trips():
    order = _order()
    assert validate_order(order) is order
    rebuilt = build_order(order.to_record())
    assert rebuilt == order
    assert rebuilt.item_id == "order-test"
    assert rebuilt.stage == "kept"
    record = order_record(order)
    assert record["type"] == "order_order"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert campaign_record(ref)["type"] == "order_run"
    assert campaign_record(ref)["state"] == "live"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _order(stages=[])
    assert order_gaps(silent) == (
        "has passed through no step: the order has not started",)
    assert order_green(silent) is False
    walking = _order(stages=["stated", "recorded"])
    assert order_gaps(walking) == (
        "has not reached kept: the order stands at recorded",)
    assert walking.stage == "recorded"
    sideways = _order(stages=["recorded", "bound", "honoured", "kept"])
    assert order_gaps(sideways) == (
        "opens at recorded, not at stated: the order opens "
        "with the reflection",)
    repaired = _order(stages=["stated", "recorded", "bound", "honoured", "stated", "recorded", "bound", "honoured", "kept"])
    assert order_gaps(repaired) == ()
    assert order_green(repaired) is True
    with pytest.raises(ValueError):
        _order(stages=[42])
    with pytest.raises(ValueError):
        _order(stages="inspect as a bare string")
    with pytest.raises(ValueError):
        _order(stages=["stated", "polish"])
    with pytest.raises(ValueError):
        _order(claims=["weather"])
    with pytest.raises(ValueError):
        _order(claims="word_ref")
    none_order = _order(stages=None, claims=None)
    assert none_order.stages == ()
    assert none_order.claims == ()

def test_order_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "orders", "coverage", "current_order",
                "ledger", "order"):
        fields = _order().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_order(fields)
    fields = _order().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_order(fields)


def test_order_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _order().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_order(fields)


def test_order_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _order(title="")
    with pytest.raises(ValueError):
        _order(campaign_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "stated > recorded > bound > honoured > kept"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_orders_own_fields():
    order = _order(claims=["word_ref"])
    assert plain_lines(order) == (
        "Order: A test order",
        "Campaign: campaign-test",
        "Stage: kept",
        "Claims: word_ref")
    segment = segment_of(order)
    assert segment.startswith("order-test: A test order")
    assert "stage: 'kept'" in segment
    assert "gaps: none" in segment
    assert plain_words(order).startswith(
        "A test order - from campaign-test")

def test_red_orders_stand_named_in_their_gaps():
    asking = _order(claims=["feeling", "word_ref", "summary"])
    assert order_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert order_green(asking) is False
    skipping = _order(stages=["stated", "recorded", "kept"])
    assert order_gaps(skipping) == (
        "steps from recorded to kept, which the order sequence "
        "does not allow",)
    book = _book(orders=[
        _order(),
        _order(order_id="order-skipping", seq=2,
             stages=["stated", "recorded", "kept"]),
    ])
    assert transition_breaks(book) == (
        "order-skipping: recorded > kept",)
    assert current_order(book).order_id == "order-skipping"
    assert [g.order_id for g in order_order(book)] == [
        "order-test", "order-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "order_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "order_note"
    assert record["order_id"] == "order-test"
    assert view_plain_words(view) == "View view-test: shows all orders."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_orders_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.stage for e in index.orders] == ["kept"]
    assert index.orders[0] == IndexOrder(
        stage="kept",
        order_id="order-test", title="A test order")
    assert index.gaps == ("order-hidden",)
    record = index_record(book)
    assert record["type"] == "order_index"
    assert record["gaps"] == ["order-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "order_book"

def test_check_target_reaches_its_order_and_an_unheld_target_reaches_nothing():
    book = load_order()
    assert order_for_check(book, "kept").order_id == (
        "order-held-order")
    assert order_for_check(book, "") is None
    assert order_for_check(book, None) is None
    assert order_for_check(book, "not held at all") is None
    text = format_stage(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_order()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Order note note order-held-order" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").order_id == "order-test"
    assert note_for_order(book, "order-test").note_id == "note-test"
    assert note_for_order(book, "order-test", "praise") is None
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
    row = build_row(None, _order(), book)
    assert row.standing == "complete"
    assert validate_row(row, _order(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_orders():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "order_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "kept"
    empty_book = _book(orders=[_order(stages=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(OrderVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_readings():
    book = load_order()
    assert [g.order_id for g in shown_orders(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.order_id for g in shown_orders(book, "view-kept")] == [
        "order-held-order", "order-retried-order", "order-own-order"]
    assert [g.order_id for g in orders_for_campaign(
        book, "campaign-m226-orders")] == [
            "order-own-order", "order-bare-order",
            "order-leaping-order"]
    assert orders_for_campaign(book, "campaign-nope") == ()
    assert current_order(_mixed_book()).order_id == "order-hidden"
    assert current_order(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "order-test") == (
        "stated > recorded > bound > honoured > kept")
    assert trace_current(stale, "order-test") is False
    assert ledger_record(stale)["traces"] == [
        {"order_id": "order-test", "trace": "stale"}]

def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(orders=[_order(), _order(seq=2)])
    with pytest.raises(ValueError):
        _book(orders=[_order(), _order(order_id="order-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(orders=[_order(campaign_id="campaign-nope")])
    with pytest.raises(ValueError):
        _book(campaigns=[_ref(), _ref(
            campaign_id="campaign-cold", seq=2, state="dormant")],
            orders=[_order(campaign_id="campaign-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(campaign_id="campaign-nope")])
    fields = {
        "schema": ORDER_SCHEMA, "campaign": "M-226",
        "standing_orders": {"title": "A bound book"},
        "campaigns": [_ref().to_record()],
        "order_records": [_order().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "kept"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_order"] = "order-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_order")
    fields["trace"] = "order-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / ORDER_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "standing_orders.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_order_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.order_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = OrderRegistry()
    assert registry.title() is None
    registry.register_campaign_ref(_ref())
    registry.register_order(_order())
    registry.register_view(_view())
    assert [g.order_id for g in registry.list_orders()] == ["order-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_order("order-test").title == "A test order"
    assert registry.get_slice("campaign-test").state == "live"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("order-test").order_id == "order-test"
    with pytest.raises(ValueError):
        registry.register_order(_order(seq=9))
    with pytest.raises(ValueError):
        registry.register_order(_order(order_id="order-two"))
    with pytest.raises(KeyError):
        registry.get_order("order-nope")
    assert registry.book().title == "An unheld order book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = OrderRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test order book"
    assert registry.title() == "A test order book"
    assert len(registry.list_orders()) == 2
    other = OrderRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    order = _order()
    assert "A test order" in plain_words(order)
    assert panel_plain_words(_mixed_book()).startswith(
        "The order book holds 2 orders")
    assert verdict_plain_words(_mixed_book()) == (
        "The orders stand held: 1 of 2 shown orders stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green orders; red, "
        "named in its gaps: order-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_order(order)
    assert "Order: A test order" in text
    assert "stands complete" in text
    text = format_order(_order(stages=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The Order Gate (M-226) - A test order book" in book_text
    assert "order-hidden" in format_book(_mixed_book(), "campaign-test")
    assert "Order panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "kept - A test order (order-test)" in index_text
    assert "order-hidden" in index_text
    screen = format_order_screen()
    assert "The Order Gate (M-226)" in screen
    assert "order-bare-order" in screen

def test_parse_args_well_and_loader_targets():
    assert parse_order_args("") == ("show", None)
    assert parse_order_args(None) == ("show", None)
    assert parse_order_args("show") == ("show", None)
    assert parse_order_args("order order-test") == (
        "order", "order-test")
    assert parse_order_args("stage kept") == (
        "stage", "kept")
    assert parse_order_args("campaign campaign-test") == (
        "campaign", "campaign-test")
    assert parse_order_args("view view-test") == ("view", "view-test")
    assert parse_order_args("note note-test") == ("note", "note-test")
    assert parse_order_args("index") == ("index", None)
    assert parse_order_args("panel") == ("panel", None)
    assert parse_order_args("verdict") == ("verdict", None)
    for bad in ("dance", "order", "stage", "campaign", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_order_args(bad)
    ledger = ledger_record()
    assert ledger["type"] == "order_well"
    assert ledger["total"] == 5
    assert ledger["current_order"] == "order-bare-order"
    book = load_order({
        "schema": ORDER_SCHEMA, "campaign": "M-226",
        "standing_orders": {"title": "A bound book"},
        "campaigns": [_ref().to_record()],
        "order_records": [_order().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, OrderBook)
    assert book.title == "A bound book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_order({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_order({"campaign": "M-999"})
    built = build_order(
        order_id="order-kw", seq=3, campaign_id="campaign-test",
        title="Kw Order", stages=["stated", "recorded", "bound", "honoured", "kept"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="order-test")
    assert built.order_id == "order-kw"
    assert order_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-226 agent layer: the agent holds a order
# book for the session, orders and views are
# published as session news through the
# checkpoint target (ledger first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held orders, the ledger is derived from
# the held orders' completeness, the roadmap standing
# is honoured from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no campaign. This layer orders
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session ledger news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_ORDER_EVENT_TYPES = (
    "order_order", "order_run", "order_view",
    "order_panel", "order_verdict")


def _order_events(store, session_id, campaign):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == campaign]


def _write_orders_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / ORDER_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "standing_orders.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestOrderAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.orders_status()
        assert status["order_records"] == []
        assert status["campaigns"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["orders_book"]["title"] == EXAMPLE_TITLE
        assert len(status["orders_book"]["campaigns"]) == 3
        assert len(status["orders_book"]["order_records"]) == 5
        assert len(status["orders_book"]["views"]) == 2
        assert len(status["orders_book"]["notes"]) == 2
        assert len(status["orders_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-m225-campaign"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["stage"] for e in status["index"]["orders"]] == (
            EXAMPLE_STAGES)
        assert status["index"]["gaps"] == [
            "order-bare-order", "order-leaping-order"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["ledger"]["total"] == 5
        assert status["ledger"]["current_order"] == "order-bare-order"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 231
        assert status["roadmap"]["next_slice"] == "M-232"
        assert status["roadmap"]["m226_title"] == "Standing orders"
        assert "held as data alone" in status["rule"]
        assert "order-bare-order" in status["plain_words"]
        assert "The Order Gate (M-226)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._orders_registry()
        assert agent._orders_registry() is first
        assert agent._orders_store is first
        for name in ("orders_book", "orders_status", "orders_panel",
                     "orders_verdict", "orders_index", "report_orders"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_orders_registry", "orders_book", "orders_status",
            "get_orders_order", "get_orders_view", "get_orders_note",
            "orders_for_campaign", "orders_green",
            "orders_panel", "orders_verdict", "orders_index",
            "register_orders_order", "register_orders_view",
            "view_orders", "register_orders_book",
            "record_orders_book", "report_orders",
            "_publish_orders_record", "_orders_screen",
            "_orders_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.orders_status()
        assert agent.get_orders_order(
            "order-held-order").title == "The held order"
        assert agent.get_orders_view(
            "view-orders").view_filter == "all"
        assert agent.get_orders_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.order_id for d in agent.orders_for_campaign(
            "campaign-m226-orders")] == [
            "order-own-order", "order-bare-order",
            "order-leaping-order"]
        assert [d.order_id for d in agent.orders_green()] == [
            "order-held-order", "order-retried-order", "order-own-order"]
        agent.orders_panel()
        agent.orders_verdict()
        agent.orders_index()
        agent.report_orders()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _ORDER_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_orders_order("order-nope")
        with pytest.raises(KeyError):
            agent.get_orders_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_orders_note("note-nope")
        with pytest.raises(ValueError):
            agent.orders_for_campaign("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_orders_order(_order())
        status = agent.orders_status()
        assert [d["order_id"] for d in status["order_records"]] == ["order-test"]
        assert status["book"]["title"] == "An unheld order book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["stage"] for e in status["index"]["orders"]] == [
            "kept"]
        assert status["first_note"] is None
        assert "order-test" in status["screen"]
    def test_held_order_never_falls_back_to_the_example(
            self, agent):
        agent.register_orders_order(_order())
        with pytest.raises(KeyError):
            agent.get_orders_order("order-held-order")
        with pytest.raises(KeyError):
            agent.get_orders_view("view-orders")
        with pytest.raises(KeyError):
            agent.get_orders_note("note-note-first")
        order = agent.get_orders_order("order-test")
        assert order.title == "A test order"
        assert agent.orders_book().title == (
            "An unheld order book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_orders_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.order_id == "order-held-order"
        status = agent.orders_status()
        assert status["index"]["gaps"] == [
            "order-bare-order", "order-leaping-order"]
        assert status["first_note"]["order_id"] == (
            "order-held-order")
        assert status["first_note"]["stance"] == "note"

class TestOrderAgentHolding:
    def test_register_order_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_orders_order(_order())
        assert result["order"]["order_id"] == "order-test"
        assert result["record_news"]["type"] == "order_order"
        assert "order-test" in result["screen"]
        events = _order_events(store, session_id, "order_order")
        assert len(events) == 1
        agent.close()

    def test_duplicate_order_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_orders_order(_order())
        with pytest.raises(ValueError):
            agent.register_orders_order(_order(seq=9))
        with pytest.raises(ValueError):
            agent.register_orders_order(_order(order_id="order-two"))
        events = _order_events(store, session_id, "order_order")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_orders_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_order_events(
            store, session_id, "order_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_orders_order(_order())
        result = agent.view_orders("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "order_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "kept"
        assert len(_order_events(
            store, session_id, "order_view")) == 1
        assert len(_order_events(
            store, session_id, "order_panel")) == 1
        assert len(_order_events(
            store, session_id, "order_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_orders_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "order_run", "order_order", "order_view"]
        assert len(_order_events(
            store, session_id, "order_order")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_orders_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "order_panel"
        assert result["index_record"]["gaps"] == [
            "order-bare-order", "order-leaping-order"]
        with pytest.raises(ValueError):
            agent.record_orders_book()
        assert len(_order_events(
            store, session_id, "order_run")) == 3
        assert len(_order_events(
            store, session_id, "order_order")) == 5
        assert len(_order_events(
            store, session_id, "order_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_orders_book_file(tmp_path)
        book = load_order_file(path)
        result = agent.record_orders_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_runrt_renders_example_then_held_book_only(self, agent):
        order = agent.report_orders()
        assert order["book"]["title"] == EXAMPLE_TITLE
        assert order["verdict"]["verdict"] == "held"
        assert order["index"]["gaps"] == [
            "order-bare-order", "order-leaping-order"]
        assert "order-held-order" in order["book_text"]
        assert "kept - The held order (order-held-order)" in order["index_text"]
        agent.register_orders_order(_order())
        order = agent.report_orders()
        assert order["book"]["title"] == "An unheld order book"
        assert order["panel"] is None
        assert order["verdict"] is None

class TestOrderTerminalHeading:
    def test_show_order_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/orders")
        assert "The Order Gate (M-226)" in text
        _, _, text = _slash(agent, "/orders order order-held-order")
        assert "Order: The held order" in text
        _, _, text = _slash(
            agent, "/orders stage kept")
        assert "Order: The held order" in text
        _, _, text = _slash(agent, "/orders stage triple order")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/orders campaign campaign-m226-orders")
        assert "order-bare-order" in text
        assert "order-held-order" not in text
        _, _, text = _slash(agent, "/orders view view-orders")
        assert "filter all" in text
        _, _, text = _slash(agent, "/orders note note-note-first")
        assert "Order note note order-held-order" in text
        _, _, text = _slash(agent, "/orders index")
        assert "Order index" in text
        assert "order-bare-order" in text
        _, _, text = _slash(agent, "/orders panel")
        assert "Order panel under view view-orders" in text
        _, _, text = _slash(agent, "/orders verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/orders [show|order <order-id>"
                "|stage <stage>|campaign <campaign-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/orders dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/orders order order-nope")
        assert "no order named" in text
@pytest.fixture()
def order_handler(agent, monkeypatch):
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


def _order_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestOrderCommand:
    def test_show_is_default(self, order_handler, agent):
        order_handler._handle_orders("")
        assert "The Order Gate (M-226)" in (
            _order_published_text(order_handler))

    def test_order_check_slice_view_note_index_panel_verdict(
            self, order_handler, agent):
        order_handler._handle_orders("order order-held-order")
        assert "Order: The held order" in _order_published_text(
            order_handler)
        order_handler._handle_orders(
            "stage kept")
        assert "Order: The held order" in _order_published_text(
            order_handler)
        order_handler._handle_orders("campaign campaign-m226-orders")
        assert "order-bare-order" in _order_published_text(
            order_handler)
        order_handler._handle_orders("view view-orders")
        assert "filter all" in _order_published_text(order_handler)
        order_handler._handle_orders("note note-note-first")
        assert "Order note note order-held-order" in (
            _order_published_text(order_handler))
        order_handler._handle_orders("index")
        assert "Order index" in _order_published_text(order_handler)
        order_handler._handle_orders("panel")
        assert "Order panel under view" in _order_published_text(
            order_handler)
        order_handler._handle_orders("verdict")
        assert "held" in _order_published_text(order_handler)
    def test_bad_grammar_is_published(
            self, order_handler, agent):
        order_handler._handle_orders("dance party")
        assert USAGE in _order_published_text(order_handler)
        order_handler._handle_orders("order order-nope")
        assert "no order named" in _order_published_text(
            order_handler)


class TestChatScreenRoutingOrder:
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
        screen.handle_command("/orders panel", _FakeLog())
        assert calls == [("/orders", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/orders[/green] - show the Order gate (M-226)" in (
            text)
        assert ('"/orders": "Usage: /orders | '
                '/orders order <order-id>') in text

class TestOrderDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.orders_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-orders"
        verdict = agent.orders_verdict()
        assert verdict.verdict == "held"
        found = agent.orders_verdict("view-kept")
        assert found.verdict == "kept"
        assert found.green_shown == 3
        agent.register_orders_order(_order())
        with pytest.raises(ValueError):
            agent.orders_panel()
        with pytest.raises(ValueError):
            agent.orders_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_orders_order(_order(stages=[]))
        result = agent.view_orders("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.orders_index()
        assert [e["stage"] for e in result["index"]["orders"]] == (
            EXAMPLE_STAGES)
        assert result["index"]["gaps"] == [
            "order-bare-order", "order-leaping-order"]
        assert "kept - The held order (order-held-order)" in (
            result["index_text"])
        order = agent.get_orders_order("order-leaping-order")
        assert order_gaps(order, agent.orders_book()) == (
            "steps from recorded to kept, which the order sequence "
            "does not allow",)
        assert order_green(order, agent.orders_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _ORDER_EVENT_TYPES] == []
        agent.close()
