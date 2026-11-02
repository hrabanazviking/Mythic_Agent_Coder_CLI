"""The Subscription Doors Study (All-Features roadmap slice M-033).

OAuth-style sign-ins some rivals use to spend a consumer
subscription instead of an API key — studied behaviourally,
clean-room from the vendors' own public documentation and legal
pages. This slice builds NOTHING: every door in the study carries
``built: false``, and the study's whole product is the verdicts.

Each door records the plans it serves, its sign-in flow, where the
official client keeps the credential, what the usage bills
against, and a terms verdict in a fixed vocabulary:

* ``not_offered`` — the vendor's terms do not allow Mythic to
  build this door, or no vendor programme for it exists; the
  reason is recorded and the sanctioned alternative is named.
* ``first_party_only`` — the sign-in exists, but only inside the
  vendor's own clients.
* ``allowed_via_programme`` — a documented vendor programme lets
  a third-party app ask for this grant, under stated conditions;
  a future build slice may implement it only through that
  programme.

The validator enforces the study's honesty shape: the five doors
in study order, every door unbuilt, every non-built verdict
carrying its reason and its Mythic action, and the study's rules
carrying the never-borrow and never-impersonate rules verbatim —
a login issued to another tool is never Mythic's to spend, and
Mythic never presents itself as the official client.

Data lives in ``mythic_agent/data/subscription_doors.yaml``.
"""

from __future__ import annotations

__all__ = [
    "CATALOG_RESOURCE",
    "CATALOG_SCHEMA",
    "DOOR_IDS",
    "Any",
    "Dict",
    "Door",
    "Finding",
    "List",
    "NEVER_BORROW",
    "NEVER_IMPERSONATE",
    "Optional",
    "Rule",
    "SubscriptionDoors",
    "Tuple",
    "VERDICTS",
    "load_study",
    "render_markdown",
    "validate_study",
]

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .validation import ValidationError

#: Resource name of the study data file inside ``mythic_agent/data``.
CATALOG_RESOURCE = "subscription_doors.yaml"

#: The only schema this loader accepts.
CATALOG_SCHEMA = "mythic.subscription_doors/1"

#: The doors this study records, in study order.
DOOR_IDS = (
    "anthropic-claude-subscription",
    "openai-codex-sign-in",
    "openai-sign-in-with-chatgpt",
    "google-sign-in",
    "github-copilot-sign-in",
)

#: The fixed verdict vocabulary. There is no "maybe".
VERDICTS = ("not_offered", "first_party_only", "allowed_via_programme")

NEVER_BORROW = (
    "never borrow a credential: Mythic never reads, copies, "
    "refreshes or replays a login token stored by or issued to "
    "another tool"
)

NEVER_IMPERSONATE = (
    "never impersonate the official client: Mythic never sends "
    "another client's name, user agent, system prompt or client "
    "identity to spend a subscription"
)

_DOOR_ID_RE = re.compile(r"^D-\d{2}$")
_FINDING_ID_RE = re.compile(r"^F-\d{2}$")
_RULE_ID_RE = re.compile(r"^R-\d{2}$")


@dataclass(frozen=True)
class Door:
    """One subscription sign-in door, studied and verdicted."""

    id: str
    door: str
    name: str
    vendor: str
    rival: str
    mythic_provider: str
    plans: str
    flow: str
    credential_locus: str
    billing: str
    verdict: str
    verdict_reason: str
    mythic_action: str
    evidence: str
    built: bool


@dataclass(frozen=True)
class Finding:
    """One cross-door finding and what it means for Mythic."""

    id: str
    finding: str
    implication: str


@dataclass(frozen=True)
class Rule:
    """One rule binding any future subscription-door work."""

    id: str
    rule: str


@dataclass(frozen=True)
class SubscriptionDoors:
    """The validated study: doors, findings, rules."""

    recorded: str
    scope_note: str
    doors: Tuple[Door, ...]
    findings: Tuple[Finding, ...]
    rules: Tuple[Rule, ...]

    def counts(self) -> Tuple[int, int, int]:
        """(doors, findings, rules) as recorded."""
        return (len(self.doors), len(self.findings), len(self.rules))

    def door_ids(self) -> Tuple[str, ...]:
        """Slugs of the studied doors, in study order."""
        return tuple(d.door for d in self.doors)

    def verdicts(self) -> Tuple[str, ...]:
        """The doors' verdicts, in study order."""
        return tuple(d.verdict for d in self.doors)

    def not_offered(self) -> Tuple[Door, ...]:
        """The doors recorded NOT OFFERED, in study order."""
        return tuple(d for d in self.doors if d.verdict == "not_offered")

    def provider_names(self) -> Tuple[str, ...]:
        """Mythic provider names the doors map to (may hold 'none')."""
        return tuple(d.mythic_provider for d in self.doors)

    def finding_ids(self) -> Tuple[str, ...]:
        """Ids of the findings, in study order."""
        return tuple(f.id for f in self.findings)

    def rule_texts(self) -> Tuple[str, ...]:
        """The study's rules, in study order."""
        return tuple(r.rule for r in self.rules)


