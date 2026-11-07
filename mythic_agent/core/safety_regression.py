"""Safety regression suite (All-Features roadmap slice M-117).

Part V - Autonomy & Safety. The roadmap words:
``every doctrine rule above as a test; the suite is a
release gate, not documentation.``

What already shipped, and what this slice adds:

* Slices M-103..M-116 each shipped one Part V safety
  layer as a pure module plus its own test file -
  background jobs, the keeper, scheduled work, fleet
  mode, budgets, the kill switch, the audit trail,
  secret hygiene, the destructive-command doctrine,
  rollback drills, multi-repo workspaces, remote
  work, offline grace, and approval moments. Each
  layer's rules are pinned by its own tests, but
  nothing held the fourteen doctrines together as
  one named, counted, release-gating suite: a rule
  could quietly lose its pinning test and no single
  record would notice.
* This slice is that missing gate, in the exact
  shape of the shipped part gates (``part4_gate.py``
  / ``part4_gate.yaml``, M-094): a validated gate
  record (``mythic_agent/data/safety_regression.yaml``)
  naming the slices it closes over (M-103..M-116),
  the M-116 confirmation-suite baseline it is banked
  against, and one doctrine rule per slice - each
  rule stating the doctrine in plain words and
  naming the shipped module that carries it and the
  exact tests that pin it.
* The gate's tests do not take this record's word
  for any of it: every named pinning test must exist
  in its named test file, every named module must
  import and state its own slice, and the sharpest
  rules are re-proven live against the shipped pure
  roads. A rule whose pinning tests are gone fails
  the gate - the suite is a release gate, not
  documentation.

Honesty rules, enforced by the validator and pinned
by tests:

* The verdict is ``PASS`` and the validator accepts
  no other verdict: a gate that has failed is a
  defect to fix, not a record.
* Every slice M-103..M-116 carries at least one
  rule, and every rule names at least one pinning
  test. A rule with no test is documentation, and
  this gate refuses it.
* Rule ids are the fixed sequence R-01.. in slice
  order, never reused or reordered silently.
* The baseline section must close arithmetically:
  the M-116 confirmation suite's counted totals
  (6021 collected, 6018 passed, 2 failed - the two
  long-classified environment cases - 1 skipped).

This module is the gate's machinery only: it loads
and validates the record, states it in plain words
and renders it as markdown. It runs no test, opens
no session, and imports no agent / UI code; the
gate's tests own the live re-proof.
"""

from __future__ import annotations

__all__ = [
    "BASELINE_RESOURCE",
    "EVIDENCE_KIND",
    "GATE_RESOURCE",
    "GATE_SCHEMA",
    "GATE_SLICE",
    "PLAIN_EXPLANATION",
    "RULE_IDS",
    "SAFETY_REGRESSION_SLICE",
    "SLICE_IDS",
    "Any",
    "Dict",
    "Gate",
    "List",
    "Optional",
    "Rule",
    "SliceRef",
    "Tuple",
    "format_gate_screen",
    "format_rule",
    "format_rules",
    "gate_record",
    "load_gate",
    "plain_words",
    "render_markdown",
    "validate_gate",
]

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .validation import ValidationError

#: Resource name of the gate data file inside ``mythic_agent/data``.
GATE_RESOURCE = "safety_regression.yaml"

#: The only schema this loader accepts.
GATE_SCHEMA = "mythic.safety_regression/1"

#: The slice that owns this gate.
GATE_SLICE = "M-117"

#: The shorter name other layers cite for this slice.
SAFETY_REGRESSION_SLICE = GATE_SLICE

#: The Part V safety slices this gate closes over, in roadmap order.
SLICE_IDS = tuple(f"M-{n:03d}" for n in range(103, 117))

#: The gate's rule ids, in slice order.
RULE_IDS = tuple(f"R-{n:02d}" for n in range(1, len(SLICE_IDS) + 1))

#: The confirmation suite the gate is banked against.
BASELINE_RESOURCE = "m116_confirmation_suite"

