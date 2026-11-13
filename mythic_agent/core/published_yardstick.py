"""The published-yardstick book (roadmap slice M-256) - pure layer.

Part XI - Proof. The roadmap words: **SWE-bench-style
public sets run where licences allow, results reported
with model, cost, and date - comparable to the field's
claims, never inflated.**

What this layer holds, as data:

* A **yardstick registry** held as data - one entry
  per public set (swe_bench, swe_bench_lite,
  swe_bench_verified, swe_bench_multimodal): its id,
  its plain label, the word that set gives a single
  run, the licence the set is published under, that
  licence's standing as data (held, or listed-only
  where the licence is not held), the set's maximum
  score, the standing the entry arrives with, and why
  the entry stands, in plain words. Every entry
  arrives as listed data (standing 'listed'); a set
  the registry does not hold refuses BY NAME; a
  duplicated, half-written, or published entry
  refuses whole. A set whose licence is not held is
  listed-only here: it is named for sight, and no run
  on it can ever stand held. A new public set needs
  no code change.
* A **run record** holds, for one yardstick and one
  run, one published-yardstick run as a supplied
  fact: the model that ran, what the run cost, the
  date it ran, the score it reached, the stages it
  has walked, and the claims it rests on, by kind.
  Its standing is DERIVED at call time against the
  explicit stage walk held as data (STAGES,
  TRANSITIONS): named, licensed, run, reported,
  held. A run stands held only when its licence
  rests on held evidence (a licence_ref among held
  evidence - licence_ref, run_log_ref, report_ref,
  journal_ref - never a bare claim: feeling, memory,
  assertion, summary), the run is complete on the
  walk, and its report carries model AND cost AND
  date - missing any of those three stands open,
  named in its gaps. A score above the set's
  maximum, or a negative cost, refuses whole by
  name: a result is never inflated here.
* A **run report** is the only shape a run record
  may produce, prepared only through the prepare
  road. A report stands at state "ready" by default,
  may be marked "shared" by a human, and reports a
  run exactly as it ran - with its model, its cost
  and its date, at its true score. A report asking
  to be sealed or locked instead of ready/shared, to
  be inflated instead of reported, to carry a score
  above the set's maximum or a negative cost, or
  dressing a bare claim up as a result, refuses
  BY NAME.

Honesty rule, made code: a published-yardstick
result counts only when the set's licence is held,
the licence rests on held evidence, and the report
carries model, cost and date together. Anything
short of that stands open by construction - this
book will not dress a claim up as a comparable
result, and it never inflates one.

Honest boundary: this layer holds registry entries,
run records, derived standings and run reports as
data. It runs no benchmark, downloads no set,
executes no grading test and writes nothing outside
the session; the agent layer owns holding a
session's records and speaking for them.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date as _date
from typing import Dict, Iterable, Optional, Tuple
from .validation import ValidationError

__all__ = [
    "REPORT_STATES",
    "BARE_CLAIMS",
    "EVIDENCE_KINDS",
    "HELD_EVIDENCE",
    "LICENCE_STANDINGS",
    "PLAIN_EXPLANATION",
    "STAGES",
    "TRANSITIONS",
    "STANDINGS",
    "USAGE",
    "YARDSTICKS",
    "PUBLISHED_YARDSTICK_SCHEMA",
    "PUBLISHED_YARDSTICK_SLICE",
    "RunStanding",
    "RunRecord",
    "RunDraft",
    "YardstickEntry",
    "YardstickRegistry",
    "default_registry",
    "derive_standing",
    "format_record",
    "format_records",
    "format_yardstick",
    "format_yardsticks",
    "prepare_report",
]

PUBLISHED_YARDSTICK_SLICE = "M-256"
PUBLISHED_YARDSTICK_SCHEMA = "mythic.published_yardstick/1"

PLAIN_EXPLANATION = (
    "Published yardsticks, run honestly: SWE-bench-style "
    "public sets are run only where their licences allow, "
    "and every result is reported with its model, its "
    "cost and its date, so the numbers compare with the "
    "field's own claims. A set whose licence is not held "
    "is listed-only and can hold no run, a report missing "
    "its model, cost or date stands open, and no result "
    "is ever inflated here."
)
USAGE = (
    "Record each run against its yardstick; read its "
    "derived standing before letting it prepare a run "
    "report; prepare any report only as a report, with "
    "model, cost and date, and let a human share it. "
    "The field's yardsticks, answered honestly, as "
    "data first."
)

STAGES = ("named", "licensed", "run", "reported", "held")
TRANSITIONS = {
    "named": ("licensed",),
    "licensed": ("run",),
    "run": ("reported",),
    "reported": ("held",),
    "held": (),
}
LICENCE_STANDINGS = ("held", "listed_only")
HELD_EVIDENCE = ("licence_ref", "run_log_ref", "report_ref", "journal_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
EVIDENCE_KINDS = HELD_EVIDENCE + BARE_CLAIMS
REPORT_STATES = ("ready", "shared")
STANDINGS = ("listed",)


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _check_date(value: str) -> None:
    ok = (isinstance(value, str) and len(value) == 10
          and value[4] == "-" and value[7] == "-")
    if ok:
        try:
            _date.fromisoformat(value)
        except ValueError:
            ok = False
    if not ok:
        raise ValidationError(f"unknown run date: {value}")


@dataclass(frozen=True)
class YardstickEntry:
    id: str
    label: str
    item_word: str
    licence: str
    licence_standing: str
    max_score: float
    standing: str
    reason: str

    def validate(self) -> None:
        for name in ("id", "label", "item_word", "licence",
                     "licence_standing", "standing", "reason"):
            if not str(getattr(self, name)).strip():
                raise ValidationError(f"yardstick entry missing {name}")
        if self.licence_standing not in LICENCE_STANDINGS:
            raise ValidationError(
                f"unknown licence standing: {self.licence_standing}")
        if not _is_number(self.max_score) or self.max_score <= 0:
            raise ValidationError(
                "yardstick entry maximum score is not a "
                "positive number")
        if self.standing != "listed":
            raise ValidationError(
                "yardstick sets are listed data "
                "only, never a published result here; "
                f"refused standing: {self.standing}")


YARDSTICKS = (
    YardstickEntry("swe_bench", "SWE-bench", "run", "MIT", "held", 100, "listed",
                   "the original SWE-bench public set of real GitHub issues, run where its MIT licence allows and reported with model, cost and date"),
    YardstickEntry("swe_bench_lite", "SWE-bench Lite", "run", "MIT", "held", 100, "listed",
                   "the lighter SWE-bench subset for quicker comparable runs, under the same MIT licence"),
    YardstickEntry("swe_bench_verified", "SWE-bench Verified", "run", "MIT", "held", 100, "listed",
                   "the human-verified SWE-bench subset, the field's most quoted comparison set, run under its licence"),
    YardstickEntry("swe_bench_multimodal", "SWE-bench Multimodal", "run", "not held", "listed_only", 100, "listed",
                   "the multimodal SWE-bench set, whose licence this house does not hold: listed for sight only, and no run on it can stand held here"),
)


class YardstickRegistry:
    def __init__(self, entries: Iterable[YardstickEntry] = YARDSTICKS):
        self._entries: Dict[str, YardstickEntry] = {}
        for entry in entries:
            entry.validate()
            if entry.id in self._entries:
                raise ValidationError(f"duplicate yardstick: {entry.id}")
            self._entries[entry.id] = entry

    def get(self, yardstick_id: str) -> YardstickEntry:
        try:
            return self._entries[yardstick_id]
        except KeyError:
            raise ValidationError(
                f"unknown yardstick: {yardstick_id}") from None

    def ids(self) -> Tuple[str, ...]:
        return tuple(self._entries)

    def entries(self) -> Tuple[YardstickEntry, ...]:
        return tuple(self._entries.values())


def default_registry() -> YardstickRegistry:
    return YardstickRegistry()


@dataclass(frozen=True)
class RunRecord:
    yardstick: str
    run: str
    model: str
    cost: Optional[float]
    date: str
    score: Optional[float]
    stages: Tuple[str, ...]
    claims: Tuple[str, ...]

    def validate(self, registry: Optional[YardstickRegistry] = None) -> None:
        entry = (registry or default_registry()).get(self.yardstick)
        if not self.run.strip():
            raise ValidationError("record names no run")
        if self.model is not None and not isinstance(self.model, str):
            raise ValidationError(f"unknown run model: {self.model!r}")
        if self.cost is not None:
            if not _is_number(self.cost):
                raise ValidationError(f"unknown run cost: {self.cost!r}")
            if self.cost < 0:
                raise ValidationError(
                    f"run cost is negative: {self.cost}")
        if self.date:
            _check_date(self.date)
        if self.score is not None:
            if not _is_number(self.score):
                raise ValidationError(f"unknown run score: {self.score!r}")
            if self.score < 0:
                raise ValidationError(
                    f"run score is negative: {self.score}")
            if self.score > entry.max_score:
                raise ValidationError(
                    f"score {self.score} stands above the "
                    f"maximum {entry.max_score} for "
                    f"{entry.id}: a result is never "
                    "inflated here")
        for kind in self.claims:
            if kind not in EVIDENCE_KINDS:
                raise ValidationError(f"unknown run evidence kind: {kind}")


@dataclass(frozen=True)
class RunStanding:
    held: bool
    stage: str
    grade: str
    gaps: Tuple[str, ...]


def derive_standing(record: RunRecord,
                    registry: Optional[YardstickRegistry] = None) -> RunStanding:
    record.validate(registry)
    entry = (registry or default_registry()).get(record.yardstick)
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
    if entry.licence_standing != "held":
        gaps.append(
            f"yardstick {entry.id} is listed-only: its "
            "licence is not held, so no run on it can "
            "stand held")
    held_kinds = [c for c in record.claims if c in HELD_EVIDENCE]
    bare = [c for c in record.claims if c in BARE_CLAIMS]
    if "licence_ref" not in record.claims:
        gaps.append(
            "the run's licence rests on no held "
            "licence evidence")
    if not held_kinds:
        gaps.append("record rests on no held evidence")
    if bare and not held_kinds:
        gaps.append("record rests on bare claims only: " + ", ".join(bare))
    if not str(record.model or "").strip():
        gaps.append("report names no model")
    if record.cost is None:
        gaps.append("report names no cost")
    if not record.date:
        gaps.append("report names no run date")
    if record.score is None:
        gaps.append("run reports no score")
    return RunStanding(held=not gaps, stage=stage,
                       grade="held" if not gaps else "open",
                       gaps=tuple(gaps))


@dataclass(frozen=True)
class RunDraft:
    yardstick: str
    entry: str
    run: str
    report: str
    model: str
    cost: Optional[float]
    date: str
    score: Optional[float]
    claims: Tuple[str, ...]
    state: str = "ready"
    inflated: bool = False

    def validate(self, registry: Optional[YardstickRegistry] = None) -> None:
        entry = (registry or default_registry()).get(self.yardstick)
        if not self.entry.strip():
            raise ValidationError("report names no entry")
        if not self.run.strip():
            raise ValidationError("report names no run")
        if not self.report.strip():
            raise ValidationError("run report reports nothing")
        if not str(self.model or "").strip():
            raise ValidationError(
                "report names no model: a published "
                "result is reported with model, cost "
                "and date")
        if self.cost is None:
            raise ValidationError(
                "report names no cost: a published "
                "result is reported with model, cost "
                "and date")
        if not _is_number(self.cost):
            raise ValidationError(f"unknown run cost: {self.cost!r}")
        if self.cost < 0:
            raise ValidationError(
                f"report cost is negative: {self.cost}")
        if not self.date:
            raise ValidationError(
                "report names no run date: a published "
                "result is reported with model, cost "
                "and date")
        _check_date(self.date)
        if self.score is None:
            raise ValidationError("report names no score")
        if not _is_number(self.score):
            raise ValidationError(f"unknown run score: {self.score!r}")
        if self.score < 0:
            raise ValidationError(
                f"report score is negative: {self.score}")
        if self.score > entry.max_score:
            raise ValidationError(
                f"score {self.score} stands above the "
                f"maximum {entry.max_score} for "
                f"{entry.id}: a report is never "
                "inflated here")
        for kind in self.claims:
            if kind not in EVIDENCE_KINDS:
                raise ValidationError(f"unknown run evidence kind: {kind}")
        if not [c for c in self.claims if c in HELD_EVIDENCE]:
            raise ValidationError(
                "run reports report held results only; "
                "a report dressing a bare claim as a "
                "result refuses here")
        if self.state not in REPORT_STATES:
            raise ValidationError(
                "run reports stand ready or shared only, "
                "never sealed or locked; refused "
                f"state: {self.state}")
        if self.inflated:
            raise ValidationError(
                "run reports report runs exactly as "
                "they ran; a report is never inflated here")


def prepare_report(yardstick: str, entry: str, run: str, report: str,
                   model: str, cost: Optional[float], date: str,
                   score: Optional[float],
                   claims: Tuple[str, ...] = (),
                   state: str = "ready") -> RunDraft:
    made = RunDraft(yardstick=yardstick, entry=entry,
                    run=run, report=report,
                    model=model, cost=cost,
                    date=date, score=score,
                    claims=tuple(claims),
                    state=state)
    made.validate()
    return made


def format_yardstick(entry: YardstickEntry) -> str:
    return (f"{entry.label} ({entry.id}): one {entry.item_word} "
            f"at a time, licence {entry.licence} "
            f"({entry.licence_standing}), maximum score "
            f"{entry.max_score}, standing {entry.standing} "
            f"- {entry.reason}")


def format_yardsticks(registry: Optional[YardstickRegistry] = None) -> str:
    reg = registry or default_registry()
    return "\n".join(format_yardstick(e) for e in reg.entries())


def format_record(record: RunRecord,
                  registry: Optional[YardstickRegistry] = None) -> str:
    reg = registry or default_registry()
    entry = reg.get(record.yardstick)
    standing = derive_standing(record, reg)
    state = "held as reported" if standing.held else "open: " + "; ".join(standing.gaps)
    return (f"{record.yardstick}/{record.run}: model "
            f"{record.model or '(no model named)'} on "
            f"{entry.label} - score {record.score} of "
            f"{entry.max_score}, cost {record.cost}, "
            f"date {record.date or '(no date)'} - {state}")


def format_records(records: Iterable[RunRecord],
                   registry: Optional[YardstickRegistry] = None) -> str:
    return "\n".join(format_record(r, registry) for r in records)
