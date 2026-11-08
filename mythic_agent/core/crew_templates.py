"""Crew templates (All-Features roadmap slice M-143).

Part VI continues here. The roadmap's words:
``saved formations (Duo, Full Six, Research Swarm,
Review Panel) summonable by name.``

What already shipped, and what this slice adds:

* The crew itself is already data
  (``core/crew_members.py``, M-121): a formation's
  seats name that casting's own members, read by
  its ``normalize_member_id`` by import. The
  formations themselves already live as run
  records - a research swarm (``core/
  research_swarms.py``, M-131) is one question's
  fan-out with its findings, and a review panel
  (``core/review_panels.py``, M-132) is one
  change's two reviews - but neither is a saved
  formation that can be summoned by name, and
  crew sizing (``core/crew_sizing.py``, M-135)
  recommends a size for a task's shape; it saves
  no formation either. What nothing holds is the
  template itself, as data: a named formation -
  its seats, in order, each naming a real casting
  member - that a name resolves to.
* This slice is that template book, as a pure
  layer: a formation record validated as data (one
  saved formation, named in plain words, with the
  seats it fields), a roster per formation whose
  member list and size are DERIVED from the
  formation's seats, a template index whose rows,
  totals and account are DERIVED from the whole
  book, the shipped data file
  (``mythic_agent/data/crew_templates.yaml``)
  holding one example template book in exactly
  the shape a real template file takes, a loader
  for a template file anywhere on disk, records
  shaped as session news, and a small in-memory
  registry model. This module summons no crew,
  spawns no agent, calls no model, persists
  nothing and imports no agent / UI code; the
  agent layer owns holding a template book for a
  session. "Summonable by name" at this layer
  means a template can be looked up and resolved
  by name to its validated formation record,
  nothing more.
Honesty rules, enforced here and pinned by tests:

* **Size is derived, never stored loose.** A
  formation record names its seats and no size of
  its own: how many members it fields is read off
  its seats, so a stored ``size`` / ``members`` /
  ``count`` key on a record refuses as an unknown
  key, and no record can claim more seats than it
  names.
* **Members are the shipped casting's own.**
  Member ids read exactly as the M-121 layer
  reads them, composed by import, so every seat
  answers to exactly the validator a live crew
  answers to, and the shipped example's seats are
  all real casting members.
* **A roster is derived, never stored loose.** A
  roster's members, size and account are read off
  its formation's seats, in held order, so a
  stored roster that disagrees with the roster
  derived from its formation refuses. A roster
  naming no account of its own refuses too.
* **The index is derived, never stored loose.**
  The index's rows are the book's rosters, in
  held order; its totals are read off the records
  (every formation held, every seat named, every
  distinct member standing in them) and its
  account is read off the rows and totals, so a
  stored index whose rows, totals or account
  disagree with the derived index refuses.
* **One name, one formation.** A book holding two
  formations under one template word or one
  template id refuses: a name that summoned two
  formations would summon neither honestly.
* **A lead stands in the formation.** A record
  may name the member who leads it; a lead who
  holds no seat in the formation refuses.
* **Data only - no live road is claimed.** A
  template here is a validated record held as
  data: no crew is summoned, spawned or run, no
  agent runs, no model is called and nothing is
  persisted. The formations are visible through
  this slice's own /templates screen.
* **Malformed refuses.** A duplicate template id
  or template word in one book, a roster or index
  naming a formation the book holds no record
  for, and unknown keys in a record, a roster, an
  index or a template mapping all raise instead
  of being skipped or guessed at.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .crew_members import normalize_member_id
from .validation import ValidationError

__all__ = [
    "PLAIN_EXPLANATION",
    "CREW_TEMPLATES_RESOURCE",
    "CREW_TEMPLATES_SCHEMA",
    "CREW_TEMPLATES_SLICE",
    "USAGE",
    "CrewTemplate",
    "CrewTemplateBook",
    "FormationRoster",
    "TemplateIndex",
    "TemplateRegistry",
    "book_record",
    "build_book",
    "build_index",
    "build_roster",
    "build_template",
    "derive_index",
    "derive_roster",
    "format_crew_templates_screen",
    "format_index",
    "format_roster",
    "format_template",
    "format_templates",
    "index_plain_words",
    "index_record",
    "load_crew_templates",
    "load_crew_templates_file",
    "parse_crew_templates_args",
    "plain_words",
    "roster_plain_words",
    "roster_record",
    "template_record",
    "validate_book",
    "validate_index",
    "validate_roster",
    "validate_template",
]

CREW_TEMPLATES_SLICE = "M-143"

#: The packaged data resource holding the example book.
CREW_TEMPLATES_RESOURCE = "crew_templates.yaml"

#: The schema word a crew templates file must carry.
CREW_TEMPLATES_SCHEMA = "mythic.crew_templates/1"

_TEMPLATE_KEYS = frozenset({
    "template_id", "id", "template", "name",
    "title", "headline", "detail", "description",
    "purpose", "slots", "seats", "formation",
    "lead", "leader",
})

_ROSTER_KEYS = frozenset({
    "roster_id", "id", "template", "template_id",
    "members", "member_ids", "size", "count",
    "account", "statements",
})

_INDEX_KEYS = frozenset({
    "index_id", "id", "rows", "rosters",
    "total_templates", "templates",
    "total_slots", "slots",
    "total_members", "members",
    "account", "statements",
})

_BOOK_KEYS = frozenset({"title", "name"})

_CREW_TEMPLATES_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "templates_note", "guide", "entries", "indexes",
})

#: The shipped example book's title, held to this
#: by the loader's example check.
_EXAMPLE_TITLE = "Crew template book at the M-142 slice boundary"

#: The shipped example's template ids, in held
#: order, pinned by the loader.
_EXAMPLE_TEMPLATE_IDS = (
    "tpl-duo", "tpl-full-six",
    "tpl-research-swarm", "tpl-review-panel")

#: The shipped example's template words, in held
#: order, pinned by the loader: the roadmap's four
#: named formations.
_EXAMPLE_TEMPLATE_WORDS = (
    "duo", "full_six", "research_swarm", "review_panel")

#: The shipped example's formation sizes, in held
#: order, pinned by the loader - each name claims
#: exactly the seats its record holds.
_EXAMPLE_TEMPLATE_SIZES = (2, 6, 4, 2)

#: The shipped example's one index: its rows are
#: the formations in held order and its totals are
#: pinned by the loader.
_EXAMPLE_INDEX_ID = "index-m142-boundary"

_EXAMPLE_INDEX_ROWS = (
    "duo", "full_six", "research_swarm", "review_panel")

_EXAMPLE_INDEX_TOTALS = (4, 14, 7)

_EXAMPLE_INDEX_ACCOUNT = (
    "The book holds 4 saved formation(s) naming "
    "14 seat(s) in all.",
    "7 member(s) of the shipped casting stand in "
    "these formations; every seat names a real "
    "casting member.",
    "A template is summoned by name to its record; "
    "nothing in this book runs a crew.",
)

#: The shipped example's pinned first roster: the
#: duo's two seats, its account pinned word-for-word
#: by the loader.
_EXAMPLE_FIRST_ROSTER_ACCOUNT = (
    "duo fields 2 member(s): forge_worker, auditor.",
    "Every seat names a member of the shipped "
    "casting (M-121).",
    "Summoning a template resolves its name to "
    "this formation record; no crew is run by "
    "this layer.",
)

PLAIN_EXPLANATION = (
    "Crew templates: saved formations (Duo, Full "
    "Six, Research Swarm, Review Panel) summonable "
    "by name. A template record names one saved "
    "formation in plain words and the seats it "
    "fields, each seat naming a member of the "
    "shipped casting. A formation's member list and "
    "size are derived from its seats, never stored "
    "loose, and the rosters and the template index "
    "are read off the held records, so a stored "
    "form that disagrees refuses. This layer holds "
    "templates as data only; it summons no crew, "
    "spawns no agent, calls no model and persists "
    "nothing itself - summonable by name here means "
    "a name resolves to the validated formation "
    "record, nothing more."
)

USAGE = (
    "Usage: /templates, /templates show, "
    "/templates template <template>, "
    "/templates member <member-id>, "
    "/templates roster <template>, "
    "/templates index"
)


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_title(value: Any, what: str = "a title") -> str:
    text = _clean_text(value, what)
    if len(text) > 120 or "\x00" in text:
        raise ValueError(
            f"{what} must be plain text of at most "
            f"120 characters, got {len(text)} characters")
    return text


def _check_long_text(value: Any, what: str) -> str:
    text = _clean_text(value, what)
    if len(text) > 2000 or "\x00" in text:
        raise ValueError(
            f"{what} must be plain text of at most "
            f"2000 characters, got {len(text)} characters")
    return text


def _check_account(value: Any) -> Tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"an account must be a list of statements, "
            f"got {value!r}")
    account = tuple(
        _check_long_text(a, "an account statement")
        for a in value)
    if not account:
        raise ValueError("an account carries at least one statement")
    if len(account) > 16:
        raise ValueError(
            f"an account carries at most 16 statements, "
            f"got {len(account)}")
    if len(set(account)) != len(account):
        raise ValueError("an account states one statement twice")
    return account


def _pick_any(mapping: Dict[str, Any], spellings: Tuple[str, ...],
              what: str) -> Any:
    values = [mapping[s] for s in spellings if s in mapping]
    if not values:
        return None
    if any(value != values[0] for value in values[1:]):
        raise ValueError(f"a record names two different {what}")
    return values[0]


def _check_count(value: Any, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{what} must be a count, got {value!r}")
    if value < 0:
        raise ValueError(f"{what} must not be negative, got {value!r}")
    return value


def _check_id_list(value: Any, what: str) -> Tuple[str, ...]:
    if isinstance(value, (str, bytes)) \
            or not isinstance(value, (list, tuple)):
        raise ValueError(f"{what} must be a list, got {value!r}")
    return tuple(normalize_member_id(v) for v in value)


def _check_slots(value: Any) -> Tuple[str, ...]:
    slots = _check_id_list(value, "a formation's slots")
    if not slots:
        raise ValueError("a formation fields at least one seat")
    if len(set(slots)) != len(slots):
        raise ValueError(
            "a formation names one member twice: "
            "one member holds one seat")
    return slots


# ---------------------------------------------------------------------
# The template record: one saved formation, summonable by name.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class CrewTemplate:
    """One saved crew formation, summonable by name.

    ``template`` is the formation's own word - the
    name it is summoned by; ``title`` names it in
    plain words and ``detail`` says what the
    formation is for. ``slots`` are its seats, in
    order, each naming a member of the shipped
    casting; ``lead`` is the member who leads it,
    when it names one, and a lead holds a seat.
    The record names NO size and NO member list of
    its own: both are read off the seats, so a
    record can never claim more members than its
    seats name.
    """

    template: str
    title: str
    detail: str
    slots: Tuple[str, ...] = ()
    lead: Optional[str] = None
    template_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.template_id is not None:
            object.__setattr__(
                self, "template_id",
                normalize_member_id(self.template_id))
        object.__setattr__(
            self, "template", normalize_member_id(self.template))
        object.__setattr__(
            self, "title", _check_title(self.title, "a template's title"))
        object.__setattr__(
            self, "detail",
            _check_long_text(self.detail, "a template's detail"))
        object.__setattr__(self, "slots", _check_slots(self.slots))
        if self.lead is not None:
            object.__setattr__(
                self, "lead", normalize_member_id(self.lead))
            if self.lead not in self.slots:
                raise ValueError(
                    "a formation's lead holds one of its "
                    "seats: the lead names a member the "
                    "formation does not field")

    @property
    def members(self) -> Tuple[str, ...]:
        """The formation's member list, derived from its seats."""
        return self.slots

    @property
    def size(self) -> int:
        """How many members the formation fields, derived."""
        return len(self.slots)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "crew_template",
            "slice": CREW_TEMPLATES_SLICE,
            "template_id": self.template_id,
            "template": self.template,
            "title": self.title,
            "detail": self.detail,
            "slots": list(self.slots),
            "members": list(self.members),
            "size": self.size,
            "lead": self.lead,
        }