def _check_doors(entries: Any, problems: List[str]) -> None:
    if not isinstance(entries, list) or not entries:
        problems.append("doors must be a non-empty list")
        return
    slugs: List[str] = []
    for position, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            problems.append(f"door entry is not a mapping: {entry!r}")
            continue
        eid = entry.get("id")
        expected = f"D-{position:02d}"
        if not isinstance(eid, str) or not _DOOR_ID_RE.match(eid):
            problems.append(f"door entry {eid!r}: id must look like 'D-01'")
        elif eid != expected:
            problems.append(
                f"door entry {eid}: ids must be sequential, expected {expected}"
            )
        for key in (
            "door", "name", "vendor", "rival", "mythic_provider", "plans",
            "flow", "credential_locus", "billing", "verdict_reason",
            "mythic_action", "evidence",
        ):
            if not isinstance(entry.get(key), str) or not entry[key]:
                problems.append(f"door entry {eid}: {key} must be non-empty")
        slug = entry.get("door")
        if isinstance(slug, str):
            slugs.append(slug)
        verdict = entry.get("verdict")
        if verdict not in VERDICTS:
            problems.append(
                f"door entry {eid}: verdict {verdict!r} not in {VERDICTS} "
                "— a door is verdicted in the fixed vocabulary or not at all"
            )
        if entry.get("built") is not False:
            problems.append(
                f"door entry {eid}: built must be false — this is a study "
                "slice; a door is built only by its own later build slice, "
                "which re-records the door there"
            )
    if tuple(slugs) != DOOR_IDS:
        problems.append(
            f"doors must be the studied five in study order {DOOR_IDS}, "
            f"got {tuple(slugs)}"
        )


def _check_findings(entries: Any, problems: List[str]) -> None:
    if not isinstance(entries, list) or len(entries) < 4:
        problems.append("findings must list at least four findings")
        return
    for position, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            problems.append(f"finding entry is not a mapping: {entry!r}")
            continue
        eid = entry.get("id")
        expected = f"F-{position:02d}"
        if not isinstance(eid, str) or not _FINDING_ID_RE.match(eid):
            problems.append(f"finding entry {eid!r}: id must look like 'F-01'")
        elif eid != expected:
            problems.append(
                f"finding entry {eid}: ids must be sequential, "
                f"expected {expected}"
            )
        for key in ("finding", "implication"):
            if not isinstance(entry.get(key), str) or not entry[key]:
                problems.append(f"finding entry {eid}: {key} must be non-empty")


def _check_rules(entries: Any, problems: List[str]) -> None:
    if not isinstance(entries, list) or len(entries) < 4:
        problems.append("rules must list at least four rules")
        return
    texts: List[str] = []
    for position, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            problems.append(f"rule entry is not a mapping: {entry!r}")
            continue
        eid = entry.get("id")
        expected = f"R-{position:02d}"
        if not isinstance(eid, str) or not _RULE_ID_RE.match(eid):
            problems.append(f"rule entry {eid!r}: id must look like 'R-01'")
        elif eid != expected:
            problems.append(
                f"rule entry {eid}: ids must be sequential, expected {expected}"
            )
        rule = entry.get("rule")
        if not isinstance(rule, str) or not rule:
            problems.append(f"rule entry {eid}: rule must be non-empty")
        elif isinstance(rule, str):
            texts.append(rule)
    for verbatim, label in (
        (NEVER_BORROW, "never-borrow"),
        (NEVER_IMPERSONATE, "never-impersonate"),
    ):
        if verbatim not in texts:
            problems.append(
                f"rules must carry the {label} rule verbatim: {verbatim!r}"
            )


