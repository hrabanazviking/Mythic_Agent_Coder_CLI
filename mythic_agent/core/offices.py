"""The six offices formalised (All-Features roadmap slice M-122).

Part VI - Agents as files - continues here. The
roadmap's words: ``Skald (intent & vision), Architect
(design), Forge Worker (build), Auditor (verify),
Cartographer (map & research), Scribe (memory &
docs) - duties, tools, and hand-off contracts per
office.``

What already shipped, and what this slice adds:

* The offices already exist - as vocabulary. The
  shipped office list lives in
  ``core/role_routing.py`` (M-029): nine offices in
  crew order (``primary``, ``polymath``,
  ``architect``, ``auditor``, ``cartographer``,
  ``forge_worker``, ``scribe``, ``skald``,
  ``guardian``), each with a title and a purpose,
  and :func:`office_for_agent_name` maps every
  shipped crew member name to exactly one of them.
  M-121 then cast the crew as data
  (``core/crew_members.py`` +
  ``mythic_agent/data/crew_members.yaml``): each
  member holds one office and works with a named
  tool list. What nothing held is the office itself
  formalised - its duties, its tools, what it takes
  in and produces, and the contracts by which it
  hands work to the other offices.
* This slice is that formalisation, as a pure
  layer: the six offices the roadmap names, held as
  validated data (``mythic_agent/data/offices.yaml``),
  an office definition validated as data, a loader
  for an offices file anywhere on disk, hand-off
  contracts validated as a closed graph over the
  six, an office record shaped as session news, and
  a small in-memory registry model. This module
  spawns no agent, runs no model, opens no session
  and imports no agent / UI code; the agent layer
  owns holding the registry for a session and
  offering the offices on a live surface.

Honesty rules, enforced here and pinned by tests:

* **The six are the roadmap's six, from the shipped
  vocabulary.** Every formalised office id is a
  shipped M-029 office, composed with by import -
  this module invents no office and keeps no second
  office list of its own devising: the six are the
  roadmap slice's own naming. The shipped
  vocabulary is larger, and the difference is
  stated, never hidden: ``polymath`` and
  ``guardian`` are shipped crew offices (M-121
  casts members into them) that this slice does
  not formalise, and ``primary`` is the lead
  session itself, never a working office.
* **The formalisation describes the shipped crew,
  it does not re-cast it.** Each office's title and
  purpose in the shipped file are the M-029 layer's
  own words, and its tools are exactly the tools
  the M-121 casting gives the member holding that
  office - pinned against both live sources by
  tests.
* **Hand-offs are a closed graph.** A contract
  names a target among the offices defined in the
  same file, never the office itself, with the
  artifact handed over and the condition it must
  meet stated in plain words. A dangling, self, or
  duplicated contract refuses.
* **Malformed refuses.** An unknown or unformalised
  office, an empty duty / input / output, an empty
  or duplicated tool list, a duplicate office or
  contract in one file, and unknown keys all raise
  instead of being skipped or guessed at.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .crew_members import member_offices
from .crew_members import normalize_office as _crew_normalize_office
from .role_routing import get_office, office_ids
from .validation import ValidationError

__all__ = [
    "FORMAL_OFFICES",
    "OFFICES_RESOURCE",
    "OFFICES_SCHEMA",
    "OFFICES_SLICE",
    "PLAIN_EXPLANATION",
    "UNFORMALISED_OFFICES",
    "USAGE",
    "HandoffContract",
    "OfficeDefinition",
    "OfficeRegistry",
    "OfficesBook",
    "build_office",
    "formal_office_ids",
    "format_office",
    "format_offices",
    "format_offices_screen",
    "load_offices",
    "load_offices_file",
    "normalize_formal_office",
    "office_record",
    "parse_offices_args",
    "plain_words",
    "validate_offices",
]

OFFICES_SLICE = "M-122"

#: The packaged data resource holding the formalised offices.
OFFICES_RESOURCE = "offices.yaml"

#: The schema word an offices file must carry.
OFFICES_SCHEMA = "mythic.offices/1"

#: The six offices this slice formalises, in the roadmap's
#: own order for the slice. Every id is a shipped M-029
#: office; the tuple is the roadmap's naming, composed
#: with the shipped vocabulary, never a rival list.
FORMAL_OFFICES: Tuple[str, ...] = (
    "skald", "architect", "forge_worker",
    "auditor", "cartographer", "scribe")

#: The shipped crew offices this slice does not formalise:
#: every M-121 member office outside the six. ``primary``
#: is not a member office and never appears here - it is
#: the lead session itself.
UNFORMALISED_OFFICES: Tuple[str, ...] = tuple(
    o for o in member_offices() if o not in FORMAL_OFFICES)

PLAIN_EXPLANATION = (
    "The six offices, formalised: Skald (intent & "
    "vision), Architect (design), Forge Worker "
    "(build), Auditor (verify), Cartographer (map "
    "& research) and Scribe (memory & docs) - each "
    "held as data with its duties, its tools, what "
    "it takes in and produces, and its hand-off "
    "contracts: who it hands work to, with what "
    "artifact, under what condition. Every office "
    "is a shipped office of the role-routing "
    "layer; the shipped polymath and guardian "
    "offices are not among the six and are not "
    "formalised here. This layer holds the offices "
    "as data only; it spawns no agent and runs no "
    "model itself."
)

USAGE = (
    "Usage: /offices, /offices show, "
    "/offices show <office>, /offices handoffs <office>, "
    "/offices contract <from> <to>"
)

_OFFICE_KEYS = frozenset({
    "id", "office", "title", "focus", "purpose",
    "duties", "tools", "inputs", "outputs", "handoffs",
})

_BOOK_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "formal_note", "offices",
})

_HANDOFF_KEYS = frozenset({"to", "artifact", "condition"})

_TOOL_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789_")


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def normalize_formal_office(value: Any) -> str:
    """The canonical formalised office a word names.

    Office words read exactly as the crew layer
    reads them (case-insensitively, dashes as
    underscores, composed from M-121 / M-029 - never
    a second reading). A shipped office outside the
    six (``polymath``, ``guardian``, ``primary``)
    refuses here, naming the boundary: it is a real
    office, but not one this slice formalises. An
    unknown office raises.
    """
    try:
        office = _crew_normalize_office(value)
    except ValueError:
        if isinstance(value, str) and value.strip().lower() \
                .replace("-", "_") in office_ids():
            raise ValueError(
                "the %s office is the lead session itself, "
                "never a formalised working office"
                % value.strip().lower().replace("-", "_")) from None
        raise ValueError(
            "an office must be one of %s, got %r"
            % ("/".join(FORMAL_OFFICES), value)) from None
    if office not in FORMAL_OFFICES:
        raise ValueError(
            "the %s office ships in the crew but is not one "
            "of the six offices M-122 formalises (%s), got %r"
            % (office, "/".join(FORMAL_OFFICES), value))
    return office


def formal_office_ids() -> Tuple[str, ...]:
    """Every formalised office id, in the roadmap's order."""
    return FORMAL_OFFICES


