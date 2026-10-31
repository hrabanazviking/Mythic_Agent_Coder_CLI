"""The roadmap made data (All-Features roadmap slice M-017).

This road's own 272 slices, in a machine file the app itself can
display, check off, and report — Part IX's method engine eats first
from its own kitchen. Data lives in
``mythic_agent/data/roadmap_slices.yaml`` (generated from the
roadmap's text by the M-017 generator); this module loads, validates,
and renders it. The honesty rules are enforced by
:func:`validate_roadmap`:

* Exactly 11 parts and 272 slices — the road as Volmarr approved it;
  a slice cannot quietly appear or vanish.
* Slice ids are ``M-001``..``M-272``, unique and sequential, and part
  ranges are contiguous: part *n* starts the slice after part *n-1*
  ended, part I starts at M-001, part XI ends at M-272.
* Part numbering is sequential in arabic and roman alike.
* A slice's status is ``done`` or ``queued``, and done slices form a
  prefix of the road: the campaign banks in order, so a done slice
  after a queued one is a ledger error, not a state.
* Every slice carries the roadmap's own title and summary — no empty
  rows, no invented text.
"""

from __future__ import annotations

__all__ = [
    "ROADMAP_RESOURCE",
    "ROADMAP_SCHEMA",
    "STATUSES",
    "TOTAL_PARTS",
    "TOTAL_SLICES",
    "Any",
    "Dict",
    "List",
    "Optional",
    "Roadmap",
    "RoadmapPart",
    "RoadmapSlice",
    "Tuple",
    "load_roadmap",
    "render_markdown",
    "validate_roadmap",
]

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .validation import ValidationError

#: Resource name of the roadmap data file inside ``mythic_agent/data``.
ROADMAP_RESOURCE = "roadmap_slices.yaml"

#: The only schema this loader accepts.
ROADMAP_SCHEMA = "mythic.roadmap_slices/1"

#: The road's fixed shape, as approved 2026-10-30.
TOTAL_PARTS = 11
TOTAL_SLICES = 272

#: The only slice statuses the ledger knows.
STATUSES = ("done", "queued")

_ROMAN = ("I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI")
_ID_RE = re.compile(r"^M-\d{3}$")


@dataclass(frozen=True)
class RoadmapPart:
    """One part of the road: a numbered, titled run of slices."""

    number: int
    roman: str
    title: str
    first_slice: str
    last_slice: str


@dataclass(frozen=True)
class RoadmapSlice:
    """One slice of the road, with its ledger status."""

    id: str
    part: int
    title: str
    summary: str
    status: str


@dataclass(frozen=True)
class Roadmap:
    """The validated road: parts, slices, and the check-off ledger."""

    roadmap: str
    source_note: str
    parts: Tuple[RoadmapPart, ...]
    slices: Tuple[RoadmapSlice, ...]

    def part(self, number: int) -> RoadmapPart:
        """Return part *number* (KeyError if absent)."""
        for part in self.parts:
            if part.number == number:
                return part
        raise KeyError(f"no part {number!r}")

    def slice(self, slice_id: str) -> RoadmapSlice:
        """Return the slice with id *slice_id* (KeyError if absent)."""
        for slice_ in self.slices:
            if slice_.id == slice_id:
                return slice_
        raise KeyError(f"no slice {slice_id!r}")

    def by_part(self, number: int) -> Tuple[RoadmapSlice, ...]:
        """Every slice in part *number*, in road order."""
        return tuple(s for s in self.slices if s.part == number)

    def done(self) -> Tuple[RoadmapSlice, ...]:
        """Every slice the ledger marks done, in road order."""
        return tuple(s for s in self.slices if s.status == "done")

    def next_slice(self) -> Optional[RoadmapSlice]:
        """The first queued slice — where the campaign resumes."""
        for slice_ in self.slices:
            if slice_.status == "queued":
                return slice_
        return None

    def progress(self) -> Tuple[Tuple[RoadmapPart, int, int], ...]:
        """Per-part progress as (part, done count, slice count)."""
        rows = []
        for part in self.parts:
            members = self.by_part(part.number)
            rows.append(
                (part, sum(1 for s in members if s.status == "done"), len(members))
            )
        return tuple(rows)


