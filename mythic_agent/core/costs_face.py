"""Costs face (All-Features roadmap slice M-190).

Part VIII - The Beautiful Face - builds here. The
roadmap's words: *live spend per session and per
slice, with the honesty rule kept (unknown =
unknown) and budgets from M-107 as gentle warnings
before walls.*

What already ships, and what this slice adds:

* The shipped tree already carries budgets
  (M-107: a budget guards one task or a whole
  session, its judge warns at four fifths of a
  limit - :data:`GENTLE_WARNING_FRACTION`, the
  M-107 warning fraction itself, reused here and
  never re-invented) and cost records of many
  kinds. What nothing held is *the costs face*:
  live spend per session and per slice, held as
  checkable data - one spend line per session or
  slice, held whole with its amount and its
  period and the M-107 budget it stands under;
  the costs index, derived from those held lines;
  and the gentle budget warnings, held as data
  beside them - a warning naming its subject, its
  level and the threshold it stands at, held as
  data, never enforced by this layer. This slice
  is that book, in its own module.
* A line is held whole: the label of the session
  or slice it stands for, its scope (a closed
  vocabulary - session, slice), its amount and
  its period - held honestly, an unknown amount
  standing empty, never invented - the M-107
  budget it stands under, named as data, and its
  detail. A line naming no budget is held honestly
  with an empty budget: it stands unheld, named
  in its gaps - its standing is judged from the
  held records alone, never claimed live.
* The costs index is DERIVED at call time from
  the held lines - never a second stored copy
  that could drift from the lines themselves.
  A stored index, counting verdict or coverage
  judgement on any record refuses by name.
* The gentle warnings are held as data: a warning
  record naming its subject, its level - gentle,
  near or over, a closed vocabulary - and the
  threshold the warning stands at. A book holds
  at most one warning record per subject level.
  Holding a warning enforces none of it: the rule
  stands as data (:data:`COSTS_RULE`) and a record
  claiming a budget was enforced or blocked, or
  that spend was actually charged, refuses BY
  NAME.
* The shipped data file (``mythic_agent/data/
  costs_face.yaml``) holds one example book in
  exactly the shape a real costs file takes, a
  loader reads a costs file anywhere on disk,
  lines and views are shaped as session news, and
  a small in-memory registry holds records one by
  one. The agent layer owns holding a costs book
  for a session and telling from it. This layer
  reaches no live road: it charges nothing,
  enforces no budget, blocks nothing and opens
  no network - it holds the costs as data and
  tells it.

Honesty rules, enforced here and pinned by tests:

* **Standing from records alone.** Every counting
  telling is derived from the held line records;
  a claim of a live charge, billing or budget
  enforcement refuses by name.
* **Unknown stays unknown.** An amount or period
  that is not known stands empty on its line -
  no figure is invented for it, and an unknown
  line stands uncounted, named in its gaps.
* **Warnings before walls.** The M-107 budgets
  warn gently before any wall: a warning is held
  as data at its threshold, and holding, viewing
  or reporting it enforces and blocks nothing.
* **The index is derived, never stored.** The
  costs index is derived from the held lines at
  call time; a stored index refuses by name, so
  it can never drift.
* **One line per spend.** Two lines standing for
  one line id refuse by name, and one warning
  record stands per subject level.
* **The warnings are data alone.** The records
  hold the warnings; holding, viewing or telling
  them charges, enforces and blocks nothing.
"""

from __future__ import annotations

