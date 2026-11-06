"""M-094 — Part IV gate.

TIER: integration

The Part IV gate (``mythic_agent/data/part4_gate.yaml`` +
``mythic_agent.core.part4_gate``): on a benchmark-pack-style
throwaway git repo, one benchmark refactor task completed
with zero failed applies, hunk review used, auto-commits
clean, and checkpoint restore proven mid-task, evidence
banked against the M-093 confirmation suite.

These tests do not take the record's word for any of it:

* the gate record loads and validates, its slices are
  M-071..M-093 with titles matching the roadmap data, and
  its baseline is the M-093 confirmation suite's counted
  totals,
* the refactor is RE-PROVEN LIVE on a real throwaway git
  repo through the shipped Agent roads: pricing.py edited
  by a unified diff that first passes through M-074's hunk
  review (``Agent.apply_hunk_review`` — the tax-rate hunk
  rejected and proven never to land, the two rename hunks
  accepted), shop.py edited through M-071's
  ``Agent.apply_edit_format`` search-and-replace road —
  2 attempted applies, 0 failed,
* the checkpoint is RE-PROVEN LIVE mid-task: M-075's
  ``Agent.take_checkpoint`` freezes the refactored tree, a
  later change is made, and ``Agent.restore_checkpoint``
  with discard returns both files to their checkpoint
  contents exactly and removes the scratch file,
* the auto-commit is RE-PROVEN LIVE: M-078's
  ``Agent.commit_accepted_edits`` lands the accepted edit
  set as one commit on the exercise repo's working branch,
  and the working tree is clean afterwards,
* the exercise's hidden grading tests pass in full, and
  the seed alone does not satisfy them,
* the honesty bounds hold: the evidence kind is
  agent-roads-measured — every step rides a real Agent
  road, nothing is faked, and the campaign tree is never
  the exercise repo.
"""

from __future__ import annotations

import copy
import subprocess
from pathlib import Path

import pytest

from mythic_agent.core.part4_gate import (
    EXERCISE_IDS,
    GATE_SLICE,
    Gate,
    grade_exercise,
    load_gate,
    materialise_exercise,
    render_markdown,
    validate_gate,
    verify_refactor,
)
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.validation import ValidationError
from mythic_agent.resources import load_resource


@pytest.fixture(scope="module")
def gate() -> Gate:
    return load_gate()


def test_shipped_gate_loads_and_validates(gate):
    assert isinstance(gate, Gate)
    assert validate_gate(load_resource("part4_gate.yaml")) == []
    assert gate.gate_slice == GATE_SLICE == "M-094"
    assert gate.part == 4
    assert gate.part_title == "The Editor's Hand"
    assert gate.verdict == "PASS"


def test_slices_cover_part4_in_order(gate):
    assert gate.slice_ids() == tuple(f"M-{n:03d}" for n in range(71, 94))
    road = load_roadmap()
    for ref in gate.slices:
        assert road.slice(ref.slice).title == ref.title, ref.slice
    assert road.part(4).title == gate.part_title
    done_ids = [s.id for s in road.done()]
    assert [f"M-{n:03d}" for n in range(71, 94)] == [
        d for d in done_ids if "M-071" <= d <= "M-093"]
    nxt = road.next_slice()
    assert nxt is not None
    assert nxt.id == "M-094" or nxt.part >= 5


def test_baseline_is_the_m093_confirmation_suite(gate):
    assert gate.baseline_resource == "m093_confirmation_suite"
    # The M-093 confirmation suite, counted from its on-disk
    # log on the laptop (logs/m093-fullsuite2.log): the 2
    # failures are exactly the long-classified environment
    # cases (tiktoken-premise estimator; PortAudio import).
    assert gate.baseline_totals() == (4811, 4808, 2, 1)


