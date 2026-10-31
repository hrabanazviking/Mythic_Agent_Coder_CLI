"""The Gap Audit (All-Features roadmap slice M-003).

The census (M-001) names every gap and the slice that owns it; this
audit traces each of those 24 PARTIAL/MISSING rows to the *module* that
will own its fix, and records the classification of the campaign
baseline's five unclassified test failures. Data lives in
``mythic_agent/data/gap_audit.yaml``; this module loads, validates, and
renders it.

Honesty rules, enforced by :func:`validate_audit`:

* Every census gap has exactly one audit row, and every audit row is a
  census gap — the two files cannot drift apart silently.
* ``slice`` and ``state`` on a row must match the census row's
  ``roadmap_ref`` and Mythic state.
* ``module_kind`` is ``existing`` or ``proposed`` and is checked
  against the tree at validation time when a repository root is given:
  an ``existing`` module must be present, a ``proposed`` one absent.
  (Without a root, only the data's internal consistency is checked, so
  installed wheels can still load the audit.)
* Every baseline-failure entry carries a verdict from a fixed set and
  non-empty evidence — a classification without evidence is a guess.
"""

from __future__ import annotations

__all__ = [
    "AUDIT_RESOURCE",
    "AUDIT_SCHEMA",
    "FAILURE_VERDICTS",
    "MODULE_KINDS",
    "Any",
    "AuditRow",
    "Dict",
    "FailureFinding",
    "GapAudit",
    "List",
    "Optional",
    "Path",
    "Tuple",
    "load_audit",
    "render_markdown",
    "validate_audit",
]

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .feature_census import load_census
from .validation import ValidationError

#: Resource name of the audit data file inside ``mythic_agent/data``.
AUDIT_RESOURCE = "gap_audit.yaml"

#: The only schema this loader accepts.
AUDIT_SCHEMA = "mythic.gap_audit/1"

#: A module either already stands in the tree or is proposed by the audit.
MODULE_KINDS = ("existing", "proposed")

#: Verdicts a baseline failure may carry — evidence decides, not vibes.
FAILURE_VERDICTS = ("product-defect", "test-timing", "environment", "unclassified")

_SLICE_REF = re.compile(r"^M-\d{3}$")
_PARTS = ("I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI")

# Roadmap part boundaries (All-Features roadmap, section 4 table).
_PART_RANGES = (
    ("I", 1, 18), ("II", 19, 42), ("III", 43, 70), ("IV", 71, 94),
    ("V", 95, 120), ("VI", 121, 146), ("VII", 147, 170),
    ("VIII", 171, 200), ("IX", 201, 232), ("X", 233, 254),
    ("XI", 255, 272),
)


def _part_for(slice_ref: str) -> Optional[str]:
    number = int(slice_ref.split("-")[1])
    for part, lo, hi in _PART_RANGES:
        if lo <= number <= hi:
            return part
    return None


@dataclass(frozen=True)
class AuditRow:
    """One census gap traced to its owning module."""

    feature: str
    slice: str
    part: str
    state: str
    owning_module: str
    module_kind: str
    basis: str
    fix_shape: str


@dataclass(frozen=True)
class FailureFinding:
    """One classified baseline failure."""

    test: str
    verdict: str
    fixed_in: str
    evidence: str


@dataclass(frozen=True)
class GapAudit:
    """The validated audit: one row per census gap, plus findings."""

    audited: str
    source_note: str
    rows: Tuple[AuditRow, ...]
    baseline_failures: Tuple[FailureFinding, ...]

    def row(self, feature_id: str) -> AuditRow:
        """Return the audit row for *feature_id* (KeyError if absent)."""
        for row in self.rows:
            if row.feature == feature_id:
                return row
        raise KeyError(f"no audit row for feature {feature_id!r}")

    def rows_for_part(self, part: str) -> Tuple[AuditRow, ...]:
        """Rows whose owning slice sits in roadmap part *part*."""
        return tuple(row for row in self.rows if row.part == part)

    def verdicts(self) -> Dict[str, int]:
        """Baseline-failure verdict -> number of findings."""
        tally = {verdict: 0 for verdict in FAILURE_VERDICTS}
        for finding in self.baseline_failures:
            tally[finding.verdict] += 1
        return tally