def validate_template(template: Any) -> CrewTemplate:
    """Validate one template record into a CrewTemplate.

    Accepts a CrewTemplate or a mapping naming a
    ``template`` (or ``name``), a ``title`` (or
    ``headline``), a ``detail`` (or ``description``
    / ``purpose``), ``slots`` (or ``seats`` /
    ``formation``), an optional ``template_id``
    (or ``id``) and an optional ``lead`` (or
    ``leader``). Naming two spellings of one field
    with different values refuses, and unknown keys
    refuse - a stored size key among them, because
    size is derived from the seats, never stored
    on a record.
    """
    if isinstance(template, CrewTemplate):
        return template
    if not isinstance(template, dict):
        raise ValueError(
            f"a template record must be a mapping, "
            f"got {template!r}")
    unknown = set(template) - _TEMPLATE_KEYS
    if unknown:
        raise ValueError(
            "unknown template-record keys: %s"
            % ", ".join(sorted(unknown)))
    name = _pick_any(template, ("template", "name"), "templates")
    if name is None:
        raise ValueError("a template record is missing its template")
    title = _pick_any(template, ("title", "headline"), "titles")
    if title is None:
        raise ValueError("a template record is missing its title")
    detail = _pick_any(
        template, ("detail", "description", "purpose"), "details")
    if detail is None:
        raise ValueError("a template record is missing its detail")
    slots = _pick_any(
        template, ("slots", "seats", "formation"), "slots")
    if slots is None:
        raise ValueError("a template record is missing its slots")
    kwargs: Dict[str, Any] = {
        "template": name, "title": title, "detail": detail,
        "slots": slots}
    template_id = _pick_any(
        template, ("template_id", "id"), "template ids")
    if template_id is not None:
        kwargs["template_id"] = template_id
    lead = _pick_any(template, ("lead", "leader"), "leads")
    if lead is not None:
        kwargs["lead"] = lead
    return CrewTemplate(**kwargs)


