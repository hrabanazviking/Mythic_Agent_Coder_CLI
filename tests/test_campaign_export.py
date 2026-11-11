"""M-225 Campaign export - pure-layer tests.

TIER: integration

The pure layer is the taxonomist, held as data: one
record per bundle, held whole - the campaign it
answers for, named by campaign id, its title, the
steps it walked in walk order and the evidence
it carries, held by campaign. The question walk is
explicit - named, packed, sealed, checked,
carried, with their legal steps held as data -
and a bundle's standing is derived at call
time: a bundle that opens anywhere but gathered, steps where the sequence does not allow,
carries a bare claim in place of held evidence,
or has not yet gathered carried stands open,
named in its gaps. A bundle stands only for
an active campaign: a bundle naming no held
campaign, or one that is not active, refuses by
name. The bundle's trace - its walked steps
as one line - is derived at call time, and a held
trace record stands current only while it agrees
with the derived trace. The index, panel,
verdict, ledger, trace, order and current
bundle are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
question was actually answered, checked or
carried live. The shipped example book is held
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

from mythic_agent.core.campaign_export import (
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
    BUNDLE_RESOURCE,
    BUNDLE_RULE,
    BUNDLE_SCHEMA,
    BUNDLE_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    BundleRecord,
    IndexBundle,
    CampaignRef,
    NoteRecord,
    BundleBook,
    BundleIndex,
    BundlePanel,
    BundleRegistry,
    BundleVerdict,
    BundleView,
    trace_for_bundle,
    ledger_record,
    book_record,
    build_trace,
    build_book,
    build_bundle,
    build_campaign_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_bundle,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    bundle_for_check,
    bundle_gaps,
    bundle_order,
    bundle_record,
    bundle_green,
    bundles_for_campaign,
    first_note,
    format_book,
    format_bundle,
    format_index,
    format_note,
    format_stage,
    format_panel,
    format_bundle_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    campaign_record,
    load_bundle,
    legal_step,
    load_bundle_file,
    next_stage,
    normalize_stage,
    normalize_claim_kind,
    normalize_campaign_state,
    normalize_stance,
    normalize_view_filter,
    note_for_bundle,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_bundle_args,
    green_bundles,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_bundles,
    validate_book,
    validate_bundle,
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
EXAMPLE_TITLE = "Campaign export at the M-225 slice run"
EXAMPLE_STAGES = ["carried", "carried", "carried"]
EXAMPLE_RUN_IDS = (
    "bundle-held-bundle", "bundle-retried-bundle",
    "bundle-own-bundle", "bundle-bare-bundle",
    "bundle-leaping-bundle")
EXAMPLE_TRACE = "gathered > packed > sealed > checked > carried"


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
        "origin_session": "bundle-test",
    }
    fields.update(overrides)
    return build_campaign_ref(fields)


def _bundle(**overrides):
    fields = {
        "bundle_id": "bundle-test",
        "seq": 1,
        "campaign_id": "campaign-test",
        "title": "A test bundle",
        "stages": ["gathered", "packed", "sealed", "checked", "carried"],
        "claims": [],
        "detail": "A test bundle held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "bundle-test",
    }
    fields.update(overrides)
    return build_bundle(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "bundle-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "bundle_id": "bundle-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "bundle-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "bundle_id": "bundle-test",
        "trace": "gathered > packed > sealed > checked > carried",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "bundle-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(campaigns=None, bundles=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": BUNDLE_SCHEMA,
        "campaign": "M-225",
        "campaign_export": {"title": "A test bundle book"},
        "campaigns": [item.to_record() for item in (
            campaigns if campaigns is not None else [_ref()])],
        "bundle_records": [item.to_record() for item in (
            bundles if bundles is not None else [_bundle()])],
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
    return _book(bundles=[
        _bundle(),
        _bundle(bundle_id="bundle-hidden", seq=2,
               title="A hidden bundle", stages=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_bundle()
    assert book.title == EXAMPLE_TITLE
    assert book.bundle_ids() == EXAMPLE_RUN_IDS
    assert book.campaign_ids() == (
        "campaign-m224-dryrun", "campaign-m225-export",
        "campaign-m226-orders")
    assert [v.view_id for v in book.views] == [
        "view-bundles", "view-carried"]
    assert [m.bundle_id for m in book.notes] == [
        "bundle-held-bundle", "bundle-bare-bundle"]
    assert [a.bundle_id for a in book.traces] == ["bundle-held-bundle"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m224-campaign"
    assert panel.as_of == "2026-11-11"
    assert [row.item_id for row in panel.rows] == list(book.bundle_ids())
    derived = derive_panel(book, "view-bundles")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-bundles").verdict == "held"
    assert derive_verdict(book, "view-bundles").green_shown == 3
    assert derive_verdict(book, "view-carried").verdict == "carried"
    assert derive_verdict(book, "view-carried").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / BUNDLE_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == BUNDLE_SCHEMA
    assert raw["campaign"] == "M-225"
    assert "verdict" not in raw
    assert "bundle_index" not in raw
    assert "ledger" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-225")]
    assert slice_.title == "Campaign export"
    assert slice_.part == 9
    assert "the whole campaign (file, journal, map, evidence) as a portable bundle" in slice_.summary
    assert "a project's memory" in slice_.summary
    assert BUNDLE_SLICE == "M-225"

def test_charter_rows_do_not_name_m225():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-225" not in owners
    method = load_method_charter()
    assert "M-201" in method.source_note
    assert "M-232" in method.source_note
    assert "YRSA_CODING_JUGGERNAUT" in method.source_note

def test_closed_vocabularies():
    assert COMPLETE_WORDS == ("complete", "open")
    assert STAGE_FIELDS == ("stages", "claims")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "complete", "open")
    assert VERDICT_WORDS == ("carried", "held", "blocked")
    assert CAMPAIGN_STATES == ("live", "dormant")
    assert STAGES == ("gathered", "packed", "sealed", "checked", "carried")
    assert HELD_EVIDENCE == ("file_ref", "journal_ref", "map_ref", "evidence_ref", "bundle_ref")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_KINDS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["checked"] == ("gathered", "carried")
    assert TRANSITIONS["carried"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_STAGE == "carried"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_campaign_state("LIVE") == "live"
    assert normalize_stage("SEALED") == "sealed"
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
    assert legal_step("sealed", "checked") is True
    assert legal_step("packed", "carried") is False
    assert legal_step("carried", "gathered") is False
    assert next_stage("gathered") == "packed"
    assert next_stage("sealed") == "checked"
    assert next_stage("checked", failed=True) == "gathered"
    assert next_stage("checked") == "carried"
    assert next_stage("carried") is None
    assert "held as data alone" in BUNDLE_RULE
    assert "bundle sequence" in BUNDLE_RULE
    assert "M-225" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /export")

def test_shipped_book_judged_honestly_as_data():
    book = load_bundle()
    opening = book.bundle_for("bundle-held-bundle")
    assert bundle_green(opening, book) is True
    assert bundle_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Bundle: The held bundle",
        "Campaign: campaign-m224-dryrun",
        "Stage: carried",
        "Claims: file_ref")
    asking = book.bundle_for("bundle-bare-bundle")
    assert bundle_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert bundle_green(asking, book) is False
    skipping = book.bundle_for("bundle-leaping-bundle")
    assert bundle_gaps(skipping, book) == (
        "steps from packed to carried, which the bundle sequence "
        "does not allow",)
    assert [g.bundle_id for g in green_bundles(book)] == [
        "bundle-held-bundle", "bundle-retried-bundle", "bundle-own-bundle"]
    index = derive_index(book)
    assert [e.stage for e in index.bundles] == EXAMPLE_STAGES
    assert index.gaps == ("bundle-bare-bundle", "bundle-leaping-bundle")
    assert bundle_for_check(book, EXAMPLE_STAGE).bundle_id == (
        "bundle-held-bundle")
    assert bundle_for_check(book, "triple bundle") is None
    assert transition_breaks(book) == (
        "bundle-leaping-bundle: packed > carried",)
    assert [g.bundle_id for g in bundle_order(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "bundle-held-bundle") == EXAMPLE_TRACE
    assert trace_current(book, "bundle-held-bundle") is True
    assert trace_current(book, "bundle-retried-bundle") is False
    assert trace_for_bundle(
        book, "bundle-held-bundle").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_bundle(
        book, "bundle-held-bundle", "note").note_id == (
            "note-note-first")
    assert note_for_bundle(book, "bundle-nope") is None
    assert current_bundle(book).bundle_id == "bundle-bare-bundle"
    ledger = ledger_record(book)
    assert ledger["standings"] == [
        {"standing": "complete", "bundle_records": 3},
        {"standing": "open", "bundle_records": 2}]
    assert ledger["total"] == 5
    assert ledger["current_bundle"] == "bundle-bare-bundle"
    assert ledger["traces"] == [
        {"bundle_id": "bundle-held-bundle", "trace": "current"},
        {"bundle_id": "bundle-retried-bundle", "trace": "unheld"},
        {"bundle_id": "bundle-own-bundle", "trace": "unheld"},
        {"bundle_id": "bundle-bare-bundle", "trace": "unheld"},
        {"bundle_id": "bundle-leaping-bundle", "trace": "unheld"}]
    assert ledger["breaks"] == ["bundle-leaping-bundle: packed > carried"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 224
    assert citizen["next_slice"] == "M-225"
    assert citizen["m225_title"] == "Campaign export"
    assert citizen["m225_part"] == 9
    assert citizen["m225_status"] == "queued"

def test_bundle_record_round_trips():
    bundle = _bundle()
    assert validate_bundle(bundle) is bundle
    rebuilt = build_bundle(bundle.to_record())
    assert rebuilt == bundle
    assert rebuilt.item_id == "bundle-test"
    assert rebuilt.stage == "carried"
    record = bundle_record(bundle)
    assert record["type"] == "bundle_bundle"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert campaign_record(ref)["type"] == "bundle_run"
    assert campaign_record(ref)["state"] == "live"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _bundle(stages=[])
    assert bundle_gaps(silent) == (
        "has passed through no step: the bundle has not started",)
    assert bundle_green(silent) is False
    walking = _bundle(stages=["gathered", "packed"])
    assert bundle_gaps(walking) == (
        "has not reached carried: the bundle stands at packed",)
    assert walking.stage == "packed"
    sideways = _bundle(stages=["packed", "sealed", "checked", "carried"])
    assert bundle_gaps(sideways) == (
        "opens at packed, not at gathered: the bundle opens "
        "with the reflection",)
    repaired = _bundle(stages=["gathered", "packed", "sealed", "checked", "gathered", "packed", "sealed", "checked", "carried"])
    assert bundle_gaps(repaired) == ()
    assert bundle_green(repaired) is True
    with pytest.raises(ValueError):
        _bundle(stages=[42])
    with pytest.raises(ValueError):
        _bundle(stages="inspect as a bare string")
    with pytest.raises(ValueError):
        _bundle(stages=["gathered", "polish"])
    with pytest.raises(ValueError):
        _bundle(claims=["weather"])
    with pytest.raises(ValueError):
        _bundle(claims="file_ref")
    none_bundle = _bundle(stages=None, claims=None)
    assert none_bundle.stages == ()
    assert none_bundle.claims == ()

def test_bundle_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "bundles", "coverage", "current_bundle",
                "ledger", "order"):
        fields = _bundle().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_bundle(fields)
    fields = _bundle().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_bundle(fields)


def test_bundle_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _bundle().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_bundle(fields)


def test_bundle_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _bundle(title="")
    with pytest.raises(ValueError):
        _bundle(campaign_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "gathered > packed > sealed > checked > carried"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_bundles_own_fields():
    bundle = _bundle(claims=["file_ref"])
    assert plain_lines(bundle) == (
        "Bundle: A test bundle",
        "Campaign: campaign-test",
        "Stage: carried",
        "Claims: file_ref")
    segment = segment_of(bundle)
    assert segment.startswith("bundle-test: A test bundle")
    assert "stage: 'carried'" in segment
    assert "gaps: none" in segment
    assert plain_words(bundle).startswith(
        "A test bundle - from campaign-test")

def test_red_bundles_stand_named_in_their_gaps():
    asking = _bundle(claims=["feeling", "file_ref", "summary"])
    assert bundle_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert bundle_green(asking) is False
    skipping = _bundle(stages=["gathered", "packed", "carried"])
    assert bundle_gaps(skipping) == (
        "steps from packed to carried, which the bundle sequence "
        "does not allow",)
    book = _book(bundles=[
        _bundle(),
        _bundle(bundle_id="bundle-skipping", seq=2,
             stages=["gathered", "packed", "carried"]),
    ])
    assert transition_breaks(book) == (
        "bundle-skipping: packed > carried",)
    assert current_bundle(book).bundle_id == "bundle-skipping"
    assert [g.bundle_id for g in bundle_order(book)] == [
        "bundle-test", "bundle-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "bundle_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "bundle_note"
    assert record["bundle_id"] == "bundle-test"
    assert view_plain_words(view) == "View view-test: shows all bundles."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_bundles_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.stage for e in index.bundles] == ["carried"]
    assert index.bundles[0] == IndexBundle(
        stage="carried",
        bundle_id="bundle-test", title="A test bundle")
    assert index.gaps == ("bundle-hidden",)
    record = index_record(book)
    assert record["type"] == "bundle_index"
    assert record["gaps"] == ["bundle-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "bundle_book"

def test_check_target_reaches_its_bundle_and_an_unheld_target_reaches_nothing():
    book = load_bundle()
    assert bundle_for_check(book, "carried").bundle_id == (
        "bundle-held-bundle")
    assert bundle_for_check(book, "") is None
    assert bundle_for_check(book, None) is None
    assert bundle_for_check(book, "not held at all") is None
    text = format_stage(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_bundle()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Bundle note note bundle-held-bundle" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").bundle_id == "bundle-test"
    assert note_for_bundle(book, "bundle-test").note_id == "note-test"
    assert note_for_bundle(book, "bundle-test", "praise") is None
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
    row = build_row(None, _bundle(), book)
    assert row.standing == "complete"
    assert validate_row(row, _bundle(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_bundles():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "bundle_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "carried"
    empty_book = _book(bundles=[_bundle(stages=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(BundleVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_readings():
    book = load_bundle()
    assert [g.bundle_id for g in shown_bundles(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.bundle_id for g in shown_bundles(book, "view-carried")] == [
        "bundle-held-bundle", "bundle-retried-bundle", "bundle-own-bundle"]
    assert [g.bundle_id for g in bundles_for_campaign(
        book, "campaign-m225-export")] == [
            "bundle-own-bundle", "bundle-bare-bundle",
            "bundle-leaping-bundle"]
    assert bundles_for_campaign(book, "campaign-nope") == ()
    assert current_bundle(_mixed_book()).bundle_id == "bundle-hidden"
    assert current_bundle(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "bundle-test") == (
        "gathered > packed > sealed > checked > carried")
    assert trace_current(stale, "bundle-test") is False
    assert ledger_record(stale)["traces"] == [
        {"bundle_id": "bundle-test", "trace": "stale"}]

def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(bundles=[_bundle(), _bundle(seq=2)])
    with pytest.raises(ValueError):
        _book(bundles=[_bundle(), _bundle(bundle_id="bundle-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(bundles=[_bundle(campaign_id="campaign-nope")])
    with pytest.raises(ValueError):
        _book(campaigns=[_ref(), _ref(
            campaign_id="campaign-cold", seq=2, state="dormant")],
            bundles=[_bundle(campaign_id="campaign-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(campaign_id="campaign-nope")])
    fields = {
        "schema": BUNDLE_SCHEMA, "campaign": "M-225",
        "campaign_export": {"title": "A sealed book"},
        "campaigns": [_ref().to_record()],
        "bundle_records": [_bundle().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "carried"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_bundle"] = "bundle-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_bundle")
    fields["trace"] = "bundle-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / BUNDLE_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "campaign_export.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_bundle_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.bundle_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = BundleRegistry()
    assert registry.title() is None
    registry.register_campaign_ref(_ref())
    registry.register_bundle(_bundle())
    registry.register_view(_view())
    assert [g.bundle_id for g in registry.list_bundles()] == ["bundle-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_bundle("bundle-test").title == "A test bundle"
    assert registry.get_slice("campaign-test").state == "live"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("bundle-test").bundle_id == "bundle-test"
    with pytest.raises(ValueError):
        registry.register_bundle(_bundle(seq=9))
    with pytest.raises(ValueError):
        registry.register_bundle(_bundle(bundle_id="bundle-two"))
    with pytest.raises(KeyError):
        registry.get_bundle("bundle-nope")
    assert registry.book().title == "An unheld bundle book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = BundleRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test bundle book"
    assert registry.title() == "A test bundle book"
    assert len(registry.list_bundles()) == 2
    other = BundleRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    bundle = _bundle()
    assert "A test bundle" in plain_words(bundle)
    assert panel_plain_words(_mixed_book()).startswith(
        "The bundle book holds 2 bundles")
    assert verdict_plain_words(_mixed_book()) == (
        "The bundles stand held: 1 of 2 shown bundles stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green bundles; red, "
        "named in its gaps: bundle-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_bundle(bundle)
    assert "Bundle: A test bundle" in text
    assert "stands complete" in text
    text = format_bundle(_bundle(stages=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The Bundle Gate (M-225) - A test bundle book" in book_text
    assert "bundle-hidden" in format_book(_mixed_book(), "campaign-test")
    assert "Bundle panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "carried - A test bundle (bundle-test)" in index_text
    assert "bundle-hidden" in index_text
    screen = format_bundle_screen()
    assert "The Bundle Gate (M-225)" in screen
    assert "bundle-bare-bundle" in screen

def test_parse_args_well_and_loader_targets():
    assert parse_bundle_args("") == ("show", None)
    assert parse_bundle_args(None) == ("show", None)
    assert parse_bundle_args("show") == ("show", None)
    assert parse_bundle_args("bundle bundle-test") == (
        "bundle", "bundle-test")
    assert parse_bundle_args("stage carried") == (
        "stage", "carried")
    assert parse_bundle_args("campaign campaign-test") == (
        "campaign", "campaign-test")
    assert parse_bundle_args("view view-test") == ("view", "view-test")
    assert parse_bundle_args("note note-test") == ("note", "note-test")
    assert parse_bundle_args("index") == ("index", None)
    assert parse_bundle_args("panel") == ("panel", None)
    assert parse_bundle_args("verdict") == ("verdict", None)
    for bad in ("dance", "bundle", "stage", "campaign", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_bundle_args(bad)
    ledger = ledger_record()
    assert ledger["type"] == "bundle_well"
    assert ledger["total"] == 5
    assert ledger["current_bundle"] == "bundle-bare-bundle"
    book = load_bundle({
        "schema": BUNDLE_SCHEMA, "campaign": "M-225",
        "campaign_export": {"title": "A sealed book"},
        "campaigns": [_ref().to_record()],
        "bundle_records": [_bundle().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, BundleBook)
    assert book.title == "A sealed book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_bundle({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_bundle({"campaign": "M-999"})
    built = build_bundle(
        bundle_id="bundle-kw", seq=3, campaign_id="campaign-test",
        title="Kw Bundle", stages=["gathered", "packed", "sealed", "checked", "carried"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="bundle-test")
    assert built.bundle_id == "bundle-kw"
    assert bundle_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-225 agent layer: the agent holds a bundle
# book for the session, bundles and views are
# published as session news through the
# checkpoint target (ledger first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held bundles, the ledger is derived from
# the held bundles' completeness, the roadmap standing
# is checked from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no campaign. This layer bundles
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session ledger news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_BUNDLE_EVENT_TYPES = (
    "bundle_bundle", "bundle_run", "bundle_view",
    "bundle_panel", "bundle_verdict")


def _bundle_events(store, session_id, campaign):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == campaign]


def _write_export_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / BUNDLE_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "campaign_export.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestBundleAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.export_status()
        assert status["bundle_records"] == []
        assert status["campaigns"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["export_book"]["title"] == EXAMPLE_TITLE
        assert len(status["export_book"]["campaigns"]) == 3
        assert len(status["export_book"]["bundle_records"]) == 5
        assert len(status["export_book"]["views"]) == 2
        assert len(status["export_book"]["notes"]) == 2
        assert len(status["export_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-m224-campaign"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["stage"] for e in status["index"]["bundles"]] == (
            EXAMPLE_STAGES)
        assert status["index"]["gaps"] == [
            "bundle-bare-bundle", "bundle-leaping-bundle"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["ledger"]["total"] == 5
        assert status["ledger"]["current_bundle"] == "bundle-bare-bundle"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 224
        assert status["roadmap"]["next_slice"] == "M-225"
        assert status["roadmap"]["m225_title"] == "Campaign export"
        assert "held as data alone" in status["rule"]
        assert "bundle-bare-bundle" in status["plain_words"]
        assert "The Bundle Gate (M-225)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._export_registry()
        assert agent._export_registry() is first
        assert agent._export_store is first
        for name in ("export_book", "export_status", "export_panel",
                     "export_verdict", "export_index", "report_export"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_export_registry", "export_book", "export_status",
            "get_export_bundle", "get_export_view", "get_export_note",
            "bundles_for_campaign", "bundles_green",
            "export_panel", "export_verdict", "export_index",
            "register_export_bundle", "register_export_view",
            "view_export", "register_export_book",
            "record_export_book", "report_export",
            "_publish_export_record", "_export_screen",
            "_export_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.export_status()
        assert agent.get_export_bundle(
            "bundle-held-bundle").title == "The held bundle"
        assert agent.get_export_view(
            "view-bundles").view_filter == "all"
        assert agent.get_export_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.bundle_id for d in agent.bundles_for_campaign(
            "campaign-m225-export")] == [
            "bundle-own-bundle", "bundle-bare-bundle",
            "bundle-leaping-bundle"]
        assert [d.bundle_id for d in agent.bundles_green()] == [
            "bundle-held-bundle", "bundle-retried-bundle", "bundle-own-bundle"]
        agent.export_panel()
        agent.export_verdict()
        agent.export_index()
        agent.report_export()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _BUNDLE_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_export_bundle("bundle-nope")
        with pytest.raises(KeyError):
            agent.get_export_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_export_note("note-nope")
        with pytest.raises(ValueError):
            agent.bundles_for_campaign("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_export_bundle(_bundle())
        status = agent.export_status()
        assert [d["bundle_id"] for d in status["bundle_records"]] == ["bundle-test"]
        assert status["book"]["title"] == "An unheld bundle book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["stage"] for e in status["index"]["bundles"]] == [
            "carried"]
        assert status["first_note"] is None
        assert "bundle-test" in status["screen"]
    def test_held_bundle_never_falls_back_to_the_example(
            self, agent):
        agent.register_export_bundle(_bundle())
        with pytest.raises(KeyError):
            agent.get_export_bundle("bundle-held-bundle")
        with pytest.raises(KeyError):
            agent.get_export_view("view-bundles")
        with pytest.raises(KeyError):
            agent.get_export_note("note-note-first")
        bundle = agent.get_export_bundle("bundle-test")
        assert bundle.title == "A test bundle"
        assert agent.export_book().title == (
            "An unheld bundle book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_export_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.bundle_id == "bundle-held-bundle"
        status = agent.export_status()
        assert status["index"]["gaps"] == [
            "bundle-bare-bundle", "bundle-leaping-bundle"]
        assert status["first_note"]["bundle_id"] == (
            "bundle-held-bundle")
        assert status["first_note"]["stance"] == "note"

class TestBundleAgentHolding:
    def test_register_bundle_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_export_bundle(_bundle())
        assert result["bundle"]["bundle_id"] == "bundle-test"
        assert result["record_news"]["type"] == "bundle_bundle"
        assert "bundle-test" in result["screen"]
        events = _bundle_events(store, session_id, "bundle_bundle")
        assert len(events) == 1
        agent.close()

    def test_duplicate_bundle_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_export_bundle(_bundle())
        with pytest.raises(ValueError):
            agent.register_export_bundle(_bundle(seq=9))
        with pytest.raises(ValueError):
            agent.register_export_bundle(_bundle(bundle_id="bundle-two"))
        events = _bundle_events(store, session_id, "bundle_bundle")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_export_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_bundle_events(
            store, session_id, "bundle_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_export_bundle(_bundle())
        result = agent.view_export("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "bundle_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "carried"
        assert len(_bundle_events(
            store, session_id, "bundle_view")) == 1
        assert len(_bundle_events(
            store, session_id, "bundle_panel")) == 1
        assert len(_bundle_events(
            store, session_id, "bundle_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_export_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "bundle_run", "bundle_bundle", "bundle_view"]
        assert len(_bundle_events(
            store, session_id, "bundle_bundle")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_export_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "bundle_panel"
        assert result["index_record"]["gaps"] == [
            "bundle-bare-bundle", "bundle-leaping-bundle"]
        with pytest.raises(ValueError):
            agent.record_export_book()
        assert len(_bundle_events(
            store, session_id, "bundle_run")) == 3
        assert len(_bundle_events(
            store, session_id, "bundle_bundle")) == 5
        assert len(_bundle_events(
            store, session_id, "bundle_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_export_book_file(tmp_path)
        book = load_bundle_file(path)
        result = agent.record_export_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_runrt_renders_example_then_held_book_only(self, agent):
        bundle = agent.report_export()
        assert bundle["book"]["title"] == EXAMPLE_TITLE
        assert bundle["verdict"]["verdict"] == "held"
        assert bundle["index"]["gaps"] == [
            "bundle-bare-bundle", "bundle-leaping-bundle"]
        assert "bundle-held-bundle" in bundle["book_text"]
        assert "carried - The held bundle (bundle-held-bundle)" in bundle["index_text"]
        agent.register_export_bundle(_bundle())
        bundle = agent.report_export()
        assert bundle["book"]["title"] == "An unheld bundle book"
        assert bundle["panel"] is None
        assert bundle["verdict"] is None

class TestBundleTerminalHeading:
    def test_show_bundle_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/export")
        assert "The Bundle Gate (M-225)" in text
        _, _, text = _slash(agent, "/export bundle bundle-held-bundle")
        assert "Bundle: The held bundle" in text
        _, _, text = _slash(
            agent, "/export stage carried")
        assert "Bundle: The held bundle" in text
        _, _, text = _slash(agent, "/export stage triple bundle")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/export campaign campaign-m225-export")
        assert "bundle-bare-bundle" in text
        assert "bundle-held-bundle" not in text
        _, _, text = _slash(agent, "/export view view-bundles")
        assert "filter all" in text
        _, _, text = _slash(agent, "/export note note-note-first")
        assert "Bundle note note bundle-held-bundle" in text
        _, _, text = _slash(agent, "/export index")
        assert "Bundle index" in text
        assert "bundle-bare-bundle" in text
        _, _, text = _slash(agent, "/export panel")
        assert "Bundle panel under view view-bundles" in text
        _, _, text = _slash(agent, "/export verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/export [show|bundle <bundle-id>"
                "|stage <stage>|campaign <campaign-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/export dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/export bundle bundle-nope")
        assert "no bundle named" in text
@pytest.fixture()
def bundle_handler(agent, monkeypatch):
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


def _bundle_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestBundleCommand:
    def test_show_is_default(self, bundle_handler, agent):
        bundle_handler._handle_export("")
        assert "The Bundle Gate (M-225)" in (
            _bundle_published_text(bundle_handler))

    def test_bundle_check_slice_view_note_index_panel_verdict(
            self, bundle_handler, agent):
        bundle_handler._handle_export("bundle bundle-held-bundle")
        assert "Bundle: The held bundle" in _bundle_published_text(
            bundle_handler)
        bundle_handler._handle_export(
            "stage carried")
        assert "Bundle: The held bundle" in _bundle_published_text(
            bundle_handler)
        bundle_handler._handle_export("campaign campaign-m225-export")
        assert "bundle-bare-bundle" in _bundle_published_text(
            bundle_handler)
        bundle_handler._handle_export("view view-bundles")
        assert "filter all" in _bundle_published_text(bundle_handler)
        bundle_handler._handle_export("note note-note-first")
        assert "Bundle note note bundle-held-bundle" in (
            _bundle_published_text(bundle_handler))
        bundle_handler._handle_export("index")
        assert "Bundle index" in _bundle_published_text(bundle_handler)
        bundle_handler._handle_export("panel")
        assert "Bundle panel under view" in _bundle_published_text(
            bundle_handler)
        bundle_handler._handle_export("verdict")
        assert "held" in _bundle_published_text(bundle_handler)
    def test_bad_grammar_is_published(
            self, bundle_handler, agent):
        bundle_handler._handle_export("dance party")
        assert USAGE in _bundle_published_text(bundle_handler)
        bundle_handler._handle_export("bundle bundle-nope")
        assert "no bundle named" in _bundle_published_text(
            bundle_handler)


class TestChatScreenRoutingBundle:
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
        screen.handle_command("/export panel", _FakeLog())
        assert calls == [("/export", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/export[/green] - show the Bundle gate (M-225)" in (
            text)
        assert ('"/export": "Usage: /export | '
                '/export bundle <bundle-id>') in text

class TestBundleDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.export_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-bundles"
        verdict = agent.export_verdict()
        assert verdict.verdict == "held"
        found = agent.export_verdict("view-carried")
        assert found.verdict == "carried"
        assert found.green_shown == 3
        agent.register_export_bundle(_bundle())
        with pytest.raises(ValueError):
            agent.export_panel()
        with pytest.raises(ValueError):
            agent.export_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_export_bundle(_bundle(stages=[]))
        result = agent.view_export("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.export_index()
        assert [e["stage"] for e in result["index"]["bundles"]] == (
            EXAMPLE_STAGES)
        assert result["index"]["gaps"] == [
            "bundle-bare-bundle", "bundle-leaping-bundle"]
        assert "carried - The held bundle (bundle-held-bundle)" in (
            result["index_text"])
        bundle = agent.get_export_bundle("bundle-leaping-bundle")
        assert bundle_gaps(bundle, agent.export_book()) == (
            "steps from packed to carried, which the bundle sequence "
            "does not allow",)
        assert bundle_green(bundle, agent.export_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _BUNDLE_EVENT_TYPES] == []
        agent.close()
