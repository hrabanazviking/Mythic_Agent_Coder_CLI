"""The regression-court book (roadmap slice M-257) - pure layer.

Part XI - Proof. The roadmap words: **every part's
gate results re-run as one battery; a red anywhere
stops the release, not just the part.**

What this layer holds, as data:

* A **part registry** held as data - one entry per
  part of the road (part_01..part_11, Parts I..XI):
  its id, its number and roman numeral, its plain
  label, the first and last slices of the part, the
  standing the entry arrives with, and why the entry
  stands, in plain words. Every entry arrives as
  listed data (standing 'listed'); a part the
  registry does not hold refuses BY NAME; a
  duplicated, half-written, or published entry
  refuses whole. A new part needs no code change.
* A **court record** holds, for one part and one
  re-run, that part's gate battery re-run as a
  supplied fact: the date it re-ran, its outcome
  (green or red), the gate counts it reached
  (passed of total), the stages it has walked, and
  the claims it rests on, by kind. Its standing is
  DERIVED at call time against the explicit stage
  walk held as data (STAGES, TRANSITIONS): named,
  scheduled, rerun, judged, held. A record stands
  held only when its gate rests on held evidence
  (a gate_log_ref among held evidence - gate_log_ref,
  rerun_log_ref, report_ref, journal_ref - never a
  bare claim: feeling, memory, assertion, summary),
  the walk is complete, its outcome is green, and
  its gate counts are complete (passed == total).
  A red outcome, a short count, or a missing date
  stands open, named in its gaps: a red anywhere
  stops the release, not just the part.
* A **court verdict** is DERIVED over a whole
  battery of records: the release stands ready
  only when every part of the road carries a held
  record - a missing part, an open record, or a
  red anywhere stops the release, and the verdict
  names what stopped it.
* A **verdict draft** is the only shape a battery
  may produce as a release verdict, prepared only
  through the prepare road. A draft stands at
  state "ready" by default, may be marked "shared"
  by a human, and reports the battery exactly as
  it re-ran. A draft asking to be sealed or locked
  instead of ready/shared, to be inflated instead
  of reported, to dress a bare claim up as a
  verdict, or to claim the release while any part
  stands short of green, refuses BY NAME.

Honesty rule, made code: a release counts only
when every part's gate has re-run green on held
evidence, as one battery. Anything short of that
stops the release by construction - this court
will not dress a part's green up as the road's,
and it never inflates one.

Honest boundary: this layer holds registry
entries, court records, derived standings,
derived battery verdicts and verdict drafts as
data. It re-runs no gate, executes no test and
writes nothing outside the session; the agent
layer owns holding a session's records and
speaking for them.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date as _date
from typing import Dict, Iterable, Optional, Tuple
from .validation import ValidationError

__all__ = [
    "BARE_CLAIMS",
    "EVIDENCE_KINDS",
    "HELD_EVIDENCE",
    "OUTCOMES",
    "PLAIN_EXPLANATION",
    "STAGES",
    "TRANSITIONS",
    "USAGE",
    "PARTS",
    "REGRESSION_COURT_SCHEMA",
    "REGRESSION_COURT_SLICE",
    "RecordStanding",
    "CourtVerdict",
    "CourtRecord",
    "VerdictDraft",
    "PartEntry",
    "PartRegistry",
    "default_registry",
    "derive_standing",
    "derive_verdict",
    "format_record",
    "format_records",
    "format_part",
    "format_parts",
    "prepare_verdict",
]

REGRESSION_COURT_SLICE = "M-257"
REGRESSION_COURT_SCHEMA = "mythic.regression_court/1"

PLAIN_EXPLANATION = (
    "The regression court, held honestly: every "
    "part's gate results are re-run as one battery "
    "before a release, and a red anywhere stops the "
    "release, not just the part. A part whose re-run "
    "rests on no held gate evidence, whose counts "
    "fall short, or whose outcome stands red holds "
    "the whole road open, and no verdict here claims "
    "a release the battery has not earned."
)
USAGE = (
    "Record each part's gate re-run against its "
    "part; read the derived battery verdict before "
    "letting any verdict draft claim the release; "
    "prepare a verdict only as a verdict, with every "
    "part green, and let a human share it. The whole "
    "road's gates, answered together, as data first."
)

STAGES = ("named", "scheduled", "rerun", "judged", "held")
TRANSITIONS = {
    "named": ("scheduled",),
    "scheduled": ("rerun",),
    "rerun": ("judged",),
    "judged": ("held",),
    "held": (),
}
HELD_EVIDENCE = ("gate_log_ref", "rerun_log_ref", "report_ref", "journal_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
EVIDENCE_KINDS = HELD_EVIDENCE + BARE_CLAIMS
OUTCOMES = ("green", "red")
VERDICT_STATES = ("ready", "shared")


def _check_date(value: str) -> None:
    ok = (isinstance(value, str) and len(value) == 10
          and value[4] == "-" and value[7] == "-")
    if ok:
        try:
            _date.fromisoformat(value)
        except ValueError:
            ok = False
    if not ok:
        raise ValidationError(f"unknown re-run date: {value}")


@dataclass(frozen=True)
class PartEntry:
    id: str
    number: int
    roman: str
    label: str
    first_slice: str
    last_slice: str
    standing: str
    reason: str

    def validate(self) -> None:
        for name in ("id", "roman", "label", "first_slice",
                     "last_slice", "standing", "reason"):
            if not str(getattr(self, name)).strip():
                raise ValidationError(f"part entry missing {name}")
        if not isinstance(self.number, int) or isinstance(self.number, bool) \
                or not 1 <= self.number <= 11:
            raise ValidationError(
                f"unknown part number: {self.number}")
        if self.standing != "listed":
            raise ValidationError(
                "part entries are listed data "
                "only, never a published verdict here; "
                f"refused standing: {self.standing}")


PARTS = (
    PartEntry("part_01", 1, "I", "The Census & The Charter", "M-001", "M-018", "listed",
              "the first part's gate, re-run in the court battery like every other part"),
    PartEntry("part_02", 2, "II", "The Provider Ocean", "M-019", "M-042", "listed",
              "the provider part's gate, re-run in the court battery like every other part"),
    PartEntry("part_03", 3, "III", "Code Intelligence", "M-043", "M-070", "listed",
              "the code-intelligence part's gate, re-run in the court battery like every other part"),
    PartEntry("part_04", 4, "IV", "The Editor's Hand", "M-071", "M-094", "listed",
              "the editor part's gate, re-run in the court battery like every other part"),
    PartEntry("part_05", 5, "V", "Autonomy & Safety", "M-095", "M-120", "listed",
              "the safety part's gate, re-run in the court battery like every other part"),
    PartEntry("part_06", 6, "VI", "The Crew", "M-121", "M-146", "listed",
              "the crew part's gate, re-run in the court battery like every other part"),
    PartEntry("part_07", 7, "VII", "Memory & Context", "M-147", "M-170", "listed",
              "the memory part's gate, re-run in the court battery like every other part"),
    PartEntry("part_08", 8, "VIII", "The Beautiful Face", "M-171", "M-200", "listed",
              "the face part's gate, re-run in the court battery like every other part"),
    PartEntry("part_09", 9, "IX", "The Mythic Method Engine", "M-201", "M-232", "listed",
              "the method-engine part's gate, re-run in the court battery like every other part"),
    PartEntry("part_10", 10, "X", "Bridges", "M-233", "M-254", "listed",
              "the bridges part's gate, re-run in the court battery like every other part"),
    PartEntry("part_11", 11, "XI", "The Proof Spine", "M-255", "M-272", "listed",
              "the proof part's own gate, re-run in the court battery like every other part"),
)


class PartRegistry:
    def __init__(self, entries: Iterable[PartEntry] = PARTS):
        self._entries: Dict[str, PartEntry] = {}
        for entry in entries:
            entry.validate()
            if entry.id in self._entries:
                raise ValidationError(f"duplicate part: {entry.id}")
            self._entries[entry.id] = entry

    def get(self, part_id: str) -> PartEntry:
        try:
            return self._entries[part_id]
        except KeyError:
            raise ValidationError(
                f"unknown part: {part_id}") from None

    def ids(self) -> Tuple[str, ...]:
        return tuple(self._entries)

    def entries(self) -> Tuple[PartEntry, ...]:
        return tuple(self._entries.values())


def default_registry() -> PartRegistry:
    return PartRegistry()


@dataclass(frozen=True)
class CourtRecord:
    part: str
    run: str
    date: str
    outcome: Optional[str]
    passed: Optional[int]
    total: Optional[int]
    stages: Tuple[str, ...]
    claims: Tuple[str, ...]

    def validate(self, registry: Optional[PartRegistry] = None) -> None:
        (registry or default_registry()).get(self.part)
        if not self.run.strip():
            raise ValidationError("record names no re-run")
        if self.date:
            _check_date(self.date)
        if self.outcome is not None and self.outcome not in OUTCOMES:
            raise ValidationError(
                f"unknown re-run outcome: {self.outcome}")
        for name in ("passed", "total"):
            value = getattr(self, name)
            if value is not None:
                if not isinstance(value, int) or isinstance(value, bool):
                    raise ValidationError(
                        f"unknown gate {name} count: {value!r}")
                if value < 0:
                    raise ValidationError(
                        f"gate {name} count is negative: {value}")
        if self.passed is not None and self.total is not None \
                and self.passed > self.total:
            raise ValidationError(
                f"gate passed count {self.passed} stands "
                f"above its total {self.total}: a count "
                "is never inflated here")
        for kind in self.claims:
            if kind not in EVIDENCE_KINDS:
                raise ValidationError(f"unknown record evidence kind: {kind}")


@dataclass(frozen=True)
class RecordStanding:
    held: bool
    stage: str
    grade: str
    gaps: Tuple[str, ...]


def derive_standing(record: CourtRecord,
                    registry: Optional[PartRegistry] = None) -> RecordStanding:
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
    if "gate_log_ref" not in record.claims:
        gaps.append(
            "the re-run's gate rests on no held "
            "gate evidence")
    if not held_kinds:
        gaps.append("record rests on no held evidence")
    if bare and not held_kinds:
        gaps.append("record rests on bare claims only: " + ", ".join(bare))
    if not record.date:
        gaps.append("record names no re-run date")
    if record.outcome is None:
        gaps.append("record reports no outcome")
    if record.outcome == "red":
        gaps.append(
            "gate re-run stands red: a red anywhere "
            "stops the release, not just the part")
    if record.passed is None or record.total is None:
        gaps.append("record reports no gate counts")
    elif record.passed < record.total:
        gaps.append(
            f"gate counts fall short: {record.passed} "
            f"of {record.total} passed")
    return RecordStanding(held=not gaps, stage=stage,
                          grade="held" if not gaps else "open",
                          gaps=tuple(gaps))


@dataclass(frozen=True)
class CourtVerdict:
    ready: bool
    gaps: Tuple[str, ...]
    red_parts: Tuple[str, ...]
    missing_parts: Tuple[str, ...]


def derive_verdict(records: Iterable[CourtRecord],
                   registry: Optional[PartRegistry] = None) -> CourtVerdict:
    reg = registry or default_registry()
    by_part: Dict[str, CourtRecord] = {}
    gaps = []
    for record in records:
        record.validate(reg)
        if record.part in by_part:
            gaps.append(f"part {record.part} carries two re-runs")
        else:
            by_part[record.part] = record
    missing = tuple(pid for pid in reg.ids() if pid not in by_part)
    for pid in missing:
        gaps.append(f"part {pid} has no gate re-run in the battery")
    red = []
    for pid, record in by_part.items():
        standing = derive_standing(record, reg)
        if record.outcome == "red":
            red.append(pid)
        if not standing.held:
            gaps.append(
                f"part {pid} stands open: " + "; ".join(standing.gaps))
    return CourtVerdict(ready=not gaps, gaps=tuple(gaps),
                        red_parts=tuple(red), missing_parts=missing)


@dataclass(frozen=True)
class VerdictDraft:
    battery: str
    entry: str
    verdict: str
    date: str
    green_parts: int
    total_parts: int
    claims: Tuple[str, ...]
    state: str = "ready"
    released: bool = False
    inflated: bool = False

    def validate(self, registry: Optional[PartRegistry] = None) -> None:
        reg = registry or default_registry()
        if not self.battery.strip():
            raise ValidationError("verdict names no battery")
        if not self.entry.strip():
            raise ValidationError("verdict names no entry")
        if not self.verdict.strip():
            raise ValidationError("court verdict reports nothing")
        if not self.date:
            raise ValidationError(
                "verdict names no date: a court "
                "verdict is reported with its date")
        _check_date(self.date)
        if self.total_parts != len(reg.ids()):
            raise ValidationError(
                f"verdict battery holds {self.total_parts} "
                f"parts, not the road's {len(reg.ids())}")
        if self.green_parts < 0 or self.green_parts > self.total_parts:
            raise ValidationError(
                f"unknown green part count: {self.green_parts}")
        for kind in self.claims:
            if kind not in EVIDENCE_KINDS:
                raise ValidationError(f"unknown verdict evidence kind: {kind}")
        if not [c for c in self.claims if c in HELD_EVIDENCE]:
            raise ValidationError(
                "court verdicts report held re-runs "
                "only; a verdict dressing a bare claim "
                "as a result refuses here")
        if self.state not in VERDICT_STATES:
            raise ValidationError(
                "court verdicts stand ready or shared "
                "only, never sealed or locked; refused "
                f"state: {self.state}")
        if self.released and self.green_parts < self.total_parts:
            raise ValidationError(
                "a red or missing gate anywhere stops "
                "the release: this verdict may not "
                "claim the release short of every "
                "part green")
        if self.inflated:
            raise ValidationError(
                "court verdicts report the battery "
                "exactly as it re-ran; a verdict is "
                "never inflated here")


def prepare_verdict(battery: str, entry: str, verdict: str,
                    date: str, green_parts: int, total_parts: int,
                    claims: Tuple[str, ...] = (),
                    state: str = "ready",
                    released: bool = False) -> VerdictDraft:
    made = VerdictDraft(battery=battery, entry=entry,
                        verdict=verdict, date=date,
                        green_parts=green_parts,
                        total_parts=total_parts,
                        claims=tuple(claims),
                        state=state, released=released)
    made.validate()
    return made


def format_part(entry: PartEntry) -> str:
    return (f"Part {entry.roman} ({entry.id}): "
            f"{entry.label}, slices {entry.first_slice}"
            f"-{entry.last_slice}, standing "
            f"{entry.standing} - {entry.reason}")


def format_parts(registry: Optional[PartRegistry] = None) -> str:
    reg = registry or default_registry()
    return "\n".join(format_part(e) for e in reg.entries())


def format_record(record: CourtRecord,
                  registry: Optional[PartRegistry] = None) -> str:
    reg = registry or default_registry()
    entry = reg.get(record.part)
    standing = derive_standing(record, reg)
    state = "held as re-run" if standing.held else "open: " + "; ".join(standing.gaps)
    return (f"{record.part}/{record.run}: Part "
            f"{entry.roman} {entry.label} - outcome "
            f"{record.outcome or '(no outcome)'}, gates "
            f"{record.passed} of {record.total} passed, "
            f"date {record.date or '(no date)'} - {state}")


def format_records(records: Iterable[CourtRecord],
                   registry: Optional[PartRegistry] = None) -> str:
    return "\n".join(format_record(r, registry) for r in records)
