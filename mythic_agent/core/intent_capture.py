"""Intent capture (PROJECT_FORGE form) (roadmap slice M-202).

Part IX - The Mythic Method Engine. The roadmap
words: *a new project opens with what/why/success
in the user's plain words, stored verbatim; the
coder's plan must cite it.*

What already ships, and what this slice adds:

* The M-201 campaigns book holds a campaign as
  data, and the M-005 method charter names the
  whole of Part IX (M-201-M-232) as the part that
  executes it. What nothing held is *the intent
  itself as a book*: the PROJECT_FORGE form a new
  project opens with - what the user wants, why
  they want it, and what success looks like, in
  the user's own plain words, held as checkable
  data beside the coder plan that must cite it.
  This slice is that book, in its own module,
  standing in the M-195 copy-and-share book shape
  the M-201 book stands in.

* No charter row names this slice: the M-171 TUI
  redesign charter binds Part VIII alone (M-172 to
  M-200) and names M-202 on no row, and the slice
  tests pin that absence live. The M-005 method
  charter names no slice row either: its own words
  name the whole of Part IX as the part that
  executes the charter, and this slice is built
  to the roadmap words and that execution note
  together.

* An intent is held whole: the project it opens,
  and what, why and success in the user's plain
  words, stored VERBATIM - the exact string the
  user gave, never stripped, normalised, summarised
  or rewritten by this layer. A field that is not
  a string, or that carries no words at all,
  refuses by name; a field carrying words stands
  exactly as given, spaces and capitals and all.
* The coder's plan must cite the intent. The plan's
  citation is held as data on the intent record:
  the exact words the plan cites. The citation
  check is DERIVED at call time from the stored
  words alone: a plan carrying no citation stands
  uncited, named in its gaps; a plan citing words
  that stand nowhere in the stored what, why or
  success stands uncited too, named in its gaps
  beside it - the citation must stand verbatim in
  one of the three fields, and the field it stands
  in is derived and told, never stored.
* The intent index is DERIVED at call time from
  the held intents - one entry per intent whose
  plan cites it, under its own citation - never a
  second stored copy that could drift. A stored
  index, citation verdict, panel or current-intent
  claim on any record refuses by name.
* The current intent is DERIVED at call time - the
  first held intent, in held order, whose plan does
  not yet cite it - never stored where it could go
  stale: that is where the next plan must look.
* The notes are held as data: a note record naming
  its intent, its stance - note, concern, praise,
  question, a closed vocabulary - and what it feeds
  back toward, one record per intent stance;
  holding a note posts none of it, the rule stands
  as data (:data:`INTENT_RULE`), and a record
  claiming a project was actually opened, a plan
  actually run or executed live, or a push actually
  made, refuses BY NAME.
* The shipped data file holds one example book in
  exactly the shape a real intent file takes, a
  loader reads an intent file anywhere on disk,
  intents and views are shaped as session news, and
  a small in-memory registry holds records one by
  one. The agent layer owns holding an intent book
  for a session and telling from it. This layer
  reaches no live road: it opens no project, runs
  no plan, executes nothing, pushes nothing and
  opens no network - it holds intents as data and
  tells them.

Honesty rules, enforced here and pinned by tests:

* **Verbatim means verbatim.** What, why and
  success stand exactly as the user gave them;
  no telling rewords them, and the citation check
  reads the stored words themselves.
* **A plan must cite the intent.** A plan carrying
  no citation stands uncited, named in its gaps -
  no citation is invented for it.
* **Cited words must stand in the intent.** A
  citation that stands in none of the stored what,
  why or success stands flagged by name - it cites
  words the user never gave.
* **Unknown stays unknown.** An intent whose plan
  citation is not yet held stands with its citation
  empty - no words are invented for it.
* **The index, panel, verdict and current intent
  are derived, never stored.** Each is derived
  from the held intents at call time; a stored one
  refuses by name, so it can never drift.
* **One intent per intent.** Two intents standing
  for one intent id refuse by name, and one note
  record stands per intent stance.
* **The notes are data alone.** The records hold
  the feedback; holding, viewing or telling them
  opens nothing, plans nothing and posts nothing.
"""


