"""The Terminology Bridge (All-Features roadmap slice M-006).

Every field term a user brings from another coding tool — checkpoint,
hook, skill, plan mode, and the rest of the census vocabulary — is
given its Mythic name here, *and kept searchable by its common name*:
a user coming from any rival finds their word honoured, never
corrected away. Data lives in ``mythic_agent/data/terminology.yaml``;
this module loads, validates, searches, and renders it.

Searchability is the point, and :func:`validate_bridge` enforces it:

* Term ids are ``T-01``..``T-NN``, unique and sequential — the bridge
  is cited by number, so the numbering cannot have gaps.
* The roadmap's named examples (:data:`REQUIRED_COMMON_TERMS`) are
  carried exactly once each — a bridge that drops one is not the
  bridge M-006 was charged to build.
* Common names and Mythic names are each unique under normalisation
  (case, hyphens, and repeated whitespace do not create a second
  entry), so any word resolves to at most one term.
* No alias may collide with a *different* term's common name, Mythic
  name, or alias — a colliding alias would make a search ambiguous,
  which is the one failure this slice exists to prevent.
"""

from __future__ import annotations

__all__ = [
    "BRIDGE_RESOURCE",
    "BRIDGE_SCHEMA",
    "REQUIRED_COMMON_TERMS",
    "Any",
    "Bridge",
    "Dict",
    "List",
    "Optional",
    "Term",
    "Tuple",
    "load_bridge",
    "render_markdown",
    "validate_bridge",
]

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .validation import ValidationError

#: Resource name of the bridge data file inside ``mythic_agent/data``.
BRIDGE_RESOURCE = "terminology.yaml"

#: The only schema this loader accepts.
BRIDGE_SCHEMA = "mythic.terminology/1"

#: The field terms the roadmap's M-006 names verbatim ("checkpoint,
#: hook, skill, plan mode..."). Each must be carried exactly once.
REQUIRED_COMMON_TERMS = (
    "checkpoint",
    "hook",
    "skill",
    "plan mode",
)

_ID_RE = re.compile(r"^T-\d{2}$")


def _norm(text: str) -> str:
    """Normalise a search word: case, separators, and spacing fold."""
    return re.sub(r"\s+", " ", text.strip().lower().replace("-", " ").replace("_", " "))


@dataclass(frozen=True)
class Term:
    """One bridged term: the field's word, Mythic's name, the meaning."""

    id: str
    common: str
    mythic: str
    aliases: Tuple[str, ...]
    definition: str


@dataclass(frozen=True)
class Bridge:
    """The validated terminology bridge: searchable both ways."""

    bridged: str
    source_note: str
    terms: Tuple[Term, ...]

    def find(self, query: str) -> Optional[Term]:
        """Return the term *query* names, or None if it names none.

        The query is matched, normalised, against every term's common
        name, Mythic name, and aliases — a rival's word and Mythic's
        word resolve to the same term.
        """
        want = _norm(query)
        for term in self.terms:
            names = (term.common, term.mythic, *term.aliases)
            if any(_norm(name) == want for name in names):
                return term
        return None

    def searchable_names(self) -> Tuple[Tuple[str, str], ...]:
        """Every searchable name, as (name, term id) pairs, sorted."""
        pairs = [
            (name, term.id)
            for term in self.terms
            for name in (term.common, term.mythic, *term.aliases)
        ]
        return tuple(sorted(pairs, key=lambda pair: _norm(pair[0])))


