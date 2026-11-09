"""Approval cards perfected (All-Features roadmap slice M-174).

Part VIII - The Beautiful Face - builds here. The
roadmap's words: *one decision per card, full
context on the card, remembered-scope offered
precisely, keyboard and mouse equal.*

What already ships, and what this slice adds:

* The shipped approval roads ask, but nothing
  holds the CARD itself as data. The elder
  ToolPolicy ``ask`` road (``core/policy.py``)
  takes a bare boolean back; approval moments
  (``core/approval_moments.py``, M-116) shape one
  complete question - what, where, what it does -
  but hold no card; remembered approvals
  (``core/remembered_approvals.py``, M-096) hold a
  standing answer at an exact scope - command,
  args pattern and project path - but are never
  offered from a card; the destructive-command
  doctrine (``core/destructive_doctrine.py``,
  M-111) places an act on its ladder, but no card
  reads its alarm off that ladder; and the M-171
  TUI redesign charter judged the command
  approval modal (its S-04 row) REPAIR and names
  M-174 as its owning slice: *perfect the card:
  name the target and the consequence as their
  own lines, offer a precisely-scoped remembered
  approval on the card, keep keyboard and mouse
  exactly equal, and reserve alarm styling for
  destructive operations* - its K-02 judgement
  strains because no remembered scope is offered
  or named on the card, its K-03 judgement fails
  because the exact target stands only inside the
  raw command text, and its L-05 judgement strains
  because alarm styling is spent on every approval,
  routine ones included.
* This slice is that perfected card, as a pure
  layer: one approval card validated as data WITH
  ITS PROVENANCE WHOLE - exactly one decision;
  the operation verbatim; the target and the
  consequence each named as their own line; the
  full context carried on the card as its own
  statements; the act itself as a command, its
  arguments and its project path, from which the
  remembered-approval offer is DERIVED through
  the shipped remembered-approvals road by import
  - the exact scope of this card's own act, never
  broader; whether the act is destructive, from
  which the card's alarm level is DERIVED; and
  the day it was recorded, who recorded it, its
  source and the session it was recorded in. A
  card composed from a command BY IMPORT is judged
  by the shipped destructive doctrine: an act the
  doctrine places on the irreversible rung is
  destructive, and a destructive word named
  against that judgement refuses. A card composed
  from an approval moment BY IMPORT takes its
  decision, target and consequence from the
  moment's what, where and what-it-does, and only
  from a moment the shipped judge reads complete.
  The answer to a card is held as its own record
  - one decision record, judged whole: the card
  it answers, the answer in the closed answer set
  (allow, reject, remember), its own words, and
  its provenance whole. The panel is DERIVED from
  the held cards and their answers (its rows the
  cards in held order carrying their derived
  lines, alarm levels and answers, its totals the
  cards' own counts), and a verdict is DERIVED for
  the whole book. The shipped data file
  (``mythic_agent/data/approval_cards.yaml``)
  holds one example book in exactly the shape a
  real card file takes, a loader reads a card file
  anywhere on disk, cards and decisions are shaped
  as session news, and a small in-memory registry
  model holds cards and decisions one by one. The
  agent layer owns holding cards for a session
  and standing a decision on one.

Honesty rules, enforced here and pinned by tests:

* **One decision per card.** A card carries
  exactly one decision field; there is no second
  question to smuggle in - a key this layer does
  not carry refuses, and a card is answered by
  exactly one decision record: a second answer
  standing on an answered card refuses the whole
  derivation.
* **The target and the consequence are their own
  lines.** Each is a named field of the card,
  carried and formatted as its own line - never
  left inside the raw operation text for the
  reader to parse out, which is the charter's
  K-03 failure this slice repairs.
* **The remembered scope is the card's own act,
  exactly.** The offer is derived from the card's
  command, arguments and project path through the
  shipped M-096 scope road: the scope names this
  command, these arguments, this project - never
  a broader command, never a wider path, and no
  stored scope may disagree with the derived one.
* **Keyboard and mouse are exactly equal.** Both
  paths offer the same acts in the same order -
  allow, reject, remember - read off one held
  tuple, so the two can never drift apart; the
  decision is carried by the act words, never by
  colour or pointer alone.
* **Alarm is derived, and reserved.** A card's
  alarm level is read off its destructive flag
  alone - alarm for a destructive operation, calm
  for a routine one - and a stored alarm level is
  not a field: a mapping naming one refuses. A
  card composed from a command takes its
  destructive flag from the shipped doctrine's
  ladder, never from a guess.
* **Data only.** This layer holds questions as
  data: it runs no operation, executes no
  approval, saves no remembered approval beyond
  naming the exact scope the shipped M-096 road
  would hold, sends nothing, posts nothing,
  schedules nothing, calls no model and persists
  nothing - a card held here is a question, never
  the act it asks about, and no live UI is
  rendered here.
"""

from __future__ import annotations

__all__ = [
    "ALARM_LEVELS",
    "ANSWERS",
    "ANSWER_WORDS",
    "APPROVAL_CARDS_RESOURCE",
    "APPROVAL_CARDS_SCHEMA",
    "APPROVAL_CARDS_SLICE",
    "DECISION_ACTS",
    "PLAIN_EXPLANATION",
    "THE_APPROVAL_CARDS_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "Any",
    "AnswerCount",
    "ApprovalCard",
    "ApprovalCardRegistry",
    "ApprovalCardsBook",
    "ApprovalPanel",
    "ApprovalPanelRow",
    "ApprovalVerdict",
    "CardDecision",
    "Dict",
    "List",
    "Optional",
    "Tuple",
    "alarm_of",
    "book_record",
    "build_book",
    "build_card",
    "build_decision",
    "build_panel",
    "build_row",
    "build_verdict",
    "card_from_command",
    "card_from_moment",
    "card_record",
    "cards_with_alarm",
    "decision_plain_words",
    "decision_record",
    "derive_panel",
    "derive_verdict",
    "effective_answers",
    "format_approval_cards_screen",
    "format_book",
    "format_card",
    "format_decision",
    "format_panel",
    "format_verdict",
    "inspect_operation_source",
    "line_of",
    "load_approval_cards",
    "load_approval_cards_file",
    "normalize_alarm",
    "normalize_answer",
    "panel_plain_words",
    "panel_record",
    "parse_approval_cards_args",
    "paths_of",
    "plain_words",
    "scope_line_of",
    "scope_of",
    "total_cards",
    "validate_book",
    "validate_card",
    "validate_decision",
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

APPROVAL_CARDS_SLICE = "M-174"

#: The longer name other layers cite for this slice.
THE_APPROVAL_CARDS_SLICE = APPROVAL_CARDS_SLICE

APPROVAL_CARDS_RESOURCE = "approval_cards.yaml"

APPROVAL_CARDS_SCHEMA = "mythic.approval_cards/1"

#: The answers one card may be given, in the
#: charter's own order of concern: allow this act,
#: reject it, or remember the answer at the card's
#: own exact scope.
ANSWERS = ("allow", "reject", "remember")

_ANSWER_ALIASES = {
    "allow": "allow", "approve": "allow", "yes": "allow",
    "reject": "reject", "deny": "reject", "refuse": "reject",
    "no": "reject",
    "remember": "remember", "always": "remember",
    "remembered": "remember",
}

#: The answer words a panel counts, in order: the
#: three answers a card may be given, then the
#: state of a card no decision stands on yet.
ANSWER_WORDS = ("allow", "reject", "remember", "awaiting")

#: The acts each input path offers on a card, in
#: order. Keyboard and mouse read this one tuple,
#: so the two paths are equal by construction.
DECISION_ACTS = ("allow", "reject", "remember")

#: The alarm levels a card may carry, in order of
#: quiet: a routine card stands calm; alarm is
#: priced for the destructive few alone.
ALARM_LEVELS = ("calm", "alarm")

_ALARM_ALIASES = {
    "calm": "calm", "routine": "calm", "quiet": "calm",
    "none": "calm",
    "alarm": "alarm", "alarmed": "alarm", "destructive": "alarm",
}

#: The words a whole book's verdict may carry:
#: complete while every card stands answered,
#: alarmed while an unanswered destructive card
#: stands, waiting while the book only waits.
VERDICT_WORDS = ("complete", "waiting", "alarmed")

_CARD_KEYS = frozenset({
    "card_id", "id", "decision", "question",
    "operation", "command_text", "target",
    "consequence", "effect", "context",
    "command", "args", "arguments",
    "path", "project", "destructive",
    "recorded_on", "day", "date",
    "actor", "by", "who", "source",
    "origin_session", "session"})

_ROW_KEYS = frozenset({
    "card_id", "id", "decision", "target",
    "alarm", "answer", "line", "recorded_on"})

_ANSWER_COUNT_KEYS = frozenset({"answer", "items", "count"})

_PANEL_KEYS = frozenset({
    "panel_id", "id", "rows", "cards",
    "total_cards", "total", "total_destructive",
    "destructive", "total_alarmed", "alarmed",
    "total_allowed", "allowed", "total_rejected",
    "rejected", "total_remembered", "remembered",
    "total_awaiting", "awaiting",
    "answer_counts", "answers",
    "as_of", "day", "account", "statements"})

_DECISION_KEYS = frozenset({
    "decision_id", "id", "seq", "sequence", "order",
    "card_id", "card", "answer", "choice",
    "detail", "reason",
    "recorded_on", "day", "date",
    "actor", "by", "who", "source",
    "origin_session", "session"})

_VERDICT_KEYS = frozenset({
    "total_cards", "total", "total_destructive",
    "destructive", "total_alarmed", "alarmed",
    "total_allowed", "allowed", "total_rejected",
    "rejected", "total_remembered", "remembered",
    "total_awaiting", "awaiting",
    "earliest_on", "earliest", "latest_on", "latest",
    "verdict"})

_BOOK_KEYS = frozenset({"title", "name"})

_APPROVAL_CARDS_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "canon_note", "guide", "cards", "decisions",
    "panels"})

