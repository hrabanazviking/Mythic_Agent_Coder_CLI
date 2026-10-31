"""
TIER: unit
The Arcanum Review gate (All-Features roadmap slice M-011).

The shipped review (``mythic_agent/data/arcanum_review.yaml``) maps
the standalone tarot TUI at ``arcanum/arcanum.py`` section by
section: what each section owns, what it duplicates in the package,
and the absorb/leave verdict for Parts III, VI, and VII. These
tests cross-check the review against the live file — its sha256,
its exact line/byte counts, each section's span and anchor, an AST
parse of the whole file, and the literal data tables — so the map
cannot silently drift from the territory.

They also hold the repairs for the three defects the review proved
(all fixed in M-011): D-01 the file did not compile, D-02
``render_celtic_cross_layout`` was called but never defined, D-03
the ``reversal_pct`` setting was never wired to the draw. The
compile/AST gates here are the net that catches D-01's class forever.
"""

import ast
import copy
import hashlib
import importlib.util
import random
from pathlib import Path

import pytest

from mythic_agent.core.arcanum_review import (
    ArcanumReview,
    load_review,
    render_markdown,
    validate_review,
)
from mythic_agent.core.validation import ValidationError
from mythic_agent.resources import load_resource

REPO_ROOT = Path(__file__).resolve().parent.parent
ARCANUM = REPO_ROOT / "arcanum" / "arcanum.py"


@pytest.fixture(scope="module")
def review() -> ArcanumReview:
    return load_review()


@pytest.fixture(scope="module")
def source() -> str:
    return ARCANUM.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def arcanum_module():
    spec = importlib.util.spec_from_file_location("arcanum_under_review", ARCANUM)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _by_name(review):
    return {s.name: s for s in review.sections}


# ---------------------------------------------------------------------------
# Review cross-checks against the live file
# ---------------------------------------------------------------------------

def test_shipped_review_loads_and_validates(review):
    assert isinstance(review, ArcanumReview)
    assert validate_review(load_resource("arcanum_review.yaml")) == []
    assert review.counts() == (16, 3, 3)


def test_live_file_matches_the_reviewed_file_exactly(review, source):
    raw = ARCANUM.read_bytes()
    assert review.file_lines == len(source.splitlines())
    assert review.file_bytes == len(raw)
    assert review.file_sha256 == hashlib.sha256(raw).hexdigest()


def test_section_spans_cover_the_file_and_hold_their_anchors(review, source):
    lines = source.splitlines()
    assert review.sections[0].lines[0] == 1
    assert review.sections[-1].lines[1] == len(lines)
    for prev, nxt in zip(review.sections, review.sections[1:]):
        assert nxt.lines[0] == prev.lines[1] + 1
    for entry in review.sections:
        span = "\n".join(lines[entry.lines[0] - 1: entry.lines[1]])
        assert entry.anchor in span, (entry.name, entry.anchor)


def test_ids_are_sequential(review):
    assert [s.id for s in review.sections] == [
        f"A-{n:02d}" for n in range(1, len(review.sections) + 1)]
    assert review.defect_ids() == ("D-01", "D-02", "D-03")
    assert [f.id for f in review.findings] == ["F-01", "F-02", "F-03"]


def test_every_verdict_for_parts_iii_vi_vii_is_leave(review):
    """The review's core claim: these three parts absorb nothing."""
    for name in review.section_names():
        for part in ("iii", "vi", "vii"):
            assert review.verdict_of(name, part) == "leave", (name, part)
    assert review.overall_verdict.startswith("LEAVE")


def test_the_file_parses_and_defines_what_the_review_names(source):
    """D-01's gate: the whole file must parse, with its named defs present."""
    tree = ast.parse(source)
    defined = {
        node.name for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.ClassDef))
    }
    for expected in (
        "load_config", "save_config", "TarotCard", "TarotDeck",
        "check_dignity", "apply_dignities", "render_card",
        "render_card_mini", "render_celtic_cross_layout", "ai_reading",
        "do_reading", "save_reading", "show_settings", "main",
    ):
        assert expected in defined, expected


