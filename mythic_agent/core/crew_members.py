"""Agents as files (All-Features roadmap slice M-121).

Part VI - Agents as files - opens here. The roadmap's
words: ``crew members defined in data (name, office,
model route, tools, posture, character) - the existing
characters become the first castings; new members are
files, not code.``

What already shipped, and what this slice adds:

* The crew already exists - as code. The shipped
  sub-agent definitions live in
  ``mythic_agent/constants.py`` (``DEFAULT_SUBAGENTS``:
  name + prompt prose for eight members), the character
  prose lives as files in ``default_agent_characters/``,
  and :class:`~mythic_agent.agents.llm.AgentManager`
  spawns a member by looking its name up in the session
  config's ``sub_agents`` list. A member's office is
  already data-shaped: ``core/role_routing.py`` (M-029)
  holds the crew's offices and maps every shipped
  member name to exactly one office, and a member's
  posture already has a shipped vocabulary
  (``core/permission_profiles.py``, M-095). What
  nothing in the tree holds is the member *itself* as
  data - one record naming the member's name, office,
  model route, tools, posture and character together,
  so a new member could arrive as a file instead of a
  code change.
* This slice is that missing record, as a pure layer:
  the shipped casting held as validated data
  (``mythic_agent/data/crew_members.yaml`` - the eight
  existing characters as the first castings, their
  names exactly the shipped ``DEFAULT_SUBAGENTS``
  names, their offices exactly the M-029 offices those
  names already map to, their character fields naming
  the shipped character files), a crew member
  validated as data, a loader for a casting file
  anywhere on disk (a new member is a new record in a
  file, proven by tests that load one from a temp
  file), a member record shaped as session news, and
  a small in-memory registry model with deterministic
  ids. This module spawns no agent, runs no model,
  opens no session and imports no agent / UI code;
  the agent layer owns holding the registry for a
  session, spawning a member from its record, and
  publishing a member record into the session.

Honesty rules, enforced here and pinned by tests:

* **The casting is the shipped crew, no more.** The
  shipped file holds exactly the eight shipped
  sub-agent names, one per non-primary office, in
  crew order. A name or office the tree does not
  ship cannot be cast by editing the record's
  spelling - validation refuses unknown offices,
  the ``primary`` office (the lead session itself,
  never a crew member), and postures outside the
  shipped M-095 vocabulary.
* **A route is a route or the session default.**
  ``model_route`` is either null - the member rides
  the session default, which is the shipped truth
  today (``role_routes`` names no office) - or a
  mapping naming a model and a door together. Half
  a route refuses; a route never claims a provider,
  exactly as M-029 holds.
* **New members are files, not code.** Loading a
  casting from any path validates the same shape;
  nothing about a member lives in this module's
  code beyond the shape itself. A file that adds a
  member needs no code change, and a member record
  that is malformed refuses whole, naming the
  problem - it is never skipped or guessed at.
* **The character is named, never copied.** A
  member's ``character`` field names the character
  file that carries its voice; the prose stays in
  that file, so the casting can never drift into a
  second copy of a character.
* **Malformed refuses.** An unknown office or
  posture, an empty name, an empty or duplicated
  tool list, a duplicate member id, name or office
  in one casting, and unknown keys in a member or
  casting mapping all raise instead of being
  skipped or guessed at.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .permission_profiles import BUILTIN_PROFILE_IDS
from .role_routing import office_ids
from .validation import ValidationError

__all__ = [
    "CREW_RESOURCE",
    "CREW_SCHEMA",
    "CREW_SLICE",
    "PLAIN_EXPLANATION",
    "POSTURES",
    "USAGE",
    "Casting",
    "CrewMember",
    "CrewRegistry",
    "CrewRoute",
    "build_member",
    "casting_record",
    "format_crew_screen",
    "format_member",
    "format_members",
    "load_casting",
    "load_casting_file",
    "member_offices",
    "normalize_member_id",
    "normalize_office",
    "normalize_posture",
    "parse_crew_args",
    "plain_words",
    "validate_casting",
    "validate_member",
]

CREW_SLICE = "M-121"

#: The packaged data resource holding the shipped casting.
CREW_RESOURCE = "crew_members.yaml"

#: The schema word a casting file must carry.
CREW_SCHEMA = "mythic.crew_members/1"

#: The postures a member may hold: the shipped M-095
#: permission-profile ids, no others.
POSTURES = BUILTIN_PROFILE_IDS

#: The offices a crew member may hold: every M-029
#: office except ``primary`` - the lead session itself
#: is never a crew member.
_MEMBER_OFFICES = tuple(o for o in office_ids() if o != "primary")

PLAIN_EXPLANATION = (
    "A crew member is a file, not code: one record "
    "names the member's name, the office it holds, "
    "the model route it rides (or the session "
    "default, when it names none), the tools it "
    "works with, the posture it works under, and "
    "the character file that carries its voice. "
    "The existing characters are the first castings "
    "- the shipped crew, held as data in the "
    "casting file. A new member joins by adding a "
    "record to a file in that shape; no code "
    "changes, and a malformed record is refused "
    "whole instead of being skipped or guessed at. "
    "This layer holds the castings and the members "
    "as data only; it spawns no agent and runs no "
    "model itself."
)

USAGE = (
    "Usage: /crew, /crew show, "
    "/crew show <member>, /crew office <office>"
)

_MEMBER_KEYS = frozenset({
    "id", "member_id", "name", "office",
    "model_route", "route", "tools", "posture",
    "character",
})

_CASTING_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "casting_note", "members",
})

_MEMBER_ID_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789-_.")

_TOOL_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789_")


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def normalize_member_id(value: Any) -> str:
    """The canonical member id a word names.

    A member id is one word of letters, digits,
    dashes, underscores and dots, read with its
    case kept. Anything else raises.
    """
    if isinstance(value, str):
        wanted = value.strip()
        if wanted and all(ch in _MEMBER_ID_CHARS for ch in wanted):
            return wanted
    raise ValueError(
        f"a crew member id must be a non-empty word of letters, "
        f"digits, dashes, underscores and dots, got {value!r}")


def normalize_office(value: Any) -> str:
    """The canonical crew office a word names.

    Office words read case-insensitively, with
    dashes read as underscores - the reading the
    role-routing layer gives its office words. The
    ``primary`` office refuses: it is the lead
    session itself, never a crew member. An
    unknown office raises.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace("-", "_")
        if wanted == "primary":
            raise ValueError(
                "the primary office is the lead session itself, "
                "never a crew member")
        if wanted in _MEMBER_OFFICES:
            return wanted
    raise ValueError(
        "a crew office must be one of %s, got %r"
        % ("/".join(_MEMBER_OFFICES), value))


