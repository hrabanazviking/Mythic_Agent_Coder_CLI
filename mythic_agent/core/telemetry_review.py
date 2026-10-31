"""The Telemetry Honesty Review (All-Features roadmap slice M-015).

What the app records today, where it stays, and the rule that it
never phones home — written down as validated data.

The review inventories every place the package records information
about a session (metrics, costs, audit, journal, sessions, logs,
cache, memory), every channel through which information can leave
the machine at all, and the telemetry systems it honestly does NOT
have (no analytics SDK, no crash upload, no update phone-home, no
background beacon). The validator enforces the honesty shape:

* every recorded item stays local (destination_kind ``local-file``
  or ``in-memory``) and carries ``leaves_machine: false``;
* every outbound channel is user-initiated or user-configured —
  ``background`` and ``automatic`` triggers are refused outright;
* the never-phones-home rule is present verbatim among the rules;
* every recorded item and channel names a real owner module in the
  tree (the tests cross-check those files exist and carry the
  destination / endpoint strings the review cites).

Sending a prompt to a provider the user chose is not telemetry —
it is the work itself — but it IS an outbound channel, so it is
listed here with exactly what it sends, including OpenRouter's
app-identification headers (``HTTP-Referer`` = the project's repo
URL, ``X-Title`` = the app name). Nothing else leaves, and nothing
leaves in the background.

Data lives in ``mythic_agent/data/telemetry_review.yaml``.
"""

from __future__ import annotations

__all__ = [
    "CATALOG_RESOURCE",
    "CATALOG_SCHEMA",
    "DESTINATION_KINDS",
    "Any",
    "AbsentSystem",
    "Dict",
    "List",
    "NEVER_PHONES_HOME",
    "Optional",
    "OutboundChannel",
    "RecordedItem",
    "Rule",
    "TRIGGERS",
    "TelemetryReview",
    "Tuple",
    "load_review",
    "render_markdown",
    "validate_review",
]

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .validation import ValidationError

#: Resource name of the review data file inside ``mythic_agent/data``.
CATALOG_RESOURCE = "telemetry_review.yaml"

#: The only schema this loader accepts.
CATALOG_SCHEMA = "mythic.telemetry_review/1"

DESTINATION_KINDS = ("local-file", "in-memory")

TRIGGERS = ("user-initiated", "user-configured", "provider-call")

NEVER_PHONES_HOME = (
    "never phones home: no recorded information is sent to the "
    "project, its authors, or any third party except through an "
    "outbound channel in this review that the user initiated or "
    "configured"
)

_RECORDED_ID_RE = re.compile(r"^R-\d{2}$")
_CHANNEL_ID_RE = re.compile(r"^O-\d{2}$")
_ABSENT_ID_RE = re.compile(r"^A-\d{2}$")
_RULE_ID_RE = re.compile(r"^H-\d{2}$")


@dataclass(frozen=True)
class RecordedItem:
    """One thing the app records, and where it stays."""

    id: str
    name: str
    owner_module: str
    records: str
    destination: str
    destination_kind: str
    leaves_machine: bool


@dataclass(frozen=True)
class OutboundChannel:
    """One way information can leave the machine at all."""

    id: str
    name: str
    owner_module: str
    trigger: str
    sends: str
    condition: str


@dataclass(frozen=True)
class AbsentSystem:
    """One telemetry system the app honestly does not have."""

    id: str
    name: str
    evidence: str


@dataclass(frozen=True)
class Rule:
    """One honesty rule binding future recording / sending."""

    id: str
    rule: str


@dataclass(frozen=True)
class TelemetryReview:
    """The validated review: recordings, channels, absences, rules."""

    recorded: str
    scope_note: str
    recorded_items: Tuple[RecordedItem, ...]
    outbound_channels: Tuple[OutboundChannel, ...]
    absent_systems: Tuple[AbsentSystem, ...]
    rules: Tuple[Rule, ...]

    def counts(self) -> Tuple[int, int, int, int]:
        """(recorded items, outbound channels, absent systems, rules)."""
        return (
            len(self.recorded_items),
            len(self.outbound_channels),
            len(self.absent_systems),
            len(self.rules),
        )

    def recorded_ids(self) -> Tuple[str, ...]:
        """Ids of the recorded items, in review order."""
        return tuple(r.id for r in self.recorded_items)

    def channel_ids(self) -> Tuple[str, ...]:
        """Ids of the outbound channels, in review order."""
        return tuple(c.id for c in self.outbound_channels)

    def absent_names(self) -> Tuple[str, ...]:
        """Names of the absent telemetry systems, in review order."""
        return tuple(a.name for a in self.absent_systems)

    def rule_texts(self) -> Tuple[str, ...]:
        """The honesty rules, in review order."""
        return tuple(r.rule for r in self.rules)