def validate_roadmap(data: Any) -> List[str]:
    """Return a list of human-readable problems with roadmap *data*."""
    problems: List[str] = []
    if not isinstance(data, dict):
        return [f"roadmap root must be a mapping, got {type(data).__name__}"]
    if data.get("schema") != ROADMAP_SCHEMA:
        problems.append(
            f"schema must be {ROADMAP_SCHEMA!r}, got {data.get('schema')!r}"
        )
    for key in ("roadmap", "source_note"):
        if not isinstance(data.get(key), str) or not data[key]:
            problems.append(f"{key} must be a non-empty string")

    parts = data.get("parts")
    if not isinstance(parts, list) or not parts:
        problems.append("parts must be a non-empty list")
        return problems
    if len(parts) != TOTAL_PARTS:
        problems.append(
            f"parts must number exactly {TOTAL_PARTS} (the approved road), "
            f"got {len(parts)}"
        )
    parsed_parts: List[Tuple[int, str, str]] = []  # (number, first, last)
    for position, part in enumerate(parts, start=1):
        if not isinstance(part, dict):
            problems.append(f"part is not a mapping: {part!r}")
            continue
        number = part.get("number")
        label = f"part {number!r}" if number else f"part at position {position}"
        if number != position:
            problems.append(
                f"{label}: part numbers must be sequential, expected {position}"
            )
        if position <= len(_ROMAN) and part.get("roman") != _ROMAN[position - 1]:
            problems.append(
                f"{label}: roman numeral must be {_ROMAN[position - 1]!r}, "
                f"got {part.get('roman')!r}"
            )
        if not isinstance(part.get("title"), str) or not part["title"]:
            problems.append(f"{label}: title must be non-empty")
        first, last = part.get("first_slice"), part.get("last_slice")
        for key, value in (("first_slice", first), ("last_slice", last)):
            if not isinstance(value, str) or not _ID_RE.match(value):
                problems.append(f"{label}: {key} must look like 'M-001'")
        if (
            isinstance(first, str)
            and isinstance(last, str)
            and _ID_RE.match(first)
            and _ID_RE.match(last)
        ):
            if first > last:
                problems.append(f"{label}: range {first}..{last} is inverted")
            parsed_parts.append((position, first, last))
    for prev, curr in zip(parsed_parts, parsed_parts[1:]):
        expected = f"M-{int(prev[2][2:]) + 1:03d}"
        if curr[1] != expected:
            problems.append(
                f"part {curr[0]}: ranges must be contiguous, expected first "
                f"slice {expected} after part {prev[0]} ended at {prev[2]}, "
                f"got {curr[1]}"
            )
    if parsed_parts:
        if parsed_parts[0][1] != "M-001":
            problems.append(
                f"part I must start at M-001, got {parsed_parts[0][1]}"
            )
        if parsed_parts[-1][2] != f"M-{TOTAL_SLICES:03d}":
            problems.append(
                f"the last part must end at M-{TOTAL_SLICES:03d}, "
                f"got {parsed_parts[-1][2]}"
            )

    slices = data.get("slices")
    if not isinstance(slices, list) or not slices:
        problems.append("slices must be a non-empty list")
        return problems
    if len(slices) != TOTAL_SLICES:
        problems.append(
            f"slices must number exactly {TOTAL_SLICES} (the approved road), "
            f"got {len(slices)}"
        )
    seen_queued = False
    for position, slice_ in enumerate(slices, start=1):
        if not isinstance(slice_, dict):
            problems.append(f"slice is not a mapping: {slice_!r}")
            continue
        sid = slice_.get("id")
        label = sid if isinstance(sid, str) and sid else repr(slice_)[:60]
        expected = f"M-{position:03d}"
        if not isinstance(sid, str) or not _ID_RE.match(sid):
            problems.append(f"slice {label}: id must look like 'M-001'")
        elif sid != expected:
            problems.append(
                f"slice {label}: ids must be sequential, expected {expected}"
            )
        part_no = slice_.get("part")
        if not isinstance(part_no, int) or not 1 <= part_no <= TOTAL_PARTS:
            problems.append(f"slice {label}: part must be 1..{TOTAL_PARTS}")
        elif (
            part_no <= len(parsed_parts)
            and isinstance(sid, str)
            and _ID_RE.match(sid)
        ):
            _, first, last = parsed_parts[part_no - 1]
            if not first <= sid <= last:
                problems.append(
                    f"slice {label}: part {part_no} spans {first}..{last}, "
                    "so this slice does not belong to it"
                )
        for key in ("title", "summary"):
            if not isinstance(slice_.get(key), str) or not slice_[key]:
                problems.append(f"slice {label}: {key} must be non-empty")
        status = slice_.get("status")
        if status not in STATUSES:
            problems.append(
                f"slice {label}: status must be one of {STATUSES}, "
                f"got {status!r}"
            )
        elif status == "queued":
            seen_queued = True
        elif seen_queued:
            problems.append(
                f"slice {label}: done slices must form a prefix of the road "
                "(the campaign banks in order); a done slice follows a "
                "queued one"
            )
    return problems


