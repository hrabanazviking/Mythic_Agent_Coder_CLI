"""Review panels (All-Features roadmap slice M-132).

Part VI - Agents as files - continues here. The
roadmap's words: ``two Auditors with different
models review the same change; disagreements are
surfaced, not averaged away.``

What already shipped, and what this slice adds:

* The crew itself is already data
  (``core/crew_members.py``, M-121: the casting
  holds an ``auditor`` member, Solrun Hvitmynd,
  and a ``guardian`` member, Thor Guardian, both
  read-only scouts whose work is checking), the
  offices are formalised (M-122, M-123),
  heterogeneous crews already hold which member
  rides which provider on which model as data
  (M-129), and the Auditor's veto already judges
  given evidence mechanically (M-130). What
  nothing held is the panel itself: one change
  put to two reviewers riding different models,
  each returning their own verdict in their own
  words, and the panel's outcome derived from
  the two verdicts alone - so today a change is
  read by one reviewer on one model, and if a
  second reading would have disagreed, nothing
  anywhere records that it did.
* This slice is that panel, as a pure layer: the
  panel validated as data (a change - the change
  under review, named and summarised; and a
  review - one reviewer's verdict on that
  change, the provider and model they rode, their
  notes in plain words, and the concerns they
  name), the shipped data file
  (``mythic_agent/data/review_panels.yaml``)
  holding one example panel in exactly the shape
  a real panel's file takes, a loader for a panel
  file anywhere on disk, the panel outcome
  derived mechanically from the reviews alone,
  an outcome record shaped as session news, and
  a small in-memory registry model. This module
  runs no review, calls no model, executes no
  change and imports no agent / UI code; the
  agent layer owns holding the panel for a
  session and handing the outcome to the human.

Honesty rules, enforced here and pinned by tests:

* **The outcome is derived, never stored.** A
  panel's outcome is computed from the change
  and the reviews it is judged under, so it can
  never disagree with them; the same panel
  always yields the same outcome (deterministic
  order, deterministic wording).
* **Two reviewers, two models.** A panel holds
  at most two reviews, from two different
  reviewers, riding two different models - the
  roadmap's shape exactly. A third review, a
  second review from the same reviewer, and a
  second review on the same model all refuse:
  a panel is two independent readings, not a
  crowd and not an echo.
* **Disagreements are surfaced, not averaged
  away.** When the two verdicts differ, the
  outcome is a disagreement and it names both
  positions, reviewer by reviewer - there is no
  middle verdict, no score and no tie-break in
  this layer. When the two verdicts agree, the
  outcome is that verdict, held by both. When
  fewer than two reviews are held, the outcome
  is awaiting - the panel has not spoken yet,
  and nothing here pretends it has.
* **Reviewers are the shipped casting.** A
  review names its reviewer as an M-121 member
  id read exactly as the M-121 layer reads one
  (``core/crew_members.py``) - composed by
  import, never re-read here - and the model it
  rode as a plain model word beside its
  provider, the M-129 heterogeneous-crew shape.
* **The panel is data only; no review is run
  here.** No model is called, no change is
  executed, no crew is spawned and no reviewer
  is tasked in this slice: a panel here is a
  validated record of two reviews and the
  outcome they derive, not the reviewing
  itself, and the live readings arrive through
  later roads. The roadmap names the board
  (Part VIII) as where crew state will be
  visible; that board does not exist yet, so the
  outcome is visible through this slice's own
  /panel screen, and nothing here claims a
  board exists.
* **Malformed refuses.** An unknown verdict, a
  malformed reviewer, provider, model or
  concern, two reviews from one reviewer, two
  reviews on one model, a third review, and
  unknown keys in a change, a review, an
  outcome or a panel mapping all raise instead
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
    "OUTCOME_KINDS",
    "PANEL_RESOURCE",
    "PANEL_SCHEMA",
    "PANEL_SLICE",
    "PLAIN_EXPLANATION",
    "USAGE",
    "VERDICT_KINDS",
    "PanelChange",
    "PanelOutcome",
    "PanelReview",
    "ReviewPanel",
    "ReviewPanelRegistry",
    "build_change",
    "build_outcome",
    "build_review",
    "change_record",
    "format_outcome",
    "format_panel_screen",
    "format_review",
    "format_reviews",
    "format_verdict_kinds",
    "load_review_panel",
    "load_review_panel_file",
    "normalize_model",
    "normalize_outcome",
    "normalize_provider",
    "normalize_verdict",
    "outcome_of_panel",
    "outcome_plain_words",
    "outcome_record",
    "parse_panel_args",
    "plain_words",
    "review_record",
    "validate_change",
    "validate_outcome",
    "validate_panel",
    "validate_review",
]

PANEL_SLICE = "M-132"

#: The packaged data resource holding the example panel.
PANEL_RESOURCE = "review_panels.yaml"

#: The schema word a panel file must carry.
PANEL_SCHEMA = "mythic.review_panels/1"

#: The verdict kinds, in panel order: the change
#: stands, the change must grow first, the change
#: must not stand.
VERDICT_KINDS = ("approve", "request_changes", "reject")

#: The outcome kinds, in panel order: the two
#: verdicts agree, the two verdicts disagree and
#: the disagreement is surfaced, or the panel is
#: still awaiting its second review.
OUTCOME_KINDS = ("agreed", "disagreement", "awaiting")

_VERDICT_READINGS = {
    "approve": "approve",
    "approved": "approve",
    "accept": "approve",
    "accepted": "approve",
    "pass": "approve",
    "ok": "approve",
    "request_changes": "request_changes",
    "changes": "request_changes",
    "changes_requested": "request_changes",
    "block": "request_changes",
    "blocked": "request_changes",
    "reject": "reject",
    "rejected": "reject",
    "veto": "reject",
    "deny": "reject",
    "denied": "reject",
}

_OUTCOME_READINGS = {
    "agreed": "agreed",
    "agree": "agreed",
    "consensus": "agreed",
    "disagreement": "disagreement",
    "disagreed": "disagreement",
    "dispute": "disagreement",
    "awaiting": "awaiting",
    "waiting": "awaiting",
    "pending": "awaiting",
}

_CHANGE_KEYS = frozenset({
    "id", "change_id", "title", "name",
    "summary", "description", "text",
})

_REVIEW_KEYS = frozenset({
    "id", "review_id", "reviewer", "reviewer_id",
    "member", "member_id", "provider", "provider_id",
    "model", "model_id", "verdict", "decision",
    "notes", "note", "concerns", "concern",
})

_OUTCOME_KEYS = frozenset({
    "title", "change", "outcome", "kind",
    "verdict", "reviewers", "verdicts", "complete",
})

_PANEL_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "panel_note", "change", "reviews",
})

#: The shipped example panel's reviewers, in file
#: order. The shipped data file is held to exactly
#: this list by the loader's example check.
_EXAMPLE_REVIEWERS = ("auditor", "guardian")

#: The shipped example panel's models, in file
#: order: two different models, as the roadmap
#: names - the example is held to this list.
_EXAMPLE_MODELS = ("claude-sonnet-4-5", "llama3.1")

#: The shipped example panel's verdicts, in file
#: order: the two reviewers disagree, so the
#: example outcome is a disagreement, surfaced.
_EXAMPLE_VERDICTS = ("approve", "request_changes")

PLAIN_EXPLANATION = (
    "Review panels: one change put to two "
    "reviewers riding different models, each "
    "returning their own verdict in their own "
    "words. The outcome is derived from the two "
    "verdicts alone, and disagreements are "
    "surfaced, not averaged away - when the "
    "verdicts differ, the outcome names both "
    "positions and there is no middle verdict. "
    "There is no Part VIII board yet, so the "
    "outcome is visible on this slice's own "
    "screen, not on a board. This layer holds "
    "the panel as data only; it runs no review, "
    "calls no model and spawns no crew itself - "
    "the reviews arrive through later roads."
)

USAGE = (
    "Usage: /panel, /panel show, "
    "/panel show <reviewer>, /panel outcome, "
    "/panel verdicts, /panel kinds"
)


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_short_text(value: Any, what: str) -> str:
    text = _clean_text(value, what)
    if len(text) > 200 or "\x00" in text:
        raise ValueError(
            f"{what} must be plain text of at most "
            f"200 characters, got {len(text)} characters")
    return text


def _check_long_text(value: Any, what: str) -> str:
    text = _clean_text(value, what)
    if len(text) > 2000 or "\x00" in text:
        raise ValueError(
            f"{what} must be plain text of at most "
            f"2000 characters, got {len(text)} characters")
    return text


def normalize_verdict(value: Any) -> str:
    """The canonical verdict kind a word names.

    Verdict words read case-insensitively, with
    dashes read as underscores: ``approved`` and
    ``pass`` read as approve, ``changes`` and
    ``block`` as request_changes, ``veto`` and
    ``denied`` as reject. Anything else raises -
    a verdict is one of the panel's three, never
    a maybe.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace("-", "_")
        if wanted in _VERDICT_READINGS:
            return _VERDICT_READINGS[wanted]
    raise ValueError(
        "a verdict must be one of %s, got %r"
        % ("/".join(VERDICT_KINDS), value))


