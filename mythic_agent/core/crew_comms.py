"""Crew comms (All-Features roadmap slice M-126).

Part VI - Agents as files - continues here. The
roadmap's words: ``structured hand-offs (findings,
diffs, questions) between members; a member's
question to the human is batched and asked once,
with full context.``

What already shipped, and what this slice adds:

* The crew itself is already data
  (``core/crew_members.py``, M-121: every member
  holds one office), the offices are formalised
  (``core/offices.py``, M-122, and
  ``core/custom_offices.py``, M-123), the worktree
  discipline is already data (``core/worktrees.py``,
  M-124), and the dealing of a plan's slices to the
  crew is already data (``core/task_dealing.py``,
  M-125). What nothing held is the traffic between
  the members once the dealing lands: the findings
  one member hands to another, the diff it hands
  over for review, and the questions members raise
  - above all the questions a member holds for the
  human, which arrive piecemeal today, one
  interruption at a time, each stripped of the
  context the others would have given it.
* This slice is that traffic, as a pure layer: a
  hand-off validated as data (a sender member, a
  recipient member - or the human - a kind, the
  slice it belongs to, a title and a body), the
  shipped data file (``mythic_agent/data/
  crew_comms.yaml``) holding one example ledger of
  hand-offs in exactly the shape a real ledger's
  file takes, a loader for a ledger file anywhere
  on disk, the human-question batch derived
  mechanically from a set of hand-offs, a hand-off
  record and a batch record shaped as session
  news, and a small in-memory registry model. This
  module spawns no agent, sends no message, runs
  no model and imports no agent / UI code; the
  agent layer owns holding the ledger for a
  session and carrying out the one batched ask.

Honesty rules, enforced here and pinned by tests:

* **Hand-offs are structured, never prose alone.**
  Every hand-off names its sender, its recipient,
  its kind, its slice, a title and a body, all
  validated; a hand-off missing a part, or
  carrying unknown keys, refuses whole instead of
  being skipped or guessed at.
* **Members are the shipped crew's.** A sender or
  recipient member id reads exactly as the M-121
  layer reads one - composed with by import, never
  re-read here. The one recipient who is not a
  member is the human, read as the plain word
  ``human``; the human never sends a hand-off -
  a sender naming the human refuses.
* **The kinds are the roadmap's three.** A
  hand-off is ``findings`` (what a member found),
  ``diff`` (a change handed over) or ``question``
  (a question for its recipient) - no other kind
  is read, and an unknown kind refuses.
* **A member's question to the human is batched
  and asked once, with full context.** Questions
  addressed to the human are never asked
  piecemeal: the batch is derived from the whole
  set of hand-offs - every waiting question, in
  the order handed, each carrying its sender, its
  slice, its title and its body - and the batch
  record is ONE record holding them all, so the
  ask happens once, together, with nothing's
  context stripped. A question between members is
  an ordinary hand-off and is never batched.
* **The batch is derived, never stored.** A batch
  is computed from the hand-offs it is batched
  under, in hand-off order, so it can never
  disagree with them; the same hand-offs always
  batch the same batch.
* **There is no live crew on this road yet, and
  no Part VIII board.** No crew is spawned or
  messaged by this slice: a hand-off here is a
  validated record held as data, not a delivered
  message, and the roadmap's board (Part VIII)
  does not exist in this tree. The hand-offs and
  the one batched ask are visible through this
  slice's own surfaces - the formatters both
  /comms roads share - and nothing here claims a
  message was delivered or a board exists.
* **Malformed refuses.** An unknown kind, a
  sender naming the human, a malformed slice,
  title or body, and unknown keys in a hand-off
  or ledger mapping all raise instead of being
  skipped or guessed at.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .crew_members import normalize_member_id
from .validation import ValidationError
from .worktrees import normalize_slice_id

__all__ = [
    "COMMS_RESOURCE",
    "COMMS_SCHEMA",
    "COMMS_SLICE",
    "HANDOFF_KINDS",
    "HUMAN_RECIPIENT",
    "PLAIN_EXPLANATION",
    "USAGE",
    "CrewCommsRegistry",
    "Handoff",
    "HandoffLedger",
    "HumanQuestionBatch",
    "batch_human_questions",
    "batch_plain_words",
    "batch_record",
    "build_handoff",
    "format_comms_screen",
    "format_handoff",
    "format_handoffs",
    "format_human_batch",
    "format_kinds",
    "handoff_record",
    "human_questions",
    "load_comms_ledger",
    "load_comms_ledger_file",
    "normalize_kind",
    "normalize_recipient",
    "normalize_slice_id",
    "parse_comms_args",
    "plain_words",
    "validate_batch",
    "validate_handoff",
    "validate_ledger",
]

COMMS_SLICE = "M-126"

#: The packaged data resource holding the example ledger.
COMMS_RESOURCE = "crew_comms.yaml"

#: The schema word a comms ledger file must carry.
COMMS_SCHEMA = "mythic.crew_comms/1"

#: The one recipient who is not a crew member.
HUMAN_RECIPIENT = "human"

#: The kinds a hand-off may carry, in roadmap order:
#: what a member found, a change handed over, and a
#: question for the recipient.
HANDOFF_KINDS = ("findings", "diff", "question")

_KIND_READINGS = {
    "finding": "findings",
    "findings": "findings",
    "diff": "diff",
    "diffs": "diff",
    "question": "question",
    "questions": "question",
}

PLAIN_EXPLANATION = (
    "Crew comms: members hand structured hand-offs "
    "to each other - findings, a diff, or a question "
    "- each naming its sender, its recipient, the "
    "slice it belongs to, a title and a body. A "
    "member's question to the human is never asked "
    "piecemeal: the waiting questions are batched "
    "and asked once, together, each with its full "
    "context. There is no Part VIII board yet, so "
    "the hand-offs and the batch are visible on "
    "this slice's own screen, not on a board. This "
    "layer holds hand-offs as data only; it spawns "
    "no crew and delivers no message itself."
)

USAGE = (
    "Usage: /comms, /comms show, "
    "/comms show <member>, /comms ask, /comms kinds"
)

_HANDOFF_KEYS = frozenset({
    "id", "handoff_id", "sender", "from_member",
    "recipient", "to_member", "kind", "handoff_kind",
    "slice", "slice_id", "title", "body", "text",
})

_LEDGER_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "ledger_note", "keeper", "handoffs",
})

_TITLE_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789 -'&/().,")

#: The shipped example ledger's hand-offs, in ledger
#: order: (sender, recipient, kind, slice, title,
#: body). The shipped data file is held to exactly
#: this list by the loader's example check. Three of
#: the six are questions to the human, from three
#: different members - the batch the example makes.
_EXAMPLE_HANDOFFS = (
    ("cartographer", "forge_worker", "findings", "M-126",
     "Comms shape mapped",
     "The crew holds no structured hand-off record yet: "
     "findings, diffs and questions pass in prose, so "
     "nothing can be checked, counted or batched."),
    ("forge_worker", "auditor", "diff", "M-126",
     "Hand-off record diff",
     "crew_comms holds every hand-off as validated data "
     "- sender, recipient, kind, slice, title and body "
     "- and refuses unknown keys instead of guessing."),
    ("scribe", "human", "question", "M-126",
     "Board or screen first",
     "When the Part VIII board exists, should the "
     "batched human questions appear there too, or "
     "stay on this slice's own screen until then?"),
    ("auditor", "human", "question", "M-125",
     "Re-deal record kept",
     "When a slice is re-dealt, should the record keep "
     "the first dealing beside the new one, or only "
     "the dealing the slice finally holds?"),
    ("guardian", "human", "question", "M-126",
     "Largest question batch",
     "Is there a largest batch of member questions to "
     "ask the human at once, or is every waiting "
     "question asked together, however many wait?"),
    ("auditor", "scribe", "findings", "M-126",
     "Batching rule checked",
     "Three members hold questions for the human in "
     "this ledger; the batch gathers all three and "
     "asks them once, each with its sender, slice "
     "and body."),
)


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_title(value: Any) -> str:
    title = _clean_text(value, "a hand-off's title")
    if len(title) > 120 or not all(
            ch in _TITLE_CHARS for ch in title):
        raise ValueError(
            f"a hand-off's title must be plain words of at most "
            f"120 characters, got {value!r}")
    return title


def _check_body(value: Any) -> str:
    body = _clean_text(value, "a hand-off's body")
    if len(body) > 8000 or "\x00" in body:
        raise ValueError(
            f"a hand-off's body must be plain text of at most "
            f"8000 characters, got {len(body)} characters")
    return body


def normalize_kind(value: Any) -> str:
    """The canonical hand-off kind a word names.

    Kind words read case-insensitively; the
    singular and plural spellings of the roadmap's
    three kinds read as the one canonical kind.
    Anything else raises.
    """
    if isinstance(value, str):
        wanted = value.strip().lower()
        if wanted in _KIND_READINGS:
            return _KIND_READINGS[wanted]
    raise ValueError(
        "a hand-off kind must be one of %s, got %r"
        % ("/".join(HANDOFF_KINDS), value))


def normalize_recipient(value: Any) -> str:
    """The canonical recipient a word names.

    A recipient is a crew member id, read exactly
    as the M-121 layer reads one, or the human -
    the plain word ``human``, read in any case.
    """
    if isinstance(value, str) \
            and value.strip().lower() == HUMAN_RECIPIENT:
        return HUMAN_RECIPIENT
    return normalize_member_id(value)


def _check_sender(value: Any) -> str:
    if isinstance(value, str) \
            and value.strip().lower() == HUMAN_RECIPIENT:
        raise ValueError(
            "the human never sends a hand-off; a sender "
            "is a crew member")
    return normalize_member_id(value)


def _pick(mapping: Dict[str, Any], first: str, second: str,
          what: str) -> Any:
    """One field from its two spellings, or a refusal."""
    if first in mapping and second in mapping:
        if mapping[first] != mapping[second]:
            raise ValueError(f"a hand-off names two different {what}")
        return mapping[first]
    if first in mapping:
        return mapping[first]
    return mapping.get(second)


# ---------------------------------------------------------------------
# The hand-off: one structured message between members, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class Handoff:
    """One structured hand-off between crew members, as data.

    ``sender`` is the sending member's M-121 member
    id; ``recipient`` is the receiving member's id,
    or ``human``; ``kind`` is one of the roadmap's
    three kinds; ``slice_id`` is the slice the
    hand-off belongs to; ``title`` names it in plain
    words and ``body`` carries its whole content -
    the findings, the diff, or the question itself.
    Constructing one validates it. A hand-off is a
    record held as data, not a delivered message.
    """

    handoff_id: Optional[str] = None
    sender: str = ""
    recipient: str = ""
    kind: str = ""
    slice_id: str = ""
    title: str = ""
    body: str = ""

    def __post_init__(self) -> None:
        if self.handoff_id is not None:
            object.__setattr__(
                self, "handoff_id",
                normalize_member_id(self.handoff_id))
        object.__setattr__(self, "sender", _check_sender(self.sender))
        object.__setattr__(
            self, "recipient", normalize_recipient(self.recipient))
        object.__setattr__(self, "kind", normalize_kind(self.kind))
        object.__setattr__(
            self, "slice_id", normalize_slice_id(self.slice_id))
        object.__setattr__(self, "title", _check_title(self.title))
        object.__setattr__(self, "body", _check_body(self.body))

    @property
    def to_human(self) -> bool:
        """True when this hand-off is addressed to the human."""
        return self.recipient == HUMAN_RECIPIENT

    @property
    def is_question(self) -> bool:
        """True when this hand-off carries a question."""
        return self.kind == "question"

    @property
    def waits_for_human(self) -> bool:
        """True when this is a member's question to the human.

        Only these hand-offs are batched: a question
        between members is an ordinary hand-off.
        """
        return self.to_human and self.is_question

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "crew_handoff",
            "slice": COMMS_SLICE,
            "handoff_id": self.handoff_id,
            "sender": self.sender,
            "recipient": self.recipient,
            "kind": self.kind,
            "slice_id": self.slice_id,
            "title": self.title,
            "body": self.body,
            "to_human": self.to_human,
        }


def validate_handoff(handoff: Any) -> Handoff:
    """Validate one hand-off into a Handoff.

    Accepts a Handoff or a mapping naming a
    ``sender`` (or ``from_member``), a ``recipient``
    (or ``to_member``), a ``kind`` (or
    ``handoff_kind``), a ``slice_id`` (or ``slice``),
    a ``title``, a ``body`` (or ``text``) and an
    optional ``handoff_id`` (or ``id``). Naming both
    spellings of one field with different values
    refuses, and unknown keys refuse.
    """
    if isinstance(handoff, Handoff):
        return handoff
    if not isinstance(handoff, dict):
        raise ValueError(
            f"a hand-off must be a mapping, got {handoff!r}")
    unknown = set(handoff) - _HANDOFF_KEYS
    if unknown:
        raise ValueError(
            "unknown hand-off keys: %s"
            % ", ".join(sorted(unknown)))
    sender = _pick(handoff, "sender", "from_member", "senders")
    if sender is None:
        raise ValueError("a hand-off is missing its sender")
    recipient = _pick(handoff, "recipient", "to_member", "recipients")
    if recipient is None:
        raise ValueError("a hand-off is missing its recipient")
    kind = _pick(handoff, "kind", "handoff_kind", "kinds")
    if kind is None:
        raise ValueError("a hand-off is missing its kind")
    slice_id = _pick(handoff, "slice_id", "slice", "slices")
    if slice_id is None:
        raise ValueError("a hand-off is missing its slice")
    body = _pick(handoff, "body", "text", "bodies")
    if body is None:
        raise ValueError("a hand-off is missing its body")
    if "title" not in handoff:
        raise ValueError("a hand-off is missing its title")
    kwargs: Dict[str, Any] = {
        "sender": sender,
        "recipient": recipient,
        "kind": kind,
        "slice_id": slice_id,
        "title": handoff["title"],
        "body": body,
    }
    handoff_id = _pick(handoff, "handoff_id", "id", "hand-off ids")
    if handoff_id is not None:
        kwargs["handoff_id"] = handoff_id
    return Handoff(**kwargs)


def build_handoff(handoff: Any = None, **kwargs: Any) -> Handoff:
    """Build one validated hand-off.

    From a Handoff, from a mapping (the spellings
    :func:`validate_handoff` reads), or from field
    words given as keyword arguments.
    """
    if isinstance(handoff, Handoff) and not kwargs:
        return handoff
    if isinstance(handoff, dict) or handoff is None:
        merged: Dict[str, Any] = {}
        if isinstance(handoff, dict):
            merged.update(handoff)
        merged.update(kwargs)
        return validate_handoff(merged)
    raise ValueError(
        f"a hand-off must be a mapping, got {handoff!r}")


# ---------------------------------------------------------------------
# The ledger: the hand-offs one file holds, under one keeper.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class HandoffLedger:
    """A whole ledger: the hand-offs one file holds, in file order.

    ``keeper`` is the member id of the one who keeps
    the ledger - in the shipped example the house
    coordinator word. Constructing one holds the
    ledger law: at least one hand-off.
    """

    handoffs: Tuple[Handoff, ...] = ()
    keeper: str = ""
    ledger_note: str = ""

    def __post_init__(self) -> None:
        if isinstance(self.handoffs, (str, bytes)) \
                or not isinstance(self.handoffs, (list, tuple)):
            raise ValueError(
                f"a ledger's hand-offs must be a list of "
                f"hand-offs, got {self.handoffs!r}")
        handoffs = tuple(
            h if isinstance(h, Handoff) else validate_handoff(h)
            for h in self.handoffs)
        if not handoffs:
            raise ValueError("a ledger must hold at least one hand-off")
        object.__setattr__(self, "handoffs", handoffs)
        object.__setattr__(
            self, "keeper", normalize_member_id(self.keeper))
        object.__setattr__(
            self, "ledger_note", str(self.ledger_note or ""))

    def by_slice(self, slice_id: Any) -> Tuple[Handoff, ...]:
        """Every hand-off one slice holds, in ledger order."""
        wanted = normalize_slice_id(slice_id)
        return tuple(
            h for h in self.handoffs if h.slice_id == wanted)


def validate_ledger(data: Any, *,
                    require_example: bool = False) -> list:
    """Every problem in a comms ledger mapping, as plain strings.

    An empty list means the ledger is well-formed.
    With ``require_example`` the ledger must be
    exactly the shipped example: the six hand-offs
    in ledger order, with their senders, recipients,
    kinds, slices, titles and bodies, kept by the
    coordinator - and the batch derived from it must
    hold exactly its three questions to the human,
    one per asking member (the check the shipped
    file is held to; a real ledger's file is read
    without it).
    """
    if not isinstance(data, dict):
        return [f"a comms ledger must be a mapping, got {data!r}"]
    problems = []
    unknown = set(data) - _LEDGER_KEYS
    if unknown:
        problems.append(
            "unknown comms ledger keys: %s"
            % ", ".join(sorted(unknown)))
    if data.get("schema") != COMMS_SCHEMA:
        problems.append(
            f"a comms ledger's schema must be "
            f"{COMMS_SCHEMA!r}, got {data.get('schema')!r}")
    if data.get("slice") != COMMS_SLICE:
        problems.append(
            f"a comms ledger's slice must be "
            f"{COMMS_SLICE!r}, got {data.get('slice')!r}")
    keeper = None
    if data.get("keeper") is None:
        problems.append("a comms ledger is missing its keeper")
    else:
        try:
            keeper = normalize_member_id(data["keeper"])
        except ValueError as exc:
            problems.append(f"keeper: {exc}")
    raw = data.get("handoffs")
    if not isinstance(raw, list) or not raw:
        problems.append(
            "a comms ledger must hold a non-empty handoffs list")
        return problems
    parsed = []
    for index, entry in enumerate(raw):
        try:
            parsed.append(validate_handoff(entry))
        except ValueError as exc:
            problems.append(f"hand-off {index + 1}: {exc}")
    if require_example and len(parsed) == len(raw):
        held = tuple(
            (h.sender, h.recipient, h.kind, h.slice_id,
             h.title, h.body) for h in parsed)
        if held != _EXAMPLE_HANDOFFS:
            problems.append(
                "the shipped example ledger must hold exactly "
                "the six hand-offs in ledger order, with their "
                "senders, recipients, kinds, slices, titles "
                "and bodies")
        if keeper is not None and keeper != "coordinator":
            problems.append(
                "the shipped example ledger is kept by the "
                "coordinator")
        if held == _EXAMPLE_HANDOFFS:
            batch = batch_human_questions(tuple(parsed))
            senders = tuple(q.sender for q in batch.questions)
            if senders != ("scribe", "auditor", "guardian"):
                problems.append(
                    "the shipped example batch must hold the "
                    "three questions to the human, from scribe, "
                    "auditor and guardian, in ledger order")
    return problems


def _ledger_from(data: Any, *, require_example: bool) -> HandoffLedger:
    problems = validate_ledger(data, require_example=require_example)
    if problems:
        raise ValidationError(
            "invalid comms ledger: " + "; ".join(problems))
    assert isinstance(data, dict)
    return HandoffLedger(
        handoffs=tuple(
            validate_handoff(entry) for entry in data["handoffs"]),
        keeper=data["keeper"],
        ledger_note=str(data.get("ledger_note") or ""))


def load_comms_ledger(
        data: Optional[Dict[str, Any]] = None) -> HandoffLedger:
    """Load and validate the shipped example ledger (or *data*).

    The shipped file is held to the example check:
    exactly the six hand-offs, kept by the
    coordinator, batching exactly the three
    questions to the human. Raises
    :class:`ValidationError` listing every problem
    when the record is not a well-formed ledger.
    """
    raw = data if data is not None else load_resource(COMMS_RESOURCE)
    return _ledger_from(raw, require_example=True)


def load_comms_ledger_file(path: Any) -> HandoffLedger:
    """Load and validate a comms ledger from a file at *path*.

    This is the road a real ledger arrives by: any
    file in the ledger shape, anywhere on disk,
    validated whole - a malformed file raises
    :class:`ValidationError` naming the problem,
    and a missing file raises ``FileNotFoundError``.
    The example check is not held: a ledger may
    hold a single hand-off.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _ledger_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The registry model: hand-offs held in registration order, ids