def _check_words(value: Any, what: str) -> Tuple[str, ...]:
    if isinstance(value, (str, bytes)) \
            or not isinstance(value, (list, tuple)):
        raise ValueError(f"{what} must be a list of phrases, got {value!r}")
    words = [_clean_text(entry, f"one of {what}") for entry in value]
    if not words:
        raise ValueError(f"{what} must name at least one entry")
    if len(set(words)) != len(words):
        raise ValueError(f"{what} names an entry twice")
    return tuple(words)


def _check_tools(value: Any) -> Tuple[str, ...]:
    if isinstance(value, (str, bytes)) \
            or not isinstance(value, (list, tuple)):
        raise ValueError(
            f"an office's tools must be a list of tool names, "
            f"got {value!r}")
    tools = []
    for entry in value:
        if not isinstance(entry, str) or not entry.strip() \
                or not all(ch in _TOOL_CHARS for ch in entry.strip()):
            raise ValueError(
                f"a tool name must be one word of letters, digits "
                f"and underscores, got {entry!r}")
        tools.append(entry.strip())
    if not tools:
        raise ValueError("an office must name at least one tool")
    if len(set(tools)) != len(tools):
        raise ValueError(
            "an office's tools name a tool twice: %s"
            % ", ".join(sorted(
                t for t in set(tools) if tools.count(t) > 1)))
    return tuple(tools)


