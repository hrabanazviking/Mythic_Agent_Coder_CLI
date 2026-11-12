"""M-227 Workflow default honoured - pure-layer tests.

TIER: integration

The pure layer is the dispatcher, held as data: one
record per proposal, held whole - the campaign it
answers for, named by campaign id, its title, the
steps it walked in walk proposal and the evidence
it carries, held by campaign. The question walk is
explicit - named, checked, declared, manual,
upheld, with their legal steps held as data -
and a proposal's standing is derived at call
time: a proposal that opens anywhere but proposed, steps where the sequence does not allow,
carries a bare claim in place of held evidence,
or has not yet proposed upheld stands open,
named in its gaps. A proposal stands only for
an active campaign: a proposal naming no held
campaign, or one that is not active, refuses by
name. The proposal's trace - its walked steps
as one line - is derived at call time, and a held
trace record stands current only while it agrees
with the derived trace. The index, panel,
verdict, ledger, trace, proposal and current
proposal are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
question was actually answered, manual or
upheld live. The shipped example book is held
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

from mythic_agent.core.workflow_default import (
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
    PROPOSAL_RESOURCE,
    PROPOSAL_RULE,
    PROPOSAL_SCHEMA,
    PROPOSAL_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    ProposalRecord,
    IndexProposal,
    CampaignRef,
    NoteRecord,
    ProposalBook,
    ProposalIndex,
    ProposalPanel,
    ProposalRegistry,
    ProposalVerdict,
    ProposalView,
    trace_for_proposal,
    ledger_record,
    book_record,
    build_trace,
    build_book,
    build_proposal,
    build_campaign_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_proposal,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    proposal_for_check,
    proposal_gaps,
    proposal_proposal,
    proposal_record,
    proposal_green,
    proposals_for_campaign,
    first_note,
    format_book,
    format_proposal,
    format_index,
    format_note,
    format_stage,
    format_panel,
    format_proposal_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    campaign_record,
    load_proposal,
    legal_step,
    load_proposal_file,
    next_stage,
    normalize_stage,
    normalize_claim_kind,
    normalize_campaign_state,
    normalize_stance,
    normalize_view_filter,
    note_for_proposal,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_proposal_args,
    green_proposals,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_proposals,
    validate_book,
    validate_proposal,
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
EXAMPLE_TITLE = "Workflow default honoured at the M-227 slice run"
EXAMPLE_STAGES = ["upheld", "upheld", "upheld"]
EXAMPLE_RUN_IDS = (
    "proposal-held-proposal", "proposal-retried-proposal",
    "proposal-own-proposal", "proposal-bare-proposal",
    "proposal-leaping-proposal")
EXAMPLE_TRACE = "proposed > checked > declared > manual > upheld"


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
        "origin_session": "proposal-test",
    }
    fields.update(overrides)
    return build_campaign_ref(fields)


def _proposal(**overrides):
    fields = {
        "proposal_id": "proposal-test",
        "seq": 1,
        "campaign_id": "campaign-test",
        "title": "A test proposal",
        "stages": ["proposed", "checked", "declared", "manual", "upheld"],
        "claims": [],
        "detail": "A test proposal held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "proposal-test",
    }
    fields.update(overrides)
    return build_proposal(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "proposal-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "proposal_id": "proposal-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "proposal-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "proposal_id": "proposal-test",
        "trace": "proposed > checked > declared > manual > upheld",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "proposal-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(campaigns=None, proposals=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": PROPOSAL_SCHEMA,
        "campaign": "M-227",
        "workflow_default": {"title": "A test proposal book"},
        "campaigns": [item.to_record() for item in (
            campaigns if campaigns is not None else [_ref()])],
        "proposal_records": [item.to_record() for item in (
            proposals if proposals is not None else [_proposal()])],
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
    return _book(proposals=[
        _proposal(),
        _proposal(proposal_id="proposal-hidden", seq=2,
               title="A hidden proposal", stages=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_proposal()
    assert book.title == EXAMPLE_TITLE
    assert book.proposal_ids() == EXAMPLE_RUN_IDS
    assert book.campaign_ids() == (
        "campaign-m226-orders", "campaign-m227-workflow",
        "campaign-m228-scaling")
    assert [v.view_id for v in book.views] == [
        "view-proposals", "view-upheld"]
    assert [m.proposal_id for m in book.notes] == [
        "proposal-held-proposal", "proposal-bare-proposal"]
    assert [a.proposal_id for a in book.traces] == ["proposal-held-proposal"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m226-campaign"
    assert panel.as_of == "2026-11-11"
    assert [row.item_id for row in panel.rows] == list(book.proposal_ids())
    derived = derive_panel(book, "view-proposals")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-proposals").verdict == "held"
    assert derive_verdict(book, "view-proposals").green_shown == 3
    assert derive_verdict(book, "view-upheld").verdict == "upheld"
    assert derive_verdict(book, "view-upheld").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / PROPOSAL_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == PROPOSAL_SCHEMA
    assert raw["campaign"] == "M-227"
    assert "verdict" not in raw
    assert "proposal_index" not in raw
    assert "ledger" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-227")]
    assert slice_.title == "Workflow default honoured"
    assert slice_.part == 9
    assert "repositories' CI is proposed as manual-dispatch by default on Volmarr's projects (his standing" in slice_.summary
    assert "the coder says so when it writes a workflow" in slice_.summary
    assert PROPOSAL_SLICE == "M-227"

def test_charter_rows_do_not_name_m227():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-227" not in owners
    method = load_method_charter()
    assert "M-201" in method.source_note
    assert "M-232" in method.source_note
    assert "YRSA_CODING_JUGGERNAUT" in method.source_note

def test_closed_vocabularies():
    assert COMPLETE_WORDS == ("complete", "open")
    assert STAGE_FIELDS == ("stages", "claims")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "complete", "open")
    assert VERDICT_WORDS == ("upheld", "held", "blocked")
    assert CAMPAIGN_STATES == ("live", "dormant")
    assert STAGES == ("proposed", "checked", "declared", "manual", "upheld")
    assert HELD_EVIDENCE == ("workflow_ref", "dispatch_ref", "repo_ref", "trigger_ref", "proposal_ref")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_KINDS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["manual"] == ("proposed", "upheld")
    assert TRANSITIONS["upheld"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_STAGE == "upheld"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_campaign_state("LIVE") == "live"
    assert normalize_stage("DECLARED") == "declared"
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
    assert legal_step("declared", "manual") is True
    assert legal_step("checked", "upheld") is False
    assert legal_step("upheld", "proposed") is False
    assert next_stage("proposed") == "checked"
    assert next_stage("declared") == "manual"
    assert next_stage("manual", failed=True) == "proposed"
    assert next_stage("manual") == "upheld"
    assert next_stage("upheld") is None
    assert "held as data alone" in PROPOSAL_RULE
    assert "proposal sequence" in PROPOSAL_RULE
    assert "M-227" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /workflow")

def test_shipped_book_judged_honestly_as_data():
    book = load_proposal()
    opening = book.proposal_for("proposal-held-proposal")
    assert proposal_green(opening, book) is True
    assert proposal_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Proposal: The held proposal",
        "Campaign: campaign-m226-orders",
        "Stage: upheld",
        "Claims: workflow_ref")
    asking = book.proposal_for("proposal-bare-proposal")
    assert proposal_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert proposal_green(asking, book) is False
    skipping = book.proposal_for("proposal-leaping-proposal")
    assert proposal_gaps(skipping, book) == (
        "steps from checked to upheld, which the proposal sequence "
        "does not allow",)
    assert [g.proposal_id for g in green_proposals(book)] == [
        "proposal-held-proposal", "proposal-retried-proposal", "proposal-own-proposal"]
    index = derive_index(book)
    assert [e.stage for e in index.proposals] == EXAMPLE_STAGES
    assert index.gaps == ("proposal-bare-proposal", "proposal-leaping-proposal")
    assert proposal_for_check(book, EXAMPLE_STAGE).proposal_id == (
        "proposal-held-proposal")
    assert proposal_for_check(book, "triple proposal") is None
    assert transition_breaks(book) == (
        "proposal-leaping-proposal: checked > upheld",)
    assert [g.proposal_id for g in proposal_proposal(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "proposal-held-proposal") == EXAMPLE_TRACE
    assert trace_current(book, "proposal-held-proposal") is True
    assert trace_current(book, "proposal-retried-proposal") is False
    assert trace_for_proposal(
        book, "proposal-held-proposal").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_proposal(
        book, "proposal-held-proposal", "note").note_id == (
            "note-note-first")
    assert note_for_proposal(book, "proposal-nope") is None
    assert current_proposal(book).proposal_id == "proposal-bare-proposal"
    ledger = ledger_record(book)
    assert ledger["standings"] == [
        {"standing": "complete", "proposal_records": 3},
        {"standing": "open", "proposal_records": 2}]
    assert ledger["total"] == 5
    assert ledger["current_proposal"] == "proposal-bare-proposal"
    assert ledger["traces"] == [
        {"proposal_id": "proposal-held-proposal", "trace": "current"},
        {"proposal_id": "proposal-retried-proposal", "trace": "unheld"},
        {"proposal_id": "proposal-own-proposal", "trace": "unheld"},
        {"proposal_id": "proposal-bare-proposal", "trace": "unheld"},
        {"proposal_id": "proposal-leaping-proposal", "trace": "unheld"}]
    assert ledger["breaks"] == ["proposal-leaping-proposal: checked > upheld"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 244
    assert citizen["next_slice"] == "M-245"
    assert citizen["m227_title"] == "Workflow default honoured"
    assert citizen["m227_part"] == 9
    assert citizen["m227_status"] == "done"

def test_proposal_record_round_trips():
    proposal = _proposal()
    assert validate_proposal(proposal) is proposal
    rebuilt = build_proposal(proposal.to_record())
    assert rebuilt == proposal
    assert rebuilt.item_id == "proposal-test"
    assert rebuilt.stage == "upheld"
    record = proposal_record(proposal)
    assert record["type"] == "proposal_proposal"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert campaign_record(ref)["type"] == "proposal_run"
    assert campaign_record(ref)["state"] == "live"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _proposal(stages=[])
    assert proposal_gaps(silent) == (
        "has passed through no step: the proposal has not started",)
    assert proposal_green(silent) is False
    walking = _proposal(stages=["proposed", "checked"])
    assert proposal_gaps(walking) == (
        "has not reached upheld: the proposal stands at checked",)
    assert walking.stage == "checked"
    sideways = _proposal(stages=["checked", "declared", "manual", "upheld"])
    assert proposal_gaps(sideways) == (
        "opens at checked, not at proposed: the proposal opens "
        "with the reflection",)
    repaired = _proposal(stages=["proposed", "checked", "declared", "manual", "proposed", "checked", "declared", "manual", "upheld"])
    assert proposal_gaps(repaired) == ()
    assert proposal_green(repaired) is True
    with pytest.raises(ValueError):
        _proposal(stages=[42])
    with pytest.raises(ValueError):
        _proposal(stages="inspect as a bare string")
    with pytest.raises(ValueError):
        _proposal(stages=["proposed", "polish"])
    with pytest.raises(ValueError):
        _proposal(claims=["weather"])
    with pytest.raises(ValueError):
        _proposal(claims="workflow_ref")
    none_proposal = _proposal(stages=None, claims=None)
    assert none_proposal.stages == ()
    assert none_proposal.claims == ()

def test_proposal_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "proposals", "coverage", "current_proposal",
                "ledger", "proposal"):
        fields = _proposal().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_proposal(fields)
    fields = _proposal().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_proposal(fields)


def test_proposal_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _proposal().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_proposal(fields)


def test_proposal_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _proposal(title="")
    with pytest.raises(ValueError):
        _proposal(campaign_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "proposed > checked > declared > manual > upheld"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_proposals_own_fields():
    proposal = _proposal(claims=["workflow_ref"])
    assert plain_lines(proposal) == (
        "Proposal: A test proposal",
        "Campaign: campaign-test",
        "Stage: upheld",
        "Claims: workflow_ref")
    segment = segment_of(proposal)
    assert segment.startswith("proposal-test: A test proposal")
    assert "stage: 'upheld'" in segment
    assert "gaps: none" in segment
    assert plain_words(proposal).startswith(
        "A test proposal - from campaign-test")

def test_red_proposals_stand_named_in_their_gaps():
    asking = _proposal(claims=["feeling", "workflow_ref", "summary"])
    assert proposal_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert proposal_green(asking) is False
    skipping = _proposal(stages=["proposed", "checked", "upheld"])
    assert proposal_gaps(skipping) == (
        "steps from checked to upheld, which the proposal sequence "
        "does not allow",)
    book = _book(proposals=[
        _proposal(),
        _proposal(proposal_id="proposal-skipping", seq=2,
             stages=["proposed", "checked", "upheld"]),
    ])
    assert transition_breaks(book) == (
        "proposal-skipping: checked > upheld",)
    assert current_proposal(book).proposal_id == "proposal-skipping"
    assert [g.proposal_id for g in proposal_proposal(book)] == [
        "proposal-test", "proposal-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "proposal_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "proposal_note"
    assert record["proposal_id"] == "proposal-test"
    assert view_plain_words(view) == "View view-test: shows all proposals."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_proposals_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.stage for e in index.proposals] == ["upheld"]
    assert index.proposals[0] == IndexProposal(
        stage="upheld",
        proposal_id="proposal-test", title="A test proposal")
    assert index.gaps == ("proposal-hidden",)
    record = index_record(book)
    assert record["type"] == "proposal_index"
    assert record["gaps"] == ["proposal-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "proposal_book"

def test_check_target_reaches_its_proposal_and_an_unheld_target_reaches_nothing():
    book = load_proposal()
    assert proposal_for_check(book, "upheld").proposal_id == (
        "proposal-held-proposal")
    assert proposal_for_check(book, "") is None
    assert proposal_for_check(book, None) is None
    assert proposal_for_check(book, "not held at all") is None
    text = format_stage(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_proposal()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Proposal note note proposal-held-proposal" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").proposal_id == "proposal-test"
    assert note_for_proposal(book, "proposal-test").note_id == "note-test"
    assert note_for_proposal(book, "proposal-test", "praise") is None
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
    row = build_row(None, _proposal(), book)
    assert row.standing == "complete"
    assert validate_row(row, _proposal(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_proposals():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "proposal_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "upheld"
    empty_book = _book(proposals=[_proposal(stages=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(ProposalVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_readings():
    book = load_proposal()
    assert [g.proposal_id for g in shown_proposals(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.proposal_id for g in shown_proposals(book, "view-upheld")] == [
        "proposal-held-proposal", "proposal-retried-proposal", "proposal-own-proposal"]
    assert [g.proposal_id for g in proposals_for_campaign(
        book, "campaign-m227-workflow")] == [
            "proposal-own-proposal", "proposal-bare-proposal",
            "proposal-leaping-proposal"]
    assert proposals_for_campaign(book, "campaign-nope") == ()
    assert current_proposal(_mixed_book()).proposal_id == "proposal-hidden"
    assert current_proposal(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "proposal-test") == (
        "proposed > checked > declared > manual > upheld")
    assert trace_current(stale, "proposal-test") is False
    assert ledger_record(stale)["traces"] == [
        {"proposal_id": "proposal-test", "trace": "stale"}]

def test_dispatch_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(proposals=[_proposal(), _proposal(seq=2)])
    with pytest.raises(ValueError):
        _book(proposals=[_proposal(), _proposal(proposal_id="proposal-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(proposals=[_proposal(campaign_id="campaign-nope")])
    with pytest.raises(ValueError):
        _book(campaigns=[_ref(), _ref(
            campaign_id="campaign-cold", seq=2, state="dormant")],
            proposals=[_proposal(campaign_id="campaign-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(campaign_id="campaign-nope")])
    fields = {
        "schema": PROPOSAL_SCHEMA, "campaign": "M-227",
        "workflow_default": {"title": "A declared book"},
        "campaigns": [_ref().to_record()],
        "proposal_records": [_proposal().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "upheld"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_proposal"] = "proposal-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_proposal")
    fields["trace"] = "proposal-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / PROPOSAL_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "workflow_default.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_proposal_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.proposal_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = ProposalRegistry()
    assert registry.title() is None
    registry.register_campaign_ref(_ref())
    registry.register_proposal(_proposal())
    registry.register_view(_view())
    assert [g.proposal_id for g in registry.list_proposals()] == ["proposal-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_proposal("proposal-test").title == "A test proposal"
    assert registry.get_slice("campaign-test").state == "live"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("proposal-test").proposal_id == "proposal-test"
    with pytest.raises(ValueError):
        registry.register_proposal(_proposal(seq=9))
    with pytest.raises(ValueError):
        registry.register_proposal(_proposal(proposal_id="proposal-two"))
    with pytest.raises(KeyError):
        registry.get_proposal("proposal-nope")
    assert registry.book().title == "An unheld proposal book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = ProposalRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test proposal book"
    assert registry.title() == "A test proposal book"
    assert len(registry.list_proposals()) == 2
    other = ProposalRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    proposal = _proposal()
    assert "A test proposal" in plain_words(proposal)
    assert panel_plain_words(_mixed_book()).startswith(
        "The proposal book holds 2 proposals")
    assert verdict_plain_words(_mixed_book()) == (
        "The proposals stand held: 1 of 2 shown proposals stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green proposals; red, "
        "named in its gaps: proposal-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_proposal(proposal)
    assert "Proposal: A test proposal" in text
    assert "stands complete" in text
    text = format_proposal(_proposal(stages=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The Proposal Gate (M-227) - A test proposal book" in book_text
    assert "proposal-hidden" in format_book(_mixed_book(), "campaign-test")
    assert "Proposal panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "upheld - A test proposal (proposal-test)" in index_text
    assert "proposal-hidden" in index_text
    screen = format_proposal_screen()
    assert "The Proposal Gate (M-227)" in screen
    assert "proposal-bare-proposal" in screen

def test_parse_args_well_and_loader_targets():
    assert parse_proposal_args("") == ("show", None)
    assert parse_proposal_args(None) == ("show", None)
    assert parse_proposal_args("show") == ("show", None)
    assert parse_proposal_args("proposal proposal-test") == (
        "proposal", "proposal-test")
    assert parse_proposal_args("stage upheld") == (
        "stage", "upheld")
    assert parse_proposal_args("campaign campaign-test") == (
        "campaign", "campaign-test")
    assert parse_proposal_args("view view-test") == ("view", "view-test")
    assert parse_proposal_args("note note-test") == ("note", "note-test")
    assert parse_proposal_args("index") == ("index", None)
    assert parse_proposal_args("panel") == ("panel", None)
    assert parse_proposal_args("verdict") == ("verdict", None)
    for bad in ("dance", "proposal", "stage", "campaign", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_proposal_args(bad)
    ledger = ledger_record()
    assert ledger["type"] == "proposal_well"
    assert ledger["total"] == 5
    assert ledger["current_proposal"] == "proposal-bare-proposal"
    book = load_proposal({
        "schema": PROPOSAL_SCHEMA, "campaign": "M-227",
        "workflow_default": {"title": "A declared book"},
        "campaigns": [_ref().to_record()],
        "proposal_records": [_proposal().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, ProposalBook)
    assert book.title == "A declared book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_proposal({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_proposal({"campaign": "M-999"})
    built = build_proposal(
        proposal_id="proposal-kw", seq=3, campaign_id="campaign-test",
        title="Kw Proposal", stages=["proposed", "checked", "declared", "manual", "upheld"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="proposal-test")
    assert built.proposal_id == "proposal-kw"
    assert proposal_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-227 agent layer: the agent holds a proposal
# book for the session, proposals and views are
# published as session news through the
# checkpoint target (ledger first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held proposals, the ledger is derived from
# the held proposals' completeness, the roadmap standing
# is manual from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no campaign. This layer proposals
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session ledger news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_PROPOSAL_EVENT_TYPES = (
    "proposal_proposal", "proposal_run", "proposal_view",
    "proposal_panel", "proposal_verdict")


def _proposal_events(store, session_id, campaign):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == campaign]


def _write_workflow_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / PROPOSAL_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "workflow_default.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestProposalAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.workflow_status()
        assert status["proposal_records"] == []
        assert status["campaigns"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["workflow_book"]["title"] == EXAMPLE_TITLE
        assert len(status["workflow_book"]["campaigns"]) == 3
        assert len(status["workflow_book"]["proposal_records"]) == 5
        assert len(status["workflow_book"]["views"]) == 2
        assert len(status["workflow_book"]["notes"]) == 2
        assert len(status["workflow_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-m226-campaign"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["stage"] for e in status["index"]["proposals"]] == (
            EXAMPLE_STAGES)
        assert status["index"]["gaps"] == [
            "proposal-bare-proposal", "proposal-leaping-proposal"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["ledger"]["total"] == 5
        assert status["ledger"]["current_proposal"] == "proposal-bare-proposal"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 244
        assert status["roadmap"]["next_slice"] == "M-245"
        assert status["roadmap"]["m227_title"] == "Workflow default honoured"
        assert "held as data alone" in status["rule"]
        assert "proposal-bare-proposal" in status["plain_words"]
        assert "The Proposal Gate (M-227)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._workflow_registry()
        assert agent._workflow_registry() is first
        assert agent._workflow_store is first
        for name in ("workflow_book", "workflow_status", "workflow_panel",
                     "workflow_verdict", "workflow_index", "report_workflow"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_workflow_registry", "workflow_book", "workflow_status",
            "get_workflow_proposal", "get_workflow_view", "get_workflow_note",
            "proposals_for_campaign", "workflow_green",
            "workflow_panel", "workflow_verdict", "workflow_index",
            "register_workflow_proposal", "register_workflow_view",
            "view_workflow", "register_workflow_book",
            "record_workflow_book", "report_workflow",
            "_publish_workflow_record", "_workflow_screen",
            "_workflow_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.workflow_status()
        assert agent.get_workflow_proposal(
            "proposal-held-proposal").title == "The held proposal"
        assert agent.get_workflow_view(
            "view-proposals").view_filter == "all"
        assert agent.get_workflow_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.proposal_id for d in agent.proposals_for_campaign(
            "campaign-m227-workflow")] == [
            "proposal-own-proposal", "proposal-bare-proposal",
            "proposal-leaping-proposal"]
        assert [d.proposal_id for d in agent.workflow_green()] == [
            "proposal-held-proposal", "proposal-retried-proposal", "proposal-own-proposal"]
        agent.workflow_panel()
        agent.workflow_verdict()
        agent.workflow_index()
        agent.report_workflow()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _PROPOSAL_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_workflow_proposal("proposal-nope")
        with pytest.raises(KeyError):
            agent.get_workflow_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_workflow_note("note-nope")
        with pytest.raises(ValueError):
            agent.proposals_for_campaign("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_workflow_proposal(_proposal())
        status = agent.workflow_status()
        assert [d["proposal_id"] for d in status["proposal_records"]] == ["proposal-test"]
        assert status["book"]["title"] == "An unheld proposal book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["stage"] for e in status["index"]["proposals"]] == [
            "upheld"]
        assert status["first_note"] is None
        assert "proposal-test" in status["screen"]
    def test_held_proposal_never_falls_back_to_the_example(
            self, agent):
        agent.register_workflow_proposal(_proposal())
        with pytest.raises(KeyError):
            agent.get_workflow_proposal("proposal-held-proposal")
        with pytest.raises(KeyError):
            agent.get_workflow_view("view-proposals")
        with pytest.raises(KeyError):
            agent.get_workflow_note("note-note-first")
        proposal = agent.get_workflow_proposal("proposal-test")
        assert proposal.title == "A test proposal"
        assert agent.workflow_book().title == (
            "An unheld proposal book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_workflow_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.proposal_id == "proposal-held-proposal"
        status = agent.workflow_status()
        assert status["index"]["gaps"] == [
            "proposal-bare-proposal", "proposal-leaping-proposal"]
        assert status["first_note"]["proposal_id"] == (
            "proposal-held-proposal")
        assert status["first_note"]["stance"] == "note"

class TestProposalAgentHolding:
    def test_register_proposal_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_workflow_proposal(_proposal())
        assert result["proposal"]["proposal_id"] == "proposal-test"
        assert result["record_news"]["type"] == "proposal_proposal"
        assert "proposal-test" in result["screen"]
        events = _proposal_events(store, session_id, "proposal_proposal")
        assert len(events) == 1
        agent.close()

    def test_duplicate_proposal_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_workflow_proposal(_proposal())
        with pytest.raises(ValueError):
            agent.register_workflow_proposal(_proposal(seq=9))
        with pytest.raises(ValueError):
            agent.register_workflow_proposal(_proposal(proposal_id="proposal-two"))
        events = _proposal_events(store, session_id, "proposal_proposal")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_workflow_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_proposal_events(
            store, session_id, "proposal_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_workflow_proposal(_proposal())
        result = agent.view_workflow("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "proposal_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "upheld"
        assert len(_proposal_events(
            store, session_id, "proposal_view")) == 1
        assert len(_proposal_events(
            store, session_id, "proposal_panel")) == 1
        assert len(_proposal_events(
            store, session_id, "proposal_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_proposal(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_workflow_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "proposal_run", "proposal_proposal", "proposal_view"]
        assert len(_proposal_events(
            store, session_id, "proposal_proposal")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_workflow_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "proposal_panel"
        assert result["index_record"]["gaps"] == [
            "proposal-bare-proposal", "proposal-leaping-proposal"]
        with pytest.raises(ValueError):
            agent.record_workflow_book()
        assert len(_proposal_events(
            store, session_id, "proposal_run")) == 3
        assert len(_proposal_events(
            store, session_id, "proposal_proposal")) == 5
        assert len(_proposal_events(
            store, session_id, "proposal_view")) == 2
        agent.close()

    def test_book_from_a_file_is_checked_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_workflow_book_file(tmp_path)
        book = load_proposal_file(path)
        result = agent.record_workflow_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_runrt_renders_example_then_held_book_only(self, agent):
        proposal = agent.report_workflow()
        assert proposal["book"]["title"] == EXAMPLE_TITLE
        assert proposal["verdict"]["verdict"] == "held"
        assert proposal["index"]["gaps"] == [
            "proposal-bare-proposal", "proposal-leaping-proposal"]
        assert "proposal-held-proposal" in proposal["book_text"]
        assert "upheld - The held proposal (proposal-held-proposal)" in proposal["index_text"]
        agent.register_workflow_proposal(_proposal())
        proposal = agent.report_workflow()
        assert proposal["book"]["title"] == "An unheld proposal book"
        assert proposal["panel"] is None
        assert proposal["verdict"] is None

class TestProposalTerminalHeading:
    def test_show_proposal_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/workflow")
        assert "The Proposal Gate (M-227)" in text
        _, _, text = _slash(agent, "/workflow proposal proposal-held-proposal")
        assert "Proposal: The held proposal" in text
        _, _, text = _slash(
            agent, "/workflow stage upheld")
        assert "Proposal: The held proposal" in text
        _, _, text = _slash(agent, "/workflow stage triple proposal")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/workflow campaign campaign-m227-workflow")
        assert "proposal-bare-proposal" in text
        assert "proposal-held-proposal" not in text
        _, _, text = _slash(agent, "/workflow view view-proposals")
        assert "filter all" in text
        _, _, text = _slash(agent, "/workflow note note-note-first")
        assert "Proposal note note proposal-held-proposal" in text
        _, _, text = _slash(agent, "/workflow index")
        assert "Proposal index" in text
        assert "proposal-bare-proposal" in text
        _, _, text = _slash(agent, "/workflow panel")
        assert "Proposal panel under view view-proposals" in text
        _, _, text = _slash(agent, "/workflow verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/workflow [show|proposal <proposal-id>"
                "|stage <stage>|campaign <campaign-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/workflow dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/workflow proposal proposal-nope")
        assert "no proposal named" in text
@pytest.fixture()
def proposal_handler(agent, monkeypatch):
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


def _proposal_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestProposalCommand:
    def test_show_is_default(self, proposal_handler, agent):
        proposal_handler._handle_workflow("")
        assert "The Proposal Gate (M-227)" in (
            _proposal_published_text(proposal_handler))

    def test_proposal_check_slice_view_note_index_panel_verdict(
            self, proposal_handler, agent):
        proposal_handler._handle_workflow("proposal proposal-held-proposal")
        assert "Proposal: The held proposal" in _proposal_published_text(
            proposal_handler)
        proposal_handler._handle_workflow(
            "stage upheld")
        assert "Proposal: The held proposal" in _proposal_published_text(
            proposal_handler)
        proposal_handler._handle_workflow("campaign campaign-m227-workflow")
        assert "proposal-bare-proposal" in _proposal_published_text(
            proposal_handler)
        proposal_handler._handle_workflow("view view-proposals")
        assert "filter all" in _proposal_published_text(proposal_handler)
        proposal_handler._handle_workflow("note note-note-first")
        assert "Proposal note note proposal-held-proposal" in (
            _proposal_published_text(proposal_handler))
        proposal_handler._handle_workflow("index")
        assert "Proposal index" in _proposal_published_text(proposal_handler)
        proposal_handler._handle_workflow("panel")
        assert "Proposal panel under view" in _proposal_published_text(
            proposal_handler)
        proposal_handler._handle_workflow("verdict")
        assert "held" in _proposal_published_text(proposal_handler)
    def test_bad_grammar_is_published(
            self, proposal_handler, agent):
        proposal_handler._handle_workflow("dance party")
        assert USAGE in _proposal_published_text(proposal_handler)
        proposal_handler._handle_workflow("proposal proposal-nope")
        assert "no proposal named" in _proposal_published_text(
            proposal_handler)


class TestChatScreenRoutingProposal:
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
        screen.handle_command("/workflow panel", _FakeLog())
        assert calls == [("/workflow", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/workflow[/green] - show the Proposal gate (M-227)" in (
            text)
        assert ('"/workflow": "Usage: /workflow | '
                '/workflow proposal <proposal-id>') in text

class TestProposalDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.workflow_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-proposals"
        verdict = agent.workflow_verdict()
        assert verdict.verdict == "held"
        found = agent.workflow_verdict("view-upheld")
        assert found.verdict == "upheld"
        assert found.green_shown == 3
        agent.register_workflow_proposal(_proposal())
        with pytest.raises(ValueError):
            agent.workflow_panel()
        with pytest.raises(ValueError):
            agent.workflow_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_workflow_proposal(_proposal(stages=[]))
        result = agent.view_workflow("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.workflow_index()
        assert [e["stage"] for e in result["index"]["proposals"]] == (
            EXAMPLE_STAGES)
        assert result["index"]["gaps"] == [
            "proposal-bare-proposal", "proposal-leaping-proposal"]
        assert "upheld - The held proposal (proposal-held-proposal)" in (
            result["index_text"])
        proposal = agent.get_workflow_proposal("proposal-leaping-proposal")
        assert proposal_gaps(proposal, agent.workflow_book()) == (
            "steps from checked to upheld, which the proposal sequence "
            "does not allow",)
        assert proposal_green(proposal, agent.workflow_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _PROPOSAL_EVENT_TYPES] == []
        agent.close()