#: The one evidence kind a rule may honestly claim: its doctrine
#: is pinned by named tests the gate verifies and the suite runs.
EVIDENCE_KIND = "tests-verified"

PLAIN_EXPLANATION = (
    "Safety regression suite: every Part V doctrine "
    "rule from M-103 to M-116 held as one named rule "
    "in a gate record, each rule stating the doctrine "
    "in plain words and naming the shipped module "
    "that carries it and the exact tests that pin it. "
    "The gate's own tests verify every named pinning "
    "test truly exists, every named module truly "
    "carries its slice, and the sharpest rules are "
    "re-proven live, so a doctrine that loses its "
    "tests fails the release gate instead of quietly "
    "becoming documentation. This layer holds the "
    "record as data only; running the suite is the "
    "test runner's work."
)


@dataclass(frozen=True)
class SliceRef:
    """One Part V safety slice the gate closes over."""

    slice: str
    title: str


@dataclass(frozen=True)
class Rule:
    """One doctrine rule: the doctrine, its carrier, its pins.

    ``rule`` is the doctrine stated in plain words.
    ``module`` is the shipped core module that carries
    the doctrine, ``test_file`` its test file, and
    ``tests`` the exact test functions in that file
    that pin the rule - each one verified to exist by
    the gate's tests on every run.
    """

    id: str
    slice: str
    rule: str
    module: str
    test_file: str
    tests: Tuple[str, ...]

    def pin_count(self) -> int:
        """How many named tests pin this rule."""
        return len(self.tests)


