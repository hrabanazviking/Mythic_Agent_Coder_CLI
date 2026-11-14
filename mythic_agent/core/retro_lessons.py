"""The retro and lessons book (roadmap slice M-271) - pure layer.

Part XI - Proof. The roadmap words: **the campaign retrospective written into the Self-Improving ledger; patterns worth keeping named as skills.**

What this layer holds, as data: a retro registry L-01..L-12 (the lessons and patterns this campaign taught, from banking discipline to ledger capture), each listed only, each labelled and evidenced; a retro record per lesson holding its work, date, disposition KEPT or ROADED or DROPPED, owner, proof kind and stage walk named-labelled-evidenced-dispositioned-held; a derived standing; a derived retro verdict over the whole book; and a retro report prepared only through the prepare road, ready or shared, never sealed, inflated or certified short of every lesson answered.

Honesty rule, made code: a pattern counts KEPT only on held proof measured in the campaign itself resting on held evidence written in the ledger (a ledger_ref among evidence_ref, test_ref, ledger_ref, run_ref - never a bare claim). A lesson counts ROADED only where the road it names rests on held evidence and its owner is named in the open. A lesson counts DROPPED only with a named owner and the reason recorded. Silence is not a disposition: a lesson with no record stands missing, named in the verdict gaps.

Honest boundary: this book holds and judges retro records as data; naming a pattern as a skill candidate does not itself publish or install a skill, and the book does not rewrite campaign history. It proves nothing and ships nothing; the agent layer owns holding session records and speaking for them.
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
    "RETRO_ENTRIES",
    "RETRO_LESSONS_SCHEMA",
    "RETRO_LESSONS_SLICE",
    "RetroStanding",
    "RetroVerdict",
    "RetroRecord",
    "RetroReport",
    "RetroEntry",
    "RetroRegistry",
    "default_registry",
    "derive_standing",
    "derive_verdict",
    "format_record",
    "format_records",
    "format_entry",
    "format_entries",
    "prepare_report",
]

RETRO_LESSONS_SLICE = "M-270"
RETRO_LESSONS_SCHEMA = "mythic.retro_lessons/1"

PLAIN_EXPLANATION = (
    "The campaign retro, done honestly: "
    "the retrospective written into the "
    "self-improving ledger, lesson by lesson, "
    "with patterns worth keeping named as "
    "skill candidates. A pattern counts KEPT "
    "only on held campaign evidence written "
    "in the ledger, a lesson counts ROADED "
    "only where its road rests on held "
    "evidence and its owner is named, and a "
    "lesson counts DROPPED only with its "
    "reason recorded - never silent, never "
    "inflated, never dressed as kept.")


USAGE = (
    "Record each lesson against its entry, "
    "kept on held ledger evidence, roaded "
    "with its owner and road, or dropped "
    "with its reason recorded; read the "
    "derived retro verdict before letting "
    "any report claim the retro written; "
    "prepare a report only as a report, with "
    "every lesson answered - kept, roaded "
    "or dropped, each in the open - and "
    "let a human share it. The whole campaign "
    "retro, answered lesson by lesson, as data "
    "first.")


STAGES = ("named", "labelled", "evidenced", "dispositioned", "held")
TRANSITIONS = {
    "named": ("labelled",),
    "labelled": ("evidenced",),
    "evidenced": ("dispositioned",),
    "dispositioned": ("held",),
    "held": (),
}
HELD_EVIDENCE = ("evidence_ref", "test_ref", "ledger_ref", "run_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
EVIDENCE_KINDS = HELD_EVIDENCE + BARE_CLAIMS
REPORT_STATES = ("ready", "shared")
DISPOSITIONS = ("KEPT", "ROADED", "DROPPED")
PROOF_KINDS = ("kept-and-held", "roaded-open", "none")
DOCTRINE_REFS = ("campaign-evidence", "self-improving", "forge-method", "keeper-law")
SUBJECTS = ("banking-discipline", "stall-guard", "verify-from-disk", "closure-heals", "env-classification", "pure-book-pattern", "journal-first", "refspec-push", "roadmap-order", "boundary-pins", "honest-boundary", "ledger-capture")

def _check_date(value: str) -> None:
    ok = (isinstance(value, str) and len(value) == 10 and value[4] == "-" and value[7] == "-")
    if ok:
        try:
            _date.fromisoformat(value)
        except ValueError:
            ok = False
    if not ok:
        raise ValidationError(f"unknown report date: {value}")


@dataclass(frozen=True)
class RetroEntry:
    id: str
    doctrine: str
    subject: str
    standing: str
    reason: str
    labelled: bool = True
    evidenced: bool = True

    def validate(self) -> None:
        for name in ("id", "doctrine", "subject", "standing", "reason"):
            if not str(getattr(self, name)).strip():
                raise ValidationError(f"lesson entry missing {name}")
        if self.doctrine not in DOCTRINE_REFS:
            raise ValidationError(f"unknown lesson doctrine: {self.doctrine}")
        if self.subject not in SUBJECTS:
            raise ValidationError(f"unknown lesson subject: {self.subject}")
        if self.standing != "listed":
            raise ValidationError("lesson entries are listed data only, never a published verdict here; " f"refused standing: {self.standing}")
        if not self.labelled:
            raise ValidationError("lesson entries are labelled only; " f"refused unlabelled entry: {self.id}")
        if not self.evidenced:
            raise ValidationError("lesson entries are evidenced only; " f"refused unevidenced entry: {self.id}")


RETRO_ENTRIES = (
    RetroEntry("L-01", "campaign-evidence", "banking-discipline", "listed", "banking in roadmap order with the remote verified after every slice, learned across the whole campaign"),
    RetroEntry("L-02", "keeper-law", "stall-guard", "listed", "the ten-minute minder restarts stopped work and never merely reports, learned when teams stalled between ticks"),
    RetroEntry("L-03", "campaign-evidence", "verify-from-disk", "listed", "counts come only from git and the test runner on disk, never from a worker report"),
    RetroEntry("L-04", "forge-method", "closure-heals", "listed", "closure heals the inventory failures a slice creates, in the same banking, never left for later"),
    RetroEntry("L-05", "campaign-evidence", "env-classification", "listed", "environment failures are named and proven by solo re-runs, never counted as code defects"),
    RetroEntry("L-06", "forge-method", "pure-book-pattern", "listed", "each slice lands as a pure book of data first, with standing derived at call time, never stored"),
    RetroEntry("L-07", "self-improving", "journal-first", "listed", "session news is journaled before it is shown, so a crash never loses the record"),
    RetroEntry("L-08", "keeper-law", "refspec-push", "listed", "pushes use an explicit refspec with an ancestor check and are never forced"),
    RetroEntry("L-09", "forge-method", "roadmap-order", "listed", "slices are taken strictly in roadmap order, one per team, never skipped or duplicated"),
    RetroEntry("L-10", "campaign-evidence", "boundary-pins", "listed", "roadmap-boundary pins move with each closure, matching the slices that remain"),
    RetroEntry("L-11", "self-improving", "honest-boundary", "listed", "every book names what it does not do, in its own docstring, before any claim is made"),
    RetroEntry("L-12", "self-improving", "ledger-capture", "listed", "lessons worth keeping are written into the self-improving ledger as data, with their evidence"),
)


class RetroRegistry:
    def __init__(self, entries: Iterable[RetroEntry] = RETRO_ENTRIES):
        self._entries: Dict[str, RetroEntry] = {}
        for entry in entries:
            entry.validate()
            if entry.id in self._entries:
                raise ValidationError(f"duplicate lesson: {entry.id}")
            self._entries[entry.id] = entry

    def get(self, lesson_id: str) -> RetroEntry:
        try:
            return self._entries[lesson_id]
        except KeyError:
            raise ValidationError(
                f"unknown lesson: {lesson_id}") from None

    def ids(self) -> Tuple[str, ...]:
        return tuple(self._entries)

    def entries(self) -> Tuple[RetroEntry, ...]:
        return tuple(self._entries.values())

    def combinations(self) -> Tuple[str, ...]:
        return tuple(self._entries)


def default_registry() -> RetroRegistry:
    return RetroRegistry()


@dataclass(frozen=True)
class RetroRecord:
    lesson: str
    work: str
    date: str
    disposition: str
    owner: str
    proof_kind: str
    stages: Tuple[str, ...]
    claims: Tuple[str, ...]

    def validate(self, registry: Optional[RetroRegistry] = None) -> None:
        (registry or default_registry()).get(self.lesson)
        if not self.work.strip():
            raise ValidationError("record names no lesson work")
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
class RetroStanding:
    held: bool
    stage: str
    grade: str
    gaps: Tuple[str, ...]


def derive_standing(record: RetroRecord,
                    registry: Optional[RetroRegistry] = None) -> RetroStanding:
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
        gaps.append("record names no report date")
    if record.disposition == "KEPT":
        if record.proof_kind != "kept-and-held":
            gaps.append(
                f"a KEPT lesson rests on {record.proof_kind} "
                "evidence, not held proof measured in the campaign itself: "
                "the lesson tells the truth or stands open")
        if "ledger_ref" not in record.claims:
            gaps.append(
                "the kept lesson rests on no held "
                "held evidence")
        if not held_kinds:
            gaps.append("record rests on no held evidence")
        if bare and not held_kinds:
            gaps.append("record rests on bare claims only: " + ", ".join(bare))
    else:
        if not record.owner.strip():
            gaps.append(
                "a roaded or dropped lesson with no owner "
                "named is a wish, not a road")
        if not record.claims:
            gaps.append(
                "a roaded or dropped lesson with nothing "
                "recorded stands silent, not answered")
        if record.disposition == "ROADED" and not held_kinds:
            gaps.append(
                "a roaded lesson rests on no held "
                "evidence: the road it names must rest "
                "on held evidence, not on a claim")
        if record.disposition == "DROPPED" and record.proof_kind == "kept-and-held":
            gaps.append(
                "a DROPPED lesson resting on full "
                "measured proof contradicts itself: "
                "re-disposition it KEPT or ROADED")
    return RetroStanding(held=not gaps, stage=stage,
                           grade="held" if not gaps else "open",
                           gaps=tuple(gaps))


@dataclass(frozen=True)
class RetroVerdict:
    ready: bool
    gaps: Tuple[str, ...]
    kept_lessons: Tuple[str, ...]
    roaded_lessons: Tuple[str, ...]
    dropped_lessons: Tuple[str, ...]
    missing_lessons: Tuple[str, ...]


def derive_verdict(records: Iterable[RetroRecord],
                   registry: Optional[RetroRegistry] = None) -> RetroVerdict:
    reg = registry or default_registry()
    by_lesson: Dict[str, RetroRecord] = {}
    gaps = []
    for record in records:
        record.validate(reg)
        if record.lesson in by_lesson:
            gaps.append(
                f"lesson {record.lesson} carries two records")
        else:
            by_lesson[record.lesson] = record
    missing = tuple(aid for aid in reg.combinations()
                    if aid not in by_lesson)
    for lesson_id in missing:
        gaps.append(f"lesson {lesson_id} has no record in the book")
    kept = []
    roaded = []
    dropped = []
    for lesson_id, record in by_lesson.items():
        standing = derive_standing(record, reg)
        if standing.held and record.disposition == "KEPT":
            kept.append(lesson_id)
        if standing.held and record.disposition == "ROADED":
            roaded.append(lesson_id)
        if standing.held and record.disposition == "DROPPED":
            dropped.append(lesson_id)
        if not standing.held:
            gaps.append(
                f"lesson {lesson_id} stands open: "
                + "; ".join(standing.gaps))
    return RetroVerdict(ready=not gaps, gaps=tuple(gaps),
                        kept_lessons=tuple(kept),
                        roaded_lessons=tuple(roaded),
                        dropped_lessons=tuple(dropped), missing_lessons=missing)


@dataclass(frozen=True)
class RetroReport:
    book: str
    entry: str
    report: str
    date: str
    kept_count: int
    roaded_count: int
    dropped_count: int
    total_lessons: int
    claims: Tuple[str, ...]
    state: str = "ready"
    certified: bool = False
    inflated: bool = False

    def validate(self, registry: Optional[RetroRegistry] = None) -> None:
        reg = registry or default_registry()
        if not self.book.strip():
            raise ValidationError("report names no book")
        if not self.entry.strip():
            raise ValidationError("report names no entry")
        if not self.report.strip():
            raise ValidationError("lesson reports nothing")
        if not self.date:
            raise ValidationError(
                "report names no date: a retro "
                "report is reported with its date")
        _check_date(self.date)
        expected = len(reg.combinations())
        if self.total_lessons != expected:
            raise ValidationError(
                f"report book holds {self.total_lessons} "
                f"lessons, not the road's {expected}")
        if self.kept_count < 0 or self.roaded_count < 0 or self.dropped_count < 0:
            raise ValidationError(
                "unknown lesson count: "
                f"{self.kept_count}/{self.roaded_count}/{self.dropped_count}")
        if self.kept_count + self.roaded_count + self.dropped_count > self.total_lessons:
            raise ValidationError(
                "answered lessons exceed the book: "
                f"{self.kept_count} + {self.roaded_count} + {self.dropped_count} "
                f"of {self.total_lessons}")
        for kind in self.claims:
            if kind not in EVIDENCE_KINDS:
                raise ValidationError(f"unknown report evidence kind: {kind}")
        if not [c for c in self.claims if c in HELD_EVIDENCE]:
            raise ValidationError(
                "lessons report held findings "
                "only; a report dressing a bare claim "
                "as a proof refuses here")
        if self.state not in REPORT_STATES:
            raise ValidationError(
                "retro reports stand ready or shared "
                "only, never sealed or locked; refused "
                f"state: {self.state}")
        if self.certified and \
                self.kept_count + self.roaded_count + self.dropped_count < self.total_lessons:
            raise ValidationError(
                "an unanswered lesson anywhere stops "
                "the closing claim: this report may not "
                "claim the retro complete short of "
                "every lesson answered")
        if self.inflated:
            raise ValidationError(
                "retro reports report the findings "
                "exactly as they were dispositioned; a "
                "report is never inflated here")


def prepare_report(book: str, entry: str, report: str,
                   date: str, kept_count: int, roaded_count: int, dropped_count: int,
                   total_lessons: int,
                   claims: Tuple[str, ...] = (),
                   state: str = "ready",
                   certified: bool = False) -> RetroReport:
    made = RetroReport(book=book, entry=entry,
                       report=report, date=date,
                       kept_count=kept_count,
                       roaded_count=roaded_count,
                       dropped_count=dropped_count,
                       total_lessons=total_lessons,
                       claims=tuple(claims),
                       state=state, certified=certified)
    made.validate()
    return made


def format_entry(entry: RetroEntry) -> str:
    return (f"{entry.id} {entry.doctrine}/{entry.subject}: "
            f"standing {entry.standing} "
            f"- {entry.reason}")


def format_entries(registry: Optional[RetroRegistry] = None) -> str:
    reg = registry or default_registry()
    return "\n".join(format_entry(e) for e in reg.entries())


def format_record(record: RetroRecord,
                  registry: Optional[RetroRegistry] = None) -> str:
    reg = registry or default_registry()
    entry = reg.get(record.lesson)
    standing = derive_standing(record, reg)
    state = "held as answered" if standing.held else "open: " + "; ".join(standing.gaps)
    return (f"{record.lesson} {entry.doctrine}/{entry.subject}: "
            f"disposition {record.disposition} "
            f"({record.proof_kind}), date "
            f"{record.date or '(no date)'} - {state}")


def format_records(records: Iterable[RetroRecord],
                   registry: Optional[RetroRegistry] = None) -> str:
    return "\n".join(format_record(r, registry) for r in records)