def normalize_outcome(value: Any) -> str:
    """The canonical outcome kind a word names.

    Outcome words read case-insensitively, with
    dashes read as underscores: ``consensus``
    reads as agreed, ``dispute`` as disagreement,
    ``pending`` as awaiting. Anything else
    raises.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace("-", "_")
        if wanted in _OUTCOME_READINGS:
            return _OUTCOME_READINGS[wanted]
    raise ValueError(
        "an outcome must be one of %s, got %r"
        % ("/".join(OUTCOME_KINDS), value))


def normalize_provider(value: Any) -> str:
    """The canonical provider word a word names.

    A provider is one word of letters, digits,
    dashes, underscores and dots, read in lower
    case - the M-129 heterogeneous-crew shape.
    Anything else raises.
    """
    return normalize_member_id(value).lower()


def normalize_model(value: Any) -> str:
    """The canonical model word a word names.

    A model is one word of letters, digits,
    dashes, underscores and dots, read with its
    case kept - ``claude-sonnet-4-5`` and
    ``llama3.1`` are model words. Anything else
    raises.
    """
    return normalize_member_id(value)


def _check_concerns(value: Any) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        items = [value]
    elif isinstance(value, (list, tuple)):
        items = list(value)
    else:
        raise ValueError(
            f"a review's concerns must be a list, got {value!r}")
    concerns = tuple(
        _check_short_text(item, "a concern") for item in items)
    if len(set(concerns)) != len(concerns):
        raise ValueError("a review names one concern twice")
    return concerns


def _pick_any(mapping: Dict[str, Any], spellings: Tuple[str, ...],
              what: str) -> Any:
    """One field from any of its spellings, or a refusal.

    Every spelling present must name the same
    value; two different values under two spellings
    of one field refuse.
    """
    values = [mapping[s] for s in spellings if s in mapping]
    if not values:
        return None
    if any(value != values[0] for value in values[1:]):
        raise ValueError(f"a record names two different {what}")
    return values[0]


# ---------------------------------------------------------------------
# The change: the one change the panel is asked to judge.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class PanelChange:
    """One change put to a review panel, as data.

    ``title`` names the change; ``summary`` says
    in plain words what the change does and what
    it honestly does not do. Constructing one
    validates its shape only: who reviewed it is
    the panel's concern, not the validator's.
    """

    change_id: Optional[str] = None
    title: str = ""
    summary: str = ""

    def __post_init__(self) -> None:
        if self.change_id is not None:
            object.__setattr__(
                self, "change_id",
                normalize_member_id(self.change_id))
        object.__setattr__(
            self, "title", _check_short_text(self.title, "a title"))
        object.__setattr__(
            self, "summary",
            _check_long_text(self.summary, "a summary"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "panel_change",
            "slice": PANEL_SLICE,
            "change_id": self.change_id,
            "title": self.title,
            "summary": self.summary,
        }


def validate_change(change: Any) -> PanelChange:
    """Validate one change into a PanelChange.

    Accepts a PanelChange or a mapping naming a
    ``title`` (or ``name``), a ``summary`` (or
    ``description`` / ``text``) and an optional
    ``change_id`` (or ``id``). Naming two
    spellings of one field with different values
    refuses, and unknown keys refuse.
    """
    if isinstance(change, PanelChange):
        return change
    if not isinstance(change, dict):
        raise ValueError(
            f"a change must be a mapping, got {change!r}")
    unknown = set(change) - _CHANGE_KEYS
    if unknown:
        raise ValueError(
            "unknown change keys: %s"
            % ", ".join(sorted(unknown)))
    title = _pick_any(change, ("title", "name"), "titles")
    if title is None:
        raise ValueError("a change is missing its title")
    summary = _pick_any(
        change, ("summary", "description", "text"), "summaries")
    if summary is None:
        raise ValueError("a change is missing its summary")
    kwargs: Dict[str, Any] = {"title": title, "summary": summary}
    change_id = _pick_any(change, ("change_id", "id"), "change ids")
    if change_id is not None:
        kwargs["change_id"] = change_id
    return PanelChange(**kwargs)


def build_change(change: Any = None, **kwargs: Any) -> PanelChange:
    """Build one validated change.

    From a PanelChange, from a mapping (the
    spellings :func:`validate_change` reads), or
    from field words given as keyword arguments.
    """
    if isinstance(change, PanelChange) and not kwargs:
        return change
    if isinstance(change, dict) or change is None:
        merged: Dict[str, Any] = {}
        if isinstance(change, dict):
            merged.update(change)
        merged.update(kwargs)
        return validate_change(merged)
    raise ValueError(f"a change must be a mapping, got {change!r}")


# ---------------------------------------------------------------------
# The review: one reviewer's verdict on the change, on their model.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class PanelReview:
    """One reviewer's review of the change, as data.

    ``reviewer`` is the M-121 member who reviews;
    ``provider`` and ``model`` name the road they
    rode - the M-129 shape; ``verdict`` is their
    verdict kind; ``notes`` is their reading in
    plain words; ``concerns`` names what they
    flag, each concern once, and may be empty.
    Constructing one validates its shape only:
    whether a second reviewer read the same
    change on a different model is the panel's
    concern, not the validator's.
    """

    review_id: Optional[str] = None
    reviewer: str = ""
    provider: str = ""
    model: str = ""
    verdict: str = ""
    notes: str = ""
    concerns: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.review_id is not None:
            object.__setattr__(
                self, "review_id",
                normalize_member_id(self.review_id))
        object.__setattr__(
            self, "reviewer", normalize_member_id(self.reviewer))
        object.__setattr__(
            self, "provider", normalize_provider(self.provider))
        object.__setattr__(
            self, "model", normalize_model(self.model))
        object.__setattr__(
            self, "verdict", normalize_verdict(self.verdict))
        object.__setattr__(
            self, "notes", _check_long_text(self.notes, "notes"))
        object.__setattr__(
            self, "concerns", _check_concerns(self.concerns))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "panel_review",
            "slice": PANEL_SLICE,
            "review_id": self.review_id,
            "reviewer": self.reviewer,
            "provider": self.provider,
            "model": self.model,
            "verdict": self.verdict,
            "notes": self.notes,
            "concerns": list(self.concerns),
        }


def validate_review(review: Any) -> PanelReview:
    """Validate one review into a PanelReview.

    Accepts a PanelReview or a mapping naming a
    ``reviewer`` (or ``reviewer_id`` / ``member``
    / ``member_id``), a ``provider`` (or
    ``provider_id``), a ``model`` (or
    ``model_id``), a ``verdict`` (or ``decision``),
    ``notes`` (or ``note``), optional ``concerns``
    (or a single ``concern``) and an optional
    ``review_id`` (or ``id``). Naming two
    spellings of one field with different values
    refuses, and unknown keys refuse.
    """
    if isinstance(review, PanelReview):
        return review
    if not isinstance(review, dict):
        raise ValueError(
            f"a review must be a mapping, got {review!r}")
    unknown = set(review) - _REVIEW_KEYS
    if unknown:
        raise ValueError(
            "unknown review keys: %s"
            % ", ".join(sorted(unknown)))
    reviewer = _pick_any(
        review, ("reviewer", "reviewer_id", "member", "member_id"),
        "reviewers")
    if reviewer is None:
        raise ValueError("a review is missing its reviewer")
    provider = _pick_any(
        review, ("provider", "provider_id"), "providers")
    if provider is None:
        raise ValueError("a review is missing its provider")
    model = _pick_any(review, ("model", "model_id"), "models")
    if model is None:
        raise ValueError("a review is missing its model")
    verdict = _pick_any(review, ("verdict", "decision"), "verdicts")
    if verdict is None:
        raise ValueError("a review is missing its verdict")
    notes = _pick_any(review, ("notes", "note"), "notes")
    if notes is None:
        raise ValueError("a review is missing its notes")
    kwargs: Dict[str, Any] = {
        "reviewer": reviewer, "provider": provider,
        "model": model, "verdict": verdict, "notes": notes}
    concerns = _pick_any(review, ("concerns", "concern"), "concerns")
    if concerns is not None:
        kwargs["concerns"] = concerns
    review_id = _pick_any(review, ("review_id", "id"), "review ids")
    if review_id is not None:
        kwargs["review_id"] = review_id
    return PanelReview(**kwargs)


def build_review(review: Any = None, **kwargs: Any) -> PanelReview:
    """Build one validated review.

    From a PanelReview, from a mapping (the
    spellings :func:`validate_review` reads), or
    from field words given as keyword arguments.
    """
    if isinstance(review, PanelReview) and not kwargs:
        return review
    if isinstance(review, dict) or review is None:
        merged: Dict[str, Any] = {}
        if isinstance(review, dict):
            merged.update(review)
        merged.update(kwargs)
        return validate_review(merged)
    raise ValueError(f"a review must be a mapping, got {review!r}")


# ---------------------------------------------------------------------
# The panel: one change and its (at most two) reviews, whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ReviewPanel:
    """One whole review panel, as data.

    ``change`` is the PanelChange under review;
    ``reviews`` are the readings held, in file
    order, at most two; ``panel_note`` is the
    file's own words about itself. A panel is
    validated whole by :func:`validate_panel`:
    no reviewer reads twice, no model is ridden
    twice, and a third review refuses.
    """

    change: Optional[PanelChange] = None
    reviews: Tuple[PanelReview, ...] = ()
    panel_note: str = ""

    def review_for(self, reviewer: Any) -> PanelReview:
        """The review one reviewer returned; unreported raises."""
        wanted = normalize_member_id(reviewer)
        for review in self.reviews:
            if review.reviewer == wanted:
                return review
        raise KeyError(f"no review from reviewer: {wanted!r}")

    def reviewers(self) -> Tuple[str, ...]:
        """Every reviewer who has reported, in file order."""
        return tuple(review.reviewer for review in self.reviews)

    def is_complete(self) -> bool:
        """True exactly when both of the panel's reviews are held."""
        return len(self.reviews) == 2

    def disagrees(self) -> bool:
        """True exactly when two held verdicts differ."""
        return (
            len(self.reviews) == 2
            and self.reviews[0].verdict != self.reviews[1].verdict)


