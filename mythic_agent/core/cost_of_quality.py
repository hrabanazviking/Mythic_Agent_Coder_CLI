"""The cost-of-quality book (roadmap slice M-267) - pure layer.

Part XI - Proof. The roadmap words: **benchmark scores against spend per model route - the honest shopping guide for the user's own money.**

What this layer holds, as data: a route registry Q-01..Q-12 (the local free route, the local Aesir route, the cheap cloud route, the mid cloud route, the frontier route, the reasoning route, the vision route, the long-context route, the coding route, the fast route, the spend ledger route, the fallback route), each listed only, each benchmarked and priced; a cost record per route holding its costing work, date, disposition PROVEN or ROADED, owner, proof kind and stage walk named-benchmarked-priced-dispositioned-held; a derived standing; a derived cost verdict over the whole book; and a cost report prepared only through the prepare road, ready or shared, never sealed, inflated or certified short of every route answered.

Honesty rule, made code: a route counts PROVEN only on benchmark scores measured against spend actually paid resting on held evidence (a benchmark_ref among benchmark_ref, spend_ref, receipt_ref, run_ref - never a bare claim). A PROVEN finding on a vendor claim or no proof stands open, named in its gaps: no vendor word. A ROADED finding stands held only with a named owner and something recorded - ownerless is a wish, silent is not a road. A route praised as cheap and good on a vendor's word alone, not on measured scores against paid spend, faces the book as data here, not as an inherited truth.

Honest boundary: this book holds and judges cost records as data; it does not itself run a benchmark or spend a coin. It benchmarks nothing and buys nothing; the agent layer owns holding session records and speaking for them.
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
    "ROUTES",
    "COST_OF_QUALITY_SCHEMA",
    "COST_OF_QUALITY_SLICE",
    "CostOfQualityStanding",
    "CostOfQualityVerdict",
    "CostOfQualityRecord",
    "CostOfQualityReport",
    "CostOfQualityEntry",
    "CostOfQualityRegistry",
    "default_registry",
    "derive_standing",
    "derive_verdict",
    "format_record",
    "format_records",
    "format_route",
    "format_routes",
    "prepare_report",
]

COST_OF_QUALITY_SLICE = "M-267"
COST_OF_QUALITY_SCHEMA = "mythic.cost_of_quality/1"

PLAIN_EXPLANATION = (
    "The cost-of-quality report, done honestly: "
    "benchmark scores set against spend per "
    "model route - the honest shopping guide "
    "for the user's own money. A route counts "
    "PROVEN only on scores measured against "
    "spend actually paid, resting on held "
    "evidence. Every other route ships ROADED "
    "with a named owner, in the open - an "
    "ownerless road is named, never silent, and "
    "no route is praised on a vendor's word."
)
USAGE = (
    "Record each route finding against its "
    "route, proven by benchmark scores measured "
    "against spend actually paid or roaded with "
    "its owner named; read the derived cost "
    "verdict before letting any report claim "
    "the cost report complete; prepare a report "
    "only as a report, with every route "
    "answered - proven on held evidence or "
    "roaded with an owner - and let a human "
    "share it. The whole cost book, answered "
    "route by route, as data first."
)


STAGES = ("named", "benchmarked", "priced", "dispositioned", "held")
TRANSITIONS = {
    "named": ("benchmarked",),
    "benchmarked": ("priced",),
    "priced": ("dispositioned",),
    "dispositioned": ("held",),
    "held": (),
}
HELD_EVIDENCE = ("benchmark_ref", "spend_ref", "receipt_ref", "run_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
EVIDENCE_KINDS = HELD_EVIDENCE + BARE_CLAIMS
REPORT_STATES = ("ready", "shared")
DISPOSITIONS = ("PROVEN", "ROADED")
PROOF_KINDS = ("measured-and-priced", "vendor-claim-only", "none")
DOCTRINE_REFS = ("honest-shopping", "own-money", "standing-law", "proof-duty")
SUBJECTS = ("local-free-route", "local-aesir-route", "cheap-cloud-route", "mid-cloud-route", "frontier-route", "reasoning-route", "vision-route", "long-context-route", "coding-route", "fast-route", "spend-ledger-route", "fallback-route")


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
class CostOfQualityEntry:
    id: str
    doctrine: str
    subject: str
    standing: str
    reason: str
    benchmarked: bool = True
    priced: bool = True
    def validate(self) -> None:
        for name in ("id", "doctrine", "subject", "standing", "reason"):
            if not str(getattr(self, name)).strip():
                raise ValidationError(f"route entry missing {name}")
        if self.doctrine not in DOCTRINE_REFS:
            raise ValidationError(f"unknown route doctrine: {self.doctrine}")
        if self.subject not in SUBJECTS:
            raise ValidationError(f"unknown route subject: {self.subject}")
        if self.standing != "listed":
            raise ValidationError("route entries are listed data only, never a published verdict here; " f"refused standing: {self.standing}")
        if not self.benchmarked:
            raise ValidationError("route entries are benchmarked only; " f"refused unbenchmarked entry: {self.id}")
        if not self.priced:
            raise ValidationError("route entries are priced only; " f"refused unpriced entry: {self.id}")


ROUTES = (
    CostOfQualityEntry("Q-01", "honest-shopping", "local-free-route", "listed",
              "the local free route: on-device models at no spend per run - its quality score is the floor every paid route must beat to earn its money"),
    CostOfQualityEntry("Q-02", "own-money", "local-aesir-route", "listed",
              "the Aesir local route: the house engine on house hardware - its spend is the hardware already owned, scored on the same benchmarks as every paid door"),
    CostOfQualityEntry("Q-03", "honest-shopping", "cheap-cloud-route", "listed",
              "the cheap cloud route: the lowest-spend hosted door - proven only when its benchmark score per coin clears the local free floor"),
    CostOfQualityEntry("Q-04", "own-money", "mid-cloud-route", "listed",
              "the mid cloud route: the middle-spend hosted door, the everyday-driver candidate - scored against both of its neighbours, never in isolation"),
    CostOfQualityEntry("Q-05", "honest-shopping", "frontier-route", "listed",
              "the frontier route: the highest-spend hosted door - its premium is honest only where its scores clear the mid route by a named margin"),
    CostOfQualityEntry("Q-06", "honest-shopping", "reasoning-route", "listed",
              "the reasoning route: deep-thinking models at reasoning prices - scored on hard problems, never on chatter"),
    CostOfQualityEntry("Q-07", "honest-shopping", "vision-route", "listed",
              "the vision route: models that see - scored on real image work set against what the seeing costs"),
    CostOfQualityEntry("Q-08", "honest-shopping", "long-context-route", "listed",
              "the long-context route: wide-window models - scored on book-length work set against the wide-window price"),
    CostOfQualityEntry("Q-09", "own-money", "coding-route", "listed",
              "the coding route: the route this coder itself drives by - scored on real slices, its spend counted per banked slice"),
    CostOfQualityEntry("Q-10", "honest-shopping", "fast-route", "listed",
              "the fast route: quick-answer models - scored on latency-bound work where waiting itself is a cost"),
    CostOfQualityEntry("Q-11", "standing-law", "spend-ledger-route", "listed",
              "the spend ledger route: every route's spend itself, counted from the cost ledger and never from memory - a route with no ledger entry has no proven spend"),
    CostOfQualityEntry("Q-12", "proof-duty", "fallback-route", "listed",
              "the fallback route: the door the fallback chain walks to - scored like every other route, no free pass for standing second"),
)


class CostOfQualityRegistry:
    def __init__(self, entries: Iterable[CostOfQualityEntry] = ROUTES):
        self._entries: Dict[str, CostOfQualityEntry] = {}
        for entry in entries:
            entry.validate()
            if entry.id in self._entries:
                raise ValidationError(f"duplicate route: {entry.id}")
            self._entries[entry.id] = entry

    def get(self, route_id: str) -> CostOfQualityEntry:
        try:
            return self._entries[route_id]
        except KeyError:
            raise ValidationError(
                f"unknown route: {route_id}") from None

    def ids(self) -> Tuple[str, ...]:
        return tuple(self._entries)

    def entries(self) -> Tuple[CostOfQualityEntry, ...]:
        return tuple(self._entries.values())

    def combinations(self) -> Tuple[str, ...]:
        return tuple(self._entries)


def default_registry() -> CostOfQualityRegistry:
    return CostOfQualityRegistry()


@dataclass(frozen=True)
class CostOfQualityRecord:
    route: str
    work: str
    date: str
    disposition: str
    owner: str
    proof_kind: str
    stages: Tuple[str, ...]
    claims: Tuple[str, ...]

    def validate(self, registry: Optional[CostOfQualityRegistry] = None) -> None:
        (registry or default_registry()).get(self.route)
        if not self.work.strip():
            raise ValidationError("record names no costing work")
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
class CostOfQualityStanding:
    held: bool
    stage: str
    grade: str
    gaps: Tuple[str, ...]


def derive_standing(record: CostOfQualityRecord,
                    registry: Optional[CostOfQualityRegistry] = None) -> CostOfQualityStanding:
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
        if record.proof_kind != "measured-and-priced":
            gaps.append(
                f"a PROVEN route rests on {record.proof_kind} "
                "evidence, not benchmark scores measured against spend actually paid: "
                "no vendor word")
        if "benchmark_ref" not in record.claims:
            gaps.append(
                "the proven route rests on no held "
                "benchmark evidence")
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
    return CostOfQualityStanding(held=not gaps, stage=stage,
                           grade="held" if not gaps else "open",
                           gaps=tuple(gaps))


@dataclass(frozen=True)
class CostOfQualityVerdict:
    ready: bool
    gaps: Tuple[str, ...]
    proven_routes: Tuple[str, ...]
    roaded_routes: Tuple[str, ...]
    missing_routes: Tuple[str, ...]


def derive_verdict(records: Iterable[CostOfQualityRecord],
                   registry: Optional[CostOfQualityRegistry] = None) -> CostOfQualityVerdict:
    reg = registry or default_registry()
    by_route: Dict[str, CostOfQualityRecord] = {}
    gaps = []
    for record in records:
        record.validate(reg)
        if record.route in by_route:
            gaps.append(
                f"route {record.route} carries two findings")
        else:
            by_route[record.route] = record
    missing = tuple(aid for aid in reg.combinations()
                    if aid not in by_route)
    for route_id in missing:
        gaps.append(f"route {route_id} has no finding in the book")
    fixed = []
    roaded = []
    for route_id, record in by_route.items():
        standing = derive_standing(record, reg)
        if standing.held and record.disposition == "PROVEN":
            fixed.append(route_id)
        if standing.held and record.disposition == "ROADED":
            roaded.append(route_id)
        if not standing.held:
            gaps.append(
                f"route {route_id} stands open: "
                + "; ".join(standing.gaps))
    return CostOfQualityVerdict(ready=not gaps, gaps=tuple(gaps),
                        proven_routes=tuple(fixed),
                        roaded_routes=tuple(roaded),
                        missing_routes=missing)


@dataclass(frozen=True)
class CostOfQualityReport:
    book: str
    entry: str
    report: str
    date: str
    proven_count: int
    roaded_count: int
    total_routes: int
    claims: Tuple[str, ...]
    state: str = "ready"
    certified: bool = False
    inflated: bool = False

    def validate(self, registry: Optional[CostOfQualityRegistry] = None) -> None:
        reg = registry or default_registry()
        if not self.book.strip():
            raise ValidationError("report names no book")
        if not self.entry.strip():
            raise ValidationError("report names no entry")
        if not self.report.strip():
            raise ValidationError("cost report reports nothing")
        if not self.date:
            raise ValidationError(
                "report names no date: a cost "
                "report is reported with its date")
        _check_date(self.date)
        expected = len(reg.combinations())
        if self.total_routes != expected:
            raise ValidationError(
                f"report book holds {self.total_routes} "
                f"routes, not the road's {expected}")
        if self.proven_count < 0 or self.roaded_count < 0:
            raise ValidationError(
                "unknown route count: "
                f"{self.proven_count}/{self.roaded_count}")
        if self.proven_count + self.roaded_count > self.total_routes:
            raise ValidationError(
                "answered routes exceed the book: "
                f"{self.proven_count} + {self.roaded_count} "
                f"of {self.total_routes}")
        for kind in self.claims:
            if kind not in EVIDENCE_KINDS:
                raise ValidationError(f"unknown report evidence kind: {kind}")
        if not [c for c in self.claims if c in HELD_EVIDENCE]:
            raise ValidationError(
                "cost reports report held findings "
                "only; a report dressing a bare claim "
                "as a proof refuses here")
        if self.state not in REPORT_STATES:
            raise ValidationError(
                "cost reports stand ready or shared "
                "only, never sealed or locked; refused "
                f"state: {self.state}")
        if self.certified and \
                self.proven_count + self.roaded_count < self.total_routes:
            raise ValidationError(
                "an unanswered route anywhere stops "
                "the closing claim: this report may not "
                "claim the cost report complete short of "
                "every route answered")
        if self.inflated:
            raise ValidationError(
                "cost reports report the findings "
                "exactly as they were dispositioned; a "
                "report is never inflated here")


def prepare_report(book: str, entry: str, report: str,
                   date: str, proven_count: int, roaded_count: int,
                   total_routes: int,
                   claims: Tuple[str, ...] = (),
                   state: str = "ready",
                   certified: bool = False) -> CostOfQualityReport:
    made = CostOfQualityReport(book=book, entry=entry,
                       report=report, date=date,
                       proven_count=proven_count,
                       roaded_count=roaded_count,
                       total_routes=total_routes,
                       claims=tuple(claims),
                       state=state, certified=certified)
    made.validate()
    return made


def format_route(entry: CostOfQualityEntry) -> str:
    return (f"{entry.id} {entry.doctrine}/{entry.subject}: "
            f"standing {entry.standing} "
            f"- {entry.reason}")


def format_routes(registry: Optional[CostOfQualityRegistry] = None) -> str:
    reg = registry or default_registry()
    return "\n".join(format_route(e) for e in reg.entries())


def format_record(record: CostOfQualityRecord,
                  registry: Optional[CostOfQualityRegistry] = None) -> str:
    reg = registry or default_registry()
    entry = reg.get(record.route)
    standing = derive_standing(record, reg)
    state = "held as answered" if standing.held else "open: " + "; ".join(standing.gaps)
    return (f"{record.route} {entry.doctrine}/{entry.subject}: "
            f"disposition {record.disposition} "
            f"({record.proof_kind}), date "
            f"{record.date or '(no date)'} - {state}")


def format_records(records: Iterable[CostOfQualityRecord],
                   registry: Optional[CostOfQualityRegistry] = None) -> str:
    return "\n".join(format_record(r, registry) for r in records)