def _to_roadmap(data: Dict[str, Any]) -> Roadmap:
    return Roadmap(
        roadmap=data["roadmap"],
        source_note=data["source_note"],
        parts=tuple(
            RoadmapPart(
                number=p["number"],
                roman=p["roman"],
                title=p["title"],
                first_slice=p["first_slice"],
                last_slice=p["last_slice"],
            )
            for p in data["parts"]
        ),
        slices=tuple(
            RoadmapSlice(
                id=s["id"],
                part=s["part"],
                title=s["title"],
                summary=s["summary"],
                status=s["status"],
            )
            for s in data["slices"]
        ),
    )


def load_roadmap(data: Optional[Dict[str, Any]] = None) -> Roadmap:
    """Load and validate the shipped roadmap data (or *data*).

    Raises :class:`~mythic_agent.core.validation.ValidationError`
    listing every problem when the data is not a well-formed road.
    """
    raw = data if data is not None else load_resource(ROADMAP_RESOURCE)
    problems = validate_roadmap(raw)
    if problems:
        raise ValidationError(
            "roadmap slices failed validation: " + "; ".join(problems)
        )
    return _to_roadmap(raw)  # type: ignore[arg-type]


def render_markdown(roadmap: Roadmap) -> str:
    """Render the road as markdown: progress per part, then the slices."""
    done = roadmap.done()
    nxt = roadmap.next_slice()
    lines = [
        "# The All-Features Road — slices as data",
        "",
        f"*{roadmap.roadmap}. Slice M-017 of the All-Features road.*",
        "",
        roadmap.source_note,
        "",
        f"**Progress: {len(done)} of {len(roadmap.slices)} slices done.**",
        "",
    ]
    if nxt is not None:
        lines.append(
            f"**Next slice: {nxt.id} — {nxt.title}** (part {nxt.part})."
        )
        lines.append("")
    lines += ["## Parts", ""]
    for part, done_count, total in roadmap.progress():
        lines.append(
            f"- Part {part.roman} — {part.title} "
            f"({part.first_slice}..{part.last_slice}): {done_count}/{total} done"
        )
    lines.append("")
    for part in roadmap.parts:
        lines.append(
            f"## Part {part.roman} — {part.title} "
            f"({part.first_slice}..{part.last_slice})"
        )
        lines.append("")
        for slice_ in roadmap.by_part(part.number):
            mark = "x" if slice_.status == "done" else " "
            lines.append(f"- [{mark}] **{slice_.id}** {slice_.title}: {slice_.summary}")
        lines.append("")
    return "\n".join(lines)
