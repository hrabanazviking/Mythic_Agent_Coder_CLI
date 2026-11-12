"""The docs MCP pattern generalised book (roadmap slice M-252) - pure layer.

Part X - Bridges. The roadmap words: **any project's docs
MCP (like the Mojo one) attachable as a knowledge bridge
in one step.**

The pattern being generalised is the one that already
stands in this codebase: the official Mojo documentation
rides the Mojo Docs MCP connector (named in the Mojo
sight book, M-064, entry K-09, as the road a question
takes when it outgrows the distilled entries), and
docs-at-hand (M-060) already generalised that pattern
offline. This book holds the pattern itself, as data, so
any project's docs MCP can be attached the same way.

What this layer holds, as data:

* A **docs project registry** held as data - one entry
  per project (mojo, python, rust, generic): its id, its
  plain label, the word that project gives a single doc,
  the transport/endpoint shape its docs MCP rides, the
  knowledge-bridge standing it arrives with, and why the
  entry stands, in plain words. Every entry arrives as
  recorded data (bridge 'recorded'); a project the
  registry does not hold refuses BY NAME; a duplicated,
  half-written, or live-attached entry refuses whole.
  A new project needs no code change.
* An **attachment record** holds, for one project and
  one record, one attachment telling as a supplied fact:
  its scope, its title, its subject, when it was
  observed, how old the telling is in seconds, the
  stages it has walked, and the claims it rests on, by
  kind. Its standing is DERIVED at call time against
  the explicit fact walk held as data (STAGES,
  TRANSITIONS): named, described, checked, held - and
  against the fresh limit held as data
  (FRESH_LIMIT_SECONDS). A record resting on a bare
  claim (feeling, memory, assertion, summary) instead
  of held evidence (manifest_ref, endpoint_ref,
  journal_ref, keeper_ref), naming no subject, not
  knowing its scope, or older than the fresh limit
  stands open, named in its gaps. An absent record
  reads as unknown and a stale record reads as stale -
  never as a fact.
* An **attachment proposal** is the only shape an
  attachment record may produce. A proposal is never
  attached by this layer: it stands at state "ready"
  by default, may be marked "shared" by a human, and
  never carries an attachment out on its own - this
  book prepares attachment proposals; a human performs
  any real attachment. A proposal asking to be locked
  or gated instead of ready/shared, or to be attached
  instead of proposed, refuses BY NAME.

Honesty rule, made code: a record is a fact only when
it rests on held evidence. A record standing on bare
claims alone, or past the fresh limit, stands open by
construction - this book will not dress a claim, or
yesterday's telling, up as an attached bridge.

Honest boundary: this layer holds registry entries,
attachment records, derived standings and attachment
proposals as data. It attaches nothing live, calls no
host API, probes no network and writes nothing outside
the session; the agent layer owns holding a session's
records and speaking for them.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Tuple
from .validation import ValidationError

__all__ = [
    "ATTACH_STATES",
    "BARE_CLAIMS",
    "EVIDENCE_KINDS",
    "ATTACH_SCOPES",
    "FRESH_LIMIT_SECONDS",
    "HELD_EVIDENCE",
    "PLAIN_EXPLANATION",
    "PROJECTS",
    "STAGES",
    "TRANSITIONS",
    "BRIDGES",
    "USAGE",
    "DOCS_MCP_PATTERN_SCHEMA",
    "DOCS_MCP_PATTERN_SLICE",
    "AttachmentStanding",
    "AttachmentRecord",
    "AttachmentDraft",
    "ProjectEntry",
    "ProjectRegistry",
    "default_registry",
    "derive_standing",
    "format_record",
    "format_records",
    "format_project",
    "format_projects",
    "prepare_proposal",
]

DOCS_MCP_PATTERN_SLICE = "M-252"
DOCS_MCP_PATTERN_SCHEMA = "mythic.docs_mcp_pattern/1"

PLAIN_EXPLANATION = (
    "Any project's docs MCP attaches as a knowledge "
    "bridge in one step, as a recorded attachment "
    "record - the Mojo Docs MCP is the original of the "
    "pattern. A record that is absent reads as unknown "
    "and one past the fresh limit reads as stale, never "
    "as a fact, and this book only prepares attachment "
    "proposals: a human performs any real attachment, "
    "and nothing is attached live here."
)
USAGE = (
    "Record each attachment against its project and "
    "record; read its derived standing before letting "
    "it prepare an attachment proposal; prepare any "
    "attachment only as a proposal and let a human "
    "carry it out. One step, as data first."
)

STAGES = ("named", "described", "checked", "held")
TRANSITIONS = {
    "named": ("described",),
    "described": ("checked",),
    "checked": ("held",),
    "held": (),
}
ATTACH_SCOPES = ("full", "search_only", "read_only", "index_only", "unknown")
FRESH_LIMIT_SECONDS = 600
HELD_EVIDENCE = ("manifest_ref", "endpoint_ref", "journal_ref", "keeper_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
EVIDENCE_KINDS = HELD_EVIDENCE + BARE_CLAIMS
ATTACH_STATES = ("ready", "shared")
BRIDGES = ("recorded",)


@dataclass(frozen=True)
class ProjectEntry:
    id: str
    label: str
    item_word: str
    transport: str
    bridge: str
    reason: str

    def validate(self) -> None:
        for name in ("id", "label", "item_word", "transport", "bridge", "reason"):
            if not str(getattr(self, name)).strip():
                raise ValidationError(f"docs project entry missing {name}")
        if self.bridge != "recorded":
            raise ValidationError(
                "docs MCP attachments are recorded data "
                "only, never live-attached; refused "
                f"bridge: {self.bridge}")


PROJECTS = (
    ProjectEntry("mojo", "Mojo Docs", "doc", "remote_mcp", "recorded",
                 "the original pattern: the official Mojo documentation rides the Mojo Docs MCP connector"),
    ProjectEntry("python", "Python Docs", "reference", "remote_mcp", "recorded",
                 "a project's language docs served by its own docs MCP, attached the same way"),
    ProjectEntry("rust", "Rust Docs", "doc", "stdio_mcp", "recorded",
                 "a project's language docs served by a local docs MCP, attached the same way"),
    ProjectEntry("generic", "Any Project Docs", "page", "recorded_mcp", "recorded",
                 "any project's docs MCP attachable in one step, by the same pattern"),
)


class ProjectRegistry:
    def __init__(self, entries: Iterable[ProjectEntry] = PROJECTS):
        self._entries: Dict[str, ProjectEntry] = {}
        for entry in entries:
            entry.validate()
            if entry.id in self._entries:
                raise ValidationError(f"duplicate docs project: {entry.id}")
            self._entries[entry.id] = entry

    def get(self, project_id: str) -> ProjectEntry:
        try:
            return self._entries[project_id]
        except KeyError:
            raise ValidationError(f"unknown docs project: {project_id}") from None

    def ids(self) -> Tuple[str, ...]:
        return tuple(self._entries)

    def entries(self) -> Tuple[ProjectEntry, ...]:
        return tuple(self._entries.values())


def default_registry() -> ProjectRegistry:
    return ProjectRegistry()


@dataclass(frozen=True)
class AttachmentRecord:
    project: str
    record: str
    scope: str
    title: str
    subject: str
    observed_at: str
    age_seconds: int
    stages: Tuple[str, ...]
    claims: Tuple[str, ...]

    def validate(self, registry: Optional[ProjectRegistry] = None) -> None:
        (registry or default_registry()).get(self.project)
        if not self.record.strip():
            raise ValidationError("record names no record")
        if self.scope not in ATTACH_SCOPES:
            raise ValidationError(f"unknown attachment record scope: {self.scope}")
        if not self.title.strip():
            raise ValidationError("record names no title")
        if not str(self.observed_at).strip():
            raise ValidationError("record names no observed time")
        if (not isinstance(self.age_seconds, int)
                or isinstance(self.age_seconds, bool)
                or self.age_seconds < 0):
            raise ValidationError(
                "record age is not a non-negative whole number")
        for kind in self.claims:
            if kind not in EVIDENCE_KINDS:
                raise ValidationError(f"unknown attachment evidence kind: {kind}")


@dataclass(frozen=True)
class AttachmentStanding:
    held: bool
    stage: str
    freshness: str
    gaps: Tuple[str, ...]


def derive_standing(record: AttachmentRecord,
                    registry: Optional[ProjectRegistry] = None) -> AttachmentStanding:
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
    if record.age_seconds > FRESH_LIMIT_SECONDS:
        freshness = "stale"
        gaps.append(
            f"record is stale: age {record.age_seconds}s over "
            f"the fresh limit {FRESH_LIMIT_SECONDS}s")
    elif not stages:
        freshness = "unknown"
    else:
        freshness = "current"
    if record.scope == "unknown":
        gaps.append("record does not know its scope")
    if not record.subject.strip():
        gaps.append("record names no subject")
    held_kinds = [c for c in record.claims if c in HELD_EVIDENCE]
    bare = [c for c in record.claims if c in BARE_CLAIMS]
    if not held_kinds:
        gaps.append("record rests on no held evidence")
    if bare and not held_kinds:
        gaps.append("record rests on bare claims only: " + ", ".join(bare))
    return AttachmentStanding(held=not gaps, stage=stage,
                              freshness=freshness, gaps=tuple(gaps))


@dataclass(frozen=True)
class AttachmentDraft:
    bridge: str
    project: str
    record: str
    proposal: str
    state: str = "ready"
    attached: bool = False

    def validate(self) -> None:
        if not self.bridge.strip():
            raise ValidationError("proposal names no bridge")
        if not self.project.strip():
            raise ValidationError("proposal names no project")
        if not self.record.strip():
            raise ValidationError("proposal names no record")
        if not self.proposal.strip():
            raise ValidationError("attachment proposal proposes nothing")
        if self.state not in ATTACH_STATES:
            raise ValidationError(
                "attachment proposals stand ready or shared only, "
                "never gated or locked; refused "
                f"state: {self.state}")
        if self.attached:
            raise ValidationError(
                "attachment proposals are proposals only; a proposal is "
                "never attached here")


def prepare_proposal(bridge: str, project: str, record: str, proposal: str,
                     state: str = "ready") -> AttachmentDraft:
    made = AttachmentDraft(bridge=bridge, project=project,
                           record=record, proposal=proposal,
                           state=state)
    made.validate()
    return made


def format_project(entry: ProjectEntry) -> str:
    return f"{entry.label} ({entry.id}): {entry.item_word} as a {entry.bridge} knowledge bridge via {entry.transport} - {entry.reason}"


def format_projects(registry: Optional[ProjectRegistry] = None) -> str:
    reg = registry or default_registry()
    return "\n".join(format_project(e) for e in reg.entries())


def format_record(record: AttachmentRecord,
                  registry: Optional[ProjectRegistry] = None) -> str:
    standing = derive_standing(record, registry)
    state = "held as bridge" if standing.held else "open: " + "; ".join(standing.gaps)
    return (f"{record.project}/{record.record}: scope {record.scope}, "
            f"{record.title} [{standing.freshness}] - {state}")


def format_records(records: Iterable[AttachmentRecord],
                   registry: Optional[ProjectRegistry] = None) -> str:
    return "\n".join(format_record(r, registry) for r in records)
