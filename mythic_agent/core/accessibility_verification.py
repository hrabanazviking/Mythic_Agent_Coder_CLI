"""Accessibility verification (All-Features roadmap slice M-199).

Part VIII - The Beautiful Face - builds here. The
roadmap words: *M-016's tests re-run as gates -
keyboard-only completion, contrast, reduced
motion, no-colour play.*

What already ships, and what this slice adds:

* The M-016 accessibility baseline measured the
  "before" picture - a keyboard-only task pass, a
  screen-reader pass, a contrast audit - and left
  its closing to Part VIII. What nothing held is
  *that baseline re-run as gates, as a book*: every
  gate held as checkable data - one card per gate,
  held whole with its title, its kind (a closed
  vocabulary - keyboard, contrast, motion, colour),
  its measure held honestly, and the evidence it
  carries, named as data; the verification index,
  derived from those held gates; the views, which
  show every gate, the ready or the incomplete; and
  the notes on gates, held as data beside them -
  note, concern, praise and question named as
  stances, each feeding back to the user as data,
  never applied by this layer. This slice is that
  book, in its own module, standing in the M-198
  UI-undo book shape. The M-171 charter names NO
  row for this slice - the grep stands empty and
  the slice tests pin that live - so there is no
  charter verdict for this slice to honour; the
  slice is built to the roadmap words alone, in
  the M-194/M-195 manner.

* A gate is held whole: the title it stands
  under, its kind, its measure - held honestly, an
  unknown measure standing empty, never invented -
  the evidence it carries, named as data, and
  its detail. A gate naming no held evidence is
  held honestly with empty evidence: it stands
  incomplete, named in its gaps - completeness is
  judged from the held records alone, never
  claimed live.
* The verification index is DERIVED at call time
  from the held gates - never a second stored copy
  that could drift from the gates themselves. A
  stored index, completeness verdict or coverage
  judgement on any record refuses by name.
* The notes are held as data: a note record
  naming its gate, its stance - note, concern,
  praise or question, a closed vocabulary - and
  what it feeds back toward. A book holds at most
  one note record per gate stance. Holding a note
  applies none of it: the rule stands as data
  (:data:`VERIFY_RULE`) and a record claiming a
  check was actually run, a gate actually passed
  live, or a reader actually launched, refuses
  BY NAME.
* The shipped data file holds one example book in
  exactly the shape a real verification file
  takes, a loader reads a verification file
  anywhere on disk, gates and views are shaped as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding a verification book for a session and
  telling from it. This layer reaches no live
  road: it runs no check, measures nothing live,
  launches no reader, opens no network and writes
  nothing - it holds the gates as data and tells
  them.

Honesty rules, enforced here and pinned by tests:

* **Completeness from records alone.** Every
  completeness telling is derived from the held
  gate records; a claim of a live run, live pass
  or live measurement refuses by name.
* **Incomplete stands incomplete.** A gate naming
  no held evidence stands incomplete, named in
  its gaps - no evidence is invented for it.
* **Unknown stays unknown.** A measure that is
  not known stands empty on its gate - no figure
  is invented for it.
* **The index is derived, never stored.** The
  verification index is derived from the held
  gates at call time; a stored index refuses by
  name, so it can never drift.
* **One gate per gate.** Two gates standing for
  one gate id refuse by name, and one note record
  stands per gate stance.
"""



from __future__ import annotations