def validate_panel(data: Any, *, require_example: bool = False) -> ReviewPanel:
    """Validate one panel mapping into a ReviewPanel.

    The mapping names a ``schema`` (the panel
    schema word), a ``change`` and a ``reviews``
    list. Every piece is validated, then the
    whole is judged: at most two reviews, no
    reviewer twice, no model ridden twice. With
    ``require_example`` the shipped example is
    held to its pinned shape: the two pinned
    reviewers on the two pinned models, holding
    the two pinned verdicts, so the example
    outcome is a disagreement, surfaced.
    Problems raise :class:`ValidationError` or
    ``ValueError`` naming the problem.
    """
    if isinstance(data, ReviewPanel):
        return data
    if not isinstance(data, dict):
        raise ValidationError(
            f"a review panel must be a mapping, got {data!r}")
    unknown = set(data) - _PANEL_KEYS
    if unknown:
        raise ValidationError(
            "unknown panel keys: %s" % ", ".join(sorted(unknown)))
    if data.get("schema") != PANEL_SCHEMA:
        raise ValidationError(
            f"a review panel must carry schema {PANEL_SCHEMA!r}, "
            f"got {data.get('schema')!r}")
    if "change" not in data:
        raise ValidationError("a review panel is missing its change")
    change = validate_change(data["change"])
    raw_reviews = data.get("reviews") or []
    if not isinstance(raw_reviews, (list, tuple)):
        raise ValidationError("a panel's reviews must be a list")
    reviews = tuple(validate_review(entry) for entry in raw_reviews)
    if len(reviews) > 2:
        raise ValidationError(
            "a review panel holds two reviews, no more: "
            "a third reading is a second panel, not a vote")
    reviewers = [review.reviewer for review in reviews]
    if len(set(reviewers)) != len(reviewers):
        raise ValidationError(
            "a reviewer reviews twice in one panel")
    models = [review.model for review in reviews]
    if len(set(models)) != len(models):
        raise ValidationError(
            "two reviews ride the same model in one panel: "
            "the roadmap names two different models")
    note = data.get("panel_note") or ""
    if not isinstance(note, str):
        raise ValidationError("a panel's note must be text")
    panel = ReviewPanel(
        change=change, reviews=reviews, panel_note=note.strip())
    if require_example:
        if tuple(r.reviewer for r in reviews) != _EXAMPLE_REVIEWERS:
            raise ValidationError(
                "the shipped example panel's reviewers are not "
                "the pinned two, in order")
        if tuple(r.model for r in reviews) != _EXAMPLE_MODELS:
            raise ValidationError(
                "the shipped example panel's models are not "
                "the pinned two, in order")
        if tuple(r.verdict for r in reviews) != _EXAMPLE_VERDICTS:
            raise ValidationError(
                "the shipped example panel's verdicts are not "
                "the pinned two, in order")
        if not panel.disagrees():
            raise ValidationError(
                "the shipped example panel must disagree, "
                "so the surfacing is what ships")
    return panel


