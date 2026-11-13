"""The tutorial grown (All-Features roadmap slice M-185).

Part VIII - The Beautiful Face - builds here. The
roadmap's words: *interactive lessons per feature
family, runnable inside a scratch repo; `mythic
tutorial` becomes the manual you play.*

What already ships, and what this slice adds:

* The shipped tree already carries a first-run
  tutorial road (``mythic_agent/onboarding.py``'s
  ``mythic tutorial``, with its own steps and its
  own road - it stands untouched behind a seam).
  What nothing held is the *grown tutorial itself*,
  as checkable data: one interactive lesson per
  feature family, held whole with its provenance;
  the scratch repo a lesson runs inside, held as
  data; and the play - the lesson steps held in
  order - under the one rule the roadmap names.
  This slice is that book, in its own module.
* A lesson is held whole: its title, its feature
  family (a closed vocabulary - providers, code
  intelligence, the editor's hand, sandboxing,
  parallel crews, memory and context, plain
  language, bridges), its readiness, ready or
  blocked, and its detail. Readiness is never
  faked: a lesson whose exercise does not stand
  ready stands blocked, named in its gaps.
* Lessons run inside a scratch repo, never
  against the real workspace, and the rule stands
  as data (:data:`SCRATCH_REPO_RULE`): a record
  claiming a run outside a scratch repo, or
  against the real workspace, refuses BY NAME.
  The play's steps stand held in order - open,
  read, try, check, clean - and a play that
  cleans its scratch repo away before its
  exercise stands tried refuses by name too.
* The shipped data file (``mythic_agent/data/
  tutorial_grown.yaml``) holds one example book
  in exactly the shape a real tutorial file
  takes, a loader reads a tutorial file anywhere
  on disk, lessons and views are shaped as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding a tutorial book for a session and
  playing it. This layer reaches no live road:
  it runs no lesson, opens no repo and writes
  nothing to any real workspace - it holds the
  grown tutorial as data and tells it.

Honesty rules, enforced here and pinned by tests:

* **Readiness never faked.** A lesson's readiness
  is its own held word; a blocked lesson stands
  blocked and named in its gaps, and no exercise
  is invented for it.
* **Scratch repo only.** Every lesson runs
  inside a scratch repo; a claim to run outside
  one, or against the real workspace, refuses
  by name.
* **Holding runs nothing.** Holding, viewing or
  reading a lesson runs nothing and writes
  nothing to any real workspace.
* **The play stands in order.** The scratch repo
  is opened before any exercise is tried, and
  is not cleaned away before the exercise stands
  tried and checked.
"""

from __future__ import annotations

__all__ = [
    "READINESS_WORDS",
    "SCRATCH_STATES",
    "TUTORIAL_GROWN_RESOURCE",
    "TUTORIAL_GROWN_SCHEMA",
    "TUTORIAL_GROWN_SLICE",
    "PLAIN_EXPLANATION",
    "FEATURE_FAMILIES",
    "SCRATCH_REPO_RULE",
    "THE_TUTORIAL_GROWN_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "PLAY_ACTION",
    "PLAY_PHASES",
    "Any",
    "Dict",
    "List",
    "Optional",
    "LessonRecord",
    "ScratchRecord",
    "TutorialBook",
    "TutorialPanel",
    "TutorialPanelRow",
    "TutorialRegistry",
    "TutorialVerdict",
    "TutorialView",
    "TutorialPlay",
    "ReadinessCount",
    "PlayStep",
    "book_record",
    "build_book",
    "build_lesson",
    "build_scratch",
    "build_panel",
    "build_row",
    "build_step",
    "build_verdict",
    "build_view",
    "derive_panel",
    "derive_verdict",
    "derive_play",
    "lesson_gaps",
    "lesson_passes",
    "lesson_plain_words",
    "lessons_for_readiness",
    "format_book",
    "format_lesson",
    "format_scratch",
    "format_tutorial_grown_screen",
    "format_panel",
    "format_verdict",
    "format_view",
    "format_play",
    "inspect_tutorial_source",
    "load_tutorial_grown",
    "load_tutorial_grown_file",
    "normalize_state",
    "normalize_readiness",
    "normalize_phase",
    "normalize_family",
    "normalize_view_filter",
    "scratch_record",
    "panel_plain_words",
    "panel_record",
    "parse_tutorial_args",
    "passing_lessons",
    "plain_lines",
    "plain_words",
    "segment_of",
    "shown_lessons",
    "step_record",
    "total_lessons",
    "validate_book",
    "validate_lesson",
    "validate_scratch",
    "validate_panel",
    "validate_row",
    "validate_step",
    "validate_verdict",
    "validate_view",
    "verdict_plain_words",
    "verdict_record",
    "view_plain_words",
    "view_record",
    "play_plain_words",
    "play_record",
    "play_steps",
]

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

TUTORIAL_GROWN_SCHEMA = "mythic.tutorial_grown/1"
TUTORIAL_GROWN_SLICE = "M-185"
THE_TUTORIAL_GROWN_SLICE = TUTORIAL_GROWN_SLICE
TUTORIAL_GROWN_RESOURCE = "tutorial_grown.yaml"
PLAY_ACTION = "play"
READINESS_WORDS = ("ready", "blocked")
FEATURE_FAMILIES = (
    "providers", "code intelligence", "the editor's hand",
    "sandboxing", "parallel crews", "memory and context",
    "plain language", "bridges")