@dataclass(frozen=True)
class Gate:
    """The validated safety regression gate record."""

    gate_slice: str
    part: int
    part_title: str
    verdict: str
    gate_note: str
    baseline_resource: str
    baseline: Tuple[int, int, int, int]
    slices: Tuple[SliceRef, ...]
    rules: Tuple[Rule, ...]

    def slice_ids(self) -> Tuple[str, ...]:
        """The gated slices, in road order (M-103..M-116)."""
        return tuple(s.slice for s in self.slices)

    def rule_ids(self) -> Tuple[str, ...]:
        """The gate's rule ids, in slice order."""
        return tuple(r.id for r in self.rules)

    def rule(self, rule_id: str) -> Rule:
        """The rule named *rule_id* (KeyError if absent)."""
        for rule in self.rules:
            if rule.id == rule_id:
                return rule
        raise KeyError(f"no rule {rule_id!r}")

    def rules_for(self, slice_id: str) -> Tuple[Rule, ...]:
        """Every rule the gate holds for one slice."""
        return tuple(r for r in self.rules if r.slice == slice_id)

    def pin_count(self) -> int:
        """The total named pinning tests across all rules."""
        return sum(r.pin_count() for r in self.rules)

    def baseline_totals(self) -> Tuple[int, int, int, int]:
        """The M-116 baseline: collected/passed/failed/skipped."""
        return self.baseline


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def validate_gate(data: Any) -> List[str]:
    """Return a list of human-readable problems with gate *data*."""
    problems: List[str] = []
    if not isinstance(data, dict):
        return [f"gate root must be a mapping, got {type(data).__name__}"]
    if data.get("schema") != GATE_SCHEMA:
        problems.append(
            f"schema must be {GATE_SCHEMA!r}, got {data.get('schema')!r}")
    if data.get("gate_slice") != GATE_SLICE:
        problems.append(
            f"gate_slice must be {GATE_SLICE!r}, "
            f"got {data.get('gate_slice')!r}")
    if data.get("part") != 5:
        problems.append(f"part must be 5, got {data.get('part')!r}")
    if data.get("verdict") != "PASS":
        problems.append(
            "verdict must be 'PASS' (a failed gate is a defect, not a "
            f"record), got {data.get('verdict')!r}")
    for key in ("part_title", "gate_note"):
        if not isinstance(data.get(key), str) or not data[key]:
            problems.append(f"{key} must be a non-empty string")

    baseline = data.get("baseline")
    if not isinstance(baseline, dict):
        problems.append("baseline must be a mapping")
    else:
        if baseline.get("resource") != BASELINE_RESOURCE:
            problems.append(
                f"baseline.resource must be {BASELINE_RESOURCE!r}, got "
                f"{baseline.get('resource')!r}")
        counts = [baseline.get(k) for k in
                  ("collected", "passed", "failed", "skipped")]
        if not all(_is_int(c) and c >= 0 for c in counts):
            problems.append(
                "baseline counts must be non-negative integers, got "
                f"{counts!r}")
        elif counts[0] != counts[1] + counts[2] + counts[3]:
            problems.append(
                "baseline must close arithmetically: collected "
                f"{counts[0]} != passed {counts[1]} + failed "
                f"{counts[2]} + skipped {counts[3]}")

    slices = data.get("slices")
    if not isinstance(slices, list):
        problems.append("slices must be a list")
        slices = []
    seen_slices: List[str] = []
    for entry in slices:
        if not isinstance(entry, dict):
            problems.append(f"slice entry must be a mapping, got {entry!r}")
            continue
        sid = entry.get("slice")
        if sid not in SLICE_IDS:
            problems.append(
                f"slice must be one of M-103..M-116, got {sid!r}")
        elif sid in seen_slices:
            problems.append(f"slice {sid} is named twice")
        seen_slices.append(sid)
        if not isinstance(entry.get("title"), str) or not entry["title"]:
            problems.append(f"slice {sid!r} must name a non-empty title")
    if tuple(seen_slices) != SLICE_IDS:
        problems.append(
            "slices must be exactly M-103..M-116 in roadmap order, got "
            f"{seen_slices!r}")

    rules = data.get("rules")
    if not isinstance(rules, list):
        problems.append("rules must be a list")
        rules = []
    seen_ids: List[str] = []
    covered: List[str] = []
    for entry in rules:
        if not isinstance(entry, dict):
            problems.append(f"rule entry must be a mapping, got {entry!r}")
            continue
        rid = entry.get("id")
        if rid in seen_ids:
            problems.append(f"rule id {rid!r} is named twice")
        seen_ids.append(rid)
        sid = entry.get("slice")
        if sid not in SLICE_IDS:
            problems.append(
                f"rule {rid!r} names slice {sid!r}, outside M-103..M-116")
        else:
            covered.append(sid)
        if entry.get("evidence_kind") != EVIDENCE_KIND:
            problems.append(
                f"rule {rid!r} evidence_kind must be {EVIDENCE_KIND!r}, "
                f"got {entry.get('evidence_kind')!r}")
        if not isinstance(entry.get("rule"), str) or not entry["rule"]:
            problems.append(f"rule {rid!r} must state its doctrine")
        module = entry.get("module")
        if not isinstance(module, str) or not module.startswith(
                "mythic_agent/core/") or not module.endswith(".py"):
            problems.append(
                f"rule {rid!r} module must name a shipped core module, "
                f"got {module!r}")
        test_file = entry.get("test_file")
        if not isinstance(test_file, str) or not test_file.startswith(
                "tests/test_") or not test_file.endswith(".py"):
            problems.append(
                f"rule {rid!r} test_file must name a shipped test file, "
                f"got {test_file!r}")
        tests = entry.get("tests")
        if not isinstance(tests, list) or not tests:
            problems.append(
                f"rule {rid!r} names no pinning test - a rule with no "
                "test is documentation, and this gate refuses it")
        else:
            for name in tests:
                if not isinstance(name, str) or not name.startswith(
                        "test_"):
                    problems.append(
                        f"rule {rid!r} pinning test {name!r} is not a "
                        "test function name")
            if len(set(tests)) != len(tests):
                problems.append(
                    f"rule {rid!r} names a pinning test twice")
    if tuple(seen_ids) != RULE_IDS:
        problems.append(
            f"rule ids must be exactly {list(RULE_IDS)!r} in order, "
            f"got {seen_ids!r}")
    for sid in SLICE_IDS:
        if sid not in covered:
            problems.append(
                f"slice {sid} carries no rule - every doctrine above "
                "must be pinned")
    return problems


