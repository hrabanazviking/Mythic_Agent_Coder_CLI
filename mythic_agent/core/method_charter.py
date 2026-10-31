"""The Method Charter in-app (All-Features roadmap slice M-005).

Volmarr's six-plug Forge Protocol — PROJECT_FORGE, the Plain-Language
Build Protocol, the Project Memory Map, the Coding Juggernaut loop,
the Autonomy & Completion lines, and the Self-Improving Forge —
summarised into the app's own doctrine file. Data lives in
``mythic_agent/data/method_charter.yaml``; this module loads,
validates, and renders it. This is the text Part IX's Mythic Method
Engine executes, so executability is enforced by
:func:`validate_charter`:

* The six plugs appear exactly once each, in stack order
  (:data:`STACK_PLUGS`) — the stack is a stack; reordering or dropping
  a plug is not the charter M-005 was charged to write.
* Tenet ids are ``F-01``..``F-06``, unique and sequential — doctrine
  is cited by number, so the numbering cannot have gaps.
* Every tenet carries at least one directive: a plain-English
  instruction the engine can act on. A tenet with no directives is
  prose, not doctrine.
* The autonomy tenet (F-05) carries the pause lines exactly
  (:data:`PAUSE_LINES`) — the bounds are the charter's hard edge, and
  no other tenet may invent pause lines of its own.
* The charter carries a definition of done: the checklist a slice is
  banked against.
"""

from __future__ import annotations

