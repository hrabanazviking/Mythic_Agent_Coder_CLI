"""The plain-language skin (All-Features roadmap slice M-182).

Part VIII - The Beautiful Face - builds here. The
roadmap's words: *a "Jarl mode" register - reports,
approvals, and stand-ups in plain everyday words,
technical detail folded behind a keypress.*
(Volmarr's standing law for his own Muse, built
into his own coder.)

What already ships, and what this slice adds:

* The shipped tree already carries the surfaces
  this skin speaks over: approval cards (M-174),
  the status line of truth (M-178), stand-ups and
  the prompt surfaces. What nothing held is the
  *register* those surfaces speak in, as checkable
  data: one held report, one held approval ask and
  one held stand-up, each rendered two ways from
  the SAME held fields - plain everyday words in
  Jarl mode, the full technical words in the
  technical register - with the technical detail
  folded behind one named keypress in Jarl mode,
  never deleted and never shown by default. This
  slice is that skin, in its own module; the
  shipped surfaces stand untouched behind seams,
  and this layer renders over held data in their
  shape, never rewriting them.
* The plain rendering is DERIVED from the held
  item's own fields at call time, through a
  plain-words lexicon held as data in the book:
  a shipped term names its plain words, and the
  plain line is the technical line with each
  listed term spoken plainly. There is no second
  hand-written plain copy anywhere in this layer
  that could drift from the facts: the numbers,
  the names and the one action an approval names
  are the item's own, carried whole into both
  registers. A watched term with no lexicon entry
  is a MISS: it passes through unchanged, it is
  named in the item's misses, and it keeps the
  item from standing whole - never silently
  invented, never quietly dropped.
* The register is a named mode - ``jarl`` or
  ``technical`` - DERIVED from session or config
  state at call time by :func:`derive_register`,
  never stored on any item or message: a mapping
  naming a stored register on an item refuses.
  Jarl is the default register, as the law holds
  plain words first.
* In Jarl mode the technical lines stand FOLDED:
  a rendering carries them as folded data,
  reachable by the one named unfold action
  (:func:`unfold_rendering`, the ``unfold``
  keypress of the /skin grammar), and the folded
  lines are the item's own technical lines whole.
  In the technical register nothing stands folded.
* The shipped data file (``mythic_agent/data/
  plain_language_skin.yaml``) holds one example
  book in exactly the shape a real skin file
  takes, a loader reads a skin file anywhere on
  disk, items and views are shaped as session
  news, and a small in-memory registry holds
  items and views one by one. The agent layer
  owns holding a skin book for a session and
  rendering its items in the session's register.
  This layer reaches no live road: it renders
  words only, and approves nothing.

Honesty rules, enforced here and pinned by tests:

* **Same facts, plainer words.** The plain line
  is derived from the technical line through the
  lexicon alone; every number and name in the
  technical line stands in the plain line too.
* **Folded, never deleted.** Jarl mode folds the
  technical detail behind the unfold keypress;
  it does not drop, summarise or rewrite it.
* **An approval asks plainly and names one
  action.** An approval held whole names exactly
  one action - the single step its ask turns on;
  none, or several, refuses by name.
* **A lexicon miss is honest.** A watched term
  with no plain words stands unchanged in the
  rendering and named in the misses; this layer
  invents no plain words for it.
* **The register is derived, never stored.** No
  item and no rendering request stores a mode on
  the data; the mode is derived from the session
  or config handed to the call.
"""

from __future__ import annotations

__all__ = [
    "DEFAULT_REGISTER",
    "ITEM_KINDS",
    "JARL_IS_THE_DEFAULT_REGISTER",
    "PLAIN_EXPLANATION",
    "PLAIN_LANGUAGE_SKIN_RESOURCE",
    "PLAIN_LANGUAGE_SKIN_SCHEMA",
    "PLAIN_LANGUAGE_SKIN_SLICE",
    "REGISTERS",
    "THE_PLAIN_LANGUAGE_SKIN_SLICE",
    "UNFOLD_ACTION",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_KINDS",
    "Any",
    "Dict",
    "List",
    "Optional",
    "SkinApproval",
    "SkinBook",
    "SkinKindCount",
    "SkinPanel",
    "SkinPanelRow",
    "SkinRegistry",
    "SkinRendering",
    "SkinReport",
    "SkinStandup",
    "SkinTerm",
    "SkinVerdict",
    "SkinView",
    "Tuple",
    "approval_plain_words",
    "approval_record",
    "book_record",
    "build_approval",
    "build_book",
    "build_panel",
    "build_report",
    "build_standup",
    "build_term",
    "build_verdict",
    "build_view",
    "derive_panel",
    "derive_register",
    "derive_verdict",
    "format_approval",
    "format_book",
    "format_panel",
    "format_plain_language_skin_screen",
    "format_rendering",
    "format_report",
    "format_standup",
    "format_term",
    "format_verdict",
    "format_view",
    "inspect_item_source",
    "item_misses",
    "item_passes",
    "item_record",
    "items_for_kind",
    "lexicon_misses",
    "load_plain_language_skin",
    "load_plain_language_skin_file",
    "normalize_kind",
    "normalize_kind_filter",
    "normalize_register",
    "normalize_term",
    "panel_plain_words",
    "panel_record",
    "passing_items",
    "plain_for_term",
    "plain_lines",
    "plain_words",
    "render_item",
    "rendering_record",
    "report_plain_words",
    "report_record",
    "segment_of",
    "shown_items",
    "standup_plain_words",
    "standup_record",
    "technical_lines",
    "term_plain_words",
    "term_record",
    "total_items",
    "translate_text",
    "unfold_rendering",
    "validate_approval",
    "validate_book",
    "validate_panel",
    "validate_report",
    "validate_standup",
    "validate_term",
    "validate_verdict",
    "validate_view",
    "verdict_plain_words",
    "verdict_record",
    "view_plain_words",
    "view_record",
]

import re
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .crew_members import normalize_member_id

PLAIN_LANGUAGE_SKIN_SLICE = "M-182"

#: The longer name other layers cite for this slice.
THE_PLAIN_LANGUAGE_SKIN_SLICE = PLAIN_LANGUAGE_SKIN_SLICE

PLAIN_LANGUAGE_SKIN_RESOURCE = "plain_language_skin.yaml"

PLAIN_LANGUAGE_SKIN_SCHEMA = "mythic.plain_language_skin/1"

#: The kinds of item one skin book holds, in held
#: order: the reports the skin speaks over, the
#: approval asks, the stand-ups, and the plain-
#: words lexicon terms themselves.
ITEM_KINDS = ("report", "approval", "standup", "term")

_KIND_ALIASES = {
    "report": "report", "reports": "report",
    "approval": "approval", "approvals": "approval",
    "ask": "approval",
    "standup": "standup", "standups": "standup",
    "stand-up": "standup",
    "term": "term", "terms": "term",
    "word": "term", "lexicon": "term"}

#: The views a panel may stand under: every kind
#: at once, or one kind alone.
VIEW_KINDS = ("all",) + ITEM_KINDS

#: The registers the skin speaks in: Jarl mode
#: (plain everyday words, technical detail folded)
#: or the full technical register (nothing folded).
REGISTERS = ("jarl", "technical")

_REGISTER_ALIASES = {
    "jarl": "jarl", "plain": "jarl",
    "plain_language": "jarl", "everyday": "jarl",
    "technical": "technical", "full": "technical",
    "tech": "technical", "full_technical": "technical"}

#: The register a session stands in when its state
#: names none: Jarl mode, plain words first.
DEFAULT_REGISTER = "jarl"

#: The standing law, as data: Jarl mode is the
#: default register of this layer.
JARL_IS_THE_DEFAULT_REGISTER = True

#: The one named action that unfolds folded
#: technical detail in Jarl mode - the keypress
#: the roadmap names.
UNFOLD_ACTION = "unfold"

VERDICT_WORDS = ("open", "strained", "shut")

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]*")

_PROVENANCE_KEYS = (
    "detail", "reason", "recorded_on", "day", "date",
    "actor", "by", "who", "source",
    "origin_session", "session")

#: Keys a record may never store because this layer
#: derives them at call time. "plain" is NOT among
#: them: for a lexicon term the plain words are the
#: held datum itself, and on every other item a
#: stored "plain" refuses as an unknown field.
_DERIVED_KEYS = frozenset({
    "passes", "segment", "misses", "register",
    "mode", "shown", "folded", "verdict"})

_REPORT_KEYS = frozenset({
    "report_id", "id", "seq", "sequence", "order",
    "title", "name", "lines", "facts",
    "action", "next_step"} | set(_PROVENANCE_KEYS))

_APPROVAL_KEYS = frozenset({
    "approval_id", "id", "seq", "sequence", "order",
    "title", "name", "ask", "question",
    "action", "actions", "lines", "context"}
    | set(_PROVENANCE_KEYS))

_STANDUP_KEYS = frozenset({
    "standup_id", "id", "seq", "sequence", "order",
    "person", "member", "done", "doing",
    "blocked"} | set(_PROVENANCE_KEYS))

_TERM_KEYS = frozenset({
    "term_id", "id", "seq", "sequence", "order",
    "term", "word", "plain", "plain_words"}
    | set(_PROVENANCE_KEYS))

_VIEW_KEYS = frozenset({
    "view_id", "id", "seq", "sequence", "order",
    "kind_filter", "filter", "kind"}
    | set(_PROVENANCE_KEYS))

_ROW_KEYS = frozenset({
    "item_id", "id", "kind", "label", "name",
    "segment", "recorded_on", "day", "date"})

_PANEL_KEYS = frozenset({
    "panel_id", "id", "view_id", "view",
    "kind_filter", "filter", "kind", "rows", "shown",
    "total_items", "items", "total_shown", "matched",
    "kind_counts", "kinds", "as_of", "day",
    "account", "statements"})

_VERDICT_KEYS = frozenset({
    "total_items", "items", "total_shown", "matched",
    "passing_shown", "passing", "distinct_kinds", "kinds",
    "earliest_on", "earliest", "latest_on", "latest",
    "verdict"})

_BOOK_KEYS = frozenset({"title", "name"})

_SKIN_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "canon_note", "guide", "reports", "approvals",
    "standups", "terms", "watched", "views", "panels"})