def _check_recorded(entries: Any, problems: List[str]) -> None:
    if not isinstance(entries, list) or not entries:
        problems.append("recorded_items must be a non-empty list")
        return
    for position, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            problems.append(f"recorded entry is not a mapping: {entry!r}")
            continue
        eid = entry.get("id")
        expected = f"R-{position:02d}"
        if not isinstance(eid, str) or not _RECORDED_ID_RE.match(eid):
            problems.append(f"recorded entry {eid!r}: id must look like 'R-01'")
        elif eid != expected:
            problems.append(
                f"recorded entry {eid}: ids must be sequential, expected {expected}"
            )
        for key in ("name", "owner_module", "records", "destination"):
            if not isinstance(entry.get(key), str) or not entry[key]:
                problems.append(f"recorded entry {eid}: {key} must be non-empty")
        kind = entry.get("destination_kind")
        if kind not in DESTINATION_KINDS:
            problems.append(
                f"recorded entry {eid}: destination_kind {kind!r} "
                f"not in {DESTINATION_KINDS} (recordings stay local)"
            )
        if entry.get("leaves_machine") is not False:
            problems.append(
                f"recorded entry {eid}: leaves_machine must be false — "
                "a recording that leaves the machine is an outbound "
                "channel, not a recording"
            )


def _check_channels(entries: Any, problems: List[str]) -> None:
    if not isinstance(entries, list) or not entries:
        problems.append("outbound_channels must be a non-empty list")
        return
    for position, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            problems.append(f"channel entry is not a mapping: {entry!r}")
            continue
        eid = entry.get("id")
        expected = f"O-{position:02d}"
        if not isinstance(eid, str) or not _CHANNEL_ID_RE.match(eid):
            problems.append(f"channel entry {eid!r}: id must look like 'O-01'")
        elif eid != expected:
            problems.append(
                f"channel entry {eid}: ids must be sequential, expected {expected}"
            )
        for key in ("name", "owner_module", "sends", "condition"):
            if not isinstance(entry.get(key), str) or not entry[key]:
                problems.append(f"channel entry {eid}: {key} must be non-empty")
        trigger = entry.get("trigger")
        if trigger not in TRIGGERS:
            problems.append(
                f"channel entry {eid}: trigger {trigger!r} not in "
                f"{TRIGGERS} — background or automatic sending is "
                "refused (never phones home)"
            )


def _check_absent(entries: Any, problems: List[str]) -> None:
    if not isinstance(entries, list) or len(entries) < 4:
        problems.append("absent_systems must list at least four systems")
        return
    for position, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            problems.append(f"absent entry is not a mapping: {entry!r}")
            continue
        eid = entry.get("id")
        expected = f"A-{position:02d}"
        if not isinstance(eid, str) or not _ABSENT_ID_RE.match(eid):
            problems.append(f"absent entry {eid!r}: id must look like 'A-01'")
        elif eid != expected:
            problems.append(
                f"absent entry {eid}: ids must be sequential, expected {expected}"
            )
        for key in ("name", "evidence"):
            if not isinstance(entry.get(key), str) or not entry[key]:
                problems.append(f"absent entry {eid}: {key} must be non-empty")


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
        expected = f"H-{position:02d}"
        if not isinstance(eid, str) or not _RULE_ID_RE.match(eid):
            problems.append(f"rule entry {eid!r}: id must look like 'H-01'")
        elif eid != expected:
            problems.append(
                f"rule entry {eid}: ids must be sequential, expected {expected}"
            )
        rule = entry.get("rule")
        if not isinstance(rule, str) or not rule:
            problems.append(f"rule entry {eid}: rule must be non-empty")
        elif isinstance(rule, str):
            texts.append(rule)
    if NEVER_PHONES_HOME not in texts:
        problems.append(
            "rules must carry the never-phones-home rule verbatim: "
            f"{NEVER_PHONES_HOME!r}"
        )