__all__ = [
    "CHARTER_RESOURCE",
    "CHARTER_SCHEMA",
    "PAUSE_LINES",
    "STACK_PLUGS",
    "Any",
    "Dict",
    "List",
    "MethodCharter",
    "Optional",
    "Tenet",
    "Tuple",
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
CHARTER_RESOURCE = "method_charter.yaml"

#: The only schema this loader accepts.
CHARTER_SCHEMA = "mythic.method_charter/1"

#: The six plugs, in stack order: (tenet key, original plug name).
STACK_PLUGS = (
    ("project-forge", "PROJECT_FORGE"),
    ("plain-language-build", "PLAIN_LANGUAGE_BUILD_PROTOCOL"),
    ("project-memory-map", "PROJECT_MEMORY_MAP"),
    ("juggernaut-loop", "YRSA_CODING_JUGGERNAUT"),
    ("autonomy-lines", "YRSA_AUTONOMY_AND_COMPLETION"),
    ("self-improving-forge", "YRSA_SELF_IMPROVING_FORGE"),
)

#: The pause lines of the Autonomy plug (F-05): actions the forge must
#: not take without the human's word. Carried exactly, as a set.
PAUSE_LINES = (
    "destroy-important-data",
    "irreversible-infrastructure-change",
    "unexpected-cost",
    "public-publishing",
    "send-as-the-user",
    "expose-secrets",
    "weaken-security",
    "unavailable-credentials",
)

_AUTONOMY_KEY = "autonomy-lines"
_ID_RE = re.compile(r"^F-\d{2}$")


@dataclass(frozen=True)
class Tenet:
    """One plug of the stack, summarised as executable doctrine."""

    id: str
    key: str
    plug: str
    name: str
    summary: str
    directives: Tuple[str, ...]
    pause_before: Tuple[str, ...]


@dataclass(frozen=True)
class MethodCharter:
    """The validated charter: the method Part IX's engine executes."""

    chartered: str
    author: str
    executed_by: str
    source_note: str
    definition_of_done: Tuple[str, ...]
    tenets: Tuple[Tenet, ...]

    def tenet(self, key: str) -> Tenet:
        """Return the tenet with plug key *key* (KeyError if absent)."""
        for tenet in self.tenets:
            if tenet.key == key:
                return tenet
        raise KeyError(f"no tenet {key!r}")

    def directives(self) -> Tuple[Tuple[str, str], ...]:
        """Every directive in the charter, as (tenet id, directive)."""
        return tuple(
            (tenet.id, directive)
            for tenet in self.tenets
            for directive in tenet.directives
        )

    def pause_lines(self) -> Tuple[str, ...]:
        """The pause lines the autonomy tenet binds the forge to."""
        return self.tenet(_AUTONOMY_KEY).pause_before


def validate_charter(data: Any) -> List[str]:
    """Return a list of human-readable problems with charter *data*."""
    problems: List[str] = []
    if not isinstance(data, dict):
        return [f"charter root must be a mapping, got {type(data).__name__}"]
    if data.get("schema") != CHARTER_SCHEMA:
        problems.append(
            f"schema must be {CHARTER_SCHEMA!r}, got {data.get('schema')!r}"
        )
    for key in ("chartered", "author", "executed_by"):
        if not isinstance(data.get(key), str) or not data[key]:
            problems.append(f"{key} must be a non-empty string")
    done = data.get("definition_of_done")
    if not isinstance(done, list) or not done:
        problems.append("definition_of_done must be a non-empty list")
    elif any(not isinstance(item, str) or not item for item in done):
        problems.append("definition_of_done items must be non-empty strings")

    tenets = data.get("tenets")
    if not isinstance(tenets, list) or not tenets:
        problems.append("tenets must be a non-empty list")
        return problems
    if len(tenets) != len(STACK_PLUGS):
        problems.append(
            f"tenets must number exactly {len(STACK_PLUGS)} (the six plugs), "
            f"got {len(tenets)}"
        )
    seen_ids: set = set()
    for position, tenet in enumerate(tenets, start=1):
        if not isinstance(tenet, dict):
            problems.append(f"tenet is not a mapping: {tenet!r}")
            continue
        tid = tenet.get("id")
        label = tid if isinstance(tid, str) and tid else repr(tenet)[:60]
        expected = f"F-{position:02d}"
        if not isinstance(tid, str) or not _ID_RE.match(tid):
            problems.append(f"tenet {label}: id must look like 'F-01'")
        elif tid != expected:
            problems.append(
                f"tenet {label}: ids must be sequential, expected {expected}"
            )
        if tid in seen_ids:
            problems.append(f"tenet {label}: duplicate id")
        seen_ids.add(tid)
        if position <= len(STACK_PLUGS):
            want_key, want_plug = STACK_PLUGS[position - 1]
            if tenet.get("key") != want_key:
                problems.append(
                    f"tenet {label}: stack order position {position} must be "
                    f"{want_key!r}, got {tenet.get('key')!r}"
                )
            if tenet.get("plug") != want_plug:
                problems.append(
                    f"tenet {label}: plug must be {want_plug!r}, "
                    f"got {tenet.get('plug')!r}"
                )
        for key in ("name", "summary"):
            if not isinstance(tenet.get(key), str) or not tenet[key]:
                problems.append(f"tenet {label}: {key} must be non-empty")
        directives = tenet.get("directives")
        if not isinstance(directives, list) or not directives:
            problems.append(
                f"tenet {label}: directives must be a non-empty list "
                "(doctrine the engine can execute)"
            )
        elif any(not isinstance(d, str) or not d for d in directives):
            problems.append(f"tenet {label}: directives must be non-empty strings")
        pause = tenet.get("pause_before")
        if tenet.get("key") == _AUTONOMY_KEY:
            if not isinstance(pause, list) or not pause:
                problems.append(
                    f"tenet {label}: the autonomy tenet must carry pause_before"
                )
            elif set(pause) != set(PAUSE_LINES):
                problems.append(
                    f"tenet {label}: pause_before must be exactly the "
                    f"charter's pause lines {sorted(PAUSE_LINES)}, "
                    f"got {sorted(pause)}"
                )
            elif len(pause) != len(set(pause)):
                problems.append(f"tenet {label}: pause_before has duplicates")
        elif pause is not None:
            problems.append(
                f"tenet {label}: only the autonomy tenet ({_AUTONOMY_KEY}) "
                "may carry pause_before"
            )
    return problems


def _to_charter(data: Dict[str, Any]) -> MethodCharter:
    tenets = tuple(
        Tenet(
            id=t["id"],
            key=t["key"],
            plug=t["plug"],
            name=t["name"],
            summary=t["summary"],
            directives=tuple(t["directives"]),
            pause_before=tuple(t.get("pause_before") or ()),
        )
        for t in data["tenets"]
    )
    return MethodCharter(
        chartered=data["chartered"],
        author=data["author"],
        executed_by=data["executed_by"],
        source_note=data.get("source_note", ""),
        definition_of_done=tuple(data["definition_of_done"]),
        tenets=tenets,
    )


def load_charter(data: Optional[Dict[str, Any]] = None) -> MethodCharter:
    """Load and validate the shipped method charter (or *data*).

    Raises :class:`~mythic_agent.core.validation.ValidationError`
    listing every problem when the data is not a well-formed charter.
    """
    raw = data if data is not None else load_resource(CHARTER_RESOURCE)
    problems = validate_charter(raw)
    if problems:
        raise ValidationError(
            "method charter failed validation: " + "; ".join(problems)
        )
    return _to_charter(raw)  # type: ignore[arg-type]


def render_markdown(charter: MethodCharter) -> str:
    """Render the charter as markdown: the stack, then the done-check."""
    lines = [
        "# Method Charter — the Forge Protocol, in-app",
        "",
        f"*Chartered {charter.chartered} by {charter.author}. "
        "Slice M-005 of the All-Features road.*",
        "",
        charter.source_note,
        "",
        f"**Executed by:** {charter.executed_by}",
        "",
    ]
    for tenet in charter.tenets:
        lines.append(f"## {tenet.id} — {tenet.name}")
        lines.append("")
        lines.append(f"*Plug: `{tenet.plug}` (key `{tenet.key}`)*")
        lines.append("")
        lines.append(tenet.summary)
        lines.append("")
        for directive in tenet.directives:
            lines.append(f"- {directive}")
        lines.append("")
        if tenet.pause_before:
            lines.append("**Pause before:**")
            lines.append("")
            for line_ in tenet.pause_before:
                lines.append(f"- `{line_}`")
            lines.append("")
    lines += ["## The pause lines, gathered", ""]
    lines.append(
        "The forge pauses for the human's word before any action that would:"
    )
    lines.append("")
    for pause_line in charter.pause_lines():
        lines.append(f"- `{pause_line}`")
    lines += ["", "## Definition of done", ""]
    for item in charter.definition_of_done:
        lines.append(f"- {item}")
    flat = charter.directives()
    lines += [
        "",
        f"*{len(flat)} directives across {len(charter.tenets)} tenets — "
        "the engine's instruction index is `MethodCharter.directives()`.*",
        "",
    ]
    return "\n".join(lines)
