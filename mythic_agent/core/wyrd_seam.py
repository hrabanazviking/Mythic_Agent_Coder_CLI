"""The WYRD seam (roadmap slice M-249) - pure layer.

Part X - Bridges. The roadmap words: **world-state from
Volmarr's WYRD engine can inform long campaigns (which
machine is free, which forge is hot) - the workshop aware
of itself.**

What this layer holds, as data:

* A **world-state source registry** held as data - one entry
  per source (wyrd_engine, manual_report, campaign_journal,
  keeper_report): its id, its plain label, the word that
  source gives a single telling, the transport it arrives
  by, and why the entry stands, in plain words. Every entry
  arrives as recorded data (transport 'recorded'); a source
  the registry does not hold refuses BY NAME; a duplicated,
  half-written, or live-probing entry refuses whole. A new
  source needs no code change.
* A **node snapshot** holds, for one source and one node
  (a machine or a forge), one world-state telling as a
  supplied fact: the node's availability, its forge state,
  its load band, the campaign position it reports, when it
  was observed, how old the telling is in seconds, the
  stages it has walked, and the claims it rests on, by kind.
  Its standing is DERIVED at call time against the explicit
  fact walk held as data (STAGES, TRANSITIONS): reported,
  recorded, checked, held - and against the fresh limit held
  as data (FRESH_LIMIT_SECONDS). A snapshot resting on a bare
  claim (feeling, memory, assertion, summary) instead of
  held evidence (engine_ref, snapshot_ref, journal_ref,
  keeper_ref), naming no node or no observed time, older
  than the fresh limit, or not knowing its node's
  availability or forge state stands open, named in its
  gaps. An absent snapshot reads as unknown and a stale
  snapshot reads as stale - never as current fact.
* A **campaign advice** is the only shape a proposed
  campaign move may take. Advice is never applied by this
  layer: it stands at approval "pending" by default, may be
  marked "approved" by a human, and never reroutes a
  campaign on its own - the seam informs campaigns; a human
  approves and carries out any move. A proposal asking to
  be executed instead of advised, or carrying any other
  approval word, refuses BY NAME.

Honesty rule, made code: world-state is current only when a
fresh snapshot rests on held evidence. A snapshot standing
at held on bare claims alone, or past the fresh limit,
stands open by construction - the seam will not dress a
claim, or yesterday's telling, up as the workshop now.

Honest boundary: this layer holds registry entries, node
snapshots, derived standings and campaign advice as data.
It calls no WYRD engine API, probes no machine, measures no
load and reroutes no campaign; the agent layer owns holding
a session's snapshots and speaking for them.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Tuple
from .validation import ValidationError

__all__ = [
    "AVAILABILITIES",
    "BARE_CLAIMS",
    "EVIDENCE_KINDS",
    "FORGE_STATES",
    "FRESH_LIMIT_SECONDS",
    "HELD_EVIDENCE",
    "LOAD_BANDS",
    "PLAIN_EXPLANATION",
    "SOURCES",
    "STAGES",
    "TRANSITIONS",
    "USAGE",
    "WYRD_SEAM_SCHEMA",
    "WYRD_SEAM_SLICE",
    "AdviceDraft",
    "NodeSnapshot",
    "SnapshotStanding",
    "SourceEntry",
    "SourceRegistry",
    "default_registry",
    "derive_standing",
    "format_snapshot",
    "format_snapshots",
    "format_source",
    "format_sources",
    "propose_advice",
]

WYRD_SEAM_SLICE = "M-249"
WYRD_SEAM_SCHEMA = "mythic.wyrd_seam/1"

PLAIN_EXPLANATION = (
    "World-state enters a campaign only as a recorded "
    "snapshot with provenance and a timestamp - which "
    "machine is free, which forge is hot. A snapshot that "
    "is absent reads as unknown and one past the fresh "
    "limit reads as stale, never as current fact, and the "
    "seam only advises campaigns: it never reroutes one "
    "on its own."
)
USAGE = (
    "Record each world-state snapshot against its source "
    "and node; read its derived standing before letting "
    "it inform a campaign; propose any campaign move "
    "only as advice and let a human approve and carry "
    "it out."
)

STAGES = ("reported", "recorded", "checked", "held")
TRANSITIONS = {
    "reported": ("recorded",),
    "recorded": ("checked",),
    "checked": ("held",),
    "held": (),
}
AVAILABILITIES = ("free", "busy", "offline", "unknown")
FORGE_STATES = ("hot", "cold", "warming", "unknown")
LOAD_BANDS = ("idle", "light", "heavy", "unknown")
FRESH_LIMIT_SECONDS = 600
HELD_EVIDENCE = ("engine_ref", "snapshot_ref", "journal_ref", "keeper_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
EVIDENCE_KINDS = HELD_EVIDENCE + BARE_CLAIMS
APPROVALS = ("pending", "approved")


@dataclass(frozen=True)
class SourceEntry:
    id: str
    label: str
    snapshot_word: str
    transport: str
    reason: str

    def validate(self) -> None:
        for name in ("id", "label", "snapshot_word", "transport", "reason"):
            if not str(getattr(self, name)).strip():
                raise ValidationError(f"wyrd source entry missing {name}")
        if self.transport != "recorded":
            raise ValidationError(
                "world-state snapshots are recorded data only, "
                "never live probes; refused "
                f"transport: {self.transport}")


SOURCES = (
    SourceEntry("wyrd_engine", "WYRD engine", "snapshot", "recorded",
                "Volmarr's WYRD engine, when it supplies a snapshot for the record"),
    SourceEntry("manual_report", "Manual report", "report", "recorded",
                "a world-state telling supplied by hand and recorded as data"),
    SourceEntry("campaign_journal", "Campaign journal", "entry", "recorded",
                "the campaign journal's own recorded world-state entries"),
    SourceEntry("keeper_report", "Keeper report", "report", "recorded",
                "a keeper's recorded world-state report for a campaign"),
)


class SourceRegistry:
    def __init__(self, entries: Iterable[SourceEntry] = SOURCES):
        self._entries: Dict[str, SourceEntry] = {}
        for entry in entries:
            entry.validate()
            if entry.id in self._entries:
                raise ValidationError(f"duplicate wyrd source: {entry.id}")
            self._entries[entry.id] = entry

    def get(self, source_id: str) -> SourceEntry:
        try:
            return self._entries[source_id]
        except KeyError:
            raise ValidationError(f"unknown wyrd source: {source_id}") from None

    def ids(self) -> Tuple[str, ...]:
        return tuple(self._entries)

    def entries(self) -> Tuple[SourceEntry, ...]:
        return tuple(self._entries.values())


def default_registry() -> SourceRegistry:
    return SourceRegistry()


@dataclass(frozen=True)
class NodeSnapshot:
    source: str
    node: str
    availability: str
    forge_state: str
    load_band: str
    campaign_position: str
    observed_at: str
    age_seconds: int
    stages: Tuple[str, ...]
    claims: Tuple[str, ...]

    def validate(self, registry: Optional[SourceRegistry] = None) -> None:
        (registry or default_registry()).get(self.source)
        if not self.node.strip():
            raise ValidationError("snapshot names no node")
        if self.availability not in AVAILABILITIES:
            raise ValidationError(f"unknown availability: {self.availability}")
        if self.forge_state not in FORGE_STATES:
            raise ValidationError(f"unknown forge state: {self.forge_state}")
        if self.load_band not in LOAD_BANDS:
            raise ValidationError(f"unknown load band: {self.load_band}")
        if not str(self.observed_at).strip():
            raise ValidationError("snapshot names no observed time")
        if (not isinstance(self.age_seconds, int)
                or isinstance(self.age_seconds, bool)
                or self.age_seconds < 0):
            raise ValidationError(
                "snapshot age is not a non-negative whole number")
        for kind in self.claims:
            if kind not in EVIDENCE_KINDS:
                raise ValidationError(f"unknown wyrd evidence kind: {kind}")


@dataclass(frozen=True)
class SnapshotStanding:
    held: bool
    stage: str
    freshness: str
    gaps: Tuple[str, ...]


def derive_standing(snapshot: NodeSnapshot,
                    registry: Optional[SourceRegistry] = None) -> SnapshotStanding:
    snapshot.validate(registry)
    gaps = []
    stages = snapshot.stages
    if not stages or stages[0] != STAGES[0]:
        gaps.append("snapshot does not open at reported")
        stages = stages or ()
    else:
        for prev, nxt in zip(stages, stages[1:]):
            if nxt not in TRANSITIONS.get(prev, ()):
                gaps.append(f"stage step {prev} -> {nxt} not in the walk")
    stage = stages[-1] if stages else "unseen"
    if stage != "held":
        gaps.append(f"snapshot stands at {stage}, not held")
    if snapshot.age_seconds > FRESH_LIMIT_SECONDS:
        freshness = "stale"
        gaps.append(
            f"snapshot is stale: age {snapshot.age_seconds}s over "
            f"the fresh limit {FRESH_LIMIT_SECONDS}s")
    elif not stages:
        freshness = "unknown"
    else:
        freshness = "current"
    if snapshot.availability == "unknown":
        gaps.append("snapshot does not know the node's availability")
    if snapshot.forge_state == "unknown":
        gaps.append("snapshot does not know the node's forge state")
    held_kinds = [c for c in snapshot.claims if c in HELD_EVIDENCE]
    bare = [c for c in snapshot.claims if c in BARE_CLAIMS]
    if not held_kinds:
        gaps.append("snapshot rests on no held evidence")
    if bare and not held_kinds:
        gaps.append("snapshot rests on bare claims only: " + ", ".join(bare))
    return SnapshotStanding(held=not gaps, stage=stage,
                            freshness=freshness, gaps=tuple(gaps))


@dataclass(frozen=True)
class AdviceDraft:
    campaign: str
    node: str
    advice: str
    approval: str = "pending"
    applied: bool = False

    def validate(self) -> None:
        if not self.campaign.strip():
            raise ValidationError("advice names no campaign")
        if not self.node.strip():
            raise ValidationError("advice names no node")
        if not self.advice.strip():
            raise ValidationError("advice proposes nothing")
        if self.approval not in APPROVALS:
            raise ValidationError(
                "campaign advice is by approval only; refused "
                f"approval: {self.approval}")
        if self.applied:
            raise ValidationError(
                "campaign advice is advisory only; advice is "
                "never applied here")


def propose_advice(campaign: str, node: str, advice: str,
                   approval: str = "pending") -> AdviceDraft:
    draft = AdviceDraft(campaign=campaign, node=node,
                        advice=advice, approval=approval)
    draft.validate()
    return draft


def format_source(entry: SourceEntry) -> str:
    return f"{entry.label} ({entry.id}): {entry.snapshot_word} via {entry.transport} - {entry.reason}"


def format_sources(registry: Optional[SourceRegistry] = None) -> str:
    reg = registry or default_registry()
    return "\n".join(format_source(e) for e in reg.entries())


def format_snapshot(snapshot: NodeSnapshot,
                    registry: Optional[SourceRegistry] = None) -> str:
    standing = derive_standing(snapshot, registry)
    state = "current as recorded" if standing.held else "open: " + "; ".join(standing.gaps)
    return (f"{snapshot.source}/{snapshot.node}: availability "
            f"{snapshot.availability}, forge {snapshot.forge_state}, "
            f"load {snapshot.load_band} [{standing.freshness}] - {state}")


def format_snapshots(snapshots: Iterable[NodeSnapshot],
                     registry: Optional[SourceRegistry] = None) -> str:
    return "\n".join(format_snapshot(s, registry) for s in snapshots)
