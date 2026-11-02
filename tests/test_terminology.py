"""
TIER: unit
Terminology Bridge gate (All-Features roadmap slice M-006).

The shipped bridge (``mythic_agent/data/terminology.yaml``) must give
every field term its Mythic name and keep every term searchable by
its common name, its Mythic name, and its aliases — a user coming
from any rival finds their word honoured. The roadmap's named
examples (checkpoint, hook, skill, plan mode) are carried exactly
once, and no name may resolve ambiguously.
"""

import copy

import pytest

from mythic_agent.core.terminology import (
    REQUIRED_COMMON_TERMS,
    Bridge,
    load_bridge,
    render_markdown,
    validate_bridge,
)
from mythic_agent.core.validation import ValidationError
from mythic_agent.resources import load_resource


@pytest.fixture(scope="module")
def bridge() -> Bridge:
    return load_bridge()


def test_shipped_bridge_loads_and_validates(bridge):
    assert isinstance(bridge, Bridge)
    assert validate_bridge(load_resource("terminology.yaml")) == []
    assert bridge.bridged
    assert len(bridge.terms) >= len(REQUIRED_COMMON_TERMS)


def test_ids_are_sequential(bridge):
    assert [t.id for t in bridge.terms] == [
        f"T-{n:02d}" for n in range(1, len(bridge.terms) + 1)
    ]


def test_roadmap_named_terms_carried_exactly_once(bridge):
    commons = [t.common.strip().lower() for t in bridge.terms]
    for required in REQUIRED_COMMON_TERMS:
        assert commons.count(required) == 1


def test_every_term_has_a_mythic_name_and_definition(bridge):
    for term in bridge.terms:
        assert term.mythic.strip() and term.definition.strip()
        assert term.mythic.strip().lower() != term.common.strip().lower()


def test_find_by_common_mythic_and_alias(bridge):
    for term in bridge.terms:
        assert bridge.find(term.common) is term
        assert bridge.find(term.mythic) is term
        for alias in term.aliases:
            assert bridge.find(alias) is term


def test_find_is_case_and_separator_insensitive(bridge):
    plan = bridge.find("PLAN  MODE")
    assert plan is not None and plan.common == "plan mode"
    assert bridge.find("Plan-Mode") is plan
    assert bridge.find("waymark").common == "checkpoint"
    assert bridge.find("no-such-field-word") is None


def test_search_index_covers_every_name_exactly_once(bridge):
    names = [name for name, _ in bridge.searchable_names()]
    normalised = [name.strip().lower().replace("-", " ") for name in names]
    assert len(normalised) == len(set(normalised))
    expected = sum(2 + len(t.aliases) for t in bridge.terms)
    assert len(names) == expected


def test_render_covers_terms_and_required_words(bridge):
    text = render_markdown(bridge)
    for term in bridge.terms:
        assert term.id in text and term.common in text
        assert term.mythic in text and term.definition.split(".")[0] in text
    for required in REQUIRED_COMMON_TERMS:
        assert f"`{required}`" in text


def _tampered(mutator):
    data = copy.deepcopy(load_resource("terminology.yaml"))
    mutator(data)
    return data


def test_validation_rejects_a_dropped_required_term():
    data = _tampered(
        lambda d: d["terms"].__setitem__(
            1, {**d["terms"][1], "common": "rest stop"}
        )
    )
    problems = validate_bridge(data)
    assert any("checkpoint" in p and "exactly" in p for p in problems)
    with pytest.raises(ValidationError):
        load_bridge(data)


def test_validation_rejects_a_colliding_alias():
    data = _tampered(lambda d: d["terms"][0]["aliases"].append("hook"))
    problems = validate_bridge(data)
    assert any("collides" in p for p in problems)


def test_validation_rejects_a_duplicate_mythic_name():
    data = _tampered(
        lambda d: d["terms"][1].update(mythic=d["terms"][0]["mythic"])
    )
    problems = validate_bridge(data)
    assert any("collides" in p for p in problems)


def test_validation_rejects_a_numbering_gap():
    data = _tampered(lambda d: d["terms"][2].update(id="T-09"))
    problems = validate_bridge(data)
    assert any("sequential" in p for p in problems)


def test_validation_rejects_a_term_without_definition():
    data = _tampered(lambda d: d["terms"][0].update(definition=""))
    problems = validate_bridge(data)
    assert any("definition must be non-empty" in p for p in problems)
