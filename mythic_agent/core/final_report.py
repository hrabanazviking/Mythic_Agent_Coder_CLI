"""The final report book (roadmap slice M-272) - pure layer.

Part XI - Proof. The roadmap words: **plain language first - what the coder can now do, where it beats the field, where it does not yet - with the evidence index.**

What this layer holds, as data: a final report registry F-01..F-12 (the sections of the final report to Volmarr, from what the coder can now do to the evidence index itself), each listed only, each labelled and evidenced; a report record per section holding its work, date, disposition PROVEN or PARTIAL or NOT_PROVEN, owner, proof kind and stage walk named-labelled-evidenced-dispositioned-held; a derived standing; a derived final verdict over the whole book; and a final report prepared only through the prepare road, ready or shared, never sealed, inflated or certified short of every section answered.

Honesty rule, made code: a section counts PROVEN only on held proof measured in the campaign itself resting on held evidence in the evidence index (an evidence_ref among evidence_ref, test_ref, ledger_ref, run_ref - never a bare claim). A section counts PARTIAL only where the proven part rests on held evidence and the remainder is roaded with its owner named in the open. A section counts NOT_PROVEN only with a named owner and the reason recorded. Silence is not a disposition: a section with no record stands missing, named in the verdict gaps.

Honest boundary: this book holds and judges final report records as data; it does not itself deliver the report to Volmarr, publish anything, or rewrite campaign history. It proves nothing and ships nothing; the agent layer owns holding session records and speaking for them.
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
    "FINAL_REPORT_ENTRIES",
    "FINAL_REPORT_SCHEMA",
    "FINAL_REPORT_SLICE",
    "FinalReportStanding",
    "FinalReportVerdict",
    "FinalReportRecord",
    "FinalReportReport",
    "FinalReportEntry",
    "FinalReportRegistry",
    "default_registry",
    "derive_standing",
    "derive_verdict",
    "format_record",
    "format_records",
    "format_entry",
    "format_entries",
    "prepare_report",
]

FINAL_REPORT_SLICE = "M-272"
FINAL_REPORT_SCHEMA = "mythic.final_report/1"

PLAIN_EXPLANATION = (
    "The final report to Volmarr, plain "
    "language first: what the coder can now "
    "do, where it beats the field, and where "
    "it does not yet - with the evidence "
    "index behind every claim. A section "
    "counts PROVEN only on held evidence in "
    "the index, PARTIAL only where the proven "
    "part rests on held evidence and the rest "
    "is roaded with its owner named, and "
    "NOT_PROVEN only with its reason recorded "
    "- never silent, never inflated.")


USAGE = (
    "Record each section against its entry, "
    "proven on held indexed evidence, partial "
    "with its owner and road, or not proven "
    "with its reason recorded; read the derived "
    "final verdict before letting any report "
    "claim the campaign told; prepare a report "
    "only as a report, with every section "
    "answered - proven, partial or not proven, "
    "each in the open - and let a human share "
    "it. The whole final report, answered "
    "section by section, as data first.")



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
DISPOSITIONS = ("PROVEN", "PARTIAL", "NOT_PROVEN")
PROOF_KINDS = ("proven-and-held", "partially-held", "none")
DOCTRINE_REFS = ("plain-language", "evidence-index", "field-honesty", "report-duty")
SUBJECTS = ("what-it-can-do", "provider-ocean", "code-intelligence", "editors-hand", "native-sandbox", "parallel-crews", "memory-context", "jarl-mode", "bridges", "method-engine", "where-it-falls-short", "evidence-index")


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
class FinalReportEntry:
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
                raise ValidationError(f"section entry missing {name}")
        if self.doctrine not in DOCTRINE_REFS:
            raise ValidationError(f"unknown section doctrine: {self.doctrine}")
        if self.subject not in SUBJECTS:
            raise ValidationError(f"unknown section subject: {self.subject}")
        if self.standing != "listed":
            raise ValidationError("section entries are listed data only, never a published verdict here; " f"refused standing: {self.standing}")
        if not self.labelled:
            raise ValidationError("section entries are labelled only; " f"refused unlabelled entry: {self.id}")
        if not self.evidenced:
            raise ValidationError("section entries are evidenced only; " f"refused unevidenced entry: {self.id}")


FINAL_REPORT_ENTRIES = (
    FinalReportEntry("F-01", "plain-language", "what-it-can-do", "listed", "what the coder can now do, in plain language first, every power named as the user meets it"),
    FinalReportEntry("F-02", "evidence-index", "provider-ocean", "listed", "the provider ocean, Ollama and Project Aesir among them, keys held in Kista, answered on held evidence"),
    FinalReportEntry("F-03", "plain-language", "code-intelligence", "listed", "code intelligence: reading, navigating and understanding a codebase, answered in the open"),
    FinalReportEntry("F-04", "field-honesty", "editors-hand", "listed", "the editors hand: edits, renames and multi-file change sets, journal-first, answered with its road where partial"),
    FinalReportEntry("F-05", "evidence-index", "native-sandbox", "listed", "native sandboxing with no Docker anywhere, answered in the open, none silent"),
    FinalReportEntry("F-06", "plain-language", "parallel-crews", "listed", "parallel crews: ten teams building at once, one slice each, banked in roadmap order"),
    FinalReportEntry("F-07", "field-honesty", "memory-context", "listed", "memory and context: what the coder remembers and how the window is spent, answered with its reason where not proven"),
    FinalReportEntry("F-08", "report-duty", "jarl-mode", "listed", "the plain-language Jarl mode for the user who does not code, answered in the open"),
    FinalReportEntry("F-09", "evidence-index", "bridges", "listed", "the bridges to Samverk and Samtal and the agent-facing transports, answered on held evidence"),
    FinalReportEntry("F-10", "plain-language", "method-engine", "listed", "the Mythic Engineering method engine at the heart of the coder, answered with its road where partial"),
    FinalReportEntry("F-11", "field-honesty", "where-it-falls-short", "listed", "where the coder does not yet beat the field, named plainly, answered in the open, none silent"),
    FinalReportEntry("F-12", "report-duty", "evidence-index", "listed", "the evidence index itself: every claim in this report resting on a held ref, or named not proven"),
)


class FinalReportRegistry:
    def __init__(self, entries: Iterable[FinalReportEntry] = FINAL_REPORT_ENTRIES):
        self._entries: Dict[str, FinalReportEntry] = {}
        for entry in entries:
            entry.validate()
            if entry.id in self._entries:
                raise ValidationError(f"duplicate section: {entry.id}")
            self._entries[entry.id] = entry

    def get(self, section_id: str) -> FinalReportEntry:
        try:
            return self._entries[section_id]
        except KeyError:
            raise ValidationError(
                f"unknown section: {section_id}") from None

    def ids(self) -> Tuple[str, ...]:
        return tuple(self._entries)

    def entries(self) -> Tuple[FinalReportEntry, ...]:
        return tuple(self._entries.values())

    def combinations(self) -> Tuple[str, ...]:
        return tuple(self._entries)


def default_registry() -> FinalReportRegistry:
    return FinalReportRegistry()


@dataclass(frozen=True)
class FinalReportRecord:
    section: str
    work: str
    date: str
    disposition: str
    owner: str
    proof_kind: str
    stages: Tuple[str, ...]
    claims: Tuple[str, ...]

    def validate(self, registry: Optional[FinalReportRegistry] = None) -> None:
        (registry or default_registry()).get(self.section)
        if not self.work.strip():
            raise ValidationError("record names no section work")
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
class FinalReportStanding:
    held: bool
    stage: str
    grade: str
    gaps: Tuple[str, ...]


def derive_standing(record: FinalReportRecord,
                    registry: Optional[FinalReportRegistry] = None) -> FinalReportStanding:
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
    if record.disposition == "PROVEN":
        if record.proof_kind != "proven-and-held":
            gaps.append(
                f"a PROVEN section rests on {record.proof_kind} "
                "evidence, not held proof measured in the campaign itself: "
                "the section tells the truth or stands open")
        if "evidence_ref" not in record.claims:
            gaps.append(
                "the proven section rests on no held "
                "held evidence")
        if not held_kinds:
            gaps.append("record rests on no held evidence")
        if bare and not held_kinds:
            gaps.append("record rests on bare claims only: " + ", ".join(bare))
    else:
        if not record.owner.strip():
            gaps.append(
                "a partial or not proven section with no owner "
                "named is a wish, not a road")
        if not record.claims:
            gaps.append(
                "a partial or not proven section with nothing "
                "recorded stands silent, not answered")
        if record.disposition == "PARTIAL" and not held_kinds:
            gaps.append(
                "a partial section rests on no held "
                "evidence: the proven part must rest "
                "on held evidence, not on a claim")
        if record.disposition == "NOT_PROVEN" and record.proof_kind == "proven-and-held":
            gaps.append(
                "a NOT_PROVEN section resting on full "
                "measured proof contradicts itself: "
                "re-disposition it PROVEN or PARTIAL")
    return FinalReportStanding(held=not gaps, stage=stage,
                           grade="held" if not gaps else "open",
                           gaps=tuple(gaps))


@dataclass(frozen=True)
class FinalReportVerdict:
    ready: bool
    gaps: Tuple[str, ...]
    proven_sections: Tuple[str, ...]
    partial_sections: Tuple[str, ...]
    not_proven_sections: Tuple[str, ...]
    missing_sections: Tuple[str, ...]


def derive_verdict(records: Iterable[FinalReportRecord],
                   registry: Optional[FinalReportRegistry] = None) -> FinalReportVerdict:
    reg = registry or default_registry()
    by_section: Dict[str, FinalReportRecord] = {}
    gaps = []
    for record in records:
        record.validate(reg)
        if record.section in by_section:
            gaps.append(
                f"section {record.section} carries two records")
        else:
            by_section[record.section] = record
    missing = tuple(aid for aid in reg.combinations()
                    if aid not in by_section)
    for section_id in missing:
        gaps.append(f"section {section_id} has no record in the book")
    fixed = []
    shaping = []
    notready = []
    for section_id, record in by_section.items():
        standing = derive_standing(record, reg)
        if standing.held and record.disposition == "PROVEN":
            fixed.append(section_id)
        if standing.held and record.disposition == "PARTIAL":
            shaping.append(section_id)
        if standing.held and record.disposition == "NOT_PROVEN":
            notready.append(section_id)
        if not standing.held:
            gaps.append(
                f"section {section_id} stands open: "
                + "; ".join(standing.gaps))
    return FinalReportVerdict(ready=not gaps, gaps=tuple(gaps),
                        proven_sections=tuple(fixed),
                        partial_sections=tuple(shaping),
                        not_proven_sections=tuple(notready), missing_sections=missing)


@dataclass(frozen=True)
class FinalReportReport:
    book: str
    entry: str
    report: str
    date: str
    proven_count: int
    partial_count: int
    not_proven_count: int
    total_sections: int
    claims: Tuple[str, ...]
    state: str = "ready"
    certified: bool = False
    inflated: bool = False

    def validate(self, registry: Optional[FinalReportRegistry] = None) -> None:
        reg = registry or default_registry()
        if not self.book.strip():
            raise ValidationError("report names no book")
        if not self.entry.strip():
            raise ValidationError("report names no entry")
        if not self.report.strip():
            raise ValidationError("section reports nothing")
        if not self.date:
            raise ValidationError(
                "report names no date: a final "
                "report is reported with its date")
        _check_date(self.date)
        expected = len(reg.combinations())
        if self.total_sections != expected:
            raise ValidationError(
                f"report book holds {self.total_sections} "
                f"sections, not the road's {expected}")
        if self.proven_count < 0 or self.partial_count < 0 or self.not_proven_count < 0:
            raise ValidationError(
                "unknown section count: "
                f"{self.proven_count}/{self.partial_count}/{self.not_proven_count}")
        if self.proven_count + self.partial_count + self.not_proven_count > self.total_sections:
            raise ValidationError(
                "answered sections exceed the book: "
                f"{self.proven_count} + {self.partial_count} + {self.not_proven_count} "
                f"of {self.total_sections}")
        for kind in self.claims:
            if kind not in EVIDENCE_KINDS:
                raise ValidationError(f"unknown report evidence kind: {kind}")
        if not [c for c in self.claims if c in HELD_EVIDENCE]:
            raise ValidationError(
                "sections report held records "
                "only; a report dressing a bare claim "
                "as a proof refuses here")
        if self.state not in REPORT_STATES:
            raise ValidationError(
                "final reports stand ready or shared "
                "only, never sealed or locked; refused "
                f"state: {self.state}")
        if self.certified and \
                self.proven_count + self.partial_count + self.not_proven_count < self.total_sections:
            raise ValidationError(
                "an unanswered section anywhere stops "
                "the closing claim: this report may not "
                "claim the report complete short of "
                "every section answered")
        if self.inflated:
            raise ValidationError(
                "final reports report the sections "
                "exactly as they were dispositioned; a "
                "report is never inflated here")


def prepare_report(book: str, entry: str, report: str,
                   date: str, proven_count: int, partial_count: int, not_proven_count: int,
                   total_sections: int,
                   claims: Tuple[str, ...] = (),
                   state: str = "ready",
                   certified: bool = False) -> FinalReportReport:
    made = FinalReportReport(book=book, entry=entry,
                       report=report, date=date,
                       proven_count=proven_count,
                       partial_count=partial_count,
                       not_proven_count=not_proven_count,
                       total_sections=total_sections,
                       claims=tuple(claims),
                       state=state, certified=certified)
    made.validate()
    return made


def format_entry(entry: FinalReportEntry) -> str:
    return (f"{entry.id} {entry.doctrine}/{entry.subject}: "
            f"standing {entry.standing} "
            f"- {entry.reason}")


def format_entries(registry: Optional[FinalReportRegistry] = None) -> str:
    reg = registry or default_registry()
    return "\n".join(format_entry(e) for e in reg.entries())


def format_record(record: FinalReportRecord,
                  registry: Optional[FinalReportRegistry] = None) -> str:
    reg = registry or default_registry()
    entry = reg.get(record.section)
    standing = derive_standing(record, reg)
    state = "held as answered" if standing.held else "open: " + "; ".join(standing.gaps)
    return (f"{record.section} {entry.doctrine}/{entry.subject}: "
            f"disposition {record.disposition} "
            f"({record.proof_kind}), date "
            f"{record.date or '(no date)'} - {state}")


def format_records(records: Iterable[FinalReportRecord],
                   registry: Optional[FinalReportRegistry] = None) -> str:
    return "\n".join(format_record(r, registry) for r in records)