def test_literal_data_tables_match_the_review(source):
    """The catalogued data sections hold the counts the review states."""
    tree = ast.parse(source)
    tables = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in (
                "MAJOR_ARCANA", "MINOR_ARCANA", "COURT_CARDS",
                "SPREADS", "ELEMENT_HARMONY",
            ):
                tables[target.id] = ast.literal_eval(node.value)
    assert len(tables["MAJOR_ARCANA"]) == 22
    assert len(tables["MINOR_ARCANA"]) == 40
    assert len(tables["COURT_CARDS"]) == 16
    assert len(tables["SPREADS"]) == 8
    assert len(tables["ELEMENT_HARMONY"]) == 16
    assert sum(s["count"] for s in tables["SPREADS"].values()) == 54


def test_render_covers_every_section_defect_and_finding(review):
    text = render_markdown(review)
    for name in review.section_names():
        assert f"`{name}`" in text
        assert review.verdict_of(name, "iii") in text
    for defect_id in review.defect_ids():
        assert defect_id in text
    for finding in review.findings:
        assert finding.id in text and finding.name in text
    assert review.file_sha256 in text


def _tampered(mutator):
    data = copy.deepcopy(load_resource("arcanum_review.yaml"))
    mutator(data)
    return data


def test_validation_rejects_a_dropped_section():
    data = _tampered(lambda d: d["sections"].pop(3))
    problems = validate_review(data)
    assert any("sequential" in p or "contiguous" in p for p in problems)
    with pytest.raises(ValidationError):
        load_review(data)


def test_validation_rejects_an_unfixed_defect():
    data = _tampered(lambda d: d["defects"][0].update(status="noted"))
    problems = validate_review(data)
    assert any("fixed-in-slice" in p for p in problems)


def test_validation_rejects_an_unknown_kind():
    data = _tampered(lambda d: d["sections"][0].update(kind="somewhere"))
    problems = validate_review(data)
    assert any("kind" in p for p in problems)


# ---------------------------------------------------------------------------
# The in-slice repairs, exercised live (D-01, D-02, D-03)
# ---------------------------------------------------------------------------

def test_deck_builds_78_cards(arcanum_module):
    deck = arcanum_module.TarotDeck()
    assert len(deck.cards) == 78
    majors = [c for c in deck.cards if c.is_major]
    courts = [c for c in deck.cards if c.is_court]
    assert len(majors) == 22 and len(courts) == 16


def test_d03_reversal_percentage_is_wired_to_the_draw(arcanum_module):
    random.seed(20261031)
    none_reversed = arcanum_module.TarotDeck().draw(20, reversal_pct=0)
    assert len(none_reversed) == 20
    assert not any(c.is_reversed for c in none_reversed)
    all_reversed = arcanum_module.TarotDeck().draw(20, reversal_pct=100)
    assert all(c.is_reversed for c in all_reversed)
    # The old hardcoded behaviour is the default: 35%.
    import inspect
    assert inspect.signature(
        arcanum_module.TarotDeck.draw).parameters["reversal_pct"].default == 35


def test_d02_celtic_cross_layout_renders_all_ten_positions(arcanum_module):
    deck = arcanum_module.TarotDeck()
    drawn = deck.draw(10, reversal_pct=0)
    positions = arcanum_module.SPREADS["celtic_cross"]["positions"]
    cards_with_positions = [
        {"card": card, "position_name": pos["name"],
         "position_meaning": pos["meaning"], "dignity": "neutral"}
        for card, pos in zip(drawn, positions)
    ]
    layout = arcanum_module.render_celtic_cross_layout(cards_with_positions)
    assert isinstance(layout, str) and layout
    for card, pos in zip(drawn, positions):
        assert card.name in layout
        assert pos["name"] in layout


def test_d01_ai_reading_exists_with_its_documented_signature(arcanum_module):
    import inspect
    params = list(inspect.signature(arcanum_module.ai_reading).parameters)
    assert params == ["spread_name", "cards_with_positions", "question",
                      "api_key", "model"]
    assert arcanum_module.ai_reading.__defaults__ == ("openai/gpt-4o",)
    # With requests present it is callable; without a key call it must
    # still answer honestly rather than NameError (D-01's symptom).
    result, error = arcanum_module.ai_reading(
        "The Three Card Spread", [], "q?", api_key="")
    assert result is None and error  # an API error string, not a crash