_EXAMPLE_TITLE = "Plain language at the M-181 slice boundary"

_EXAMPLE_REPORT_IDS = ("report-morning-build", "report-usage")

_EXAMPLE_APPROVAL_IDS = ("approval-release", "approval-wipe")

_EXAMPLE_STANDUP_IDS = ("standup-yrsa", "standup-tess")

_EXAMPLE_TERM_IDS = (
    "term-checkpoint", "term-deploy", "term-idempotent",
    "term-latency", "term-rollback", "term-throughput")

_EXAMPLE_WATCHED = (
    "checkpoint", "deploy", "idempotent", "latency",
    "quorum", "rollback", "throughput")

_EXAMPLE_PANEL_ID = "panel-m181-boundary"

_EXAMPLE_AS_OF = "2026-11-09"

_EXAMPLE_VIEW_IDS = ("view-all", "view-report")

PLAIN_EXPLANATION = (
    "The Plain-Language Skin: a Jarl mode register - "
    "reports, approvals, and stand-ups in plain "
    "everyday words, technical detail folded behind "
    "a keypress. A report, an approval ask and a "
    "stand-up are each held whole, and each renders "
    "two ways from the same held fields: plain words "
    "in Jarl mode, derived line by line through the "
    "book's plain-words lexicon, and the full "
    "technical words in the technical register. In "
    "Jarl mode the technical lines stand folded as "
    "data, unfolded by the one named unfold action, "
    "never deleted. An approval names exactly one "
    "action. A watched term with no lexicon entry "
    "is a miss: it passes through unchanged, stands "
    "named in the misses, and keeps its item from "
    "standing whole - no plain words are invented "
    "for it. The register is a named mode derived "
    "from session or config state at call time, "
    "never stored on an item or a message, and Jarl "
    "mode stands default. This layer renders words "
    "only: it approves nothing and sends nothing."
)

USAGE = (
    "Usage: /skin, /skin show, "
    "/skin report <report-id>, "
    "/skin approval <approval-id>, "
    "/skin standup <standup-id>, "
    "/skin term <term-id>, "
    "/skin view <view-id>, "
    "/skin kind <kind>, "
    "/skin panel, /skin verdict, "
    "/skin unfold <item-id>, /skin register"
)


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty text")
    return value.strip()


def _check_title(value: Any, what: str = "a title") -> str:
    return _clean_text(value, what)


def _check_long_text(value: Any, what: str) -> str:
    return _clean_text(value, what)


def _pick_any(mapping: Dict[str, Any], spellings: Tuple[str, ...],
              what: str) -> Any:
    for key in spellings:
        if key in mapping and mapping[key] is not None:
            return mapping[key]
    raise ValueError(f"a skin record names no {what}")


