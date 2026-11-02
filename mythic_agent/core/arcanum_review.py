"""The Arcanum Review (All-Features roadmap slice M-011).

The 116 KB standalone Golden Dawn tarot TUI at ``arcanum/arcanum.py``
mapped as validated data: every banner-delimited section with its
line span in the reviewed file, what it owns, what it duplicates in
the ``mythic_agent`` package, and the verdict for Parts III, VI, and
VII — absorb or leave — with the section's disposition.

The verdict of the whole review: LEAVE. ``arcanum/`` is an adjacent
project (ARCHITECTURE.md says so, and this review proves it section
by section): it holds no code-intelligence surface for Part III, no
agents or delegation for Part VI, and no retrievable memory for
Part VII. The two genuine duplication risks — plaintext key custody
in its own config, and an AI reading that bypasses the package
provider layer — are recorded as findings with their absorbing
parts named (Kista via Part II M-032; the OpenRouterProvider via
Part II), so a future integration has its roads marked.

The review also proved three defects in the file, all fixed in this
slice and recorded in the data: D-01 the file did not compile (a
lost ``return`` and a lost ``def ai_reading`` line), D-02
``render_celtic_cross_layout`` was called but never defined, and
D-03 the ``reversal_pct`` setting was never wired to the draw. The
tests in ``tests/test_arcanum_review.py`` cross-check the review
against the live file (sha256, line spans, anchors, AST) so the map
cannot silently drift from the territory.

Data lives in ``mythic_agent/data/arcanum_review.yaml``.
"""

from __future__ import annotations