__all__ = [
    "SCOPES",
    "EXAMPLE_BUDGET",
    "LEVELS",
    "INDEX_ACTION",
    "COSTS_FACE_RESOURCE",
    "COSTS_FACE_SCHEMA",
    "COSTS_FACE_SLICE",
    "COSTS_RULE",
    "PLAIN_EXPLANATION",
    "THE_COSTS_FACE_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "GENTLE_WARNING_FRACTION",
    "VIEW_FILTERS",
    "STANDING_WORDS",
    "Any",
    "Dict",
    "List",
    "Optional",
    "SpendLine",
    "IndexEntry",
    "WarningRecord",
    "CostsBook",
    "CostsIndex",
    "CostsPanel",
    "CostsPanelRow",
    "CostsFaceRegistry",
    "CostsVerdict",
    "CostsView",
    "StandingCount",
    "book_record",
    "build_book",
    "build_line",
    "build_warning",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "first_warning",
    "format_book",
    "format_line",
    "format_index",
    "format_warning",
    "format_costs_screen",
    "format_panel",
    "format_budget",
    "format_verdict",
    "format_view",
    "line_for_budget",
    "line_gaps",
    "line_counted",
    "line_plain_words",
    "line_record",
    "lines_for_scope",
    "index_plain_words",
    "index_record",
    "inspect_costs_source",
    "warning_for_subject",
    "warning_plain_words",
    "warning_record",
    "load_costs_face",
    "load_costs_face_file",
    "normalize_scope",
    "normalize_level",
    "normalize_view_filter",
    "panel_plain_words",
    "panel_record",
    "parse_costs_args",
    "counted_lines",
    "plain_lines",
    "plain_words",
    "segment_of",
    "shown_lines",
    "total_lines",
    "validate_book",
    "validate_line",
    "validate_warning",
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

from .budgets import WARNING_FRACTION

#: The gentle-warning threshold, taken from the
#: M-107 budgets themselves (their warning
#: fraction), never re-invented here.
GENTLE_WARNING_FRACTION = WARNING_FRACTION

COSTS_FACE_SCHEMA = "mythic.costs_face/1"
COSTS_FACE_SLICE = "M-190"
THE_COSTS_FACE_SLICE = COSTS_FACE_SLICE
COSTS_FACE_RESOURCE = "costs_face.yaml"
INDEX_ACTION = "index"
EXAMPLE_BUDGET = "session-budget"
STANDING_WORDS = ("counted", "unknown")
SCOPES = ("session", "slice")
LEVELS = ("gentle", "near", "over")
VIEW_FILTERS = ("all", "counted", "unknown")
VERDICT_WORDS = ("open", "strained", "shut")
COSTS_RULE = (
    "costs face is held as data alone: "
    "holding, viewing and reporting spend "
    "charges nothing, enforces no budget, "
    "blocks nothing and opens no network - "
    "an unknown cost stands unknown, never "
    "invented, and the M-107 budgets warn "
    "gently before any wall")
PLAIN_EXPLANATION = (
    "Costs face (M-190): live spend per session "
    "and per slice stands held line by line, "
    "its amount and period honest - unknown "
    "stands unknown - the index tells from "
    "those held lines, and the M-107 budgets "
    "stand beside them as gentle warnings "
    "before walls.")
USAGE = (
    "Usage: /costs | /costs line <line-id> | "
    "/costs budget <budget> | /costs scope <scope> | "
    "/costs view <view-id> | /costs warning <warning-id> | "
    "/costs index | /costs panel | /costs verdict")

_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_LINE_KEYS = frozenset({
    "line_id", "seq", "label", "scope", "amount", "period",
    "budget", "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_WARNING_KEYS = frozenset({
    "warning_id", "seq", "subject", "level", "threshold", "title",
    "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "standing", "counted", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "entries", "coverage", "covered", "uncovered",
    "total", "totals", "warning", "warnings", "charged"})
_LIVE_KEYS = (
    "live_session", "live_costs", "resumes_session",
    "resume_session", "resumed_session", "forks_session",
    "fork_session", "forked_session", "exports_session",
    "export_session", "exported_session", "opens_session",
    "open_session", "opens_network", "writes_file",
    "write_file", "live_resume", "resume_now",
    "fork_now", "export_now", "performs_resume",
    "performs_fork", "performs_export")


# ---------------------------------------------------------------------
# Small judges, in the sibling shape.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_budget(value: Any) -> str:
    """A held costs budget: a line named as data, or honestly empty.

    A line naming no costs budget is held with an
    empty budget and stands unknown in its gaps; a
    budget that is not a string at all refuses.
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError("a budget must be a string naming the costs budget")
    return value.strip()


def _check_measure(value: Any, what: str) -> str:
    """A held measure: cost or period, named as data or honestly empty.

    A session whose cost or period is not known is
    held with an empty measure: unknown stays
    unknown, and no figure is invented for it. A
    measure that is not a string at all refuses.
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"{what} must be a string naming it, or empty")
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
    for key in _LIVE_KEYS:
        if key in mapping:
            raise ValueError(
                f"{what} claims a live costs budget "
                f"({key!r} is named on it): "
                f"{COSTS_RULE}")
    for key in mapping:
        if key in _DERIVED_KEYS:
            raise ValueError(
                f"{what} carries {key!r}, which is derived from its "
                f"own fields and never stored")
        if key not in allowed:
            raise ValueError(f"{what} carries unknown field {key!r}")


def normalize_scope(value: Any) -> str:
    scope = _clean_text(value, "an scope").lower()
    if scope not in SCOPES:
        raise ValueError(
            f"scope {scope!r} is not one of the named scopes: "
            + ", ".join(SCOPES))
    return scope


def normalize_level(value: Any) -> str:
    warning = _clean_text(value, "an warning").lower()
    if warning not in LEVELS:
        raise ValueError(
            f"warning {warning!r} is not one of the held "
            f"warnings: " + ", ".join(LEVELS))
    return warning


def normalize_view_filter(value: Any) -> str:
    view_filter = _clean_text(value, "a view filter").lower()
    if view_filter not in VIEW_FILTERS:
        raise ValueError(
            f"view filter {view_filter!r} is not one of the held "
            f"filters: " + ", ".join(VIEW_FILTERS))
    return view_filter