def _check_count(value: Any, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{what} must be a whole count")
    if value < 0:
        raise ValueError(f"{what} must not stand negative")
    return value


def _check_seq(value: Any, what: str = "a sequence") -> int:
    number = _check_count(value, what)
    if number < 1:
        raise ValueError(f"{what} must stand at 1 or later")
    return number


def _check_word(value: Any, what: str) -> str:
    text = _clean_text(value, what)
    if any(ch.isspace() for ch in text):
        raise ValueError(f"{what} must be one word: {text!r}")
    return text


def _check_day(value: Any, what: str = "a day") -> str:
    text = _clean_text(value, what)
    try:
        date.fromisoformat(text)
    except ValueError:
        raise ValueError(
            f"{what} must stand as a day (YYYY-MM-DD): {text!r}") from None
    return text


def _check_lines(value: Any, what: str) -> Tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError(f"{what} must be a list of lines")
    lines = tuple(_check_long_text(line, what) for line in value)
    return lines


def _provenance(mapping: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "detail": _check_long_text(
            _pick_any(mapping, ("detail", "reason"), "a detail"),
            "a detail"),
        "recorded_on": _check_day(_pick_any(
            mapping, ("recorded_on", "day", "date"), "a day")),
        "actor": _clean_text(_pick_any(
            mapping, ("actor", "by", "who"), "an actor"), "an actor"),
        "source": _clean_text(
            _pick_any(mapping, ("source",), "a source"), "a source"),
        "origin_session": _check_word(_pick_any(
            mapping, ("origin_session", "session"),
            "an origin session"), "an origin session"),
    }


def _needed(mapping: Dict[str, Any],
            allowed: frozenset, what: str) -> None:
    if not isinstance(mapping, dict):
        raise ValueError(f"{what} must be a mapping")
    derived = sorted(set(mapping) & _DERIVED_KEYS)
    if derived:
        raise ValueError(
            f"{what} names stored judgements {derived} - "
            f"passes, misses, the register and the segments "
            f"are derived at call time, never stored")
    unknown = sorted(set(mapping) - allowed)
    if unknown:
        raise ValueError(f"{what} names unknown fields {unknown}")


def normalize_kind(value: Any) -> str:
    text = _check_word(value, "a kind")
    kind = _KIND_ALIASES.get(text.lower())
    if kind is None:
        raise ValueError(
            f"unknown skin kind {text!r} - kinds stand: "
            f"{', '.join(ITEM_KINDS)}")
    return kind


def normalize_kind_filter(value: Any) -> str:
    text = _check_word(value, "a kind filter")
    if text.lower() == "all":
        return "all"
    return normalize_kind(text)


def normalize_term(value: Any) -> str:
    text = _check_word(value, "a term")
    return text.lower()


def normalize_register(value: Any) -> str:
    """One register name, from any of its spellings."""
    if isinstance(value, bool):
        return "jarl" if value else "technical"
    text = _check_word(value, "a register")
    register = _REGISTER_ALIASES.get(text.lower())
    if register is None:
        raise ValueError(
            f"unknown register {text!r} - registers stand: "
            f"{', '.join(REGISTERS)}")
    return register


def derive_register(source: Any = None) -> str:
    """The register a session or config stands in.

    The mode is DERIVED at call time from the state
    handed in - a register name itself, a mapping
    naming one under register, mode, jarl_mode or
    plain_language (a boolean there reads as the
    Jarl switch), or an object carrying such a
    mapping as its config or such a name as its
    register - and Jarl mode stands when the state
    names none. The mode is never read off an item
    and never stored on one.
    """
    if source is None:
        return DEFAULT_REGISTER
    if isinstance(source, (str, bool)):
        return normalize_register(source)
    if isinstance(source, dict):
        for key in ("register", "mode", "jarl_mode",
                    "plain_language", "plain"):
            if key in source and source[key] is not None:
                return normalize_register(source[key])
        return DEFAULT_REGISTER
    config = getattr(source, "config", None)
    if isinstance(config, dict):
        return derive_register(config)
    named = getattr(source, "register", None)
    if named is not None:
        return normalize_register(named)
    return DEFAULT_REGISTER


# ---------------------------------------------------------------------
# The held items: a report, an approval, a stand-up,
# and a lexicon term, each held whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class SkinReport:
    """One report, held whole under the skin.

    The report stands under its title with its
    technical lines - the facts as the technical
    register speaks them - and the one next step
    it names, if it names one. Its plain lines,
    its folded detail, its misses and whether it
    stands whole are derived from those fields and
    the book's lexicon at call time, never stored.
    """

    report_id: str
    seq: int
    title: str
    lines: Tuple[str, ...]
    action: Optional[str]
    detail: str
    recorded_on: str
    actor: str
    source: str
    origin_session: str

    kind = "report"

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "report_id", _check_word(self.report_id, "a report id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "title", _check_title(self.title, "a report title"))
        lines = _check_lines(self.lines, "report lines")
        if not lines:
            raise ValueError(
                f"report {self.report_id!r} names no lines - "
                f"a report the skin speaks over holds its "
                f"facts as lines")
        object.__setattr__(self, "lines", lines)
        if self.action is not None:
            object.__setattr__(
                self, "action",
                _check_long_text(self.action, "a next step"))
        object.__setattr__(
            self, "detail", _check_long_text(self.detail, "a detail"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))
        object.__setattr__(
            self, "actor", _clean_text(self.actor, "an actor"))
        object.__setattr__(
            self, "source", _clean_text(self.source, "a source"))
        object.__setattr__(
            self, "origin_session",
            _check_word(self.origin_session, "an origin session"))

    @property
    def item_id(self) -> str:
        return self.report_id

    def to_record(self) -> Dict[str, Any]:
        return _report_record(self)


def _check_report_ref(value: Any) -> SkinReport:
    if isinstance(value, SkinReport):
        return value
    return build_report(value)


def validate_report(report: Any) -> SkinReport:
    """Judge one report whole, from a record or a mapping."""
    return _check_report_ref(report)


def build_report(report: Any = None, **kwargs: Any) -> SkinReport:
    """Build one report from a mapping or field words."""
    if kwargs:
        if report is not None:
            raise ValueError("build_report takes a mapping or fields")
        report = kwargs
    if isinstance(report, SkinReport):
        return report
    _needed(report, _REPORT_KEYS, "a report")
    return SkinReport(
        report_id=_check_word(_pick_any(
            report, ("report_id", "id"), "a report id"), "a report id"),
        seq=_check_seq(_pick_any(
            report, ("seq", "sequence", "order"), "a sequence")),
        title=_check_title(_pick_any(
            report, ("title", "name"), "a report title"),
            "a report title"),
        lines=_check_lines(_pick_any(
            report, ("lines", "facts"), "report lines"), "report lines"),
        action=report.get("action", report.get("next_step")),
        **_provenance(report))


@dataclass(frozen=True)
class SkinApproval:
    """One approval ask, held whole under the skin.

    The approval stands under its title with its
    ask - the question as the technical register
    speaks it - its context lines, and exactly the
    one action that matters: the single step the
    ask turns on. An approval naming no action, or
    several, refuses by name; its plain ask, its
    misses and whether it stands whole are derived
    at call time, never stored.
    """

    approval_id: str
    seq: int
    title: str
    ask: str
    action: str
    lines: Tuple[str, ...]
    detail: str
    recorded_on: str
    actor: str
    source: str
    origin_session: str

    kind = "approval"

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "approval_id",
            _check_word(self.approval_id, "an approval id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "title", _check_title(self.title, "an approval title"))
        object.__setattr__(
            self, "ask", _check_long_text(self.ask, "an ask"))
        action = self.action
        if isinstance(action, (list, tuple)):
            raise ValueError(
                f"approval {self.approval_id!r} names several "
                f"actions - an approval names exactly the one "
                f"action that matters, and naming several "
                f"refuses by name")
        object.__setattr__(
            self, "action",
            _check_long_text(action, "the one action"))
        object.__setattr__(
            self, "lines", _check_lines(self.lines, "approval lines"))
        object.__setattr__(
            self, "detail", _check_long_text(self.detail, "a detail"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))
        object.__setattr__(
            self, "actor", _clean_text(self.actor, "an actor"))
        object.__setattr__(
            self, "source", _clean_text(self.source, "a source"))
        object.__setattr__(
            self, "origin_session",
            _check_word(self.origin_session, "an origin session"))

    @property
    def item_id(self) -> str:
        return self.approval_id

    def to_record(self) -> Dict[str, Any]:
        return _approval_record(self)


def _check_approval_ref(value: Any) -> SkinApproval:
    if isinstance(value, SkinApproval):
        return value
    return build_approval(value)


def validate_approval(approval: Any) -> SkinApproval:
    """Judge one approval whole, from a record or a mapping."""
    return _check_approval_ref(approval)


def build_approval(approval: Any = None, **kwargs: Any) -> SkinApproval:
    """Build one approval from a mapping or field words."""
    if kwargs:
        if approval is not None:
            raise ValueError("build_approval takes a mapping or fields")
        approval = kwargs
    if isinstance(approval, SkinApproval):
        return approval
    _needed(approval, _APPROVAL_KEYS, "an approval")
    if "action" not in approval and "actions" not in approval:
        raise ValueError(
            "an approval names no action - an approval asks "
            "with exactly the one action that matters, and "
            "an approval naming none refuses by name")
    return SkinApproval(
        approval_id=_check_word(_pick_any(
            approval, ("approval_id", "id"), "an approval id"),
            "an approval id"),
        seq=_check_seq(_pick_any(
            approval, ("seq", "sequence", "order"), "a sequence")),
        title=_check_title(_pick_any(
            approval, ("title", "name"), "an approval title"),
            "an approval title"),
        ask=_check_long_text(_pick_any(
            approval, ("ask", "question"), "an ask"), "an ask"),
        action=_pick_any(approval, ("action", "actions"), "an action"),
        lines=_check_lines(
            approval.get("lines", approval.get("context", ())),
            "approval lines"),
        **_provenance(approval))


@dataclass(frozen=True)
class SkinStandup:
    """One stand-up, held whole under the skin.

    The stand-up stands under its person's name
    with what they have done, what they are doing
    and what stands blocked, each as lines in the
    technical register's words. Its plain lines,
    its misses and whether it stands whole are
    derived at call time, never stored.
    """

    standup_id: str
    seq: int
    person: str
    done: Tuple[str, ...]
    doing: Tuple[str, ...]
    blocked: Tuple[str, ...]
    detail: str
    recorded_on: str
    actor: str
    source: str
    origin_session: str

    kind = "standup"

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "standup_id",
            _check_word(self.standup_id, "a stand-up id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "person",
            normalize_member_id(
                _clean_text(self.person, "a person")))
        object.__setattr__(
            self, "done", _check_lines(self.done, "done lines"))
        doing = _check_lines(self.doing, "doing lines")
        if not doing:
            raise ValueError(
                f"stand-up {self.standup_id!r} names nothing "
                f"doing - a stand-up speaks of work in hand")
        object.__setattr__(self, "doing", doing)
        object.__setattr__(
            self, "blocked",
            _check_lines(self.blocked, "blocked lines"))
        object.__setattr__(
            self, "detail", _check_long_text(self.detail, "a detail"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))
        object.__setattr__(
            self, "actor", _clean_text(self.actor, "an actor"))
        object.__setattr__(
            self, "source", _clean_text(self.source, "a source"))
        object.__setattr__(
            self, "origin_session",
            _check_word(self.origin_session, "an origin session"))

    @property
    def item_id(self) -> str:
        return self.standup_id

    def to_record(self) -> Dict[str, Any]:
        return _standup_record(self)


def _check_standup_ref(value: Any) -> SkinStandup:
    if isinstance(value, SkinStandup):
        return value
    return build_standup(value)


def validate_standup(standup: Any) -> SkinStandup:
    """Judge one stand-up whole, from a record or a mapping."""
    return _check_standup_ref(standup)


def build_standup(standup: Any = None, **kwargs: Any) -> SkinStandup:
    """Build one stand-up from a mapping or field words."""
    if kwargs:
        if standup is not None:
            raise ValueError("build_standup takes a mapping or fields")
        standup = kwargs
    if isinstance(standup, SkinStandup):
        return standup
    _needed(standup, _STANDUP_KEYS, "a stand-up")
    return SkinStandup(
        standup_id=_check_word(_pick_any(
            standup, ("standup_id", "id"), "a stand-up id"),
            "a stand-up id"),
        seq=_check_seq(_pick_any(
            standup, ("seq", "sequence", "order"), "a sequence")),
        person=_clean_text(_pick_any(
            standup, ("person", "member"), "a person"), "a person"),
        done=_check_lines(standup.get("done", ()), "done lines"),
        doing=_check_lines(_pick_any(
            standup, ("doing",), "doing lines"), "doing lines"),
        blocked=_check_lines(
            standup.get("blocked", ()), "blocked lines"),
        **_provenance(standup))


@dataclass(frozen=True)
class SkinTerm:
    """One lexicon term, held whole: a technical
    word and the plain everyday words it is spoken
    with in Jarl mode. The lexicon is data - a term
    stands here or the skin holds no plain words
    for it, and invents none."""

    term_id: str
    seq: int
    term: str
    plain: str
    detail: str
    recorded_on: str
    actor: str
    source: str
    origin_session: str

    kind = "term"

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "term_id", _check_word(self.term_id, "a term id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "term", normalize_term(self.term))
        object.__setattr__(
            self, "plain",
            _check_long_text(self.plain, "plain words"))
        object.__setattr__(
            self, "detail", _check_long_text(self.detail, "a detail"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))
        object.__setattr__(
            self, "actor", _clean_text(self.actor, "an actor"))
        object.__setattr__(
            self, "source", _clean_text(self.source, "a source"))
        object.__setattr__(
            self, "origin_session",
            _check_word(self.origin_session, "an origin session"))

    @property
    def item_id(self) -> str:
        return self.term_id

    def to_record(self) -> Dict[str, Any]:
        return _term_record(self)


def _check_term_ref(value: Any) -> SkinTerm:
    if isinstance(value, SkinTerm):
        return value
    return build_term(value)


def validate_term(term: Any) -> SkinTerm:
    """Judge one lexicon term whole."""
    return _check_term_ref(term)


def build_term(term: Any = None, **kwargs: Any) -> SkinTerm:
    """Build one lexicon term from a mapping or fields."""
    if kwargs:
        if term is not None:
            raise ValueError("build_term takes a mapping or fields")
        term = kwargs
    if isinstance(term, SkinTerm):
        return term
    _needed(term, _TERM_KEYS, "a term")
    return SkinTerm(
        term_id=_check_word(_pick_any(
            term, ("term_id", "id"), "a term id"), "a term id"),
        seq=_check_seq(_pick_any(
            term, ("seq", "sequence", "order"), "a sequence")),
        term=normalize_term(_pick_any(
            term, ("term", "word"), "a term")),
        plain=_check_long_text(_pick_any(
            term, ("plain", "plain_words"), "plain words"),
            "plain words"),
        **_provenance(term))


@dataclass(frozen=True)
class SkinView:
    """One held view: every kind at once, or one
    kind alone. A view is its own record; the panel
    and the verdict are derived under it."""

    view_id: str
    seq: int
    kind_filter: str
    detail: str
    recorded_on: str
    actor: str
    source: str
    origin_session: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "view_id", _check_word(self.view_id, "a view id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "kind_filter",
            normalize_kind_filter(self.kind_filter))
        object.__setattr__(
            self, "detail", _check_long_text(self.detail, "a detail"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))
        object.__setattr__(
            self, "actor", _clean_text(self.actor, "an actor"))
        object.__setattr__(
            self, "source", _clean_text(self.source, "a source"))
        object.__setattr__(
            self, "origin_session",
            _check_word(self.origin_session, "an origin session"))

    def to_record(self) -> Dict[str, Any]:
        return _view_record(self)


def _check_view_ref(value: Any) -> SkinView:
    if isinstance(value, SkinView):
        return value
    return build_view(value)


def validate_view(view: Any) -> SkinView:
    """Judge one view whole."""
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> SkinView:
    """Build one view from a mapping or field words."""
    if kwargs:
        if view is not None:
            raise ValueError("build_view takes a mapping or fields")
        view = kwargs
    if isinstance(view, SkinView):
        return view
    _needed(view, _VIEW_KEYS, "a view")
    return SkinView(
        view_id=_check_word(_pick_any(
            view, ("view_id", "id"), "a view id"), "a view id"),
        seq=_check_seq(_pick_any(
            view, ("seq", "sequence", "order"), "a sequence")),
        kind_filter=normalize_kind_filter(_pick_any(
            view, ("kind_filter", "filter", "kind"),
            "a kind filter")),
        **_provenance(view))


# ---------------------------------------------------------------------
# The rendering engine: same facts, plainer words;
# technical detail folded, never deleted.
# ---------------------------------------------------------------------


def _terms_map(source: Any) -> Dict[str, str]:
    """The lexicon a source carries, as term -> plain.

    A source may be a skin book, a mapping of term
    to plain words, an iterable of lexicon terms,
    or nothing (the empty lexicon).
    """
    if source is None:
        return {}
    if isinstance(source, SkinBook):
        return source.terms_map()
    if isinstance(source, dict):
        return {normalize_term(key): _check_long_text(
            value, "plain words") for key, value in source.items()}
    return {term.term: term.plain
            for term in (_check_term_ref(item) for item in source)}


def _watched(source: Any) -> Tuple[str, ...]:
    if isinstance(source, SkinBook):
        return source.watched
    return ()


def plain_for_term(term: Any, source: Any) -> Optional[str]:
    """The plain words one term stands with, or None.

    None is the honest answer for a term the
    lexicon holds no entry for: this layer invents
    no plain words.
    """
    return _terms_map(source).get(normalize_term(term))


def translate_text(text: Any, source: Any) -> str:
    """One line spoken plainly, derived from itself.

    Each word the lexicon lists is spoken with its
    plain words; every other word - every number,
    every name, every unlisted term - stands
    exactly as written. The plain line is the
    technical line and nothing else, so the facts
    cannot drift between the registers.
    """
    line = _check_long_text(text, "a line")
    lexicon = _terms_map(source)
    if not lexicon:
        return line

    def _spoken(match: Any) -> str:
        plain = lexicon.get(match.group(0).lower())
        return plain if plain is not None else match.group(0)

    return _TOKEN_RE.sub(_spoken, line)


def technical_lines(item: Any) -> Tuple[str, ...]:
    """An item's lines as the technical register
    speaks them, derived from its held fields."""
    if isinstance(item, SkinReport):
        lines = list(item.lines)
        if item.action is not None:
            lines.append(f"next step: {item.action}")
        return tuple(lines)
    if isinstance(item, SkinApproval):
        lines = [f"ask: {item.ask}", f"action: {item.action}"]
        lines.extend(item.lines)
        return tuple(lines)
    if isinstance(item, SkinStandup):
        lines = [f"done: {line}" for line in item.done]
        lines.extend(f"doing: {line}" for line in item.doing)
        lines.extend(f"blocked: {line}" for line in item.blocked)
        return tuple(lines)
    if isinstance(item, SkinTerm):
        return (f"{item.term} stands for: {item.plain}",)
    raise ValueError(f"no skin item stands in {item!r}")


def plain_lines(item: Any, source: Any) -> Tuple[str, ...]:
    """An item's lines in plain everyday words -
    the technical lines, derived through the
    lexicon alone."""
    return tuple(translate_text(line, source)
                 for line in technical_lines(item))


def item_misses(item: Any, source: Any) -> Tuple[str, ...]:
    """The watched terms an item speaks that the
    lexicon holds no plain words for, in the order
    the item speaks them. A miss is honest: the
    term stands unchanged in every rendering and
    is named here, never silently invented."""
    watched = set(_watched(source))
    if not watched:
        return ()
    lexicon = _terms_map(source)
    misses: List[str] = []
    for line in technical_lines(item):
        for match in _TOKEN_RE.finditer(line):
            word = match.group(0).lower()
            if (word in watched and word not in lexicon
                    and word not in misses):
                misses.append(word)
    return tuple(misses)


def lexicon_misses(source: Any) -> Tuple[str, ...]:
    """Every watched term the lexicon holds no
    entry for, in watched order."""
    lexicon = _terms_map(source)
    return tuple(word for word in _watched(source)
                 if word not in lexicon)


def item_passes(item: Any, source: Any = None) -> bool:
    """Whether an item stands whole under the skin:
    it speaks no watched term the lexicon cannot
    speak plainly. A lexicon term stands whole by
    standing in the lexicon at all."""
    if isinstance(item, SkinTerm):
        return True
    return not item_misses(item, source)


def segment_of(item: Any, source: Any = None) -> str:
    """An item's one-line segment, derived from its
    own fields and the lexicon: its first technical
    line, its first plain line, and its misses."""
    tech = technical_lines(item)
    plain = plain_lines(item, source)
    misses = item_misses(item, source)
    miss_words = ", ".join(misses) if misses else "none"
    return (f"{item.item_id}: {item.kind} says "
            f"'{tech[0]}' - plainly: '{plain[0]}' "
            f"- misses: {miss_words}")


@dataclass(frozen=True)
class SkinRendering:
    """One item rendered in one register.

    The shown lines are what the register speaks
    aloud; the folded lines are the technical
    detail folded behind the unfold keypress in
    Jarl mode - held whole as data, empty in the
    technical register, where nothing stands
    folded. The register is the mode of this one
    rendering, derived at call time; it is stored
    on no item and no message.
    """

    item_id: str
    kind: str
    register: str
    shown: Tuple[str, ...]
    folded: Tuple[str, ...]
    misses: Tuple[str, ...]
    action: Optional[str]

    def to_record(self) -> Dict[str, Any]:
        return _rendering_record(self)


def render_item(item: Any, source: Any = None,
                register: Any = None) -> SkinRendering:
    """Render one item in a register.

    The register is derived from the state handed
    in (or the book's own session state) when none
    is named; with none anywhere, Jarl mode stands.
    In Jarl mode the shown lines are the plain
    lines and the technical lines stand folded;
    in the technical register the technical lines
    are shown and nothing stands folded.
    """
    item = _check_item_ref(item)
    mode = (normalize_register(register) if register is not None
            else derive_register(source))
    tech = technical_lines(item)
    action = item.action if isinstance(
        item, (SkinReport, SkinApproval)) else None
    if mode == "jarl":
        return SkinRendering(
            item_id=item.item_id, kind=item.kind, register=mode,
            shown=plain_lines(item, source), folded=tech,
            misses=item_misses(item, source), action=action)
    return SkinRendering(
        item_id=item.item_id, kind=item.kind, register=mode,
        shown=tech, folded=(),
        misses=item_misses(item, source), action=action)


def unfold_rendering(rendering: Any) -> SkinRendering:
    """The one named unfold action: the folded
    technical detail stands shown, whole, after
    the lines already shown. Nothing is rewritten
    and nothing is lost - the folded lines move,
    they are never regenerated."""
    if not isinstance(rendering, SkinRendering):
        raise ValueError("unfold takes one rendering")
    if not rendering.folded:
        return rendering
    return replace(rendering,
                   shown=rendering.shown + rendering.folded,
                   folded=())


def _check_item_ref(value: Any) -> Any:
    if isinstance(value, (SkinReport, SkinApproval,
                          SkinStandup, SkinTerm)):
        return value
    return build_item(value)


def build_item(item: Any) -> Any:
    """Build one item of whichever kind its shape
    names, from a mapping."""
    found = inspect_item_source(item)
    kind = found["kind"]
    if kind == "report":
        return build_report(item)
    if kind == "approval":
        return build_approval(item)
    if kind == "standup":
        return build_standup(item)
    if kind == "term":
        return build_term(item)
    raise ValueError(found["reason"])


def inspect_item_source(piece: Any) -> Dict[str, Any]:
    """Name what kind of item a source stands for,
    or why it stands for none."""
    if isinstance(piece, (SkinReport, SkinApproval,
                          SkinStandup, SkinTerm)):
        return {"kind": piece.kind, "reason": "a held item"}
    if not isinstance(piece, dict):
        return {"kind": None,
                "reason": "a skin item source must be a mapping"}
    derived = sorted(set(piece) & _DERIVED_KEYS)
    if derived:
        return {"kind": None,
                "reason": (f"the source names stored judgements "
                           f"{derived} - passes, misses and the "
                           f"register are derived, never stored")}
    if "report_id" in piece or "lines" in piece or "facts" in piece:
        return {"kind": "report", "reason": "report fields stand"}
    if "approval_id" in piece or "ask" in piece:
        return {"kind": "approval", "reason": "approval fields stand"}
    if "standup_id" in piece or "doing" in piece:
        return {"kind": "standup", "reason": "stand-up fields stand"}
    if "term_id" in piece or ("term" in piece and "plain" in piece):
        return {"kind": "term", "reason": "term fields stand"}
    return {"kind": None,
            "reason": "no skin item fields stand in the source"}


# ---------------------------------------------------------------------
# The panel and the verdict, derived under one view.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class SkinPanelRow:
    """One row of a panel: one shown item, its kind,
    its label, and its derived segment."""

    item_id: str
    kind: str
    label: str
    segment: str
    recorded_on: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id, "kind": self.kind,
            "label": self.label, "segment": self.segment,
            "recorded_on": self.recorded_on}


def _row_for_item(item: Any, source: Any) -> SkinPanelRow:
    label = (item.title if isinstance(
        item, (SkinReport, SkinApproval)) else item.item_id)
    return SkinPanelRow(
        item_id=item.item_id, kind=item.kind, label=label,
        segment=segment_of(item, source),
        recorded_on=item.recorded_on)


def _check_row_ref(value: Any) -> SkinPanelRow:
    if isinstance(value, SkinPanelRow):
        return value
    if not isinstance(value, dict):
        raise ValueError("a panel row must be a mapping")
    unknown = sorted(set(value) - _ROW_KEYS)
    if unknown:
        raise ValueError(f"a panel row names unknown fields {unknown}")
    return SkinPanelRow(
        item_id=_check_word(_pick_any(
            value, ("item_id", "id"), "an item id"), "an item id"),
        kind=normalize_kind(_pick_any(
            value, ("kind",), "a kind")),
        label=_clean_text(_pick_any(
            value, ("label", "name"), "a label"), "a label"),
        segment=_check_long_text(_pick_any(
            value, ("segment",), "a segment"), "a segment"),
        recorded_on=_check_day(_pick_any(
            value, ("recorded_on", "day", "date"), "a day")))


def validate_row(row: Any, item: Any = None,
                 source: Any = None) -> SkinPanelRow:
    """Judge one panel row whole; against its item,
    the row must agree with the derived row."""
    checked = _check_row_ref(row)
    if item is not None:
        derived = _row_for_item(_check_item_ref(item), source)
        if checked != derived:
            raise ValueError(
                f"panel row {checked.item_id!r} disagrees with "
                f"its item - rows are derived, never stored apart")
    return checked


def build_row(row: Any = None, item: Any = None,
              source: Any = None, **kwargs: Any) -> SkinPanelRow:
    """Build one panel row from a mapping, or derive
    it from its item."""
    if kwargs:
        if row is not None:
            raise ValueError("build_row takes a mapping or fields")
        row = kwargs
    if row is None and item is not None:
        return _row_for_item(_check_item_ref(item), source)
    return validate_row(row, item, source)


@dataclass(frozen=True)
class SkinKindCount:
    """How many shown items stand of one kind."""

    kind: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"kind": self.kind, "items": self.items}


def _check_kind_count_ref(value: Any) -> SkinKindCount:
    if isinstance(value, SkinKindCount):
        return value
    if not isinstance(value, dict):
        raise ValueError("a kind count must be a mapping")
    return SkinKindCount(
        kind=normalize_kind(_pick_any(
            value, ("kind",), "a kind")),
        items=_check_count(_pick_any(
            value, ("items",), "an item count"), "an item count"))


def _kind_counts(rows: Tuple[SkinPanelRow, ...]
                 ) -> Tuple[SkinKindCount, ...]:
    counts: Dict[str, int] = {}
    for row in rows:
        counts[row.kind] = counts.get(row.kind, 0) + 1
    return tuple(SkinKindCount(kind=kind, items=counts[kind])
                 for kind in ITEM_KINDS if kind in counts)


def _panel_account(total_items: int, total_shown: int,
                   counts: Tuple[SkinKindCount, ...],
                   passing_shown: int, kind_filter: str,
                   as_of: str) -> Tuple[str, ...]:
    by_kind = ", ".join(
        f"{count.kind} {count.items}" for count in counts)
    return (
        f"The plain-language book holds {total_items} items "
        f"as of {as_of}: the view '{kind_filter}' shows "
        f"{total_shown} of them: {by_kind}; {passing_shown} "
        f"of the shown items stand whole.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its item's own fields "
        "and the book's lexicon - the plain line from the "
        "technical line through the lexicon alone - and no "
        "judgement is stored on any item.",
        "Jarl mode speaks plain everyday words and folds the "
        "technical detail behind the unfold keypress; the "
        "technical register folds nothing. A watched term "
        "with no lexicon entry is a miss: it passes through "
        "unchanged, stands named, and keeps its item from "
        "standing whole.",
    )


@dataclass(frozen=True)
class SkinPanel:
    """The panel of one book under one view, derived
    whole: its rows in held order, its tallies, and
    its account of itself."""

    panel_id: str
    view_id: str
    kind_filter: str
    rows: Tuple[SkinPanelRow, ...]
    total_items: int
    total_shown: int
    kind_counts: Tuple[SkinKindCount, ...]
    as_of: str
    account: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return _panel_record(self)


def _held_items(source: Any) -> Tuple[Any, ...]:
    book = _source_book(source)
    return book.items()


def _held_views(source: Any) -> Tuple[SkinView, ...]:
    return _source_book(source).views


def _resolve_view(source: Any, view: Any) -> SkinView:
    book = _source_book(source)
    if view is None:
        return _default_view(book)
    if isinstance(view, SkinView):
        return view
    return book.view_for(view)


def _default_view(source: Any) -> SkinView:
    book = _source_book(source)
    if not book.views:
        raise ValueError(
            f"book {book.title!r} holds no view - a panel "
            f"stands under a held view alone")
    return book.views[0]


def shown_items(source: Any, view: Any = None) -> Tuple[Any, ...]:
    """The items one view shows, in held order."""
    book = _source_book(source)
    held = _resolve_view(book, view)
    if held.kind_filter == "all":
        return book.items()
    return tuple(item for item in book.items()
                 if item.kind == held.kind_filter)


def items_for_kind(source: Any, kind: Any) -> Tuple[Any, ...]:
    """The book's items of one kind, in held order."""
    book = _source_book(source)
    wanted = normalize_kind(kind)
    return tuple(item for item in book.items()
                 if item.kind == wanted)


def passing_items(source: Any) -> Tuple[Any, ...]:
    """The book's items that stand whole."""
    book = _source_book(source)
    return tuple(item for item in book.items()
                 if item_passes(item, book))


def total_items(source: Any) -> int:
    return len(_source_book(source).items())


def derive_panel(source: Any, view: Any = None) -> SkinPanel:
    """Derive the panel of one book under one view."""
    book = _source_book(source)
    held = _resolve_view(book, view)
    shown = shown_items(book, held)
    rows = tuple(_row_for_item(item, book) for item in shown)
    counts = _kind_counts(rows)
    passing = sum(1 for item in shown if item_passes(item, book))
    as_of = max((item.recorded_on for item in book.items()),
                default=_EXAMPLE_AS_OF)
    return SkinPanel(
        panel_id=f"panel-{held.view_id}", view_id=held.view_id,
        kind_filter=held.kind_filter, rows=rows,
        total_items=len(book.items()), total_shown=len(shown),
        kind_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.items()), len(shown), counts, passing,
            held.kind_filter, as_of))


