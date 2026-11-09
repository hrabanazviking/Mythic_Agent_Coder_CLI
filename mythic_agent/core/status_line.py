"""The status line of truth (All-Features roadmap slice M-178).

Part VIII - The Beautiful Face - builds here. The
roadmap's words: *model, posture, context meter,
cost so far, crew state, sandbox state - six
facts, always visible, each opening its panel on
a keypress.*

What already ships, and what this slice adds:

* The shipped tree's main chat screen carries its
  state scattered: a token count in dim text here,
  a footer agent status leaning on colour there,
  and no one place where the model in use, the
  posture in force, the context meter, the cost so
  far, the crew state and the sandbox state stand
  together in plain words - so none of it can be
  looked at, counted or judged in one room.
* The M-171 TUI redesign charter's S-03 row (the
  main chat screen, verdict repair, owned by
  M-172, M-173 and this slice) gives the direction
  honoured live here: *gather model, context, cost
  and crew state into one status line of truth -
  no structural rebuild of the screen.* The
  roadmap's six facts complete the gathering:
  posture and sandbox state stand beside the
  charter's four. This slice gathers and derives
  the line and wires the command surface; it does
  NOT rebuild the live screen structurally.
* This slice is that one room, as a pure layer:
  one status fact validated as data WITH ITS
  PROVENANCE WHOLE - its kind in the closed kind
  set (model, posture, context, cost, crew,
  sandbox: the roadmap's own order), its title,
  its value held whole in plain words, its detail,
  and the panel and keypress it opens, named as
  data. The status line itself is DERIVED from
  the six facts - one segment per kind in the
  roadmap's order, a kind holding no measured
  fact standing in the line as honestly unknown -
  and a view is held as its own record (the one
  kind it looks at, or every kind at once). The
  panel is DERIVED for one held view (its rows the
  shown facts in the roadmap's kind order,
  carrying their derived segments, panels and
  keypresses) and a verdict is DERIVED for the
  whole book under one view (complete while all
  six facts stand measured, partial while some
  stand measured, empty while none does). The
  shipped data file
  (``mythic_agent/data/status_line.yaml``) holds
  one example book in exactly the shape a real
  status file takes, a loader reads a status file
  anywhere on disk, facts and views are shaped as
  session news, and a small in-memory registry
  model holds facts and views one by one. The
  agent layer owns holding facts for a session
  and standing a view on them.

Honesty rules, enforced here and pinned by tests:

* **The line is derived, never stored.** A fact
  carries no line, no segment and no status line:
  a mapping naming one refuses. A segment and a
  line exist only as the derivation of the facts'
  own titles and values, and a panel row is judged
  against that derivation: a stored row whose
  segment disagrees refuses.
* **Unmeasured facts stay honestly unknown.** A
  fact whose value is not measured stands with
  the value ``unknown``, and a kind holding no
  fact at all stands in the derived line as
  unknown. This layer never invents a live value
  it cannot measure: no model name, meter, cost,
  crew state or sandbox state is read live here.
* **The panel and keypress are named, not bound.**
  Each fact names the one panel it opens and the
  one keypress that opens it, as data, checked
  against the kind's own panel and keypress. No
  live key is bound and no live panel is opened
  by this layer, and the live chat screen is not
  rebuilt - the charter forbids the rebuild and
  this slice honours it.
* **Data only.** This layer holds facts and views
  as data: it measures nothing live, reads no live
  model, context, cost, crew or sandbox state,
  renders no live UI, binds no key, opens no
  panel, calls no model and persists nothing - a
  fact held here is a finding, never the live
  state of the screen it describes.
"""

from __future__ import annotations

__all__ = [
    "FACT_KINDS",
    "KEYPRESS_FOR_KIND",
    "KIND_TITLES",
    "PANEL_FOR_KIND",
    "PLAIN_EXPLANATION",
    "STATUS_LINE_RESOURCE",
    "STATUS_LINE_SCHEMA",
    "STATUS_LINE_SLICE",
    "THE_STATUS_LINE_SLICE",
    "UNKNOWN_VALUE",
    "USAGE",
    "VERDICT_WORDS",
    "Any",
    "Dict",
    "List",
    "Optional",
    "StatusFact",
    "StatusKindCount",
    "StatusLineBook",
    "StatusLineRegistry",
    "StatusPanel",
    "StatusPanelRow",
    "StatusVerdict",
    "StatusView",
    "Tuple",
    "book_record",
    "build_book",
    "build_fact",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "derive_panel",
    "derive_verdict",
    "fact_from_measured_value",
    "fact_record",
    "facts_for_kind",
    "format_book",
    "format_fact",
    "format_line",
    "format_panel",
    "format_status_line_screen",
    "format_verdict",
    "format_view",
    "inspect_fact_source",
    "is_measured",
    "line_of",
    "load_status_line",
    "load_status_line_file",
    "measured_facts",
    "normalize_kind",
    "normalize_kind_filter",
    "panel_plain_words",
    "panel_record",
    "parse_status_line_args",
    "plain_words",
    "segment_of",
    "shown_facts",
    "total_facts",
    "unknown_fact",
    "unknown_facts",
    "validate_book",
    "validate_fact",
    "validate_panel",
    "validate_row",
    "validate_verdict",
    "validate_view",
    "verdict_plain_words",
    "verdict_record",
    "view_plain_words",
    "view_record",
]

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .crew_members import normalize_member_id

STATUS_LINE_SLICE = "M-178"

#: The longer name other layers cite for this slice.
THE_STATUS_LINE_SLICE = STATUS_LINE_SLICE

STATUS_LINE_RESOURCE = "status_line.yaml"

STATUS_LINE_SCHEMA = "mythic.status_line/1"

#: The kinds one fact may stand under, in the
#: roadmap's own order: the model, the posture, the
#: context meter, the cost so far, the crew state
#: and the sandbox state. The line stands in this
#: order, always.
FACT_KINDS = ("model", "posture", "context", "cost", "crew", "sandbox")

_KIND_ALIASES = {
    "model": "model", "models": "model",
    "posture": "posture", "position": "posture",
    "profile": "posture",
    "context": "context", "meter": "context",
    "context-meter": "context",
    "cost": "cost", "costs": "cost",
    "cost-so-far": "cost",
    "crew": "crew", "team": "crew",
    "crew-state": "crew",
    "sandbox": "sandbox", "sandbox-state": "sandbox",
}

#: The plain title each kind carries in the line.
KIND_TITLES = {
    "model": "Model", "posture": "Posture",
    "context": "Context", "cost": "Cost so far",
    "crew": "Crew", "sandbox": "Sandbox",
}

#: The one panel each kind's fact opens, named as
#: data. No live panel is opened by this layer.
PANEL_FOR_KIND = {
    "model": "model panel", "posture": "posture panel",
    "context": "context panel", "cost": "cost panel",
    "crew": "crew panel", "sandbox": "sandbox panel",
}

#: The one keypress that opens each kind's panel,
#: named as data, in the roadmap's kind order. No
#: live key is bound by this layer.
KEYPRESS_FOR_KIND = {
    "model": "1", "posture": "2", "context": "3",
    "cost": "4", "crew": "5", "sandbox": "6",
}

#: The value a fact carries when it is not
#: measured: the honest word, never an invention.
UNKNOWN_VALUE = "unknown"

#: The words a whole book's verdict under one view
#: may carry: complete while all six facts stand
#: measured, partial while some stand measured,
#: empty while no shown fact stands measured.
VERDICT_WORDS = ("complete", "partial", "empty")

_FACT_KEYS = frozenset({
    "fact_id", "id", "kind", "type_of",
    "title", "name", "label",
    "value", "reading",
    "detail", "note", "description",
    "panel", "panel_name", "opens",
    "keypress", "key", "key_press",
    "recorded_on", "day", "date",
    "actor", "by", "who", "source",
    "origin_session", "session"})

_DERIVED_FACT_KEYS = frozenset({"line", "segment", "status_line"})

_ROW_KEYS = frozenset({
    "fact_id", "id", "kind", "title",
    "segment", "panel", "keypress", "recorded_on"})

_KIND_COUNT_KEYS = frozenset({"kind", "facts", "count"})

_PANEL_KEYS = frozenset({
    "panel_id", "id", "view_id", "view",
    "kind_filter", "filter", "kind",
    "rows", "shown",
    "total_facts", "facts",
    "total_shown", "matched",
    "kind_counts", "kinds",
    "as_of", "day", "account", "statements"})

_VIEW_KEYS = frozenset({
    "view_id", "id", "seq", "sequence", "order",
    "kind_filter", "filter", "kind",
    "detail", "reason",
    "recorded_on", "day", "date",
    "actor", "by", "who", "source",
    "origin_session", "session"})

