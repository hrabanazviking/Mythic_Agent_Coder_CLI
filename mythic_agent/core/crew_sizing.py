"""Crew sizing honesty (All-Features roadmap slice M-135).

Part VI continues here. The roadmap's words:
``the app recommends crew size by task shape and
says when one pair of hands beats six.``

What already shipped, and what this slice adds:

* The crew itself is already data
  (``core/crew_members.py``, M-121), its offices
  are formalised (``core/offices.py``, M-122),
  its work is dealt as data (M-125) and the
  coordinator's stand-up digest is derived from
  its entries, never stored (M-134). What nothing
  held is an honest answer to ``how many hands
  does this task want?``: crew size was a habit,
  not a judgement that could be checked against
  the shape of the task itself.
* This slice is that judgement, as a pure layer:
  a sizing book validated as data - sizing cases
  (one task shape per case: a title, the task in
  plain words, the member who would lead it, the
  office the work fits, how many independent
  pieces the work splits into, and whether the
  work is tightly coupled or loose) under a title
  - the shipped data file
  (``mythic_agent/data/crew_sizing.yaml``)
  holding one example sizing book in exactly the
  shape a real sizing file takes, a loader for a
  sizing file anywhere on disk, the recommended
  size derived mechanically from the shape alone,
  a record shaped as session news, and a small
  in-memory registry model. This module spawns
  no crew, sizes no live crew, calls no model
  and imports no agent / UI code; the agent layer
  owns holding the sizing for a session and
  showing the recommendation on demand.

Honesty rules, enforced here and pinned by tests:

* **The recommendation is derived, never
  stored.** A case's recommended size is computed
  from its shape alone: tightly coupled work
  recommends one pair of hands however many
  pieces it names - one pair of hands beats six
  when the work must be held in one head - and
  loose work recommends one pair of hands per
  independent piece, up to six, so the same shape
  always yields the same recommendation. A stored
  recommendation that disagrees with the derived
  one refuses, exactly as a stored stand-up
  digest does (M-134).
* **The solo case is said plainly.** When the
  derived size is one, the recommendation's
  reason says so in plain words - one pair of
  hands beats six - never dressing a solo task
  up as crew work, and never shrinking a wide,
  loose task down to one pair either.
* **Members and offices are the shipped
  casting.** A case names its lead as an M-121
  member id and its office as an M-122 formal
  office, each read exactly as those layers read
  one (``core/crew_members.py`` /
  ``core/offices.py``) - composed by import,
  never re-read here.
* **Data only.** No crew is spawned, sized or
  modelled here and no model call is claimed or
  attempted: a sizing here is a validated record
  of the recommended size, not the crewing
  itself. The roadmap names the board (Part
  VIII) as where crew state will be visible;
  that board does not exist yet, so the
  recommendation is visible through this slice's
  own /crewsize screen, and nothing here claims
  a board exists.
* **Malformed refuses.** An unknown coupling, an
  empty title or detail, a malformed member, an
  office outside the six formalised ones, a
  piece count under one, a duplicate case id
  anywhere in the book, and unknown keys in a
  case, a recommendation, or a sizing mapping
  all raise instead of being skipped or guessed
  at.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .crew_members import normalize_member_id
from .offices import normalize_formal_office
from .validation import ValidationError

__all__ = [
    "COUPLING_KINDS",
    "CREW_SIZING_RESOURCE",
    "CREW_SIZING_SCHEMA",
    "CREW_SIZING_SLICE",
    "MAX_CREW_SIZE",
    "PLAIN_EXPLANATION",
    "SIZE_KINDS",
    "USAGE",
    "SizingBook",
    "SizingRecommendation",
    "SizingRegistry",
    "TaskShape",
    "book_record",
    "build_book",
    "build_recommendation",
    "build_shape",
    "case_record",
    "derive_recommendation",
    "format_crew_sizing_screen",
    "format_recommendation",
    "format_shape",
    "format_shapes",
    "format_size_kinds",
    "load_crew_sizing",
    "load_crew_sizing_file",
    "normalize_coupling",
    "normalize_size_kind",
    "parse_crew_size_args",
    "plain_words",
    "recommendation_plain_words",
    "recommendation_record",
    "size_kind_for",
    "validate_book",
    "validate_recommendation",
    "validate_shape",
]

CREW_SIZING_SLICE = "M-135"

#: The packaged data resource holding the example sizing book.
CREW_SIZING_RESOURCE = "crew_sizing.yaml"

#: The schema word a sizing file must carry.
CREW_SIZING_SCHEMA = "mythic.crew_sizing/1"

#: The largest crew this layer ever recommends:
#: six pairs of hands. More is crowding, not help.
MAX_CREW_SIZE = 6

#: The two couplings a task shape can stand in:
#: tightly coupled work must be held in one head,
#: loose work splits into pieces worked at once.
COUPLING_KINDS = ("tight", "loose")

#: The size bands a recommendation falls in, by
#: its derived size: one pair of hands, a pair,
#: a crew, or the full crew of six.
SIZE_KINDS = ("solo", "pair", "crew", "full_crew")

_COUPLING_READINGS = {
    "tight": "tight",
    "tightly_coupled": "tight",
    "coupled": "tight",
    "entangled": "tight",
    "single_thread": "tight",
    "single_head": "tight",
    "loose": "loose",
    "independent": "loose",
    "parallel": "loose",
    "splittable": "loose",
    "split": "loose",
}

_SIZE_KIND_READINGS = {
    "solo": "solo",
    "one": "solo",
    "alone": "solo",
    "single": "solo",
    "pair": "pair",
    "two": "pair",
    "crew": "crew",
    "small_crew": "crew",
    "full_crew": "full_crew",
    "full": "full_crew",
    "max": "full_crew",
    "maximum": "full_crew",
}

_SHAPE_KEYS = frozenset({
    "id", "case_id", "shape_id", "lead", "member", "lead_member",
    "office", "lead_office", "title", "name", "detail", "body",
    "text", "notes", "independent_pieces", "pieces", "chunks",
    "coupling", "coupling_kind", "tightness",
    "recommended_size", "size", "crew_size",
})

_RECOMMENDATION_KEYS = frozenset({
    "case_id", "id", "shape_id", "recommended_size", "size",
    "crew_size", "kind", "band", "reason",
})

_BOOK_KEYS = frozenset({"title", "name"})

_SIZING_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "sizing_note", "guide", "cases",
})

#: The shipped example book's title, held to this
#: by the loader's example check.
_EXAMPLE_TITLE = "Crew sizing at the M-134 slice boundary"

#: The shipped example's case ids in each size
#: band, in book order, pinned by the loader, with
#: the derived size each case must recommend.
_EXAMPLE_BANDS = {
    "solo": ("tangled-single-file-fix",),
    "pair": ("docs-and-tests-split",),
    "crew": ("four-independent-slices",),
    "full_crew": ("wide-census-sweep",),
}

_EXAMPLE_SIZES = {
    "tangled-single-file-fix": 1,
    "docs-and-tests-split": 2,
    "four-independent-slices": 4,
    "wide-census-sweep": 6,
}

PLAIN_EXPLANATION = (
    "Crew sizing honesty: the app recommends a "
    "crew size by the shape of the task, and says "
    "plainly when one pair of hands beats six. A "
    "sizing case holds one task shape - how many "
    "independent pieces the work splits into, and "
    "whether it is tightly coupled or loose - and "
    "the recommended size is derived from the "
    "shape alone: tightly coupled work takes one "
    "pair of hands, loose work takes one pair per "
    "piece, up to six. This layer holds the sizing "
    "as data only; it spawns no crew, sizes no "
    "live crew and calls no model itself."
)

USAGE = (
    "Usage: /crewsize, /crewsize show, "
    "/crewsize recommend <case-id>, "
    "/crewsize case <case-id>, /crewsize solo, "
    "/crewsize pair, /crewsize crew, "
    "/crewsize full-crew, /crewsize kinds"
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


def _check_pieces(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(
            f"a task shape's independent pieces must be a "
            f"whole count, got {value!r}")
    if value < 1 or value > 99:
        raise ValueError(
            f"a task shape's independent pieces must stand "
            f"between 1 and 99, got {value!r}")
    return value


def _check_size(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(
            f"a recommended size must be a whole count, "
            f"got {value!r}")
    if value < 1 or value > MAX_CREW_SIZE:
        raise ValueError(
            f"a recommended size must stand between 1 and "
            f"{MAX_CREW_SIZE}, got {value!r}")
    return value


def normalize_coupling(value: Any) -> str:
    """The canonical coupling a word names.

    Coupling words read case-insensitively, with
    dashes read as underscores: ``tightly-coupled``,
    ``coupled`` and ``single-head`` read as tight,
    and ``independent``, ``parallel`` and
    ``splittable`` as loose. Anything else raises -
    a task shape stands in one of the two, never a
    maybe.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace("-", "_")
        if wanted in _COUPLING_READINGS:
            return _COUPLING_READINGS[wanted]
    raise ValueError(
        "a coupling must be one of %s, got %r"
        % ("/".join(COUPLING_KINDS), value))