from __future__ import annotations

__all__ = [
    "CITATION_FIELDS",
    "EXAMPLE_CITATION",
    "STANCES",
    "INDEX_ACTION",
    "INTENT_RESOURCE",
    "INTENT_SCHEMA",
    "INTENT_SLICE",
    "INTENT_RULE",
    "PLAIN_EXPLANATION",
    "THE_INTENT_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "CITING_WORDS",
    "Any",
    "Dict",
    "List",
    "Optional",
    "IntentRecord",
    "IndexEntry",
    "NoteRecord",
    "IntentBook",
    "IntentIndex",
    "IntentPanel",
    "IntentPanelRow",
    "IntentRegistry",
    "IntentVerdict",
    "IntentView",
    "TargetCount",
    "board_record",
    "book_record",
    "build_book",
    "build_intent",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "citation_field",
    "current_intent",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "first_note",
    "format_book",
    "format_citation",
    "format_index",
    "format_intent",
    "format_intent_screen",
    "format_note",
    "format_panel",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "intent_for_citation",
    "intent_record",
    "intents_for_project",
    "load_intents",
    "load_intents_file",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_intent",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_intent_args",
    "passing_intents",
    "plain_lines",
    "plain_words",
    "roadmap_record",
    "segment_of",
    "shown_intents",
    "validate_book",
    "validate_intent",
    "validate_note",
    "validate_panel",
    "validate_row",
    "validate_verdict",
    "validate_view",
    "verdict_plain_words",
    "verdict_record",
    "view_plain_words",
    "view_record",
    "intent_gaps",
    "intent_cites",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

INTENT_SCHEMA = "mythic.intent_capture/1"
INTENT_SLICE = "M-202"
THE_INTENT_SLICE = INTENT_SLICE
INTENT_RESOURCE = "intent_capture.yaml"
INDEX_ACTION = "index"
EXAMPLE_CITATION = "my own words for what, why and success"
CITATION_FIELDS = ("what", "why", "success")
CITING_WORDS = ("citing", "uncited")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "citing", "uncited")
VERDICT_WORDS = ("open", "strained", "shut")
INTENT_RULE = (
    "intents are held as data alone: what, why "
    "and success stand in the user's plain words, "
    "stored verbatim and never rewritten; holding, "
    "viewing and reading an intent opens no "
    "project, runs no plan, executes nothing and "
    "opens no network - a plan is judged from the "
    "citation it carries against the stored words "
    "alone, never claimed live")
PLAIN_EXPLANATION = (
    "Intent capture (M-202): a new project opens "
    "with what, why and success in the user's "
    "plain words, stored verbatim (the "
    "PROJECT_FORGE form); the coder's plan must "
    "cite the intent, and a plan citing no intent "
    "- or words that are not in it - stands "
    "flagged by name.")
USAGE = (
    "Usage: /intent | /intent intent <intent-id> | "
    "/intent citation <citation> | /intent project <project> | "
    "/intent view <view-id> | /intent note <note-id> | "
    "/intent index | /intent panel | /intent verdict")

_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_INTENT_KEYS = frozenset({
    "intent_id", "seq", "project", "what", "why", "success",
    "citation", "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "intent_id", "stance", "target", "title",
    "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "standing", "cites", "citing", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "entries", "coverage", "covered", "uncovered",
    "current_intent", "next_intent", "progress", "board",
    "current", "citation_field", "cited_in"})
_LIVE_KEYS = (
    "live_intent", "live_plan", "plans_live",
    "planned_live", "runs_plan", "ran_plan",
    "runs_live", "executes_plan", "executed_plan",
    "executes_live", "live_execution",
    "opens_project", "opened_project",
    "creates_project", "created_project",
    "starts_project", "started_project",
    "banks_intent", "banked_live", "banking_live",
    "pushes_intent", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_intent", "sent_intent",
    "posts_note", "posted_note")