def validate_panel(panel: Any, source: Any = None) -> SkinPanel:
    """Judge one panel whole; against its book, the
    panel must agree with the derived panel."""
    checked = _check_panel_ref(panel)
    if source is not None:
        book = _source_book(source)
        derived = derive_panel(book, checked.view_id)
        if (checked.view_id != derived.view_id
                or checked.kind_filter != derived.kind_filter
                or checked.rows != derived.rows
                or checked.total_items != derived.total_items
                or checked.total_shown != derived.total_shown
                or checked.kind_counts != derived.kind_counts
                or checked.as_of != derived.as_of
                or checked.account != derived.account):
            raise ValueError(
                f"panel {checked.panel_id!r} disagrees with "
                f"its book - panels are derived, never stored apart")
    return checked


def _check_panel_ref(value: Any) -> SkinPanel:
    if isinstance(value, SkinPanel):
        return value
    if not isinstance(value, dict):
        raise ValueError("a panel must be a mapping")
    unknown = sorted(set(value) - _PANEL_KEYS)
    if unknown:
        raise ValueError(f"a panel names unknown fields {unknown}")
    rows = tuple(_check_row_ref(row) for row in _pick_any(
        value, ("rows", "shown"), "panel rows"))
    return SkinPanel(
        panel_id=_check_word(_pick_any(
            value, ("panel_id", "id"), "a panel id"), "a panel id"),
        view_id=_check_word(_pick_any(
            value, ("view_id", "view"), "a view id"), "a view id"),
        kind_filter=normalize_kind_filter(_pick_any(
            value, ("kind_filter", "filter", "kind"),
            "a kind filter")),
        rows=rows,
        total_items=_check_count(_pick_any(
            value, ("total_items", "items"), "a total"), "a total"),
        total_shown=_check_count(_pick_any(
            value, ("total_shown", "matched"), "a shown total"),
            "a shown total"),
        kind_counts=tuple(_check_kind_count_ref(count)
                          for count in value.get("kind_counts",
                                                 value.get("kinds", ()))),
        as_of=_check_day(_pick_any(
            value, ("as_of", "day"), "an as-of day")),
        account=_check_lines(_pick_any(
            value, ("account", "statements"), "an account"),
            "an account"))