def normalize_posture(value: Any) -> str:
    """The canonical posture a word names (an M-095 profile id)."""
    if isinstance(value, str):
        wanted = value.strip().lower().replace("_", "-")
        if wanted in POSTURES:
            return wanted
    raise ValueError(
        "a crew posture must be one of %s, got %r"
        % ("/".join(POSTURES), value))


def member_offices() -> Tuple[str, ...]:
    """Every office a crew member may hold, in crew order."""
    return _MEMBER_OFFICES


def _check_tools(value: Any) -> Tuple[str, ...]:
    if isinstance(value, (str, bytes)) \
            or not isinstance(value, (list, tuple)):
        raise ValueError(
            f"a crew member's tools must be a list of tool names, "
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
        raise ValueError("a crew member must name at least one tool")
    if len(set(tools)) != len(tools):
        raise ValueError(
            "a crew member's tools name a tool twice: %s"
            % ", ".join(sorted(
                t for t in set(tools) if tools.count(t) > 1)))
    return tuple(tools)


# ---------------------------------------------------------------------
# The model route: a model and a door together, or the session default.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class CrewRoute:
    """One member's explicit model route: a model and its door.

    A route names a model and a base_url together -
    half a route is malformed. A route never claims
    a provider: the provider is inferred from the
    door by the M-029 road when the route is applied.
    """

    model: str = ""
    base_url: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "model", _clean_text(self.model, "a route model"))
        object.__setattr__(
            self, "base_url",
            _clean_text(self.base_url, "a route base_url"))

    def to_record(self) -> Dict[str, Any]:
        return {"model": self.model, "base_url": self.base_url}


def _check_route(value: Any) -> Optional[CrewRoute]:
    if value is None:
        return None
    if isinstance(value, CrewRoute):
        return value
    if isinstance(value, dict):
        unknown = set(value) - {"model", "base_url"}
        if unknown:
            raise ValueError(
                "unknown model route keys: %s"
                % ", ".join(sorted(unknown)))
        if "model" not in value or "base_url" not in value:
            raise ValueError(
                "a model route names a model and a base_url "
                "together, or is null for the session default")
        return CrewRoute(model=value["model"],
                         base_url=value["base_url"])
    raise ValueError(
        f"a model route must be null or a mapping with a model "
        f"and a base_url, got {value!r}")


