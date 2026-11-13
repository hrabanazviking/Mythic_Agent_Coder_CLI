"""Streaming Work View (All-Features roadmap slice M-172).

Part VIII - The Beautiful Face - builds here. The
roadmap's words: *the coder's actions stream as a
calm narrative (reading..., editing ``auth.py``...,
running tests...) with tool detail one keystroke
away, never in the face.*

What already ships, and what this slice adds:

* The main chat screen and the terminal loop both
  stream tool work as machinery first and narrative
  second - the M-171 TUI redesign charter judged
  both screens REPAIR on exactly that count (its
  S-03 and S-08 rows, both naming M-172 as an
  owning slice): stream the work as a calm
  narrative with tool detail one keystroke away,
  and let errors and states travel as words. The
  live tool roads already know what the coder did;
  until this slice, nothing held the stream of
  actions as a judged whole, in narrative words.
* This slice is that stream, as a pure layer: one
  work event validated as data WITH ITS
  PROVENANCE WHOLE - the action it stands for,
  named by its event id alone in the stream; its
  kind in the closed kind set; the target it
  touches; the tool that carries it; the tool
  detail it holds back; its state - started, done
  or failed - and the day it happened, who acted,
  its source and the session it happened in. What
  the user reads is never stored loose: the
  NARRATIVE line is DERIVED from the event's kind,
  target and state - a started action speaks in
  the present with an ellipsis, a done action in
  the past, a failed action as a could-not - and
  the tool detail NEVER crosses into the
  narrative, the panel or the verdict: it is
  shown only on the detail road, one keystroke
  away. The work PANEL is derived from the whole
  book (its rows the events in stream order, its
  totals the events' own counts, its current
  event the last action still standing started),
  and a work VERDICT is derived for the whole
  book. An event is composed BY IMPORT from a
  shipped tool call - the shipped tool schemas'
  own tool names judged onto the kind set - the
  tool's own words never crossing beyond the
  detail the event holds back. The shipped data
  file (``mythic_agent/data/work_view.yaml``)
  holds one example book in exactly the shape a
  real book file takes, a loader reads a book
  file anywhere on disk, events are shaped as
  session news, and a small in-memory registry
  model holds events one by one. The agent layer
  owns holding a book for a session and raising
  an event over a live tool action.

Honesty rules, enforced here and pinned by tests:

* **The narrative is derived, never chosen.** An
  event's line is read off its kind, its target
  and its state alone. A stored narrative naming
  anything else refuses, and no field of an event
  may smuggle a chosen line in.
* **Detail stays behind the keystroke.** The
  narrative formatters, the panel, the verdict
  and the default screen carry no tool detail at
  all; the detail stands only in the event's own
  held record and on the detail road that names
  it. What the stream shows by default is the
  calm line and the state as words - colour is
  never the only signal, because there is no
  colour in this layer at all.
* **Kinds are judged from shipped tools.** An
  event raised over a tool call takes its kind
  from the shipped tool's own name, read onto
  the closed kind set; a tool the set does not
  know refuses plainly rather than inventing a
  kind.
* **The stream stands in order.** A book holds
  its events in stream order - sequence numbers
  strictly ascending, one event per id and per
  sequence - so the narrative can never fork or
  run backwards.
* **Data only.** This layer holds actions as
  data: it runs no tool, streams nothing live,
  sends nothing, posts nothing, schedules
  nothing, calls no model and persists nothing -
  an event held here is a record of work, never
  the work itself.
"""

from __future__ import annotations

__all__ = [
    "KINDS",
    "PLAIN_EXPLANATION",
    "STATES",
    "TOOL_KINDS",
    "USAGE",
    "VERDICT_WORDS",
    "WORK_VIEW_RESOURCE",
    "WORK_VIEW_SCHEMA",
    "WORK_VIEW_SLICE",
    "Any",
    "Dict",
    "KindCount",
    "List",
    "Optional",
    "STREAMING_WORK_VIEW_SLICE",
    "Tuple",
    "WorkBook",
    "WorkEvent",
    "WorkPanel",
    "WorkPanelRow",
    "WorkRegistry",
    "WorkVerdict",
    "book_record",
    "build_book",
    "build_event",
    "build_panel",
    "build_row",
    "build_verdict",
    "derive_panel",
    "derive_verdict",
    "detail_of",
    "detail_plain_words",
    "event_from_tool_call",
    "event_record",
    "events_of_kind",
    "format_event",
    "format_event_detail",
    "format_panel",
    "format_stream",
    "format_verdict",
    "format_work_view_screen",
    "inspect_action_source",
    "kind_for_tool",
    "load_work_view",
    "load_work_view_file",
    "narrative_of",
    "normalize_kind",
    "normalize_state",
    "panel_plain_words",
    "panel_record",
    "parse_work_view_args",
    "plain_words",
    "total_events",
    "validate_book",
    "validate_event",
    "validate_panel",
    "validate_row",
    "validate_verdict",
    "verdict_plain_words",
    "verdict_record",
]

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .crew_members import normalize_member_id
from .validation import ValidationError

WORK_VIEW_SLICE = "M-172"

#: The longer name other layers cite for this slice.
STREAMING_WORK_VIEW_SLICE = WORK_VIEW_SLICE

WORK_VIEW_RESOURCE = "work_view.yaml"

WORK_VIEW_SCHEMA = "mythic.work_view/1"

#: The kinds one coder action may stand as, in
#: panel order: taking in, changing, searching,
#: proving, running, and the quiet kinds.
KINDS = (
    "reading", "editing", "writing", "searching",
    "running-tests", "running-command", "checking",
    "thinking")

_KIND_ALIASES = {
    "reading": "reading", "read": "reading",
    "editing": "editing", "edit": "editing",
    "writing": "writing", "write": "writing",
    "searching": "searching", "search": "searching",
    "running-tests": "running-tests",
    "running_tests": "running-tests",
    "tests": "running-tests", "test": "running-tests",
    "running-command": "running-command",
    "running_command": "running-command",
    "command": "running-command",
    "checking": "checking", "check": "checking",
    "thinking": "thinking", "think": "thinking",
}

#: The states one action may stand in: begun,
#: finished, or failed - always as words.
STATES = ("started", "done", "failed")

_STATE_ALIASES = {
    "started": "started", "start": "started",
    "running": "started", "in-progress": "started",
    "done": "done", "finished": "done",
    "complete": "done", "passed": "done",
    "failed": "failed", "fail": "failed",
    "error": "failed", "errored": "failed",
}

#: The words a whole book's work verdict may
#: carry: troubled while any action stands
#: failed, working while any action still stands
#: started, calm while every action stands done.
VERDICT_WORDS = ("calm", "working", "troubled")

#: The shipped tools judged onto the kind set:
#: each name is a tool the shipped tool schemas
#: themselves declare, and its kind is the action
#: that tool performs. run_command is judged by
#: its command text at the raising road (a test
#: run is running-tests, anything else is
#: running-command) and stands here as its plain
#: reading.
TOOL_KINDS = {
    "read_file": "reading",
    "list_dir": "reading",
    "replace_file_content": "editing",
    "core_memory_replace": "editing",
    "write_file": "writing",
    "core_memory_append": "writing",
    "archival_memory_insert": "writing",
    "send_message": "writing",
    "grep_search": "searching",
    "archival_memory_search": "searching",
    "knowledge_db_semantic_search": "searching",
    "knowledge_db_sql_query": "searching",
    "run_command": "running-command",
    "github_execute": "running-command",
    "delegate_task": "thinking",
    "delegate_parallel_tasks": "thinking",
    "update_status": "checking",
    "clear_context": "checking",
}

