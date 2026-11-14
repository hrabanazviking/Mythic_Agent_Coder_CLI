"""The release shaping book (roadmap slice M-269) - pure layer.

Part XI - Proof. The roadmap words: **ready / shaping / NOT READY per release, by version, shape and readiness, in the release itself.**

What this layer holds, as data: a release registry R-01..R-12 (the version number, the release notes shape, the readiness gate, the release shape, the artifact set, the upgrade notes, the known issues, the support window, the rollback note, checksums and signature, the install shape, the announcement shape), each listed only, each labelled and evidenced; a release record per release holding its truth work, date, disposition READY or SHAPING or NOT_READY, owner, proof kind and stage walk named-labelled-evidenced-dispositioned-held; a derived standing; a derived release verdict over the whole book; and a release report prepared only through the prepare road, ready or shared, never sealed, inflated or certified short of every release answered.

Honesty rule, made code: a release counts READY only on held proof measured in the release itself resting on held evidence (an evidence_ref among evidence_ref, test_ref, run_ref, ledger_ref - never a bare claim). A release counts SHAPING only where the ready part rests on held evidence and the unready part is owned and recorded in the open. A release counts NOT_READY only with a named owner and the reason recorded - an unready release admitted in the open is honest; an unready release dressed as ready is not. Silence is not a label: a release with no record stands missing, named in the verdict gaps.

Honest boundary: this book holds and judges release records as data; it does not itself cut a release or run a test. It proves nothing and ships nothing; the agent layer owns holding session records and speaking for them.
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
    "RELEASES",
    "RELEASE_SHAPING_SCHEMA",
    "RELEASE_SHAPING_SLICE",
    "ReleaseShapingStanding",
    "ReleaseShapingVerdict",
    "ReleaseShapingRecord",
    "ReleaseShapingReport",
    "ReleaseShapingEntry",
    "ReleaseShapingRegistry",
    "default_registry",
    "derive_standing",
    "derive_verdict",
    "format_record",
    "format_records",
    "format_release",
    "format_releases",
    "prepare_report",
]

RELEASE_SHAPING_SLICE = "M-269"
RELEASE_SHAPING_SCHEMA = "mythic.release_shaping/1"

PLAIN_EXPLANATION = (
    "The release shaping, done honestly: "
    "ready, shaping or NOT READY per "
    "release, printed in the release itself. A "
    "release counts READY only on held proof, "
    "SHAPING only where the ready part rests "
    "on held evidence and the rest is owned in "
    "the open, and NOT READY only with its "
    "reason recorded - never silent, never "
    "inflated, never dressed as ready.")
USAGE = (
    "Record each release finding against its "
    "release, ready on held evidence, shaping "
    "with the ready part evidenced and the "
    "remainder owned, or not ready with its "
    "owner and reason recorded; read the "
    "derived release verdict before letting "
    "any report claim the release complete; "
    "prepare a report only as a report, with "
    "every release answered - ready, shaping "
    "or not ready, each in the open - and "
    "let a human share it. The whole release "
    "book, answered release by release, as data "
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
DISPOSITIONS = ("READY", "SHAPING", "NOT_READY")
PROOF_KINDS = ("ready-and-held", "partially-held", "none")
DOCTRINE_REFS = ("version-truth", "shape-honesty", "readiness-law", "release-duty")
SUBJECTS = ("version-number", "release-notes-shape", "readiness-gate", "release-shape", "artifact-set", "upgrade-notes", "known-issues", "support-window", "rollback-note", "checksums-signature", "install-shape", "announcement-shape")


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
class ReleaseShapingEntry:
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
                raise ValidationError(f"release entry missing {name}")
        if self.doctrine not in DOCTRINE_REFS:
            raise ValidationError(f"unknown release doctrine: {self.doctrine}")
        if self.subject not in SUBJECTS:
            raise ValidationError(f"unknown release subject: {self.subject}")
        if self.standing != "listed":
            raise ValidationError("release entries are listed data only, never a published verdict here; " f"refused standing: {self.standing}")
        if not self.labelled:
            raise ValidationError("release entries are labelled only; " f"refused unlabelled entry: {self.id}")
        if not self.evidenced:
            raise ValidationError("release entries are evidenced only; " f"refused unevidenced entry: {self.id}")


RELEASES = (
    ReleaseShapingEntry("R-01", "version-truth", "version-number", "listed",
              "the version number itself: one number, honestly bumped for what actually changed, never decorated or held back"),
    ReleaseShapingEntry("R-02", "version-truth", "release-notes-shape", "listed",
              "the release notes shape: what changed, in plain words first, grouped by what a user can feel"),
    ReleaseShapingEntry("R-03", "shape-honesty", "readiness-gate", "listed",
              "the readiness gate: the checks a release must pass before it may call itself ready, named before they are run"),
    ReleaseShapingEntry("R-04", "version-truth", "release-shape", "listed",
              "the release shape inside the release: every change listed once, in its own words, nothing inflated"),
    ReleaseShapingEntry("R-05", "shape-honesty", "artifact-set", "listed",
              "the artifact set: the exact files the release consists of, named and counted, no extras riding along"),
    ReleaseShapingEntry("R-06", "version-truth", "upgrade-notes", "listed",
              "the upgrade notes: what a user moving from the last release must do, step by step, with nothing assumed"),
    ReleaseShapingEntry("R-07", "shape-honesty", "known-issues", "listed",
              "the known issues: what is still broken or unready in this release, admitted in the open with owners"),
    ReleaseShapingEntry("R-08", "version-truth", "support-window", "listed",
              "the support window: how long this release is supported and what support honestly means here"),
    ReleaseShapingEntry("R-09", "readiness-law", "rollback-note", "listed",
              "the rollback note: how to return to the previous release if this one fails, written before it is needed"),
    ReleaseShapingEntry("R-10", "release-duty", "checksums-signature", "listed",
              "checksums and signature: the digests a user can verify the artifacts against, held with the release"),
    ReleaseShapingEntry("R-11", "version-truth", "install-shape", "listed",
              "the install shape: how this release is installed on each platform, one road per platform, no hidden steps"),
    ReleaseShapingEntry("R-12", "release-duty", "announcement-shape", "listed",
              "the announcement shape: how the release is announced, plain language first, claims no larger than the proof"),
)


class ReleaseShapingRegistry:
    def __init__(self, entries: Iterable[ReleaseShapingEntry] = RELEASES):
        self._entries: Dict[str, ReleaseShapingEntry] = {}
        for entry in entries:
            entry.validate()
            if entry.id in self._entries:
                raise ValidationError(f"duplicate release: {entry.id}")
            self._entries[entry.id] = entry

    def get(self, release_id: str) -> ReleaseShapingEntry:
        try:
            return self._entries[release_id]
        except KeyError:
            raise ValidationError(
                f"unknown release: {release_id}") from None

    def ids(self) -> Tuple[str, ...]:
        return tuple(self._entries)

    def entries(self) -> Tuple[ReleaseShapingEntry, ...]:
        return tuple(self._entries.values())

    def combinations(self) -> Tuple[str, ...]:
        return tuple(self._entries)


def default_registry() -> ReleaseShapingRegistry:
    return ReleaseShapingRegistry()


@dataclass(frozen=True)
class ReleaseShapingRecord:
    release: str
    work: str
    date: str
    disposition: str
    owner: str
    proof_kind: str
    stages: Tuple[str, ...]
    claims: Tuple[str, ...]

    def validate(self, registry: Optional[ReleaseShapingRegistry] = None) -> None:
        (registry or default_registry()).get(self.release)
        if not self.work.strip():
            raise ValidationError("record names no release work")
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
class ReleaseShapingStanding:
    held: bool
    stage: str
    grade: str
    gaps: Tuple[str, ...]


def derive_standing(record: ReleaseShapingRecord,
                    registry: Optional[ReleaseShapingRegistry] = None) -> ReleaseShapingStanding:
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
    if record.disposition == "READY":
        if record.proof_kind != "ready-and-held":
            gaps.append(
                f"a READY release rests on {record.proof_kind} "
                "evidence, not held proof measured in the release itself: "
                "the release tells the truth or stands open")
        if "evidence_ref" not in record.claims:
            gaps.append(
                "the ready release rests on no held "
                "held evidence")
        if not held_kinds:
            gaps.append("record rests on no held evidence")
        if bare and not held_kinds:
            gaps.append("record rests on bare claims only: " + ", ".join(bare))
    else:
        if not record.owner.strip():
            gaps.append(
                "a shaping or not ready finding with no owner "
                "named is a wish, not a road")
        if not record.claims:
            gaps.append(
                "a shaping or not ready finding with nothing "
                "recorded stands silent, not answered")
        if record.disposition == "SHAPING" and not held_kinds:
            gaps.append(
                "a shaping release rests on no held "
                "evidence: the ready part must rest "
                "on held evidence, not on a claim")
        if record.disposition == "NOT_READY" and record.proof_kind == "ready-and-held":
            gaps.append(
                "a NOT READY release resting on full "
                "measured proof contradicts itself: "
                "re-disposition it READY or SHAPING")
    return ReleaseShapingStanding(held=not gaps, stage=stage,
                           grade="held" if not gaps else "open",
                           gaps=tuple(gaps))


@dataclass(frozen=True)
class ReleaseShapingVerdict:
    ready: bool
    gaps: Tuple[str, ...]
    ready_releases: Tuple[str, ...]
    shaping_releases: Tuple[str, ...]
    not_ready_releases: Tuple[str, ...]
    missing_releases: Tuple[str, ...]


def derive_verdict(records: Iterable[ReleaseShapingRecord],
                   registry: Optional[ReleaseShapingRegistry] = None) -> ReleaseShapingVerdict:
    reg = registry or default_registry()
    by_release: Dict[str, ReleaseShapingRecord] = {}
    gaps = []
    for record in records:
        record.validate(reg)
        if record.release in by_release:
            gaps.append(
                f"release {record.release} carries two findings")
        else:
            by_release[record.release] = record
    missing = tuple(aid for aid in reg.combinations()
                    if aid not in by_release)
    for release_id in missing:
        gaps.append(f"release {release_id} has no finding in the book")
    fixed = []
    shaping = []
    notready = []
    for release_id, record in by_release.items():
        standing = derive_standing(record, reg)
        if standing.held and record.disposition == "READY":
            fixed.append(release_id)
        if standing.held and record.disposition == "SHAPING":
            shaping.append(release_id)
        if standing.held and record.disposition == "NOT_READY":
            notready.append(release_id)
        if not standing.held:
            gaps.append(
                f"release {release_id} stands open: "
                + "; ".join(standing.gaps))
    return ReleaseShapingVerdict(ready=not gaps, gaps=tuple(gaps),
                        ready_releases=tuple(fixed),
                        shaping_releases=tuple(shaping),
                        not_ready_releases=tuple(notready), missing_releases=missing)


@dataclass(frozen=True)
class ReleaseShapingReport:
    book: str
    entry: str
    report: str
    date: str
    ready_count: int
    shaping_count: int
    not_ready_count: int
    total_releases: int
    claims: Tuple[str, ...]
    state: str = "ready"
    certified: bool = False
    inflated: bool = False

    def validate(self, registry: Optional[ReleaseShapingRegistry] = None) -> None:
        reg = registry or default_registry()
        if not self.book.strip():
            raise ValidationError("report names no book")
        if not self.entry.strip():
            raise ValidationError("report names no entry")
        if not self.report.strip():
            raise ValidationError("release reports nothing")
        if not self.date:
            raise ValidationError(
                "report names no date: a release "
                "report is reported with its date")
        _check_date(self.date)
        expected = len(reg.combinations())
        if self.total_releases != expected:
            raise ValidationError(
                f"report book holds {self.total_releases} "
                f"releases, not the road's {expected}")
        if self.ready_count < 0 or self.shaping_count < 0 or self.not_ready_count < 0:
            raise ValidationError(
                "unknown release count: "
                f"{self.ready_count}/{self.shaping_count}/{self.not_ready_count}")
        if self.ready_count + self.shaping_count + self.not_ready_count > self.total_releases:
            raise ValidationError(
                "answered releases exceed the book: "
                f"{self.ready_count} + {self.shaping_count} + {self.not_ready_count} "
                f"of {self.total_releases}")
        for kind in self.claims:
            if kind not in EVIDENCE_KINDS:
                raise ValidationError(f"unknown report evidence kind: {kind}")
        if not [c for c in self.claims if c in HELD_EVIDENCE]:
            raise ValidationError(
                "releases report held findings "
                "only; a report dressing a bare claim "
                "as a proof refuses here")
        if self.state not in REPORT_STATES:
            raise ValidationError(
                "releases stand ready or shared "
                "only, never sealed or locked; refused "
                f"state: {self.state}")
        if self.certified and \
                self.ready_count + self.shaping_count + self.not_ready_count < self.total_releases:
            raise ValidationError(
                "an unanswered release anywhere stops "
                "the closing claim: this report may not "
                "claim the release complete short of "
                "every release answered")
        if self.inflated:
            raise ValidationError(
                "releases report the findings "
                "exactly as they were dispositioned; a "
                "report is never inflated here")


def prepare_report(book: str, entry: str, report: str,
                   date: str, ready_count: int, shaping_count: int, not_ready_count: int,
                   total_releases: int,
                   claims: Tuple[str, ...] = (),
                   state: str = "ready",
                   certified: bool = False) -> ReleaseShapingReport:
    made = ReleaseShapingReport(book=book, entry=entry,
                       report=report, date=date,
                       ready_count=ready_count,
                       shaping_count=shaping_count,
                       not_ready_count=not_ready_count,
                       total_releases=total_releases,
                       claims=tuple(claims),
                       state=state, certified=certified)
    made.validate()
    return made


def format_release(entry: ReleaseShapingEntry) -> str:
    return (f"{entry.id} {entry.doctrine}/{entry.subject}: "
            f"standing {entry.standing} "
            f"- {entry.reason}")


def format_releases(registry: Optional[ReleaseShapingRegistry] = None) -> str:
    reg = registry or default_registry()
    return "\n".join(format_release(e) for e in reg.entries())


def format_record(record: ReleaseShapingRecord,
                  registry: Optional[ReleaseShapingRegistry] = None) -> str:
    reg = registry or default_registry()
    entry = reg.get(record.release)
    standing = derive_standing(record, reg)
    state = "held as answered" if standing.held else "open: " + "; ".join(standing.gaps)
    return (f"{record.release} {entry.doctrine}/{entry.subject}: "
            f"disposition {record.disposition} "
            f"({record.proof_kind}), date "
            f"{record.date or '(no date)'} - {state}")


def format_records(records: Iterable[ReleaseShapingRecord],
                   registry: Optional[ReleaseShapingRegistry] = None) -> str:
    return "\n".join(format_record(r, registry) for r in records)
