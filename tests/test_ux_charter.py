"""
TIER: unit
UX Principles Charter gate (All-Features roadmap slice M-004).

The shipped charter (``mythic_agent/data/ux_charter.yaml``) must carry
the roadmap's five named kindness mandates exactly once each, number
its principles sequentially (law is cited by number), and give every
principle a review check phrased as a question a reviewer can answer
yes or no from a later slice's own evidence.
"""

import copy

import pytest

from mythic_agent.core.ux_charter import (
    ROADMAP_MANDATES,
    UxCharter,
    load_charter,
    render_markdown,
    validate_charter,
)
from mythic_agent.core.validation import ValidationError
from mythic_agent.resources import load_resource


@pytest.fixture(scope="module")
def charter() -> UxCharter:
    return load_charter()


def test_shipped_charter_loads_and_validates(charter):
    assert isinstance(charter, UxCharter)
    assert validate_charter(load_resource("ux_charter.yaml")) == []
    assert charter.chartered


def test_ids_are_sequential_from_k01(charter):
    expected = [f"K-{n:02d}" for n in range(1, len(charter.principles) + 1)]
    assert [p.id for p in charter.principles] == expected


def test_five_roadmap_mandates_carried_exactly_once(charter):
    covered = charter.mandates_covered()
    assert set(covered) == set(ROADMAP_MANDATES)
    assert covered["plain-language-first"] == "K-01"
    assert covered["one-tap-approvals"] == "K-02"
    assert covered["named-target-destruction"] == "K-03"
    assert covered["explained-refusals"] == "K-04"
    assert covered["visible-slices"] == "K-05"


def test_every_principle_is_reviewable(charter):
    for principle in charter.principles:
        assert principle.name and principle.rule and principle.why
        assert principle.review_check.rstrip().endswith("?")
        assert principle.applies_to


def test_part_lookup(charter):
    part_viii = {p.id for p in charter.for_part("VIII")}
    # Approvals, refusals, slices, and calm all bind the interface part.
    assert {"K-02", "K-04", "K-05", "K-09"} <= part_viii
    # Plain language and named targets bind everywhere after Part I.
    for part in ("II", "VII", "XI"):
        ids = {p.id for p in charter.for_part(part)}
        assert "K-01" in ids and "K-03" in ids
    with pytest.raises(KeyError):
        charter.principle("K-99")


def test_render_covers_law_mandates_and_parts(charter):
    text = render_markdown(charter)
    for principle in charter.principles:
        assert principle.id in text and principle.name in text
        assert principle.review_check in text
    for mandate in ROADMAP_MANDATES:
        assert mandate in text
    assert "Part VIII" in text


def _tampered(mutator):
    data = copy.deepcopy(load_resource("ux_charter.yaml"))
    mutator(data)
    return data


def test_validation_rejects_a_dropped_mandate():
    data = _tampered(lambda d: d["principles"][0].update(mandate=None))
    problems = validate_charter(data)
    assert any("plain-language-first" in p for p in problems)
    with pytest.raises(ValidationError):
        load_charter(data)


def test_validation_rejects_a_doubled_mandate():
    data = _tampered(
        lambda d: d["principles"][1].update(mandate="plain-language-first")
    )
    problems = validate_charter(data)
    assert any("already carried" in p for p in problems)


def test_validation_rejects_a_non_question_review_check():
    data = _tampered(
        lambda d: d["principles"][2].update(review_check="Targets are named.")
    )
    problems = validate_charter(data)
    assert any("must be a question" in p for p in problems)


def test_validation_rejects_a_numbering_gap():
    data = _tampered(lambda d: d["principles"][3].update(id="K-07"))
    problems = validate_charter(data)
    assert any("sequential" in p for p in problems)


def test_validation_rejects_an_unknown_part():
    data = _tampered(lambda d: d["principles"][0].update(applies_to=["XII"]))
    problems = validate_charter(data)
    assert any("not one of" in p for p in problems)