# deterministic. Unlike the dealing registry, a registry here refuses
# nothing for repetition: hand-offs are messages, and the same member
# may hand the same kind of news twice - each registration is its own
# hand-off with its own id.
# ---------------------------------------------------------------------


class CrewCommsRegistry:
    """An in-memory registry of hand-offs.

    Hand-offs are held in registration order. Ids
    are deterministic: a caller-supplied id is used
    as given, and an unsupplied id is the next
    ``comms-N`` in sequence, skipping any number a
    supplied id already took. A supplied id already
    held refuses. Storage beyond memory (a session's
    journal, a file) is the agent layer's concern;
    this model is neutral.
    """

    def __init__(self) -> None:
        self._handoffs: Dict[str, Handoff] = {}
        self._next = 1

    def _fresh_id(self) -> str:
        while f"comms-{self._next}" in self._handoffs:
            self._next += 1
        handoff_id = f"comms-{self._next}"
        self._next += 1
        return handoff_id

    def register(self, handoff: Any) -> Handoff:
        """Register one hand-off and hold it."""
        validated = build_handoff(handoff)
        if validated.handoff_id is not None \
                and validated.handoff_id in self._handoffs:
            raise ValueError(
                f"a hand-off named {validated.handoff_id!r} "
                f"already exists")
        if validated.handoff_id is None:
            from dataclasses import replace
            validated = replace(
                validated, handoff_id=self._fresh_id())
        self._handoffs[validated.handoff_id] = validated
        return validated

    def register_ledger(self, ledger: Any) -> Tuple[Handoff, ...]:
        """Register every hand-off of one ledger, in order."""
        if not isinstance(ledger, HandoffLedger):
            raise ValueError(f"a comms ledger is needed, got {ledger!r}")
        return tuple(self.register(h) for h in ledger.handoffs)

    def get(self, handoff_id: Any) -> Handoff:
        """The hand-off one id names; an unknown id raises."""
        wanted = normalize_member_id(handoff_id)
        if wanted not in self._handoffs:
            raise KeyError(f"unknown hand-off: {wanted!r}")
        return self._handoffs[wanted]

    def list_handoffs(self) -> Tuple[Handoff, ...]:
        """Every held hand-off, in registration order."""
        return tuple(self._handoffs.values())

    def by_sender(self, member: Any) -> Tuple[Handoff, ...]:
        """Every hand-off one member sent, in order held."""
        wanted = normalize_member_id(member)
        return tuple(
            h for h in self._handoffs.values() if h.sender == wanted)

    def by_recipient(self, member: Any) -> Tuple[Handoff, ...]:
        """Every hand-off one recipient holds, in order held."""
        wanted = normalize_recipient(member)
        return tuple(
            h for h in self._handoffs.values()
            if h.recipient == wanted)

    def for_member(self, member: Any) -> Tuple[Handoff, ...]:
        """Every hand-off one member sent or received, in order."""
        wanted = normalize_recipient(member)
        return tuple(
            h for h in self._handoffs.values()
            if h.sender == wanted or h.recipient == wanted)

    def by_slice(self, slice_id: Any) -> Tuple[Handoff, ...]:
        """Every held hand-off one slice holds, in order held."""
        wanted = normalize_slice_id(slice_id)
        return tuple(
            h for h in self._handoffs.values()
            if h.slice_id == wanted)

    def human_questions(self) -> Tuple[Handoff, ...]:
        """The held questions to the human, in order held."""
        return tuple(
            h for h in self._handoffs.values() if h.waits_for_human)

    def batch(self) -> "HumanQuestionBatch":
        """The one batch of the held questions to the human."""
        return HumanQuestionBatch(questions=self.human_questions())