def build_panel(panel: Any = None, source: Any = None,
                view: Any = None, **kwargs: Any) -> SkinPanel:
    """Build one panel from a mapping, or derive it
    from its book under a view."""
    if kwargs:
        if panel is not None:
            raise ValueError("build_panel takes a mapping or fields")
        panel = kwargs
    if panel is None:
        return derive_panel(source, view)
    return validate_panel(panel, source)


def _verdict_word(total_shown: int, passing_shown: int) -> str:
    if total_shown and passing_shown == total_shown:
        return "open"
    if passing_shown:
        return "strained"
    return "shut"


@dataclass(frozen=True)
class SkinVerdict:
    """The verdict of one book under one view,
    derived from the shown items alone."""

    total_items: int
    total_shown: int
    passing_shown: int
    distinct_kinds: int
    earliest_on: Optional[str]
    latest_on: Optional[str]
    verdict: str

    def to_record(self) -> Dict[str, Any]:
        return _verdict_record(self)


def derive_verdict(source: Any, view: Any = None) -> SkinVerdict:
    """Derive the verdict of one book under one view."""
    book = _source_book(source)
    shown = shown_items(book, view)
    passing = sum(1 for item in shown if item_passes(item, book))
    days = [item.recorded_on for item in shown]
    return SkinVerdict(
        total_items=len(book.items()), total_shown=len(shown),
        passing_shown=passing,
        distinct_kinds=len({item.kind for item in shown}),
        earliest_on=min(days) if days else None,
        latest_on=max(days) if days else None,
        verdict=_verdict_word(len(shown), passing))


def _check_verdict_ref(value: Any) -> SkinVerdict:
    if isinstance(value, SkinVerdict):
        return value
    if not isinstance(value, dict):
        raise ValueError("a verdict must be a mapping")
    unknown = sorted(set(value) - _VERDICT_KEYS)
    if unknown:
        raise ValueError(f"a verdict names unknown fields {unknown}")
    word = _check_word(_pick_any(
        value, ("verdict",), "a verdict"), "a verdict")
    if word not in VERDICT_WORDS:
        raise ValueError(f"unknown verdict word {word!r}")
    earliest = value.get("earliest_on", value.get("earliest"))
    latest = value.get("latest_on", value.get("latest"))
    return SkinVerdict(
        total_items=_check_count(_pick_any(
            value, ("total_items", "items"), "a total"), "a total"),
        total_shown=_check_count(_pick_any(
            value, ("total_shown", "matched"), "a shown total"),
            "a shown total"),
        passing_shown=_check_count(_pick_any(
            value, ("passing_shown", "passing"), "a passing total"),
            "a passing total"),
        distinct_kinds=_check_count(_pick_any(
            value, ("distinct_kinds", "kinds"), "a kinds total"),
            "a kinds total"),
        earliest_on=(_check_day(earliest) if earliest else None),
        latest_on=(_check_day(latest) if latest else None),
        verdict=word)


def validate_verdict(verdict: Any, source: Any = None,
                     view: Any = None) -> SkinVerdict:
    """Judge one verdict whole; against its book, it
    must agree with the derived verdict."""
    checked = _check_verdict_ref(verdict)
    if source is not None:
        derived = derive_verdict(source, view)
        if checked != derived:
            raise ValueError(
                "the verdict disagrees with its book - verdicts "
                "are derived, never stored apart")
    return checked


def build_verdict(verdict: Any = None, source: Any = None,
                  view: Any = None, **kwargs: Any) -> SkinVerdict:
    """Build one verdict from a mapping, or derive it."""
    if kwargs:
        if verdict is not None:
            raise ValueError("build_verdict takes a mapping or fields")
        verdict = kwargs
    if verdict is None:
        return derive_verdict(source, view)
    return validate_verdict(verdict, source, view)