# ---------------------------------------------------------------------
# The hand-off contract: one edge of the offices' graph.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class HandoffContract:
    """One hand-off contract: an artifact, and its condition.

    ``to_office`` is the formalised office the work
    goes to; ``artifact`` names what is handed over;
    ``condition`` states, in plain words, what must
    be true of the artifact when it changes hands.
    Whether the target is defined in the same book
    is a book-level rule, checked by
    :func:`validate_offices`.
    """

    to_office: str = ""
    artifact: str = ""
    condition: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "to_office", normalize_formal_office(self.to_office))
        object.__setattr__(
            self, "artifact", _clean_text(self.artifact, "a hand-off artifact"))
        object.__setattr__(
            self, "condition",
            _clean_text(self.condition, "a hand-off condition"))

    def to_record(self) -> Dict[str, Any]:
        return {"to": self.to_office, "artifact": self.artifact,
                "condition": self.condition}


def _check_handoff(value: Any) -> HandoffContract:
    if isinstance(value, HandoffContract):
        return value
    if not isinstance(value, dict):
        raise ValueError(f"a hand-off contract must be a mapping, got {value!r}")
    unknown = set(value) - _HANDOFF_KEYS
    if unknown:
        raise ValueError(
            "unknown hand-off keys: %s" % ", ".join(sorted(unknown)))
    for field in ("to", "artifact", "condition"):
        if field not in value:
            raise ValueError(f"a hand-off contract is missing its {field}")
    return HandoffContract(to_office=value["to"], artifact=value["artifact"],
                           condition=value["condition"])


# ---------------------------------------------------------------------
# The office definition: one office, formalised, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class OfficeDefinition:
    """One formalised office, as data.

    ``office`` is the shipped M-029 office id;
    ``title`` and ``purpose`` are that office's own
    words in the shipped file; ``focus`` is the
    roadmap's parenthetical for the office;
    ``duties`` states what the office is responsible
    for; ``tools`` is the tool names it works with;
    ``inputs`` / ``outputs`` name what it takes in
    and produces; ``handoffs`` is its hand-off
    contracts. Constructing one validates it, so a
    definition that exists is one a session could
    be shown.
    """

    office: str = ""
    title: str = ""
    focus: str = ""
    purpose: str = ""
    duties: Tuple[str, ...] = ()
    tools: Tuple[str, ...] = ()
    inputs: Tuple[str, ...] = ()
    outputs: Tuple[str, ...] = ()
    handoffs: Tuple[HandoffContract, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "office", normalize_formal_office(self.office))
        object.__setattr__(
            self, "title", _clean_text(self.title, "an office title"))
        object.__setattr__(
            self, "focus", _clean_text(self.focus, "an office focus"))
        object.__setattr__(
            self, "purpose", _clean_text(self.purpose, "an office purpose"))
        object.__setattr__(
            self, "duties", _check_words(self.duties, "an office's duties"))
        object.__setattr__(self, "tools", _check_tools(self.tools))
        object.__setattr__(
            self, "inputs", _check_words(self.inputs, "an office's inputs"))
        object.__setattr__(
            self, "outputs", _check_words(self.outputs, "an office's outputs"))
        if isinstance(self.handoffs, (str, bytes)) \
                or not isinstance(self.handoffs, (list, tuple)):
            raise ValueError(
                f"an office's handoffs must be a list of contracts, "
                f"got {self.handoffs!r}")
        contracts = tuple(_check_handoff(h) for h in self.handoffs)
        for contract in contracts:
            if contract.to_office == self.office:
                raise ValueError(
                    f"the {self.office} office hands off to itself; "
                    "a contract names another office")
        targets = [c.to_office for c in contracts]
        if len(set(targets)) != len(targets):
            raise ValueError(
                "an office's hand-offs name a target twice: %s"
                % ", ".join(sorted(
                    t for t in set(targets) if targets.count(t) > 1)))
        object.__setattr__(self, "handoffs", contracts)

    def contract_to(self, office: Any) -> HandoffContract:
        """The contract to one office; no contract raises KeyError."""
        wanted = normalize_formal_office(office)
        for contract in self.handoffs:
            if contract.to_office == wanted:
                return contract
        raise KeyError(
            f"the {self.office} office has no hand-off to {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "office",
            "slice": OFFICES_SLICE,
            "office": self.office,
            "title": self.title,
            "focus": self.focus,
            "purpose": self.purpose,
            "duties": list(self.duties),
            "tools": list(self.tools),
            "inputs": list(self.inputs),
            "outputs": list(self.outputs),
            "handoffs": [c.to_record() for c in self.handoffs],
        }