# ---------------------------------------------------------------------
# The human-question batch: derived from a set of hand-offs, never
# stored - every waiting question, asked once, with full context.
# ---------------------------------------------------------------------


def _selected_handoffs(source: Any) -> Tuple[Handoff, ...]:
    if source is None:
        return ()
    if isinstance(source, CrewCommsRegistry):
        return source.list_handoffs()
    if isinstance(source, HandoffLedger):
        return source.handoffs
    if isinstance(source, (str, bytes)) \
            or not isinstance(source, (list, tuple)):
        raise ValueError(
            "hand-offs must be a list of hand-offs")
    return tuple(
        h if isinstance(h, Handoff) else build_handoff(h)
        for h in source)


def human_questions(source: Any) -> Tuple[Handoff, ...]:
    """Every member question to the human in *source*, in order.

    Accepts a list of hand-offs, a HandoffLedger or
    a CrewCommsRegistry. A question between members
    is not gathered: only questions addressed to
    the human wait for the batch.
    """
    return tuple(
        h for h in _selected_handoffs(source) if h.waits_for_human)


@dataclass(frozen=True)
class HumanQuestionBatch:
    """One batch of questions for the human, as data.

    ``questions`` are the members' questions to the
    human, in the order they were handed - the whole
    batch, so the ask happens once, together, each
    question carrying its sender, its slice, its
    title and its body: its full context.
    Constructing one validates it: every question in
    a batch is a question addressed to the human.
    """

    questions: Tuple[Handoff, ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.questions, (str, bytes)) \
                or not isinstance(self.questions, (list, tuple)):
            raise ValueError(
                f"a batch's questions must be a list of "
                f"hand-offs, got {self.questions!r}")
        questions = tuple(
            q if isinstance(q, Handoff) else validate_handoff(q)
            for q in self.questions)
        for question in questions:
            if not question.waits_for_human:
                raise ValueError(
                    f"a batch holds only members' questions to "
                    f"the human; {question.title!r} is a "
                    f"{question.kind} for {question.recipient!r}")
        object.__setattr__(self, "questions", questions)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "human_question_batch",
            "slice": COMMS_SLICE,
            "count": len(self.questions),
            "question_ids": [q.handoff_id for q in self.questions],
            "questions": [q.to_record() for q in self.questions],
        }