_VERDICT_KEYS = frozenset({
    "total_facts", "facts",
    "total_shown", "matched",
    "measured_shown", "measured",
    "distinct_kinds", "kinds",
    "earliest_on", "earliest", "latest_on", "latest",
    "verdict"})

_BOOK_KEYS = frozenset({"title", "name"})

_STATUS_LINE_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "canon_note", "guide", "facts", "views",
    "panels"})

_EXAMPLE_TITLE = "Status Line at the M-177 slice boundary"

_EXAMPLE_FACT_IDS = (
    "fact-model", "fact-posture", "fact-context",
    "fact-cost", "fact-crew", "fact-sandbox")

_EXAMPLE_FIRST_FACT_ID = "fact-model"

_EXAMPLE_FIRST_FACT_KIND = "model"

_EXAMPLE_PANEL_ID = "panel-m177-boundary"

_EXAMPLE_AS_OF = "2026-11-09"

_EXAMPLE_VIEW_IDS = ("view-all", "view-cost")

PLAIN_EXPLANATION = (
    "Status Line of Truth: six facts, always "
    "visible - the model, the posture, the context "
    "meter, the cost so far, the crew state and "
    "the sandbox state - gathered into one line, "
    "each fact opening its panel on a keypress. A "
    "fact is one of those six held whole - its "
    "kind (model, posture, context, cost, crew or "
    "sandbox, in the roadmap's own order), its "
    "title, its value and its detail, the panel "
    "and keypress it opens, with its provenance "
    "whole. The M-171 charter's S-03 direction is "
    "honoured live: gather model, context, cost "
    "and crew state into one status line of truth, "
    "with no structural rebuild of the screen. "
    "The status line itself is derived from the "
    "six facts, one segment per kind in the "
    "roadmap's order - never stored, never written "
    "by hand. A fact that is not measured stands "
    "honestly unknown, and a kind holding no fact "
    "stands unknown in the line: no live value is "
    "invented here. Each panel and keypress is "
    "named as data only - no live key is bound, "
    "no live panel is opened and the live chat "
    "screen is not rebuilt. This layer holds "
    "facts and views as data only: it measures "
    "nothing live, reads no live model, context, "
    "cost, crew or sandbox state, renders no live "
    "UI, calls no model and persists nothing - a "
    "fact held here is a finding, never the live "
    "state of the screen it describes."
)

USAGE = (
    "Usage: /statusline, /statusline show, "
    "/statusline fact <fact-id>, "
    "/statusline view <view-id>, "
    "/statusline kind <kind>, "
    "/statusline line, /statusline panel, "
    "/statusline verdict"
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


def _check_seq(value: Any) -> int:
    seq = _check_count(value, "a view's sequence")
    if seq < 1:
        raise ValueError(
            f"a view's sequence stands from 1, got {value!r}")
    return seq


def _check_word(value: Any, what: str) -> str:
    try:
        return normalize_member_id(value)
    except ValueError:
        raise ValueError(
            f"{what} must be one plain word, "
            f"got {value!r}") from None


def _check_day(value: Any, what: str = "a day") -> str:
    text = _clean_text(value, what)
    try:
        parsed = date.fromisoformat(text)
    except ValueError:
        raise ValueError(
            f"{what} must be an ISO date "
            f"(YYYY-MM-DD), got {text!r}") from None
    if parsed.isoformat() != text:
        raise ValueError(
            f"{what} must be an ISO date "
            f"(YYYY-MM-DD), got {text!r}")
    return text


def normalize_kind(value: Any) -> str:
    """One kind word, read onto the closed kind set."""
    if not isinstance(value, str):
        raise ValueError(f"a kind must be a word, got {value!r}")
    kind = _KIND_ALIASES.get(value.strip().lower())
    if kind is None:
        raise ValueError(
            "a kind is one of %s, got %r"
            % ("/".join(FACT_KINDS), value))
    return kind


def normalize_kind_filter(value: Any) -> str:
    """One kind-filter word: every kind, or one named kind."""
    if not isinstance(value, str):
        raise ValueError(
            f"a kind filter must be a word, got {value!r}")
    if value.strip().lower() == "all":
        return "all"
    return normalize_kind(value)


def _check_panel(kind: str, value: Any) -> str:
    panel = _check_title(value, "a panel name")
    wanted = PANEL_FOR_KIND[kind]
    if panel != wanted:
        raise ValueError(
            f"a {kind} fact opens the {wanted!r} panel, "
            f"got {panel!r} - a fact names its kind's own "
            f"panel, never another kind's")
    return panel


def _check_keypress(kind: str, value: Any) -> str:
    keypress = _check_word(value, "a keypress")
    wanted = KEYPRESS_FOR_KIND[kind]
    if keypress != wanted:
        raise ValueError(
            f"a {kind} fact opens on keypress {wanted!r}, "
            f"got {keypress!r} - a fact names its kind's "
            f"own keypress, never another kind's")
    return keypress


def is_measured(fact: Any) -> bool:
    """True when one fact carries a measured value.

    A fact whose value is the honest word
    ``unknown`` is not measured: it stands in the
    line as unknown, and no value is invented
    for it.
    """
    current = _check_fact_ref(fact)
    return current.value.lower() != UNKNOWN_VALUE


def segment_of(fact: Any) -> str:
    """The segment one status fact derives in the line.

    Read off the fact's title and value alone:
    what the fact is called, and what it stands
    at. The segment is derived at call time - it
    is never a field of the fact.
    """
    current = _check_fact_ref(fact)
    return f"{current.title}: {current.value}"


def _segments_for(facts: Tuple["StatusFact", ...]) -> Tuple[str, ...]:
    by_kind = {fact.kind: fact for fact in facts}
    segments = []
    for kind in FACT_KINDS:
        held = by_kind.get(kind)
        if held is None:
            segments.append(f"{KIND_TITLES[kind]}: {UNKNOWN_VALUE}")
        else:
            segments.append(segment_of(held))
    return tuple(segments)


def line_of(source: Any) -> str:
    """The status line one source derives, whole.

    One segment per kind in the roadmap's own
    order, joined in the line's own shape. A kind
    holding no fact stands as honestly unknown.
    The line is derived at call time - it is
    never stored anywhere.
    """
    return " | ".join(_segments_for(_held_facts(source)))


# ---------------------------------------------------------------------
# The fact: one of the six facts, held whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class StatusFact:
    """One status fact: one of the six facts, held whole.

    ``kind`` is the fact's kind in the closed kind
    set; ``title`` is the fact's own name in plain
    words; ``value`` is the fact's standing in
    plain words, or the honest word ``unknown``
    when the fact is not measured; ``detail`` is
    the fact's own words; ``panel`` is the one
    panel the fact opens and ``keypress`` the one
    keypress that opens it - both the kind's own,
    named as data, never bound or opened here. The
    fact carries NO line and NO segment - those
    are derived from the facts at call time, never
    fields. The provenance - the day it was
    recorded, who recorded it, its source and the
    session it was recorded in - rides whole.
    """

    fact_id: str
    kind: str
    title: str
    value: str
    detail: str
    panel: str
    keypress: str
    recorded_on: str
    actor: str
    source: str
    origin_session: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "fact_id",
            _check_word(self.fact_id, "a fact id"))
        object.__setattr__(self, "kind", normalize_kind(self.kind))
        object.__setattr__(
            self, "title", _check_title(self.title, "a fact title"))
        object.__setattr__(
            self, "value", _check_title(self.value, "a fact value"))
        object.__setattr__(
            self, "detail",
            _check_long_text(self.detail, "the fact's words"))
        object.__setattr__(
            self, "panel", _check_panel(self.kind, self.panel))
        object.__setattr__(
            self, "keypress", _check_keypress(self.kind, self.keypress))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))
        object.__setattr__(
            self, "actor", _check_title(self.actor, "an actor"))
        object.__setattr__(
            self, "source", _check_title(self.source, "a source"))
        object.__setattr__(
            self, "origin_session",
            _check_word(self.origin_session, "an origin session"))

    @property
    def segment(self) -> str:
        """The derived segment of this fact in the line."""
        return segment_of(self)

    @property
    def measured(self) -> bool:
        """True when this fact carries a measured value."""
        return is_measured(self)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "status_line_fact",
            "slice": STATUS_LINE_SLICE,
            "fact_id": self.fact_id,
            "kind": self.kind,
            "title": self.title,
            "value": self.value,
            "detail": self.detail,
            "panel": self.panel,
            "keypress": self.keypress,
            "segment": self.segment,
            "measured": self.measured,
            "recorded_on": self.recorded_on,
            "actor": self.actor,
            "source": self.source,
            "origin_session": self.origin_session,
        }


def _check_fact_ref(value: Any) -> StatusFact:
    if isinstance(value, StatusFact):
        return value
    return validate_fact(value)