_EXAMPLE_TITLE = "Approval Cards at the M-173 slice boundary"

_EXAMPLE_CARD_IDS = (
    "card-test-run", "card-commit-m174",
    "card-push-roadmap", "card-remove-team99")

_EXAMPLE_FIRST_CARD_ID = "card-test-run"

_EXAMPLE_FIRST_CARD_DECISION = "Allow the slice-board test run"

_EXAMPLE_PANEL_ID = "panel-m173-boundary"

_EXAMPLE_AS_OF = "2026-11-09"

_EXAMPLE_DECISION_IDS = (
    "dec-remember-tests", "dec-allow-commit")

PLAIN_EXPLANATION = (
    "Approval Cards Perfected: one decision per "
    "card, with the full context carried on the "
    "card - the operation verbatim, the target and "
    "the consequence each named as their own line, "
    "and the card's provenance whole. The "
    "remembered approval a card offers is derived "
    "from the card's own act through the shipped "
    "remembered-approvals road: always allow this "
    "command, with these arguments, in this "
    "project - the exact scope of this card's act, "
    "never broader. Keyboard and mouse offer the "
    "same acts in the same order, allow, reject and "
    "remember, read off one held tuple, so the two "
    "paths are exactly equal. A card's alarm level "
    "is derived from its act alone: alarm for a "
    "destructive operation, calm for a routine one "
    "- alarm styling is reserved for the dangerous "
    "few. A card composed from a command takes its "
    "destructive standing from the shipped "
    "destructive doctrine's ladder. This layer "
    "holds questions as data only: it runs no "
    "operation, executes no approval, saves no "
    "remembered approval, renders no live UI, "
    "sends nothing, posts nothing, schedules "
    "nothing, calls no model and persists nothing "
    "- a card held here is a question, never the "
    "act it asks about."
)

USAGE = (
    "Usage: /approvalcards, /approvalcards show, "
    "/approvalcards card <card-id>, "
    "/approvalcards decision <decision-id>, "
    "/approvalcards panel, /approvalcards verdict"
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


def _check_context(value: Any) -> Tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"a card's context must be a list of statements, "
            f"got {value!r}")
    context = tuple(
        _check_long_text(s, "a context statement")
        for s in value)
    if not context:
        raise ValueError(
            "a card carries its full context: at least "
            "one context statement stands on the card")
    if len(context) > 16:
        raise ValueError(
            f"a card's context carries at most 16 statements, "
            f"got {len(context)}")
    if len(set(context)) != len(context):
        raise ValueError("a card's context states one statement twice")
    return context


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
    seq = _check_count(value, "a decision's sequence")
    if seq < 1:
        raise ValueError(
            f"a decision's sequence stands from 1, got {value!r}")
    return seq


def _check_word(value: Any, what: str) -> str:
    try:
        return normalize_member_id(value)
    except ValueError:
        raise ValueError(
            f"{what} must be one plain word, "
            f"got {value!r}") from None


def _check_flag(value: Any, what: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{what} must be true or false, got {value!r}")
    return value


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


def normalize_answer(value: Any) -> str:
    """One answer word, read onto the closed answer set."""
    if not isinstance(value, str):
        raise ValueError(f"an answer must be a word, got {value!r}")
    answer = _ANSWER_ALIASES.get(value.strip().lower())
    if answer is None:
        raise ValueError(
            "an answer is one of %s, got %r"
            % ("/".join(ANSWERS), value))
    return answer


def normalize_alarm(value: Any) -> str:
    """One alarm-level word, read onto the closed set."""
    if not isinstance(value, str):
        raise ValueError(f"an alarm level must be a word, got {value!r}")
    alarm = _ALARM_ALIASES.get(value.strip().lower())
    if alarm is None:
        raise ValueError(
            "an alarm level is one of %s, got %r"
            % ("/".join(ALARM_LEVELS), value))
    return alarm


def _scope_of_fields(command: Any, args: Any, path: Any):
    """The exact M-096 scope of one act, judged by import.

    The shipped remembered-approvals road judges
    the scope whole - one command carrying no
    pattern, an args pattern of plain strings, and
    one project path, spelling-normalised - and
    this layer's cards stand on that judgement:
    a malformed act refuses here, in the shipped
    road's own words, rather than being re-judged
    loosely.
    """
    from .remembered_approvals import validate_scope
    if isinstance(args, (list, tuple)):
        pattern: Any = list(args)
    else:
        pattern = args
    return validate_scope({
        "command": command, "args_pattern": pattern, "path": path})


def scope_of(card: Any):
    """The remembered scope one card offers, derived.

    Read off the card's own command, arguments and
    project path through the shipped M-096 road:
    the scope is this card's act exactly - never a
    broader command, never a wider path.
    """
    current = _check_card_ref(card)
    return _scope_of_fields(
        current.command, current.args, current.path)


def scope_line_of(card: Any) -> str:
    """The remembered-scope offer, as the card's own line.

    The line names the derived scope exactly:
    always allow this command, with these
    arguments, in this project.
    """
    scope = scope_of(card)
    args = " ".join(scope.args_pattern)
    if args:
        return (
            f"always allow {scope.command} {args} "
            f"in {scope.path}")
    return f"always allow {scope.command} in {scope.path}"


def alarm_of(card: Any) -> str:
    """The alarm level one card derives.

    Read off the card's destructive flag alone:
    alarm for a destructive operation, calm for a
    routine one - alarm styling is reserved for
    the dangerous few, per the charter's L-05
    judgement. There is no colour in this layer at
    all: the level is a word.
    """
    current = _check_card_ref(card)
    return "alarm" if current.destructive else "calm"


def line_of(card: Any) -> str:
    """The card line one approval card derives.

    Read off the card's decision and its derived
    alarm level alone: the one decision, and
    whether the card stands calm or alarmed.
    """
    current = _check_card_ref(card)
    return f"{current.decision} - {alarm_of(current)}"


def paths_of(card: Any) -> Dict[str, Tuple[str, ...]]:
    """The acts each input path offers on one card.

    Keyboard and mouse read the one held
    ``DECISION_ACTS`` tuple, so the two paths are
    exactly equal - same acts, same order - by
    construction, for every card.
    """
    _check_card_ref(card)
    return {"keyboard": DECISION_ACTS, "mouse": DECISION_ACTS}


# ---------------------------------------------------------------------
# The card: one decision, held whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ApprovalCard:
    """One approval card: exactly one decision, held whole.

    ``decision`` is the one question the card asks;
    ``operation`` is the act verbatim, exactly what
    will run; ``target`` and ``consequence`` are
    each named as their own line; ``context`` is
    the full context carried on the card, as its
    own statements. The act itself - ``command``,
    its ``args`` and the project ``path`` - is
    judged whole through the shipped M-096 scope
    road, and the remembered scope the card offers
    is derived from it. ``destructive`` says the
    act cannot be undone (or can be undone only as
    the doctrine's irreversible rung reads it);
    the alarm level is never a field - it is
    derived by :func:`alarm_of` at call time. The
    provenance - the day it was recorded, who
    recorded it, its source and the session it was
    recorded in - rides whole.
    """

    card_id: str
    decision: str
    operation: str
    target: str
    consequence: str
    context: Tuple[str, ...]
    command: str
    args: Tuple[str, ...]
    path: str
    destructive: bool
    recorded_on: str
    actor: str
    source: str
    origin_session: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "card_id", _check_word(self.card_id, "a card id"))
        object.__setattr__(
            self, "decision",
            _check_title(self.decision, "the card's one decision"))
        object.__setattr__(
            self, "operation",
            _check_long_text(self.operation, "the operation"))
        object.__setattr__(
            self, "target", _check_title(self.target, "the target"))
        object.__setattr__(
            self, "consequence",
            _check_long_text(self.consequence, "the consequence"))
        object.__setattr__(
            self, "context", _check_context(self.context))
        scope = _scope_of_fields(self.command, self.args, self.path)
        object.__setattr__(self, "command", scope.command)
        object.__setattr__(self, "args", tuple(scope.args_pattern))
        object.__setattr__(self, "path", scope.path)
        object.__setattr__(
            self, "destructive",
            _check_flag(self.destructive, "a card's destructive flag"))
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
    def alarm(self) -> str:
        """The derived alarm level of this card."""
        return alarm_of(self)

    @property
    def line(self) -> str:
        """The derived card line of this card."""
        return line_of(self)

    @property
    def scope_line(self) -> str:
        """The derived remembered-scope line of this card."""
        return scope_line_of(self)

    def to_record(self) -> Dict[str, Any]:
        from .remembered_approvals import scope_fingerprint
        scope = scope_of(self)
        return {
            "type": "approval_card",
            "slice": APPROVAL_CARDS_SLICE,
            "card_id": self.card_id,
            "decision": self.decision,
            "operation": self.operation,
            "target": self.target,
            "consequence": self.consequence,
            "context": list(self.context),
            "command": self.command,
            "args": list(self.args),
            "path": self.path,
            "destructive": self.destructive,
            "alarm": self.alarm,
            "line": self.line,
            "scope": scope.to_record(),
            "scope_id": scope_fingerprint(scope),
            "scope_line": self.scope_line,
            "keyboard": list(DECISION_ACTS),
            "mouse": list(DECISION_ACTS),
            "recorded_on": self.recorded_on,
            "actor": self.actor,
            "source": self.source,
            "origin_session": self.origin_session,
        }


