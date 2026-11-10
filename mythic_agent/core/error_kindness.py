"""Error kindness (All-Features roadmap slice M-183).

Part VIII - The Beautiful Face - builds here. The
roadmap's words: *every error states what happened,
what it means, and the most likely fix in plain
words - technical trace one key away; no raw stack
ever lands on a user unaccompanied.*

What already ships, and what this slice adds:

* The shipped tree already raises errors on every
  road - refused pushes, missing files, broken
  tests, calls that time out - and most of them
  land on the user as a raw stack or a bare code,
  with no plain telling of what happened, what it
  means, or what to try first. What nothing held
  is the *kindness* an error is owed, as checkable
  data: one held error record carrying what
  happened, what it means and the most likely fix
  in plain words, with its technical trace held
  folded behind one named key, reachable by that
  key and never shown by default. This slice is
  that book, in its own module; the shipped error
  roads stand untouched behind seams, and this
  layer holds errors in their shape, never
  rewriting them.
* The plain telling is DERIVED from the held
  error's own fields at call time: the telling's
  three lines are the error's own happened,
  meaning and fix, spoken under their plain
  headings. There is no second hand-written plain
  copy anywhere in this layer that could drift
  from the facts: the words a user reads are the
  error's own words, carried whole.
* The ruling stands as data (:data:`NO_RAW_STACK_RULE`):
  no raw stack ever lands on a user unaccompanied.
  An error record that claims to stand whole
  without its plain telling and its named fix -
  a record naming itself bare, standalone or
  unaccompanied - refuses BY NAME, and an error
  naming no fix refuses by name too: the fix is
  part of what an error is, not an ornament.
* The technical trace stands FOLDED: a rendering
  carries the trace lines as folded data,
  reachable by the one named trace action
  (:func:`trace_rendering`, the ``trace`` keypress
  of the /errors grammar), and the folded lines
  are the error's own trace whole - never deleted,
  never summarised, never shown by default. An
  error held with no trace folded stands named in
  its gaps and does not stand whole: this layer
  invents no trace for it.
* The shipped data file (``mythic_agent/data/
  error_kindness.yaml``) holds one example book
  in exactly the shape a real error file takes,
  a loader reads an error file anywhere on disk,
  errors and views are shaped as session news,
  and a small in-memory registry holds records
  one by one. The agent layer owns holding an
  error book for a session and rendering its
  errors kindly. This layer reaches no live road:
  it fixes nothing and sends nothing - it tells.

Honesty rules, enforced here and pinned by tests:

* **Told plainly, from its own fields.** The
  plain telling is derived from the held error's
  happened, meaning and fix alone; nothing is
  added and nothing is dropped.
* **No raw stack unaccompanied.** A bare or
  standalone error claim refuses by name; every
  rendering carries the plain telling with it.
* **Folded, never deleted.** The trace stands
  folded behind the trace keypress; it is not
  dropped, summarised or rewritten.
* **A missing trace is honest.** An error with
  no trace folded names that gap and does not
  stand whole; no trace is invented for it.
* **The fix is named.** An error naming no most
  likely fix refuses by name - kindness without
  a next step is only half a telling.
"""

from __future__ import annotations