#: Narrative stems per kind: (infinitive, present,
#: past). The derived line is built from these
#: alone, so every event of one kind speaks the
#: same calm grammar.
_NARRATIVE_STEMS = {
    "reading": ("read", "reading", "read"),
    "editing": ("edit", "editing", "edited"),
    "writing": ("write", "writing", "wrote"),
    "searching": ("search for", "searching for", "searched for"),
    "running-tests": ("run the tests", "running tests", "ran the tests"),
    "running-command": ("run", "running", "ran"),
    "checking": ("check", "checking", "checked"),
    "thinking": ("think through", "thinking through", "thought through"),
}

#: Targets that name the test suite itself, for
#: which running-tests speaks without a suffix.
_GENERIC_TEST_TARGETS = ("tests", "the tests", "the test suite", "test suite")

_EVENT_KEYS = frozenset({
    "event_id", "id", "seq", "sequence", "order",
    "kind", "action", "target", "tool",
    "detail", "state", "status",
    "occurred_on", "day", "date",
    "actor", "by", "who", "source",
    "origin_session", "session"})

_ROW_KEYS = frozenset({
    "event_id", "id", "seq", "kind", "state",
    "narrative", "line", "target", "occurred_on"})

_KIND_COUNT_KEYS = frozenset({"kind", "items", "count"})

_PANEL_KEYS = frozenset({
    "panel_id", "id", "rows", "events",
    "total_events", "total", "total_done", "done",
    "total_started", "started", "total_failed",
    "failed", "distinct_targets", "targets",
    "kind_counts", "kinds", "current_event_id",
    "current", "as_of", "day", "account",
    "statements"})

_VERDICT_KEYS = frozenset({
    "total_events", "total", "total_done", "done",
    "total_started", "started", "total_failed",
    "failed", "distinct_targets", "targets",
    "earliest_on", "earliest", "latest_on",
    "latest", "verdict"})

_BOOK_KEYS = frozenset({"title", "name"})

_WORK_BOOK_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "canon_note", "guide", "events", "actions",
    "panels"})

_EXAMPLE_TITLE = "Streaming Work View at the M-171 slice boundary"

_EXAMPLE_EVENT_IDS = (
    "event-screens-read", "event-kindness-searched",
    "event-charter-data-written",
    "event-charter-module-edited",
    "event-charter-tests-run", "event-verdicts-checked")

_EXAMPLE_FIRST_EVENT_ID = "event-screens-read"

_EXAMPLE_FIRST_EVENT_TARGET = "mythic_agent/ui/screens/chat_screen.py"

_EXAMPLE_PANEL_ID = "panel-m171-boundary"

_EXAMPLE_AS_OF = "2026-11-09"

_EXAMPLE_PANEL_ROW_IDS = _EXAMPLE_EVENT_IDS

PLAIN_EXPLANATION = (
    "Streaming Work View: the coder's actions "
    "stream as a calm narrative - reading, "
    "editing a file, running tests - each action "
    "held as one event carrying its kind, its "
    "target, the tool that carries it, the tool "
    "detail it holds back, its state as words and "
    "its provenance whole. The narrative line is "
    "derived, never chosen: a started action "
    "speaks in the present with an ellipsis, a "
    "done action in the past, a failed action as "
    "a could-not - and the tool detail never "
    "crosses into the narrative, the panel or "
    "the verdict; it stands one keystroke away "
    "on the detail road alone. The work panel is "
    "derived from the whole book at call time, "
    "the work verdict is derived for the whole "
    "book, and an event raised over a tool call "
    "takes its kind from the shipped tool's own "
    "name. This layer holds actions as data "
    "only: it runs no tool, streams nothing "
    "live, sends nothing, posts nothing, "
    "schedules nothing, calls no model and "
    "persists nothing - an event held here is a "
    "record of work, never the work itself."
)

USAGE = (
    "Usage: /workview, /workview show, "
    "/workview event <event-id>, "
    "/workview detail [<event-id>], "
    "/workview kind <kind>, "
    "/workview panel, /workview verdict"
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
        raise ValueError(f"an event names two different {what}")
    return values[0]


def _check_count(value: Any, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{what} must be a count, got {value!r}")
    if value < 0:
        raise ValueError(f"{what} must not be negative, got {value!r}")
    return value


def _check_seq(value: Any) -> int:
    seq = _check_count(value, "an event's sequence")
    if seq < 1:
        raise ValueError(
            f"an event's sequence stands from 1, got {value!r}")
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
            % ("/".join(KINDS), value))
    return kind


def normalize_state(value: Any) -> str:
    """One state word, read onto the closed state set."""
    if not isinstance(value, str):
        raise ValueError(f"a state must be a word, got {value!r}")
    state = _STATE_ALIASES.get(value.strip().lower())
    if state is None:
        raise ValueError(
            "a state is one of %s, got %r"
            % ("/".join(STATES), value))
    return state


def _display_target(event: Any) -> str:
    """The target as the narrative speaks it.

    A file-like target (one word carrying a path
    or a dotted name) is spoken in backticks, as
    the roadmap's own example speaks ``auth.py``;
    a spoken target stands plain. A command target
    is always spoken in backticks - it is a command.
    """
    target = event.target
    if event.kind == "running-command":
        return f"`{target}`"
    if " " not in target and ("/" in target or "." in target):
        return f"`{target}`"
    return target


def narrative_of(event: Any) -> str:
    """The calm narrative line one event derives.

    Read off the event's kind, target and state
    alone: a started action speaks in the present
    with an ellipsis, a done action in the past,
    a failed action as a could-not. The tool and
    its detail never enter the line.
    """
    current = _check_event_ref(event)
    infinitive, present, past = _NARRATIVE_STEMS[current.kind]
    if current.kind == "running-tests":
        if current.target in _GENERIC_TEST_TARGETS:
            if current.state == "started":
                return f"{present}\u2026"
            if current.state == "done":
                return past
            return f"could not {infinitive}"
        shown = _display_target(current)
        if current.state == "started":
            return f"{present}: {shown}\u2026"
        if current.state == "done":
            return f"{past}: {shown}"
        return f"could not {infinitive}: {shown}"
    shown = _display_target(current)
    if current.state == "started":
        return f"{present} {shown}\u2026"
    if current.state == "done":
        return f"{past} {shown}"
    return f"could not {infinitive} {shown}"


def detail_of(event: Any) -> str:
    """The tool detail one event holds back.

    This is the one-keystroke-away road at the
    pure layer: the detail stands in the event's
    own held record and is spoken only here (and
    by the detail formatters built on it), never
    by the narrative, the panel or the verdict.
    """
    return _check_event_ref(event).detail


# ---------------------------------------------------------------------
# The event: one coder action, held whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class WorkEvent:
    """One coder action in the stream, held whole.

    ``kind`` is the action's kind in the closed
    kind set; ``target`` is what the action
    touches, in the target's own words; ``tool``
    is the shipped tool that carries it; ``detail``
    is the tool detail the narrative holds back;
    ``state`` is where the action stands, as a
    word. ``seq`` is the event's place in the
    stream, from 1. The provenance - the day it
    happened, who acted, its source and the
    session it happened in - rides whole. The
    narrative is never a field: it is derived by
    :func:`narrative_of` at call time.
    """

    seq: int
    kind: str
    target: str
    tool: str
    detail: str
    state: str
    occurred_on: str
    actor: str
    source: str
    origin_session: str
    event_id: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(self, "kind", normalize_kind(self.kind))
        object.__setattr__(
            self, "target", _check_title(self.target, "a target"))
        object.__setattr__(
            self, "tool", _check_word(self.tool, "a tool"))
        object.__setattr__(
            self, "detail",
            _check_long_text(self.detail, "the tool detail"))
        object.__setattr__(self, "state", normalize_state(self.state))
        object.__setattr__(
            self, "occurred_on", _check_day(self.occurred_on))
        object.__setattr__(
            self, "actor", _check_title(self.actor, "an actor"))
        object.__setattr__(
            self, "source", _check_title(self.source, "a source"))
        object.__setattr__(
            self, "origin_session",
            _check_word(self.origin_session, "an origin session"))
        if self.event_id is not None:
            object.__setattr__(
                self, "event_id",
                _check_word(self.event_id, "an event id"))

    @property
    def narrative(self) -> str:
        """The derived calm line of this event."""
        return narrative_of(self)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "work_view_event",
            "slice": WORK_VIEW_SLICE,
            "event_id": self.event_id,
            "seq": self.seq,
            "kind": self.kind,
            "target": self.target,
            "tool": self.tool,
            "detail": self.detail,
            "state": self.state,
            "narrative": self.narrative,
            "occurred_on": self.occurred_on,
            "actor": self.actor,
            "source": self.source,
            "origin_session": self.origin_session,
        }


