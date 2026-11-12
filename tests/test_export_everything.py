"""M-251 Export everything - pure-layer tests.

TIER: unit

Sessions, campaigns, memories and configs leave only as a
recorded record in an open format; an absent record reads
as unknown and a stale one as stale, never as a fact,
and this book only prepares export drafts - leaving is
as easy as arriving.
"""
import pytest

from mythic_agent.core.export_everything import (
    BARE_CLAIMS,
    RECORD_SCOPES,
    FRESH_LIMIT_SECONDS,
    HELD_EVIDENCE,
    KINDS,
    STAGES,
    ExportDraft,
    ExportRecord,
    KindEntry,
    KindRegistry,
    default_registry,
    derive_standing,
    format_kind,
    format_kinds,
    format_record,
    prepare_draft,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(kind="sessions", record="export-42",
                scope="full", title="Leave with everything",
                subject="Session 42 in mythic-coder",
                observed_at="2026-11-12T12:00:00", age_seconds=60,
                stages=STAGES, claims=("content_ref",))
    base.update(kw)
    return ExportRecord(**base)


def test_registry_holds_four_kinds_open_only():
    reg = default_registry()
    assert reg.ids() == ("sessions", "campaigns",
                         "memories", "configs")
    assert all(e.openness == "open" for e in reg.entries())


def test_registry_unknown_kind_refused_by_name():
    with pytest.raises(ValidationError, match="unknown export kind: guess"):
        default_registry().get("guess")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate export kind"):
        KindRegistry(KINDS + KINDS[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing label"):
        KindRegistry([KindEntry("x", "", "thing", "JSON", "open", "why")])


def test_entry_proprietary_format_refused():
    with pytest.raises(ValidationError, match="open formats only"):
        KindRegistry([KindEntry("x", "X", "thing", "LockedBin", "locked", "why")])


def test_kind_words_and_formats_differ_by_kind():
    reg = default_registry()
    assert reg.get("sessions").item_word == "session"
    assert reg.get("campaigns").item_word == "campaign"
    assert reg.get("memories").item_word == "memory"
    assert reg.get("configs").item_word == "config"
    assert reg.get("sessions").format_name == "JSON"
    assert reg.get("campaigns").format_name == "Markdown"
    assert reg.get("memories").format_name == "Markdown"
    assert reg.get("configs").format_name == "YAML"


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
    standing = derive_standing(fresh_record(stages=("listed", "gathered")))
    assert not standing.held and standing.stage == "gathered"


def test_walk_must_open_at_listed():
    standing = derive_standing(
        fresh_record(stages=("gathered", "checked", "held")))
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


def test_record_unknown_kind_and_missing_fields_refused():
    with pytest.raises(ValidationError, match="unknown export kind"):
        derive_standing(fresh_record(kind="guess"))
    with pytest.raises(ValidationError, match="no record"):
        fresh_record(record=" ").validate()
    with pytest.raises(ValidationError, match="no observed time"):
        fresh_record(observed_at="").validate()


def test_record_scope_words_must_be_known():
    with pytest.raises(ValidationError, match="unknown export record scope"):
        fresh_record(scope="green").validate()
    for scope in RECORD_SCOPES:
        fresh_record(scope=scope).validate()


def test_record_claim_kind_and_age_must_be_known():
    with pytest.raises(ValidationError, match="unknown export evidence kind"):
        fresh_record(claims=("vibes",)).validate()
    for kind in HELD_EVIDENCE + BARE_CLAIMS:
        fresh_record(claims=(kind,)).validate()
    with pytest.raises(ValidationError, match="non-negative"):
        fresh_record(age_seconds=-1).validate()


def test_draft_defaults_to_ready_state():
    draft = prepare_draft("mythic-coder", "sessions", "export-42",
                          "export the session")
    assert draft.state == "ready" and draft.exported is False


def test_draft_locked_or_gated_state_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_draft("b", "sessions", "export-1", "x", state="locked")
    shared = prepare_draft("b", "sessions", "export-1", "x", state="shared")
    assert shared.state == "shared" and shared.exported is False


def test_draft_never_exported_and_format_lines():
    with pytest.raises(ValidationError, match="never exported"):
        ExportDraft("b", "sessions", "export-1", "x", exported=True).validate()
    with pytest.raises(ValidationError, match="no bundle"):
        prepare_draft(" ", "sessions", "export-1", "x")
    with pytest.raises(ValidationError, match="no record"):
        prepare_draft("b", "sessions", " ", "x")
    with pytest.raises(ValidationError, match="drafts nothing"):
        prepare_draft("b", "sessions", "export-1", " ")
    reg = default_registry()
    assert "Sessions" in format_kind(reg.get("sessions"))
    assert "via open" in format_kind(reg.get("configs"))
    assert format_kinds(reg).count("\n") == 3
    line = format_record(fresh_record())
    assert "held as open" in line and "export-42" in line
    open_line = format_record(fresh_record(claims=()))
    assert "open:" in open_line
