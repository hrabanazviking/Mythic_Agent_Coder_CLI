"""The README-care book (roadmap slice M-264) - pure layer.

Part XI - Proof. The roadmap words: **the repo README extended by hand with the new story - nothing removed, per Volmarr's standing law.**

What this layer holds, as data: a section registry R-01..R-12 (opening story, install story, provider ocean story, editor hand story, sandbox story, crew story, memory and context story, jarl mode story, bridges story, commands story, care law note, closing story), each listed only; a care record per section holding its extension work, date, disposition EXTENDED or ROADED, owner, proof kind and stage walk named-extended-judged-dispositioned-held; a derived standing; a derived README verdict over the whole book; and a README report prepared only through the prepare road, ready or shared, never sealed, inflated or certified short of every section answered.

Honesty rule, made code: a section counts EXTENDED only on hand extension against the README as it stands resting on held README evidence (a readme_ref among readme_ref, doc_ref, local_run_ref, journal_ref - never a bare claim). An EXTENDED finding on historical or no proof stands open, named in its gaps: no inheritance. A ROADED finding stands held only with a named owner and something recorded - ownerless is a wish, silent is not a road. A section claimed extended from memory of the README, not from the README as it stands, faces the book as data here, not as an inherited truth.

Honest boundary: this layer holds entries, records, standings, verdicts and reports as data. It writes no README, edits no file and writes nothing outside the session; the agent layer owns holding a session records and speaking for them.
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
    "SECTIONS",
    "README_CARE_SCHEMA",
    "README_CARE_SLICE",
    "CareStanding",
    "ReadmeVerdict",
    "CareRecord",
    "ReadmeReport",
    "CareEntry",
    "CareRegistry",
    "default_registry",
    "derive_standing",
    "derive_verdict",
    "format_record",
    "format_records",
    "format_section",
    "format_sections",
    "prepare_report",
]

README_CARE_SLICE = "M-264"
README_CARE_SCHEMA = "mythic.readme_care/1"

PLAIN_EXPLANATION = (
    "README care, done honestly: "
    "the repo README extended by hand with the "
    "new story - nothing removed, ever, per "
    "Volmarr's standing law. A section counts "
    "EXTENDED only on hand extension resting on "
    "held evidence of the README as it stands. "
    "Every other section ships ROADED with a named "
    "owner, in the open - an ownerless road is "
    "named, never silent, and no section is "
    "claimed extended from memory."
)
USAGE = (
    "Record each section finding against its section, "
    "extended by hand against the README as it stands "
    "or roaded with its owner named; read the derived "
    "README verdict before letting any report "
    "claim the README complete; prepare a report only as "
    "a report, with every section answered - extended on "
    "held README evidence or roaded with an owner - "
    "and let a human share it. The whole README book, "
    "answered section by section, as data first."
)


STAGES = ("named", "extended", "judged", "dispositioned", "held")
TRANSITIONS = {
    "named": ("extended",),
    "extended": ("judged",),
    "judged": ("dispositioned",),
    "dispositioned": ("held",),
    "held": (),
}
HELD_EVIDENCE = ("readme_ref", "doc_ref", "local_run_ref", "journal_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
EVIDENCE_KINDS = HELD_EVIDENCE + BARE_CLAIMS
REPORT_STATES = ("ready", "shared")
DISPOSITIONS = ("EXTENDED", "ROADED")
PROOF_KINDS = ("extended-by-hand", "historical-only", "none")
DOCTRINE_REFS = ("standing-law", "shipped-story", "new-story", "care-duty")
SUBJECTS = ("opening-story", "install-story", "provider-ocean-story", "editor-hand-story", "sandbox-story", "crew-story", "memory-context-story", "jarl-mode-story", "bridges-story", "commands-story", "care-law-note", "closing-story")


def _check_date(value: str) -> None:
    ok = (isinstance(value, str) and len(value) == 10 and value[4] == "-" and value[7] == "-")
    if ok:
        try:
            _date.fromisoformat(value)
        except ValueError:
            ok = False
    if not ok:
        raise ValidationError(f"unknown care date: {value}")


@dataclass(frozen=True)
class CareEntry:
    id: str
    doctrine: str
    subject: str
    standing: str
    reason: str
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


SECTIONS = (
    CareEntry("R-01", "new-story", "opening-story", "listed",
              "the opening story, what the coder is, extended by hand with the new All-Features story - nothing removed"),
    CareEntry("R-02", "shipped-story", "install-story", "listed",
              "install and setup across Windows, macOS, Linux x86-64 and Linux ARM, as shipped"),
    CareEntry("R-03", "new-story", "provider-ocean-story", "listed",
              "the Provider Ocean story, every provider with Ollama and Project Aesir among them, keys in Kista, as shipped"),
    CareEntry("R-04", "new-story", "editor-hand-story", "listed",
              "the Editor's Hand story, edits, journals and undo as shipped"),
    CareEntry("R-05", "standing-law", "sandbox-story", "listed",
              "the sandbox story, native sandboxing with no Docker ever, as shipped"),
    CareEntry("R-06", "new-story", "crew-story", "listed",
              "the crew story, parallel crews working the Mythic Engineering way, as shipped"),
    CareEntry("R-07", "new-story", "memory-context-story", "listed",
              "the memory and context story, sessions, memory and context as shipped"),
    CareEntry("R-08", "new-story", "jarl-mode-story", "listed",
              "the Jarl mode story, plain-language working for the Jarl, as shipped"),
    CareEntry("R-09", "shipped-story", "bridges-story", "listed",
              "the bridges story, the Samverk and Samtal crossings as shipped"),
    CareEntry("R-10", "shipped-story", "commands-story", "listed",
              "the commands story, the slash roads and screens as shipped"),
    CareEntry("R-11", "standing-law", "care-law-note", "listed",
              "the care note itself: this README is extended by hand only and nothing is removed, per the standing law the M-079 guardians keep"),
    CareEntry("R-12", "care-duty", "closing-story", "listed",
              "the closing story, the roadmap and the proof, kept current by hand as the work banks"),
)


class CareRegistry:
    def __init__(self, entries: Iterable[CareEntry] = SECTIONS):
        self._entries: Dict[str, CareEntry] = {}
        for entry in entries:
            entry.validate()
            if entry.id in self._entries:
                raise ValidationError(f"duplicate section: {entry.id}")
            self._entries[entry.id] = entry

    def get(self, section_id: str) -> CareEntry:
        try:
            return self._entries[section_id]
        except KeyError:
            raise ValidationError(
                f"unknown section: {section_id}") from None

    def ids(self) -> Tuple[str, ...]:
        return tuple(self._entries)

    def entries(self) -> Tuple[CareEntry, ...]:
        return tuple(self._entries.values())

    def combinations(self) -> Tuple[str, ...]:
        return tuple(self._entries)


def default_registry() -> CareRegistry:
    return CareRegistry()


@dataclass(frozen=True)
class CareRecord:
    section: str
    work: str
    date: str
    disposition: str
    owner: str
    proof_kind: str
    stages: Tuple[str, ...]
    claims: Tuple[str, ...]

    def validate(self, registry: Optional[CareRegistry] = None) -> None:
        (registry or default_registry()).get(self.section)
        if not self.work.strip():
            raise ValidationError("record names no extension work")
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
class CareStanding:
    held: bool
    stage: str
    grade: str
    gaps: Tuple[str, ...]


def derive_standing(record: CareRecord,
                    registry: Optional[CareRegistry] = None) -> CareStanding:
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
        gaps.append("record names no care date")
    if record.disposition == "EXTENDED":
        if record.proof_kind != "extended-by-hand":
            gaps.append(
                f"an EXTENDED section rests on {record.proof_kind} "
                "evidence, not hand extension against the README as it stands: "
                "no inheritance")
        if "readme_ref" not in record.claims:
            gaps.append(
                "the extended section rests on no held "
                "README evidence")
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
    return CareStanding(held=not gaps, stage=stage,
                           grade="held" if not gaps else "open",
                           gaps=tuple(gaps))


@dataclass(frozen=True)
class ReadmeVerdict:
    ready: bool
    gaps: Tuple[str, ...]
    extended_sections: Tuple[str, ...]
    roaded_sections: Tuple[str, ...]
    missing_sections: Tuple[str, ...]


def derive_verdict(records: Iterable[CareRecord],
                   registry: Optional[CareRegistry] = None) -> ReadmeVerdict:
    reg = registry or default_registry()
    by_section: Dict[str, CareRecord] = {}
    gaps = []
    for record in records:
        record.validate(reg)
        if record.section in by_section:
            gaps.append(
                f"section {record.section} carries two findings")
        else:
            by_section[record.section] = record
    missing = tuple(aid for aid in reg.combinations()
                    if aid not in by_section)
    for section_id in missing:
        gaps.append(f"section {section_id} has no finding in the book")
    fixed = []
    roaded = []
    for section_id, record in by_section.items():
        standing = derive_standing(record, reg)
        if standing.held and record.disposition == "EXTENDED":
            fixed.append(section_id)
        if standing.held and record.disposition == "ROADED":
            roaded.append(section_id)
        if not standing.held:
            gaps.append(
                f"section {section_id} stands open: "
                + "; ".join(standing.gaps))
    return ReadmeVerdict(ready=not gaps, gaps=tuple(gaps),
                        extended_sections=tuple(fixed),
                        roaded_sections=tuple(roaded),
                        missing_sections=missing)


@dataclass(frozen=True)
class ReadmeReport:
    book: str
    entry: str
    report: str
    date: str
    extended_count: int
    roaded_count: int
    total_sections: int
    claims: Tuple[str, ...]
    state: str = "ready"
    certified: bool = False
    inflated: bool = False

    def validate(self, registry: Optional[CareRegistry] = None) -> None:
        reg = registry or default_registry()
        if not self.book.strip():
            raise ValidationError("report names no book")
        if not self.entry.strip():
            raise ValidationError("report names no entry")
        if not self.report.strip():
            raise ValidationError("README report reports nothing")
        if not self.date:
            raise ValidationError(
                "report names no date: a README "
                "report is reported with its date")
        _check_date(self.date)
        expected = len(reg.combinations())
        if self.total_sections != expected:
            raise ValidationError(
                f"report book holds {self.total_sections} "
                f"sections, not the road's {expected}")
        if self.extended_count < 0 or self.roaded_count < 0:
            raise ValidationError(
                "unknown section count: "
                f"{self.extended_count}/{self.roaded_count}")
        if self.extended_count + self.roaded_count > self.total_sections:
            raise ValidationError(
                "answered sections exceed the book: "
                f"{self.extended_count} + {self.roaded_count} "
                f"of {self.total_sections}")
        for kind in self.claims:
            if kind not in EVIDENCE_KINDS:
                raise ValidationError(f"unknown report evidence kind: {kind}")
        if not [c for c in self.claims if c in HELD_EVIDENCE]:
            raise ValidationError(
                "README reports report held findings "
                "only; a report dressing a bare claim "
                "as a proof refuses here")
        if self.state not in REPORT_STATES:
            raise ValidationError(
                "README reports stand ready or shared "
                "only, never sealed or locked; refused "
                f"state: {self.state}")
        if self.certified and \
                self.extended_count + self.roaded_count < self.total_sections:
            raise ValidationError(
                "an unanswered section anywhere stops "
                "the closing claim: this report may not "
                "claim the README complete short of "
                "every section answered")
        if self.inflated:
            raise ValidationError(
                "README reports report the findings "
                "exactly as they were dispositioned; a "
                "report is never inflated here")


def prepare_report(book: str, entry: str, report: str,
                   date: str, extended_count: int, roaded_count: int,
                   total_sections: int,
                   claims: Tuple[str, ...] = (),
                   state: str = "ready",
                   certified: bool = False) -> ReadmeReport:
    made = ReadmeReport(book=book, entry=entry,
                       report=report, date=date,
                       extended_count=extended_count,
                       roaded_count=roaded_count,
                       total_sections=total_sections,
                       claims=tuple(claims),
                       state=state, certified=certified)
    made.validate()
    return made


def format_section(entry: CareEntry) -> str:
    return (f"{entry.id} {entry.doctrine}/{entry.subject}: "
            f"standing {entry.standing} "
            f"- {entry.reason}")


def format_sections(registry: Optional[CareRegistry] = None) -> str:
    reg = registry or default_registry()
    return "\n".join(format_section(e) for e in reg.entries())


def format_record(record: CareRecord,
                  registry: Optional[CareRegistry] = None) -> str:
    reg = registry or default_registry()
    entry = reg.get(record.section)
    standing = derive_standing(record, reg)
    state = "held as answered" if standing.held else "open: " + "; ".join(standing.gaps)
    return (f"{record.section} {entry.doctrine}/{entry.subject}: "
            f"disposition {record.disposition} "
            f"({record.proof_kind}), date "
            f"{record.date or '(no date)'} - {state}")


def format_records(records: Iterable[CareRecord],
                   registry: Optional[CareRegistry] = None) -> str:
    return "\n".join(format_record(r, registry) for r in records)
