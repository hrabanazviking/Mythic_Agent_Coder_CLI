"""M-242 Cross-app method - pure-layer tests.

TIER: integration

The pure layer is the tracker, held as data: one
record per exchange, held whole - the repo it
answers for, opened by repo id, its title, the
steps it walked in walk exchange and the evidence
it carries, held by repo. The question walk is
explicit - opened, triaged, crafted, reviewed,
held, with their legal steps held as data -
and a exchange's standing is derived at call
time: a exchange that opens anywhere but opened, steps where the sequence does not allow,
carries a bare claim in place of held evidence,
or has not yet opened held stands open,
opened in its gaps. A exchange stands only for
an active repo: a exchange naming no held
repo, or one that is not active, refuses by
name. The exchange's trace - its walked steps
as one line - is derived at call time, and a held
trace record stands current only while it agrees
with the derived trace. The index, panel,
verdict, ledger, trace, exchange and current
exchange are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
question was actually answered, reviewed or
held live. The shipped example book is held
in a data file, and a loader reads a book from
any file. No charter row names this repo: the
M-171 TUI charter binds Part VIII alone, and the
M-005 method charter names the whole of Part X
as the part that executes it, both pinned live
below.
"""


from pathlib import Path

import pytest
import yaml

from mythic_agent.core.samverk_bridge import (
    EXAMPLE_STAGE,
    BARE_CLAIMS,
    HELD_EVIDENCE,
    INDEX_ACTION,
    STAGES,
    CLAIM_KINDS,
    TRANSITIONS,
    REPO_STATES,
    STAGE_FIELDS,
    PLAIN_EXPLANATION,
    EXCHANGE_RESOURCE,
    EXCHANGE_RULE,
    EXCHANGE_SCHEMA,
    EXCHANGE_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    ExchangeRecord,
    IndexExchange,
    RepoRef,
    NoteRecord,
    ExchangeBook,
    ExchangeIndex,
    ExchangePanel,
    ExchangeRegistry,
    ExchangeVerdict,
    ExchangeView,
    trace_for_exchange,
    ledger_record,
    book_record,
    build_trace,
    build_book,
    build_exchange,
    build_repo_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_exchange,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    exchange_for_check,
    exchange_gaps,
    exchange_exchange,
    exchange_record,
    exchange_green,
    exchanges_for_repo,
    first_note,
    format_book,
    format_exchange,
    format_index,
    format_note,
    format_stage,
    format_panel,
    format_exchange_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    repo_record,
    load_exchange,
    legal_step,
    load_exchange_file,
    next_stage,
    normalize_stage,
    normalize_claim_kind,
    normalize_repo_state,
    normalize_stance,
    normalize_view_filter,
    note_for_exchange,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_exchange_args,
    green_exchanges,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_exchanges,
    validate_book,
    validate_exchange,
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
EXAMPLE_TITLE = "Samverk bridge at the M-242 slice run"
EXAMPLE_STAGES = ["held", "held", "held"]
EXAMPLE_RUN_IDS = (
    "exchange-held-exchange", "exchange-retried-exchange",
    "exchange-own-exchange", "exchange-bare-exchange",
    "exchange-leaping-exchange")
EXAMPLE_TRACE = "opened > triaged > crafted > reviewed > held"


def _ref(**overrides):
    fields = {
        "repo_id": "repo-test",
        "seq": 1,
        "title": "A test repo",
        "state": "live",
        "detail": "A test repo reference held as data.",
        "recorded_on": ON,
        "actor": BY,
        "repo": "test repo",
        "origin_session": "exchange-test",
    }
    fields.update(overrides)
    return build_repo_ref(fields)


def _exchange(**overrides):
    fields = {
        "exchange_id": "exchange-test",
        "seq": 1,
        "repo_id": "repo-test",
        "title": "A test exchange",
        "stages": ["opened", "triaged", "crafted", "reviewed", "held"],
        "claims": [],
        "detail": "A test exchange held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "repo": "test repo",
        "origin_session": "exchange-test",
    }
    fields.update(overrides)
    return build_exchange(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "repo": "test repo",
        "origin_session": "exchange-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "exchange_id": "exchange-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "repo": "test repo",
        "origin_session": "exchange-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "exchange_id": "exchange-test",
        "trace": "opened > triaged > crafted > reviewed > held",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "repo": "test repo",
        "origin_session": "exchange-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(repos=None, exchanges=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": EXCHANGE_SCHEMA,
        "repo": "M-242",
        "samverk_bridge": {"title": "A test exchange book"},
        "repos": [item.to_record() for item in (
            repos if repos is not None else [_ref()])],
        "exchange_records": [item.to_record() for item in (
            exchanges if exchanges is not None else [_exchange()])],
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
    return _book(exchanges=[
        _exchange(),
        _exchange(exchange_id="exchange-hidden", seq=2,
               title="A hidden exchange", stages=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_exchange()
    assert book.title == EXAMPLE_TITLE
    assert book.exchange_ids() == EXAMPLE_RUN_IDS
    assert book.repo_ids() == (
        "forge-mythic", "forge-samtal",
        "forge-archive")
    assert [v.view_id for v in book.views] == [
        "view-exchanges", "view-held"]
    assert [m.exchange_id for m in book.notes] == [
        "exchange-held-exchange", "exchange-bare-exchange"]
    assert [a.exchange_id for a in book.traces] == ["exchange-held-exchange"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-samverk"
    assert panel.as_of == "2026-11-11"
    assert [row.item_id for row in panel.rows] == list(book.exchange_ids())
    derived = derive_panel(book, "view-exchanges")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-exchanges").verdict == "held"
    assert derive_verdict(book, "view-exchanges").green_shown == 3
    assert derive_verdict(book, "view-held").verdict == "held"
    assert derive_verdict(book, "view-held").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / EXCHANGE_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == EXCHANGE_SCHEMA
    assert raw["repo"] == "M-242"
    assert "verdict" not in raw
    assert "exchange_index" not in raw
    assert "ledger" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-242")]
    assert slice_.title == "Samverk bridge"
    assert slice_.part == 10
    assert "repos, issues, and PRs on Volmarr" in slice_.summary
    assert "once Samverk" in slice_.summary
    assert EXCHANGE_SLICE == "M-242"

def test_charter_rows_do_not_name_m242():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-242" not in owners
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
    assert REPO_STATES == ("live", "dormant")
    assert STAGES == ("opened", "triaged", "crafted", "reviewed", "held")
    assert HELD_EVIDENCE == ("repo_ref", "issue_ref", "pr_ref", "review_ref", "craft_ref", "link_ref")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_KINDS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["reviewed"] == ("opened", "held")
    assert TRANSITIONS["held"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_STAGE == "held"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_repo_state("LIVE") == "live"
    assert normalize_stage("CRAFTED") == "crafted"
    assert normalize_claim_kind("FEELING") == "feeling"
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    with pytest.raises(ValueError):
        normalize_repo_state("blessed")
    with pytest.raises(ValueError):
        normalize_stage("polish")
    with pytest.raises(ValueError):
        normalize_claim_kind("weather")
    assert legal_step("crafted", "reviewed") is True
    assert legal_step("triaged", "held") is False
    assert legal_step("held", "opened") is False
    assert next_stage("opened") == "triaged"
    assert next_stage("crafted") == "reviewed"
    assert next_stage("reviewed", failed=True) == "opened"
    assert next_stage("reviewed") == "held"
    assert next_stage("held") is None
    assert "held as data alone" in EXCHANGE_RULE
    assert "exchange sequence" in EXCHANGE_RULE
    assert "M-242" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /samverkbridge")

def test_shipped_book_judged_honestly_as_data():
    book = load_exchange()
    opening = book.exchange_for("exchange-held-exchange")
    assert exchange_green(opening, book) is True
    assert exchange_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Exchange: The held exchange",
        "Repo: forge-mythic",
        "Stage: held",
        "Claims: repo_ref")
    asking = book.exchange_for("exchange-bare-exchange")
    assert exchange_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert exchange_green(asking, book) is False
    skipping = book.exchange_for("exchange-leaping-exchange")
    assert exchange_gaps(skipping, book) == (
        "steps from triaged to held, which the exchange sequence "
        "does not allow",)
    assert [g.exchange_id for g in green_exchanges(book)] == [
        "exchange-held-exchange", "exchange-retried-exchange", "exchange-own-exchange"]
    index = derive_index(book)
    assert [e.stage for e in index.exchanges] == EXAMPLE_STAGES
    assert index.gaps == ("exchange-bare-exchange", "exchange-leaping-exchange")
    assert exchange_for_check(book, EXAMPLE_STAGE).exchange_id == (
        "exchange-held-exchange")
    assert exchange_for_check(book, "triple exchange") is None
    assert transition_breaks(book) == (
        "exchange-leaping-exchange: triaged > held",)
    assert [g.exchange_id for g in exchange_exchange(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "exchange-held-exchange") == EXAMPLE_TRACE
    assert trace_current(book, "exchange-held-exchange") is True
    assert trace_current(book, "exchange-retried-exchange") is False
    assert trace_for_exchange(
        book, "exchange-held-exchange").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_exchange(
        book, "exchange-held-exchange", "note").note_id == (
            "note-note-first")
    assert note_for_exchange(book, "exchange-nope") is None
    assert current_exchange(book).exchange_id == "exchange-bare-exchange"
    ledger = ledger_record(book)
    assert ledger["standings"] == [
        {"standing": "complete", "exchange_records": 3},
        {"standing": "open", "exchange_records": 2}]
    assert ledger["total"] == 5
    assert ledger["current_exchange"] == "exchange-bare-exchange"
    assert ledger["traces"] == [
        {"exchange_id": "exchange-held-exchange", "trace": "current"},
        {"exchange_id": "exchange-retried-exchange", "trace": "unheld"},
        {"exchange_id": "exchange-own-exchange", "trace": "unheld"},
        {"exchange_id": "exchange-bare-exchange", "trace": "unheld"},
        {"exchange_id": "exchange-leaping-exchange", "trace": "unheld"}]
    assert ledger["breaks"] == ["exchange-leaping-exchange: triaged > held"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 268
    assert citizen["next_slice"] == "M-269"
    assert citizen["m242_title"] == "Samverk bridge"
    assert citizen["m242_part"] == 10
    assert citizen["m242_status"] == "done"

def test_exchange_record_round_trips():
    exchange = _exchange()
    assert validate_exchange(exchange) is exchange
    rebuilt = build_exchange(exchange.to_record())
    assert rebuilt == exchange
    assert rebuilt.item_id == "exchange-test"
    assert rebuilt.stage == "held"
    record = exchange_record(exchange)
    assert record["type"] == "exchange_exchange"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert repo_record(ref)["type"] == "exchange_run"
    assert repo_record(ref)["state"] == "live"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _exchange(stages=[])
    assert exchange_gaps(silent) == (
        "has passed through no step: the exchange has not started",)
    assert exchange_green(silent) is False
    walking = _exchange(stages=["opened", "triaged"])
    assert exchange_gaps(walking) == (
        "has not reached held: the exchange stands at triaged",)
    assert walking.stage == "triaged"
    sideways = _exchange(stages=["triaged", "crafted", "reviewed", "held"])
    assert exchange_gaps(sideways) == (
        "opens at triaged, not at opened: the exchange opens "
        "with the reflection",)
    repaired = _exchange(stages=["opened", "triaged", "crafted", "reviewed", "opened", "triaged", "crafted", "reviewed", "held"])
    assert exchange_gaps(repaired) == ()
    assert exchange_green(repaired) is True
    with pytest.raises(ValueError):
        _exchange(stages=[42])
    with pytest.raises(ValueError):
        _exchange(stages="inspect as a bare string")
    with pytest.raises(ValueError):
        _exchange(stages=["opened", "polish"])
    with pytest.raises(ValueError):
        _exchange(claims=["weather"])
    with pytest.raises(ValueError):
        _exchange(claims="repo_ref")
    none_exchange = _exchange(stages=None, claims=None)
    assert none_exchange.stages == ()
    assert none_exchange.claims == ()

def test_link_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "exchanges", "coverage", "current_exchange",
                "ledger", "exchange"):
        fields = _exchange().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_exchange(fields)
    fields = _exchange().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_exchange(fields)


def test_link_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _exchange().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_exchange(fields)


def test_exchange_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _exchange(title="")
    with pytest.raises(ValueError):
        _exchange(repo_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "opened > triaged > crafted > reviewed > held"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_exchanges_own_fields():
    exchange = _exchange(claims=["repo_ref"])
    assert plain_lines(exchange) == (
        "Exchange: A test exchange",
        "Repo: repo-test",
        "Stage: held",
        "Claims: repo_ref")
    segment = segment_of(exchange)
    assert segment.startswith("exchange-test: A test exchange")
    assert "stage: 'held'" in segment
    assert "gaps: none" in segment
    assert plain_words(exchange).startswith(
        "A test exchange - from repo-test")

def test_red_exchanges_stand_named_in_their_gaps():
    asking = _exchange(claims=["feeling", "repo_ref", "summary"])
    assert exchange_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert exchange_green(asking) is False
    skipping = _exchange(stages=["opened", "triaged", "held"])
    assert exchange_gaps(skipping) == (
        "steps from triaged to held, which the exchange sequence "
        "does not allow",)
    book = _book(exchanges=[
        _exchange(),
        _exchange(exchange_id="exchange-skipping", seq=2,
             stages=["opened", "triaged", "held"]),
    ])
    assert transition_breaks(book) == (
        "exchange-skipping: triaged > held",)
    assert current_exchange(book).exchange_id == "exchange-skipping"
    assert [g.exchange_id for g in exchange_exchange(book)] == [
        "exchange-test", "exchange-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "exchange_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "exchange_note"
    assert record["exchange_id"] == "exchange-test"
    assert view_plain_words(view) == "View view-test: shows all exchanges."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_exchanges_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.stage for e in index.exchanges] == ["held"]
    assert index.exchanges[0] == IndexExchange(
        stage="held",
        exchange_id="exchange-test", title="A test exchange")
    assert index.gaps == ("exchange-hidden",)
    record = index_record(book)
    assert record["type"] == "exchange_index"
    assert record["gaps"] == ["exchange-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "exchange_book"

def test_check_target_reaches_its_exchange_and_an_unheld_target_reaches_nothing():
    book = load_exchange()
    assert exchange_for_check(book, "held").exchange_id == (
        "exchange-held-exchange")
    assert exchange_for_check(book, "") is None
    assert exchange_for_check(book, None) is None
    assert exchange_for_check(book, "not held at all") is None
    text = format_stage(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_exchange()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Exchange note note exchange-held-exchange" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").exchange_id == "exchange-test"
    assert note_for_exchange(book, "exchange-test").note_id == "note-test"
    assert note_for_exchange(book, "exchange-test", "praise") is None
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
    row = build_row(None, _exchange(), book)
    assert row.standing == "complete"
    assert validate_row(row, _exchange(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_exchanges():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "exchange_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "held"
    empty_book = _book(exchanges=[_exchange(stages=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(ExchangeVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_exchanges():
    book = load_exchange()
    assert [g.exchange_id for g in shown_exchanges(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.exchange_id for g in shown_exchanges(book, "view-held")] == [
        "exchange-held-exchange", "exchange-retried-exchange", "exchange-own-exchange"]
    assert [g.exchange_id for g in exchanges_for_repo(
        book, "forge-samtal")] == [
            "exchange-own-exchange", "exchange-bare-exchange",
            "exchange-leaping-exchange"]
    assert exchanges_for_repo(book, "repo-nope") == ()
    assert current_exchange(_mixed_book()).exchange_id == "exchange-hidden"
    assert current_exchange(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "exchange-test") == (
        "opened > triaged > crafted > reviewed > held")
    assert trace_current(stale, "exchange-test") is False
    assert ledger_record(stale)["traces"] == [
        {"exchange_id": "exchange-test", "trace": "stale"}]

def test_issue_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(exchanges=[_exchange(), _exchange(seq=2)])
    with pytest.raises(ValueError):
        _book(exchanges=[_exchange(), _exchange(exchange_id="exchange-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(exchanges=[_exchange(repo_id="repo-nope")])
    with pytest.raises(ValueError):
        _book(repos=[_ref(), _ref(
            repo_id="repo-cold", seq=2, state="dormant")],
            exchanges=[_exchange(repo_id="repo-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(repo_id="repo-nope")])
    fields = {
        "schema": EXCHANGE_SCHEMA, "repo": "M-242",
        "samverk_bridge": {"title": "A crafted book"},
        "repos": [_ref().to_record()],
        "exchange_records": [_exchange().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "held"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_exchange"] = "exchange-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_exchange")
    fields["trace"] = "exchange-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / EXCHANGE_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "samverk_bridge.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_exchange_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.exchange_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = ExchangeRegistry()
    assert registry.title() is None
    registry.register_repo_ref(_ref())
    registry.register_exchange(_exchange())
    registry.register_view(_view())
    assert [g.exchange_id for g in registry.list_exchanges()] == ["exchange-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_exchange("exchange-test").title == "A test exchange"
    assert registry.get_slice("repo-test").state == "live"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("exchange-test").exchange_id == "exchange-test"
    with pytest.raises(ValueError):
        registry.register_exchange(_exchange(seq=9))
    with pytest.raises(ValueError):
        registry.register_exchange(_exchange(exchange_id="exchange-two"))
    with pytest.raises(KeyError):
        registry.get_exchange("exchange-nope")
    assert registry.book().title == "An unheld exchange book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = ExchangeRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test exchange book"
    assert registry.title() == "A test exchange book"
    assert len(registry.list_exchanges()) == 2
    other = ExchangeRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    exchange = _exchange()
    assert "A test exchange" in plain_words(exchange)
    assert panel_plain_words(_mixed_book()).startswith(
        "The exchange book holds 2 exchanges")
    assert verdict_plain_words(_mixed_book()) == (
        "The exchanges stand held: 1 of 2 shown exchanges stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green exchanges; red, "
        "opened in its gaps: exchange-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_exchange(exchange)
    assert "Exchange: A test exchange" in text
    assert "stands complete" in text
    text = format_exchange(_exchange(stages=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The Samverk Bridge (M-242) - A test exchange book" in book_text
    assert "exchange-hidden" in format_book(_mixed_book(), "repo-test")
    assert "Exchange panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "held - A test exchange (exchange-test)" in index_text
    assert "exchange-hidden" in index_text
    screen = format_exchange_screen()
    assert "The Samverk Bridge (M-242)" in screen
    assert "exchange-bare-exchange" in screen

def test_parse_args_well_and_loader_targets():
    assert parse_exchange_args("") == ("show", None)
    assert parse_exchange_args(None) == ("show", None)
    assert parse_exchange_args("show") == ("show", None)
    assert parse_exchange_args("exchange exchange-test") == (
        "exchange", "exchange-test")
    assert parse_exchange_args("stage held") == (
        "stage", "held")
    assert parse_exchange_args("repo repo-test") == (
        "repo", "repo-test")
    assert parse_exchange_args("view view-test") == ("view", "view-test")
    assert parse_exchange_args("note note-test") == ("note", "note-test")
    assert parse_exchange_args("index") == ("index", None)
    assert parse_exchange_args("panel") == ("panel", None)
    assert parse_exchange_args("verdict") == ("verdict", None)
    for bad in ("dance", "exchange", "stage", "repo", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_exchange_args(bad)
    ledger = ledger_record()
    assert ledger["type"] == "exchange_well"
    assert ledger["total"] == 5
    assert ledger["current_exchange"] == "exchange-bare-exchange"
    book = load_exchange({
        "schema": EXCHANGE_SCHEMA, "repo": "M-242",
        "samverk_bridge": {"title": "A crafted book"},
        "repos": [_ref().to_record()],
        "exchange_records": [_exchange().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, ExchangeBook)
    assert book.title == "A crafted book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_exchange({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_exchange({"repo": "M-999"})
    built = build_exchange(
        exchange_id="exchange-kw", seq=3, repo_id="repo-test",
        title="Kw Exchange", stages=["opened", "triaged", "crafted", "reviewed", "held"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        repo="test repo", origin_session="exchange-test")
    assert built.exchange_id == "exchange-kw"
    assert exchange_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-242 agent layer: the agent holds a exchange
# book for the session, exchanges and views are
# published as session news through the
# checkpoint target (ledger first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held exchanges, the ledger is derived from
# the held exchanges' completeness, the roadmap standing
# is reviewed from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no repo. This layer exchanges
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session ledger news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_EXCHANGE_EVENT_TYPES = (
    "exchange_exchange", "exchange_run", "exchange_view",
    "exchange_panel", "exchange_verdict")


def _exchange_events(store, session_id, repo):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == repo]


def _write_samverkbridge_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / EXCHANGE_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "samverk_bridge.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestExchangeAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.samverkbridge_status()
        assert status["exchange_records"] == []
        assert status["repos"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["samverkbridge_book"]["title"] == EXAMPLE_TITLE
        assert len(status["samverkbridge_book"]["repos"]) == 3
        assert len(status["samverkbridge_book"]["exchange_records"]) == 5
        assert len(status["samverkbridge_book"]["views"]) == 2
        assert len(status["samverkbridge_book"]["notes"]) == 2
        assert len(status["samverkbridge_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-samverk"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["stage"] for e in status["index"]["exchanges"]] == (
            EXAMPLE_STAGES)
        assert status["index"]["gaps"] == [
            "exchange-bare-exchange", "exchange-leaping-exchange"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["ledger"]["total"] == 5
        assert status["ledger"]["current_exchange"] == "exchange-bare-exchange"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 268
        assert status["roadmap"]["next_slice"] == "M-269"
        assert status["roadmap"]["m242_title"] == "Samverk bridge"
        assert "held as data alone" in status["rule"]
        assert "exchange-bare-exchange" in status["plain_words"]
        assert "The Samverk Bridge (M-242)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._samverkbridge_registry()
        assert agent._samverkbridge_registry() is first
        assert agent._samverkbridge_store is first
        for name in ("samverkbridge_book", "samverkbridge_status", "samverkbridge_panel",
                     "samverkbridge_verdict", "samverkbridge_index", "report_samverkbridge"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_samverkbridge_registry", "samverkbridge_book", "samverkbridge_status",
            "get_samverkbridge_exchange", "get_samverkbridge_view", "get_samverkbridge_note",
            "exchanges_for_repo", "samverkbridge_green",
            "samverkbridge_panel", "samverkbridge_verdict", "samverkbridge_index",
            "register_samverkbridge_exchange", "register_samverkbridge_view",
            "view_samverkbridge", "register_samverkbridge_book",
            "record_samverkbridge_book", "report_samverkbridge",
            "_publish_samverkbridge_record", "_samverkbridge_screen",
            "_samverkbridge_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.samverkbridge_status()
        assert agent.get_samverkbridge_exchange(
            "exchange-held-exchange").title == "The held exchange"
        assert agent.get_samverkbridge_view(
            "view-exchanges").view_filter == "all"
        assert agent.get_samverkbridge_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.exchange_id for d in agent.exchanges_for_repo(
            "forge-samtal")] == [
            "exchange-own-exchange", "exchange-bare-exchange",
            "exchange-leaping-exchange"]
        assert [d.exchange_id for d in agent.samverkbridge_green()] == [
            "exchange-held-exchange", "exchange-retried-exchange", "exchange-own-exchange"]
        agent.samverkbridge_panel()
        agent.samverkbridge_verdict()
        agent.samverkbridge_index()
        agent.report_samverkbridge()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _EXCHANGE_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_samverkbridge_exchange("exchange-nope")
        with pytest.raises(KeyError):
            agent.get_samverkbridge_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_samverkbridge_note("note-nope")
        with pytest.raises(ValueError):
            agent.exchanges_for_repo("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_samverkbridge_exchange(_exchange())
        status = agent.samverkbridge_status()
        assert [d["exchange_id"] for d in status["exchange_records"]] == ["exchange-test"]
        assert status["book"]["title"] == "An unheld exchange book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["stage"] for e in status["index"]["exchanges"]] == [
            "held"]
        assert status["first_note"] is None
        assert "exchange-test" in status["screen"]
    def test_held_exchange_never_falls_back_to_the_example(
            self, agent):
        agent.register_samverkbridge_exchange(_exchange())
        with pytest.raises(KeyError):
            agent.get_samverkbridge_exchange("exchange-held-exchange")
        with pytest.raises(KeyError):
            agent.get_samverkbridge_view("view-exchanges")
        with pytest.raises(KeyError):
            agent.get_samverkbridge_note("note-note-first")
        exchange = agent.get_samverkbridge_exchange("exchange-test")
        assert exchange.title == "A test exchange"
        assert agent.samverkbridge_book().title == (
            "An unheld exchange book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_samverkbridge_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.exchange_id == "exchange-held-exchange"
        status = agent.samverkbridge_status()
        assert status["index"]["gaps"] == [
            "exchange-bare-exchange", "exchange-leaping-exchange"]
        assert status["first_note"]["exchange_id"] == (
            "exchange-held-exchange")
        assert status["first_note"]["stance"] == "note"

class TestExchangeAgentHolding:
    def test_register_exchange_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_samverkbridge_exchange(_exchange())
        assert result["exchange"]["exchange_id"] == "exchange-test"
        assert result["record_news"]["type"] == "exchange_exchange"
        assert "exchange-test" in result["screen"]
        events = _exchange_events(store, session_id, "exchange_exchange")
        assert len(events) == 1
        agent.close()

    def test_duplicate_link_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_samverkbridge_exchange(_exchange())
        with pytest.raises(ValueError):
            agent.register_samverkbridge_exchange(_exchange(seq=9))
        with pytest.raises(ValueError):
            agent.register_samverkbridge_exchange(_exchange(exchange_id="exchange-two"))
        events = _exchange_events(store, session_id, "exchange_exchange")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_samverkbridge_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_exchange_events(
            store, session_id, "exchange_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_samverkbridge_exchange(_exchange())
        result = agent.view_samverkbridge("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "exchange_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "held"
        assert len(_exchange_events(
            store, session_id, "exchange_view")) == 1
        assert len(_exchange_events(
            store, session_id, "exchange_panel")) == 1
        assert len(_exchange_events(
            store, session_id, "exchange_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_exchange(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_samverkbridge_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "exchange_run", "exchange_exchange", "exchange_view"]
        assert len(_exchange_events(
            store, session_id, "exchange_exchange")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_samverkbridge_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "exchange_panel"
        assert result["index_record"]["gaps"] == [
            "exchange-bare-exchange", "exchange-leaping-exchange"]
        with pytest.raises(ValueError):
            agent.record_samverkbridge_book()
        assert len(_exchange_events(
            store, session_id, "exchange_run")) == 3
        assert len(_exchange_events(
            store, session_id, "exchange_exchange")) == 5
        assert len(_exchange_events(
            store, session_id, "exchange_view")) == 2
        agent.close()

    def test_book_from_a_file_is_linked_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_samverkbridge_book_file(tmp_path)
        book = load_exchange_file(path)
        result = agent.record_samverkbridge_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_runrt_renders_example_then_held_book_only(self, agent):
        exchange = agent.report_samverkbridge()
        assert exchange["book"]["title"] == EXAMPLE_TITLE
        assert exchange["verdict"]["verdict"] == "held"
        assert exchange["index"]["gaps"] == [
            "exchange-bare-exchange", "exchange-leaping-exchange"]
        assert "exchange-held-exchange" in exchange["book_text"]
        assert "held - The held exchange (exchange-held-exchange)" in exchange["index_text"]
        agent.register_samverkbridge_exchange(_exchange())
        exchange = agent.report_samverkbridge()
        assert exchange["book"]["title"] == "An unheld exchange book"
        assert exchange["panel"] is None
        assert exchange["verdict"] is None

class TestExchangeTerminalHeading:
    def test_show_exchange_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/samverkbridge")
        assert "The Samverk Bridge (M-242)" in text
        _, _, text = _slash(agent, "/samverkbridge exchange exchange-held-exchange")
        assert "Exchange: The held exchange" in text
        _, _, text = _slash(
            agent, "/samverkbridge stage held")
        assert "Exchange: The held exchange" in text
        _, _, text = _slash(agent, "/samverkbridge stage triple exchange")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/samverkbridge repo forge-samtal")
        assert "exchange-bare-exchange" in text
        assert "exchange-held-exchange" not in text
        _, _, text = _slash(agent, "/samverkbridge view view-exchanges")
        assert "filter all" in text
        _, _, text = _slash(agent, "/samverkbridge note note-note-first")
        assert "Exchange note note exchange-held-exchange" in text
        _, _, text = _slash(agent, "/samverkbridge index")
        assert "Exchange index" in text
        assert "exchange-bare-exchange" in text
        _, _, text = _slash(agent, "/samverkbridge panel")
        assert "Exchange panel under view view-exchanges" in text
        _, _, text = _slash(agent, "/samverkbridge verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/samverkbridge [show|exchange <exchange-id>"
                "|stage <stage>|repo <repo-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/samverkbridge dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/samverkbridge exchange exchange-nope")
        assert "no exchange opened" in text
@pytest.fixture()
def exchange_handler(agent, monkeypatch):
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


def _exchange_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestExchangeSource:
    def test_show_is_default(self, exchange_handler, agent):
        exchange_handler._handle_samverkbridge("")
        assert "The Samverk Bridge (M-242)" in (
            _exchange_published_text(exchange_handler))

    def test_exchange_check_slice_view_note_index_panel_verdict(
            self, exchange_handler, agent):
        exchange_handler._handle_samverkbridge("exchange exchange-held-exchange")
        assert "Exchange: The held exchange" in _exchange_published_text(
            exchange_handler)
        exchange_handler._handle_samverkbridge(
            "stage held")
        assert "Exchange: The held exchange" in _exchange_published_text(
            exchange_handler)
        exchange_handler._handle_samverkbridge("repo forge-samtal")
        assert "exchange-bare-exchange" in _exchange_published_text(
            exchange_handler)
        exchange_handler._handle_samverkbridge("view view-exchanges")
        assert "filter all" in _exchange_published_text(exchange_handler)
        exchange_handler._handle_samverkbridge("note note-note-first")
        assert "Exchange note note exchange-held-exchange" in (
            _exchange_published_text(exchange_handler))
        exchange_handler._handle_samverkbridge("index")
        assert "Exchange index" in _exchange_published_text(exchange_handler)
        exchange_handler._handle_samverkbridge("panel")
        assert "Exchange panel under view" in _exchange_published_text(
            exchange_handler)
        exchange_handler._handle_samverkbridge("verdict")
        assert "held" in _exchange_published_text(exchange_handler)
    def test_bad_grammar_is_published(
            self, exchange_handler, agent):
        exchange_handler._handle_samverkbridge("dance party")
        assert USAGE in _exchange_published_text(exchange_handler)
        exchange_handler._handle_samverkbridge("exchange exchange-nope")
        assert "no exchange opened" in _exchange_published_text(
            exchange_handler)


class TestChatScreenRoutingExchange:
    def test_onwell_routes_as_system_repo(self, monkeypatch):
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
        screen.handle_command("/samverkbridge panel", _FakeLog())
        assert calls == [("/samverkbridge", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/samverkbridge[/green] - show the Samverk bridge (M-242)" in (
            text)
        assert ('"/samverkbridge": "Usage: /samverkbridge | '
                '/samverkbridge exchange <exchange-id>') in text

class TestExchangeDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.samverkbridge_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-exchanges"
        verdict = agent.samverkbridge_verdict()
        assert verdict.verdict == "held"
        opened = agent.samverkbridge_verdict("view-held")
        assert opened.verdict == "held"
        assert opened.green_shown == 3
        agent.register_samverkbridge_exchange(_exchange())
        with pytest.raises(ValueError):
            agent.samverkbridge_panel()
        with pytest.raises(ValueError):
            agent.samverkbridge_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_samverkbridge_exchange(_exchange(stages=[]))
        result = agent.view_samverkbridge("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.samverkbridge_index()
        assert [e["stage"] for e in result["index"]["exchanges"]] == (
            EXAMPLE_STAGES)
        assert result["index"]["gaps"] == [
            "exchange-bare-exchange", "exchange-leaping-exchange"]
        assert "held - The held exchange (exchange-held-exchange)" in (
            result["index_text"])
        exchange = agent.get_samverkbridge_exchange("exchange-leaping-exchange")
        assert exchange_gaps(exchange, agent.samverkbridge_book()) == (
            "steps from triaged to held, which the exchange sequence "
            "does not allow",)
        assert exchange_green(exchange, agent.samverkbridge_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _EXCHANGE_EVENT_TYPES] == []
        agent.close()
