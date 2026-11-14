"""The truthful changelog book (roadmap slice M-268) - pure layer.

Part XI - Proof. The roadmap words: **proven / partial / NOT PROVEN per feature family, in the release itself.**

What this layer holds, as data: a family registry C-01..C-12 (the provider ocean family, the code intelligence family, the editors-hand family, the sandbox family, the parallel crews family, the memory and context family, the jarl mode family, the bridges family, the method engine family, the proof family, the core CLI family, the release family), each listed only, each labelled and evidenced; a changelog record per family holding its truth work, date, disposition PROVEN or PARTIAL or NOT_PROVEN, owner, proof kind and stage walk named-labelled-evidenced-dispositioned-held; a derived standing; a derived changelog verdict over the whole book; and a changelog report prepared only through the prepare road, ready or shared, never sealed, inflated or certified short of every family answered.

Honesty rule, made code: a family counts PROVEN only on held proof measured in the release itself resting on held evidence (an evidence_ref among evidence_ref, test_ref, run_ref, ledger_ref - never a bare claim). A family counts PARTIAL only where the proven part rests on held evidence and the unproven part is owned and recorded in the open. A family counts NOT_PROVEN only with a named owner and the reason recorded - an unproven family admitted in the open is honest; an unproven family dressed as proven is not. Silence is not a label: a family with no record stands missing, named in the verdict gaps.

Honest boundary: this book holds and judges changelog records as data; it does not itself cut a release or run a test. It proves nothing and ships nothing; the agent layer owns holding session records and speaking for them.
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
    "FAMILIES",
    "TRUTHFUL_CHANGELOG_SCHEMA",
    "TRUTHFUL_CHANGELOG_SLICE",
    "TruthfulChangelogStanding",
    "TruthfulChangelogVerdict",
    "TruthfulChangelogRecord",
    "TruthfulChangelogReport",
    "TruthfulChangelogEntry",
    "TruthfulChangelogRegistry",
    "default_registry",
    "derive_standing",
    "derive_verdict",
    "format_record",
    "format_records",
    "format_family",
    "format_families",
    "prepare_report",
]

TRUTHFUL_CHANGELOG_SLICE = "M-268"
TRUTHFUL_CHANGELOG_SCHEMA = "mythic.truthful_changelog/1"

PLAIN_EXPLANATION = (
    "The truthful changelog, done honestly: "
    "proven, partial or NOT PROVEN per feature "
    "family, printed in the release itself. A "
    "family counts PROVEN only on held proof, "
    "PARTIAL only where the proven part rests "
    "on held evidence and the rest is owned in "
    "the open, and NOT PROVEN only with its "
    "reason recorded - never silent, never "
    "inflated, never dressed as proven.")
USAGE = (
    "Record each family finding against its "
    "family, proven on held evidence, partial "
    "with the proven part evidenced and the "
    "remainder owned, or not proven with its "
    "owner and reason recorded; read the "
    "derived changelog verdict before letting "
    "any report claim the changelog complete; "
    "prepare a report only as a report, with "
    "every family answered - proven, partial "
    "or not proven, each in the open - and "
    "let a human share it. The whole changelog "
    "book, answered family by family, as data "
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
DISPOSITIONS = ("PROVEN", "PARTIAL", "NOT_PROVEN")
PROOF_KINDS = ("measured-and-held", "partially-held", "none")
DOCTRINE_REFS = ("truth-in-release", "no-inflation", "standing-law", "proof-duty")
SUBJECTS = ("provider-ocean-family", "code-intelligence-family", "editors-hand-family", "sandbox-family", "parallel-crews-family", "memory-context-family", "jarl-mode-family", "bridges-family", "method-engine-family", "proof-family", "core-cli-family", "release-family")


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
class TruthfulChangelogEntry:
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
                raise ValidationError(f"family entry missing {name}")
        if self.doctrine not in DOCTRINE_REFS:
            raise ValidationError(f"unknown family doctrine: {self.doctrine}")
        if self.subject not in SUBJECTS:
            raise ValidationError(f"unknown family subject: {self.subject}")
        if self.standing != "listed":
            raise ValidationError("family entries are listed data only, never a published verdict here; " f"refused standing: {self.standing}")
        if not self.labelled:
            raise ValidationError("family entries are labelled only; " f"refused unlabelled entry: {self.id}")
        if not self.evidenced:
            raise ValidationError("family entries are evidenced only; " f"refused unevidenced entry: {self.id}")


FAMILIES = (
    TruthfulChangelogEntry("C-01", "truth-in-release", "provider-ocean-family", "listed",
              "the provider ocean family: every provider door the coder can drive, Ollama and the house Aesir engine among them, keys held in Kista and never in the open"),
    TruthfulChangelogEntry("C-02", "truth-in-release", "code-intelligence-family", "listed",
              "the code intelligence family: the coder reading, searching and understanding a codebase before it lays a hand on it"),
    TruthfulChangelogEntry("C-03", "no-inflation", "editors-hand-family", "listed",
              "the editors-hand family: precise edits, renames and multi-file change sets, journal-first so every change can be undone"),
    TruthfulChangelogEntry("C-04", "truth-in-release", "sandbox-family", "listed",
              "the sandbox family: native sandboxing with no Docker anywhere in the road, by the standing law of the house"),
    TruthfulChangelogEntry("C-05", "no-inflation", "parallel-crews-family", "listed",
              "the parallel crews family: many teams building at once in separate worktrees, banking in roadmap order and never out of it"),
    TruthfulChangelogEntry("C-06", "truth-in-release", "memory-context-family", "listed",
              "the memory and context family: session memory, context assembly and the long memory of the campaign itself"),
    TruthfulChangelogEntry("C-07", "no-inflation", "jarl-mode-family", "listed",
              "the jarl mode family: plain language first for the human in charge, technical depth behind it and never instead of it"),
    TruthfulChangelogEntry("C-08", "truth-in-release", "bridges-family", "listed",
              "the bridges family: the roads to Samverk and Samtal and the wider world, credentials never leaving Kista"),
    TruthfulChangelogEntry("C-09", "standing-law", "method-engine-family", "listed",
              "the method engine family: the Mythic Engineering heart - inspect, build, test, repair, continue - that every slice of this road was built by"),
    TruthfulChangelogEntry("C-10", "proof-duty", "proof-family", "listed",
              "the proof family: the evidence discipline of Part XI itself - suites counted from logs, banking verified from git, nothing claimed uncounted"),
    TruthfulChangelogEntry("C-11", "truth-in-release", "core-cli-family", "listed",
              "the core CLI family: the terminal and chat surfaces the human actually drives, commands answering in their own words"),
    TruthfulChangelogEntry("C-12", "proof-duty", "release-family", "listed",
              "the release family: the release cut itself, its version shaping and this changelog riding inside it, telling the truth about all the rest"),
)


class TruthfulChangelogRegistry:
    def __init__(self, entries: Iterable[TruthfulChangelogEntry] = FAMILIES):
        self._entries: Dict[str, TruthfulChangelogEntry] = {}
        for entry in entries:
            entry.validate()
            if entry.id in self._entries:
                raise ValidationError(f"duplicate family: {entry.id}")
            self._entries[entry.id] = entry

    def get(self, family_id: str) -> TruthfulChangelogEntry:
        try:
            return self._entries[family_id]
        except KeyError:
            raise ValidationError(
                f"unknown family: {family_id}") from None

    def ids(self) -> Tuple[str, ...]:
        return tuple(self._entries)

    def entries(self) -> Tuple[TruthfulChangelogEntry, ...]:
        return tuple(self._entries.values())

    def combinations(self) -> Tuple[str, ...]:
        return tuple(self._entries)


def default_registry() -> TruthfulChangelogRegistry:
    return TruthfulChangelogRegistry()


@dataclass(frozen=True)
class TruthfulChangelogRecord:
    family: str
    work: str
    date: str
    disposition: str
    owner: str
    proof_kind: str
    stages: Tuple[str, ...]
    claims: Tuple[str, ...]

    def validate(self, registry: Optional[TruthfulChangelogRegistry] = None) -> None:
        (registry or default_registry()).get(self.family)
        if not self.work.strip():
            raise ValidationError("record names no changelog work")
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
class TruthfulChangelogStanding:
    held: bool
    stage: str
    grade: str
    gaps: Tuple[str, ...]


def derive_standing(record: TruthfulChangelogRecord,
                    registry: Optional[TruthfulChangelogRegistry] = None) -> TruthfulChangelogStanding:
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
        if record.proof_kind != "measured-and-held":
            gaps.append(
                f"a PROVEN family rests on {record.proof_kind} "
                "evidence, not held proof measured in the release itself: "
                "the changelog tells the truth or stands open")
        if "evidence_ref" not in record.claims:
            gaps.append(
                "the proven family rests on no held "
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
                "a partial family rests on no held "
                "evidence: the proven part must rest "
                "on held evidence, not on a claim")
        if record.disposition == "NOT_PROVEN" and record.proof_kind == "measured-and-held":
            gaps.append(
                "a NOT PROVEN family resting on full "
                "measured proof contradicts itself: "
                "re-disposition it PROVEN or PARTIAL")
    return TruthfulChangelogStanding(held=not gaps, stage=stage,
                           grade="held" if not gaps else "open",
                           gaps=tuple(gaps))


@dataclass(frozen=True)
class TruthfulChangelogVerdict:
    ready: bool
    gaps: Tuple[str, ...]
    proven_families: Tuple[str, ...]
    partial_families: Tuple[str, ...]
    not_proven_families: Tuple[str, ...]
    missing_families: Tuple[str, ...]


def derive_verdict(records: Iterable[TruthfulChangelogRecord],
                   registry: Optional[TruthfulChangelogRegistry] = None) -> TruthfulChangelogVerdict:
    reg = registry or default_registry()
    by_family: Dict[str, TruthfulChangelogRecord] = {}
    gaps = []
    for record in records:
        record.validate(reg)
        if record.family in by_family:
            gaps.append(
                f"family {record.family} carries two findings")
        else:
            by_family[record.family] = record
    missing = tuple(aid for aid in reg.combinations()
                    if aid not in by_family)
    for family_id in missing:
        gaps.append(f"family {family_id} has no finding in the book")
    fixed = []
    partial = []
    notproven = []
    for family_id, record in by_family.items():
        standing = derive_standing(record, reg)
        if standing.held and record.disposition == "PROVEN":
            fixed.append(family_id)
        if standing.held and record.disposition == "PARTIAL":
            partial.append(family_id)
        if standing.held and record.disposition == "NOT_PROVEN":
            notproven.append(family_id)
        if not standing.held:
            gaps.append(
                f"family {family_id} stands open: "
                + "; ".join(standing.gaps))
    return TruthfulChangelogVerdict(ready=not gaps, gaps=tuple(gaps),
                        proven_families=tuple(fixed),
                        partial_families=tuple(partial),
                        not_proven_families=tuple(notproven), missing_families=missing)


@dataclass(frozen=True)
class TruthfulChangelogReport:
    book: str
    entry: str
    report: str
    date: str
    proven_count: int
    partial_count: int
    not_proven_count: int
    total_families: int
    claims: Tuple[str, ...]
    state: str = "ready"
    certified: bool = False
    inflated: bool = False

    def validate(self, registry: Optional[TruthfulChangelogRegistry] = None) -> None:
        reg = registry or default_registry()
        if not self.book.strip():
            raise ValidationError("report names no book")
        if not self.entry.strip():
            raise ValidationError("report names no entry")
        if not self.report.strip():
            raise ValidationError("changelog reports nothing")
        if not self.date:
            raise ValidationError(
                "report names no date: a changelog "
                "report is reported with its date")
        _check_date(self.date)
        expected = len(reg.combinations())
        if self.total_families != expected:
            raise ValidationError(
                f"report book holds {self.total_families} "
                f"families, not the road's {expected}")
        if self.proven_count < 0 or self.partial_count < 0 or self.not_proven_count < 0:
            raise ValidationError(
                "unknown family count: "
                f"{self.proven_count}/{self.partial_count}/{self.not_proven_count}")
        if self.proven_count + self.partial_count + self.not_proven_count > self.total_families:
            raise ValidationError(
                "answered families exceed the book: "
                f"{self.proven_count} + {self.partial_count} + {self.not_proven_count} "
                f"of {self.total_families}")
        for kind in self.claims:
            if kind not in EVIDENCE_KINDS:
                raise ValidationError(f"unknown report evidence kind: {kind}")
        if not [c for c in self.claims if c in HELD_EVIDENCE]:
            raise ValidationError(
                "changelogs report held findings "
                "only; a report dressing a bare claim "
                "as a proof refuses here")
        if self.state not in REPORT_STATES:
            raise ValidationError(
                "changelogs stand ready or shared "
                "only, never sealed or locked; refused "
                f"state: {self.state}")
        if self.certified and \
                self.proven_count + self.partial_count + self.not_proven_count < self.total_families:
            raise ValidationError(
                "an unanswered family anywhere stops "
                "the closing claim: this report may not "
                "claim the changelog complete short of "
                "every family answered")
        if self.inflated:
            raise ValidationError(
                "changelogs report the findings "
                "exactly as they were dispositioned; a "
                "report is never inflated here")


def prepare_report(book: str, entry: str, report: str,
                   date: str, proven_count: int, partial_count: int, not_proven_count: int,
                   total_families: int,
                   claims: Tuple[str, ...] = (),
                   state: str = "ready",
                   certified: bool = False) -> TruthfulChangelogReport:
    made = TruthfulChangelogReport(book=book, entry=entry,
                       report=report, date=date,
                       proven_count=proven_count,
                       partial_count=partial_count,
                       not_proven_count=not_proven_count,
                       total_families=total_families,
                       claims=tuple(claims),
                       state=state, certified=certified)
    made.validate()
    return made


def format_family(entry: TruthfulChangelogEntry) -> str:
    return (f"{entry.id} {entry.doctrine}/{entry.subject}: "
            f"standing {entry.standing} "
            f"- {entry.reason}")


def format_families(registry: Optional[TruthfulChangelogRegistry] = None) -> str:
    reg = registry or default_registry()
    return "\n".join(format_family(e) for e in reg.entries())


def format_record(record: TruthfulChangelogRecord,
                  registry: Optional[TruthfulChangelogRegistry] = None) -> str:
    reg = registry or default_registry()
    entry = reg.get(record.family)
    standing = derive_standing(record, reg)
    state = "held as answered" if standing.held else "open: " + "; ".join(standing.gaps)
    return (f"{record.family} {entry.doctrine}/{entry.subject}: "
            f"disposition {record.disposition} "
            f"({record.proof_kind}), date "
            f"{record.date or '(no date)'} - {state}")


def format_records(records: Iterable[TruthfulChangelogRecord],
                   registry: Optional[TruthfulChangelogRegistry] = None) -> str:
    return "\n".join(format_record(r, registry) for r in records)