def batch_human_questions(source: Any) -> HumanQuestionBatch:
    """The one batch of *source*'s questions to the human.

    The mechanical judge of the batching rule, as
    data only: every question addressed to the
    human, in hand-off order, gathered into ONE
    batch - never asked piecemeal. With no waiting
    question the batch is empty and asks nothing.
    """
    return HumanQuestionBatch(questions=human_questions(source))


def validate_batch(source: Any, batch: Any) -> list:
    """Every problem in a claimed batch of *source*, as strings.

    An empty list means the batch answers the
    source exactly: every question to the human in
    the source, in source order, and nothing else -
    a batch missing a waiting question, or holding
    a question the source does not hold, is named.
    """
    if not isinstance(batch, HumanQuestionBatch):
        return [f"a human-question batch is needed, got {batch!r}"]
    try:
        wanted = human_questions(source)
    except ValueError as exc:
        return [str(exc)]
    problems = []
    held = [
        (q.sender, q.kind, q.slice_id, q.title, q.body)
        for q in batch.questions]
    expected = [
        (q.sender, q.kind, q.slice_id, q.title, q.body)
        for q in wanted]
    if held != expected:
        problems.append(
            "the batch does not hold exactly the source's "
            "questions to the human, in order: the batch "
            "must ask every waiting question once, together, "
            "and no other question")
    return problems