def size_kind_for(size: Any) -> str:
    """The size band one derived size falls in."""
    count = _check_size(size)
    if count == 1:
        return "solo"
    if count == 2:
        return "pair"
    if count <= 4:
        return "crew"
    return "full_crew"


def normalize_size_kind(value: Any) -> str:
    """The canonical size band a word names.

    Band words read case-insensitively, with
    dashes read as underscores: ``one`` and
    ``single`` read as solo, ``two`` as pair,
    ``small-crew`` as crew, and ``full`` and
    ``maximum`` as full_crew. Anything else
    raises.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace("-", "_")
        if wanted in _SIZE_KIND_READINGS:
            return _SIZE_KIND_READINGS[wanted]
    raise ValueError(
        "a size kind must be one of %s, got %r"
        % ("/".join(SIZE_KINDS), value))


def _kind_words(kind: str) -> str:
    """One band's plain display words."""
    return "full-crew" if kind == "full_crew" else kind


def _size_words(size: int) -> str:
    """One derived size in plain words."""
    if size == 1:
        return "one pair of hands"
    return f"{size} pairs of hands"


def _derived_size(coupling: str, pieces: int) -> int:
    """The size one shape's coupling and pieces derive."""
    if coupling == "tight":
        return 1
    return max(1, min(pieces, MAX_CREW_SIZE))


