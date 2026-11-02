"""
TIER: unit
Method Charter gate (All-Features roadmap slice M-005).

The shipped charter (``mythic_agent/data/method_charter.yaml``) must
carry Volmarr's six Forge Protocol plugs exactly once each, in stack
order, give every tenet directives Part IX's engine can execute, and
carry the autonomy tenet's pause lines exactly — the bounds are the
charter's hard edge.
"""

import copy

import pytest

from mythic_agent.core.method_charter import (
    PAUSE_LINES,
    STACK_PLUGS,
    MethodCharter,
    load_charter,
    render_markdown,
    validate_charter,
)
from mythic_agent.core.validation import ValidationError
from mythic_agent.resources import load_resource


@pytest.fixture(scope="module")
def charter() -> MethodCharter:
    return load_charter()


def test_shipped_charter_loads_and_validates(charter):
    assert isinstance(charter, MethodCharter)
    assert validate_charter(load_resource("method_charter.yaml")) == []
    assert charter.chartered and charter.author


def test_six_plugs_in_stack_order(charter):
    assert [t.key for t in charter.tenets] == [k for k, _ in STACK_PLUGS]
    assert [t.plug for t in charter.tenets] == [p for _, p in STACK_PLUGS]
    assert [t.id for t in charter.tenets] == [
        f"F-{n:02d}" for n in range(1, len(STACK_PLUGS) + 1)
    ]


def test_every_tenet_is_executable_doctrine(charter):
    for tenet in charter.tenets:
        assert tenet.name and tenet.summary
        assert tenet.directives, f"{tenet.id} carries no directives"
        assert all(d.strip() for d in tenet.directives)
    flat = charter.directives()
    assert len(flat) == sum(len(t.directives) for t in charter.tenets)
    assert {tid for tid, _ in flat} == {t.id for t in charter.tenets}


def test_pause_lines_exact_and_only_on_autonomy(charter):
    assert set(charter.pause_lines()) == set(PAUSE_LINES)
    assert len(charter.pause_lines()) == len(PAUSE_LINES)
    for tenet in charter.tenets:
        if tenet.key != "autonomy-lines":
            assert tenet.pause_before == ()
    with pytest.raises(KeyError):
        charter.tenet("no-such-plug")


def test_definition_of_done_present(charter):
    assert len(charter.definition_of_done) >= 5
    assert all(item.strip() for item in charter.definition_of_done)


def test_render_covers_stack_pause_lines_and_done(charter):
    text = render_markdown(charter)
    for tenet in charter.tenets:
        assert tenet.id in text and tenet.plug in text and tenet.name in text
        for directive in tenet.directives:
            assert directive in text
    for line_ in PAUSE_LINES:
        assert line_ in text
    for item in charter.definition_of_done:
        assert item in text
    assert "Part IX" in text


def _tampered(mutator):
    data = copy.deepcopy(load_resource("method_charter.yaml"))
    mutator(data)
    return data


def test_validation_rejects_a_reordered_stack():
    def swap(d):
        d["tenets"][0], d["tenets"][1] = d["tenets"][1], d["tenets"][0]

    problems = validate_charter(_tampered(swap))
    assert any("stack order" in p for p in problems)


def test_validation_rejects_a_dropped_plug():
    data = _tampered(lambda d: d["tenets"].pop())
    problems = validate_charter(data)
    assert any("exactly 6" in p for p in problems)
    with pytest.raises(ValidationError):
        load_charter(data)


def test_validation_rejects_a_tenet_without_directives():
    data = _tampered(lambda d: d["tenets"][3].update(directives=[]))
    problems = validate_charter(data)
    assert any("directives must be a non-empty list" in p for p in problems)


def test_validation_rejects_a_softened_pause_line():
    data = _tampered(
        lambda d: d["tenets"][4]["pause_before"].remove("expose-secrets")
    )
    problems = validate_charter(data)
    assert any("pause_before must be exactly" in p for p in problems)


def test_validation_rejects_pause_lines_on_another_tenet():
    data = _tampered(
        lambda d: d["tenets"][0].update(pause_before=["unexpected-cost"])
    )
    problems = validate_charter(data)
    assert any("only the autonomy tenet" in p for p in problems)


def test_validation_rejects_a_numbering_gap():
    data = _tampered(lambda d: d["tenets"][2].update(id="F-09"))
    problems = validate_charter(data)
    assert any("sequential" in p for p in problems)