def validate_review(data: Any) -> List[str]:
    """Return a list of human-readable problems with review *data*."""
    problems: List[str] = []
    if not isinstance(data, dict):
        return [f"review root must be a mapping, got {type(data).__name__}"]
    if data.get("schema") != CATALOG_SCHEMA:
        problems.append(f"schema must be {CATALOG_SCHEMA!r}, got {data.get('schema')!r}")
    if data.get("slice") != "M-015":
        problems.append(f"slice must be 'M-015', got {data.get('slice')!r}")
    for key in ("recorded", "scope_note"):
        if not isinstance(data.get(key), str) or not data[key]:
            problems.append(f"{key} must be a non-empty string")
    _check_recorded(data.get("recorded_items"), problems)
    _check_channels(data.get("outbound_channels"), problems)
    _check_absent(data.get("absent_systems"), problems)
    _check_rules(data.get("rules"), problems)
    return problems


def _to_review(data: Dict[str, Any]) -> TelemetryReview:
    return TelemetryReview(
        recorded=data["recorded"],
        scope_note=data["scope_note"],
        recorded_items=tuple(
            RecordedItem(
                id=r["id"], name=r["name"], owner_module=r["owner_module"],
                records=r["records"], destination=r["destination"],
                destination_kind=r["destination_kind"],
                leaves_machine=r["leaves_machine"],
            )
            for r in data["recorded_items"]
        ),
        outbound_channels=tuple(
            OutboundChannel(
                id=c["id"], name=c["name"], owner_module=c["owner_module"],
                trigger=c["trigger"], sends=c["sends"], condition=c["condition"],
            )
            for c in data["outbound_channels"]
        ),
        absent_systems=tuple(
            AbsentSystem(id=a["id"], name=a["name"], evidence=a["evidence"])
            for a in data["absent_systems"]
        ),
        rules=tuple(
            Rule(id=h["id"], rule=h["rule"]) for h in data["rules"]
        ),
    )


def load_review(data: Optional[Dict[str, Any]] = None) -> TelemetryReview:
    """Load and validate the shipped telemetry honesty review (or *data*).

    Raises :class:`~mythic_agent.core.validation.ValidationError`
    listing every problem when the data is not a well-formed review.
    """
    raw = data if data is not None else load_resource(CATALOG_RESOURCE)
    problems = validate_review(raw)
    if problems:
        raise ValidationError(
            "telemetry review failed validation: " + "; ".join(problems)
        )
    return _to_review(raw)  # type: ignore[arg-type]


def render_markdown(review: TelemetryReview) -> str:
    """Render the review as markdown.

    Built from :meth:`TelemetryReview.counts`,
    :meth:`TelemetryReview.recorded_ids`,
    :meth:`TelemetryReview.channel_ids`,
    :meth:`TelemetryReview.absent_names`, and
    :meth:`TelemetryReview.rule_texts`, so the rendered page is
    computed from the same accessors the tests pin.
    """
    n_rec, n_chan, n_abs, n_rules = review.counts()
    lines = [
        "# Telemetry Honesty Review (M-015)",
        "",
        f"*Recorded {review.recorded}: {n_rec} recorded items, "
        f"{n_chan} outbound channels, {n_abs} absent systems, "
        f"{n_rules} honesty rules.*",
        "",
        review.scope_note,
        "",
        "## What is recorded (and stays here)",
        "",
    ]
    for item in review.recorded_items:
        lines.append(
            f"- {item.id} {item.name} (`{item.owner_module}`): "
            f"{item.records} Stored: {item.destination}."
        )
    lines += ["", "## What can leave the machine at all", ""]
    for channel in review.outbound_channels:
        lines.append(
            f"- {channel.id} {channel.name} (`{channel.owner_module}`, "
            f"{channel.trigger}): sends {channel.sends} "
            f"Condition: {channel.condition}."
        )
    lines += ["", "## What the app does not have", ""]
    for absent in review.absent_systems:
        lines.append(f"- {absent.id} {absent.name}: {absent.evidence}")
    lines += ["", "## The rules", ""]
    for rule in review.rules:
        lines.append(f"- {rule.id} {rule.rule}")
    lines += [
        "",
        "## The count, plainly",
        "",
        f"Recorded: {', '.join(review.recorded_ids())}.",
        f"Channels: {', '.join(review.channel_ids())}.",
        f"Absent: {', '.join(review.absent_names())}.",
        f"Rules: {len(review.rule_texts())} honesty rules, the first: "
        f"{review.rule_texts()[0]}",
        "",
    ]
    return "\n".join(lines)
