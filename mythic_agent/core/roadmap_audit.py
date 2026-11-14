"""The roadmap audit book (roadmap slice M-270) - pure layer.

Part XI - Proof. The roadmap words: **every slice marked DONE with evidence, PARTIAL with its road, or NOT PROVEN with its reason - in this file closing twin.**

What this layer holds, as data: a roadmap registry A-01..A-12 (the eleven roadmap parts and the closing twin), each listed only, each labelled and evidenced; an audit record per part holding its truth work, date, disposition DONE or PARTIAL or NOT_PROVEN, owner, proof kind and stage walk named-labelled-evidenced-dispositioned-held; a derived standing; a derived audit verdict over the whole book; and an audit report prepared only through the prepare road, ready or shared, never sealed, inflated or certified short of every part answered.

Honesty rule, made code: a part counts DONE only on held proof measured in the campaign itself resting on held evidence (an evidence_ref among evidence_ref, test_ref, run_ref, ledger_ref - never a bare claim). A part counts PARTIAL only where the done part rests on held evidence and the remainder is owned and roaded in the open. A part counts NOT_PROVEN only with a named owner and the reason recorded. Silence is not a label: a part with no record stands missing, named in the verdict gaps.

Honest boundary: this book holds and judges audit records as data; it does not itself rewrite the roadmap or bank slices. It proves nothing and ships nothing; the agent layer owns holding session records and speaking for them.
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
    "AUDIT_PARTS",
    "ROADMAP_AUDIT_SCHEMA",
    "ROADMAP_AUDIT_SLICE",
    "RoadmapAuditStanding",
    "RoadmapAuditVerdict",
    "RoadmapAuditRecord",
    "RoadmapAuditReport",
    "RoadmapAuditEntry",
    "RoadmapAuditRegistry",
    "default_registry",
    "derive_standing",
    "derive_verdict",
    "format_record",
    "format_records",
    "format_part",
    "format_parts",
    "prepare_report",
]

ROADMAP_AUDIT_SLICE = "M-270"
ROADMAP_AUDIT_SCHEMA = "mythic.roadmap_audit/1"

PLAIN_EXPLANATION = (
    "The roadmap audit, done honestly: "
    "DONE with evidence, PARTIAL with its "
    "road, or NOT PROVEN with its reason, per "
    "roadmap part, printed in the closing twin. A "
    "part counts DONE only on held proof, "
    "PARTIAL only where the done part rests on "
    "held evidence and the rest is roaded in "
    "the open, and NOT PROVEN only with its "
    "reason recorded - never silent, never "
    "inflated, never dressed as done.")


USAGE = (
    "Record each audit finding against its "
    "part, done on held evidence, partial "
    "with the done part evidenced and the "
    "remainder roaded, or not proven with "
    "its owner and reason recorded; read the "
    "derived audit verdict before letting "
    "any report claim the roadmap answered; "
    "prepare a report only as a report, with "
    "every part answered - done, partial "
    "or not proven, each in the open - and "
    "let a human share it. The whole roadmap "
    "book, answered part by part, as data "
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
DISPOSITIONS = ("DONE", "PARTIAL", "NOT_PROVEN")
PROOF_KINDS = ("done-and-held", "partially-held", "none")
DOCTRINE_REFS = ("audit-truth", "evidence-law", "road-honesty", "audit-duty")
SUBJECTS = ("part-01", "part-02", "part-03", "part-04", "part-05", "part-06", "part-07", "part-08", "part-09", "part-10", "part-11", "closing-twin")


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
class RoadmapAuditEntry:
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
                raise ValidationError(f"part entry missing {name}")
        if self.doctrine not in DOCTRINE_REFS:
            raise ValidationError(f"unknown part doctrine: {self.doctrine}")
        if self.subject not in SUBJECTS:
            raise ValidationError(f"unknown part subject: {self.subject}")
        if self.standing != "listed":
            raise ValidationError("part entries are listed data only, never a published verdict here; " f"refused standing: {self.standing}")
        if not self.labelled:
            raise ValidationError("part entries are labelled only; " f"refused unlabelled entry: {self.id}")
        if not self.evidenced:
            raise ValidationError("part entries are evidenced only; " f"refused unevidenced entry: {self.id}")


AUDIT_PARTS = (
    RoadmapAuditEntry("A-01", "audit-truth", "part-01", "listed", "part one of the roadmap: its slices, each answered done, partial or not proven on held evidence"),
    RoadmapAuditEntry("A-02", "evidence-law", "part-02", "listed", "part two of the roadmap: its slices, each answered in the open, none silent"),
    RoadmapAuditEntry("A-03", "audit-truth", "part-03", "listed", "part three of the roadmap: its slices, each answered done, partial or not proven on held evidence"),
    RoadmapAuditEntry("A-04", "road-honesty", "part-04", "listed", "part four of the roadmap: its slices, each answered with its road where partial"),
    RoadmapAuditEntry("A-05", "evidence-law", "part-05", "listed", "part five of the roadmap: its slices, each answered in the open, none silent"),
    RoadmapAuditEntry("A-06", "audit-truth", "part-06", "listed", "part six of the roadmap: its slices, each answered done, partial or not proven on held evidence"),
    RoadmapAuditEntry("A-07", "road-honesty", "part-07", "listed", "part seven of the roadmap: its slices, each answered with its reason where not proven"),
    RoadmapAuditEntry("A-08", "audit-duty", "part-08", "listed", "part eight of the roadmap: its slices, each answered in the open, none silent"),
    RoadmapAuditEntry("A-09", "evidence-law", "part-09", "listed", "part nine of the roadmap: its slices, each answered done, partial or not proven on held evidence"),
    RoadmapAuditEntry("A-10", "audit-truth", "part-10", "listed", "part ten of the roadmap: its slices, each answered with its road where partial"),
    RoadmapAuditEntry("A-11", "road-honesty", "part-11", "listed", "part eleven of the roadmap: its slices, each answered in the open, none silent"),
    RoadmapAuditEntry("A-12", "audit-duty", "closing-twin", "listed", "the closing twin of this roadmap file: every slice answered here, in the twin, as data first"),
)


class RoadmapAuditRegistry:
    def __init__(self, entries: Iterable[RoadmapAuditEntry] = AUDIT_PARTS):
        self._entries: Dict[str, RoadmapAuditEntry] = {}
        for entry in entries:
            entry.validate()
            if entry.id in self._entries:
                raise ValidationError(f"duplicate part: {entry.id}")
            self._entries[entry.id] = entry

    def get(self, part_id: str) -> RoadmapAuditEntry:
        try:
            return self._entries[part_id]
        except KeyError:
            raise ValidationError(
                f"unknown part: {part_id}") from None

    def ids(self) -> Tuple[str, ...]:
        return tuple(self._entries)

    def entries(self) -> Tuple[RoadmapAuditEntry, ...]:
        return tuple(self._entries.values())

    def combinations(self) -> Tuple[str, ...]:
        return tuple(self._entries)


def default_registry() -> RoadmapAuditRegistry:
    return RoadmapAuditRegistry()


@dataclass(frozen=True)
class RoadmapAuditRecord:
    part: str
    work: str
    date: str
    disposition: str
    owner: str
    proof_kind: str
    stages: Tuple[str, ...]
    claims: Tuple[str, ...]

    def validate(self, registry: Optional[RoadmapAuditRegistry] = None) -> None:
        (registry or default_registry()).get(self.part)
        if not self.work.strip():
            raise ValidationError("record names no part work")
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
class RoadmapAuditStanding:
    held: bool
    stage: str
    grade: str
    gaps: Tuple[str, ...]


def derive_standing(record: RoadmapAuditRecord,
                    registry: Optional[RoadmapAuditRegistry] = None) -> RoadmapAuditStanding:
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
    if record.disposition == "DONE":
        if record.proof_kind != "done-and-held":
            gaps.append(
                f"a DONE part rests on {record.proof_kind} "
                "evidence, not held proof measured in the part itself: "
                "the part tells the truth or stands open")
        if "evidence_ref" not in record.claims:
            gaps.append(
                "the done part rests on no held "
                "held evidence")
        if not held_kinds:
            gaps.append("record rests on no held evidence")
        if bare and not held_kinds:
            gaps.append("record rests on bare claims only: " + ", ".join(bare))
    else:
        if not record.owner.strip():
            gaps.append(
                "a partial or not proven finding with no owner "
                "named is a wish, not a road")
        if not record.claims:
            gaps.append(
                "a partial or not proven finding with nothing "
                "recorded stands silent, not answered")
        if record.disposition == "PARTIAL" and not held_kinds:
            gaps.append(
                "a partial part rests on no held "
                "evidence: the done part must rest "
                "on held evidence, not on a claim")
        if record.disposition == "NOT_PROVEN" and record.proof_kind == "done-and-held":
            gaps.append(
                "a NOT_PROVEN part resting on full "
                "measured proof contradicts itself: "
                "re-disposition it DONE or PARTIAL")
    return RoadmapAuditStanding(held=not gaps, stage=stage,
                           grade="held" if not gaps else "open",
                           gaps=tuple(gaps))


@dataclass(frozen=True)
class RoadmapAuditVerdict:
    ready: bool
    gaps: Tuple[str, ...]
    done_parts: Tuple[str, ...]
    partial_parts: Tuple[str, ...]
    not_proven_parts: Tuple[str, ...]
    missing_parts: Tuple[str, ...]


def derive_verdict(records: Iterable[RoadmapAuditRecord],
                   registry: Optional[RoadmapAuditRegistry] = None) -> RoadmapAuditVerdict:
    reg = registry or default_registry()
    by_part: Dict[str, RoadmapAuditRecord] = {}
    gaps = []
    for record in records:
        record.validate(reg)
        if record.part in by_part:
            gaps.append(
                f"part {record.part} carries two findings")
        else:
            by_part[record.part] = record
    missing = tuple(aid for aid in reg.combinations()
                    if aid not in by_part)
    for part_id in missing:
        gaps.append(f"part {part_id} has no finding in the book")
    fixed = []
    shaping = []
    notready = []
    for part_id, record in by_part.items():
        standing = derive_standing(record, reg)
        if standing.held and record.disposition == "DONE":
            fixed.append(part_id)
        if standing.held and record.disposition == "PARTIAL":
            shaping.append(part_id)
        if standing.held and record.disposition == "NOT_PROVEN":
            notready.append(part_id)
        if not standing.held:
            gaps.append(
                f"part {part_id} stands open: "
                + "; ".join(standing.gaps))
    return RoadmapAuditVerdict(ready=not gaps, gaps=tuple(gaps),
                        done_parts=tuple(fixed),
                        partial_parts=tuple(shaping),
                        not_proven_parts=tuple(notready), missing_parts=missing)


@dataclass(frozen=True)
class RoadmapAuditReport:
    book: str
    entry: str
    report: str
    date: str
    done_count: int
    partial_count: int
    not_proven_count: int
    total_parts: int
    claims: Tuple[str, ...]
    state: str = "ready"
    certified: bool = False
    inflated: bool = False

    def validate(self, registry: Optional[RoadmapAuditRegistry] = None) -> None:
        reg = registry or default_registry()
        if not self.book.strip():
            raise ValidationError("report names no book")
        if not self.entry.strip():
            raise ValidationError("report names no entry")
        if not self.report.strip():
            raise ValidationError("part reports nothing")
        if not self.date:
            raise ValidationError(
                "report names no date: a part "
                "report is reported with its date")
        _check_date(self.date)
        expected = len(reg.combinations())
        if self.total_parts != expected:
            raise ValidationError(
                f"report book holds {self.total_parts} "
                f"parts, not the road's {expected}")
        if self.done_count < 0 or self.partial_count < 0 or self.not_proven_count < 0:
            raise ValidationError(
                "unknown part count: "
                f"{self.done_count}/{self.partial_count}/{self.not_proven_count}")
        if self.done_count + self.partial_count + self.not_proven_count > self.total_parts:
            raise ValidationError(
                "answered parts exceed the book: "
                f"{self.done_count} + {self.partial_count} + {self.not_proven_count} "
                f"of {self.total_parts}")
        for kind in self.claims:
            if kind not in EVIDENCE_KINDS:
                raise ValidationError(f"unknown report evidence kind: {kind}")
        if not [c for c in self.claims if c in HELD_EVIDENCE]:
            raise ValidationError(
                "parts report held findings "
                "only; a report dressing a bare claim "
                "as a proof refuses here")
        if self.state not in REPORT_STATES:
            raise ValidationError(
                "parts stand ready or shared "
                "only, never sealed or locked; refused "
                f"state: {self.state}")
        if self.certified and \
                self.done_count + self.partial_count + self.not_proven_count < self.total_parts:
            raise ValidationError(
                "an unanswered part anywhere stops "
                "the closing claim: this report may not "
                "claim the part complete short of "
                "every part answered")
        if self.inflated:
            raise ValidationError(
                "parts report the findings "
                "exactly as they were dispositioned; a "
                "report is never inflated here")


def prepare_report(book: str, entry: str, report: str,
                   date: str, done_count: int, partial_count: int, not_proven_count: int,
                   total_parts: int,
                   claims: Tuple[str, ...] = (),
                   state: str = "ready",
                   certified: bool = False) -> RoadmapAuditReport:
    made = RoadmapAuditReport(book=book, entry=entry,
                       report=report, date=date,
                       done_count=done_count,
                       partial_count=partial_count,
                       not_proven_count=not_proven_count,
                       total_parts=total_parts,
                       claims=tuple(claims),
                       state=state, certified=certified)
    made.validate()
    return made


def format_part(entry: RoadmapAuditEntry) -> str:
    return (f"{entry.id} {entry.doctrine}/{entry.subject}: "
            f"standing {entry.standing} "
            f"- {entry.reason}")


def format_parts(registry: Optional[RoadmapAuditRegistry] = None) -> str:
    reg = registry or default_registry()
    return "\n".join(format_part(e) for e in reg.entries())


def format_record(record: RoadmapAuditRecord,
                  registry: Optional[RoadmapAuditRegistry] = None) -> str:
    reg = registry or default_registry()
    entry = reg.get(record.part)
    standing = derive_standing(record, reg)
    state = "held as answered" if standing.held else "open: " + "; ".join(standing.gaps)
    return (f"{record.part} {entry.doctrine}/{entry.subject}: "
            f"disposition {record.disposition} "
            f"({record.proof_kind}), date "
            f"{record.date or '(no date)'} - {state}")


def format_records(records: Iterable[RoadmapAuditRecord],
                   registry: Optional[RoadmapAuditRegistry] = None) -> str:
    return "\n".join(format_record(r, registry) for r in records)