def _check_card_ref(value: Any) -> ApprovalCard:
    if isinstance(value, ApprovalCard):
        return value
    return validate_card(value)


def validate_card(card: Any) -> ApprovalCard:
    """Judge one approval card whole and return it.

    A mapping is read through its spellings: a
    derived key (``line``, ``alarm``, ``scope``,
    ``keyboard`` or ``mouse``) refuses - those are
    derived, never stored - as does any key the
    card does not carry, and two spellings naming
    two different values.
    """
    if isinstance(card, ApprovalCard):
        return card
    if not isinstance(card, dict):
        raise ValueError(
            f"an approval card must be a mapping, got {card!r}")
    unknown = set(card) - _CARD_KEYS
    if unknown:
        raise ValueError(
            f"an approval card carries unknown keys: "
            f"{sorted(unknown)}")
    if "type" in card:
        raise ValueError("an approval card is judged without its news keys")

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(card, spellings, what)
        if value is None:
            raise ValueError(f"an approval card names no {what}")
        return value

    return ApprovalCard(
        card_id=_needed(("card_id", "id"), "card id"),
        decision=_needed(("decision", "question"), "decision"),
        operation=_needed(("operation", "command_text"), "operation"),
        target=_needed(("target",), "target"),
        consequence=_needed(("consequence", "effect"), "consequence"),
        context=_needed(("context",), "context"),
        command=_needed(("command",), "command"),
        args=_needed(("args", "arguments"), "arguments"),
        path=_needed(("path", "project"), "project path"),
        destructive=_needed(("destructive",), "destructive flag"),
        recorded_on=_needed(
            ("recorded_on", "day", "date"), "day it was recorded"),
        actor=_needed(("actor", "by", "who"), "actor"),
        source=_needed(("source",), "source"),
        origin_session=_needed(
            ("origin_session", "session"), "origin session"),
    )


def build_card(card: Any = None, **kwargs: Any) -> ApprovalCard:
    """Build one card from a mapping, a card, or fields."""
    if kwargs:
        if card is not None:
            raise ValueError("a card is built one way at a time")
        card = kwargs
    return validate_card(card)


def card_from_command(operation: Any = None, *,
                      card_id: Any, decision: Any,
                      target: Any = None,
                      consequence: Any, context: Any,
                      path: Any,
                      recorded_on: Any = "2026-11-09",
                      actor: Any = "the coordinator",
                      source: Any = "approval cards",
                      origin_session: Any = "session-m174",
                      destructive: Any = None) -> ApprovalCard:
    """Raise one card over a command, judged by the doctrine.

    The operation text is judged BY IMPORT through
    the shipped destructive doctrine (M-111): its
    argv gives the card's command and arguments,
    its rung gives the card's destructive standing
    - an act on the irreversible rung is
    destructive; every other standing (costly,
    reversible, or unclassified and never claimed
    safe) is not - and a destructive word named
    here that disagrees with the doctrine's
    judgement refuses. The target defaults to the
    doctrine's own named targets for the act; a
    card whose act names no target and is given
    none refuses plainly - the target is the
    card's own line, never parsed out of the raw
    text by the reader.
    """
    from .destructive_doctrine import judge_command
    if operation is None:
        raise ValueError("an operation is needed to raise a card")
    judgement = judge_command(operation)
    if not judgement.argv:
        raise ValueError(
            "the doctrine reads no command out of this "
            "operation - no card stands over it")
    derived = judgement.rung == "irreversible"
    if destructive is not None and bool(destructive) != derived:
        raise ValueError(
            f"a destructive standing named for this operation "
            f"must be the doctrine's own judgement {derived!r} "
            f"(rung {judgement.rung or 'unclassified'}), got "
            f"{destructive!r} - destructiveness is judged from "
            f"the shipped ladder, never chosen")
    if target is None:
        if judgement.targets:
            target = ", ".join(judgement.targets)
        else:
            raise ValueError(
                "this operation names no target through the "
                "doctrine - name the card's target as its "
                "own line")
    return ApprovalCard(
        card_id=card_id, decision=decision,
        operation=judgement.command, target=target,
        consequence=consequence, context=context,
        command=judgement.argv[0], args=tuple(judgement.argv[1:]),
        path=path, destructive=derived,
        recorded_on=recorded_on, actor=actor,
        source=source, origin_session=origin_session)


def card_from_moment(moment: Any = None, *,
                     card_id: Any, command: Any,
                     args: Any = (), path: Any,
                     destructive: Any = False,
                     context: Any = None,
                     operation: Any = None,
                     recorded_on: Any = "2026-11-09",
                     actor: Any = "the coordinator",
                     source: Any = "approval cards",
                     origin_session: Any = "session-m174") -> ApprovalCard:
    """Raise one card over a shipped approval moment, by import.

    The moment (M-116) is judged by its own shipped
    judge first: only a moment read complete may
    stand on a card - an incomplete moment refuses,
    naming its missing parts. The card's decision
    is the moment's what, its target the moment's
    where, its consequence the moment's
    what-it-does; the context defaults to those
    three carried whole. The operation defaults to
    the moment's what-it-does road's act named by
    ``command`` and ``args`` joined plainly.
    """
    from .approval_moments import judge_moment
    if moment is None:
        raise ValueError("an approval moment is needed to raise a card")
    assessment = judge_moment(moment)
    if assessment.state != "complete":
        missing = ", ".join(assessment.missing) or "its context"
        raise ValueError(
            f"only a complete approval moment stands on a "
            f"card - this moment is incomplete, missing "
            f"{missing}")
    held = assessment.moment
    if context is None:
        context = (held.what, held.where, held.what_it_does)
    if operation is None:
        operation = " ".join(
            part for part in (command, *tuple(args)) if part)
    return ApprovalCard(
        card_id=card_id, decision=held.what,
        operation=operation, target=held.where,
        consequence=held.what_it_does, context=context,
        command=command, args=tuple(args), path=path,
        destructive=destructive,
        recorded_on=recorded_on, actor=actor,
        source=source, origin_session=origin_session)


def inspect_operation_source(piece: Any) -> Dict[str, Any]:
    """Judge one raw operation piece and name what it is.

    A piece shaped like an operation - a mapping
    carrying an ``operation`` (or ``command_text``)
    - is judged through the shipped doctrine and
    read onto the alarm level it derives, without
    holding a card. Anything else is named
    not-an-operation.
    """
    from .destructive_doctrine import judge_command
    if not isinstance(piece, dict):
        return {"alarm": None, "destructive": None,
                "reason": "not a mapping - no operation stands here"}
    operation = _pick_any(
        piece, ("operation", "command_text"), "operation")
    if operation is None:
        return {"alarm": None, "destructive": None,
                "reason": "no operation named - no card stands here"}
    try:
        judgement = judge_command(operation)
    except ValueError as exc:
        return {"alarm": None, "destructive": None,
                "operation": operation, "reason": str(exc)}
    destructive = judgement.rung == "irreversible"
    return {
        "alarm": "alarm" if destructive else "calm",
        "destructive": destructive,
        "rung": judgement.rung,
        "operation": judgement.command,
        "reason": "an operation judged by the shipped doctrine"}