def validate_fact(fact: Any) -> StatusFact:
    """Judge one status fact whole and return it.

    A mapping is read through its spellings: a
    derived key (``line``, ``segment`` or
    ``status_line``) refuses - those are derived,
    never stored - as does any key the fact does
    not carry, and two spellings naming two
    different values.
    """
    if isinstance(fact, StatusFact):
        return fact
    if not isinstance(fact, dict):
        raise ValueError(
            f"a status fact must be a mapping, got {fact!r}")
    derived = set(fact) & _DERIVED_FACT_KEYS
    if derived:
        raise ValueError(
            f"a status fact carries no derived keys: "
            f"{sorted(derived)} - the segment and the "
            f"status line are derived from the facts, "
            f"never stored on one")
    unknown = set(fact) - _FACT_KEYS
    if unknown:
        raise ValueError(
            f"a status fact carries unknown keys: "
            f"{sorted(unknown)}")
    if "type" in fact:
        raise ValueError(
            "a status fact is judged without its news keys")

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(fact, spellings, what)
        if value is None:
            raise ValueError(f"a status fact names no {what}")
        return value

    return StatusFact(
        fact_id=_needed(("fact_id", "id"), "fact id"),
        kind=_needed(("kind", "type_of"), "kind"),
        title=_needed(("title", "name", "label"), "title"),
        value=_needed(("value", "reading"), "value"),
        detail=_needed(
            ("detail", "note", "description"), "the fact's words"),
        panel=_needed(("panel", "panel_name", "opens"), "panel"),
        keypress=_needed(
            ("keypress", "key", "key_press"), "keypress"),
        recorded_on=_needed(
            ("recorded_on", "day", "date"), "day it was recorded"),
        actor=_needed(("actor", "by", "who"), "actor"),
        source=_needed(("source",), "source"),
        origin_session=_needed(
            ("origin_session", "session"), "origin session"),
    )


def build_fact(fact: Any = None, **kwargs: Any) -> StatusFact:
    """Build one fact from a mapping, a fact, or fields."""
    if kwargs:
        if fact is not None:
            raise ValueError("a fact is built one way at a time")
        fact = kwargs
    return validate_fact(fact)


# ---------------------------------------------------------------------
# Composition: facts raised from their own readings, honestly.
# ---------------------------------------------------------------------


def fact_from_measured_value(
        kind: Any, value: Any, *,
        fact_id: Any, detail: Any,
        title: Any = None,
        recorded_on: Any = "2026-11-09",
        actor: Any = "the coordinator",
        source: Any = "status line",
        origin_session: Any = "session-m178") -> StatusFact:
    """Raise one measured fact over a measured value.

    The value is the caller's own measured
    standing, held whole in plain words - this
    layer measures nothing itself, so a caller
    with no measurement names none here: the
    honest word ``unknown`` refuses on this road,
    because an unmeasured fact is raised by
    :func:`unknown_fact`, never dressed as
    measured. The fact's panel and keypress are
    its kind's own.
    """
    held_kind = normalize_kind(kind)
    held_value = _check_title(value, "a fact value")
    if held_value.lower() == UNKNOWN_VALUE:
        raise ValueError(
            "an unmeasured fact is not raised as measured - "
            "raise it by the unknown-fact road, honestly")
    return StatusFact(
        fact_id=fact_id, kind=held_kind,
        title=title if title is not None else KIND_TITLES[held_kind],
        value=held_value, detail=detail,
        panel=PANEL_FOR_KIND[held_kind],
        keypress=KEYPRESS_FOR_KIND[held_kind],
        recorded_on=recorded_on, actor=actor,
        source=source, origin_session=origin_session)


def unknown_fact(
        kind: Any, *,
        fact_id: Any,
        detail: Any = None,
        title: Any = None,
        recorded_on: Any = "2026-11-09",
        actor: Any = "the coordinator",
        source: Any = "status line",
        origin_session: Any = "session-m178") -> StatusFact:
    """Raise one honestly unknown fact over no measurement.

    The fact stands in the line with the value
    ``unknown``: this layer invents no live value
    it cannot measure, and an unmeasured kind is
    named unknown in plain words, never filled in.
    """
    held_kind = normalize_kind(kind)
    return StatusFact(
        fact_id=fact_id, kind=held_kind,
        title=title if title is not None else KIND_TITLES[held_kind],
        value=UNKNOWN_VALUE,
        detail=detail if detail is not None else (
            f"No {held_kind} reading stands held - the "
            f"fact is honestly unknown, not invented."),
        panel=PANEL_FOR_KIND[held_kind],
        keypress=KEYPRESS_FOR_KIND[held_kind],
        recorded_on=recorded_on, actor=actor,
        source=source, origin_session=origin_session)


def inspect_fact_source(piece: Any) -> Dict[str, Any]:
    """Judge one raw fact piece and name what it is.

    A piece shaped like a fact - a mapping carrying
    a ``kind`` and a ``value`` - is read onto its
    closed kind without holding a fact. Anything
    else is named not-a-fact.
    """
    if not isinstance(piece, dict):
        return {"kind": None,
                "reason": "not a mapping - no fact stands here"}
    kind_in = _pick_any(piece, ("kind", "type_of"), "kind")
    value = _pick_any(piece, ("value", "reading"), "value")
    if kind_in is None or value is None:
        return {"kind": None,
                "reason": "no kind or no value named - no fact "
                          "stands here"}
    try:
        kind = normalize_kind(kind_in)
    except ValueError as exc:
        return {"kind": None, "value": value, "reason": str(exc)}
    return {
        "kind": kind, "value": value,
        "reason": "a fact piece in the closed kind set"}


# ---------------------------------------------------------------------
# The view record: the one kind a panel looks at, held whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class StatusView:
    """One view, held as its own record.

    ``kind_filter`` is the one kind the view looks
    at, or ``all`` for every kind at once - it
    narrows which facts stand in the view's panel,
    never how they are judged; ``detail`` is the
    view's own words. ``seq`` is the view's place
    in the book's recorded order, from 1. The
    provenance rides whole. A view carries no
    results of its own: its panel and the book's
    verdict under it are derived.
    """

    seq: int
    kind_filter: str
    detail: str
    recorded_on: str
    actor: str
    source: str
    origin_session: str
    view_id: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "kind_filter",
            normalize_kind_filter(self.kind_filter))
        object.__setattr__(
            self, "detail",
            _check_long_text(self.detail, "the view's words"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))
        object.__setattr__(
            self, "actor", _check_title(self.actor, "an actor"))
        object.__setattr__(
            self, "source", _check_title(self.source, "a source"))
        object.__setattr__(
            self, "origin_session",
            _check_word(self.origin_session, "an origin session"))
        if self.view_id is not None:
            object.__setattr__(
                self, "view_id",
                _check_word(self.view_id, "a view id"))

    def shows(self, fact: Any) -> bool:
        """True when this view shows the fact."""
        current = _check_fact_ref(fact)
        return (self.kind_filter == "all"
                or current.kind == self.kind_filter)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "status_line_view",
            "slice": STATUS_LINE_SLICE,
            "view_id": self.view_id,
            "seq": self.seq,
            "kind_filter": self.kind_filter,
            "detail": self.detail,
            "recorded_on": self.recorded_on,
            "actor": self.actor,
            "source": self.source,
            "origin_session": self.origin_session,
        }


def _check_view_ref(value: Any) -> StatusView:
    if isinstance(value, StatusView):
        return value
    return validate_view(value)


def validate_view(view: Any) -> StatusView:
    """Judge one view record whole and return it."""
    if isinstance(view, StatusView):
        return view
    if not isinstance(view, dict):
        raise ValueError(
            f"a view record must be a mapping, got {view!r}")
    unknown = set(view) - _VIEW_KEYS
    if unknown:
        raise ValueError(
            f"a view record carries unknown keys: "
            f"{sorted(unknown)}")
    if "type" in view:
        raise ValueError(
            "a view record is judged without its news keys")

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(view, spellings, what)
        if value is None:
            raise ValueError(f"a view record names no {what}")
        return value

    return StatusView(
        view_id=_pick_any(view, ("view_id", "id"), "view id"),
        seq=_needed(("seq", "sequence", "order"), "sequence"),
        kind_filter=_needed(
            ("kind_filter", "filter", "kind"), "kind filter"),
        detail=_needed(("detail", "reason"), "the view's words"),
        recorded_on=_needed(
            ("recorded_on", "day", "date"), "day it was recorded"),
        actor=_needed(("actor", "by", "who"), "actor"),
        source=_needed(("source",), "source"),
        origin_session=_needed(
            ("origin_session", "session"), "origin session"),
    )


def build_view(view: Any = None, **kwargs: Any) -> StatusView:
    """Build one view record from a mapping, a record, or fields."""
    if kwargs:
        if view is not None:
            raise ValueError("a view record is built one way at a time")
        view = kwargs
    return validate_view(view)