# ---------------------------------------------------------------------
# Small judges, in the sibling shape.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _verbatim_text(value: Any, what: str) -> str:
    """The user's own words, stored VERBATIM.

    The field must be a string carrying words; the
    string itself stands exactly as given - never
    stripped, normalised or rewritten - because the
    intent is the user's words, not a telling of
    them.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be the user's words, as a non-empty string")
    return value


def _check_citation(value: Any) -> str:
    """A held plan citation: words named as data, or honestly empty.

    A plan whose citation is not yet held is held
    with an empty citation and stands uncited in its
    gaps; a citation that is not a string at all
    refuses.
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError("citation must be a string naming the words the plan cites")
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
                f"{what} claims a live project opening or plan "
                f"execution ({key!r} is named on it): "
                f"{INTENT_RULE}")
    for key in mapping:
        if key in _DERIVED_KEYS:
            raise ValueError(
                f"{what} carries {key!r}, which is derived from its "
                f"own fields and never stored")
        if key not in allowed:
            raise ValueError(f"{what} carries unknown field {key!r}")


def normalize_stance(value: Any) -> str:
    stance = _clean_text(value, "a stance").lower()
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
# The held intent: one PROJECT_FORGE form, with the plan citation.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IntentRecord:
    """One intent, held as data with its plan's citation.

    The intent names the project it opens, and what,
    why and success in the user's plain words -
    stored verbatim, exactly as given - and the
    citation the coder's plan carries, named as
    data. A plan carrying no citation is held with
    an empty citation: it stands uncited, named in
    its gaps, and no citation is invented for it. A
    plan citing words that stand in none of the
    stored what, why or success stands uncited too.
    The intent is local data alone - no live project
    or plan stands behind it: holding it opens
    nothing and runs nothing.
    """

    intent_id: str
    seq: int
    project: str
    what: str
    why: str
    success: str
    citation: str = ""
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "intent_id", _clean_text(self.intent_id, "an intent id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "project", _clean_text(self.project, "a project"))
        object.__setattr__(
            self, "what", _verbatim_text(self.what, "the what, in the user's words"))
        object.__setattr__(
            self, "why", _verbatim_text(self.why, "the why, in the user's words"))
        object.__setattr__(
            self, "success", _verbatim_text(self.success, "the success, in the user's words"))
        object.__setattr__(
            self, "citation", _check_citation(self.citation))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an intent detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.intent_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "intent_id": self.intent_id, "seq": self.seq,
            "project": self.project, "what": self.what,
            "why": self.why, "success": self.success,
            "citation": self.citation, "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_intent_ref(value: Any) -> IntentRecord:
    if not isinstance(value, IntentRecord):
        raise ValueError("an intent must be an IntentRecord")
    return value


def validate_intent(intent: Any) -> IntentRecord:
    return _check_intent_ref(intent)


def build_intent(record: Any = None, **kwargs: Any) -> IntentRecord:
    """Build one held intent from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, IntentRecord):
        if kwargs:
            raise ValueError("an intent stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("an intent must be a mapping or an IntentRecord")
    _needed(data, _INTENT_KEYS, "an intent")
    return IntentRecord(
        intent_id=data.get("intent_id"), seq=data.get("seq"),
        project=data.get("project"), what=data.get("what"),
        why=data.get("why"), success=data.get("success"),
        citation=data.get("citation"), detail=data.get("detail"),
        **_provenance(data))


def citation_field(intent: Any) -> Optional[str]:
    """The stored field the plan's citation stands in, DERIVED.

    The citation must stand verbatim in the stored
    what, why or success; the first field, in form
    order, that holds it is the field it cites. A
    plan carrying no citation, or citing words held
    nowhere, cites no field and stands None here.
    """
    checked = _check_intent_ref(intent)
    if not checked.citation:
        return None
    for name in CITATION_FIELDS:
        if checked.citation in getattr(checked, name):
            return name
    return None


def intent_gaps(intent: Any) -> Tuple[str, ...]:
    """The gaps that keep an intent's plan from standing citing."""
    checked = _check_intent_ref(intent)
    if not checked.citation:
        return ("the plan cites no intent",)
    if citation_field(checked) is None:
        return ("the plan cites words not in the stored intent",)
    return ()


def intent_cites(intent: Any) -> bool:
    return not intent_gaps(intent)


def plain_lines(intent: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the intent's own fields.

    What, why and success are told verbatim - the
    stored strings themselves, never a rewording.
    """
    checked = _check_intent_ref(intent)
    return (
        f"Intent: {checked.project}",
        f"What: {checked.what}",
        f"Why: {checked.why}",
        f"Success: {checked.success}",
        f"Citation: {checked.citation if checked.citation else 'none'}",
    )


def segment_of(intent: Any) -> str:
    checked = _check_intent_ref(intent)
    gaps = intent_gaps(checked)
    return (
        f"{checked.intent_id}: {checked.project} - what: "
        f"'{checked.what}' - why: "
        f"'{checked.why}' - success: "
        f"'{checked.success}' - citation: "
        f"'{checked.citation if checked.citation else 'none'}' - "
        f"cited in: '{citation_field(checked) or 'none'}' - "
        f"detail: '{checked.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held stance: a note on an intent, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One intent stance, held as data.

    The record names its intent, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per intent stance
    in a book. The record is data alone: holding
    it opens nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    intent_id: str
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
            self, "intent_id", _clean_text(self.intent_id, "an intent id"))
        object.__setattr__(self, "stance", normalize_stance(self.stance))
        object.__setattr__(
            self, "target", _clean_text(self.target, "a stance target"))
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
            "intent_id": self.intent_id, "stance": self.stance,
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
        intent_id=data.get("intent_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held view: which intents a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IntentView:
    """A view over the book: every intent, the citing, the rest."""

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

    @property
    def item_id(self) -> str:
        return self.view_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "view_id": self.view_id, "seq": self.seq,
            "view_filter": self.view_filter, "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_view_ref(value: Any) -> IntentView:
    if not isinstance(value, IntentView):
        raise ValueError("a view must be an IntentView")
    return value


def validate_view(view: Any) -> IntentView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> IntentView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, IntentView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an IntentView")
    _needed(data, _VIEW_KEYS, "a view")
    return IntentView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IntentPanelRow:
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


def _row_for_intent(intent: IntentRecord) -> IntentPanelRow:
    return IntentPanelRow(
        item_id=intent.intent_id,
        standing="citing" if intent_cites(intent) else "uncited",
        label=intent.project, segment=segment_of(intent),
        recorded_on=intent.recorded_on)


def _check_row_ref(value: Any) -> IntentPanelRow:
    if not isinstance(value, IntentPanelRow):
        raise ValueError("a panel row must be an IntentPanelRow")
    return value


def validate_row(row: Any, intent: Any = None) -> IntentPanelRow:
    checked = _check_row_ref(row)
    if intent is not None:
        derived = _row_for_intent(_check_intent_ref(intent))
        if checked != derived:
            raise ValueError(
                f"panel row {checked.item_id!r} does not agree with "
                f"the row derived from its intent")
    return checked


def build_row(row: Any = None, intent: Any = None,
              **kwargs: Any) -> IntentPanelRow:
    if intent is not None:
        derived = _row_for_intent(_check_intent_ref(intent))
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            IntentPanelRow(**kwargs))
        return validate_row(built, intent)
    if isinstance(row, IntentPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in CITING_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return IntentPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return IntentPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an IntentPanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[IntentPanelRow, ...]
                 ) -> Tuple[TargetCount, ...]:
    counts: List[TargetCount] = []
    for standing in CITING_WORDS:
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
        f"The intent book holds {total_items} intents as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {passing_shown} of the shown intents "
        f"stand citing.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its intent's own fields "
        "- the project, and what, why and success held "
        "verbatim in the user's plain words, and the "
        "citation the plan honestly carries - and no "
        "judgement is stored on any intent.",
        "Citation is judged from the held records alone: "
        "a plan citing no intent stands uncited, a plan "
        "citing words that are not in the stored intent "
        "stands named in its gaps, and the intent index is "
        "derived from the held intents, never stored where "
        "it could drift.",
    )


@dataclass(frozen=True)
class IntentPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[IntentPanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> IntentView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, IntentView):
        return view
    return book.view_for(view)


def shown_intents(source: Any, view: Any = None
                   ) -> Tuple[IntentRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.intents
    if resolved.view_filter == "citing":
        return tuple(g for g in book.intents if intent_cites(g))
    return tuple(g for g in book.intents if not intent_cites(g))


def intents_for_project(source: Any, project: Any
                      ) -> Tuple[IntentRecord, ...]:
    wanted = _clean_text(project, "a project")
    return tuple(
        g for g in _source_book(source).intents if g.project == wanted)


def passing_intents(source: Any) -> Tuple[IntentRecord, ...]:
    return tuple(
        g for g in _source_book(source).intents if intent_cites(g))


def current_intent(source: Any) -> Optional[IntentRecord]:
    """The book's current intent, DERIVED at call time.

    The first held intent, in held order, whose plan
    does not yet cite it - where the next plan must
    look. Nothing here is stored: the telling is
    derived from the held citations alone, so it can
    never go stale against them. A book whose every
    plan cites its intent has no current intent.
    """
    for intent in _source_book(source).intents:
        if not intent_cites(intent):
            return intent
    return None


def derive_panel(source: Any, view: Any = None) -> IntentPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_intents(book, resolved)
    rows = tuple(_row_for_intent(intent) for intent in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.intents), default="")
    passing = sum(1 for g in shown if intent_cites(g))
    return IntentPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.intents), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.intents), len(shown), passing, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> IntentPanel:
    if not isinstance(value, IntentPanel):
        raise ValueError("a panel must be an IntentPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> IntentPanel:
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
                **kwargs: Any) -> IntentPanel:
    if isinstance(panel, IntentPanel):
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
        built = IntentPanel(
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
    raise ValueError("a panel must be a mapping, an IntentPanel, or derived")


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
class IntentVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> IntentVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_intents(book, resolved)
    passing = sum(1 for g in shown if intent_cites(g))
    latest = max((g.recorded_on for g in shown), default="")
    return IntentVerdict(
        verdict=_verdict_word(len(shown), passing),
        view_id=resolved.view_id, total_shown=len(shown),
        passing_shown=passing, latest_on=latest)


def _check_verdict_ref(value: Any) -> IntentVerdict:
    if not isinstance(value, IntentVerdict):
        raise ValueError("a verdict must be an IntentVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> IntentVerdict:
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
                  **kwargs: Any) -> IntentVerdict:
    if isinstance(verdict, IntentVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = IntentVerdict(
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
        "a verdict must be a mapping, an IntentVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held intents' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexEntry:
    citation: str
    intent_id: str
    project: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "citation": self.citation, "intent_id": self.intent_id,
            "project": self.project,
        }


@dataclass(frozen=True)
class IntentIndex:
    """The intent index, derived from the held intents.

    The index names one entry per citing intent, in
    held order - the plan's own citation, its intent
    id and its project - and the intents whose plans
    stand uncited, named in its gaps. Nothing here
    is stored on any intent: the index is derived at
    call time from the held records alone, so it can
    never drift from them.
    """

    entries: Tuple[IndexEntry, ...]
    gaps: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "entries": [e.to_record() for e in self.entries],
            "gaps": list(self.gaps),
        }


def derive_index(source: Any) -> IntentIndex:
    """Derive the intent index from the book's held intents."""
    book = _source_book(source)
    entries = tuple(
        IndexEntry(citation=g.citation, intent_id=g.intent_id,
                   project=g.project)
        for g in book.intents if intent_cites(g))
    gaps = tuple(
        g.intent_id for g in book.intents if not intent_cites(g))
    return IntentIndex(entries=entries, gaps=gaps)


def intent_for_citation(source: Any, citation: Any) -> Optional[IntentRecord]:
    """The first held intent one citation reaches, or none - honestly."""
    wanted = _check_citation(citation)
    if not wanted:
        return None
    for intent in _source_book(source).intents:
        if intent.citation == wanted:
            return intent
    return None


def note_for_intent(source: Any, intent_id: Any,
                       stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one intent (and stance, when named)."""
    wanted = _clean_text(intent_id, "an intent id")
    for record in _source_book(source).notes:
        if record.intent_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the intent targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


def board_record(source: Any = None) -> Dict[str, Any]:
    """The intent board, DERIVED here from the held intents alone.

    The board counts the held intents by their
    derived citation standing - citing and uncited -
    and names the current intent, the first whose
    plan does not yet cite it. Nothing here is
    stored: the telling is derived at call time.
    """
    book = _source_book(source)
    standings = []
    for standing in CITING_WORDS:
        number = sum(
            1 for g in book.intents
            if ("citing" if intent_cites(g) else "uncited") == standing)
        standings.append({"standing": standing, "intents": number})
    current = current_intent(book)
    return {
        "type": "intent_board",
        "slice": INTENT_SLICE,
        "standings": standings,
        "total": len(book.intents),
        "current_intent": current.intent_id if current is not None else None,
    }


def roadmap_record() -> Dict[str, Any]:
    """This slice's own roadmap standing, proved from the roadmap itself.

    The record loads this repo's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 slices in 11 parts,
    the banked prefix, the next slice where the
    campaign resumes, and M-202's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(INTENT_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "intent_roadmap",
        "slice": INTENT_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m202_title": own.title,
        "m202_part": own.part,
        "m202_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: intents, views and notes held together, one pinned panel
# at most per telling, and no verdict or index ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IntentBook:
    title: str
    intents: Tuple[IntentRecord, ...] = ()
    views: Tuple[IntentView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    panels: Tuple[IntentPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        intents = tuple(_check_intent_ref(g) for g in self.intents)
        views = tuple(_check_view_ref(v) for v in self.views)
        notes = tuple(_check_note_ref(m) for m in self.notes)
        panels = tuple(_check_panel_ref(p) for p in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for intent in intents:
            if intent.intent_id in seen_ids:
                raise ValueError(
                    f"two intents stand under id {intent.intent_id!r}")
            if intent.seq in seen_seqs:
                raise ValueError(
                    f"two intents stand at sequence {intent.seq}")
            seen_ids.add(intent.intent_id)
            seen_seqs.add(intent.seq)
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
            target = (record.intent_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for intent "
                    f"{record.intent_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per intent target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        object.__setattr__(
            self, "intents", tuple(sorted(intents, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.intents + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.intent_id for g in self.intents) + tuple(
            v.view_id for v in self.views)

    def intent_ids(self) -> Tuple[str, ...]:
        return tuple(g.intent_id for g in self.intents)

    def intent_for(self, intent_id: Any) -> IntentRecord:
        wanted = _clean_text(intent_id, "an intent id")
        for intent in self.intents:
            if intent.intent_id == wanted:
                return intent
        raise KeyError(f"no intent named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> IntentView:
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
        for intent in self.intents:
            if intent.intent_id == wanted:
                return intent
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "intents": [g.to_record() for g in self.intents],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "panels": [p.to_record() for p in self.panels],
        }


def _judge_book_panels(book: IntentBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: IntentBook) -> None:
    if book.title != "Intent capture at the M-201 slice boundary":
        raise ValueError("the shipped example book carries another title")
    if len(book.intents) != 4 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold four intents and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m201-boundary":
        raise ValueError("the pinned panel is panel-m201-boundary")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "strained" or verdict.passing_shown != 2:
        raise ValueError("the shipped example book verdict must stand strained at two citing of four")
    index = derive_index(book)
    if [e.citation for e in index.entries] != ["my own words for what, why and success", "word for word as I gave it"]:
        raise ValueError("the shipped example book index must derive the two held citing plans in held order")
    if index.gaps != ("intent-drifting-plan", "intent-unplanned"):
        raise ValueError("the shipped example book must leave the drifting and unplanned intents honestly uncited, named in its gaps")
    found = intent_for_citation(book, EXAMPLE_CITATION)
    if found is None or found.intent_id != "intent-plain-words":
        raise ValueError("the shipped example book must reach its opening intent under the example citation")
    first = first_note(book)
    if first is None or first.note_id != "note-note-open":
        raise ValueError("the shipped example book must hold the opening note as its first note road")


def validate_book(data: Any, *, require_example: bool = False) -> IntentBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, IntentBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("an intent book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live project opening or plan "
                f"execution ({key!r} is named on it): {INTENT_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its intents under a view")
    if "intent_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held intents at call time")
    if "board" in data or "current_intent" in data:
        raise ValueError(
            "a book stores no board and no current intent: both are "
            "derived from its held intents at call time")
    if data.get("schema") is not None and (
            data["schema"] != INTENT_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{INTENT_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != INTENT_SLICE):
        raise ValueError(
            f"a book's slice must be {INTENT_SLICE!r}")
    head = data.get("intents_head") or data.get("intent_capture") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's intent head must be a mapping")
    title = head.get("title") or data.get("title")
    intents = tuple(build_intent(g) for g in data.get("intents") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    book = IntentBook(
        title=title, intents=intents, views=views, notes=notes, panels=())
    panels = tuple(
        build_panel(p, book) for p in data.get("panels") or ())
    book = IntentBook(
        title=book.title, intents=book.intents, views=book.views,
        notes=book.notes, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> IntentBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (IntentBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an IntentBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> IntentBook:
    return validate_book(data, require_example=require_example)


def load_intents(
        data: Optional[Dict[str, Any]] = None) -> IntentBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(INTENT_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_intents_file(path: Any) -> IntentBook:
    """Load one intent file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: intents and views held one by one.
# ---------------------------------------------------------------------

class IntentRegistry:
    """An in-memory holding of intents and views.

    The registry is the pure layer's model of a
    session's intent book: intents are held under
    their ids, one intent per id and per sequence,
    and views are held in recorded order, one view
    per sequence and per id. Holding is data only -
    nothing held here opens anything, plans
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._intents: List[IntentRecord] = []
        self._views: List[IntentView] = []
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

    def register_intent(self, item: Any) -> IntentRecord:
        """Hold one intent, judged whole before held."""
        checked = _check_intent_ref(item)
        return self._register(
            self._intents, checked, "intent_id", "intent")

    def register_view(self, view: Any) -> IntentView:
        """Hold one view; a view naming no id takes a fresh one."""
        checked = _check_view_ref(view)
        if not checked.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            checked = build_view({**checked.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, checked, "view_id", "view")

    def register_book(self, book: Any) -> IntentBook:
        """Hold a whole book's intents and views, under its title."""
        checked = build_book(book)
        if self._title is not None and checked.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {checked.title!r}")
        for intent in checked.intents:
            self.register_intent(intent)
        for view in checked.views:
            self.register_view(view)
        self._title = checked.title
        return self.book()

    def book(self) -> IntentBook:
        return IntentBook(
            title=self._title or "An unheld intent book",
            intents=tuple(self._intents), views=tuple(self._views),
            notes=(), panels=())

    def list_intents(self) -> Tuple[IntentRecord, ...]:
        return tuple(self._intents)

    def list_views(self) -> Tuple[IntentView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._intents) + tuple(self._views)

    def get_intent(self, intent_id: Any) -> IntentRecord:
        return self.book().intent_for(intent_id)

    def get_view(self, view_id: Any) -> IntentView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records shaped for the journal target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> IntentBook:
    if source is None:
        return load_intents()
    if isinstance(source, IntentBook):
        return source
    if isinstance(source, IntentRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def intent_record(intent: Any, source: Any = None) -> Dict[str, Any]:
    checked = _check_intent_ref(intent)
    record = {
        "type": "intent_record",
        "slice": INTENT_SLICE,
        "intent_id": checked.intent_id,
        "project": checked.project,
        "segment": segment_of(checked),
        "cites": intent_cites(checked),
        "gaps": list(intent_gaps(checked)),
    }
    record.update(_provenance_record(checked))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    checked = _check_view_ref(view)
    record = {
        "type": "intent_view",
        "slice": INTENT_SLICE,
        "view_id": checked.view_id, "seq": checked.seq,
        "view_filter": checked.view_filter,
    }
    record.update(_provenance_record(checked))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    checked = _check_note_ref(record_in)
    record = {
        "type": "intent_note",
        "slice": INTENT_SLICE,
        "note_id": checked.note_id,
        "intent_id": checked.intent_id,
        "stance": checked.stance,
    }
    record.update(_provenance_record(checked))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    checked = validate_panel(panel, source)
    record = {"type": "intent_panel",
              "slice": INTENT_SLICE}
    record.update(checked.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, IntentVerdict):
        checked = validate_verdict(verdict, source)
    else:
        checked = derive_verdict(_source_book(verdict), view)
    record = {"type": "intent_verdict",
              "slice": INTENT_SLICE}
    record.update(checked.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, IntentIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "intent_index",
              "slice": INTENT_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    checked = _source_book(book)
    record = {"type": "intent_book",
              "slice": INTENT_SLICE,
              "title": checked.title}
    record.update(checked.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(intent: Any, source: Any = None) -> str:
    checked = _check_intent_ref(intent)
    return (
        f"{checked.project} - what {checked.what}: "
        f"why {checked.why}, success {checked.success}. "
        f"{checked.detail}")


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The intents stand {verdict.verdict}: "
        f"{verdict.passing_shown} of {verdict.total_shown} shown "
        f"intents stand citing.")


def view_plain_words(view: Any) -> str:
    checked = _check_view_ref(view)
    return f"View {checked.view_id}: shows {checked.view_filter} intents."


def note_plain_words(record_in: Any) -> str:
    checked = _check_note_ref(record_in)
    return (
        f"Note {checked.note_id}: {checked.stance} "
        f"{checked.intent_id}, toward {checked.target}. "
        f"{checked.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, IntentIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.entries)} citing plans for "
        f"{len(index.entries)} intents; uncited, named in "
        f"its gaps: {gaps}.")


def format_intent(intent: Any, source: Any = None) -> str:
    checked = _check_intent_ref(intent)
    lines = [f"{checked.project} ({checked.intent_id})"]
    lines.extend(plain_lines(checked))
    lines.append(checked.detail)
    if intent_cites(checked):
        lines.append(
            f"This intent stands cited - its plan cites the "
            f"{citation_field(checked)} it stands in, in the "
            f"user's own stored words.")
    else:
        lines.append(
            "This intent stands uncited - it stands named in "
            f"its gaps: {', '.join(intent_gaps(checked))}, and "
            "nothing is invented for it.")
    return "\n".join(lines)


def format_view(view: Any) -> str:
    checked = _check_view_ref(view)
    return (
        f"View {checked.view_id}: filter {checked.view_filter} - "
        f"{checked.detail}")


def format_note(record_in: Any) -> str:
    checked = _check_note_ref(record_in)
    lines = [
        f"Intent note {checked.stance} {checked.intent_id} "
        f"({checked.note_id}): {checked.title}. {checked.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or reading it opens nothing, plans nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_citation(source: Any, citation: Any) -> str:
    intent = intent_for_citation(source, citation)
    if intent is not None:
        return format_intent(intent)
    wanted = _check_citation(citation)
    return (
        f"No held intent stands under citation {wanted!r} yet - the "
        f"citation reaches nothing in this book, and no intent is "
        f"invented for it.")


def format_book(source: Any = None, project: Any = None) -> str:
    book = _source_book(source)
    intents = (intents_for_project(book, project)
                if project is not None else book.intents)
    lines = [f"Intent Capture (M-202) - {book.title}"]
    lines.extend(segment_of(intent) for intent in intents)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Intent panel under view {panel.view_id}:"]
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
    lines = ["Intent index, derived from the held intents:"]
    for entry in index.entries:
        lines.append(f"{entry.citation} - {entry.project} ({entry.intent_id})")
    if index.gaps:
        lines.append(
            "Uncited, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "opens nothing, plans nothing and opens no network.")
    return "\n".join(lines)


def format_intent_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "Intent Capture (M-202)",
        f"{book.title}: {len(book.intents)} intents held, "
        f"{len(passing_intents(book))} intents standing citing, "
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


def parse_intent_args(args: Any) -> Tuple[str, Any]:
    """Parse the /intent grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("intent", "view", "note"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("citation", "project"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("index", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
