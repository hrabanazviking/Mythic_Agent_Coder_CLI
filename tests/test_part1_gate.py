"""
TIER: unit
Part I gate (All-Features roadmap slice M-018).

The shipped gate record (``mythic_agent/data/part1_gate.yaml``) closes
Part I: census + concordance + audits published in-repo, baseline
evidence banked, and Volmarr's 500-slice Mimisbrunnr file untouched.
These tests do not take the record's word for any of it — every data
artefact is re-loaded through its own shipped loader, the Concordance
document is opened, the gate's baseline totals are cross-checked
against the frozen baseline itself, the roadmap data must agree that
M-001..M-017 are done with M-018 next, and the live Mimisbrunnr file
is hashed and measured against the gate's pin.
"""

import copy
import hashlib
import importlib
from pathlib import Path

import pytest

from mythic_agent.core.baseline_freeze import load_freeze
from mythic_agent.core.part1_gate import (
    GATE_SLICE,
    KINDS,
    Gate,
    load_gate,
    render_markdown,
    validate_gate,
)
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.validation import ValidationError
from mythic_agent.resources import load_resource

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def gate() -> Gate:
    return load_gate()


def test_shipped_gate_loads_and_validates(gate):
    assert isinstance(gate, Gate)
    assert validate_gate(load_resource("part1_gate.yaml")) == []
    assert gate.gate_slice == GATE_SLICE == "M-018"
    assert gate.part == 1
    assert gate.verdict == "PASS"


def test_artefacts_cover_part1_in_order(gate):
    assert gate.artefact_ids() == tuple(f"M-{n:03d}" for n in range(1, 18))
    assert len(gate.by_kind("data")) == 16
    assert len(gate.by_kind("doc")) == 1
    for art in gate.artefacts:
        assert art.kind in KINDS
        assert art.title and art.evidence


def test_artefact_titles_match_the_roadmap(gate):
    road = load_roadmap()
    for art in gate.artefacts:
        assert road.slice(art.slice).title == art.title, art.slice
    # The gate's own road position: Part I's first seventeen slices
    # are done in the roadmap data, and the gate slice is next.
    assert [s.id for s in road.done()] == [f"M-{n:03d}" for n in range(1, 18)]
    assert road.next_slice().id == "M-018"
    assert road.part(1).title == gate.part_title


def test_every_data_artefact_loads_through_its_own_loader(gate):
    assert len(gate.loaders()) == 16
    for art in gate.by_kind("data"):
        # The resource the gate names is the resource that ships.
        load_resource(art.location)
        module_name, _, func_name = art.loader.partition(":")
        loader = getattr(importlib.import_module(module_name), func_name)
        loaded = loader()
        assert loaded is not None, art.slice


def test_concordance_doc_is_published_in_repo(gate):
    (doc_art,) = gate.by_kind("doc")
    assert doc_art.slice == "M-002"
    path = REPO_ROOT / doc_art.location
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "MIM-" in text  # the elder road is cited there
    assert "M-" in text


def test_baseline_totals_equal_the_frozen_baseline(gate):
    freeze = load_freeze()
    assert gate.baseline_totals() == freeze.suite_totals()
    collected, passed, failed, skipped = gate.baseline_totals()
    assert passed + failed + skipped == collected


def test_mimisbrunnr_file_matches_its_pin(gate):
    path = REPO_ROOT / gate.mimis_path
    blob = path.read_bytes()
    assert hashlib.sha256(blob).hexdigest() == gate.mimis_sha256
    assert len(blob) == gate.mimis_bytes
    lines = blob.decode("utf-8").count("\n") + (
        0 if blob.endswith(b"\n") else 1
    )
    assert lines == gate.mimis_lines == 9469


def test_render_markdown_reports_the_gate(gate):
    text = render_markdown(gate)
    assert "PASS" in text
    assert "M-001" in text and "M-017" in text
    assert gate.mimis_sha256 in text
    collected, passed, failed, skipped = gate.baseline_totals()
    assert f"{passed} passed" in text


def _mutated(mutator):
    data = copy.deepcopy(load_resource("part1_gate.yaml"))
    mutator(data)
    return data


def test_validator_rejects_a_missing_artefact():
    data = _mutated(lambda d: d["artefacts"].pop())
    assert any("17" in p for p in validate_gate(data))


def test_validator_rejects_a_non_pass_verdict():
    data = _mutated(lambda d: d.update(verdict="FAIL"))
    assert any("PASS" in p for p in validate_gate(data))


def test_validator_rejects_a_loaderless_data_artefact():
    def spoil(d):
        d["artefacts"][0]["loader"] = ""

    assert validate_gate(_mutated(spoil))


def test_validator_rejects_a_bad_mimisbrunnr_pin():
    def spoil(d):
        d["mimisbrunnr"]["sha256"] = "xyz"

    assert any("sha256" in p for p in validate_gate(_mutated(spoil)))


def test_validator_rejects_unclosed_baseline_arithmetic():
    def spoil(d):
        d["baseline"]["passed"] += 1

    assert any("arithmetic" in p for p in validate_gate(_mutated(spoil)))


def test_load_raises_on_invalid_data():
    with pytest.raises(ValidationError):
        load_gate({"schema": "nope", "artefacts": [], "baseline": {}, "mimisbrunnr": {}})
