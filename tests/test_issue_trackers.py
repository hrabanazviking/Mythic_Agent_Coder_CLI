"""M-248 Issue trackers beyond git hosts - pure-layer tests.

TIER: unit

Issues enter the session as facts only when they rest on
held evidence; trackers are MCP-first and read-mostly, and
any write is proposed only as a draft, by approval.
"""
import pytest

from mythic_agent.core.issue_trackers import (
    BARE_CLAIMS,
    HELD_EVIDENCE,
    ISSUE_STATES,
    STAGES,
    TRACKERS,
    IssueRecord,
    TrackerEntry,
    TrackerRegistry,
    WriteDraft,
    default_registry,
    derive_standing,
    format_record,
    format_tracker,
    format_trackers,
    propose_write,
)
from mythic_agent.core.validation import ValidationError


def held_record(**kw):
    base = dict(tracker="linear", issue_key="ENG-1",
                title="Fix the bridge", state="open",
                stages=STAGES, claims=("issue_ref",))
    base.update(kw)
    return IssueRecord(**base)


def test_registry_holds_three_trackers_mcp_first():
    reg = default_registry()
    assert reg.ids() == ("linear", "jira", "generic_mcp")
    assert all(e.transport == "mcp" for e in reg.entries())


def test_registry_unknown_tracker_refused_by_name():
    with pytest.raises(ValidationError, match="unknown issue tracker: asana"):
        default_registry().get("asana")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate issue tracker"):
        TrackerRegistry(TRACKERS + TRACKERS[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing label"):
        TrackerRegistry([TrackerEntry("x", "", "issue", "mcp", "why")])


def test_entry_non_mcp_transport_refused():
    with pytest.raises(ValidationError, match="MCP-first"):
        TrackerRegistry([TrackerEntry("x", "X", "issue", "rest", "why")])


def test_tracker_words_differ_by_tracker():
    reg = default_registry()
    assert reg.get("linear").issue_word == "issue"
    assert reg.get("jira").issue_word == "ticket"
    assert reg.get("generic_mcp").issue_word == "work item"


def test_held_record_stands_held():
    standing = derive_standing(held_record())
    assert standing.held and standing.stage == "held" and standing.gaps == ()


def test_bare_claims_only_stands_open():
    standing = derive_standing(held_record(claims=("assertion",)))
    assert not standing.held
    assert any("bare claims" in g for g in standing.gaps)


def test_no_evidence_stands_open():
    standing = derive_standing(held_record(claims=()))
    assert not standing.held
    assert any("no held evidence" in g for g in standing.gaps)


def test_unfinished_walk_stands_open():
    standing = derive_standing(held_record(stages=("seen", "fetched")))
    assert not standing.held and standing.stage == "fetched"


def test_walk_must_open_at_seen():
    standing = derive_standing(held_record(stages=("fetched", "read", "held")))
    assert not standing.held
    assert any("open at seen" in g for g in standing.gaps)


def test_walk_rejects_skipped_stage():
    standing = derive_standing(held_record(stages=("seen", "read", "held")))
    assert not standing.held
    assert any("not in the walk" in g for g in standing.gaps)


def test_record_unknown_tracker_refused():
    with pytest.raises(ValidationError, match="unknown issue tracker"):
        derive_standing(held_record(tracker="asana"))


def test_record_names_issue_and_title():
    with pytest.raises(ValidationError, match="no issue"):
        held_record(issue_key=" ").validate()
    with pytest.raises(ValidationError, match="no title"):
        held_record(title="").validate()


def test_record_state_must_be_known():
    with pytest.raises(ValidationError, match="unknown issue state"):
        held_record(state="green").validate()
    for state in ISSUE_STATES:
        held_record(state=state).validate()


def test_record_claim_kind_must_be_known():
    with pytest.raises(ValidationError, match="unknown issue evidence kind"):
        held_record(claims=("vibes",)).validate()
    for kind in HELD_EVIDENCE + BARE_CLAIMS:
        held_record(claims=(kind,)).validate()


def test_write_draft_defaults_to_pending_approval():
    draft = propose_write("linear", "ENG-1", "close as done")
    assert draft.approval == "pending" and draft.applied is False


def test_write_unapproved_execution_refused():
    with pytest.raises(ValidationError, match="by approval only"):
        propose_write("linear", "ENG-1", "x", approval="executed")
    approved = propose_write("jira", "OPS-2", "x", approval="approved")
    assert approved.approval == "approved" and approved.applied is False


def test_write_draft_never_applied():
    with pytest.raises(ValidationError, match="drafts only"):
        WriteDraft("linear", "ENG-1", "x", applied=True).validate()
    with pytest.raises(ValidationError, match="no issue"):
        propose_write("linear", " ", "x")
    with pytest.raises(ValidationError, match="no change"):
        propose_write("linear", "ENG-1", " ")


def test_format_lines():
    reg = default_registry()
    assert "Linear" in format_tracker(reg.get("linear"))
    assert "via mcp" in format_tracker(reg.get("jira"))
    assert format_trackers(reg).count("\n") == 2
    line = format_record(held_record())
    assert "held as fact" in line and "ENG-1" in line
    open_line = format_record(held_record(claims=()))
    assert "open:" in open_line
