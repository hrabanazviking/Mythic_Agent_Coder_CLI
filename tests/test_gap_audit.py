"""
TIER: unit
Gap Audit gate (All-Features roadmap slice M-003).

The shipped audit (``mythic_agent/data/gap_audit.yaml``) must trace
every M-001 census gap to exactly one owning module, agree with the
census on owner slice and state, name the roadmap part that slice
lives in, and tell the truth about the tree (an "existing" module is
present, a "proposed" one is not). It must also carry the classified
verdicts for the campaign baseline's five unclassified failures —
each with its evidence, none left unclassified.
"""

import copy
from pathlib import Path

import pytest

from mythic_agent.core.feature_census import load_census
from mythic_agent.core.gap_audit import (
    FAILURE_VERDICTS,
    GapAudit,
    load_audit,
    render_markdown,
    validate_audit,
)
from mythic_agent.core.validation import ValidationError
from mythic_agent.resources import load_resource

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def audit() -> GapAudit:
    return load_audit(repo_root=REPO_ROOT)


def test_shipped_audit_loads_and_validates_against_tree(audit):
    assert isinstance(audit, GapAudit)
    assert validate_audit(load_resource("gap_audit.yaml"), repo_root=REPO_ROOT) == []
    assert audit.audited


def test_every_census_gap_has_exactly_one_row(audit):
    gaps = load_census().gaps()
    assert len(audit.rows) == len(gaps) == 24
    assert {row.feature for row in audit.rows} == {gap.id for gap in gaps}


def test_rows_agree_with_census_owner_and_state(audit):
    census = load_census()
    for row in audit.rows:
        gap = census.feature(row.feature)
        assert row.slice == gap.roadmap_ref
        assert row.state == gap.mythic.state
        assert row.fix_shape and row.basis


def test_module_kind_matches_the_tree(audit):
    for row in audit.rows:
        exists = (REPO_ROOT / row.owning_module).exists()
        if row.module_kind == "existing":
            assert exists, row.feature
        else:
            assert not exists, row.feature


def test_parts_match_roadmap_ranges(audit):
    # Spot-check the part boundaries across the road.
    assert audit.row("provider-breadth").part == "II"
    assert audit.row("repo-map").part == "III"
    assert audit.row("checkpoints-undo").part == "IV"
    assert audit.row("hooks").part == "V"
    assert audit.row("agent-teams-worktrees").part == "VI"
    assert audit.row("voice-input").part == "VIII"
    assert audit.row("method-engine").part == "IX"
    assert audit.row("mcp-client").part == "X"
    # Every part II-X with work is seeded by at least one row.
    seeded = {row.part for row in audit.rows_for_part("II")}
    assert seeded == {"II"}


def test_baseline_failures_all_classified_with_evidence(audit):
    assert len(audit.baseline_failures) == 5
    for finding in audit.baseline_failures:
        assert finding.verdict in FAILURE_VERDICTS
        assert finding.verdict != "unclassified"
        assert finding.evidence
    verdicts = audit.verdicts()
    assert verdicts["product-defect"] == 3  # provider x2 params + truncate
    assert verdicts["environment"] == 1
    assert verdicts["test-timing"] == 1
    by_test = {f.test: f for f in audit.baseline_failures}
    provider = [t for t in by_test if "empty_model_name" in t]
    assert len(provider) == 2
    assert all(by_test[t].fixed_in == "M-003" for t in provider)


def test_render_markdown_lists_every_row_and_finding(audit):
    text = render_markdown(audit)
    for row in audit.rows:
        assert row.feature in text
        assert row.owning_module in text
    for finding in audit.baseline_failures:
        assert finding.test in text
    assert audit.audited in text


def test_row_lookup_raises_keyerror(audit):
    with pytest.raises(KeyError):
        audit.row("no-such-feature")


def test_validation_rejects_broken_data():
    raw = load_resource("gap_audit.yaml")

    bad_schema = copy.deepcopy(raw)
    bad_schema["schema"] = "something/else"
    assert any("schema" in p for p in validate_audit(bad_schema))

    dropped_row = copy.deepcopy(raw)
    dropped_row["rows"] = [r for r in dropped_row["rows"] if r["feature"] != "repo-map"]
    assert any("no audit row" in p for p in validate_audit(dropped_row))

    wrong_owner = copy.deepcopy(raw)
    for row in wrong_owner["rows"]:
        if row["feature"] == "repo-map":
            row["slice"] = "M-043"
    assert any("census owner" in p for p in validate_audit(wrong_owner))

    wrong_part = copy.deepcopy(raw)
    for row in wrong_part["rows"]:
        if row["feature"] == "repo-map":
            row["part"] = "IV"
    assert any("roadmap part" in p for p in validate_audit(wrong_part))

    lying_kind = copy.deepcopy(raw)
    for row in lying_kind["rows"]:
        if row["feature"] == "repo-map":
            row["module_kind"] = "existing"
    assert any("marked existing but absent" in p
               for p in validate_audit(lying_kind, repo_root=REPO_ROOT))

    verdictless = copy.deepcopy(raw)
    verdictless["baseline_failures"][0]["verdict"] = "probably-fine"
    assert any("verdict" in p for p in validate_audit(verdictless))

    evidenceless = copy.deepcopy(raw)
    evidenceless["baseline_failures"][0]["evidence"] = ""
    assert any("evidence" in p for p in validate_audit(evidenceless))


def test_load_audit_raises_on_invalid_data():
    raw = load_resource("gap_audit.yaml")
    raw["rows"] = []
    with pytest.raises(ValidationError):
        load_audit(raw)