def _panel_from(data: Any, *, require_example: bool) -> ReviewPanel:
    try:
        return validate_panel(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_review_panel(
        data: Optional[Dict[str, Any]] = None) -> ReviewPanel:
    """Load and validate the shipped example panel (or *data*).

    The shipped file is held to the example check:
    exactly the two pinned reviewers on the two
    pinned models, holding the two pinned
    verdicts - a disagreement, surfaced. Raises
    :class:`ValidationError` naming the problem
    when the record is not a well-formed panel.
    """
    raw = data if data is not None else load_resource(PANEL_RESOURCE)
    return _panel_from(raw, require_example=True)


def load_review_panel_file(path: Any) -> ReviewPanel:
    """Load and validate a review panel from a file at *path*.

    This is the road a real panel arrives by: any
    file in the panel shape, anywhere on disk,
    validated whole - a malformed file raises
    :class:`ValidationError` naming the problem,
    and a missing file raises ``FileNotFoundError``.
    The example check is not held: a real panel
    may still be awaiting its second review.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _panel_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The outcome: what the panel's verdicts add up to, derived, never
# stored. Two agreeing verdicts yield that verdict; two differing
# verdicts yield a disagreement naming both positions; fewer than
# two reviews yield awaiting. There is no middle verdict.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class PanelOutcome:
    """One panel's outcome, derived from its reviews.

    ``title`` is the change's title; ``outcome``
    is the outcome kind; ``verdict`` is the agreed
    verdict when the outcome is agreed and empty
    otherwise - a disagreement holds no single
    verdict, by design; ``reviewers`` and
    ``verdicts`` name each held position in panel
    order; ``complete`` says whether both reviews
    are held. The shape is self-judging: an
    agreed outcome must hold two identical
    verdicts and name their verdict, a
    disagreement must hold two differing verdicts
    and name none, and an awaiting outcome must
    hold fewer than two reviews.
    """

    title: str = ""
    outcome: str = ""
    verdict: str = ""
    reviewers: Tuple[str, ...] = ()
    verdicts: Tuple[str, ...] = ()
    complete: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_short_text(self.title, "a title"))
        object.__setattr__(
            self, "outcome", normalize_outcome(self.outcome))
        verdict = self.verdict
        if verdict:
            verdict = normalize_verdict(verdict)
        object.__setattr__(self, "verdict", verdict)
        reviewers = tuple(
            normalize_member_id(r) for r in self.reviewers)
        if len(set(reviewers)) != len(reviewers):
            raise ValueError("an outcome names one reviewer twice")
        if len(reviewers) > 2:
            raise ValueError("an outcome holds two positions, no more")
        object.__setattr__(self, "reviewers", reviewers)
        verdicts = tuple(normalize_verdict(v) for v in self.verdicts)
        if len(verdicts) != len(reviewers):
            raise ValueError(
                "an outcome holds one verdict per reviewer")
        object.__setattr__(self, "verdicts", verdicts)
        if not isinstance(self.complete, bool):
            raise ValueError(
                f"an outcome's complete must be true or false, "
                f"got {self.complete!r}")
        if self.complete != (len(reviewers) == 2):
            raise ValueError(
                "an outcome is complete exactly when both "
                "reviews are held")
        if self.outcome == "agreed":
            if not self.complete or len(set(verdicts)) != 1:
                raise ValueError(
                    "an agreed outcome holds two identical verdicts")
            if self.verdict != verdicts[0]:
                raise ValueError(
                    "an agreed outcome names the verdict both hold")
        elif self.outcome == "disagreement":
            if not self.complete or len(set(verdicts)) != 2:
                raise ValueError(
                    "a disagreement holds two differing verdicts")
            if self.verdict:
                raise ValueError(
                    "a disagreement names no single verdict - "
                    "it is surfaced, not averaged")
        else:
            if self.complete:
                raise ValueError(
                    "an awaiting outcome holds fewer than two reviews")
            if self.verdict:
                raise ValueError(
                    "an awaiting outcome names no verdict yet")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "panel_outcome",
            "slice": PANEL_SLICE,
            "title": self.title,
            "outcome": self.outcome,
            "verdict": self.verdict,
            "reviewers": list(self.reviewers),
            "verdicts": list(self.verdicts),
            "complete": bool(self.complete),
        }


def outcome_of_panel(source: Any) -> PanelOutcome:
    """The outcome one panel yields, derived from its reviews alone.

    Accepts a ReviewPanel or a ReviewPanelRegistry.
    No reviews or one review yields awaiting; two
    identical verdicts yield agreed, naming the
    verdict both hold; two differing verdicts
    yield a disagreement naming both positions -
    never a blend, a score or a tie-break.
    """
    if isinstance(source, ReviewPanelRegistry):
        panel = source.panel()
    elif isinstance(source, ReviewPanel):
        panel = source
    else:
        raise ValueError(f"a review panel is needed, got {source!r}")
    assert panel.change is not None
    reviewers = tuple(r.reviewer for r in panel.reviews)
    verdicts = tuple(r.verdict for r in panel.reviews)
    if len(panel.reviews) < 2:
        return PanelOutcome(
            title=panel.change.title, outcome="awaiting",
            verdict="", reviewers=reviewers, verdicts=verdicts,
            complete=False)
    if verdicts[0] == verdicts[1]:
        return PanelOutcome(
            title=panel.change.title, outcome="agreed",
            verdict=verdicts[0], reviewers=reviewers,
            verdicts=verdicts, complete=True)
    return PanelOutcome(
        title=panel.change.title, outcome="disagreement",
        verdict="", reviewers=reviewers, verdicts=verdicts,
        complete=True)


def validate_outcome(outcome: Any, panel: Any = None) -> PanelOutcome:
    """Validate one outcome into a PanelOutcome.

    Accepts a PanelOutcome or a mapping naming a
    ``title`` (or ``change``), an ``outcome`` (or
    ``kind``), a ``verdict``, ``reviewers``,
    ``verdicts`` and a ``complete`` word. When
    *panel* is given, the outcome is also judged
    against the outcome that panel derives: any
    disagreement refuses, because an outcome is
    derived, never stored.
    """
    if isinstance(outcome, PanelOutcome):
        current = outcome
    elif isinstance(outcome, dict):
        unknown = set(outcome) - _OUTCOME_KEYS
        if unknown:
            raise ValueError(
                "unknown outcome keys: %s" % ", ".join(sorted(unknown)))
        title = _pick_any(outcome, ("title", "change"), "titles")
        kind = _pick_any(outcome, ("outcome", "kind"), "outcomes")
        if title is None or kind is None:
            raise ValueError(
                "an outcome is missing its title or its kind")
        current = PanelOutcome(
            title=title, outcome=kind,
            verdict=outcome.get("verdict") or "",
            reviewers=tuple(outcome.get("reviewers") or ()),
            verdicts=tuple(outcome.get("verdicts") or ()),
            complete=bool(outcome.get("complete", False)))
    else:
        raise ValueError(f"an outcome must be a mapping, got {outcome!r}")
    if panel is not None:
        derived = outcome_of_panel(panel)
        if current != derived:
            raise ValueError(
                "a stored outcome disagrees with the outcome its "
                "panel derives - an outcome is derived, never stored")
    return current


def build_outcome(outcome: Any = None, **kwargs: Any) -> PanelOutcome:
    """Build one validated outcome.

    From a PanelOutcome, from a mapping (the
    spellings :func:`validate_outcome` reads), or
    from field words given as keyword arguments.
    """
    if isinstance(outcome, PanelOutcome) and not kwargs:
        return outcome
    if isinstance(outcome, dict) or outcome is None:
        merged: Dict[str, Any] = {}
        if isinstance(outcome, dict):
            merged.update(outcome)
        merged.update(kwargs)
        return validate_outcome(merged)
    raise ValueError(f"an outcome must be a mapping, got {outcome!r}")


# ---------------------------------------------------------------------
# The registry model: a panel held piece by piece, in order, with
# deterministic ids. A registry refuses a supplied id already held,
# a reviewer reporting twice, a model ridden twice and a third
# review: repetition here is a second reading by the same eyes or
# the same model, not two pieces of a panel, so it is refused,
# never hidden.
# ---------------------------------------------------------------------


class ReviewPanelRegistry:
    """One session's review panel, held piece by piece."""

    def __init__(self, change: Any = None) -> None:
        self._change: Optional[PanelChange] = (
            build_change(change) if change is not None else None)
        self._reviews: Dict[str, PanelReview] = {}
        self._next_review = 1

    def hold_change(self, change: Any) -> PanelChange:
        """Hold the panel's one change; a second refuses."""
        validated = build_change(change)
        if self._change is not None:
            raise ValueError("a panel holds one change only")
        if validated.change_id is None:
            validated = replace(validated, change_id="change-1")
        self._change = validated
        return validated

    def change(self) -> PanelChange:
        """The held change; none held raises."""
        if self._change is None:
            raise KeyError("no change is held in this registry")
        return self._change

    def _fresh_review_id(self) -> str:
        while f"review-{self._next_review}" in self._reviews:
            self._next_review += 1
        fresh = f"review-{self._next_review}"
        self._next_review += 1
        return fresh

    def register_review(self, review: Any) -> PanelReview:
        """Register one review and hold it.

        The panel holds two reviews, no more: a
        third refuses, as does a second review
        from a reviewer already held and a second
        review riding a model already ridden.
        """
        validated = build_review(review)
        if len(self._reviews) >= 2:
            raise ValueError(
                "a review panel holds two reviews, no more: "
                "a third reading is a second panel, not a vote")
        for held in self._reviews.values():
            if held.reviewer == validated.reviewer:
                raise ValueError(
                    f"a reviewer reviews twice: {validated.reviewer} "
                    f"holds two reviews")
            if held.model == validated.model:
                raise ValueError(
                    f"two reviews ride the same model: "
                    f"{validated.model} is already ridden in "
                    f"this panel")
        if validated.review_id is not None \
                and validated.review_id in self._reviews:
            raise ValueError(
                f"a review named {validated.review_id!r} "
                f"already exists")
        if validated.review_id is None:
            validated = replace(
                validated, review_id=self._fresh_review_id())
        self._reviews[validated.review_id] = validated
        return validated

    def register_panel(self, panel: Any) -> ReviewPanel:
        """Register every piece of one panel, in order."""
        if not isinstance(panel, ReviewPanel):
            raise ValueError(f"a review panel is needed, got {panel!r}")
        self.hold_change(panel.change)
        for review in panel.reviews:
            self.register_review(review)
        return self.panel()

    def get_review(self, review_id: Any) -> PanelReview:
        """The review one id names; an unknown id raises."""
        wanted = normalize_member_id(review_id)
        if wanted not in self._reviews:
            raise KeyError(f"unknown review: {wanted!r}")
        return self._reviews[wanted]

    def list_reviews(self) -> Tuple[PanelReview, ...]:
        """Every held review, in registration order."""
        return tuple(self._reviews.values())

    def reviews_for(self, member: Any) -> Tuple[PanelReview, ...]:
        """Every held review of one reviewer (at most one)."""
        wanted = normalize_member_id(member)
        return tuple(
            held for held in self._reviews.values()
            if held.reviewer == wanted)

    def panel(self) -> ReviewPanel:
        """The held pieces as one validated panel."""
        return ReviewPanel(
            change=self.change(), reviews=self.list_reviews())

    def outcome(self) -> PanelOutcome:
        """The outcome the held panel yields."""
        return outcome_of_panel(self.panel())


# ---------------------------------------------------------------------
# Panel news, shaped as session records.
# ---------------------------------------------------------------------


def change_record(change: Any) -> Dict[str, Any]:
    """The session-news record of one change."""
    current = change if isinstance(
        change, PanelChange) else build_change(change)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"A change is put to a review panel: {current.title}")
    return record


