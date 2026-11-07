"""Custom offices (All-Features roadmap slice M-123).

Part VI - Agents as files - continues here. The
roadmap's words: ``user-defined roles beyond the
six (a "Gatekeeper" for security review, a
"Benchmarker") with the same contract machinery.``

What already shipped, and what this slice adds:

* M-122 (``core/offices.py``) formalised the six
  roadmap offices - Skald, Architect, Forge Worker,
  Auditor, Cartographer, Scribe - as validated data:
  an office definition with duties, tools, inputs,
  outputs and hand-off contracts, a book loader for
  a file anywhere on disk, hand-off closure held
  over the book, and a registry. That machinery
  only ever holds the six: its word reading refuses
  every other office by design.
* This slice is the road beyond the six, as a pure
  layer: user-defined custom offices held as
  validated data (``mythic_agent/data/
  custom_offices.yaml`` ships the roadmap's two
  named examples, Gatekeeper and Benchmarker), a
  custom office definition validated with the SAME
  contract machinery - the duties / tools / inputs /
  outputs / hand-off validators are M-122's own,
  composed with by import, never re-written here -
  a loader for a custom offices file anywhere on
  disk, hand-off contracts validated as a closed
  graph over the custom offices in the same book
  plus the six formalised offices, a custom office
  record shaped as session news, and a small
  in-memory registry model. This module spawns no
  agent, runs no model, opens no session and
  imports no agent / UI code; the agent layer owns
  holding the registry for a session and offering
  the custom offices on a live surface.

Honesty rules, enforced here and pinned by tests:

* **Custom offices are user-defined, never
  formalised.** A custom office is not one of the
  six, does not become one by being defined here,
  and carries that fact in its record (``formal``
  is false, ``custom`` is true). The shipped file
  holds examples, not a second formalisation: the
  roadmap names the Gatekeeper and the Benchmarker
  as examples of what a user may define.
* **No collision with the shipped vocabulary.** A
  custom office id must not name ANY shipped
  office - not one of the six formalised offices,
  not the shipped crew offices M-122 does not
  formalise (``polymath``, ``guardian``), and never
  ``primary``, the lead session itself. The refusal
  is plain and names the boundary, so a custom
  office can never silently override, shadow or
  be mistaken for a shipped office.
* **Hand-offs are a closed graph, widened only to
  the six.** A contract names a target that is
  either a formalised office (read through M-122's
  own word reading) or a custom office defined in
  the same book - never the office itself. A
  dangling, self, or duplicated contract refuses.
* **Malformed refuses.** An empty duty / input /
  output, an empty or duplicated tool list, a
  duplicate office or contract in one file, and
  unknown keys all raise instead of being skipped
  or guessed at - the M-122 rule, held by M-122's
  own validators.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Tuple

from ..resources import load_resource
from .offices import FORMAL_OFFICES, OfficeDefinition
from .offices import _check_tools, _check_words, _clean_text
from .offices import normalize_formal_office
from .role_routing import office_ids
from .validation import ValidationError

__all__ = [
    "CUSTOM_OFFICES_RESOURCE",
    "CUSTOM_OFFICES_SCHEMA",
    "CUSTOM_OFFICES_SLICE",
    "EXAMPLE_CUSTOM_OFFICES",
    "PLAIN_EXPLANATION",
    "USAGE",
    "CustomHandoffContract",
    "CustomOfficeDefinition",
    "CustomOfficeRegistry",
    "CustomOfficesBook",
    "build_custom_office",
    "custom_office_record",
    "example_custom_office_ids",
    "format_custom_office",
    "format_custom_offices",
    "format_custom_offices_screen",
    "is_custom_office_id",
    "load_custom_offices",
    "load_custom_offices_file",
    "normalize_custom_office",
    "normalize_handoff_target",
    "parse_custom_offices_args",
    "plain_words",
    "validate_custom_office",
    "validate_custom_offices",
]

CUSTOM_OFFICES_SLICE = "M-123"

#: The packaged data resource holding the example custom offices.
CUSTOM_OFFICES_RESOURCE = "custom_offices.yaml"

#: The schema word a custom offices file must carry.
CUSTOM_OFFICES_SCHEMA = "mythic.custom_offices/1"

#: The example custom offices the shipped file holds, in file
#: order: the two examples the roadmap itself names. They are
#: examples of user-defined offices, not a formalised list -
#: a user's own file may define any custom offices whose ids
#: obey the no-collision rule.
EXAMPLE_CUSTOM_OFFICES: Tuple[str, ...] = ("gatekeeper", "benchmarker")

PLAIN_EXPLANATION = (
    "Custom offices: roles a user defines beyond "
    "the six formalised offices - the roadmap's "
    "examples are a Gatekeeper (security review) "
    "and a Benchmarker - held as data with the "
    "same duties, tools, inputs, outputs and "
    "hand-off contracts as a formalised office, "
    "validated by the same machinery. A custom "
    "office is user-defined, not formalised: its "
    "name must not collide with any shipped office "
    "(the six, or the shipped polymath and guardian "
    "crew offices, or the primary lead session), "
    "and it never overrides one. Its hand-offs land "
    "on a formalised office or on a custom office "
    "defined in the same book. This layer holds "
    "custom offices as data only; it spawns no "
    "agent and runs no model itself."
)

USAGE = (
    "Usage: /offices custom, /offices custom show, "
    "/offices custom show <office>, "
    "/offices custom handoffs <office>, "
    "/offices custom contract <from> <to>"
)

_CUSTOM_OFFICE_KEYS = frozenset({
    "id", "office", "title", "focus", "purpose",
    "duties", "tools", "inputs", "outputs", "handoffs",
})

_BOOK_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "custom_note", "offices",
})

_HANDOFF_KEYS = frozenset({"to", "artifact", "condition"})

_ID_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyz0123456789_")


def _raw_word(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip().lower().replace("-", "_")


def normalize_custom_office(value: Any) -> str:
    """The canonical custom office id a word names.

    Custom office words read as the shipped office
    words read (case-insensitively, dashes as
    underscores), then the no-collision rule is held:
    a word naming any shipped office refuses, naming
    the boundary - a formalised office is already
    formalised, a shipped crew office is already the
    crew's, and ``primary`` is the lead session
    itself. A custom id is one word of lowercase
    letters, digits and underscores, starting with a
    letter; anything else raises.
    """
    wanted = _raw_word(value)
    if wanted in FORMAL_OFFICES:
        raise ValueError(
            "the %s office is one of the six formalised "
            "offices (M-122); a custom office must not "
            "collide with or override a formalised office"
            % wanted)
    if wanted == "primary":
        raise ValueError(
            "the primary office is the lead session itself, "
            "never a custom office")
    if wanted in office_ids():
        raise ValueError(
            "the %s office is a shipped crew office; a custom "
            "office must not collide with a shipped office"
            % wanted)
    if not wanted or wanted[0] not in "abcdefghijklmnopqrstuvwxyz" \
            or not all(ch in _ID_CHARS for ch in wanted):
        raise ValueError(
            "a custom office id must be one word of letters, "
            "digits and underscores, starting with a letter, "
            f"got {value!r}")
    return wanted


def is_custom_office_id(value: Any) -> bool:
    """True when a word names a valid custom office id."""
    try:
        normalize_custom_office(value)
    except ValueError:
        return False
    return True


def normalize_handoff_target(value: Any) -> str:
    """The canonical hand-off target a word names.

    A target is a formalised office (read through
    M-122's own reading, composed by import) or a
    custom office id. A shipped office outside the
    six refuses here, as it refuses in M-122: a
    hand-off must land on an office this machinery
    holds - a formalised office, or a custom office
    the same book defines (the book-level closure
    check in :func:`validate_custom_offices`).
    """
    wanted = _raw_word(value)
    if wanted in FORMAL_OFFICES:
        return normalize_formal_office(value)
    if wanted in office_ids():
        return normalize_formal_office(value)
    return normalize_custom_office(value)


def example_custom_office_ids() -> Tuple[str, ...]:
    """Every example custom office id, in the shipped order."""
    return EXAMPLE_CUSTOM_OFFICES


# ---------------------------------------------------------------------
# The hand-off contract: one edge of the custom offices' graph.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class CustomHandoffContract:
    """One hand-off contract: an artifact, and its condition.

    ``to_office`` is a formalised office or a custom
    office; ``artifact`` names what is handed over;
    ``condition`` states, in plain words, what must
    be true of the artifact when it changes hands.
    Whether a custom target is defined in the same
    book is a book-level rule, checked by
    :func:`validate_custom_offices`.
    """

    to_office: str = ""
    artifact: str = ""
    condition: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "to_office", normalize_handoff_target(self.to_office))
        object.__setattr__(
            self, "artifact", _clean_text(self.artifact, "a hand-off artifact"))
        object.__setattr__(
            self, "condition",
            _clean_text(self.condition, "a hand-off condition"))

    def to_record(self) -> Dict[str, Any]:
        return {"to": self.to_office, "artifact": self.artifact,
                "condition": self.condition}


def _check_handoff(value: Any) -> CustomHandoffContract:
    if isinstance(value, CustomHandoffContract):
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
    return CustomHandoffContract(
        to_office=value["to"], artifact=value["artifact"],
        condition=value["condition"])


# ---------------------------------------------------------------------
# The custom office definition: one user-defined office, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class CustomOfficeDefinition:
    """One custom office, as data.

    The shape is M-122's office shape, held by
    M-122's own validators (composed by import):
    ``office`` is the user-defined custom id;
    ``title`` names the office as its user calls
    it; ``focus`` is its one-phrase charge;
    ``purpose`` states what it is for; ``duties``
    states what it is responsible for; ``tools``
    is the tool names it works with; ``inputs`` /
    ``outputs`` name what it takes in and produces;
    ``handoffs`` is its hand-off contracts.
    Constructing one validates it, so a definition
    that exists is one a session could be shown.
    """

    office: str = ""
    title: str = ""
    focus: str = ""
    purpose: str = ""
    duties: Tuple[str, ...] = ()
    tools: Tuple[str, ...] = ()
    inputs: Tuple[str, ...] = ()
    outputs: Tuple[str, ...] = ()
    handoffs: Tuple[CustomHandoffContract, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "office", normalize_custom_office(self.office))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a custom office title"))
        object.__setattr__(
            self, "focus", _clean_text(self.focus, "a custom office focus"))
        object.__setattr__(
            self, "purpose",
            _clean_text(self.purpose, "a custom office purpose"))
        object.__setattr__(
            self, "duties", _check_words(self.duties, "a custom office's duties"))
        object.__setattr__(self, "tools", _check_tools(self.tools))
        object.__setattr__(
            self, "inputs", _check_words(self.inputs, "a custom office's inputs"))
        object.__setattr__(
            self, "outputs",
            _check_words(self.outputs, "a custom office's outputs"))
        if isinstance(self.handoffs, (str, bytes)) \
                or not isinstance(self.handoffs, (list, tuple)):
            raise ValueError(
                f"a custom office's handoffs must be a list of "
                f"contracts, got {self.handoffs!r}")
        contracts = tuple(_check_handoff(h) for h in self.handoffs)
        for contract in contracts:
            if contract.to_office == self.office:
                raise ValueError(
                    f"the {self.office} custom office hands off to "
                    "itself; a contract names another office")
        targets = [c.to_office for c in contracts]
        if len(set(targets)) != len(targets):
            raise ValueError(
                "a custom office's hand-offs name a target twice: %s"
                % ", ".join(sorted(
                    t for t in set(targets) if targets.count(t) > 1)))
        object.__setattr__(self, "handoffs", contracts)

    def contract_to(self, office: Any) -> CustomHandoffContract:
        """The contract to one office; no contract raises KeyError."""
        wanted = normalize_handoff_target(office)
        for contract in self.handoffs:
            if contract.to_office == wanted:
                return contract
        raise KeyError(
            f"the {self.office} custom office has no hand-off "
            f"to {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "custom_office",
            "slice": CUSTOM_OFFICES_SLICE,
            "office": self.office,
            "title": self.title,
            "focus": self.focus,
            "purpose": self.purpose,
            "duties": list(self.duties),
            "tools": list(self.tools),
            "inputs": list(self.inputs),
            "outputs": list(self.outputs),
            "handoffs": [c.to_record() for c in self.handoffs],
            "formal": False,
            "custom": True,
        }


def _pick(mapping: Dict[str, Any], first: str, second: str,
          what: str) -> Any:
    """One field from its two spellings, or a refusal."""
    if first in mapping and second in mapping:
        if mapping[first] != mapping[second]:
            raise ValueError(f"a custom office names two different {what}")
        return mapping[first]
    if first in mapping:
        return mapping[first]
    return mapping.get(second)


def validate_custom_office(definition: Any) -> CustomOfficeDefinition:
    """Validate one custom office definition.

    Accepts a CustomOfficeDefinition or a mapping
    naming an ``office`` (or ``id``), a ``title``, a
    ``focus``, a ``purpose``, ``duties``, ``tools``,
    ``inputs``, ``outputs`` and ``handoffs``. A
    formalised OfficeDefinition refuses plainly: it
    is already held by the M-122 machinery. Naming
    both spellings of the office with different
    values refuses, and unknown keys refuse.
    """
    if isinstance(definition, CustomOfficeDefinition):
        return definition
    if isinstance(definition, OfficeDefinition):
        raise ValueError(
            "a formalised office is held by the M-122 offices "
            "machinery, never as a custom office")
    if not isinstance(definition, dict):
        raise ValueError(
            f"a custom office definition must be a mapping, "
            f"got {definition!r}")
    unknown = set(definition) - _CUSTOM_OFFICE_KEYS
    if unknown:
        raise ValueError(
            "unknown custom office keys: %s" % ", ".join(sorted(unknown)))
    for field in ("title", "focus", "purpose", "duties", "tools",
                  "inputs", "outputs", "handoffs"):
        if field not in definition:
            raise ValueError(
                f"a custom office definition is missing its {field}")
    office = _pick(definition, "office", "id", "office ids")
    if office is None:
        raise ValueError("a custom office definition is missing its office")
    return CustomOfficeDefinition(
        office=office, title=definition["title"], focus=definition["focus"],
        purpose=definition["purpose"], duties=definition["duties"],
        tools=definition["tools"], inputs=definition["inputs"],
        outputs=definition["outputs"], handoffs=definition["handoffs"])


def build_custom_office(definition: Any = None,
                        **kwargs: Any) -> CustomOfficeDefinition:
    """Build one validated custom office definition.

    From a CustomOfficeDefinition, from a mapping
    (the spellings :func:`validate_custom_office`
    reads), or from field words given as keyword
    arguments.
    """
    if isinstance(definition, CustomOfficeDefinition) and not kwargs:
        return definition
    if isinstance(definition, dict) or definition is None:
        merged: Dict[str, Any] = {}
        if isinstance(definition, dict):
            merged.update(definition)
        merged.update(kwargs)
        return validate_custom_office(merged)
    return validate_custom_office(definition)


# ---------------------------------------------------------------------
# The book: the custom offices held in one file, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class CustomOfficesBook:
    """A whole book: the custom offices one file defines, in order."""

    definitions: Tuple[CustomOfficeDefinition, ...] = ()
    custom_note: str = ""

    def get(self, office: Any) -> CustomOfficeDefinition:
        """The definition one custom office names; undefined raises."""
        wanted = normalize_custom_office(office)
        for definition in self.definitions:
            if definition.office == wanted:
                return definition
        raise KeyError(f"no definition holds the custom office: {wanted!r}")

    def contract(self, from_office: Any,
                 to_office: Any) -> CustomHandoffContract:
        """The contract between two offices; none raises KeyError."""
        return self.get(from_office).contract_to(to_office)

    def handoffs_from(self, office: Any) -> Tuple[CustomHandoffContract, ...]:
        """Every contract one custom office hands out under."""
        return self.get(office).handoffs

    def handoffs_to(self, office: Any) -> Tuple[
            Tuple[str, CustomHandoffContract], ...]:
        """Every (from-office, contract) pair that hands to one office.

        The target may be a formalised office or a
        custom office - both are offices a contract
        in this book may name.
        """
        wanted = normalize_handoff_target(office)
        return tuple(
            (d.office, c) for d in self.definitions
            for c in d.handoffs if c.to_office == wanted)


def validate_custom_offices(data: Any, *,
                             require_examples: bool = False) -> list:
    """Every problem in a custom offices mapping, as plain strings.

    An empty list means the book is well-formed.
    With ``require_examples`` the book must hold
    exactly the shipped examples, each once, in the
    shipped order (the check the shipped file is
    held to; a user's own file is read without it).
    Hand-off closure is always held, widened only
    to the six: every contract's target must be a
    formalised office or a custom office defined in
    the same book.
    """
    if not isinstance(data, dict):
        return [f"a custom offices book must be a mapping, got {data!r}"]
    problems = []
    unknown = set(data) - _BOOK_KEYS
    if unknown:
        problems.append(
            "unknown custom offices book keys: %s"
            % ", ".join(sorted(unknown)))
    if data.get("schema") != CUSTOM_OFFICES_SCHEMA:
        problems.append(
            f"a custom offices book's schema must be "
            f"{CUSTOM_OFFICES_SCHEMA!r}, got {data.get('schema')!r}")
    if data.get("slice") != CUSTOM_OFFICES_SLICE:
        problems.append(
            f"a custom offices book's slice must be "
            f"{CUSTOM_OFFICES_SLICE!r}, got {data.get('slice')!r}")
    raw = data.get("offices")
    if not isinstance(raw, list) or not raw:
        problems.append(
            "a custom offices book must hold a non-empty offices list")
        return problems
    seen: set = set()
    parsed = []
    for index, entry in enumerate(raw):
        try:
            definition = validate_custom_office(entry)
        except ValueError as exc:
            problems.append(f"office {index + 1}: {exc}")
            continue
        parsed.append(definition)
        if definition.office in seen:
            problems.append(
                f"duplicate custom office definition: "
                f"{definition.office!r}")
        seen.add(definition.office)
    for definition in parsed:
        for contract in definition.handoffs:
            if contract.to_office in FORMAL_OFFICES:
                continue
            if contract.to_office not in seen:
                problems.append(
                    f"the {definition.office} custom office hands "
                    f"off to {contract.to_office!r}, which is "
                    "neither a formalised office nor a custom "
                    "office this book defines")
    if require_examples:
        held = tuple(d.office for d in parsed)
        if held != EXAMPLE_CUSTOM_OFFICES:
            problems.append(
                "the shipped book must hold exactly the example "
                "custom offices %s in order, got %s"
                % ("/".join(EXAMPLE_CUSTOM_OFFICES),
                   "/".join(held) or "none"))
    return problems


def _book_from(data: Any, *, require_examples: bool) -> CustomOfficesBook:
    problems = validate_custom_offices(
        data, require_examples=require_examples)
    if problems:
        raise ValidationError(
            "invalid custom offices book: " + "; ".join(problems))
    assert isinstance(data, dict)
    return CustomOfficesBook(
        definitions=tuple(
            validate_custom_office(entry) for entry in data["offices"]),
        custom_note=str(data.get("custom_note") or ""))


def load_custom_offices(data: Any = None) -> CustomOfficesBook:
    """Load and validate the shipped book (or *data*).

    The shipped book is held to its examples: exactly
    the Gatekeeper and the Benchmarker, each once, in
    the shipped order. Raises :class:`ValidationError`
    listing every problem when the record is not a
    well-formed book.
    """
    raw = data if data is not None else load_resource(CUSTOM_OFFICES_RESOURCE)
    return _book_from(raw, require_examples=True)


def load_custom_offices_file(path: Any) -> CustomOfficesBook:
    """Load and validate a custom offices book from a file at *path*.

    Any file in the book shape, anywhere on disk,
    validated whole - a malformed file raises
    :class:`ValidationError` naming the problem,
    and a missing file raises ``FileNotFoundError``.
    The shipped examples are not required: a file
    may define a single custom office (its hand-offs
    must still land on a formalised office or inside
    the same file).
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _book_from(raw, require_examples=False)


# ---------------------------------------------------------------------
# Custom office news, shaped as a session record.
# ---------------------------------------------------------------------


def custom_office_record(definition: Any) -> Dict[str, Any]:
    """The session-news record of one custom office.

    Carries the office's whole definition plus a
    one-line plain headline, so a custom office shown
    in a session is news with its shape attached,
    never a bare log line. The record states plainly
    that the office is custom and not formalised.
    """
    current = definition if isinstance(definition, CustomOfficeDefinition) \
        else build_custom_office(definition)
    record = current.to_record()
    record["news"] = True
    record["headline"] = plain_words(current)
    return record


def plain_words(definition: Any) -> str:
    """One custom office, in one plain sentence."""
    current = definition if isinstance(definition, CustomOfficeDefinition) \
        else build_custom_office(definition)
    hands = ", ".join(
        f"{c.to_office.replace('_', ' ')} ({c.artifact.split(' - ')[0]})"
        for c in current.handoffs) or "no office"
    return (
        f"The {current.title} custom office ({current.focus}): "
        f"duties - {'; '.join(current.duties)} "
        f"Tools: {', '.join(current.tools)}. "
        f"Hands off to {hands}.")


# ---------------------------------------------------------------------
# The registry model: definitions held in registration order.
# ---------------------------------------------------------------------


class CustomOfficeRegistry:
    """An in-memory registry of custom office definitions.

    Definitions are held in registration order,
    keyed by their custom office id - a duplicate
    office refuses. This registry holds custom
    offices only; the formalised six are held by
    M-122's OfficeRegistry, and a formalised
    definition offered here refuses. Storage beyond
    memory (a session's journal, a file) is the
    agent layer's concern; this model is neutral.
    """

    def __init__(self) -> None:
        self._definitions: Dict[str, CustomOfficeDefinition] = {}

    def register(self, definition: Any) -> CustomOfficeDefinition:
        """Register one definition and hold it; duplicates refuse."""
        validated = build_custom_office(definition)
        if validated.office in self._definitions:
            raise ValueError(
                f"the custom office {validated.office!r} is "
                "already registered")
        self._definitions[validated.office] = validated
        return validated

    def register_book(self, book: Any) -> Tuple[CustomOfficeDefinition, ...]:
        """Register every definition of one book, in file order."""
        if not isinstance(book, CustomOfficesBook):
            raise ValueError(f"a custom offices book is needed, got {book!r}")
        return tuple(self.register(d) for d in book.definitions)

    def get(self, office: Any) -> CustomOfficeDefinition:
        """The definition one custom office names; unknown raises."""
        wanted = normalize_custom_office(office)
        if wanted not in self._definitions:
            raise KeyError(f"unknown custom office: {wanted!r}")
        return self._definitions[wanted]

    def list_definitions(self) -> Tuple[CustomOfficeDefinition, ...]:
        """Every held definition, in registration order."""
        return tuple(self._definitions.values())


# ---------------------------------------------------------------------
# The /offices custom surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------


def format_custom_office(definition: Any) -> str:
    """One custom office, in plain words."""
    current = definition if isinstance(definition, CustomOfficeDefinition) \
        else build_custom_office(definition)
    return f"  {current.office}: {plain_words(current)}"


def format_custom_offices(definitions: Any = None) -> str:
    """The custom offices, in plain words, in the order given.

    With no offices at all the text starts with the
    plain statement of that fact.
    """
    if definitions is None:
        selected: Tuple[CustomOfficeDefinition, ...] = ()
    elif isinstance(definitions, (CustomOfficeRegistry, CustomOfficesBook)):
        selected = definitions.list_definitions() \
            if isinstance(definitions, CustomOfficeRegistry) \
            else definitions.definitions
    else:
        if isinstance(definitions, (str, bytes)) \
                or not isinstance(definitions, (list, tuple)):
            raise ValueError("custom offices must be a list of definitions")
        selected = tuple(
            d if isinstance(d, CustomOfficeDefinition)
            else build_custom_office(d) for d in definitions)
    if not selected:
        return "Custom offices: none. No custom offices are defined."
    lines = [f"Custom offices: {len(selected)} defined."]
    for definition in selected:
        lines.append(format_custom_office(definition))
    return "\n".join(lines)


def format_custom_offices_screen(definitions: Any = None) -> str:
    """The whole slice, in plain words, for /offices custom."""
    lines = ["Custom offices (M-123) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_custom_offices(definitions))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_custom_offices_args(args: Any) -> Tuple[str, Any]:
    """Parse the /offices custom grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    custom offices; ``show <office>`` and a bare
    custom office id show one office; ``handoffs
    <office>`` asks for one office's contracts;
    ``contract <from> <to>`` asks for one contract
    (the from-office is a custom office; the target
    may be formalised or custom). Anything else is
    a usage error naming the grammar. Returns
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
            return ("show", normalize_custom_office(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "handoffs" and len(words) == 2:
        try:
            return ("handoffs", normalize_custom_office(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "contract" and len(words) == 3:
        try:
            return ("contract", (normalize_custom_office(words[1]),
                                  normalize_handoff_target(words[2])))
        except ValueError:
            raise ValueError(USAGE) from None
    if head in ("show", "handoffs", "contract"):
        raise ValueError(USAGE)
    if len(words) == 1:
        try:
            return ("show", normalize_custom_office(words[0]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
