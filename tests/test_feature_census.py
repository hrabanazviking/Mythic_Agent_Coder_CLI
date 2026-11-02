"""
TIER: unit
Feature Census gate (All-Features roadmap slice M-001).

The shipped census (``mythic_agent/data/feature_census.yaml``) must stay
a well-formed living matrix: at least ten named rivals, every feature
row carrying a cell for every rival, every Mythic PARTIAL/MISSING row
owned by a roadmap slice, and every Mythic HAVE/BETTER claim backed by
an evidence pointer into this repository. These tests are the census's
rot protection — they fail loudly when the data drifts out of shape.
"""

import copy

import pytest

from mythic_agent.core.feature_census import (
    MYTHIC_STATES,
    Census,
    load_census,
    render_markdown,
    validate_census,
)
from mythic_agent.core.validation import ValidationError
from mythic_agent.resources import load_resource

EXPECTED_RIVALS = {
    "claude-code",
    "codex-cli",
    "gemini-cli",
    "opencode",
    "aider",
    "copilot-cli",
    "goose",
    "cline",
    "amp",
    "pi",
}


@pytest.fixture(scope="module")
def census() -> Census:
    return load_census()


def test_shipped_census_loads_and_validates(census):
    assert isinstance(census, Census)
    assert validate_census(load_resource("feature_census.yaml")) == []
    assert census.refreshed  # a refresh stamp is always present


def test_at_least_ten_named_rivals(census):
    ids = {rival.id for rival in census.rivals}
    assert len(ids) >= 10
    assert EXPECTED_RIVALS <= ids
    for rival in census.rivals:
        assert rival.name  # every column is a named tool, not a stub


def test_every_feature_row_is_complete(census):
    rival_ids = {rival.id for rival in census.rivals}
    assert len(census.features) >= 30
    for row in census.features:
        assert set(row.rivals) == rival_ids
        assert row.mythic.state in MYTHIC_STATES
        assert row.mythic.form


def test_every_gap_is_owned_by_a_roadmap_slice(census):
    gaps = census.gaps()
    assert gaps  # the census exists because gaps exist
    for row in gaps:
        assert row.roadmap_ref is not None
        assert row.roadmap_ref.startswith("M-")


def test_have_and_better_claims_carry_evidence(census):
    for row in census.features:
        if row.mythic.state in ("HAVE", "BETTER"):
            assert row.mythic.evidence, row.id


def test_known_truths_from_the_roadmap(census):
    # Roadmap section 2 names these gaps plainly; the census must agree.
    assert census.feature("repo-map").mythic.state == "MISSING"
    assert census.feature("repo-map").roadmap_ref == "M-044"
    assert census.feature("mcp-client").mythic.state == "MISSING"
    assert census.feature("hooks").mythic.state == "MISSING"
    assert census.feature("provider-breadth").mythic.state == "PARTIAL"
    assert census.feature("method-engine").roadmap_ref == "M-201"
    # Named frontier holders are credited, not flattened.
    assert census.feature("repo-map").rivals["aider"].state == "HAVE"
    assert census.feature("debugger-dap").rivals["omp"].state == "HAVE"
    assert census.feature("lsp-integration").rivals["opencode"].state == "HAVE"
    assert census.feature("agent-teams-worktrees").rivals["claude-code"].state == "HAVE"


def test_unknown_is_used_not_guessed(census):
    # Where the roadmap census does not name a holder, cells stay UNKNOWN.
    assert census.feature("debugger-dap").rivals["goose"].state == "UNKNOWN"


def test_counts_cover_every_row(census):
    counts = census.counts()
    assert sum(counts.values()) == len(census.features)
    assert counts["MISSING"] >= 5
    assert counts["HAVE"] >= 10


def test_render_markdown_lists_every_feature(census):
    text = render_markdown(census)
    for row in census.features:
        assert row.name in text
    assert census.refreshed in text
    assert "owned by M-044" in text  # the gaps section names each owner


def test_validation_rejects_broken_data():
    raw = load_resource("feature_census.yaml")

    not_a_map = validate_census(["nope"])
    assert not_a_map  # root must be a mapping

    bad_schema = copy.deepcopy(raw)
    bad_schema["schema"] = "something/else"
    assert any("schema" in p for p in validate_census(bad_schema))

    dropped_cell = copy.deepcopy(raw)
    del dropped_cell["features"][0]["rivals"]["aider"]
    assert any("missing rival cells" in p for p in validate_census(dropped_cell))

    unowned_gap = copy.deepcopy(raw)
    for row in unowned_gap["features"]:
        if row["id"] == "repo-map":
            row["roadmap_ref"] = None
    assert any("roadmap_ref" in p for p in validate_census(unowned_gap))

    evidenceless = copy.deepcopy(raw)
    for row in evidenceless["features"]:
        if row["mythic"]["state"] == "HAVE":
            row["mythic"]["evidence"] = ""
            break
    assert any("evidence" in p for p in validate_census(evidenceless))

    mythic_unknown = copy.deepcopy(raw)
    mythic_unknown["features"][0]["mythic"]["state"] = "UNKNOWN"
    assert any("mythic state" in p for p in validate_census(mythic_unknown))


def test_load_census_raises_on_invalid_data():
    raw = load_resource("feature_census.yaml")
    raw["features"] = []
    with pytest.raises(ValidationError):
        load_census(raw)


def test_missing_feature_and_rival_raise_keyerror(census):
    with pytest.raises(KeyError):
        census.feature("no-such-feature")
    with pytest.raises(KeyError):
        census.rival("no-such-rival")