def validate_audit(
    data: Any, repo_root: Optional[Path] = None
) -> List[str]:
    """Return a list of human-readable problems with audit *data*.

    Cross-checks the shipped census: row set, slice, and state must
    agree with it exactly. When *repo_root* is given, ``module_kind``
    claims are also checked against the real tree.
    """
    problems: List[str] = []
    if not isinstance(data, dict):
        return [f"audit root must be a mapping, got {type(data).__name__}"]
    if data.get("schema") != AUDIT_SCHEMA:
        problems.append(f"schema must be {AUDIT_SCHEMA!r}, got {data.get('schema')!r}")
    if not isinstance(data.get("audited"), str) or not data["audited"]:
        problems.append("audited must be a non-empty date string")

    census = load_census()
    gaps = {row.id: row for row in census.gaps()}

    rows = data.get("rows")
    if not isinstance(rows, list) or not rows:
        problems.append("rows must be a non-empty list")
        return problems
    seen: set = set()
    for row in rows:
        if not isinstance(row, dict):
            problems.append(f"audit row is not a mapping: {row!r}")
            continue
        fid = row.get("feature")
        label = fid if isinstance(fid, str) and fid else repr(row)[:60]
        if not fid or fid in seen:
            problems.append(f"audit row feature missing or duplicated: {label}")
        seen.add(fid)
        gap = gaps.get(fid) if isinstance(fid, str) else None
        if gap is None:
            problems.append(f"audit row {label}: not a census gap (PARTIAL/MISSING) feature")
            continue
        if row.get("slice") != gap.roadmap_ref:
            problems.append(
                f"audit row {label}: slice {row.get('slice')!r} != census owner {gap.roadmap_ref!r}"
            )
        if row.get("state") != gap.mythic.state:
            problems.append(
                f"audit row {label}: state {row.get('state')!r} != census state {gap.mythic.state!r}"
            )
        slice_ref = row.get("slice")
        if not isinstance(slice_ref, str) or not _SLICE_REF.match(slice_ref):
            problems.append(f"audit row {label}: slice must look like 'M-044'")
        elif row.get("part") != _part_for(slice_ref):
            problems.append(
                f"audit row {label}: part {row.get('part')!r} != roadmap part {_part_for(slice_ref)!r} for {slice_ref}"
            )
        if row.get("part") not in _PARTS:
            problems.append(f"audit row {label}: part must be one of {_PARTS}")
        kind = row.get("module_kind")
        if kind not in MODULE_KINDS:
            problems.append(f"audit row {label}: module_kind must be one of {MODULE_KINDS}")
        module = row.get("owning_module")
        if not isinstance(module, str) or not module:
            problems.append(f"audit row {label}: owning_module must be non-empty")
        elif repo_root is not None and kind in MODULE_KINDS:
            exists = (repo_root / module).exists()
            if kind == "existing" and not exists:
                problems.append(f"audit row {label}: owning_module {module} marked existing but absent")
            if kind == "proposed" and exists:
                problems.append(f"audit row {label}: owning_module {module} marked proposed but present")
        for key in ("basis", "fix_shape"):
            if not row.get(key):
                problems.append(f"audit row {label}: {key} must be non-empty")
    missing = [fid for fid in gaps if fid not in seen]
    if missing:
        problems.append(f"census gaps with no audit row: {missing}")

    findings = data.get("baseline_failures")
    if not isinstance(findings, list) or not findings:
        problems.append("baseline_failures must be a non-empty list")
    else:
        for finding in findings:
            if not isinstance(finding, dict):
                problems.append(f"baseline failure is not a mapping: {finding!r}")
                continue
            if finding.get("verdict") not in FAILURE_VERDICTS:
                problems.append(
                    f"baseline failure {finding.get('test')!r}: verdict must be one of {FAILURE_VERDICTS}"
                )
            if not finding.get("evidence"):
                problems.append(
                    f"baseline failure {finding.get('test')!r}: evidence must be non-empty"
                )
            if not finding.get("test"):
                problems.append("baseline failure: test must be non-empty")
    return problems


def _to_audit(data: Dict[str, Any]) -> GapAudit:
    rows = tuple(
        AuditRow(
            feature=r["feature"],
            slice=r["slice"],
            part=r["part"],
            state=r["state"],
            owning_module=r["owning_module"],
            module_kind=r["module_kind"],
            basis=r["basis"],
            fix_shape=r["fix_shape"],
        )
        for r in data["rows"]
    )
    findings = tuple(
        FailureFinding(
            test=f["test"],
            verdict=f["verdict"],
            fixed_in=f.get("fixed_in", ""),
            evidence=f["evidence"],
        )
        for f in data["baseline_failures"]
    )
    return GapAudit(
        audited=data["audited"],
        source_note=data.get("source_note", ""),
        rows=rows,
        baseline_failures=findings,
    )


def load_audit(
    data: Optional[Dict[str, Any]] = None,
    repo_root: Optional[Path] = None,
) -> GapAudit:
    """Load and validate the shipped gap audit (or *data* when given).

    Raises :class:`~mythic_agent.core.validation.ValidationError`
    listing every problem when the data is not a well-formed audit.
    """
    raw = data if data is not None else load_resource(AUDIT_RESOURCE)
    problems = validate_audit(raw, repo_root=repo_root)
    if problems:
        raise ValidationError("gap audit failed validation: " + "; ".join(problems))
    return _to_audit(raw)  # type: ignore[arg-type]


def render_markdown(audit: GapAudit) -> str:
    """Render the audit as markdown: gaps by part, then the findings."""
    lines = [
        "# Gap Audit — every census gap traced to its owning module",
        "",
        f"*Audited {audit.audited}. Slice M-003 of the All-Features road.*",
        "",
        audit.source_note,
        "",
        "| Feature | State | Owning slice | Part | Owning module | Kind |",
        "|---|---|---|---|---|---|",
    ]
    for row in audit.rows:
        lines.append(
            f"| {row.feature} | {row.state} | {row.slice} | {row.part} "
            f"| `{row.owning_module}` | {row.module_kind} |"
        )
    lines += ["", "## The gaps, by part", ""]
    for part in _PARTS:
        part_rows = audit.rows_for_part(part)
        if part_rows:
            lines.append(
                f"- Part {part}: {len(part_rows)} gap(s) — "
                + ", ".join(f"{row.feature} ({row.slice})" for row in part_rows)
            )
    tally = audit.verdicts()
    lines += [
        "",
        "## Baseline failures, classified",
        "",
        "Verdict tally: "
        + ", ".join(f"{verdict} {count}" for verdict, count in tally.items() if count)
        + ".",
        "",
    ]
    for finding in audit.baseline_failures:
        lines.append(f"- **{finding.test}** — {finding.verdict} (fixed in {finding.fixed_in}).")
    lines.append("")
    return "\n".join(lines)
