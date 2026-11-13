"""The migration-proof book (roadmap slice M-265) - pure layer.

Part XI - Proof. The roadmap words: **a workspace from the current release opens in the new one - sessions, journals, configs, memories intact - proven by the M-010 forward-compat tests grown teeth.**

What this layer holds, as data: an area registry G-01..G-12 (session store, journal store, config store, memory store, workspace layout, provider configs, editor state, crew state, chat history, project map, key vault refs, forward-compat suite), each listed only; a migration record per area holding its opening work, date, disposition PROVEN or ROADED, owner, proof kind and stage walk named-opened-checked-dispositioned-held; a derived standing; a derived migration verdict over the whole book; and a migration report prepared only through the prepare road, ready or shared, never sealed, inflated or certified short of every area answered.

Honesty rule, made code: an area counts PROVEN only on the old workspace actually opening in the new release resting on held workspace evidence (a workspace_ref among workspace_ref, session_ref, journal_ref, local_run_ref - never a bare claim). A PROVEN finding on historical or no proof stands open, named in its gaps: no inheritance. A ROADED finding stands held only with a named owner and something recorded - ownerless is a wish, silent is not a road. A workspace claimed migrated from memory of the old release, not from opening it in the new one, faces the book as data here, not as an inherited truth.

Honest boundary: this layer holds entries, records, standings, verdicts and reports as data. It opens no workspace, migrates no file and writes nothing outside the session; the agent layer owns holding a session records and speaking for them.
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
    "AREAS",
    "MIGRATION_PROOF_SCHEMA",
    "MIGRATION_PROOF_SLICE",
    "MigrationStanding",
    "MigrationVerdict",
    "MigrationRecord",
    "MigrationReport",
    "MigrationEntry",
    "MigrationRegistry",
    "default_registry",
    "derive_standing",
    "derive_verdict",
    "format_record",
    "format_records",
    "format_area",
    "format_areas",
    "prepare_report",
]

MIGRATION_PROOF_SLICE = "M-265"
MIGRATION_PROOF_SCHEMA = "mythic.migration_proof/1"

PLAIN_EXPLANATION = (
    "Migration proof, done honestly: "
    "a workspace from the current release "
    "opens in the new one - sessions, journals, "
    "configs, memories intact. An area counts "
    "PROVEN only on the old workspace actually "
    "opening in the new release resting on held "
    "workspace evidence. Every other area ships "
    "ROADED with a named owner, in the open - an "
    "ownerless road is named, never silent, and "
    "no area is claimed migrated from memory."
)
USAGE = (
    "Record each area finding against its area, "
    "proven by opening the current-release "
    "workspace in the new release or roaded with "
    "its owner named; read the derived migration "
    "verdict before letting any report claim the "
    "migration complete; prepare a report only as "
    "a report, with every area answered - proven on "
    "held workspace evidence or roaded with an "
    "owner - and let a human share it. The whole "
    "migration book, answered area by area, as "
    "data first."
)


STAGES = ("named", "opened", "checked", "dispositioned", "held")
TRANSITIONS = {
    "named": ("opened",),
    "opened": ("checked",),
    "checked": ("dispositioned",),
    "dispositioned": ("held",),
    "held": (),
}
HELD_EVIDENCE = ("workspace_ref", "session_ref", "journal_ref", "local_run_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
EVIDENCE_KINDS = HELD_EVIDENCE + BARE_CLAIMS
REPORT_STATES = ("ready", "shared")
DISPOSITIONS = ("PROVEN", "ROADED")
PROOF_KINDS = ("opened-in-new-release", "historical-only", "none")
DOCTRINE_REFS = ("forward-compat", "shipped-workspace", "standing-law", "proof-duty")
SUBJECTS = ("session-store", "journal-store", "config-store", "memory-store", "workspace-layout", "provider-configs", "editor-state", "crew-state", "chat-history", "project-map", "key-vault-refs", "forward-compat-suite")


def _check_date(value: str) -> None:
    ok = (isinstance(value, str) and len(value) == 10 and value[4] == "-" and value[7] == "-")
    if ok:
        try:
            _date.fromisoformat(value)
        except ValueError:
            ok = False
    if not ok:
        raise ValidationError(f"unknown migration date: {value}")


@dataclass(frozen=True)
class MigrationEntry:
    id: str
    doctrine: str
    subject: str
    standing: str
    reason: str
    def validate(self) -> None:
        for name in ("id", "doctrine", "subject", "standing", "reason"):
            if not str(getattr(self, name)).strip():
                raise ValidationError(f"area entry missing {name}")
        if self.doctrine not in DOCTRINE_REFS:
            raise ValidationError(f"unknown area doctrine: {self.doctrine}")
        if self.subject not in SUBJECTS:
            raise ValidationError(f"unknown area subject: {self.subject}")
        if self.standing != "listed":
            raise ValidationError("area entries are listed data only, never a published verdict here; " f"refused standing: {self.standing}")


AREAS = (
    MigrationEntry("G-01", "forward-compat", "session-store", "listed",
              "sessions written by the current release open in the new one, history intact, proven by the M-010 forward-compat tests grown teeth"),
    MigrationEntry("G-02", "shipped-workspace", "journal-store", "listed",
              "the edit journals of the current release open in the new one, every entry intact and undo unbroken"),
    MigrationEntry("G-03", "shipped-workspace", "config-store", "listed",
              "configs written by the current release open in the new one, every setting carried, none silently dropped"),
    MigrationEntry("G-04", "forward-compat", "memory-store", "listed",
              "memories kept by the current release open in the new one, intact and readable in their own words"),
    MigrationEntry("G-05", "shipped-workspace", "workspace-layout", "listed",
              "the workspace layout itself - its folders and its marks - is recognised by the new release as its own"),
    MigrationEntry("G-06", "shipped-workspace", "provider-configs", "listed",
              "provider configs open in the new one with the Provider Ocean intact; keys stay in Kista, only their refs travel"),
    MigrationEntry("G-07", "shipped-workspace", "editor-state", "listed",
              "editor state - open files, hand positions, checkpoints - opens in the new one where the hand left it"),
    MigrationEntry("G-08", "shipped-workspace", "crew-state", "listed",
              "crew state - parallel crews and their standing work - opens in the new one, no crew's work lost"),
    MigrationEntry("G-09", "shipped-workspace", "chat-history", "listed",
              "chat history opens in the new one, the whole conversation readable as it was left"),
    MigrationEntry("G-10", "shipped-workspace", "project-map", "listed",
              "the project map opens in the new one, its slices and standings carried whole"),
    MigrationEntry("G-11", "standing-law", "key-vault-refs", "listed",
              "key vault refs open in the new one as refs only - no secret is copied, moved or exposed by the migration itself"),
    MigrationEntry("G-12", "proof-duty", "forward-compat-suite", "listed",
              "the forward-compat suite itself: the M-010 tests grown teeth, run against a real current-release workspace, not a sketch of one"),
)


class MigrationRegistry:
    def __init__(self, entries: Iterable[MigrationEntry] = AREAS):
        self._entries: Dict[str, MigrationEntry] = {}
        for entry in entries:
            entry.validate()
            if entry.id in self._entries:
                raise ValidationError(f"duplicate area: {entry.id}")
            self._entries[entry.id] = entry

    def get(self, area_id: str) -> MigrationEntry:
        try:
            return self._entries[area_id]
        except KeyError:
            raise ValidationError(
                f"unknown area: {area_id}") from None

    def ids(self) -> Tuple[str, ...]:
        return tuple(self._entries)

    def entries(self) -> Tuple[MigrationEntry, ...]:
        return tuple(self._entries.values())

    def combinations(self) -> Tuple[str, ...]:
        return tuple(self._entries)


def default_registry() -> MigrationRegistry:
    return MigrationRegistry()


@dataclass(frozen=True)
class MigrationRecord:
    area: str
    work: str
    date: str
    disposition: str
    owner: str
    proof_kind: str
    stages: Tuple[str, ...]
    claims: Tuple[str, ...]

    def validate(self, registry: Optional[MigrationRegistry] = None) -> None:
        (registry or default_registry()).get(self.area)
        if not self.work.strip():
            raise ValidationError("record names no opening work")
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
class MigrationStanding:
    held: bool
    stage: str
    grade: str
    gaps: Tuple[str, ...]


def derive_standing(record: MigrationRecord,
                    registry: Optional[MigrationRegistry] = None) -> MigrationStanding:
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
        gaps.append("record names no migration date")
    if record.disposition == "PROVEN":
        if record.proof_kind != "opened-in-new-release":
            gaps.append(
                f"a PROVEN area rests on {record.proof_kind} "
                "evidence, not the old workspace opening in the new release: "
                "no inheritance")
        if "workspace_ref" not in record.claims:
            gaps.append(
                "the proven area rests on no held "
                "workspace evidence")
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
    return MigrationStanding(held=not gaps, stage=stage,
                           grade="held" if not gaps else "open",
                           gaps=tuple(gaps))


@dataclass(frozen=True)
class MigrationVerdict:
    ready: bool
    gaps: Tuple[str, ...]
    proven_areas: Tuple[str, ...]
    roaded_areas: Tuple[str, ...]
    missing_areas: Tuple[str, ...]


def derive_verdict(records: Iterable[MigrationRecord],
                   registry: Optional[MigrationRegistry] = None) -> MigrationVerdict:
    reg = registry or default_registry()
    by_area: Dict[str, MigrationRecord] = {}
    gaps = []
    for record in records:
        record.validate(reg)
        if record.area in by_area:
            gaps.append(
                f"area {record.area} carries two findings")
        else:
            by_area[record.area] = record
    missing = tuple(aid for aid in reg.combinations()
                    if aid not in by_area)
    for area_id in missing:
        gaps.append(f"area {area_id} has no finding in the book")
    fixed = []
    roaded = []
    for area_id, record in by_area.items():
        standing = derive_standing(record, reg)
        if standing.held and record.disposition == "PROVEN":
            fixed.append(area_id)
        if standing.held and record.disposition == "ROADED":
            roaded.append(area_id)
        if not standing.held:
            gaps.append(
                f"area {area_id} stands open: "
                + "; ".join(standing.gaps))
    return MigrationVerdict(ready=not gaps, gaps=tuple(gaps),
                        proven_areas=tuple(fixed),
                        roaded_areas=tuple(roaded),
                        missing_areas=missing)


@dataclass(frozen=True)
class MigrationReport:
    book: str
    entry: str
    report: str
    date: str
    proven_count: int
    roaded_count: int
    total_areas: int
    claims: Tuple[str, ...]
    state: str = "ready"
    certified: bool = False
    inflated: bool = False

    def validate(self, registry: Optional[MigrationRegistry] = None) -> None:
        reg = registry or default_registry()
        if not self.book.strip():
            raise ValidationError("report names no book")
        if not self.entry.strip():
            raise ValidationError("report names no entry")
        if not self.report.strip():
            raise ValidationError("migration report reports nothing")
        if not self.date:
            raise ValidationError(
                "report names no date: a migration "
                "report is reported with its date")
        _check_date(self.date)
        expected = len(reg.combinations())
        if self.total_areas != expected:
            raise ValidationError(
                f"report book holds {self.total_areas} "
                f"areas, not the road's {expected}")
        if self.proven_count < 0 or self.roaded_count < 0:
            raise ValidationError(
                "unknown area count: "
                f"{self.proven_count}/{self.roaded_count}")
        if self.proven_count + self.roaded_count > self.total_areas:
            raise ValidationError(
                "answered areas exceed the book: "
                f"{self.proven_count} + {self.roaded_count} "
                f"of {self.total_areas}")
        for kind in self.claims:
            if kind not in EVIDENCE_KINDS:
                raise ValidationError(f"unknown report evidence kind: {kind}")
        if not [c for c in self.claims if c in HELD_EVIDENCE]:
            raise ValidationError(
                "migration reports report held findings "
                "only; a report dressing a bare claim "
                "as a proof refuses here")
        if self.state not in REPORT_STATES:
            raise ValidationError(
                "migration reports stand ready or shared "
                "only, never sealed or locked; refused "
                f"state: {self.state}")
        if self.certified and \
                self.proven_count + self.roaded_count < self.total_areas:
            raise ValidationError(
                "an unanswered area anywhere stops "
                "the closing claim: this report may not "
                "claim the migration complete short of "
                "every area answered")
        if self.inflated:
            raise ValidationError(
                "migration reports report the findings "
                "exactly as they were dispositioned; a "
                "report is never inflated here")


def prepare_report(book: str, entry: str, report: str,
                   date: str, proven_count: int, roaded_count: int,
                   total_areas: int,
                   claims: Tuple[str, ...] = (),
                   state: str = "ready",
                   certified: bool = False) -> MigrationReport:
    made = MigrationReport(book=book, entry=entry,
                       report=report, date=date,
                       proven_count=proven_count,
                       roaded_count=roaded_count,
                       total_areas=total_areas,
                       claims=tuple(claims),
                       state=state, certified=certified)
    made.validate()
    return made


def format_area(entry: MigrationEntry) -> str:
    return (f"{entry.id} {entry.doctrine}/{entry.subject}: "
            f"standing {entry.standing} "
            f"- {entry.reason}")


def format_areas(registry: Optional[MigrationRegistry] = None) -> str:
    reg = registry or default_registry()
    return "\n".join(format_area(e) for e in reg.entries())


def format_record(record: MigrationRecord,
                  registry: Optional[MigrationRegistry] = None) -> str:
    reg = registry or default_registry()
    entry = reg.get(record.area)
    standing = derive_standing(record, reg)
    state = "held as answered" if standing.held else "open: " + "; ".join(standing.gaps)
    return (f"{record.area} {entry.doctrine}/{entry.subject}: "
            f"disposition {record.disposition} "
            f"({record.proof_kind}), date "
            f"{record.date or '(no date)'} - {state}")


def format_records(records: Iterable[MigrationRecord],
                   registry: Optional[MigrationRegistry] = None) -> str:
    return "\n".join(format_record(r, registry) for r in records)