def build_template(template: Any = None, **kwargs: Any) -> CrewTemplate:
    """Build one validated template record, from a mapping or field words."""
    if isinstance(template, CrewTemplate) and not kwargs:
        return template
    if isinstance(template, dict) or template is None:
        merged: Dict[str, Any] = {}
        if isinstance(template, dict):
            merged.update(template)
        merged.update(kwargs)
        return validate_template(merged)
    raise ValueError(
        f"a template record must be a mapping, got {template!r}")


def _check_template_ref(value: Any) -> CrewTemplate:
    if isinstance(value, CrewTemplate):
        return value
    if isinstance(value, dict):
        return validate_template(value)
    raise ValueError(f"a template record is needed, got {value!r}")


def _held_templates(source: Any) -> Tuple[CrewTemplate, ...]:
    """The template records one source holds, in held order."""
    if isinstance(source, CrewTemplateBook):
        return source.entries
    if isinstance(source, TemplateRegistry):
        return source.list_templates()
    if isinstance(source, (list, tuple)):
        return tuple(_check_template_ref(e) for e in source)
    raise ValueError(f"template records are needed, got {source!r}")


# ---------------------------------------------------------------------
# The formation roster: one formation's members, derived.
# ---------------------------------------------------------------------


def _roster_account(template: str,
                    members: Tuple[str, ...]) -> Tuple[str, ...]:
    names = ", ".join(members)
    return (
        f"{template} fields {len(members)} member(s): "
        f"{names}.",
        "Every seat names a member of the shipped "
        "casting (M-121).",
        "Summoning a template resolves its name to "
        "this formation record; no crew is run by "
        "this layer.",
    )


@dataclass(frozen=True)
class FormationRoster:
    """One formation's roster, derived from its seats.

    ``members`` are the formation's seats read as
    its member list, in held order; ``size`` is
    their count; ``account`` is the roster's own
    account. Every field is a derivation:
    :func:`validate_roster` judged against a
    formation refuses a roster whose fields
    disagree with the roster that formation
    derives.
    """

    template: str
    members: Tuple[str, ...] = ()
    size: int = 0
    account: Tuple[str, ...] = ()
    template_id: Optional[str] = None
    roster_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.roster_id is not None:
            object.__setattr__(
                self, "roster_id", normalize_member_id(self.roster_id))
        if self.template_id is not None:
            object.__setattr__(
                self, "template_id",
                normalize_member_id(self.template_id))
        object.__setattr__(
            self, "template", normalize_member_id(self.template))
        members = _check_id_list(self.members, "a roster's members")
        if not members:
            raise ValueError("a roster fields at least one member")
        if len(set(members)) != len(members):
            raise ValueError("a roster names one member twice")
        object.__setattr__(self, "members", members)
        object.__setattr__(
            self, "size", _check_count(self.size, "a roster's size"))
        if self.size != len(members):
            raise ValueError(
                "a roster's size must be its members' count")
        object.__setattr__(self, "account", _check_account(self.account))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "crew_formation_roster",
            "slice": CREW_TEMPLATES_SLICE,
            "roster_id": self.roster_id,
            "template_id": self.template_id,
            "template": self.template,
            "members": list(self.members),
            "size": self.size,
            "account": list(self.account),
        }


def derive_roster(template: Any) -> FormationRoster:
    """Derive one formation's roster from its record.

    The roster's members, size and account are read
    off the formation's seats alone, in held order.
    """
    current = _check_template_ref(template)
    return FormationRoster(
        template=current.template,
        members=current.members,
        size=current.size,
        account=_roster_account(current.template, current.members),
        template_id=current.template_id)