# ---------------------------------------------------------------------
# The held line: one line, with the budget that reaches it.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class SpendLine:
    """One line, held as data with its costs budget.

    The line names its title, the scope it lives
    in - one of the closed scope vocabulary - its
    kind, one of the closed line vocabulary,
    the costs budget that reaches it, named as data,
    and its detail. A line naming no costs budget
    is held with an empty budget: it stands unknown,
    named in its gaps, and no budget is invented for
    it. The line is local data alone - no live
    budget stands behind it: holding it clicks
    nothing.
    """

    line_id: str
    seq: int
    label: str
    scope: str
    amount: str = ""
    period: str = ""
    budget: str = ""
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "line_id", _clean_text(self.line_id, "a line id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "label", _clean_text(self.label, "a label"))
        object.__setattr__(self, "scope", normalize_scope(self.scope))
        object.__setattr__(
            self, "amount", _check_measure(self.amount, "a cost"))
        object.__setattr__(
            self, "period", _check_measure(self.period, "a period"))
        object.__setattr__(self, "budget", _check_budget(self.budget))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a line detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.line_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "line_id": self.line_id, "seq": self.seq,
            "label": self.label, "scope": self.scope,
            "amount": self.amount, "period": self.period,
            "budget": self.budget, "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_line_ref(value: Any) -> SpendLine:
    if not isinstance(value, SpendLine):
        raise ValueError("a line must be a SpendLine")
    return value


def validate_line(line: Any) -> SpendLine:
    return _check_line_ref(line)


def build_line(record: Any = None, **kwargs: Any) -> SpendLine:
    """Build one held line from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, SpendLine):
        if kwargs:
            raise ValueError("a line stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a line must be a mapping or a SpendLine")
    _needed(data, _LINE_KEYS, "a line")
    return SpendLine(
        line_id=data.get("line_id"), seq=data.get("seq"),
        label=data.get("label"), scope=data.get("scope"),
        amount=data.get("amount"), period=data.get("period"),
        budget=data.get("budget"), detail=data.get("detail"),
        **_provenance(data))


def line_gaps(line: Any) -> Tuple[str, ...]:
    """The gaps that keep a line from the costs face."""
    checked = _check_line_ref(line)
    gaps = []
    if not checked.amount:
        gaps.append("spend unknown")
    if not checked.budget:
        gaps.append("no budget held")
    return tuple(gaps)


def line_counted(line: Any) -> bool:
    return not line_gaps(line)


def plain_lines(line: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the line's own fields."""
    checked = _check_line_ref(line)
    return (
        f"Line: {checked.label}",
        f"Scope: {checked.scope}",
        f"Amount: {checked.amount if checked.amount else 'unknown'}",
        f"Period: {checked.period if checked.period else 'unknown'}",
        f"Budget: {checked.budget if checked.budget else 'none'}",
    )


def segment_of(line: Any) -> str:
    checked = _check_line_ref(line)
    gaps = line_gaps(checked)
    return (
        f"{checked.line_id}: {checked.label} - scope: "
        f"'{checked.scope}' - amount: "
        f"'{checked.amount if checked.amount else 'unknown'}' - "
        f"period: "
        f"'{checked.period if checked.period else 'unknown'}' - "
        f"budget: '{checked.budget if checked.budget else 'none'}' - "
        f"detail: '{checked.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


@dataclass(frozen=True)
class WarningRecord:
    """One file warning, held as data.

    The record names its file, its line number and
    the editor that stands as its threshold, with its
    title and its detail. One record stands per
    file line in a book. The record is data alone:
    holding it opens no file and launches no
    editor, ever.
    """

    warning_id: str
    seq: int
    subject: str
    level: str
    threshold: str
    title: str
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "warning_id", _clean_text(self.warning_id, "a warning id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "subject", _clean_text(self.subject, "a session id"))
        object.__setattr__(self, "level", normalize_level(self.level))
        object.__setattr__(
            self, "threshold", _clean_text(self.threshold, "an warning threshold"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a warning title"))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a warning detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.warning_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "warning_id": self.warning_id, "seq": self.seq,
            "subject": self.subject, "level": self.level,
            "threshold": self.threshold, "title": self.title,
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_warning_ref(value: Any) -> WarningRecord:
    if not isinstance(value, WarningRecord):
        raise ValueError("a warning must be a WarningRecord")
    return value


def validate_warning(warning: Any) -> WarningRecord:
    return _check_warning_ref(warning)


def build_warning(warning: Any = None, **kwargs: Any) -> WarningRecord:
    if warning is None:
        data = dict(kwargs)
    elif isinstance(warning, WarningRecord):
        if kwargs:
            raise ValueError("a warning stands whole or by fields, not both")
        return warning
    elif isinstance(warning, dict):
        data = dict(warning)
        data.update(kwargs)
    else:
        raise ValueError("a warning must be a mapping or a WarningRecord")
    _needed(data, _WARNING_KEYS, "a warning")
    return WarningRecord(
        warning_id=data.get("warning_id"), seq=data.get("seq"),
        subject=data.get("subject"), level=data.get("level"),
        threshold=data.get("threshold"), title=data.get("title"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held view: which lines a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class CostsView:
    """A view over the book: every line, the counted, the rest."""

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


def _check_view_ref(value: Any) -> CostsView:
    if not isinstance(value, CostsView):
        raise ValueError("a view must be a CostsView")
    return value


def validate_view(view: Any) -> CostsView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> CostsView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, CostsView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or a CostsView")
    _needed(data, _VIEW_KEYS, "a view")
    return CostsView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


def inspect_costs_source(piece: Any) -> Dict[str, Any]:
    """Name what one costs source piece is, without judging it."""
    if isinstance(piece, SpendLine):
        return {"kind": "line", "line_id": piece.line_id}
    if isinstance(piece, dict):
        if "line_id" in piece:
            return {"kind": "line", "line_id": piece.get("line_id")}
        if "view_id" in piece:
            return {"kind": "view", "view_id": piece.get("view_id")}
        if "warning_id" in piece:
            return {"kind": "warning", "warning_id": piece.get("warning_id")}
    return {"kind": "unknown", "line_id": None}


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class CostsPanelRow:
    item_id: str
    standing: str
    label: str
    segment: str
    recorded_on: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id, "standing": self.standing,
            "label": self.label, "segment": self.segment,
            "recorded_on": self.recorded_on,
        }


def _row_for_line(line: SpendLine) -> CostsPanelRow:
    return CostsPanelRow(
        item_id=line.line_id,
        standing="counted" if line_counted(line) else "unknown",
        label=line.label, segment=segment_of(line),
        recorded_on=line.recorded_on)


def _check_row_ref(value: Any) -> CostsPanelRow:
    if not isinstance(value, CostsPanelRow):
        raise ValueError("a panel row must be a CostsPanelRow")
    return value


def validate_row(row: Any, line: Any = None) -> CostsPanelRow:
    checked = _check_row_ref(row)
    if line is not None:
        derived = _row_for_line(_check_line_ref(line))
        if checked != derived:
            raise ValueError(
                f"panel row {checked.item_id!r} does not agree with "
                f"the row derived from its line")
    return checked


def build_row(row: Any = None, line: Any = None,
              **kwargs: Any) -> CostsPanelRow:
    if line is not None:
        derived = _row_for_line(_check_line_ref(line))
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            CostsPanelRow(**kwargs))
        return validate_row(built, line)
    if isinstance(row, CostsPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in STANDING_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return CostsPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return CostsPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or a CostsPanelRow")


@dataclass(frozen=True)
class StandingCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _standing_counts(rows: Tuple[CostsPanelRow, ...]
                 ) -> Tuple[StandingCount, ...]:
    counts: List[StandingCount] = []
    for standing in STANDING_WORDS:
        number = sum(1 for row in rows if row.standing == standing)
        if number:
            counts.append(StandingCount(standing=standing, items=number))
    return tuple(counts)


def _panel_account(total_items: int, total_shown: int,
                   passing_shown: int,
                   standing_counts: Tuple[StandingCount, ...],
                   view_filter: str, as_of: str) -> Tuple[str, ...]:
    standing_words = ", ".join(
        f"{count.standing} {count.items}"
        for count in standing_counts) or "none"
    return (
        f"The costs book holds {total_items} lines as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {passing_shown} of the shown lines "
        f"stand counted.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its line's own fields "
        "- the label, the scope, the amount and period "
        "honestly held and the M-107 budget it stands "
        "under - and no judgement is stored on any line.",
        "Spend is judged from the held records alone: "
        "a line naming no amount stands unknown, a line "
        "naming no budget stands unheld, and the "
        "costs index is derived from the held lines, "
        "never stored where it could drift.",
    )


@dataclass(frozen=True)
class CostsPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[CostsPanelRow, ...]
    total_items: int
    total_shown: int
    standing_counts: Tuple[StandingCount, ...]
    as_of: str
    account: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "panel_id": self.panel_id, "view_id": self.view_id,
            "view_filter": self.view_filter,
            "rows": [row.to_record() for row in self.rows],
            "total_items": self.total_items,
            "total_shown": self.total_shown,
            "standing_counts": [c.to_record() for c in self.standing_counts],
            "as_of": self.as_of, "account": list(self.account),
        }


def _resolve_view(source: Any, view: Any) -> CostsView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, CostsView):
        return view
    return book.view_for(view)


def shown_lines(source: Any, view: Any = None
                   ) -> Tuple[SpendLine, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.lines
    if resolved.view_filter == "counted":
        return tuple(g for g in book.lines if line_counted(g))
    return tuple(g for g in book.lines if not line_counted(g))


def lines_for_scope(source: Any, scope: Any
                      ) -> Tuple[SpendLine, ...]:
    wanted = normalize_scope(scope)
    return tuple(
        g for g in _source_book(source).lines if g.scope == wanted)


def counted_lines(source: Any) -> Tuple[SpendLine, ...]:
    return tuple(
        g for g in _source_book(source).lines if line_counted(g))


def total_lines(source: Any) -> int:
    return len(_source_book(source).lines)


def derive_panel(source: Any, view: Any = None) -> CostsPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_lines(book, resolved)
    rows = tuple(_row_for_line(line) for line in shown)
    counts = _standing_counts(rows)
    as_of = max((g.recorded_on for g in book.lines), default="")
    passing = sum(1 for g in shown if line_counted(g))
    return CostsPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.lines), total_shown=len(shown),
        standing_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.lines), len(shown), passing, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> CostsPanel:
    if not isinstance(value, CostsPanel):
        raise ValueError("a panel must be a CostsPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> CostsPanel:
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
                     "total_shown", "standing_counts", "as_of", "account"):
            if getattr(checked, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {checked.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return checked


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> CostsPanel:
    if isinstance(panel, CostsPanel):
        if kwargs:
            raise ValueError("a panel stands whole or by fields, not both")
        return validate_panel(panel, source)
    if isinstance(panel, dict):
        data = dict(panel)
        data.update(kwargs)
        rows = tuple(build_row(row) for row in data.get("rows") or ())
        counts = tuple(
            StandingCount(
                standing=_clean_text(
                    c.get("standing"), "a standing count word").lower(),
                items=_check_count(c.get("items"), "a standing count"))
            for c in data.get("standing_counts") or ()
            if isinstance(c, dict))
        built = CostsPanel(
            panel_id=_clean_text(data.get("panel_id"), "a panel id"),
            view_id=data.get("view_id"),
            view_filter=normalize_view_filter(data.get("view_filter")),
            rows=rows,
            total_items=_check_count(
                data.get("total_items"), "a total_items count"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            standing_counts=counts,
            as_of=_clean_text(data.get("as_of"), "an as_of day"),
            account=_check_lines(data.get("account"), "the account"))
        return validate_panel(built, source)
    if panel is None and source is not None:
        return derive_panel(source, kwargs.get("view"))
    raise ValueError("a panel must be a mapping, a CostsPanel, or derived")


def _check_lines(value: Any, what: str) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError(f"{what} must be a list of lines")
    lines = []
    for line in value:
        lines.append(_clean_text(line, f"a line of {what}"))
    return tuple(lines)


def _verdict_word(total_shown: int, passing_shown: int) -> str:
    if total_shown > 0 and passing_shown == total_shown:
        return "open"
    if passing_shown == 0:
        return "shut"
    return "strained"


@dataclass(frozen=True)
class CostsVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> CostsVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_lines(book, resolved)
    passing = sum(1 for g in shown if line_counted(g))
    latest = max((g.recorded_on for g in shown), default="")
    return CostsVerdict(
        verdict=_verdict_word(len(shown), passing),
        view_id=resolved.view_id, total_shown=len(shown),
        passing_shown=passing, latest_on=latest)


def _check_verdict_ref(value: Any) -> CostsVerdict:
    if not isinstance(value, CostsVerdict):
        raise ValueError("a verdict must be a CostsVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> CostsVerdict:
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
                  **kwargs: Any) -> CostsVerdict:
    if isinstance(verdict, CostsVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = CostsVerdict(
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
        "a verdict must be a mapping, a CostsVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held lines' budgets at call time, and
# the warning budgets: which file warnings the book holds, derived too.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexEntry:
    budget: str
    line_id: str
    label: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "budget": self.budget, "line_id": self.line_id,
            "label": self.label,
        }


@dataclass(frozen=True)
class CostsIndex:
    """The line index, derived from the held lines.

    The index names one entry per counted line, in
    held order - the line's own budget, its id and
    its title - and the lines that stand
    unknown, named in its gaps. Nothing here is
    stored on any line: the index is derived at
    call time from the held records alone, so it
    can never drift from them.
    """

    entries: Tuple[IndexEntry, ...]
    gaps: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "entries": [e.to_record() for e in self.entries],
            "gaps": list(self.gaps),
        }


def derive_index(source: Any) -> CostsIndex:
    """Derive the line index from the book's held lines."""
    book = _source_book(source)
    entries = tuple(
        IndexEntry(budget=g.budget, line_id=g.line_id, label=g.label)
        for g in book.lines if line_counted(g))
    gaps = tuple(
        g.line_id for g in book.lines if not line_counted(g))
    return CostsIndex(entries=entries, gaps=gaps)


def line_for_budget(source: Any, budget: Any) -> Optional[SpendLine]:
    """The first held line one budget reaches, or none - honestly."""
    wanted = _check_budget(budget)
    if not wanted:
        return None
    for line in _source_book(source).lines:
        if line.budget == wanted:
            return line
    return None


def warning_for_subject(source: Any, subject: Any,
                       warning: Any = None) -> Optional[WarningRecord]:
    """The held warning budget for one session (and warning, when named)."""
    wanted = _clean_text(subject, "a session id")
    for record in _source_book(source).warnings:
        if record.subject == wanted and (
                warning is None
                or record.level == normalize_level(warning)):
            return record
    return None


def first_warning(source: Any) -> Optional[WarningRecord]:
    """The first held warning budget, standing for the costs budgets, or none."""
    warnings = _source_book(source).warnings
    return warnings[0] if warnings else None


# ---------------------------------------------------------------------
# The book: lines, views and warnings held together, one pinned panel
# at most per telling, and no verdict or index ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class CostsBook:
    title: str
    lines: Tuple[SpendLine, ...] = ()
    views: Tuple[CostsView, ...] = ()
    warnings: Tuple[WarningRecord, ...] = ()
    panels: Tuple[CostsPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        lines = tuple(_check_line_ref(g) for g in self.lines)
        views = tuple(_check_view_ref(v) for v in self.views)
        warnings = tuple(_check_warning_ref(m) for m in self.warnings)
        panels = tuple(_check_panel_ref(p) for p in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for line in lines:
            if line.line_id in seen_ids:
                raise ValueError(
                    f"two lines stand under id {line.line_id!r}")
            if line.seq in seen_seqs:
                raise ValueError(
                    f"two lines stand at sequence {line.seq}")
            seen_ids.add(line.line_id)
            seen_seqs.add(line.seq)
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
        warning_ids = set()
        warning_seqs = set()
        warning_thresholds = set()
        for record in warnings:
            if record.warning_id in warning_ids:
                raise ValueError(
                    f"two warnings stand under id {record.warning_id!r}")
            if record.seq in warning_seqs:
                raise ValueError(
                    f"two warnings stand at sequence {record.seq}")
            threshold = (record.subject, record.level)
            if threshold in warning_thresholds:
                raise ValueError(
                    f"two warning records stand for session "
                    f"{record.subject!r} under warning "
                    f"{record.level!r}: one warning stands "
                    f"per session budget")
            warning_ids.add(record.warning_id)
            warning_seqs.add(record.seq)
            warning_thresholds.add(threshold)
        object.__setattr__(
            self, "lines", tuple(sorted(lines, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "warnings", tuple(sorted(warnings, key=lambda m: m.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.lines + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.line_id for g in self.lines) + tuple(
            v.view_id for v in self.views)

    def line_ids(self) -> Tuple[str, ...]:
        return tuple(g.line_id for g in self.lines)

    def line_for(self, line_id: Any) -> SpendLine:
        wanted = _clean_text(line_id, "a line id")
        for line in self.lines:
            if line.line_id == wanted:
                return line
        raise KeyError(f"no line named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> CostsView:
        wanted = _clean_text(view_id, "a view id")
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no view named {wanted!r} stands in this book")

    def warning_for(self, warning_id: Any) -> WarningRecord:
        wanted = _clean_text(warning_id, "a warning id")
        for record in self.warnings:
            if record.warning_id == wanted:
                return record
        raise KeyError(f"no warning named {wanted!r} stands in this book")

    def item_for(self, item_id: Any) -> Any:
        wanted = _clean_text(item_id, "an item id")
        for line in self.lines:
            if line.line_id == wanted:
                return line
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "lines": [g.to_record() for g in self.lines],
            "views": [v.to_record() for v in self.views],
            "warnings": [m.to_record() for m in self.warnings],
            "panels": [p.to_record() for p in self.panels],
        }


def _judge_book_panels(book: CostsBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: CostsBook) -> None:
    if book.title != "Costs face at the M-189 slice boundary":
        raise ValueError("the shipped example book carries another title")
    if len(book.lines) != 6 or len(book.views) != 2:
        raise ValueError(
            "the shipped example book must hold six lines and two views")
    if len(book.warnings) != 2:
        raise ValueError(
            "the shipped example book must hold two warning records")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m189-boundary":
        raise ValueError("the pinned panel is panel-m189-boundary")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "strained" or verdict.passing_shown != 5:
        raise ValueError(
            "the shipped example book's verdict must stand strained "
            "at five counted of six")
    index = derive_index(book)
    if [e.budget for e in index.entries] != [
            "session-budget", "slice-budget", "session-budget",
            "slice-budget", "slice-budget"]:
        raise ValueError(
            "the shipped example book's index must derive the "
            "five held budgets in held order")
    if index.gaps != ("spend-store-sweep",):
        raise ValueError(
            "the shipped example book must leave the store "
            "sweep spend honestly unknown, named in its gaps")
    found = line_for_budget(book, EXAMPLE_BUDGET)
    if found is None or found.line_id != "spend-login-session":
        raise ValueError(
            "the shipped example book must reach its login "
            "line under the example budget")
    first = first_warning(book)
    if first is None or first.warning_id != "warning-gentle-login":
        raise ValueError(
            "the shipped example book must hold the login gentle "
            "warning as its first warning record")


def validate_book(data: Any, *, require_example: bool = False) -> CostsBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, CostsBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a costs book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live costs budget "
                f"({key!r} is named on it): {COSTS_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its lines under a view")
    if "costs_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held lines at call time")
    if data.get("schema") is not None and (
            data["schema"] != COSTS_FACE_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{COSTS_FACE_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != COSTS_FACE_SLICE):
        raise ValueError(
            f"a book's slice must be {COSTS_FACE_SLICE!r}")
    head = data.get("costs") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's costs head must be a mapping")
    title = head.get("title") or data.get("title")
    lines = tuple(build_line(g) for g in data.get("lines") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    warnings = tuple(build_warning(m) for m in data.get("warnings") or ())
    book = CostsBook(
        title=title, lines=lines, views=views, warnings=warnings, panels=())
    panels = tuple(
        build_panel(p, book) for p in data.get("panels") or ())
    book = CostsBook(
        title=book.title, lines=book.lines, views=book.views,
        warnings=book.warnings, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> CostsBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (CostsBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or a CostsBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> CostsBook:
    return validate_book(data, require_example=require_example)


def load_costs_face(
        data: Optional[Dict[str, Any]] = None) -> CostsBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(COSTS_FACE_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_costs_face_file(path: Any) -> CostsBook:
    """Load one line file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: lines and views held one by one.
# ---------------------------------------------------------------------

class CostsFaceRegistry:
    """An in-memory holding of lines and views.

    The registry is the pure layer's model of a
    session's costs book: lines are held under
    their ids, one line per id and per
    sequence, and views are held in recorded
    order, one view per sequence and per id.
    Holding is data only - nothing held here moves
    a pointer, clicks anything, or opens a file.
    """

    def __init__(self, book: Any = None) -> None:
        self._lines: List[SpendLine] = []
        self._views: List[CostsView] = []
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

    def register_line(self, item: Any) -> SpendLine:
        """Hold one line, judged whole before held."""
        checked = _check_line_ref(item)
        return self._register(
            self._lines, checked, "line_id", "line")

    def register_view(self, view: Any) -> CostsView:
        """Hold one view; a view naming no id takes a fresh one."""
        checked = _check_view_ref(view)
        if not checked.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            checked = build_view({**checked.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, checked, "view_id", "view")

    def register_book(self, book: Any) -> CostsBook:
        """Hold a whole book's lines and views, under its title."""
        checked = build_book(book)
        if self._title is not None and checked.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {checked.title!r}")
        for line in checked.lines:
            self.register_line(line)
        for view in checked.views:
            self.register_view(view)
        self._title = checked.title
        return self.book()

    def book(self) -> CostsBook:
        return CostsBook(
            title=self._title or "An unheld costs book",
            lines=tuple(self._lines), views=tuple(self._views),
            warnings=(), panels=())

    def list_lines(self) -> Tuple[SpendLine, ...]:
        return tuple(self._lines)

    def list_views(self) -> Tuple[CostsView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._lines) + tuple(self._views)

    def get_line(self, line_id: Any) -> SpendLine:
        return self.book().line_for(line_id)

    def get_view(self, view_id: Any) -> CostsView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records shaped for the journal budget.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> CostsBook:
    if source is None:
        return load_costs_face()
    if isinstance(source, CostsBook):
        return source
    if isinstance(source, CostsFaceRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def line_record(line: Any, source: Any = None) -> Dict[str, Any]:
    checked = _check_line_ref(line)
    record = {
        "type": "spend_line",
        "slice": COSTS_FACE_SLICE,
        "line_id": checked.line_id,
        "label": checked.label,
        "segment": segment_of(checked),
        "passes": line_counted(checked),
        "gaps": list(line_gaps(checked)),
    }
    record.update(_provenance_record(checked))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    checked = _check_view_ref(view)
    record = {
        "type": "costs_view",
        "slice": COSTS_FACE_SLICE,
        "view_id": checked.view_id, "seq": checked.seq,
        "view_filter": checked.view_filter,
    }
    record.update(_provenance_record(checked))
    return record


def warning_record(record_in: Any) -> Dict[str, Any]:
    checked = _check_warning_ref(record_in)
    record = {
        "type": "costs_warning",
        "slice": COSTS_FACE_SLICE,
        "warning_id": checked.warning_id,
        "subject": checked.subject,
        "level": checked.level,
    }
    record.update(_provenance_record(checked))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    checked = validate_panel(panel, source)
    record = {"type": "costs_panel",
              "slice": COSTS_FACE_SLICE}
    record.update(checked.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, CostsVerdict):
        checked = validate_verdict(verdict, source)
    else:
        checked = derive_verdict(_source_book(verdict), view)
    record = {"type": "costs_verdict",
              "slice": COSTS_FACE_SLICE}
    record.update(checked.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, CostsIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "costs_index",
              "slice": COSTS_FACE_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    checked = _source_book(book)
    record = {"type": "costs_book",
              "slice": COSTS_FACE_SLICE,
              "title": checked.title}
    record.update(checked.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(line: Any, source: Any = None) -> str:
    checked = _check_line_ref(line)
    return (
        f"{checked.label} - scope {checked.scope}: "
        f"amount {checked.amount if checked.amount else 'unknown'}, "
        f"period {checked.period if checked.period else 'unknown'}, "
        f"budget {checked.budget if checked.budget else 'none'}. "
        f"{checked.detail}")


def line_plain_words(line: Any, source: Any = None) -> str:
    return plain_words(line, source)


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The costs face stands {verdict.verdict}: "
        f"{verdict.passing_shown} of {verdict.total_shown} shown "
        f"lines stand counted.")


def view_plain_words(view: Any) -> str:
    checked = _check_view_ref(view)
    return f"View {checked.view_id}: shows {checked.view_filter} lines."


def warning_plain_words(record_in: Any) -> str:
    checked = _check_warning_ref(record_in)
    return (
        f"Warning {checked.warning_id}: {checked.level} "
        f"for {checked.subject}, at {checked.threshold}. "
        f"{checked.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, CostsIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.entries)} budgets for "
        f"{len(index.entries)} lines; uncounted, named in "
        f"its gaps: {gaps}.")


def format_line(line: Any, source: Any = None) -> str:
    checked = _check_line_ref(line)
    lines = [f"{checked.label} ({checked.line_id})"]
    lines.extend(plain_lines(checked))
    lines.append(checked.detail)
    if line_counted(checked):
        lines.append(
            "This line stands counted on the costs face, under "
            "the M-107 budget its record names.")
    else:
        lines.append(
            "This line stands uncounted - its spend or its "
            "budget stands unheld, named in its gaps, and no "
            "figure is invented for it.")
    return "\n".join(lines)


def format_view(view: Any) -> str:
    checked = _check_view_ref(view)
    return (
        f"View {checked.view_id}: filter {checked.view_filter} - "
        f"{checked.detail}")


def format_warning(record_in: Any) -> str:
    checked = _check_warning_ref(record_in)
    lines = [
        f"Budget warning {checked.level} for {checked.subject} "
        f"({checked.warning_id}): {checked.title}. {checked.detail}"]
    lines.append(
        "This warning stands held as data alone - holding "
        "or reading it charges nothing, enforces no "
        "budget and blocks nothing.")
    return "\n".join(lines)


def format_budget(source: Any, budget: Any) -> str:
    line = line_for_budget(source, budget)
    if line is not None:
        return format_line(line)
    wanted = _check_budget(budget)
    return (
        f"No held line stands under budget {wanted!r} yet - the "
        f"budget reaches nothing in this book, and no line is "
        f"invented for it.")


def format_book(source: Any = None, scope: Any = None) -> str:
    book = _source_book(source)
    lines = (lines_for_scope(book, scope)
             if scope is not None else book.lines)
    out = [f"Costs Face (M-190) - {book.title}"]
    out.extend(segment_of(line) for line in lines)
    return "\n".join(out)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Costs panel under view {panel.view_id}:"]
    lines.extend(row.segment for row in panel.rows)
    lines.extend(panel.account)
    return "\n".join(lines)


def format_verdict(source: Any = None, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return verdict_plain_words(source, view) + (
        f" (view {verdict.view_id}, as of {verdict.latest_on})")


def format_index(source: Any = None) -> str:
    book = _source_book(source)
    index = derive_index(book)
    lines = ["Spend index, derived from the held lines:"]
    for entry in index.entries:
        lines.append(f"{entry.budget} - {entry.label} ({entry.line_id})")
    if index.gaps:
        lines.append(
            "Uncounted on the costs face, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "charges nothing and opens no network.")
    return "\n".join(lines)


def format_costs_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "Costs Face (M-190)",
        f"{book.title}: {len(book.lines)} lines held, "
        f"{len(counted_lines(book))} lines standing counted, "
        f"{len(book.warnings)} budget warnings held.",
    ]
    if book.views:
        panel = derive_panel(book, book.views[0])
        lines.append(
            f"{panel.total_shown} of {panel.total_items} items show "
            f"under the first view.")
        lines.extend(row.segment for row in panel.rows)
    lines.append(index_plain_words(book))
    lines.append(PLAIN_EXPLANATION)
    return "\n".join(lines)


def parse_costs_args(args: Any) -> Tuple[str, Any]:
    """Parse the /costs grammar into (action, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("line", "view", "warning"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("budget", "scope"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("index", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)


