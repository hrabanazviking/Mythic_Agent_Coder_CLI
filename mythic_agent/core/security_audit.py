"""The security-audit book (roadmap slice M-260) - pure layer.

Part XI - Proof. The roadmap words: **the Part V
doctrine + M-118 red-team pack + an independent
read of the sandbox/jail code, findings fixed or
roaded with owners.**

What this layer holds, as data:

* An **area registry** held as data - one entry
  per ground the audit must cover: the Part V
  doctrine slices (permission profiles, remembered
  approvals, the OS sandbox, network gates, the
  path jail, the hooks lifecycle, the kill switch,
  the audit trail, secret hygiene, the
  destructive-command doctrine, policy as code)
  and the M-118 red-team pack, S-01..S-12 in
  doctrine order, its plain standing, and why the
  entry stands, in plain words. Every entry
  arrives as listed data (standing 'listed'); an
  area the registry does not hold refuses BY
  NAME; a duplicated, half-written, or published
  entry refuses whole. A new area needs no code
  change.
* A **finding record** holds, for one area, that
  area's audit finding as a supplied fact: the
  audit run that found it, the date it was found,
  the disposition it carries (FIXED or ROADED),
  the owner who carries it, the kind of proof it
  rests on (independent-read, historical-only, or
  none), the stages it has walked, and the claims
  it rests on, by kind. Its standing is DERIVED
  at call time against the explicit stage walk
  held as data (STAGES, TRANSITIONS): named,
  examined, judged, dispositioned, held. A FIXED
  finding stands held only when its proof is the
  audit's own independent read and rests on held
  local evidence (a local_run_ref among held
  evidence - local_run_ref, ci_run_ref,
  report_ref, journal_ref - never a bare claim:
  feeling, memory, assertion, summary), and the
  walk is complete: no inheritance, so a FIXED
  verdict resting on historical or no evidence
  stands open, named in its gaps. A ROADED
  finding stands held only when it names its
  owner and is recorded openly - a roaded finding
  with no owner is a wish, not a road, and a
  roaded finding with nothing recorded stands
  open as silent.
* An **audit verdict** is DERIVED over a whole
  book of records: the audit stands ready only
  when every area carries a held record - a
  missing area, an open record, or a silent
  finding anywhere stops the audit, and the
  verdict names what stopped it, beside the
  fixed and roaded areas it holds.
* An **audit report** is the only shape a book
  may produce as a report, prepared only through
  the prepare road. A report stands at state
  "ready" by default, may be marked "shared" by
  a human, and reports the findings exactly as
  they were dispositioned. A report asking to be
  sealed or locked instead of ready/shared, to
  be inflated instead of reported, to dress a
  bare claim up as a proof, or to claim the
  audit closed while any area stands unanswered,
  refuses BY NAME.

Honesty rule, made code: a finding counts FIXED
only on the audit's own independent read, on the
current tree, resting on held local evidence.
Everything else ships ROADED with a named owner,
in the open - never inherited, never ownerless,
never silent, never inflated.

Honest boundary: this layer holds registry
entries, finding records, derived standings,
derived audit verdicts and audit reports as
data. It reads no sandbox code, runs no attack,
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
    "AREAS",
    "SECURITY_AUDIT_SCHEMA",
    "SECURITY_AUDIT_SLICE",
    "FindingStanding",
    "AuditVerdict",
    "FindingRecord",
    "AuditReport",
    "AreaEntry",
    "AreaRegistry",
    "default_registry",
    "derive_standing",
    "derive_verdict",
    "format_record",
    "format_records",
    "format_area",
    "format_areas",
    "prepare_report",
]

SECURITY_AUDIT_SLICE = "M-260"
SECURITY_AUDIT_SCHEMA = "mythic.security_audit/1"

PLAIN_EXPLANATION = (
    "The security audit, done honestly: the "
    "Part V doctrine grounds, the M-118 red-team "
    "pack and an independent read of the sandbox "
    "and jail code are audited area by area, and "
    "a finding counts FIXED only on the audit's "
    "own independent read resting on held local "
    "evidence. Every other finding ships ROADED "
    "with a named owner, in the open - an "
    "ownerless road is named, never silent, and "
    "no historical audit is inherited as proof."
)
USAGE = (
    "Record each area's finding against its "
    "area, fixed on independent-read evidence or "
    "roaded with its owner named; read the "
    "derived audit verdict before letting any "
    "report claim the audit closed; prepare a "
    "report only as a report, with every area "
    "answered - fixed on held evidence or roaded "
    "with an owner - and let a human share it. "
    "The whole doctrine, answered area by area, "
    "as data first."
)

STAGES = ("named", "examined", "judged", "dispositioned", "held")
TRANSITIONS = {
    "named": ("examined",),
    "examined": ("judged",),
    "judged": ("dispositioned",),
    "dispositioned": ("held",),
    "held": (),
}
HELD_EVIDENCE = ("local_run_ref", "ci_run_ref", "report_ref", "journal_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
EVIDENCE_KINDS = HELD_EVIDENCE + BARE_CLAIMS
REPORT_STATES = ("ready", "shared")
DISPOSITIONS = ("FIXED", "ROADED")
PROOF_KINDS = ("independent-read", "historical-only", "none")
DOCTRINE_REFS = ("M-095", "M-096", "M-097", "M-098", "M-099", "M-101",
                 "M-108", "M-109", "M-110", "M-111", "M-118", "M-119")
SUBJECTS = ("permission-profiles", "remembered-approvals", "os-sandbox",
            "network-gates", "path-jail", "hooks-lifecycle", "kill-switch",
            "audit-trail", "secret-hygiene", "destructive-commands",
            "red-team-pack", "policy-as-code")


def _check_date(value: str) -> None:
    ok = (isinstance(value, str) and len(value) == 10
          and value[4] == "-" and value[7] == "-")
    if ok:
        try:
            _date.fromisoformat(value)
        except ValueError:
            ok = False
    if not ok:
        raise ValidationError(f"unknown audit date: {value}")


@dataclass(frozen=True)
class AreaEntry:
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
            raise ValidationError(
                "area entries are listed data "
                "only, never a published verdict here; "
                f"refused standing: {self.standing}")


AREAS = (
    AreaEntry("S-01", "M-095", "permission-profiles", "listed",
              "the Part V permission profiles, audited area by area in the security audit"),
    AreaEntry("S-02", "M-096", "remembered-approvals", "listed",
              "the Part V remembered approvals with scope, audited area by area in the security audit"),
    AreaEntry("S-03", "M-097", "os-sandbox", "listed",
              "the Part V OS sandbox, read independently in the security audit"),
    AreaEntry("S-04", "M-098", "network-gates", "listed",
              "the Part V network gates, audited area by area in the security audit"),
    AreaEntry("S-05", "M-099", "path-jail", "listed",
              "the Part V path jail, read independently in the security audit"),
    AreaEntry("S-06", "M-101", "hooks-lifecycle", "listed",
              "the Part V hooks lifecycle, audited area by area in the security audit"),
    AreaEntry("S-07", "M-108", "kill-switch", "listed",
              "the Part V kill switch everywhere, audited area by area in the security audit"),
    AreaEntry("S-08", "M-109", "audit-trail", "listed",
              "the Part V audit trail, audited area by area in the security audit"),
    AreaEntry("S-09", "M-110", "secret-hygiene", "listed",
              "the Part V secret hygiene in action, audited area by area in the security audit"),
    AreaEntry("S-10", "M-111", "destructive-commands", "listed",
              "the Part V destructive-command doctrine, audited area by area in the security audit"),
    AreaEntry("S-11", "M-118", "red-team-pack", "listed",
              "the M-118 third-party red-team pack, audited area by area in the security audit"),
    AreaEntry("S-12", "M-119", "policy-as-code", "listed",
              "the Part V policy as code, audited area by area in the security audit"),
)


class AreaRegistry:
    def __init__(self, entries: Iterable[AreaEntry] = AREAS):
        self._entries: Dict[str, AreaEntry] = {}
        for entry in entries:
            entry.validate()
            if entry.id in self._entries:
                raise ValidationError(f"duplicate area: {entry.id}")
            self._entries[entry.id] = entry

    def get(self, area_id: str) -> AreaEntry:
        try:
            return self._entries[area_id]
        except KeyError:
            raise ValidationError(
                f"unknown area: {area_id}") from None

    def ids(self) -> Tuple[str, ...]:
        return tuple(self._entries)

    def entries(self) -> Tuple[AreaEntry, ...]:
        return tuple(self._entries.values())

    def combinations(self) -> Tuple[str, ...]:
        return tuple(self._entries)


def default_registry() -> AreaRegistry:
    return AreaRegistry()


@dataclass(frozen=True)
class FindingRecord:
    area: str
    run: str
    date: str
    disposition: str
    owner: str
    proof_kind: str
    stages: Tuple[str, ...]
    claims: Tuple[str, ...]

    def validate(self, registry: Optional[AreaRegistry] = None) -> None:
        (registry or default_registry()).get(self.area)
        if not self.run.strip():
            raise ValidationError("record names no audit run")
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
class FindingStanding:
    held: bool
    stage: str
    grade: str
    gaps: Tuple[str, ...]


def derive_standing(record: FindingRecord,
                    registry: Optional[AreaRegistry] = None) -> FindingStanding:
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
        gaps.append("record names no audit date")
    if record.disposition == "FIXED":
        if record.proof_kind != "independent-read":
            gaps.append(
                f"a FIXED finding rests on {record.proof_kind} "
                "evidence, not the audit's independent read: "
                "no inheritance")
        if "local_run_ref" not in record.claims:
            gaps.append(
                "the fix rests on no held "
                "local evidence")
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
    return FindingStanding(held=not gaps, stage=stage,
                           grade="held" if not gaps else "open",
                           gaps=tuple(gaps))


@dataclass(frozen=True)
class AuditVerdict:
    ready: bool
    gaps: Tuple[str, ...]
    fixed_areas: Tuple[str, ...]
    roaded_areas: Tuple[str, ...]
    missing_areas: Tuple[str, ...]


def derive_verdict(records: Iterable[FindingRecord],
                   registry: Optional[AreaRegistry] = None) -> AuditVerdict:
    reg = registry or default_registry()
    by_area: Dict[str, FindingRecord] = {}
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
        if standing.held and record.disposition == "FIXED":
            fixed.append(area_id)
        if standing.held and record.disposition == "ROADED":
            roaded.append(area_id)
        if not standing.held:
            gaps.append(
                f"area {area_id} stands open: "
                + "; ".join(standing.gaps))
    return AuditVerdict(ready=not gaps, gaps=tuple(gaps),
                        fixed_areas=tuple(fixed),
                        roaded_areas=tuple(roaded),
                        missing_areas=missing)


@dataclass(frozen=True)
class AuditReport:
    book: str
    entry: str
    report: str
    date: str
    fixed_count: int
    roaded_count: int
    total_areas: int
    claims: Tuple[str, ...]
    state: str = "ready"
    certified: bool = False
    inflated: bool = False

    def validate(self, registry: Optional[AreaRegistry] = None) -> None:
        reg = registry or default_registry()
        if not self.book.strip():
            raise ValidationError("report names no book")
        if not self.entry.strip():
            raise ValidationError("report names no entry")
        if not self.report.strip():
            raise ValidationError("audit report reports nothing")
        if not self.date:
            raise ValidationError(
                "report names no date: an audit "
                "report is reported with its date")
        _check_date(self.date)
        expected = len(reg.combinations())
        if self.total_areas != expected:
            raise ValidationError(
                f"report book holds {self.total_areas} "
                f"areas, not the road's {expected}")
        if self.fixed_count < 0 or self.roaded_count < 0:
            raise ValidationError(
                "unknown area count: "
                f"{self.fixed_count}/{self.roaded_count}")
        if self.fixed_count + self.roaded_count > self.total_areas:
            raise ValidationError(
                "answered areas exceed the book: "
                f"{self.fixed_count} + {self.roaded_count} "
                f"of {self.total_areas}")
        for kind in self.claims:
            if kind not in EVIDENCE_KINDS:
                raise ValidationError(f"unknown report evidence kind: {kind}")
        if not [c for c in self.claims if c in HELD_EVIDENCE]:
            raise ValidationError(
                "audit reports report held findings "
                "only; a report dressing a bare claim "
                "as a proof refuses here")
        if self.state not in REPORT_STATES:
            raise ValidationError(
                "audit reports stand ready or shared "
                "only, never sealed or locked; refused "
                f"state: {self.state}")
        if self.certified and \
                self.fixed_count + self.roaded_count < self.total_areas:
            raise ValidationError(
                "an unanswered area anywhere stops "
                "the closing claim: this report may not "
                "claim the audit closed short of "
                "every area answered")
        if self.inflated:
            raise ValidationError(
                "audit reports report the findings "
                "exactly as they were dispositioned; a "
                "report is never inflated here")


def prepare_report(book: str, entry: str, report: str,
                   date: str, fixed_count: int, roaded_count: int,
                   total_areas: int,
                   claims: Tuple[str, ...] = (),
                   state: str = "ready",
                   certified: bool = False) -> AuditReport:
    made = AuditReport(book=book, entry=entry,
                       report=report, date=date,
                       fixed_count=fixed_count,
                       roaded_count=roaded_count,
                       total_areas=total_areas,
                       claims=tuple(claims),
                       state=state, certified=certified)
    made.validate()
    return made


def format_area(entry: AreaEntry) -> str:
    return (f"{entry.id} {entry.doctrine}/{entry.subject}: "
            f"standing {entry.standing} "
            f"- {entry.reason}")


def format_areas(registry: Optional[AreaRegistry] = None) -> str:
    reg = registry or default_registry()
    return "\n".join(format_area(e) for e in reg.entries())


def format_record(record: FindingRecord,
                  registry: Optional[AreaRegistry] = None) -> str:
    reg = registry or default_registry()
    entry = reg.get(record.area)
    standing = derive_standing(record, reg)
    state = "held as answered" if standing.held else "open: " + "; ".join(standing.gaps)
    return (f"{record.area} {entry.doctrine}/{entry.subject}: "
            f"disposition {record.disposition} "
            f"({record.proof_kind}), date "
            f"{record.date or '(no date)'} - {state}")


def format_records(records: Iterable[FindingRecord],
                   registry: Optional[AreaRegistry] = None) -> str:
    return "\n".join(format_record(r, registry) for r in records)
