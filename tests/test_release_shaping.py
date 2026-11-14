"""M-269 Release shaping - pure-layer tests.

TIER: unit

Proven, shaping or NOT READY per feature release, in the
release itself: a release counts READY only on held proof
measured in the release itself resting on held evidence,
a shaping release only where the ready part rests on held
evidence and the rest is owned in the open, and a not
ready release only with its owner and reason recorded -
an unready release admitted in the open is honest.
"""
import pytest

from mythic_agent.core.release_shaping import (
    RELEASES,
    BARE_CLAIMS,
    DISPOSITIONS,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    STAGES,
    ReleaseShapingEntry,
    ReleaseShapingRegistry,
    ReleaseShapingRecord,
    default_registry,
    derive_standing,
    derive_verdict,
    format_release,
    format_releases,
    format_record,
    format_records,
    prepare_report,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(release="R-03",
                work="release-2026-11-a",
                date="2026-11-13", disposition="READY",
                owner="yrsa",
                proof_kind="ready-and-held",
                stages=STAGES,
                claims=("evidence_ref", "test_ref"))
    base.update(kw)
    return ReleaseShapingRecord(**base)


def shaping_record(**kw):
    base = dict(release="R-05",
                work="release-2026-11-a",
                date="2026-11-13", disposition="SHAPING",
                owner="yrsa",
                proof_kind="partially-held",
                stages=STAGES,
                claims=("test_ref",))
    base.update(kw)
    return ReleaseShapingRecord(**base)


def not_ready_record(**kw):
    base = dict(release="R-07",
                work="release-2026-11-a",
                date="2026-11-13", disposition="NOT_READY",
                owner="yrsa",
                proof_kind="none",
                stages=STAGES,
                claims=("test_ref",))
    base.update(kw)
    return ReleaseShapingRecord(**base)


def full_book(**overrides):
    records = []
    for release_id in default_registry().combinations():
        if release_id in ("R-01", "R-02", "R-03"):
            kw = dict(release=release_id, work="release-2026-11-a",
                      date="2026-11-13", disposition="READY",
                      owner="yrsa",
                      proof_kind="ready-and-held",
                      stages=STAGES,
                      claims=("evidence_ref", "test_ref"))
        elif release_id in ("R-04", "R-05", "R-06", "R-07"):
            kw = dict(release=release_id, work="release-2026-11-a",
                      date="2026-11-13", disposition="SHAPING",
                      owner="yrsa",
                      proof_kind="partially-held",
                      stages=STAGES,
                      claims=("test_ref",))
        else:
            kw = dict(release=release_id, work="release-2026-11-a",
                      date="2026-11-13", disposition="NOT_READY",
                      owner="yrsa",
                      proof_kind="none",
                      stages=STAGES,
                      claims=("test_ref",))
        kw.update(overrides.get(release_id, {}))
        records.append(ReleaseShapingRecord(**kw))
    return records


def test_registry_holds_twelve_releases_listed_only():
    reg = default_registry()
    assert len(reg.ids()) == 12
    assert reg.ids()[0] == "R-01"
    assert reg.ids()[-1] == "R-12"
    assert all(e.standing == "listed" for e in reg.entries())
    assert len(reg.combinations()) == 12


def test_registry_releases_cover_the_doctrine_sources():
    reg = default_registry()
    pairs = {(e.doctrine, e.subject) for e in reg.entries()}
    assert len(pairs) == 12
    assert reg.get("R-01").doctrine == "version-truth"
    assert reg.get("R-01").subject == "version-number"
    assert reg.get("R-02").subject == "release-notes-shape"
    assert reg.get("R-03").subject == "readiness-gate"
    assert reg.get("R-04").subject == "release-shape"
    assert reg.get("R-11").doctrine == "version-truth"
    assert reg.get("R-11").subject == "install-shape"
    assert reg.get("R-12").doctrine == "release-duty"
    assert DISPOSITIONS == ("READY", "SHAPING", "NOT_READY")


def test_registry_unknown_release_refused_by_name():
    with pytest.raises(ValidationError, match="unknown release: C-99"):
        default_registry().get("C-99")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate release"):
        ReleaseShapingRegistry(RELEASES + RELEASES[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing reason"):
        ReleaseShapingRegistry([ReleaseShapingEntry("R-01", "version-truth", "version-number", "listed", "")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        ReleaseShapingRegistry([ReleaseShapingEntry("R-01", "version-truth", "version-number", "published", "why")])
    with pytest.raises(ValidationError, match="labelled"):
        ReleaseShapingRegistry([ReleaseShapingEntry("R-01", "version-truth", "version-number", "listed", "why", labelled=False)])
    with pytest.raises(ValidationError, match="evidenced"):
        ReleaseShapingRegistry([ReleaseShapingEntry("R-01", "version-truth", "version-number", "listed", "why", evidenced=False)])


def test_entry_unknown_doctrine_refused():
    with pytest.raises(ValidationError, match="unknown release doctrine"):
        ReleaseShapingRegistry([ReleaseShapingEntry("R-01", "M-999", "version-number", "listed", "why")])


def test_record_ready_measured_and_held_stands_held():
    standing = derive_standing(fresh_record())
    assert standing.held
    assert standing.grade == "held"
    assert standing.gaps == ()


def test_record_incomplete_walk_stands_open():
    standing = derive_standing(fresh_record(stages=STAGES[:3]))
    assert not standing.held
    assert any("not held" in g for g in standing.gaps)


def test_record_bad_stage_step_stands_open():
    bad = ("named", "evidenced", "dispositioned", "held")
    standing = derive_standing(fresh_record(stages=bad))
    assert not standing.held
    assert any("not in the walk" in g for g in standing.gaps)


def test_record_ready_on_shaping_proof_stands_open():
    standing = derive_standing(fresh_record(proof_kind="partially-held"))
    assert not standing.held
    assert any("tells the truth" in g for g in standing.gaps)


def test_record_ready_without_evidence_ref_stands_open():
    standing = derive_standing(fresh_record(claims=("test_ref",)))
    assert not standing.held
    assert any("no held" in g for g in standing.gaps)


def test_record_ready_on_bare_claims_stands_open():
    standing = derive_standing(fresh_record(claims=("feeling",)))
    assert not standing.held
    assert any("bare claims only" in g for g in standing.gaps)


def test_record_shaping_with_owner_stands_held():
    standing = derive_standing(shaping_record())
    assert standing.held
    assert standing.grade == "held"


def test_record_shaping_without_owner_stands_open():
    standing = derive_standing(shaping_record(owner=""))
    assert not standing.held
    assert any("not a road" in g for g in standing.gaps)


def test_record_not_ready_silent_stands_open():
    standing = derive_standing(not_ready_record(claims=()))
    assert not standing.held
    assert any("silent" in g for g in standing.gaps)


def test_record_without_date_stands_open():
    standing = derive_standing(fresh_record(date=""))
    assert not standing.held
    assert any("no report date" in g for g in standing.gaps)


def test_record_unknown_disposition_refused():
    with pytest.raises(ValidationError, match="unknown record disposition"):
        derive_standing(fresh_record(disposition="MAYBE"))


def test_verdict_full_book_ready_with_shaping_releases():
    verdict = derive_verdict(full_book())
    assert verdict.ready
    assert verdict.gaps == ()
    assert verdict.ready_releases == ("R-01", "R-02", "R-03")
    assert len(verdict.shaping_releases) == 4
    assert len(verdict.not_ready_releases) == 5
    assert verdict.missing_releases == ()


def test_verdict_missing_release_stops_the_report():
    verdict = derive_verdict(full_book()[:-1])
    assert not verdict.ready
    assert verdict.missing_releases == ("R-12",)
    assert any("R-12" in g for g in verdict.gaps)


def test_verdict_open_record_stops_the_report():
    verdict = derive_verdict(full_book(**{"R-02": {"proof_kind": "none"}}))
    assert not verdict.ready
    assert any("R-02 stands open" in g for g in verdict.gaps)


def test_verdict_duplicate_release_named():
    records = full_book()
    records.append(records[0])
    verdict = derive_verdict(records)
    assert not verdict.ready
    assert any("two findings" in g for g in verdict.gaps)


def test_report_ready_and_shared_states():
    report = prepare_report("release-a", "R-01", "findings as dispositioned",
                            "2026-11-13", 3, 4, 5, 12,
                            claims=("evidence_ref",))
    assert report.state == "ready"
    shared = prepare_report("release-a", "R-01", "findings as dispositioned",
                            "2026-11-13", 3, 4, 5, 12,
                            claims=("evidence_ref",), state="shared",
                            certified=True)
    assert shared.state == "shared"
    assert shared.certified


def test_report_sealed_state_and_short_certified_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report("release-a", "R-01", "findings", "2026-11-13",
                       3, 4, 5, 12, claims=("evidence_ref",), state="sealed")
    with pytest.raises(ValidationError, match="release complete"):
        prepare_report("release-a", "R-01", "findings", "2026-11-13",
                       3, 2, 2, 12, claims=("evidence_ref",), certified=True)


def test_report_bare_claim_refused_and_format_roads():
    with pytest.raises(ValidationError, match="bare claim"):
        prepare_report("release-a", "R-01", "findings", "2026-11-13",
                       3, 4, 5, 12, claims=("feeling",))
    assert "R-01" in format_release(default_registry().get("R-01"))
    assert "R-12" in format_releases()
    assert "READY" in format_record(fresh_record())
    assert "SHAPING" in format_records([shaping_record()])
    assert set(HELD_EVIDENCE) <= set(EVIDENCE_KINDS)
    assert set(BARE_CLAIMS) <= set(EVIDENCE_KINDS)
    from pathlib import Path as _P
    _src = (_P(__file__).resolve().parent.parent
            / "mythic_agent" / "core" / "release_shaping.py").read_text(
                encoding="utf-8")
    assert "open(" not in _src
    assert "socket" not in _src
    assert "subprocess" not in _src
    assert "urllib" not in _src
