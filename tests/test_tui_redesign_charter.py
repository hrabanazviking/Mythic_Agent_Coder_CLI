"""M-171 - The TUI redesign charter.

TIER: unit

The TUI redesign charter (``mythic_agent/data/tui_redesign_charter.yaml``
+ ``mythic_agent.core.tui_redesign_charter``): every screen re-judged
against M-004's kindness rules and the Visual Design Lawbook, a
written verdict per screen before code moves.

These tests do not take the record's word for any of it:

* the charter loads and validates, its screens are exactly the
  surfaces that ship, in the order a user meets them,
* the surfaces are RE-PROVEN LIVE: every named file exists in the
  tree and defines the symbol the record names,
* the kindness set is RE-PROVEN LIVE against M-004: it is exactly
  the set the shipped UX charter binds on Part VIII,
* every verdict is DERIVED: each screen's stored verdict equals
  the verdict its own judgement counts derive, the panel closes
  on the judgements themselves, and the overall verdict is the
  screens' verdicts derived,
* the honesty bounds hold: the evidence kind is code-inspected
  and nothing stronger is claimed - no user test, no live run,
  no screen code moved by the charter itself.
"""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from mythic_agent.core.tui_redesign_charter import (
    CHARTER_SLICE,
    EVIDENCE_KINDS,
    KINDNESS_IDS,
    LAWBOOK_IDS,
    PLAIN_EXPLANATION,
    SCREENS,
    Charter,
    charter_record,
    derive_overall,
    derive_panel,
    derived_verdict_for,
    load_charter,
    plain_words,
    render_markdown,
    validate_charter,
)
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.validation import ValidationError
from mythic_agent.resources import load_resource

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def charter() -> Charter:
    return load_charter()


def test_shipped_charter_loads_and_validates(charter):
    assert isinstance(charter, Charter)
    assert validate_charter(load_resource("tui_redesign_charter.yaml")) == []
    assert charter.chartered
    assert charter.evidence_kind in EVIDENCE_KINDS == ("code-inspected",)
    assert PLAIN_EXPLANATION


def test_charter_is_the_part8_opener(charter):
    road = load_roadmap()
    slice171 = road.slice("M-171")
    assert slice171.title == "The TUI redesign charter"
    assert slice171.part == 8
    assert road.part(8).first_slice == CHARTER_SLICE == "M-171"
    assert road.part(8).title == "The Beautiful Face"


def test_screens_are_exactly_the_shipped_surfaces(charter):
    assert charter.screen_keys() == SCREENS == (
        "splash", "setup_wizard", "main_chat", "command_approval",
        "github_config", "subagent_picker", "subagent_editor",
        "terminal_loop")
    assert [s.id for s in charter.screens] == [
        f"S-{n:02d}" for n in range(1, 9)]
    for review in charter.screens:
        assert review.title and review.evidence and review.direction
        assert review.owning_slices
        for sid in review.owning_slices:
            assert "M-172" <= sid <= "M-200"


def test_surfaces_exist_and_define_their_symbols(charter):
    for review in charter.screens:
        path = ROOT / review.surface
        assert path.is_file(), review.surface
        text = path.read_text(encoding="utf-8")
        assert (f"class {review.symbol}" in text
                or f"def {review.symbol}" in text), review.symbol


def test_kindness_set_is_m004s_part8_binding(charter):
    from mythic_agent.core.ux_charter import load_charter as load_ux

    ux = load_ux()
    assert {p.id for p in ux.for_part("VIII")} == set(KINDNESS_IDS)
    for review in charter.screens:
        assert tuple(j.ref for j in review.kindness) == KINDNESS_IDS
        for judgement in review.kindness:
            # Every judged principle is real M-004 law, cited whole.
            principle = ux.principle(judgement.ref)
            assert principle.review_check.endswith("?")


def test_lawbook_rules_are_reviewable(charter):
    assert tuple(r.id for r in charter.lawbook) == LAWBOOK_IDS
    for rule in charter.lawbook:
        assert rule.name and rule.rule
        assert rule.check.rstrip().endswith("?")
    for review in charter.screens:
        assert tuple(j.ref for j in review.lawbook) == LAWBOOK_IDS


def test_every_judgement_carries_its_evidence(charter):
    for review in charter.screens:
        assert len(review.judgements()) == 14
        for judgement in review.judgements():
            assert judgement.standing in (
                "holds", "strains", "fails", "not-engaged")
            assert judgement.note


def test_verdicts_are_derived_never_chosen(charter):
    assert derived_verdict_for(2, 0) == "rebuild"
    assert derived_verdict_for(1, 0) == "repair"
    assert derived_verdict_for(0, 4) == "repair"
    assert derived_verdict_for(0, 3) == "keep"
    for review in charter.screens:
        assert review.verdict == review.derived_verdict(), review.key
        assert review.verdict == derived_verdict_for(
            review.fails(), review.strains())


def test_panel_closes_on_the_judgements(charter):
    panel = derive_panel(charter)
    assert panel.total_screens == 8
    assert panel.total_judgements == 8 * 14 == 112
    assert (panel.holds + panel.strains + panel.fails
            + panel.not_engaged) == panel.total_judgements
    assert panel.fails == sum(s.fails() for s in charter.screens)
    assert panel.strains == sum(s.strains() for s in charter.screens)
    assert (panel.keeps, panel.repairs, panel.rebuilds) \
        == charter.verdict_counts()
    assert panel.keeps + panel.repairs + panel.rebuilds == 8