__all__ = [
    "CATALOG_RESOURCE",
    "CATALOG_SCHEMA",
    "Any",
    "ArcanumReview",
    "DefectEntry",
    "Dict",
    "FindingEntry",
    "List",
    "Optional",
    "SectionEntry",
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
CATALOG_RESOURCE = "arcanum_review.yaml"

#: The only schema this loader accepts.
CATALOG_SCHEMA = "mythic.arcanum_review/1"

SECTION_KINDS = (
    "data",
    "config",
    "domain",
    "engine",
    "entry",
    "flow",
    "rendering",
    "tui",
)

VERDICTS = ("absorb", "leave")
_PARTS = ("iii", "vi", "vii")

_SECTION_ID_RE = re.compile(r"^A-\d{2}$")
_DEFECT_ID_RE = re.compile(r"^D-\d{2}$")
_FINDING_ID_RE = re.compile(r"^F-\d{2}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class SectionEntry:
    """One mapped section of arcanum.py."""

    id: str
    name: str
    kind: str
    lines: Tuple[int, int]
    anchor: str
    owns: str
    duplicates: str
    verdict_part_iii: str
    verdict_part_vi: str
    verdict_part_vii: str
    disposition: str


@dataclass(frozen=True)
class DefectEntry:
    """One defect the review proved in the file."""

    id: str
    name: str
    section: str
    evidence: str
    status: str
    fix: str


@dataclass(frozen=True)
class FindingEntry:
    """One recorded finding (a road marked, not a repair owed)."""

    id: str
    name: str
    note: str


@dataclass(frozen=True)
class ArcanumReview:
    """The validated arcanum review: sections, defects, findings."""

    reviewed: str
    file: str
    file_lines: int
    file_bytes: int
    file_sha256: str
    scope_note: str
    overall_verdict: str
    sections: Tuple[SectionEntry, ...]
    defects: Tuple[DefectEntry, ...]
    findings: Tuple[FindingEntry, ...]

    def section_names(self) -> Tuple[str, ...]:
        """Every mapped section name, in file order."""
        return tuple(s.name for s in self.sections)

    def verdict_of(self, name: str, part: str) -> str:
        """The verdict ('absorb' or 'leave') of section *name* for *part*.

        *part* is one of 'iii', 'vi', 'vii'.
        """
        if part not in _PARTS:
            raise KeyError(part)
        for entry in self.sections:
            if entry.name == name:
                return getattr(entry, f"verdict_part_{part}")
        raise KeyError(name)

    def defect_ids(self) -> Tuple[str, ...]:
        """Every recorded defect id, in order."""
        return tuple(d.id for d in self.defects)

    def counts(self) -> Tuple[int, int, int]:
        """(sections, defects, findings) as recorded."""
        return (len(self.sections), len(self.defects), len(self.findings))


def validate_review(data: Any) -> List[str]:
    """Return a list of human-readable problems with review *data*."""
    problems: List[str] = []
    if not isinstance(data, dict):
        return [f"review root must be a mapping, got {type(data).__name__}"]
    if data.get("schema") != CATALOG_SCHEMA:
        problems.append(
            f"schema must be {CATALOG_SCHEMA!r}, got {data.get('schema')!r}"
        )
    if data.get("slice") != "M-011":
        problems.append(f"slice must be 'M-011', got {data.get('slice')!r}")
    for key in ("reviewed", "scope_note", "overall_verdict"):
        if not isinstance(data.get(key), str) or not data[key]:
            problems.append(f"{key} must be a non-empty string")
    if data.get("file") != "arcanum/arcanum.py":
        problems.append(f"file must be 'arcanum/arcanum.py', got {data.get('file')!r}")
    if isinstance(data.get("scope_note"), str) and "arcanum" not in data["scope_note"]:
        problems.append("scope_note must name the arcanum (the review's subject)")
    if isinstance(data.get("overall_verdict"), str) and not data[
        "overall_verdict"
    ].startswith("LEAVE"):
        problems.append("overall_verdict must open with the LEAVE verdict")
    for key in ("file_lines", "file_bytes"):
        if not isinstance(data.get(key), int) or data[key] <= 0:
            problems.append(f"{key} must be a positive integer")
    if not isinstance(data.get("file_sha256"), str) or not _SHA256_RE.match(
        data["file_sha256"]
    ):
        problems.append("file_sha256 must be a 64-char lowercase hex digest")

    sections = data.get("sections")
    if not isinstance(sections, list) or not sections:
        problems.append("sections must be a non-empty list")
        return problems
    seen: set = set()
    expected_start = 1
    for position, entry in enumerate(sections, start=1):
        if not isinstance(entry, dict):
            problems.append(f"sections entry is not a mapping: {entry!r}")
            continue
        eid = entry.get("id")
        expected = f"A-{position:02d}"
        if not isinstance(eid, str) or not _SECTION_ID_RE.match(eid):
            problems.append(f"sections entry {eid!r}: id must look like 'A-01'")
        elif eid != expected:
            problems.append(
                f"sections entry {eid}: ids must be sequential, expected {expected}"
            )
        for key in ("name", "kind", "anchor", "owns", "duplicates", "disposition"):
            if not isinstance(entry.get(key), str) or not entry[key]:
                problems.append(f"sections entry {eid}: {key} must be non-empty")
        if isinstance(entry.get("kind"), str) and entry["kind"] not in SECTION_KINDS:
            problems.append(
                f"section {entry.get('name')!r}: kind {entry.get('kind')!r} "
                f"not in {SECTION_KINDS}"
            )
        name = entry.get("name")
        if isinstance(name, str):
            if name in seen:
                problems.append(f"sections entry {name!r} is named twice")
            seen.add(name)
        for part in _PARTS:
            verdict = entry.get(f"verdict_part_{part}")
            if verdict not in VERDICTS:
                problems.append(
                    f"section {name!r}: verdict_part_{part} must be one of "
                    f"{VERDICTS}, got {verdict!r}"
                )
        span = entry.get("lines")
        if (
            not isinstance(span, list)
            or len(span) != 2
            or any(not isinstance(v, int) for v in span)
        ):
            problems.append(f"section {name!r}: lines must be a [start, end] pair")
        else:
            if span[0] != expected_start:
                problems.append(
                    f"section {name!r}: lines must be contiguous, "
                    f"expected start {expected_start}, got {span[0]}"
                )
            if span[1] < span[0]:
                problems.append(f"section {name!r}: lines end before they start")
            else:
                expected_start = span[1] + 1
    if isinstance(data.get("file_lines"), int) and expected_start - 1 != data[
        "file_lines"
    ]:
        problems.append(
            f"sections must cover the whole file: they end at "
            f"{expected_start - 1}, file_lines is {data['file_lines']}"
        )

    for group, id_re, prefix in (
        ("defects", _DEFECT_ID_RE, "D"),
        ("findings", _FINDING_ID_RE, "F"),
    ):
        entries = data.get(group)
        if not isinstance(entries, list) or not entries:
            problems.append(f"{group} must be a non-empty list")
            continue
        for position, entry in enumerate(entries, start=1):
            if not isinstance(entry, dict):
                problems.append(f"{group} entry is not a mapping: {entry!r}")
                continue
            eid = entry.get("id")
            expected = f"{prefix}-{position:02d}"
            if not isinstance(eid, str) or not id_re.match(eid):
                problems.append(f"{group} entry {eid!r}: id must look like '{prefix}-01'")
            elif eid != expected:
                problems.append(
                    f"{group} entry {eid}: ids must be sequential, expected {expected}"
                )
            keys = (
                ("name", "section", "evidence", "status", "fix")
                if group == "defects"
                else ("name", "note")
            )
            for key in keys:
                if not isinstance(entry.get(key), str) or not entry[key]:
                    problems.append(f"{group} entry {eid}: {key} must be non-empty")
            if group == "defects" and entry.get("status") != "fixed-in-slice":
                problems.append(
                    f"defect {eid}: status must be 'fixed-in-slice' — a proven "
                    "defect is fixed in its slice or commissioned, never left noted"
                )
    return problems


def _to_review(data: Dict[str, Any]) -> ArcanumReview:
    return ArcanumReview(
        reviewed=data["reviewed"],
        file=data["file"],
        file_lines=data["file_lines"],
        file_bytes=data["file_bytes"],
        file_sha256=data["file_sha256"],
        scope_note=data["scope_note"],
        overall_verdict=data["overall_verdict"],
        sections=tuple(
            SectionEntry(
                id=s["id"], name=s["name"], kind=s["kind"],
                lines=(s["lines"][0], s["lines"][1]), anchor=s["anchor"],
                owns=s["owns"], duplicates=s["duplicates"],
                verdict_part_iii=s["verdict_part_iii"],
                verdict_part_vi=s["verdict_part_vi"],
                verdict_part_vii=s["verdict_part_vii"],
                disposition=s["disposition"],
            )
            for s in data["sections"]
        ),
        defects=tuple(
            DefectEntry(
                id=d["id"], name=d["name"], section=d["section"],
                evidence=d["evidence"], status=d["status"], fix=d["fix"],
            )
            for d in data["defects"]
        ),
        findings=tuple(
            FindingEntry(id=f["id"], name=f["name"], note=f["note"])
            for f in data["findings"]
        ),
    )


def load_review(data: Optional[Dict[str, Any]] = None) -> ArcanumReview:
    """Load and validate the shipped arcanum review (or *data*).

    Raises :class:`~mythic_agent.core.validation.ValidationError`
    listing every problem when the data is not a well-formed review.
    """
    raw = data if data is not None else load_resource(CATALOG_RESOURCE)
    problems = validate_review(raw)
    if problems:
        raise ValidationError(
            "arcanum review failed validation: " + "; ".join(problems)
        )
    return _to_review(raw)  # type: ignore[arg-type]


def render_markdown(review: ArcanumReview) -> str:
    """Render the review as markdown: verdict, sections, defects, findings.

    Built from :meth:`ArcanumReview.counts`,
    :meth:`ArcanumReview.section_names`,
    :meth:`ArcanumReview.verdict_of`, and
    :meth:`ArcanumReview.defect_ids`, so the rendered page is computed
    from the same accessors the tests pin.
    """
    n_sections, n_defects, n_findings = review.counts()
    lines = [
        "# The Arcanum Review — arcanum/arcanum.py mapped (M-011)",
        "",
        f"*Reviewed {review.reviewed}: {review.file} — {review.file_lines} lines, "
        f"{review.file_bytes} bytes, sha256 {review.file_sha256}. "
        f"{n_sections} sections, {n_defects} defects, {n_findings} findings.*",
        "",
        review.scope_note,
        "",
        f"**Overall verdict:** {review.overall_verdict}",
        "",
        "## Sections",
        "",
    ]
    by_name = {s.name: s for s in review.sections}
    for name in review.section_names():
        entry = by_name[name]
        lines.append(
            f"- {entry.id} `{entry.name}` ({entry.kind}, lines "
            f"{entry.lines[0]}–{entry.lines[1]}) — owns: {entry.owns} "
            f"Duplicates: {entry.duplicates} "
            f"Verdicts: Part III {review.verdict_of(name, 'iii')}, "
            f"Part VI {review.verdict_of(name, 'vi')}, "
            f"Part VII {review.verdict_of(name, 'vii')}. {entry.disposition}"
        )
    lines += ["", "## Defects (all fixed in-slice)", ""]
    by_id = {d.id: d for d in review.defects}
    for defect_id in review.defect_ids():
        defect = by_id[defect_id]
        lines.append(
            f"- {defect.id} {defect.name} [{defect.section}] — "
            f"{defect.evidence} Fix: {defect.fix}"
        )
    lines += ["", "## Findings", ""]
    for finding in review.findings:
        lines.append(f"- {finding.id} {finding.name} — {finding.note}")
    lines.append("")
    return "\n".join(lines)