def _check_event_ref(value: Any) -> WorkEvent:
    if isinstance(value, WorkEvent):
        return value
    return validate_event(value)


def validate_event(event: Any) -> WorkEvent:
    """Judge one event whole and return it as a WorkEvent.

    A mapping is read through its spellings: a
    derived key (``narrative``/``line``) refuses -
    the line is derived, never stored - as does
    any key the event does not carry, and two
    spellings naming two different values.
    """
    if isinstance(event, WorkEvent):
        return event
    if not isinstance(event, dict):
        raise ValueError(
            f"a work event must be a mapping, got {event!r}")
    unknown = set(event) - _EVENT_KEYS
    if unknown:
        raise ValueError(
            f"a work event carries unknown keys: "
            f"{sorted(unknown)}")
    if "type" in event or "slice" in event:
        raise ValueError("a work event is judged without its news keys")

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(event, spellings, what)
        if value is None:
            raise ValueError(f"a work event names no {what}")
        return value

    return WorkEvent(
        event_id=_pick_any(event, ("event_id", "id"), "event id"),
        seq=_needed(("seq", "sequence", "order"), "sequence"),
        kind=_needed(("kind", "action"), "kind"),
        target=_needed(("target",), "target"),
        tool=_needed(("tool",), "tool"),
        detail=_needed(("detail",), "tool detail"),
        state=_needed(("state", "status"), "state"),
        occurred_on=_needed(
            ("occurred_on", "day", "date"), "day it happened"),
        actor=_needed(("actor", "by", "who"), "actor"),
        source=_needed(("source",), "source"),
        origin_session=_needed(
            ("origin_session", "session"), "origin session"),
    )


def build_event(event: Any = None, **kwargs: Any) -> WorkEvent:
    """Build one event from a mapping, an event, or fields."""
    if kwargs:
        if event is not None:
            raise ValueError("an event is built one way at a time")
        event = kwargs
    return validate_event(event)


def kind_for_tool(tool: Any, target: Any = "",
                  detail: Any = "") -> str:
    """The kind a shipped tool's action derives.

    The tool is read off the shipped tool names
    judged onto the kind set; ``run_command``
    derives running-tests when its command text
    (the target, then the detail) names a test
    run, and running-command otherwise. A tool
    the set does not know refuses plainly.
    """
    name = _check_word(tool, "a tool")
    kind = TOOL_KINDS.get(name)
    if kind is None:
        raise ValueError(
            f"no kind stands judged for tool {name!r} - the "
            f"work view narrates only the shipped tools it "
            f"knows, and invents no kind for the rest")
    if name == "run_command":
        text = f"{target} {detail}".lower()
        if "pytest" in text or "unittest" in text or (
                "test" in text and "run" in text) or (
                "test" in text and "python" in text):
            return "running-tests"
        if text.strip().startswith("pytest") or " tests/" in text:
            return "running-tests"
    return kind


def event_from_tool_call(tool: Any = None, *,
                         target: Any, detail: Any,
                         state: Any = "done",
                         seq: Any,
                         occurred_on: Any = "2026-11-09",
                         actor: Any = "the coder",
                         source: Any = "work view",
                         origin_session: Any = "session-m172",
                         event_id: Any = None,
                         kind: Any = None) -> WorkEvent:
    """Raise one event over a shipped tool call, by import.

    The kind is DERIVED from the tool's own name
    by :func:`kind_for_tool` - a kind named here
    that disagrees with the derived one refuses.
    The tool's arguments and results never cross
    beyond the ``detail`` the event holds back:
    what the stream shows of this action is its
    derived narrative alone.
    """
    derived = kind_for_tool(tool, target, detail)
    if kind is not None and normalize_kind(kind) != derived:
        raise ValueError(
            f"a kind named for tool {tool!r} must be the "
            f"derived kind {derived!r}, got {kind!r} - the "
            f"kind is derived from the tool, never chosen")
    return WorkEvent(
        event_id=event_id, seq=seq, kind=derived,
        target=target, tool=tool, detail=detail,
        state=state, occurred_on=occurred_on, actor=actor,
        source=source, origin_session=origin_session)


def inspect_action_source(piece: Any) -> Dict[str, Any]:
    """Judge one raw action piece and name what it is.

    A piece shaped like a tool call - a mapping
    carrying a tool name (``tool``/``name``), a
    target (``target``/``path``/``command``) and a
    detail (``detail``/``result``/``args``) - is
    read onto the kind it derives, without holding
    it. Anything else is named not-an-action.
    """
    if not isinstance(piece, dict):
        return {"kind": None, "tool": None,
                "reason": "not a mapping - no action stands here"}
    tool = _pick_any(piece, ("tool", "name"), "tool")
    if tool is None:
        return {"kind": None, "tool": None,
                "reason": "no tool named - no action stands here"}
    target = _pick_any(
        piece, ("target", "path", "command"), "target")
    detail = _pick_any(
        piece, ("detail", "result", "args"), "tool detail")
    try:
        kind = kind_for_tool(
            tool, target or "", detail or "")
    except ValueError as exc:
        return {"kind": None, "tool": tool,
                "reason": str(exc)}
    return {"kind": kind, "tool": tool,
            "target": target, "reason": "a shipped tool action"}