def test_shipped_findings_are_the_recorded_ones(charter):
    # The charter's findings, pinned so a softened edit must
    # argue with this test, not slip past it.
    assert charter.verdict_counts() == (2, 4, 2)
    assert charter.screen("splash").verdict == "rebuild"
    assert charter.screen("setup_wizard").verdict == "rebuild"
    assert charter.screen("main_chat").verdict == "repair"
    assert charter.screen("command_approval").verdict == "repair"
    assert charter.screen("github_config").verdict == "keep"
    assert charter.screen("subagent_picker").verdict == "keep"
    assert charter.screen("subagent_editor").verdict == "repair"
    assert charter.screen("terminal_loop").verdict == "repair"
    panel = derive_panel(charter)
    assert panel.fails == 8
    assert panel.overall == charter.overall_verdict \
        == "rebuild-where-named"


def test_overall_is_derived(charter):
    assert derive_overall(("keep", "keep")) == "holds"
    assert derive_overall(("keep", "repair")) == "repair-first"
    assert derive_overall(("repair", "rebuild")) \
        == "rebuild-where-named"
    assert derive_overall(
        tuple(s.verdict for s in charter.screens)) \
        == charter.overall_verdict


def test_render_plain_and_record_report_the_charter(charter):
    text = render_markdown(charter)
    for review in charter.screens:
        assert review.title in text and review.verdict in text
        assert review.direction in text
        for sid in review.owning_slices:
            assert sid in text
    for rule in charter.lawbook:
        assert rule.id in text and rule.check in text
    words = plain_words(charter)
    assert "8 screens re-judged" in words
    assert "112 judgements" in words
    assert "rebuild-where-named" in words
    record = charter_record(charter)
    assert record["type"] == "tui_redesign_charter"
    assert record["slice"] == "M-171"
    assert record["overall"] == "rebuild-where-named"
    assert record["fails"] == 8
    with pytest.raises(KeyError):
        charter.screen("no_such_screen")
    with pytest.raises(KeyError):
        charter.screen("splash").judgement("K-99")


def test_module_purity():
    import inspect

    import mythic_agent.core.tui_redesign_charter as module

    source = inspect.getsource(module)
    assert "from mythic_agent.agents" not in source
    assert "import mythic_agent.agents" not in source
    assert "from .ux_charter" not in source
    assert "import textual" not in source


# ----------------------------------------------------------------------
# Validator honesty
# ----------------------------------------------------------------------


def _mutated(mutator):
    data = copy.deepcopy(load_resource("tui_redesign_charter.yaml"))
    mutator(data)
    return data


def test_validator_rejects_a_dropped_screen():
    data = _mutated(lambda d: d["screens"].pop())
    assert any("screens must be exactly" in p
               for p in validate_charter(data))


def test_validator_rejects_an_invented_screen():
    def spoil(d):
        d["screens"][0]["key"] = "hologram_deck"

    assert any("screens must be exactly" in p
               for p in validate_charter(_mutated(spoil)))


def test_validator_rejects_a_softened_verdict():
    def spoil(d):
        d["screens"][0]["verdict"] = "keep"

    assert any("derived, never" in p
               for p in validate_charter(_mutated(spoil)))


def test_validator_rejects_a_dropped_judgement():
    data = _mutated(lambda d: d["screens"][2]["kindness"].pop())
    assert any("kindness refs must be exactly" in p
               for p in validate_charter(data))


def test_validator_rejects_a_judgement_without_evidence():
    def spoil(d):
        d["screens"][2]["lawbook"][0]["note"] = ""

    assert any("note must be" in p
               for p in validate_charter(_mutated(spoil)))


def test_validator_rejects_an_unknown_standing():
    def spoil(d):
        d["screens"][0]["kindness"][0]["standing"] = "fine"

    assert any("standing must be" in p
               for p in validate_charter(_mutated(spoil)))


def test_validator_rejects_a_stronger_evidence_claim():
    def spoil(d):
        d["evidence_kind"] = "user-tested"

    assert any("evidence_kind" in p
               for p in validate_charter(_mutated(spoil)))


def test_validator_rejects_an_owner_outside_part8():
    def spoil(d):
        d["screens"][0]["owning_slices"] = ["M-201"]

    assert any("Part VIII" in p
               for p in validate_charter(_mutated(spoil)))


def test_validator_rejects_a_softened_overall():
    def spoil(d):
        d["overall_verdict"] = "holds"

    assert any("overall_verdict is derived" in p
               for p in validate_charter(_mutated(spoil)))


def test_validator_rejects_a_non_question_lawbook_check():
    def spoil(d):
        d["lawbook"][0]["check"] = "Themed elements do jobs."

    assert any("must be a question" in p
               for p in validate_charter(_mutated(spoil)))


def test_load_raises_on_invalid_data():
    with pytest.raises(ValidationError):
        load_charter({"schema": "nope", "screens": [],
                      "lawbook": []})
