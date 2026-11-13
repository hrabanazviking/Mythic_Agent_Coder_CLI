"""The benchmark harness book (roadmap slice M-255) - pure layer.

Part XI - Proof. The roadmap words: **M-008's pack
automated - task, sandbox repo, run, grade (tests +
diff review rubric) - repeatable per part and per
release.**

What this layer holds, as data:

* A **harness registry** held as data - one entry per
  run kind (part_run, release_run): its id, its plain
  label, the word that kind gives a single run's scope
  (part / release), the scope it repeats over, the
  standing it arrives with, and why the entry stands,
  in plain words. Every entry arrives as listed data
  (standing 'listed'); a kind the registry does not
  hold refuses BY NAME; a duplicated, half-written, or
  published entry refuses whole. A new run kind needs
  no code change.
* A **run record** holds, for one run kind and one
  run, one benchmark task run as a supplied fact: the
  pack task it ran (B-01..B-20, in one of the pack's
  five categories), its title, the sandbox repo the
  run was given, how its grading tests came out
  (passed of total), the diff review rubric it was
  graded against and the criteria it met, the stages
  it has walked, and the claims it rests on, by kind.
  Its standing is DERIVED at call time against the
  explicit run walk held as data (STAGES, TRANSITIONS):
  tasked, sandboxed, run, graded. A record resting on
  a bare claim (feeling, memory, assertion, summary)
  instead of held evidence (test_log_ref, diff_ref,
  sandbox_ref, journal_ref), graded on no tests, with
  tests not all passing, or with rubric criteria unmet
  stands open, named in its gaps. A run is graded by
  tests *and* the diff review rubric together - either
  one alone never passes a run here.
* A **run report** is the only shape a run record may
  produce. A report is never an inflated claim by this
  layer: it stands at state "ready" by default, may be
  marked "shared" by a human, and reports graded runs
  exactly as they graded - this book automates the
  pack and prepares run reports; it never inflates a
  result. A report asking to be sealed or locked
  instead of ready/shared, or to be inflated instead
  of reported, refuses BY NAME.

Honesty rule, made code: a run passes only when it
rests on held evidence and both of its gradings are
complete. A run standing on bare claims alone, or
graded on tests alone, stands open by construction -
this book will not dress a claim, or half a grading,
up as a benchmark result.

Honest boundary: this layer holds registry entries,
run records, derived standings and run reports as
data. It runs no task, creates no sandbox, executes
no grading test and writes nothing outside the
session; the agent layer owns holding a session's
records and speaking for them, and the shipped pack
itself stays M-008's (mythic_agent.core.benchmark_tasks).
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Tuple
from .validation import ValidationError

__all__ = [
    "REPORT_STATES",
    "BARE_CLAIMS",
    "EVIDENCE_KINDS",
    "CATEGORIES",
    "HELD_EVIDENCE",
    "PLAIN_EXPLANATION",
    "RUN_KINDS",
    "STAGES",
    "TRANSITIONS",
    "STANDINGS",
    "USAGE",
    "BENCHMARK_HARNESS_SCHEMA",
    "BENCHMARK_HARNESS_SLICE",
    "RunStanding",
    "RunRecord",
    "RunDraft",
    "HarnessEntry",
    "HarnessRegistry",
    "default_registry",
    "derive_standing",
    "format_record",
    "format_records",
    "format_kind",
    "format_kinds",
    "prepare_report",
]

BENCHMARK_HARNESS_SLICE = "M-255"
BENCHMARK_HARNESS_SCHEMA = "mythic.benchmark_harness/1"

PLAIN_EXPLANATION = (
    "The M-008 pack, automated: each run takes one "
    "task, is given its own sandbox repo, runs, and is "
    "graded by its tests and its diff review rubric "
    "together, repeatable per part and per release. A "
    "run graded on tests alone, or resting on bare "
    "claims, stands open, and this book only prepares "
    "run reports: a result is reported exactly as it "
    "graded, never inflated."
)
USAGE = (
    "Record each run against its kind and task; read "
    "its derived standing before letting it prepare a "
    "run report; prepare any report only as a report "
    "and let a human share it. The whole pack, "
    "automated, as data first."
)

STAGES = ("tasked", "sandboxed", "run", "graded")
TRANSITIONS = {
    "tasked": ("sandboxed",),
    "sandboxed": ("run",),
    "run": ("graded",),
    "graded": (),
}
CATEGORIES = ("bugfix", "feature", "refactor", "test-writing", "docs")
HELD_EVIDENCE = ("test_log_ref", "diff_ref", "sandbox_ref", "journal_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
EVIDENCE_KINDS = HELD_EVIDENCE + BARE_CLAIMS
REPORT_STATES = ("ready", "shared")
STANDINGS = ("listed",)


@dataclass(frozen=True)
class HarnessEntry:
    id: str
    label: str
    item_word: str
    scope: str
    standing: str
    reason: str

    def validate(self) -> None:
        for name in ("id", "label", "item_word", "scope", "standing", "reason"):
            if not str(getattr(self, name)).strip():
                raise ValidationError(f"harness entry missing {name}")
        if self.standing != "listed":
            raise ValidationError(
                "harness run kinds are listed data "
                "only, never a published yardstick here; "
                f"refused standing: {self.standing}")


RUN_KINDS = (
    HarnessEntry("part_run", "Part benchmark run", "part", "per_part", "listed",
                 "one part's pack tasks run through the harness on demand - task, sandbox repo, run, grade - repeatable for every part"),
    HarnessEntry("release_run", "Release benchmark run", "release", "per_release", "listed",
                 "the whole pack run for a release and graded the same way as a part run, so part and release results compare honestly"),
)


class HarnessRegistry:
    def __init__(self, entries: Iterable[HarnessEntry] = RUN_KINDS):
        self._entries: Dict[str, HarnessEntry] = {}
        for entry in entries:
            entry.validate()
            if entry.id in self._entries:
                raise ValidationError(f"duplicate run kind: {entry.id}")
            self._entries[entry.id] = entry

    def get(self, kind_id: str) -> HarnessEntry:
        try:
            return self._entries[kind_id]
        except KeyError:
            raise ValidationError(f"unknown run kind: {kind_id}") from None

    def ids(self) -> Tuple[str, ...]:
        return tuple(self._entries)

    def entries(self) -> Tuple[HarnessEntry, ...]:
        return tuple(self._entries.values())


def default_registry() -> HarnessRegistry:
    return HarnessRegistry()


@dataclass(frozen=True)
class RunRecord:
    kind: str
    run: str
    task: str
    category: str
    title: str
    sandbox: str
    tests_passed: int
    tests_total: int
    rubric_criteria: Tuple[str, ...]
    rubric_met: Tuple[str, ...]
    stages: Tuple[str, ...]
    claims: Tuple[str, ...]

    def validate(self, registry: Optional[HarnessRegistry] = None) -> None:
        (registry or default_registry()).get(self.kind)
        if not self.run.strip():
            raise ValidationError("record names no run")
        task = self.task
        ok = (len(task) == 4 and task.startswith("B-")
              and task[2:].isdigit() and 1 <= int(task[2:]) <= 20)
        if not ok:
            raise ValidationError(f"unknown benchmark task: {task}")
        if self.category not in CATEGORIES:
            raise ValidationError(f"unknown benchmark category: {self.category}")
        if not self.title.strip():
            raise ValidationError("record names no title")
        if not self.sandbox.strip():
            raise ValidationError("record names no sandbox repo")
        for name in ("tests_passed", "tests_total"):
            value = getattr(self, name)
            if (not isinstance(value, int) or isinstance(value, bool)
                    or value < 0):
                raise ValidationError(
                    f"record {name} is not a non-negative whole number")
        if self.tests_passed > self.tests_total:
            raise ValidationError(
                "record passes more tests than it ran")
        for criterion in self.rubric_met:
            if criterion not in self.rubric_criteria:
                raise ValidationError(
                    f"rubric criterion met but not in the rubric: {criterion}")
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
                    registry: Optional[HarnessRegistry] = None) -> RunStanding:
    record.validate(registry)
    gaps = []
    stages = record.stages
    if not stages or stages[0] != STAGES[0]:
        gaps.append("record does not open at tasked")
        stages = stages or ()
    else:
        for prev, nxt in zip(stages, stages[1:]):
            if nxt not in TRANSITIONS.get(prev, ()):
                gaps.append(f"stage step {prev} -> {nxt} not in the walk")
    stage = stages[-1] if stages else "unseen"
    if stage != "graded":
        gaps.append(f"record stands at {stage}, not graded")
    if record.tests_total == 0:
        gaps.append("run was graded on no tests")
    elif record.tests_passed < record.tests_total:
        gaps.append(
            f"tests not all passing: {record.tests_passed} "
            f"of {record.tests_total}")
    if not record.rubric_criteria:
        gaps.append("run carries no diff review rubric")
    else:
        missing = [c for c in record.rubric_criteria
                   if c not in record.rubric_met]
        if missing:
            gaps.append(
                "diff review rubric not fully met: " + ", ".join(missing))
    held_kinds = [c for c in record.claims if c in HELD_EVIDENCE]
    bare = [c for c in record.claims if c in BARE_CLAIMS]
    if not held_kinds:
        gaps.append("record rests on no held evidence")
    if bare and not held_kinds:
        gaps.append("record rests on bare claims only: " + ", ".join(bare))
    return RunStanding(held=not gaps, stage=stage,
                       grade="passed" if not gaps else "open",
                       gaps=tuple(gaps))


@dataclass(frozen=True)
class RunDraft:
    kind: str
    entry: str
    run: str
    report: str
    state: str = "ready"
    inflated: bool = False

    def validate(self) -> None:
        if not self.kind.strip():
            raise ValidationError("report names no run kind")
        if not self.entry.strip():
            raise ValidationError("report names no entry")
        if not self.run.strip():
            raise ValidationError("report names no run")
        if not self.report.strip():
            raise ValidationError("run report reports nothing")
        if self.state not in REPORT_STATES:
            raise ValidationError(
                "run reports stand ready or shared only, "
                "never sealed or locked; refused "
                f"state: {self.state}")
        if self.inflated:
            raise ValidationError(
                "run reports report graded runs exactly; "
                "a report is never inflated here")


def prepare_report(kind: str, entry: str, run: str, report: str,
                   state: str = "ready") -> RunDraft:
    made = RunDraft(kind=kind, entry=entry,
                    run=run, report=report,
                    state=state)
    made.validate()
    return made


def format_kind(entry: HarnessEntry) -> str:
    return f"{entry.label} ({entry.id}): one {entry.item_word} at a time, scope {entry.scope}, standing {entry.standing} - {entry.reason}"


def format_kinds(registry: Optional[HarnessRegistry] = None) -> str:
    reg = registry or default_registry()
    return "\n".join(format_kind(e) for e in reg.entries())


def format_record(record: RunRecord,
                  registry: Optional[HarnessRegistry] = None) -> str:
    standing = derive_standing(record, registry)
    state = "passed as graded" if standing.held else "open: " + "; ".join(standing.gaps)
    return (f"{record.kind}/{record.run}: task {record.task} "
            f"({record.category}) in sandbox {record.sandbox} - "
            f"tests {record.tests_passed}/{record.tests_total}, "
            f"rubric {len(record.rubric_met)}/{len(record.rubric_criteria)} "
            f"met - {state}")


def format_records(records: Iterable[RunRecord],
                   registry: Optional[HarnessRegistry] = None) -> str:
    return "\n".join(format_record(r, registry) for r in records)