def _pick_any(mapping: Dict[str, Any], spellings: Tuple[str, ...],
              what: str) -> Any:
    values = [mapping[s] for s in spellings if s in mapping]
    if not values:
        return None
    if any(value != values[0] for value in values[1:]):
        raise ValueError(f"a record names two different {what}")
    return values[0]


# ---------------------------------------------------------------------
# The shape: one task, and the shape it stands in.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class TaskShape:
    """One task shape in a sizing book, as data.

    ``lead`` is the M-121 member who would lead
    the task; ``office`` is the M-122 formal
    office the work fits; ``title`` names the
    task; ``detail`` is the task in plain words;
    ``independent_pieces`` counts the pieces the
    work splits into; ``coupling`` is tight when
    the work must be held in one head, loose when
    its pieces can be worked at once. The
    recommended size is never a field here: it is
    derived from this shape alone. Constructing
    one validates its shape only: whether its id
    already stands in its book is the book's
    concern.
    """

    case_id: Optional[str] = None
    lead: str = ""
    office: str = ""
    title: str = ""
    detail: str = ""
    independent_pieces: int = 1
    coupling: str = ""

    def __post_init__(self) -> None:
        if self.case_id is not None:
            object.__setattr__(
                self, "case_id", normalize_member_id(self.case_id))
        object.__setattr__(
            self, "lead", normalize_member_id(self.lead))
        object.__setattr__(
            self, "office", normalize_formal_office(self.office))
        object.__setattr__(
            self, "title", _check_short_text(self.title, "a title"))
        object.__setattr__(
            self, "detail", _check_long_text(self.detail, "a detail"))
        object.__setattr__(
            self, "independent_pieces",
            _check_pieces(self.independent_pieces))
        object.__setattr__(
            self, "coupling", normalize_coupling(self.coupling))

    def recommended_size(self) -> int:
        """The size this shape alone derives."""
        return _derived_size(self.coupling, self.independent_pieces)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "crew_sizing_case",
            "slice": CREW_SIZING_SLICE,
            "case_id": self.case_id,
            "lead": self.lead,
            "office": self.office,
            "title": self.title,
            "detail": self.detail,
            "independent_pieces": self.independent_pieces,
            "coupling": self.coupling,
        }


