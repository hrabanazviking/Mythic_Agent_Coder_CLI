"""The Feature Census (All-Features roadmap slice M-001).

A living matrix — feature x rival tool x Mythic's own state — stored as
data in ``mythic_agent/data/feature_census.yaml`` and loaded, validated,
and rendered through this module. The census is the evidence base the
rest of the All-Features road builds on: every PARTIAL or MISSING row
must name the roadmap slice that owns its fix (``roadmap_ref``), and
every HAVE or BETTER claim about Mythic itself must name its evidence
(the module or path in this repository that proves it).

Honesty rules, enforced by :func:`validate_census`:

* Rival cells may be ``UNKNOWN`` — unknown means unknown, never guessed.
  Mythic's own cells may never be ``UNKNOWN``: we can always inspect
  our own tree.
* ``HAVE`` / ``BETTER`` rows for Mythic require a non-empty evidence
  pointer; ``PARTIAL`` / ``MISSING`` rows require a roadmap reference
  of the form ``M-###``.
* Every feature row carries a cell for every rival in the census —
  a missing cell is a validation error, not a silent gap.

Refresh workflow: edit the YAML (it is data, not code), bump its
``refreshed`` date, and run the census tests
(``tests/test_feature_census.py``); Part I's gate (M-018) publishes
the rendered matrix in-repo.
"""

from __future__ import annotations

__all__ = [
    "CENSUS_RESOURCE",
    "CENSUS_SCHEMA",
    "MYTHIC_STATES",
    "RIVAL_STATES",
    "Any",
    "Census",
    "Dict",
    "Feature",
    "List",
    "MythicCell",
    "Optional",
    "Rival",
    "RivalCell",
    "Tuple",
    "load_census",
    "render_markdown",
    "validate_census",
]

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .validation import ValidationError

#: Resource name of the census data file inside ``mythic_agent/data``.
CENSUS_RESOURCE = "feature_census.yaml"

#: The only schema this loader accepts.
CENSUS_SCHEMA = "mythic.feature_census/1"

#: States a rival cell may hold. UNKNOWN is a first-class result.
RIVAL_STATES = ("HAVE", "PARTIAL", "MISSING", "BETTER", "UNKNOWN")

#: States Mythic's own cell may hold — never UNKNOWN (our tree is ours
#: to inspect), and BETTER is allowed where the form genuinely leads.
MYTHIC_STATES = ("HAVE", "PARTIAL", "MISSING", "BETTER")

_ROADMAP_REF = re.compile(r"^M-\d{3}$")


@dataclass(frozen=True)
class Rival:
    """One rival tool column of the matrix."""

    id: str
    name: str


@dataclass(frozen=True)
class RivalCell:
    """One rival's state for one feature."""

    state: str
    form: str


@dataclass(frozen=True)
class MythicCell:
    """Mythic's own state for one feature, with its evidence pointer."""

    state: str
    form: str
    evidence: str


@dataclass(frozen=True)
class Feature:
    """One feature row of the matrix."""

    id: str
    name: str
    category: str
    mythic: MythicCell
    roadmap_ref: Optional[str]
    rivals: Dict[str, RivalCell]


@dataclass(frozen=True)
class Census:
    """The validated census: rivals, features, and the refresh stamp."""

    refreshed: str
    source_note: str
    rivals: Tuple[Rival, ...]
    features: Tuple[Feature, ...]

    def feature(self, feature_id: str) -> Feature:
        """Return the feature row with *feature_id* (KeyError if absent)."""
        for row in self.features:
            if row.id == feature_id:
                return row
        raise KeyError(f"no census feature with id {feature_id!r}")

    def rival(self, rival_id: str) -> Rival:
        """Return the rival column with *rival_id* (KeyError if absent)."""
        for rival in self.rivals:
            if rival.id == rival_id:
                return rival
        raise KeyError(f"no census rival with id {rival_id!r}")

    def gaps(self) -> Tuple[Feature, ...]:
        """Rows where Mythic is PARTIAL or MISSING — the road's work list."""
        return tuple(
            row for row in self.features if row.mythic.state in ("PARTIAL", "MISSING")
        )

    def counts(self) -> Dict[str, int]:
        """Mythic state -> number of feature rows, for every known state."""
        tally = {state: 0 for state in MYTHIC_STATES}
        for row in self.features:
            tally[row.mythic.state] += 1
        return tally


