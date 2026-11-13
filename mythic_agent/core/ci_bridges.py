"""CI bridges (roadmap slice M-247) - pure layer.

Part X - Bridges. The roadmap words: **read CI results as facts into
the session; propose workflow changes only as drafts (and
manual-dispatch by default on Volmarr's repos, M-227).**

What this layer holds, as data:

* A **CI provider registry** held as data - one entry per provider
  (github_actions, gitlab_ci, bitbucket_pipelines, local_manual):
  its id, its plain label, the word that provider gives a single
  run, and why the entry stands, in plain words. A provider the
  registry does not hold refuses BY NAME; a duplicated or
  half-written entry refuses whole. A new provider needs no code
  change.
* A **CI run record** holds, for one provider, one workflow run as
  a fact: the workflow, the ref it ran on, its conclusion, the
  stages it has walked, and the claims it rests on, by kind. Its
  standing is DERIVED at call time against the explicit fact walk
  held as data (STAGES, TRANSITIONS): seen, fetched, read, held.
  A record resting on a bare claim (feeling, memory, assertion,
  summary) instead of held evidence (run_ref, log_ref,
  artifact_ref, provider_ref), naming no workflow, or not reached
  at held stands open, named in its gaps.
* A **workflow draft** is the only shape a proposed workflow change
  may take. A draft is never applied by this layer: its standing is
  always draft, and on Volmarr's repos its trigger defaults to
  manual dispatch (workflow_dispatch, the M-227 law). A proposal
  asking for automatic triggers on his repos, or asking to be
  applied rather than drafted, refuses BY NAME.

Honesty rule, made code: a CI result is a fact only when it rests
on held evidence. A record standing at held on bare claims alone
stands open by construction - the bridge will not dress a claim up
as a result.

Honest boundary: this layer holds registry entries, run records,
derived standings and drafts as data. It calls no CI API, fetches
no run, changes no workflow and dispatches nothing; the agent
layer owns holding a session's records and speaking to a provider
on the live roads.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Tuple
from .validation import ValidationError

__all__ = [
    "BARE_CLAIMS",
    "CI_BRIDGE_SCHEMA",
    "CI_BRIDGE_SLICE",
    "CONCLUSIONS",
    "EVIDENCE_KINDS",
    "HELD_EVIDENCE",
    "PLAIN_EXPLANATION",
    "PROVIDERS",
    "STAGES",
    "TRANSITIONS",
    "USAGE",
    "CIRecord",
    "CIStanding",
    "ProviderEntry",
    "ProviderRegistry",
    "WorkflowDraft",
    "default_registry",
    "derive_standing",
    "format_provider",
    "format_providers",
    "format_record",
    "format_records",
    "propose_draft",
]

CI_BRIDGE_SLICE = "M-247"
CI_BRIDGE_SCHEMA = "mythic.ci_bridges/1"

PLAIN_EXPLANATION = (
    "CI results enter the session as facts only when they rest on "
    "held evidence - a run reference, a log reference, an artifact "
    "reference. Workflow changes are proposed only as drafts, and "
    "on Volmarr's repos a draft dispatches manually by default."
)
USAGE = (
    "Hold each CI run as a record against its provider; read its "
    "derived standing before treating it as a fact; propose any "
    "workflow change as a draft and let a human apply it."
)

STAGES = ("seen", "fetched", "read", "held")
TRANSITIONS = {
    "seen": ("fetched",),
    "fetched": ("read",),
    "read": ("held",),
    "held": (),
}
CONCLUSIONS = ("passed", "failed", "cancelled", "running", "queued", "unknown")
HELD_EVIDENCE = ("run_ref", "log_ref", "artifact_ref", "provider_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
EVIDENCE_KINDS = HELD_EVIDENCE + BARE_CLAIMS


@dataclass(frozen=True)
class ProviderEntry:
    id: str
    label: str
    run_word: str
    reason: str

    def validate(self) -> None:
        for name in ("id", "label", "run_word", "reason"):
            if not str(getattr(self, name)).strip():
                raise ValidationError(f"ci provider entry missing {name}")


PROVIDERS = (
    ProviderEntry("github_actions", "GitHub Actions", "workflow run",
                  "the CI of the hosts the forge already works on"),
    ProviderEntry("gitlab_ci", "GitLab CI", "pipeline",
                  "the CI standing beside the GitLab host entry"),
    ProviderEntry("bitbucket_pipelines", "Bitbucket Pipelines", "pipeline",
                  "the CI standing beside the Bitbucket host entry"),
    ProviderEntry("local_manual", "Local manual run", "run",
                  "a run walked by hand on our own machines, held to the same evidence law"),
)


class ProviderRegistry:
    def __init__(self, entries: Iterable[ProviderEntry] = PROVIDERS):
        self._entries: Dict[str, ProviderEntry] = {}
        for entry in entries:
            entry.validate()
            if entry.id in self._entries:
                raise ValidationError(f"duplicate ci provider: {entry.id}")
            self._entries[entry.id] = entry

    def get(self, provider_id: str) -> ProviderEntry:
        try:
            return self._entries[provider_id]
        except KeyError:
            raise ValidationError(f"unknown ci provider: {provider_id}") from None

    def ids(self) -> Tuple[str, ...]:
        return tuple(self._entries)

    def entries(self) -> Tuple[ProviderEntry, ...]:
        return tuple(self._entries.values())


def default_registry() -> ProviderRegistry:
    return ProviderRegistry()


@dataclass(frozen=True)
class CIRecord:
    provider: str
    workflow: str
    ref: str
    conclusion: str
    stages: Tuple[str, ...]
    claims: Tuple[str, ...]

    def validate(self, registry: Optional[ProviderRegistry] = None) -> None:
        (registry or default_registry()).get(self.provider)
        if not self.workflow.strip():
            raise ValidationError("ci record names no workflow")
        if not self.ref.strip():
            raise ValidationError("ci record names no ref")
        if self.conclusion not in CONCLUSIONS:
            raise ValidationError(f"unknown ci conclusion: {self.conclusion}")
        for kind in self.claims:
            if kind not in EVIDENCE_KINDS:
                raise ValidationError(f"unknown ci evidence kind: {kind}")


@dataclass(frozen=True)
class CIStanding:
    held: bool
    stage: str
    gaps: Tuple[str, ...]


def derive_standing(record: CIRecord,
                    registry: Optional[ProviderRegistry] = None) -> CIStanding:
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
    return CIStanding(held=not gaps, stage=stage, gaps=tuple(gaps))


@dataclass(frozen=True)
class WorkflowDraft:
    provider: str
    workflow: str
    change: str
    trigger: str = "workflow_dispatch"
    applied: bool = False

    def validate(self, registry: Optional[ProviderRegistry] = None) -> None:
        (registry or default_registry()).get(self.provider)
        if not self.workflow.strip():
            raise ValidationError("workflow draft names no workflow")
        if not self.change.strip():
            raise ValidationError("workflow draft proposes no change")
        if self.applied:
            raise ValidationError(
                "workflow changes are drafts only; a draft is never applied here")


def propose_draft(provider: str, workflow: str, change: str,
                  trigger: str = "workflow_dispatch",
                  registry: Optional[ProviderRegistry] = None) -> WorkflowDraft:
    if trigger != "workflow_dispatch":
        raise ValidationError(
            "on Volmarr's repos a workflow draft dispatches manually by "
            f"default (M-227); refused trigger: {trigger}")
    draft = WorkflowDraft(provider=provider, workflow=workflow,
                          change=change, trigger=trigger)
    draft.validate(registry)
    return draft


def format_provider(entry: ProviderEntry) -> str:
    return f"{entry.label} ({entry.id}): {entry.run_word} - {entry.reason}"


def format_providers(registry: Optional[ProviderRegistry] = None) -> str:
    reg = registry or default_registry()
    return "\n".join(format_provider(e) for e in reg.entries())


def format_record(record: CIRecord,
                  registry: Optional[ProviderRegistry] = None) -> str:
    standing = derive_standing(record, registry)
    state = "held as fact" if standing.held else "open: " + "; ".join(standing.gaps)
    return (f"{record.provider}/{record.workflow} @ {record.ref}: "
            f"{record.conclusion} - {state}")


def format_records(records: Iterable[CIRecord],
                   registry: Optional[ProviderRegistry] = None) -> str:
    return "\n".join(format_record(r, registry) for r in records)