def validate_shape(shape: Any) -> TaskShape:
    """Validate one case into a TaskShape.

    Accepts a TaskShape or a mapping naming a
    ``lead`` (or ``member`` / ``lead_member``), an
    ``office`` (or ``lead_office``), a ``title``
    (or ``name``), a ``detail`` (or ``body`` /
    ``text`` / ``notes``), ``independent_pieces``
    (or ``pieces`` / ``chunks``), a ``coupling``
    (or ``coupling_kind`` / ``tightness``) and an
    optional ``case_id`` (or ``id`` / ``shape_id``).
    A stored recommendation named in the mapping
    (``recommended_size`` / ``size`` / ``crew_size``)
    is judged against the size the shape derives:
    any disagreement refuses, because a
    recommendation is derived, never stored.
    Naming two spellings of one field with
    different values refuses, and unknown keys
    refuse.
    """
    if isinstance(shape, TaskShape):
        return shape
    if not isinstance(shape, dict):
        raise ValueError(f"a case must be a mapping, got {shape!r}")
    unknown = set(shape) - _SHAPE_KEYS
    if unknown:
        raise ValueError(
            "unknown case keys: %s" % ", ".join(sorted(unknown)))
    lead = _pick_any(shape, ("lead", "member", "lead_member"), "leads")
    if lead is None:
        raise ValueError("a case is missing its lead")
    office = _pick_any(shape, ("office", "lead_office"), "offices")
    if office is None:
        raise ValueError("a case is missing its office")
    title = _pick_any(shape, ("title", "name"), "titles")
    if title is None:
        raise ValueError("a case is missing its title")
    detail = _pick_any(
        shape, ("detail", "body", "text", "notes"), "details")
    if detail is None:
        raise ValueError("a case is missing its detail")
    pieces = _pick_any(
        shape, ("independent_pieces", "pieces", "chunks"),
        "piece counts")
    if pieces is None:
        raise ValueError("a case is missing its independent pieces")
    coupling = _pick_any(
        shape, ("coupling", "coupling_kind", "tightness"), "couplings")
    if coupling is None:
        raise ValueError("a case is missing its coupling")
    kwargs: Dict[str, Any] = {
        "lead": lead, "office": office, "title": title,
        "detail": detail, "independent_pieces": pieces,
        "coupling": coupling}
    case_id = _pick_any(shape, ("case_id", "id", "shape_id"), "case ids")
    if case_id is not None:
        kwargs["case_id"] = case_id
    current = TaskShape(**kwargs)
    stored = _pick_any(
        shape, ("recommended_size", "size", "crew_size"),
        "recommended sizes")
    if stored is not None and _check_size(stored) != current.recommended_size():
        raise ValueError(
            "a stored recommendation disagrees with the size its "
            "shape derives - a recommendation is derived, never stored")
    return current


def build_shape(shape: Any = None, **kwargs: Any) -> TaskShape:
    """Build one validated case, from a mapping or field words."""
    if isinstance(shape, TaskShape) and not kwargs:
        return shape
    if isinstance(shape, dict) or shape is None:
        merged: Dict[str, Any] = {}
        if isinstance(shape, dict):
            merged.update(shape)
        merged.update(kwargs)
        return validate_shape(merged)
    raise ValueError(f"a case must be a mapping, got {shape!r}")


# ---------------------------------------------------------------------
# The book: the cases whole, under a title.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class SizingBook:
    """One sizing book, whole, as data.

    ``title`` names the book; ``cases`` are the
    task shapes, in file order, their ids unique
    across the book. Every recommendation is
    derived from the cases held, never stored on
    the book.
    """

    title: str = ""
    cases: Tuple[TaskShape, ...] = ()
    sizing_note: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_short_text(self.title, "a title"))
        cases = tuple(
            c if isinstance(c, TaskShape) else validate_shape(c)
            for c in self.cases)
        ids = [c.case_id for c in cases if c.case_id is not None]
        if len(set(ids)) != len(ids):
            raise ValueError("a book holds one case id twice")
        object.__setattr__(self, "cases", cases)
        if not isinstance(self.sizing_note, str):
            raise ValueError("a sizing book's note must be text")
        object.__setattr__(self, "sizing_note", self.sizing_note.strip())

    def case_for(self, case_id: Any) -> TaskShape:
        """The case one id names in this book; unknown raises."""
        wanted = normalize_member_id(case_id)
        for case in self.cases:
            if case.case_id == wanted:
                return case
        raise KeyError(f"no case in the sizing book: {wanted!r}")

    def cases_for(self, kind: Any) -> Tuple[TaskShape, ...]:
        """Every case whose derived band is one kind, in book order."""
        wanted = normalize_size_kind(kind)
        return tuple(
            c for c in self.cases
            if size_kind_for(c.recommended_size()) == wanted)

    def case_ids(self) -> Tuple[str, ...]:
        """Every held case id, in book order (id-less skipped)."""
        return tuple(c.case_id for c in self.cases if c.case_id)

    def recommendations(self) -> Tuple["SizingRecommendation", ...]:
        """Every case's derived recommendation, in book order."""
        return tuple(derive_recommendation(c) for c in self.cases)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "crew_sizing_book",
            "slice": CREW_SIZING_SLICE,
            "title": self.title,
            "case_ids": list(self.case_ids()),
            "case_count": len(self.cases),
        }