def review_record(review: Any) -> Dict[str, Any]:
    """The session-news record of one review."""
    current = review if isinstance(
        review, PanelReview) else build_review(review)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.reviewer} reviews the change on "
        f"{current.provider}/{current.model}: {current.verdict}.")
    return record


def outcome_record(outcome: Any) -> Dict[str, Any]:
    """The session-news record of one outcome."""
    current = outcome if isinstance(
        outcome, PanelOutcome) else build_outcome(outcome)
    record = current.to_record()
    record["news"] = True
    if current.outcome == "agreed":
        record["headline"] = (
            f"The panel agrees: {current.verdict}.")
    elif current.outcome == "disagreement":
        record["headline"] = (
            "The panel disagrees: "
            + "; ".join(
                f"{r} holds {v}" for r, v in zip(
                    current.reviewers, current.verdicts))
            + " - surfaced, not averaged.")
    else:
        record["headline"] = (
            "The panel is still awaiting its second review.")
    return record


def plain_words(change: Any) -> str:
    """One change, in one plain sentence."""
    current = change if isinstance(
        change, PanelChange) else build_change(change)
    return f"Change under review: {current.title} - {current.summary}"


def outcome_plain_words(outcome: Any) -> str:
    """One outcome, in one plain sentence."""
    current = outcome if isinstance(
        outcome, PanelOutcome) else build_outcome(outcome)
    if current.outcome == "agreed":
        return (
            f"Agreed ({current.verdict}): both reviewers "
            f"hold {current.verdict} on {current.title}.")
    if current.outcome == "disagreement":
        return (
            "Disagreement on " + current.title + ": "
            + "; ".join(
                f"{r} holds {v}" for r, v in zip(
                    current.reviewers, current.verdicts))
            + " - surfaced, not averaged.")
    if current.reviewers:
        return (
            f"Awaiting a second review on {current.title}: "
            f"only {current.reviewers[0]} has reported "
            f"({current.verdicts[0]}).")
    return f"No reviews have come back yet on {current.title}."


