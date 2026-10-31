"""The Session Catalogue (All-Features roadmap slice M-010).

Session archaeology, frozen as validated data: every session and
journal format the app writes today — the SQLite session store, the
plain-dict session record and export, the write-ahead journal, the
structured crash report, the transcript spill file, and the
session-event payload — each with its on-disk location, its format
version, the module that reads it, its fields, and the compatibility
rule that binds its future.

This catalogue is the forward-compat contract: a format may gain a
new version only with a reader that still reads version 1, and the
golden fixtures frozen in ``tests/test_session_catalog.py`` — literal
v1 bytes and records, built with raw SQL / raw JSON, never with the
current writers — must never break. The tests cross-check the
catalogue against the live version constants and the live SQLite
schema, so a new format or a silent version bump cannot land
uncatalogued.

Data lives in ``mythic_agent/data/session_catalog.yaml``.
"""

from __future__ import annotations

__all__ = [
    "CATALOG_RESOURCE",
    "CATALOG_SCHEMA",
    "Any",
    "Dict",
    "FormatEntry",
    "List",
    "Optional",
    "SessionCatalog",
    "load_catalog",
    "render_markdown",
    "validate_catalog",
]

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .validation import ValidationError

#: Resource name of the catalogue data file inside ``mythic_agent/data``.
CATALOG_RESOURCE = "session_catalog.yaml"

#: The only schema this loader accepts.
CATALOG_SCHEMA = "mythic.session_catalog/1"

FORMAT_KINDS = (
    "sqlite-store",
    "dict-record",
    "dict-export",
    "jsonl-journal",
    "json-report",
    "jsonl-spill",
    "json-payload",
)

_FORMAT_ID_RE = re.compile(r"^J-\d{2}$")


@dataclass(frozen=True)
class FormatEntry:
    """One catalogued session/journal format."""

    id: str
    name: str
    kind: str
    location: str
    version: str
    reader: str
    fields: Tuple[str, ...]
    compat_rule: str


@dataclass(frozen=True)
class SessionCatalog:
    """The validated session catalogue: every format, in order."""

    catalogued: str
    scope_note: str
    formats: Tuple[FormatEntry, ...]

    def format_names(self) -> Tuple[str, ...]:
        """Every catalogued format name, in catalogue order."""
        return tuple(f.name for f in self.formats)

    def version_of(self, name: str) -> str:
        """The catalogued version string of the format called *name*."""
        for entry in self.formats:
            if entry.name == name:
                return entry.version
        raise KeyError(name)

    def counts(self) -> Tuple[int]:
        """(formats,) as catalogued."""
        return (len(self.formats),)


def validate_catalog(data: Any) -> List[str]:
    """Return a list of human-readable problems with catalogue *data*."""
    problems: List[str] = []
    if not isinstance(data, dict):
        return [f"catalogue root must be a mapping, got {type(data).__name__}"]
    if data.get("schema") != CATALOG_SCHEMA:
        problems.append(
            f"schema must be {CATALOG_SCHEMA!r}, got {data.get('schema')!r}"
        )
    if data.get("slice") != "M-010":
        problems.append(f"slice must be 'M-010', got {data.get('slice')!r}")
    for key in ("catalogued", "scope_note"):
        if not isinstance(data.get(key), str) or not data[key]:
            problems.append(f"{key} must be a non-empty string")
    if isinstance(data.get("scope_note"), str) and "forward-compat" not in data["scope_note"]:
        problems.append("scope_note must name forward-compat (the contract's purpose)")

    entries = data.get("formats")
    if not isinstance(entries, list) or not entries:
        problems.append("formats must be a non-empty list")
        return problems
    seen: set = set()
    for position, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            problems.append(f"formats entry is not a mapping: {entry!r}")
            continue
        eid = entry.get("id")
        expected = f"J-{position:02d}"
        if not isinstance(eid, str) or not _FORMAT_ID_RE.match(eid):
            problems.append(f"formats entry {eid!r}: id must look like 'J-01'")
        elif eid != expected:
            problems.append(
                f"formats entry {eid}: ids must be sequential, expected {expected}"
            )
        for key in ("name", "kind", "location", "version", "reader", "compat_rule"):
            if not isinstance(entry.get(key), str) or not entry[key]:
                problems.append(f"formats entry {eid}: {key} must be non-empty")
        if isinstance(entry.get("kind"), str) and entry["kind"] not in FORMAT_KINDS:
            problems.append(
                f"format {entry.get('name')!r}: kind {entry.get('kind')!r} "
                f"not in {FORMAT_KINDS}"
            )
        name = entry.get("name")
        if isinstance(name, str):
            if name in seen:
                problems.append(f"formats entry {name!r} is named twice")
            seen.add(name)
        fields = entry.get("fields")
        if (
            not isinstance(fields, list)
            or not fields
            or any(not isinstance(f, str) or not f for f in fields)
        ):
            problems.append(f"format {name!r}: fields must be a non-empty list of strings")
        elif len(set(fields)) != len(fields):
            problems.append(f"format {name!r}: fields contain duplicates")
    return problems


def _to_catalog(data: Dict[str, Any]) -> SessionCatalog:
    return SessionCatalog(
        catalogued=data["catalogued"],
        scope_note=data["scope_note"],
        formats=tuple(
            FormatEntry(
                id=f["id"], name=f["name"], kind=f["kind"],
                location=f["location"], version=f["version"],
                reader=f["reader"], fields=tuple(f["fields"]),
                compat_rule=f["compat_rule"],
            )
            for f in data["formats"]
        ),
    )


def load_catalog(data: Optional[Dict[str, Any]] = None) -> SessionCatalog:
    """Load and validate the shipped session catalogue (or *data*).

    Raises :class:`~mythic_agent.core.validation.ValidationError`
    listing every problem when the data is not a well-formed catalogue.
    """
    raw = data if data is not None else load_resource(CATALOG_RESOURCE)
    problems = validate_catalog(raw)
    if problems:
        raise ValidationError(
            "session catalogue failed validation: " + "; ".join(problems)
        )
    return _to_catalog(raw)  # type: ignore[arg-type]


def render_markdown(catalog: SessionCatalog) -> str:
    """Render the catalogue as markdown: one line per format.

    Built from :meth:`SessionCatalog.counts`,
    :meth:`SessionCatalog.format_names`, and
    :meth:`SessionCatalog.version_of`, so the rendered page is
    computed from the same accessors the tests pin.
    """
    (n_formats,) = catalog.counts()
    lines = [
        "# Session Catalogue — the forward-compat contract (M-010)",
        "",
        f"*Catalogued {catalog.catalogued}: {n_formats} formats.*",
        "",
        catalog.scope_note,
        "",
        "## Formats",
        "",
    ]
    by_name = {f.name: f for f in catalog.formats}
    for name in catalog.format_names():
        entry = by_name[name]
        lines.append(
            f"- {entry.id} `{entry.name}` ({entry.kind}, "
            f"version {catalog.version_of(name)}) at `{entry.location}` — "
            f"fields: {', '.join(entry.fields)}. "
            f"Reader: `{entry.reader}`. {entry.compat_rule}"
        )
    lines.append("")
    return "\n".join(lines)