def _pick(mapping: Dict[str, Any], first: str, second: str,
          what: str) -> Any:
    """One field from its two spellings, or a refusal."""
    if first in mapping and second in mapping:
        if mapping[first] != mapping[second]:
            raise ValueError(f"an office names two different {what}")
        return mapping[first]
    if first in mapping:
        return mapping[first]
    return mapping.get(second)


def validate_office(definition: Any) -> OfficeDefinition:
    """Validate one office definition into an OfficeDefinition.

    Accepts an OfficeDefinition or a mapping naming
    an ``office`` (or ``id``), a ``title``, a
    ``focus``, a ``purpose``, ``duties``, ``tools``,
    ``inputs``, ``outputs`` and ``handoffs``.
    Naming both spellings of the office with
    different values refuses, and unknown keys
    refuse.
    """
    if isinstance(definition, OfficeDefinition):
        return definition
    if not isinstance(definition, dict):
        raise ValueError(
            f"an office definition must be a mapping, got {definition!r}")
    unknown = set(definition) - _OFFICE_KEYS
    if unknown:
        raise ValueError(
            "unknown office keys: %s" % ", ".join(sorted(unknown)))
    for field in ("title", "focus", "purpose", "duties", "tools",
                  "inputs", "outputs", "handoffs"):
        if field not in definition:
            raise ValueError(f"an office definition is missing its {field}")
    office = _pick(definition, "office", "id", "office ids")
    if office is None:
        raise ValueError("an office definition is missing its office")
    return OfficeDefinition(
        office=office, title=definition["title"], focus=definition["focus"],
        purpose=definition["purpose"], duties=definition["duties"],
        tools=definition["tools"], inputs=definition["inputs"],
        outputs=definition["outputs"], handoffs=definition["handoffs"])


def build_office(definition: Any = None, **kwargs: Any) -> OfficeDefinition:
    """Build one validated office definition.

    From an OfficeDefinition, from a mapping (the
    spellings :func:`validate_office` reads), or
    from field words given as keyword arguments.
    """
    if isinstance(definition, OfficeDefinition) and not kwargs:
        return definition
    if isinstance(definition, dict) or definition is None:
        merged: Dict[str, Any] = {}
        if isinstance(definition, dict):
            merged.update(definition)
        merged.update(kwargs)
        return validate_office(merged)
    raise ValueError(
        f"an office definition must be a mapping, got {definition!r}")


# ---------------------------------------------------------------------
# The book: the formalised offices held in one file, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class OfficesBook:
    """A whole book: the offices one file defines, in file order."""

    definitions: Tuple[OfficeDefinition, ...] = ()
    formal_note: str = ""

    def get(self, office: Any) -> OfficeDefinition:
        """The definition one office names; an undefined office raises."""
        wanted = normalize_formal_office(office)
        for definition in self.definitions:
            if definition.office == wanted:
                return definition
        raise KeyError(f"no definition holds the office: {wanted!r}")

    def contract(self, from_office: Any, to_office: Any) -> HandoffContract:
        """The contract between two offices; none raises KeyError."""
        return self.get(from_office).contract_to(to_office)

    def handoffs_from(self, office: Any) -> Tuple[HandoffContract, ...]:
        """Every contract one office hands out under."""
        return self.get(office).handoffs

    def handoffs_to(self, office: Any) -> Tuple[Tuple[str, HandoffContract], ...]:
        """Every (from-office, contract) pair that hands to one office."""
        wanted = normalize_formal_office(office)
        return tuple(
            (d.office, c) for d in self.definitions
            for c in d.handoffs if c.to_office == wanted)