# ---------------------------------------------------------------------
# The panel: the whole stream, derived at a glance.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class WorkPanelRow:
    """One event as the panel carries it: narrative only.

    The row carries the event's id, its place in
    the stream, its kind, its state as a word, its
    DERIVED narrative line, its target and its
    day. The tool and its detail never stand in a
    row - the panel is the calm face of the stream.
    """

    event_id: Optional[str]
    seq: int
    kind: str
    state: str
    narrative: str
    target: str
    occurred_on: str

    def __post_init__(self) -> None:
        if self.event_id is not None:
            object.__setattr__(
                self, "event_id",
                _check_word(self.event_id, "an event id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(self, "kind", normalize_kind(self.kind))
        object.__setattr__(self, "state", normalize_state(self.state))
        object.__setattr__(
            self, "narrative",
            _check_long_text(self.narrative, "a narrative line"))
        object.__setattr__(
            self, "target", _check_title(self.target, "a target"))
        object.__setattr__(
            self, "occurred_on", _check_day(self.occurred_on))

    def sort_key(self) -> Tuple[int, str]:
        return (self.seq, self.event_id or "")

    def to_record(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "seq": self.seq,
            "kind": self.kind,
            "state": self.state,
            "narrative": self.narrative,
            "target": self.target,
            "occurred_on": self.occurred_on,
        }


def _row_for_event(event: WorkEvent) -> WorkPanelRow:
    return WorkPanelRow(
        event_id=event.event_id, seq=event.seq,
        kind=event.kind, state=event.state,
        narrative=narrative_of(event), target=event.target,
        occurred_on=event.occurred_on)


def _check_row_ref(value: Any) -> WorkPanelRow:
    if isinstance(value, WorkPanelRow):
        return value
    return validate_row(value)


def validate_row(row: Any, event: Any = None) -> WorkPanelRow:
    """Judge one panel row, against its event when named."""
    if isinstance(row, WorkPanelRow):
        current = row
    elif isinstance(row, dict):
        unknown = set(row) - _ROW_KEYS
        if unknown:
            raise ValueError(
                f"a work panel row carries unknown keys: "
                f"{sorted(unknown)}")

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            value = _pick_any(row, spellings, what)
            if value is None:
                raise ValueError(f"a work panel row names no {what}")
            return value

        current = WorkPanelRow(
            event_id=_pick_any(row, ("event_id", "id"), "event id"),
            seq=_needed(("seq",), "sequence"),
            kind=_needed(("kind",), "kind"),
            state=_needed(("state",), "state"),
            narrative=_needed(("narrative", "line"), "narrative line"),
            target=_needed(("target",), "target"),
            occurred_on=_needed(("occurred_on",), "day it happened"))
    else:
        raise ValueError(
            f"a work panel row must be a mapping, got {row!r}")
    if event is not None:
        wanted = _row_for_event(_check_event_ref(event))
        if current != wanted:
            raise ValueError(
                "a work panel row must be its event's own row - "
                "the narrative is derived from the event, never "
                "written beside it")
    return current


def build_row(row: Any = None, event: Any = None,
              **kwargs: Any) -> WorkPanelRow:
    """Build one panel row from a mapping, a row, or its event."""
    if event is not None:
        if row is not None or kwargs:
            return validate_row(row if row is not None else kwargs,
                                event)
        return _row_for_event(_check_event_ref(event))
    if kwargs:
        if row is not None:
            raise ValueError("a row is built one way at a time")
        row = kwargs
    return validate_row(row)


@dataclass(frozen=True)
class KindCount:
    """How many events of one kind a panel holds."""

    kind: str
    items: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", normalize_kind(self.kind))
        object.__setattr__(
            self, "items", _check_count(self.items, "a kind's items"))

    def to_record(self) -> Dict[str, Any]:
        return {"kind": self.kind, "items": self.items}


def _check_kind_count_ref(value: Any) -> KindCount:
    if isinstance(value, KindCount):
        return value
    if isinstance(value, dict):
        unknown = set(value) - _KIND_COUNT_KEYS
        if unknown:
            raise ValueError(
                f"a kind count carries unknown keys: "
                f"{sorted(unknown)}")
        kind = _pick_any(value, ("kind",), "kind")
        items = _pick_any(value, ("items", "count"), "items")
        if kind is None or items is None:
            raise ValueError("a kind count names its kind and its items")
        return KindCount(kind=kind, items=items)
    raise ValueError(f"a kind count must be a mapping, got {value!r}")


def _kind_counts(rows: Tuple[WorkPanelRow, ...]) -> Tuple[KindCount, ...]:
    counts: Dict[str, int] = {}
    for row in rows:
        counts[row.kind] = counts.get(row.kind, 0) + 1
    return tuple(
        KindCount(kind=kind, items=counts[kind])
        for kind in KINDS if kind in counts)


def _panel_account(total_events: int, total_done: int,
                   total_started: int, total_failed: int,
                   distinct_targets: int,
                   kind_counts: Tuple[KindCount, ...],
                   as_of: str) -> Tuple[str, ...]:
    kinds = ", ".join(
        f"{count.kind} {count.items}" for count in kind_counts)
    return (
        f"The work panel holds {total_events} actions as of "
        f"{as_of}: {total_done} done, {total_started} still "
        f"standing started and {total_failed} failed over "
        f"{distinct_targets} targets: {kinds}.",
        "Rows stand in stream order, first action first, so "
        "two panels of one book diff cleanly, line by line.",
        "Every row carries its derived narrative line and "
        "its state as words: the tool detail stands behind "
        "the detail road, one keystroke away, and never in "
        "this panel.",
        "The panel is read off the book at call time - it "
        "is derived, never stored loose - and standing on "
        "this panel runs no tool and streams nothing live: "
        "actions are held as data alone.",
    )


@dataclass(frozen=True)
class WorkPanel:
    """The derived panel of one book: the stream at a glance.

    Rows stand in stream order; the totals are the
    rows' own counts; ``current_event_id`` is the
    last row still standing started, or None while
    nothing stands started. A stored panel is
    judged whole in ``__post_init__``: its totals,
    its kind counts, its current event, its as-of
    day and its account must all be the rows' own
    derived shape - a panel may not soften its
    stream.
    """

    panel_id: Optional[str]
    rows: Tuple[WorkPanelRow, ...]
    total_events: int
    total_done: int
    total_started: int
    total_failed: int
    distinct_targets: int
    kind_counts: Tuple[KindCount, ...]
    current_event_id: Optional[str]
    as_of: str
    account: Tuple[str, ...]

    def __post_init__(self) -> None:
        if self.panel_id is not None:
            object.__setattr__(
                self, "panel_id",
                _check_word(self.panel_id, "a panel id"))
        rows = tuple(_check_row_ref(r) for r in self.rows)
        object.__setattr__(self, "rows", rows)
        seqs = [r.seq for r in rows]
        if seqs != sorted(seqs) or len(set(seqs)) != len(seqs):
            raise ValueError(
                "panel rows stand in stream order, one row "
                "per sequence")
        for field in ("total_events", "total_done",
                      "total_started", "total_failed",
                      "distinct_targets"):
            object.__setattr__(
                self, field,
                _check_count(getattr(self, field), f"a panel's {field}"))
        counts = tuple(
            _check_kind_count_ref(c) for c in self.kind_counts)
        object.__setattr__(self, "kind_counts", counts)
        if self.current_event_id is not None:
            object.__setattr__(
                self, "current_event_id",
                _check_word(self.current_event_id, "a current event id"))
        object.__setattr__(self, "as_of", _check_day(self.as_of, "an as-of day"))
        object.__setattr__(self, "account", _check_account(self.account))
        if self.total_events != len(rows):
            raise ValueError("a panel's total is its rows' own count")
        if self.total_done != sum(
                1 for r in rows if r.state == "done"):
            raise ValueError("a panel's done total is its rows' own count")
        if self.total_started != sum(
                1 for r in rows if r.state == "started"):
            raise ValueError(
                "a panel's started total is its rows' own count")
        if self.total_failed != sum(
                1 for r in rows if r.state == "failed"):
            raise ValueError("a panel's failed total is its rows' own count")
        if self.distinct_targets != len({r.target for r in rows}):
            raise ValueError(
                "a panel's distinct targets are its rows' own count")
        if counts != _kind_counts(rows):
            raise ValueError("a panel's kind counts are its rows' own counts")
        started = [r for r in rows if r.state == "started"]
        current = started[-1].event_id if started else None
        if self.current_event_id != current:
            raise ValueError(
                "a panel's current event is the last row still "
                "standing started, derived, never chosen")
        if rows and self.as_of != max(r.occurred_on for r in rows):
            raise ValueError("a panel's as-of day is its rows' latest day")
        wanted = _panel_account(
            self.total_events, self.total_done, self.total_started,
            self.total_failed, self.distinct_targets, counts, self.as_of)
        if self.account != wanted:
            raise ValueError("a panel's account is its derived account")

    def row_for(self, event_id: Any) -> WorkPanelRow:
        """The row one event id names (KeyError if absent)."""
        wanted = _check_word(event_id, "an event id")
        for row in self.rows:
            if row.event_id == wanted:
                return row
        raise KeyError(f"no row named {wanted!r} stands in the panel")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "work_view_panel",
            "slice": WORK_VIEW_SLICE,
            "panel_id": self.panel_id,
            "rows": [r.to_record() for r in self.rows],
            "total_events": self.total_events,
            "total_done": self.total_done,
            "total_started": self.total_started,
            "total_failed": self.total_failed,
            "distinct_targets": self.distinct_targets,
            "kind_counts": [c.to_record() for c in self.kind_counts],
            "current_event_id": self.current_event_id,
            "as_of": self.as_of,
            "account": list(self.account),
        }


def _held_events(source: Any) -> Tuple[WorkEvent, ...]:
    if isinstance(source, WorkBook):
        return source.events
    if isinstance(source, WorkRegistry):
        return source.list_events()
    if isinstance(source, WorkEvent):
        return (source,)
    raise ValueError(f"a work-view source is needed, got {source!r}")


def derive_panel(source: Any) -> WorkPanel:
    """Derive the work panel of a book, registry or event."""
    events = _held_events(source)
    rows = tuple(_row_for_event(e) for e in events)
    counts = _kind_counts(rows)
    total_done = sum(1 for r in rows if r.state == "done")
    total_started = sum(1 for r in rows if r.state == "started")
    total_failed = sum(1 for r in rows if r.state == "failed")
    distinct = len({r.target for r in rows})
    as_of = max((r.occurred_on for r in rows), default=_EXAMPLE_AS_OF)
    started = [r for r in rows if r.state == "started"]
    return WorkPanel(
        panel_id=None, rows=rows, total_events=len(rows),
        total_done=total_done, total_started=total_started,
        total_failed=total_failed, distinct_targets=distinct,
        kind_counts=counts,
        current_event_id=(started[-1].event_id if started else None),
        as_of=as_of,
        account=_panel_account(
            len(rows), total_done, total_started, total_failed,
            distinct, counts, as_of))


def validate_panel(panel: Any, source: Any = None) -> WorkPanel:
    """Judge one panel whole, against its source when named."""
    if isinstance(panel, WorkPanel):
        current = panel
    elif isinstance(panel, dict):
        data = dict(panel)
        data.pop("type", None)
        data.pop("slice", None)
        unknown = set(data) - _PANEL_KEYS
        if unknown:
            raise ValueError(
                f"a work panel carries unknown keys: {sorted(unknown)}")

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            value = _pick_any(data, spellings, what)
            if value is None:
                raise ValueError(f"a work panel names no {what}")
            return value

        rows_in = _needed(("rows", "events"), "rows")
        counts_in = _needed(("kind_counts", "kinds"), "kind counts")
        current = WorkPanel(
            panel_id=_pick_any(data, ("panel_id", "id"), "panel id"),
            rows=tuple(validate_row(r) for r in rows_in),
            total_events=_needed(("total_events", "total"), "total events"),
            total_done=_needed(("total_done", "done"), "done total"),
            total_started=_needed(
                ("total_started", "started"), "started total"),
            total_failed=_needed(("total_failed", "failed"), "failed total"),
            distinct_targets=_needed(
                ("distinct_targets", "targets"), "distinct targets"),
            kind_counts=tuple(
                _check_kind_count_ref(c) for c in counts_in),
            current_event_id=_pick_any(
                data, ("current_event_id", "current"), "current event"),
            as_of=_needed(("as_of", "day"), "as-of day"),
            account=tuple(_needed(("account", "statements"), "account")))
    else:
        raise ValueError(f"a work panel must be a mapping, got {panel!r}")
    if source is not None:
        derived = derive_panel(source)
        if (current.rows != derived.rows
                or current.total_events != derived.total_events
                or current.total_done != derived.total_done
                or current.total_started != derived.total_started
                or current.total_failed != derived.total_failed
                or current.distinct_targets != derived.distinct_targets
                or current.kind_counts != derived.kind_counts
                or current.current_event_id != derived.current_event_id
                or current.as_of != derived.as_of
                or current.account != derived.account):
            raise ValueError(
                "a stored panel must equal the panel its book "
                "derives - the panel is derived, never stored loose")
    return current


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> WorkPanel:
    """Build one panel from a mapping, a panel, or its source."""
    if kwargs:
        if panel is not None:
            raise ValueError("a panel is built one way at a time")
        panel = kwargs
    if panel is None and source is not None:
        return derive_panel(source)
    return validate_panel(panel, source)


# ---------------------------------------------------------------------
# The verdict: the whole stream, judged in one word.
# ---------------------------------------------------------------------


def _verdict_word(total_failed: int, total_started: int) -> str:
    if total_failed > 0:
        return "troubled"
    if total_started > 0:
        return "working"
    return "calm"


@dataclass(frozen=True)
class WorkVerdict:
    """The derived verdict of one whole book.

    The word is read off the tallies alone:
    troubled while any action stands failed,
    working while any action still stands
    started, calm while every action stands done.
    A stored verdict is judged against those
    tallies in ``__post_init__``.
    """

    total_events: int
    total_done: int
    total_started: int
    total_failed: int
    distinct_targets: int
    earliest_on: str
    latest_on: str
    verdict: str

    def __post_init__(self) -> None:
        for field in ("total_events", "total_done", "total_started",
                      "total_failed", "distinct_targets"):
            object.__setattr__(
                self, field,
                _check_count(getattr(self, field), f"a verdict's {field}"))
        object.__setattr__(
            self, "earliest_on", _check_day(self.earliest_on, "an earliest day"))
        object.__setattr__(
            self, "latest_on", _check_day(self.latest_on, "a latest day"))
        if self.latest_on < self.earliest_on:
            raise ValueError("a verdict's latest day precedes its earliest")
        if self.total_events != (
                self.total_done + self.total_started + self.total_failed):
            raise ValueError(
                "a verdict's tallies must close on its total")
        word = _clean_text(self.verdict, "a verdict")
        if word not in VERDICT_WORDS:
            raise ValueError(
                f"a verdict is one of {VERDICT_WORDS}, got {word!r}")
        object.__setattr__(self, "verdict", word)
        if word != _verdict_word(self.total_failed, self.total_started):
            raise ValueError(
                "a verdict's word is derived from its tallies, "
                "never chosen")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "work_view_verdict",
            "slice": WORK_VIEW_SLICE,
            "total_events": self.total_events,
            "total_done": self.total_done,
            "total_started": self.total_started,
            "total_failed": self.total_failed,
            "distinct_targets": self.distinct_targets,
            "earliest_on": self.earliest_on,
            "latest_on": self.latest_on,
            "verdict": self.verdict,
        }