def load_gate(data: Optional[Dict[str, Any]] = None) -> Gate:
    """Load and validate the shipped gate record (or *data*).

    Raises :class:`~mythic_agent.core.validation.ValidationError`
    listing every problem when the record is not a well-formed gate.
    """
    raw = data if data is not None else load_resource(GATE_RESOURCE)
    problems = validate_gate(raw)
    if problems:
        raise ValidationError(
            "invalid safety regression gate: " + "; ".join(problems))
    assert isinstance(raw, dict)
    baseline = raw["baseline"]
    return Gate(
        gate_slice=raw["gate_slice"],
        part=raw["part"],
        part_title=raw["part_title"],
        verdict=raw["verdict"],
        gate_note=raw["gate_note"],
        baseline_resource=baseline["resource"],
        baseline=(baseline["collected"], baseline["passed"],
                  baseline["failed"], baseline["skipped"]),
        slices=tuple(
            SliceRef(slice=entry["slice"], title=entry["title"])
            for entry in raw["slices"]),
        rules=tuple(
            Rule(
                id=entry["id"],
                slice=entry["slice"],
                rule=entry["rule"],
                module=entry["module"],
                test_file=entry["test_file"],
                tests=tuple(entry["tests"]),
            )
            for entry in raw["rules"]),
    )


def plain_words(gate: Gate) -> str:
    """The gate stated in one plain sentence."""
    collected, passed, failed, skipped = gate.baseline_totals()
    return (
        f"Safety regression gate {gate.gate_slice}: "
        f"{gate.verdict} - {len(gate.rules)} doctrine rules over "
        f"slices M-103..M-116, pinned by {gate.pin_count()} named "
        f"tests, banked against the M-116 confirmation suite "
        f"({collected} collected, {passed} passed, {failed} failed, "
        f"{skipped} skipped). A rule that loses its pinning tests "
        "fails this gate.")


def gate_record(gate: Gate) -> Dict[str, Any]:
    """The gate shaped as a session-news record."""
    return {
        "type": "safety_regression_gate",
        "session_event": "safety_regression_gate",
        "news": True,
        "slice": gate.gate_slice,
        "verdict": gate.verdict,
        "rules": len(gate.rules),
        "pinning_tests": gate.pin_count(),
        "headline": plain_words(gate),
    }


def format_rule(rule: Rule) -> str:
    """One rule stated in plain words, with its pins."""
    pins = ", ".join(rule.tests)
    return (
        f"{rule.id} ({rule.slice}): {rule.rule} "
        f"[carried by {rule.module}; pinned by "
        f"{rule.test_file}: {pins}]")


def format_rules(gate: Gate) -> str:
    """Every rule, one per line, in slice order."""
    return "\n".join(format_rule(rule) for rule in gate.rules)


def format_gate_screen(gate: Gate) -> str:
    """The whole gate as one screen of plain words."""
    return plain_words(gate) + "\n" + format_rules(gate)


def render_markdown(gate: Gate) -> str:
    """The gate record rendered as a markdown report."""
    collected, passed, failed, skipped = gate.baseline_totals()
    lines = [
        f"# Safety regression gate ({gate.gate_slice})",
        "",
        f"Part {gate.part} - {gate.part_title}. Verdict: {gate.verdict}.",
        "",
        f"Baseline: the M-116 confirmation suite - {collected} "
        f"collected, {passed} passed, {failed} failed, "
        f"{skipped} skipped.",
        "",
        "Slices closed over: M-103..M-116.",
        "",
        "## Doctrine rules",
        "",
    ]
    for rule in gate.rules:
        lines.append(f"- {format_rule(rule)}")
    lines.append("")
    lines.append(plain_words(gate))
    return "\n".join(lines) + "\n"