def validate_offices(data: Any, *,
                      require_complete: bool = False) -> list:
    """Every problem in an offices mapping, as plain strings.

    An empty list means the book is well-formed.
    With ``require_complete`` the book must hold
    exactly the six formalised offices, each once,
    each carrying the shipped M-029 title and
    purpose (the check the shipped file is held to;
    a file formalising fewer offices is read
    without it). Hand-off closure is always held:
    every contract's target must be defined in the
    same book.
    """
    if not isinstance(data, dict):
        return [f"an offices book must be a mapping, got {data!r}"]
    problems = []
    unknown = set(data) - _BOOK_KEYS
    if unknown:
        problems.append(
            "unknown offices book keys: %s" % ", ".join(sorted(unknown)))
    if data.get("schema") != OFFICES_SCHEMA:
        problems.append(
            f"an offices book's schema must be {OFFICES_SCHEMA!r}, "
            f"got {data.get('schema')!r}")
    if data.get("slice") != OFFICES_SLICE:
        problems.append(
            f"an offices book's slice must be {OFFICES_SLICE!r}, "
            f"got {data.get('slice')!r}")
    raw = data.get("offices")
    if not isinstance(raw, list) or not raw:
        problems.append("an offices book must hold a non-empty offices list")
        return problems
    seen: set = set()
    parsed = []
    for index, entry in enumerate(raw):
        try:
            definition = validate_office(entry)
        except ValueError as exc:
            problems.append(f"office {index + 1}: {exc}")
            continue
        parsed.append(definition)
        if definition.office in seen:
            problems.append(
                f"duplicate office definition: {definition.office!r}")
        seen.add(definition.office)
    for definition in parsed:
        for contract in definition.handoffs:
            if contract.to_office not in seen:
                problems.append(
                    f"the {definition.office} office hands off to "
                    f"{contract.to_office!r}, which this book does "
                    "not define")
    if require_complete:
        for office in FORMAL_OFFICES:
            if office not in seen:
                problems.append(f"no definition holds the office {office!r}")
        for definition in parsed:
            shipped = get_office(definition.office)
            if definition.title != shipped.title:
                problems.append(
                    f"the {definition.office} office's title "
                    f"{definition.title!r} is not the shipped title "
                    f"{shipped.title!r}")
            if definition.purpose != shipped.purpose:
                problems.append(
                    f"the {definition.office} office's purpose is not "
                    "the shipped role-routing purpose")
    return problems


def _book_from(data: Any, *, require_complete: bool) -> OfficesBook:
    problems = validate_offices(data, require_complete=require_complete)
    if problems:
        raise ValidationError(
            "invalid offices book: " + "; ".join(problems))
    assert isinstance(data, dict)
    return OfficesBook(
        definitions=tuple(validate_office(entry) for entry in data["offices"]),
        formal_note=str(data.get("formal_note") or ""))


def load_offices(data: Optional[Dict[str, Any]] = None) -> OfficesBook:
    """Load and validate the shipped book (or *data*).

    The shipped book is held to completeness: exactly
    the six formalised offices, each once, each with
    its shipped title and purpose. Raises
    :class:`ValidationError` listing every problem
    when the record is not a well-formed book.
    """
    raw = data if data is not None else load_resource(OFFICES_RESOURCE)
    return _book_from(raw, require_complete=True)