def derive_verdict(source: Any) -> WorkVerdict:
    """Derive the work verdict of a book, registry or event."""
    events = _held_events(source)
    total_done = sum(1 for e in events if e.state == "done")
    total_started = sum(1 for e in events if e.state == "started")
    total_failed = sum(1 for e in events if e.state == "failed")
    days = [e.occurred_on for e in events]
    return WorkVerdict(
        total_events=len(events), total_done=total_done,
        total_started=total_started, total_failed=total_failed,
        distinct_targets=len({e.target for e in events}),
        earliest_on=min(days) if days else _EXAMPLE_AS_OF,
        latest_on=max(days) if days else _EXAMPLE_AS_OF,
        verdict=_verdict_word(total_failed, total_started))


def _check_verdict_ref(value: Any) -> WorkVerdict:
    if isinstance(value, WorkVerdict):
        return value
    return validate_verdict(value)


def validate_verdict(verdict: Any, source: Any = None) -> WorkVerdict:
    """Judge one verdict whole, against its source when named."""
    if isinstance(verdict, WorkVerdict):
        current = verdict
    elif isinstance(verdict, dict):
        data = dict(verdict)
        data.pop("type", None)
        data.pop("slice", None)
        unknown = set(data) - _VERDICT_KEYS
        if unknown:
            raise ValueError(
                f"a work verdict carries unknown keys: {sorted(unknown)}")

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            value = _pick_any(data, spellings, what)
            if value is None:
                raise ValueError(f"a work verdict names no {what}")
            return value

        current = WorkVerdict(
            total_events=_needed(("total_events", "total"), "total events"),
            total_done=_needed(("total_done", "done"), "done total"),
            total_started=_needed(
                ("total_started", "started"), "started total"),
            total_failed=_needed(("total_failed", "failed"), "failed total"),
            distinct_targets=_needed(
                ("distinct_targets", "targets"), "distinct targets"),
            earliest_on=_needed(("earliest_on", "earliest"), "earliest day"),
            latest_on=_needed(("latest_on", "latest"), "latest day"),
            verdict=_needed(("verdict",), "verdict"))
    else:
        raise ValueError(f"a work verdict must be a mapping, got {verdict!r}")
    if source is not None:
        derived = derive_verdict(source)
        if current != derived:
            raise ValueError(
                "a stored verdict must equal the verdict its "
                "book derives - the verdict is derived, never "
                "stored loose")
    return current


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> WorkVerdict:
    """Build one verdict from a mapping, a verdict, or its source."""
    if kwargs:
        if verdict is not None:
            raise ValueError("a verdict is built one way at a time")
        verdict = kwargs
    if verdict is None and source is not None:
        return derive_verdict(source)
    return validate_verdict(verdict, source)