def validate_book(data: Any, *, require_example: bool = False) -> SizingBook:
    """Validate one sizing mapping into a SizingBook.

    The mapping names a ``schema`` (the sizing
    schema word), a ``guide`` mapping (its
    ``title``) and a ``cases`` list. Every case is
    validated, then the whole is judged: case ids
    unique across the book. With
    ``require_example`` the shipped example is
    held to its pinned shape: the pinned title and
    the pinned case ids in each of the four size
    bands, at their pinned derived sizes. Problems
    raise :class:`ValidationError` or ``ValueError``
    naming the problem.
    """
    if isinstance(data, SizingBook):
        return data
    if not isinstance(data, dict):
        raise ValidationError(f"a sizing book must be a mapping, got {data!r}")
    unknown = set(data) - _SIZING_KEYS
    if unknown:
        raise ValidationError(
            "unknown sizing keys: %s" % ", ".join(sorted(unknown)))
    if data.get("schema") != CREW_SIZING_SCHEMA:
        raise ValidationError(
            f"a sizing book must carry schema {CREW_SIZING_SCHEMA!r}, "
            f"got {data.get('schema')!r}")
    if "cases" not in data:
        raise ValidationError("a sizing book is missing its cases")
    raw = data["cases"]
    if not isinstance(raw, (list, tuple)):
        raise ValidationError("a sizing book's cases must be a list")
    head = data.get("guide") or {}
    if not isinstance(head, dict):
        raise ValidationError("a sizing book's guide must be a mapping")
    unknown_head = set(head) - _BOOK_KEYS
    if unknown_head:
        raise ValidationError(
            "unknown guide keys: %s" % ", ".join(sorted(unknown_head)))
    try:
        title = _pick_any(head, ("title", "name"), "titles")
        if title is None:
            raise ValidationError("a sizing book is missing its title")
        cases = tuple(validate_shape(c) for c in raw)
        note = data.get("sizing_note") or ""
        if not isinstance(note, str):
            raise ValidationError("a sizing book's note must be text")
        book = SizingBook(title=title, cases=cases, sizing_note=note)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    if require_example:
        if book.title != _EXAMPLE_TITLE:
            raise ValidationError(
                "the shipped example sizing book's title is not "
                "the pinned title")
        for kind in SIZE_KINDS:
            ids = tuple(c.case_id for c in book.cases_for(kind))
            if ids != _EXAMPLE_BANDS[kind]:
                raise ValidationError(
                    f"the shipped example sizing book's {kind} band "
                    "is not the pinned shape")
        for case_id, size in _EXAMPLE_SIZES.items():
            if book.case_for(case_id).recommended_size() != size:
                raise ValidationError(
                    f"the shipped example case {case_id} does not "
                    f"derive its pinned size {size}")
    return book


def build_book(book: Any = None, **kwargs: Any) -> SizingBook:
    """Build one validated book, from a mapping or field words."""
    if isinstance(book, SizingBook) and not kwargs:
        return book
    if isinstance(book, (list, tuple)) and not kwargs:
        raise ValueError("a book needs its title")
    if isinstance(book, dict):
        if "cases" in book or "schema" in book:
            return validate_book(book)
        merged: Dict[str, Any] = dict(book)
        merged.update(kwargs)
        return SizingBook(**merged)
    if book is None:
        return SizingBook(**kwargs)
    raise ValueError(f"a sizing book is needed, got {book!r}")


