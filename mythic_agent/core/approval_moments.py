"""Approval by phone-sized moments (All-Features roadmap slice M-116).

Part V - Autonomy & Safety. The roadmap words:
``approvals are single, complete questions with full
context (Volmarr's law for his own Muse, applied to
his coder): what, where, what it does, one tap.``

What already shipped, and what this slice adds:

* The ToolPolicy ``ask`` road (``core/policy.py``)
  calls an approval callback with a tool name and
  its arguments and takes a bare boolean back. The
  TUI road (``agents/tools.py``
  ``prompt_approval_sync``, ``bind_tui`` in
  ``agents/llm.py``, ``action_request_approval`` in
  ``ui/main_app.py``) shows that call and collects
  the tap. Nothing shaped the QUESTION itself as
  data: one complete question, with its context,
  that a person can answer in one phone-sized
  moment.
* Remembered approvals (``remembered_approvals.py``,
  M-096) hold a standing answer with an exact scope,
  so a repeated ask need not be asked again. Nothing
  judged whether a fresh ask, when one is owed, is
  complete enough to answer at all.
* This slice is that missing question layer, as a
  pure layer in the exact sibling shape: an approval
  moment held as validated data (what is asked,
  where it acts, what it does, and its choices -
  each choice naming what choosing it does), a
  mechanical judge that derives whether a proposed
  moment is complete from given data only, a moment
  record shaped as session news, and a small
  in-memory registry model with deterministic ids.
  This module asks nothing, calls no callback,
  writes no file, changes no setting and imports no
  agent / UI code; the agent layer owns building a
  moment on the live approval road and holding the
  registry for a session.

The law of this slice, enforced here and pinned by
tests:

* **One moment, one question.** A moment carries
  exactly one question. A proposal naming several
  questions, or a ``what`` asking two questions at
  once, is judged incomplete - never a pile-up a
  person must untangle on a phone screen.
* **Full context, always.** A complete moment names
  what is asked, where it acts, and what it does.
  A moment missing any part is judged incomplete
  and the missing parts are named - a bare yes/no
  stripped of context is never complete.
* **Every choice says what it does.** Each choice
  carries its effect in plain words. A choice with
  no stated effect makes the moment incomplete:
  one tap must be an informed tap.
* **Phone-sized.** A complete moment fits one
  phone-sized moment: its whole text stays within
  ``MOMENT_CHAR_BUDGET`` characters. A longer ask
  is judged incomplete, however full its context.
* **Completeness is derived, never invented.** The
  judge reads only the proposal it is given. It
  invents no context, no choice and no effect.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Dict, List, Optional, Tuple

__all__ = [
    "APPROVAL_MOMENTS_SLICE",
    "CHOICE_KEYS",
    "MOMENT_CHAR_BUDGET",
    "PLAIN_EXPLANATION",
    "REQUIRED_PARTS",
    "STATES",
    "USAGE",
    "ApprovalChoice",
    "ApprovalMoment",
    "ApprovalMomentRegistry",
    "Assessment",
    "Choice",
    "Moment",
    "MomentAssessment",
    "Registry",
    "build_choice",
    "build_moment",
    "format_assessment",
    "format_choice",
    "format_moment",
    "format_moment_record",
    "format_moment_screen",
    "format_parts",
    "format_record",
    "judge_moment",
    "moment_record",
    "normalize_choice_key",
    "normalize_record_id",
    "parse_moment_args",
    "plain_words",
    "validate_choice",
    "validate_moment",
]

APPROVAL_MOMENTS_SLICE = "M-116"

#: The parts a complete moment must carry, in
#: roadmap order: what, where, what it does, and
#: the choices the one tap picks between.
REQUIRED_PARTS = ("what", "where", "what_it_does", "choices")

#: The completeness states, in honesty order.
STATES = ("complete", "incomplete")

#: The whole moment text - what, where, what it
#: does, and every choice with its effect - must
#: fit one phone-sized moment: at most this many
#: characters in total.
MOMENT_CHAR_BUDGET = 600

#: The choice keys a moment commonly offers. The
#: vocabulary is NOT closed: any plain key word is
#: a choice, so long as the choice states its
#: effect. These are the usual two, named so tests
#: and callers share the spelling.
CHOICE_KEYS = ("approve", "deny")

PLAIN_EXPLANATION = (
    "Approval by phone-sized moments: an approval "
    "ask is a single, complete question with full "
    "context - what is asked, where it acts, and "
    "what it does - and each choice says what "
    "choosing it does, so the whole ask can be "
    "answered with one tap in one phone-sized "
    "moment. A moment missing any part, asking "
    "more than one question, carrying a choice "
    "with no stated effect, or running longer "
    "than one moment holds is judged incomplete "
    "and the missing parts are named. This layer "
    "holds moments as data only; the agent layer "
    "builds a moment on the live approval road "
    "and holds the registry for a session."
)

USAGE = (
    "Usage: /moment, /moment show, "
    "/moment show <record>, /moment parts"
)

_ID_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789-_.")


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _soft_text(value: Any, what: str) -> str:
    """Text that may be empty: a missing part is data for the judge."""
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"{what} must be text, got {value!r}")
    return value.strip()


def _pick(mapping: Dict[str, Any], names: Tuple[str, ...],
          what: str) -> Any:
    found = [name for name in names if name in mapping]
    if not found:
        return None
    first = mapping[found[0]]
    for name in found[1:]:
        if mapping[name] != first:
            raise ValueError(
                f"a moment names two different {what}")
    return first


def normalize_choice_key(value: Any) -> str:
    """The canonical choice key a word names.

    A plain word of letters, digits, dashes and
    underscores, read case-insensitively and held
    lowercase. Any other shape refuses.
    """
    if isinstance(value, str):
        wanted = value.strip().lower()
        if wanted and all(ch in _ID_CHARS and ch != "."
                           for ch in wanted):
            return wanted
    raise ValueError(
        f"a choice key must be a non-empty word of letters, "
        f"digits, dashes and underscores, got {value!r}")


def normalize_record_id(value: Any) -> str:
    """The canonical registry record id a word names."""
    if isinstance(value, str):
        wanted = value.strip()
        if wanted and all(ch in _ID_CHARS for ch in wanted):
            return wanted
    raise ValueError(
        f"a record id must be a non-empty word of letters, "
        f"digits, dashes, underscores and dots, got {value!r}")


# ---------------------------------------------------------------------
# The choice: one tap a person can make, and what it does.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ApprovalChoice:
    """One choice on a moment: its key, its label, its effect.

    ``key`` is the plain word the tap names.
    ``label`` is the words shown for the choice, or
    empty when none was given - the judge names a
    missing label, this layer never invents one.
    ``effect`` is what choosing it does, in plain
    words, or empty when none was given: an empty
    effect is exactly the bare tap this slice
    forbids, so the judge names it missing.
    """

    key: str
    label: str = ""
    effect: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "key", normalize_choice_key(self.key))
        object.__setattr__(
            self, "label", _soft_text(self.label, "a choice label"))
        object.__setattr__(
            self, "effect", _soft_text(self.effect, "a choice effect"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "effect": self.effect,
        }


#: The shorter word for one approval choice.
Choice = ApprovalChoice

_CHOICE_KEYS = frozenset({"key", "label", "effect", "does", "name"})


def validate_choice(choice: Any) -> ApprovalChoice:
    """Validate one choice into an ApprovalChoice.

    Accepts an ApprovalChoice, a key word, or a
    mapping naming a ``key`` (or ``name``) and
    optionally a ``label`` and an ``effect`` (or
    ``does``). Naming two spellings of one field
    with different values refuses, and unknown
    keys refuse.
    """
    if isinstance(choice, ApprovalChoice):
        return choice
    if isinstance(choice, str):
        return ApprovalChoice(key=choice)
    if not isinstance(choice, dict):
        raise ValueError(f"a choice must be a mapping, got {choice!r}")
    unknown = set(choice) - _CHOICE_KEYS
    if unknown:
        raise ValueError(
            "unknown choice keys: %s" % ", ".join(sorted(unknown)))
    key = _pick(choice, ("key", "name"), "choice keys")
    if key is None:
        raise ValueError("a choice must name its key")
    kwargs: Dict[str, Any] = {"key": key}
    label = _pick(choice, ("label",), "choice labels")
    if label is not None:
        kwargs["label"] = label
    effect = _pick(choice, ("effect", "does"), "choice effects")
    if effect is not None:
        kwargs["effect"] = effect
    return ApprovalChoice(**kwargs)


def build_choice(key: Any, label: Any = "",
                 effect: Any = "") -> ApprovalChoice:
    """Build one validated choice from its key, label and effect."""
    return ApprovalChoice(key=key, label=label, effect=effect)


# ---------------------------------------------------------------------
# The moment: one complete question, held as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ApprovalMoment:
    """One approval moment: a single question with full context.

    ``what`` is the one question asked, ``where``
    is where the act lands, ``what_it_does`` is
    what the act does, and ``choices`` is the taps
    offered - each stating its effect. Any part
    may be empty in the data: emptiness is what
    the judge reads, so an incomplete proposal is
    representable and is judged, never refused
    into invisibility. What must hold even here:
    choices are validated choices with distinct
    keys, and ``question_count`` - when a caller
    states how many questions the proposal carries
    - is a whole number of at least one.
    """

    what: str = ""
    where: str = ""
    what_it_does: str = ""
    choices: Tuple[ApprovalChoice, ...] = ()
    question_count: int = 1
    record_id: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "what", _soft_text(self.what, "what is asked"))
        object.__setattr__(
            self, "where", _soft_text(self.where, "where it acts"))
        object.__setattr__(
            self, "what_it_does",
            _soft_text(self.what_it_does, "what it does"))
        cleaned = tuple(validate_choice(item) for item in self.choices)
        keys = [item.key for item in cleaned]
        if len(set(keys)) != len(keys):
            raise ValueError("a moment names each choice key once")
        object.__setattr__(self, "choices", cleaned)
        if (isinstance(self.question_count, bool)
                or not isinstance(self.question_count, int)
                or self.question_count < 1):
            raise ValueError(
                "a question count must be a whole number of at "
                f"least one, got {self.question_count!r}")
        if self.record_id is not None:
            object.__setattr__(
                self, "record_id", normalize_record_id(self.record_id))

    @property
    def choice_keys(self) -> Tuple[str, ...]:
        return tuple(item.key for item in self.choices)

    def text_size(self) -> int:
        """The whole moment text size, for the phone-sized rule."""
        total = len(self.what) + len(self.where) + len(self.what_it_does)
        for item in self.choices:
            total += len(item.label) + len(item.effect)
        return total

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "approval_moment",
            "slice": APPROVAL_MOMENTS_SLICE,
            "record_id": self.record_id,
            "what": self.what,
            "where": self.where,
            "what_it_does": self.what_it_does,
            "choices": [item.to_record() for item in self.choices],
            "choice_keys": list(self.choice_keys),
            "question_count": self.question_count,
        }


#: The shorter word for an approval moment.
Moment = ApprovalMoment

_MOMENT_KEYS = frozenset({
    "what", "question", "where", "location", "path",
    "what_it_does", "does", "effect", "choices",
    "questions", "question_count",
})


def validate_moment(moment: Any) -> ApprovalMoment:
    """Validate one moment proposal into an ApprovalMoment.

    Accepts an ApprovalMoment or a mapping naming
    ``what`` (or ``question``), ``where`` (or
    ``location`` / ``path``), ``what_it_does`` (or
    ``does`` / ``effect``) and ``choices``. A
    ``questions`` list names the questions the
    proposal carries: its length is the question
    count, and a single entry also answers ``what``
    when ``what`` itself is not named. Naming two
    spellings of one field with different values
    refuses, and unknown keys refuse.
    """
    if isinstance(moment, ApprovalMoment):
        return moment
    if not isinstance(moment, dict):
        raise ValueError(f"a moment must be a mapping, got {moment!r}")
    unknown = set(moment) - _MOMENT_KEYS
    if unknown:
        raise ValueError(
            "unknown moment keys: %s" % ", ".join(sorted(unknown)))
    questions = moment.get("questions")
    question_count = 1
    listed_what: Any = None
    if questions is not None:
        if not isinstance(questions, (list, tuple)):
            raise ValueError("questions must be a list of questions")
        question_count = len(questions)
        if question_count == 1:
            listed_what = questions[0]
    stated = moment.get("question_count")
    if stated is not None:
        if questions is not None and stated != question_count:
            raise ValueError(
                "a moment names two different question counts")
        question_count = stated
    what = _pick(moment, ("what", "question"), "questions asked")
    if what is None:
        what = listed_what
    where = _pick(moment, ("where", "location", "path"), "places")
    does = _pick(moment, ("what_it_does", "does", "effect"), "effects")
    raw_choices = moment.get("choices")
    if raw_choices is None:
        choices: Tuple[Any, ...] = ()
    elif isinstance(raw_choices, (list, tuple)):
        choices = tuple(raw_choices)
    else:
        raise ValueError("choices must be a list of choices")
    return ApprovalMoment(
        what=what if what is not None else "",
        where=where if where is not None else "",
        what_it_does=does if does is not None else "",
        choices=choices,
        question_count=question_count,
    )


def build_moment(what: Any = "", where: Any = "",
                 what_it_does: Any = "",
                 choices: Any = (),
                 question_count: Any = 1) -> ApprovalMoment:
    """Build one validated moment from its parts."""
    return ApprovalMoment(
        what=what, where=where, what_it_does=what_it_does,
        choices=tuple(choices), question_count=question_count)


# ---------------------------------------------------------------------
# The assessment: the judged completeness, and the judge.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class MomentAssessment:
    """The judged completeness of one moment, with its reasons.

    ``state`` is ``complete`` or ``incomplete``.
    ``missing`` names what a complete moment needs
    that this one lacks, in a fixed order: the
    required parts first (roadmap order), then
    ``choice_effects``, ``single_question`` and
    ``phone_sized``. ``reasons`` carries the
    judgement in plain words - why this state,
    never just the verdict. The state must agree
    with its own evidence on construction: complete
    names nothing missing, incomplete names at
    least one missing part - an assessment can
    never disagree with itself.
    """

    state: str
    moment: ApprovalMoment
    missing: Tuple[str, ...] = ()
    reasons: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.state not in STATES:
            raise ValueError(
                "a moment state must be one of %s, got %r"
                % ("/".join(STATES), self.state))
        if not isinstance(self.moment, ApprovalMoment):
            object.__setattr__(
                self, "moment", validate_moment(self.moment))
        allowed = REQUIRED_PARTS + (
            "choice_effects", "single_question", "phone_sized")
        missing = tuple(str(item).strip().lower()
                        for item in self.missing)
        for item in missing:
            if item not in allowed:
                raise ValueError(f"an unknown missing part: {item!r}")
        if len(set(missing)) != len(missing):
            raise ValueError("an assessment names each missing part once")
        ordered = tuple(name for name in allowed if name in missing)
        object.__setattr__(self, "missing", ordered)
        reasons = tuple(
            _clean_text(item, "a reason") for item in self.reasons)
        object.__setattr__(self, "reasons", reasons)
        if self.state == "complete" and ordered:
            raise ValueError("a complete assessment names nothing missing")
        if self.state == "incomplete" and not ordered:
            raise ValueError(
                "an incomplete assessment names at least one missing part")

    @property
    def record_id(self) -> Optional[str]:
        return self.moment.record_id

    def to_record(self) -> Dict[str, Any]:
        record = self.moment.to_record()
        record.update({
            "type": "approval_moment_assessment",
            "state": self.state,
            "missing": list(self.missing),
            "reasons": list(self.reasons),
        })
        return record


#: The shorter word for a moment assessment.
Assessment = MomentAssessment


def judge_moment(proposal: Any) -> MomentAssessment:
    """Judge whether a proposed moment is complete, mechanically.

    ``proposal`` is an ApprovalMoment or a mapping
    in ``validate_moment`` shape. The judge reads
    data only:

    * no ``what`` / ``where`` / ``what_it_does``
      text names that part missing;
    * fewer than two choices names ``choices``
      missing - one tap must be a real choice;
    * any choice with no label or no stated effect
      names ``choice_effects`` missing;
    * a stated question count above one, or a
      ``what`` asking more than one question,
      names ``single_question`` missing;
    * a whole text over ``MOMENT_CHAR_BUDGET``
      names ``phone_sized`` missing.

    Nothing missing makes the moment complete.
    The judge invents nothing: no context, choice
    or effect is supplied on the proposal's behalf.
    """
    moment = validate_moment(proposal)
    missing: List[str] = []
    reasons: List[str] = []
    if moment.what:
        reasons.append(f"What is asked: {moment.what}")
    else:
        missing.append("what")
        reasons.append(
            "What is asked is missing: the moment does not say what "
            "is being approved.")
    if moment.where:
        reasons.append(f"Where it acts: {moment.where}")
    else:
        missing.append("where")
        reasons.append(
            "Where it acts is missing: the moment does not say where "
            "the act lands.")
    if moment.what_it_does:
        reasons.append(f"What it does: {moment.what_it_does}")
    else:
        missing.append("what_it_does")
        reasons.append(
            "What it does is missing: the moment does not say what "
            "the act does.")
    if len(moment.choices) >= 2:
        reasons.append(
            "Choices offered: %s." % ", ".join(moment.choice_keys))
    else:
        missing.append("choices")
        reasons.append(
            "Choices are missing: one tap must pick between at "
            "least two stated choices.")
    bare = [item.key for item in moment.choices
            if not item.label or not item.effect]
    if bare:
        missing.append("choice_effects")
        reasons.append(
            "Choice effects are missing: %s - a choice must say "
            "what choosing it does, and show the words it is "
            "tapped by." % ", ".join(bare))
    elif moment.choices:
        reasons.append("Every choice says what choosing it does.")
    if moment.question_count > 1 or moment.what.count("?") > 1:
        missing.append("single_question")
        reasons.append(
            "One question only: this proposal asks more than one "
            "question, and a moment carries exactly one.")
    else:
        reasons.append("One question only: the moment asks one question.")
    size = moment.text_size()
    if size > MOMENT_CHAR_BUDGET:
        missing.append("phone_sized")
        reasons.append(
            "Phone-sized: the moment runs %d characters, over the "
            "%d one moment holds." % (size, MOMENT_CHAR_BUDGET))
    else:
        reasons.append(
            "Phone-sized: the moment runs %d of %d characters."
            % (size, MOMENT_CHAR_BUDGET))
    state = "incomplete" if missing else "complete"
    return MomentAssessment(
        state=state, moment=moment,
        missing=tuple(missing), reasons=tuple(reasons))


# ---------------------------------------------------------------------
# The news record: one judged moment, shaped as session news.
# ---------------------------------------------------------------------


def plain_words(assessment: Any) -> str:
    """One moment assessment, in plain words, said whole.

    A complete assessment restates the one question
    with its full context. An incomplete assessment
    names every missing part - it never calls the
    moment ready and never reduces it to a bare
    verdict.
    """
    if not isinstance(assessment, MomentAssessment):
        raise ValueError("plain words need a moment assessment")
    moment = assessment.moment
    if assessment.state == "complete":
        return (
            "Approval moment: complete - one question with full "
            f"context. What: {moment.what} Where: {moment.where} "
            f"What it does: {moment.what_it_does} Choices: "
            + ", ".join(
                f"{item.key} ({item.effect})" for item in moment.choices)
            + ".")
    return (
        "Approval moment: incomplete - missing %s. The moment is "
        "not ready to ask: one complete question with full context "
        "is owed." % ", ".join(assessment.missing))


def moment_record(assessment: Any) -> Dict[str, Any]:
    """The session-news record of one judged moment.

    Every judged moment yields a record - the agent
    layer publishes this record as a session event,
    so an approval ask is announced as the complete
    question it is, never lost as a bare prompt.
    The record names the state, the moment whole,
    what is missing, and the plain-words headline.
    """
    if not isinstance(assessment, MomentAssessment):
        raise ValueError("a record needs a moment assessment")
    record = assessment.to_record()
    return {
        "type": "approval_moment",
        "session_event": "approval_moment",
        "news": True,
        "slice": APPROVAL_MOMENTS_SLICE,
        "record_id": record["record_id"],
        "state": record["state"],
        "what": record["what"],
        "where": record["where"],
        "what_it_does": record["what_it_does"],
        "choices": record["choices"],
        "choice_keys": record["choice_keys"],
        "question_count": record["question_count"],
        "missing": record["missing"],
        "reasons": record["reasons"],
        "headline": plain_words(assessment),
    }


# ---------------------------------------------------------------------
# The registry model: a session of judged moments, ids deterministic.
# ---------------------------------------------------------------------


class ApprovalMomentRegistry:
    """An in-memory, storage-neutral approval-moment registry.

    Assessments are held in the order judged, under
    deterministic ``approval-moment-N`` ids: a
    caller-supplied id is used as given (a duplicate
    refuses), and an unsupplied id is the next
    ``approval-moment-N`` in sequence, skipping any
    number a supplied id already took - no
    randomness a test cannot pin. Storage beyond
    memory is the agent layer concern; this model
    is neutral.
    """

    def __init__(self) -> None:
        self._records: Dict[str, MomentAssessment] = {}
        self._next = 1

    def _fresh_id(self) -> str:
        while f"approval-moment-{self._next}" in self._records:
            self._next += 1
        record_id = f"approval-moment-{self._next}"
        self._next += 1
        return record_id

    def register(self, assessment: Any) -> MomentAssessment:
        """Hold one assessment, under its id or a fresh deterministic one."""
        if not isinstance(assessment, MomentAssessment):
            raise ValueError("the registry holds moment assessments")
        if assessment.record_id is None:
            assessment = replace(
                assessment,
                moment=replace(
                    assessment.moment, record_id=self._fresh_id()))
        elif assessment.record_id in self._records:
            raise ValueError(
                f"a moment record named {assessment.record_id!r} "
                "already exists")
        self._records[assessment.record_id] = assessment
        return assessment

    def judge_and_register(self, proposal: Any) -> MomentAssessment:
        """Judge a proposal and hold the assessment, in one move."""
        return self.register(judge_moment(proposal))

    def get(self, record_id: Any) -> MomentAssessment:
        """The assessment one id names; an unknown id raises KeyError."""
        wanted = normalize_record_id(record_id)
        if wanted not in self._records:
            raise KeyError(f"unknown moment record: {wanted!r}")
        return self._records[wanted]

    def list_records(self) -> Tuple[MomentAssessment, ...]:
        """Every held assessment, in the order judged, as a tuple."""
        return tuple(self._records.values())

    def __len__(self) -> int:
        return len(self._records)

    def record(self, record_id: Any) -> Dict[str, Any]:
        """One held assessment session-news record."""
        return moment_record(self.get(record_id))


#: The shorter word for the moment registry.
Registry = ApprovalMomentRegistry


# ---------------------------------------------------------------------
# The /moment surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------


def format_choice(choice: Any) -> str:
    """One choice, in plain words: what choosing it does, stated whole."""
    current = validate_choice(choice)
    label = current.label or current.key
    lines = [f"{current.key}: {label}."]
    if current.effect:
        lines.append(f"  does: {current.effect}")
    else:
        lines.append("  does: not stated - this choice is not ready")
    return "\n".join(lines)


def format_parts() -> str:
    """Every part a complete moment must carry, in roadmap order."""
    lines = ["Approval moment parts: %d required." % len(REQUIRED_PARTS)]
    lines.append("  what: the one question asked")
    lines.append("  where: where the act lands")
    lines.append("  what_it_does: what the act does")
    lines.append(
        "  choices: at least two choices, each saying what "
        "choosing it does")
    lines.append(
        "  one question only, and the whole text within %d "
        "characters - one phone-sized moment" % MOMENT_CHAR_BUDGET)
    return "\n".join(lines)


def format_moment(moment: Any) -> str:
    """One moment, in plain words: its full context, stated whole."""
    current = validate_moment(moment)
    name = current.record_id or "moment"
    lines = [f"{name}: {current.what or 'what is asked is not stated'}"]
    lines.append(f"  where: {current.where or 'not stated'}")
    lines.append(f"  what it does: {current.what_it_does or 'not stated'}")
    for item in current.choices:
        lines.append(f"  {format_choice(item)}")
    return "\n".join(lines)


def format_assessment(assessment: Any) -> str:
    """One moment assessment, in plain words: missing always stated."""
    if not isinstance(assessment, MomentAssessment):
        raise ValueError("formatting needs a moment assessment")
    name = assessment.record_id or "assessment"
    lines = [f"{name}: {plain_words(assessment)}"]
    for reason in assessment.reasons:
        lines.append(f"  {reason}")
    if assessment.missing:
        lines.append(f"  missing: {', '.join(assessment.missing)}")
    return "\n".join(lines)


def _assessments_from(source: Any) -> Tuple[MomentAssessment, ...]:
    if source is None:
        return ()
    if isinstance(source, ApprovalMomentRegistry):
        return source.list_records()
    if isinstance(source, MomentAssessment):
        return (source,)
    if isinstance(source, (list, tuple)):
        result = []
        for item in source:
            if not isinstance(item, MomentAssessment):
                raise ValueError("held records must be moment assessments")
            result.append(item)
        return tuple(result)
    raise ValueError("records must be a registry, assessment or list")


def format_moment_record(record: Any) -> str:
    """One moment news record as its plain headline."""
    if isinstance(record, dict) and record.get("type") == "approval_moment":
        return str(record["headline"])
    raise ValueError("format_moment_record needs a moment record")


#: The record formatter under its short name.
format_record = format_moment_record


def format_moment_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /moment."""
    records = _assessments_from(source)
    lines = ["Approval by phone-sized moments (M-116) - "
             + PLAIN_EXPLANATION, ""]
    if not records:
        lines.append(
            "Approval moments: no records held. No approval moment "
            "is held for this session.")
    else:
        lines.append(f"Approval moments: {len(records)} held.")
        for item in records:
            lines.append(f"  {format_assessment(item).splitlines()[0]}")
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


_GRAMMAR_WORDS = ("show", "parts")


def parse_moment_args(args: Any) -> Tuple[str, Optional[str]]:
    """Parse the /moment grammar both surfaces share.

    No words (or ``show``) shows the held records;
    ``show <record>`` and a bare record id show one
    record; ``parts`` shows the required parts
    alone. A grammar word in the wrong shape is a
    usage error naming the grammar, never a record
    id. Returns ``(action, target-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() == "show":
        return ("show", None)
    if text.lower() == "parts":
        return ("parts", None)
    words = text.split()
    head = words[0].lower()
    if head == "show" and len(words) == 2:
        if words[1].lower() in _GRAMMAR_WORDS:
            raise ValueError(USAGE)
        try:
            return ("show", normalize_record_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head in _GRAMMAR_WORDS or len(words) != 1:
        raise ValueError(USAGE)
    try:
        return ("show", normalize_record_id(words[0]))
    except ValueError:
        raise ValueError(USAGE) from None
