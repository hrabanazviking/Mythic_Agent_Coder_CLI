"""The UX Principles Charter (All-Features roadmap slice M-004).

The roadmap's kindness rules, written as reviewable law for all later
parts: plain language first; one-tap approvals with remembered scopes;
nothing destructive without a named target; every refusal explains
itself; every long job shows its slices. Data lives in
``mythic_agent/data/ux_charter.yaml``; this module loads, validates,
and renders it.

Reviewability is the point, and :func:`validate_charter` enforces it:

* Principle ids are ``K-01``..``K-NN``, unique and sequential — law is
  cited by number, so the numbering cannot have gaps or duplicates.
* The five roadmap mandates each appear exactly once (see
  :data:`ROADMAP_MANDATES`); a charter that drops or doubles a mandate
  is not the charter M-004 was charged to write.
* Every principle carries a ``review_check`` phrased as a question —
  a reviewer answers it yes or no from a later slice's own evidence.
* ``applies_to`` names real roadmap parts, so :meth:`UxCharter.for_part`
  can answer "which law binds Part VIII?" without guessing.
"""

from __future__ import annotations

__all__ = [
    "CHARTER_RESOURCE",
    "CHARTER_SCHEMA",
    "ROADMAP_MANDATES",
    "Any",
    "Dict",
    "List",
    "Optional",
    "Principle",
    "Tuple",
    "UxCharter",
    "load_charter",
    "render_markdown",
    "validate_charter",
]

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .validation import ValidationError

#: Resource name of the charter data file inside ``mythic_agent/data``.
CHARTER_RESOURCE = "ux_charter.yaml"

#: The only schema this loader accepts.
CHARTER_SCHEMA = "mythic.ux_charter/1"

#: The five kindness rules the roadmap's M-004 names verbatim. Each must
#: be carried by exactly one principle.
ROADMAP_MANDATES = (
    "plain-language-first",
    "one-tap-approvals",
    "named-target-destruction",
    "explained-refusals",
    "visible-slices",
)

_PARTS = ("I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI")
_ID_RE = re.compile(r"^K-\d{2}$")


@dataclass(frozen=True)
class Principle:
    """One numbered kindness rule, citable as law."""

    id: str
    name: str
    mandate: Optional[str]
    rule: str
    why: str
    applies_to: Tuple[str, ...]
    review_check: str


@dataclass(frozen=True)
class UxCharter:
    """The validated charter: numbered principles binding later parts."""

    chartered: str
    binding_on: str
    source_note: str
    principles: Tuple[Principle, ...]

    def principle(self, principle_id: str) -> Principle:
        """Return the principle with id *principle_id* (KeyError if absent)."""
        for principle in self.principles:
            if principle.id == principle_id:
                return principle
        raise KeyError(f"no principle {principle_id!r}")

    def for_part(self, part: str) -> Tuple[Principle, ...]:
        """Principles binding roadmap part *part*, in charter order."""
        return tuple(p for p in self.principles if part in p.applies_to)

    def mandates_covered(self) -> Dict[str, str]:
        """Roadmap mandate key -> the id of the principle carrying it."""
        return {
            p.mandate: p.id for p in self.principles if p.mandate is not None
        }