VIEW_FILTERS = ("all", "ready", "blocked")
PLAY_PHASES = ("open", "read", "try", "check", "clean")
SCRATCH_STATES = ("open", "closed", "pending")
VERDICT_WORDS = ("open", "strained", "shut")
SCRATCH_REPO_RULE = (
    "lessons run inside a scratch repo, never against "
    "the real workspace: the scratch repo is opened "
    "before any exercise is tried, every exercise "
    "runs inside it, and it is not cleaned away before "
    "the exercise stands tried and checked")
PLAIN_EXPLANATION = (
    "The tutorial grown (M-185): interactive lessons "
    "per feature family, runnable inside a scratch "
    "repo - mythic tutorial becomes the manual you "
    "play.")
USAGE = (
    "Usage: /lessons | /lessons lesson <lesson-id> | "
    "/lessons play | /lessons scratch <scratch-id> | "
    "/lessons view <view-id> | /lessons readiness <readiness> | "
    "/lessons panel | /lessons verdict")

_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_LESSON_KEYS = frozenset({
    "lesson_id", "seq", "title", "family", "readiness",
    "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_STEP_KEYS = frozenset({
    "step_id", "seq", "phase", "title", "detail",
} | set(_PROVENANCE))
_SCRATCH_KEYS = frozenset({
    "scratch_id", "seq", "repo", "state", "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "passes", "gaps", "segment", "plain_lines", "telling",
    "verdict", "in_order", "play"})
_OUTSIDE_SCRATCH_KEYS = (
    "real_workspace", "runs_in_real_workspace",
    "against_real_workspace", "outside_scratch_repo",
    "run_outside_scratch", "runs_outside_scratch")


# ---------------------------------------------------------------------
# Small judges, in the sibling shape.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_count(value: Any, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{what} must be a whole number")
    if value < 0:
        raise ValueError(f"{what} must not be negative")
    return value


def _check_seq(value: Any, what: str = "a sequence") -> int:
    number = _check_count(value, what)
    if number < 1:
        raise ValueError(f"{what} must stand at 1 or later")
    return number


def _check_lines(value: Any, what: str) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError(f"{what} must be a list of lines")
    lines = []
    for line in value:
        lines.append(_clean_text(line, f"a line of {what}"))
    return tuple(lines)


def _provenance(mapping: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key in _PROVENANCE:
        if key == "recorded_on":
            out[key] = _clean_text(mapping.get(key), "a recorded_on day")
        else:
            out[key] = _clean_text(mapping.get(key), f"a {key}")
    return out


def _needed(mapping: Dict[str, Any], allowed: frozenset,
            what: str) -> None:
    if not isinstance(mapping, dict):
        raise ValueError(f"{what} must be a mapping")
    for key in _OUTSIDE_SCRATCH_KEYS:
        if key in mapping:
            raise ValueError(
                f"{what} claims a run outside a scratch repo "
                f"({key!r} is named on it): "
                f"{SCRATCH_REPO_RULE}")
    for key in mapping:
        if key in _DERIVED_KEYS:
            raise ValueError(
                f"{what} carries {key!r}, which is derived from its "
                f"own fields and never stored")
        if key not in allowed:
            raise ValueError(f"{what} carries unknown field {key!r}")


def normalize_readiness(value: Any) -> str:
    readiness = _clean_text(value, "a lesson readiness").lower()
    if readiness not in READINESS_WORDS:
        raise ValueError(
            f"lesson readiness {readiness!r} is not one of the held "
            f"readiness_words: " + ", ".join(READINESS_WORDS))
    return readiness


def normalize_family(value: Any) -> str:
    family = _clean_text(value, "a family").lower()
    if family not in FEATURE_FAMILIES:
        raise ValueError(
            f"family {family!r} is not one of the named families: "
            + ", ".join(FEATURE_FAMILIES))
    return family


def normalize_view_filter(value: Any) -> str:
    view_filter = _clean_text(value, "a view filter").lower()
    if view_filter not in VIEW_FILTERS:
        raise ValueError(
            f"view filter {view_filter!r} is not one of the held "
            f"filters: " + ", ".join(VIEW_FILTERS))
    return view_filter


def normalize_phase(value: Any) -> str:
    phase = _clean_text(value, "a play phase").lower()
    if phase not in PLAY_PHASES:
        raise ValueError(
            f"play phase {phase!r} is not one of the held phases: "
            + ", ".join(PLAY_PHASES))
    return phase


def normalize_state(value: Any) -> str:
    state = _clean_text(value, "a scratch state").lower()
    if state not in SCRATCH_STATES:
        raise ValueError(
            f"scratch state {state!r} is not one of the held "
            f"states: " + ", ".join(SCRATCH_STATES))
    return state


# ---------------------------------------------------------------------
# The held lesson: one lesson, its feature family, and the
# readiness its exercise honestly stands in.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class LessonRecord:
    """One interactive lesson, held as data.

    The lesson names its title, its feature
    family - one of the closed family vocabulary -
    and its readiness, ready or blocked. A lesson
    whose exercise does not stand ready stands
    blocked, named in its gaps, and does not stand
    ready: readiness is never faked here. The
    lesson runs inside a scratch repo, never
    against the real workspace.
    """

    lesson_id: str
    seq: int
    title: str
    family: str
    readiness: str
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "lesson_id",
            _clean_text(self.lesson_id, "a lesson id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a title"))
        object.__setattr__(self, "family", normalize_family(self.family))
        object.__setattr__(
            self, "readiness", normalize_readiness(self.readiness))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a lesson detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.lesson_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "lesson_id": self.lesson_id, "seq": self.seq,
            "title": self.title, "family": self.family,
            "readiness": self.readiness, "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_lesson_ref(value: Any) -> LessonRecord:
    if not isinstance(value, LessonRecord):
        raise ValueError("a lesson must be a LessonRecord")
    return value


