"""Issue trackers beyond git hosts (roadmap slice M-248) - pure layer.

Part X - Bridges. The roadmap words: **Linear/Jira-class bridges
as MCP-first integrations, read-mostly, write by approval.**

What this layer holds, as data:

* An **issue tracker registry** held as data - one entry per
  tracker (linear, jira, generic_mcp): its id, its plain label,
  the word that tracker gives a single issue, the transport it is
  reached by, and why the entry stands, in plain words. Every
  entry is reached MCP-first (transport 'mcp'); a tracker the
  registry does not hold refuses BY NAME; a duplicated,
  half-written, or non-MCP entry refuses whole. A new tracker
  needs no code change.
* An **issue record** holds, for one tracker, one issue as a
  fact read from it: the issue key, its title, its state, the
  stages it has walked, and the claims it rests on, by kind. Its
  standing is DERIVED at call time against the explicit fact walk
  held as data (STAGES, TRANSITIONS): seen, fetched, read, held.
  A record resting on a bare claim (feeling, memory, assertion,
  summary) instead of held evidence (issue_ref, comment_ref,
  tracker_ref, mcp_ref), naming no issue or no title, or not
  reached at held stands open, named in its gaps. The bridges
  are read-mostly: reading is the ordinary road.
* A **write draft** is the only shape a proposed tracker write
  may take. A draft is never executed by this layer: it stands
  at approval \"pending\" by default, may be marked \"approved\"
  by a human, and is never applied here - writes happen only by
  approval, outside this layer. A proposal asking to be executed
  instead of drafted, or carrying any other approval word,
  refuses BY NAME.

Honesty rule, made code: an issue is a fact only when it rests
on held evidence. A record standing at held on bare claims
alone stands open by construction - the bridge will not dress
a claim up as an issue.

Honest boundary: this layer holds registry entries, issue
records, derived standings and write drafts as data. It calls
no tracker API, fetches no issue, writes nothing to any tracker
and probes no network; the agent layer owns holding a session's
records and speaking to a tracker on the live MCP roads.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Tuple
from .validation import ValidationError

__all__ = [
    "BARE_CLAIMS",
    "EVIDENCE_KINDS",
    "HELD_EVIDENCE",
    "ISSUE_STATES",
    "ISSUE_TRACKER_SCHEMA",
    "ISSUE_TRACKER_SLICE",
    "PLAIN_EXPLANATION",
    "STAGES",
    "TRACKERS",
    "TRANSITIONS",
    "USAGE",
    "IssueRecord",
    "IssueStanding",
    "TrackerEntry",
    "TrackerRegistry",
    "WriteDraft",
    "default_registry",
    "derive_standing",
    "format_record",
    "format_records",
    "format_tracker",
    "format_trackers",
    "propose_write",
]

ISSUE_TRACKER_SLICE = "M-248"
ISSUE_TRACKER_SCHEMA = "mythic.issue_trackers/1"

PLAIN_EXPLANATION = (
    "Issues enter the session as facts only when they rest on "
    "held evidence - an issue reference, a comment reference, a "
    "tracker reference. Trackers are reached MCP-first and read "
    "mostly; any write is proposed only as a draft and happens "
    "only by approval."
)
USAGE = (
    "Hold each tracker issue as a record against its tracker; "
    "read its derived standing before treating it as a fact; "
    "propose any tracker write as a draft and let a human "
    "approve and carry it out."
)

STAGES = ("seen", "fetched", "read", "held")
TRANSITIONS = {
    "seen": ("fetched",),
    "fetched": ("read",),
    "read": ("held",),
    "held": (),
}
ISSUE_STATES = ("open", "in_progress", "blocked", "done", "unknown")
HELD_EVIDENCE = ("issue_ref", "comment_ref", "tracker_ref", "mcp_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
EVIDENCE_KINDS = HELD_EVIDENCE + BARE_CLAIMS
APPROVALS = ("pending", "approved")


@dataclass(frozen=True)
class TrackerEntry:
    id: str
    label: str
    issue_word: str
    transport: str
    reason: str

    def validate(self) -> None:
        for name in ("id", "label", "issue_word", "transport", "reason"):
            if not str(getattr(self, name)).strip():
                raise ValidationError(f"issue tracker entry missing {name}")
        if self.transport != "mcp":
            raise ValidationError(
                "issue tracker bridges are MCP-first; refused "
                f"transport: {self.transport}")


TRACKERS = (
    TrackerEntry("linear", "Linear", "issue", "mcp",
                 "the Linear-class tracker, reached MCP-first and read mostly"),
    TrackerEntry("jira", "Jira", "ticket", "mcp",
                 "the Jira-class tracker, reached MCP-first and read mostly"),
    TrackerEntry("generic_mcp", "Generic MCP tracker", "work item", "mcp",
                 "any further tracker that speaks MCP, held to the same evidence and approval law"),
)


class TrackerRegistry:
    def __init__(self, entries: Iterable[TrackerEntry] = TRACKERS):
        self._entries: Dict[str, TrackerEntry] = {}
        for entry in entries:
            entry.validate()
            if entry.id in self._entries:
                raise ValidationError(f"duplicate issue tracker: {entry.id}")
            self._entries[entry.id] = entry

    def get(self, tracker_id: str) -> TrackerEntry:
        try:
            return self._entries[tracker_id]
        except KeyError:
            raise ValidationError(f"unknown issue tracker: {tracker_id}") from None

    def ids(self) -> Tuple[str, ...]:
        return tuple(self._entries)

    def entries(self) -> Tuple[TrackerEntry, ...]:
        return tuple(self._entries.values())


def default_registry() -> TrackerRegistry:
    return TrackerRegistry()


@dataclass(frozen=True)
class IssueRecord:
    tracker: str
    issue_key: str
    title: str
    state: str
    stages: Tuple[str, ...]
    claims: Tuple[str, ...]

    def validate(self, registry: Optional[TrackerRegistry] = None) -> None:
        (registry or default_registry()).get(self.tracker)
        if not self.issue_key.strip():
            raise ValidationError("issue record names no issue")
        if not self.title.strip():
            raise ValidationError("issue record names no title")
        if self.state not in ISSUE_STATES:
            raise ValidationError(f"unknown issue state: {self.state}")
        for kind in self.claims:
            if kind not in EVIDENCE_KINDS:
                raise ValidationError(f"unknown issue evidence kind: {kind}")


@dataclass(frozen=True)
class IssueStanding:
    held: bool
    stage: str
    gaps: Tuple[str, ...]


def derive_standing(record: IssueRecord,
                    registry: Optional[TrackerRegistry] = None) -> IssueStanding:
    record.validate(registry)
    gaps = []
    stages = record.stages
    if not stages or stages[0] != STAGES[0]:
        gaps.append("record does not open at seen")
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
    if not held_kinds:
        gaps.append("record rests on no held evidence")
    if bare and not held_kinds:
        gaps.append("record rests on bare claims only: " + ", ".join(bare))
    return IssueStanding(held=not gaps, stage=stage, gaps=tuple(gaps))


@dataclass(frozen=True)
class WriteDraft:
    tracker: str
    issue_key: str
    change: str
    approval: str = "pending"
    applied: bool = False

    def validate(self, registry: Optional[TrackerRegistry] = None) -> None:
        (registry or default_registry()).get(self.tracker)
        if not self.issue_key.strip():
            raise ValidationError("write draft names no issue")
        if not self.change.strip():
            raise ValidationError("write draft proposes no change")
        if self.approval not in APPROVALS:
            raise ValidationError(
                "tracker writes are by approval only; refused "
                f"approval: {self.approval}")
        if self.applied:
            raise ValidationError(
                "tracker writes are drafts only; a draft is never applied here")


def propose_write(tracker: str, issue_key: str, change: str,
                  approval: str = "pending",
                  registry: Optional[TrackerRegistry] = None) -> WriteDraft:
    draft = WriteDraft(tracker=tracker, issue_key=issue_key,
                       change=change, approval=approval)
    draft.validate(registry)
    return draft


def format_tracker(entry: TrackerEntry) -> str:
    return f"{entry.label} ({entry.id}): {entry.issue_word} via {entry.transport} - {entry.reason}"


def format_trackers(registry: Optional[TrackerRegistry] = None) -> str:
    reg = registry or default_registry()
    return "\n".join(format_tracker(e) for e in reg.entries())


def format_record(record: IssueRecord,
                  registry: Optional[TrackerRegistry] = None) -> str:
    standing = derive_standing(record, registry)
    state = "held as fact" if standing.held else "open: " + "; ".join(standing.gaps)
    return (f"{record.tracker}/{record.issue_key}: {record.title} "
            f"[{record.state}] - {state}")


def format_records(records: Iterable[IssueRecord],
                   registry: Optional[TrackerRegistry] = None) -> str:
    return "\n".join(format_record(r, registry) for r in records)