# ---------------------------------------------------------------------
# The decision record: one card's answer, held whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class CardDecision:
    """One card's answer, held as its own record.

    ``card_id`` is the card answered; ``answer`` is
    the answer in the closed answer set - allow,
    reject or remember; ``detail`` is the answer's
    own words. A remember answer carries no scope
    of its own: the remembered scope is the card's
    own derived scope, never a scope the answer
    could widen. ``seq`` is the answer's place in
    the book's recorded order, from 1. The
    provenance rides whole.
    """

    seq: int
    card_id: str
    answer: str
    detail: str
    recorded_on: str
    actor: str
    source: str
    origin_session: str
    decision_id: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "card_id", _check_word(self.card_id, "a card id"))
        object.__setattr__(self, "answer", normalize_answer(self.answer))
        object.__setattr__(
            self, "detail",
            _check_long_text(self.detail, "the answer's words"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))
        object.__setattr__(
            self, "actor", _check_title(self.actor, "an actor"))
        object.__setattr__(
            self, "source", _check_title(self.source, "a source"))
        object.__setattr__(
            self, "origin_session",
            _check_word(self.origin_session, "an origin session"))
        if self.decision_id is not None:
            object.__setattr__(
                self, "decision_id",
                _check_word(self.decision_id, "a decision id"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "approval_card_decision",
            "slice": APPROVAL_CARDS_SLICE,
            "decision_id": self.decision_id,
            "seq": self.seq,
            "card_id": self.card_id,
            "answer": self.answer,
            "detail": self.detail,
            "recorded_on": self.recorded_on,
            "actor": self.actor,
            "source": self.source,
            "origin_session": self.origin_session,
        }


def _check_decision_ref(value: Any) -> CardDecision:
    if isinstance(value, CardDecision):
        return value
    return validate_decision(value)


def validate_decision(decision: Any) -> CardDecision:
    """Judge one decision record whole and return it."""
    if isinstance(decision, CardDecision):
        return decision
    if not isinstance(decision, dict):
        raise ValueError(
            f"a decision record must be a mapping, got {decision!r}")
    unknown = set(decision) - _DECISION_KEYS
    if unknown:
        raise ValueError(
            f"a decision record carries unknown keys: "
            f"{sorted(unknown)}")
    if "type" in decision:
        raise ValueError(
            "a decision record is judged without its news keys")

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(decision, spellings, what)
        if value is None:
            raise ValueError(f"a decision record names no {what}")
        return value

    return CardDecision(
        decision_id=_pick_any(
            decision, ("decision_id", "id"), "decision id"),
        seq=_needed(("seq", "sequence", "order"), "sequence"),
        card_id=_needed(("card_id", "card"), "card id"),
        answer=_needed(("answer", "choice"), "answer"),
        detail=_needed(("detail", "reason"), "the answer's words"),
        recorded_on=_needed(
            ("recorded_on", "day", "date"), "day it was recorded"),
        actor=_needed(("actor", "by", "who"), "actor"),
        source=_needed(("source",), "source"),
        origin_session=_needed(
            ("origin_session", "session"), "origin session"),
    )


def build_decision(decision: Any = None, **kwargs: Any) -> CardDecision:
    """Build one decision record from a mapping, a record, or fields."""
    if kwargs:
        if decision is not None:
            raise ValueError("a decision record is built one way at a time")
        decision = kwargs
    return validate_decision(decision)


def effective_answers(cards: Any, decisions: Any = ()) -> Dict[str, CardDecision]:
    """The answers standing on a set of cards, judged whole.

    Decisions are read in recorded order; every
    decision must answer a card that stands here,
    and a card is answered exactly once - a second
    answer standing on an answered card refuses
    the whole derivation plainly (one decision per
    card, answered once).
    """
    held = {_check_card_ref(c).card_id for c in cards}
    answers: Dict[str, CardDecision] = {}
    for decision in sorted(
            (_check_decision_ref(d) for d in decisions),
            key=lambda d: d.seq):
        if decision.card_id not in held:
            raise ValueError(
                f"a decision answers card {decision.card_id!r}, "
                f"which stands on no card of this book")
        if decision.card_id in answers:
            raise ValueError(
                f"card {decision.card_id!r} already stands "
                f"answered - one decision per card, answered "
                f"once")
        answers[decision.card_id] = decision
    return answers


# ---------------------------------------------------------------------
# The panel: the whole book, derived at a glance.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ApprovalPanelRow:
    """One card as the panel carries it.

    The row carries the card's id, its one
    decision, its target as its own line, its
    DERIVED alarm level, the answer standing on
    it (or ``awaiting`` while none does), its
    DERIVED card line and its recorded day. The
    operation and the context never stand in a
    row - the panel is the book at a glance.
    """

    card_id: str
    decision: str
    target: str
    alarm: str
    answer: str
    line: str
    recorded_on: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "card_id", _check_word(self.card_id, "a card id"))
        object.__setattr__(
            self, "decision",
            _check_title(self.decision, "the card's one decision"))
        object.__setattr__(
            self, "target", _check_title(self.target, "the target"))
        object.__setattr__(self, "alarm", normalize_alarm(self.alarm))
        answer = self.answer
        if answer != "awaiting":
            answer = normalize_answer(answer)
        object.__setattr__(self, "answer", answer)
        object.__setattr__(
            self, "line", _check_long_text(self.line, "a card line"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))

    def sort_key(self) -> Tuple[str]:
        return (self.card_id,)

    def to_record(self) -> Dict[str, Any]:
        return {
            "card_id": self.card_id,
            "decision": self.decision,
            "target": self.target,
            "alarm": self.alarm,
            "answer": self.answer,
            "line": self.line,
            "recorded_on": self.recorded_on,
        }


def _row_for_card(card: ApprovalCard,
                  decision: Optional[CardDecision]) -> ApprovalPanelRow:
    return ApprovalPanelRow(
        card_id=card.card_id, decision=card.decision,
        target=card.target, alarm=alarm_of(card),
        answer=decision.answer if decision is not None else "awaiting",
        line=line_of(card), recorded_on=card.recorded_on)


def _check_row_ref(value: Any) -> ApprovalPanelRow:
    if isinstance(value, ApprovalPanelRow):
        return value
    return validate_row(value)


def validate_row(row: Any, card: Any = None,
                 decision: Any = None) -> ApprovalPanelRow:
    """Judge one panel row, against its card when named."""
    if isinstance(row, ApprovalPanelRow):
        current = row
    elif isinstance(row, dict):
        unknown = set(row) - _ROW_KEYS
        if unknown:
            raise ValueError(
                f"an approval panel row carries unknown keys: "
                f"{sorted(unknown)}")

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            value = _pick_any(row, spellings, what)
            if value is None:
                raise ValueError(f"an approval panel row names no {what}")
            return value

        current = ApprovalPanelRow(
            card_id=_needed(("card_id", "id"), "card id"),
            decision=_needed(("decision",), "decision"),
            target=_needed(("target",), "target"),
            alarm=_needed(("alarm",), "alarm level"),
            answer=_needed(("answer",), "answer"),
            line=_needed(("line",), "card line"),
            recorded_on=_needed(("recorded_on",), "day it was recorded"))
    else:
        raise ValueError(
            f"an approval panel row must be a mapping, got {row!r}")
    if card is not None:
        held = _check_card_ref(card)
        standing = None
        if decision is not None:
            standing = _check_decision_ref(decision)
            if standing.card_id != held.card_id:
                raise ValueError(
                    "a panel row's decision answers another card")
        wanted = _row_for_card(held, standing)
        if current != wanted:
            raise ValueError(
                "an approval panel row must be its card's own "
                "row - the alarm level and the card line are "
                "derived from the card, never written beside it")
    return current


def build_row(row: Any = None, card: Any = None,
              decision: Any = None,
              **kwargs: Any) -> ApprovalPanelRow:
    """Build one panel row from a mapping, a row, or its card."""
    if card is not None:
        if row is not None or kwargs:
            return validate_row(
                row if row is not None else kwargs, card, decision)
        standing = (
            _check_decision_ref(decision)
            if decision is not None else None)
        return _row_for_card(_check_card_ref(card), standing)
    if kwargs:
        if row is not None:
            raise ValueError("a row is built one way at a time")
        row = kwargs
    return validate_row(row)


@dataclass(frozen=True)
class AnswerCount:
    """How many cards of one answer a panel holds."""

    answer: str
    items: int

    def __post_init__(self) -> None:
        answer = self.answer
        if answer != "awaiting":
            answer = normalize_answer(answer)
        object.__setattr__(self, "answer", answer)
        object.__setattr__(
            self, "items", _check_count(self.items, "an answer's items"))

    def to_record(self) -> Dict[str, Any]:
        return {"answer": self.answer, "items": self.items}


def _check_answer_count_ref(value: Any) -> AnswerCount:
    if isinstance(value, AnswerCount):
        return value
    if isinstance(value, dict):
        unknown = set(value) - _ANSWER_COUNT_KEYS
        if unknown:
            raise ValueError(
                f"an answer count carries unknown keys: "
                f"{sorted(unknown)}")
        answer = _pick_any(value, ("answer",), "answer")
        items = _pick_any(value, ("items", "count"), "items")
        if answer is None or items is None:
            raise ValueError("an answer count names its answer and its items")
        return AnswerCount(answer=answer, items=items)
    raise ValueError(f"an answer count must be a mapping, got {value!r}")


def _answer_counts(rows: Tuple[ApprovalPanelRow, ...]) -> Tuple[AnswerCount, ...]:
    counts: Dict[str, int] = {}
    for row in rows:
        counts[row.answer] = counts.get(row.answer, 0) + 1
    return tuple(
        AnswerCount(answer=answer, items=counts[answer])
        for answer in ANSWER_WORDS if answer in counts)


def _panel_account(total_cards: int, total_destructive: int,
                   total_alarmed: int, total_allowed: int,
                   total_rejected: int, total_remembered: int,
                   total_awaiting: int,
                   answer_counts: Tuple[AnswerCount, ...],
                   as_of: str) -> Tuple[str, ...]:
    answers = ", ".join(
        f"{count.answer} {count.items}" for count in answer_counts)
    return (
        f"The approval cards hold {total_cards} cards as of "
        f"{as_of}: {total_allowed} allowed, {total_rejected} "
        f"rejected and {total_remembered} remembered, with "
        f"{total_awaiting} still awaiting an answer: "
        f"{answers}; {total_destructive} cards ask about a "
        f"destructive operation and {total_alarmed} of them "
        f"stand alarmed and unanswered.",
        "Rows stand in held order, first card first, so "
        "two panels of one book diff cleanly, line by line.",
        "Every row carries its target as its own line and "
        "its alarm level as a word: alarm is reserved for "
        "destructive operations, and routine cards stand "
        "calm.",
        "Every card offers its remembered scope at exactly "
        "its own act - this command, these arguments, this "
        "project - and keyboard and mouse offer the same "
        "acts in the same order on every card.",
    )