# ---------------------------------------------------------------------
# Comms news, shaped as session records.
# ---------------------------------------------------------------------


def plain_words(handoff: Any) -> str:
    """One hand-off, in one plain sentence."""
    current = handoff if isinstance(handoff, Handoff) \
        else build_handoff(handoff)
    if current.waits_for_human:
        tail = ("a question for the human - batched with "
                "the other waiting questions and asked once.")
    elif current.recipient == HUMAN_RECIPIENT:
        tail = f"handed to the human as {current.kind}."
    else:
        tail = f"handed to {current.recipient} as {current.kind}."
    return (
        f"{current.slice_id} ({current.title}) from "
        f"{current.sender} - {tail}")


def handoff_record(handoff: Any) -> Dict[str, Any]:
    """The session-news record of one hand-off.

    Carries the hand-off's whole record plus a
    one-line plain headline, so a hand-off made in
    a session is news with its shape attached,
    never a bare log line.
    """
    current = handoff if isinstance(handoff, Handoff) \
        else build_handoff(handoff)
    record = current.to_record()
    record["news"] = True
    record["headline"] = plain_words(current)
    return record


def batch_plain_words(batch: Any) -> str:
    """One human-question batch, in one plain sentence."""
    current = batch if isinstance(batch, HumanQuestionBatch) \
        else HumanQuestionBatch(questions=batch)
    if not current.questions:
        return "No member question waits for the human."
    asked = "; ".join(
        f"{q.slice_id} from {q.sender} - {q.title}"
        for q in current.questions)
    return (
        f"{len(current.questions)} questions for the human, "
        f"asked once together: {asked}.")