def validate_roster(roster: Any, source: Any = None) -> FormationRoster:
    """Validate one formation roster into a FormationRoster.

    Accepts a FormationRoster or a mapping naming
    a ``template``, ``members`` (or
    ``member_ids``), a ``size`` (or ``count``), an
    ``account`` (or ``statements``) and optional
    ``template_id`` and ``roster_id`` (or ``id``)
    spellings. With *source* given (one formation
    record), the roster is judged against the
    roster derived from that formation: a stored
    roster whose template, members, size or
    account disagree with the derived roster
    refuses. A roster naming no account refuses
    too.
    """
    if isinstance(roster, FormationRoster):
        current = roster
    elif isinstance(roster, dict):
        unknown = set(roster) - _ROSTER_KEYS
        if unknown:
            raise ValueError(
                "unknown roster keys: %s" % ", ".join(sorted(unknown)))
        template = _pick_any(roster, ("template",), "templates")
        if template is None:
            raise ValueError("a roster is missing its template")
        members = _pick_any(
            roster, ("members", "member_ids"), "members")
        if members is None:
            raise ValueError("a roster is missing its members")
        size = _pick_any(roster, ("size", "count"), "sizes")
        if size is None:
            raise ValueError("a roster is missing its size")
        account = _pick_any(roster, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError("a roster names no account of its own")
        kwargs: Dict[str, Any] = {
            "template": template, "members": members,
            "size": size, "account": account}
        template_id = _pick_any(
            roster, ("template_id",), "template ids")
        if template_id is not None:
            kwargs["template_id"] = template_id
        roster_id = _pick_any(roster, ("roster_id", "id"), "roster ids")
        if roster_id is not None:
            kwargs["roster_id"] = roster_id
        current = FormationRoster(**kwargs)
    else:
        raise ValueError(f"a roster must be a mapping, got {roster!r}")
    if source is not None:
        derived = derive_roster(source)
        if (current.template != derived.template
                or current.members != derived.members
                or current.size != derived.size
                or current.account != derived.account):
            raise ValueError(
                "a stored roster disagrees with the roster "
                "derived from its formation")
    return current


def build_roster(roster: Any = None, source: Any = None,
                 **kwargs: Any) -> FormationRoster:
    """Build one validated roster, from a mapping or field words."""
    if isinstance(roster, FormationRoster) and not kwargs:
        return validate_roster(roster, source)
    if isinstance(roster, dict) or roster is None:
        merged: Dict[str, Any] = {}
        if isinstance(roster, dict):
            merged.update(roster)
        merged.update(kwargs)
        return validate_roster(merged, source)
    return validate_roster(roster, source)


# ---------------------------------------------------------------------
# The template index: the whole book, derived.
# ---------------------------------------------------------------------


def _index_account(rows: Tuple[FormationRoster, ...],
                   total_templates: int, total_slots: int,
                   total_members: int) -> Tuple[str, ...]:
    return (
        f"The book holds {total_templates} saved "
        f"formation(s) naming {total_slots} seat(s) "
        f"in all.",
        f"{total_members} member(s) of the shipped "
        f"casting stand in these formations; every "
        f"seat names a real casting member.",
        "A template is summoned by name to its "
        "record; nothing in this book runs a crew.",
    )


def _check_roster_ref(value: Any) -> FormationRoster:
    if isinstance(value, FormationRoster):
        return value
    if isinstance(value, dict):
        return validate_roster(value)
    raise ValueError(f"a roster is needed, got {value!r}")


@dataclass(frozen=True)
class TemplateIndex:
    """The template index of one crew template book.

    ``rows`` are the book's rosters, in held order;
    ``total_templates`` is every formation the book
    holds, ``total_slots`` every seat they name and
    ``total_members`` every distinct member
    standing in them, and ``account`` is read off
    the rows and totals. An index whose totals are
    not its own rows' counts refuses at
    construction: the slot total must be its rows'
    own sum and the member total their distinct
    members' count.
    """

    rows: Tuple[FormationRoster, ...] = ()
    total_templates: int = 0
    total_slots: int = 0
    total_members: int = 0
    account: Tuple[str, ...] = ()
    index_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.index_id is not None:
            object.__setattr__(
                self, "index_id", normalize_member_id(self.index_id))
        if isinstance(self.rows, (str, bytes)) \
                or not isinstance(self.rows, (list, tuple)):
            raise ValueError(
                f"an index's rows must be a list of rosters, "
                f"got {self.rows!r}")
        rows = tuple(_check_roster_ref(r) for r in self.rows)
        templates = [row.template for row in rows]
        if len(set(templates)) != len(templates):
            raise ValueError("an index names one formation twice")
        object.__setattr__(self, "rows", rows)
        object.__setattr__(
            self, "total_templates",
            _check_count(
                self.total_templates, "an index's total templates"))
        object.__setattr__(
            self, "total_slots",
            _check_count(self.total_slots, "an index's total slots"))
        object.__setattr__(
            self, "total_members",
            _check_count(self.total_members, "an index's total members"))
        if self.total_templates != len(rows):
            raise ValueError(
                "an index's template total must be its "
                "own rows' count")
        slots = sum(row.size for row in rows)
        if self.total_slots != slots:
            raise ValueError(
                "an index's slot total must be its own "
                "rows' sum")
        members = {m for row in rows for m in row.members}
        if self.total_members != len(members):
            raise ValueError(
                "an index's member total must be its "
                "rows' distinct members")
        object.__setattr__(self, "account", _check_account(self.account))

    def row_for(self, template: Any) -> FormationRoster:
        """The row one formation names in this index."""
        wanted = normalize_member_id(template)
        for row in self.rows:
            if row.template == wanted:
                return row
        raise KeyError(f"no row in the index: template {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "crew_template_index",
            "slice": CREW_TEMPLATES_SLICE,
            "index_id": self.index_id,
            "rows": [row.to_record() for row in self.rows],
            "total_templates": self.total_templates,
            "total_slots": self.total_slots,
            "total_members": self.total_members,
            "account": list(self.account),
        }


def derive_index(source: Any) -> TemplateIndex:
    """Derive the template index from template records.

    The rows are the formations' rosters, in held
    order; the totals are the records' own counts
    and the account is read off the rows and
    totals. An empty source refuses - an index of
    nothing is no index.
    """
    entries = _held_templates(source)
    if not entries:
        raise ValueError("an index needs at least one template record")
    rows = tuple(derive_roster(entry) for entry in entries)
    total_slots = sum(entry.size for entry in entries)
    total_members = len({m for entry in entries for m in entry.members})
    return TemplateIndex(
        rows=rows,
        total_templates=len(entries),
        total_slots=total_slots,
        total_members=total_members,
        account=_index_account(
            rows, len(entries), total_slots, total_members))


def validate_index(index: Any, source: Any = None) -> TemplateIndex:
    """Validate one template index into a TemplateIndex.

    Accepts a TemplateIndex or a mapping naming
    ``rows`` (or ``rosters``),
    ``total_templates`` (or ``templates``),
    ``total_slots`` (or ``slots``),
    ``total_members`` (or ``members``), an
    ``account`` (or ``statements``) and an optional
    ``index_id`` (or ``id``). With *source* given,
    the index is judged against the index derived
    from those records: a stored index whose rows,
    totals or account disagree with the derived
    index refuses.
    """
    if isinstance(index, TemplateIndex):
        current = index
    elif isinstance(index, dict):
        unknown = set(index) - _INDEX_KEYS
        if unknown:
            raise ValueError(
                "unknown index keys: %s" % ", ".join(sorted(unknown)))
        rows = _pick_any(index, ("rows", "rosters"), "rows")
        if rows is None:
            raise ValueError("an index is missing its rows")
        total_templates = _pick_any(
            index, ("total_templates", "templates"), "total templates")
        if total_templates is None:
            raise ValueError("an index is missing its total templates")
        total_slots = _pick_any(
            index, ("total_slots", "slots"), "total slots")
        if total_slots is None:
            raise ValueError("an index is missing its total slots")
        total_members = _pick_any(
            index, ("total_members", "members"), "total members")
        if total_members is None:
            raise ValueError("an index is missing its total members")
        account = _pick_any(index, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError("an index names no account of its own")
        kwargs: Dict[str, Any] = {
            "rows": rows, "total_templates": total_templates,
            "total_slots": total_slots, "total_members": total_members,
            "account": account}
        index_id = _pick_any(index, ("index_id", "id"), "index ids")
        if index_id is not None:
            kwargs["index_id"] = index_id
        current = TemplateIndex(**kwargs)
    else:
        raise ValueError(f"an index must be a mapping, got {index!r}")
    if source is not None:
        derived = derive_index(source)
        if (current.rows != derived.rows
                or current.total_templates != derived.total_templates
                or current.total_slots != derived.total_slots
                or current.total_members != derived.total_members
                or current.account != derived.account):
            raise ValueError(
                "a stored index disagrees with the index "
                "derived from its records")
    return current


def build_index(index: Any = None, source: Any = None,
                **kwargs: Any) -> TemplateIndex:
    """Build one validated index, from a mapping or field words."""
    if isinstance(index, TemplateIndex) and not kwargs:
        return validate_index(index, source)
    if isinstance(index, dict) or index is None:
        merged: Dict[str, Any] = {}
        if isinstance(index, dict):
            merged.update(index)
        merged.update(kwargs)
        return validate_index(merged, source)
    return validate_index(index, source)


# ---------------------------------------------------------------------
# The template book: formation records in held order, indexes judged.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class CrewTemplateBook:
    """One crew template book: saved formations, held whole.

    ``entries`` are the template records, in held
    order; ``indexes`` are template indexes of the
    book - derivations, judged against the book's
    records by :func:`validate_book`;
    ``templates_note`` is the book's own note.
    """

    title: str = ""
    entries: Tuple[CrewTemplate, ...] = ()
    indexes: Tuple[TemplateIndex, ...] = ()
    templates_note: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book's title"))
        if isinstance(self.entries, (str, bytes)) \
                or not isinstance(self.entries, (list, tuple)):
            raise ValueError(
                f"a book's entries must be a list of template "
                f"records, got {self.entries!r}")
        entries = tuple(_check_template_ref(e) for e in self.entries)
        if not entries:
            raise ValueError(
                "a crew template book holds at least one "
                "template record")
        seen_ids = set()
        seen_words = set()
        for entry in entries:
            if entry.template_id is not None:
                if entry.template_id in seen_ids:
                    raise ValueError(
                        f"a template record named "
                        f"{entry.template_id!r} already exists")
                seen_ids.add(entry.template_id)
            if entry.template in seen_words:
                raise ValueError(
                    f"a formation named {entry.template!r} "
                    f"already stands in this book: one "
                    f"name summons one formation")
            seen_words.add(entry.template)
        object.__setattr__(self, "entries", entries)
        if isinstance(self.indexes, (str, bytes)) \
                or not isinstance(self.indexes, (list, tuple)):
            raise ValueError(
                f"a book's indexes must be a list of indexes, "
                f"got {self.indexes!r}")
        indexes = tuple(
            idx if isinstance(idx, TemplateIndex)
            else validate_index(idx)
            for idx in self.indexes)
        seen_indexes = set()
        for index in indexes:
            if index.index_id is not None:
                if index.index_id in seen_indexes:
                    raise ValueError(
                        f"an index named {index.index_id!r} "
                        f"already exists")
                seen_indexes.add(index.index_id)
        object.__setattr__(self, "indexes", indexes)
        if not isinstance(self.templates_note, str):
            raise ValueError("a book's note must be text")
        object.__setattr__(
            self, "templates_note", self.templates_note.strip())

    def template_for(self, template_id: Any) -> CrewTemplate:
        """The template record one id names in this book."""
        wanted = normalize_member_id(template_id)
        for entry in self.entries:
            if entry.template_id == wanted:
                return entry
        raise KeyError(f"no template record in the book: {wanted!r}")

    def template_named(self, template: Any) -> CrewTemplate:
        """The template record one formation word names in this book."""
        wanted = normalize_member_id(template)
        for entry in self.entries:
            if entry.template == wanted:
                return entry
        raise KeyError(f"no formation in the book: {wanted!r}")

    def resolve_template(self, name: Any) -> CrewTemplate:
        """Resolve one name to its formation record.

        A name is a template id or a formation word:
        summoning by name at this layer is this
        lookup, and nothing more. An unknown name
        raises ``KeyError``.
        """
        wanted = normalize_member_id(name)
        for entry in self.entries:
            if entry.template_id == wanted or entry.template == wanted:
                return entry
        raise KeyError(f"no formation answers to the name: {wanted!r}")

    def templates_for(self, member: Any) -> Tuple[CrewTemplate, ...]:
        """Every formation one member stands in, in held order."""
        wanted = normalize_member_id(member)
        return tuple(e for e in self.entries if wanted in e.slots)

    def index_for(self, index_id: Any) -> TemplateIndex:
        """The index one id names in this book."""
        wanted = normalize_member_id(index_id)
        for index in self.indexes:
            if index.index_id == wanted:
                return index
        raise KeyError(f"no index in the book: {wanted!r}")

    def template_ids(self) -> Tuple[str, ...]:
        """Every held template id, in held order."""
        return tuple(e.template_id for e in self.entries if e.template_id)

    def template_words(self) -> Tuple[str, ...]:
        """Every held formation word, in held order."""
        return tuple(e.template for e in self.entries)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "crew_template_book",
            "slice": CREW_TEMPLATES_SLICE,
            "title": self.title,
            "template_ids": list(self.template_ids()),
            "template_count": len(self.entries),
            "index_count": len(self.indexes),
        }


def validate_book(data: Any, *, require_example: bool = False) -> CrewTemplateBook:
    """Validate one crew templates mapping into a CrewTemplateBook.

    The mapping names a ``schema`` (the crew
    templates schema word), a ``guide`` mapping
    (its ``title``), an ``entries`` list and an
    optional ``indexes`` list. Every record stands
    on its own validation, then the whole is
    judged: template ids and formation words
    unique, and every index judged against the
    book's own template records. With
    ``require_example`` the shipped example is held
    to its pinned shape: the pinned title, records
    and index, the index's pinned rows, totals and
    account word-for-word, and the first roster's
    pinned account. Problems raise
    :class:`ValidationError` or ``ValueError``.
    """
    if isinstance(data, CrewTemplateBook):
        return data
    if not isinstance(data, dict):
        raise ValidationError(
            f"a crew template book must be a mapping, got {data!r}")
    unknown = set(data) - _CREW_TEMPLATES_KEYS
    if unknown:
        raise ValidationError(
            "unknown crew templates keys: %s" % ", ".join(sorted(unknown)))
    if data.get("schema") != CREW_TEMPLATES_SCHEMA:
        raise ValidationError(
            f"a crew template book must carry schema "
            f"{CREW_TEMPLATES_SCHEMA!r}, got {data.get('schema')!r}")
    if "entries" not in data:
        raise ValidationError("a crew template book is missing its entries")
    if not isinstance(data["entries"], (list, tuple)):
        raise ValidationError("a crew template book's entries must be a list")
    if data.get("indexes") is not None \
            and not isinstance(data["indexes"], (list, tuple)):
        raise ValidationError("a crew template book's indexes must be a list")
    head = data.get("guide") or {}
    if not isinstance(head, dict):
        raise ValidationError("a crew template book's guide must be a mapping")
    unknown_head = set(head) - _BOOK_KEYS
    if unknown_head:
        raise ValidationError(
            "unknown guide keys: %s" % ", ".join(sorted(unknown_head)))
    try:
        title = _pick_any(head, ("title", "name"), "titles")
        if title is None:
            raise ValidationError("a crew template book is missing its title")
        note = data.get("templates_note") or ""
        if not isinstance(note, str):
            raise ValidationError("a crew template book's note must be text")
        book = CrewTemplateBook(
            title=title, entries=tuple(data["entries"]),
            indexes=tuple(data.get("indexes") or ()),
            templates_note=note)
        for index in book.indexes:
            validate_index(index, book.entries)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    if require_example:
        if book.title != _EXAMPLE_TITLE:
            raise ValidationError(
                "the shipped example crew template book's title is "
                "not the pinned title")
        if book.template_ids() != _EXAMPLE_TEMPLATE_IDS:
            raise ValidationError(
                "the shipped example's template records are not "
                "the pinned records")
        if book.template_words() != _EXAMPLE_TEMPLATE_WORDS:
            raise ValidationError(
                "the shipped example's formations are not "
                "the pinned formations")
        if tuple(e.size for e in book.entries) != _EXAMPLE_TEMPLATE_SIZES:
            raise ValidationError(
                "the shipped example's formations do not field "
                "their pinned sizes")
        index = book.index_for(_EXAMPLE_INDEX_ID)
        if tuple(r.template for r in index.rows) != _EXAMPLE_INDEX_ROWS:
            raise ValidationError(
                "the shipped example index does not name "
                "its pinned rows")
        totals = (
            index.total_templates, index.total_slots,
            index.total_members)
        if totals != _EXAMPLE_INDEX_TOTALS:
            raise ValidationError(
                "the shipped example index does not carry "
                "its pinned totals")
        if index.account != _EXAMPLE_INDEX_ACCOUNT:
            raise ValidationError(
                "the shipped example index does not carry "
                "its pinned account word-for-word")
        first = derive_roster(book.entries[0])
        if first.account != _EXAMPLE_FIRST_ROSTER_ACCOUNT:
            raise ValidationError(
                "the shipped example's first roster does not "
                "carry its pinned account word-for-word")
    return book


def build_book(book: Any = None, **kwargs: Any) -> CrewTemplateBook:
    """Build one validated book, from a mapping or field words."""
    if isinstance(book, CrewTemplateBook) and not kwargs:
        return book
    if isinstance(book, dict):
        if "entries" in book or "schema" in book:
            return validate_book(book)
        merged: Dict[str, Any] = dict(book)
        merged.update(kwargs)
        return CrewTemplateBook(**merged)
    if book is None:
        return CrewTemplateBook(**kwargs)
    raise ValueError(f"a crew template book is needed, got {book!r}")


def _book_from(data: Any, *, require_example: bool) -> CrewTemplateBook:
    try:
        return validate_book(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_crew_templates(
        data: Optional[Dict[str, Any]] = None) -> CrewTemplateBook:
    """Load and validate the shipped example book (or *data*).

    The shipped file is held to the example check:
    the pinned title, template records and index -
    the M-142 boundary book of the roadmap's four
    named formations - so the shipped book covers
    the formations this slice exists to hold.
    """
    raw = data if data is not None else load_resource(CREW_TEMPLATES_RESOURCE)
    return _book_from(raw, require_example=True)


def load_crew_templates_file(path: Any) -> CrewTemplateBook:
    """Load and validate a crew template book from a file at *path*.

    Any file in the crew templates shape, anywhere
    on disk, validated whole - a malformed file
    raises :class:`ValidationError` naming the
    problem, and a missing file raises
    ``FileNotFoundError``. The example check is
    not held: a real template book stands on its
    own records.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _book_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The registry model: one book held record by record, in held order.
# ---------------------------------------------------------------------


class TemplateRegistry:
    """One session's crew template book, held record by record.

    The registry holds template records, never
    rosters or indexes: both are derivations, read
    off held records at call time, so nothing here
    can hold a total stale.
    """

    def __init__(self, book: Any = None) -> None:
        self._title: Optional[str] = None
        self._entries: Dict[str, CrewTemplate] = {}
        self._order: list = []
        self._next_entry = 1
        if book is not None:
            self.register_book(book)

    def _fresh_template_id(self, held_ids: Any) -> str:
        while f"template-{self._next_entry}" in held_ids:
            self._next_entry += 1
        fresh = f"template-{self._next_entry}"
        self._next_entry += 1
        return fresh

    def register_template(self, template: Any) -> CrewTemplate:
        """Register one template record into the held book.

        A record with no id is given a deterministic
        ``template-N`` id. A record id or formation
        word already standing here refuses.
        """
        validated = build_template(template)
        held_ids = set(self._entries)
        if validated.template_id is not None \
                and validated.template_id in held_ids:
            raise ValueError(
                f"a template record named "
                f"{validated.template_id!r} already exists")
        if any(e.template == validated.template
               for e in self._entries.values()):
            raise ValueError(
                f"a formation named {validated.template!r} "
                f"already stands in this book: one name "
                f"summons one formation")
        if validated.template_id is None:
            validated = replace(
                validated,
                template_id=self._fresh_template_id(held_ids))
        self._entries[validated.template_id] = validated
        self._order.append(validated.template_id)
        return validated

    def register_book(self, book: Any) -> CrewTemplateBook:
        """Register every template record of one book, in order.

        The first book held sets the title; a later
        book under a different title refuses, as does
        a book naming a held record id or formation
        word. The book's indexes are derivations,
        not holdings, and are not held.
        """
        validated = build_book(book)
        if self._title is not None and validated.title != self._title:
            raise ValueError(
                "this registry already holds a crew template book "
                "under a different title")
        for entry in validated.entries:
            if entry.template_id in self._entries:
                raise ValueError(
                    f"a template record named "
                    f"{entry.template_id!r} already exists")
            if any(e.template == entry.template
                   for e in self._entries.values()):
                raise ValueError(
                    f"a formation named {entry.template!r} "
                    f"already stands in this book: one name "
                    f"summons one formation")
        self._title = validated.title
        for entry in validated.entries:
            self.register_template(entry)
        return self.book()

    def get_template(self, template_id: Any) -> CrewTemplate:
        """The template record one id names among the held records."""
        wanted = normalize_member_id(template_id)
        if wanted not in self._entries:
            raise KeyError(f"unknown template record: {wanted!r}")
        return self._entries[wanted]

    def resolve_template(self, name: Any) -> CrewTemplate:
        """Resolve one name to its held formation record.

        A name is a template id or a formation word.
        An unknown name raises ``KeyError``.
        """
        wanted = normalize_member_id(name)
        if wanted in self._entries:
            return self._entries[wanted]
        for entry in self._entries.values():
            if entry.template == wanted:
                return entry
        raise KeyError(f"no formation answers to the name: {wanted!r}")

    def list_templates(self) -> Tuple[CrewTemplate, ...]:
        """Every held template record, in the order they were held."""
        return tuple(self._entries[e] for e in self._order)

    def book(self) -> CrewTemplateBook:
        """The held template records as one validated book."""
        if self._title is None:
            raise ValueError("no crew template book is held yet")
        return CrewTemplateBook(
            title=self._title, entries=self.list_templates())

    def roster_for(self, template: Any) -> FormationRoster:
        """Derive one formation's roster, at call time.

        The roster is derived from the held record
        the name resolves to, read at call time -
        the registry holds records, and this roster
        is derived from them.
        """
        return derive_roster(self.resolve_template(template))

    def index(self) -> TemplateIndex:
        """Derive the template index of the held book.

        The rows, totals and account are the held
        records' own counts, read at call time.
        """
        return derive_index(self.list_templates())


# ---------------------------------------------------------------------
# Crew template news, shaped as session records.
# ---------------------------------------------------------------------


def template_record(template: Any) -> Dict[str, Any]:
    """The session-news record of one template record."""
    current = template if isinstance(template, CrewTemplate) \
        else build_template(template)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.template} is a saved formation of "
        f"{current.size} member(s), summonable by name.")
    return record


def roster_record(roster: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one formation roster.

    With *source* given, the roster is first judged
    against the formation it belongs to.
    """
    current = validate_roster(roster, source)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.template} fields {current.size} "
        f"member(s): {', '.join(current.members)}.")
    return record