def validate_study(data: Any) -> List[str]:
    """Return a list of human-readable problems with study *data*."""
    problems: List[str] = []
    if not isinstance(data, dict):
        return [f"study root must be a mapping, got {type(data).__name__}"]
    if data.get("schema") != CATALOG_SCHEMA:
        problems.append(
            f"schema must be {CATALOG_SCHEMA!r}, got {data.get('schema')!r}"
        )
    if data.get("slice") != "M-033":
        problems.append(f"slice must be 'M-033', got {data.get('slice')!r}")
    for key in ("recorded", "scope_note"):
        if not isinstance(data.get(key), str) or not data[key]:
            problems.append(f"{key} must be a non-empty string")
    _check_doors(data.get("doors"), problems)
    _check_findings(data.get("findings"), problems)
    _check_rules(data.get("rules"), problems)
    return problems


def _to_study(data: Dict[str, Any]) -> SubscriptionDoors:
    return SubscriptionDoors(
        recorded=data["recorded"],
        scope_note=data["scope_note"],
        doors=tuple(
            Door(
                id=d["id"], door=d["door"], name=d["name"],
                vendor=d["vendor"], rival=d["rival"],
                mythic_provider=d["mythic_provider"], plans=d["plans"],
                flow=d["flow"], credential_locus=d["credential_locus"],
                billing=d["billing"], verdict=d["verdict"],
                verdict_reason=d["verdict_reason"],
                mythic_action=d["mythic_action"], evidence=d["evidence"],
                built=d["built"],
            )
            for d in data["doors"]
        ),
        findings=tuple(
            Finding(id=f["id"], finding=f["finding"],
                    implication=f["implication"])
            for f in data["findings"]
        ),
        rules=tuple(
            Rule(id=r["id"], rule=r["rule"]) for r in data["rules"]
        ),
    )


def load_study(data: Optional[Dict[str, Any]] = None) -> SubscriptionDoors:
    """Load and validate the shipped subscription doors study (or *data*).

    Raises :class:`~mythic_agent.core.validation.ValidationError`
    listing every problem when the data is not a well-formed study.
    """
    raw = data if data is not None else load_resource(CATALOG_RESOURCE)
    problems = validate_study(raw)
    if problems:
        raise ValidationError(
            "subscription doors study failed validation: "
            + "; ".join(problems)
        )
    return _to_study(raw)  # type: ignore[arg-type]


def render_markdown(study: SubscriptionDoors) -> str:
    """Render the study as markdown.

    Built from :meth:`SubscriptionDoors.counts`,
    :meth:`SubscriptionDoors.door_ids`,
    :meth:`SubscriptionDoors.verdicts`,
    :meth:`SubscriptionDoors.not_offered`,
    :meth:`SubscriptionDoors.provider_names`,
    :meth:`SubscriptionDoors.finding_ids`, and
    :meth:`SubscriptionDoors.rule_texts`, so the rendered page is
    computed from the same accessors the tests pin.
    """
    n_doors, n_findings, n_rules = study.counts()
    lines = [
        "# Subscription Doors Study (M-033)",
        "",
        f"*Recorded {study.recorded}: {n_doors} doors studied, "
        f"{n_findings} findings, {n_rules} rules. Nothing in this "
        "study is built.*",
        "",
        study.scope_note,
        "",
        "## The doors",
        "",
    ]
    for door in study.doors:
        lines.append(
            f"- {door.id} {door.name} ({door.vendor}; Mythic provider: "
            f"{door.mythic_provider}) — verdict: {door.verdict}. "
            f"Plans: {door.plans}. Flow: {door.flow}. "
            f"Credential: {door.credential_locus}. "
            f"Billing: {door.billing}. "
            f"Why: {door.verdict_reason}. "
            f"Mythic: {door.mythic_action}. "
            f"Evidence: {door.evidence}."
        )
    lines += ["", "## Findings", ""]
    for finding in study.findings:
        lines.append(
            f"- {finding.id} {finding.finding} "
            f"Implication: {finding.implication}"
        )
    lines += ["", "## The rules", ""]
    for rule in study.rules:
        lines.append(f"- {rule.id} {rule.rule}")
    lines += [
        "",
        "## The count, plainly",
        "",
        f"Doors: {', '.join(study.door_ids())}.",
        f"Verdicts: {', '.join(study.verdicts())}.",
        f"NOT OFFERED: {len(study.not_offered())} of {n_doors} doors.",
        f"Providers: {', '.join(study.provider_names())}.",
        f"Findings: {', '.join(study.finding_ids())}.",
        f"Rules: {len(study.rule_texts())} rules, the first: "
        f"{study.rule_texts()[0]}",
        "",
    ]
    return "\n".join(lines)
