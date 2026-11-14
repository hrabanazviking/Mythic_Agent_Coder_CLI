"""The stranger-fleet-test book (roadmap slice M-266) - pure layer.

Part XI - Proof. The roadmap words: **M-200's stranger + a headless CI run + a crew campaign, all from docs alone, on a clean machine.**

What this layer holds, as data: an exercise registry F-01..F-03 (the stranger task, the headless CI run, the crew campaign), each listed only, each docs-only and clean-machine; a fleet record per exercise holding its exercise work, date, disposition PROVEN or ROADED, owner, proof kind and stage walk named-attempted-checked-dispositioned-held; a derived standing; a derived fleet verdict over the whole book; and a fleet report prepared only through the prepare road, ready or shared, never sealed, inflated or certified short of every exercise answered.

Honesty rule, made code: an exercise counts PROVEN only on a docs-only run on a clean machine resting on held evidence (a run_ref among run_ref, report_ref, log_ref, transcript_ref - never a bare claim). A PROVEN finding on secondhand or no proof stands open, named in its gaps: no secondhand proof. A ROADED finding stands held only with a named owner and something recorded - ownerless is a wish, silent is not a road. A fleet claimed passed on secondhand word, not on a docs-only clean-machine run, faces the book as data here, not as an inherited truth.

Honest boundary: this book holds and judges exercise records as data; it does not itself run a stranger, a CI fleet, or a crew campaign. It runs no stranger, starts no CI and crews no campaign; the agent layer owns holding session records and speaking for them.
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
    "EXERCISES",
    "STRANGER_FLEET_TEST_SCHEMA",
    "STRANGER_FLEET_TEST_SLICE",
    "StrangerFleetStanding",
    "StrangerFleetVerdict",
    "StrangerFleetRecord",
    "StrangerFleetReport",
    "StrangerFleetEntry",
    "StrangerFleetRegistry",
    "default_registry",
    "derive_standing",
    "derive_verdict",
    "format_record",
    "format_records",
    "format_exercise",
    "format_exercises",
    "prepare_report",
]

STRANGER_FLEET_TEST_SLICE = "M-266"
STRANGER_FLEET_TEST_SCHEMA = "mythic.stranger_fleet_test/1"

PLAIN_EXPLANATION = (
    "The stranger fleet test, done honestly: "
    "M-200's stranger, a headless CI run and a "
    "crew campaign, all from docs alone, on a "
    "clean machine. An exercise counts PROVEN "
    "only on a docs-only clean-machine run "
    "resting on held evidence. Every other "
    "exercise ships ROADED with a named owner, "
    "in the open - an ownerless road is named, "
    "never silent, and no exercise is claimed "
    "passed from secondhand word."
)
USAGE = (
    "Record each exercise finding against its "
    "exercise, proven by a docs-only run on a "
    "clean machine or roaded with its owner "
    "named; read the derived fleet verdict "
    "before letting any report claim the fleet "
    "test complete; prepare a report only as "
    "a report, with every exercise answered - "
    "proven on held evidence or roaded with an "
    "owner - and let a human share it. The whole "
    "fleet book, answered exercise by exercise, "
    "as data first."
)


STAGES = ("named", "attempted", "checked", "dispositioned", "held")
TRANSITIONS = {
    "named": ("attempted",),
    "attempted": ("checked",),
    "checked": ("dispositioned",),
    "dispositioned": ("held",),
    "held": (),
}
HELD_EVIDENCE = ("run_ref", "report_ref", "log_ref", "transcript_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
EVIDENCE_KINDS = HELD_EVIDENCE + BARE_CLAIMS
REPORT_STATES = ("ready", "shared")
DISPOSITIONS = ("PROVEN", "ROADED")
PROOF_KINDS = ("docs-only-clean-machine", "secondhand-only", "none")
DOCTRINE_REFS = ("stranger-duty", "ci-duty", "crew-duty", "proof-duty")
SUBJECTS = ("stranger-task", "headless-ci-run", "crew-campaign")


def _check_date(value: str) -> None:
    ok = (isinstance(value, str) and len(value) == 10 and value[4] == "-" and value[7] == "-")
    if ok:
        try:
            _date.fromisoformat(value)
        except ValueError:
            ok = False
    if not ok:
        raise ValidationError(f"unknown fleet date: {value}")


@dataclass(frozen=True)
class StrangerFleetEntry:
    id: str
    doctrine: str
    subject: str
    standing: str
    reason: str
    docs_only: bool = True
    clean_machine: bool = True
    def validate(self) -> None:
        for name in ("id", "doctrine", "subject", "standing", "reason"):
            if not str(getattr(self, name)).strip():
                raise ValidationError(f"exercise entry missing {name}")
        if self.doctrine not in DOCTRINE_REFS:
            raise ValidationError(f"unknown exercise doctrine: {self.doctrine}")
        if self.subject not in SUBJECTS:
            raise ValidationError(f"unknown exercise subject: {self.subject}")
        if self.standing != "listed":
            raise ValidationError("exercise entries are listed data only, never a published verdict here; " f"refused standing: {self.standing}")
        if not self.docs_only:
            raise ValidationError("exercise entries are docs-only only; " f"refused non-docs-only entry: {self.id}")
        if not self.clean_machine:
            raise ValidationError("exercise entries are clean-machine only; " f"refused non-clean-machine entry: {self.id}")


EXERCISES = (
    StrangerFleetEntry("F-01", "stranger-duty", "stranger-task", "listed",
              "M-200's stranger: a new user, docs only, completes a real task in the TUI inside thirty minutes, on a clean machine"),
    StrangerFleetEntry("F-02", "ci-duty", "headless-ci-run", "listed",
              "a headless CI run set up and run from docs alone, on a clean machine, from first step to green"),
    StrangerFleetEntry("F-03", "crew-duty", "crew-campaign", "listed",
              "a crew campaign planned and run from docs alone, on a clean machine, crews flowing slice to slice"),
)


class StrangerFleetRegistry:
    def __init__(self, entries: Iterable[StrangerFleetEntry] = EXERCISES):
        self._entries: Dict[str, StrangerFleetEntry] = {}
        for entry in entries:
            entry.validate()
            if entry.id in self._entries:
                raise ValidationError(f"duplicate exercise: {entry.id}")
            self._entries[entry.id] = entry

    def get(self, exercise_id: str) -> StrangerFleetEntry:
        try:
            return self._entries[exercise_id]
        except KeyError:
            raise ValidationError(
                f"unknown exercise: {exercise_id}") from None

    def ids(self) -> Tuple[str, ...]:
        return tuple(self._entries)

    def entries(self) -> Tuple[StrangerFleetEntry, ...]:
        return tuple(self._entries.values())

    def combinations(self) -> Tuple[str, ...]:
        return tuple(self._entries)


def default_registry() -> StrangerFleetRegistry:
    return StrangerFleetRegistry()


@dataclass(frozen=True)
class StrangerFleetRecord:
    exercise: str
    work: str
    date: str
    disposition: str
    owner: str
    proof_kind: str
    stages: Tuple[str, ...]
    claims: Tuple[str, ...]

    def validate(self, registry: Optional[StrangerFleetRegistry] = None) -> None:
        (registry or default_registry()).get(self.exercise)
        if not self.work.strip():
            raise ValidationError("record names no exercise work")
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
class StrangerFleetStanding:
    held: bool
    stage: str
    grade: str
    gaps: Tuple[str, ...]


def derive_standing(record: StrangerFleetRecord,
                    registry: Optional[StrangerFleetRegistry] = None) -> StrangerFleetStanding:
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
        gaps.append("record names no fleet date")
    if record.disposition == "PROVEN":
        if record.proof_kind != "docs-only-clean-machine":
            gaps.append(
                f"a PROVEN exercise rests on {record.proof_kind} "
                "evidence, not a docs-only run on a clean machine: "
                "no secondhand proof")
        if "run_ref" not in record.claims:
            gaps.append(
                "the proven exercise rests on no held "
                "run evidence")
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
    return StrangerFleetStanding(held=not gaps, stage=stage,
                           grade="held" if not gaps else "open",
                           gaps=tuple(gaps))


@dataclass(frozen=True)
class StrangerFleetVerdict:
    ready: bool
    gaps: Tuple[str, ...]
    proven_exercises: Tuple[str, ...]
    roaded_exercises: Tuple[str, ...]
    missing_exercises: Tuple[str, ...]


def derive_verdict(records: Iterable[StrangerFleetRecord],
                   registry: Optional[StrangerFleetRegistry] = None) -> StrangerFleetVerdict:
    reg = registry or default_registry()
    by_exercise: Dict[str, StrangerFleetRecord] = {}
    gaps = []
    for record in records:
        record.validate(reg)
        if record.exercise in by_exercise:
            gaps.append(
                f"exercise {record.exercise} carries two findings")
        else:
            by_exercise[record.exercise] = record
    missing = tuple(aid for aid in reg.combinations()
                    if aid not in by_exercise)
    for exercise_id in missing:
        gaps.append(f"exercise {exercise_id} has no finding in the book")
    fixed = []
    roaded = []
    for exercise_id, record in by_exercise.items():
        standing = derive_standing(record, reg)
        if standing.held and record.disposition == "PROVEN":
            fixed.append(exercise_id)
        if standing.held and record.disposition == "ROADED":
            roaded.append(exercise_id)
        if not standing.held:
            gaps.append(
                f"exercise {exercise_id} stands open: "
                + "; ".join(standing.gaps))
    return StrangerFleetVerdict(ready=not gaps, gaps=tuple(gaps),
                        proven_exercises=tuple(fixed),
                        roaded_exercises=tuple(roaded),
                        missing_exercises=missing)


@dataclass(frozen=True)
class StrangerFleetReport:
    book: str
    entry: str
    report: str
    date: str
    proven_count: int
    roaded_count: int
    total_exercises: int
    claims: Tuple[str, ...]
    state: str = "ready"
    certified: bool = False
    inflated: bool = False

    def validate(self, registry: Optional[StrangerFleetRegistry] = None) -> None:
        reg = registry or default_registry()
        if not self.book.strip():
            raise ValidationError("report names no book")
        if not self.entry.strip():
            raise ValidationError("report names no entry")
        if not self.report.strip():
            raise ValidationError("fleet report reports nothing")
        if not self.date:
            raise ValidationError(
                "report names no date: a fleet "
                "report is reported with its date")
        _check_date(self.date)
        expected = len(reg.combinations())
        if self.total_exercises != expected:
            raise ValidationError(
                f"report book holds {self.total_exercises} "
                f"exercises, not the road's {expected}")
        if self.proven_count < 0 or self.roaded_count < 0:
            raise ValidationError(
                "unknown exercise count: "
                f"{self.proven_count}/{self.roaded_count}")
        if self.proven_count + self.roaded_count > self.total_exercises:
            raise ValidationError(
                "answered exercises exceed the book: "
                f"{self.proven_count} + {self.roaded_count} "
                f"of {self.total_exercises}")
        for kind in self.claims:
            if kind not in EVIDENCE_KINDS:
                raise ValidationError(f"unknown report evidence kind: {kind}")
        if not [c for c in self.claims if c in HELD_EVIDENCE]:
            raise ValidationError(
                "fleet reports report held findings "
                "only; a report dressing a bare claim "
                "as a proof refuses here")
        if self.state not in REPORT_STATES:
            raise ValidationError(
                "fleet reports stand ready or shared "
                "only, never sealed or locked; refused "
                f"state: {self.state}")
        if self.certified and \
                self.proven_count + self.roaded_count < self.total_exercises:
            raise ValidationError(
                "an unanswered exercise anywhere stops "
                "the closing claim: this report may not "
                "claim the fleet test complete short of "
                "every exercise answered")
        if self.inflated:
            raise ValidationError(
                "fleet reports report the findings "
                "exactly as they were dispositioned; a "
                "report is never inflated here")


def prepare_report(book: str, entry: str, report: str,
                   date: str, proven_count: int, roaded_count: int,
                   total_exercises: int,
                   claims: Tuple[str, ...] = (),
                   state: str = "ready",
                   certified: bool = False) -> StrangerFleetReport:
    made = StrangerFleetReport(book=book, entry=entry,
                       report=report, date=date,
                       proven_count=proven_count,
                       roaded_count=roaded_count,
                       total_exercises=total_exercises,
                       claims=tuple(claims),
                       state=state, certified=certified)
    made.validate()
    return made


def format_exercise(entry: StrangerFleetEntry) -> str:
    return (f"{entry.id} {entry.doctrine}/{entry.subject}: "
            f"standing {entry.standing} "
            f"- {entry.reason}")


def format_exercises(registry: Optional[StrangerFleetRegistry] = None) -> str:
    reg = registry or default_registry()
    return "\n".join(format_exercise(e) for e in reg.entries())


def format_record(record: StrangerFleetRecord,
                  registry: Optional[StrangerFleetRegistry] = None) -> str:
    reg = registry or default_registry()
    entry = reg.get(record.exercise)
    standing = derive_standing(record, reg)
    state = "held as answered" if standing.held else "open: " + "; ".join(standing.gaps)
    return (f"{record.exercise} {entry.doctrine}/{entry.subject}: "
            f"disposition {record.disposition} "
            f"({record.proof_kind}), date "
            f"{record.date or '(no date)'} - {state}")


def format_records(records: Iterable[StrangerFleetRecord],
                   registry: Optional[StrangerFleetRegistry] = None) -> str:
    return "\n".join(format_record(r, registry) for r in records)