@dataclass(frozen=True)
class ApprovalPanel:
    """The derived panel of one book: the cards at a glance.

    Rows stand in held card order; the totals are
    the rows' own counts; ``total_alarmed`` counts
    the destructive rows still awaiting an answer.
    A stored panel is judged whole in
    ``__post_init__``: its totals, its answer
    counts, its as-of day and its account must all
    be the rows' own derived shape - a panel may
    not soften its book.
    """

    panel_id: Optional[str]
    rows: Tuple[ApprovalPanelRow, ...]
    total_cards: int
    total_destructive: int
    total_alarmed: int
    total_allowed: int
    total_rejected: int
    total_remembered: int
    total_awaiting: int
    answer_counts: Tuple[AnswerCount, ...]
    as_of: str
    account: Tuple[str, ...]

    def __post_init__(self) -> None:
        if self.panel_id is not None:
            object.__setattr__(
                self, "panel_id",
                _check_word(self.panel_id, "a panel id"))
        rows = tuple(_check_row_ref(r) for r in self.rows)
        object.__setattr__(self, "rows", rows)
        ids = [r.card_id for r in rows]
        if len(set(ids)) != len(ids):
            raise ValueError("panel rows stand one row per card")
        for field in ("total_cards", "total_destructive",
                      "total_alarmed", "total_allowed",
                      "total_rejected", "total_remembered",
                      "total_awaiting"):
            object.__setattr__(
                self, field,
                _check_count(getattr(self, field), f"a panel's {field}"))
        counts = tuple(
            _check_answer_count_ref(c) for c in self.answer_counts)
        object.__setattr__(self, "answer_counts", counts)
        object.__setattr__(self, "as_of", _check_day(self.as_of, "an as-of day"))
        object.__setattr__(self, "account", _check_account(self.account))
        if self.total_cards != len(rows):
            raise ValueError("a panel's total is its rows' own count")
        if self.total_destructive != sum(
                1 for r in rows if r.alarm == "alarm"):
            raise ValueError(
                "a panel's destructive total is its alarmed "
                "rows' own count")
        if self.total_alarmed != sum(
                1 for r in rows
                if r.alarm == "alarm" and r.answer == "awaiting"):
            raise ValueError(
                "a panel's alarmed total is its unanswered "
                "alarmed rows' own count")
        for answer, field in (
                ("allow", "total_allowed"),
                ("reject", "total_rejected"),
                ("remember", "total_remembered"),
                ("awaiting", "total_awaiting")):
            if getattr(self, field) != sum(
                    1 for r in rows if r.answer == answer):
                raise ValueError(
                    f"a panel's {answer} total is its rows' own count")
        if counts != _answer_counts(rows):
            raise ValueError("a panel's answer counts are its rows' own counts")
        if rows and self.as_of != max(r.recorded_on for r in rows):
            raise ValueError(
                "a panel's as-of day is its rows' latest recorded day")
        if self.account != _panel_account(
                self.total_cards, self.total_destructive,
                self.total_alarmed, self.total_allowed,
                self.total_rejected, self.total_remembered,
                self.total_awaiting, counts, self.as_of):
            raise ValueError(
                "a panel's account is its rows' own account, "
                "derived, never written loose")

    def row_for(self, card_id: Any) -> ApprovalPanelRow:
        """The row one card id names (KeyError if absent)."""
        wanted = _check_word(card_id, "a card id")
        for row in self.rows:
            if row.card_id == wanted:
                return row
        raise KeyError(f"no row named {wanted!r} stands on the panel")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "approval_cards_panel",
            "slice": APPROVAL_CARDS_SLICE,
            "panel_id": self.panel_id,
            "rows": [r.to_record() for r in self.rows],
            "total_cards": self.total_cards,
            "total_destructive": self.total_destructive,
            "total_alarmed": self.total_alarmed,
            "total_allowed": self.total_allowed,
            "total_rejected": self.total_rejected,
            "total_remembered": self.total_remembered,
            "total_awaiting": self.total_awaiting,
            "answer_counts": [c.to_record() for c in self.answer_counts],
            "as_of": self.as_of,
            "account": list(self.account),
        }


def _held_cards(source: Any) -> Tuple[ApprovalCard, ...]:
    if isinstance(source, ApprovalCardsBook):
        return source.cards
    if isinstance(source, ApprovalCardRegistry):
        return source.list_cards()
    if isinstance(source, ApprovalCard):
        return (source,)
    raise ValueError(f"an approval-cards source is needed, got {source!r}")


def _held_decisions(source: Any) -> Tuple[CardDecision, ...]:
    if isinstance(source, ApprovalCardsBook):
        return source.decisions
    if isinstance(source, ApprovalCardRegistry):
        return source.list_decisions()
    return ()


def derive_panel(source: Any) -> ApprovalPanel:
    """Derive the panel of a book, registry or card."""
    cards = _held_cards(source)
    answers = effective_answers(cards, _held_decisions(source))
    rows = tuple(
        _row_for_card(c, answers.get(c.card_id)) for c in cards)
    counts = _answer_counts(rows)
    totals = {
        answer: sum(1 for r in rows if r.answer == answer)
        for answer in ANSWER_WORDS}
    destructive = sum(1 for r in rows if r.alarm == "alarm")
    alarmed = sum(
        1 for r in rows
        if r.alarm == "alarm" and r.answer == "awaiting")
    as_of = max((r.recorded_on for r in rows), default=_EXAMPLE_AS_OF)
    return ApprovalPanel(
        panel_id=None, rows=rows, total_cards=len(rows),
        total_destructive=destructive, total_alarmed=alarmed,
        total_allowed=totals["allow"],
        total_rejected=totals["reject"],
        total_remembered=totals["remember"],
        total_awaiting=totals["awaiting"],
        answer_counts=counts, as_of=as_of,
        account=_panel_account(
            len(rows), destructive, alarmed, totals["allow"],
            totals["reject"], totals["remember"],
            totals["awaiting"], counts, as_of))


def validate_panel(panel: Any, source: Any = None) -> ApprovalPanel:
    """Judge one panel whole, against its source when named."""
    if isinstance(panel, ApprovalPanel):
        current = panel
    elif isinstance(panel, dict):
        data = dict(panel)
        data.pop("type", None)
        data.pop("slice", None)
        unknown = set(data) - _PANEL_KEYS
        if unknown:
            raise ValueError(
                f"an approval panel carries unknown keys: "
                f"{sorted(unknown)}")

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            value = _pick_any(data, spellings, what)
            if value is None:
                raise ValueError(f"an approval panel names no {what}")
            return value

        rows_in = _needed(("rows", "cards"), "rows")
        counts_in = _needed(("answer_counts", "answers"), "answer counts")
        current = ApprovalPanel(
            panel_id=_pick_any(data, ("panel_id", "id"), "panel id"),
            rows=tuple(validate_row(r) for r in rows_in),
            total_cards=_needed(("total_cards", "total"), "total cards"),
            total_destructive=_needed(
                ("total_destructive", "destructive"), "destructive total"),
            total_alarmed=_needed(
                ("total_alarmed", "alarmed"), "alarmed total"),
            total_allowed=_needed(
                ("total_allowed", "allowed"), "allowed total"),
            total_rejected=_needed(
                ("total_rejected", "rejected"), "rejected total"),
            total_remembered=_needed(
                ("total_remembered", "remembered"), "remembered total"),
            total_awaiting=_needed(
                ("total_awaiting", "awaiting"), "awaiting total"),
            answer_counts=tuple(
                _check_answer_count_ref(c) for c in counts_in),
            as_of=_needed(("as_of", "day"), "as-of day"),
            account=tuple(_needed(("account", "statements"), "account")))
    else:
        raise ValueError(f"an approval panel must be a mapping, got {panel!r}")
    if source is not None:
        derived = derive_panel(source)
        if (current.rows != derived.rows
                or current.total_cards != derived.total_cards
                or current.total_destructive != derived.total_destructive
                or current.total_alarmed != derived.total_alarmed
                or current.total_allowed != derived.total_allowed
                or current.total_rejected != derived.total_rejected
                or current.total_remembered != derived.total_remembered
                or current.total_awaiting != derived.total_awaiting
                or current.answer_counts != derived.answer_counts
                or current.as_of != derived.as_of
                or current.account != derived.account):
            raise ValueError(
                "a stored panel must equal the panel its book "
                "derives - the panel is derived, never stored loose")
    return current


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> ApprovalPanel:
    """Build one panel from a mapping, a panel, or its source."""
    if kwargs:
        if panel is not None:
            raise ValueError("a panel is built one way at a time")
        panel = kwargs
    if panel is None and source is not None:
        return derive_panel(source)
    return validate_panel(panel, source)


# ---------------------------------------------------------------------
# The verdict: the whole book, judged in one word.
# ---------------------------------------------------------------------


def _verdict_word(total_cards: int, total_alarmed: int,
                  total_awaiting: int) -> str:
    if total_alarmed > 0:
        return "alarmed"
    if total_cards > 0 and total_awaiting == 0:
        return "complete"
    return "waiting"


@dataclass(frozen=True)
class ApprovalVerdict:
    """The derived verdict of one whole book of cards.

    The word is read off the tallies alone:
    alarmed while a destructive card stands
    unanswered, complete while every card stands
    answered, waiting while the book only waits.
    A stored verdict is judged against those
    tallies in ``__post_init__``.
    """

    total_cards: int
    total_destructive: int
    total_alarmed: int
    total_allowed: int
    total_rejected: int
    total_remembered: int
    total_awaiting: int
    earliest_on: str
    latest_on: str
    verdict: str

    def __post_init__(self) -> None:
        for field in ("total_cards", "total_destructive",
                      "total_alarmed", "total_allowed",
                      "total_rejected", "total_remembered",
                      "total_awaiting"):
            object.__setattr__(
                self, field,
                _check_count(getattr(self, field), f"a verdict's {field}"))
        object.__setattr__(
            self, "earliest_on", _check_day(self.earliest_on, "an earliest day"))
        object.__setattr__(
            self, "latest_on", _check_day(self.latest_on, "a latest day"))
        if self.latest_on < self.earliest_on:
            raise ValueError("a verdict's latest day precedes its earliest")
        if self.total_cards != (
                self.total_allowed + self.total_rejected
                + self.total_remembered + self.total_awaiting):
            raise ValueError(
                "a verdict's tallies must close on its total")
        if self.total_alarmed > self.total_destructive:
            raise ValueError(
                "a verdict's alarmed tally cannot exceed its "
                "destructive tally")
        if self.total_alarmed > self.total_awaiting:
            raise ValueError(
                "a verdict's alarmed tally cannot exceed its "
                "awaiting tally")
        word = _clean_text(self.verdict, "a verdict")
        if word not in VERDICT_WORDS:
            raise ValueError(
                f"a verdict is one of {VERDICT_WORDS}, got {word!r}")
        object.__setattr__(self, "verdict", word)
        if word != _verdict_word(
                self.total_cards, self.total_alarmed,
                self.total_awaiting):
            raise ValueError(
                "a verdict's word is derived from its tallies, "
                "never chosen")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "approval_cards_verdict",
            "slice": APPROVAL_CARDS_SLICE,
            "total_cards": self.total_cards,
            "total_destructive": self.total_destructive,
            "total_alarmed": self.total_alarmed,
            "total_allowed": self.total_allowed,
            "total_rejected": self.total_rejected,
            "total_remembered": self.total_remembered,
            "total_awaiting": self.total_awaiting,
            "earliest_on": self.earliest_on,
            "latest_on": self.latest_on,
            "verdict": self.verdict,
        }


