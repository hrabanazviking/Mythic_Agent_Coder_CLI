"""Git host parity (roadmap slice M-246) - pure layer.

Part X - Bridges. The roadmap words: **the forge's git craft is
host-agnostic; hosts are registry entries like providers.**

What already ships, and what this slice adds:

* The forge's git craft already stands in the tree as host-agnostic
  work (Part IV): cloning, branching, committing, pushing, and the
  request / issue / review / merge craft were built once, not once
  per host. The GitHub roads name GitHub because that is where the
  work first landed, not because the craft belongs to it.
* Providers already stand as registry entries: a provider is held
  as data (a name, a shape, a telling of its limits) and the session
  holds the registry, not a hard-coded list. Until this slice, git
  hosts had no such registry - GitHub was simply assumed, and
  whether GitLab or Bitbucket stood at parity with it was a thing
  people said, not a thing the forge held.

This layer is the parity book, held as data:

* A **host registry** (packaged data, schema
  'mythic.git_host_parity/1') records one entry per host - github,
  gitlab, bitbucket - the way the provider registry records a
  provider: its id, its plain label, the word that host gives the
  request craft (GitLab says merge request; GitHub and Bitbucket
  say pull request), and why the entry stands, in plain words. A
  host the registry does not hold refuses BY NAME; a duplicated or
  half-written entry refuses whole. The registry is data: a new
  host casting needs no code change.
* A **parity record** holds, for one host, the host-agnostic crafts
  claimed for it, the stages it has walked, and the claims it rests
  on, by kind. Its standing is DERIVED at call time against the
  explicit parity walk held as data (STAGES, TRANSITIONS):
  registered, mapped, crafted, evidenced, held. A record that opens
  anywhere but registered, steps where the walk does not allow,
  rests on a bare claim (feeling, memory, assertion, summary)
  instead of held evidence (remote_ref, repo_ref, request_ref,
  review_ref, craft_ref, parity_ref), names no craft, or has not
  reached held stands open, named in its gaps.
* Honesty rule, made code: parity is never claimed without held
  evidence. A record standing at held on bare claims alone, or on
  no held evidence at all, stands open by construction - the book
  will not dress a claim up as parity.

Honest boundary: this layer holds registry entries, parity records
and derived standings as data. It clones nothing, pushes nothing,
opens no request, calls no host API and probes no network; the
agent layer owns holding a session's records and speaking to a
host on the live roads.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple
import yaml
from ..resources import load_resource
from .validation import ValidationError

__all__ = [
    "BARE_CLAIMS",
    "CLAIM_KINDS",
    "CRAFTS",
    "GIT_HOST_SCHEMA",
    "GIT_HOST_SLICE",
    "HELD_EVIDENCE",
    "HOSTS",
    "HOST_RESOURCE",
    "PLAIN_EXPLANATION",
    "REQUEST_WORDS",
    "STAGES",
    "TRANSITIONS",
    "USAGE",
    "HostEntry",
    "HostRegistry",
    "ParityRecord",
    "ParityStanding",
    "derive_standing",
    "format_host",
    "format_hosts",
    "format_parity",
    "host_record",
    "legal_step",
    "load_host_registry",
    "load_host_registry_file",
    "parity_gaps",
    "plain_words",
    "validate_host_entry",
    "validate_host_registry",
    "validate_parity_record",
]

GIT_HOST_SLICE = "M-246"

#: The packaged data resource holding the shipped host registry.
HOST_RESOURCE = "git_host_parity.yaml"

#: The schema word a host registry file must carry.
GIT_HOST_SCHEMA = "mythic.git_host_parity/1"

#: The hosts the parity book holds, in registry order.
HOSTS: Tuple[str, ...] = ("github", "gitlab", "bitbucket")

#: The words a host may give the request craft.
REQUEST_WORDS: Tuple[str, ...] = ("pull request", "merge request")

#: The host-agnostic git crafts parity is judged over: the craft is
#: built once, and each host either stands at parity for it on held
#: evidence or stands open.
CRAFTS: Tuple[str, ...] = (
    "clone",
    "branch",
    "commit",
    "push",
    "request",
    "issue",
    "review",
    "merge",
)

#: The parity walk, held as data: a host is first registered, its
#: craft is then mapped host by host, the craft is exercised, the
#: exercise is evidenced, and only then is parity held.
STAGES: Tuple[str, ...] = (
    "registered", "mapped", "crafted", "evidenced", "held")

#: The legal steps of the parity walk, held as data.
TRANSITIONS: Dict[str, Tuple[str, ...]] = {
    "registered": ("mapped",),
    "mapped": ("crafted",),
    "crafted": ("evidenced",),
    "evidenced": ("held",),
    "held": (),
}

#: Claim kinds that are held evidence: a reference the forge holds.
HELD_EVIDENCE: Tuple[str, ...] = (
    "remote_ref", "repo_ref", "request_ref",
    "review_ref", "craft_ref", "parity_ref")

#: Claim kinds that are bare claims: a saying, never evidence.
BARE_CLAIMS: Tuple[str, ...] = (
    "feeling", "memory", "assertion", "summary")

#: Every claim kind a parity record may name.
CLAIM_KINDS: Tuple[str, ...] = HELD_EVIDENCE + BARE_CLAIMS

_HOST_KEYS = frozenset(("host", "label", "request_word", "reason"))
_REGISTRY_KEYS = frozenset(("schema", "hosts"))
_PARITY_KEYS = frozenset(
    ("host", "crafts", "stages", "claims", "detail"))

PLAIN_EXPLANATION = (
    "The forge's git craft is host-agnostic, and hosts are "
    "registry entries like providers. The registry book names "
    "each host the forge speaks - GitHub, GitLab, Bitbucket - "
    "with the word that host gives a change request: GitLab "
    "says merge request, the others say pull request. Parity "
    "is not a thing a host is granted by being listed: for each "
    "host a parity record holds the crafts claimed for it, the "
    "stages it has walked - registered, mapped, crafted, "
    "evidenced, held - and the claims it rests on. Parity "
    "stands held only when the walk is whole and legal and "
    "rests on held evidence; a record resting on a bare claim, "
    "or stopping short of held, stands open and names its "
    "gaps. No parity is ever claimed without held evidence.")

USAGE = (
    "derive_standing (config-free): read a host from the "
    "registry book, hold one parity record per host as data "
    "(its crafts, its walked stages, its claims by kind), and "
    "derive its standing; the standing names held only on a "
    "full legal walk resting on held evidence, and otherwise "
    "stands open, naming every gap.")


def plain_words() -> str:
    """The plain-language explanation of this slice."""
    return PLAIN_EXPLANATION


@dataclass(frozen=True)
class HostEntry:
    """One git host, held as a registry entry like a provider."""

    host: str
    label: str
    request_word: str
    reason: str

    def record(self) -> Dict[str, Any]:
        """This entry as a plain mapping."""
        return {"host": self.host, "label": self.label,
                "request_word": self.request_word,
                "reason": self.reason}


def validate_host_entry(raw: Any) -> HostEntry:
    """Validate one host registry entry, whole, by name."""
    if not isinstance(raw, dict):
        raise ValidationError(
            "a host entry must be a mapping, not "
            f"{type(raw).__name__}")
    unknown = sorted(set(raw) - _HOST_KEYS)
    if unknown:
        raise ValidationError(
            "unknown host entry keys: " + ", ".join(unknown))
    host = raw.get("host")
    if host not in HOSTS:
        raise ValidationError(
            f"unknown host {host!r}; the parity book holds: "
            + ", ".join(HOSTS))
    label = raw.get("label")
    if not isinstance(label, str) or not label.strip():
        raise ValidationError(
            "a host entry must carry its label in plain words")
    request_word = raw.get("request_word")
    if request_word not in REQUEST_WORDS:
        raise ValidationError(
            f"unknown request word {request_word!r}; a host "
            "names one of: " + ", ".join(REQUEST_WORDS))
    reason = raw.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise ValidationError(
            "a host entry must carry its reason in plain words")
    return HostEntry(host=host, label=label.strip(),
                     request_word=request_word,
                     reason=reason.strip())


@dataclass(frozen=True)
class HostRegistry:
    """The whole host registry: one entry per host held."""

    hosts: Tuple[HostEntry, ...]

    def for_host(self, host_id: Any) -> HostEntry:
        """The entry for *host_id*, refused by name."""
        if host_id not in HOSTS:
            raise ValidationError(
                f"unknown host {host_id!r}; the parity book "
                "holds: " + ", ".join(HOSTS))
        for entry in self.hosts:
            if entry.host == host_id:
                return entry
        raise ValidationError(
            f"the host registry holds no entry for host "
            f"{host_id!r}")

    def record(self) -> Dict[str, Any]:
        """This registry as a plain mapping."""
        return {"schema": GIT_HOST_SCHEMA,
                "hosts": [h.record() for h in self.hosts]}


def validate_host_registry(raw: Any) -> HostRegistry:
    """Validate a whole host registry mapping, whole."""
    if not isinstance(raw, dict):
        raise ValidationError(
            "a host registry must be a mapping, not "
            f"{type(raw).__name__}")
    unknown = sorted(set(raw) - _REGISTRY_KEYS)
    if unknown:
        raise ValidationError(
            "unknown host registry keys: " + ", ".join(unknown))
    if raw.get("schema") != GIT_HOST_SCHEMA:
        raise ValidationError(
            f"a host registry must carry schema "
            f"{GIT_HOST_SCHEMA!r}")
    rows = raw.get("hosts")
    if not isinstance(rows, list) or not rows:
        raise ValidationError(
            "a host registry must hold a non-empty hosts list")
    hosts = tuple(validate_host_entry(row) for row in rows)
    seen = set()
    for entry in hosts:
        if entry.host in seen:
            raise ValidationError(
                f"duplicate host entry for host {entry.host!r}")
        seen.add(entry.host)
    return HostRegistry(hosts=hosts)


def host_record(registry: HostRegistry,
                host_id: Any) -> Dict[str, Any]:
    """One host's registry entry as a plain mapping."""
    return registry.for_host(host_id).record()