# ---------------------------------------------------------------------
# Screens: the formatters and the shared /panel grammar.
# ---------------------------------------------------------------------


def _source_panel(source: Any) -> ReviewPanel:
    if source is None:
        return load_review_panel()
    if isinstance(source, ReviewPanelRegistry):
        return source.panel()
    if isinstance(source, ReviewPanel):
        return source
    raise ValueError(f"a review panel is needed, got {source!r}")


def format_review(review: Any) -> str:
    """One review as a screen line, with its concerns."""
    current = review if isinstance(
        review, PanelReview) else build_review(review)
    line = (
        f"{current.reviewer} ({current.provider}/{current.model}): "
        f"{current.verdict} - {current.notes}")
    if current.concerns:
        line += f" [concerns: {'; '.join(current.concerns)}]"
    return line


def format_reviews(source: Any = None) -> str:
    """Every review of one panel, in panel order."""
    panel = _source_panel(source)
    lines = [format_review(review) for review in panel.reviews]
    if len(panel.reviews) == 0:
        lines.append("No reviews are held yet.")
    elif len(panel.reviews) == 1:
        lines.append("One review still to come.")
    return "\n".join(lines)


def format_outcome(source: Any = None) -> str:
    """One panel's outcome, with both positions named."""
    panel = _source_panel(source)
    outcome = outcome_of_panel(panel)
    lines = [outcome_plain_words(outcome)]
    lines.extend(format_review(review) for review in panel.reviews)
    return "\n".join(lines)