__all__ = [
    "ERROR_KINDS",
    "ERROR_KINDNESS_RESOURCE",
    "ERROR_KINDNESS_SCHEMA",
    "ERROR_KINDNESS_SLICE",
    "NO_RAW_STACK_RULE",
    "PLAIN_EXPLANATION",
    "THE_ERROR_KINDNESS_SLICE",
    "TRACE_ACTION",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "Any",
    "Dict",
    "List",
    "Optional",
    "ErrorBook",
    "ErrorKindnessRegistry",
    "ErrorPanel",
    "ErrorPanelRow",
    "ErrorRecord",
    "ErrorRendering",
    "ErrorVerdict",
    "ErrorView",
    "KindCount",
    "book_record",
    "build_book",
    "build_error",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "derive_panel",
    "derive_verdict",
    "error_gaps",
    "error_passes",
    "error_plain_words",
    "error_record",
    "errors_for_kind",
    "format_book",
    "format_error",
    "format_error_kindness_screen",
    "format_panel",
    "format_rendering",
    "format_verdict",
    "format_view",
    "inspect_error_source",
    "load_error_kindness",
    "load_error_kindness_file",
    "normalize_kind",
    "normalize_view_filter",
    "panel_plain_words",
    "panel_record",
    "parse_error_kindness_args",
    "passing_errors",
    "plain_lines",
    "plain_words",
    "render_error",
    "rendering_record",
    "segment_of",
    "shown_errors",
    "technical_lines",
    "total_errors",
    "trace_rendering",
    "validate_book",
    "validate_error",
    "validate_panel",
    "validate_row",
    "validate_verdict",
    "validate_view",
    "verdict_plain_words",
    "verdict_record",
    "view_plain_words",
    "view_record",
]

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

ERROR_KINDNESS_SCHEMA = "mythic.error_kindness/1"
ERROR_KINDNESS_SLICE = "M-183"
THE_ERROR_KINDNESS_SLICE = ERROR_KINDNESS_SLICE
ERROR_KINDNESS_RESOURCE = "error_kindness.yaml"
TRACE_ACTION = "trace"
ERROR_KINDS = (
    "refused", "missing", "broken", "timeout", "mismatch", "denied")
VIEW_FILTERS = ("all", "whole", "open")
VERDICT_WORDS = ("open", "strained", "shut")
NO_RAW_STACK_RULE = (
    "no raw stack ever lands on a user unaccompanied: every error "
    "is told in plain words - what happened, what it means, and "
    "the most likely fix - with its technical trace folded behind "
    "the trace key, one key away and never shown by default")
PLAIN_EXPLANATION = (
    "Error kindness (M-183): every error states what happened, "
    "what it means, and the most likely fix in plain words - "
    "technical trace one key away; no raw stack ever lands on "
    "a user unaccompanied.")
USAGE = (
    "Usage: /errors | /errors error <error-id> | "
    "/errors trace <error-id> | /errors view <view-id> | "
    "/errors kind <kind> | /errors panel | /errors verdict")

_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_ERROR_KEYS = frozenset({
    "error_id", "seq", "kind", "title", "happened", "meaning",
    "fix", "trace", "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "passes", "gaps", "segment", "plain_lines", "telling",
    "verdict", "trace_shown", "folded", "whole"})
_BARE_KEYS = ("unaccompanied", "bare", "standalone", "accompanied")


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
    for key in _BARE_KEYS:
        if key in mapping:
            raise ValueError(
                f"{what} claims to stand unaccompanied ({key!r} is "
                f"named on it): {NO_RAW_STACK_RULE}")
    for key in mapping:
        if key in _DERIVED_KEYS:
            raise ValueError(
                f"{what} carries {key!r}, which is derived from its "
                f"own fields and never stored")
        if key not in allowed:
            raise ValueError(f"{what} carries unknown field {key!r}")


def normalize_kind(value: Any) -> str:
    kind = _clean_text(value, "an error kind").lower()
    if kind not in ERROR_KINDS:
        raise ValueError(
            f"error kind {kind!r} is not one of the held kinds: "
            + ", ".join(ERROR_KINDS))
    return kind


def normalize_view_filter(value: Any) -> str:
    view_filter = _clean_text(value, "a view filter").lower()
    if view_filter not in VIEW_FILTERS:
        raise ValueError(
            f"view filter {view_filter!r} is not one of the held "
            f"filters: " + ", ".join(VIEW_FILTERS))
    return view_filter