# ---------------------------------------------------------------------
# The book: items, the lexicon, the watched terms,
# views and pinned panels, held whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class SkinBook:
    """One plain-language book, held whole: its
    reports, approvals, stand-ups and lexicon
    terms, the terms it watches, its views, and
    the panels pinned in its file, each judged
    against the derivation when the book loads."""

    title: str
    reports: Tuple[SkinReport, ...]
    approvals: Tuple[SkinApproval, ...]
    standups: Tuple[SkinStandup, ...]
    terms: Tuple[SkinTerm, ...]
    watched: Tuple[str, ...]
    views: Tuple[SkinView, ...]
    panels: Tuple[SkinPanel, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book title"))
        for name in ("reports", "approvals", "standups", "terms"):
            items = tuple(getattr(self, name))
            ids = [item.item_id for item in items]
            seqs = [item.seq for item in items]
            if len(set(ids)) != len(ids):
                raise ValueError(
                    f"book {self.title!r} holds two {name} "
                    f"under one id")
            if len(set(seqs)) != len(seqs):
                raise ValueError(
                    f"book {self.title!r} holds two {name} "
                    f"at one sequence")
            object.__setattr__(
                self, name,
                tuple(sorted(items, key=lambda item: item.seq)))
        words = [term.term for term in self.terms]
        if len(set(words)) != len(words):
            raise ValueError(
                f"book {self.title!r} holds two lexicon "
                f"entries for one term - the lexicon speaks "
                f"for a term once, or not at all")
        object.__setattr__(
            self, "watched", tuple(
                normalize_term(word) for word in self.watched))
        views = tuple(self.views)
        view_ids = [view.view_id for view in views]
        if len(set(view_ids)) != len(view_ids):
            raise ValueError(
                f"book {self.title!r} holds two views "
                f"under one id")
        object.__setattr__(
            self, "views",
            tuple(sorted(views, key=lambda view: view.seq)))
        object.__setattr__(self, "panels", tuple(self.panels))
        _judge_book_panels(self)

    def items(self) -> Tuple[Any, ...]:
        return (self.reports + self.approvals
                + self.standups + self.terms)

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(item.item_id for item in self.items())

    def report_ids(self) -> Tuple[str, ...]:
        return tuple(item.report_id for item in self.reports)

    def approval_ids(self) -> Tuple[str, ...]:
        return tuple(item.approval_id for item in self.approvals)

    def standup_ids(self) -> Tuple[str, ...]:
        return tuple(item.standup_id for item in self.standups)

    def term_ids(self) -> Tuple[str, ...]:
        return tuple(item.term_id for item in self.terms)

    def terms_map(self) -> Dict[str, str]:
        return {term.term: term.plain for term in self.terms}

    def item_for(self, item_id: Any) -> Any:
        wanted = _check_word(item_id, "an item id")
        for item in self.items():
            if item.item_id == wanted:
                return item
        raise KeyError(
            f"no item named {wanted!r} in this book")

    def report_for(self, report_id: Any) -> SkinReport:
        wanted = _check_word(report_id, "a report id")
        for item in self.reports:
            if item.report_id == wanted:
                return item
        raise KeyError(f"no report named {wanted!r} in this book")

    def approval_for(self, approval_id: Any) -> SkinApproval:
        wanted = _check_word(approval_id, "an approval id")
        for item in self.approvals:
            if item.approval_id == wanted:
                return item
        raise KeyError(
            f"no approval named {wanted!r} in this book")

    def standup_for(self, standup_id: Any) -> SkinStandup:
        wanted = _check_word(standup_id, "a stand-up id")
        for item in self.standups:
            if item.standup_id == wanted:
                return item
        raise KeyError(
            f"no stand-up named {wanted!r} in this book")

    def term_for(self, term_id: Any) -> SkinTerm:
        wanted = _check_word(term_id, "a term id")
        for item in self.terms:
            if item.term_id == wanted:
                return item
        raise KeyError(f"no term named {wanted!r} in this book")

    def view_for(self, view_id: Any) -> SkinView:
        wanted = _check_word(view_id, "a view id")
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no view named {wanted!r} in this book")

    def to_record(self) -> Dict[str, Any]:
        return _book_record(self)


def _judge_book_panels(book: SkinBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _strip_derived(raw: Dict[str, Any],
                     record: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(raw)
    for key in ("type", "slice", "passes", "segment", "misses"):
        merged.pop(key, None)
    return merged


def validate_book(data: Any, *, require_example: bool = False
                  ) -> SkinBook:
    """Judge one whole skin book from its file shape."""
    if isinstance(data, SkinBook):
        book = data
    else:
        if not isinstance(data, dict):
            raise ValueError("a skin book must be a mapping")
        unknown = sorted(set(data) - _SKIN_KEYS)
        if unknown:
            raise ValueError(
                f"a skin book names unknown fields {unknown}")
        if data.get("schema") != PLAIN_LANGUAGE_SKIN_SCHEMA:
            raise ValueError(
                f"a skin book names schema "
                f"{data.get('schema')!r}, not "
                f"{PLAIN_LANGUAGE_SKIN_SCHEMA!r}")
        if data.get("slice") != PLAIN_LANGUAGE_SKIN_SLICE:
            raise ValueError(
                f"a skin book names slice {data.get('slice')!r}, "
                f"not {PLAIN_LANGUAGE_SKIN_SLICE!r}")
        guide = data.get("guide") or {}
        if not isinstance(guide, dict):
            raise ValueError("a skin book's guide must be a mapping")
        guide_unknown = sorted(set(guide) - _BOOK_KEYS)
        if guide_unknown:
            raise ValueError(
                f"a skin book's guide names unknown fields "
                f"{guide_unknown}")
        book = SkinBook(
            title=_check_title(_pick_any(
                guide, ("title", "name"), "a book title"),
                "a book title"),
            reports=tuple(build_report(item)
                          for item in data.get("reports", ())),
            approvals=tuple(build_approval(item)
                            for item in data.get("approvals", ())),
            standups=tuple(build_standup(item)
                           for item in data.get("standups", ())),
            terms=tuple(build_term(item)
                        for item in data.get("terms", ())),
            watched=tuple(data.get("watched", ())),
            views=tuple(build_view(item)
                        for item in data.get("views", ())),
            panels=tuple(_check_panel_ref(item)
                         for item in data.get("panels", ())))
        _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def _check_example(book: SkinBook) -> None:
    if book.title != _EXAMPLE_TITLE:
        raise ValueError(
            f"the shipped example book is titled "
            f"{_EXAMPLE_TITLE!r}, not {book.title!r}")
    if book.report_ids() != _EXAMPLE_REPORT_IDS:
        raise ValueError("the shipped example reports differ")
    if book.approval_ids() != _EXAMPLE_APPROVAL_IDS:
        raise ValueError("the shipped example approvals differ")
    if book.standup_ids() != _EXAMPLE_STANDUP_IDS:
        raise ValueError("the shipped example stand-ups differ")
    if book.term_ids() != _EXAMPLE_TERM_IDS:
        raise ValueError("the shipped example terms differ")
    if book.watched != _EXAMPLE_WATCHED:
        raise ValueError("the shipped example watched terms differ")
    if tuple(view.view_id for view in book.views) != _EXAMPLE_VIEW_IDS:
        raise ValueError("the shipped example views differ")
    if tuple(panel.panel_id for panel in book.panels) != (
            _EXAMPLE_PANEL_ID,):
        raise ValueError("the shipped example panel differs")


def build_book(book: Any = None, **kwargs: Any) -> SkinBook:
    """Build one book from a mapping or field words."""
    if kwargs:
        if book is not None:
            raise ValueError("build_book takes a mapping or fields")
        fields = kwargs
        return SkinBook(
            title=fields["title"],
            reports=tuple(build_report(item)
                          for item in fields.get("reports", ())),
            approvals=tuple(build_approval(item)
                            for item in fields.get("approvals", ())),
            standups=tuple(build_standup(item)
                           for item in fields.get("standups", ())),
            terms=tuple(build_term(item)
                        for item in fields.get("terms", ())),
            watched=tuple(fields.get("watched", ())),
            views=tuple(build_view(item)
                        for item in fields.get("views", ())),
            panels=tuple(_check_panel_ref(item)
                         for item in fields.get("panels", ())))
    return validate_book(book)


def _book_from(data: Any, *, require_example: bool) -> SkinBook:
    return validate_book(data, require_example=require_example)


def load_plain_language_skin(
        data: Optional[Dict[str, Any]] = None) -> SkinBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(PLAIN_LANGUAGE_SKIN_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_plain_language_skin_file(path: Any) -> SkinBook:
    """Load one skin file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: skin items and views held one by one.
# ---------------------------------------------------------------------


class SkinRegistry:
    """An in-memory holding of skin items and views.

    The registry is the pure layer's model of a
    session's skin book: reports, approvals,
    stand-ups and terms are held under their ids,
    one item per id and per sequence within its
    kind, one lexicon entry per term, and views are
    held in recorded order, one view per sequence
    and per id. The watched terms are held as the
    session's watch list when a book is registered
    whole. Holding is data only - nothing held here
    renders aloud, approves anything, or sends
    anything.
    """

    def __init__(self, book: Any = None) -> None:
        self._reports: List[SkinReport] = []
        self._approvals: List[SkinApproval] = []
        self._standups: List[SkinStandup] = []
        self._terms: List[SkinTerm] = []
        self._views: List[SkinView] = []
        self._watched: List[str] = []
        self._title: Optional[str] = None
        if book is not None:
            self.register_book(book)

    def title(self) -> Optional[str]:
        return self._title

    def watched(self) -> Tuple[str, ...]:
        return tuple(self._watched)

    def _fresh_view_id(self, held_ids: Any) -> str:
        n = 1
        while f"view-{n}" in held_ids:
            n += 1
        return f"view-{n}"

    def _register(self, held: List[Any], item: Any,
                  id_attr: str, what: str) -> Any:
        for other in held:
            if getattr(other, id_attr) == getattr(item, id_attr):
                raise ValueError(
                    f"a {what} already stands under id "
                    f"{getattr(item, id_attr)!r}")
            if other.seq == item.seq:
                raise ValueError(
                    f"a {what} already stands at sequence "
                    f"{item.seq}")
        held.append(item)
        held.sort(key=lambda held_item: held_item.seq)
        return item

    def register_report(self, item: Any) -> SkinReport:
        """Hold one report, judged whole before held."""
        return self._register(
            self._reports, _check_report_ref(item),
            "report_id", "report")

    def register_approval(self, item: Any) -> SkinApproval:
        """Hold one approval, judged whole before held."""
        return self._register(
            self._approvals, _check_approval_ref(item),
            "approval_id", "approval")

    def register_standup(self, item: Any) -> SkinStandup:
        """Hold one stand-up, judged whole before held."""
        return self._register(
            self._standups, _check_standup_ref(item),
            "standup_id", "stand-up")

    def register_term(self, item: Any) -> SkinTerm:
        """Hold one lexicon term; a second entry for
        one term refuses, as the book refuses it."""
        checked = _check_term_ref(item)
        for held in self._terms:
            if held.term == checked.term:
                raise ValueError(
                    f"a lexicon entry already stands for "
                    f"term {checked.term!r}")
        return self._register(
            self._terms, checked, "term_id", "term")

    def register_view(self, view: Any) -> SkinView:
        """Hold one view, under a fresh view-N id when
        it names none."""
        if isinstance(view, dict) and not view.get(
                "view_id", view.get("id")):
            view = dict(view)
            view["view_id"] = self._fresh_view_id(
                {held.view_id for held in self._views})
        checked = _check_view_ref(view)
        return self._register(
            self._views, checked, "view_id", "view")

    def register_book(self, book: Any) -> SkinBook:
        """Hold one whole book; a second title refuses."""
        checked = validate_book(book)
        if self._title is not None and self._title != checked.title:
            raise ValueError(
                f"a book already stands here under title "
                f"{self._title!r}")
        for item in checked.reports:
            self.register_report(item)
        for item in checked.approvals:
            self.register_approval(item)
        for item in checked.standups:
            self.register_standup(item)
        for item in checked.terms:
            self.register_term(item)
        for view in checked.views:
            self.register_view(view)
        self._watched = list(checked.watched)
        self._title = checked.title
        return self.book()

    def book(self) -> SkinBook:
        """The held book, composed from what stands held."""
        return SkinBook(
            title=self._title or "An unheld skin book",
            reports=tuple(self._reports),
            approvals=tuple(self._approvals),
            standups=tuple(self._standups),
            terms=tuple(self._terms),
            watched=tuple(self._watched),
            views=tuple(self._views), panels=())

    def list_reports(self) -> Tuple[SkinReport, ...]:
        return tuple(self._reports)

    def list_approvals(self) -> Tuple[SkinApproval, ...]:
        return tuple(self._approvals)

    def list_standups(self) -> Tuple[SkinStandup, ...]:
        return tuple(self._standups)

    def list_terms(self) -> Tuple[SkinTerm, ...]:
        return tuple(self._terms)

    def list_views(self) -> Tuple[SkinView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return (tuple(self._reports) + tuple(self._approvals)
                + tuple(self._standups) + tuple(self._terms))

    def get_report(self, report_id: Any) -> SkinReport:
        wanted = _check_word(report_id, "a report id")
        for item in self._reports:
            if item.report_id == wanted:
                return item
        raise KeyError(f"no report named {wanted!r} stands held")

    def get_approval(self, approval_id: Any) -> SkinApproval:
        wanted = _check_word(approval_id, "an approval id")
        for item in self._approvals:
            if item.approval_id == wanted:
                return item
        raise KeyError(f"no approval named {wanted!r} stands held")

    def get_standup(self, standup_id: Any) -> SkinStandup:
        wanted = _check_word(standup_id, "a stand-up id")
        for item in self._standups:
            if item.standup_id == wanted:
                return item
        raise KeyError(f"no stand-up named {wanted!r} stands held")

    def get_term(self, term_id: Any) -> SkinTerm:
        wanted = _check_word(term_id, "a term id")
        for item in self._terms:
            if item.term_id == wanted:
                return item
        raise KeyError(f"no term named {wanted!r} stands held")

    def get_view(self, view_id: Any) -> SkinView:
        wanted = _check_word(view_id, "a view id")
        for view in self._views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no view named {wanted!r} stands held")

    def get_item(self, item_id: Any) -> Any:
        wanted = _check_word(item_id, "an item id")
        for item in self.list_items():
            if item.item_id == wanted:
                return item
        raise KeyError(f"no item named {wanted!r} stands held")


# ---------------------------------------------------------------------
# Records: items and views shaped as session news.
# ---------------------------------------------------------------------


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {
        "detail": item.detail, "recorded_on": item.recorded_on,
        "actor": item.actor, "source": item.source,
        "origin_session": item.origin_session}


def _report_record(report: SkinReport,
                     source: Any = None) -> Dict[str, Any]:
    record = {
        "type": "plain_language_report",
        "slice": PLAIN_LANGUAGE_SKIN_SLICE,
        "report_id": report.report_id, "seq": report.seq,
        "kind": "report", "title": report.title,
        "lines": list(report.lines), "action": report.action,
        "misses": list(item_misses(report, source)),
        "passes": item_passes(report, source),
        "segment": segment_of(report, source)}
    record.update(_provenance_record(report))
    return record


def _approval_record(approval: SkinApproval,
                       source: Any = None) -> Dict[str, Any]:
    record = {
        "type": "plain_language_approval",
        "slice": PLAIN_LANGUAGE_SKIN_SLICE,
        "approval_id": approval.approval_id, "seq": approval.seq,
        "kind": "approval", "title": approval.title,
        "ask": approval.ask, "action": approval.action,
        "lines": list(approval.lines),
        "misses": list(item_misses(approval, source)),
        "passes": item_passes(approval, source),
        "segment": segment_of(approval, source)}
    record.update(_provenance_record(approval))
    return record


def _standup_record(standup: SkinStandup,
                      source: Any = None) -> Dict[str, Any]:
    record = {
        "type": "plain_language_standup",
        "slice": PLAIN_LANGUAGE_SKIN_SLICE,
        "standup_id": standup.standup_id, "seq": standup.seq,
        "kind": "standup", "person": standup.person,
        "done": list(standup.done), "doing": list(standup.doing),
        "blocked": list(standup.blocked),
        "misses": list(item_misses(standup, source)),
        "passes": item_passes(standup, source),
        "segment": segment_of(standup, source)}
    record.update(_provenance_record(standup))
    return record


def _term_record(term: SkinTerm) -> Dict[str, Any]:
    record = {
        "type": "plain_language_term",
        "slice": PLAIN_LANGUAGE_SKIN_SLICE,
        "term_id": term.term_id, "seq": term.seq,
        "kind": "term", "term": term.term, "plain": term.plain,
        "passes": True, "segment": segment_of(term)}
    record.update(_provenance_record(term))
    return record


def _view_record(view: SkinView) -> Dict[str, Any]:
    record = {
        "type": "plain_language_view",
        "slice": PLAIN_LANGUAGE_SKIN_SLICE,
        "view_id": view.view_id, "seq": view.seq,
        "kind_filter": view.kind_filter}
    record.update(_provenance_record(view))
    return record


def _panel_record(panel: SkinPanel) -> Dict[str, Any]:
    return {
        "type": "plain_language_panel",
        "slice": PLAIN_LANGUAGE_SKIN_SLICE,
        "panel_id": panel.panel_id, "view_id": panel.view_id,
        "kind_filter": panel.kind_filter,
        "rows": [row.to_record() for row in panel.rows],
        "total_items": panel.total_items,
        "total_shown": panel.total_shown,
        "kind_counts": [count.to_record()
                        for count in panel.kind_counts],
        "as_of": panel.as_of, "account": list(panel.account)}


def _verdict_record(verdict: SkinVerdict) -> Dict[str, Any]:
    return {
        "type": "plain_language_verdict",
        "slice": PLAIN_LANGUAGE_SKIN_SLICE,
        "total_items": verdict.total_items,
        "total_shown": verdict.total_shown,
        "passing_shown": verdict.passing_shown,
        "distinct_kinds": verdict.distinct_kinds,
        "earliest_on": verdict.earliest_on,
        "latest_on": verdict.latest_on,
        "verdict": verdict.verdict}


def _rendering_record(rendering: SkinRendering) -> Dict[str, Any]:
    return {
        "type": "plain_language_rendering",
        "slice": PLAIN_LANGUAGE_SKIN_SLICE,
        "item_id": rendering.item_id, "kind": rendering.kind,
        "register": rendering.register,
        "shown": list(rendering.shown),
        "folded": list(rendering.folded),
        "misses": list(rendering.misses),
        "action": rendering.action}


def report_record(report: Any, source: Any = None) -> Dict[str, Any]:
    """One report as its session-news record."""
    return _report_record(_check_report_ref(report), source)


def approval_record(approval: Any,
                      source: Any = None) -> Dict[str, Any]:
    """One approval as its session-news record."""
    return _approval_record(_check_approval_ref(approval), source)


def standup_record(standup: Any,
                     source: Any = None) -> Dict[str, Any]:
    """One stand-up as its session-news record."""
    return _standup_record(_check_standup_ref(standup), source)


def term_record(term: Any) -> Dict[str, Any]:
    """One lexicon term as its session-news record."""
    return _term_record(_check_term_ref(term))


def item_record(item: Any, source: Any = None) -> Dict[str, Any]:
    """One item of any kind as its session-news record."""
    checked = _check_item_ref(item)
    if isinstance(checked, SkinReport):
        return _report_record(checked, source)
    if isinstance(checked, SkinApproval):
        return _approval_record(checked, source)
    if isinstance(checked, SkinStandup):
        return _standup_record(checked, source)
    return _term_record(checked)


def view_record(view: Any) -> Dict[str, Any]:
    """One view as its session-news record."""
    return _view_record(_check_view_ref(view))


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    """One panel as its session-news record."""
    return _panel_record(validate_panel(panel, source))


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    """One verdict as its session-news record."""
    return _verdict_record(validate_verdict(verdict, source, view))


def rendering_record(rendering: Any) -> Dict[str, Any]:
    """One rendering as a plain record."""
    if not isinstance(rendering, SkinRendering):
        raise ValueError("a rendering record takes one rendering")
    return _rendering_record(rendering)


def _book_record(book: SkinBook) -> Dict[str, Any]:
    return {
        "type": "plain_language_book",
        "slice": PLAIN_LANGUAGE_SKIN_SLICE,
        "title": book.title,
        "reports": [_report_record(item, book)
                    for item in book.reports],
        "approvals": [_approval_record(item, book)
                      for item in book.approvals],
        "standups": [_standup_record(item, book)
                     for item in book.standups],
        "terms": [_term_record(item) for item in book.terms],
        "watched": list(book.watched),
        "views": [_view_record(view) for view in book.views],
        "panels": [_panel_record(panel) for panel in book.panels]}


def book_record(book: Any) -> Dict[str, Any]:
    """One whole book as its session-news record."""
    return _book_record(validate_book(book))


def _source_book(source: Any) -> SkinBook:
    if source is None:
        return load_plain_language_skin()
    if isinstance(source, SkinBook):
        return source
    if isinstance(source, SkinRegistry):
        return source.book()
    return validate_book(source)


# ---------------------------------------------------------------------
# Plain words: one item told in Jarl mode.
# ---------------------------------------------------------------------


def plain_words(item: Any, source: Any = None) -> str:
    """One item told plainly: its first plain line."""
    checked = _check_item_ref(item)
    return plain_lines(checked, source)[0]


def report_plain_words(report: Any, source: Any = None) -> str:
    checked = _check_report_ref(report)
    return (f"Report '{checked.title}': "
            f"{plain_lines(checked, source)[0]}")


def approval_plain_words(approval: Any,
                           source: Any = None) -> str:
    """An approval told plainly: the plain ask and
    the one action it turns on, both derived."""
    checked = _check_approval_ref(approval)
    ask = translate_text(checked.ask, source)
    action = translate_text(checked.action, source)
    return f"Approval asks plainly: {ask} The one action: {action}."


def standup_plain_words(standup: Any, source: Any = None) -> str:
    checked = _check_standup_ref(standup)
    doing = translate_text(checked.doing[0], source)
    return f"{checked.person} is doing: {doing}"


def term_plain_words(term: Any) -> str:
    checked = _check_term_ref(term)
    return f"{checked.term} in plain words: {checked.plain}"


def panel_plain_words(source: Any, view: Any = None) -> str:
    book = _source_book(source)
    panel = derive_panel(book, view)
    return (f"The panel shows {panel.total_shown} of "
            f"{panel.total_items} items for kind "
            f"'{panel.kind_filter}'.")


def verdict_plain_words(source: Any, view: Any = None) -> str:
    book = _source_book(source)
    verdict = derive_verdict(book, view)
    return (f"The book stands {verdict.verdict}: "
            f"{verdict.passing_shown} of {verdict.total_shown} "
            f"shown items stand whole.")


def view_plain_words(view: Any) -> str:
    checked = _check_view_ref(view)
    return f"View {checked.view_id} shows kind '{checked.kind_filter}'."


# ---------------------------------------------------------------------
# Formatters: the surfaces the /skin roads speak.
# ---------------------------------------------------------------------


def format_report(report: Any, source: Any = None) -> str:
    checked = _check_report_ref(report)
    rendering = render_item(checked, source)
    lines = [
        f"Report: {checked.report_id} - {checked.title}",
        f"In plain words: {rendering.shown[0]}",
    ]
    lines.extend(f"  {line}" for line in rendering.shown)
    if rendering.action is not None:
        lines.append(
            f"Next step: {translate_text(rendering.action, source)}")
    lines.append(f"Detail: {checked.detail}")
    return "\n".join(lines)


def format_approval(approval: Any, source: Any = None) -> str:
    checked = _check_approval_ref(approval)
    lines = [
        f"Approval: {checked.approval_id} - {checked.title}",
        f"Ask: {translate_text(checked.ask, source)}",
        f"The one action: {translate_text(checked.action, source)}",
    ]
    lines.extend(
        f"  {translate_text(line, source)}" for line in checked.lines)
    lines.append(f"Detail: {checked.detail}")
    return "\n".join(lines)


def format_standup(standup: Any, source: Any = None) -> str:
    checked = _check_standup_ref(standup)
    lines = [f"Stand-up: {checked.standup_id} - {checked.person}"]
    lines.extend(f"Done: {translate_text(line, source)}"
                 for line in checked.done)
    lines.extend(f"Doing: {translate_text(line, source)}"
                 for line in checked.doing)
    lines.extend(f"Blocked: {translate_text(line, source)}"
                 for line in checked.blocked)
    lines.append(f"Detail: {checked.detail}")
    return "\n".join(lines)


def format_term(term: Any) -> str:
    checked = _check_term_ref(term)
    return "\n".join([
        f"Term: {checked.term_id} - {checked.term}",
        f"In plain words: {checked.plain}",
        f"Detail: {checked.detail}"])


def format_view(view: Any) -> str:
    checked = _check_view_ref(view)
    return "\n".join([
        f"View: {checked.view_id}",
        f"Shows kind '{checked.kind_filter}'.",
        f"Detail: {checked.detail}"])


def format_rendering(rendering: Any) -> str:
    """One rendering spoken: the shown lines, and
    the folded detail named as folded while any
    stands folded - present, counted, and one
    unfold away, never silently dropped."""
    if not isinstance(rendering, SkinRendering):
        raise ValueError("format_rendering takes one rendering")
    lines = [
        f"Rendering: {rendering.item_id} "
        f"in the {rendering.register} register"]
    lines.extend(f"  {line}" for line in rendering.shown)
    if rendering.action is not None:
        lines.append(f"The one action: {rendering.action}")
    if rendering.folded:
        lines.append(
            f"Folded detail: {len(rendering.folded)} technical "
            f"line(s) stand folded - {UNFOLD_ACTION} unfolds them.")
    if rendering.misses:
        lines.append(
            f"Misses: {', '.join(rendering.misses)} stand with "
            f"no plain words in the lexicon, unchanged.")
    return "\n".join(lines)


def format_book(source: Any = None, kind: Any = None) -> str:
    book = _source_book(source)
    items = (book.items() if kind is None
             else items_for_kind(book, kind))
    lines = [f"Book: {book.title} ({len(items)} items)"]
    lines.extend(f"  {segment_of(item, book)}" for item in items)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    book = _source_book(source)
    panel = derive_panel(book, view)
    lines = [
        f"Panel in {book.title}",
        f"View: {panel.view_id} - kind '{panel.kind_filter}' - "
        f"{panel.total_shown} of {panel.total_items} items show.",
    ]
    lines.extend(f"  {row.segment}" for row in panel.rows)
    lines.extend(f"  {line}" for line in panel.account)
    return "\n".join(lines)


def format_verdict(source: Any = None, view: Any = None) -> str:
    book = _source_book(source)
    verdict = derive_verdict(book, view)
    return "\n".join([
        f"Verdict in {book.title}",
        f"Verdict: {verdict.verdict} - {verdict.passing_shown} "
        f"of {verdict.total_shown} shown items stand whole."])


def format_plain_language_skin_screen(source: Any = None) -> str:
    """The whole plain-language screen for one book."""
    book = _source_book(source)
    view = _default_view(book)
    panel = derive_panel(book, view)
    verdict = derive_verdict(book, view)
    register = derive_register(source)
    lines = [
        f"The Plain-Language Skin (M-182) - {book.title}",
        format_book(book),
        f"Register: {register} - Jarl mode speaks plain "
        f"everyday words with the technical detail folded "
        f"behind the {UNFOLD_ACTION} keypress; the technical "
        f"register folds nothing.",
        f"Panel: {panel.total_shown} of {panel.total_items} "
        f"items show for kind {panel.kind_filter!r}.",
        f"Verdict: {verdict.verdict}.",
        f"Lexicon misses: "
        f"{', '.join(lexicon_misses(book)) or 'none'}.",
        "This layer renders words only - it approves "
        "nothing, sends nothing, and invents no plain "
        "words: the plain line is the technical line "
        "spoken through the lexicon, same facts, "
        "plainer words.",
    ]
    return "\n".join(lines)


def parse_plain_language_skin_args(args: Any) -> Tuple[str, Any]:
    """Parse the /skin grammar into (action, target).

    ``""``/``show``/``list`` show the book;
    ``report <report-id>`` shows one report whole;
    ``approval <approval-id>`` shows one approval;
    ``standup <standup-id>`` shows one stand-up;
    ``term <term-id>`` shows one lexicon term;
    ``view <view-id>`` shows one held view record;
    ``kind <kind>`` shows one kind's items;
    ``panel`` and ``verdict`` show the derived panel
    and verdict under the book's own view;
    ``unfold <item-id>`` stands for the unfold
    keypress on one item; ``register`` names the
    register the session stands in. Anything else
    raises ValueError carrying the usage line.
    """
    if args is None:
        return ("show", None)
    if not isinstance(args, str):
        raise ValueError(USAGE)
    parts = args.split()
    if not parts or parts == ["show"] or parts == ["list"]:
        return ("show", None)
    if parts[0] == "report" and len(parts) == 2:
        return ("report", _check_word(parts[1], "a report id"))
    if parts[0] == "approval" and len(parts) == 2:
        return ("approval", _check_word(parts[1], "an approval id"))
    if parts[0] == "standup" and len(parts) == 2:
        return ("standup", _check_word(parts[1], "a stand-up id"))
    if parts[0] == "term" and len(parts) == 2:
        return ("term", _check_word(parts[1], "a term id"))
    if parts[0] == "view" and len(parts) == 2:
        return ("view", _check_word(parts[1], "a view id"))
    if parts[0] == "kind" and len(parts) == 2:
        try:
            return ("kind", normalize_kind(parts[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if parts == ["panel"]:
        return ("panel", None)
    if parts == ["verdict"]:
        return ("verdict", None)
    if parts[0] == UNFOLD_ACTION and len(parts) == 2:
        return (UNFOLD_ACTION, _check_word(parts[1], "an item id"))
    if parts == ["register"]:
        return ("register", None)
    raise ValueError(USAGE)
