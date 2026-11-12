"""M-252 Docs MCP pattern - pure-layer tests.

TIER: unit

Sessions, campaigns, memories and configs leave only as a
recorded record in an open format; an absent record reads
as unknown and a stale one as stale, never as a fact,
and this book only proposes export proposals - leaving is
as easy as arriving.
"""
import pytest

from mythic_agent.core.docs_mcp_pattern import (
    BARE_CLAIMS,
    ATTACH_SCOPES,
    FRESH_LIMIT_SECONDS,
    HELD_EVIDENCE,
    PROJECTS,
    STAGES,
    AttachmentDraft,
    AttachmentRecord,
    ProjectEntry,
    ProjectRegistry,
    default_registry,
    derive_standing,
    format_project,
    format_projects,
    format_record,
    prepare_proposal,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(project="mojo", record="attach-42",
                scope="full", title="Leave with everything",
                subject="Session 42 in mythic-coder",
                observed_at="2026-11-12T12:00:00", age_seconds=60,
                stages=STAGES, claims=("manifest_ref",))
    base.update(kw)
    return AttachmentRecord(**base)


def test_registry_holds_four_projects_open_only():
    reg = default_registry()
    assert reg.ids() == ("mojo", "python",
                         "rust", "generic")
    assert all(e.bridge == "recorded" for e in reg.entries())


def test_registry_unknown_project_refused_by_name():
    with pytest.raises(ValidationError, match="unknown docs project: guess"):
        default_registry().get("guess")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate docs project"):
        ProjectRegistry(PROJECTS + PROJECTS[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing label"):
        ProjectRegistry([ProjectEntry("x", "", "thing", "JSON", "open", "why")])


def test_entry_proprietary_format_refused():
    with pytest.raises(ValidationError, match="recorded data only"):
        ProjectRegistry([ProjectEntry("x", "X", "thing", "remote_mcp", "live", "why")])


def test_project_words_and_formats_differ_by_project():
    reg = default_registry()
    assert reg.get("mojo").item_word == "doc"
    assert reg.get("python").item_word == "reference"
    assert reg.get("rust").item_word == "doc"
    assert reg.get("generic").item_word == "page"
    assert reg.get("mojo").transport == "remote_mcp"
    assert reg.get("python").transport == "remote_mcp"
    assert reg.get("rust").transport == "stdio_mcp"
    assert reg.get("generic").transport == "recorded_mcp"


def test_fresh_held_record_stands_held():
    standing = derive_standing(fresh_record())
    assert standing.held and standing.stage == "held"
    assert standing.freshness == "current" and standing.gaps == ()


def test_bare_claims_only_stands_open():
    standing = derive_standing(fresh_record(claims=("assertion",)))
    assert not standing.held
    assert any("bare claims" in g for g in standing.gaps)


def test_no_evidence_stands_open():
    standing = derive_standing(fresh_record(claims=()))
    assert not standing.held
    assert any("no held evidence" in g for g in standing.gaps)


def test_unfinished_walk_stands_open():
    standing = derive_standing(fresh_record(stages=("named", "described")))
    assert not standing.held and standing.stage == "described"


def test_walk_must_open_at_listed():
    standing = derive_standing(
        fresh_record(stages=("described", "checked", "held")))
    assert not standing.held
    assert any("open at named" in g for g in standing.gaps)


def test_walk_rejects_skipped_stage():
    standing = derive_standing(
        fresh_record(stages=("named", "checked", "held")))
    assert not standing.held
    assert any("not in the walk" in g for g in standing.gaps)


def test_stale_record_stands_open_as_stale():
    standing = derive_standing(
        fresh_record(age_seconds=FRESH_LIMIT_SECONDS + 1))
    assert not standing.held and standing.freshness == "stale"
    assert any("stale" in g for g in standing.gaps)
    fresh = derive_standing(
        fresh_record(age_seconds=FRESH_LIMIT_SECONDS))
    assert fresh.held and fresh.freshness == "current"


def test_unknown_scope_or_no_subject_stands_open():
    standing = derive_standing(fresh_record(scope="unknown"))
    assert not standing.held
    assert any("scope" in g for g in standing.gaps)
    standing = derive_standing(fresh_record(subject=""))
    assert not standing.held
    assert any("subject" in g for g in standing.gaps)


def test_record_unknown_project_and_missing_fields_refused():
    with pytest.raises(ValidationError, match="unknown docs project"):
        derive_standing(fresh_record(project="guess"))
    with pytest.raises(ValidationError, match="no record"):
        fresh_record(record=" ").validate()
    with pytest.raises(ValidationError, match="no observed time"):
        fresh_record(observed_at="").validate()


def test_record_scope_words_must_be_known():
    with pytest.raises(ValidationError, match="unknown attachment record scope"):
        fresh_record(scope="green").validate()
    for scope in ATTACH_SCOPES:
        fresh_record(scope=scope).validate()


def test_record_claim_project_and_age_must_be_known():
    with pytest.raises(ValidationError, match="unknown attachment evidence kind"):
        fresh_record(claims=("vibes",)).validate()
    for project in HELD_EVIDENCE + BARE_CLAIMS:
        fresh_record(claims=(project,)).validate()
    with pytest.raises(ValidationError, match="non-negative"):
        fresh_record(age_seconds=-1).validate()


def test_proposal_defaults_to_ready_state():
    proposal = prepare_proposal("mythic-coder", "mojo", "attach-42",
                          "export the session")
    assert proposal.state == "ready" and proposal.attached is False


def test_proposal_locked_or_gated_state_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_proposal("b", "mojo", "export-1", "x", state="locked")
    shared = prepare_proposal("b", "mojo", "export-1", "x", state="shared")
    assert shared.state == "shared" and shared.attached is False


def test_proposal_never_attached_and_format_lines():
    with pytest.raises(ValidationError, match="never attached"):
        AttachmentDraft("b", "mojo", "export-1", "x", attached=True).validate()
    with pytest.raises(ValidationError, match="no bridge"):
        prepare_proposal(" ", "mojo", "export-1", "x")
    with pytest.raises(ValidationError, match="no record"):
        prepare_proposal("b", "mojo", " ", "x")
    with pytest.raises(ValidationError, match="proposes nothing"):
        prepare_proposal("b", "mojo", "export-1", " ")
    reg = default_registry()
    assert "Mojo Docs" in format_project(reg.get("mojo"))
    assert "recorded knowledge bridge" in format_project(reg.get("generic"))
    assert format_projects(reg).count("\n") == 3
    line = format_record(fresh_record())
    assert "held as bridge" in line and "attach-42" in line
    open_line = format_record(fresh_record(claims=()))
    assert "open:" in open_line


