"""The accessibility-final-gate book (roadmap slice M-262) - pure layer.

Part XI - Proof. The roadmap words: **M-199 checks on the shipped TUI, with the keyboard-only task timed.**

What this layer holds, as data: a check registry A-01..A-12 (keyboard task and approval, body and muted contrast, reduced motion, no-colour, screen-reader, focus, alt text, shortcut truth, setup traversal, status by text), each listed only; a gate record per check holding its timed task, date, disposition PASSED or ROADED, owner, proof kind and stage walk named-rerun-judged-dispositioned-held; a derived standing; a derived accessibility verdict over the whole book; and a final-gate report prepared only through the prepare road, ready or shared, never sealed, inflated or certified short of every check answered.

Honesty rule, made code: a check counts PASSED only on the gate own shipped-TUI re-run resting on held rerun evidence (a rerun_ref among rerun_ref, timed_ref, local_run_ref, journal_ref - never a bare claim). A PASSED finding on historical or no proof stands open, named in its gaps: no inheritance. A ROADED finding stands held only with a named owner and something recorded - ownerless is a wish, silent is not a road. The M-016 baseline proved no real screen-reader pass and found muted contrast failing; those checks face the gate as data here, not as inherited passes.

Honest boundary: this layer holds entries, records, standings, verdicts and reports as data. It runs no TUI, times no task, measures no contrast and writes nothing outside the session; the agent layer owns holding a session records and speaking for them.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date as _date
from typing import Dict, Iterable, Optional, Tuple
from .validation import ValidationError

__all__ = [
    "BARE_CLAIMS",
    "DISPOSITIONS",
    "EVIDENCE_KINDS",
    "HELD_EVIDENCE",
    "PLAIN_EXPLANATION",
    "STAGES",
    "TRANSITIONS",
    "USAGE",
    "CHECKS",
    "ACCESSIBILITY_FINAL_SCHEMA",
    "ACCESSIBILITY_FINAL_SLICE",
    "GateStanding",
    "AccessibilityVerdict",
    "GateRecord",
    "AccessibilityReport",
    "CheckEntry",
    "CheckRegistry",
    "default_registry",
    "derive_standing",
    "derive_verdict",
    "format_record",
    "format_records",
    "format_check",
    "format_checks",
    "prepare_report",
]

ACCESSIBILITY_FINAL_SLICE = "M-262"
ACCESSIBILITY_FINAL_SCHEMA = "mythic.accessibility_final/1"

PLAIN_EXPLANATION = (
    "The accessibility final gate, done honestly: "
    "M-199 checks re-run on the shipped TUI, with "
    "the keyboard-only task timed, and the timing "
    "is the evidence. A check counts PASSED only "
    "on the gate own shipped-TUI re-run resting on "
    "held rerun evidence. Every other finding ships "
    "ROADED with a named owner, in the open - an "
    "ownerless road is named, never silent, and "
    "no historical pass is inherited as proof."
)
USAGE = (
    "Record each check finding against its check, "
    "passed on shipped-tui-rerun evidence or roaded "
    "with its owner named; read the derived "
    "accessibility verdict before letting any report "
    "claim the gate closed; prepare a report only as "
    "a report, with every check answered - passed on "
    "held rerun evidence or roaded with an owner - "
    "and let a human share it. The whole M-199 book, "
    "answered check by check, as data first."
)


STAGES = ("named", "rerun", "judged", "dispositioned", "held")
TRANSITIONS = {
    "named": ("rerun",),
    "rerun": ("judged",),
    "judged": ("dispositioned",),
    "dispositioned": ("held",),
    "held": (),
}
HELD_EVIDENCE = ("rerun_ref", "timed_ref", "local_run_ref", "journal_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
EVIDENCE_KINDS = HELD_EVIDENCE + BARE_CLAIMS
REPORT_STATES = ("ready", "shared")
DISPOSITIONS = ("PASSED", "ROADED")
PROOF_KINDS = ("shipped-tui-rerun", "historical-only", "none")
DOCTRINE_REFS = ("M-199", "M-016", "M-198", "M-013")
SUBJECTS = ("keyboard-task", "keyboard-approval", "contrast-body", "contrast-muted", "reduced-motion", "no-colour", "screen-reader", "focus-visible", "alt-text", "shortcut-truth", "setup-traversal", "status-by-text")


def _check_date(value: str) -> None:
    ok = (isinstance(value, str) and len(value) == 10 and value[4] == "-" and value[7] == "-")
    if ok:
        try:
            _date.fromisoformat(value)
        except ValueError:
            ok = False
    if not ok:
        raise ValidationError(f"unknown gate date: {value}")


@dataclass(frozen=True)
class CheckEntry:
    id: str
    doctrine: str
    subject: str
    standing: str
    reason: str
    def validate(self) -> None:
        for name in ("id", "doctrine", "subject", "standing", "reason"):
            if not str(getattr(self, name)).strip():
                raise ValidationError(f"check entry missing {name}")
        if self.doctrine not in DOCTRINE_REFS:
            raise ValidationError(f"unknown check doctrine: {self.doctrine}")
        if self.subject not in SUBJECTS:
            raise ValidationError(f"unknown check subject: {self.subject}")
        if self.standing != "listed":
            raise ValidationError("check entries are listed data only, never a published verdict here; " f"refused standing: {self.standing}")


CHECKS = (
    CheckEntry("A-01", "M-199", "keyboard-task", "listed",
              "the keyboard-only task on the shipped TUI, timed in the accessibility final gate"),
    CheckEntry("A-02", "M-199", "keyboard-approval", "listed",
              "the security approval dialog approved and rejected by keyboard alone on the shipped TUI"),
    CheckEntry("A-03", "M-016", "contrast-body", "listed",
              "body text contrast on every shipped theme, re-measured in the final gate"),
    CheckEntry("A-04", "M-016", "contrast-muted", "listed",
              "muted text contrast, the baseline failure re-measured honestly in the final gate"),
    CheckEntry("A-05", "M-199", "reduced-motion", "listed",
              "reduced motion honoured on request on the shipped TUI"),
    CheckEntry("A-06", "M-199", "no-colour", "listed",
              "meaning surviving without colour on the shipped TUI"),
    CheckEntry("A-07", "M-016", "screen-reader", "listed",
              "a real screen-reader pass, never proven in the baseline, faced in the final gate"),
    CheckEntry("A-08", "M-199", "focus-visible", "listed",
              "focus staying visible through the whole keyboard task"),
    CheckEntry("A-09", "M-016", "alt-text", "listed",
              "text alternatives for the portrait and the splash art"),
    CheckEntry("A-10", "M-016", "shortcut-truth", "listed",
              "the advertised shortcut registry against the keys the shipped TUI actually binds"),
    CheckEntry("A-11", "M-016", "setup-traversal", "listed",
              "the setup wizard traversed by keyboard alone"),
    CheckEntry("A-12", "M-199", "status-by-text", "listed",
              "key statuses carried by text, not by colour alone"),
)


class CheckRegistry:
    def __init__(self, entries: Iterable[CheckEntry] = CHECKS):
        self._entries: Dict[str, CheckEntry] = {}
        for entry in entries:
            entry.validate()
            if entry.id in self._entries:
                raise ValidationError(f"duplicate check: {entry.id}")
            self._entries[entry.id] = entry

    def get(self, check_id: str) -> CheckEntry:
        try:
            return self._entries[check_id]
        except KeyError:
            raise ValidationError(
                f"unknown check: {check_id}") from None

    def ids(self) -> Tuple[str, ...]:
        return tuple(self._entries)

    def entries(self) -> Tuple[CheckEntry, ...]:
        return tuple(self._entries.values())

    def combinations(self) -> Tuple[str, ...]:
        return tuple(self._entries)


def default_registry() -> CheckRegistry:
    return CheckRegistry()


@dataclass(frozen=True)
class GateRecord:
    check: str
    task: str
    date: str
    disposition: str
    owner: str
    proof_kind: str
    stages: Tuple[str, ...]
    claims: Tuple[str, ...]

    def validate(self, registry: Optional[CheckRegistry] = None) -> None:
        (registry or default_registry()).get(self.check)
        if not self.task.strip():
            raise ValidationError("record names no timed task")
        if self.date:
            _check_date(self.date)
        if self.disposition not in DISPOSITIONS:
            raise ValidationError(
                f"unknown record disposition: {self.disposition}")
        if self.proof_kind not in PROOF_KINDS:
            raise ValidationError(f"unknown record proof kind: {self.proof_kind}")
        for kind in self.claims:
            if kind not in EVIDENCE_KINDS:
                raise ValidationError(f"unknown record evidence kind: {kind}")


@dataclass(frozen=True)
class GateStanding:
    held: bool
    stage: str
    grade: str
    gaps: Tuple[str, ...]


def derive_standing(record: GateRecord,
                    registry: Optional[CheckRegistry] = None) -> GateStanding:
    record.validate(registry)
    gaps = []
    stages = record.stages
    if not stages or stages[0] != STAGES[0]:
        gaps.append("record does not open at named")
        stages = stages or ()
    else:
        for prev, nxt in zip(stages, stages[1:]):
            if nxt not in TRANSITIONS.get(prev, ()):
                gaps.append(f"stage step {prev} -> {nxt} not in the walk")
    stage = stages[-1] if stages else "unseen"
    if stage != "held":
        gaps.append(f"record stands at {stage}, not held")
    held_kinds = [c for c in record.claims if c in HELD_EVIDENCE]
    bare = [c for c in record.claims if c in BARE_CLAIMS]
    if not record.date:
        gaps.append("record names no gate date")
    if record.disposition == "PASSED":
        if record.proof_kind != "shipped-tui-rerun":
            gaps.append(
                f"a PASSED finding rests on {record.proof_kind} "
                "evidence, not the final gate's shipped-TUI re-run: "
                "no inheritance")
        if "rerun_ref" not in record.claims:
            gaps.append(
                "the passed finding rests on no held "
                "rerun evidence")
        if not held_kinds:
            gaps.append("record rests on no held evidence")
        if bare and not held_kinds:
            gaps.append("record rests on bare claims only: " + ", ".join(bare))
    else:
        if not record.owner.strip():
            gaps.append(
                "a roaded finding with no owner "
                "named is a wish, not a road")
        if not record.claims:
            gaps.append(
                "a roaded finding with nothing "
                "recorded stands silent, not roaded")
    return GateStanding(held=not gaps, stage=stage,
                           grade="held" if not gaps else "open",
                           gaps=tuple(gaps))


@dataclass(frozen=True)
class AccessibilityVerdict:
    ready: bool
    gaps: Tuple[str, ...]
    passed_checks: Tuple[str, ...]
    roaded_checks: Tuple[str, ...]
    missing_checks: Tuple[str, ...]


def derive_verdict(records: Iterable[GateRecord],
                   registry: Optional[CheckRegistry] = None) -> AccessibilityVerdict:
    reg = registry or default_registry()
    by_check: Dict[str, GateRecord] = {}
    gaps = []
    for record in records:
        record.validate(reg)
        if record.check in by_check:
            gaps.append(
                f"check {record.check} carries two findings")
        else:
            by_check[record.check] = record
    missing = tuple(aid for aid in reg.combinations()
                    if aid not in by_check)
    for check_id in missing:
        gaps.append(f"check {check_id} has no finding in the book")
    fixed = []
    roaded = []
    for check_id, record in by_check.items():
        standing = derive_standing(record, reg)
        if standing.held and record.disposition == "PASSED":
            fixed.append(check_id)
        if standing.held and record.disposition == "ROADED":
            roaded.append(check_id)
        if not standing.held:
            gaps.append(
                f"check {check_id} stands open: "
                + "; ".join(standing.gaps))
    return AccessibilityVerdict(ready=not gaps, gaps=tuple(gaps),
                        passed_checks=tuple(fixed),
                        roaded_checks=tuple(roaded),
                        missing_checks=missing)


@dataclass(frozen=True)
class AccessibilityReport:
    book: str
    entry: str
    report: str
    date: str
    passed_count: int
    roaded_count: int
    total_checks: int
    claims: Tuple[str, ...]
    state: str = "ready"
    certified: bool = False
    inflated: bool = False

    def validate(self, registry: Optional[CheckRegistry] = None) -> None:
        reg = registry or default_registry()
        if not self.book.strip():
            raise ValidationError("report names no book")
        if not self.entry.strip():
            raise ValidationError("report names no entry")
        if not self.report.strip():
            raise ValidationError("final-gate report reports nothing")
        if not self.date:
            raise ValidationError(
                "report names no date: a final-gate "
                "report is reported with its date")
        _check_date(self.date)
        expected = len(reg.combinations())
        if self.total_checks != expected:
            raise ValidationError(
                f"report book holds {self.total_checks} "
                f"checks, not the road's {expected}")
        if self.passed_count < 0 or self.roaded_count < 0:
            raise ValidationError(
                "unknown check count: "
                f"{self.passed_count}/{self.roaded_count}")
        if self.passed_count + self.roaded_count > self.total_checks:
            raise ValidationError(
                "answered checks exceed the book: "
                f"{self.passed_count} + {self.roaded_count} "
                f"of {self.total_checks}")
        for kind in self.claims:
            if kind not in EVIDENCE_KINDS:
                raise ValidationError(f"unknown report evidence kind: {kind}")
        if not [c for c in self.claims if c in HELD_EVIDENCE]:
            raise ValidationError(
                "final-gate reports report held findings "
                "only; a report dressing a bare claim "
                "as a proof refuses here")
        if self.state not in REPORT_STATES:
            raise ValidationError(
                "final-gate reports stand ready or shared "
                "only, never sealed or locked; refused "
                f"state: {self.state}")
        if self.certified and \
                self.passed_count + self.roaded_count < self.total_checks:
            raise ValidationError(
                "an unanswered check anywhere stops "
                "the closing claim: this report may not "
                "claim the gate closed short of "
                "every check answered")
        if self.inflated:
            raise ValidationError(
                "final-gate reports report the findings "
                "exactly as they were dispositioned; a "
                "report is never inflated here")


def prepare_report(book: str, entry: str, report: str,
                   date: str, passed_count: int, roaded_count: int,
                   total_checks: int,
                   claims: Tuple[str, ...] = (),
                   state: str = "ready",
                   certified: bool = False) -> AccessibilityReport:
    made = AccessibilityReport(book=book, entry=entry,
                       report=report, date=date,
                       passed_count=passed_count,
                       roaded_count=roaded_count,
                       total_checks=total_checks,
                       claims=tuple(claims),
                       state=state, certified=certified)
    made.validate()
    return made


def format_check(entry: CheckEntry) -> str:
    return (f"{entry.id} {entry.doctrine}/{entry.subject}: "
            f"standing {entry.standing} "
            f"- {entry.reason}")


def format_checks(registry: Optional[CheckRegistry] = None) -> str:
    reg = registry or default_registry()
    return "\n".join(format_check(e) for e in reg.entries())


def format_record(record: GateRecord,
                  registry: Optional[CheckRegistry] = None) -> str:
    reg = registry or default_registry()
    entry = reg.get(record.check)
    standing = derive_standing(record, reg)
    state = "held as answered" if standing.held else "open: " + "; ".join(standing.gaps)
    return (f"{record.check} {entry.doctrine}/{entry.subject}: "
            f"disposition {record.disposition} "
            f"({record.proof_kind}), date "
            f"{record.date or '(no date)'} - {state}")


def format_records(records: Iterable[GateRecord],
                   registry: Optional[CheckRegistry] = None) -> str:
    return "\n".join(format_record(r, registry) for r in records)