def load_host_registry() -> HostRegistry:
    """Load the shipped host registry from packaged data."""
    data = load_resource(HOST_RESOURCE)
    return validate_host_registry(data)


def load_host_registry_file(path: Any) -> HostRegistry:
    """Load and validate a host registry from any file."""
    text = Path(path).read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    return validate_host_registry(data)


def legal_step(before: Any, after: Any) -> bool:
    """True when the parity walk allows *before* -> *after*."""
    return after in TRANSITIONS.get(before, ())


@dataclass(frozen=True)
class ParityRecord:
    """One host's parity, held whole as data.

    The crafts named are the host-agnostic crafts claimed for
    this host; the stages are the steps of the parity walk it
    has walked, in walk order; the claims are the claim kinds it
    rests on - held evidence and bare claims alike are held
    honestly, and the derivation judges them.
    """

    host: str
    crafts: Tuple[str, ...]
    stages: Tuple[str, ...]
    claims: Tuple[str, ...]
    detail: str

    @property
    def stage(self) -> str:
        """The stage this record stands at: its last walked."""
        return self.stages[-1] if self.stages else ""

    def record(self) -> Dict[str, Any]:
        """This parity record as a plain mapping."""
        return {"host": self.host, "crafts": list(self.crafts),
                "stages": list(self.stages),
                "claims": list(self.claims),
                "detail": self.detail}