# ---------------------------------------------------------------------
# The crew member: one member of the crew, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class CrewMember:
    """One crew member, as data.

    ``name`` is the member's shipped name; ``office``
    is the M-029 office it holds; ``model_route`` is
    its explicit route or None for the session
    default; ``tools`` is the tool names it works
    with; ``posture`` is its M-095 permission-profile
    id; ``character`` names the character file that
    carries its voice.

    Constructing one validates it, so a CrewMember
    that exists is a member a session could spawn.
    """

    member_id: Optional[str] = None
    name: str = ""
    office: str = ""
    model_route: Optional[CrewRoute] = None
    tools: Tuple[str, ...] = ()
    posture: str = ""
    character: str = ""

    def __post_init__(self) -> None:
        if self.member_id is not None:
            object.__setattr__(
                self, "member_id",
                normalize_member_id(self.member_id))
        name = _clean_text(self.name, "a crew member name")
        if len(name) > 120:
            raise ValueError(
                f"a crew member name is at most 120 characters, "
                f"got {len(name)}")
        object.__setattr__(self, "name", name)
        object.__setattr__(
            self, "office", normalize_office(self.office))
        object.__setattr__(
            self, "model_route", _check_route(self.model_route))
        object.__setattr__(self, "tools", _check_tools(self.tools))
        object.__setattr__(
            self, "posture", normalize_posture(self.posture))
        object.__setattr__(
            self, "character",
            _clean_text(self.character, "a character file"))

    @property
    def route_words(self) -> str:
        """The member's route in plain words."""
        if self.model_route is None:
            return "the session default"
        return (f"{self.model_route.model} at "
                f"{self.model_route.base_url}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "crew_member",
            "slice": CREW_SLICE,
            "member_id": self.member_id,
            "name": self.name,
            "office": self.office,
            "model_route": (None if self.model_route is None
                            else self.model_route.to_record()),
            "tools": list(self.tools),
            "posture": self.posture,
            "character": self.character,
        }


def _pick(mapping: Dict[str, Any], first: str, second: str,
          what: str) -> Any:
    """One field from its two spellings, or a refusal.

    Naming both spellings with different values
    refuses - a member is never repaired by
    guessing which spelling the caller meant.
    """
    if first in mapping and second in mapping:
        if mapping[first] != mapping[second]:
            raise ValueError(f"a crew member names two different {what}")
        return mapping[first]
    if first in mapping:
        return mapping[first]
    return mapping.get(second)


def validate_member(member: Any) -> CrewMember:
    """Validate one crew member into a CrewMember.

    Accepts a CrewMember or a mapping naming a
    ``name``, an ``office``, a ``posture``, a
    ``character``, a ``tools`` list, an optional
    ``model_route`` (or ``route``) and an optional
    ``member_id`` (or ``id``). Naming both spellings
    of one field with different values refuses, and
    unknown keys refuse.
    """
    if isinstance(member, CrewMember):
        return member
    if not isinstance(member, dict):
        raise ValueError(
            f"a crew member must be a mapping, got {member!r}")
    unknown = set(member) - _MEMBER_KEYS
    if unknown:
        raise ValueError(
            "unknown crew member keys: %s"
            % ", ".join(sorted(unknown)))
    for field in ("name", "office", "tools", "posture", "character"):
        if field not in member:
            raise ValueError(f"a crew member is missing its {field}")
    kwargs: Dict[str, Any] = {
        "name": member["name"],
        "office": member["office"],
        "tools": member["tools"],
        "posture": member["posture"],
        "character": member["character"],
    }
    member_id = _pick(member, "member_id", "id", "member ids")
    if member_id is not None:
        kwargs["member_id"] = member_id
    route = _pick(member, "model_route", "route", "model routes")
    if route is not None:
        kwargs["model_route"] = route
    return CrewMember(**kwargs)


def build_member(member: Any = None, **kwargs: Any) -> CrewMember:
    """Build one validated crew member.

    From a CrewMember, from a mapping (the spellings
    :func:`validate_member` reads), or from field
    words given as keyword arguments.
    """
    if isinstance(member, CrewMember) and not kwargs:
        return member
    if isinstance(member, dict) or member is None:
        merged: Dict[str, Any] = {}
        if isinstance(member, dict):
            merged.update(member)
        merged.update(kwargs)
        return validate_member(merged)
    raise ValueError(
        f"a crew member must be a mapping, got {member!r}")