__all__ = [
    "KINDS",
    "EXAMPLE_EVIDENCE",
    "STANCES",
    "INDEX_ACTION",
    "ACCESSIBILITY_VERIFICATION_RESOURCE",
    "ACCESSIBILITY_VERIFICATION_SCHEMA",
    "ACCESSIBILITY_VERIFICATION_SLICE",
    "VERIFY_RULE",
    "PLAIN_EXPLANATION",
    "THE_ACCESSIBILITY_VERIFICATION_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "READY_WORDS",
    "Any",
    "Dict",
    "List",
    "Optional",
    "GateCard",
    "IndexEntry",
    "NoteRecord",
    "AccessBook",
    "AccessIndex",
    "AccessPanel",
    "AccessPanelRow",
    "AccessVerifyRegistry",
    "AccessVerdict",
    "AccessView",
    "TargetCount",
    "book_record",
    "build_book",
    "build_gate",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "first_note",
    "format_book",
    "format_gate",
    "format_index",
    "format_note",
    "format_verify_screen",
    "format_panel",
    "format_evidence",
    "format_verdict",
    "format_view",
    "gate_for_evidence",
    "gate_gaps",
    "gate_passes",
    "gate_plain_words",
    "gate_record",
    "gates_for_kind",
    "index_plain_words",
    "index_record",
    "inspect_gate_source",
    "note_for_gate",
    "note_plain_words",
    "note_record",
    "load_accessibility_verification",
    "load_accessibility_verification_file",
    "normalize_kind",
    "normalize_stance",
    "normalize_view_filter",
    "panel_plain_words",
    "panel_record",
    "parse_verify_args",
    "passing_gates",
    "plain_lines",
    "plain_words",
    "segment_of",
    "shown_gates",
    "total_gates",
    "validate_book",
    "validate_gate",
    "validate_note",
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

ACCESSIBILITY_VERIFICATION_SCHEMA = "mythic.accessibility_verification/1"
ACCESSIBILITY_VERIFICATION_SLICE = "M-199"
THE_ACCESSIBILITY_VERIFICATION_SLICE = ACCESSIBILITY_VERIFICATION_SLICE
ACCESSIBILITY_VERIFICATION_RESOURCE = "accessibility_verification.yaml"
INDEX_ACTION = "index"
EXAMPLE_EVIDENCE = "the task completed by keyboard alone"
READY_WORDS = ("ready", "unready")
KINDS = ("keyboard", "contrast", "motion", "colour")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "ready", "unready")
VERDICT_WORDS = ("open", "strained", "shut")

VERIFY_RULE = (
    "Accessibility verification is held as data alone: "
    "holding, viewing and telling the verification "
    "book runs no check, measures nothing live, "
    "launches no reader, opens no network and "
    "writes nothing - completeness is judged "
    "from the held records alone, never "
    "claimed live")
PLAIN_EXPLANATION = (
    "Accessibility verification (M-199): "
    "M-016's accessibility tests re-run as "
    "gates - keyboard-only completion, "
    "contrast, reduced motion and no-colour "
    "play - each gate held as a card with "
    "its kind, its measure honestly held, "
    "and the evidence it carries.")
USAGE = (
    "Usage: /accessverify | /accessverify gate <gate-id> | "
    "/accessverify evidence <evidence> | /accessverify kind <kind> | "
    "/accessverify view <view-id> | /accessverify note <note-id> | "
    "/accessverify index | /accessverify panel | /accessverify verdict")

_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_PANE_KEYS = frozenset({
    "gate_id", "seq", "title", "kind", "measure",
    "evidence", "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "gate_id", "stance", "target", "title",
    "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "standing", "ready", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "gates", "coverage", "covered", "uncovered"})
_LIVE_KEYS = (
    "live_gate", "live_check", "runs_check",
    "ran_check", "run_check", "verifies_now",
    "verified_live", "verify_live", "measures_live",
    "measured_live", "passes_gate", "passed_gate",
    "pass_gate", "opens_browser", "launches_reader",
    "starts_reader", "performs_check",
    "performed_check", "opens_network", "writes_file",
    "write_file", "renders_now", "posts_note", "posted_note",
    "shows_gate", "shown_gate")


# ---------------------------------------------------------------------
# Small judges, in the sibling shape.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_evidence(value: Any) -> str:
    """Held held evidence: named as data, or honestly empty.

    An gate naming no held evidence is held with
    empty words and stands incomplete in its
    gaps; words that are not a string at all
    refuse.
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError("evidence must be a string naming the held evidence")
    return value.strip()


def _check_measure(value: Any, what: str) -> str:
    """A held measure: a measure, named as data or honestly empty.

    An gate whose measure is not known is
    held with an empty measure: unknown stays unknown,
    and no key is invented for it. A measure that
    is not a string at all refuses.
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
                f"{what} claims a live verification execution "
                f"({key!r} is named on it): "
                f"{VERIFY_RULE}")
    for key in mapping:
        if key in _DERIVED_KEYS:
            raise ValueError(
                f"{what} carries {key!r}, which is derived from its "
                f"own fields and never stored")
        if key not in allowed:
            raise ValueError(f"{what} carries unknown field {key!r}")


def normalize_kind(value: Any) -> str:
    kind = _clean_text(value, "a kind").lower()
    if kind not in KINDS:
        raise ValueError(
            f"kind {kind!r} is not one of the named kinds: "
            + ", ".join(KINDS))
    return kind


def normalize_stance(value: Any) -> str:
    stance = _clean_text(value, "an stance").lower()
    if stance not in STANCES:
        raise ValueError(
            f"stance {stance!r} is not one of the held "
            f"notes: " + ", ".join(STANCES))
    return stance


def normalize_view_filter(value: Any) -> str:
    view_filter = _clean_text(value, "a view filter").lower()
    if view_filter not in VIEW_FILTERS:
        raise ValueError(
            f"view filter {view_filter!r} is not one of the held "
            f"filters: " + ", ".join(VIEW_FILTERS))
    return view_filter


# ---------------------------------------------------------------------
# The held gate: one door, with the words that find it.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class GateCard:
    """One undo gate, held as data with its held evidence.

    The gate names its plain title, the kind it
    lives in - one of the closed kind vocabulary -
    its measure, the held evidence it carries, named
    as data, and its detail. An gate naming no
    held evidence is held with empty words: it stands
    incomplete, named in its gaps, and no words are
    invented for it. The gate is local data alone -
    no live execution stands behind it: holding it
    executes nothing.
    """

    gate_id: str
    seq: int
    title: str
    kind: str
    measure: str = ""
    evidence: str = ""
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "gate_id", _clean_text(self.gate_id, "a gate id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a title"))
        object.__setattr__(self, "kind", normalize_kind(self.kind))
        object.__setattr__(
            self, "measure", _check_measure(self.measure, "a measure"))
        object.__setattr__(
            self, "evidence", _check_evidence(self.evidence))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a gate detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.gate_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "gate_id": self.gate_id, "seq": self.seq,
            "title": self.title, "kind": self.kind,
            "measure": self.measure,
            "evidence": self.evidence, "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_gate_ref(value: Any) -> GateCard:
    if not isinstance(value, GateCard):
        raise ValueError("a gate must be a GateCard")
    return value