# ---------------------------------------------------------------------
# The held error: what happened, what it means, the most likely fix,
# and its technical trace folded behind the trace key.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ErrorRecord:
    """One error, held whole and told kindly.

    The error stands under its title with what
    happened, what it means and the most likely
    fix in plain words - the three parts of its
    telling, each the error's own words - and its
    technical trace lines, held folded as data.
    An error naming no fix is not an error this
    book holds: it refuses by name. An error with
    no trace folded is held honestly, stands named
    in its gaps, and does not stand whole.
    """

    error_id: str
    seq: int
    kind: str
    title: str
    happened: str
    meaning: str
    fix: str
    trace: Tuple[str, ...] = ()
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "error_id", _clean_text(self.error_id, "an error id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(self, "kind", normalize_kind(self.kind))
        object.__setattr__(
            self, "title", _clean_text(self.title, "an error title"))
        object.__setattr__(
            self, "happened",
            _clean_text(self.happened, "what happened"))
        object.__setattr__(
            self, "meaning", _clean_text(self.meaning, "what it means"))
        if not isinstance(self.fix, str) or not self.fix.strip():
            raise ValueError(
                f"error {self.error_id!r} names no fix: every error "
                f"names the most likely fix in plain words")
        object.__setattr__(self, "fix", self.fix.strip())
        object.__setattr__(
            self, "trace", _check_lines(self.trace, "the trace"))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an error detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.error_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "error_id": self.error_id, "seq": self.seq,
            "kind": self.kind, "title": self.title,
            "happened": self.happened, "meaning": self.meaning,
            "fix": self.fix, "trace": list(self.trace),
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_error_ref(value: Any) -> ErrorRecord:
    if not isinstance(value, ErrorRecord):
        raise ValueError("an error must be an ErrorRecord")
    return value


def validate_error(error: Any) -> ErrorRecord:
    return _check_error_ref(error)


def build_error(error: Any = None, **kwargs: Any) -> ErrorRecord:
    """Build one held error from a mapping or fields."""
    if error is None:
        data = dict(kwargs)
    elif isinstance(error, ErrorRecord):
        if kwargs:
            raise ValueError("an error stands whole or by fields, not both")
        return error
    elif isinstance(error, dict):
        data = dict(error)
        data.update(kwargs)
    else:
        raise ValueError("an error must be a mapping or an ErrorRecord")
    _needed(data, _ERROR_KEYS, "an error")
    if "fix" not in data or data.get("fix") is None or (
            isinstance(data.get("fix"), str)
            and not data["fix"].strip()):
        raise ValueError(
            "an error names no fix: every error names the most "
            "likely fix in plain words")
    return ErrorRecord(
        error_id=data.get("error_id"), seq=data.get("seq"),
        kind=data.get("kind"), title=data.get("title"),
        happened=data.get("happened"), meaning=data.get("meaning"),
        fix=data.get("fix"), trace=data.get("trace") or (),
        detail=data.get("detail"), **_provenance(data))


def error_gaps(error: Any) -> Tuple[str, ...]:
    """The gaps that keep an error from standing whole."""
    checked = _check_error_ref(error)
    return () if checked.trace else ("trace",)


def error_passes(error: Any) -> bool:
    return not error_gaps(error)


def plain_lines(error: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the error's own fields."""
    checked = _check_error_ref(error)
    return (
        f"What happened: {checked.happened}",
        f"What it means: {checked.meaning}",
        f"The most likely fix: {checked.fix}",
    )


def technical_lines(error: Any) -> Tuple[str, ...]:
    return _check_error_ref(error).trace


def segment_of(error: Any) -> str:
    checked = _check_error_ref(error)
    gaps = error_gaps(checked)
    return (
        f"{checked.error_id}: {checked.kind} says "
        f"'{checked.happened}' - plainly: '{checked.meaning}' - "
        f"fix: '{checked.fix}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The rendering: the plain telling spoken, the trace folded.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ErrorRendering:
    """One error rendered kindly.

    The rendering carries the plain telling -
    derived from the error's own fields - and the
    error's trace lines as folded data. ``folded``
    says whether the trace stands folded (the
    default telling) or stands shown whole by the
    one named trace action. The trace is never
    deleted either way.
    """

    error_id: str
    plain_lines: Tuple[str, ...]
    trace_lines: Tuple[str, ...]
    folded: bool = True
    action: str = TRACE_ACTION

    def to_record(self) -> Dict[str, Any]:
        return {
            "error_id": self.error_id,
            "plain_lines": list(self.plain_lines),
            "trace_lines": list(self.trace_lines),
            "folded": self.folded, "action": self.action,
        }


def render_error(error: Any) -> ErrorRendering:
    """Render one error kindly: told plainly, trace folded."""
    checked = _check_error_ref(error)
    return ErrorRendering(
        error_id=checked.error_id, plain_lines=plain_lines(checked),
        trace_lines=checked.trace, folded=True)


def trace_rendering(rendering: Any) -> ErrorRendering:
    """Walk the one named trace action: the trace, whole.

    The unfolded rendering carries the same plain
    telling and the same trace lines - nothing is
    added and nothing is rewritten; the trace
    simply stands shown instead of folded.
    """
    if not isinstance(rendering, ErrorRendering):
        raise ValueError("a rendering must be an ErrorRendering")
    return ErrorRendering(
        error_id=rendering.error_id,
        plain_lines=rendering.plain_lines,
        trace_lines=rendering.trace_lines, folded=False)


def inspect_error_source(piece: Any) -> Dict[str, Any]:
    """Name what one error source piece is, without judging it."""
    if isinstance(piece, ErrorRecord):
        return {"kind": "error", "error_id": piece.error_id}
    if isinstance(piece, dict):
        if "error_id" in piece:
            return {"kind": "error", "error_id": piece.get("error_id")}
        if "view_id" in piece:
            return {"kind": "view", "view_id": piece.get("view_id")}
    return {"kind": "unknown", "error_id": None}


# ---------------------------------------------------------------------
# The held view: which errors a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ErrorView:
    """A view over the book: every error, the whole ones, the open."""

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


def _check_view_ref(value: Any) -> ErrorView:
    if not isinstance(value, ErrorView):
        raise ValueError("a view must be an ErrorView")
    return value


def validate_view(view: Any) -> ErrorView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> ErrorView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, ErrorView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an ErrorView")
    _needed(data, _VIEW_KEYS, "a view")
    return ErrorView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ErrorPanelRow:
    item_id: str
    kind: str
    label: str
    segment: str
    recorded_on: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id, "kind": self.kind,
            "label": self.label, "segment": self.segment,
            "recorded_on": self.recorded_on,
        }


def _row_for_error(error: ErrorRecord) -> ErrorPanelRow:
    return ErrorPanelRow(
        item_id=error.error_id, kind=error.kind, label=error.title,
        segment=segment_of(error), recorded_on=error.recorded_on)


def _check_row_ref(value: Any) -> ErrorPanelRow:
    if not isinstance(value, ErrorPanelRow):
        raise ValueError("a panel row must be an ErrorPanelRow")
    return value


def validate_row(row: Any, error: Any = None) -> ErrorPanelRow:
    checked = _check_row_ref(row)
    if error is not None:
        derived = _row_for_error(_check_error_ref(error))
        if checked != derived:
            raise ValueError(
                f"panel row {checked.item_id!r} does not agree with "
                f"the row derived from its error")
    return checked


def build_row(row: Any = None, error: Any = None,
              **kwargs: Any) -> ErrorPanelRow:
    if error is not None:
        derived = _row_for_error(_check_error_ref(error))
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            ErrorPanelRow(**kwargs))
        return validate_row(built, error)
    if isinstance(row, ErrorPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        return ErrorPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            kind=normalize_kind(data.get("kind")),
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return ErrorPanelRow(**kwargs)
    raise ValueError("a panel row must be a mapping or an ErrorPanelRow")


@dataclass(frozen=True)
class KindCount:
    kind: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"kind": self.kind, "items": self.items}


def _kind_counts(rows: Tuple[ErrorPanelRow, ...]
                 ) -> Tuple[KindCount, ...]:
    counts: List[KindCount] = []
    for kind in ERROR_KINDS:
        number = sum(1 for row in rows if row.kind == kind)
        if number:
            counts.append(KindCount(kind=kind, items=number))
    return tuple(counts)


def _panel_account(total_items: int, total_shown: int,
                   passing_shown: int,
                   kind_counts: Tuple[KindCount, ...],
                   view_filter: str, as_of: str) -> Tuple[str, ...]:
    kinds = ", ".join(
        f"{count.kind} {count.items}" for count in kind_counts) or "none"
    return (
        f"The error book holds {total_items} errors as of {as_of}: "
        f"the view '{view_filter}' shows {total_shown} of them: "
        f"{kinds}; {passing_shown} of the shown errors stand whole.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its error's own fields - "
        "what happened, what it means and the most likely fix - "
        "and no judgement is stored on any error.",
        "Every error is told plainly, and its technical trace "
        "stands folded behind the trace keypress, never shown "
        "by default and never deleted. An error with no trace "
        "folded stands named in its gaps and does not stand "
        "whole.",
    )


@dataclass(frozen=True)
class ErrorPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[ErrorPanelRow, ...]
    total_items: int
    total_shown: int
    kind_counts: Tuple[KindCount, ...]
    as_of: str
    account: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "panel_id": self.panel_id, "view_id": self.view_id,
            "view_filter": self.view_filter,
            "rows": [row.to_record() for row in self.rows],
            "total_items": self.total_items,
            "total_shown": self.total_shown,
            "kind_counts": [c.to_record() for c in self.kind_counts],
            "as_of": self.as_of, "account": list(self.account),
        }