def _book_from(data: Any, *, require_example: bool) -> SizingBook:
    try:
        return validate_book(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_crew_sizing(data: Optional[Dict[str, Any]] = None) -> SizingBook:
    """Load and validate the shipped example sizing book (or *data*).

    The shipped file is held to the example check:
    the pinned title and the pinned case ids in
    each of the four size bands, so the shipped
    book covers solo, pair, crew and full-crew -
    including the case where one pair of hands
    beats six.
    """
    raw = data if data is not None else load_resource(CREW_SIZING_RESOURCE)
    return _book_from(raw, require_example=True)


def load_crew_sizing_file(path: Any) -> SizingBook:
    """Load and validate a sizing book from a file at *path*.

    Any file in the sizing shape, anywhere on
    disk, validated whole - a malformed file
    raises :class:`ValidationError` naming the
    problem, and a missing file raises
    ``FileNotFoundError``. The example check is
    not held: a real sizing book stands on its own
    shapes.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _book_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The recommendation: the size, derived from the shape alone.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class SizingRecommendation:
    """One case's recommended crew size, derived from its shape.

    ``case_id`` and ``title`` are the case's own;
    ``recommended_size`` is the derived count of
    pairs of hands; ``kind`` is the band that size
    falls in; ``reason`` is the derivation in
    plain words. The band is judged against the
    size at construction, so a recommendation can
    never name a band its size does not fall in.
    """

    case_id: Optional[str] = None
    title: str = ""
    recommended_size: int = 1
    kind: str = ""
    reason: str = ""

    def __post_init__(self) -> None:
        if self.case_id is not None:
            object.__setattr__(
                self, "case_id", normalize_member_id(self.case_id))
        object.__setattr__(
            self, "title", _check_short_text(self.title, "a title"))
        size = _check_size(self.recommended_size)
        object.__setattr__(self, "recommended_size", size)
        kind = normalize_size_kind(self.kind)
        if kind != size_kind_for(size):
            raise ValueError(
                "a recommendation's band disagrees with its size - "
                "a band is read off the size, never named apart from it")
        object.__setattr__(self, "kind", kind)
        object.__setattr__(
            self, "reason", _check_long_text(self.reason, "a reason"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "crew_sizing_recommendation",
            "slice": CREW_SIZING_SLICE,
            "case_id": self.case_id,
            "title": self.title,
            "recommended_size": self.recommended_size,
            "kind": self.kind,
            "reason": self.reason,
        }


def _reason_for(shape: TaskShape, size: int) -> str:
    """The derivation of one size, in plain words."""
    if shape.coupling == "tight":
        return (
            "One pair of hands beats six here: the work is "
            "tightly coupled, so extra hands would collide "
            "and wait instead of helping.")
    if size == 1:
        return (
            "The work is one piece that does not split, so "
            "one pair of hands holds it whole.")
    if shape.independent_pieces > size:
        return (
            f"The work splits into {shape.independent_pieces} "
            f"independent pieces, but six pairs of hands is "
            f"the honest crew: more would crowd the same ground.")
    return (
        f"The work splits into {shape.independent_pieces} "
        f"independent pieces, so {_size_words(size)} can "
        f"work at once without waiting on each other.")


def derive_recommendation(source: Any) -> SizingRecommendation:
    """The recommendation one shape yields, derived from it alone.

    Accepts a TaskShape. Tightly coupled work
    derives one pair of hands however many pieces
    it names; loose work derives one pair of hands
    per independent piece, capped at six. An
    unnamed case refuses: a recommendation names
    the case it recommends for.
    """
    shape = source if isinstance(source, TaskShape) else build_shape(source)
    if shape.case_id is None:
        raise ValueError(
            "a recommendation names its case by id; a case "
            "without an id cannot be recommended for")
    size = _derived_size(shape.coupling, shape.independent_pieces)
    return SizingRecommendation(
        case_id=shape.case_id, title=shape.title,
        recommended_size=size, kind=size_kind_for(size),
        reason=_reason_for(shape, size))


def validate_recommendation(
        recommendation: Any, shape: Any = None) -> SizingRecommendation:
    """Validate one recommendation into a SizingRecommendation.

    Accepts a SizingRecommendation or a mapping
    naming a ``case_id`` (or ``id`` / ``shape_id``),
    a ``recommended_size`` (or ``size`` /
    ``crew_size``) and optionally a ``kind`` (or
    ``band``) and a ``reason``. When *shape* is
    given, the recommendation is also judged
    against the recommendation that shape derives:
    any disagreement refuses, because a
    recommendation is derived, never stored.
    """
    if isinstance(recommendation, SizingRecommendation):
        current = recommendation
    elif isinstance(recommendation, dict):
        unknown = set(recommendation) - _RECOMMENDATION_KEYS
        if unknown:
            raise ValueError(
                "unknown recommendation keys: %s"
                % ", ".join(sorted(unknown)))
        case_id = _pick_any(
            recommendation, ("case_id", "id", "shape_id"), "case ids")
        size = _pick_any(
            recommendation, ("recommended_size", "size", "crew_size"),
            "recommended sizes")
        if size is None:
            raise ValueError("a recommendation is missing its size")
        kind = _pick_any(recommendation, ("kind", "band"), "size kinds")
        if kind is None:
            kind = size_kind_for(size)
        if shape is None:
            raise ValueError(
                "a stored recommendation names no title or reason "
                "of its own - judge it against its shape")
        derived = derive_recommendation(shape)
        current = SizingRecommendation(
            case_id=case_id if case_id is not None else derived.case_id,
            title=derived.title, recommended_size=size, kind=kind,
            reason=recommendation.get("reason") or derived.reason)
    else:
        raise ValueError(
            f"a recommendation must be a mapping, got {recommendation!r}")
    if shape is not None:
        derived = derive_recommendation(shape)
        if current != derived:
            raise ValueError(
                "a stored recommendation disagrees with the "
                "recommendation its shape derives - a "
                "recommendation is derived, never stored")
    return current


def build_recommendation(
        recommendation: Any = None, **kwargs: Any) -> SizingRecommendation:
    """Build one validated recommendation, from a mapping or words."""
    if isinstance(recommendation, SizingRecommendation) and not kwargs:
        return recommendation
    if isinstance(recommendation, dict) or recommendation is None:
        merged: Dict[str, Any] = {}
        if isinstance(recommendation, dict):
            merged.update(recommendation)
        merged.update(kwargs)
        return validate_recommendation(merged)
    raise ValueError(
        f"a recommendation must be a mapping, got {recommendation!r}")


# ---------------------------------------------------------------------
# The registry model: one book held case by case, in order.
# ---------------------------------------------------------------------


class SizingRegistry:
    """One session's sizing book, held case by case."""

    def __init__(self, book: Any = None) -> None:
        self._title: Optional[str] = None
        self._cases: Dict[str, TaskShape] = {}
        self._order: list = []
        self._next_case = 1
        if book is not None:
            self.register_book(book)

    def _fresh_case_id(self, held_ids: Any) -> str:
        while f"case-{self._next_case}" in held_ids:
            self._next_case += 1
        fresh = f"case-{self._next_case}"
        self._next_case += 1
        return fresh

    def register_case(self, shape: Any) -> TaskShape:
        """Register one case into the held book.

        A case with no id is given a deterministic
        ``case-N`` id. A duplicate case id refuses.
        The held book's title must already stand
        (register a book first, or hold cases under
        a book registered whole).
        """
        validated = build_shape(shape)
        if validated.case_id is not None \
                and validated.case_id in self._cases:
            raise ValueError(
                f"a case named {validated.case_id!r} already exists")
        if validated.case_id is None:
            validated = replace(
                validated,
                case_id=self._fresh_case_id(set(self._cases)))
        self._cases[validated.case_id] = validated
        self._order.append(validated.case_id)
        return validated

    def register_book(self, book: Any) -> SizingBook:
        """Register every case of one book, in order.

        The first book held sets the title; a later
        book under a different title refuses, as
        does a book whose case ids already stand
        here.
        """
        validated = build_book(book)
        if self._title is not None and validated.title != self._title:
            raise ValueError(
                "this registry already holds a sizing book under "
                "a different title")
        for case in validated.cases:
            if case.case_id is not None \
                    and case.case_id in self._cases:
                raise ValueError(
                    f"a case named {case.case_id!r} already exists")
        self._title = validated.title
        for case in validated.cases:
            self.register_case(case)
        return self.book()

    def get_case(self, case_id: Any) -> TaskShape:
        """The case one id names among the held cases."""
        wanted = normalize_member_id(case_id)
        if wanted not in self._cases:
            raise KeyError(f"unknown case: {wanted!r}")
        return self._cases[wanted]

    def list_cases(self) -> Tuple[TaskShape, ...]:
        """Every held case, in the order they were held."""
        return tuple(self._cases[i] for i in self._order)

    def cases_for(self, kind: Any) -> Tuple[TaskShape, ...]:
        """Every held case in one size band, in held order."""
        wanted = normalize_size_kind(kind)
        return tuple(
            c for c in self.list_cases()
            if size_kind_for(c.recommended_size()) == wanted)

    def book(self) -> SizingBook:
        """The held cases as one validated sizing book."""
        if self._title is None:
            raise ValueError("no sizing book is held yet")
        return SizingBook(title=self._title, cases=self.list_cases())

    def recommendation_for(self, case_id: Any) -> SizingRecommendation:
        """The held case's derived recommendation."""
        return derive_recommendation(self.get_case(case_id))

    def recommendations(self) -> Tuple[SizingRecommendation, ...]:
        """Every held case's recommendation, derived at call time."""
        return tuple(derive_recommendation(c) for c in self.list_cases())


# ---------------------------------------------------------------------
# Sizing news, shaped as session records.
# ---------------------------------------------------------------------


def case_record(shape: Any) -> Dict[str, Any]:
    """The session-news record of one case."""
    current = shape if isinstance(shape, TaskShape) else build_shape(shape)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.lead} sizes {current.title}: "
        f"{current.coupling}, {current.independent_pieces} piece(s).")
    return record


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one book."""
    current = book if isinstance(book, SizingBook) else build_book(book)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Sizing book {current.title}: {record['case_count']} "
        f"task shape(s) stand sized.")
    return record


def recommendation_record(
        recommendation: Any, shape: Any = None) -> Dict[str, Any]:
    """The session-news record of one recommendation.

    With *shape* given, the recommendation is
    first judged against the recommendation that
    shape derives.
    """
    current = validate_recommendation(recommendation, shape)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.title}: {_size_words(current.recommended_size)} "
        f"({_kind_words(current.kind)}). {current.reason}")
    return record


def plain_words(shape: Any) -> str:
    """One case, in one plain sentence."""
    current = shape if isinstance(shape, TaskShape) else build_shape(shape)
    return (
        f"{current.lead} - {current.title} "
        f"({current.coupling}, {current.independent_pieces} piece(s)): "
        f"{current.detail}")


def recommendation_plain_words(source: Any) -> str:
    """Recommendations in plain words: every case, in full.

    Accepts a SizingRecommendation, a TaskShape, a
    SizingBook or a SizingRegistry. Each case names
    its derived size and its reason, so the solo
    case says plainly that one pair of hands beats
    six - nothing is hidden and nothing is
    invented.
    """
    if isinstance(source, SizingRecommendation):
        recs = (source,)
        title = None
    elif isinstance(source, TaskShape):
        recs = (derive_recommendation(source),)
        title = None
    elif isinstance(source, (SizingBook, SizingRegistry)):
        book = source.book() if isinstance(
            source, SizingRegistry) else source
        recs = book.recommendations()
        title = book.title
    else:
        raise ValueError(f"a sizing source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    for rec in recs:
        lines.append(
            f"{rec.title}: {_size_words(rec.recommended_size)} "
            f"({_kind_words(rec.kind)}) - {rec.reason}")
    return "\n".join(lines)


# ---------------------------------------------------------------------
# Screens: the formatters and the shared /crewsize grammar.
# ---------------------------------------------------------------------


def _source_book(source: Any) -> SizingBook:
    if source is None:
        return load_crew_sizing()
    if isinstance(source, SizingRegistry):
        return source.book()
    if isinstance(source, SizingBook):
        return source
    raise ValueError(f"a sizing book is needed, got {source!r}")


def format_shape(shape: Any) -> str:
    """One case as a screen line, with its derived size."""
    current = shape if isinstance(shape, TaskShape) else build_shape(shape)
    rec = derive_recommendation(current)
    return (
        f"{current.lead} / {current.case_id or '-'} "
        f"[{_kind_words(rec.kind)}, "
        f"{_size_words(rec.recommended_size)}]: {current.title} - "
        f"{current.detail}")


def format_shapes(source: Any = None, kind: Any = None) -> str:
    """Cases of one book, in book order.

    With *kind* given, only the cases whose
    derived band is that kind are shown.
    """
    book = _source_book(source)
    cases = book.cases if kind is None else book.cases_for(kind)
    lines = [format_shape(case) for case in cases]
    if not lines:
        lines.append("No task shapes stand sized.")
    return "\n".join(lines)


def format_recommendation(source: Any = None) -> str:
    """The recommendations of one book as screen lines, case by case."""
    book = _source_book(source)
    lines = [f"Sizing for {book.title}:"]
    for case in book.cases:
        rec = derive_recommendation(case)
        lines.append(
            f"{_kind_words(rec.kind)} ({rec.recommended_size}): "
            f"{case.title} - {rec.reason}")
    if len(lines) == 1:
        lines.append("Nothing here.")
    return "\n".join(lines)


def format_size_kinds() -> str:
    """The four size bands, in order, as one line."""
    return "Size kinds: " + ", ".join(
        _kind_words(kind) for kind in SIZE_KINDS)


def format_crew_sizing_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /crewsize.

    With nothing named, the shipped example sizing
    book is shown - the example this slice ships -
    so the screen is never empty.
    """
    book = _source_book(source)
    lines = ["Crew sizing honesty (M-135) - " + PLAIN_EXPLANATION, ""]
    lines.append(recommendation_plain_words(book))
    lines.append("")
    lines.append(format_recommendation(book))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_crew_size_args(args: Any) -> Tuple[str, Optional[str]]:
    """Parse the /crewsize grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    sizing book; ``recommend <case-id>`` shows one
    case's derived recommendation; ``case
    <case-id>`` shows one case; a band word
    (``solo`` / ``pair`` / ``crew`` / ``full-crew``)
    shows that band; ``kinds`` lists the four size
    bands. Anything else is a usage error naming
    the grammar. Returns ``(action, value-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() in ("show", "list"):
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head == "kinds" and len(words) == 1:
        return ("kinds", None)
    if head in ("recommend", "case") and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if len(words) == 1:
        try:
            return ("band", normalize_size_kind(words[0]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