# ---------------------------------------------------------------------
# The book: one stream of actions, held whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class WorkBook:
    """One stream of coder actions, held as a book.

    Events stand in stream order - sequence
    numbers strictly ascending, one event per id
    and per sequence - and every stored panel is
    judged against the book it stands in.
    """

    title: str
    events: Tuple[WorkEvent, ...] = ()
    panels: Tuple[WorkPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book title"))
        events = tuple(_check_event_ref(e) for e in self.events)
        object.__setattr__(self, "events", events)
        seqs = [e.seq for e in events]
        if seqs != sorted(seqs) or len(set(seqs)) != len(seqs):
            raise ValueError(
                "a book's events stand in stream order, one "
                "event per sequence")
        ids = [e.event_id for e in events if e.event_id is not None]
        if len(set(ids)) != len(ids):
            raise ValueError("a book holds one event per event id")
        panels = tuple(
            validate_panel(p, self) for p in self.panels)
        object.__setattr__(self, "panels", panels)

    def event_for(self, event_id: Any) -> WorkEvent:
        """The event one id names (KeyError if absent)."""
        wanted = _check_word(event_id, "an event id")
        for event in self.events:
            if event.event_id == wanted:
                return event
        raise KeyError(f"no event named {wanted!r} stands in the book")

    def panel_for(self, panel_id: Any) -> WorkPanel:
        """The panel one id names (KeyError if absent)."""
        wanted = _check_word(panel_id, "a panel id")
        for panel in self.panels:
            if panel.panel_id == wanted:
                return panel
        raise KeyError(f"no panel named {wanted!r} stands in the book")

    def event_ids(self) -> Tuple[Optional[str], ...]:
        """The book's event ids, in stream order."""
        return tuple(e.event_id for e in self.events)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "work_view_book",
            "slice": WORK_VIEW_SLICE,
            "title": self.title,
            "events": [e.to_record() for e in self.events],
            "panels": [p.to_record() for p in self.panels],
            "event_count": len(self.events),
        }