def validate_charter(data: Any) -> List[str]:
    """Return a list of human-readable problems with charter *data*."""
    problems: List[str] = []
    if not isinstance(data, dict):
        return [f"charter root must be a mapping, got {type(data).__name__}"]
    if data.get("schema") != CHARTER_SCHEMA:
        problems.append(
            f"schema must be {CHARTER_SCHEMA!r}, got {data.get('schema')!r}"
        )
    if not isinstance(data.get("chartered"), str) or not data["chartered"]:
        problems.append("chartered must be a non-empty date string")
    if not isinstance(data.get("binding_on"), str) or not data["binding_on"]:
        problems.append("binding_on must be a non-empty string")

    principles = data.get("principles")
    if not isinstance(principles, list) or not principles:
        problems.append("principles must be a non-empty list")
        return problems
    seen_ids: set = set()
    mandate_ids: Dict[str, str] = {}
    for position, principle in enumerate(principles, start=1):
        if not isinstance(principle, dict):
            problems.append(f"principle is not a mapping: {principle!r}")
            continue
        pid = principle.get("id")
        label = pid if isinstance(pid, str) and pid else repr(principle)[:60]
        expected = f"K-{position:02d}"
        if not isinstance(pid, str) or not _ID_RE.match(pid):
            problems.append(f"principle {label}: id must look like 'K-01'")
        elif pid != expected:
            problems.append(
                f"principle {label}: ids must be sequential, expected {expected}"
            )
        if pid in seen_ids:
            problems.append(f"principle {label}: duplicate id")
        seen_ids.add(pid)
        mandate = principle.get("mandate")
        if mandate is not None:
            if mandate not in ROADMAP_MANDATES:
                problems.append(
                    f"principle {label}: mandate {mandate!r} is not a roadmap mandate"
                )
            elif mandate in mandate_ids:
                problems.append(
                    f"principle {label}: mandate {mandate!r} already carried "
                    f"by {mandate_ids[mandate]}"
                )
            else:
                mandate_ids[mandate] = pid
        for key in ("name", "rule", "why"):
            if not isinstance(principle.get(key), str) or not principle[key]:
                problems.append(f"principle {label}: {key} must be non-empty")
        check = principle.get("review_check")
        if not isinstance(check, str) or not check:
            problems.append(f"principle {label}: review_check must be non-empty")
        elif not check.rstrip().endswith("?"):
            problems.append(
                f"principle {label}: review_check must be a question (end with '?')"
            )
        applies = principle.get("applies_to")
        if not isinstance(applies, list) or not applies:
            problems.append(f"principle {label}: applies_to must be a non-empty list")
        else:
            for part in applies:
                if part not in _PARTS:
                    problems.append(
                        f"principle {label}: applies_to part {part!r} not one of {_PARTS}"
                    )
    missing = [m for m in ROADMAP_MANDATES if m not in mandate_ids]
    if missing:
        problems.append(f"roadmap mandates carried by no principle: {missing}")
    return problems


def _to_charter(data: Dict[str, Any]) -> UxCharter:
    principles = tuple(
        Principle(
            id=p["id"],
            name=p["name"],
            mandate=p.get("mandate"),
            rule=p["rule"],
            why=p["why"],
            applies_to=tuple(p["applies_to"]),
            review_check=p["review_check"],
        )
        for p in data["principles"]
    )
    return UxCharter(
        chartered=data["chartered"],
        binding_on=data["binding_on"],
        source_note=data.get("source_note", ""),
        principles=principles,
    )


def load_charter(data: Optional[Dict[str, Any]] = None) -> UxCharter:
    """Load and validate the shipped UX charter (or *data* when given).

    Raises :class:`~mythic_agent.core.validation.ValidationError`
    listing every problem when the data is not a well-formed charter.
    """
    raw = data if data is not None else load_resource(CHARTER_RESOURCE)
    problems = validate_charter(raw)
    if problems:
        raise ValidationError("ux charter failed validation: " + "; ".join(problems))
    return _to_charter(raw)  # type: ignore[arg-type]


def render_markdown(charter: UxCharter) -> str:
    """Render the charter as markdown: the law, then its reach by part."""
    lines = [
        "# UX Principles Charter — the kindness rules, as law",
        "",
        f"*Chartered {charter.chartered}. Slice M-004 of the All-Features road.*",
        "",
        charter.source_note,
        "",
        f"**Binding on:** {charter.binding_on}",
        "",
    ]
    for principle in charter.principles:
        lines.append(f"## {principle.id} — {principle.name}")
        lines.append("")
        lines.append(principle.rule)
        lines.append("")
        lines.append(f"*Why:* {principle.why}")
        lines.append("")
        lines.append(f"*Review:* {principle.review_check}")
        lines.append("")
    covered = charter.mandates_covered()
    lines += ["## The roadmap mandates, and who carries them", ""]
    for mandate in ROADMAP_MANDATES:
        lines.append(f"- `{mandate}` — {covered[mandate]}")
    lines += ["", "## Which law binds which part", ""]
    for part in _PARTS:
        part_principles = charter.for_part(part)
        if part_principles:
            lines.append(
                f"- Part {part}: "
                + ", ".join(p.id for p in part_principles)
            )
    lines.append("")
    return "\n".join(lines)
