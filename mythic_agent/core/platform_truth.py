"""The Platform Truth Table (All-Features roadmap slice M-013).

Linux, Windows, and macOS, each against four surfaces — install,
run, TUI, voice — twelve cells, each PROVEN or NOT PROVEN as of the
recorded date, with no inheritance. A cell earns PROVEN only on
evidence measured locally in this campaign: the validator refuses a
PROVEN verdict whose evidence kind is anything but
``local-measured``, so a historical hosted run, a documentation
promise, or a rival's claim can never be dressed up as proof.

Historical evidence is still named where it exists — the hosted
six-job matrix passed for earlier revisions (runs recorded in
``docs/development/PROGRESS.md``) — but those cells stay NOT PROVEN
until the evidence is re-earned on the current tree: the workflow
is manual-dispatch only, and no Windows or macOS machine is
available to this campaign. Voice is NOT PROVEN on every platform:
on this Linux machine the absence is itself measured (the PortAudio
system library is missing, so the audio import fails), and the
hosted matrix never installs the voice extra at all.

The tests cross-check the table against the live CI workflow (its
OS matrix, its manual-only trigger, its install step) and against
the hosted run ids recorded in ``docs/development/PROGRESS.md``, so
the table cannot drift away from the evidence it cites.

Data lives in ``mythic_agent/data/platform_truth.yaml``.
"""

from __future__ import annotations

__all__ = [
    "CATALOG_RESOURCE",
    "CATALOG_SCHEMA",
    "EVIDENCE_KINDS",
    "Any",
    "Cell",
    "Dict",
    "List",
    "Optional",
    "PLATFORMS",
    "PlatformTruth",
    "SURFACES",
    "VERDICTS",
    "load_truth",
    "render_markdown",
    "validate_truth",
]

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .validation import ValidationError

#: Resource name of the truth-table data file inside ``mythic_agent/data``.
CATALOG_RESOURCE = "platform_truth.yaml"

#: The only schema this loader accepts.
CATALOG_SCHEMA = "mythic.platform_truth/1"

PLATFORMS = ("linux", "windows", "macos")

SURFACES = ("install", "run", "tui", "voice")

VERDICTS = ("PROVEN", "NOT PROVEN")

EVIDENCE_KINDS = ("local-measured", "historical-only", "none")

_CELL_ID_RE = re.compile(r"^P-\d{2}$")


@dataclass(frozen=True)
class Cell:
    """One platform x surface cell of the truth table."""

    id: str
    platform: str
    surface: str
    verdict: str
    evidence_kind: str
    evidence: str
    retest: str


@dataclass(frozen=True)
class PlatformTruth:
    """The validated platform truth table: twelve cells."""

    recorded: str
    scope_note: str
    cells: Tuple[Cell, ...]

    def verdict_for(self, platform: str, surface: str) -> Optional[str]:
        """The verdict for one platform/surface pair, or None."""
        for cell in self.cells:
            if cell.platform == platform and cell.surface == surface:
                return cell.verdict
        return None

    def counts(self) -> Tuple[int, int]:
        """(cells, proven cells) as recorded."""
        proven = sum(1 for c in self.cells if c.verdict == "PROVEN")
        return (len(self.cells), proven)

    def proven_cells(self) -> Tuple[str, ...]:
        """Ids of the PROVEN cells, in table order."""
        return tuple(c.id for c in self.cells if c.verdict == "PROVEN")

    def not_proven_cells(self) -> Tuple[str, ...]:
        """Ids of the NOT PROVEN cells, in table order."""
        return tuple(c.id for c in self.cells if c.verdict == "NOT PROVEN")