def derive_verdict(source: Any) -> ApprovalVerdict:
    """Derive the verdict of a book, registry or card."""
    cards = _held_cards(source)
    answers = effective_answers(cards, _held_decisions(source))
    totals = {answer: 0 for answer in ANSWER_WORDS}
    destructive = 0
    alarmed = 0
    for card in cards:
        standing = answers.get(card.card_id)
        answer = standing.answer if standing is not None else "awaiting"
        totals[answer] += 1
        if card.destructive:
            destructive += 1
            if standing is None:
                alarmed += 1
    days = [c.recorded_on for c in cards]
    return ApprovalVerdict(
        total_cards=len(cards), total_destructive=destructive,
        total_alarmed=alarmed, total_allowed=totals["allow"],
        total_rejected=totals["reject"],
        total_remembered=totals["remember"],
        total_awaiting=totals["awaiting"],
        earliest_on=min(days) if days else _EXAMPLE_AS_OF,
        latest_on=max(days) if days else _EXAMPLE_AS_OF,
        verdict=_verdict_word(len(cards), alarmed, totals["awaiting"]))


def _check_verdict_ref(value: Any) -> ApprovalVerdict:
    if isinstance(value, ApprovalVerdict):
        return value
    return validate_verdict(value)


def validate_verdict(verdict: Any, source: Any = None) -> ApprovalVerdict:
    """Judge one verdict whole, against its source when named."""
    if isinstance(verdict, ApprovalVerdict):
        current = verdict
    elif isinstance(verdict, dict):
        data = dict(verdict)
        data.pop("type", None)
        data.pop("slice", None)
        unknown = set(data) - _VERDICT_KEYS
        if unknown:
            raise ValueError(
                f"an approval verdict carries unknown keys: "
                f"{sorted(unknown)}")

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            value = _pick_any(data, spellings, what)
            if value is None:
                raise ValueError(f"an approval verdict names no {what}")
            return value

        current = ApprovalVerdict(
            total_cards=_needed(("total_cards", "total"), "total cards"),
            total_destructive=_needed(
                ("total_destructive", "destructive"), "destructive total"),
            total_alarmed=_needed(
                ("total_alarmed", "alarmed"), "alarmed total"),
            total_allowed=_needed(
                ("total_allowed", "allowed"), "allowed total"),
            total_rejected=_needed(
                ("total_rejected", "rejected"), "rejected total"),
            total_remembered=_needed(
                ("total_remembered", "remembered"), "remembered total"),
            total_awaiting=_needed(
                ("total_awaiting", "awaiting"), "awaiting total"),
            earliest_on=_needed(("earliest_on", "earliest"), "earliest day"),
            latest_on=_needed(("latest_on", "latest"), "latest day"),
            verdict=_needed(("verdict",), "verdict"))
    else:
        raise ValueError(f"an approval verdict must be a mapping, got {verdict!r}")
    if source is not None:
        derived = derive_verdict(source)
        if current != derived:
            raise ValueError(
                "a stored verdict must equal the verdict its "
                "book derives - the verdict is derived, never "
                "stored loose")
    return current


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> ApprovalVerdict:
    """Build one verdict from a mapping, a verdict, or its source."""
    if kwargs:
        if verdict is not None:
            raise ValueError("a verdict is built one way at a time")
        verdict = kwargs
    if verdict is None and source is not None:
        return derive_verdict(source)
    return validate_verdict(verdict, source)


# ---------------------------------------------------------------------
# The book: one set of cards, held whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ApprovalCardsBook:
    """One set of approval cards, held whole.

    Cards stand in held order - one card per card
    id - decisions stand in recorded order, one
    decision per sequence and per id, every
    decision must stand legally on the cards it
    answers (the effective answers are derived in
    ``__post_init__``), and every stored panel is
    judged against the book it stands in.
    """

    title: str
    cards: Tuple[ApprovalCard, ...] = ()
    decisions: Tuple[CardDecision, ...] = ()
    panels: Tuple[ApprovalPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book title"))
        cards = tuple(_check_card_ref(c) for c in self.cards)
        object.__setattr__(self, "cards", cards)
        ids = [c.card_id for c in cards]
        if len(set(ids)) != len(ids):
            raise ValueError("a book holds one card per card id")
        decisions = tuple(_check_decision_ref(d) for d in self.decisions)
        object.__setattr__(self, "decisions", decisions)
        seqs = [d.seq for d in decisions]
        if seqs != sorted(seqs) or len(set(seqs)) != len(seqs):
            raise ValueError(
                "a book's decisions stand in recorded order, "
                "one decision per sequence")
        decision_ids = [
            d.decision_id for d in decisions if d.decision_id is not None]
        if len(set(decision_ids)) != len(decision_ids):
            raise ValueError("a book holds one decision per decision id")
        # Every held decision must stand legally on
        # the cards of this book.
        effective_answers(cards, decisions)
        panels = tuple(
            validate_panel(p, self) for p in self.panels)
        object.__setattr__(self, "panels", panels)

    def card_for(self, card_id: Any) -> ApprovalCard:
        """The card one id names (KeyError if absent)."""
        wanted = _check_word(card_id, "a card id")
        for card in self.cards:
            if card.card_id == wanted:
                return card
        raise KeyError(f"no card named {wanted!r} stands in the book")

    def decision_for(self, decision_id: Any) -> CardDecision:
        """The decision record one id names (KeyError if absent)."""
        wanted = _check_word(decision_id, "a decision id")
        for decision in self.decisions:
            if decision.decision_id == wanted:
                return decision
        raise KeyError(f"no decision named {wanted!r} stands in the book")

    def answer_for(self, card_id: Any) -> Optional[CardDecision]:
        """The decision standing on one card, or None while it waits."""
        wanted = _check_word(card_id, "a card id")
        self.card_for(wanted)
        for decision in self.decisions:
            if decision.card_id == wanted:
                return decision
        return None

    def panel_for(self, panel_id: Any) -> ApprovalPanel:
        """The panel one id names (KeyError if absent)."""
        wanted = _check_word(panel_id, "a panel id")
        for panel in self.panels:
            if panel.panel_id == wanted:
                return panel
        raise KeyError(f"no panel named {wanted!r} stands in the book")

    def card_ids(self) -> Tuple[str, ...]:
        """The book's card ids, in held order."""
        return tuple(c.card_id for c in self.cards)

    def decision_ids(self) -> Tuple[Optional[str], ...]:
        """The book's decision ids, in recorded order."""
        return tuple(d.decision_id for d in self.decisions)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "approval_cards_book",
            "slice": APPROVAL_CARDS_SLICE,
            "title": self.title,
            "cards": [c.to_record() for c in self.cards],
            "decisions": [d.to_record() for d in self.decisions],
            "panels": [p.to_record() for p in self.panels],
            "card_count": len(self.cards),
            "decision_count": len(self.decisions),
        }


