"""M-216 Campaigns - pure-layer tests.

TIER: integration

The pure layer is the hallkeeper, held as data: one
record per campaign, held whole - the slice it
answers for, named by slice id, its title, the
steps it walked in walk order and the evidence
it carries, held by kind. The question walk is
explicit - named, boarded, kept, reported,
glanced, with their legal steps held as data -
and a campaign's standing is derived at call
time: a campaign that opens anywhere but gathered, steps where the sequence does not allow,
carries a bare claim in place of held evidence,
or has not yet reached glanced stands open,
named in its gaps. A campaign stands only for
an active slice: a campaign naming no held
slice, or one that is not active, refuses by
name. The campaign's trace - its walked steps
as one line - is derived at call time, and a held
trace record stands current only while it agrees
with the derived trace. The index, panel,
verdict, board, trace, order and current
campaign are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
question was actually answered, reported or
glanced live. The shipped example book is held
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

from mythic_agent.core.multi_campaign_hall import (
    EXAMPLE_CHECK,
    BARE_CLAIMS,
    HELD_EVIDENCE,
    INDEX_ACTION,
    CHECKS,
    CLAIM_KINDS,
    TRANSITIONS,
    REPO_STATES,
    CHECK_FIELDS,
    PLAIN_EXPLANATION,
    CAMPAIGN_RESOURCE,
    CAMPAIGN_RULE,
    CAMPAIGN_SCHEMA,
    CAMPAIGN_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    CampaignRecord,
    IndexEntry,
    RepoRef,
    NoteRecord,
    CampaignBook,
    CampaignIndex,
    CampaignPanel,
    CampaignRegistry,
    CampaignVerdict,
    CampaignView,
    trace_for_campaign,
    board_record,
    book_record,
    build_trace,
    build_book,
    build_campaign,
    build_repo_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_campaign,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    campaign_for_check,
    campaign_gaps,
    campaign_order,
    campaign_record,
    campaign_green,
    campaigns_for_repo,
    first_note,
    format_book,
    format_campaign,
    format_index,
    format_note,
    format_check,
    format_panel,
    format_campaign_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    repo_record,
    load_campaign,
    legal_step,
    load_campaign_file,
    next_check,
    normalize_check,
    normalize_claim_kind,
    normalize_repo_state,
    normalize_stance,
    normalize_view_filter,
    note_for_campaign,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_campaign_args,
    green_campaigns,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_campaigns,
    validate_book,
    validate_campaign,
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
EXAMPLE_TITLE = "Multi-campaign hall at the M-215 slice boundary"
EXAMPLE_CHECKS = ["glanced", "glanced", "glanced"]
EXAMPLE_RUN_IDS = (
    "campaign-held-campaign", "campaign-remeasured-campaign",
    "campaign-own-campaign", "campaign-bare-campaign",
    "campaign-leaping-campaign")
EXAMPLE_TRACE = "gathered > boarded > kept > reported > glanced"


def _ref(**overrides):
    fields = {
        "repo_id": "slice-test",
        "seq": 1,
        "title": "A test slice",
        "state": "live",
        "detail": "A test slice reference held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "campaign-test",
    }
    fields.update(overrides)
    return build_repo_ref(fields)


def _campaign(**overrides):
    fields = {
        "campaign_id": "campaign-test",
        "seq": 1,
        "repo_id": "slice-test",
        "title": "A test campaign",
        "checks": ["gathered", "boarded", "kept", "reported", "glanced"],
        "claims": [],
        "detail": "A test campaign held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "campaign-test",
    }
    fields.update(overrides)
    return build_campaign(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "campaign-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "campaign_id": "campaign-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "campaign-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "campaign_id": "campaign-test",
        "trace": "gathered > boarded > kept > reported > glanced",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "campaign-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(slices=None, campaigns=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": CAMPAIGN_SCHEMA,
        "slice": "M-216",
        "multi_campaign_hall": {"title": "A test campaign book"},
        "repos": [item.to_record() for item in (
            slices if slices is not None else [_ref()])],
        "campaign_records": [item.to_record() for item in (
            campaigns if campaigns is not None else [_campaign()])],
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
    return _book(campaigns=[
        _campaign(),
        _campaign(campaign_id="campaign-hidden", seq=2,
               title="A hidden campaign", checks=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_campaign()
    assert book.title == EXAMPLE_TITLE
    assert book.campaign_ids() == EXAMPLE_RUN_IDS
    assert book.repo_ids() == (
        "repo-m215-estimate", "slice-m216-campaign",
        "repo-m217-templates")
    assert [v.view_id for v in book.views] == [
        "view-campaigns", "view-glanced"]
    assert [m.campaign_id for m in book.notes] == [
        "campaign-held-campaign", "campaign-bare-campaign"]
    assert [a.campaign_id for a in book.traces] == ["campaign-held-campaign"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m215-boundary"
    assert panel.as_of == "2026-11-11"
    assert [row.item_id for row in panel.rows] == list(book.campaign_ids())
    derived = derive_panel(book, "view-campaigns")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-campaigns").verdict == "held"
    assert derive_verdict(book, "view-campaigns").green_shown == 3
    assert derive_verdict(book, "view-glanced").verdict == "glanced"
    assert derive_verdict(book, "view-glanced").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / CAMPAIGN_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == CAMPAIGN_SCHEMA
    assert raw["slice"] == "M-216"
    assert "verdict" not in raw
    assert "campaign_index" not in raw
    assert "board" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-216")]
    assert slice_.title == "Multi-campaign hall"
    assert slice_.part == 9
    assert "several campaigns across repos with one board" in slice_.summary
    assert "keepers per campaign" in slice_.summary
    assert "the human sees the whole forge at a glance" in slice_.summary
    assert CAMPAIGN_SLICE == "M-216"

def test_charter_rows_do_not_name_m216():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-216" not in owners
    method = load_method_charter()
    assert "M-201" in method.source_note
    assert "M-232" in method.source_note
    assert "YRSA_CODING_JUGGERNAUT" in method.source_note

def test_closed_vocabularies():
    assert COMPLETE_WORDS == ("complete", "open")
    assert CHECK_FIELDS == ("checks", "claims")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "complete", "open")
    assert VERDICT_WORDS == ("glanced", "held", "blocked")
    assert REPO_STATES == ("live", "dormant")
    assert CHECKS == ("gathered", "boarded", "kept", "reported", "glanced")
    assert HELD_EVIDENCE == ("repo_ref", "board_ref", "keeper_record", "glance_ref")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_KINDS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["reported"] == ("gathered", "glanced")
    assert TRANSITIONS["glanced"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_CHECK == "glanced"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_repo_state("LIVE") == "live"
    assert normalize_check("KEPT") == "kept"
    assert normalize_claim_kind("FEELING") == "feeling"
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    with pytest.raises(ValueError):
        normalize_repo_state("blessed")
    with pytest.raises(ValueError):
        normalize_check("polish")
    with pytest.raises(ValueError):
        normalize_claim_kind("weather")
    assert legal_step("kept", "reported") is True
    assert legal_step("boarded", "glanced") is False
    assert legal_step("glanced", "gathered") is False
    assert next_check("gathered") == "boarded"
    assert next_check("kept") == "reported"
    assert next_check("reported", failed=True) == "gathered"
    assert next_check("reported") == "glanced"
    assert next_check("glanced") is None
    assert "held as data alone" in CAMPAIGN_RULE
    assert "campaign sequence" in CAMPAIGN_RULE
    assert "M-216" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /hall")

def test_shipped_book_judged_honestly_as_data():
    book = load_campaign()
    opening = book.campaign_for("campaign-held-campaign")
    assert campaign_green(opening, book) is True
    assert campaign_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Campaign: The held campaign",
        "Repo: repo-m215-estimate",
        "Check: glanced",
        "Claims: repo_ref")
    asking = book.campaign_for("campaign-bare-campaign")
    assert campaign_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert campaign_green(asking, book) is False
    skipping = book.campaign_for("campaign-leaping-campaign")
    assert campaign_gaps(skipping, book) == (
        "steps from boarded to glanced, which the campaign sequence "
        "does not allow",)
    assert [g.campaign_id for g in green_campaigns(book)] == [
        "campaign-held-campaign", "campaign-remeasured-campaign", "campaign-own-campaign"]
    index = derive_index(book)
    assert [e.check for e in index.entries] == EXAMPLE_CHECKS
    assert index.gaps == ("campaign-bare-campaign", "campaign-leaping-campaign")
    assert campaign_for_check(book, EXAMPLE_CHECK).campaign_id == (
        "campaign-held-campaign")
    assert campaign_for_check(book, "triple resume") is None
    assert transition_breaks(book) == (
        "campaign-leaping-campaign: boarded > glanced",)
    assert [g.campaign_id for g in campaign_order(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "campaign-held-campaign") == EXAMPLE_TRACE
    assert trace_current(book, "campaign-held-campaign") is True
    assert trace_current(book, "campaign-remeasured-campaign") is False
    assert trace_for_campaign(
        book, "campaign-held-campaign").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_campaign(
        book, "campaign-held-campaign", "note").note_id == (
            "note-note-first")
    assert note_for_campaign(book, "campaign-nope") is None
    assert current_campaign(book).campaign_id == "campaign-bare-campaign"
    board = board_record(book)
    assert board["standings"] == [
        {"standing": "complete", "campaign_records": 3},
        {"standing": "open", "campaign_records": 2}]
    assert board["total"] == 5
    assert board["current_campaign"] == "campaign-bare-campaign"
    assert board["traces"] == [
        {"campaign_id": "campaign-held-campaign", "trace": "current"},
        {"campaign_id": "campaign-remeasured-campaign", "trace": "unheld"},
        {"campaign_id": "campaign-own-campaign", "trace": "unheld"},
        {"campaign_id": "campaign-bare-campaign", "trace": "unheld"},
        {"campaign_id": "campaign-leaping-campaign", "trace": "unheld"}]
    assert board["breaks"] == ["campaign-leaping-campaign: boarded > glanced"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 262
    assert citizen["next_slice"] == "M-263"
    assert citizen["m216_title"] == "Multi-campaign hall"
    assert citizen["m216_part"] == 9
    assert citizen["m216_status"] == "done"

def test_campaign_record_round_trips():
    campaign = _campaign()
    assert validate_campaign(campaign) is campaign
    rebuilt = build_campaign(campaign.to_record())
    assert rebuilt == campaign
    assert rebuilt.item_id == "campaign-test"
    assert rebuilt.check == "glanced"
    record = campaign_record(campaign)
    assert record["type"] == "campaign_campaign"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert repo_record(ref)["type"] == "campaign_slice"
    assert repo_record(ref)["state"] == "live"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _campaign(checks=[])
    assert campaign_gaps(silent) == (
        "has passed through no step: the campaign has not started",)
    assert campaign_green(silent) is False
    walking = _campaign(checks=["gathered", "boarded"])
    assert campaign_gaps(walking) == (
        "has not reached glanced: the campaign stands at boarded",)
    assert walking.check == "boarded"
    sideways = _campaign(checks=["boarded", "kept", "reported", "glanced"])
    assert campaign_gaps(sideways) == (
        "opens at boarded, not at gathered: the campaign opens "
        "with the reflection",)
    repaired = _campaign(checks=["gathered", "boarded", "kept", "reported", "gathered", "boarded", "kept", "reported", "glanced"])
    assert campaign_gaps(repaired) == ()
    assert campaign_green(repaired) is True
    with pytest.raises(ValueError):
        _campaign(checks=[42])
    with pytest.raises(ValueError):
        _campaign(checks="inspect as a bare string")
    with pytest.raises(ValueError):
        _campaign(checks=["gathered", "polish"])
    with pytest.raises(ValueError):
        _campaign(claims=["weather"])
    with pytest.raises(ValueError):
        _campaign(claims="repo_ref")
    none_campaign = _campaign(checks=None, claims=None)
    assert none_campaign.checks == ()
    assert none_campaign.claims == ()

def test_campaign_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "entries", "coverage", "current_campaign",
                "board", "order"):
        fields = _campaign().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_campaign(fields)
    fields = _campaign().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_campaign(fields)


def test_campaign_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _campaign().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_campaign(fields)


def test_campaign_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _campaign(title="")
    with pytest.raises(ValueError):
        _campaign(repo_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "gathered > boarded > kept > reported > glanced"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_campaigns_own_fields():
    campaign = _campaign(claims=["repo_ref"])
    assert plain_lines(campaign) == (
        "Campaign: A test campaign",
        "Repo: slice-test",
        "Check: glanced",
        "Claims: repo_ref")
    segment = segment_of(campaign)
    assert segment.startswith("campaign-test: A test campaign")
    assert "check: 'glanced'" in segment
    assert "gaps: none" in segment
    assert plain_words(campaign).startswith(
        "A test campaign - from slice-test")

def test_red_campaigns_stand_named_in_their_gaps():
    asking = _campaign(claims=["feeling", "repo_ref", "summary"])
    assert campaign_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert campaign_green(asking) is False
    skipping = _campaign(checks=["gathered", "boarded", "glanced"])
    assert campaign_gaps(skipping) == (
        "steps from boarded to glanced, which the campaign sequence "
        "does not allow",)
    book = _book(campaigns=[
        _campaign(),
        _campaign(campaign_id="campaign-skipping", seq=2,
             checks=["gathered", "boarded", "glanced"]),
    ])
    assert transition_breaks(book) == (
        "campaign-skipping: boarded > glanced",)
    assert current_campaign(book).campaign_id == "campaign-skipping"
    assert [g.campaign_id for g in campaign_order(book)] == [
        "campaign-test", "campaign-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "campaign_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "campaign_note"
    assert record["campaign_id"] == "campaign-test"
    assert view_plain_words(view) == "View view-test: shows all campaigns."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_campaigns_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.check for e in index.entries] == ["glanced"]
    assert index.entries[0] == IndexEntry(
        check="glanced",
        campaign_id="campaign-test", title="A test campaign")
    assert index.gaps == ("campaign-hidden",)
    record = index_record(book)
    assert record["type"] == "campaign_index"
    assert record["gaps"] == ["campaign-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "campaign_book"

def test_check_target_reaches_its_campaign_and_an_unheld_target_reaches_nothing():
    book = load_campaign()
    assert campaign_for_check(book, "glanced").campaign_id == (
        "campaign-held-campaign")
    assert campaign_for_check(book, "") is None
    assert campaign_for_check(book, None) is None
    assert campaign_for_check(book, "not held at all") is None
    text = format_check(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_campaign()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Campaign note note campaign-held-campaign" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").campaign_id == "campaign-test"
    assert note_for_campaign(book, "campaign-test").note_id == "note-test"
    assert note_for_campaign(book, "campaign-test", "praise") is None
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
    row = build_row(None, _campaign(), book)
    assert row.standing == "complete"
    assert validate_row(row, _campaign(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_campaigns():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "campaign_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "glanced"
    empty_book = _book(campaigns=[_campaign(checks=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(CampaignVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_readings():
    book = load_campaign()
    assert [g.campaign_id for g in shown_campaigns(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.campaign_id for g in shown_campaigns(book, "view-glanced")] == [
        "campaign-held-campaign", "campaign-remeasured-campaign", "campaign-own-campaign"]
    assert [g.campaign_id for g in campaigns_for_repo(
        book, "slice-m216-campaign")] == [
            "campaign-own-campaign", "campaign-bare-campaign",
            "campaign-leaping-campaign"]
    assert campaigns_for_repo(book, "slice-nope") == ()
    assert current_campaign(_mixed_book()).campaign_id == "campaign-hidden"
    assert current_campaign(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "campaign-test") == (
        "gathered > boarded > kept > reported > glanced")
    assert trace_current(stale, "campaign-test") is False
    assert board_record(stale)["traces"] == [
        {"campaign_id": "campaign-test", "trace": "stale"}]

def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(campaigns=[_campaign(), _campaign(seq=2)])
    with pytest.raises(ValueError):
        _book(campaigns=[_campaign(), _campaign(campaign_id="campaign-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(campaigns=[_campaign(repo_id="slice-nope")])
    with pytest.raises(ValueError):
        _book(slices=[_ref(), _ref(
            repo_id="slice-cold", seq=2, state="dormant")],
            campaigns=[_campaign(repo_id="slice-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(repo_id="slice-nope")])
    fields = {
        "schema": CAMPAIGN_SCHEMA, "slice": "M-216",
        "multi_campaign_hall": {"title": "A kept book"},
        "slices": [_ref().to_record()],
        "campaign_records": [_campaign().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "glanced"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_campaign"] = "campaign-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_campaign")
    fields["trace"] = "campaign-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / CAMPAIGN_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "multi_campaign_hall.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_campaign_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.campaign_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = CampaignRegistry()
    assert registry.title() is None
    registry.register_repo_ref(_ref())
    registry.register_campaign(_campaign())
    registry.register_view(_view())
    assert [g.campaign_id for g in registry.list_campaigns()] == ["campaign-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_campaign("campaign-test").title == "A test campaign"
    assert registry.get_slice("slice-test").state == "live"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("campaign-test").campaign_id == "campaign-test"
    with pytest.raises(ValueError):
        registry.register_campaign(_campaign(seq=9))
    with pytest.raises(ValueError):
        registry.register_campaign(_campaign(campaign_id="campaign-two"))
    with pytest.raises(KeyError):
        registry.get_campaign("campaign-nope")
    assert registry.book().title == "An unheld campaign book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = CampaignRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test campaign book"
    assert registry.title() == "A test campaign book"
    assert len(registry.list_campaigns()) == 2
    other = CampaignRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    campaign = _campaign()
    assert "A test campaign" in plain_words(campaign)
    assert panel_plain_words(_mixed_book()).startswith(
        "The campaign book holds 2 campaigns")
    assert verdict_plain_words(_mixed_book()) == (
        "The campaigns stand held: 1 of 2 shown campaigns stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green campaigns; red, "
        "named in its gaps: campaign-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_campaign(campaign)
    assert "Campaign: A test campaign" in text
    assert "stands complete" in text
    text = format_campaign(_campaign(checks=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The Campaign Gate (M-216) - A test campaign book" in book_text
    assert "campaign-hidden" in format_book(_mixed_book(), "slice-test")
    assert "Campaign panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "glanced - A test campaign (campaign-test)" in index_text
    assert "campaign-hidden" in index_text
    screen = format_campaign_screen()
    assert "The Campaign Gate (M-216)" in screen
    assert "campaign-bare-campaign" in screen

def test_parse_args_board_and_loader_targets():
    assert parse_campaign_args("") == ("show", None)
    assert parse_campaign_args(None) == ("show", None)
    assert parse_campaign_args("show") == ("show", None)
    assert parse_campaign_args("campaign campaign-test") == (
        "campaign", "campaign-test")
    assert parse_campaign_args("check glanced") == (
        "check", "glanced")
    assert parse_campaign_args("repo slice-test") == (
        "repo", "slice-test")
    assert parse_campaign_args("view view-test") == ("view", "view-test")
    assert parse_campaign_args("note note-test") == ("note", "note-test")
    assert parse_campaign_args("index") == ("index", None)
    assert parse_campaign_args("panel") == ("panel", None)
    assert parse_campaign_args("verdict") == ("verdict", None)
    for bad in ("dance", "campaign", "check", "slice", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_campaign_args(bad)
    board = board_record()
    assert board["type"] == "campaign_board"
    assert board["total"] == 5
    assert board["current_campaign"] == "campaign-bare-campaign"
    book = load_campaign({
        "schema": CAMPAIGN_SCHEMA, "slice": "M-216",
        "multi_campaign_hall": {"title": "A kept book"},
        "slices": [_ref().to_record()],
        "campaign_records": [_campaign().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, CampaignBook)
    assert book.title == "A kept book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_campaign({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_campaign({"slice": "M-999"})
    built = build_campaign(
        campaign_id="campaign-kw", seq=3, repo_id="slice-test",
        title="Kw Campaign", checks=["gathered", "boarded", "kept", "reported", "glanced"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="campaign-test")
    assert built.campaign_id == "campaign-kw"
    assert campaign_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-216 agent layer: the agent holds a campaign
# book for the session, campaigns and views are
# published as session news through the
# checkpoint target (journal first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held campaigns, the board is derived from
# the held campaigns' completeness, the roadmap standing
# is read from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no slice. This layer campaigns
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session journal news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_CAMPAIGN_EVENT_TYPES = (
    "campaign_campaign", "campaign_slice", "campaign_view",
    "campaign_panel", "campaign_verdict")


def _campaign_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_hall_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / CAMPAIGN_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "multi_campaign_hall.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestCampaignAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.hall_status()
        assert status["campaign_records"] == []
        assert status["slices"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["hall_book"]["title"] == EXAMPLE_TITLE
        assert len(status["hall_book"]["slices"]) == 3
        assert len(status["hall_book"]["campaign_records"]) == 5
        assert len(status["hall_book"]["views"]) == 2
        assert len(status["hall_book"]["notes"]) == 2
        assert len(status["hall_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-m215-boundary"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["check"] for e in status["index"]["entries"]] == (
            EXAMPLE_CHECKS)
        assert status["index"]["gaps"] == [
            "campaign-bare-campaign", "campaign-leaping-campaign"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["board"]["total"] == 5
        assert status["board"]["current_campaign"] == "campaign-bare-campaign"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 262
        assert status["roadmap"]["next_slice"] == "M-263"
        assert status["roadmap"]["m216_title"] == "Multi-campaign hall"
        assert "held as data alone" in status["rule"]
        assert "campaign-bare-campaign" in status["plain_words"]
        assert "The Campaign Gate (M-216)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._hall_registry()
        assert agent._hall_registry() is first
        assert agent._hall_store is first
        for name in ("hall_book", "hall_status", "hall_panel",
                     "hall_verdict", "hall_index", "report_hall"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_hall_registry", "hall_book", "hall_status",
            "get_hall_campaign", "get_hall_view", "get_hall_note",
            "hall_campaigns_for_repo", "hall_campaigns_green",
            "hall_panel", "hall_verdict", "hall_index",
            "register_hall_campaign", "register_hall_view",
            "view_hall", "register_hall_book",
            "record_hall_book", "report_hall",
            "_publish_hall_record", "_hall_screen",
            "_hall_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.hall_status()
        assert agent.get_hall_campaign(
            "campaign-held-campaign").title == "The held campaign"
        assert agent.get_hall_view(
            "view-campaigns").view_filter == "all"
        assert agent.get_hall_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.campaign_id for d in agent.hall_campaigns_for_repo(
            "slice-m216-campaign")] == [
            "campaign-own-campaign", "campaign-bare-campaign",
            "campaign-leaping-campaign"]
        assert [d.campaign_id for d in agent.hall_campaigns_green()] == [
            "campaign-held-campaign", "campaign-remeasured-campaign", "campaign-own-campaign"]
        agent.hall_panel()
        agent.hall_verdict()
        agent.hall_index()
        agent.report_hall()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _CAMPAIGN_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_hall_campaign("campaign-nope")
        with pytest.raises(KeyError):
            agent.get_hall_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_hall_note("note-nope")
        with pytest.raises(ValueError):
            agent.hall_campaigns_for_repo("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_hall_campaign(_campaign())
        status = agent.hall_status()
        assert [d["campaign_id"] for d in status["campaign_records"]] == ["campaign-test"]
        assert status["book"]["title"] == "An unheld campaign book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["check"] for e in status["index"]["entries"]] == [
            "glanced"]
        assert status["first_note"] is None
        assert "campaign-test" in status["screen"]
    def test_held_campaign_never_falls_back_to_the_example(
            self, agent):
        agent.register_hall_campaign(_campaign())
        with pytest.raises(KeyError):
            agent.get_hall_campaign("campaign-held-campaign")
        with pytest.raises(KeyError):
            agent.get_hall_view("view-campaigns")
        with pytest.raises(KeyError):
            agent.get_hall_note("note-note-first")
        campaign = agent.get_hall_campaign("campaign-test")
        assert campaign.title == "A test campaign"
        assert agent.hall_book().title == (
            "An unheld campaign book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_hall_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.campaign_id == "campaign-held-campaign"
        status = agent.hall_status()
        assert status["index"]["gaps"] == [
            "campaign-bare-campaign", "campaign-leaping-campaign"]
        assert status["first_note"]["campaign_id"] == (
            "campaign-held-campaign")
        assert status["first_note"]["stance"] == "note"

class TestCampaignAgentHolding:
    def test_register_campaign_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_hall_campaign(_campaign())
        assert result["campaign"]["campaign_id"] == "campaign-test"
        assert result["record_news"]["type"] == "campaign_campaign"
        assert "campaign-test" in result["screen"]
        events = _campaign_events(store, session_id, "campaign_campaign")
        assert len(events) == 1
        agent.close()

    def test_duplicate_campaign_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_hall_campaign(_campaign())
        with pytest.raises(ValueError):
            agent.register_hall_campaign(_campaign(seq=9))
        with pytest.raises(ValueError):
            agent.register_hall_campaign(_campaign(campaign_id="campaign-two"))
        events = _campaign_events(store, session_id, "campaign_campaign")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_hall_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_campaign_events(
            store, session_id, "campaign_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_hall_campaign(_campaign())
        result = agent.view_hall("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "campaign_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "glanced"
        assert len(_campaign_events(
            store, session_id, "campaign_view")) == 1
        assert len(_campaign_events(
            store, session_id, "campaign_panel")) == 1
        assert len(_campaign_events(
            store, session_id, "campaign_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_hall_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "campaign_slice", "campaign_campaign", "campaign_view"]
        assert len(_campaign_events(
            store, session_id, "campaign_campaign")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_hall_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "campaign_panel"
        assert result["index_record"]["gaps"] == [
            "campaign-bare-campaign", "campaign-leaping-campaign"]
        with pytest.raises(ValueError):
            agent.record_hall_book()
        assert len(_campaign_events(
            store, session_id, "campaign_slice")) == 3
        assert len(_campaign_events(
            store, session_id, "campaign_campaign")) == 5
        assert len(_campaign_events(
            store, session_id, "campaign_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_hall_book_file(tmp_path)
        book = load_campaign_file(path)
        result = agent.record_hall_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_hall()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "held"
        assert report["index"]["gaps"] == [
            "campaign-bare-campaign", "campaign-leaping-campaign"]
        assert "campaign-held-campaign" in report["book_text"]
        assert "glanced - The held campaign (campaign-held-campaign)" in report["index_text"]
        agent.register_hall_campaign(_campaign())
        report = agent.report_hall()
        assert report["book"]["title"] == "An unheld campaign book"
        assert report["panel"] is None
        assert report["verdict"] is None

class TestCampaignTerminalHeading:
    def test_show_campaign_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/hall")
        assert "The Campaign Gate (M-216)" in text
        _, _, text = _slash(agent, "/hall campaign campaign-held-campaign")
        assert "Campaign: The held campaign" in text
        _, _, text = _slash(
            agent, "/hall check glanced")
        assert "Campaign: The held campaign" in text
        _, _, text = _slash(agent, "/hall check triple resume")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/hall repo slice-m216-campaign")
        assert "campaign-bare-campaign" in text
        assert "campaign-held-campaign" not in text
        _, _, text = _slash(agent, "/hall view view-campaigns")
        assert "filter all" in text
        _, _, text = _slash(agent, "/hall note note-note-first")
        assert "Campaign note note campaign-held-campaign" in text
        _, _, text = _slash(agent, "/hall index")
        assert "Campaign index" in text
        assert "campaign-bare-campaign" in text
        _, _, text = _slash(agent, "/hall panel")
        assert "Campaign panel under view view-campaigns" in text
        _, _, text = _slash(agent, "/hall verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/hall [show|campaign <campaign-id>"
                "|check <check>|repo <repo-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/hall dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/hall campaign campaign-nope")
        assert "no campaign named" in text
@pytest.fixture()
def campaign_handler(agent, monkeypatch):
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


def _campaign_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestCampaignCommand:
    def test_show_is_default(self, campaign_handler, agent):
        campaign_handler._handle_campaign("")
        assert "The Campaign Gate (M-216)" in (
            _campaign_published_text(campaign_handler))

    def test_campaign_check_slice_view_note_index_panel_verdict(
            self, campaign_handler, agent):
        campaign_handler._handle_campaign("campaign campaign-held-campaign")
        assert "Campaign: The held campaign" in _campaign_published_text(
            campaign_handler)
        campaign_handler._handle_campaign(
            "check glanced")
        assert "Campaign: The held campaign" in _campaign_published_text(
            campaign_handler)
        campaign_handler._handle_campaign("repo slice-m216-campaign")
        assert "campaign-bare-campaign" in _campaign_published_text(
            campaign_handler)
        campaign_handler._handle_campaign("view view-campaigns")
        assert "filter all" in _campaign_published_text(campaign_handler)
        campaign_handler._handle_campaign("note note-note-first")
        assert "Campaign note note campaign-held-campaign" in (
            _campaign_published_text(campaign_handler))
        campaign_handler._handle_campaign("index")
        assert "Campaign index" in _campaign_published_text(campaign_handler)
        campaign_handler._handle_campaign("panel")
        assert "Campaign panel under view" in _campaign_published_text(
            campaign_handler)
        campaign_handler._handle_campaign("verdict")
        assert "held" in _campaign_published_text(campaign_handler)
    def test_bad_grammar_is_published(
            self, campaign_handler, agent):
        campaign_handler._handle_campaign("dance party")
        assert USAGE in _campaign_published_text(campaign_handler)
        campaign_handler._handle_campaign("campaign campaign-nope")
        assert "no campaign named" in _campaign_published_text(
            campaign_handler)


class TestChatScreenRoutingCampaign:
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
        screen.handle_command("/hall panel", _FakeLog())
        assert calls == [("/hall", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/hall[/green] - show the Campaign gate (M-216)" in (
            text)
        assert ('"/hall": "Usage: /hall | '
                '/hall campaign <campaign-id>') in text

class TestCampaignDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.hall_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-campaigns"
        verdict = agent.hall_verdict()
        assert verdict.verdict == "held"
        found = agent.hall_verdict("view-glanced")
        assert found.verdict == "glanced"
        assert found.green_shown == 3
        agent.register_hall_campaign(_campaign())
        with pytest.raises(ValueError):
            agent.hall_panel()
        with pytest.raises(ValueError):
            agent.hall_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_hall_campaign(_campaign(checks=[]))
        result = agent.view_hall("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.hall_index()
        assert [e["check"] for e in result["index"]["entries"]] == (
            EXAMPLE_CHECKS)
        assert result["index"]["gaps"] == [
            "campaign-bare-campaign", "campaign-leaping-campaign"]
        assert "glanced - The held campaign (campaign-held-campaign)" in (
            result["index_text"])
        campaign = agent.get_hall_campaign("campaign-leaping-campaign")
        assert campaign_gaps(campaign, agent.hall_book()) == (
            "steps from boarded to glanced, which the campaign sequence "
            "does not allow",)
        assert campaign_green(campaign, agent.hall_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _CAMPAIGN_EVENT_TYPES] == []
        agent.close()