def shown_facts(facts: Any, view: Any) -> Tuple[StatusFact, ...]:
    """The facts one view shows, in the roadmap's kind order."""
    held_view = _check_view_ref(view)
    shown = [
        current for current in (
            _check_fact_ref(fact) for fact in facts)
        if held_view.shows(current)]
    shown.sort(key=lambda fact: FACT_KINDS.index(fact.kind))
    return tuple(shown)


# ---------------------------------------------------------------------
# The panel row: one shown fact as the panel carries it.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class StatusPanelRow:
    """One shown fact as the panel carries it.

    The row carries the fact's id, its kind, its
    title, its DERIVED segment, the panel and
    keypress it opens and its recorded day. The
    fact's detail never stands in a row - the
    panel is the line at a glance.
    """

    fact_id: str
    kind: str
    title: str
    segment: str
    panel: str
    keypress: str
    recorded_on: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "fact_id",
            _check_word(self.fact_id, "a fact id"))
        object.__setattr__(self, "kind", normalize_kind(self.kind))
        object.__setattr__(
            self, "title", _check_title(self.title, "a fact title"))
        object.__setattr__(
            self, "segment",
            _check_long_text(self.segment, "a fact segment"))
        object.__setattr__(
            self, "panel", _check_panel(self.kind, self.panel))
        object.__setattr__(
            self, "keypress", _check_keypress(self.kind, self.keypress))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))

    @property
    def measured(self) -> bool:
        """True when this row's segment carries a measured value."""
        return self.segment != f"{self.title}: {UNKNOWN_VALUE}"

    def to_record(self) -> Dict[str, Any]:
        return {
            "fact_id": self.fact_id,
            "kind": self.kind,
            "title": self.title,
            "segment": self.segment,
            "panel": self.panel,
            "keypress": self.keypress,
            "recorded_on": self.recorded_on,
        }


def _row_for_fact(fact: StatusFact) -> StatusPanelRow:
    return StatusPanelRow(
        fact_id=fact.fact_id, kind=fact.kind,
        title=fact.title, segment=segment_of(fact),
        panel=fact.panel, keypress=fact.keypress,
        recorded_on=fact.recorded_on)


def _check_row_ref(value: Any) -> StatusPanelRow:
    if isinstance(value, StatusPanelRow):
        return value
    return validate_row(value)


def validate_row(row: Any, fact: Any = None) -> StatusPanelRow:
    """Judge one panel row, against its fact when named."""
    if isinstance(row, StatusPanelRow):
        current = row
    elif isinstance(row, dict):
        unknown = set(row) - _ROW_KEYS
        if unknown:
            raise ValueError(
                f"a status-line panel row carries unknown keys: "
                f"{sorted(unknown)}")

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            value = _pick_any(row, spellings, what)
            if value is None:
                raise ValueError(f"a status-line panel row names no {what}")
            return value

        current = StatusPanelRow(
            fact_id=_needed(("fact_id", "id"), "fact id"),
            kind=_needed(("kind",), "kind"),
            title=_needed(("title",), "title"),
            segment=_needed(("segment",), "segment"),
            panel=_needed(("panel",), "panel"),
            keypress=_needed(("keypress",), "keypress"),
            recorded_on=_needed(("recorded_on",), "day it was recorded"))
    else:
        raise ValueError(
            f"a status-line panel row must be a mapping, got {row!r}")
    if fact is not None:
        held = _check_fact_ref(fact)
        wanted = _row_for_fact(held)
        if current != wanted:
            raise ValueError(
                "a status-line panel row must be its fact's own "
                "row - the segment is derived from the fact, "
                "never written beside it")
    return current


def build_row(row: Any = None, fact: Any = None,
              **kwargs: Any) -> StatusPanelRow:
    """Build one panel row from a mapping, a row, or its fact."""
    if fact is not None:
        if row is not None or kwargs:
            return validate_row(
                row if row is not None else kwargs, fact)
        return _row_for_fact(_check_fact_ref(fact))
    if kwargs:
        if row is not None:
            raise ValueError("a row is built one way at a time")
        row = kwargs
    return validate_row(row)


@dataclass(frozen=True)
class StatusKindCount:
    """How many shown facts of one kind a panel holds."""

    kind: str
    facts: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", normalize_kind(self.kind))
        object.__setattr__(
            self, "facts", _check_count(self.facts, "a kind's facts"))

    def to_record(self) -> Dict[str, Any]:
        return {"kind": self.kind, "facts": self.facts}


def _check_kind_count_ref(value: Any) -> StatusKindCount:
    if isinstance(value, StatusKindCount):
        return value
    if isinstance(value, dict):
        unknown = set(value) - _KIND_COUNT_KEYS
        if unknown:
            raise ValueError(
                f"a kind count carries unknown keys: "
                f"{sorted(unknown)}")
        kind = _pick_any(value, ("kind",), "kind")
        facts = _pick_any(value, ("facts", "count"), "facts")
        if kind is None or facts is None:
            raise ValueError("a kind count names its kind and its facts")
        return StatusKindCount(kind=kind, facts=facts)
    raise ValueError(f"a kind count must be a mapping, got {value!r}")


def _kind_counts(
        rows: Tuple[StatusPanelRow, ...]) -> Tuple[StatusKindCount, ...]:
    counts: Dict[str, int] = {}
    for row in rows:
        counts[row.kind] = counts.get(row.kind, 0) + 1
    return tuple(
        StatusKindCount(kind=kind, facts=counts[kind])
        for kind in FACT_KINDS if kind in counts)


def _panel_account(total_facts: int, total_shown: int,
                   kind_counts: Tuple[StatusKindCount, ...],
                   kind_filter: str,
                   as_of: str,
                   measured_shown: int) -> Tuple[str, ...]:
    kinds = ", ".join(
        f"{count.kind} {count.facts}" for count in kind_counts) or "none"
    return (
        f"The status line holds {total_facts} facts as of "
        f"{as_of}: the view {kind_filter!r} shows "
        f"{total_shown} of them: {kinds}; {measured_shown} "
        f"of the shown facts stand measured.",
        "Rows stand in the roadmap's kind order, the order "
        "the line itself stands in, so two panels of one "
        "view diff cleanly, segment by segment.",
        "Every segment and the status line itself are "
        "derived from the facts' own titles and values - "
        "no segment is stored on any fact, and no order "
        "is chosen by hand.",
        "The status line is gathered as data only: it "
        "measures nothing live, binds no key, opens no "
        "panel and rebuilds no live screen - an "
        "unmeasured fact stands honestly unknown.",
    )


@dataclass(frozen=True)
class StatusPanel:
    """The derived panel of one book under one view.

    Rows stand in the roadmap's kind order - the
    order the line itself stands in; the totals
    are the rows' own counts and the kind counts
    stand in the roadmap's kind order. A stored
    panel is judged whole in ``__post_init__``:
    its totals, its kind counts and its account
    must all be the rows' own derived shape - a
    panel may not soften its view.
    """

    panel_id: Optional[str]
    view_id: Optional[str]
    kind_filter: str
    rows: Tuple[StatusPanelRow, ...]
    total_facts: int
    total_shown: int
    kind_counts: Tuple[StatusKindCount, ...]
    as_of: str
    account: Tuple[str, ...]

    def __post_init__(self) -> None:
        if self.panel_id is not None:
            object.__setattr__(
                self, "panel_id",
                _check_word(self.panel_id, "a panel id"))
        if self.view_id is not None:
            object.__setattr__(
                self, "view_id",
                _check_word(self.view_id, "a view id"))
        object.__setattr__(
            self, "kind_filter",
            normalize_kind_filter(self.kind_filter))
        rows = tuple(_check_row_ref(r) for r in self.rows)
        object.__setattr__(self, "rows", rows)
        ids = [r.fact_id for r in rows]
        if len(set(ids)) != len(ids):
            raise ValueError("panel rows stand one row per fact")
        kinds = [r.kind for r in rows]
        if kinds != sorted(kinds, key=FACT_KINDS.index):
            raise ValueError(
                "panel rows stand in the roadmap's kind order")
        for row in rows:
            if self.kind_filter != "all" and (
                    row.kind != self.kind_filter):
                raise ValueError(
                    "a panel row stands outside its view's "
                    "kind - the view narrows the panel, "
                    "never widens it")
        for field in ("total_facts", "total_shown"):
            object.__setattr__(
                self, field,
                _check_count(getattr(self, field), f"a panel's {field}"))
        counts = tuple(
            _check_kind_count_ref(c) for c in self.kind_counts)
        object.__setattr__(self, "kind_counts", counts)
        object.__setattr__(self, "as_of", _check_day(self.as_of, "an as-of day"))
        object.__setattr__(self, "account", _check_account(self.account))
        if self.total_shown != len(rows):
            raise ValueError("a panel's shown total is its rows' own count")
        if self.total_facts < self.total_shown:
            raise ValueError(
                "a panel's fact total cannot stand below "
                "its shown total")
        if counts != _kind_counts(rows):
            raise ValueError("a panel's kind counts are its rows' own counts")
        if rows and self.as_of < max(r.recorded_on for r in rows):
            raise ValueError(
                "a panel's as-of day precedes one of its rows")
        measured = sum(1 for r in rows if r.measured)
        if self.account != _panel_account(
                self.total_facts, self.total_shown, counts,
                self.kind_filter, self.as_of, measured):
            raise ValueError(
                "a panel's account is its rows' own account, "
                "derived, never written loose")

    def row_for(self, fact_id: Any) -> StatusPanelRow:
        """The row one fact id names (KeyError if absent)."""
        wanted = _check_word(fact_id, "a fact id")
        for row in self.rows:
            if row.fact_id == wanted:
                return row
        raise KeyError(f"no row named {wanted!r} stands on the panel")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "status_line_panel",
            "slice": STATUS_LINE_SLICE,
            "panel_id": self.panel_id,
            "view_id": self.view_id,
            "kind_filter": self.kind_filter,
            "rows": [r.to_record() for r in self.rows],
            "total_facts": self.total_facts,
            "total_shown": self.total_shown,
            "kind_counts": [c.to_record() for c in self.kind_counts],
            "as_of": self.as_of,
            "account": list(self.account),
        }