def validate_census(data: Any) -> List[str]:
    """Return a list of human-readable problems with census *data*.

    An empty list means the data is a well-formed census. Every rule
    here exists so the matrix can never quietly rot: a new rival with
    no cells, a gap with no owning slice, or a HAVE claim with no
    evidence all fail loudly at load time and in the test suite.
    """
    problems: List[str] = []
    if not isinstance(data, dict):
        return [f"census root must be a mapping, got {type(data).__name__}"]
    if data.get("schema") != CENSUS_SCHEMA:
        problems.append(
            f"schema must be {CENSUS_SCHEMA!r}, got {data.get('schema')!r}"
        )
    if not isinstance(data.get("refreshed"), str) or not data["refreshed"]:
        problems.append("refreshed must be a non-empty date string")

    rivals = data.get("rivals")
    rival_ids: List[str] = []
    if not isinstance(rivals, list) or len(rivals) < 10:
        problems.append("rivals must be a list of at least ten tools")
    else:
        for entry in rivals:
            if not isinstance(entry, dict) or not entry.get("id") or not entry.get("name"):
                problems.append(f"rival entry lacks id/name: {entry!r}")
                continue
            rival_ids.append(entry["id"])
        if len(set(rival_ids)) != len(rival_ids):
            problems.append("rival ids must be unique")

    features = data.get("features")
    if not isinstance(features, list) or not features:
        problems.append("features must be a non-empty list")
        return problems
    seen: set = set()
    for row in features:
        if not isinstance(row, dict):
            problems.append(f"feature row is not a mapping: {row!r}")
            continue
        fid = row.get("id")
        label = fid if isinstance(fid, str) and fid else repr(row)[:60]
        if not fid or fid in seen:
            problems.append(f"feature id missing or duplicated: {label}")
        seen.add(fid)
        for key in ("name", "category"):
            if not row.get(key):
                problems.append(f"feature {label}: {key} must be non-empty")
        mythic = row.get("mythic")
        if not isinstance(mythic, dict):
            problems.append(f"feature {label}: mythic cell must be a mapping")
            continue
        state = mythic.get("state")
        if state not in MYTHIC_STATES:
            problems.append(
                f"feature {label}: mythic state {state!r} not in {MYTHIC_STATES}"
            )
        if not mythic.get("form"):
            problems.append(f"feature {label}: mythic form must be non-empty")
        ref = row.get("roadmap_ref")
        if state in ("HAVE", "BETTER") and not mythic.get("evidence"):
            problems.append(
                f"feature {label}: {state} claims require an evidence pointer"
            )
        if state in ("PARTIAL", "MISSING"):
            if not isinstance(ref, str) or not _ROADMAP_REF.match(ref):
                problems.append(
                    f"feature {label}: {state} rows require a roadmap_ref like 'M-044'"
                )
        cells = row.get("rivals")
        if not isinstance(cells, dict):
            problems.append(f"feature {label}: rivals must be a mapping")
            continue
        missing = [rid for rid in rival_ids if rid not in cells]
        extra = [rid for rid in cells if rid not in rival_ids]
        if missing:
            problems.append(f"feature {label}: missing rival cells: {missing}")
        if extra:
            problems.append(f"feature {label}: unknown rival cells: {extra}")
        for rid, cell in cells.items():
            if not isinstance(cell, dict) or cell.get("state") not in RIVAL_STATES:
                problems.append(
                    f"feature {label}: rival {rid} state must be one of {RIVAL_STATES}"
                )
            elif not cell.get("form"):
                problems.append(f"feature {label}: rival {rid} form must be non-empty")
    return problems


def _to_census(data: Dict[str, Any]) -> Census:
    rivals = tuple(Rival(id=r["id"], name=r["name"]) for r in data["rivals"])
    features = []
    for row in data["features"]:
        mythic = row["mythic"]
        features.append(
            Feature(
                id=row["id"],
                name=row["name"],
                category=row["category"],
                mythic=MythicCell(
                    state=mythic["state"],
                    form=mythic["form"],
                    evidence=mythic.get("evidence", ""),
                ),
                roadmap_ref=row.get("roadmap_ref"),
                rivals={
                    rid: RivalCell(state=cell["state"], form=cell["form"])
                    for rid, cell in row["rivals"].items()
                },
            )
        )
    return Census(
        refreshed=data["refreshed"],
        source_note=data.get("source_note", ""),
        rivals=rivals,
        features=tuple(features),
    )


def load_census(data: Optional[Dict[str, Any]] = None) -> Census:
    """Load and validate the shipped census (or *data* when given).

    Raises :class:`~mythic_agent.core.validation.ValidationError`
    listing every problem when the data is not a well-formed census.
    """
    raw = data if data is not None else load_resource(CENSUS_RESOURCE)
    problems = validate_census(raw)
    if problems:
        raise ValidationError(
            "feature census failed validation: " + "; ".join(problems)
        )
    return _to_census(raw)  # type: ignore[arg-type]


def render_markdown(census: Census) -> str:
    """Render the matrix as a markdown table (Mythic's state per feature,
    plus which rivals hold the feature) — the living view M-018 publishes."""
    lines = [
        "# Feature Census — Mythic Agent Coder vs the field",
        "",
        f"*Refreshed {census.refreshed}. Slice M-001 of the All-Features road.*",
        "",
        census.source_note,
        "",
        "| Feature | Category | Mythic | Owning slice | Rivals holding it |",
        "|---|---|---|---|---|",
    ]
    for row in census.features:
        holders = ", ".join(
            census.rival(rid).name
            for rid, cell in row.rivals.items()
            if cell.state in ("HAVE", "BETTER")
        )
        lines.append(
            f"| {row.name} | {row.category} | {row.mythic.state} | "
            f"{row.roadmap_ref or '—'} | {holders or '—'} |"
        )
    gaps = census.gaps()
    lines += [
        "",
        f"## The gaps, owned ({len(gaps)} of {len(census.features)} rows)",
        "",
        "Every PARTIAL or MISSING row names the roadmap slice that owns",
        "its fix — a gap without an owner is a validation error.",
        "",
    ]
    for row in gaps:
        lines.append(f"- **{row.name}** — {row.mythic.state}, owned by {row.roadmap_ref}.")
    lines.append("")
    return "\n".join(lines)
