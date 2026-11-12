"""The bridge permissions audit book (roadmap slice M-253) - pure layer.

Part X - Bridges. The roadmap words: **one screen listing
every bridge, its keys' home (Kista refs), its scopes,
its last use.**

What this layer holds, as data:

* A **bridge registry** held as data - one entry per
  bridge (github, gitlab, samverk, samtal): its id, its
  plain label, the word that bridge gives a single key,
  the Kista ref that names where its keys live, the
  audit standing it arrives with, and why the entry
  stands, in plain words. Every entry arrives as listed
  data (standing 'listed'); a bridge the registry does
  not hold refuses BY NAME; a duplicated, half-written,
  or granted entry refuses whole. A new bridge needs no
  code change.
* An **audit record** holds, for one bridge and one
  record, one audit telling as a supplied fact: its
  scope, its title, its subject, when it was observed
  (the bridge's last use), how old the telling is in
  seconds, the stages it has walked, and the claims it
  rests on, by kind. Its standing is DERIVED at call
  time against the explicit fact walk held as data
  (STAGES, TRANSITIONS): listed, scoped, checked, held -
  and against the fresh limit held as data
  (FRESH_LIMIT_SECONDS). A record resting on a bare
  claim (feeling, memory, assertion, summary) instead
  of held evidence (kista_ref, scope_ref, journal_ref,
  keeper_ref), naming no subject, not knowing its
  scope, or older than the fresh limit stands open,
  named in its gaps. An absent record reads as unknown
  and a stale record reads as stale - never as a fact.
* An **audit report** is the only shape an audit record
  may produce. A report is never a grant by this layer:
  it stands at state "ready" by default, may be marked
  "shared" by a human, and never widens a permission on
  its own - this book lists permissions and prepares
  audit reports; a human carries out any change. A
  report asking to be sealed or locked instead of
  ready/shared, or to grant instead of report, refuses
  BY NAME.

Honesty rule, made code: a record is a fact only when
it rests on held evidence. A record standing on bare
claims alone, or past the fresh limit, stands open by
construction - this book will not dress a claim, or
yesterday's telling, up as an audited permission.

Honest boundary: this layer holds registry entries,
audit records, derived standings and audit reports as
data. It grants nothing, widens no scope, reads no key
out of Kista, calls no host API, probes no network and
writes nothing outside the session; the agent layer
owns holding a session's records and speaking for them.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Tuple
from .validation import ValidationError

__all__ = [
    "REPORT_STATES",
    "BARE_CLAIMS",
    "EVIDENCE_KINDS",
    "AUDIT_SCOPES",
    "FRESH_LIMIT_SECONDS",
    "HELD_EVIDENCE",
    "PLAIN_EXPLANATION",
    "BRIDGES",
    "STAGES",
    "TRANSITIONS",
    "STANDINGS",
    "USAGE",
    "BRIDGE_PERMISSIONS_SCHEMA",
    "BRIDGE_PERMISSIONS_SLICE",
    "AuditStanding",
    "AuditRecord",
    "AuditDraft",
    "BridgeEntry",
    "BridgeRegistry",
    "default_registry",
    "derive_standing",
    "format_record",
    "format_records",
    "format_bridge",
    "format_bridges",
    "prepare_report",
]

BRIDGE_PERMISSIONS_SLICE = "M-253"
BRIDGE_PERMISSIONS_SCHEMA = "mythic.bridge_permissions/1"

PLAIN_EXPLANATION = (
    "One screen lists every bridge, its keys' home as "
    "a Kista ref, its scopes and its last use, as a "
    "listed audit record. A record that is absent reads "
    "as unknown and one past the fresh limit reads as "
    "stale, never as a fact, and this book only prepares "
    "audit reports: a human carries out any change, and "
    "no permission is granted or widened here."
)
USAGE = (
    "Record each audit against its bridge and record; "
    "read its derived standing before letting it "
    "prepare an audit report; prepare any report only "
    "as a report and let a human carry out any change. "
    "One screen, as data first."
)

STAGES = ("listed", "scoped", "checked", "held")
TRANSITIONS = {
    "listed": ("scoped",),
    "scoped": ("checked",),
    "checked": ("held",),
    "held": (),
}
AUDIT_SCOPES = ("read_only", "write", "propose_only", "full", "unknown")
FRESH_LIMIT_SECONDS = 600
HELD_EVIDENCE = ("kista_ref", "scope_ref", "journal_ref", "keeper_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
EVIDENCE_KINDS = HELD_EVIDENCE + BARE_CLAIMS
REPORT_STATES = ("ready", "shared")
STANDINGS = ("listed",)


@dataclass(frozen=True)
class BridgeEntry:
    id: str
    label: str
    item_word: str
    key_home: str
    standing: str
    reason: str

    def validate(self) -> None:
        for name in ("id", "label", "item_word", "key_home", "standing", "reason"):
            if not str(getattr(self, name)).strip():
                raise ValidationError(f"bridge entry missing {name}")
        if self.standing != "listed":
            raise ValidationError(
                "bridge permissions are listed data "
                "only, never granted or widened here; "
                f"refused standing: {self.standing}")


BRIDGES = (
    BridgeEntry("github", "GitHub Bridge", "key", "kista:github", "listed",
                "the host bridge: its token lives in Kista, named by ref, never in the open"),
    BridgeEntry("gitlab", "GitLab Bridge", "key", "kista:gitlab", "listed",
                "the second host bridge, held to the same Kista rule as the first"),
    BridgeEntry("samverk", "Samverk Bridge", "ref", "kista:samverk", "listed",
                "the sibling-campaign bridge: its exchanges ride on a Kista-held ref"),
    BridgeEntry("samtal", "Samtal Bridge", "ref", "kista:samtal", "listed",
                "the longhouse bridge: its dispatches carry no key in the open, the ref names its home in Kista"),
)


class BridgeRegistry:
    def __init__(self, entries: Iterable[BridgeEntry] = BRIDGES):
        self._entries: Dict[str, BridgeEntry] = {}
        for entry in entries:
            entry.validate()
            if entry.id in self._entries:
                raise ValidationError(f"duplicate bridge: {entry.id}")
            self._entries[entry.id] = entry

    def get(self, bridge_id: str) -> BridgeEntry:
        try:
            return self._entries[bridge_id]
        except KeyError:
            raise ValidationError(f"unknown bridge: {bridge_id}") from None

    def ids(self) -> Tuple[str, ...]:
        return tuple(self._entries)

    def entries(self) -> Tuple[BridgeEntry, ...]:
        return tuple(self._entries.values())


def default_registry() -> BridgeRegistry:
    return BridgeRegistry()


@dataclass(frozen=True)
class AuditRecord:
    bridge: str
    record: str
    scope: str
    title: str
    subject: str
    observed_at: str
    age_seconds: int
    stages: Tuple[str, ...]
    claims: Tuple[str, ...]

    def validate(self, registry: Optional[BridgeRegistry] = None) -> None:
        (registry or default_registry()).get(self.bridge)
        if not self.record.strip():
            raise ValidationError("record names no record")
        if self.scope not in AUDIT_SCOPES:
            raise ValidationError(f"unknown audit record scope: {self.scope}")
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
                raise ValidationError(f"unknown audit evidence kind: {kind}")


@dataclass(frozen=True)
class AuditStanding:
    held: bool
    stage: str
    freshness: str
    gaps: Tuple[str, ...]


def derive_standing(record: AuditRecord,
                    registry: Optional[BridgeRegistry] = None) -> AuditStanding:
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
    return AuditStanding(held=not gaps, stage=stage,
                              freshness=freshness, gaps=tuple(gaps))


@dataclass(frozen=True)
class AuditDraft:
    bridge: str
    entry: str
    record: str
    report: str
    state: str = "ready"
    granted: bool = False

    def validate(self) -> None:
        if not self.bridge.strip():
            raise ValidationError("report names no bridge")
        if not self.entry.strip():
            raise ValidationError("report names no entry")
        if not self.record.strip():
            raise ValidationError("report names no record")
        if not self.report.strip():
            raise ValidationError("audit report reports nothing")
        if self.state not in REPORT_STATES:
            raise ValidationError(
                "audit reports stand ready or shared only, "
                "never sealed or locked; refused "
                f"state: {self.state}")
        if self.granted:
            raise ValidationError(
                "audit reports are reports only; a report is "
                "never a grant here")


def prepare_report(bridge: str, entry: str, record: str, report: str,
                     state: str = "ready") -> AuditDraft:
    made = AuditDraft(bridge=bridge, entry=entry,
                           record=record, report=report,
                           state=state)
    made.validate()
    return made


def format_bridge(entry: BridgeEntry) -> str:
    return f"{entry.label} ({entry.id}): {entry.item_word} homed at {entry.key_home} in Kista, audit standing {entry.standing} - {entry.reason}"


def format_bridges(registry: Optional[BridgeRegistry] = None) -> str:
    reg = registry or default_registry()
    return "\n".join(format_bridge(e) for e in reg.entries())


def format_record(record: AuditRecord,
                  registry: Optional[BridgeRegistry] = None) -> str:
    standing = derive_standing(record, registry)
    state = "held as audited" if standing.held else "open: " + "; ".join(standing.gaps)
    return (f"{record.bridge}/{record.record}: scope {record.scope}, "
            f"{record.title} [{standing.freshness}] - {state}")


def format_records(records: Iterable[AuditRecord],
                   registry: Optional[BridgeRegistry] = None) -> str:
    return "\n".join(format_record(r, registry) for r in records)