def load_offices_file(path: Any) -> OfficesBook:
    """Load and validate an offices book from a file at *path*.

    Any file in the book shape, anywhere on disk,
    validated whole - a malformed file raises
    :class:`ValidationError` naming the problem,
    and a missing file raises ``FileNotFoundError``.
    Completeness is not required: a file may
    formalise a single office (its hand-offs must
    still land inside the same file).
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _book_from(raw, require_complete=False)


# ---------------------------------------------------------------------
# Office news, shaped as a session record.
# ---------------------------------------------------------------------


def office_record(definition: Any) -> Dict[str, Any]:
    """The session-news record of one formalised office.

    Carries the office's whole definition plus a
    one-line plain headline, so an office shown in a
    session is news with its shape attached, never a
    bare log line.
    """
    current = definition if isinstance(definition, OfficeDefinition) \
        else build_office(definition)
    record = current.to_record()
    record["news"] = True
    record["headline"] = plain_words(current)
    return record


def plain_words(definition: Any) -> str:
    """One office, in one plain sentence."""
    current = definition if isinstance(definition, OfficeDefinition) \
        else build_office(definition)
    hands = ", ".join(
        f"{c.to_office.replace('_', ' ')} ({c.artifact.split(' - ')[0]})"
        for c in current.handoffs) or "no office"
    return (
        f"The {current.title} office ({current.focus}): "
        f"duties - {'; '.join(current.duties)} "
        f"Tools: {', '.join(current.tools)}. "
        f"Hands off to {hands}.")


# ---------------------------------------------------------------------
# The registry model: definitions held in registration order.
# ---------------------------------------------------------------------


class OfficeRegistry:
    """An in-memory registry of office definitions.

    Definitions are held in registration order,
    keyed by their office id - a duplicate office
    refuses. Storage beyond memory (a session's
    journal, a file) is the agent layer's concern;
    this model is neutral.
    """

    def __init__(self) -> None:
        self._definitions: Dict[str, OfficeDefinition] = {}

    def register(self, definition: Any) -> OfficeDefinition:
        """Register one definition and hold it; duplicates refuse."""
        validated = build_office(definition)
        if validated.office in self._definitions:
            raise ValueError(
                f"the office {validated.office!r} is already registered")
        self._definitions[validated.office] = validated
        return validated

    def register_book(self, book: Any) -> Tuple[OfficeDefinition, ...]:
        """Register every definition of one book, in file order."""
        if not isinstance(book, OfficesBook):
            raise ValueError(f"an offices book is needed, got {book!r}")
        return tuple(self.register(d) for d in book.definitions)

    def get(self, office: Any) -> OfficeDefinition:
        """The definition one office names; unknown raises KeyError."""
        wanted = normalize_formal_office(office)
        if wanted not in self._definitions:
            raise KeyError(f"unknown office: {wanted!r}")
        return self._definitions[wanted]

    def list_definitions(self) -> Tuple[OfficeDefinition, ...]:
        """Every held definition, in registration order."""
        return tuple(self._definitions.values())


# ---------------------------------------------------------------------
# The /offices surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------


def format_office(definition: Any) -> str:
    """One office, in plain words."""
    current = definition if isinstance(definition, OfficeDefinition) \
        else build_office(definition)
    return f"  {current.office}: {plain_words(current)}"


def format_offices(definitions: Any = None) -> str:
    """The offices, in plain words, in the order given.

    With no offices at all the text starts with the
    plain statement of that fact.
    """
    if definitions is None:
        selected: Tuple[OfficeDefinition, ...] = ()
    elif isinstance(definitions, (OfficeRegistry, OfficesBook)):
        selected = definitions.list_definitions() \
            if isinstance(definitions, OfficeRegistry) else definitions.definitions
    else:
        if isinstance(definitions, (str, bytes)) \
                or not isinstance(definitions, (list, tuple)):
            raise ValueError("offices must be a list of definitions")
        selected = tuple(
            d if isinstance(d, OfficeDefinition) else build_office(d)
            for d in definitions)
    if not selected:
        return "Offices: none. No offices are formalised."
    lines = [f"Offices: {len(selected)} formalised."]
    for definition in selected:
        lines.append(format_office(definition))
    return "\n".join(lines)


def format_offices_screen(definitions: Any = None) -> str:
    """The whole slice, in plain words, for /offices."""
    lines = ["The six offices formalised (M-122) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_offices(definitions))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_offices_args(args: Any) -> Tuple[str, Any]:
    """Parse the /offices grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    offices; ``show <office>`` and a bare office id
    show one office; ``handoffs <office>`` asks for
    one office's contracts; ``contract <from> <to>``
    asks for one contract. Anything else is a usage
    error naming the grammar. Returns
    ``(action, value-or-None)`` - a (from, to) pair
    for ``contract``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None \
        else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() in ("show", "list"):
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head == "show" and len(words) == 2:
        try:
            return ("show", normalize_formal_office(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "handoffs" and len(words) == 2:
        try:
            return ("handoffs", normalize_formal_office(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "contract" and len(words) == 3:
        try:
            return ("contract", (normalize_formal_office(words[1]),
                                  normalize_formal_office(words[2])))
        except ValueError:
            raise ValueError(USAGE) from None
    if head in ("show", "handoffs", "contract"):
        raise ValueError(USAGE)
    if len(words) == 1:
        try:
            return ("show", normalize_formal_office(words[0]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