def _held_facts(source: Any) -> Tuple[StatusFact, ...]:
    if isinstance(source, StatusLineBook):
        return source.facts
    if isinstance(source, StatusLineRegistry):
        return source.list_facts()
    if isinstance(source, StatusFact):
        return (source,)
    raise ValueError(f"a status-line source is needed, got {source!r}")


def _held_views(source: Any) -> Tuple[StatusView, ...]:
    if isinstance(source, StatusLineBook):
        return source.views
    if isinstance(source, StatusLineRegistry):
        return source.list_views()
    return ()


def _resolve_view(source: Any, view: Any) -> StatusView:
    if view is None:
        raise ValueError(
            "a panel or verdict is derived under a named view")
    if isinstance(view, str):
        wanted = _check_word(view, "a view id")
        for held in _held_views(source):
            if held.view_id == wanted:
                return held
        raise ValueError(
            f"no view named {wanted!r} stands in the source")
    return _check_view_ref(view)


def _default_view(source: Any) -> StatusView:
    """The view a book's own panel stands under, or its first."""
    if isinstance(source, (StatusLineBook, StatusLineRegistry)):
        book = source if isinstance(source, StatusLineBook) else source.book()
        for panel in book.panels:
            if panel.view_id is not None:
                for held in book.views:
                    if held.view_id == panel.view_id:
                        return held
        if book.views:
            return book.views[0]
    raise ValueError("no view stands in the source to derive under")


def derive_panel(source: Any, view: Any = None) -> StatusPanel:
    """Derive the panel of a book under one view."""
    held_view = _resolve_view(source, view)
    facts = _held_facts(source)
    shown = shown_facts(facts, held_view)
    rows = tuple(_row_for_fact(fact) for fact in shown)
    counts = _kind_counts(rows)
    as_of = max((f.recorded_on for f in facts), default=_EXAMPLE_AS_OF)
    measured = sum(1 for r in rows if r.measured)
    return StatusPanel(
        panel_id=None, view_id=held_view.view_id,
        kind_filter=held_view.kind_filter,
        rows=rows, total_facts=len(facts),
        total_shown=len(rows), kind_counts=counts, as_of=as_of,
        account=_panel_account(
            len(facts), len(rows), counts,
            held_view.kind_filter, as_of, measured))


def validate_panel(panel: Any, source: Any = None) -> StatusPanel:
    """Judge one panel whole, against its source when named."""
    if isinstance(panel, StatusPanel):
        current = panel
    elif isinstance(panel, dict):
        data = dict(panel)
        data.pop("type", None)
        data.pop("slice", None)
        unknown = set(data) - _PANEL_KEYS
        if unknown:
            raise ValueError(
                f"a status-line panel carries unknown keys: "
                f"{sorted(unknown)}")

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            value = _pick_any(data, spellings, what)
            if value is None:
                raise ValueError(f"a status-line panel names no {what}")
            return value

        rows_in = _needed(("rows", "shown"), "rows")
        counts_in = _needed(("kind_counts", "kinds"), "kind counts")
        current = StatusPanel(
            panel_id=_pick_any(data, ("panel_id", "id"), "panel id"),
            view_id=_pick_any(data, ("view_id", "view"), "view id"),
            kind_filter=_needed(
                ("kind_filter", "filter", "kind"), "kind filter"),
            rows=tuple(validate_row(r) for r in rows_in),
            total_facts=_needed(
                ("total_facts", "facts"), "fact total"),
            total_shown=_needed(("total_shown", "matched"), "shown total"),
            kind_counts=tuple(
                _check_kind_count_ref(c) for c in counts_in),
            as_of=_needed(("as_of", "day"), "as-of day"),
            account=tuple(_needed(("account", "statements"), "account")))
    else:
        raise ValueError(f"a status-line panel must be a mapping, got {panel!r}")
    if source is not None:
        held_view = _resolve_view(source, current.view_id)
        derived = derive_panel(source, held_view)
        if (current.view_id != derived.view_id
                or current.kind_filter != derived.kind_filter
                or current.rows != derived.rows
                or current.total_facts != derived.total_facts
                or current.total_shown != derived.total_shown
                or current.kind_counts != derived.kind_counts
                or current.as_of != derived.as_of
                or current.account != derived.account):
            raise ValueError(
                "a stored panel must equal the panel its book "
                "derives under its view - the panel is "
                "derived, never stored loose")
    return current


def build_panel(panel: Any = None, source: Any = None,
                view: Any = None, **kwargs: Any) -> StatusPanel:
    """Build one panel from a mapping, a panel, or its source."""
    if kwargs:
        if panel is not None:
            raise ValueError("a panel is built one way at a time")
        panel = kwargs
    if panel is None and source is not None:
        return derive_panel(source, view)
    return validate_panel(panel, source)


# ---------------------------------------------------------------------
# The verdict: the whole book under one view, in one word.
# ---------------------------------------------------------------------


def _verdict_word(total_shown: int, measured_shown: int,
                  distinct_kinds: int) -> str:
    if measured_shown == 0:
        return "empty"
    if total_shown == len(FACT_KINDS) and (
            measured_shown == len(FACT_KINDS)) and (
            distinct_kinds == len(FACT_KINDS)):
        return "complete"
    return "partial"


@dataclass(frozen=True)
class StatusVerdict:
    """The derived verdict of one whole book under one view.

    The word is read off the shown facts alone:
    empty while no shown fact stands measured,
    complete while the shown facts are all six
    kinds and every one stands measured, partial
    otherwise. A stored verdict is judged against
    those tallies in ``__post_init__``.
    """

    total_facts: int
    total_shown: int
    measured_shown: int
    distinct_kinds: int
    earliest_on: str
    latest_on: str
    verdict: str

    def __post_init__(self) -> None:
        for field in ("total_facts", "total_shown",
                      "measured_shown", "distinct_kinds"):
            object.__setattr__(
                self, field,
                _check_count(getattr(self, field), f"a verdict's {field}"))
        object.__setattr__(
            self, "earliest_on", _check_day(self.earliest_on, "an earliest day"))
        object.__setattr__(
            self, "latest_on", _check_day(self.latest_on, "a latest day"))
        if self.latest_on < self.earliest_on:
            raise ValueError("a verdict's latest day precedes its earliest")
        if self.total_shown > self.total_facts:
            raise ValueError(
                "a verdict's shown tally cannot exceed its "
                "fact total")
        if self.measured_shown > self.total_shown:
            raise ValueError(
                "a verdict's measured tally cannot exceed "
                "its shown tally")
        if self.total_shown == 0 and (
                self.distinct_kinds != 0 or self.measured_shown != 0):
            raise ValueError(
                "an empty showing names no kind and no "
                "measured fact among its shown")
        if self.distinct_kinds > self.total_shown:
            raise ValueError(
                "a verdict's kinds cannot exceed its shown facts")
        word = _clean_text(self.verdict, "a verdict")
        if word not in VERDICT_WORDS:
            raise ValueError(
                f"a verdict is one of {VERDICT_WORDS}, got {word!r}")
        object.__setattr__(self, "verdict", word)
        if word != _verdict_word(
                self.total_shown, self.measured_shown,
                self.distinct_kinds):
            raise ValueError(
                "a verdict's word is derived from its tallies, "
                "never chosen")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "status_line_verdict",
            "slice": STATUS_LINE_SLICE,
            "total_facts": self.total_facts,
            "total_shown": self.total_shown,
            "measured_shown": self.measured_shown,
            "distinct_kinds": self.distinct_kinds,
            "earliest_on": self.earliest_on,
            "latest_on": self.latest_on,
            "verdict": self.verdict,
        }


