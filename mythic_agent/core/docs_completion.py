"""The docs-completion book (roadmap slice M-263) - pure layer.

Part XI - Proof. The roadmap words: **user guide, method guide, bridge guides, and per-part interface notes reconciled with shipped code - the Scribe's closing duty, H7-style.**

What this layer holds, as data: a guide registry D-01..D-12 (user guide, method guide, bridge guides, per-part interface notes, install and setup, provider ocean guide, editor hand guide, sandbox guide, crew guide, memory and context guide, jarl mode guide, troubleshooting guide), each listed only; a reconciliation record per guide holding its reconciliation work, date, disposition RECONCILED or ROADED, owner, proof kind and stage walk named-reconciled-judged-dispositioned-held; a derived standing; a derived docs verdict over the whole book; and a docs report prepared only through the prepare road, ready or shared, never sealed, inflated or certified short of every guide answered.

Honesty rule, made code: a guide counts RECONCILED only on reconciliation against the shipped code itself resting on held code evidence (a code_ref among code_ref, doc_ref, local_run_ref, journal_ref - never a bare claim). A RECONCILED finding on historical or no proof stands open, named in its gaps: no inheritance. A ROADED finding stands held only with a named owner and something recorded - ownerless is a wish, silent is not a road. A guide written from memory of the code, not from the shipped code, faces the book as data here, not as an inherited truth.

Honest boundary: this layer holds entries, records, standings, verdicts and reports as data. It writes no guide, reads no shipped code and writes nothing outside the session; the agent layer owns holding a session records and speaking for them.
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
    "GUIDES",
    "DOCS_COMPLETION_SCHEMA",
    "DOCS_COMPLETION_SLICE",
    "DocStanding",
    "DocsVerdict",
    "DocRecord",
    "DocsReport",
    "GuideEntry",
    "GuideRegistry",
    "default_registry",
    "derive_standing",
    "derive_verdict",
    "format_record",
    "format_records",
    "format_guide",
    "format_guides",
    "prepare_report",
]

DOCS_COMPLETION_SLICE = "M-263"
DOCS_COMPLETION_SCHEMA = "mythic.docs_completion/1"

PLAIN_EXPLANATION = (
    "The docs completion, done honestly: "
    "the user guide, method guide, bridge guides "
    "and per-part interface notes reconciled with "
    "the shipped code itself. A guide counts "
    "RECONCILED only on reconciliation against "
    "shipped code resting on held code evidence. "
    "Every other guide ships ROADED with a named "
    "owner, in the open - an ownerless road is "
    "named, never silent, and no guide written "
    "from memory is inherited as truth."
)
USAGE = (
    "Record each guide finding against its guide, "
    "reconciled against shipped code or roaded "
    "with its owner named; read the derived "
    "docs verdict before letting any report "
    "claim the docs complete; prepare a report only as "
    "a report, with every guide answered - reconciled on "
    "held code evidence or roaded with an owner - "
    "and let a human share it. The whole docs book, "
    "answered guide by guide, as data first."
)


STAGES = ("named", "reconciled", "judged", "dispositioned", "held")
TRANSITIONS = {
    "named": ("reconciled",),
    "reconciled": ("judged",),
    "judged": ("dispositioned",),
    "dispositioned": ("held",),
    "held": (),
}
HELD_EVIDENCE = ("code_ref", "doc_ref", "local_run_ref", "journal_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
EVIDENCE_KINDS = HELD_EVIDENCE + BARE_CLAIMS
REPORT_STATES = ("ready", "shared")
DISPOSITIONS = ("RECONCILED", "ROADED")
PROOF_KINDS = ("reconciled-with-code", "historical-only", "none")
DOCTRINE_REFS = ("shipped-code", "method", "bridges", "parts")
SUBJECTS = ("user-guide", "method-guide", "bridge-guides", "part-interface-notes", "install-and-setup", "provider-ocean-guide", "editor-hand-guide", "sandbox-guide", "crew-guide", "memory-and-context-guide", "jarl-mode-guide", "troubleshooting-guide")


def _check_date(value: str) -> None:
    ok = (isinstance(value, str) and len(value) == 10 and value[4] == "-" and value[7] == "-")
    if ok:
        try:
            _date.fromisoformat(value)
        except ValueError:
            ok = False
    if not ok:
        raise ValidationError(f"unknown docs date: {value}")


@dataclass(frozen=True)
class GuideEntry:
    id: str
    doctrine: str
    subject: str
    standing: str
    reason: str
    def validate(self) -> None:
        for name in ("id", "doctrine", "subject", "standing", "reason"):
            if not str(getattr(self, name)).strip():
                raise ValidationError(f"guide entry missing {name}")
        if self.doctrine not in DOCTRINE_REFS:
            raise ValidationError(f"unknown guide doctrine: {self.doctrine}")
        if self.subject not in SUBJECTS:
            raise ValidationError(f"unknown check subject: {self.subject}")
        if self.standing != "listed":
            raise ValidationError("guide entries are listed data only, never a published verdict here; " f"refused standing: {self.standing}")


GUIDES = (
    GuideEntry("D-01", "shipped-code", "user-guide", "listed",
              "the user guide, reconciled with the shipped commands and screens"),
    GuideEntry("D-02", "method", "method-guide", "listed",
              "the method guide, the Mythic Engineering way as the shipped coder practises it"),
    GuideEntry("D-03", "bridges", "bridge-guides", "listed",
              "the bridge guides, Samverk and Samtal crossings as shipped"),
    GuideEntry("D-04", "parts", "part-interface-notes", "listed",
              "per-part interface notes for all eleven parts, reconciled part by part with shipped code"),
    GuideEntry("D-05", "shipped-code", "install-and-setup", "listed",
              "install and setup, reconciled with the shipped setup road"),
    GuideEntry("D-06", "shipped-code", "provider-ocean-guide", "listed",
              "the provider ocean guide, providers and keys in Kista as shipped"),
    GuideEntry("D-07", "shipped-code", "editor-hand-guide", "listed",
              "the editor hand guide, edits and journals as shipped"),
    GuideEntry("D-08", "shipped-code", "sandbox-guide", "listed",
              "the sandbox guide, native sandboxing with no Docker, as shipped"),
    GuideEntry("D-09", "method", "crew-guide", "listed",
              "the crew guide, parallel crews and their offices as shipped"),
    GuideEntry("D-10", "shipped-code", "memory-and-context-guide", "listed",
              "the memory and context guide, sessions and context as shipped"),
    GuideEntry("D-11", "method", "jarl-mode-guide", "listed",
              "the jarl mode guide, plain-language working as shipped"),
    GuideEntry("D-12", "shipped-code", "troubleshooting-guide", "listed",
              "the troubleshooting guide, every error carrying its fix, as shipped"),
)


class GuideRegistry:
    def __init__(self, entries: Iterable[GuideEntry] = GUIDES):
        self._entries: Dict[str, GuideEntry] = {}
        for entry in entries:
            entry.validate()
            if entry.id in self._entries:
                raise ValidationError(f"duplicate guide: {entry.id}")
            self._entries[entry.id] = entry

    def get(self, guide_id: str) -> GuideEntry:
        try:
            return self._entries[guide_id]
        except KeyError:
            raise ValidationError(
                f"unknown guide: {guide_id}") from None

    def ids(self) -> Tuple[str, ...]:
        return tuple(self._entries)

    def entries(self) -> Tuple[GuideEntry, ...]:
        return tuple(self._entries.values())

    def combinations(self) -> Tuple[str, ...]:
        return tuple(self._entries)


def default_registry() -> GuideRegistry:
    return GuideRegistry()


@dataclass(frozen=True)
class DocRecord:
    guide: str
    work: str
    date: str
    disposition: str
    owner: str
    proof_kind: str
    stages: Tuple[str, ...]
    claims: Tuple[str, ...]

    def validate(self, registry: Optional[GuideRegistry] = None) -> None:
        (registry or default_registry()).get(self.guide)
        if not self.work.strip():
            raise ValidationError("record names no reconciliation work")
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
class DocStanding:
    held: bool
    stage: str
    grade: str
    gaps: Tuple[str, ...]


def derive_standing(record: DocRecord,
                    registry: Optional[GuideRegistry] = None) -> DocStanding:
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
        gaps.append("record names no docs date")
    if record.disposition == "RECONCILED":
        if record.proof_kind != "reconciled-with-code":
            gaps.append(
                f"a RECONCILED guide rests on {record.proof_kind} "
                "evidence, not reconciliation with shipped code: "
                "no inheritance")
        if "code_ref" not in record.claims:
            gaps.append(
                "the reconciled guide rests on no held "
                "code evidence")
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
    return DocStanding(held=not gaps, stage=stage,
                           grade="held" if not gaps else "open",
                           gaps=tuple(gaps))


@dataclass(frozen=True)
class DocsVerdict:
    ready: bool
    gaps: Tuple[str, ...]
    reconciled_guides: Tuple[str, ...]
    roaded_guides: Tuple[str, ...]
    missing_guides: Tuple[str, ...]


def derive_verdict(records: Iterable[DocRecord],
                   registry: Optional[GuideRegistry] = None) -> DocsVerdict:
    reg = registry or default_registry()
    by_guide: Dict[str, DocRecord] = {}
    gaps = []
    for record in records:
        record.validate(reg)
        if record.guide in by_guide:
            gaps.append(
                f"guide {record.guide} carries two findings")
        else:
            by_guide[record.guide] = record
    missing = tuple(aid for aid in reg.combinations()
                    if aid not in by_guide)
    for guide_id in missing:
        gaps.append(f"guide {guide_id} has no finding in the book")
    fixed = []
    roaded = []
    for guide_id, record in by_guide.items():
        standing = derive_standing(record, reg)
        if standing.held and record.disposition == "RECONCILED":
            fixed.append(guide_id)
        if standing.held and record.disposition == "ROADED":
            roaded.append(guide_id)
        if not standing.held:
            gaps.append(
                f"guide {guide_id} stands open: "
                + "; ".join(standing.gaps))
    return DocsVerdict(ready=not gaps, gaps=tuple(gaps),
                        reconciled_guides=tuple(fixed),
                        roaded_guides=tuple(roaded),
                        missing_guides=missing)


@dataclass(frozen=True)
class DocsReport:
    book: str
    entry: str
    report: str
    date: str
    reconciled_count: int
    roaded_count: int
    total_guides: int
    claims: Tuple[str, ...]
    state: str = "ready"
    certified: bool = False
    inflated: bool = False

    def validate(self, registry: Optional[GuideRegistry] = None) -> None:
        reg = registry or default_registry()
        if not self.book.strip():
            raise ValidationError("report names no book")
        if not self.entry.strip():
            raise ValidationError("report names no entry")
        if not self.report.strip():
            raise ValidationError("docs report reports nothing")
        if not self.date:
            raise ValidationError(
                "report names no date: a docs "
                "report is reported with its date")
        _check_date(self.date)
        expected = len(reg.combinations())
        if self.total_guides != expected:
            raise ValidationError(
                f"report book holds {self.total_guides} "
                f"guides, not the road's {expected}")
        if self.reconciled_count < 0 or self.roaded_count < 0:
            raise ValidationError(
                "unknown guide count: "
                f"{self.reconciled_count}/{self.roaded_count}")
        if self.reconciled_count + self.roaded_count > self.total_guides:
            raise ValidationError(
                "answered guides exceed the book: "
                f"{self.reconciled_count} + {self.roaded_count} "
                f"of {self.total_guides}")
        for kind in self.claims:
            if kind not in EVIDENCE_KINDS:
                raise ValidationError(f"unknown report evidence kind: {kind}")
        if not [c for c in self.claims if c in HELD_EVIDENCE]:
            raise ValidationError(
                "docs reports report held findings "
                "only; a report dressing a bare claim "
                "as a proof refuses here")
        if self.state not in REPORT_STATES:
            raise ValidationError(
                "docs reports stand ready or shared "
                "only, never sealed or locked; refused "
                f"state: {self.state}")
        if self.certified and \
                self.reconciled_count + self.roaded_count < self.total_guides:
            raise ValidationError(
                "an unanswered guide anywhere stops "
                "the closing claim: this report may not "
                "claim the docs complete short of "
                "every guide answered")
        if self.inflated:
            raise ValidationError(
                "docs reports report the findings "
                "exactly as they were dispositioned; a "
                "report is never inflated here")


def prepare_report(book: str, entry: str, report: str,
                   date: str, reconciled_count: int, roaded_count: int,
                   total_guides: int,
                   claims: Tuple[str, ...] = (),
                   state: str = "ready",
                   certified: bool = False) -> DocsReport:
    made = DocsReport(book=book, entry=entry,
                       report=report, date=date,
                       reconciled_count=reconciled_count,
                       roaded_count=roaded_count,
                       total_guides=total_guides,
                       claims=tuple(claims),
                       state=state, certified=certified)
    made.validate()
    return made


def format_guide(entry: GuideEntry) -> str:
    return (f"{entry.id} {entry.doctrine}/{entry.subject}: "
            f"standing {entry.standing} "
            f"- {entry.reason}")


def format_guides(registry: Optional[GuideRegistry] = None) -> str:
    reg = registry or default_registry()
    return "\n".join(format_guide(e) for e in reg.entries())


def format_record(record: DocRecord,
                  registry: Optional[GuideRegistry] = None) -> str:
    reg = registry or default_registry()
    entry = reg.get(record.guide)
    standing = derive_standing(record, reg)
    state = "held as answered" if standing.held else "open: " + "; ".join(standing.gaps)
    return (f"{record.guide} {entry.doctrine}/{entry.subject}: "
            f"disposition {record.disposition} "
            f"({record.proof_kind}), date "
            f"{record.date or '(no date)'} - {state}")


def format_records(records: Iterable[DocRecord],
                   registry: Optional[GuideRegistry] = None) -> str:
    return "\n".join(format_record(r, registry) for r in records)
