"""The performance-budgets book (roadmap slice M-258) - pure layer.

Part XI - Proof. The roadmap words: **cold start,
repo-map build on a 100k-file repo, TUI frame
health, memory ceiling - measured on the VM,
Mimir-class ARM, and the laptop; budgets from
measurement.**

What this layer holds, as data:

* A **budget registry** held as data - one entry
  per measure of the road (cold_start,
  repo_map_100k, tui_frame, memory_ceiling): its
  id, its plain label, the unit its measurement
  and budget are counted in, the standing the
  entry arrives with, and why the entry stands,
  in plain words. Every entry arrives as listed
  data (standing 'listed'); a measure the registry
  does not hold refuses BY NAME; a duplicated,
  half-written, or published entry refuses whole.
  A new measure needs no code change.
* A **machine set** held as data - the three
  machines the roadmap names: the VM, Mimir-class
  ARM, and the laptop. A record naming a machine
  outside that set refuses by name.
* A **budget record** holds, for one measure on
  one machine, that measure's measurement as a
  supplied fact: the date it was measured, the
  measured value and the budget value it stands
  against (both counted in the measure's unit),
  the stages it has walked, and the claims it
  rests on, by kind. Its standing is DERIVED at
  call time against the explicit stage walk held
  as data (STAGES, TRANSITIONS): named, measured,
  compared, judged, held. A record stands held
  only when its measurement rests on held
  evidence (a measurement_log_ref among held
  evidence - measurement_log_ref, benchmark_ref,
  report_ref, journal_ref - never a bare claim:
  feeling, memory, assertion, summary), the walk
  is complete, and its measurement stands within
  its budget. A measurement over its budget, a
  missing date, or a missing value stands open,
  named in its gaps: over budget anywhere stops
  the claim, not just the measure.
* A **budget verdict** is DERIVED over a whole
  book of records: the book stands ready only
  when every measure on every machine carries a
  held record - a missing combination, an open
  record, or an over-budget measurement anywhere
  stops the book, and the verdict names what
  stopped it.
* A **budget report** is the only shape a book
  may produce as a report, prepared only through
  the prepare road. A report stands at state
  "ready" by default, may be marked "shared" by
  a human, and reports the measurements exactly
  as they were measured. A report asking to be
  sealed or locked instead of ready/shared, to be
  inflated instead of reported, to dress a bare
  claim up as a measurement, or to claim the book
  certified while any combination stands short
  of within-budget, refuses BY NAME.

Honesty rule, made code: a budget counts only
when it comes from a measurement held on
evidence, on the machine it names, within the
budget it names. Budgets here are from
measurement - never invented, never widened to
fit a slow run after the fact.

Honest boundary: this layer holds registry
entries, budget records, derived standings,
derived book verdicts and budget reports as
data. It measures nothing, times no start,
builds no repo map and writes nothing outside
the session; the agent layer owns holding a
session's records and speaking for them.
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
    "PLAIN_EXPLANATION",
    "STAGES",
    "TRANSITIONS",
    "USAGE",
    "MEASURES",
    "MACHINES",
    "PERFORMANCE_BUDGETS_SCHEMA",
    "PERFORMANCE_BUDGETS_SLICE",
    "RecordStanding",
    "BudgetVerdict",
    "BudgetRecord",
    "BudgetReport",
    "BudgetEntry",
    "BudgetRegistry",
    "default_registry",
    "derive_standing",
    "derive_verdict",
    "format_record",
    "format_records",
    "format_measure",
    "format_measures",
    "prepare_report",
]

PERFORMANCE_BUDGETS_SLICE = "M-258"
PERFORMANCE_BUDGETS_SCHEMA = "mythic.performance_budgets/1"

PLAIN_EXPLANATION = (
    "Performance budgets, held honestly: cold "
    "start, a repo-map build on a 100k-file repo, "
    "TUI frame health, and the memory ceiling are "
    "measured on the VM, on Mimir-class ARM, and "
    "on the laptop, and the budgets come from "
    "those measurements. A measure whose run rests "
    "on no held measurement evidence, or whose "
    "measurement stands over its budget on any "
    "machine, holds the whole book open."
)
USAGE = (
    "Record each measure's measurement on each "
    "machine against its budget; read the derived "
    "book verdict before letting any report claim "
    "the book certified; prepare a report only as "
    "a report, with every combination measured "
    "within budget, and let a human share it. "
    "Budgets from measurement, as data first."
)

STAGES = ("named", "measured", "compared", "judged", "held")
TRANSITIONS = {
    "named": ("measured",),
    "measured": ("compared",),
    "compared": ("judged",),
    "judged": ("held",),
    "held": (),
}
HELD_EVIDENCE = ("measurement_log_ref", "benchmark_ref", "report_ref", "journal_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
EVIDENCE_KINDS = HELD_EVIDENCE + BARE_CLAIMS
REPORT_STATES = ("ready", "shared")
UNITS = ("milliseconds", "megabytes")


def _check_date(value: str) -> None:
    ok = (isinstance(value, str) and len(value) == 10
          and value[4] == "-" and value[7] == "-")
    if ok:
        try:
            _date.fromisoformat(value)
        except ValueError:
            ok = False
    if not ok:
        raise ValidationError(f"unknown measurement date: {value}")


@dataclass(frozen=True)
class MachineEntry:
    id: str
    label: str
    reason: str


MACHINES = (
    MachineEntry("vm", "The VM",
                 "the cloud VM, measured like every other machine in the book"),
    MachineEntry("mimir_arm", "Mimir-class ARM",
                 "Mimir-class ARM, measured like every other machine in the book"),
    MachineEntry("laptop", "The laptop",
                 "the laptop, measured like every other machine in the book"),
)
MACHINE_IDS = tuple(m.id for m in MACHINES)


@dataclass(frozen=True)
class BudgetEntry:
    id: str
    label: str
    unit: str
    standing: str
    reason: str

    def validate(self) -> None:
        for name in ("id", "label", "unit", "standing", "reason"):
            if not str(getattr(self, name)).strip():
                raise ValidationError(f"budget entry missing {name}")
        if self.unit not in UNITS:
            raise ValidationError(f"unknown budget unit: {self.unit}")
        if self.standing != "listed":
            raise ValidationError(
                "budget entries are listed data "
                "only, never a published budget here; "
                f"refused standing: {self.standing}")


MEASURES = (
    BudgetEntry("cold_start", "Cold start", "milliseconds", "listed",
                "how long the tool takes to stand up, measured cold on each machine"),
    BudgetEntry("repo_map_100k", "Repo-map build on a 100k-file repo", "milliseconds", "listed",
                "how long a repo map takes to build over a 100k-file repo, measured on each machine"),
    BudgetEntry("tui_frame", "TUI frame health", "milliseconds", "listed",
                "how long a TUI frame takes to draw, measured on each machine"),
    BudgetEntry("memory_ceiling", "Memory ceiling", "megabytes", "listed",
                "how much memory a run may stand under, measured on each machine"),
)


class BudgetRegistry:
    def __init__(self, entries: Iterable[BudgetEntry] = MEASURES):
        self._entries: Dict[str, BudgetEntry] = {}
        for entry in entries:
            entry.validate()
            if entry.id in self._entries:
                raise ValidationError(f"duplicate measure: {entry.id}")
            self._entries[entry.id] = entry

    def get(self, measure_id: str) -> BudgetEntry:
        try:
            return self._entries[measure_id]
        except KeyError:
            raise ValidationError(
                f"unknown measure: {measure_id}") from None

    def ids(self) -> Tuple[str, ...]:
        return tuple(self._entries)

    def entries(self) -> Tuple[BudgetEntry, ...]:
        return tuple(self._entries.values())

    def machine_ids(self) -> Tuple[str, ...]:
        return MACHINE_IDS

    def combinations(self) -> Tuple[Tuple[str, str], ...]:
        return tuple((mid, mach) for mid in self._entries
                     for mach in MACHINE_IDS)


def default_registry() -> BudgetRegistry:
    return BudgetRegistry()


@dataclass(frozen=True)
class BudgetRecord:
    measure: str
    machine: str
    run: str
    date: str
    measured: Optional[int]
    limit: Optional[int]
    stages: Tuple[str, ...]
    claims: Tuple[str, ...]

    def validate(self, registry: Optional[BudgetRegistry] = None) -> None:
        (registry or default_registry()).get(self.measure)
        if self.machine not in MACHINE_IDS:
            raise ValidationError(f"unknown machine: {self.machine}")
        if not self.run.strip():
            raise ValidationError("record names no measurement run")
        if self.date:
            _check_date(self.date)
        for name in ("measured", "limit"):
            value = getattr(self, name)
            if value is not None:
                if not isinstance(value, int) or isinstance(value, bool):
                    raise ValidationError(
                        f"unknown {name} value: {value!r}")
                if value < 0:
                    raise ValidationError(
                        f"{name} value is negative: {value}")
        for kind in self.claims:
            if kind not in EVIDENCE_KINDS:
                raise ValidationError(f"unknown record evidence kind: {kind}")


@dataclass(frozen=True)
class RecordStanding:
    held: bool
    stage: str
    grade: str
    gaps: Tuple[str, ...]


def derive_standing(record: BudgetRecord,
                    registry: Optional[BudgetRegistry] = None) -> RecordStanding:
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
    if "measurement_log_ref" not in record.claims:
        gaps.append(
            "the measurement rests on no held "
            "measurement evidence")
    if not held_kinds:
        gaps.append("record rests on no held evidence")
    if bare and not held_kinds:
        gaps.append("record rests on bare claims only: " + ", ".join(bare))
    if not record.date:
        gaps.append("record names no measurement date")
    if record.measured is None:
        gaps.append("record reports no measurement")
    if record.limit is None:
        gaps.append("record names no budget")
    if record.measured is not None and record.limit is not None \
            and record.measured > record.limit:
        gaps.append(
            f"measurement {record.measured} stands "
            f"over its budget {record.limit}: over "
            "budget anywhere stops the claim, not "
            "just the measure")
    return RecordStanding(held=not gaps, stage=stage,
                          grade="held" if not gaps else "open",
                          gaps=tuple(gaps))


@dataclass(frozen=True)
class BudgetVerdict:
    ready: bool
    gaps: Tuple[str, ...]
    over_combinations: Tuple[str, ...]
    missing_combinations: Tuple[str, ...]


def derive_verdict(records: Iterable[BudgetRecord],
                   registry: Optional[BudgetRegistry] = None) -> BudgetVerdict:
    reg = registry or default_registry()
    by_combo: Dict[Tuple[str, str], BudgetRecord] = {}
    gaps = []
    for record in records:
        record.validate(reg)
        combo = (record.measure, record.machine)
        if combo in by_combo:
            gaps.append(
                f"measure {record.measure} on {record.machine} "
                "carries two measurements")
        else:
            by_combo[combo] = record
    missing = tuple(f"{mid}/{mach}" for mid, mach in reg.combinations()
                    if (mid, mach) not in by_combo)
    for combo_name in missing:
        gaps.append(f"combination {combo_name} has no measurement in the book")
    over = []
    for (mid, mach), record in by_combo.items():
        standing = derive_standing(record, reg)
        if record.measured is not None and record.limit is not None \
                and record.measured > record.limit:
            over.append(f"{mid}/{mach}")
        if not standing.held:
            gaps.append(
                f"combination {mid}/{mach} stands open: "
                + "; ".join(standing.gaps))
    return BudgetVerdict(ready=not gaps, gaps=tuple(gaps),
                         over_combinations=tuple(over),
                         missing_combinations=missing)


@dataclass(frozen=True)
class BudgetReport:
    book: str
    entry: str
    report: str
    date: str
    within_count: int
    total_combinations: int
    claims: Tuple[str, ...]
    state: str = "ready"
    certified: bool = False
    inflated: bool = False

    def validate(self, registry: Optional[BudgetRegistry] = None) -> None:
        reg = registry or default_registry()
        if not self.book.strip():
            raise ValidationError("report names no book")
        if not self.entry.strip():
            raise ValidationError("report names no entry")
        if not self.report.strip():
            raise ValidationError("budget report reports nothing")
        if not self.date:
            raise ValidationError(
                "report names no date: a budget "
                "report is reported with its date")
        _check_date(self.date)
        expected = len(reg.combinations())
        if self.total_combinations != expected:
            raise ValidationError(
                f"report book holds {self.total_combinations} "
                f"combinations, not the road's {expected}")
        if self.within_count < 0 or self.within_count > self.total_combinations:
            raise ValidationError(
                f"unknown within-budget count: {self.within_count}")
        for kind in self.claims:
            if kind not in EVIDENCE_KINDS:
                raise ValidationError(f"unknown report evidence kind: {kind}")
        if not [c for c in self.claims if c in HELD_EVIDENCE]:
            raise ValidationError(
                "budget reports report held measurements "
                "only; a report dressing a bare claim "
                "as a measurement refuses here")
        if self.state not in REPORT_STATES:
            raise ValidationError(
                "budget reports stand ready or shared "
                "only, never sealed or locked; refused "
                f"state: {self.state}")
        if self.certified and self.within_count < self.total_combinations:
            raise ValidationError(
                "an over-budget or unmeasured "
                "combination anywhere stops the "
                "certification: this report may not "
                "claim the book certified short of "
                "every combination within budget")
        if self.inflated:
            raise ValidationError(
                "budget reports report the measurements "
                "exactly as they were measured; a "
                "report is never inflated here")


def prepare_report(book: str, entry: str, report: str,
                   date: str, within_count: int, total_combinations: int,
                   claims: Tuple[str, ...] = (),
                   state: str = "ready",
                   certified: bool = False) -> BudgetReport:
    made = BudgetReport(book=book, entry=entry,
                        report=report, date=date,
                        within_count=within_count,
                        total_combinations=total_combinations,
                        claims=tuple(claims),
                        state=state, certified=certified)
    made.validate()
    return made


def format_measure(entry: BudgetEntry) -> str:
    return (f"{entry.label} ({entry.id}): counted in "
            f"{entry.unit}, standing {entry.standing} "
            f"- {entry.reason}")


def format_measures(registry: Optional[BudgetRegistry] = None) -> str:
    reg = registry or default_registry()
    return "\n".join(format_measure(e) for e in reg.entries())


def format_record(record: BudgetRecord,
                  registry: Optional[BudgetRegistry] = None) -> str:
    reg = registry or default_registry()
    entry = reg.get(record.measure)
    standing = derive_standing(record, reg)
    state = "held as measured" if standing.held else "open: " + "; ".join(standing.gaps)
    return (f"{record.measure}/{record.machine}: "
            f"{entry.label} - measured "
            f"{record.measured} of budget {record.limit} "
            f"{entry.unit}, date "
            f"{record.date or '(no date)'} - {state}")


def format_records(records: Iterable[BudgetRecord],
                   registry: Optional[BudgetRegistry] = None) -> str:
    return "\n".join(format_record(r, registry) for r in records)