def batch_record(batch: Any) -> Dict[str, Any]:
    """The session-news record of one batched ask.

    ONE record holding every waiting question with
    its full context - the ask itself, as news:
    the human is asked once, together, never one
    record per question.
    """
    current = batch if isinstance(batch, HumanQuestionBatch) \
        else HumanQuestionBatch(questions=batch)
    record = current.to_record()
    record["news"] = True
    record["headline"] = batch_plain_words(current)
    return record


# ---------------------------------------------------------------------
# The /comms surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------


def format_handoff(handoff: Any) -> str:
    """One hand-off, in plain words."""
    current = handoff if isinstance(handoff, Handoff) \
        else build_handoff(handoff)
    name = current.handoff_id or current.slice_id
    return f"  {name}: {plain_words(current)}"


def format_handoffs(source: Any = None) -> str:
    """The hand-offs, in plain words, in the order given.

    Accepts a list of hand-offs, a HandoffLedger or
    a CrewCommsRegistry. With no hand-offs at all
    the text starts with the plain statement of
    that fact.
    """
    selected = _selected_handoffs(source)
    if not selected:
        return "Crew hand-offs: none. No hand-off is recorded."
    lines = [f"Crew hand-offs: {len(selected)} handed."]
    for handoff in selected:
        lines.append(format_handoff(handoff))
    return "\n".join(lines)