def _check_cells(entries: Any, problems: List[str]) -> List[Dict[str, Any]]:
    if not isinstance(entries, list) or not entries:
        problems.append("cells must be a non-empty list")
        return []
    seen: set = set()
    for position, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            problems.append(f"cell entry is not a mapping: {entry!r}")
            continue
        eid = entry.get("id")
        expected = f"P-{position:02d}"
        if not isinstance(eid, str) or not _CELL_ID_RE.match(eid):
            problems.append(f"cell entry {eid!r}: id must look like 'P-01'")
        elif eid != expected:
            problems.append(
                f"cell entry {eid}: ids must be sequential, expected {expected}"
            )
        platform = entry.get("platform")
        surface = entry.get("surface")
        if platform not in PLATFORMS:
            problems.append(
                f"cell entry {eid}: platform {platform!r} not in {PLATFORMS}"
            )
        if surface not in SURFACES:
            problems.append(
                f"cell entry {eid}: surface {surface!r} not in {SURFACES}"
            )
        if isinstance(platform, str) and isinstance(surface, str):
            pair = (platform, surface)
            if pair in seen:
                problems.append(f"cell entry {eid}: {pair} is tabled twice")
            seen.add(pair)
        verdict = entry.get("verdict")
        kind = entry.get("evidence_kind")
        if verdict not in VERDICTS:
            problems.append(
                f"cell entry {eid}: verdict {verdict!r} not in {VERDICTS}"
            )
        if kind not in EVIDENCE_KINDS:
            problems.append(
                f"cell entry {eid}: evidence_kind {kind!r} not in {EVIDENCE_KINDS}"
            )
        if verdict == "PROVEN" and kind != "local-measured":
            problems.append(
                f"cell entry {eid}: PROVEN requires evidence_kind "
                f"'local-measured' (no inheritance), got {kind!r}"
            )
        for key in ("evidence", "retest"):
            if not isinstance(entry.get(key), str) or not entry[key]:
                problems.append(f"cell entry {eid}: {key} must be non-empty")
    expected_pairs = {(p, s) for p in PLATFORMS for s in SURFACES}
    if seen != expected_pairs:
        problems.append(
            f"cells must cover every platform x surface pair exactly once; "
            f"missing {sorted(expected_pairs - seen)}, "
            f"extra {sorted(seen - expected_pairs)}"
        )
    return entries


def validate_truth(data: Any) -> List[str]:
    """Return a list of human-readable problems with truth-table *data*."""
    problems: List[str] = []
    if not isinstance(data, dict):
        return [f"truth table root must be a mapping, got {type(data).__name__}"]
    if data.get("schema") != CATALOG_SCHEMA:
        problems.append(f"schema must be {CATALOG_SCHEMA!r}, got {data.get('schema')!r}")
    if data.get("slice") != "M-013":
        problems.append(f"slice must be 'M-013', got {data.get('slice')!r}")
    for key in ("recorded", "scope_note"):
        if not isinstance(data.get(key), str) or not data[key]:
            problems.append(f"{key} must be a non-empty string")
    _check_cells(data.get("cells"), problems)
    return problems


def _to_truth(data: Dict[str, Any]) -> PlatformTruth:
    return PlatformTruth(
        recorded=data["recorded"],
        scope_note=data["scope_note"],
        cells=tuple(
            Cell(
                id=c["id"], platform=c["platform"], surface=c["surface"],
                verdict=c["verdict"], evidence_kind=c["evidence_kind"],
                evidence=c["evidence"], retest=c["retest"],
            )
            for c in data["cells"]
        ),
    )


def load_truth(data: Optional[Dict[str, Any]] = None) -> PlatformTruth:
    """Load and validate the shipped platform truth table (or *data*).

    Raises :class:`~mythic_agent.core.validation.ValidationError`
    listing every problem when the data is not a well-formed table.
    """
    raw = data if data is not None else load_resource(CATALOG_RESOURCE)
    problems = validate_truth(raw)
    if problems:
        raise ValidationError(
            "platform truth table failed validation: " + "; ".join(problems)
        )
    return _to_truth(raw)  # type: ignore[arg-type]


def render_markdown(truth: PlatformTruth) -> str:
    """Render the truth table as markdown, platform by platform.

    Built from :meth:`PlatformTruth.counts`,
    :meth:`PlatformTruth.verdict_for`,
    :meth:`PlatformTruth.proven_cells`, and
    :meth:`PlatformTruth.not_proven_cells`, so the rendered page is
    computed from the same accessors the tests pin.
    """
    n_cells, n_proven = truth.counts()
    lines = [
        "# Platform Truth Table — PROVEN or NOT PROVEN, no inheritance (M-013)",
        "",
        f"*Recorded {truth.recorded}: {n_cells} cells, {n_proven} PROVEN, "
        f"{n_cells - n_proven} NOT PROVEN.*",
        "",
        truth.scope_note,
        "",
    ]
    by_pair = {(c.platform, c.surface): c for c in truth.cells}
    for platform in PLATFORMS:
        lines += [f"## {platform}", ""]
        for surface in SURFACES:
            cell = by_pair[(platform, surface)]
            verdict = truth.verdict_for(platform, surface)
            lines.append(
                f"- {cell.id} {surface}: **{verdict}** "
                f"({cell.evidence_kind}) — {cell.evidence} "
                f"Re-test: {cell.retest}"
            )
        lines.append("")
    lines += [
        "## The count, plainly",
        "",
        f"PROVEN: {', '.join(truth.proven_cells()) or 'none'}.",
        f"NOT PROVEN: {', '.join(truth.not_proven_cells()) or 'none'}.",
        "",
    ]
    return "\n".join(lines)
