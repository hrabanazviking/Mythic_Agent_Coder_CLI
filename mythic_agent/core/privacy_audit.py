"""The privacy-audit book (roadmap slice M-261) - pure layer.

Part XI - Proof. The roadmap words: **no phone-home
verified by network capture during a full benchmark
run; the capture is the evidence.**

What this layer holds, as data:

* A **surface registry** held as data - one entry
  per surface that could carry data out of the
  machine: telemetry, provider calls, the benchmark
  run itself, update checks, DNS lookups, crash
  reports, analytics, model downloads, log uploads,
  license checks, plugin loads and external links,
  P-01..P-12 in audit order, its plain standing,
  and why the entry stands, in plain words. Every
  entry arrives as listed data (standing 'listed');
  a surface the registry does not hold refuses BY
  NAME; a duplicated, half-written, or published
  entry refuses whole. A new surface needs no code
  change.
* A **capture record** holds, for one surface,
  that surface's privacy finding as a supplied
  fact: the benchmark run that was captured, the
  date of the capture, the disposition it carries
  (CLEAN or ROADED), the owner who carries it,
  the kind of proof it rests on (network-capture,
  historical-only, or none), the stages it has
  walked, and the claims it rests on, by kind.
  Its standing is DERIVED at call time against
  the explicit stage walk held as data (STAGES,
  TRANSITIONS): named, captured, judged,
  dispositioned, held. A CLEAN finding stands
  held only when its proof is the audit's own
  network capture and rests on held capture
  evidence (a capture_ref among held evidence -
  capture_ref, local_run_ref, ci_run_ref,
  journal_ref - never a bare claim: feeling,
  memory, assertion, summary), and the walk is
  complete: no inheritance, so a CLEAN verdict
  resting on historical or no evidence stands
  open, named in its gaps. A ROADED finding
  stands held only when it names its owner and
  is recorded openly - a roaded finding with no
  owner is a wish, not a road, and a roaded
  finding with nothing recorded stands open as
  silent.
* A **privacy verdict** is DERIVED over a whole
  book of records: the audit stands ready only
  when every surface carries a held record - a
  missing surface, an open record, or a silent
  finding anywhere stops the audit, and the
  verdict names what stopped it, beside the
  clean and roaded surfaces it holds.
* A **privacy report** is the only shape a book
  may produce as a report, prepared only through
  the prepare road. A report stands at state
  "ready" by default, may be marked "shared" by
  a human, and reports the findings exactly as
  they were dispositioned. A report asking to be
  sealed or locked instead of ready/shared, to
  be inflated instead of reported, to dress a
  bare claim up as a proof, or to claim the
  audit closed while any surface stands
  unanswered, refuses BY NAME.

Honesty rule, made code: a surface counts CLEAN
only on the audit's own network capture, taken
during a full benchmark run, resting on held
capture evidence. Everything else ships ROADED
with a named owner, in the open - never
inherited, never ownerless, never silent, never
inflated.

Honest boundary: this layer holds registry
entries, capture records, derived standings,
derived privacy verdicts and privacy reports as
data. It captures no traffic, runs no benchmark,
fixes nothing and writes nothing outside the
session; the agent layer owns holding a
session's records and speaking for them.
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
    "SURFACES",
    "PRIVACY_AUDIT_SCHEMA",
    "PRIVACY_AUDIT_SLICE",
    "CaptureStanding",
    "PrivacyVerdict",
    "CaptureRecord",
    "PrivacyReport",
    "SurfaceEntry",
    "SurfaceRegistry",
    "default_registry",
    "derive_standing",
    "derive_verdict",
    "format_record",
    "format_records",
    "format_surface",
    "format_surfaces",
    "prepare_report",
]

PRIVACY_AUDIT_SLICE = "M-261"
PRIVACY_AUDIT_SCHEMA = "mythic.privacy_audit/1"

PLAIN_EXPLANATION = (
    "The privacy audit, done honestly: no "
    "phone-home is verified by network capture "
    "during a full benchmark run, and the capture "
    "is the evidence. A surface counts CLEAN only "
    "on the audit's own capture resting on held "
    "capture evidence. Every other finding ships "
    "ROADED with a named owner, in the open - an "
    "ownerless road is named, never silent, and "
    "no historical capture is inherited as proof."
)
USAGE = (
    "Record each surface's finding against its "
    "surface, clean on network-capture evidence or "
    "roaded with its owner named; read the derived "
    "privacy verdict before letting any report claim "
    "the audit closed; prepare a report only as a "
    "report, with every surface answered - clean on "
    "held capture evidence or roaded with an owner - "
    "and let a human share it. The whole doctrine, "
    "answered surface by surface, as data first."
)

STAGES = ("named", "captured", "judged", "dispositioned", "held")
TRANSITIONS = {
    "named": ("captured",),
    "captured": ("judged",),
    "judged": ("dispositioned",),
    "dispositioned": ("held",),
    "held": (),
}
HELD_EVIDENCE = ("capture_ref", "local_run_ref", "ci_run_ref", "journal_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
EVIDENCE_KINDS = HELD_EVIDENCE + BARE_CLAIMS
REPORT_STATES = ("ready", "shared")
DISPOSITIONS = ("CLEAN", "ROADED")
PROOF_KINDS = ("network-capture", "historical-only", "none")
DOCTRINE_REFS = ("M-015", "M-098", "M-255", "M-109", "M-110", "M-119")
SUBJECTS = ("telemetry", "provider-calls", "benchmark-run", "update-checks",
            "dns-lookups", "crash-reports", "analytics", "model-downloads",
            "log-uploads", "license-checks", "plugin-loads", "external-links")


def _check_date(value: str) -> None:
    ok = (isinstance(value, str) and len(value) == 10
          and value[4] == "-" and value[7] == "-")
    if ok:
        try:
            _date.fromisoformat(value)
        except ValueError:
            ok = False
    if not ok:
        raise ValidationError(f"unknown capture date: {value}")


@dataclass(frozen=True)
class SurfaceEntry:
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
            raise ValidationError(f"unknown surface doctrine: {self.doctrine}")
        if self.subject not in SUBJECTS:
            raise ValidationError(f"unknown surface subject: {self.subject}")
        if self.standing != "listed":
            raise ValidationError(
                "surface entries are listed data "
                "only, never a published verdict here; "
                f"refused standing: {self.standing}")


SURFACES = (
    SurfaceEntry("P-01", "M-015", "telemetry", "listed",
              "the telemetry honesty ground, captured during a full benchmark run in the privacy audit"),
    SurfaceEntry("P-02", "M-098", "provider-calls", "listed",
              "the provider calls a benchmark run makes, captured in the privacy audit"),
    SurfaceEntry("P-03", "M-255", "benchmark-run", "listed",
              "the full benchmark run itself, the capture occasion of the privacy audit"),
    SurfaceEntry("P-04", "M-015", "update-checks", "listed",
              "update checks that could phone home, captured in the privacy audit"),
    SurfaceEntry("P-05", "M-098", "dns-lookups", "listed",
              "DNS lookups during the run, captured in the privacy audit"),
    SurfaceEntry("P-06", "M-109", "crash-reports", "listed",
              "crash reports that could leave the machine, captured in the privacy audit"),
    SurfaceEntry("P-07", "M-110", "analytics", "listed",
              "analytics beacons, captured during a full benchmark run in the privacy audit"),
    SurfaceEntry("P-08", "M-098", "model-downloads", "listed",
              "model downloads and their hosts, captured in the privacy audit"),
    SurfaceEntry("P-09", "M-109", "log-uploads", "listed",
              "log uploads that could leave the machine, captured in the privacy audit"),
    SurfaceEntry("P-10", "M-015", "license-checks", "listed",
              "license checks that could phone home, captured in the privacy audit"),
    SurfaceEntry("P-11", "M-098", "plugin-loads", "listed",
              "plugin loads reaching the network, captured in the privacy audit"),
    SurfaceEntry("P-12", "M-119", "external-links", "listed",
              "external links opened during the run, captured in the privacy audit"),
)


class SurfaceRegistry:
    def __init__(self, entries: Iterable[SurfaceEntry] = SURFACES):
        self._entries: Dict[str, SurfaceEntry] = {}
        for entry in entries:
            entry.validate()
            if entry.id in self._entries:
                raise ValidationError(f"duplicate surface: {entry.id}")
            self._entries[entry.id] = entry

    def get(self, surface_id: str) -> SurfaceEntry:
        try:
            return self._entries[surface_id]
        except KeyError:
            raise ValidationError(
                f"unknown surface: {surface_id}") from None

    def ids(self) -> Tuple[str, ...]:
        return tuple(self._entries)

    def entries(self) -> Tuple[SurfaceEntry, ...]:
        return tuple(self._entries.values())

    def combinations(self) -> Tuple[str, ...]:
        return tuple(self._entries)


def default_registry() -> SurfaceRegistry:
    return SurfaceRegistry()


@dataclass(frozen=True)
class CaptureRecord:
    surface: str
    run: str
    date: str
    disposition: str
    owner: str
    proof_kind: str
    stages: Tuple[str, ...]
    claims: Tuple[str, ...]

    def validate(self, registry: Optional[SurfaceRegistry] = None) -> None:
        (registry or default_registry()).get(self.surface)
        if not self.run.strip():
            raise ValidationError("record names no benchmark run")
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
class CaptureStanding:
    held: bool
    stage: str
    grade: str
    gaps: Tuple[str, ...]


def derive_standing(record: CaptureRecord,
                    registry: Optional[SurfaceRegistry] = None) -> CaptureStanding:
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
        gaps.append("record names no capture date")
    if record.disposition == "CLEAN":
        if record.proof_kind != "network-capture":
            gaps.append(
                f"a CLEAN finding rests on {record.proof_kind} "
                "evidence, not the audit's network capture: "
                "no inheritance")
        if "capture_ref" not in record.claims:
            gaps.append(
                "the clean finding rests on no held "
                "capture evidence")
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
    return CaptureStanding(held=not gaps, stage=stage,
                           grade="held" if not gaps else "open",
                           gaps=tuple(gaps))


@dataclass(frozen=True)
class PrivacyVerdict:
    ready: bool
    gaps: Tuple[str, ...]
    clean_surfaces: Tuple[str, ...]
    roaded_surfaces: Tuple[str, ...]
    missing_surfaces: Tuple[str, ...]


def derive_verdict(records: Iterable[CaptureRecord],
                   registry: Optional[SurfaceRegistry] = None) -> PrivacyVerdict:
    reg = registry or default_registry()
    by_surface: Dict[str, CaptureRecord] = {}
    gaps = []
    for record in records:
        record.validate(reg)
        if record.surface in by_surface:
            gaps.append(
                f"surface {record.surface} carries two findings")
        else:
            by_surface[record.surface] = record
    missing = tuple(aid for aid in reg.combinations()
                    if aid not in by_surface)
    for surface_id in missing:
        gaps.append(f"surface {surface_id} has no finding in the book")
    fixed = []
    roaded = []
    for surface_id, record in by_surface.items():
        standing = derive_standing(record, reg)
        if standing.held and record.disposition == "CLEAN":
            fixed.append(surface_id)
        if standing.held and record.disposition == "ROADED":
            roaded.append(surface_id)
        if not standing.held:
            gaps.append(
                f"surface {surface_id} stands open: "
                + "; ".join(standing.gaps))
    return PrivacyVerdict(ready=not gaps, gaps=tuple(gaps),
                        clean_surfaces=tuple(fixed),
                        roaded_surfaces=tuple(roaded),
                        missing_surfaces=missing)


@dataclass(frozen=True)
class PrivacyReport:
    book: str
    entry: str
    report: str
    date: str
    clean_count: int
    roaded_count: int
    total_surfaces: int
    claims: Tuple[str, ...]
    state: str = "ready"
    certified: bool = False
    inflated: bool = False

    def validate(self, registry: Optional[SurfaceRegistry] = None) -> None:
        reg = registry or default_registry()
        if not self.book.strip():
            raise ValidationError("report names no book")
        if not self.entry.strip():
            raise ValidationError("report names no entry")
        if not self.report.strip():
            raise ValidationError("privacy report reports nothing")
        if not self.date:
            raise ValidationError(
                "report names no date: a privacy "
                "report is reported with its date")
        _check_date(self.date)
        expected = len(reg.combinations())
        if self.total_surfaces != expected:
            raise ValidationError(
                f"report book holds {self.total_surfaces} "
                f"surfaces, not the road's {expected}")
        if self.clean_count < 0 or self.roaded_count < 0:
            raise ValidationError(
                "unknown surface count: "
                f"{self.clean_count}/{self.roaded_count}")
        if self.clean_count + self.roaded_count > self.total_surfaces:
            raise ValidationError(
                "answered surfaces exceed the book: "
                f"{self.clean_count} + {self.roaded_count} "
                f"of {self.total_surfaces}")
        for kind in self.claims:
            if kind not in EVIDENCE_KINDS:
                raise ValidationError(f"unknown report evidence kind: {kind}")
        if not [c for c in self.claims if c in HELD_EVIDENCE]:
            raise ValidationError(
                "privacy reports report held findings "
                "only; a report dressing a bare claim "
                "as a proof refuses here")
        if self.state not in REPORT_STATES:
            raise ValidationError(
                "privacy reports stand ready or shared "
                "only, never sealed or locked; refused "
                f"state: {self.state}")
        if self.certified and \
                self.clean_count + self.roaded_count < self.total_surfaces:
            raise ValidationError(
                "an unanswered surface anywhere stops "
                "the closing claim: this report may not "
                "claim the audit closed short of "
                "every surface answered")
        if self.inflated:
            raise ValidationError(
                "privacy reports report the findings "
                "exactly as they were dispositioned; a "
                "report is never inflated here")


def prepare_report(book: str, entry: str, report: str,
                   date: str, clean_count: int, roaded_count: int,
                   total_surfaces: int,
                   claims: Tuple[str, ...] = (),
                   state: str = "ready",
                   certified: bool = False) -> PrivacyReport:
    made = PrivacyReport(book=book, entry=entry,
                       report=report, date=date,
                       clean_count=clean_count,
                       roaded_count=roaded_count,
                       total_surfaces=total_surfaces,
                       claims=tuple(claims),
                       state=state, certified=certified)
    made.validate()
    return made


def format_surface(entry: SurfaceEntry) -> str:
    return (f"{entry.id} {entry.doctrine}/{entry.subject}: "
            f"standing {entry.standing} "
            f"- {entry.reason}")


def format_surfaces(registry: Optional[SurfaceRegistry] = None) -> str:
    reg = registry or default_registry()
    return "\n".join(format_surface(e) for e in reg.entries())


def format_record(record: CaptureRecord,
                  registry: Optional[SurfaceRegistry] = None) -> str:
    reg = registry or default_registry()
    entry = reg.get(record.surface)
    standing = derive_standing(record, reg)
    state = "held as answered" if standing.held else "open: " + "; ".join(standing.gaps)
    return (f"{record.surface} {entry.doctrine}/{entry.subject}: "
            f"disposition {record.disposition} "
            f"({record.proof_kind}), date "
            f"{record.date or '(no date)'} - {state}")


def format_records(records: Iterable[CaptureRecord],
                   registry: Optional[SurfaceRegistry] = None) -> str:
    return "\n".join(format_record(r, registry) for r in records)