def _check_names(value: Any, allowed: Tuple[str, ...],
                 what: str) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValidationError(f"{what} must be a list of names")
    out = []
    for name in value:
        if name not in allowed:
            raise ValidationError(
                f"unknown {what} name {name!r}; the book "
                "names: " + ", ".join(allowed))
        if name not in out:
            out.append(name)
    return tuple(out)


def validate_parity_record(raw: Any) -> ParityRecord:
    """Validate one parity record, whole, by name."""
    if isinstance(raw, ParityRecord):
        return raw
    if not isinstance(raw, dict):
        raise ValidationError(
            "a parity record must be a mapping, not "
            f"{type(raw).__name__}")
    unknown = sorted(set(raw) - _PARITY_KEYS)
    if unknown:
        raise ValidationError(
            "unknown parity record keys: " + ", ".join(unknown))
    host = raw.get("host")
    if host not in HOSTS:
        raise ValidationError(
            f"unknown host {host!r}; the parity book holds: "
            + ", ".join(HOSTS))
    crafts = _check_names(raw.get("crafts"), CRAFTS, "craft")
    stages = _check_names(raw.get("stages"), STAGES, "stage")
    claims = _check_names(raw.get("claims"), CLAIM_KINDS, "claim")
    detail = raw.get("detail")
    if not isinstance(detail, str) or not detail.strip():
        raise ValidationError(
            "a parity record must carry its detail in plain "
            "words")
    return ParityRecord(host=host, crafts=crafts, stages=stages,
                        claims=claims, detail=detail.strip())


