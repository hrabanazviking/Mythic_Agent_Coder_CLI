"""Self-improving ledger (All-Features roadmap slice M-155).

Part VII closes. The roadmap's words:
``after significant work, durable lessons and
reusable patterns are captured as candidate
memories; the human (or standing rule) promotes
them - Part IX's learning loop.``

What already shipped, and what this slice adds:

* The forge's own doctrine already ships as data:
  the method charter (``core/method_charter.py``)
  carries the Self-Improving Forge plug
  (``YRSA_SELF_IMPROVING_FORGE``, tenet F-06) -
  after significant work, capture the durable
  lessons it taught; when a pattern repeats,
  extract it into reusable machinery. Part IX's
  learning loop (M-213 retrospectives flowing
  here, M-214 pattern extraction drafting
  candidates for approval) stands on this ledger.
* A project's facts already ship as data: the
  project memory map (``core/project_memory_map.py``,
  M-150), session memory across days
  (``core/session_memory.py``, M-153) and
  cross-project memory
  (``core/cross_project_memory.py``, M-154) hold
  lessons inside and across projects. Nothing yet
  holds the forge's OWN learning: the candidate
  memories significant work teaches, standing
  between capture and standing memory.
* This slice is that holding, as a pure layer: a
  candidate memory captured after significant
  work, validated as data WITH ITS PROVENANCE
  WHOLE - the work it was learned in, the context
  it was learned in, the evidence it stands on,
  and where it was read from - standing as a
  candidate until an explicit promotion decision
  by the human or a named standing rule promotes
  it. A candidate becomes a standing memory ONLY
  through that decision, never silently. The
  shipped data file
  (``mythic_agent/data/self_improving_ledger.yaml``)
  holds one example book in exactly the shape a
  real book file takes, a loader reads a book file
  anywhere on disk, the composition roads read the
  shipped project memory map, session memory and
  cross-project memory onto candidates BY IMPORT,
  the charter road reads the Self-Improving Forge
  tenet's directives BY IMPORT, the ledger panel
  is DERIVED from the whole book (every candidate
  standing with its decision whole, in a settled
  order), records are shaped as session news, and
  a small in-memory registry model holds
  candidates and decisions one by one. The agent
  layer owns holding a book for a session and
  capturing the session's own memory-map entries
  as candidates.

Honesty rules, enforced here and pinned by tests:

* **Provenance, always.** A candidate carries
  where it was learned (its source work), the
  context it was learned in and the evidence it
  stands on. A candidate with no provenance
  refuses - candidates are never captured
  anonymously, and a bare memory-map entry becomes
  a candidate only when the provenance words are
  named with it.
* **Promotion is explicit, never silent.** A
  candidate stands as a candidate by default. It
  becomes a standing memory only through a
  promotion decision in the promoted state, and a
  decided state (promoted, declined or
  quarantined) names who decided it - the human
  or a named standing rule. There is no road here
  that promotes by capture, by age or by count.
* **Composed, never duplicated.** Candidates are
  the shipped project memory map's entries, the
  shipped session memory's carried notes and the
  shipped cross-project memory's shared lessons,
  read onto this layer by import, and the capture
  doctrine is the shipped method charter's own
  Self-Improving Forge tenet, read by import. No
  second taxonomy of lessons is invented here.
* **The panel is derived, never stored loose.**
  Its rows are the book's candidates with their
  standings carried whole, in settled order
  (promoted first, then candidate, then declined,
  then quarantined; within a state, by source
  work, then candidate title), and its totals are
  the candidates' own counts; a stored panel or
  book whose rows, totals, counts or account
  disagree with the derived shape refuses.
* **Data only - capturing changes no memory.** A
  candidate or a decision here is validated data:
  no model is called, no project files are
  written, no live memory is updated, and nothing
  persists beyond the session journal news the
  agent layer publishes. A promoted candidate
  STANDS as a standing memory on this layer,
  derived at call time - promotion writes it into
  no project's own records.
* **Malformed refuses.** A duplicate candidate or
  decision id in one book, the same fact named
  twice by one work, a decision naming a candidate
  the book does not hold, two decisions standing
  on one candidate, a decided state naming no
  decider, and unknown keys in a candidate, a
  decision, a panel or a book mapping all raise
  instead of being skipped or guessed at.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .crew_members import normalize_member_id
from .cross_project_memory import SharedLesson
from .cross_project_memory import validate_lesson as _validate_shared_lesson
from .method_charter import load_charter
from .project_memory_map import MemoryMapEntry
from .project_memory_map import validate_entry as _validate_map_entry
from .session_memory import CarriedMemory, SessionSituation
from .session_memory import validate_note as _validate_session_note
from .validation import ValidationError

__all__ = [
    "CANDIDATE_KINDS",
    "PLAIN_EXPLANATION",
    "PROMOTION_STATES",
    "SELF_IMPROVING_RESOURCE",
    "SELF_IMPROVING_SCHEMA",
    "SELF_IMPROVING_SLICE",
    "SELF_IMPROVING_TENET",
    "USAGE",
    "CandidateMemory",
    "LedgerPanel",
    "LedgerPanelRow",
    "PromotionDecision",
    "PromotionStateCount",
    "SelfImprovingBook",
    "SelfImprovingRegistry",
    "book_record",
    "build_book",
    "build_candidate",
    "build_decision",
    "build_panel",
    "build_row",
    "candidate_from_map_entry",
    "candidate_record",
    "candidates_from_cross_project",
    "candidates_from_memory_map",
    "candidates_from_session_memory",
    "decision_record",
    "derive_panel",
    "format_candidate",
    "format_candidates",
    "format_decisions",
    "format_panel",
    "format_self_improving_screen",
    "format_standing",
    "load_self_improving_ledger",
    "load_self_improving_ledger_file",
    "normalize_candidate_kind",
    "normalize_promotion_state",
    "panel_plain_words",
    "panel_record",
    "parse_self_improving_args",
    "plain_words",
    "self_improving_directives",
    "standing_memories",
    "validate_book",
    "validate_candidate",
    "validate_decision",
    "validate_panel",
    "validate_row",
]

SELF_IMPROVING_SLICE = "M-155"

#: The packaged data resource holding the example book.
SELF_IMPROVING_RESOURCE = "self_improving_ledger.yaml"

#: The schema word a self-improving-ledger file must carry.
SELF_IMPROVING_SCHEMA = "mythic.self_improving_ledger/1"

#: The method charter's Self-Improving Forge tenet
#: key: the plug whose directives are this ledger's
#: capture doctrine, read by import.
SELF_IMPROVING_TENET = "self-improving-forge"

#: The kinds one candidate memory may be: a durable
#: lesson significant work taught, or a reusable
#: pattern extracted from repeated work.
CANDIDATE_KINDS = ("lesson", "pattern")

_CANDIDATE_KIND_ALIASES = {
    "lesson": "lesson",
    "durable-lesson": "lesson",
    "durable_lesson": "lesson",
    "pattern": "pattern",
    "reusable-pattern": "pattern",
    "reusable_pattern": "pattern",
}

#: The states one candidate may stand in: a
#: candidate awaiting its word, promoted (it stands
#: as a standing memory), declined (the word was
#: no) or quarantined (held apart until its
#: evidence is judged again).
PROMOTION_STATES = (
    "candidate", "promoted", "declined", "quarantined")

_PROMOTION_STATE_ALIASES = {
    "candidate": "candidate",
    "pending": "candidate",
    "promoted": "promoted",
    "approved": "promoted",
    "declined": "declined",
    "rejected": "declined",
    "quarantined": "quarantined",
    "held": "quarantined",
}

#: The order candidates stand in on the ledger
#: panel: what stands as memory first, then what
#: awaits its word, then what was refused and what
#: is held apart.
_PANEL_STATE_ORDER = (
    "promoted", "candidate", "declined", "quarantined")

_CANDIDATE_KEYS = frozenset({
    "candidate_id", "id", "kind", "type_of_memory",
    "title", "name", "detail", "body",
    "source_work", "work", "from_work",
    "context", "learned_in", "situation",
    "evidence", "proof", "backing",
    "source", "ref", "path", "reference",
})

_DECISION_KEYS = frozenset({
    "decision_id", "id", "candidate_id", "candidate",
    "state", "status", "decided_by", "decider",
    "authority", "note", "detail",
})

_ROW_KEYS = frozenset({
    "state", "candidate_id", "id", "kind", "title",
    "detail", "source_work",
})

_STATE_COUNT_KEYS = frozenset({"state", "items", "count"})

_PANEL_KEYS = frozenset({
    "panel_id", "id", "rows", "candidates",
    "total_items", "total", "total_promoted",
    "total_candidate", "total_declined",
    "total_quarantined", "state_counts", "states",
    "account", "statements",
})

_BOOK_KEYS = frozenset({"title", "name"})

_SELF_IMPROVING_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "canon_note", "guide", "candidates", "decisions", "panels",
})

#: The shipped example book's title, held to this
#: by the loader's example check.
_EXAMPLE_TITLE = "Self-improving ledger at the M-154 slice boundary"

#: The shipped example's candidate ids, in held
#: order, pinned by the loader.
_EXAMPLE_CANDIDATE_IDS = (
    "candidate-commit-before-answer", "candidate-reap-at-bank",
    "candidate-bank-incrementally")

#: The shipped example's first candidate and the
#: work it was learned in, pinned by the loader.
_EXAMPLE_FIRST_CANDIDATE_ID = "candidate-commit-before-answer"

_EXAMPLE_FIRST_CANDIDATE_WORK = "samtal-gatekeeper"

#: The shipped example's one panel id, and its rows
#: in panel order, pinned by the loader.
_EXAMPLE_PANEL_ID = "panel-m154-boundary"

_EXAMPLE_PANEL_ROW_IDS = (
    "candidate-reap-at-bank", "candidate-commit-before-answer",
    "candidate-bank-incrementally")

_EXAMPLE_PANEL_ACCOUNT = (
    "The ledger panel holds 3 candidates: promoted 1, "
    "candidate 1, declined 1, quarantined 0.",
    "Candidates stand promoted first, then candidate, "
    "then declined, then quarantined; within a state, "
    "by source work, then candidate title - so two "
    "panels of one book diff cleanly, line by line.",
    "A candidate stands as a standing memory only "
    "through an explicit promotion by the human or a "
    "named standing rule, and it stands there with "
    "its provenance whole - where it was learned, in "
    "what context, and on what evidence.",
    "The panel is read off the book at call time - "
    "it is derived, never stored loose.",
)

PLAIN_EXPLANATION = (
    "The self-improving ledger: after significant "
    "work, durable lessons and reusable patterns are "
    "captured as candidate memories - with "
    "provenance, never promoted silently. A candidate "
    "memory is one lesson or pattern carried with "
    "where it was learned (its source work), the "
    "context it was learned in and the evidence it "
    "stands on. A candidate becomes a standing memory "
    "only through an explicit promotion decision by "
    "the human or a named standing rule - candidate, "
    "promoted, declined or quarantined - and a "
    "decided state names its decider. The ledger "
    "panel is derived from the book at call time: "
    "every candidate standing with its decision "
    "whole, promoted first, then candidate, declined "
    "and quarantined. This layer holds candidates "
    "and decisions as data only: it calls no model, "
    "writes no project files, updates no live memory "
    "and persists nothing."
)

USAGE = (
    "Usage: /ledger, /ledger show, "
    "/ledger candidate <candidate-id>, "
    "/ledger decisions, "
    "/ledger standing, "
    "/ledger panel"
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


def _check_ref(value: Any) -> str:
    text = _clean_text(value, "a candidate's reference")
    if len(text) > 300 or "\x00" in text:
        raise ValueError(
            f"a candidate's reference must be plain text "
            f"of at most 300 characters, got {len(text)} characters")
    if any(ch.isspace() for ch in text):
        raise ValueError(
            f"a candidate's reference names no spaces, "
            f"got {text!r}")
    return text


def _check_work(value: Any, what: str = "a source work") -> str:
    """One source-work name, judged as one plain word.

    Source-work names on this layer are the shipped
    id shape (letters, digits, dashes, underscores
    and dots, case kept) - the same word a registry
    id takes - so the work a candidate was learned
    in can be compared exactly.
    """
    try:
        return normalize_member_id(value)
    except ValueError:
        raise ValueError(
            f"{what} must be one plain work word, "
            f"got {value!r}") from None


def normalize_candidate_kind(value: Any) -> str:
    """The canonical candidate kind a word names.

    A kind is one of :data:`CANDIDATE_KINDS` -
    ``lesson`` (a durable lesson) or ``pattern`` (a
    reusable pattern) - read case-insensitively,
    with ``durable-lesson`` read onto ``lesson`` and
    ``reusable-pattern`` onto ``pattern``. Anything
    else raises, plainly naming the two.
    """
    if isinstance(value, str):
        wanted = _CANDIDATE_KIND_ALIASES.get(value.strip().lower())
        if wanted is not None:
            return wanted
    raise ValueError(
        "a candidate's kind must be one of %s, got %r"
        % ("/".join(CANDIDATE_KINDS), value))


def normalize_promotion_state(value: Any) -> str:
    """The canonical promotion state a word names.

    A state is one of :data:`PROMOTION_STATES` -
    ``candidate``, ``promoted``, ``declined`` or
    ``quarantined`` - read case-insensitively, with
    ``pending`` read onto ``candidate``, ``approved``
    onto ``promoted``, ``rejected`` onto ``declined``
    and ``held`` onto ``quarantined``. Anything else
    raises, plainly naming the four.
    """
    if isinstance(value, str):
        wanted = _PROMOTION_STATE_ALIASES.get(value.strip().lower())
        if wanted is not None:
            return wanted
    raise ValueError(
        "a promotion's state must be one of %s, got %r"
        % ("/".join(PROMOTION_STATES), value))


# ---------------------------------------------------------------------
# The candidate memory: one lesson or pattern, with provenance whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class CandidateMemory:
    """One candidate memory captured after significant work.

    ``kind`` is the candidate's kind in the closed
    set - a durable ``lesson`` or a reusable
    ``pattern``; ``title`` names the candidate;
    ``detail`` is the lesson or pattern itself, in
    plain words. The provenance stands whole beside
    it: ``source_work`` is the work it was learned
    in, ``context`` is the situation it was learned
    in, ``evidence`` is what it stands on, ``source``
    names where it was read from, and ``ref`` is
    where the thing it names lives. A candidate with
    any provenance word missing is no candidate at
    all - candidates are never captured anonymously.
    A candidate carries no standing of its own: it
    stands as a candidate until a promotion decision
    says otherwise.
    """

    kind: str
    title: str
    detail: str
    source_work: str
    context: str
    evidence: str
    source: str
    ref: str
    candidate_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.candidate_id is not None:
            object.__setattr__(
                self, "candidate_id",
                normalize_member_id(self.candidate_id))
        object.__setattr__(
            self, "kind", normalize_candidate_kind(self.kind))
        object.__setattr__(
            self, "title", _check_title(self.title, "a candidate's title"))
        object.__setattr__(
            self, "detail",
            _check_long_text(self.detail, "a candidate's detail"))
        object.__setattr__(
            self, "source_work",
            _check_work(
                self.source_work, "a candidate's source work"))
        object.__setattr__(
            self, "context",
            _check_long_text(self.context, "a candidate's context"))
        object.__setattr__(
            self, "evidence",
            _check_long_text(self.evidence, "a candidate's evidence"))
        object.__setattr__(
            self, "source",
            _check_title(self.source, "a candidate's source"))
        object.__setattr__(self, "ref", _check_ref(self.ref))

    @property
    def kind_index(self) -> int:
        """This candidate's kind's place in kind order (derived)."""
        return CANDIDATE_KINDS.index(self.kind)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "self_improving_candidate",
            "slice": SELF_IMPROVING_SLICE,
            "candidate_id": self.candidate_id,
            "kind": self.kind,
            "title": self.title,
            "detail": self.detail,
            "source_work": self.source_work,
            "context": self.context,
            "evidence": self.evidence,
            "source": self.source,
            "ref": self.ref,
        }


def _provenance_words(kind: Any, source_work: Any, context: Any,
                      evidence: Any) -> Tuple[str, str, str, str]:
    """The words a composed candidate must carry, or a refusal.

    A memory-map entry, a carried session note or a
    shared cross-project lesson becomes a candidate
    only when the words are named with it: its kind,
    the work it was learned in, the context it was
    learned in, and the evidence it stands on. A
    missing word refuses plainly - never a guessed
    or empty provenance. A shared lesson may stand
    in for its own context and evidence words (they
    are the lesson's own, carried whole), and for
    its source work (the project it was learned in);
    that stand-in is taken in :func:`validate_candidate`,
    not here.
    """
    if kind is None or source_work is None \
            or context is None or evidence is None:
        raise ValueError(
            "a candidate memory must carry its kind and "
            "its provenance: the work it was learned in, "
            "the context it was learned in and the "
            "evidence it stands on")
    return (
        normalize_candidate_kind(kind),
        _check_work(source_work, "a candidate's source work"),
        _check_long_text(context, "a candidate's context"),
        _check_long_text(evidence, "a candidate's evidence"))


def validate_candidate(candidate: Any, *, kind: Any = None,
                        source_work: Any = None,
                        context: Any = None,
                        evidence: Any = None) -> CandidateMemory:
    """Validate one candidate record into a CandidateMemory.

    Accepts a candidate; a shipped memory-map entry,
    a session-memory carried note or a cross-project
    shared lesson (whose title, detail, source and
    reference are read onto the candidate - the
    shipped memory layers composed by import - with
    the kind and provenance words named beside it:
    *kind*, *source_work*, *context* and *evidence*;
    a shared lesson's own source project, context
    and evidence stand in for those words when they
    are not named, and its kind defaults to
    ``lesson``); or a mapping naming a ``kind`` (or
    ``type_of_memory``), a ``title`` (or ``name``), a
    ``detail`` (or ``body``), a ``source_work`` (or
    ``work`` / ``from_work``), a ``context`` (or
    ``learned_in`` / ``situation``), an ``evidence``
    (or ``proof`` / ``backing``), a ``source``, a
    ``ref`` (or ``path`` / ``reference``) and an
    optional ``candidate_id`` (or ``id``). Naming
    two spellings of one field with different values
    refuses, and unknown keys refuse.
    """
    if isinstance(candidate, CandidateMemory):
        return candidate
    if isinstance(candidate, SharedLesson):
        named_kind = "lesson" if kind is None else kind
        named_work = candidate.source_project \
            if source_work is None else source_work
        named_context = candidate.context \
            if context is None else context
        named_evidence = candidate.evidence \
            if evidence is None else evidence
        kind_word, work, learned_in, stands_on = _provenance_words(
            named_kind, named_work, named_context, named_evidence)
        return CandidateMemory(
            kind=kind_word, title=candidate.title,
            detail=candidate.detail, source_work=work,
            context=learned_in, evidence=stands_on,
            source=candidate.source, ref=candidate.ref,
            candidate_id=candidate.lesson_id)
    if isinstance(candidate, (MemoryMapEntry, CarriedMemory)):
        kind_word, work, learned_in, stands_on = _provenance_words(
            kind, source_work, context, evidence)
        candidate_id = candidate.entry_id if isinstance(
            candidate, MemoryMapEntry) else candidate.note_id
        return CandidateMemory(
            kind=kind_word, title=candidate.title,
            detail=candidate.detail, source_work=work,
            context=learned_in, evidence=stands_on,
            source=candidate.source, ref=candidate.ref,
            candidate_id=candidate_id)
    if not isinstance(candidate, dict):
        raise ValueError(
            f"a candidate-memory record must be a mapping, "
            f"got {candidate!r}")
    unknown = set(candidate) - _CANDIDATE_KEYS
    if unknown:
        raise ValueError(
            "unknown candidate keys: %s"
            % ", ".join(sorted(unknown)))

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(candidate, spellings, what)
        if value is None:
            raise ValueError(f"a candidate record is missing its {what}")
        return value

    kwargs: Dict[str, Any] = {
        "kind": _needed(("kind", "type_of_memory"), "kind"),
        "title": _needed(("title", "name"), "title"),
        "detail": _needed(("detail", "body"), "detail"),
        "source_work": _needed(
            ("source_work", "work", "from_work"), "source work"),
        "context": _needed(
            ("context", "learned_in", "situation"), "context"),
        "evidence": _needed(
            ("evidence", "proof", "backing"), "evidence"),
        "source": _needed(("source",), "source"),
        "ref": _needed(("ref", "path", "reference"), "reference"),
    }
    named_id = _pick_any(candidate, ("candidate_id", "id"), "candidate ids")
    if named_id is not None:
        kwargs["candidate_id"] = named_id
    return CandidateMemory(**kwargs)


def build_candidate(candidate: Any = None, **kwargs: Any) -> CandidateMemory:
    """Build one validated candidate, from a mapping or field words.

    Kind and provenance words for a composed entry,
    note or lesson (``kind``, ``source_work``,
    ``context``, ``evidence``) may ride in the field
    words; in a mapping they are the record's own
    fields.
    """
    provenance = {
        key: kwargs.pop(key)
        for key in ("kind", "source_work", "context", "evidence")
        if key in kwargs}
    if isinstance(candidate, CandidateMemory) and not kwargs \
            and not provenance:
        return candidate
    if isinstance(candidate, (MemoryMapEntry, CarriedMemory, SharedLesson)):
        if kwargs:
            raise ValueError(
                "a composed candidate takes only its kind and "
                "provenance words")
        return validate_candidate(candidate, **provenance)
    if isinstance(candidate, dict) or candidate is None:
        merged: Dict[str, Any] = {}
        if isinstance(candidate, dict):
            merged.update(candidate)
        merged.update(provenance)
        merged.update(kwargs)
        return validate_candidate(merged)
    raise ValueError(
        f"a candidate-memory record must be a mapping, got {candidate!r}")


def _check_candidate_ref(value: Any) -> CandidateMemory:
    if isinstance(value, CandidateMemory):
        return value
    if isinstance(value, dict):
        return validate_candidate(value)
    raise ValueError(f"a candidate record is needed, got {value!r}")


# ---------------------------------------------------------------------
# The promotion decision: one candidate's explicit standing.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class PromotionDecision:
    """One candidate's promotion standing, decided explicitly.

    ``candidate_id`` names the candidate (a book or
    a registry judges that the candidate stands
    there - a decision names a real candidate or it
    is no decision); ``state`` is where the
    candidate stands - candidate, promoted, declined
    or quarantined; ``decided_by`` names who decided
    a decided state - the human or a named standing
    rule - and a candidate-state decision names no
    decider, because no word has been given yet;
    ``note`` says, in plain words, what the next
    reader needs to know about the standing. Nothing
    here updates any live memory: the state is the
    whole act, and only the promoted state lets a
    candidate stand as a standing memory, derived at
    call time by :func:`standing_memories`.
    """

    candidate_id: str
    state: str
    note: str
    decided_by: Optional[str] = None
    decision_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.decision_id is not None:
            object.__setattr__(
                self, "decision_id",
                normalize_member_id(self.decision_id))
        object.__setattr__(
            self, "candidate_id",
            normalize_member_id(self.candidate_id))
        object.__setattr__(
            self, "state", normalize_promotion_state(self.state))
        object.__setattr__(
            self, "note",
            _check_long_text(self.note, "a decision's note"))
        if self.state == "candidate":
            if self.decided_by not in (None, ""):
                raise ValueError(
                    "a candidate standing as a candidate names "
                    "no decider - no word has been given yet")
            object.__setattr__(self, "decided_by", None)
        else:
            if self.decided_by is None or (
                    isinstance(self.decided_by, str)
                    and not self.decided_by.strip()):
                raise ValueError(
                    "a decided state names its decider - the "
                    "human or a named standing rule; promotion "
                    "is explicit, never silent")
            object.__setattr__(
                self, "decided_by",
                _check_title(self.decided_by, "a decision's decider"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "self_improving_decision",
            "slice": SELF_IMPROVING_SLICE,
            "decision_id": self.decision_id,
            "candidate_id": self.candidate_id,
            "state": self.state,
            "decided_by": self.decided_by,
            "note": self.note,
        }


def validate_decision(decision: Any) -> PromotionDecision:
    """Validate one decision record into a PromotionDecision.

    Accepts a decision, a candidate standing as the
    decision of itself (its id names the candidate,
    with the state, decider and note named beside it
    as field words through :func:`build_decision`),
    or a mapping naming a ``candidate_id`` (or
    ``candidate``), a ``state`` (or ``status``), a
    ``note`` (or ``detail``), a ``decided_by`` (or
    ``decider`` / ``authority``) and an optional
    ``decision_id`` (or ``id``). A decided state
    naming no decider refuses, as does a
    candidate-state decision naming one. Naming two
    spellings of one field with different values
    refuses, and unknown keys refuse.
    """
    if isinstance(decision, PromotionDecision):
        return decision
    if not isinstance(decision, dict):
        raise ValueError(
            f"a promotion-decision record must be a mapping, "
            f"got {decision!r}")
    unknown = set(decision) - _DECISION_KEYS
    if unknown:
        raise ValueError(
            "unknown decision keys: %s"
            % ", ".join(sorted(unknown)))

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(decision, spellings, what)
        if value is None:
            raise ValueError(f"a decision record is missing its {what}")
        return value

    kwargs: Dict[str, Any] = {
        "candidate_id": _needed(
            ("candidate_id", "candidate"), "candidate id"),
        "state": _needed(("state", "status"), "state"),
        "note": _needed(("note", "detail"), "note"),
    }
    decider = _pick_any(
        decision, ("decided_by", "decider", "authority"), "deciders")
    if decider is not None:
        kwargs["decided_by"] = decider
    decision_id = _pick_any(decision, ("decision_id", "id"), "decision ids")
    if decision_id is not None:
        kwargs["decision_id"] = decision_id
    return PromotionDecision(**kwargs)


def build_decision(decision: Any = None, **kwargs: Any) -> PromotionDecision:
    """Build one validated decision, from a mapping or field words."""
    if isinstance(decision, PromotionDecision) and not kwargs:
        return decision
    if isinstance(decision, CandidateMemory):
        merged: Dict[str, Any] = {}
        if decision.candidate_id is None:
            raise ValueError(
                "a decision built from a candidate needs the "
                "candidate to carry an id")
        merged["candidate_id"] = decision.candidate_id
        merged.update(kwargs)
        return validate_decision(merged)
    if isinstance(decision, dict) or decision is None:
        merged = {}
        if isinstance(decision, dict):
            merged.update(decision)
        merged.update(kwargs)
        return validate_decision(merged)
    raise ValueError(
        f"a promotion-decision record must be a mapping, got {decision!r}")


def _check_decision_ref(value: Any) -> PromotionDecision:
    if isinstance(value, PromotionDecision):
        return value
    if isinstance(value, dict):
        return validate_decision(value)
    raise ValueError(f"a decision record is needed, got {value!r}")


# ---------------------------------------------------------------------
# The ledger panel: every candidate with its standing whole, derived.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class LedgerPanelRow:
    """One candidate carried whole into the panel, with its standing.

    ``state`` is the candidate's standing (its
    decision's state, or ``candidate`` while no
    decision stands on it); ``candidate_id`` names
    the candidate; ``kind``, ``title`` and ``detail``
    are the candidate's own words; ``source_work``
    is the candidate's provenance head - the work it
    was learned in. :func:`validate_row` judged
    against its candidate and decision refuses a row
    whose fields disagree with the row they derive -
    a panel row can never re-home a candidate or
    soften its standing.
    """

    state: str
    candidate_id: str
    kind: str
    title: str
    detail: str
    source_work: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "state", normalize_promotion_state(self.state))
        object.__setattr__(
            self, "candidate_id",
            normalize_member_id(self.candidate_id))
        object.__setattr__(
            self, "kind", normalize_candidate_kind(self.kind))
        object.__setattr__(
            self, "title", _check_title(self.title, "a row's title"))
        object.__setattr__(
            self, "detail",
            _check_long_text(self.detail, "a row's detail"))
        object.__setattr__(
            self, "source_work",
            _check_work(self.source_work, "a row's source work"))

    @property
    def sort_key(self) -> Tuple[int, str, str]:
        """This row's place in panel order (derived).

        Rows stand state first (promoted, candidate,
        declined, quarantined, in that settled order);
        within a state, by source work, then candidate
        title.
        """
        return (
            _PANEL_STATE_ORDER.index(self.state),
            self.source_work, self.title)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "self_improving_row",
            "slice": SELF_IMPROVING_SLICE,
            "state": self.state,
            "candidate_id": self.candidate_id,
            "kind": self.kind,
            "title": self.title,
            "detail": self.detail,
            "source_work": self.source_work,
        }


def _row_for_candidate(candidate: CandidateMemory,
                       decision: Any = None) -> LedgerPanelRow:
    if decision is not None and decision.candidate_id != candidate.candidate_id:
        raise ValueError(
            "a panel row's decision must be the candidate's own decision")
    return LedgerPanelRow(
        state=decision.state if decision is not None else "candidate",
        candidate_id=candidate.candidate_id,
        kind=candidate.kind, title=candidate.title,
        detail=candidate.detail,
        source_work=candidate.source_work)


def _check_row_ref(value: Any) -> LedgerPanelRow:
    if isinstance(value, LedgerPanelRow):
        return value
    if isinstance(value, dict):
        unknown = set(value) - _ROW_KEYS
        if unknown:
            raise ValueError(
                "unknown row keys: %s" % ", ".join(sorted(unknown)))

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            picked = _pick_any(value, spellings, what)
            if picked is None:
                raise ValueError(f"a row is missing its {what}")
            return picked

        return LedgerPanelRow(
            state=_needed(("state",), "state"),
            candidate_id=_needed(("candidate_id", "id"), "candidate id"),
            kind=_needed(("kind",), "kind"),
            title=_needed(("title",), "title"),
            detail=_needed(("detail",), "detail"),
            source_work=_needed(("source_work",), "source work"))
    raise ValueError(f"a panel row is needed, got {value!r}")


def validate_row(row: Any, candidate: Any = None,
                 decision: Any = None) -> LedgerPanelRow:
    """Validate one panel row into a LedgerPanelRow.

    Accepts a row or a mapping naming a ``state``, a
    ``candidate_id`` (or ``id``), a ``kind``, a
    ``title``, a ``detail`` and a ``source_work``.
    With *candidate* given (and its *decision*, or
    none), the row is judged against the row derived
    from that candidate and its standing: a stored
    row whose fields disagree with the derived row
    refuses.
    """
    current = _check_row_ref(row)
    if candidate is not None:
        checked_candidate = _check_candidate_ref(candidate)
        checked_decision = None if decision is None else _check_decision_ref(decision)
        derived = _row_for_candidate(checked_candidate, checked_decision)
        if current != derived:
            raise ValueError(
                "a stored row disagrees with the row "
                "derived from its candidate and decision")
    return current


def build_row(row: Any = None, candidate: Any = None,
              decision: Any = None,
              **kwargs: Any) -> LedgerPanelRow:
    """Build one validated row, from a mapping or field words."""
    if isinstance(row, LedgerPanelRow) and not kwargs:
        return validate_row(row, candidate, decision)
    if isinstance(row, dict) or row is None:
        merged: Dict[str, Any] = {}
        if isinstance(row, dict):
            merged.update(row)
        merged.update(kwargs)
        return validate_row(merged, candidate, decision)
    return validate_row(row, candidate, decision)


@dataclass(frozen=True)
class PromotionStateCount:
    """One state's count in a panel: its candidates tallied."""

    state: str
    items: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "state", normalize_promotion_state(self.state))
        object.__setattr__(
            self, "items",
            _check_count(self.items, "a state count's items"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "state": self.state,
            "items": self.items,
        }


def _check_state_count_ref(value: Any) -> PromotionStateCount:
    if isinstance(value, PromotionStateCount):
        return value
    if isinstance(value, dict):
        unknown = set(value) - _STATE_COUNT_KEYS
        if unknown:
            raise ValueError(
                "unknown state-count keys: %s"
                % ", ".join(sorted(unknown)))
        state = _pick_any(value, ("state",), "states")
        if state is None:
            raise ValueError("a state count is missing its state")
        items = _pick_any(value, ("items", "count"), "counts")
        if items is None:
            raise ValueError("a state count is missing its items")
        return PromotionStateCount(state=state, items=items)
    raise ValueError(f"a state count is needed, got {value!r}")


def _panel_account(total_items: int, total_promoted: int,
                   total_candidate: int, total_declined: int,
                   total_quarantined: int) -> Tuple[str, ...]:
    return (
        f"The ledger panel holds {total_items} candidates: "
        f"promoted {total_promoted}, candidate {total_candidate}, "
        f"declined {total_declined}, quarantined {total_quarantined}.",
        "Candidates stand promoted first, then candidate, "
        "then declined, then quarantined; within a state, "
        "by source work, then candidate title - so two "
        "panels of one book diff cleanly, line by line.",
        "A candidate stands as a standing memory only "
        "through an explicit promotion by the human or a "
        "named standing rule, and it stands there with "
        "its provenance whole - where it was learned, in "
        "what context, and on what evidence.",
        "The panel is read off the book at call time - "
        "it is derived, never stored loose.",
    )


@dataclass(frozen=True)
class LedgerPanel:
    """The ledger panel of one book, derived from the whole book.

    ``rows`` are the book's candidates with their
    standings carried whole, in panel order (promoted
    first, then candidate, then declined, then
    quarantined; within a state, by source work, then
    candidate title, so two panels of one book diff
    cleanly); ``total_items`` is the candidate count
    and the four state totals are the rows' own
    counts; ``state_counts`` are the per-state tallies
    in the order their states first appear in the
    panel; ``account`` is read off those numbers. A
    panel whose rows stand out of panel order, or
    whose totals are not its own rows' counts,
    refuses at construction; :func:`validate_panel`
    judged against a book refuses a stored panel
    that disagrees with the derived one.
    """

    rows: Tuple[LedgerPanelRow, ...] = ()
    total_items: int = 0
    total_promoted: int = 0
    total_candidate: int = 0
    total_declined: int = 0
    total_quarantined: int = 0
    state_counts: Tuple[PromotionStateCount, ...] = ()
    account: Tuple[str, ...] = ()
    panel_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.panel_id is not None:
            object.__setattr__(
                self, "panel_id",
                normalize_member_id(self.panel_id))
        if isinstance(self.rows, (str, bytes)) \
                or not isinstance(self.rows, (list, tuple)):
            raise ValueError(
                f"a panel's rows must be a list of rows, "
                f"got {self.rows!r}")
        rows = tuple(_check_row_ref(r) for r in self.rows)
        seen = set()
        for row in rows:
            if row.candidate_id in seen:
                raise ValueError(
                    f"a panel row for candidate "
                    f"{row.candidate_id!r} already exists")
            seen.add(row.candidate_id)
        order = [_PANEL_STATE_ORDER.index(r.state) for r in rows]
        if order != sorted(order):
            raise ValueError(
                "a panel's rows must stand in panel order "
                "(promoted, then candidate, then declined, "
                "then quarantined)")
        object.__setattr__(self, "rows", rows)
        for field_name, state, what in (
                ("total_promoted", "promoted", "promoted total"),
                ("total_candidate", "candidate", "candidate total"),
                ("total_declined", "declined", "declined total"),
                ("total_quarantined", "quarantined",
                 "quarantined total")):
            checked = _check_count(
                getattr(self, field_name), f"a panel's {what}")
            if checked != sum(1 for r in rows if r.state == state):
                raise ValueError(
                    f"a panel's {what} must be its own rows' count")
            object.__setattr__(self, field_name, checked)
        object.__setattr__(
            self, "total_items",
            _check_count(self.total_items, "a panel's total"))
        if self.total_items != len(rows):
            raise ValueError(
                "a panel's total must be its own rows' count")
        if isinstance(self.state_counts, (str, bytes)) \
                or not isinstance(self.state_counts, (list, tuple)):
            raise ValueError(
                f"a panel's state counts must be a list, "
                f"got {self.state_counts!r}")
        state_counts = tuple(
            _check_state_count_ref(c) for c in self.state_counts)
        seen_states = set()
        for count in state_counts:
            if count.state in seen_states:
                raise ValueError(
                    f"a state count named {count.state!r} "
                    f"already exists")
            seen_states.add(count.state)
        object.__setattr__(self, "state_counts", state_counts)
        if sum(c.items for c in state_counts) != self.total_items:
            raise ValueError(
                "a panel's state counts must sum to its own total")
        for count in state_counts:
            if count.items != sum(
                    1 for r in rows if r.state == count.state):
                raise ValueError(
                    "a panel's state counts must be its own "
                    "rows' counts")
        object.__setattr__(self, "account", _check_account(self.account))

    def row_for(self, candidate_id: Any) -> LedgerPanelRow:
        """The panel row one candidate names in this panel."""
        wanted = normalize_member_id(candidate_id)
        for row in self.rows:
            if row.candidate_id == wanted:
                return row
        raise KeyError(f"no row in the panel: candidate {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "self_improving_panel",
            "slice": SELF_IMPROVING_SLICE,
            "panel_id": self.panel_id,
            "rows": [row.to_record() for row in self.rows],
            "total_items": self.total_items,
            "total_promoted": self.total_promoted,
            "total_candidate": self.total_candidate,
            "total_declined": self.total_declined,
            "total_quarantined": self.total_quarantined,
            "state_counts": [c.to_record() for c in self.state_counts],
            "account": list(self.account),
        }


def _held_candidates(source: Any) -> Tuple[CandidateMemory, ...]:
    """The candidates one source holds, in held order."""
    if isinstance(source, SelfImprovingBook):
        return source.candidates
    if isinstance(source, SelfImprovingRegistry):
        return source.list_candidates()
    if isinstance(source, (list, tuple)):
        return tuple(_check_candidate_ref(item) for item in source)
    raise ValueError(f"candidates are needed, got {source!r}")


def _held_decisions(source: Any) -> Tuple[PromotionDecision, ...]:
    """The decisions one source holds, in held order."""
    if isinstance(source, SelfImprovingBook):
        return source.decisions
    if isinstance(source, SelfImprovingRegistry):
        return source.list_decisions()
    if isinstance(source, (list, tuple)):
        return tuple(_check_decision_ref(item) for item in source)
    raise ValueError(f"decisions are needed, got {source!r}")


def derive_panel(source: Any) -> LedgerPanel:
    """Derive the ledger panel from one book.

    The rows are the book's candidates with their
    standings carried whole, in panel order: promoted
    first, then candidate, then declined, then
    quarantined; within a state, by the candidate's
    source work, then its title. A candidate with no
    decision standing on it stands in the candidate
    state - capture alone never promotes. *source*
    is a book or a registry. A source holding no
    candidate refuses - a panel of nothing is no
    panel - and a decision naming a candidate the
    source does not hold refuses too.
    """
    candidates = _held_candidates(source)
    decisions = _held_decisions(source)
    if not candidates:
        raise ValueError("a panel needs at least one candidate")
    by_candidate: Dict[str, PromotionDecision] = {}
    for decision in decisions:
        if decision.candidate_id in by_candidate:
            raise ValueError(
                f"two decisions stand on candidate "
                f"{decision.candidate_id!r}")
        by_candidate[decision.candidate_id] = decision
    known = {item.candidate_id for item in candidates}
    for decision in decisions:
        if decision.candidate_id not in known:
            raise ValueError(
                f"a decision names a candidate the book does "
                f"not hold: {decision.candidate_id!r}")
    rows = []
    for candidate in candidates:
        if candidate.candidate_id is None:
            raise ValueError(
                "a panel row must name its candidate - a "
                "candidate with no id refuses derivation")
        rows.append(_row_for_candidate(
            candidate, by_candidate.get(candidate.candidate_id)))
    rows = tuple(sorted(rows, key=lambda r: r.sort_key))
    order: list = []
    tally: Dict[str, int] = {}
    for row in rows:
        if row.state not in tally:
            tally[row.state] = 0
            order.append(row.state)
        tally[row.state] += 1
    state_counts = tuple(
        PromotionStateCount(state=state, items=tally[state])
        for state in order)
    totals = {
        state: tally.get(state, 0) for state in PROMOTION_STATES}
    return LedgerPanel(
        rows=rows,
        total_items=len(rows),
        total_promoted=totals["promoted"],
        total_candidate=totals["candidate"],
        total_declined=totals["declined"],
        total_quarantined=totals["quarantined"],
        state_counts=state_counts,
        account=_panel_account(
            len(rows), totals["promoted"], totals["candidate"],
            totals["declined"], totals["quarantined"]))


def validate_panel(panel: Any, source: Any = None) -> LedgerPanel:
    """Validate one panel into a LedgerPanel.

    Accepts a panel or a mapping naming ``rows``
    (or ``candidates``), a ``total_items`` (or
    ``total``), the four state totals,
    ``state_counts`` (or ``states``), an ``account``
    (or ``statements``) and an optional ``panel_id``
    (or ``id``). With *source* given (a book), the
    panel is judged against the panel derived from
    that book: a stored panel whose rows, totals,
    state counts or account disagree with the
    derived panel refuses. A panel naming no
    account refuses too.
    """
    if isinstance(panel, LedgerPanel):
        current = panel
    elif isinstance(panel, dict):
        unknown = set(panel) - _PANEL_KEYS
        if unknown:
            raise ValueError(
                "unknown panel keys: %s" % ", ".join(sorted(unknown)))
        rows = _pick_any(panel, ("rows", "candidates"), "rows")
        if rows is None:
            raise ValueError("a panel is missing its rows")
        total = _pick_any(
            panel, ("total_items", "total"), "totals")
        if total is None:
            raise ValueError("a panel is missing its total items")
        state_counts = _pick_any(
            panel, ("state_counts", "states"), "state counts")
        if state_counts is None:
            raise ValueError("a panel is missing its state counts")
        account = _pick_any(panel, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError("a panel names no account of its own")
        kwargs: Dict[str, Any] = {
            "rows": rows, "total_items": total,
            "state_counts": state_counts, "account": account}
        for field_name in (
                "total_promoted", "total_candidate",
                "total_declined", "total_quarantined"):
            value = _pick_any(panel, (field_name,), field_name)
            if value is None:
                raise ValueError(f"a panel is missing its {field_name}")
            kwargs[field_name] = value
        panel_id = _pick_any(panel, ("panel_id", "id"), "panel ids")
        if panel_id is not None:
            kwargs["panel_id"] = panel_id
        current = LedgerPanel(**kwargs)
    else:
        raise ValueError(f"a panel must be a mapping, got {panel!r}")
    if source is not None:
        derived = derive_panel(source)
        if (current.rows != derived.rows
                or current.total_items != derived.total_items
                or current.total_promoted != derived.total_promoted
                or current.total_candidate != derived.total_candidate
                or current.total_declined != derived.total_declined
                or current.total_quarantined != derived.total_quarantined
                or current.state_counts != derived.state_counts
                or current.account != derived.account):
            raise ValueError(
                "a stored panel disagrees with the panel "
                "derived from its book")
    return current


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> LedgerPanel:
    """Build one validated panel, from a mapping or field words."""
    if isinstance(panel, LedgerPanel) and not kwargs:
        return validate_panel(panel, source)
    if isinstance(panel, dict) or panel is None:
        merged: Dict[str, Any] = {}
        if isinstance(panel, dict):
            merged.update(panel)
        merged.update(kwargs)
        return validate_panel(merged, source)
    return validate_panel(panel, source)


# ---------------------------------------------------------------------
# The composition roads: the shipped memory layers and charter, by import.
# ---------------------------------------------------------------------


def self_improving_directives() -> Tuple[str, ...]:
    """The Self-Improving Forge tenet's directives, by import.

    The capture doctrine this ledger executes is the
    shipped method charter's own: its
    ``self-improving-forge`` tenet (the
    ``YRSA_SELF_IMPROVING_FORGE`` plug, F-06) is read
    through the charter layer BY IMPORT and its
    directives are returned whole - after significant
    work, capture the durable lessons it taught; when
    a pattern repeats, extract it into reusable
    machinery. No second statement of the doctrine is
    kept here.
    """
    return load_charter().tenet(SELF_IMPROVING_TENET).directives


def candidate_from_map_entry(entry: Any, *, kind: Any,
                             source_work: Any, context: Any,
                             evidence: Any) -> CandidateMemory:
    """Build one candidate from a shipped memory-map entry.

    The entry - the project memory map's own record,
    judged by the map's own validation - is read onto
    a candidate BY IMPORT: its title, its detail, its
    source and its reference stand exactly as the map
    holds them. The kind and provenance words are
    named beside it: the candidate's kind, the work
    the lesson was learned in, the context it was
    learned in, and the evidence it stands on.
    Without all of them, the entry stays a fact of
    its own project - it is not captured.
    """
    validated = _validate_map_entry(entry)
    return validate_candidate(
        validated, kind=kind, source_work=source_work,
        context=context, evidence=evidence)


def _map_entries(source: Any) -> Tuple[MemoryMapEntry, ...]:
    """The shipped map entries one source holds, judged by the map."""
    from .project_memory_map import MemoryMapBook, MemoryMapRegistry
    if isinstance(source, MemoryMapBook):
        return source.entries
    if isinstance(source, MemoryMapRegistry):
        return source.list_entries()
    if isinstance(source, (list, tuple)):
        return tuple(_validate_map_entry(e) for e in source)
    if isinstance(source, (MemoryMapEntry, dict)):
        return (_validate_map_entry(source),)
    raise ValueError(f"memory map entries are needed, got {source!r}")


def candidates_from_memory_map(source: Any, *, kind: Any,
                               source_work: Any, context: Any,
                               evidence: Any
                               ) -> Tuple[CandidateMemory, ...]:
    """Candidates read off the shipped project memory map.

    Every entry of the shipped map - a book, a
    registry, the entries themselves, or one entry -
    is read onto a candidate BY IMPORT, judged by the
    map's own validation on the way, under one frame:
    the kind the entries are captured as, the work
    they were learned in, the context they were
    learned in, and the evidence they stand on.
    Nothing here re-names a fact or re-words it, and
    no entry is captured without the frame. Every
    candidate stands as a candidate - capture
    promotes nothing.
    """
    return tuple(
        validate_candidate(
            entry, kind=kind, source_work=source_work,
            context=context, evidence=evidence)
        for entry in _map_entries(source))


def _carried_notes(source: Any) -> Tuple[CarriedMemory, ...]:
    """The carried notes one session-memory source holds."""
    from .session_memory import SessionMemoryBook, SessionMemoryRegistry
    if isinstance(source, SessionSituation):
        return source.memory
    if isinstance(source, SessionMemoryBook):
        notes: list = []
        for situation in source.situations:
            notes.extend(situation.memory)
        return tuple(notes)
    if isinstance(source, SessionMemoryRegistry):
        notes = []
        for situation in source.list_situations():
            notes.extend(situation.memory)
        return tuple(notes)
    if isinstance(source, (list, tuple)):
        return tuple(
            note if isinstance(note, CarriedMemory)
            else _validate_session_note(note)
            for note in source)
    raise ValueError(f"carried notes are needed, got {source!r}")


def candidates_from_session_memory(source: Any, *, kind: Any,
                                   source_work: Any, context: Any,
                                   evidence: Any
                                   ) -> Tuple[CandidateMemory, ...]:
    """Candidates read off the shipped session memory.

    The carried notes of a session situation - or of
    a whole session-memory book or registry - are
    read onto candidates BY IMPORT: a fact a session
    carried across its days can be captured for the
    learning loop, under one frame (the kind, the
    work, the context and the evidence, all named).
    The note's own title, detail, source and
    reference stand exactly as the situation holds
    them.
    """
    return tuple(
        validate_candidate(
            note, kind=kind, source_work=source_work,
            context=context, evidence=evidence)
        for note in _carried_notes(source))


def _shared_lessons(source: Any) -> Tuple[SharedLesson, ...]:
    """The shared lessons one cross-project source holds."""
    from .cross_project_memory import (
        CrossProjectBook, CrossProjectRegistry)
    if isinstance(source, CrossProjectBook):
        return source.lessons
    if isinstance(source, CrossProjectRegistry):
        return source.list_lessons()
    if isinstance(source, (list, tuple)):
        return tuple(_validate_shared_lesson(e) for e in source)
    if isinstance(source, (SharedLesson, dict)):
        return (_validate_shared_lesson(source),)
    raise ValueError(f"shared lessons are needed, got {source!r}")


def candidates_from_cross_project(source: Any, *, kind: Any = None,
                                  source_work: Any = None,
                                  context: Any = None,
                                  evidence: Any = None
                                  ) -> Tuple[CandidateMemory, ...]:
    """Candidates read off the shipped cross-project memory.

    The shared lessons of a cross-project book, a
    registry, the lessons themselves, or one lesson
    are read onto candidates BY IMPORT: a lesson one
    project offered to others can be captured for the
    learning loop. The lesson's own provenance stands
    in where a word is not named - its source project
    for the source work, its context and evidence for
    theirs - and its kind defaults to ``lesson``; a
    named word overrides the stand-in. The lesson's
    title, detail, source and reference stand exactly
    as the exchange holds them.
    """
    return tuple(
        validate_candidate(
            lesson, kind=kind, source_work=source_work,
            context=context, evidence=evidence)
        for lesson in _shared_lessons(source))


def standing_memories(source: Any) -> Tuple[CandidateMemory, ...]:
    """The candidates standing as standing memories in one source.

    This derivation is the ONLY road by which a
    candidate stands as a standing memory on this
    layer: the candidates of *source* (a book or a
    registry) whose promotion decision stands in the
    promoted state, read in panel order, each
    candidate carried whole - its provenance standing
    beside it exactly as it was learned. A candidate
    with no decision, a declined candidate and a
    quarantined candidate stand nowhere here: not
    yet, or not at all. Nothing is copied into any
    live memory - the standing is derived at call
    time.
    """
    candidates = _held_candidates(source)
    decisions = _held_decisions(source)
    by_candidate: Dict[str, PromotionDecision] = {}
    for decision in decisions:
        if decision.candidate_id in by_candidate:
            raise ValueError(
                f"two decisions stand on candidate "
                f"{decision.candidate_id!r}")
        by_candidate[decision.candidate_id] = decision
    standing = []
    for candidate in candidates:
        decision = by_candidate.get(candidate.candidate_id)
        if decision is not None and decision.state == "promoted":
            standing.append(candidate)
    return tuple(sorted(
        standing,
        key=lambda item: (item.source_work, item.title)))


# ---------------------------------------------------------------------
# The book: candidates and decisions in held order, panels judged.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class SelfImprovingBook:
    """One self-improving book: its candidates and decisions, held.

    ``candidates`` are the candidate memories, in
    held order, each with its provenance whole;
    ``decisions`` are the promotion decisions, in
    held order, each judged against the book's
    candidates at construction: a decision names a
    candidate the book holds, and no candidate
    carries two decisions. A candidate with no
    decision stands as a candidate - capture alone
    never promotes. ``panels`` are the book's
    derivations - ledger panels of the whole book,
    each judged against the book by
    :func:`validate_book`; ``canon_note`` is the
    book's own note. The totals are the records' own
    counts, judged at construction. This book is the
    book file's shape: the shipped example is one
    book, and a real book file is a new file in this
    shape.
    """

    title: str = ""
    candidates: Tuple[CandidateMemory, ...] = ()
    decisions: Tuple[PromotionDecision, ...] = ()
    panels: Tuple[LedgerPanel, ...] = ()
    canon_note: str = ""
    total_candidates: Optional[int] = None
    total_decisions: Optional[int] = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book's title"))
        if isinstance(self.candidates, (str, bytes)) \
                or not isinstance(self.candidates, (list, tuple)):
            raise ValueError(
                f"a book's candidates must be a list of "
                f"candidate records, got {self.candidates!r}")
        candidates = tuple(
            _check_candidate_ref(item) for item in self.candidates)
        if not candidates:
            raise ValueError(
                "a self-improving book holds at least one candidate")
        seen_ids = set()
        seen_facts = set()
        for candidate in candidates:
            if candidate.candidate_id is not None:
                if candidate.candidate_id in seen_ids:
                    raise ValueError(
                        f"a candidate named "
                        f"{candidate.candidate_id!r} already exists")
                seen_ids.add(candidate.candidate_id)
            key = (candidate.source_work, candidate.kind, candidate.title)
            if key in seen_facts:
                raise ValueError(
                    f"the candidate {candidate.title!r} already "
                    f"stands in this book from {candidate.source_work}")
            seen_facts.add(key)
        object.__setattr__(self, "candidates", candidates)
        if isinstance(self.decisions, (str, bytes)) \
                or not isinstance(self.decisions, (list, tuple)):
            raise ValueError(
                f"a book's decisions must be a list of "
                f"decision records, got {self.decisions!r}")
        decisions = tuple(
            _check_decision_ref(item) for item in self.decisions)
        by_id = {item.candidate_id: item for item in candidates}
        seen_decisions = set()
        seen_on = set()
        for decision in decisions:
            if decision.decision_id is not None:
                if decision.decision_id in seen_decisions:
                    raise ValueError(
                        f"a decision named "
                        f"{decision.decision_id!r} already exists")
                seen_decisions.add(decision.decision_id)
            if decision.candidate_id not in by_id:
                raise ValueError(
                    f"a decision names a candidate the book does "
                    f"not hold: {decision.candidate_id!r}")
            if decision.candidate_id in seen_on:
                raise ValueError(
                    f"two decisions stand on candidate "
                    f"{decision.candidate_id!r}")
            seen_on.add(decision.candidate_id)
        object.__setattr__(self, "decisions", decisions)
        if isinstance(self.panels, (str, bytes)) \
                or not isinstance(self.panels, (list, tuple)):
            raise ValueError(
                f"a book's panels must be a list of panels, "
                f"got {self.panels!r}")
        panels = tuple(
            p if isinstance(p, LedgerPanel) else validate_panel(p)
            for p in self.panels)
        seen_panels = set()
        for panel in panels:
            if panel.panel_id is not None:
                if panel.panel_id in seen_panels:
                    raise ValueError(
                        f"a panel named {panel.panel_id!r} "
                        f"already exists")
                seen_panels.add(panel.panel_id)
        object.__setattr__(self, "panels", panels)
        if not isinstance(self.canon_note, str):
            raise ValueError("a book's note must be text")
        object.__setattr__(
            self, "canon_note", self.canon_note.strip())
        for field_name, held, what in (
                ("total_candidates", candidates, "candidates"),
                ("total_decisions", decisions, "decisions")):
            given = getattr(self, field_name)
            if given is None:
                object.__setattr__(self, field_name, len(held))
            else:
                checked = _check_count(
                    given, f"a book's total {what}")
                if checked != len(held):
                    raise ValueError(
                        f"a book's total {what} must be its "
                        f"own records' count")
                object.__setattr__(self, field_name, checked)

    def candidate_for(self, candidate_id: Any) -> CandidateMemory:
        """The candidate one id names in this book."""
        wanted = normalize_member_id(candidate_id)
        for candidate in self.candidates:
            if candidate.candidate_id == wanted:
                return candidate
        raise KeyError(f"no candidate in the book: {wanted!r}")

    def decision_for(self, decision_id: Any) -> PromotionDecision:
        """The decision one id names in this book."""
        wanted = normalize_member_id(decision_id)
        for decision in self.decisions:
            if decision.decision_id == wanted:
                return decision
        raise KeyError(f"no decision in the book: {wanted!r}")

    def panel_for(self, panel_id: Any) -> LedgerPanel:
        """The stored panel one id names in this book."""
        wanted = normalize_member_id(panel_id)
        for panel in self.panels:
            if panel.panel_id == wanted:
                return panel
        raise KeyError(f"no panel in the book: {wanted!r}")

    def candidate_ids(self) -> Tuple[str, ...]:
        """Every held candidate id, in held order."""
        return tuple(
            item.candidate_id for item in self.candidates
            if item.candidate_id)

    def decision_ids(self) -> Tuple[str, ...]:
        """Every held decision id, in held order."""
        return tuple(
            item.decision_id for item in self.decisions
            if item.decision_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "self_improving_book",
            "slice": SELF_IMPROVING_SLICE,
            "title": self.title,
            "candidate_ids": list(self.candidate_ids()),
            "candidate_count": len(self.candidates),
            "decision_ids": list(self.decision_ids()),
            "decision_count": len(self.decisions),
            "panel_count": len(self.panels),
        }


def validate_book(data: Any, *, require_example: bool = False
                  ) -> SelfImprovingBook:
    """Validate one self-improving mapping into a book.

    The mapping names a ``schema`` (the
    self-improving schema word), a ``guide`` mapping
    (its ``title``), a ``candidates`` list, a
    ``decisions`` list and an optional ``panels``
    list. Every record stands on its own validation,
    then the whole is judged: candidate and decision
    ids unique, every decision judged against the
    book's candidates (a real candidate, never two
    on one candidate), and every stored panel judged
    against the book (a panel the book does not
    derive refuses). With ``require_example`` the
    shipped example is held to its pinned shape: the
    pinned title, candidates and panel, and the
    panel's pinned rows and account word-for-word.
    Problems raise :class:`ValidationError` or
    ``ValueError``.
    """
    if isinstance(data, SelfImprovingBook):
        return data
    if not isinstance(data, dict):
        raise ValidationError(
            f"a self-improving book must be a mapping, got {data!r}")
    unknown = set(data) - _SELF_IMPROVING_KEYS
    if unknown:
        raise ValidationError(
            "unknown self-improving keys: %s"
            % ", ".join(sorted(unknown)))
    if data.get("schema") != SELF_IMPROVING_SCHEMA:
        raise ValidationError(
            f"a self-improving book must carry schema "
            f"{SELF_IMPROVING_SCHEMA!r}, got {data.get('schema')!r}")
    candidates = _pick_any(data, ("candidates",), "candidates")
    if candidates is None:
        raise ValidationError(
            "a self-improving book is missing its candidates")
    if not isinstance(candidates, (list, tuple)):
        raise ValidationError(
            "a self-improving book's candidates must be a list")
    decisions = _pick_any(data, ("decisions",), "decisions")
    if decisions is None:
        raise ValidationError(
            "a self-improving book is missing its decisions")
    if not isinstance(decisions, (list, tuple)):
        raise ValidationError(
            "a self-improving book's decisions must be a list")
    if data.get("panels") is not None \
            and not isinstance(data["panels"], (list, tuple)):
        raise ValidationError(
            "a self-improving book's panels must be a list")
    head = data.get("guide") or {}
    if not isinstance(head, dict):
        raise ValidationError(
            "a self-improving book's guide must be a mapping")
    unknown_head = set(head) - _BOOK_KEYS
    if unknown_head:
        raise ValidationError(
            "unknown guide keys: %s" % ", ".join(sorted(unknown_head)))
    try:
        title = _pick_any(head, ("title", "name"), "titles")
        if title is None:
            raise ValidationError(
                "a self-improving book is missing its title")
        note = data.get("canon_note") or ""
        if not isinstance(note, str):
            raise ValidationError(
                "a self-improving book's note must be text")
        book = SelfImprovingBook(
            title=title, candidates=tuple(candidates),
            decisions=tuple(decisions),
            panels=tuple(data.get("panels") or ()),
            canon_note=note)
        for panel in book.panels:
            validate_panel(panel, book)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    if require_example:
        if book.title != _EXAMPLE_TITLE:
            raise ValidationError(
                "the shipped example self-improving book's title "
                "is not the pinned title")
        if book.candidate_ids() != _EXAMPLE_CANDIDATE_IDS:
            raise ValidationError(
                "the shipped example's candidates are not "
                "the pinned records")
        panel = book.panel_for(_EXAMPLE_PANEL_ID)
        if tuple(r.candidate_id for r in panel.rows) \
                != _EXAMPLE_PANEL_ROW_IDS:
            raise ValidationError(
                "the shipped example panel does not name "
                "its pinned rows in panel order")
        if panel.account != _EXAMPLE_PANEL_ACCOUNT:
            raise ValidationError(
                "the shipped example panel does not carry "
                "its pinned account word-for-word")
        first = book.candidates[0]
        if first.candidate_id != _EXAMPLE_FIRST_CANDIDATE_ID \
                or first.source_work != _EXAMPLE_FIRST_CANDIDATE_WORK:
            raise ValidationError(
                "the shipped example's first candidate is not "
                "its pinned candidate from its pinned work")
    return book


def build_book(book: Any = None, **kwargs: Any) -> SelfImprovingBook:
    """Build one validated book, from a mapping or field words."""
    if isinstance(book, SelfImprovingBook) and not kwargs:
        return book
    if isinstance(book, dict):
        if "schema" in book:
            return validate_book(book)
        merged: Dict[str, Any] = dict(book)
        merged.update(kwargs)
        return SelfImprovingBook(**merged)
    if book is None:
        return SelfImprovingBook(**kwargs)
    raise ValueError(f"a self-improving book is needed, got {book!r}")


def _book_from(data: Any, *, require_example: bool) -> SelfImprovingBook:
    try:
        return validate_book(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_self_improving_ledger(
        data: Optional[Dict[str, Any]] = None) -> SelfImprovingBook:
    """Load and validate the shipped example book (or *data*).

    The shipped file is held to the example check:
    the pinned title, candidate records and panel -
    the M-154 slice boundary book - so the shipped
    book covers the canon this slice exists to hold.
    """
    raw = data if data is not None else load_resource(
        SELF_IMPROVING_RESOURCE)
    return _book_from(raw, require_example=True)


def load_self_improving_ledger_file(path: Any) -> SelfImprovingBook:
    """Load and validate a self-improving book from a file at *path*.

    Any file in the self-improving shape, anywhere on
    disk, validated whole - a malformed file raises
    :class:`ValidationError` naming the problem, and
    a missing file raises ``FileNotFoundError``. The
    example check is not held: a real book stands on
    its own records.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _book_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The registry model: one book held candidate and decision by decision.
# ---------------------------------------------------------------------


class SelfImprovingRegistry:
    """One session's candidates and decisions, held one by one.

    The registry holds candidate and decision
    records, never panels: the panel is a derivation,
    read off the whole held book at call time, so
    nothing here can hold a figure stale. A decision
    is held only against a candidate already standing
    here, and never two on one candidate - the
    registry judges a decision exactly as a book
    does. Capture alone promotes nothing: a candidate
    held here stands as a candidate until a promoted
    decision stands on it.
    """

    def __init__(self, book: Any = None) -> None:
        self._title: Optional[str] = None
        self._candidates: Dict[str, CandidateMemory] = {}
        self._candidate_order: list = []
        self._decisions: Dict[str, PromotionDecision] = {}
        self._decision_order: list = []
        self._next_candidate = 1
        self._next_decision = 1
        if book is not None:
            self.register_book(book)

    def _fresh_candidate_id(self, held_ids: Any) -> str:
        while f"candidate-{self._next_candidate}" in held_ids:
            self._next_candidate += 1
        fresh = f"candidate-{self._next_candidate}"
        self._next_candidate += 1
        return fresh

    def _fresh_decision_id(self, held_ids: Any) -> str:
        while f"decision-{self._next_decision}" in held_ids:
            self._next_decision += 1
        fresh = f"decision-{self._next_decision}"
        self._next_decision += 1
        return fresh

    def register_candidate(self, candidate: Any) -> CandidateMemory:
        """Register one candidate into the held book.

        A record with no id is given a deterministic
        ``candidate-N`` id. A record id already
        standing here refuses, as does a fact one work
        already stands in this book.
        """
        validated = _check_candidate_ref(candidate)
        held_ids = set(self._candidates)
        if validated.candidate_id is not None \
                and validated.candidate_id in held_ids:
            raise ValueError(
                f"a candidate named "
                f"{validated.candidate_id!r} already exists")
        for held in self._candidates.values():
            if (held.source_work, held.kind, held.title) == (
                    validated.source_work, validated.kind,
                    validated.title):
                raise ValueError(
                    f"the candidate {validated.title!r} already "
                    f"stands in this book from "
                    f"{validated.source_work}")
        if validated.candidate_id is None:
            validated = replace(
                validated,
                candidate_id=self._fresh_candidate_id(held_ids))
        self._candidates[validated.candidate_id] = validated
        self._candidate_order.append(validated.candidate_id)
        return validated

    def register_decision(self, decision: Any) -> PromotionDecision:
        """Register one decision into the held book.

        The decision is judged as a book judges it:
        its candidate must already stand here, no
        candidate carries two decisions, and a record
        with no id is given a deterministic
        ``decision-N`` id. A refusal holds nothing new.
        """
        validated = _check_decision_ref(decision)
        if validated.candidate_id not in self._candidates:
            raise ValueError(
                f"a decision names a candidate the book does "
                f"not hold: {validated.candidate_id!r}")
        for held in self._decisions.values():
            if held.candidate_id == validated.candidate_id:
                raise ValueError(
                    f"two decisions stand on candidate "
                    f"{validated.candidate_id!r}")
        held_ids = set(self._decisions)
        if validated.decision_id is not None \
                and validated.decision_id in held_ids:
            raise ValueError(
                f"a decision named "
                f"{validated.decision_id!r} already exists")
        if validated.decision_id is None:
            validated = replace(
                validated,
                decision_id=self._fresh_decision_id(held_ids))
        self._decisions[validated.decision_id] = validated
        self._decision_order.append(validated.decision_id)
        return validated

    def register_book(self, book: Any) -> SelfImprovingBook:
        """Register every candidate and decision of one book, in order.

        The first book held sets the title; a later
        book under a different title refuses, as does
        a book naming a held candidate or decision id.
        The book's panels are derivations, not
        holdings, and are not held.
        """
        validated = build_book(book)
        if self._title is not None and validated.title != self._title:
            raise ValueError(
                "this registry already holds a self-improving "
                "book under a different title")
        for candidate in validated.candidates:
            if candidate.candidate_id in self._candidates:
                raise ValueError(
                    f"a candidate named "
                    f"{candidate.candidate_id!r} already exists")
        for decision in validated.decisions:
            if decision.decision_id in self._decisions:
                raise ValueError(
                    f"a decision named "
                    f"{decision.decision_id!r} already exists")
        self._title = validated.title
        for candidate in validated.candidates:
            self.register_candidate(candidate)
        for decision in validated.decisions:
            self.register_decision(decision)
        return self.book()

    def get_candidate(self, candidate_id: Any) -> CandidateMemory:
        """The candidate one id names among the held records."""
        wanted = normalize_member_id(candidate_id)
        if wanted not in self._candidates:
            raise KeyError(f"unknown candidate: {wanted!r}")
        return self._candidates[wanted]

    def get_decision(self, decision_id: Any) -> PromotionDecision:
        """The decision one id names among the held records."""
        wanted = normalize_member_id(decision_id)
        if wanted not in self._decisions:
            raise KeyError(f"unknown decision: {wanted!r}")
        return self._decisions[wanted]

    def latest_candidate(self) -> CandidateMemory:
        """The most recently held candidate."""
        if not self._candidate_order:
            raise ValueError("no candidate is held yet")
        return self._candidates[self._candidate_order[-1]]

    def list_candidates(self) -> Tuple[CandidateMemory, ...]:
        """Every held candidate, in the order they were held."""
        return tuple(
            self._candidates[item] for item in self._candidate_order)

    def list_decisions(self) -> Tuple[PromotionDecision, ...]:
        """Every held decision, in the order they were held."""
        return tuple(
            self._decisions[item] for item in self._decision_order)

    def book(self) -> SelfImprovingBook:
        """The held candidates and decisions as one validated book."""
        if self._title is None:
            raise ValueError("no self-improving book is held yet")
        return SelfImprovingBook(
            title=self._title, candidates=self.list_candidates(),
            decisions=self.list_decisions())

    def panel(self) -> LedgerPanel:
        """Derive the ledger panel of the whole held book."""
        return derive_panel(self)

    def standing_memories(self) -> Tuple[CandidateMemory, ...]:
        """The held candidates standing as standing memories."""
        return standing_memories(self)


# ---------------------------------------------------------------------
# Candidate news, shaped as session records.
# ---------------------------------------------------------------------


def candidate_record(candidate: Any) -> Dict[str, Any]:
    """The session-news record of one candidate memory."""
    current = candidate if isinstance(candidate, CandidateMemory) \
        else build_candidate(candidate)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.title} ({current.kind}) learned in "
        f"{current.source_work} at {current.ref}: "
        f"{current.detail}")
    return record


def decision_record(decision: Any) -> Dict[str, Any]:
    """The session-news record of one promotion decision."""
    current = decision if isinstance(decision, PromotionDecision) \
        else build_decision(decision)
    record = current.to_record()
    record["news"] = True
    decider = current.decided_by or "no word yet"
    record["headline"] = (
        f"Candidate {current.candidate_id} stands "
        f"{current.state} (decided by {decider}): "
        f"{current.note}")
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived panel.

    With *source* given, the panel is first judged
    against the panel that source derives.
    """
    current = validate_panel(panel, source)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Self-improving ledger panel: {current.total_items} "
        f"candidates - promoted {current.total_promoted}, "
        f"candidate {current.total_candidate}, declined "
        f"{current.total_declined}, quarantined "
        f"{current.total_quarantined}.")
    return record


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one self-improving book."""
    current = book if isinstance(book, SelfImprovingBook) \
        else build_book(book)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Self-improving ledger {current.title}: "
        f"{record['candidate_count']} candidates named, "
        f"{record['decision_count']} decisions standing.")
    return record


def plain_words(candidate: Any) -> str:
    """One candidate memory, in one plain sentence."""
    current = candidate if isinstance(candidate, CandidateMemory) \
        else build_candidate(candidate)
    return (
        f"{current.title} - a {current.kind} candidate "
        f"learned in {current.source_work} "
        f"({current.context}), standing on "
        f"{current.evidence}: {current.detail} "
        f"(read from {current.source} at {current.ref}).")


def panel_plain_words(source: Any) -> str:
    """The ledger panel in plain words, in full.

    Accepts a LedgerPanel or a SelfImprovingBook
    (whose derived panel is told). The panel is told
    whole - its rows in panel order and its account.
    """
    if isinstance(source, LedgerPanel):
        panel = validate_panel(source)
        title = None
    elif isinstance(source, SelfImprovingBook):
        panel = derive_panel(source)
        title = source.title
    else:
        raise ValueError(
            f"a self-improving source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Candidates, in panel order:")
    for row in panel.rows:
        lines.append(
            f"{row.candidate_id}: {row.state} - {row.title} "
            f"(a {row.kind} from {row.source_work}): "
            f"{row.detail}")
    lines.extend(panel.account)
    return "\n".join(lines)


# ---------------------------------------------------------------------
# Screens: the formatters and the shared /ledger grammar.
# ---------------------------------------------------------------------


def _source_book(source: Any) -> SelfImprovingBook:
    if source is None:
        return load_self_improving_ledger()
    if isinstance(source, SelfImprovingRegistry):
        return source.book()
    if isinstance(source, SelfImprovingBook):
        return source
    raise ValueError(
        f"a self-improving book is needed, got {source!r}")


def format_candidate(candidate: Any) -> str:
    """One candidate memory as a screen block, provenance whole."""
    current = candidate if isinstance(candidate, CandidateMemory) \
        else build_candidate(candidate)
    return "\n".join([
        f"{current.candidate_id or '-'}: {current.title} - "
        f"{current.kind}, learned in {current.source_work}",
        f"Learned in this context: {current.context}",
        f"Standing on this evidence: {current.evidence}",
        f"{current.detail} (from {current.source} "
        f"at {current.ref})",
    ])


def format_candidates(source: Any = None) -> str:
    """Candidate memories of one book, in held order."""
    book = _source_book(source)
    lines = [
        f"{item.candidate_id or '-'}: {item.title} - "
        f"{item.kind} (learned in "
        f"{item.source_work}): {item.detail}"
        for item in book.candidates]
    if not lines:
        lines.append("No candidates are held.")
    return "\n".join(lines)


def format_decisions(source: Any = None) -> str:
    """Decisions of one book, in held order."""
    book = _source_book(source)
    lines = []
    for decision in book.decisions:
        candidate = book.candidate_for(decision.candidate_id)
        decider = decision.decided_by or "no word yet"
        lines.append(
            f"{decision.decision_id or '-'}: {decision.candidate_id} "
            f"({candidate.title}) from {candidate.source_work} "
            f"- {decision.state} (decided by {decider}): "
            f"{decision.note}")
    if not lines:
        lines.append("No decisions are standing.")
    return "\n".join(lines)


def format_standing(source: Any = None) -> str:
    """The candidates standing as standing memories in one book."""
    standing = standing_memories(_source_book(source))
    lines = [
        f"{item.candidate_id or '-'}: {item.title} - "
        f"learned in {item.source_work} "
        f"({item.context}), standing on "
        f"{item.evidence}: {item.detail}"
        for item in standing]
    if not lines:
        lines.append("No candidates stand promoted yet.")
    return "\n".join(lines)


def format_panel(source: Any = None) -> str:
    """The ledger panel as a screen block: every row and the account.

    Accepts a LedgerPanel or a SelfImprovingBook; a
    book shows the panel it derives.
    """
    if isinstance(source, LedgerPanel):
        panel = validate_panel(source)
        lines: list = []
    else:
        book = _source_book(source)
        if not book.candidates:
            return (f"Ledger panel in {book.title}:\n"
                    f"No candidates are held.")
        panel = derive_panel(book)
        lines = [f"Ledger panel in {book.title}:"]
    lines.append("Candidates, in panel order:")
    for row in panel.rows:
        lines.append(
            f"{row.candidate_id}: {row.state} - {row.title} "
            f"(a {row.kind} from {row.source_work}): "
            f"{row.detail}")
    lines.extend(panel.account)
    return "\n".join(lines)


def format_self_improving_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /ledger.

    With nothing named, the shipped example
    self-improving book is shown - the example this
    slice ships - so the screen is never empty.
    """
    book = _source_book(source)
    lines = ["Self-Improving Ledger (M-155) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_candidates(book))
    lines.append("")
    lines.append(format_panel(book))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_self_improving_args(args: Any) -> Tuple[str, Any]:
    """Parse the /ledger grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    self-improving book; ``candidate <candidate-id>``
    shows one candidate memory with its provenance
    whole; ``decisions`` shows the book's decisions
    in held order; ``standing`` shows the candidates
    standing as standing memories; ``panel`` shows
    the ledger panel derived from the whole book.
    Anything else is a usage error naming the grammar.
    Returns ``(action, value-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() in ("show", "list"):
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head == "decisions" and len(words) == 1:
        return (head, None)
    if head == "standing" and len(words) == 1:
        return (head, None)
    if head == "panel" and len(words) == 1:
        return (head, None)
    if head == "candidate" and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