def validate_bridge(data: Any) -> List[str]:
    """Return a list of human-readable problems with bridge *data*."""
    problems: List[str] = []
    if not isinstance(data, dict):
        return [f"bridge root must be a mapping, got {type(data).__name__}"]
    if data.get("schema") != BRIDGE_SCHEMA:
        problems.append(
            f"schema must be {BRIDGE_SCHEMA!r}, got {data.get('schema')!r}"
        )
    if not isinstance(data.get("bridged"), str) or not data["bridged"]:
        problems.append("bridged must be a non-empty string")

    terms = data.get("terms")
    if not isinstance(terms, list) or not terms:
        problems.append("terms must be a non-empty list")
        return problems

    seen_ids: set = set()
    owner: Dict[str, str] = {}  # normalised name -> first term label
    commons: List[str] = []
    for position, term in enumerate(terms, start=1):
        if not isinstance(term, dict):
            problems.append(f"term is not a mapping: {term!r}")
            continue
        tid = term.get("id")
        label = tid if isinstance(tid, str) and tid else repr(term)[:60]
        expected = f"T-{position:02d}"
        if not isinstance(tid, str) or not _ID_RE.match(tid):
            problems.append(f"term {label}: id must look like 'T-01'")
        elif tid != expected:
            problems.append(
                f"term {label}: ids must be sequential, expected {expected}"
            )
        if tid in seen_ids:
            problems.append(f"term {label}: duplicate id")
        seen_ids.add(tid)
        for key in ("common", "mythic", "definition"):
            if not isinstance(term.get(key), str) or not term[key]:
                problems.append(f"term {label}: {key} must be non-empty")
        aliases = term.get("aliases")
        if not isinstance(aliases, list):
            problems.append(f"term {label}: aliases must be a list")
            aliases = []
        elif any(not isinstance(a, str) or not a for a in aliases):
            problems.append(f"term {label}: aliases must be non-empty strings")
        if isinstance(term.get("common"), str) and term["common"]:
            commons.append(_norm(term["common"]))
        # Every name this term answers to must belong to it alone.
        for kind, values in (
            ("common", [term.get("common")]),
            ("mythic", [term.get("mythic")]),
            ("alias", aliases),
        ):
            for value in values:
                if not isinstance(value, str) or not value:
                    continue
                key = _norm(value)
                if key in owner and owner[key] != label:
                    problems.append(
                        f"term {label}: {kind} name {value!r} collides with "
                        f"{owner[key]} — a search for it would be ambiguous"
                    )
                elif key in owner:
                    problems.append(
                        f"term {label}: {kind} name {value!r} is repeated "
                        "within the same term"
                    )
                owner.setdefault(key, label)
    for required in REQUIRED_COMMON_TERMS:
        count = commons.count(_norm(required))
        if count != 1:
            problems.append(
                f"required field term {required!r} must be carried exactly "
                f"once, got {count}"
            )
    return problems


def _to_bridge(data: Dict[str, Any]) -> Bridge:
    terms = tuple(
        Term(
            id=t["id"],
            common=t["common"],
            mythic=t["mythic"],
            aliases=tuple(t["aliases"]),
            definition=t["definition"],
        )
        for t in data["terms"]
    )
    return Bridge(
        bridged=data["bridged"],
        source_note=data.get("source_note", ""),
        terms=terms,
    )


def load_bridge(data: Optional[Dict[str, Any]] = None) -> Bridge:
    """Load and validate the shipped terminology bridge (or *data*).

    Raises :class:`~mythic_agent.core.validation.ValidationError`
    listing every problem when the data is not a well-formed bridge.
    """
    raw = data if data is not None else load_resource(BRIDGE_RESOURCE)
    problems = validate_bridge(raw)
    if problems:
        raise ValidationError(
            "terminology bridge failed validation: " + "; ".join(problems)
        )
    return _to_bridge(raw)  # type: ignore[arg-type]


def render_markdown(bridge: Bridge) -> str:
    """Render the bridge as markdown: the terms, then the search index.

    The index is built from :meth:`Bridge.searchable_names` and every
    required field term is resolved through :meth:`Bridge.find`, so
    the rendered page itself proves both directions of the bridge.
    """
    lines = [
        "# Terminology Bridge — every field word honoured",
        "",
        f"*Bridged {bridge.bridged}. Slice M-006 of the All-Features road.*",
        "",
        bridge.source_note,
        "",
    ]
    for term in bridge.terms:
        lines.append(f"## {term.id} — {term.common} → {term.mythic}")
        lines.append("")
        lines.append(term.definition)
        lines.append("")
        if term.aliases:
            lines.append("**Also searched as:** " + ", ".join(term.aliases))
            lines.append("")
    lines += ["## Find your word", ""]
    for required in REQUIRED_COMMON_TERMS:
        found = bridge.find(required)
        lines.append(
            f"- `{required}` → {found.id} {found.mythic}"
            if found is not None
            else f"- `{required}` → NOT FOUND"
        )
    lines += ["", "## Search index", ""]
    for name, tid in bridge.searchable_names():
        lines.append(f"- {name} → {tid}")
    lines.append("")
    return "\n".join(lines)