def parity_gaps(record: Any) -> Tuple[str, ...]:
    """The gaps that keep one record's parity from standing held.

    The derivation is the honesty rule made code: the walk must
    open at registered and step only where TRANSITIONS allow;
    a bare claim among the claims is a gap by name; standing at
    held on no held evidence is a gap; naming no craft is a gap;
    and any stage short of held is a gap. No gaps means held.
    """
    rec = validate_parity_record(record)
    gaps = []
    if not rec.stages:
        gaps.append("no stage walked: the walk has not begun")
    else:
        if rec.stages[0] != STAGES[0]:
            gaps.append(
                f"walk opens at {rec.stages[0]!r}, not "
                f"{STAGES[0]!r}")
        for before, after in zip(rec.stages, rec.stages[1:]):
            if not legal_step(before, after):
                gaps.append(
                    f"stage step {before} -> {after} is not "
                    "in the parity walk")
    bare = [c for c in rec.claims if c in BARE_CLAIMS]
    if bare:
        gaps.append(
            "rests on bare claims: " + ", ".join(bare))
    held_evidence = [c for c in rec.claims if c in HELD_EVIDENCE]
    if rec.stage == "held" and not held_evidence:
        gaps.append("stands held on no held evidence")
    if not rec.crafts:
        gaps.append("names no git craft")
    if rec.stage != "held":
        gaps.append(
            f"stands at {rec.stage or 'no stage'}, not held")
    return tuple(gaps)


@dataclass(frozen=True)
class ParityStanding:
    """One host's parity standing, derived whole at call time."""

    host: str
    standing: str
    stage: str
    gaps: Tuple[str, ...]
    crafts: Tuple[str, ...]

    def record(self) -> Dict[str, Any]:
        """This standing as a plain mapping."""
        return {"host": self.host, "standing": self.standing,
                "stage": self.stage, "gaps": list(self.gaps),
                "crafts": list(self.crafts)}


def derive_standing(record: Any) -> ParityStanding:
    """Derive one record's parity standing at call time."""
    rec = validate_parity_record(record)
    gaps = parity_gaps(rec)
    return ParityStanding(
        host=rec.host,
        standing="held" if not gaps else "open",
        stage=rec.stage, gaps=gaps, crafts=rec.crafts)


def format_host(entry: HostEntry) -> str:
    """One registry entry as a single readable line."""
    return (f"{entry.label} ({entry.host}): the request craft "
            f"is a {entry.request_word} - {entry.reason}")


def format_hosts(registry: HostRegistry) -> str:
    """The whole registry as readable lines, in book order."""
    lines = ["Git hosts, held as registry entries:"]
    lines.extend(format_host(h) for h in registry.hosts)
    return "\n".join(lines)


def format_parity(record: Any) -> str:
    """One record's derived standing as a readable block."""
    rec = validate_parity_record(record)
    standing = derive_standing(rec)
    craft_words = ", ".join(rec.crafts) or "no craft named"
    lines = [f"{rec.host}: parity {standing.standing} "
             f"(stage: {standing.stage or 'none'}) - "
             f"crafts: {craft_words}."]
    lines.append(f"  detail: {rec.detail}")
    lines.extend("  gap: " + gap for gap in standing.gaps)
    return "\n".join(lines)
