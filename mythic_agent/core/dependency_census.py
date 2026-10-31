"""The Dependency Census (All-Features roadmap slice M-012).

Every dependency declared in ``pyproject.toml`` — core, every extra,
the dev extra, and the build system — weighed as validated data:
where it is declared, its version spec, its licence, its necessity,
what the package actually uses it for, and its installed weight
measured in the baseline venv (or an honest ``unmeasured`` where the
baseline venv does not install it).

Alongside the census sits the stdlib-first replacement list: each
candidate replacement evaluated, with a verdict. Only two verdicts
claim a real win — ``stdlib-win`` (a standard-library module does
the whole job) and ``already-core-win`` (a core dependency already
does the job, so an extra's duplicate can go). Everything else is
recorded as ``no-real-win`` with its reason, so the list cannot be
quoted as promising savings it does not contain.

The tests cross-check the census against the live ``pyproject.toml``
(declared names and groups, computed with ``tomllib``) and against
the live third-party import scan, so a new dependency cannot land
uncensused and a censused one cannot silently vanish.

Data lives in ``mythic_agent/data/dependency_census.yaml``.
"""

from __future__ import annotations

__all__ = [
    "CATALOG_RESOURCE",
    "CATALOG_SCHEMA",
    "Any",
    "Dependency",
    "DependencyCensus",
    "Dict",
    "List",
    "Optional",
    "Replacement",
    "load_census",
    "render_markdown",
    "validate_census",
    "weight_class_for",
]

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .validation import ValidationError

#: Resource name of the census data file inside ``mythic_agent/data``.
CATALOG_RESOURCE = "dependency_census.yaml"

#: The only schema this loader accepts.
CATALOG_SCHEMA = "mythic.dependency_census/1"

NECESSITIES = (
    "essential-core",
    "essential-feature",
    "optional-feature",
    "dev-only",
    "build-only",
)

WEIGHTS = ("light", "moderate", "heavy", "very-heavy", "unmeasured")

VERDICTS = ("stdlib-win", "already-core-win", "no-real-win")

_DEP_ID_RE = re.compile(r"^D-\d{2}$")
_REP_ID_RE = re.compile(r"^R-\d{2}$")


def weight_class_for(measured_kb: int) -> str:
    """The weight class for an installed size in KiB (0 = unmeasured)."""
    if measured_kb <= 0:
        return "unmeasured"
    if measured_kb < 1024:
        return "light"
    if measured_kb <= 10240:
        return "moderate"
    if measured_kb <= 51200:
        return "heavy"
    return "very-heavy"


@dataclass(frozen=True)
class Dependency:
    """One censused dependency."""

    id: str
    name: str
    import_name: str
    declared_in: Tuple[str, ...]
    spec: str
    licence: str
    necessity: str
    purpose: str
    measured_kb: int
    weight: str


@dataclass(frozen=True)
class Replacement:
    """One evaluated stdlib-first replacement candidate."""

    id: str
    dependency: str
    candidate: str
    verdict: str
    rationale: str


@dataclass(frozen=True)
class DependencyCensus:
    """The validated dependency census: dependencies + replacements."""

    censused: str
    scope_note: str
    dependencies: Tuple[Dependency, ...]
    replacements: Tuple[Replacement, ...]

    def names(self) -> Tuple[str, ...]:
        """Every censused dependency name, in census order."""
        return tuple(d.name for d in self.dependencies)

    def counts(self) -> Tuple[int, int]:
        """(dependencies, replacements) as censused."""
        return (len(self.dependencies), len(self.replacements))

    def copyleft_names(self) -> Tuple[str, ...]:
        """Dependencies whose licence is GPL/LGPL-family."""
        return tuple(
            d.name for d in self.dependencies if "GPL" in d.licence
        )

    def replacement_wins(self) -> Tuple[str, ...]:
        """Replacement ids whose verdict claims a real win."""
        return tuple(
            r.id for r in self.replacements if r.verdict != "no-real-win"
        )