def _judge_book_panels(book: WorkBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def validate_book(data: Any, *, require_example: bool = False) -> WorkBook:
    """Judge one book file's data whole and return its book."""
    if isinstance(data, WorkBook):
        book = data
        _judge_book_panels(book)
        if require_example:
            _check_example(book)
        return book
    if not isinstance(data, dict):
        raise ValueError(f"a work book must be a mapping, got {data!r}")
    unknown = set(data) - _WORK_BOOK_KEYS - {"guide"}
    if unknown:
        raise ValueError(
            f"a work book carries unknown keys: {sorted(unknown)}")
    if data.get("schema") != WORK_VIEW_SCHEMA:
        raise ValueError(
            f"a work book's schema must be {WORK_VIEW_SCHEMA!r}, "
            f"got {data.get('schema')!r}")
    if data.get("slice") != WORK_VIEW_SLICE:
        raise ValueError(
            f"a work book's slice must be {WORK_VIEW_SLICE!r}, "
            f"got {data.get('slice')!r}")
    guide = data.get("guide") or {}
    title = _pick_any(guide, ("title", "name"), "title")
    if title is None:
        title = _pick_any(data, ("title", "name"), "title")
    events_in = _pick_any(data, ("events", "actions"), "events")
    if events_in is None:
        raise ValueError("a work book names no events")
    panels_in = data.get("panels") or []
    events = []
    for raw in events_in:
        stored = dict(raw)
        stored.pop("type", None)
        stored.pop("slice", None)
        stored.pop("narrative", None)
        events.append(validate_event(stored))
    book = WorkBook(
        title=title,
        events=tuple(events),
        panels=tuple(validate_panel(p) for p in panels_in))
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def _check_example(book: WorkBook) -> None:
    if book.title != _EXAMPLE_TITLE:
        raise ValueError(
            f"the shipped example book is {_EXAMPLE_TITLE!r}, "
            f"got {book.title!r}")
    if book.event_ids() != _EXAMPLE_EVENT_IDS:
        raise ValueError("the shipped example book's events differ")
    first = book.events[0]
    if first.target != _EXAMPLE_FIRST_EVENT_TARGET:
        raise ValueError("the shipped example book's first event differs")
    if len(book.panels) != 1 or (
            book.panels[0].panel_id != _EXAMPLE_PANEL_ID):
        raise ValueError("the shipped example book's panel differs")
    if book.panels[0].as_of != _EXAMPLE_AS_OF:
        raise ValueError("the shipped example book's as-of day differs")
    if tuple(r.event_id for r in book.panels[0].rows) != (
            _EXAMPLE_PANEL_ROW_IDS):
        raise ValueError("the shipped example book's panel rows differ")


def build_book(book: Any = None, **kwargs: Any) -> WorkBook:
    """Build one book from a mapping, a book, or fields."""
    if isinstance(book, WorkBook) and not kwargs:
        return validate_book(book)
    if kwargs:
        if book is not None:
            raise ValueError("a book is built one way at a time")
        fields = dict(kwargs)
    elif isinstance(book, dict) and (
            "events" in book or "actions" in book) and (
            "schema" not in book and "guide" not in book
            and "canon_note" not in book):
        fields = dict(book)
    else:
        return _book_from(book, require_example=False)
    unknown = set(fields) - _BOOK_KEYS - {
        "events", "actions", "panels"}
    if unknown:
        raise ValueError(
            f"a work book carries unknown keys: {sorted(unknown)}")
    title = _pick_any(fields, ("title", "name"), "title")
    if title is None:
        raise ValueError("a work book names no title")
    events_in = _pick_any(fields, ("events", "actions"), "events") or ()
    return WorkBook(
        title=title,
        events=tuple(_check_event_ref(e) for e in events_in),
        panels=tuple(
            validate_panel(p) for p in fields.get("panels") or ()))


def _book_from(data: Any, *, require_example: bool) -> WorkBook:
    if isinstance(data, WorkBook):
        return validate_book(data, require_example=require_example)
    if isinstance(data, dict):
        return validate_book(data, require_example=require_example)
    raise ValueError(f"a work book must be a mapping, got {data!r}")


def load_work_view(data: Optional[Dict[str, Any]] = None) -> WorkBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(WORK_VIEW_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_work_view_file(path: Any) -> WorkBook:
    """Load one book file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: events held one by one.
# ---------------------------------------------------------------------


class WorkRegistry:
    """An in-memory holding of work events, one by one.

    The registry is the pure layer's model of a
    session's stream: events are held under their
    ids (or a deterministic ``event-N`` id), one
    event per id and per sequence, in stream
    order. Holding is data only - no event held
    here runs its tool or streams anything.
    """

    def __init__(self, book: Any = None) -> None:
        self._events: List[WorkEvent] = []
        self._title: Optional[str] = None
        if book is not None:
            self.register_book(book)

    def title(self) -> Optional[str]:
        return self._title

    def _fresh_event_id(self, held_ids: Any) -> str:
        n = 1
        while f"event-{n}" in held_ids:
            n += 1
        return f"event-{n}"

    def _check_standing_free(self, event: WorkEvent) -> None:
        for held in self._events:
            if event.event_id is not None and (
                    held.event_id == event.event_id):
                raise ValueError(
                    f"an event already stands under id "
                    f"{event.event_id!r}")
            if held.seq == event.seq:
                raise ValueError(
                    f"an event already stands at sequence "
                    f"{event.seq} - the stream holds one "
                    f"action per place")

    def register_event(self, event: Any) -> WorkEvent:
        """Hold one event, judged whole before it is held."""
        validated = _check_event_ref(event)
        self._check_standing_free(validated)
        if validated.event_id is None:
            validated = WorkEvent(
                event_id=self._fresh_event_id(
                    {e.event_id for e in self._events}),
                seq=validated.seq, kind=validated.kind,
                target=validated.target, tool=validated.tool,
                detail=validated.detail, state=validated.state,
                occurred_on=validated.occurred_on,
                actor=validated.actor, source=validated.source,
                origin_session=validated.origin_session)
        self._events.append(validated)
        self._events.sort(key=lambda e: e.seq)
        return validated

    def _hold_event(self, validated: WorkEvent) -> None:
        self._events.append(validated)
        self._events.sort(key=lambda e: e.seq)

    def register_book(self, book: Any) -> WorkBook:
        """Hold a whole book's events, judged whole first."""
        validated = build_book(book)
        for event in validated.events:
            self._check_standing_free(event)
        if self._title is None:
            self._title = validated.title
        elif validated.title != self._title:
            raise ValueError(
                "a second book under a different title refuses - "
                "one stream stands in one registry")
        for event in validated.events:
            held = event
            if held.event_id is None:
                held = WorkEvent(
                    event_id=self._fresh_event_id(
                        {e.event_id for e in self._events}
                        | {e.event_id for e in validated.events}),
                    seq=held.seq, kind=held.kind,
                    target=held.target, tool=held.tool,
                    detail=held.detail, state=held.state,
                    occurred_on=held.occurred_on, actor=held.actor,
                    source=held.source,
                    origin_session=held.origin_session)
            self._hold_event(held)
        return self.book()

    def get_event(self, event_id: Any) -> WorkEvent:
        """The event one id names (KeyError if absent)."""
        wanted = _check_word(event_id, "an event id")
        for event in self._events:
            if event.event_id == wanted:
                return event
        raise KeyError(f"no event named {wanted!r} stands held")

    def detail_for(self, event_id: Any) -> str:
        """The held detail of one event - the keystroke road."""
        return self.get_event(event_id).detail

    def latest_event(self) -> WorkEvent:
        """The last event in the stream (KeyError if empty)."""
        if not self._events:
            raise KeyError("no event stands held")
        return self._events[-1]

    def list_events(self) -> Tuple[WorkEvent, ...]:
        return tuple(self._events)

    def book(self) -> WorkBook:
        return WorkBook(
            title=self._title or "Work View",
            events=tuple(self._events))

    def panel(self) -> WorkPanel:
        return derive_panel(self.book())

    def verdict(self) -> WorkVerdict:
        return derive_verdict(self.book())


def events_of_kind(source: Any, kind: Any) -> Tuple[WorkEvent, ...]:
    """The events of one kind in a source, in stream order."""
    wanted = normalize_kind(kind)
    return tuple(
        e for e in _held_events(source) if e.kind == wanted)


def total_events(source: Any) -> int:
    """How many events a source holds."""
    return len(_held_events(source))


# ---------------------------------------------------------------------
# Session news, plain words, and the screens.
# ---------------------------------------------------------------------


def event_record(event: Any) -> Dict[str, Any]:
    """The session-news record of one work event."""
    current = _check_event_ref(event)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Work view over {current.target}: "
        f"{narrative_of(current)}.")
    return record_out


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived panel."""
    current = validate_panel(panel, source)
    record = current.to_record()
    record["news"] = True
    kinds = ", ".join(
        f"{c.kind} {c.items}" for c in current.kind_counts)
    record["headline"] = (
        f"Work panel as of {current.as_of}: "
        f"{current.total_events} actions - {current.total_done} "
        f"done, {current.total_started} standing started, "
        f"{current.total_failed} failed, over "
        f"{current.distinct_targets} targets ({kinds}).")
    return record


def verdict_record(verdict: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived verdict."""
    current = validate_verdict(verdict, source)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Work verdict: {current.verdict} - "
        f"{current.total_done} of {current.total_events} "
        f"actions done, {current.total_started} standing "
        f"started and {current.total_failed} failed, from "
        f"{current.earliest_on} to {current.latest_on}.")
    return record


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one work book."""
    current = book if isinstance(book, WorkBook) else build_book(book)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Work book {current.title}: "
        f"{record['event_count']} actions named.")
    return record


def plain_words(event: Any) -> str:
    """One event, in one plain sentence."""
    current = _check_event_ref(event)
    return (
        f"{narrative_of(current)} - a {current.kind} "
        f"action over {current.target}, standing "
        f"{current.state} on {current.occurred_on}, "
        f"carried by {current.tool}; its tool detail "
        f"stands one keystroke away, never in the face.")


def detail_plain_words(event: Any) -> str:
    """One event with its held detail, in plain words."""
    current = _check_event_ref(event)
    return (
        f"{narrative_of(current)} - detail, one keystroke "
        f"away: {current.detail}")


def panel_plain_words(source: Any) -> str:
    """The panel in plain words, in full."""
    if isinstance(source, WorkPanel):
        panel = validate_panel(source)
        title = None
    elif isinstance(source, (WorkBook, WorkRegistry)):
        panel = derive_panel(source)
        title = source.title if isinstance(source, WorkBook) else None
    else:
        raise ValueError(f"a work-view source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Actions, in stream order:")
    for row in panel.rows:
        lines.append(
            f"{row.event_id}: {row.narrative} "
            f"({row.kind}/{row.state}, {row.occurred_on})")
    lines.extend(panel.account)
    return "\n".join(lines)


def verdict_plain_words(source: Any) -> str:
    """The work verdict in plain words, in full."""
    if isinstance(source, WorkVerdict):
        verdict = validate_verdict(source)
    elif isinstance(source, (WorkBook, WorkRegistry)):
        verdict = derive_verdict(source)
    else:
        raise ValueError(f"a work-view source is needed, got {source!r}")
    return (
        f"Work verdict: {verdict.verdict} - "
        f"{verdict.total_done} actions done, "
        f"{verdict.total_started} standing started and "
        f"{verdict.total_failed} failed, over "
        f"{verdict.distinct_targets} targets, from "
        f"{verdict.earliest_on} to {verdict.latest_on}, of "
        f"{verdict.total_events} actions - every line is "
        f"derived from its event, and no tool detail "
        f"stands in this verdict.")


def _source_book(source: Any) -> WorkBook:
    if source is None:
        return load_work_view()
    if isinstance(source, WorkRegistry):
        return source.book()
    if isinstance(source, WorkBook):
        return source
    if isinstance(source, WorkEvent):
        return WorkBook(title="One work event", events=(source,))
    raise ValueError(f"a work book is needed, got {source!r}")


def format_event(event: Any) -> str:
    """One event as a screen block: narrative, no detail."""
    current = _check_event_ref(event)
    lines = [
        f"{current.event_id or '-'}: {narrative_of(current)}",
        f"Kind: {current.kind} - State: {current.state} - "
        f"Tool: {current.tool} (read from {current.source})",
        f"Target: {current.target} "
        f"(on {current.occurred_on} by {current.actor} "
        f"in {current.origin_session})",
        "Detail: held back - one keystroke away "
        f"(/workview detail {current.event_id or ''}).",
    ]
    return "\n".join(lines)


def format_event_detail(event: Any) -> str:
    """One event with its detail shown - the keystroke road."""
    current = _check_event_ref(event)
    return (
        format_event(current)
        + f"\nDetail: {current.detail}")


def format_stream(source: Any = None, kind: Any = None,
                  detail: bool = False) -> str:
    """The stream as calm lines, in stream order.

    By default the lines are narrative alone - no
    tool detail stands in the stream. With
    ``detail`` the held detail of each event
    follows its line, indented: the one-keystroke
    -away reading of the whole stream.
    """
    book = _source_book(source)
    wanted = normalize_kind(kind) if kind is not None else None
    lines = []
    for event in book.events:
        if wanted is not None and event.kind != wanted:
            continue
        lines.append(
            f"{event.event_id or '-'}: {narrative_of(event)}")
        if detail:
            lines.append(f"  detail: {event.detail}")
    if not lines:
        lines.append("No actions stand in the book on that reading.")
    return "\n".join(lines)


def format_panel(source: Any = None) -> str:
    """The panel as a screen block: every row and the account."""
    if isinstance(source, WorkPanel):
        panel = validate_panel(source)
        lines: list = []
    else:
        book = _source_book(source)
        panel = derive_panel(book)
        lines = [f"Panel in {book.title}:"]
    lines.append("Actions, in stream order:")
    for row in panel.rows:
        lines.append(
            f"{row.event_id}: {row.narrative} - "
            f"{row.kind}/{row.state} over {row.target} "
            f"({row.occurred_on})")
    lines.extend(panel.account)
    return "\n".join(lines)


def format_verdict(source: Any = None) -> str:
    """The verdict as a screen block."""
    if isinstance(source, WorkVerdict):
        verdict = validate_verdict(source)
        title = "the stream"
    else:
        book = _source_book(source)
        verdict = derive_verdict(book)
        title = book.title
    return (
        f"Verdict in Streaming Work View over {title}: "
        f"{verdict.verdict} - {verdict.total_done} of "
        f"{verdict.total_events} actions done, "
        f"{verdict.total_started} standing started, "
        f"{verdict.total_failed} failed, over "
        f"{verdict.distinct_targets} targets, from "
        f"{verdict.earliest_on} to {verdict.latest_on}.")


def format_work_view_screen(source: Any = None,
                            detail: bool = False) -> str:
    """The whole work-view screen for one book."""
    book = _source_book(source)
    panel = derive_panel(book)
    verdict = derive_verdict(book)
    lines = [
        f"Streaming Work View (M-172) - {book.title}",
        format_stream(book, detail=detail),
        f"Panel: {panel.total_events} actions - "
        f"{panel.total_done} done, {panel.total_started} "
        f"standing started, {panel.total_failed} failed; "
        f"current stands {panel.current_event_id or 'none'}.",
        f"Verdict: {verdict.verdict}.",
        "Tool detail stands one keystroke away "
        "(/workview detail) - never in this stream.",
    ]
    return "\n".join(lines)


def parse_work_view_args(args: Any) -> Tuple[str, Any]:
    """Parse the /workview grammar into (action, target).

    ``""``/``show``/``list`` show the stream;
    ``event <event-id>`` shows one event;
    ``detail`` shows the whole stream with its
    detail, ``detail <event-id>`` one event with
    its detail; ``kind <kind>`` shows one kind's
    actions; ``panel`` and ``verdict`` show the
    derived panel and verdict. Anything else
    raises ValueError carrying the usage line.
    """
    if args is None:
        return ("show", None)
    if not isinstance(args, str):
        raise ValueError(USAGE)
    parts = args.split()
    if not parts or parts == ["show"] or parts == ["list"]:
        return ("show", None)
    if parts[0] == "event" and len(parts) == 2:
        return ("event", _check_word(parts[1], "an event id"))
    if parts[0] == "detail" and len(parts) == 1:
        return ("detail", None)
    if parts[0] == "detail" and len(parts) == 2:
        return ("detail", _check_word(parts[1], "an event id"))
    if parts[0] == "kind" and len(parts) == 2:
        return ("kind", normalize_kind(parts[1]))
    if parts == ["panel"]:
        return ("panel", None)
    if parts == ["verdict"]:
        return ("verdict", None)
    raise ValueError(USAGE)