def format_verdict_kinds() -> str:
    """The three verdict kinds, in panel order."""
    return "Verdict kinds: " + ", ".join(VERDICT_KINDS)


def format_panel_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /panel.

    With nothing named, the shipped example
    panel's outcome is shown - the example this
    slice ships - so the screen is never empty.
    There is no Part VIII board yet; this screen
    is where the outcome is visible.
    """
    panel = _source_panel(source)
    lines = ["Review panels (M-132) - " + PLAIN_EXPLANATION, ""]
    lines.append(plain_words(panel.change))
    lines.append("")
    lines.append(format_reviews(panel))
    lines.append("")
    lines.append(format_outcome(panel))
    lines.append("")
    lines.append(format_verdict_kinds())
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_panel_args(args: Any) -> Tuple[str, Optional[str]]:
    """Parse the /panel grammar both surfaces share.

    No words (or ``show`` / ``list`` / ``reviews``)
    shows the panel; ``show <reviewer>`` and a
    bare reviewer id show one reviewer's review;
    ``outcome`` shows the derived outcome;
    ``verdicts`` shows the positions the panel
    holds; ``kinds`` asks for the verdict kinds.
    Anything else is a usage error naming the
    grammar. Returns ``(action, value-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None \
        else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() in ("show", "list", "reviews"):
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head == "show" and len(words) == 2:
        try:
            return ("show", normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "outcome" and len(words) == 1:
        return ("outcome", None)
    if head == "verdicts" and len(words) == 1:
        return ("verdicts", None)
    if head == "kinds" and len(words) == 1:
        return ("kinds", None)
    if head in ("show", "outcome", "verdicts", "kinds",
                "list", "reviews"):
        raise ValueError(USAGE)
    if len(words) == 1:
        try:
            return ("show", normalize_member_id(words[0]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