def _check_dependencies(entries: Any, problems: List[str]) -> List[Dict[str, Any]]:
    if not isinstance(entries, list) or not entries:
        problems.append("dependencies must be a non-empty list")
        return []
    seen: set = set()
    for position, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            problems.append(f"dependency entry is not a mapping: {entry!r}")
            continue
        eid = entry.get("id")
        expected = f"D-{position:02d}"
        if not isinstance(eid, str) or not _DEP_ID_RE.match(eid):
            problems.append(f"dependency entry {eid!r}: id must look like 'D-01'")
        elif eid != expected:
            problems.append(
                f"dependency entry {eid}: ids must be sequential, expected {expected}"
            )
        for key in ("name", "import_name", "spec", "licence", "purpose"):
            if not isinstance(entry.get(key), str) or not entry[key]:
                problems.append(f"dependency entry {eid}: {key} must be non-empty")
        name = entry.get("name")
        if isinstance(name, str):
            if name in seen:
                problems.append(f"dependency {name!r} is named twice")
            seen.add(name)
        declared = entry.get("declared_in")
        if (
            not isinstance(declared, list)
            or not declared
            or any(not isinstance(g, str) or not g for g in declared)
        ):
            problems.append(f"dependency entry {eid}: declared_in must be a non-empty list")
        if entry.get("necessity") not in NECESSITIES:
            problems.append(
                f"dependency entry {eid}: necessity {entry.get('necessity')!r} "
                f"not in {NECESSITIES}"
            )
        measured = entry.get("measured_kb")
        if not isinstance(measured, int) or isinstance(measured, bool) or measured < 0:
            problems.append(f"dependency entry {eid}: measured_kb must be an int >= 0")
        elif entry.get("weight") != weight_class_for(measured):
            problems.append(
                f"dependency entry {eid}: weight {entry.get('weight')!r} does not "
                f"match measured_kb {measured} (expected "
                f"{weight_class_for(measured)!r})"
            )
        if entry.get("weight") not in WEIGHTS:
            problems.append(
                f"dependency entry {eid}: weight {entry.get('weight')!r} not in {WEIGHTS}"
            )
    return entries


def _check_replacements(entries: Any, dep_names: set,
                        problems: List[str]) -> List[Dict[str, Any]]:
    if not isinstance(entries, list) or not entries:
        problems.append("replacements must be a non-empty list")
        return []
    for position, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            problems.append(f"replacement entry is not a mapping: {entry!r}")
            continue
        eid = entry.get("id")
        expected = f"R-{position:02d}"
        if not isinstance(eid, str) or not _REP_ID_RE.match(eid):
            problems.append(f"replacement entry {eid!r}: id must look like 'R-01'")
        elif eid != expected:
            problems.append(
                f"replacement entry {eid}: ids must be sequential, expected {expected}"
            )
        for key in ("dependency", "candidate", "rationale"):
            if not isinstance(entry.get(key), str) or not entry[key]:
                problems.append(f"replacement entry {eid}: {key} must be non-empty")
        if entry.get("verdict") not in VERDICTS:
            problems.append(
                f"replacement entry {eid}: verdict {entry.get('verdict')!r} "
                f"not in {VERDICTS}"
            )
        dep = entry.get("dependency")
        if isinstance(dep, str) and dep_names and dep not in dep_names:
            problems.append(
                f"replacement entry {eid}: dependency {dep!r} is not censused"
            )
    return entries