def derive_verdict(source: Any, view: Any = None) -> StatusVerdict:
    """Derive the verdict of a book under one view."""
    held_view = _resolve_view(source, view)
    facts = _held_facts(source)
    shown = shown_facts(facts, held_view)
    measured = sum(1 for fact in shown if is_measured(fact))
    distinct = len({fact.kind for fact in shown})
    days = [fact.recorded_on for fact in facts]
    return StatusVerdict(
        total_facts=len(facts), total_shown=len(shown),
        measured_shown=measured, distinct_kinds=distinct,
        earliest_on=min(days) if days else _EXAMPLE_AS_OF,
        latest_on=max(days) if days else _EXAMPLE_AS_OF,
        verdict=_verdict_word(len(shown), measured, distinct))


def _check_verdict_ref(value: Any) -> StatusVerdict:
    if isinstance(value, StatusVerdict):
        return value
    return validate_verdict(value)


def validate_verdict(verdict: Any, source: Any = None,
                     view: Any = None) -> StatusVerdict:
    """Judge one verdict whole, against its source when named."""
    if isinstance(verdict, StatusVerdict):
        current = verdict
    elif isinstance(verdict, dict):
        data = dict(verdict)
        data.pop("type", None)
        data.pop("slice", None)
        unknown = set(data) - _VERDICT_KEYS
        if unknown:
            raise ValueError(
                f"a status-line verdict carries unknown keys: "
                f"{sorted(unknown)}")

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            value = _pick_any(data, spellings, what)
            if value is None:
                raise ValueError(f"a status-line verdict names no {what}")
            return value

        current = StatusVerdict(
            total_facts=_needed(
                ("total_facts", "facts"), "fact total"),
            total_shown=_needed(("total_shown", "matched"), "shown total"),
            measured_shown=_needed(
                ("measured_shown", "measured"), "measured total"),
            distinct_kinds=_needed(
                ("distinct_kinds", "kinds"), "distinct kinds"),
            earliest_on=_needed(("earliest_on", "earliest"), "earliest day"),
            latest_on=_needed(("latest_on", "latest"), "latest day"),
            verdict=_needed(("verdict",), "verdict"))
    else:
        raise ValueError(f"a status-line verdict must be a mapping, got {verdict!r}")
    if source is not None:
        derived = derive_verdict(source, view)
        if current != derived:
            raise ValueError(
                "a stored verdict must equal the verdict its "
                "book derives under its view - the verdict "
                "is derived, never stored loose")
    return current


def build_verdict(verdict: Any = None, source: Any = None,
                  view: Any = None, **kwargs: Any) -> StatusVerdict:
    """Build one verdict from a mapping, a verdict, or its source."""
    if kwargs:
        if verdict is not None:
            raise ValueError("a verdict is built one way at a time")
        verdict = kwargs
    if verdict is None and source is not None:
        return derive_verdict(source, view)
    return validate_verdict(verdict, source, view)


# ---------------------------------------------------------------------
# The book: one set of facts and views, held whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class StatusLineBook:
    """One set of status facts and views, held whole.

    Facts stand in held order - one fact per fact
    id and one fact per kind, since the line holds
    six facts at most - views stand in recorded
    order, one view per sequence and per id, and
    every stored panel is judged against the book
    and the view it stands under. The book carries
    no status line: the line is derived from its
    facts at call time.
    """

    title: str
    facts: Tuple[StatusFact, ...] = ()
    views: Tuple[StatusView, ...] = ()
    panels: Tuple[StatusPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book title"))
        facts = tuple(_check_fact_ref(f) for f in self.facts)
        object.__setattr__(self, "facts", facts)
        ids = [f.fact_id for f in facts]
        if len(set(ids)) != len(ids):
            raise ValueError("a book holds one fact per fact id")
        kinds = [f.kind for f in facts]
        if len(set(kinds)) != len(kinds):
            raise ValueError(
                "a book holds one fact per kind - the line "
                "holds six facts, one of each kind")
        views = tuple(_check_view_ref(v) for v in self.views)
        object.__setattr__(self, "views", views)
        seqs = [v.seq for v in views]
        if seqs != sorted(seqs) or len(set(seqs)) != len(seqs):
            raise ValueError(
                "a book's views stand in recorded order, "
                "one view per sequence")
        view_ids = [
            v.view_id for v in views if v.view_id is not None]
        if len(set(view_ids)) != len(view_ids):
            raise ValueError("a book holds one view per view id")
        panels = tuple(validate_panel(p, self) for p in self.panels)
        object.__setattr__(self, "panels", panels)

    def fact_for(self, fact_id: Any) -> StatusFact:
        """The fact one id names (KeyError if absent)."""
        wanted = _check_word(fact_id, "a fact id")
        for fact in self.facts:
            if fact.fact_id == wanted:
                return fact
        raise KeyError(f"no fact named {wanted!r} stands in the book")

    def view_for(self, view_id: Any) -> StatusView:
        """The view one id names (KeyError if absent)."""
        wanted = _check_word(view_id, "a view id")
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no view named {wanted!r} stands in the book")

    def panel_for(self, panel_id: Any) -> StatusPanel:
        """The panel one id names (KeyError if absent)."""
        wanted = _check_word(panel_id, "a panel id")
        for panel in self.panels:
            if panel.panel_id == wanted:
                return panel
        raise KeyError(f"no panel named {wanted!r} stands in the book")

    def fact_ids(self) -> Tuple[str, ...]:
        """The book's fact ids, in held order."""
        return tuple(f.fact_id for f in self.facts)

    def view_ids(self) -> Tuple[Optional[str], ...]:
        """The book's view ids, in recorded order."""
        return tuple(v.view_id for v in self.views)

    @property
    def line(self) -> str:
        """The status line this book derives."""
        return line_of(self)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "status_line_book",
            "slice": STATUS_LINE_SLICE,
            "title": self.title,
            "facts": [f.to_record() for f in self.facts],
            "views": [v.to_record() for v in self.views],
            "panels": [p.to_record() for p in self.panels],
            "line": self.line,
            "fact_count": len(self.facts),
            "view_count": len(self.views),
        }