def test_exercise_shape_and_honesty(gate):
    assert gate.exercise_ids() == EXERCISE_IDS == ("refactor",)
    assert len(gate.completed_exercises()) == 1
    exercise = gate.exercise("refactor")
    assert exercise.status == "completed"
    assert exercise.evidence_kind == "agent-roads-measured"
    assert exercise.evidence
    assert exercise.seed_paths()
    assert exercise.details["attempted_applies"] == 2
    assert exercise.details["failed_applies"] == 0
    assert exercise.details["hunks_accepted"] >= 1
    assert exercise.details["hunks_rejected"] >= 1
    for sid in exercise.owning_slices:
        assert "M-071" <= sid <= "M-093"


def test_render_markdown_reports_the_gate(gate):
    text = render_markdown(gate)
    assert "PASS" in text
    assert "M-071..M-093" in text
    assert "4811 collected" in text
    for exercise_id in EXERCISE_IDS:
        assert gate.exercise(exercise_id).title in text


# ----------------------------------------------------------------------
# The benchmark refactor, re-proven live (M-071/M-074/M-075/M-078 roads)
# ----------------------------------------------------------------------


class _OfflineMemory:
    def __init__(self):
        self.archived = []

    def search(self, query, top_k=2):
        return []

    def insert(self, text, metadata=None):
        self.archived.append(text)


def _git(root, *args):
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


@pytest.fixture()
def bench_agent(tmp_path, monkeypatch):
    """An Agent rooted on the exercise repo, state outside it."""
    from mythic_agent.agents import llm
    from mythic_agent.core.secure_api import unsubscribe

    config = {"model": "test-model",
              "base_url": "http://localhost:1/v1", "api_keys": {}}
    monkeypatch.setattr(
        llm.config_manager, "MYTHIC_DIR", tmp_path / "gate-state")
    monkeypatch.setattr(
        llm.config_manager, "load_config",
        lambda: copy.deepcopy(config))
    monkeypatch.setattr(
        llm.config_manager, "save_config", lambda config: True)
    monkeypatch.setattr(
        llm, "get_vector_provider", lambda *args: _OfflineMemory())
    root = tmp_path / "refactor"
    root.mkdir(parents=True, exist_ok=True)
    instance = llm.Agent(project_root=root)
    yield instance, root
    unsubscribe("agent_clear_history", instance._handle_clear_history)
    unsubscribe("agent_compact_history", instance._handle_compact_history)