def _judge_book_panels(book: ApprovalCardsBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def validate_book(data: Any, *, require_example: bool = False) -> ApprovalCardsBook:
    """Judge one card file's data whole and return its book."""
    if isinstance(data, ApprovalCardsBook):
        book = data
        _judge_book_panels(book)
        if require_example:
            _check_example(book)
        return book
    if not isinstance(data, dict):
        raise ValueError(f"an approval-cards book must be a mapping, got {data!r}")
    unknown = set(data) - _APPROVAL_CARDS_KEYS - {"guide"}
    if unknown:
        raise ValueError(
            f"an approval-cards book carries unknown keys: {sorted(unknown)}")
    if data.get("schema") != APPROVAL_CARDS_SCHEMA:
        raise ValueError(
            f"an approval-cards book's schema must be "
            f"{APPROVAL_CARDS_SCHEMA!r}, got {data.get('schema')!r}")
    if data.get("slice") != APPROVAL_CARDS_SLICE:
        raise ValueError(
            f"an approval-cards book's slice must be "
            f"{APPROVAL_CARDS_SLICE!r}, got {data.get('slice')!r}")
    guide = data.get("guide") or {}
    title = _pick_any(guide, ("title", "name"), "title")
    if title is None:
        title = _pick_any(data, ("title", "name"), "title")
    cards_in = _pick_any(data, ("cards",), "cards")
    if cards_in is None:
        raise ValueError("an approval-cards book names no cards")
    decisions_in = data.get("decisions") or []
    panels_in = data.get("panels") or []
    cards = []
    for raw in cards_in:
        stored = dict(raw)
        stored.pop("type", None)
        stored.pop("slice", None)
        for derived_key in (
                "line", "alarm", "scope", "scope_id",
                "scope_line", "keyboard", "mouse"):
            stored.pop(derived_key, None)
        stored["args"] = stored.pop("args", None)
        cards.append(validate_card(stored))
    decisions = []
    for raw in decisions_in:
        stored = dict(raw)
        stored.pop("type", None)
        stored.pop("slice", None)
        decisions.append(validate_decision(stored))
    book = ApprovalCardsBook(
        title=title,
        cards=tuple(cards),
        decisions=tuple(decisions),
        panels=tuple(validate_panel(p) for p in panels_in))
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def _check_example(book: ApprovalCardsBook) -> None:
    if book.title != _EXAMPLE_TITLE:
        raise ValueError(
            f"the shipped example book is {_EXAMPLE_TITLE!r}, "
            f"got {book.title!r}")
    if book.card_ids() != _EXAMPLE_CARD_IDS:
        raise ValueError("the shipped example book's cards differ")
    first = book.cards[0]
    if first.card_id != _EXAMPLE_FIRST_CARD_ID or (
            first.decision != _EXAMPLE_FIRST_CARD_DECISION):
        raise ValueError("the shipped example book's first card differs")
    if book.decision_ids() != _EXAMPLE_DECISION_IDS:
        raise ValueError("the shipped example book's decisions differ")
    if len(book.panels) != 1 or (
            book.panels[0].panel_id != _EXAMPLE_PANEL_ID):
        raise ValueError("the shipped example book's panel differs")
    if book.panels[0].as_of != _EXAMPLE_AS_OF:
        raise ValueError("the shipped example book's as-of day differs")
    if tuple(r.card_id for r in book.panels[0].rows) != (
            _EXAMPLE_CARD_IDS):
        raise ValueError("the shipped example book's panel rows differ")


def build_book(book: Any = None, **kwargs: Any) -> ApprovalCardsBook:
    """Build one book from a mapping, a book, or fields."""
    if isinstance(book, ApprovalCardsBook) and not kwargs:
        return validate_book(book)
    if kwargs:
        if book is not None:
            raise ValueError("a book is built one way at a time")
        fields = dict(kwargs)
    elif isinstance(book, dict) and (
            "cards" in book) and (
            "schema" not in book and "guide" not in book
            and "canon_note" not in book):
        fields = dict(book)
    else:
        return _book_from(book, require_example=False)
    unknown = set(fields) - _BOOK_KEYS - {
        "cards", "decisions", "panels"}
    if unknown:
        raise ValueError(
            f"an approval-cards book carries unknown keys: "
            f"{sorted(unknown)}")
    title = _pick_any(fields, ("title", "name"), "title")
    if title is None:
        raise ValueError("an approval-cards book names no title")
    cards_in = _pick_any(fields, ("cards",), "cards") or ()
    return ApprovalCardsBook(
        title=title,
        cards=tuple(_check_card_ref(c) for c in cards_in),
        decisions=tuple(
            _check_decision_ref(d) for d in fields.get("decisions") or ()),
        panels=tuple(
            validate_panel(p) for p in fields.get("panels") or ()))


def _book_from(data: Any, *, require_example: bool) -> ApprovalCardsBook:
    if isinstance(data, ApprovalCardsBook):
        return validate_book(data, require_example=require_example)
    if isinstance(data, dict):
        return validate_book(data, require_example=require_example)
    raise ValueError(f"an approval-cards book must be a mapping, got {data!r}")


def load_approval_cards(data: Optional[Dict[str, Any]] = None) -> ApprovalCardsBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(APPROVAL_CARDS_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_approval_cards_file(path: Any) -> ApprovalCardsBook:
    """Load one card file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: cards and decisions held one by one.
# ---------------------------------------------------------------------


class ApprovalCardRegistry:
    """An in-memory holding of approval cards and decisions.

    The registry is the pure layer's model of a
    session's cards: cards are held under their
    card ids, one card per id, in held order, and
    decisions are held in recorded order, each
    judged against the held cards before it is
    held - a decision answering no held card, or
    answering a card that already stands answered,
    refuses and holds nothing. Holding is data
    only - no card held here runs its operation,
    executes its approval or saves its remembered
    scope.
    """

    def __init__(self, book: Any = None) -> None:
        self._cards: List[ApprovalCard] = []
        self._decisions: List[CardDecision] = []
        self._title: Optional[str] = None
        if book is not None:
            self.register_book(book)

    def title(self) -> Optional[str]:
        return self._title

    def _fresh_decision_id(self, held_ids: Any) -> str:
        n = 1
        while f"dec-{n}" in held_ids:
            n += 1
        return f"dec-{n}"

    def _check_card_free(self, card: ApprovalCard) -> None:
        for held in self._cards:
            if held.card_id == card.card_id:
                raise ValueError(
                    f"a card already stands under id "
                    f"{card.card_id!r}")

    def register_card(self, card: Any) -> ApprovalCard:
        """Hold one card, judged whole before it is held."""
        validated = _check_card_ref(card)
        self._check_card_free(validated)
        self._cards.append(validated)
        return validated

    def _check_decision_stands(self, decision: CardDecision) -> None:
        for held in self._decisions:
            if decision.decision_id is not None and (
                    held.decision_id == decision.decision_id):
                raise ValueError(
                    f"a decision already stands under id "
                    f"{decision.decision_id!r}")
            if held.seq == decision.seq:
                raise ValueError(
                    f"a decision already stands at sequence "
                    f"{decision.seq} - the book holds one "
                    f"answer per place")
        # The answer must stand legally on the cards
        # held here, judged before it is held.
        effective_answers(
            self._cards, tuple(self._decisions) + (decision,))

    def register_decision(self, decision: Any) -> CardDecision:
        """Hold one decision record, judged whole first.

        The decision is judged against the held
        cards before it is held - an answer standing
        on no held card, or on a card that already
        stands answered, refuses and holds nothing
        new.
        """
        validated = _check_decision_ref(decision)
        self._check_decision_stands(validated)
        if validated.decision_id is None:
            validated = CardDecision(
                decision_id=self._fresh_decision_id(
                    {d.decision_id for d in self._decisions}),
                seq=validated.seq, card_id=validated.card_id,
                answer=validated.answer, detail=validated.detail,
                recorded_on=validated.recorded_on,
                actor=validated.actor, source=validated.source,
                origin_session=validated.origin_session)
        self._decisions.append(validated)
        self._decisions.sort(key=lambda d: d.seq)
        return validated

    def register_book(self, book: Any) -> ApprovalCardsBook:
        """Hold a whole book, judged whole first."""
        validated = build_book(book)
        for card in validated.cards:
            self._check_card_free(card)
        if self._title is None:
            self._title = validated.title
        elif validated.title != self._title:
            raise ValueError(
                "a second book under a different title refuses - "
                "one book stands in one registry")
        for card in validated.cards:
            self._cards.append(card)
        for decision in validated.decisions:
            self.register_decision(decision)
        return self.book()

    def get_card(self, card_id: Any) -> ApprovalCard:
        """The card one id names (KeyError if absent)."""
        wanted = _check_word(card_id, "a card id")
        for card in self._cards:
            if card.card_id == wanted:
                return card
        raise KeyError(f"no card named {wanted!r} stands held")

    def get_decision(self, decision_id: Any) -> CardDecision:
        """The decision record one id names (KeyError if absent)."""
        wanted = _check_word(decision_id, "a decision id")
        for decision in self._decisions:
            if decision.decision_id == wanted:
                return decision
        raise KeyError(f"no decision named {wanted!r} stands held")

    def answer_for(self, card_id: Any) -> Optional[CardDecision]:
        """The decision standing on one held card, or None."""
        wanted = _check_word(card_id, "a card id")
        self.get_card(wanted)
        for decision in self._decisions:
            if decision.card_id == wanted:
                return decision
        return None

    def latest_decision(self) -> CardDecision:
        """The last decision recorded (KeyError if none)."""
        if not self._decisions:
            raise KeyError("no decision stands held")
        return self._decisions[-1]

    def list_cards(self) -> Tuple[ApprovalCard, ...]:
        return tuple(self._cards)

    def list_decisions(self) -> Tuple[CardDecision, ...]:
        return tuple(self._decisions)

    def book(self) -> ApprovalCardsBook:
        return ApprovalCardsBook(
            title=self._title or "Approval Cards",
            cards=tuple(self._cards),
            decisions=tuple(self._decisions))

    def panel(self) -> ApprovalPanel:
        return derive_panel(self.book())

    def verdict(self) -> ApprovalVerdict:
        return derive_verdict(self.book())


def cards_with_alarm(source: Any, alarm: Any) -> Tuple[ApprovalCard, ...]:
    """The cards of one derived alarm level, in held order."""
    wanted = normalize_alarm(alarm)
    return tuple(
        c for c in _held_cards(source) if alarm_of(c) == wanted)


def total_cards(source: Any) -> int:
    """How many cards a source holds."""
    return len(_held_cards(source))


# ---------------------------------------------------------------------
# Session news, plain words, and the screens.
# ---------------------------------------------------------------------


def card_record(card: Any) -> Dict[str, Any]:
    """The session-news record of one approval card."""
    current = _check_card_ref(card)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Approval card {current.card_id}: "
        f"{line_of(current)} - target: {current.target}.")
    return record_out


def decision_record(decision: Any) -> Dict[str, Any]:
    """The session-news record of one decision record."""
    current = _check_decision_ref(decision)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Approval card {current.card_id} answered "
        f"{current.answer}: {current.detail}")
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived panel."""
    current = validate_panel(panel, source)
    record = current.to_record()
    record["news"] = True
    answers = ", ".join(
        f"{c.answer} {c.items}" for c in current.answer_counts)
    record["headline"] = (
        f"Approval cards panel as of {current.as_of}: "
        f"{current.total_cards} cards - {current.total_allowed} "
        f"allowed, {current.total_rejected} rejected, "
        f"{current.total_remembered} remembered, "
        f"{current.total_awaiting} awaiting ({answers}); "
        f"{current.total_alarmed} stand alarmed.")
    return record


def verdict_record(verdict: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived verdict."""
    current = validate_verdict(verdict, source)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Approval cards verdict: {current.verdict} - "
        f"{current.total_allowed + current.total_rejected + current.total_remembered} "
        f"of {current.total_cards} cards answered, "
        f"{current.total_alarmed} alarmed and unanswered, from "
        f"{current.earliest_on} to {current.latest_on}.")
    return record


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one book of cards."""
    current = book if isinstance(book, ApprovalCardsBook) else build_book(book)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Approval cards {current.title}: "
        f"{record['card_count']} cards named, "
        f"{record['decision_count']} decisions held.")
    return record


def plain_words(card: Any) -> str:
    """One card, in one plain sentence."""
    current = _check_card_ref(card)
    alarm = (
        " It stands alarmed: the operation is destructive."
        if current.destructive else
        " It stands calm: the operation is routine.")
    return (
        f"{line_of(current)} - one decision on card "
        f"{current.card_id}: the target is "
        f"{current.target}, and the card offers to "
        f"remember exactly this scope: "
        f"{scope_line_of(current)}.{alarm}")


def decision_plain_words(decision: Any) -> str:
    """One decision record, in one plain sentence."""
    current = _check_decision_ref(decision)
    scope = ""
    if current.answer == "remember":
        scope = (
            " The remembered scope is the card's own "
            "derived scope, never broader.")
    return (
        f"Card {current.card_id} is answered "
        f"{current.answer}, recorded on "
        f"{current.recorded_on} by {current.actor}: "
        f"{current.detail}{scope}")


def panel_plain_words(source: Any) -> str:
    """The panel in plain words, in full."""
    if isinstance(source, ApprovalPanel):
        panel = validate_panel(source)
        title = None
    elif isinstance(source, (ApprovalCardsBook, ApprovalCardRegistry)):
        panel = derive_panel(source)
        title = source.title if isinstance(
            source, ApprovalCardsBook) else None
    else:
        raise ValueError(f"an approval-cards source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Cards, in held order:")
    for row in panel.rows:
        lines.append(
            f"{row.card_id}: {row.line} "
            f"(target {row.target}, answer {row.answer}, "
            f"{row.recorded_on})")
    lines.extend(panel.account)
    return "\n".join(lines)


def verdict_plain_words(source: Any) -> str:
    """The book verdict in plain words, in full."""
    if isinstance(source, ApprovalVerdict):
        verdict = validate_verdict(source)
    elif isinstance(source, (ApprovalCardsBook, ApprovalCardRegistry)):
        verdict = derive_verdict(source)
    else:
        raise ValueError(f"an approval-cards source is needed, got {source!r}")
    return (
        f"Approval cards verdict: {verdict.verdict} - "
        f"{verdict.total_allowed} allowed, "
        f"{verdict.total_rejected} rejected and "
        f"{verdict.total_remembered} remembered, "
        f"{verdict.total_awaiting} awaiting an answer, "
        f"{verdict.total_alarmed} alarmed and unanswered, "
        f"over {verdict.total_cards} cards, from "
        f"{verdict.earliest_on} to {verdict.latest_on} - "
        f"every line is derived from its card and its "
        f"held decisions.")


def _source_book(source: Any) -> ApprovalCardsBook:
    if source is None:
        return load_approval_cards()
    if isinstance(source, ApprovalCardRegistry):
        return source.book()
    if isinstance(source, ApprovalCardsBook):
        return source
    if isinstance(source, ApprovalCard):
        return ApprovalCardsBook(title="One approval card", cards=(source,))
    raise ValueError(f"an approval-cards book is needed, got {source!r}")


def format_card(card: Any) -> str:
    """One approval card as a screen block.

    The target and the consequence stand as their
    own lines, the full context stands on the
    card, the remembered scope is offered as its
    own precisely-scoped line, and the keyboard
    and mouse paths are stated side by side,
    exactly equal.
    """
    current = _check_card_ref(card)
    paths = paths_of(current)
    lines = [
        f"{current.card_id}: {line_of(current)}",
        f"Decision: {current.decision}",
        f"Operation: {current.operation}",
        f"Target: {current.target}",
        f"Consequence: {current.consequence}",
        "Context:",
    ]
    lines.extend(f"  - {statement}" for statement in current.context)
    lines.append(f"Remembered scope: {scope_line_of(current)}")
    lines.append(
        f"Keyboard: {'/'.join(paths['keyboard'])} - "
        f"Mouse: {'/'.join(paths['mouse'])} (exactly equal)")
    lines.append(
        f"Alarm: {alarm_of(current)} - "
        f"Destructive: {'yes' if current.destructive else 'no'}")
    lines.append(
        f"Recorded: on {current.recorded_on} by {current.actor} "
        f"from {current.source} in {current.origin_session}.")
    return "\n".join(lines)


def format_decision(decision: Any) -> str:
    """One decision record as a screen block."""
    current = _check_decision_ref(decision)
    lines = [
        f"{current.decision_id or '-'}: {current.answer} "
        f"{current.card_id}",
        f"Words: {current.detail}",
        f"Recorded: on {current.recorded_on} by {current.actor} "
        f"from {current.source} in {current.origin_session}.",
    ]
    return "\n".join(lines)


def format_book(source: Any = None, alarm: Any = None) -> str:
    """The book as derived lines, in held order.

    By default the lines are every card's derived
    line. With ``alarm`` only that alarm level's
    cards stand in the list.
    """
    book = _source_book(source)
    wanted = normalize_alarm(alarm) if alarm is not None else None
    lines = []
    for card in book.cards:
        if wanted is not None and alarm_of(card) != wanted:
            continue
        lines.append(f"{card.card_id}: {line_of(card)}")
    if not lines:
        lines.append("No cards stand in the book on that reading.")
    return "\n".join(lines)


def format_panel(source: Any = None) -> str:
    """The panel as a screen block: every row and the account."""
    if isinstance(source, ApprovalPanel):
        panel = validate_panel(source)
        lines: list = []
    else:
        book = _source_book(source)
        panel = derive_panel(book)
        lines = [f"Panel in {book.title}:"]
    lines.append("Cards, in held order:")
    for row in panel.rows:
        lines.append(
            f"{row.card_id}: {row.line} - "
            f"target {row.target}, answer {row.answer} "
            f"({row.recorded_on})")
    lines.extend(panel.account)
    return "\n".join(lines)


def format_verdict(source: Any = None) -> str:
    """The verdict as a screen block."""
    if isinstance(source, ApprovalVerdict):
        verdict = validate_verdict(source)
        title = "the book"
    else:
        book = _source_book(source)
        verdict = derive_verdict(book)
        title = book.title
    return (
        f"Verdict in Approval Cards over {title}: "
        f"{verdict.verdict} - {verdict.total_allowed} allowed, "
        f"{verdict.total_rejected} rejected, "
        f"{verdict.total_remembered} remembered and "
        f"{verdict.total_awaiting} awaiting of "
        f"{verdict.total_cards} cards, "
        f"{verdict.total_alarmed} alarmed, from "
        f"{verdict.earliest_on} to {verdict.latest_on}.")


def format_approval_cards_screen(source: Any = None) -> str:
    """The whole approval-cards screen for one book."""
    book = _source_book(source)
    panel = derive_panel(book)
    verdict = derive_verdict(book)
    lines = [
        f"Approval Cards (M-174) - {book.title}",
        format_book(book),
        f"Panel: {panel.total_cards} cards - "
        f"{panel.total_allowed} allowed, {panel.total_rejected} "
        f"rejected, {panel.total_remembered} remembered, "
        f"{panel.total_awaiting} awaiting; "
        f"{panel.total_alarmed} stand alarmed.",
        f"Verdict: {verdict.verdict}.",
        "No approval is executed here - a card held "
        "here is a question, never the act it asks "
        "about.",
    ]
    return "\n".join(lines)


def parse_approval_cards_args(args: Any) -> Tuple[str, Any]:
    """Parse the /approvalcards grammar into (action, target).

    ``""``/``show``/``list`` show the book;
    ``card <card-id>`` shows one card whole, with
    its target and consequence as their own lines;
    ``decision <decision-id>`` shows one held
    decision record; ``panel`` and ``verdict``
    show the derived panel and verdict. Anything
    else raises ValueError carrying the usage line.
    """
    if args is None:
        return ("show", None)
    if not isinstance(args, str):
        raise ValueError(USAGE)
    parts = args.split()
    if not parts or parts == ["show"] or parts == ["list"]:
        return ("show", None)
    if parts[0] == "card" and len(parts) == 2:
        return ("card", _check_word(parts[1], "a card id"))
    if parts[0] == "decision" and len(parts) == 2:
        return ("decision", _check_word(parts[1], "a decision id"))
    if parts == ["panel"]:
        return ("panel", None)
    if parts == ["verdict"]:
        return ("verdict", None)
    raise ValueError(USAGE)