def format_human_batch(source: Any = None) -> str:
    """The one batched ask for the human, with full context.

    Accepts a HumanQuestionBatch or anything
    :func:`batch_human_questions` reads. With no
    waiting question the text says so plainly and
    asks nothing; otherwise every waiting question
    is listed once, together, each with its sender,
    its slice, its title and its body - the full
    context the human is asked with.
    """
    if isinstance(source, HumanQuestionBatch):
        batch = source
    else:
        batch = batch_human_questions(source)
    if not batch.questions:
        return ("Questions for the human: none waiting. "
                "Nothing is asked.")
    lines = [
        f"Questions for the human: {len(batch.questions)} "
        f"waiting, asked once together with full context."]
    for question in batch.questions:
        name = question.handoff_id or question.slice_id
        lines.append(
            f"  {name}: {question.sender} asks about "
            f"{question.slice_id} ({question.title}): "
            f"{question.body}")
    return "\n".join(lines)


def format_kinds() -> str:
    """The hand-off kinds, in plain words."""
    return (
        "Hand-off kinds: findings (what a member found), "
        "diff (a change a member hands over), question "
        "(a question for its recipient - for the human "
        "when its recipient is the human, and batched "
        "when it is).")


def format_comms_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /comms.

    With nothing named, the shipped example
    ledger's hand-offs are shown - the example this
    slice ships - so the screen is never empty.
    There is no Part VIII board yet; this screen is
    where the hand-offs and the batch are visible.
    """
    shown: Any = source if source is not None \
        else load_comms_ledger()
    lines = ["Crew comms (M-126) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_handoffs(shown))
    lines.append("")
    lines.append(format_human_batch(shown))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_comms_args(args: Any) -> Tuple[str, Optional[str]]:
    """Parse the /comms grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    hand-offs; ``show <member>`` and a bare member
    id (or ``human``) show one member's hand-offs;
    ``ask`` (or ``questions`` / ``batch``) asks for
    the one batched ask of the questions waiting
    for the human; ``kinds`` asks for the kinds.
    Anything else is a usage error naming the
    grammar. Returns ``(action, value-or-None)``.
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
            return ("show", normalize_recipient(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head in ("ask", "questions", "batch") and len(words) == 1:
        return ("ask", None)
    if head == "kinds" and len(words) == 1:
        return ("kinds", None)
    if head in ("show", "ask", "questions", "batch", "kinds"):
        raise ValueError(USAGE)
    if len(words) == 1:
        try:
            return ("show", normalize_recipient(words[0]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