def _judge_book_panels(book: StatusLineBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def validate_book(data: Any, *, require_example: bool = False) -> StatusLineBook:
    """Judge one status-line file's data whole and return its book."""
    if isinstance(data, StatusLineBook):
        book = data
        _judge_book_panels(book)
        if require_example:
            _check_example(book)
        return book
    if not isinstance(data, dict):
        raise ValueError(f"a status-line book must be a mapping, got {data!r}")
    if "line" in data or "status_line" in data:
        raise ValueError(
            "a status-line book carries no stored line - "
            "the line is derived from its facts, never stored")
    unknown = set(data) - _STATUS_LINE_KEYS
    if unknown:
        raise ValueError(
            f"a status-line book carries unknown keys: {sorted(unknown)}")
    if data.get("schema") != STATUS_LINE_SCHEMA:
        raise ValueError(
            f"a status-line book's schema must be "
            f"{STATUS_LINE_SCHEMA!r}, got {data.get('schema')!r}")
    if data.get("slice") != STATUS_LINE_SLICE:
        raise ValueError(
            f"a status-line book's slice must be "
            f"{STATUS_LINE_SLICE!r}, got {data.get('slice')!r}")
    guide = data.get("guide") or {}
    title = _pick_any(guide, ("title", "name"), "title")
    if title is None:
        title = _pick_any(data, ("title", "name"), "title")
    facts_in = _pick_any(data, ("facts",), "facts")
    if facts_in is None:
        raise ValueError("a status-line book names no facts")
    views_in = data.get("views") or []
    panels_in = data.get("panels") or []
    facts = []
    for raw in facts_in:
        stored = dict(raw)
        stored.pop("type", None)
        stored.pop("slice", None)
        stored.pop("segment", None)
        stored.pop("measured", None)
        facts.append(validate_fact(stored))
    views = []
    for raw in views_in:
        stored = dict(raw)
        stored.pop("type", None)
        stored.pop("slice", None)
        views.append(validate_view(stored))
    book = StatusLineBook(
        title=title,
        facts=tuple(facts),
        views=tuple(views),
        panels=tuple(validate_panel(p) for p in panels_in))
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def _check_example(book: StatusLineBook) -> None:
    if book.title != _EXAMPLE_TITLE:
        raise ValueError(
            f"the shipped example book is {_EXAMPLE_TITLE!r}, "
            f"got {book.title!r}")
    if book.fact_ids() != _EXAMPLE_FACT_IDS:
        raise ValueError("the shipped example book's facts differ")
    first = book.facts[0]
    if first.fact_id != _EXAMPLE_FIRST_FACT_ID or (
            first.kind != _EXAMPLE_FIRST_FACT_KIND):
        raise ValueError("the shipped example book's first fact differs")
    if book.view_ids() != _EXAMPLE_VIEW_IDS:
        raise ValueError("the shipped example book's views differ")
    if len(book.panels) != 1 or (
            book.panels[0].panel_id != _EXAMPLE_PANEL_ID):
        raise ValueError("the shipped example book's panel differs")
    if book.panels[0].as_of != _EXAMPLE_AS_OF:
        raise ValueError("the shipped example book's as-of day differs")
    derived = derive_panel(book, book.panels[0].view_id)
    if tuple(r.fact_id for r in book.panels[0].rows) != tuple(
            r.fact_id for r in derived.rows):
        raise ValueError("the shipped example book's panel rows differ")


def build_book(book: Any = None, **kwargs: Any) -> StatusLineBook:
    """Build one book from a mapping, a book, or fields."""
    if isinstance(book, StatusLineBook) and not kwargs:
        return validate_book(book)
    if kwargs:
        if book is not None:
            raise ValueError("a book is built one way at a time")
        fields = dict(kwargs)
    elif isinstance(book, dict) and (
            "facts" in book) and (
            "schema" not in book and "guide" not in book
            and "canon_note" not in book):
        fields = dict(book)
    else:
        return _book_from(book, require_example=False)
    unknown = set(fields) - _BOOK_KEYS - {
        "facts", "views", "panels"}
    if unknown:
        raise ValueError(
            f"a status-line book carries unknown keys: "
            f"{sorted(unknown)}")
    title = _pick_any(fields, ("title", "name"), "title")
    if title is None:
        raise ValueError("a status-line book names no title")
    facts_in = _pick_any(fields, ("facts",), "facts") or ()
    return StatusLineBook(
        title=title,
        facts=tuple(_check_fact_ref(f) for f in facts_in),
        views=tuple(
            _check_view_ref(v) for v in fields.get("views") or ()),
        panels=tuple(
            validate_panel(p) for p in fields.get("panels") or ()))


def _book_from(data: Any, *, require_example: bool) -> StatusLineBook:
    if isinstance(data, StatusLineBook):
        return validate_book(data, require_example=require_example)
    if isinstance(data, dict):
        return validate_book(data, require_example=require_example)
    raise ValueError(f"a status-line book must be a mapping, got {data!r}")


def load_status_line(data: Optional[Dict[str, Any]] = None) -> StatusLineBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(STATUS_LINE_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_status_line_file(path: Any) -> StatusLineBook:
    """Load one status-line file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: facts and views held one by one.
# ---------------------------------------------------------------------


class StatusLineRegistry:
    """An in-memory holding of status facts and views.

    The registry is the pure layer's model of a
    session's status line: facts are held under
    their fact ids, one fact per id and one fact
    per kind, in held order, and views are held in
    recorded order, one view per sequence and per
    id. Holding is data only - no fact held here
    is measured live, and no panel is opened.
    """

    def __init__(self, book: Any = None) -> None:
        self._facts: List[StatusFact] = []
        self._views: List[StatusView] = []
        self._title: Optional[str] = None
        if book is not None:
            self.register_book(book)

    def title(self) -> Optional[str]:
        return self._title

    def _fresh_view_id(self, held_ids: Any) -> str:
        n = 1
        while f"view-{n}" in held_ids:
            n += 1
        return f"view-{n}"

    def _check_fact_free(self, fact: StatusFact) -> None:
        for held in self._facts:
            if held.fact_id == fact.fact_id:
                raise ValueError(
                    f"a fact already stands under id "
                    f"{fact.fact_id!r}")
            if held.kind == fact.kind:
                raise ValueError(
                    f"a fact already stands under kind "
                    f"{fact.kind!r} - the line holds one "
                    f"fact per kind")

    def register_fact(self, fact: Any) -> StatusFact:
        """Hold one fact, judged whole before it is held."""
        validated = _check_fact_ref(fact)
        self._check_fact_free(validated)
        self._facts.append(validated)
        return validated

    def _check_view_free(self, view: StatusView) -> None:
        for held in self._views:
            if view.view_id is not None and (
                    held.view_id == view.view_id):
                raise ValueError(
                    f"a view already stands under id "
                    f"{view.view_id!r}")
            if held.seq == view.seq:
                raise ValueError(
                    f"a view already stands at sequence "
                    f"{view.seq} - the book holds one "
                    f"view per place")

    def register_view(self, view: Any) -> StatusView:
        """Hold one view record, judged whole first.

        A view id or a sequence already standing here
        refuses and holds nothing new. A held view
        only ever looks: standing it derives its
        panel, measures nothing and opens nothing.
        """
        validated = _check_view_ref(view)
        self._check_view_free(validated)
        if validated.view_id is None:
            validated = StatusView(
                view_id=self._fresh_view_id(
                    {v.view_id for v in self._views}),
                seq=validated.seq,
                kind_filter=validated.kind_filter,
                detail=validated.detail,
                recorded_on=validated.recorded_on,
                actor=validated.actor, source=validated.source,
                origin_session=validated.origin_session)
        self._views.append(validated)
        self._views.sort(key=lambda v: v.seq)
        return validated

    def register_book(self, book: Any) -> StatusLineBook:
        """Hold a whole book, judged whole first."""
        validated = build_book(book)
        for fact in validated.facts:
            self._check_fact_free(fact)
        if self._title is None:
            self._title = validated.title
        elif validated.title != self._title:
            raise ValueError(
                "a second book under a different title refuses - "
                "one book stands in one registry")
        for fact in validated.facts:
            self._facts.append(fact)
        for view in validated.views:
            self.register_view(view)
        return self.book()

    def get_fact(self, fact_id: Any) -> StatusFact:
        """The fact one id names (KeyError if absent)."""
        wanted = _check_word(fact_id, "a fact id")
        for fact in self._facts:
            if fact.fact_id == wanted:
                return fact
        raise KeyError(f"no fact named {wanted!r} stands held")

    def get_view(self, view_id: Any) -> StatusView:
        """The view record one id names (KeyError if absent)."""
        wanted = _check_word(view_id, "a view id")
        for view in self._views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no view named {wanted!r} stands held")

    def latest_view(self) -> StatusView:
        """The last view recorded (KeyError if none)."""
        if not self._views:
            raise KeyError("no view stands held")
        return self._views[-1]

    def list_facts(self) -> Tuple[StatusFact, ...]:
        return tuple(self._facts)

    def list_views(self) -> Tuple[StatusView, ...]:
        return tuple(self._views)

    def book(self) -> StatusLineBook:
        return StatusLineBook(
            title=self._title or "Status Line",
            facts=tuple(self._facts),
            views=tuple(self._views))

    def panel(self, view: Any = None) -> StatusPanel:
        return derive_panel(self.book(), view)

    def verdict(self, view: Any = None) -> StatusVerdict:
        return derive_verdict(self.book(), view)

    def line(self) -> str:
        return line_of(self.book())


def facts_for_kind(source: Any, kind: Any) -> Tuple[StatusFact, ...]:
    """The facts of one kind, in held order (one at most)."""
    wanted = normalize_kind(kind)
    return tuple(
        f for f in _held_facts(source) if f.kind == wanted)


def measured_facts(source: Any) -> Tuple[StatusFact, ...]:
    """The facts carrying a measured value, in held order."""
    return tuple(f for f in _held_facts(source) if is_measured(f))


def unknown_facts(source: Any) -> Tuple[StatusFact, ...]:
    """The facts standing honestly unknown, in held order."""
    return tuple(f for f in _held_facts(source) if not is_measured(f))


def total_facts(source: Any) -> int:
    """How many facts a source holds."""
    return len(_held_facts(source))


# ---------------------------------------------------------------------
# Session news, plain words, and the screens.
# ---------------------------------------------------------------------


def fact_record(fact: Any) -> Dict[str, Any]:
    """The session-news record of one status fact."""
    current = _check_fact_ref(fact)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Status line fact {current.fact_id}: "
        f"{segment_of(current)} - opens the "
        f"{current.panel} on keypress "
        f"{current.keypress}.")
    return record_out


def view_record(view: Any) -> Dict[str, Any]:
    """The session-news record of one view record."""
    current = _check_view_ref(view)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Status line view {current.view_id or current.seq}: "
        f"kind {current.kind_filter!r} - "
        f"{current.detail}")
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived panel."""
    current = validate_panel(panel, source)
    record = current.to_record()
    record["news"] = True
    kinds = ", ".join(
        f"{c.kind} {c.facts}" for c in current.kind_counts)
    record["headline"] = (
        f"Status line panel as of {current.as_of}: "
        f"{current.total_shown} of {current.total_facts} "
        f"facts show for kind {current.kind_filter!r} "
        f"({kinds}).")
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived verdict."""
    current = validate_verdict(verdict, source, view)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Status line verdict: {current.verdict} - "
        f"{current.measured_shown} of {current.total_shown} "
        f"shown facts measured across "
        f"{current.distinct_kinds} kinds, from "
        f"{current.earliest_on} to {current.latest_on}.")
    return record


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one status-line book."""
    current = book if isinstance(book, StatusLineBook) else build_book(book)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Status line {current.title}: "
        f"{record['fact_count']} facts named, "
        f"{record['view_count']} views held - "
        f"{current.line}")
    return record


def plain_words(fact: Any) -> str:
    """One fact, in one plain sentence."""
    current = _check_fact_ref(fact)
    return (
        f"{segment_of(current)} - one status fact on "
        f"fact {current.fact_id}: it opens the "
        f"{current.panel} on keypress {current.keypress}. "
        f"Holding it here measures nothing live, binds "
        f"no key and opens no panel.")


def view_plain_words(view: Any) -> str:
    """One view record, in one plain sentence."""
    current = _check_view_ref(view)
    return (
        f"View {current.view_id or current.seq} looks at "
        f"kind {current.kind_filter!r}, recorded on "
        f"{current.recorded_on} by {current.actor}: "
        f"{current.detail} A view only ever looks - it "
        f"measures nothing live and opens no panel.")


def panel_plain_words(source: Any, view: Any = None) -> str:
    """The panel in plain words, in full."""
    if isinstance(source, StatusPanel):
        panel = validate_panel(source)
        title = None
    elif isinstance(source, (StatusLineBook, StatusLineRegistry)):
        book = source if isinstance(
            source, StatusLineBook) else source.book()
        panel = derive_panel(
            book, view if view is not None
            else _default_view(book))
        title = book.title
    else:
        raise ValueError(f"a status-line source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Shown, in the roadmap's kind order:")
    for row in panel.rows:
        lines.append(
            f"{row.fact_id}: {row.segment} "
            f"(opens the {row.panel} on keypress "
            f"{row.keypress}, {row.recorded_on})")
    lines.extend(panel.account)
    return "\n".join(lines)


def verdict_plain_words(source: Any, view: Any = None) -> str:
    """The book verdict in plain words, in full."""
    if isinstance(source, StatusVerdict):
        verdict = validate_verdict(source)
    elif isinstance(source, (StatusLineBook, StatusLineRegistry)):
        book = source if isinstance(
            source, StatusLineBook) else source.book()
        verdict = derive_verdict(
            book, view if view is not None
            else _default_view(book))
    else:
        raise ValueError(f"a status-line source is needed, got {source!r}")
    return (
        f"Status line verdict: {verdict.verdict} - "
        f"{verdict.measured_shown} of {verdict.total_shown} "
        f"shown facts measured, across "
        f"{verdict.distinct_kinds} kinds, from "
        f"{verdict.earliest_on} to {verdict.latest_on} - "
        f"every segment is derived from the facts' own "
        f"titles and values.")


def _source_book(source: Any) -> StatusLineBook:
    if source is None:
        return load_status_line()
    if isinstance(source, StatusLineRegistry):
        return source.book()
    if isinstance(source, StatusLineBook):
        return source
    if isinstance(source, StatusFact):
        return StatusLineBook(title="One status fact", facts=(source,))
    raise ValueError(f"a status-line book is needed, got {source!r}")


def format_fact(fact: Any) -> str:
    """One status fact as a screen block.

    The fact's kind, title, value and detail stand
    as their own lines, the panel and keypress it
    opens stand named, and its provenance stands
    whole - a fact held here is a finding, never
    the live state of the screen it describes.
    """
    current = _check_fact_ref(fact)
    lines = [
        f"{current.fact_id}: {segment_of(current)}",
        f"Kind: {current.kind}",
        f"Title: {current.title}",
        f"Value: {current.value}",
        f"Words: {current.detail}",
        f"Opens: the {current.panel} on keypress "
        f"{current.keypress} (named as data - no live "
        f"key is bound and no live panel is opened here).",
        f"Recorded: on {current.recorded_on} by {current.actor} "
        f"from {current.source} in {current.origin_session}.",
    ]
    return "\n".join(lines)


def format_view(view: Any) -> str:
    """One view record as a screen block."""
    current = _check_view_ref(view)
    lines = [
        f"{current.view_id or '-'}: kind "
        f"{current.kind_filter!r}",
        f"Words: {current.detail}",
        f"Recorded: on {current.recorded_on} by {current.actor} "
        f"from {current.source} in {current.origin_session}.",
    ]
    return "\n".join(lines)


def format_book(source: Any = None, kind: Any = None) -> str:
    """The book as derived segments, in held order.

    By default the lines are every fact's derived
    segment. With ``kind`` only that kind's facts
    stand in the list.
    """
    book = _source_book(source)
    wanted = normalize_kind(kind) if kind is not None else None
    lines = []
    for fact in book.facts:
        if wanted is not None and fact.kind != wanted:
            continue
        lines.append(f"{fact.fact_id}: {segment_of(fact)}")
    if not lines:
        lines.append("No facts stand in the book on that reading.")
    return "\n".join(lines)


def format_line(source: Any = None) -> str:
    """The derived status line as a screen block."""
    book = _source_book(source)
    return f"Status line: {line_of(book)}"


def format_panel(source: Any = None, view: Any = None) -> str:
    """The panel as a screen block: every row and the account."""
    if isinstance(source, StatusPanel):
        panel = validate_panel(source)
        lines: list = []
    else:
        book = _source_book(source)
        panel = derive_panel(
            book, view if view is not None
            else _default_view(book))
        lines = [f"Panel in {book.title}:"]
    lines.append("Shown, in the roadmap's kind order:")
    for row in panel.rows:
        lines.append(
            f"{row.fact_id}: {row.segment} - "
            f"opens the {row.panel} on keypress "
            f"{row.keypress} ({row.recorded_on})")
    lines.extend(panel.account)
    return "\n".join(lines)


def format_verdict(source: Any = None, view: Any = None) -> str:
    """The verdict as a screen block."""
    if isinstance(source, StatusVerdict):
        verdict = validate_verdict(source)
        title = "the book"
    else:
        book = _source_book(source)
        verdict = derive_verdict(
            book, view if view is not None
            else _default_view(book))
        title = book.title
    return (
        f"Verdict in Status Line over {title}: "
        f"{verdict.verdict} - {verdict.measured_shown} of "
        f"{verdict.total_shown} shown facts measured, "
        f"across {verdict.distinct_kinds} kinds, from "
        f"{verdict.earliest_on} to {verdict.latest_on}.")


def format_status_line_screen(source: Any = None) -> str:
    """The whole status-line screen for one book."""
    book = _source_book(source)
    view = _default_view(book)
    panel = derive_panel(book, view)
    verdict = derive_verdict(book, view)
    lines = [
        f"Status Line (M-178) - {book.title}",
        format_book(book),
        f"Line: {line_of(book)}",
        f"Panel: {panel.total_shown} of "
        f"{panel.total_facts} facts show "
        f"for kind {panel.kind_filter!r}.",
        f"Verdict: {verdict.verdict}.",
        "This layer holds the status line as data only - "
        "it measures nothing live, reads no live model, "
        "context, cost, crew or sandbox state, binds no "
        "key, opens no panel and rebuilds no live screen.",
    ]
    return "\n".join(lines)


def parse_status_line_args(args: Any) -> Tuple[str, Any]:
    """Parse the /statusline grammar into (action, target).

    ``""``/``show``/``list`` show the book;
    ``fact <fact-id>`` shows one fact whole;
    ``view <view-id>`` shows one held view record;
    ``kind <kind>`` shows one kind's facts;
    ``line`` shows the derived status line;
    ``panel`` and ``verdict`` show the derived
    panel and verdict under the book's own view.
    Anything else raises ValueError carrying the
    usage line.
    """
    if args is None:
        return ("show", None)
    if not isinstance(args, str):
        raise ValueError(USAGE)
    parts = args.split()
    if not parts or parts == ["show"] or parts == ["list"]:
        return ("show", None)
    if parts[0] == "fact" and len(parts) == 2:
        return ("fact", _check_word(parts[1], "a fact id"))
    if parts[0] == "view" and len(parts) == 2:
        return ("view", _check_word(parts[1], "a view id"))
    if parts[0] == "kind" and len(parts) == 2:
        try:
            return ("kind", normalize_kind(parts[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if parts == ["line"]:
        return ("line", None)
    if parts == ["panel"]:
        return ("panel", None)
    if parts == ["verdict"]:
        return ("verdict", None)
    raise ValueError(USAGE)