# ---------------------------------------------------------------------
# The casting: a whole crew held in one file, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class Casting:
    """A whole casting: the members one file defines, in file order."""

    members: Tuple[CrewMember, ...] = ()
    casting_note: str = ""

    def get(self, member_id: Any) -> CrewMember:
        """The member one id names; an unknown id raises KeyError."""
        wanted = normalize_member_id(member_id)
        for member in self.members:
            if member.member_id == wanted:
                return member
        raise KeyError(f"unknown crew member: {wanted!r}")

    def by_office(self, office: Any) -> CrewMember:
        """The member holding one office; an unheld office raises."""
        wanted = normalize_office(office)
        for member in self.members:
            if member.office == wanted:
                return member
        raise KeyError(f"no crew member holds the office: {wanted!r}")

    def by_name(self, name: Any) -> CrewMember:
        """The member one name names; an unknown name raises."""
        wanted = _clean_text(name, "a crew member name")
        for member in self.members:
            if member.name == wanted:
                return member
        raise KeyError(f"unknown crew member name: {wanted!r}")


def validate_casting(data: Any, *,
                     require_complete: bool = False) -> list:
    """Every problem in a casting mapping, as plain strings.

    An empty list means the casting is well-formed.
    With ``require_complete`` the casting must hold
    exactly the shipped crew: every non-primary
    office held exactly once (the check the shipped
    file is held to; a file adding one new member is
    read without it).
    """
    if not isinstance(data, dict):
        return [f"a casting must be a mapping, got {data!r}"]
    problems = []
    unknown = set(data) - _CASTING_KEYS
    if unknown:
        problems.append(
            "unknown casting keys: %s" % ", ".join(sorted(unknown)))
    if data.get("schema") != CREW_SCHEMA:
        problems.append(
            f"a casting's schema must be {CREW_SCHEMA!r}, "
            f"got {data.get('schema')!r}")
    if data.get("slice") != CREW_SLICE:
        problems.append(
            f"a casting's slice must be {CREW_SLICE!r}, "
            f"got {data.get('slice')!r}")
    raw_members = data.get("members")
    if not isinstance(raw_members, list) or not raw_members:
        problems.append("a casting must hold a non-empty members list")
        return problems
    seen_ids, seen_names, seen_offices = set(), set(), set()
    for index, entry in enumerate(raw_members):
        try:
            member = validate_member(entry)
        except ValueError as exc:
            problems.append(f"member {index + 1}: {exc}")
            continue
        if member.member_id is not None:
            if member.member_id in seen_ids:
                problems.append(
                    f"duplicate member id: {member.member_id!r}")
            seen_ids.add(member.member_id)
        if member.name in seen_names:
            problems.append(f"duplicate member name: {member.name!r}")
        seen_names.add(member.name)
        if member.office in seen_offices:
            problems.append(
                f"the office {member.office!r} is held twice in "
                "one casting")
        seen_offices.add(member.office)
    if require_complete:
        for office in _MEMBER_OFFICES:
            if office not in seen_offices:
                problems.append(
                    f"no member holds the office {office!r}")
    return problems


def _casting_from(data: Any, *, require_complete: bool) -> Casting:
    problems = validate_casting(data, require_complete=require_complete)
    if problems:
        raise ValidationError(
            "invalid crew casting: " + "; ".join(problems))
    assert isinstance(data, dict)
    return Casting(
        members=tuple(validate_member(entry)
                      for entry in data["members"]),
        casting_note=str(data.get("casting_note") or ""))


def load_casting(data: Optional[Dict[str, Any]] = None) -> Casting:
    """Load and validate the shipped casting (or *data*).

    The shipped casting is held to completeness:
    every non-primary office held exactly once.
    Raises :class:`ValidationError` listing every
    problem when the record is not a well-formed
    casting.
    """
    raw = data if data is not None else load_resource(CREW_RESOURCE)
    return _casting_from(raw, require_complete=True)