def validate_lesson(lesson: Any) -> LessonRecord:
    return _check_lesson_ref(lesson)


def build_lesson(lesson: Any = None, **kwargs: Any) -> LessonRecord:
    """Build one held lesson from a mapping or fields."""
    if lesson is None:
        data = dict(kwargs)
    elif isinstance(lesson, LessonRecord):
        if kwargs:
            raise ValueError(
                "a lesson stands whole or by fields, not both")
        return lesson
    elif isinstance(lesson, dict):
        data = dict(lesson)
        data.update(kwargs)
    else:
        raise ValueError(
            "a lesson must be a mapping or a LessonRecord")
    _needed(data, _LESSON_KEYS, "a lesson")
    return LessonRecord(
        lesson_id=data.get("lesson_id"), seq=data.get("seq"),
        title=data.get("title"), family=data.get("family"),
        readiness=data.get("readiness"), detail=data.get("detail"),
        **_provenance(data))


def lesson_gaps(lesson: Any) -> Tuple[str, ...]:
    """The gaps that keep a lesson from standing ready."""
    checked = _check_lesson_ref(lesson)
    return () if checked.readiness == "ready" else ("exercise",)


def lesson_passes(lesson: Any) -> bool:
    return not lesson_gaps(lesson)


def plain_lines(lesson: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the lesson's own fields."""
    checked = _check_lesson_ref(lesson)
    return (
        f"Lesson: {checked.title}",
        f"Family: {checked.family}",
        f"Readiness: {checked.readiness}",
    )


def segment_of(lesson: Any) -> str:
    checked = _check_lesson_ref(lesson)
    gaps = lesson_gaps(checked)
    return (
        f"{checked.lesson_id}: {checked.title} in family "
        f"'{checked.family}' - readiness: '{checked.readiness}' - "
        f"detail: '{checked.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held view: which lessons a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TutorialView:
    """A view over the book: every lesson, the ready, the blocked."""

    view_id: str
    seq: int
    view_filter: str
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "view_id", _clean_text(self.view_id, "a view id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "view_filter", normalize_view_filter(self.view_filter))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a view detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    def to_record(self) -> Dict[str, Any]:
        record = {
            "view_id": self.view_id, "seq": self.seq,
            "view_filter": self.view_filter, "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_view_ref(value: Any) -> TutorialView:
    if not isinstance(value, TutorialView):
        raise ValueError("a view must be a TutorialView")
    return value


def validate_view(view: Any) -> TutorialView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> TutorialView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, TutorialView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or a TutorialView")
    _needed(data, _VIEW_KEYS, "a view")
    return TutorialView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held play step and the scratch repo: the play in order,
# the scratch repo the lessons run inside, held as data.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class PlayStep:
    """One step of the tutorial play, held in order.

    The step stands under its phase - open, read,
    try, check or clean - with its title and its
    detail. The play is the steps in held order;
    the scratch-repo rule is judged on the whole
    play in the book, never on one step.
    """

    step_id: str
    seq: int
    phase: str
    title: str
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "step_id", _clean_text(self.step_id, "a step id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(self, "phase", normalize_phase(self.phase))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a step title"))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a step detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.step_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "step_id": self.step_id, "seq": self.seq,
            "phase": self.phase, "title": self.title,
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_step_ref(value: Any) -> PlayStep:
    if not isinstance(value, PlayStep):
        raise ValueError("a play step must be a PlayStep")
    return value


def validate_step(step: Any) -> PlayStep:
    return _check_step_ref(step)


def build_step(step: Any = None, **kwargs: Any) -> PlayStep:
    if step is None:
        data = dict(kwargs)
    elif isinstance(step, PlayStep):
        if kwargs:
            raise ValueError("a step stands whole or by fields, not both")
        return step
    elif isinstance(step, dict):
        data = dict(step)
        data.update(kwargs)
    else:
        raise ValueError("a step must be a mapping or a PlayStep")
    _needed(data, _STEP_KEYS, "a play step")
    return PlayStep(
        step_id=data.get("step_id"), seq=data.get("seq"),
        phase=data.get("phase"), title=data.get("title"),
        detail=data.get("detail"), **_provenance(data))


@dataclass(frozen=True)
class ScratchRecord:
    """One scratch repo, held as data.

    The scratch record holds the repo it names
    and the state it stands in - open, closed or
    still pending. Lessons run inside it, never
    against the real workspace; the repo itself
    is never created by this layer.
    """

    scratch_id: str
    seq: int
    repo: str
    state: str
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "scratch_id", _clean_text(self.scratch_id, "a scratch id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "title", _clean_text(self.repo, "a scratch repo"))
        object.__setattr__(
            self, "state", normalize_state(self.state))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a scratch detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.scratch_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "scratch_id": self.scratch_id, "seq": self.seq,
            "repo": self.repo, "state": self.state,
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_scratch_ref(value: Any) -> ScratchRecord:
    if not isinstance(value, ScratchRecord):
        raise ValueError("a scratch must be a ScratchRecord")
    return value


def validate_scratch(scratch: Any) -> ScratchRecord:
    return _check_scratch_ref(scratch)


def build_scratch(scratch: Any = None, **kwargs: Any) -> ScratchRecord:
    if scratch is None:
        data = dict(kwargs)
    elif isinstance(scratch, ScratchRecord):
        if kwargs:
            raise ValueError("a scratch stands whole or by fields, not both")
        return scratch
    elif isinstance(scratch, dict):
        data = dict(scratch)
        data.update(kwargs)
    else:
        raise ValueError("a scratch must be a mapping or a ScratchRecord")
    _needed(data, _SCRATCH_KEYS, "a scratch")
    return ScratchRecord(
        scratch_id=data.get("scratch_id"), seq=data.get("seq"),
        repo=data.get("repo"), state=data.get("state"),
        detail=data.get("detail"), **_provenance(data))


def inspect_tutorial_source(piece: Any) -> Dict[str, Any]:
    """Name what one tutorial source piece is, without judging it."""
    if isinstance(piece, LessonRecord):
        return {"kind": "lesson", "lesson_id": piece.lesson_id}
    if isinstance(piece, dict):
        if "lesson_id" in piece:
            return {"kind": "lesson",
                    "lesson_id": piece.get("lesson_id")}
        if "view_id" in piece:
            return {"kind": "view", "view_id": piece.get("view_id")}
        if "step_id" in piece:
            return {"kind": "step", "step_id": piece.get("step_id")}
        if "scratch_id" in piece:
            return {"kind": "scratch", "scratch_id": piece.get("scratch_id")}
    return {"kind": "unknown", "lesson_id": None}


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TutorialPanelRow:
    item_id: str
    readiness: str
    label: str
    segment: str
    recorded_on: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id, "readiness": self.readiness,
            "label": self.label, "segment": self.segment,
            "recorded_on": self.recorded_on,
        }


def _row_for_lesson(lesson: LessonRecord) -> TutorialPanelRow:
    return TutorialPanelRow(
        item_id=lesson.lesson_id, readiness=lesson.readiness,
        label=lesson.title, segment=segment_of(lesson),
        recorded_on=lesson.recorded_on)


def _check_row_ref(value: Any) -> TutorialPanelRow:
    if not isinstance(value, TutorialPanelRow):
        raise ValueError("a panel row must be a TutorialPanelRow")
    return value


def validate_row(row: Any, lesson: Any = None) -> TutorialPanelRow:
    checked = _check_row_ref(row)
    if lesson is not None:
        derived = _row_for_lesson(_check_lesson_ref(lesson))
        if checked != derived:
            raise ValueError(
                f"panel row {checked.item_id!r} does not agree with "
                f"the row derived from its lesson")
    return checked


def build_row(row: Any = None, lesson: Any = None,
              **kwargs: Any) -> TutorialPanelRow:
    if lesson is not None:
        derived = _row_for_lesson(_check_lesson_ref(lesson))
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            TutorialPanelRow(**kwargs))
        return validate_row(built, lesson)
    if isinstance(row, TutorialPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        return TutorialPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            readiness=normalize_readiness(data.get("readiness")),
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return TutorialPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or a TutorialPanelRow")


@dataclass(frozen=True)
class ReadinessCount:
    readiness: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"readiness": self.readiness, "items": self.items}


def _readiness_counts(rows: Tuple[TutorialPanelRow, ...]
                    ) -> Tuple[ReadinessCount, ...]:
    counts: List[ReadinessCount] = []
    for readiness in READINESS_WORDS:
        number = sum(1 for row in rows if row.readiness == readiness)
        if number:
            counts.append(ReadinessCount(readiness=readiness, items=number))
    return tuple(counts)


def _panel_account(total_items: int, total_shown: int,
                   passing_shown: int,
                   readiness_counts: Tuple[ReadinessCount, ...],
                   view_filter: str, as_of: str) -> Tuple[str, ...]:
    readiness_words = ", ".join(
        f"{count.readiness} {count.items}"
        for count in readiness_counts) or "none"
    return (
        f"The tutorial book holds {total_items} lessons as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {readiness_words}; {passing_shown} of the shown lessons "
        f"stand ready.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its lesson's own fields "
        "- the title, the feature family it belongs to and "
        "the readiness its exercise honestly stands in - and no "
        "judgement is stored on any lesson.",
        "Readiness is never faked: a lesson whose exercise "
        "does not stand ready stands blocked, named in its "
        "gaps, and every lesson runs inside a scratch repo, "
        "never against the real workspace.",
    )


@dataclass(frozen=True)
class TutorialPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[TutorialPanelRow, ...]
    total_items: int
    total_shown: int
    readiness_counts: Tuple[ReadinessCount, ...]
    as_of: str
    account: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "panel_id": self.panel_id, "view_id": self.view_id,
            "view_filter": self.view_filter,
            "rows": [row.to_record() for row in self.rows],
            "total_items": self.total_items,
            "total_shown": self.total_shown,
            "readiness_counts": [c.to_record() for c in self.readiness_counts],
            "as_of": self.as_of, "account": list(self.account),
        }


def _held_lessons(source: Any) -> Tuple[LessonRecord, ...]:
    return _source_book(source).lessons


def _resolve_view(source: Any, view: Any) -> TutorialView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, TutorialView):
        return view
    return book.view_for(view)


