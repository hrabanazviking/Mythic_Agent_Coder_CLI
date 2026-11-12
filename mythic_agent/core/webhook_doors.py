"""The webhook doors (roadmap slice M-250) - pure layer.

Part X - Bridges. The roadmap words: **inbound events (a PR
opened, an issue filed) can *propose* campaigns - proposals
only; nothing builds unbidden.**

What this layer holds, as data:

* A **webhook source registry** held as data - one entry
  per source (github, gitlab, bitbucket, generic): its id,
  its plain label, the word that source gives a single
  event, the transport it arrives by, and why the entry
  stands, in plain words. Every entry arrives as recorded
  data (transport 'recorded'); a source the registry does
  not hold refuses BY NAME; a duplicated, half-written, or
  live-listening entry refuses whole. A new source needs
  no code change.
* An **inbound event** holds, for one source and one event,
  one webhook telling as a supplied fact: the event's kind,
  its title, its subject, when it was observed, how old the
  telling is in seconds, the stages it has walked, and the
  claims it rests on, by kind. Its standing is DERIVED at
  call time against the explicit fact walk held as data
  (STAGES, TRANSITIONS): received, recorded, checked, held
  - and against the fresh limit held as data
  (FRESH_LIMIT_SECONDS). An event resting on a bare claim
  (feeling, memory, assertion, summary) instead of held
  evidence (payload_ref, delivery_ref, journal_ref,
  keeper_ref), naming no subject, not knowing its kind, or
  older than the fresh limit stands open, named in its
  gaps. An absent event reads as unknown and a stale event
  reads as stale - never as a fact.
* A **campaign proposal** is the only shape an inbound
  event may produce. A proposal is never applied or built
  by this layer: it stands at approval "pending" by
  default, may be marked "approved" by a human, and never
  starts a campaign on its own - the doors propose
  campaigns; a human approves and carries out any build.
  A proposal asking to be executed instead of proposed, or
  carrying any other approval word, refuses BY NAME.

Honesty rule, made code: an event is a fact only when it
rests on held evidence. An event standing on bare claims
alone, or past the fresh limit, stands open by construction
- the doors will not dress a claim, or yesterday's telling,
up as a campaign trigger.

Honest boundary: this layer holds registry entries, inbound
events, derived standings and campaign proposals as data.
It opens no webhook listener, calls no host API, probes no
network and starts or builds nothing; the agent layer owns
holding a session's events and speaking for them.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Tuple
from .validation import ValidationError

__all__ = [
    "APPROVALS",
    "BARE_CLAIMS",
    "EVIDENCE_KINDS",
    "EVENT_KINDS",
    "FRESH_LIMIT_SECONDS",
    "HELD_EVIDENCE",
    "PLAIN_EXPLANATION",
    "SOURCES",
    "STAGES",
    "TRANSITIONS",
    "TRANSPORTS",
    "USAGE",
    "WEBHOOK_DOORS_SCHEMA",
    "WEBHOOK_DOORS_SLICE",
    "EventStanding",
    "InboundEvent",
    "ProposalDraft",
    "SourceEntry",
    "SourceRegistry",
    "default_registry",
    "derive_standing",
    "format_event",
    "format_events",
    "format_source",
    "format_sources",
    "propose_proposal",
]

WEBHOOK_DOORS_SLICE = "M-250"
WEBHOOK_DOORS_SCHEMA = "mythic.webhook_doors/1"

PLAIN_EXPLANATION = (
    "Inbound events enter a campaign only as a recorded "
    "event with provenance and a timestamp - a PR opened, "
    "an issue filed. An event that is absent reads as "
    "unknown and one past the fresh limit reads as stale, "
    "never as a fact, and the doors only propose "
    "campaigns: nothing builds unbidden - a human approves "
    "and carries out any build."
)
USAGE = (
    "Record each inbound event against its source and "
    "event; read its derived standing before letting it "
    "propose a campaign; propose any campaign only as a "
    "proposal and let a human approve and carry it out. "
    "Nothing builds unbidden."
)

STAGES = ("received", "recorded", "checked", "held")
TRANSITIONS = {
    "received": ("recorded",),
    "recorded": ("checked",),
    "checked": ("held",),
    "held": (),
}
EVENT_KINDS = ("pr_opened", "issue_filed", "pr_merged",
               "issue_closed", "unknown")
FRESH_LIMIT_SECONDS = 600
HELD_EVIDENCE = ("payload_ref", "delivery_ref", "journal_ref", "keeper_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
EVIDENCE_KINDS = HELD_EVIDENCE + BARE_CLAIMS
APPROVALS = ("pending", "approved")
TRANSPORTS = ("recorded",)


@dataclass(frozen=True)
class SourceEntry:
    id: str
    label: str
    event_word: str
    transport: str
    reason: str

    def validate(self) -> None:
        for name in ("id", "label", "event_word", "transport", "reason"):
            if not str(getattr(self, name)).strip():
                raise ValidationError(f"webhook source entry missing {name}")
        if self.transport != "recorded":
            raise ValidationError(
                "webhook events are recorded data only, "
                "never live listeners; refused "
                f"transport: {self.transport}")


SOURCES = (
    SourceEntry("github", "GitHub", "event", "recorded",
                "GitHub, when it supplies an event for the record"),
    SourceEntry("gitlab", "GitLab", "event", "recorded",
                "a webhook telling supplied by GitLab and recorded as data"),
    SourceEntry("bitbucket", "Bitbucket", "event", "recorded",
                "a webhook telling supplied by Bitbucket and recorded as data"),
    SourceEntry("generic", "Generic webhook", "delivery", "recorded",
                "any other host's webhook telling, recorded in the generic shape"),
)


class SourceRegistry:
    def __init__(self, entries: Iterable[SourceEntry] = SOURCES):
        self._entries: Dict[str, SourceEntry] = {}
        for entry in entries:
            entry.validate()
            if entry.id in self._entries:
                raise ValidationError(f"duplicate webhook source: {entry.id}")
            self._entries[entry.id] = entry

    def get(self, source_id: str) -> SourceEntry:
        try:
            return self._entries[source_id]
        except KeyError:
            raise ValidationError(f"unknown webhook source: {source_id}") from None

    def ids(self) -> Tuple[str, ...]:
        return tuple(self._entries)

    def entries(self) -> Tuple[SourceEntry, ...]:
        return tuple(self._entries.values())


def default_registry() -> SourceRegistry:
    return SourceRegistry()


@dataclass(frozen=True)
class InboundEvent:
    source: str
    event: str
    kind: str
    title: str
    subject: str
    observed_at: str
    age_seconds: int
    stages: Tuple[str, ...]
    claims: Tuple[str, ...]

    def validate(self, registry: Optional[SourceRegistry] = None) -> None:
        (registry or default_registry()).get(self.source)
        if not self.event.strip():
            raise ValidationError("event names no event")
        if self.kind not in EVENT_KINDS:
            raise ValidationError(f"unknown webhook event kind: {self.kind}")
        if not self.title.strip():
            raise ValidationError("event names no title")
        if not str(self.observed_at).strip():
            raise ValidationError("event names no observed time")
        if (not isinstance(self.age_seconds, int)
                or isinstance(self.age_seconds, bool)
                or self.age_seconds < 0):
            raise ValidationError(
                "event age is not a non-negative whole number")
        for kind in self.claims:
            if kind not in EVIDENCE_KINDS:
                raise ValidationError(f"unknown webhook evidence kind: {kind}")


@dataclass(frozen=True)
class EventStanding:
    held: bool
    stage: str
    freshness: str
    gaps: Tuple[str, ...]


def derive_standing(event: InboundEvent,
                    registry: Optional[SourceRegistry] = None) -> EventStanding:
    event.validate(registry)
    gaps = []
    stages = event.stages
    if not stages or stages[0] != STAGES[0]:
        gaps.append("event does not open at received")
        stages = stages or ()
    else:
        for prev, nxt in zip(stages, stages[1:]):
            if nxt not in TRANSITIONS.get(prev, ()):
                gaps.append(f"stage step {prev} -> {nxt} not in the walk")
    stage = stages[-1] if stages else "unseen"
    if stage != "held":
        gaps.append(f"event stands at {stage}, not held")
    if event.age_seconds > FRESH_LIMIT_SECONDS:
        freshness = "stale"
        gaps.append(
            f"event is stale: age {event.age_seconds}s over "
            f"the fresh limit {FRESH_LIMIT_SECONDS}s")
    elif not stages:
        freshness = "unknown"
    else:
        freshness = "current"
    if event.kind == "unknown":
        gaps.append("event does not know its kind")
    if not event.subject.strip():
        gaps.append("event names no subject")
    held_kinds = [c for c in event.claims if c in HELD_EVIDENCE]
    bare = [c for c in event.claims if c in BARE_CLAIMS]
    if not held_kinds:
        gaps.append("event rests on no held evidence")
    if bare and not held_kinds:
        gaps.append("event rests on bare claims only: " + ", ".join(bare))
    return EventStanding(held=not gaps, stage=stage,
                         freshness=freshness, gaps=tuple(gaps))


@dataclass(frozen=True)
class ProposalDraft:
    campaign: str
    source: str
    event: str
    proposal: str
    approval: str = "pending"
    applied: bool = False

    def validate(self) -> None:
        if not self.campaign.strip():
            raise ValidationError("proposal names no campaign")
        if not self.source.strip():
            raise ValidationError("proposal names no source")
        if not self.event.strip():
            raise ValidationError("proposal names no event")
        if not self.proposal.strip():
            raise ValidationError("proposal proposes nothing")
        if self.approval not in APPROVALS:
            raise ValidationError(
                "campaign proposals are by approval only; refused "
                f"approval: {self.approval}")
        if self.applied:
            raise ValidationError(
                "campaign proposals are proposals only; a proposal is "
                "never applied or built here")


def propose_proposal(campaign: str, source: str, event: str, proposal: str,
                     approval: str = "pending") -> ProposalDraft:
    draft = ProposalDraft(campaign=campaign, source=source,
                          event=event, proposal=proposal,
                          approval=approval)
    draft.validate()
    return draft


def format_source(entry: SourceEntry) -> str:
    return f"{entry.label} ({entry.id}): {entry.event_word} via {entry.transport} - {entry.reason}"


def format_sources(registry: Optional[SourceRegistry] = None) -> str:
    reg = registry or default_registry()
    return "\n".join(format_source(e) for e in reg.entries())


def format_event(event: InboundEvent,
                 registry: Optional[SourceRegistry] = None) -> str:
    standing = derive_standing(event, registry)
    state = "held as recorded" if standing.held else "open: " + "; ".join(standing.gaps)
    return (f"{event.source}/{event.event}: kind {event.kind}, "
            f"{event.title} [{standing.freshness}] - {state}")


def format_events(events: Iterable[InboundEvent],
                  registry: Optional[SourceRegistry] = None) -> str:
    return "\n".join(format_event(e, registry) for e in events)
