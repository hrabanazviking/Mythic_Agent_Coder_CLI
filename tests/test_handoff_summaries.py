"""M-163 Handoff summaries - pure-layer tests.

TIER: integration

The pure layer is the handoff summary itself, held
as data: one ended session's standing written
durable - where things stand for the next session
or the next human, the stand-up (M-134) in durable
form - carried with its provenance whole (the
session it ends, the project and branch it stood
on, the claims it carries from the stand-up - done,
doing, blocked, needs-you - the session and journal
evidence those claims stand on, who wrote it, the
day, and where it was read from), composed by
import from the shipped holdings it stands beside
(the stand-ups, M-134, session memory, M-153,
multi-session per project, M-162, and long-session
endurance, M-161), each judged by its own layer's
validation, a handoff panel derived from the whole
book in settled order, a handoff verdict derived
for the whole book - what needs you is never
smoothed away - the shipped example book held in a
data file, and a loader that reads a book from any
file. Nothing here sends, posts, schedules, calls
a model or writes any project's files: holding a
handoff records a writing, and that is the whole
road.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.long_session_endurance import load_long_session_endurance
from mythic_agent.core.multi_session_projects import load_multi_session_projects
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.session_memory import load_session_memory
from mythic_agent.core.stand_ups import load_stand_up, digest_stand_up
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.handoff_summaries import (
    CLAIM_KINDS,
    HANDOFF_SUMMARIES_RESOURCE,
    HANDOFF_SUMMARIES_SCHEMA,
    HANDOFF_SUMMARIES_SLICE,
    PLAIN_EXPLANATION,
    USAGE,
    EvidenceVerdict,
    HandoffBook,
    HandoffPanel,
    HandoffPanelRow,
    HandoffRegistry,
    HandoffSummary,
    SectionCount,
    book_record,
    build_book,
    build_handoff,
    build_panel,
    build_row,
    build_verdict,
    derive_panel,
    derive_verdict,
    format_handoff,
    format_handoff_summaries_screen,
    format_handoffs,
    format_panel,
    format_verdict,
    handoff_from_endurance_record,
    handoff_from_parallel_session,
    handoff_from_session_situation,
    handoff_from_stand_up,
    handoff_record,
    handoff_refs,
    handoffs_from_multi_session_book,
    inspect_handoff_source,
    load_handoff_summaries,
    load_handoff_summaries_file,
    normalize_claim_kind,
    panel_plain_words,
    panel_record,
    parse_handoffsummary_args,
    plain_words,
    total_claims,
    total_evidence,
    validate_book,
    validate_handoff,
    validate_panel,
    validate_row,
    validate_verdict,
    verdict_plain_words,
    verdict_record,
)

ROOT = Path(__file__).resolve().parents[1]

EXAMPLE_TITLE = "Handoff summaries at the M-162 slice boundary"

BY = "Volmarr"
ON = "2026-11-08"


def _handoff(**overrides):
    fields = {
        "handoff_id": "handoff-test",
        "title": "the test session, handed off at its close",
        "session_ref": "session-test",
        "project": "mythic-agent-coder",
        "branch": "work/parser-wiring",
        "done": ["m-100-parser-done"],
        "doing": ["m-163-handoffs-wiring"],
        "blocked": [],
        "needs_you": [],
        "evidence_refs": ["entry-test-1", "entry-test-2"],
        "written_by": BY,
        "written_on": ON,
        "source": "test source",
    }
    fields.update(overrides)
    return build_handoff(fields)


def _stored_handoff(handoff):
    stored = handoff.to_record()
    for key in ("type", "slice", "claim_count", "evidence_count"):
        stored.pop(key)
    return stored


def _stored_panel(panel):
    stored = panel.to_record()
    stored.pop("type")
    stored.pop("slice")
    for row in stored["rows"]:
        row.pop("type")
        row.pop("slice")
    return stored


def _stored_verdict(verdict):
    stored = verdict.to_record()
    stored.pop("type")
    stored.pop("slice")
    return stored


def _book(handoffs=None, **overrides):
    fields = {
        "title": "A test handoff book",
        "handoffs": [_stored_handoff(item) for item in (
            handoffs if handoffs is not None else [_handoff()])],
    }
    fields.update(overrides)
    return build_book(fields)


def _shipped_raw():
    path = ROOT / "mythic_agent" / "data" / "handoff_summaries.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_constants_and_usage():
    assert HANDOFF_SUMMARIES_SLICE == "M-163"
    assert HANDOFF_SUMMARIES_SCHEMA == "mythic.handoff_summaries/1"
    assert HANDOFF_SUMMARIES_RESOURCE == "handoff_summaries.yaml"
    assert CLAIM_KINDS == ("done", "doing", "blocked", "needs_you")
    assert "where things stand" in PLAIN_EXPLANATION
    assert "stand-up in durable" in PLAIN_EXPLANATION
    assert "disagree with" in PLAIN_EXPLANATION
    assert "sends nothing" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /handoffsummary")
    assert "handoff <handoff-id>" in USAGE


def test_roadmap_boundary_is_derived_from_the_shipped_roadmap():
    road = load_roadmap()
    ids = [item.id for item in road.slices]
    assert "M-163" in ids
    mine = road.slices[ids.index("M-163")]
    assert mine.title == "Handoff summaries"
    assert mine.part == 7
    assert "where things stand" in mine.summary
    assert "stand-up" in mine.summary
    assert "durable form" in mine.summary
    for earlier in road.slices[:ids.index("M-163")]:
        assert earlier.status == "done", earlier.id


def test_shipped_example_shape():
    book = load_handoff_summaries()
    assert isinstance(book, HandoffBook)
    assert book.title == EXAMPLE_TITLE
    assert book.handoff_ids() == (
        "handoff-main-close", "handoff-graph-pause",
        "handoff-thrift-close")
    assert book.total_handoffs == 3
    first = book.handoffs[0]
    assert first.title == (
        "the endurance day, handed off on the main line")
    assert first.branch == "main"
    assert first.session_ref == "session-m161-endurance"
    assert first.claim_count == 4
    assert first.evidence_count == 2
    assert first.written_by == "Volmarr"
    assert first.written_on == "2026-11-08"
    assert len(book.panels) == 1


def test_shipped_panel_is_pinned_and_derived():
    book = load_handoff_summaries()
    panel = book.panel_for("panel-m162-boundary")
    derived = derive_panel(book)
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert [row.handoff_id for row in panel.rows] == [
        "handoff-main-close", "handoff-graph-pause",
        "handoff-thrift-close"]
    assert panel.total_handoffs == 3
    assert panel.total_claims == 7
    assert panel.total_evidence == 6


def test_shipped_verdict_names_what_needs_you():
    book = load_handoff_summaries()
    verdict = derive_verdict(book)
    assert verdict.verdict == "awaiting-you"
    assert verdict.total_needs_you == 1
    assert verdict.total_blocked == 1
    assert verdict.distinct_sessions == 3
    assert total_claims(book) == 7
    assert total_evidence(book) == 6
    claims = [claim for handoff in book.handoffs
              for kind in CLAIM_KINDS
              for claim in handoff.section(kind)]
    assert len(claims) == len(set(claims))


def test_normalizers_and_aliases():
    assert normalize_claim_kind("Finished") == "done"
    assert normalize_claim_kind("IN_PROGRESS") == "doing"
    assert normalize_claim_kind("stuck") == "blocked"
    assert normalize_claim_kind("Needs_Human") == "needs_you"
    assert normalize_claim_kind("needs-you") == "needs_you"
    with pytest.raises(ValueError):
        normalize_claim_kind("sleeping")
    with pytest.raises(ValueError):
        _handoff(branch="work/bad branch")
    with pytest.raises(ValueError):
        _handoff(branch="/leading-slash")
    with pytest.raises(ValueError):
        _handoff(branch="double//slash")


def test_handoff_validation_and_alias_spellings():
    handoff = _handoff()
    assert isinstance(handoff, HandoffSummary)
    assert handoff.claim_count == 2
    assert handoff.counts() == {
        "done": 1, "doing": 1, "blocked": 0, "needs_you": 0}
    aliased = build_handoff({
        "name": "the aliased handoff", "session": "session-alias",
        "project": "other-project", "branch": "work/alias",
        "done": [], "doing": ["m-200-alias-doing"], "blocked": [],
        "needs": ["m-200-alias-needs"],
        "evidence": ["entry-alias-1"],
        "author": "Volmarr", "day": "2026-11-08",
        "source": "the alias test"})
    assert aliased.title == "the aliased handoff"
    assert aliased.session_ref == "session-alias"
    assert aliased.needs_you == ("m-200-alias-needs",)
    assert aliased.evidence_refs == ("entry-alias-1",)
    with pytest.raises(ValueError):
        build_handoff({"title": "the bare writing"})
    with pytest.raises(ValueError):
        _handoff(written_on="08/11/2026")
    with pytest.raises(ValueError):
        _handoff(written_on="2026-13-01")


def test_handoff_refuses_missing_provenance():
    fields = _stored_handoff(_handoff())
    fields.pop("written_by")
    with pytest.raises(ValueError, match="missing its"):
        build_handoff(fields)
    fields = _stored_handoff(_handoff())
    fields.pop("source")
    with pytest.raises(ValueError, match="missing its"):
        build_handoff(fields)
    fields = _stored_handoff(_handoff())
    fields["bogus"] = "nope"
    with pytest.raises(ValueError, match="unknown handoff keys"):
        build_handoff(fields)


def test_handoff_refuses_claim_and_evidence_problems():
    with pytest.raises(ValueError, match="at least one claim"):
        _handoff(done=[], doing=[], blocked=[], needs_you=[])
    with pytest.raises(ValueError, match="two sections"):
        _handoff(blocked=["m-100-parser-done"])
    with pytest.raises(ValueError, match="twice"):
        _handoff(done=["m-100-parser-done", "m-100-parser-done"])
    with pytest.raises(ValueError, match="at least one evidence"):
        _handoff(evidence_refs=[])
    with pytest.raises(ValueError, match="twice"):
        _handoff(evidence_refs=["entry-test-1", "entry-test-1"])
    fields = _stored_handoff(_handoff())
    fields.pop("evidence_refs")
    with pytest.raises(ValueError, match="missing its evidence"):
        build_handoff(fields)
    fields = _stored_handoff(_handoff())
    fields.pop("branch")
    with pytest.raises(ValueError, match="missing its branch"):
        build_handoff(fields)


def test_book_refuses_duplicates_and_double_handoff():
    with pytest.raises(ValueError, match="already exists"):
        _book([_handoff(), _handoff(title="another title")])
    # One handoff per session: a second handoff
    # ending a held session refuses under any id.
    with pytest.raises(ValueError, match="ends once"):
        _book([_handoff(), _handoff(
            handoff_id="handoff-copy", title="the copy handoff",
            done=["m-101-copy-done"], doing=[],
            evidence_refs=["entry-copy-1"])])
    # A claim is handed off once: one claim in two
    # handoffs refuses, naming both sessions.
    with pytest.raises(ValueError, match="handed off twice"):
        _book([_handoff(), _handoff(
            handoff_id="handoff-copy", session_ref="session-copy",
            done=["m-100-parser-done"], doing=[],
            evidence_refs=["entry-copy-1"])])
    # Distinct sessions with distinct claims stand
    # together in one book.
    book = _book([_handoff(), _handoff(
        handoff_id="handoff-second", session_ref="session-second",
        branch="work/second", done=[], doing=["m-102-second-doing"],
        evidence_refs=["entry-second-1"])])
    assert book.total_handoffs == 2


def test_handoff_for_session_in_book():
    book = load_handoff_summaries()
    handoff = book.handoff_for_session("session-m152-graph")
    assert handoff.handoff_id == "handoff-graph-pause"
    assert isinstance(
        book.handoff_for("handoff-thrift-close"), HandoffSummary)
    with pytest.raises(KeyError):
        book.handoff_for_session("session-nope")
    with pytest.raises(KeyError):
        book.handoff_for("handoff-nope")


def test_composition_from_stand_up():
    report = load_stand_up()
    digest = digest_stand_up(report)
    handoff = handoff_from_stand_up(
        report, session_ref="session-m134-standup",
        project="mythic-agent-coder", branch="work/standup-care",
        evidence_refs=["entry-standup-1"],
        written_by=BY, written_on=ON)
    assert handoff.done == digest.done
    assert handoff.doing == digest.doing
    assert handoff.blocked == digest.blocked
    assert handoff.needs_you == digest.needs_you
    assert handoff.title == "handoff at the M-133 boundary"
    assert validate_handoff(handoff, report) == handoff
    blob = str(handoff.to_record())
    for entry in report.entries:
        assert entry.title not in blob
        assert entry.detail not in blob
    # A handoff whose claims disagree with its
    # evidence is refused.
    tampered = _handoff(done=list(digest.done), doing=[], blocked=[],
                        needs_you=[])
    with pytest.raises(ValueError, match="disagree with its evidence"):
        validate_handoff(tampered, report)
    with pytest.raises(ValueError, match="branch"):
        handoff_from_stand_up(
            report, session_ref="session-x", project="mythic-agent-coder",
            branch=None, evidence_refs=["entry-x-1"],
            written_by=BY, written_on=ON)


def test_composition_from_session_situation():
    situation = load_session_memory().situations[0]
    handoff = handoff_from_session_situation(
        situation, project="mythic-agent-coder",
        branch="work/graph-care", doing=["m-153-memory-next"],
        written_by=BY, written_on=ON)
    assert handoff.session_ref == situation.session_ref
    # The evidence is the ids the situation itself
    # names: 3 memory notes, 2 open slices and 2
    # standing decisions of the shipped situation.
    assert handoff.evidence_count == 7
    assert "note-connected-code" in handoff.evidence_refs
    assert "M-153" in handoff.evidence_refs
    assert "decision-no-docker" in handoff.evidence_refs
    blob = str(handoff.to_record())
    assert situation.title not in blob
    assert situation.workspace not in blob
    with pytest.raises(ValueError, match="branch"):
        handoff_from_session_situation(
            situation, project="mythic-agent-coder", branch=None,
            doing=["m-153-memory-next"], written_by=BY, written_on=ON)


def test_composition_from_parallel_session():
    book = load_multi_session_projects()
    session = book.sessions[3]
    handoff = handoff_from_parallel_session(
        session, done=["m-160-thrift-banked"])
    assert handoff.session_ref == session.session_ref
    assert handoff.project == session.project
    assert handoff.branch == session.branch
    assert handoff.evidence_refs == session.journal_entries
    assert handoff.written_by == session.recorded_by
    assert handoff.written_on == session.recorded_on
    blob = str(handoff.to_record())
    assert session.title not in blob


def test_composition_from_endurance_record():
    record = load_long_session_endurance().records[0]
    handoff = handoff_from_endurance_record(
        record, project="mythic-agent-coder",
        branch="work/endurance-care", done=["m-161-endurance-done"],
        evidence_refs=["entry-endurance-care-1"])
    assert handoff.session_ref == record.ref
    assert handoff.written_by == record.recorded_by
    assert handoff.written_on == record.recorded_on
    blob = str(handoff.to_record())
    assert record.subject not in blob
    with pytest.raises(ValueError, match="evidence"):
        handoff_from_endurance_record(
            record, project="mythic-agent-coder", branch="work/x",
            done=["m-161-endurance-done"], evidence_refs=None)


def test_inspect_handoff_source():
    report = load_stand_up()
    digest = digest_stand_up(report)
    seen = inspect_handoff_source(report)
    assert seen == {"claim_count": digest.total(), "boundary": "M-133"}
    situation = load_session_memory().situations[0]
    seen = inspect_handoff_source(situation)
    assert seen == {"session_ref": situation.session_ref,
                    "claim_count": None, "evidence_count": 7}
    session = load_multi_session_projects().sessions[0]
    seen = inspect_handoff_source(session)
    assert seen == {"session_ref": session.session_ref,
                    "claim_count": None, "evidence_count": 2}
    seen = inspect_handoff_source(_handoff())
    assert seen == {"session_ref": "session-test", "claim_count": 2,
                    "evidence_count": 2}
    with pytest.raises(ValueError, match="no shipped layer owns"):
        inspect_handoff_source(42)


def test_handoffs_from_multi_session_plural_road():
    multi_book = load_multi_session_projects()
    claims = {
        session.session_ref: {"done": [f"claim-{session.session_ref}-done"]}
        for session in multi_book.sessions}
    handoffs = handoffs_from_multi_session_book(
        multi_book, claims_by_session=claims,
        written_by=BY, written_on=ON)
    assert len(handoffs) == len(multi_book.sessions)
    assert handoffs[0].session_ref == multi_book.sessions[0].session_ref
    assert handoffs[0].evidence_refs == (
        multi_book.sessions[0].journal_entries)
    assert handoffs[0].branch == multi_book.sessions[0].branch
    assert handoffs[0].done == (
        f"claim-{multi_book.sessions[0].session_ref}-done",)
    blob = str([h.to_record() for h in handoffs])
    for session in multi_book.sessions:
        assert session.title not in blob
    # No claims named for a session refuses the
    # whole road - claims are carried, never invented.
    short = dict(claims)
    short.pop(multi_book.sessions[1].session_ref)
    with pytest.raises(ValueError, match="no claims are named"):
        handoffs_from_multi_session_book(
            multi_book, claims_by_session=short,
            written_by=BY, written_on=ON)
    with pytest.raises(ValueError, match="claims must be named"):
        handoffs_from_multi_session_book(
            multi_book, claims_by_session=None,
            written_by=BY, written_on=ON)


def test_panel_derivation_and_order():
    book = _book([
        _handoff(handoff_id="handoff-b", title="b handoff",
                 session_ref="session-b", branch="work/b",
                 done=["m-101-b-done"], doing=["m-102-b-doing"],
                 evidence_refs=["entry-b-1"]),
        _handoff(handoff_id="handoff-a", title="a handoff",
                 session_ref="session-a", branch="work/a",
                 done=["m-100-a-done"], doing=["m-106-a-doing"],
                 evidence_refs=["entry-a-1"]),
        _handoff(handoff_id="handoff-c", title="the c handoff",
                 session_ref="session-c", branch="work/c",
                 done=["m-103-c-done", "m-104-c-done"], doing=[],
                 evidence_refs=["entry-c-1", "entry-c-2"]),
    ])
    panel = derive_panel(book)
    assert isinstance(panel, HandoffPanel)
    # Panel order: project, then day, then branch,
    # then title, then handoff id.
    assert [r.handoff_id for r in panel.rows] == [
        "handoff-a", "handoff-b", "handoff-c"]
    assert panel.total_handoffs == 3
    assert panel.total_claims == 6
    assert panel.total_evidence == 4
    counts = {c.kind: c for c in panel.section_counts}
    assert counts["done"].claims == 4
    assert counts["doing"].claims == 2
    assert isinstance(counts["done"], SectionCount)
    assert panel.row_for("handoff-c").claim_count == 2
    with pytest.raises(KeyError):
        panel.row_for("handoff-nope")


def test_panel_refuses_disagreement_and_bad_rows():
    book = load_handoff_summaries()
    panel = derive_panel(book)
    stored = _stored_panel(panel)
    assert validate_panel(stored, book) == panel
    bad = _stored_panel(panel)
    bad["total_handoffs"] = 2
    with pytest.raises(ValueError):
        validate_panel(bad, book)
    bad = _stored_panel(panel)
    bad["account"] = ["A different account."]
    with pytest.raises(ValueError, match="disagrees"):
        validate_panel(bad, book)
    good_row = build_row(_stored_panel(panel)["rows"][0])
    assert isinstance(good_row, HandoffPanelRow)
    assert validate_row(good_row, book.handoffs[0]) == good_row
    bad_row = _stored_panel(panel)["rows"][0]
    bad_row["branch"] = "work/elsewhere"
    with pytest.raises(ValueError, match="disagrees"):
        validate_row(bad_row, book.handoffs[0])


def test_verdict_derivation_and_validation():
    book = _book([_handoff(), _handoff(
        handoff_id="handoff-second", session_ref="session-second",
        branch="work/second", done=[], doing=["m-102-second-doing"],
        blocked=["m-105-second-blocked"],
        evidence_refs=["entry-second-1"])])
    verdict = derive_verdict(book)
    assert isinstance(verdict, EvidenceVerdict)
    assert verdict.verdict == "held-up"
    assert verdict.total_blocked == 1
    assert verdict.total_needs_you == 0
    assert verdict.distinct_sessions == 2
    assert validate_verdict(_stored_verdict(verdict), book) == verdict
    assert build_verdict(_stored_verdict(verdict)) == verdict
    needs = derive_verdict(load_handoff_summaries())
    assert needs.verdict == "awaiting-you"
    clear = derive_verdict(_book([_handoff()]))
    assert clear.verdict == "standing-clear"
    with pytest.raises(ValueError, match="disagrees"):
        validate_verdict(_stored_verdict(clear), book)
    # A verdict whose word is not its own counts'
    # word refuses at construction.
    with pytest.raises(ValueError, match="verdict"):
        EvidenceVerdict(
            total_handoffs=2, total_claims=4, total_evidence=3,
            total_blocked=0, total_needs_you=1,
            distinct_sessions=2, verdict="standing-clear")
    with pytest.raises(ValueError, match="verdict"):
        EvidenceVerdict(
            total_handoffs=1, total_claims=2, total_evidence=2,
            total_blocked=1, total_needs_you=0,
            distinct_sessions=1, verdict="awaiting-you")


def test_book_validation_and_loader_roads(tmp_path):
    raw = _shipped_raw()
    assert validate_book(raw).title == EXAMPLE_TITLE
    assert build_book(raw).handoff_ids()[0] == "handoff-main-close"
    bad = dict(raw)
    bad["schema"] = "mythic.other/1"
    with pytest.raises(ValidationError):
        validate_book(bad)
    path = tmp_path / "handoff_summaries.yaml"
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    loaded = load_handoff_summaries_file(path)
    assert loaded.title == EXAMPLE_TITLE
    with pytest.raises(FileNotFoundError):
        load_handoff_summaries_file(tmp_path / "nope.yaml")
    assert _shipped_raw()["schema"] == HANDOFF_SUMMARIES_SCHEMA


def test_registry_holds_handoffs_one_by_one():
    registry = HandoffRegistry()
    held = registry.register_handoff(_handoff(handoff_id=None))
    assert held.handoff_id == "handoff-1"
    assert registry.latest_handoff() == held
    assert registry.get_handoff("handoff-1") == held
    assert registry.handoff_for_session("session-test") == held
    with pytest.raises(ValueError, match="already exists"):
        registry.register_handoff(held)
    with pytest.raises(ValueError, match="ends once"):
        registry.register_handoff(_handoff(
            handoff_id="handoff-copy", done=["m-101-copy-done"],
            doing=[], evidence_refs=["entry-copy-1"]))
    with pytest.raises(ValueError, match="handed off twice"):
        registry.register_handoff(_handoff(
            handoff_id="handoff-copy", session_ref="session-copy",
            doing=[], evidence_refs=["entry-copy-1"]))
    with pytest.raises(ValueError, match="no handoff book is held"):
        registry.book()
    assert registry.panel().total_handoffs == 1
    assert registry.verdict().verdict == "standing-clear"
    with pytest.raises(KeyError):
        registry.get_handoff("handoff-nope")


def test_registry_register_book_and_title_law():
    registry = HandoffRegistry()
    book = _book()
    held_book = registry.register_book(book)
    assert held_book.title == "A test handoff book"
    assert registry.list_handoffs()[0].handoff_id == "handoff-test"
    with pytest.raises(ValueError):
        registry.register_book(book)
    other = _book([_handoff(
        handoff_id="handoff-z", session_ref="session-z",
        branch="work/z", done=["m-109-z-done"], doing=[],
        evidence_refs=["entry-z-1"])], title="Another title")
    with pytest.raises(ValueError, match="different title"):
        registry.register_book(other)
    fresh = HandoffRegistry(load_handoff_summaries())
    assert fresh.book().total_handoffs == 3


def test_news_records_and_plain_words():
    handoff = _handoff()
    news = handoff_record(handoff)
    assert news["type"] == "handoff_summaries_handoff"
    assert news["news"] is True
    assert "work/parser-wiring" in news["headline"]
    book = load_handoff_summaries()
    panel_news = panel_record(derive_panel(book), book)
    assert panel_news["type"] == "handoff_summaries_panel"
    assert "3 handoffs" in panel_news["headline"]
    verdict_news = verdict_record(derive_verdict(book), book)
    assert verdict_news["type"] == "handoff_summaries_verdict"
    assert "awaiting-you" in verdict_news["headline"]
    whole = book_record(book)
    assert whole["type"] == "handoff_summaries_book"
    assert whole["handoff_count"] == 3
    words = plain_words(book.handoffs[0])
    assert "main" in words
    assert "Volmarr" in words
    panel_words = panel_plain_words(book)
    assert "handoff-graph-pause" in panel_words
    assert "derived, never stored loose" in panel_words
    verdict_words = verdict_plain_words(book)
    assert "awaiting-you" in verdict_words
    assert "needing your word" in verdict_words


def test_refs_and_totals_surface():
    book = load_handoff_summaries()
    refs = handoff_refs(book)
    assert refs[0] == ("session-m161-endurance", "main")
    assert ("session-m152-graph", "work/graph-retrieval-care") in refs
    assert len(refs) == 3
    assert validate_handoff(_stored_handoff(_handoff())) == _handoff()


def test_formatters_and_screen():
    book = load_handoff_summaries()
    block = format_handoff(book.handoffs[1])
    assert "entry-graph-1" in block
    assert "sends nothing" in block
    listing = format_handoffs(book)
    assert "handoff-main-close" in listing
    only = format_handoffs(book, "session-m161-endurance")
    assert "handoff-main-close" in only
    assert "handoff-graph-pause" not in only
    panel_text = format_panel(book)
    assert "Handoff panel in" in panel_text
    assert "derived, never stored loose" in panel_text
    verdict_text = format_verdict(book)
    assert "awaiting-you" in verdict_text
    screen = format_handoff_summaries_screen(book)
    assert "Handoff Summaries (M-163)" in screen
    assert USAGE in screen
    default_screen = format_handoff_summaries_screen()
    assert "handoff-main-close" in default_screen


def test_parse_handoffsummary_args():
    assert parse_handoffsummary_args("") == ("show", None)
    assert parse_handoffsummary_args("show") == ("show", None)
    assert parse_handoffsummary_args("list") == ("show", None)
    assert parse_handoffsummary_args(
        "handoff handoff-main-close") == (
        "handoff", "handoff-main-close")
    assert parse_handoffsummary_args(
        "session session-m161-endurance") == (
        "session", "session-m161-endurance")
    assert parse_handoffsummary_args("panel") == ("panel", None)
    assert parse_handoffsummary_args("verdict") == ("verdict", None)
    with pytest.raises(ValueError, match="Usage"):
        parse_handoffsummary_args("dance party")
    with pytest.raises(ValueError):
        parse_handoffsummary_args("session bad session")
    with pytest.raises(ValueError):
        parse_handoffsummary_args(42)
