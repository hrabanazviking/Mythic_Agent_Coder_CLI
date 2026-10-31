"""
TIER: unit
Platform Truth Table gate (All-Features roadmap slice M-013).

The shipped table (``mythic_agent/data/platform_truth.yaml``) records
Linux/Windows/macOS x install/run/TUI/voice — twelve cells, each
PROVEN or NOT PROVEN as of the recorded date, no inheritance. These
tests cross-check the table against the live CI workflow (its OS
matrix, its manual-only trigger, its install step), against the
hosted run ids recorded in ``docs/development/PROGRESS.md``, and —
on the Linux machine this campaign actually runs on — against the
live platform and the measured PortAudio absence, so the table
cannot drift away from the evidence it cites.
"""

import copy
import re
import sys
from pathlib import Path

import pytest

from mythic_agent.core.platform_truth import (
    EVIDENCE_KINDS,
    PLATFORMS,
    SURFACES,
    PlatformTruth,
    load_truth,
    render_markdown,
    validate_truth,
)
from mythic_agent.core.validation import ValidationError
from mythic_agent.resources import load_resource

REPO_ROOT = Path(__file__).resolve().parent.parent
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"
PROGRESS = REPO_ROOT / "docs" / "development" / "PROGRESS.md"

HOSTED_RUN_IDS = ("37258887547", "37258957751", "37259244508")


@pytest.fixture(scope="module")
def truth() -> PlatformTruth:
    return load_truth()


def test_shipped_table_loads_and_validates(truth):
    assert isinstance(truth, PlatformTruth)
    assert validate_truth(load_resource("platform_truth.yaml")) == []
    n_cells, n_proven = truth.counts()
    assert n_cells == 12
    assert n_proven == 3


def test_grid_is_exactly_platforms_by_surfaces(truth):
    pairs = [(c.platform, c.surface) for c in truth.cells]
    assert sorted(pairs) == sorted(
        (p, s) for p in PLATFORMS for s in SURFACES)
    assert [c.id for c in truth.cells] == [
        f"P-{n:02d}" for n in range(1, 13)]


def test_no_inheritance_only_local_measurement_proves(truth):
    for cell in truth.cells:
        assert cell.verdict in ("PROVEN", "NOT PROVEN")
        assert cell.evidence_kind in EVIDENCE_KINDS
        if cell.verdict == "PROVEN":
            assert cell.evidence_kind == "local-measured", cell.id
            assert cell.platform == "linux", cell.id


def test_voice_is_not_proven_anywhere(truth):
    for platform in PLATFORMS:
        assert truth.verdict_for(platform, "voice") == "NOT PROVEN"
    voice_kinds = {
        c.platform: c.evidence_kind for c in truth.cells if c.surface == "voice"}
    # the Linux absence is measured; the hosted matrix never installs
    # the voice extra, so windows/macos voice has no evidence at all
    assert voice_kinds["linux"] == "local-measured"
    assert voice_kinds["windows"] == "none"
    assert voice_kinds["macos"] == "none"


def test_windows_and_macos_rest_on_historical_evidence_only(truth):
    for cell in truth.cells:
        if cell.platform in ("windows", "macos"):
            assert cell.verdict == "NOT PROVEN", cell.id
            assert cell.evidence_kind in ("historical-only", "none"), cell.id


def test_ci_workflow_matches_the_tables_claims(truth):
    ci = CI_WORKFLOW.read_text(encoding="utf-8")
    # the matrix the table calls historical really covers all three OSes
    for os_name in ("ubuntu-latest", "windows-latest", "macos-latest"):
        assert os_name in ci
    # the workflow is manual-dispatch only: no hosted run can exist for
    # the current tree unless someone dispatched it — the table's
    # reason for keeping windows/macos at NOT PROVEN
    assert "workflow_dispatch" in ci
    assert not re.search(r"^\s*push:", ci, flags=re.MULTILINE)
    # the install step installs dev+tui and never the voice extra —
    # the table's reason voice has no hosted evidence anywhere
    install_lines = [ln for ln in ci.splitlines() if "pip install" in ln]
    assert install_lines and all("voice" not in ln for ln in install_lines)
    assert any("[dev,tui]" in ln for ln in install_lines)


def test_hosted_run_ids_cited_are_recorded_in_progress(truth):
    progress = PROGRESS.read_text(encoding="utf-8")
    table_text = truth.scope_note + " " + " ".join(
        c.evidence for c in truth.cells)
    for run_id in HOSTED_RUN_IDS:
        assert run_id in progress, run_id
        assert run_id in table_text, run_id


@pytest.mark.skipif(sys.platform != "linux", reason="campaign evidence is Linux-local")
def test_linux_cells_match_this_machine(truth):
    import platform as platform_module
    assert platform_module.machine() == "x86_64"
    assert truth.verdict_for("linux", "install") == "PROVEN"
    assert truth.verdict_for("linux", "run") == "PROVEN"
    assert truth.verdict_for("linux", "tui") == "PROVEN"
    # if the audio stack cannot import on this machine, the table
    # must say NOT PROVEN — the measured-absence implication
    try:
        import sounddevice  # noqa: F401
    except Exception:
        assert truth.verdict_for("linux", "voice") == "NOT PROVEN"


def test_render_covers_every_cell(truth):
    text = render_markdown(truth)
    for cell in truth.cells:
        assert cell.id in text and cell.evidence in text
    for cell_id in truth.proven_cells():
        assert cell_id in text
    for cell_id in truth.not_proven_cells():
        assert cell_id in text
    for platform in PLATFORMS:
        assert truth.verdict_for(platform, "install") in text


def _tampered(mutator):
    data = copy.deepcopy(load_resource("platform_truth.yaml"))
    mutator(data)
    return data


def test_validation_rejects_proven_on_historical_evidence():
    data = _tampered(lambda d: d["cells"][4].update(
        verdict="PROVEN"))  # P-05 windows/install is historical-only
    problems = validate_truth(data)
    assert any("no inheritance" in p for p in problems)
    with pytest.raises(ValidationError):
        load_truth(data)


def test_validation_rejects_a_dropped_cell():
    data = _tampered(lambda d: d["cells"].pop())
    problems = validate_truth(data)
    assert any("sequential" in p or "cover" in p for p in problems)


def test_validation_rejects_a_duplicated_pair():
    data = _tampered(lambda d: d["cells"][1].update(platform="linux",
                                                     surface="install"))
    problems = validate_truth(data)
    assert any("twice" in p or "cover" in p for p in problems)


def test_validation_rejects_an_unknown_verdict():
    data = _tampered(lambda d: d["cells"][0].update(verdict="PROBABLY"))
    problems = validate_truth(data)
    assert any("verdict" in p for p in problems)