def validate_census(data: Any) -> List[str]:
    """Return a list of human-readable problems with census *data*."""
    problems: List[str] = []
    if not isinstance(data, dict):
        return [f"census root must be a mapping, got {type(data).__name__}"]
    if data.get("schema") != CATALOG_SCHEMA:
        problems.append(f"schema must be {CATALOG_SCHEMA!r}, got {data.get('schema')!r}")
    if data.get("slice") != "M-012":
        problems.append(f"slice must be 'M-012', got {data.get('slice')!r}")
    for key in ("censused", "scope_note"):
        if not isinstance(data.get(key), str) or not data[key]:
            problems.append(f"{key} must be a non-empty string")
    dependencies = _check_dependencies(data.get("dependencies"), problems)
    dep_names = {
        e["name"] for e in dependencies
        if isinstance(e, dict) and isinstance(e.get("name"), str)
    }
    _check_replacements(data.get("replacements"), dep_names, problems)
    return problems


def _to_census(data: Dict[str, Any]) -> DependencyCensus:
    return DependencyCensus(
        censused=data["censused"],
        scope_note=data["scope_note"],
        dependencies=tuple(
            Dependency(
                id=d["id"], name=d["name"], import_name=d["import_name"],
                declared_in=tuple(d["declared_in"]), spec=d["spec"],
                licence=d["licence"], necessity=d["necessity"],
                purpose=d["purpose"], measured_kb=d["measured_kb"],
                weight=d["weight"],
            )
            for d in data["dependencies"]
        ),
        replacements=tuple(
            Replacement(
                id=r["id"], dependency=r["dependency"],
                candidate=r["candidate"], verdict=r["verdict"],
                rationale=r["rationale"],
            )
            for r in data["replacements"]
        ),
    )


def load_census(data: Optional[Dict[str, Any]] = None) -> DependencyCensus:
    """Load and validate the shipped dependency census (or *data*).

    Raises :class:`~mythic_agent.core.validation.ValidationError`
    listing every problem when the data is not a well-formed census.
    """
    raw = data if data is not None else load_resource(CATALOG_RESOURCE)
    problems = validate_census(raw)
    if problems:
        raise ValidationError(
            "dependency census failed validation: " + "; ".join(problems)
        )
    return _to_census(raw)  # type: ignore[arg-type]


def render_markdown(census: DependencyCensus) -> str:
    """Render the census as markdown: dependencies, then replacements.

    Built from :meth:`DependencyCensus.counts`,
    :meth:`DependencyCensus.names`,
    :meth:`DependencyCensus.copyleft_names`, and
    :meth:`DependencyCensus.replacement_wins`, so the rendered page
    is computed from the same accessors the tests pin.
    """
    n_deps, n_reps = census.counts()
    lines = [
        "# Dependency Census — every dependency weighed (M-012)",
        "",
        f"*Censused {census.censused}: {n_deps} dependencies, "
        f"{n_reps} replacement candidates evaluated.*",
        "",
        census.scope_note,
        "",
        "## Dependencies",
        "",
    ]
    by_name = {d.name: d for d in census.dependencies}
    for name in census.names():
        d = by_name[name]
        size = (
            f"{d.measured_kb} KiB installed"
            if d.measured_kb > 0 else "not installed in the baseline venv"
        )
        lines.append(
            f"- {d.id} `{d.name}` ({', '.join(d.declared_in)}; {d.spec}; "
            f"{d.licence}; {d.necessity}; {d.weight}, {size}) — {d.purpose}"
        )
    copyleft = census.copyleft_names()
    lines += ["", "## Copyleft licences", ""]
    if copyleft:
        lines.append(
            "GPL/LGPL-family licences ride only in optional extras: "
            + ", ".join(f"`{name}`" for name in copyleft) + "."
        )
    else:
        lines.append("No GPL/LGPL-family licences in the census.")
    wins = set(census.replacement_wins())
    lines += ["", "## Stdlib-first replacement list", ""]
    for r in census.replacements:
        mark = " (real win)" if r.id in wins else ""
        lines.append(
            f"- {r.id} `{r.dependency}` → {r.candidate} [{r.verdict}]{mark} — "
            f"{r.rationale}"
        )
    lines.append("")
    return "\n".join(lines)
