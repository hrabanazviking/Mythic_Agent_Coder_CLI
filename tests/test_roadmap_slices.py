"""
TIER: unit
Roadmap-as-data gate (All-Features roadmap slice M-017).

The shipped roadmap data (``mythic_agent/data/roadmap_slices.yaml``)
must be the whole approved road — 11 parts, 272 slices, sequential
ids, contiguous part ranges — with the roadmap's own titles and
summaries, and its check-off ledger must agree with the campaign
state file: a slice is done here only where CAMPAIGN_STATE.md's
ledger says DONE, and done slices form a prefix of the road.
"""

import copy
import re
from pathlib import Path

import pytest

from mythic_agent.core.roadmap_slices import (
    STATUSES,
    TOTAL_PARTS,
    TOTAL_SLICES,
    Roadmap,
    load_roadmap,
    render_markdown,
    validate_roadmap,
)
from mythic_agent.core.validation import ValidationError
from mythic_agent.resources import load_resource

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def roadmap() -> Roadmap:
    return load_roadmap()


def test_shipped_roadmap_loads_and_validates(roadmap):
    assert isinstance(roadmap, Roadmap)
    assert validate_roadmap(load_resource("roadmap_slices.yaml")) == []
    assert roadmap.roadmap and roadmap.source_note


def test_whole_road_present(roadmap):
    assert len(roadmap.parts) == TOTAL_PARTS == 11
    assert len(roadmap.slices) == TOTAL_SLICES == 272
    assert [s.id for s in roadmap.slices] == [f"M-{i:03d}" for i in range(1, 273)]
    assert roadmap.parts[0].first_slice == "M-001"
    assert roadmap.parts[-1].last_slice == "M-272"


def test_part_ranges_contiguous_and_membership_consistent(roadmap):
    for prev, curr in zip(roadmap.parts, roadmap.parts[1:]):
        assert curr.first_slice == f"M-{int(prev.last_slice[2:]) + 1:03d}"
    for part in roadmap.parts:
        members = roadmap.by_part(part.number)
        assert members[0].id == part.first_slice
        assert members[-1].id == part.last_slice
        assert all(s.part == part.number for s in members)


def test_every_slice_carries_the_roads_words(roadmap):
    for slice_ in roadmap.slices:
        assert slice_.title and slice_.summary
        assert slice_.status in STATUSES
    # Spot anchors: slices whose wording the campaign itself cites.
    assert roadmap.slice("M-017").title == "The roadmap made data"
    assert roadmap.slice("M-025").title == "Project Aesir as a provider"
    assert roadmap.slice("M-001").part == 1
    assert roadmap.slice("M-272").part == 11


def test_statuses_agree_with_campaign_state_ledger(roadmap):
    state = (REPO_ROOT / "CAMPAIGN_STATE.md").read_text(encoding="utf-8")
    ledger = dict(
        re.findall(r"\| (M-\d{3}) \| [^|]+ \| \*\*(DONE|IN PROGRESS)\*\*", state)
    )
    # Every banked-or-active Part I row (M-001..M-017) is bold-marked in
    # the state ledger; M-018 still reads plain "queued" and is absent.
    assert len(ledger) >= 17
    assert {f"M-{i:03d}" for i in range(1, 18)} <= set(ledger)
    for slice_id, mark in ledger.items():
        status = roadmap.slice(slice_id).status
        if mark == "DONE":
            assert status == "done", slice_id
        else:  # IN PROGRESS is not yet banked, so not done in the data
            assert status == "queued", slice_id
    # Nothing outside the ledger's DONE rows is marked done.
    for slice_ in roadmap.done():
        assert ledger.get(slice_.id) == "DONE", slice_.id


def test_done_prefix_and_next_slice(roadmap):
    done = roadmap.done()
    assert [s.id for s in done] == [s.id for s in roadmap.slices[: len(done)]]
    nxt = roadmap.next_slice()
    assert nxt is not None
    assert nxt.id == f"M-{len(done) + 1:03d}"
    progress = roadmap.progress()
    assert sum(total for _, _, total in progress) == TOTAL_SLICES
    assert sum(count for _, count, _ in progress) == len(done)


def test_render_markdown_reports_progress(roadmap):
    text = render_markdown(roadmap)
    assert f"{len(roadmap.done())} of 272 slices done" in text
    assert roadmap.next_slice().id in text
    for part in roadmap.parts:
        assert f"Part {part.roman}" in text
    assert "- [x] **M-001**" in text
    assert "- [ ] **M-272**" in text


def _mutated(mutator):
    data = copy.deepcopy(load_resource("roadmap_slices.yaml"))
    mutator(data)
    return data


def test_validator_rejects_a_missing_slice():
    data = _mutated(lambda d: d["slices"].pop())
    assert any("272" in p for p in validate_roadmap(data))


def test_validator_rejects_out_of_order_done():
    def spoil(d):
        d["slices"][0]["status"] = "queued"
        d["slices"][1]["status"] = "done"

    assert any("prefix" in p for p in validate_roadmap(_mutated(spoil)))


def test_validator_rejects_a_gap_in_part_ranges():
    def spoil(d):
        d["parts"][1]["first_slice"] = "M-020"

    assert validate_roadmap(_mutated(spoil))


def test_validator_rejects_misfiled_slice_part():
    def spoil(d):
        d["slices"][18]["part"] = 1  # M-019 belongs to part II

    assert validate_roadmap(_mutated(spoil))


def test_validator_rejects_unknown_status():
    def spoil(d):
        d["slices"][0]["status"] = "banked"

    assert validate_roadmap(_mutated(spoil))


def test_load_raises_on_invalid_data():
    with pytest.raises(ValidationError):
        load_roadmap({"schema": "nope", "parts": [], "slices": []})