def validate_gate(gate: Any) -> GateCard:
    return _check_gate_ref(gate)


def build_gate(record: Any = None, **kwargs: Any) -> GateCard:
    """Build one held gate from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, GateCard):
        if kwargs:
            raise ValueError("a gate stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a gate must be a mapping or a GateCard")
    _needed(data, _PANE_KEYS, "a gate")
    return GateCard(
        gate_id=data.get("gate_id"), seq=data.get("seq"),
        title=data.get("title"), kind=data.get("kind"),
        measure=data.get("measure"),
        evidence=data.get("evidence"), detail=data.get("detail"),
        **_provenance(data))


def gate_gaps(gate: Any) -> Tuple[str, ...]:
    """The gaps that keep a gate from completeness."""
    checked = _check_gate_ref(gate)
    return () if checked.evidence else ("no held evidence",)


def gate_passes(gate: Any) -> bool:
    return not gate_gaps(gate)


def plain_lines(gate: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the gate's own fields."""
    checked = _check_gate_ref(gate)
    return (
        f"Gate: {checked.title}",
        f"Kind: {checked.kind}",
        f"Measure: {checked.measure if checked.measure else 'unknown'}",
        f"Evidence: {checked.evidence if checked.evidence else 'none'}",
    )


def segment_of(gate: Any) -> str:
    checked = _check_gate_ref(gate)
    gaps = gate_gaps(checked)
    return (
        f"{checked.gate_id}: {checked.title} - kind: "
        f"'{checked.kind}' - measure: "
        f"'{checked.measure if checked.measure else 'unknown'}' - "
        f"evidence: '{checked.evidence if checked.evidence else 'none'}' - "
        f"detail: '{checked.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held stance: a note on a gate, as data.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One undo note, held as data.

    The record names its gate, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per gate
    stance in a book. The record is data alone:
    holding it executes no command and runs no
    action, ever.
    """

    note_id: str
    seq: int
    gate_id: str
    stance: str
    target: str
    title: str
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "note_id", _clean_text(self.note_id, "a stance id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "gate_id", _clean_text(self.gate_id, "a gate id"))
        object.__setattr__(self, "stance", normalize_stance(self.stance))
        object.__setattr__(
            self, "target", _clean_text(self.target, "an stance target"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a stance title"))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a stance detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.note_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "note_id": self.note_id, "seq": self.seq,
            "gate_id": self.gate_id, "stance": self.stance,
            "target": self.target, "title": self.title,
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_note_ref(value: Any) -> NoteRecord:
    if not isinstance(value, NoteRecord):
        raise ValueError("a stance must be a NoteRecord")
    return value


def validate_note(stance: Any) -> NoteRecord:
    return _check_note_ref(stance)


def build_note(stance: Any = None, **kwargs: Any) -> NoteRecord:
    if stance is None:
        data = dict(kwargs)
    elif isinstance(stance, NoteRecord):
        if kwargs:
            raise ValueError("a stance stands whole or by fields, not both")
        return stance
    elif isinstance(stance, dict):
        data = dict(stance)
        data.update(kwargs)
    else:
        raise ValueError("a stance must be a mapping or a NoteRecord")
    _needed(data, _ACTION_KEYS, "a stance")
    return NoteRecord(
        note_id=data.get("note_id"), seq=data.get("seq"),
        gate_id=data.get("gate_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held view: which gates a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class AccessView:
    """A view over the book: every gate, the ready, the rest."""

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


def _check_view_ref(value: Any) -> AccessView:
    if not isinstance(value, AccessView):
        raise ValueError("a view must be a AccessView")
    return value


def validate_view(view: Any) -> AccessView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> AccessView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, AccessView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or a AccessView")
    _needed(data, _VIEW_KEYS, "a view")
    return AccessView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


def inspect_gate_source(piece: Any) -> Dict[str, Any]:
    """Name what one gate source piece is, without judging it."""
    if isinstance(piece, GateCard):
        return {"kind": "gate", "gate_id": piece.gate_id}
    if isinstance(piece, dict):
        if "note_id" in piece:
            return {"kind": "note", "note_id": piece.get("note_id")}
        if "view_id" in piece:
            return {"kind": "view", "view_id": piece.get("view_id")}
        if "gate_id" in piece:
            return {"kind": "gate", "gate_id": piece.get("gate_id")}
    return {"kind": "unknown", "gate_id": None}


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class AccessPanelRow:
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


def _row_for_gate(gate: GateCard) -> AccessPanelRow:
    return AccessPanelRow(
        item_id=gate.gate_id,
        standing="ready" if gate_passes(gate) else "unready",
        label=gate.title, segment=segment_of(gate),
        recorded_on=gate.recorded_on)


def _check_row_ref(value: Any) -> AccessPanelRow:
    if not isinstance(value, AccessPanelRow):
        raise ValueError("a panel row must be a AccessPanelRow")
    return value


def validate_row(row: Any, gate: Any = None) -> AccessPanelRow:
    checked = _check_row_ref(row)
    if gate is not None:
        derived = _row_for_gate(_check_gate_ref(gate))
        if checked != derived:
            raise ValueError(
                f"panel row {checked.item_id!r} does not agree with "
                f"the row derived from its gate")
    return checked


def build_row(row: Any = None, gate: Any = None,
              **kwargs: Any) -> AccessPanelRow:
    if gate is not None:
        derived = _row_for_gate(_check_gate_ref(gate))
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            AccessPanelRow(**kwargs))
        return validate_row(built, gate)
    if isinstance(row, AccessPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in READY_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return AccessPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return AccessPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or a AccessPanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[AccessPanelRow, ...]
                 ) -> Tuple[TargetCount, ...]:
    counts: List[TargetCount] = []
    for standing in READY_WORDS:
        number = sum(1 for row in rows if row.standing == standing)
        if number:
            counts.append(TargetCount(standing=standing, items=number))
    return tuple(counts)


def _panel_account(total_items: int, total_shown: int,
                   passing_shown: int,
                   target_counts: Tuple[TargetCount, ...],
                   view_filter: str, as_of: str) -> Tuple[str, ...]:
    standing_words = ", ".join(
        f"{count.standing} {count.items}"
        for count in target_counts) or "none"
    return (
        f"The Accessibility verification book holds {total_items} gates as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {passing_shown} of the shown gates "
        f"stand ready.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its gate's own fields "
        "- the title, the kind, the measure honestly held "
        "and the held evidence it honestly carries - and no "
        "judgement is stored on any gate.",
        "Completeness is judged from the held records alone: "
        "a gate naming no held evidence stands unready, and the "
        "undo index is derived from the held gates, "
        "never stored where it could drift.",
    )


@dataclass(frozen=True)
class AccessPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[AccessPanelRow, ...]
    total_items: int
    total_shown: int
    target_counts: Tuple[TargetCount, ...]
    as_of: str
    account: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "panel_id": self.panel_id, "view_id": self.view_id,
            "view_filter": self.view_filter,
            "rows": [row.to_record() for row in self.rows],
            "total_items": self.total_items,
            "total_shown": self.total_shown,
            "target_counts": [c.to_record() for c in self.target_counts],
            "as_of": self.as_of, "account": list(self.account),
        }


def _resolve_view(source: Any, view: Any) -> AccessView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, AccessView):
        return view
    return book.view_for(view)


def shown_gates(source: Any, view: Any = None
                   ) -> Tuple[GateCard, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.gates
    if resolved.view_filter == "ready":
        return tuple(g for g in book.gates if gate_passes(g))
    return tuple(g for g in book.gates if not gate_passes(g))


def gates_for_kind(source: Any, kind: Any
                      ) -> Tuple[GateCard, ...]:
    wanted = normalize_kind(kind)
    return tuple(
        g for g in _source_book(source).gates if g.kind == wanted)


def passing_gates(source: Any) -> Tuple[GateCard, ...]:
    return tuple(
        g for g in _source_book(source).gates if gate_passes(g))


def total_gates(source: Any) -> int:
    return len(_source_book(source).gates)


def derive_panel(source: Any, view: Any = None) -> AccessPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_gates(book, resolved)
    rows = tuple(_row_for_gate(gate) for gate in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.gates), default="")
    passing = sum(1 for g in shown if gate_passes(g))
    return AccessPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.gates), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.gates), len(shown), passing, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> AccessPanel:
    if not isinstance(value, AccessPanel):
        raise ValueError("a panel must be a AccessPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> AccessPanel:
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
                     "total_shown", "target_counts", "as_of", "account"):
            if getattr(checked, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {checked.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return checked


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> AccessPanel:
    if isinstance(panel, AccessPanel):
        if kwargs:
            raise ValueError("a panel stands whole or by fields, not both")
        return validate_panel(panel, source)
    if isinstance(panel, dict):
        data = dict(panel)
        data.update(kwargs)
        rows = tuple(build_row(row) for row in data.get("rows") or ())
        counts = tuple(
            TargetCount(
                standing=_clean_text(
                    c.get("standing"), "a standing count word").lower(),
                items=_check_count(c.get("items"), "a standing count"))
            for c in data.get("target_counts") or ()
            if isinstance(c, dict))
        built = AccessPanel(
            panel_id=_clean_text(data.get("panel_id"), "a panel id"),
            view_id=data.get("view_id"),
            view_filter=normalize_view_filter(data.get("view_filter")),
            rows=rows,
            total_items=_check_count(
                data.get("total_items"), "a total_items count"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            target_counts=counts,
            as_of=_clean_text(data.get("as_of"), "an as_of day"),
            account=_check_lines(data.get("account"), "the account"))
        return validate_panel(built, source)
    if panel is None and source is not None:
        return derive_panel(source, kwargs.get("view"))
    raise ValueError("a panel must be a mapping, a AccessPanel, or derived")


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
class AccessVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> AccessVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_gates(book, resolved)
    passing = sum(1 for g in shown if gate_passes(g))
    latest = max((g.recorded_on for g in shown), default="")
    return AccessVerdict(
        verdict=_verdict_word(len(shown), passing),
        view_id=resolved.view_id, total_shown=len(shown),
        passing_shown=passing, latest_on=latest)


def _check_verdict_ref(value: Any) -> AccessVerdict:
    if not isinstance(value, AccessVerdict):
        raise ValueError("a verdict must be a AccessVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> AccessVerdict:
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
                  **kwargs: Any) -> AccessVerdict:
    if isinstance(verdict, AccessVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = AccessVerdict(
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
        "a verdict must be a mapping, a AccessVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held gates' words at call time, and
# the stance targets: which gate notes the book holds, derived too.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexEntry:
    evidence: str
    gate_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "evidence": self.evidence, "gate_id": self.gate_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class AccessIndex:
    """The undo index, derived from the held gates.

    The index names one gate per complete gate, in
    held order - the gate's own held evidence, its id and
    its title - and the gates that stand incomplete,
    named in its gaps. Nothing here is stored on any
    gate: the index is derived at call time from the
    held records alone, so it can never drift from them.
    """

    gates: Tuple[IndexEntry, ...]
    gaps: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "gates": [e.to_record() for e in self.gates],
            "gaps": list(self.gaps),
        }


def derive_index(source: Any) -> AccessIndex:
    """Derive the undo index from the book's held gates."""
    book = _source_book(source)
    gates = tuple(
        IndexEntry(evidence=g.evidence, gate_id=g.gate_id, title=g.title)
        for g in book.gates if gate_passes(g))
    gaps = tuple(
        g.gate_id for g in book.gates if not gate_passes(g))
    return AccessIndex(gates=gates, gaps=gaps)


def gate_for_evidence(source: Any, evidence: Any) -> Optional[GateCard]:
    """The first held gate one set of words reaches, or none - honestly."""
    wanted = _check_evidence(evidence)
    if not wanted:
        return None
    for gate in _source_book(source).gates:
        if gate.evidence == wanted:
            return gate
    return None


def note_for_gate(source: Any, gate_id: Any,
                       stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one gate (and stance, when named)."""
    wanted = _clean_text(gate_id, "a gate id")
    for record in _source_book(source).notes:
        if record.gate_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the gate targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


# ---------------------------------------------------------------------
# The book: gates, views and notes held together, one pinned panel
# at most per telling, and no verdict or index ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class AccessBook:
    title: str
    gates: Tuple[GateCard, ...] = ()
    views: Tuple[AccessView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    panels: Tuple[AccessPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        gates = tuple(_check_gate_ref(g) for g in self.gates)
        views = tuple(_check_view_ref(v) for v in self.views)
        notes = tuple(_check_note_ref(m) for m in self.notes)
        panels = tuple(_check_panel_ref(p) for p in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for gate in gates:
            if gate.gate_id in seen_ids:
                raise ValueError(
                    f"two gates stand under id {gate.gate_id!r}")
            if gate.seq in seen_seqs:
                raise ValueError(
                    f"two gates stand at sequence {gate.seq}")
            seen_ids.add(gate.gate_id)
            seen_seqs.add(gate.seq)
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
        note_ids = set()
        note_seqs = set()
        note_targets = set()
        for record in notes:
            if record.note_id in note_ids:
                raise ValueError(
                    f"two notes stand under id {record.note_id!r}")
            if record.seq in note_seqs:
                raise ValueError(
                    f"two notes stand at sequence {record.seq}")
            target = (record.gate_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for gate "
                    f"{record.gate_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per gate target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        object.__setattr__(
            self, "gates", tuple(sorted(gates, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.gates + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.gate_id for g in self.gates) + tuple(
            v.view_id for v in self.views)

    def gate_ids(self) -> Tuple[str, ...]:
        return tuple(g.gate_id for g in self.gates)

    def gate_for(self, gate_id: Any) -> GateCard:
        wanted = _clean_text(gate_id, "a gate id")
        for gate in self.gates:
            if gate.gate_id == wanted:
                return gate
        raise KeyError(f"no gate named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> AccessView:
        wanted = _clean_text(view_id, "a view id")
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no view named {wanted!r} stands in this book")

    def note_for(self, note_id: Any) -> NoteRecord:
        wanted = _clean_text(note_id, "a stance id")
        for record in self.notes:
            if record.note_id == wanted:
                return record
        raise KeyError(f"no stance named {wanted!r} stands in this book")

    def item_for(self, item_id: Any) -> Any:
        wanted = _clean_text(item_id, "an item id")
        for gate in self.gates:
            if gate.gate_id == wanted:
                return gate
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "gates": [g.to_record() for g in self.gates],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "panels": [p.to_record() for p in self.panels],
        }


def _judge_book_panels(book: AccessBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: AccessBook) -> None:
    if book.title != "Accessibility verification at the M-198 slice boundary":
        raise ValueError("the shipped example book carries another title")
    if len(book.gates) != 6 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold six gates and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m198-boundary":
        raise ValueError("the pinned panel is panel-m198-boundary")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "strained" or verdict.passing_shown != 5:
        raise ValueError("the shipped example book verdict must stand strained at five ready of six")
    index = derive_index(book)
    if [e.evidence for e in index.gates] != ["the task completed by keyboard alone", "body text clears the AA bar", "the face stands still on request", "meaning survives without colour", "focus stays visible throughout"]:
        raise ValueError("the shipped example book index must derive the five held evidences in held order")
    if index.gaps != ("gate-reader-main",):
        raise ValueError("the shipped example book must leave the quiet gate honestly incomplete, named in its gaps")
    found = gate_for_evidence(book, EXAMPLE_EVIDENCE)
    if found is None or found.gate_id != "gate-keyboard-main":
        raise ValueError("the shipped example book must reach its editor gate under the example evidence")
    first = first_note(book)
    if first is None or first.note_id != "note-note-keyboard":
        raise ValueError("the shipped example book must hold the editor note as its first note road")



def validate_book(data: Any, *, require_example: bool = False) -> AccessBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, AccessBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a verification book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live verification execution "
                f"({key!r} is named on it): {VERIFY_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its gates under a view")
    if "verify_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held gates at call time")
    if data.get("schema") is not None and (
            data["schema"] != ACCESSIBILITY_VERIFICATION_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{ACCESSIBILITY_VERIFICATION_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != ACCESSIBILITY_VERIFICATION_SLICE):
        raise ValueError(
            f"a book's slice must be {ACCESSIBILITY_VERIFICATION_SLICE!r}")
    head = data.get("accessibility_verification") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's undo head must be a mapping")
    title = head.get("title") or data.get("title")
    gates = tuple(build_gate(g) for g in data.get("gates") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    book = AccessBook(
        title=title, gates=gates, views=views, notes=notes, panels=())
    panels = tuple(
        build_panel(p, book) for p in data.get("panels") or ())
    book = AccessBook(
        title=book.title, gates=book.gates, views=book.views,
        notes=book.notes, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> AccessBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (AccessBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or a AccessBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> AccessBook:
    return validate_book(data, require_example=require_example)


def load_accessibility_verification(
        data: Optional[Dict[str, Any]] = None) -> AccessBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(ACCESSIBILITY_VERIFICATION_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_accessibility_verification_file(path: Any) -> AccessBook:
    """Load one undo file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: gates and views held one by one.
# ---------------------------------------------------------------------

class AccessVerifyRegistry:
    """An in-memory holding of gates and views.

    The registry is the pure layer's model of a
    session's verification book: gates are held under
    their ids, one gate per id and per sequence,
    and views are held in recorded order, one view
    per sequence and per id. Holding is data only -
    nothing held here executes a command, runs an
    action, or navigates anywhere.
    """

    def __init__(self, book: Any = None) -> None:
        self._gates: List[GateCard] = []
        self._views: List[AccessView] = []
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

    def register_gate(self, item: Any) -> GateCard:
        """Hold one gate, judged whole before held."""
        checked = _check_gate_ref(item)
        return self._register(
            self._gates, checked, "gate_id", "gate")

    def register_view(self, view: Any) -> AccessView:
        """Hold one view; a view naming no id takes a fresh one."""
        checked = _check_view_ref(view)
        if not checked.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            checked = build_view({**checked.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, checked, "view_id", "view")

    def register_book(self, book: Any) -> AccessBook:
        """Hold a whole book's gates and views, under its title."""
        checked = build_book(book)
        if self._title is not None and checked.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {checked.title!r}")
        for gate in checked.gates:
            self.register_gate(gate)
        for view in checked.views:
            self.register_view(view)
        self._title = checked.title
        return self.book()

    def book(self) -> AccessBook:
        return AccessBook(
            title=self._title or "An unheld verification book",
            gates=tuple(self._gates), views=tuple(self._views),
            notes=(), panels=())

    def list_gates(self) -> Tuple[GateCard, ...]:
        return tuple(self._gates)

    def list_views(self) -> Tuple[AccessView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._gates) + tuple(self._views)

    def get_gate(self, gate_id: Any) -> GateCard:
        return self.book().gate_for(gate_id)

    def get_view(self, view_id: Any) -> AccessView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records shaped for the journal target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> AccessBook:
    if source is None:
        return load_accessibility_verification()
    if isinstance(source, AccessBook):
        return source
    if isinstance(source, AccessVerifyRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def gate_record(gate: Any, source: Any = None) -> Dict[str, Any]:
    checked = _check_gate_ref(gate)
    record = {
        "type": "verify_gate",
        "slice": ACCESSIBILITY_VERIFICATION_SLICE,
        "gate_id": checked.gate_id,
        "title": checked.title,
        "segment": segment_of(checked),
        "passes": gate_passes(checked),
        "gaps": list(gate_gaps(checked)),
    }
    record.update(_provenance_record(checked))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    checked = _check_view_ref(view)
    record = {
        "type": "verify_view",
        "slice": ACCESSIBILITY_VERIFICATION_SLICE,
        "view_id": checked.view_id, "seq": checked.seq,
        "view_filter": checked.view_filter,
    }
    record.update(_provenance_record(checked))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    checked = _check_note_ref(record_in)
    record = {
        "type": "verify_note",
        "slice": ACCESSIBILITY_VERIFICATION_SLICE,
        "note_id": checked.note_id,
        "gate_id": checked.gate_id,
        "stance": checked.stance,
    }
    record.update(_provenance_record(checked))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    checked = validate_panel(panel, source)
    record = {"type": "verify_panel",
              "slice": ACCESSIBILITY_VERIFICATION_SLICE}
    record.update(checked.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, AccessVerdict):
        checked = validate_verdict(verdict, source)
    else:
        checked = derive_verdict(_source_book(verdict), view)
    record = {"type": "verify_verdict",
              "slice": ACCESSIBILITY_VERIFICATION_SLICE}
    record.update(checked.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, AccessIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "verify_index",
              "slice": ACCESSIBILITY_VERIFICATION_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    checked = _source_book(book)
    record = {"type": "verify_book",
              "slice": ACCESSIBILITY_VERIFICATION_SLICE,
              "title": checked.title}
    record.update(checked.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(gate: Any, source: Any = None) -> str:
    checked = _check_gate_ref(gate)
    return (
        f"{checked.title} - kind {checked.kind}: "
        f"measure {checked.measure if checked.measure else 'unknown'}, "
        f"evidence {checked.evidence if checked.evidence else 'none'}. "
        f"{checked.detail}")


def gate_plain_words(gate: Any, source: Any = None) -> str:
    return plain_words(gate, source)


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The accessibility verification stands {verdict.verdict}: "
        f"{verdict.passing_shown} of {verdict.total_shown} shown "
        f"gates stand ready.")


def view_plain_words(view: Any) -> str:
    checked = _check_view_ref(view)
    return f"View {checked.view_id}: shows {checked.view_filter} gates."


def note_plain_words(record_in: Any) -> str:
    checked = _check_note_ref(record_in)
    return (
        f"Note {checked.note_id}: {checked.stance} "
        f"{checked.gate_id}, toward {checked.target}. "
        f"{checked.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, AccessIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.gates)} held evidence for "
        f"{len(index.gates)} gates; incomplete, named in "
        f"its gaps: {gaps}.")


def format_gate(gate: Any, source: Any = None) -> str:
    checked = _check_gate_ref(gate)
    lines = [f"{checked.title} ({checked.gate_id})"]
    lines.extend(plain_lines(checked))
    lines.append(checked.detail)
    if gate_passes(checked):
        lines.append(
            "This gate stands ready - it carries the evidence "
            "its record names.")
    else:
        lines.append(
            "This gate stands unready - it names no held "
            "evidence, stands named in its gaps, and no evidence is "
            "invented for it.")
    return "\n".join(lines)


def format_view(view: Any) -> str:
    checked = _check_view_ref(view)
    return (
        f"View {checked.view_id}: filter {checked.view_filter} - "
        f"{checked.detail}")


def format_note(record_in: Any) -> str:
    checked = _check_note_ref(record_in)
    lines = [
        f"Verify note {checked.stance} {checked.gate_id} "
        f"({checked.note_id}): {checked.title}. {checked.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or reading it executes no command, runs no action "
        "and posts no note.")
    return "\n".join(lines)


def format_evidence(source: Any, evidence: Any) -> str:
    gate = gate_for_evidence(source, evidence)
    if gate is not None:
        return format_gate(gate)
    wanted = _check_evidence(evidence)
    return (
        f"No held gate stands under evidence {wanted!r} yet - the "
        f"evidence reaches nothing in this book, and no gate is "
        f"invented for them.")


def format_book(source: Any = None, kind: Any = None) -> str:
    book = _source_book(source)
    gates = (gates_for_kind(book, kind)
                if kind is not None else book.gates)
    lines = [f"Accessibility Verification (M-199) - {book.title}"]
    lines.extend(segment_of(gate) for gate in gates)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Undo panel under view {panel.view_id}:"]
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
    lines = ["Verify index, derived from the held gates:"]
    for gate in index.gates:
        lines.append(f"{gate.evidence} - {gate.title} ({gate.gate_id})")
    if index.gaps:
        lines.append(
            "Incomplete, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "executes no command and opens no network.")
    return "\n".join(lines)


def format_verify_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "Accessibility Verification (M-199)",
        f"{book.title}: {len(book.gates)} gates held, "
        f"{len(passing_gates(book))} gates standing ready, "
        f"{len(book.notes)} notes held.",
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


def parse_verify_args(args: Any) -> Tuple[str, Any]:
    """Parse the /accessverify grammar into (action, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("gate", "view", "note"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("evidence", "kind"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("index", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
