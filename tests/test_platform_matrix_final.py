"""M-259 Platform matrix final - pure-layer tests.

TIER: unit

M-013's table re-proven cell by cell; unproven
cells ship labelled NOT PROVEN, not silent: a
cell counts PROVEN only on evidence measured
locally, and an unproven cell with nothing
recorded stands open as silent.
"""
import pytest

from mythic_agent.core.platform_matrix_final import (
    BARE_CLAIMS,
    CELLS,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    PLATFORMS,
    STAGES,
    CellEntry,
    CellRegistry,
    MatrixRecord,
    default_registry,
    derive_standing,
    derive_verdict,
    format_cell,
    format_cells,
    format_record,
    format_records,
    prepare_report,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(cell="P-01",
                run="matrix-2026-11-a",
                date="2026-11-13", verdict="PROVEN",
                proof_kind="local-measured",
                stages=STAGES,
                claims=("local_run_ref", "report_ref"))
    base.update(kw)
    return MatrixRecord(**base)


def not_proven_record(**kw):
    base = dict(cell="P-08",
                run="matrix-2026-11-a",
                date="2026-11-13", verdict="NOT PROVEN",
                proof_kind="none",
                stages=STAGES,
                claims=("report_ref",))
    base.update(kw)
    return MatrixRecord(**base)


def full_book(**overrides):
    records = []
    for cell_id in default_registry().combinations():
        if cell_id in ("P-01", "P-02", "P-03"):
            kw = dict(cell=cell_id, run="matrix-2026-11-a",
                      date="2026-11-13", verdict="PROVEN",
                      proof_kind="local-measured",
                      stages=STAGES,
                      claims=("local_run_ref", "report_ref"))
        else:
            kw = dict(cell=cell_id, run="matrix-2026-11-a",
                      date="2026-11-13", verdict="NOT PROVEN",
                      proof_kind="historical-only",
                      stages=STAGES,
                      claims=("report_ref",))
        kw.update(overrides.get(cell_id, {}))
        records.append(MatrixRecord(**kw))
    return records


def test_registry_holds_twelve_cells_listed_only():
    reg = default_registry()
    assert len(reg.ids()) == 12
    assert reg.ids()[0] == "P-01"
    assert reg.ids()[-1] == "P-12"
    assert all(e.standing == "listed" for e in reg.entries())
    assert len(reg.combinations()) == 12


def test_registry_cells_cover_every_platform_surface():
    reg = default_registry()
    pairs = {(e.platform, e.surface) for e in reg.entries()}
    assert len(pairs) == 12
    assert reg.get("P-01").platform == "linux"
    assert reg.get("P-01").surface == "install"
    assert reg.get("P-12").platform == "macos"
    assert reg.get("P-12").surface == "voice"
    assert PLATFORMS == ("linux", "windows", "macos")


def test_registry_unknown_cell_refused_by_name():
    with pytest.raises(ValidationError, match="unknown cell: P-99"):
        default_registry().get("P-99")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate cell"):
        CellRegistry(CELLS + CELLS[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing reason"):
        CellRegistry([CellEntry("P-01", "linux", "install", "listed", "")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        CellRegistry([CellEntry("P-01", "linux", "install", "published", "why")])


def test_entry_unknown_platform_refused():
    with pytest.raises(ValidationError, match="unknown cell platform"):
        CellRegistry([CellEntry("P-01", "amiga", "install", "listed", "why")])


def test_record_proven_local_measured_stands_held():
    standing = derive_standing(fresh_record())
    assert standing.held
    assert standing.grade == "held"
    assert standing.gaps == ()


def test_record_incomplete_walk_stands_open():
    standing = derive_standing(fresh_record(stages=STAGES[:3]))
    assert not standing.held
    assert any("not held" in g for g in standing.gaps)


def test_record_bad_stage_step_stands_open():
    bad = ("named", "judged", "labelled", "held")
    standing = derive_standing(fresh_record(stages=bad))
    assert not standing.held
    assert any("not in the walk" in g for g in standing.gaps)


def test_record_proven_on_historical_evidence_stands_open():
    standing = derive_standing(fresh_record(proof_kind="historical-only"))
    assert not standing.held
    assert any("no inheritance" in g for g in standing.gaps)


def test_record_proven_without_local_evidence_stands_open():
    standing = derive_standing(fresh_record(claims=("report_ref",)))
    assert not standing.held
    assert any("no held local evidence" in g for g in standing.gaps)


def test_record_proven_on_bare_claims_stands_open():
    standing = derive_standing(fresh_record(claims=("feeling",)))
    assert not standing.held
    assert any("bare claims only" in g for g in standing.gaps)


def test_record_not_proven_labelled_stands_held():
    standing = derive_standing(not_proven_record())
    assert standing.held
    assert standing.grade == "held"


def test_record_not_proven_silent_stands_open():
    standing = derive_standing(not_proven_record(claims=()))
    assert not standing.held
    assert any("silent" in g for g in standing.gaps)


def test_record_without_date_stands_open():
    standing = derive_standing(fresh_record(date=""))
    assert not standing.held
    assert any("no re-proof date" in g for g in standing.gaps)


def test_record_unknown_verdict_refused():
    with pytest.raises(ValidationError, match="unknown record verdict"):
        derive_standing(fresh_record(verdict="MAYBE"))


def test_verdict_full_book_ready_with_labelled_cells():
    verdict = derive_verdict(full_book())
    assert verdict.ready
    assert verdict.gaps == ()
    assert verdict.proven_cells == ("P-01", "P-02", "P-03")
    assert len(verdict.not_proven_cells) == 9
    assert verdict.missing_cells == ()


def test_verdict_missing_cell_stops_the_matrix():
    verdict = derive_verdict(full_book()[:-1])
    assert not verdict.ready
    assert verdict.missing_cells == ("P-12",)
    assert any("P-12" in g for g in verdict.gaps)


def test_verdict_open_record_stops_the_matrix():
    verdict = derive_verdict(full_book(**{"P-02": {"proof_kind": "none"}}))
    assert not verdict.ready
    assert any("P-02 stands open" in g for g in verdict.gaps)


def test_verdict_duplicate_cell_named():
    records = full_book()
    records.append(records[0])
    verdict = derive_verdict(records)
    assert not verdict.ready
    assert any("two re-proofs" in g for g in verdict.gaps)


def test_report_ready_and_shared_states():
    report = prepare_report("matrix-a", "P-01", "cells as re-proven",
                            "2026-11-13", 3, 9, 12,
                            claims=("local_run_ref",))
    assert report.state == "ready"
    shared = prepare_report("matrix-a", "P-01", "cells as re-proven",
                            "2026-11-13", 3, 9, 12,
                            claims=("local_run_ref",), state="shared",
                            certified=True)
    assert shared.state == "shared"
    assert shared.certified


def test_report_sealed_state_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report("matrix-a", "P-01", "cells", "2026-11-13",
                       3, 9, 12, claims=("local_run_ref",), state="sealed")


def test_report_certified_short_of_answered_refused():
    with pytest.raises(ValidationError, match="matrix final"):
        prepare_report("matrix-a", "P-01", "cells", "2026-11-13",
                       3, 5, 12, claims=("local_run_ref",), certified=True)


def test_report_bare_claim_refused_and_format_roads():
    with pytest.raises(ValidationError, match="bare claim"):
        prepare_report("matrix-a", "P-01", "cells", "2026-11-13",
                       3, 9, 12, claims=("feeling",))
    assert "P-01" in format_cell(default_registry().get("P-01"))
    assert "P-12" in format_cells()
    assert "PROVEN" in format_record(fresh_record())
    assert "NOT PROVEN" in format_records([not_proven_record()])
    assert set(HELD_EVIDENCE) <= set(EVIDENCE_KINDS)
    assert set(BARE_CLAIMS) <= set(EVIDENCE_KINDS)