def _held_errors(source: Any) -> Tuple[ErrorRecord, ...]:
    return _source_book(source).errors


def _resolve_view(source: Any, view: Any) -> ErrorView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, ErrorView):
        return view
    return book.view_for(view)


def shown_errors(source: Any, view: Any = None) -> Tuple[ErrorRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.errors
    if resolved.view_filter == "whole":
        return tuple(e for e in book.errors if error_passes(e))
    return tuple(e for e in book.errors if not error_passes(e))


def errors_for_kind(source: Any, kind: Any) -> Tuple[ErrorRecord, ...]:
    wanted = normalize_kind(kind)
    return tuple(
        e for e in _source_book(source).errors if e.kind == wanted)


def passing_errors(source: Any) -> Tuple[ErrorRecord, ...]:
    return tuple(
        e for e in _source_book(source).errors if error_passes(e))


def total_errors(source: Any) -> int:
    return len(_source_book(source).errors)


def derive_panel(source: Any, view: Any = None) -> ErrorPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_errors(book, resolved)
    rows = tuple(_row_for_error(error) for error in shown)
    counts = _kind_counts(rows)
    as_of = max((e.recorded_on for e in book.errors), default="")
    passing = sum(1 for e in shown if error_passes(e))
    return ErrorPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.errors), total_shown=len(shown),
        kind_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.errors), len(shown), passing, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> ErrorPanel:
    if not isinstance(value, ErrorPanel):
        raise ValueError("a panel must be an ErrorPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> ErrorPanel:
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
                     "total_shown", "kind_counts", "as_of", "account"):
            if getattr(checked, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {checked.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return checked


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> ErrorPanel:
    if isinstance(panel, ErrorPanel):
        if kwargs:
            raise ValueError("a panel stands whole or by fields, not both")
        return validate_panel(panel, source)
    if isinstance(panel, dict):
        data = dict(panel)
        data.update(kwargs)
        rows = tuple(build_row(row) for row in data.get("rows") or ())
        counts = tuple(
            KindCount(kind=normalize_kind(c.get("kind")),
                      items=_check_count(c.get("items"), "a kind count"))
            for c in data.get("kind_counts") or ()
            if isinstance(c, dict))
        built = ErrorPanel(
            panel_id=_clean_text(data.get("panel_id"), "a panel id"),
            view_id=data.get("view_id"),
            view_filter=normalize_view_filter(data.get("view_filter")),
            rows=rows,
            total_items=_check_count(
                data.get("total_items"), "a total_items count"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            kind_counts=counts,
            as_of=_clean_text(data.get("as_of"), "an as_of day"),
            account=_check_lines(data.get("account"), "the account"))
        return validate_panel(built, source)
    if panel is None and source is not None:
        return derive_panel(source, kwargs.get("view"))
    raise ValueError("a panel must be a mapping, an ErrorPanel, or derived")


def _verdict_word(total_shown: int, passing_shown: int) -> str:
    if total_shown > 0 and passing_shown == total_shown:
        return "open"
    if passing_shown == 0:
        return "shut"
    return "strained"


@dataclass(frozen=True)
class ErrorVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> ErrorVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_errors(book, resolved)
    passing = sum(1 for e in shown if error_passes(e))
    latest = max((e.recorded_on for e in shown), default="")
    return ErrorVerdict(
        verdict=_verdict_word(len(shown), passing),
        view_id=resolved.view_id, total_shown=len(shown),
        passing_shown=passing, latest_on=latest)


def _check_verdict_ref(value: Any) -> ErrorVerdict:
    if not isinstance(value, ErrorVerdict):
        raise ValueError("a verdict must be an ErrorVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> ErrorVerdict:
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
                  **kwargs: Any) -> ErrorVerdict:
    if isinstance(verdict, ErrorVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = ErrorVerdict(
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
        "a verdict must be a mapping, an ErrorVerdict, or derived")


# ---------------------------------------------------------------------
# The book: errors and views held together, one pinned panel at most
# per telling, and no verdict ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ErrorBook:
    title: str
    errors: Tuple[ErrorRecord, ...] = ()
    views: Tuple[ErrorView, ...] = ()
    panels: Tuple[ErrorPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        errors = tuple(_check_error_ref(e) for e in self.errors)
        views = tuple(_check_view_ref(v) for v in self.views)
        panels = tuple(_check_panel_ref(p) for p in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for error in errors:
            if error.error_id in seen_ids:
                raise ValueError(
                    f"two errors stand under id {error.error_id!r}")
            if error.seq in seen_seqs:
                raise ValueError(
                    f"two errors stand at sequence {error.seq}")
            seen_ids.add(error.error_id)
            seen_seqs.add(error.seq)
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
        object.__setattr__(
            self, "errors", tuple(sorted(errors, key=lambda e: e.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.errors + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(e.error_id for e in self.errors) + tuple(
            v.view_id for v in self.views)

    def error_ids(self) -> Tuple[str, ...]:
        return tuple(e.error_id for e in self.errors)

    def error_for(self, error_id: Any) -> ErrorRecord:
        wanted = _clean_text(error_id, "an error id")
        for error in self.errors:
            if error.error_id == wanted:
                return error
        raise KeyError(f"no error named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> ErrorView:
        wanted = _clean_text(view_id, "a view id")
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no view named {wanted!r} stands in this book")

    def item_for(self, item_id: Any) -> Any:
        wanted = _clean_text(item_id, "an item id")
        for error in self.errors:
            if error.error_id == wanted:
                return error
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "errors": [e.to_record() for e in self.errors],
            "views": [v.to_record() for v in self.views],
            "panels": [p.to_record() for p in self.panels],
        }


def _judge_book_panels(book: ErrorBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: ErrorBook) -> None:
    if book.title != "Error kindness at the M-182 slice boundary":
        raise ValueError("the shipped example book carries another title")
    if len(book.errors) != 6 or len(book.views) != 2:
        raise ValueError(
            "the shipped example book must hold six errors and two views")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m182-boundary":
        raise ValueError("the pinned panel is panel-m182-boundary")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "strained" or verdict.passing_shown != 4:
        raise ValueError(
            "the shipped example book's verdict must stand strained "
            "at four whole of six")


def validate_book(data: Any, *, require_example: bool = False) -> ErrorBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, ErrorBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("an error book must be a mapping")
    for key in _BARE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims to stand unaccompanied ({key!r} is "
                f"named on it): {NO_RAW_STACK_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its errors under a view")
    if data.get("schema") is not None and (
            data["schema"] != ERROR_KINDNESS_SCHEMA):
        raise ValueError(
            f"a book's schema must be {ERROR_KINDNESS_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != ERROR_KINDNESS_SLICE):
        raise ValueError(
            f"a book's slice must be {ERROR_KINDNESS_SLICE!r}")
    guide = data.get("guide") or {}
    if not isinstance(guide, dict):
        raise ValueError("a book's guide must be a mapping")
    title = guide.get("title") or data.get("title")
    errors = tuple(build_error(e) for e in data.get("errors") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    book = ErrorBook(title=title, errors=errors, views=views, panels=())
    panels = tuple(
        build_panel(p, book) for p in data.get("panels") or ())
    book = ErrorBook(
        title=book.title, errors=book.errors, views=book.views,
        panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> ErrorBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (ErrorBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an ErrorBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> ErrorBook:
    return validate_book(data, require_example=require_example)


def load_error_kindness(
        data: Optional[Dict[str, Any]] = None) -> ErrorBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(ERROR_KINDNESS_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_error_kindness_file(path: Any) -> ErrorBook:
    """Load one error file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: errors and views held one by one.
# ---------------------------------------------------------------------

class ErrorKindnessRegistry:
    """An in-memory holding of errors and views.

    The registry is the pure layer's model of a
    session's error book: errors are held under
    their ids, one error per id and per sequence,
    and views are held in recorded order, one view
    per sequence and per id. Holding is data
    only - nothing held here fixes anything,
    renders aloud, or sends anything.
    """

    def __init__(self, book: Any = None) -> None:
        self._errors: List[ErrorRecord] = []
        self._views: List[ErrorView] = []
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

    def register_error(self, item: Any) -> ErrorRecord:
        """Hold one error, judged whole before held."""
        return self._register(
            self._errors, _check_error_ref(item), "error_id", "error")

    def register_view(self, view: Any) -> ErrorView:
        """Hold one view; a view naming no id takes a fresh one."""
        checked = _check_view_ref(view)
        if not checked.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            checked = build_view({**checked.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, checked, "view_id", "view")

    def register_book(self, book: Any) -> ErrorBook:
        """Hold a whole book's errors and views, under its title."""
        checked = build_book(book)
        if self._title is not None and checked.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {checked.title!r}")
        for error in checked.errors:
            self.register_error(error)
        for view in checked.views:
            self.register_view(view)
        self._title = checked.title
        return self.book()

    def book(self) -> ErrorBook:
        return ErrorBook(
            title=self._title or "An unheld error book",
            errors=tuple(self._errors), views=tuple(self._views),
            panels=())

    def list_errors(self) -> Tuple[ErrorRecord, ...]:
        return tuple(self._errors)

    def list_views(self) -> Tuple[ErrorView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._errors) + tuple(self._views)

    def get_error(self, error_id: Any) -> ErrorRecord:
        return self.book().error_for(error_id)

    def get_view(self, view_id: Any) -> ErrorView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records shaped for the journal road.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> ErrorBook:
    if source is None:
        return load_error_kindness()
    if isinstance(source, ErrorBook):
        return source
    if isinstance(source, ErrorKindnessRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def error_record(error: Any, source: Any = None) -> Dict[str, Any]:
    checked = _check_error_ref(error)
    record = {
        "type": "error_kindness_error",
        "slice": ERROR_KINDNESS_SLICE,
        "error_id": checked.error_id, "kind": checked.kind,
        "segment": segment_of(checked),
        "passes": error_passes(checked),
        "gaps": list(error_gaps(checked)),
    }
    record.update(_provenance_record(checked))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    checked = _check_view_ref(view)
    record = {
        "type": "error_kindness_view",
        "slice": ERROR_KINDNESS_SLICE,
        "view_id": checked.view_id, "seq": checked.seq,
        "view_filter": checked.view_filter,
    }
    record.update(_provenance_record(checked))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    checked = validate_panel(panel, source)
    record = {"type": "error_kindness_panel",
              "slice": ERROR_KINDNESS_SLICE}
    record.update(checked.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, ErrorVerdict):
        checked = validate_verdict(verdict, source)
    else:
        checked = derive_verdict(_source_book(verdict), view)
    record = {"type": "error_kindness_verdict",
              "slice": ERROR_KINDNESS_SLICE}
    record.update(checked.to_record())
    return record


def rendering_record(rendering: Any) -> Dict[str, Any]:
    if not isinstance(rendering, ErrorRendering):
        raise ValueError("a rendering must be an ErrorRendering")
    record = {"type": "error_kindness_rendering",
              "slice": ERROR_KINDNESS_SLICE}
    record.update(rendering.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    checked = _source_book(book)
    record = {"type": "error_kindness_book",
              "slice": ERROR_KINDNESS_SLICE, "title": checked.title}
    record.update(checked.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(error: Any, source: Any = None) -> str:
    checked = _check_error_ref(error)
    return (
        f"{checked.title} - what happened: {checked.happened} "
        f"What it means: {checked.meaning} "
        f"The most likely fix: {checked.fix}")


def error_plain_words(error: Any, source: Any = None) -> str:
    return plain_words(error, source)


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The error book stands {verdict.verdict}: "
        f"{verdict.passing_shown} of {verdict.total_shown} shown "
        f"errors stand whole.")


def view_plain_words(view: Any) -> str:
    checked = _check_view_ref(view)
    return f"View {checked.view_id}: shows {checked.view_filter} errors."


def format_error(error: Any, source: Any = None) -> str:
    checked = _check_error_ref(error)
    lines = [f"{checked.title} ({checked.error_id})"]
    lines.extend(plain_lines(checked))
    if checked.trace:
        lines.append(
            f"Trace: folded behind the trace keypress "
            f"({len(checked.trace)} lines) - press trace to see it whole.")
    else:
        lines.append(
            "Trace: none folded - this error stands named in its "
            "gaps and does not stand whole.")
    return "\n".join(lines)


def format_view(view: Any) -> str:
    checked = _check_view_ref(view)
    return (
        f"View {checked.view_id}: filter {checked.view_filter} - "
        f"{checked.detail}")


def format_rendering(rendering: Any) -> str:
    if not isinstance(rendering, ErrorRendering):
        raise ValueError("a rendering must be an ErrorRendering")
    lines = list(rendering.plain_lines)
    if rendering.folded:
        lines.append(
            f"Trace: folded ({len(rendering.trace_lines)} lines) - "
            f"the {rendering.action} key shows it whole.")
    else:
        lines.append("Trace:")
        lines.extend(rendering.trace_lines)
    return "\n".join(lines)


def format_book(source: Any = None, kind: Any = None) -> str:
    book = _source_book(source)
    errors = (errors_for_kind(book, kind) if kind is not None
              else book.errors)
    lines = [f"Error Kindness (M-183) - {book.title}"]
    lines.extend(segment_of(error) for error in errors)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Error panel under view {panel.view_id}:"]
    lines.extend(row.segment for row in panel.rows)
    lines.extend(panel.account)
    return "\n".join(lines)


def format_verdict(source: Any = None, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return verdict_plain_words(source, view) + (
        f" (view {verdict.view_id}, as of {verdict.latest_on})")


def format_error_kindness_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "The Error Kindness (M-183)",
        f"{book.title}: {len(book.errors)} errors held, "
        f"{len(passing_errors(book))} standing whole.",
    ]
    if book.views:
        panel = derive_panel(book, book.views[0])
        lines.append(
            f"{panel.total_shown} of {panel.total_items} items show "
            f"under the first view.")
        lines.extend(row.segment for row in panel.rows)
    lines.append(PLAIN_EXPLANATION)
    return "\n".join(lines)


def parse_error_kindness_args(args: Any) -> Tuple[str, Any]:
    """Parse the /errors grammar into (action, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("error", "trace", "view", "kind"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
