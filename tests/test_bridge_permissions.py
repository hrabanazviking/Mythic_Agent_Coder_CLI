"""M-253 Bridge permissions audit - pure-layer tests.

TIER: unit

Sessions, campaigns, memories and configs leave only as a
recorded record in an open format; an absent record reads
as unknown and a stale one as stale, never as a fact,
and this book only reports export reports - leaving is
as easy as arriving.
"""
import pytest

from mythic_agent.core.bridge_permissions import (
    BARE_CLAIMS,
    AUDIT_SCOPES,
    FRESH_LIMIT_SECONDS,
    HELD_EVIDENCE,
    BRIDGES,
    STAGES,
    AuditDraft,
    AuditRecord,
    BridgeEntry,
    BridgeRegistry,
    default_registry,
    derive_standing,
    format_bridge,
    format_bridges,
    format_record,
    prepare_report,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(bridge="github", record="audit-42",
                scope="full", title="Leave with everything",
                subject="Session 42 in mythic-coder",
                observed_at="2026-11-12T12:00:00", age_seconds=60,
                stages=STAGES, claims=("kista_ref",))
    base.update(kw)
    return AuditRecord(**base)


def test_registry_holds_four_bridges_open_only():
    reg = default_registry()
    assert reg.ids() == ("github", "gitlab",
                         "samverk", "samtal")
    assert all(e.standing == "listed" for e in reg.entries())


def test_registry_unknown_bridge_refused_by_name():
    with pytest.raises(ValidationError, match="unknown bridge: guess"):
        default_registry().get("guess")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate bridge"):
        BridgeRegistry(BRIDGES + BRIDGES[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing label"):
        BridgeRegistry([BridgeEntry("x", "", "thing", "JSON", "open", "why")])


def test_entry_proprietary_format_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        BridgeRegistry([BridgeEntry("x", "X", "thing", "remote_mcp", "live", "why")])


def test_bridge_words_and_formats_differ_by_bridge():
    reg = default_registry()
    assert reg.get("github").item_word == "key"
    assert reg.get("gitlab").item_word == "key"
    assert reg.get("samverk").item_word == "ref"
    assert reg.get("samtal").item_word == "ref"
    assert reg.get("github").key_home == "kista:github"
    assert reg.get("gitlab").key_home == "kista:gitlab"
    assert reg.get("samverk").key_home == "kista:samverk"
    assert reg.get("samtal").key_home == "kista:samtal"


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
    standing = derive_standing(fresh_record(stages=("listed", "scoped")))
    assert not standing.held and standing.stage == "scoped"


def test_walk_must_open_at_listed():
    standing = derive_standing(
        fresh_record(stages=("scoped", "checked", "held")))
    assert not standing.held
    assert any("open at listed" in g for g in standing.gaps)


def test_walk_rejects_skipped_stage():
    standing = derive_standing(
        fresh_record(stages=("listed", "checked", "held")))
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


def test_record_unknown_bridge_and_missing_fields_refused():
    with pytest.raises(ValidationError, match="unknown bridge"):
        derive_standing(fresh_record(bridge="guess"))
    with pytest.raises(ValidationError, match="no record"):
        fresh_record(record=" ").validate()
    with pytest.raises(ValidationError, match="no observed time"):
        fresh_record(observed_at="").validate()


def test_record_scope_words_must_be_known():
    with pytest.raises(ValidationError, match="unknown audit record scope"):
        fresh_record(scope="green").validate()
    for scope in AUDIT_SCOPES:
        fresh_record(scope=scope).validate()


def test_record_claim_bridge_and_age_must_be_known():
    with pytest.raises(ValidationError, match="unknown audit evidence kind"):
        fresh_record(claims=("vibes",)).validate()
    for bridge in HELD_EVIDENCE + BARE_CLAIMS:
        fresh_record(claims=(bridge,)).validate()
    with pytest.raises(ValidationError, match="non-negative"):
        fresh_record(age_seconds=-1).validate()


def test_report_defaults_to_ready_state():
    report = prepare_report("mythic-coder", "github", "audit-42",
                          "audit the bridge permissions")
    assert report.state == "ready" and report.granted is False


def test_report_locked_or_gated_state_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report("b", "github", "export-1", "x", state="locked")
    shared = prepare_report("b", "github", "export-1", "x", state="shared")
    assert shared.state == "shared" and shared.granted is False


def test_report_never_granted_and_format_lines():
    with pytest.raises(ValidationError, match="never a grant"):
        AuditDraft("b", "github", "export-1", "x", granted=True).validate()
    with pytest.raises(ValidationError, match="no bridge"):
        prepare_report(" ", "github", "export-1", "x")
    with pytest.raises(ValidationError, match="no record"):
        prepare_report("b", "github", " ", "x")
    with pytest.raises(ValidationError, match="reports nothing"):
        prepare_report("b", "github", "export-1", " ")
    reg = default_registry()
    assert "GitHub Bridge" in format_bridge(reg.get("github"))
    assert "audit standing listed" in format_bridge(reg.get("samtal"))
    assert format_bridges(reg).count("\n") == 3
    line = format_record(fresh_record())
    assert "held as audited" in line and "audit-42" in line
    open_line = format_record(fresh_record(claims=()))
    assert "open:" in open_line