def load_casting_file(path: Any) -> Casting:
    """Load and validate a casting from a file at *path*.

    This is the road a new member arrives by: any
    file in the casting shape, anywhere on disk,
    validated whole - a malformed file raises
    :class:`ValidationError` naming the problem,
    and a missing file raises ``FileNotFoundError``.
    Completeness is not required: a file may define
    a single new member.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _casting_from(raw, require_complete=False)


# ---------------------------------------------------------------------
# Member news, shaped as a session record.
# ---------------------------------------------------------------------


def casting_record(member: Any) -> Dict[str, Any]:
    """The session-news record of one crew member.

    Carries the member's whole record plus a one-line
    plain headline, so a member joining a session is
    news with its shape attached, never a bare log
    line.
    """
    current = build_member(member) \
        if not isinstance(member, CrewMember) else member
    record = current.to_record()
    record["news"] = True
    record["headline"] = plain_words(current)
    return record


def plain_words(member: Any) -> str:
    """One member, in one plain sentence."""
    current = member if isinstance(member, CrewMember) \
        else build_member(member)
    office_title = current.office.replace("_", " ")
    return (
        f"{current.name} holds the {office_title} office: "
        f"tools {', '.join(current.tools)}; posture "
        f"{current.posture}; model route "
        f"{current.route_words}; character from "
        f"{current.character}.")


# ---------------------------------------------------------------------
# The registry model: members held in registration order, ids
# deterministic.
# ---------------------------------------------------------------------


class CrewRegistry:
    """An in-memory registry of crew members.

    Members are held in registration order. Ids are
    deterministic: a caller-supplied id is used as
    given (a duplicate id or name refuses), and an
    unsupplied id is the next ``crew-N`` in
    sequence, skipping any number a supplied id
    already took - no randomness a test cannot pin.
    Storage beyond memory (a session's journal, a
    file) is the agent layer's concern; this model
    is neutral.
    """

    def __init__(self) -> None:
        self._members: Dict[str, CrewMember] = {}
        self._next = 1

    def _fresh_id(self) -> str:
        while f"crew-{self._next}" in self._members:
            self._next += 1
        member_id = f"crew-{self._next}"
        self._next += 1
        return member_id

    def register(self, member: Any) -> CrewMember:
        """Register one member and hold it; duplicates refuse."""
        validated = build_member(member)
        if validated.member_id is None:
            validated = replace(
                validated, member_id=self._fresh_id())
        elif validated.member_id in self._members:
            raise ValueError(
                f"a crew member named {validated.member_id!r} "
                "already exists")
        for held in self._members.values():
            if held.name == validated.name:
                raise ValueError(
                    f"a crew member named {validated.name!r} "
                    "already exists")
        self._members[validated.member_id] = validated
        return validated

    def register_casting(self, casting: Any) -> Tuple[CrewMember, ...]:
        """Register every member of one casting, in file order."""
        if not isinstance(casting, Casting):
            raise ValueError(f"a casting is needed, got {casting!r}")
        return tuple(self.register(member)
                     for member in casting.members)

    def get(self, member_id: Any) -> CrewMember:
        """The member one id names; an unknown id raises KeyError."""
        wanted = normalize_member_id(member_id)
        if wanted not in self._members:
            raise KeyError(f"unknown crew member: {wanted!r}")
        return self._members[wanted]

    def list_members(self, office: Any = None
                     ) -> Tuple[CrewMember, ...]:
        """Every held member, in registration order, optionally
        by office."""
        members = tuple(self._members.values())
        if office is None:
            return members
        wanted = normalize_office(office)
        return tuple(m for m in members if m.office == wanted)


# ---------------------------------------------------------------------
# The /crew surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------


def format_member(member: Any) -> str:
    """One member, in plain words."""
    current = member if isinstance(member, CrewMember) \
        else build_member(member)
    name = current.member_id or current.name
    return f"  {name}: {plain_words(current)}"


def format_members(members: Any = None) -> str:
    """The members, in plain words, in the order given.

    With no members at all the text starts with the
    plain statement of that fact.
    """
    if members is None:
        selected: Tuple[CrewMember, ...] = ()
    elif isinstance(members, (CrewRegistry, Casting)):
        selected = members.list_members() \
            if isinstance(members, CrewRegistry) else members.members
    else:
        if isinstance(members, (str, bytes)) \
                or not isinstance(members, (list, tuple)):
            raise ValueError("crew members must be a list of members")
        selected = tuple(
            m if isinstance(m, CrewMember) else build_member(m)
            for m in members)
    if not selected:
        return "Crew members: none. No crew is defined."
    lines = [f"Crew members: {len(selected)} held."]
    for member in selected:
        lines.append(format_member(member))
    return "\n".join(lines)


def format_crew_screen(members: Any = None) -> str:
    """The whole slice, in plain words, for /crew."""
    lines = ["Agents as files (M-121) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_members(members))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_crew_args(args: Any) -> Tuple[str, Optional[str]]:
    """Parse the /crew grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    crew; ``show <member>`` and a bare member id
    show one member; ``office <office>`` asks for
    the member holding one office. Anything else
    is a usage error naming the grammar. Returns
    ``(action, value-or-None)``.
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
            return ("show", normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "office" and len(words) == 2:
        try:
            return ("office", normalize_office(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head in ("show", "office"):
        # A grammar word in the wrong shape is a usage
        # error, never a member id that happens to spell one.
        raise ValueError(USAGE)
    if len(words) == 1:
        try:
            return ("show", normalize_member_id(words[0]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
