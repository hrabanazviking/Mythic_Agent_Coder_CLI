"""The export everything book (roadmap slice M-251) - pure layer.

Part X - Bridges. The roadmap words: **sessions, campaigns,
memories, and configs export in open formats; leaving is as
easy as arriving (the Interoperability Principle).**

What this layer holds, as data:

* An **export kind registry** held as data - one entry
  per kind (sessions, campaigns, memories, configs): its id,
  its plain label, the word that kind gives a single thing,
  the open format that kind leaves in, and why the entry
  stands, in plain words. Every entry arrives as open data
  (openness 'open'); a kind the registry does not hold
  refuses BY NAME; a duplicated, half-written, or
  proprietary/locked entry refuses whole. A new kind needs
  no code change.
* An **export record** holds, for one kind and one record,
  one thing to export as a supplied fact: its scope, its
  title, its subject, when it was observed, how old the
  telling is in seconds, the stages it has walked, and the
  claims it rests on, by kind. Its standing is DERIVED at
  call time against the explicit fact walk held as data
  (STAGES, TRANSITIONS): listed, gathered, checked, held
  - and against the fresh limit held as data
  (FRESH_LIMIT_SECONDS). A record resting on a bare claim
  (feeling, memory, assertion, summary) instead of held
  evidence (content_ref, manifest_ref, journal_ref,
  keeper_ref), naming no subject, not knowing its scope, or
  older than the fresh limit stands open, named in its
  gaps. An absent record reads as unknown and a stale record
  reads as stale - never as a fact.
* An **export draft** is the only shape an export record
  may produce. A draft is never exported by this layer: it
  stands at state "ready" by default, may be marked
  "shared" by a human, and never carries an export out on
  its own - this book prepares export drafts; a human
  carries out any export. A draft asking to be locked or
  gated instead of ready/shared, or to be exported instead
  of drafted, refuses BY NAME.

Honesty rule, made code: a record is a fact only when it
rests on held evidence. A record standing on bare claims
alone, or past the fresh limit, stands open by construction
- this book will not dress a claim, or yesterday's telling,
up as an export.

Governing principle, made code: leaving is as easy as
arriving. Exports are complete, in open formats, and never
gated or locked: a kind entry that would leave in a
proprietary or locked format refuses whole, by name, and
no draft here holds data hostage.

Honest boundary: this layer holds registry entries, export
records, derived standings and export drafts as data.
It performs no export, calls no host API, probes no
network and writes nothing outside the session; the agent
layer owns holding a session's records and speaking
for them.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Tuple
from .validation import ValidationError

__all__ = [
    "EXPORT_STATES",
    "BARE_CLAIMS",
    "EVIDENCE_KINDS",
    "RECORD_SCOPES",
    "FRESH_LIMIT_SECONDS",
    "HELD_EVIDENCE",
    "PLAIN_EXPLANATION",
    "KINDS",
    "STAGES",
    "TRANSITIONS",
    "OPENNESSES",
    "USAGE",
    "EXPORT_EVERYTHING_SCHEMA",
    "EXPORT_EVERYTHING_SLICE",
    "ExportStanding",
    "ExportRecord",
    "ExportDraft",
    "KindEntry",
    "KindRegistry",
    "default_registry",
    "derive_standing",
    "format_record",
    "format_records",
    "format_kind",
    "format_kinds",
    "prepare_draft",
]

EXPORT_EVERYTHING_SLICE = "M-251"
EXPORT_EVERYTHING_SCHEMA = "mythic.export_everything/1"

PLAIN_EXPLANATION = (
    "Sessions, campaigns, memories and configs leave "
    "only as a recorded record in an open format - "
    "JSON, Markdown or YAML. A record that is absent "
    "reads as unknown and one past the fresh limit "
    "reads as stale, never as a fact, and this book "
    "only prepares export drafts: leaving is as easy "
    "as arriving - a human carries out any export, "
    "and nothing is held hostage or locked."
)
USAGE = (
    "Record each thing to export against its kind "
    "and record; read its derived standing before "
    "letting it prepare an export draft; prepare "
    "any export only as a draft and let a human "
    "carry it out. Leaving is as easy as arriving."
)

STAGES = ("listed", "gathered", "checked", "held")
TRANSITIONS = {
    "listed": ("gathered",),
    "gathered": ("checked",),
    "checked": ("held",),
    "held": (),
}
RECORD_SCOPES = ("full", "incremental", "snapshot", "archive", "unknown")
FRESH_LIMIT_SECONDS = 600
HELD_EVIDENCE = ("content_ref", "manifest_ref", "journal_ref", "keeper_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
EVIDENCE_KINDS = HELD_EVIDENCE + BARE_CLAIMS
EXPORT_STATES = ("ready", "shared")
OPENNESSES = ("open",)


@dataclass(frozen=True)
class KindEntry:
    id: str
    label: str
    item_word: str
    format_name: str
    openness: str
    reason: str

    def validate(self) -> None:
        for name in ("id", "label", "item_word", "format_name", "openness", "reason"):
            if not str(getattr(self, name)).strip():
                raise ValidationError(f"export kind entry missing {name}")
        if self.openness != "open":
            raise ValidationError(
                "exports are open formats only, never "
                "proprietary or locked; refused "
                f"openness: {self.openness}")


KINDS = (
    KindEntry("sessions", "Sessions", "session", "JSON", "open",
              "sessions leave as JSON, readable anywhere"),
    KindEntry("campaigns", "Campaigns", "campaign", "Markdown", "open",
              "campaigns leave as Markdown, readable anywhere"),
    KindEntry("memories", "Memories", "memory", "Markdown", "open",
              "memories leave as Markdown, readable anywhere"),
    KindEntry("configs", "Configs", "config", "YAML", "open",
              "configs leave as YAML, readable anywhere"),
)


class KindRegistry:
    def __init__(self, entries: Iterable[KindEntry] = KINDS):
        self._entries: Dict[str, KindEntry] = {}
        for entry in entries:
            entry.validate()
            if entry.id in self._entries:
                raise ValidationError(f"duplicate export kind: {entry.id}")
            self._entries[entry.id] = entry

    def get(self, kind_id: str) -> KindEntry:
        try:
            return self._entries[kind_id]
        except KeyError:
            raise ValidationError(f"unknown export kind: {kind_id}") from None

    def ids(self) -> Tuple[str, ...]:
        return tuple(self._entries)

    def entries(self) -> Tuple[KindEntry, ...]:
        return tuple(self._entries.values())


def default_registry() -> KindRegistry:
    return KindRegistry()


@dataclass(frozen=True)
class ExportRecord:
    kind: str
    record: str
    scope: str
    title: str
    subject: str
    observed_at: str
    age_seconds: int
    stages: Tuple[str, ...]
    claims: Tuple[str, ...]

    def validate(self, registry: Optional[KindRegistry] = None) -> None:
        (registry or default_registry()).get(self.kind)
        if not self.record.strip():
            raise ValidationError("record names no record")
        if self.scope not in RECORD_SCOPES:
            raise ValidationError(f"unknown export record scope: {self.scope}")
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
                raise ValidationError(f"unknown export evidence kind: {kind}")


@dataclass(frozen=True)
class ExportStanding:
    held: bool
    stage: str
    freshness: str
    gaps: Tuple[str, ...]


def derive_standing(record: ExportRecord,
                    registry: Optional[KindRegistry] = None) -> ExportStanding:
    record.validate(registry)
    gaps = []
    stages = record.stages
    if not stages or stages[0] != STAGES[0]:
        gaps.append("record does not open at listed")
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
    return ExportStanding(held=not gaps, stage=stage,
                          freshness=freshness, gaps=tuple(gaps))


@dataclass(frozen=True)
class ExportDraft:
    bundle: str
    kind: str
    record: str
    draft: str
    state: str = "ready"
    exported: bool = False

    def validate(self) -> None:
        if not self.bundle.strip():
            raise ValidationError("draft names no bundle")
        if not self.kind.strip():
            raise ValidationError("draft names no kind")
        if not self.record.strip():
            raise ValidationError("draft names no record")
        if not self.draft.strip():
            raise ValidationError("export draft drafts nothing")
        if self.state not in EXPORT_STATES:
            raise ValidationError(
                "export drafts stand ready or shared only, "
                "never gated or locked; refused "
                f"state: {self.state}")
        if self.exported:
            raise ValidationError(
                "export drafts are drafts only; a draft is "
                "never exported here")


def prepare_draft(bundle: str, kind: str, record: str, draft: str,
                  state: str = "ready") -> ExportDraft:
    made = ExportDraft(bundle=bundle, kind=kind,
                       record=record, draft=draft,
                       state=state)
    made.validate()
    return made


def format_kind(entry: KindEntry) -> str:
    return f"{entry.label} ({entry.id}): {entry.item_word} as {entry.format_name} via {entry.openness} - {entry.reason}"


def format_kinds(registry: Optional[KindRegistry] = None) -> str:
    reg = registry or default_registry()
    return "\n".join(format_kind(e) for e in reg.entries())


def format_record(record: ExportRecord,
                  registry: Optional[KindRegistry] = None) -> str:
    standing = derive_standing(record, registry)
    state = "held as open" if standing.held else "open: " + "; ".join(standing.gaps)
    return (f"{record.kind}/{record.record}: scope {record.scope}, "
            f"{record.title} [{standing.freshness}] - {state}")


def format_records(records: Iterable[ExportRecord],
                   registry: Optional[KindRegistry] = None) -> str:
    return "\n".join(format_record(r, registry) for r in records)