def index_record(index: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of the template index.

    With *source* given, the index is first judged
    against the records it belongs to.
    """
    current = validate_index(index, source)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Crew templates: {current.total_templates} "
        f"saved formation(s), {current.total_slots} "
        f"seat(s), summonable by name.")
    return record


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one crew template book."""
    current = book if isinstance(book, CrewTemplateBook) else build_book(book)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Crew template book {current.title}: "
        f"{record['template_count']} template "
        f"record(s), {record['index_count']} index(es).")
    return record


def plain_words(template: Any) -> str:
    """One template record, in one plain sentence."""
    current = template if isinstance(template, CrewTemplate) \
        else build_template(template)
    text = (
        f"{current.template} - {current.title}: "
        f"{current.detail} It fields "
        f"{current.size} member(s): "
        f"{', '.join(current.members)}.")
    if current.lead is not None:
        text += f" {current.lead} leads it."
    return text


def roster_plain_words(source: Any) -> str:
    """Rosters in plain words: every roster, in full.

    Accepts a FormationRoster or a CrewTemplateBook.
    Each roster is told whole - its formation and
    its account.
    """
    if isinstance(source, FormationRoster):
        rosters = (validate_roster(source),)
        title = None
    elif isinstance(source, CrewTemplateBook):
        rosters = tuple(
            derive_roster(entry) for entry in source.entries)
        title = source.title
    else:
        raise ValueError(f"a crew template source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    for roster in rosters:
        lines.append(
            f"{roster.template} - {roster.size} member(s)")
        lines.extend(roster.account)
    return "\n".join(lines)


def index_plain_words(source: Any) -> str:
    """The template index in plain words, in full.

    Accepts a TemplateIndex or a CrewTemplateBook.
    The index is told whole - its rows and its
    account.
    """
    if isinstance(source, TemplateIndex):
        index = validate_index(source)
        title = None
    elif isinstance(source, CrewTemplateBook):
        index = derive_index(source.entries)
        title = source.title
    else:
        raise ValueError(f"a crew template source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Template index:")
    for row in index.rows:
        lines.append(
            f"{row.template} - {row.size} member(s)")
    lines.extend(index.account)
    return "\n".join(lines)


# ---------------------------------------------------------------------
# Screens: the formatters and the shared /templates grammar.
# ---------------------------------------------------------------------


def _source_book(source: Any) -> CrewTemplateBook:
    if source is None:
        return load_crew_templates()
    if isinstance(source, TemplateRegistry):
        return source.book()
    if isinstance(source, CrewTemplateBook):
        return source
    raise ValueError(f"a crew template book is needed, got {source!r}")


def format_template(template: Any) -> str:
    """One template record as a screen line."""
    current = template if isinstance(template, CrewTemplate) \
        else build_template(template)
    line = (
        f"{current.template_id or '-'}: {current.template} "
        f"- {current.title} "
        f"({current.size} member(s): "
        f"{', '.join(current.members)})")
    if current.lead is not None:
        line += f" led by {current.lead}"
    return line


def format_templates(source: Any = None, member: Any = None) -> str:
    """Template records of one book, in held order.

    With *member* given, only the formations that
    member stands in are shown.
    """
    book = _source_book(source)
    entries = book.entries if member is None \
        else book.templates_for(member)
    lines = [format_template(entry) for entry in entries]
    if not lines:
        lines.append("No template records are held.")
    return "\n".join(lines)


def format_roster(source: Any = None) -> str:
    """Rosters as screen blocks: formation over derived account.

    Accepts a FormationRoster or a CrewTemplateBook;
    a book shows every roster it derives, in book
    order.
    """
    if isinstance(source, FormationRoster):
        rosters = (validate_roster(source),)
        lines: list = []
    else:
        book = _source_book(source)
        rosters = tuple(
            derive_roster(entry) for entry in book.entries)
        lines = [f"Rosters in {book.title}:"]
    for roster in rosters:
        lines.append(
            f"{roster.template} - {roster.size} "
            f"member(s): {', '.join(roster.members)}")
        lines.extend(roster.account)
    if isinstance(source, FormationRoster):
        return "\n".join(lines)
    if len(lines) == 1:
        lines.append("Nothing here.")
    return "\n".join(lines)


def format_index(source: Any = None) -> str:
    """The template index as a screen block.

    Accepts a TemplateIndex or a CrewTemplateBook; a
    book shows the index it derives, its rows over
    its derived account.
    """
    if isinstance(source, TemplateIndex):
        index = validate_index(source)
        lines: list = []
    else:
        book = _source_book(source)
        index = derive_index(book.entries)
        lines = [f"Index in {book.title}:"]
    lines.append("Template index:")
    for row in index.rows:
        lines.append(
            f"{row.template} - {row.size} member(s)")
    lines.extend(index.account)
    return "\n".join(lines)


def format_crew_templates_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /templates.

    With nothing named, the shipped example crew
    template book is shown - the example this slice
    ships - so the screen is never empty.
    """
    book = _source_book(source)
    lines = ["Crew templates (M-143) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_templates(book))
    lines.append("")
    lines.append(format_roster(book))
    lines.append("")
    lines.append(format_index(book))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_crew_templates_args(args: Any) -> Tuple[str, Any]:
    """Parse the /templates grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the crew
    template book; ``template <template>`` shows
    one formation record, resolved by name;
    ``member <member-id>`` shows the formations one
    member stands in; ``roster <template>`` shows
    one formation's roster; ``index`` shows the
    template index. Anything else is a usage error
    naming the grammar. Returns
    ``(action, value-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() in ("show", "list"):
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head == "index" and len(words) == 1:
        return ("index", None)
    if head in ("template", "member", "roster") and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