def shown_lessons(source: Any, view: Any = None
                     ) -> Tuple[LessonRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.lessons
    if resolved.view_filter == "ready":
        return tuple(d for d in book.lessons if lesson_passes(d))
    return tuple(d for d in book.lessons if not lesson_passes(d))


def lessons_for_readiness(source: Any, readiness: Any
                           ) -> Tuple[LessonRecord, ...]:
    wanted = normalize_readiness(readiness)
    return tuple(
        d for d in _source_book(source).lessons
        if d.readiness == wanted)


def passing_lessons(source: Any) -> Tuple[LessonRecord, ...]:
    return tuple(
        d for d in _source_book(source).lessons
        if lesson_passes(d))


def total_lessons(source: Any) -> int:
    return len(_source_book(source).lessons)


def derive_panel(source: Any, view: Any = None) -> TutorialPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_lessons(book, resolved)
    rows = tuple(_row_for_lesson(lesson) for lesson in shown)
    counts = _readiness_counts(rows)
    as_of = max((d.recorded_on for d in book.lessons), default="")
    passing = sum(1 for d in shown if lesson_passes(d))
    return TutorialPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.lessons), total_shown=len(shown),
        readiness_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.lessons), len(shown), passing, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> TutorialPanel:
    if not isinstance(value, TutorialPanel):
        raise ValueError("a panel must be a TutorialPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> TutorialPanel:
    """Judge a stored panel against the panel derived from its book.

    Every derived field must agree; the stored
    panel's own name is its identity, not derived
    content (the M-182 lesson).
    """
    checked = _check_panel_ref(panel)
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(checked.view_id)
                if checked.view_id is not None else None)
        derived = derive_panel(book, view)
        for attr in ("view_id", "view_filter", "rows", "total_items",
                     "total_shown", "readiness_counts", "as_of", "account"):
            if getattr(checked, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {checked.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return checked


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> TutorialPanel:
    if isinstance(panel, TutorialPanel):
        if kwargs:
            raise ValueError("a panel stands whole or by fields, not both")
        return validate_panel(panel, source)
    if isinstance(panel, dict):
        data = dict(panel)
        data.update(kwargs)
        rows = tuple(build_row(row) for row in data.get("rows") or ())
        counts = tuple(
            ReadinessCount(
                readiness=normalize_readiness(c.get("readiness")),
                items=_check_count(c.get("items"), "an readiness count"))
            for c in data.get("readiness_counts") or ()
            if isinstance(c, dict))
        built = TutorialPanel(
            panel_id=_clean_text(data.get("panel_id"), "a panel id"),
            view_id=data.get("view_id"),
            view_filter=normalize_view_filter(data.get("view_filter")),
            rows=rows,
            total_items=_check_count(
                data.get("total_items"), "a total_items count"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            readiness_counts=counts,
            as_of=_clean_text(data.get("as_of"), "an as_of day"),
            account=_check_lines(data.get("account"), "the account"))
        return validate_panel(built, source)
    if panel is None and source is not None:
        return derive_panel(source, kwargs.get("view"))
    raise ValueError("a panel must be a mapping, a TutorialPanel, or derived")


def _verdict_word(total_shown: int, passing_shown: int) -> str:
    if total_shown > 0 and passing_shown == total_shown:
        return "open"
    if passing_shown == 0:
        return "shut"
    return "strained"


@dataclass(frozen=True)
class TutorialVerdict:
    verdict: str
    view_id: Optional[str]
    total_shown: int
    passing_shown: int
    latest_on: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict, "view_id": self.view_id,
            "total_shown": self.total_shown,
            "passing_shown": self.passing_shown,
            "latest_on": self.latest_on,
        }


def derive_verdict(source: Any, view: Any = None) -> TutorialVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_lessons(book, resolved)
    passing = sum(1 for d in shown if lesson_passes(d))
    latest = max((d.recorded_on for d in shown), default="")
    return TutorialVerdict(
        verdict=_verdict_word(len(shown), passing),
        view_id=resolved.view_id, total_shown=len(shown),
        passing_shown=passing, latest_on=latest)


def _check_verdict_ref(value: Any) -> TutorialVerdict:
    if not isinstance(value, TutorialVerdict):
        raise ValueError("a verdict must be a TutorialVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> TutorialVerdict:
    checked = _check_verdict_ref(verdict)
    if checked.verdict not in VERDICT_WORDS:
        raise ValueError(f"verdict {checked.verdict!r} is not a held word")
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(checked.view_id)
                if checked.view_id is not None else None)
        derived = derive_verdict(book, view)
        if checked != derived:
            raise ValueError(
                "the stored verdict disagrees with the verdict "
                "derived from its book")
    return checked


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> TutorialVerdict:
    if isinstance(verdict, TutorialVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = TutorialVerdict(
            verdict=_clean_text(data.get("verdict"), "a verdict"),
            view_id=data.get("view_id"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            passing_shown=_check_count(
                data.get("passing_shown"), "a passing_shown count"),
            latest_on=_clean_text(data.get("latest_on"), "a latest day"))
        return validate_verdict(built, source)
    if verdict is None and source is not None:
        return derive_verdict(source, kwargs.get("view"))
    raise ValueError(
        "a verdict must be a mapping, a TutorialVerdict, or derived")


# ---------------------------------------------------------------------
# The play: the held steps in order, judged under the scratch-repo
# rule - opened before any exercise is tried, cleaned only after.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TutorialPlay:
    """The tutorial play, derived from the book's held steps.

    The play is its steps in held order, with the
    first try step and the first clean step named
    by sequence. The play stands in order when a
    try stands, and no clean step stands before
    it: the scratch repo is not cleaned away before
    its exercise stands tried.
    """

    steps: Tuple[PlayStep, ...]
    try_seq: Optional[int]
    clean_seq: Optional[int]

    def passes(self) -> bool:
        if self.try_seq is None:
            return False
        return (self.clean_seq is None
                or self.try_seq < self.clean_seq)

    def to_record(self) -> Dict[str, Any]:
        return {
            "steps": [step.to_record() for step in self.steps],
            "try_seq": self.try_seq,
            "clean_seq": self.clean_seq,
            "passes": self.passes(),
        }


def play_steps(source: Any) -> Tuple[PlayStep, ...]:
    """The book's play steps, in held order."""
    return _source_book(source).steps


def derive_play(source: Any) -> TutorialPlay:
    book = _source_book(source)
    tried = next(
        (s.seq for s in book.steps if s.phase == "try"), None)
    clean = next(
        (s.seq for s in book.steps if s.phase == "clean"), None)
    return TutorialPlay(
        steps=book.steps, try_seq=tried, clean_seq=clean)


def _judge_play_order(steps: Tuple[PlayStep, ...]) -> None:
    tried = next((s.seq for s in steps if s.phase == "try"), None)
    clean = next(
        (s.seq for s in steps if s.phase == "clean"), None)
    if clean is not None and (
            tried is None or clean < tried):
        raise ValueError(
            f"the play cleans its scratch repo away before "
            f"its exercise stands tried: {SCRATCH_REPO_RULE}")


# ---------------------------------------------------------------------
# The book: lessons, views, play steps and scratches held together,
# one pinned panel at most per telling, and no verdict ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TutorialBook:
    title: str
    lessons: Tuple[LessonRecord, ...] = ()
    views: Tuple[TutorialView, ...] = ()
    steps: Tuple[PlayStep, ...] = ()
    scratches: Tuple[ScratchRecord, ...] = ()
    panels: Tuple[TutorialPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        lessons = tuple(
            _check_lesson_ref(d) for d in self.lessons)
        views = tuple(_check_view_ref(v) for v in self.views)
        steps = tuple(_check_step_ref(s) for s in self.steps)
        scratches = tuple(_check_scratch_ref(o) for o in self.scratches)
        panels = tuple(_check_panel_ref(p) for p in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for lesson in lessons:
            if lesson.lesson_id in seen_ids:
                raise ValueError(
                    f"two lessons stand under id "
                    f"{lesson.lesson_id!r}")
            if lesson.seq in seen_seqs:
                raise ValueError(
                    f"two lessons stand at sequence {lesson.seq}")
            seen_ids.add(lesson.lesson_id)
            seen_seqs.add(lesson.seq)
        view_ids = set()
        view_seqs = set()
        for view in views:
            if view.view_id in view_ids:
                raise ValueError(
                    f"two views stand under id {view.view_id!r}")
            if view.seq in view_seqs:
                raise ValueError(
                    f"two views stand at sequence {view.seq}")
            view_ids.add(view.view_id)
            view_seqs.add(view.seq)
        step_ids = set()
        step_seqs = set()
        for step in steps:
            if step.step_id in step_ids:
                raise ValueError(
                    f"two play steps stand under id {step.step_id!r}")
            if step.seq in step_seqs:
                raise ValueError(
                    f"two play steps stand at sequence {step.seq}")
            step_ids.add(step.step_id)
            step_seqs.add(step.seq)
        scratch_ids = set()
        scratch_seqs = set()
        for scratch in scratches:
            if scratch.scratch_id in scratch_ids:
                raise ValueError(
                    f"two scratches stand under id {scratch.scratch_id!r}")
            if scratch.seq in scratch_seqs:
                raise ValueError(
                    f"two scratches stand at sequence {scratch.seq}")
            scratch_ids.add(scratch.scratch_id)
            scratch_seqs.add(scratch.seq)
        ordered_steps = tuple(sorted(steps, key=lambda s: s.seq))
        _judge_play_order(ordered_steps)
        object.__setattr__(
            self, "lessons",
            tuple(sorted(lessons, key=lambda d: d.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(self, "steps", ordered_steps)
        object.__setattr__(
            self, "scratches", tuple(sorted(scratches, key=lambda o: o.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.lessons + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(d.lesson_id for d in self.lessons) + tuple(
            v.view_id for v in self.views)

    def lesson_ids(self) -> Tuple[str, ...]:
        return tuple(d.lesson_id for d in self.lessons)

    def lesson_for(self, lesson_id: Any) -> LessonRecord:
        wanted = _clean_text(lesson_id, "a lesson id")
        for lesson in self.lessons:
            if lesson.lesson_id == wanted:
                return lesson
        raise KeyError(
            f"no lesson named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> TutorialView:
        wanted = _clean_text(view_id, "a view id")
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no view named {wanted!r} stands in this book")

    def step_for(self, step_id: Any) -> PlayStep:
        wanted = _clean_text(step_id, "a step id")
        for step in self.steps:
            if step.step_id == wanted:
                return step
        raise KeyError(f"no step named {wanted!r} stands in this book")

    def scratch_for(self, scratch_id: Any) -> ScratchRecord:
        wanted = _clean_text(scratch_id, "a scratch id")
        for scratch in self.scratches:
            if scratch.scratch_id == wanted:
                return scratch
        raise KeyError(f"no scratch named {wanted!r} stands in this book")

    def item_for(self, item_id: Any) -> Any:
        wanted = _clean_text(item_id, "an item id")
        for lesson in self.lessons:
            if lesson.lesson_id == wanted:
                return lesson
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "lessons": [d.to_record() for d in self.lessons],
            "views": [v.to_record() for v in self.views],
            "steps": [s.to_record() for s in self.steps],
            "scratches": [o.to_record() for o in self.scratches],
            "panels": [p.to_record() for p in self.panels],
        }


def _judge_book_panels(book: TutorialBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: TutorialBook) -> None:
    if book.title != "The tutorial grown at the M-184 slice boundary":
        raise ValueError("the shipped example book carries another title")
    if len(book.lessons) != 6 or len(book.views) != 2:
        raise ValueError(
            "the shipped example book must hold six lessons and "
            "two views")
    if len(book.steps) != 5 or len(book.scratches) != 1:
        raise ValueError(
            "the shipped example book must hold five play steps and "
            "one scratch")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m184-boundary":
        raise ValueError("the pinned panel is panel-m184-boundary")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "strained" or verdict.passing_shown != 4:
        raise ValueError(
            "the shipped example book's verdict must stand strained "
            "at four ready of six")
    play = derive_play(book)
    if not play.passes():
        raise ValueError(
            "the shipped example book's play must stand in order: "
            "the scratch repo cleaned only after the try")


def validate_book(data: Any, *, require_example: bool = False) -> TutorialBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, TutorialBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a tutorial book must be a mapping")
    for key in _OUTSIDE_SCRATCH_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a run outside a scratch repo "
                f"({key!r} is named on it): "
                f"{SCRATCH_REPO_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its lessons under a view")
    if data.get("schema") is not None and (
            data["schema"] != TUTORIAL_GROWN_SCHEMA):
        raise ValueError(
            f"a book's schema must be {TUTORIAL_GROWN_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != TUTORIAL_GROWN_SLICE):
        raise ValueError(
            f"a book's slice must be {TUTORIAL_GROWN_SLICE!r}")
    guide = data.get("guide") or {}
    if not isinstance(guide, dict):
        raise ValueError("a book's guide must be a mapping")
    title = guide.get("title") or data.get("title")
    lessons = tuple(
        build_lesson(d) for d in data.get("lessons") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    steps = tuple(build_step(s) for s in data.get("steps") or ())
    scratches = tuple(build_scratch(o) for o in data.get("scratches") or ())
    book = TutorialBook(
        title=title, lessons=lessons, views=views, steps=steps,
        scratches=scratches, panels=())
    panels = tuple(
        build_panel(p, book) for p in data.get("panels") or ())
    book = TutorialBook(
        title=book.title, lessons=book.lessons, views=book.views,
        steps=book.steps, scratches=book.scratches, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> TutorialBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (TutorialBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or a TutorialBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> TutorialBook:
    return validate_book(data, require_example=require_example)


def load_tutorial_grown(
        data: Optional[Dict[str, Any]] = None) -> TutorialBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(TUTORIAL_GROWN_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_tutorial_grown_file(path: Any) -> TutorialBook:
    """Load one tutorial file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: lessons and views held one by one.
# ---------------------------------------------------------------------

class TutorialRegistry:
    """An in-memory holding of lessons and views.

    The registry is the pure layer's model of a
    session's tutorial book: lessons are held
    under their ids, one lesson per id and per
    sequence, and views are held in recorded
    order, one view per sequence and per id.
    Holding is data only - nothing held here
    runs a lesson, opens a repo, or writes
    anything to a real workspace.
    """

    def __init__(self, book: Any = None) -> None:
        self._lessons: List[LessonRecord] = []
        self._views: List[TutorialView] = []
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

    def _register(self, held: List[Any], item: Any,
                  id_attr: str, what: str) -> Any:
        for other in held:
            if getattr(other, id_attr) == getattr(item, id_attr):
                raise ValueError(
                    f"a {what} already stands under id "
                    f"{getattr(item, id_attr)!r}")
            if other.seq == item.seq:
                raise ValueError(
                    f"a {what} already stands at sequence {item.seq}")
        held.append(item)
        held.sort(key=lambda held_item: held_item.seq)
        return item

    def register_lesson(self, item: Any) -> LessonRecord:
        """Hold one lesson, judged whole before held."""
        return self._register(
            self._lessons, _check_lesson_ref(item),
            "lesson_id", "lesson")

    def register_view(self, view: Any) -> TutorialView:
        """Hold one view; a view naming no id takes a fresh one."""
        checked = _check_view_ref(view)
        if not checked.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            checked = build_view({**checked.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, checked, "view_id", "view")

    def register_book(self, book: Any) -> TutorialBook:
        """Hold a whole book's lessons and views, under its title."""
        checked = build_book(book)
        if self._title is not None and checked.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {checked.title!r}")
        for lesson in checked.lessons:
            self.register_lesson(lesson)
        for view in checked.views:
            self.register_view(view)
        self._title = checked.title
        return self.book()

    def book(self) -> TutorialBook:
        return TutorialBook(
            title=self._title or "An unheld tutorial book",
            lessons=tuple(self._lessons),
            views=tuple(self._views), steps=(), scratches=(), panels=())

    def list_lessons(self) -> Tuple[LessonRecord, ...]:
        return tuple(self._lessons)

    def list_views(self) -> Tuple[TutorialView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._lessons) + tuple(self._views)

    def get_lesson(self, lesson_id: Any) -> LessonRecord:
        return self.book().lesson_for(lesson_id)

    def get_view(self, view_id: Any) -> TutorialView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records shaped for the journal road.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> TutorialBook:
    if source is None:
        return load_tutorial_grown()
    if isinstance(source, TutorialBook):
        return source
    if isinstance(source, TutorialRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def lesson_record(lesson: Any, source: Any = None) -> Dict[str, Any]:
    checked = _check_lesson_ref(lesson)
    record = {
        "type": "tutorial_lesson",
        "slice": TUTORIAL_GROWN_SLICE,
        "lesson_id": checked.lesson_id,
        "title": checked.title,
        "segment": segment_of(checked),
        "passes": lesson_passes(checked),
        "gaps": list(lesson_gaps(checked)),
    }
    record.update(_provenance_record(checked))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    checked = _check_view_ref(view)
    record = {
        "type": "tutorial_view",
        "slice": TUTORIAL_GROWN_SLICE,
        "view_id": checked.view_id, "seq": checked.seq,
        "view_filter": checked.view_filter,
    }
    record.update(_provenance_record(checked))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    checked = validate_panel(panel, source)
    record = {"type": "tutorial_panel",
              "slice": TUTORIAL_GROWN_SLICE}
    record.update(checked.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, TutorialVerdict):
        checked = validate_verdict(verdict, source)
    else:
        checked = derive_verdict(_source_book(verdict), view)
    record = {"type": "tutorial_verdict",
              "slice": TUTORIAL_GROWN_SLICE}
    record.update(checked.to_record())
    return record


def step_record(step: Any) -> Dict[str, Any]:
    checked = _check_step_ref(step)
    record = {
        "type": "tutorial_step",
        "slice": TUTORIAL_GROWN_SLICE,
        "step_id": checked.step_id, "seq": checked.seq,
        "phase": checked.phase,
    }
    record.update(_provenance_record(checked))
    return record


def scratch_record(scratch: Any) -> Dict[str, Any]:
    checked = _check_scratch_ref(scratch)
    record = {
        "type": "tutorial_scratch",
        "slice": TUTORIAL_GROWN_SLICE,
        "scratch_id": checked.scratch_id,
        "repo": checked.repo,
        "state": checked.state,
    }
    record.update(_provenance_record(checked))
    return record


def play_record(source: Any) -> Dict[str, Any]:
    play = derive_play(source)
    record = {"type": "tutorial_play",
              "slice": TUTORIAL_GROWN_SLICE}
    record.update(play.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    checked = _source_book(book)
    record = {"type": "tutorial_book",
              "slice": TUTORIAL_GROWN_SLICE, "title": checked.title}
    record.update(checked.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(lesson: Any, source: Any = None) -> str:
    checked = _check_lesson_ref(lesson)
    return (
        f"{checked.title} - in family {checked.family}: "
        f"{checked.readiness}. {checked.detail}")


def lesson_plain_words(lesson: Any, source: Any = None) -> str:
    return plain_words(lesson, source)


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The tutorial book stands {verdict.verdict}: "
        f"{verdict.passing_shown} of {verdict.total_shown} shown "
        f"lessons stand ready.")


def view_plain_words(view: Any) -> str:
    checked = _check_view_ref(view)
    return f"View {checked.view_id}: shows {checked.view_filter} lessons."


def play_plain_words(source: Any) -> str:
    play = derive_play(source)
    phases = ", ".join(step.phase for step in play.steps) or "none"
    return (
        f"The play stands in {len(play.steps)} steps ({phases}) and "
        f"stands in order: {play.passes()} - the scratch repo "
        f"opened before the try, cleaned only after.")


def format_lesson(lesson: Any, source: Any = None) -> str:
    checked = _check_lesson_ref(lesson)
    lines = [f"{checked.title} ({checked.lesson_id})"]
    lines.extend(plain_lines(checked))
    lines.append(checked.detail)
    if lesson_passes(checked):
        lines.append("This lesson stands ready, playable inside its scratch repo.")
    else:
        lines.append(
            "This lesson stands blocked - named in its gaps, "
            "never faked as ready.")
    return "\n".join(lines)


def format_view(view: Any) -> str:
    checked = _check_view_ref(view)
    return (
        f"View {checked.view_id}: filter {checked.view_filter} - "
        f"{checked.detail}")


def format_scratch(scratch: Any) -> str:
    checked = _check_scratch_ref(scratch)
    return (
        f"Scratch {checked.scratch_id}: scratch repo "
        f"{checked.repo} - {checked.state}. {checked.detail}")


def format_book(source: Any = None, readiness: Any = None) -> str:
    book = _source_book(source)
    lessons = (lessons_for_readiness(book, readiness)
                  if readiness is not None else book.lessons)
    lines = [f"The Tutorial Grown (M-185) - {book.title}"]
    lines.extend(segment_of(lesson) for lesson in lessons)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Tutorial panel under view {panel.view_id}:"]
    lines.extend(row.segment for row in panel.rows)
    lines.extend(panel.account)
    return "\n".join(lines)


def format_verdict(source: Any = None, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return verdict_plain_words(source, view) + (
        f" (view {verdict.view_id}, as of {verdict.latest_on})")


def format_play(source: Any = None) -> str:
    book = _source_book(source)
    play = derive_play(book)
    lines = ["The tutorial play, in held order:"]
    for step in play.steps:
        lines.append(
            f"{step.seq}. [{step.phase}] {step.title} - {step.detail}")
    lines.append(play_plain_words(book))
    for scratch in book.scratches:
        lines.append(format_scratch(scratch))
    return "\n".join(lines)


def format_tutorial_grown_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "The Tutorial Grown (M-185)",
        f"{book.title}: {len(book.lessons)} lessons held, "
        f"{len(passing_lessons(book))} lessons standing ready, "
        f"{len(book.steps)} play steps held in order.",
    ]
    if book.views:
        panel = derive_panel(book, book.views[0])
        lines.append(
            f"{panel.total_shown} of {panel.total_items} items show "
            f"under the first view.")
        lines.extend(row.segment for row in panel.rows)
    lines.append(PLAIN_EXPLANATION)
    return "\n".join(lines)


def parse_tutorial_args(args: Any) -> Tuple[str, Any]:
    """Parse the /lessons grammar into (action, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("lesson", "scratch", "view", "readiness"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("play", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