def test_refactor_exercise_reproven_live(gate, bench_agent):
    agent, root = bench_agent
    exercise = gate.exercise("refactor")
    materialise_exercise(exercise, root)
    # The seed alone does not satisfy the grading tests.
    assert grade_exercise(exercise, root) != (3, 3)

    # A real throwaway git repo on a working branch.
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Slice Test")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "initial")
    _git(root, "switch", "-c", exercise.details["commit_branch"])

    attempted = 0
    failed = 0

    # Apply 1 — pricing.py through hunk review (M-074 road):
    # the tax-rate hunk is rejected, the rename hunks land.
    attempted += 1
    try:
        record = agent.apply_hunk_review(
            "pricing.py", exercise.details["diff_payload"],
            [(0, "reject"), (1, "accept"), (2, "accept")])
    except Exception:
        failed += 1
        raise
    assert record["applied"] == exercise.details["hunks_accepted"] == 2
    assert record["rejected"] == exercise.details["hunks_rejected"] == 1
    assert record["changed"] is True

    # Apply 2 — shop.py through the search-and-replace road.
    attempted += 1
    try:
        agent.apply_edit_format(
            "shop.py", "search-replace",
            exercise.details["search_payload"])
    except Exception:
        failed += 1
        raise

    # Zero failed applies, judged from the files themselves.
    assert (attempted, failed) == (
        exercise.details["attempted_applies"],
        exercise.details["failed_applies"]) == (2, 0)
    assert verify_refactor(exercise, root) == []
    pricing_after = (root / "pricing.py").read_text(encoding="utf-8")
    shop_after = (root / "shop.py").read_text(encoding="utf-8")
    assert exercise.details["rejected_marker"] not in pricing_after

    # Checkpoint mid-task (M-075 road), then a later change.
    taken = agent.take_checkpoint(exercise.details["checkpoint_name"])
    assert taken["name"] == exercise.details["checkpoint_name"]
    (root / "shop.py").write_text(
        shop_after.replace(
            "return apply_discount(price_with_tax(amount))",
            "return round(apply_discount(price_with_tax(amount)), 2)"),
        encoding="utf-8")
    (root / "notes.txt").write_text("scratch\n", encoding="utf-8")
    restored = agent.restore_checkpoint(
        exercise.details["checkpoint_name"], discard=True)
    assert restored["discarded_changes"] >= 1
    # Restore proven by file contents: both files are back
    # at the checkpoint state and the scratch file is gone.
    assert (root / "pricing.py").read_text(encoding="utf-8") == \
        pricing_after
    assert (root / "shop.py").read_text(encoding="utf-8") == shop_after
    assert not (root / "notes.txt").exists()
    assert verify_refactor(exercise, root) == []

    # Auto-commit the accepted edits (M-078 road): one
    # commit on the working branch, tree clean afterwards.
    agent.set_auto_commit(True)
    record = agent.commit_accepted_edits(
        ["pricing.py", "shop.py"],
        "Rename legacy_discount to apply_discount")
    assert record["committed"] is True
    assert record["target_branch"] == exercise.details["commit_branch"]
    assert record["on_protected"] is False
    assert _git(root, "branch", "--show-current") == \
        exercise.details["commit_branch"]
    assert _git(root, "log", "-1", "--format=%s") == \
        "Rename legacy_discount to apply_discount"
    assert _git(root, "status", "--porcelain") == ""

    # The hidden grading tests pass in full.
    assert grade_exercise(exercise, root) == (3, 3)
    agent.close()


# ----------------------------------------------------------------------
# Validator honesty
# ----------------------------------------------------------------------


def _mutated(mutator):
    data = copy.deepcopy(load_resource("part4_gate.yaml"))
    mutator(data)
    return data


def test_validator_rejects_a_non_pass_verdict():
    data = _mutated(lambda d: d.update(verdict="FAIL"))
    assert any("PASS" in p for p in validate_gate(data))


def test_validator_rejects_a_missing_slice():
    data = _mutated(lambda d: d["slices"].pop())
    assert any("23" in p for p in validate_gate(data))


def test_validator_rejects_an_uncompleted_exercise():
    def spoil(d):
        d["exercises"][0]["status"] = "queued"

    assert any("completed" in p for p in validate_gate(_mutated(spoil)))


def test_validator_rejects_a_failed_apply():
    def spoil(d):
        d["exercises"][0]["failed_applies"] = 1

    assert any("failed_applies" in p for p in validate_gate(_mutated(spoil)))


def test_validator_rejects_an_unused_review():
    def spoil(d):
        d["exercises"][0]["hunks_rejected"] = 0

    assert any("hunk review" in p for p in validate_gate(_mutated(spoil)))


def test_validator_rejects_broken_baseline_arithmetic():
    def spoil(d):
        d["baseline"]["passed"] = 1

    assert any("arithmetic" in p for p in validate_gate(_mutated(spoil)))


def test_validator_rejects_a_one_file_refactor():
    def spoil(d):
        d["exercises"][0]["seed_files"] = [
            s for s in d["exercises"][0]["seed_files"]
            if not s["path"].endswith(".py") or s["path"] == "pricing.py"]

    assert any("refactor" in p for p in validate_gate(_mutated(spoil)))


def test_load_raises_on_invalid_data():
    with pytest.raises(ValidationError):
        load_gate({"schema": "nope", "slices": [], "exercises": [],
                   "baseline": {}})
