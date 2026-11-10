"""The slicing engine (roadmap slice M-203).

Part IX - The Mythic Method Engine. The roadmap
words: *from an approved intent, the Architect
drafts slices sized to the house grain (one
verifiable outcome each) with dependencies - the
human approves the *shape*, not every step.*

What already ships, and what this slice adds:

* The M-202 intent book holds the intent itself:
  what, why and success in the user's plain
  words, stored verbatim, with the coder's plan
  citing it. The M-201 campaigns book holds a
  campaign as data, and the shipped planning
  layer (M-042 plan mode) and the M-173 slice
  board already cut and show work in their own
  shapes. What nothing held is *the drafting
  itself as a book*: the draft slices the
  Architect cuts from one approved intent, each
  sized to the house grain, with their
  dependencies, and the human's approval of
  their shape held as data beside them. This
  slice is that book, in its own module,
  standing in the M-195 copy-and-share book
  shape the M-202 book stands in. The shipped
  roads stand untouched behind their seams:
  this layer drafts over the intent book's
  words and rewrites none of them.

* No charter row names this slice: the M-171 TUI
  redesign charter binds Part VIII alone (M-172
  to M-200) and names M-203 on no row, and the
  slice tests pin that absence live. The M-005
  method charter names no slice row either: its
  own words name the whole of Part IX as the
  part that executes the charter, and this slice
  is built to the roadmap words and that
  execution note together.

* A draft slice is held whole: the approved
  intent it was drafted from, named by its
  intent id; its title; its verifiable outcomes,
  held as data; and its dependencies, named by
  draft id. The grain is DERIVED at call time:
  a draft carrying no verifiable outcome, or
  claiming two or more, is not house grain and
  stands unsound, named in its gaps - one
  verifiable outcome each, never more.
* A draft stands only from an APPROVED intent.
  The book holds each intent it drafts from as
  a reference record - its id, its project and
  its standing, approved or unapproved, held as
  data copied from the intent book's own
  telling. A draft naming an intent that stands
  nowhere in the book refuses BY NAME, and a
  draft from an intent that is not approved
  refuses BY NAME beside it: no slice is ever
  drafted from words the human has not approved.
* Dependencies are judged from the held drafts
  alone, DERIVED at call time: a dependency
  naming no held draft stands named in its
  gaps, honestly; a dependency cycle is named
  in the gaps of every draft standing in it,
  never silently ordered. The dependency ORDER
  of the book is derived at call time by
  standing each draft after the drafts it
  depends on; a draft standing in a cycle has
  no place in that order and is left out of
  it, named in the cycle, never forced in.
* The human approves the SHAPE, not every step.
  The shape of one intent's drafts - their ids
  in derived dependency order - is derived at
  call time, and an approval record holds the
  shape the human approved, as data, beside
  the drafts. An approval whose held shape no
  longer agrees with the derived shape stands
  stale, named in the board: the approval is
  of the set and its order, never of a step.
* The slicing index is DERIVED at call time
  from the held drafts - one entry per sound
  draft, under its own one verifiable outcome -
  never a second stored copy that could drift.
  A stored index, soundness verdict, panel,
  shape, order or current-draft claim on any
  record refuses by name.
* The current draft is DERIVED at call time -
  the first held draft, in held order, that does
  not yet stand sound - never stored where it
  could go stale: that is where the Architect
  must look next.
* The notes are held as data: a note record
  naming its draft, its stance - note, concern,
  praise, question, a closed vocabulary - and
  what it feeds back toward, one record per
  draft stance; holding a note posts none of
  it, the rule stands as data
  (:data:`SLICING_RULE`), and a record claiming
  a slice was actually built, executed live,
  banked or pushed refuses BY NAME.
* The shipped data file holds one example book
  in exactly the shape a real slicing file
  takes, a loader reads a slicing file anywhere
  on disk, drafts and views are shaped as
  session news, and a small in-memory registry
  holds records one by one. The agent layer
  owns holding a slicing book for a session and
  telling from it. This layer reaches no live
  road: it builds no slice, executes nothing,
  banks nothing, pushes nothing and opens no
  network - it holds draft slices as data and
  tells them.

Honesty rules, enforced here and pinned by tests:

* **House grain means one outcome.** A draft
  carrying no verifiable outcome, or claiming
  two or more, stands unsound, named in its
  gaps - the grain is derived, never stored.
* **Approved intents only.** A draft from a
  missing or unapproved intent refuses by
  name; no draft is invented from unapproved
  words.
* **Dependencies must resolve or stand named.**
  A dependency naming no held draft stands in
  its gaps; a cycle is named, never silently
  ordered or broken.
* **The shape is approved, not the steps.**
  The approval holds the derived shape as data;
  when the drafts move, the approval stands
  stale by name until the human approves the
  new shape.
* **Unknown stays unknown.** A draft whose
  outcome is not yet held stands with its
  outcomes empty - no outcome is invented.
* **The index, panel, verdict, shape, order
  and current draft are derived, never stored.**
  Each is derived from the held drafts at call
  time; a stored one refuses by name, so it can
  never drift.
* **One draft per draft.** Two drafts standing
  for one draft id refuse by name, and one
  note record stands per draft stance.
* **The notes are data alone.** The records
  hold the feedback; holding, viewing or
  telling them builds nothing and posts
  nothing.
"""


from __future__ import annotations

__all__ = [
    "OUTCOME_FIELDS",
    "EXAMPLE_OUTCOME",
    "STANCES",
    "INDEX_ACTION",
    "SLICING_RESOURCE",
    "SLICING_SCHEMA",
    "SLICING_SLICE",
    "SLICING_RULE",
    "PLAIN_EXPLANATION",
    "THE_SLICING_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "SOUND_WORDS",
    "INTENT_STATES",
    "Any",
    "Dict",
    "List",
    "Optional",
    "ApprovalRecord",
    "DraftRecord",
    "IndexEntry",
    "IntentRef",
    "NoteRecord",
    "SlicingBook",
    "SlicingIndex",
    "SlicingPanel",
    "SlicingPanelRow",
    "SlicingRegistry",
    "SlicingVerdict",
    "SlicingView",
    "TargetCount",
    "approval_for_intent",
    "approval_record",
    "board_record",
    "book_record",
    "build_approval",
    "build_book",
    "build_draft",
    "build_intent_ref",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "current_draft",
    "dependency_cycles",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "draft_for_outcome",
    "draft_order",
    "draft_record",
    "first_note",
    "format_book",
    "format_draft",
    "format_index",
    "format_note",
    "format_outcome",
    "format_panel",
    "format_slicing_screen",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "intent_record",
    "load_slicing",
    "load_slicing_file",
    "normalize_intent_state",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_draft",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_slicing_args",
    "passing_drafts",
    "plain_lines",
    "plain_words",
    "roadmap_record",
    "segment_of",
    "shape_of",
    "shape_approved",
    "shown_drafts",
    "validate_approval",
    "validate_book",
    "validate_draft",
    "validate_intent_ref",
    "validate_note",
    "validate_panel",
    "validate_row",
    "validate_verdict",
    "validate_view",
    "verdict_plain_words",
    "verdict_record",
    "view_plain_words",
    "view_record",
    "draft_gaps",
    "draft_sound",
    "drafts_for_intent",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

SLICING_SCHEMA = "mythic.slicing_engine/1"
SLICING_SLICE = "M-203"
THE_SLICING_SLICE = SLICING_SLICE
SLICING_RESOURCE = "slicing_engine.yaml"
INDEX_ACTION = "index"
EXAMPLE_OUTCOME = "the intent stands held in the user's plain words"
OUTCOME_FIELDS = ("outcomes", "dependencies")
SOUND_WORDS = ("sound", "unsound")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "sound", "unsound")
VERDICT_WORDS = ("open", "strained", "shut")
INTENT_STATES = ("approved", "unapproved")
SLICING_RULE = (
    "draft slices are held as data alone: each "
    "draft is cut from an approved intent, sized "
    "to the house grain of one verifiable outcome, "
    "with its dependencies named; holding, viewing "
    "and reading a draft builds no slice, executes "
    "nothing, banks nothing and opens no network - "
    "a draft is judged from its held outcomes, its "
    "dependencies and its intent's standing alone, "
    "never claimed live, and the human approves "
    "the shape of the drafts, never each step")
PLAIN_EXPLANATION = (
    "The slicing engine (M-203): from an approved "
    "intent, the Architect drafts slices sized to "
    "the house grain - one verifiable outcome "
    "each - with dependencies; the human approves "
    "the shape, not every step.")
USAGE = (
    "Usage: /slicing | /slicing draft <draft-id> | "
    "/slicing outcome <outcome> | /slicing intent <intent-id> | "
    "/slicing view <view-id> | /slicing note <note-id> | "
    "/slicing index | /slicing panel | /slicing verdict")

_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_DRAFT_KEYS = frozenset({
    "draft_id", "seq", "intent_id", "title", "outcomes",
    "dependencies", "detail",
} | set(_PROVENANCE))
_INTENT_REF_KEYS = frozenset({
    "intent_id", "seq", "project", "state", "detail",
} | set(_PROVENANCE))
_APPROVAL_KEYS = frozenset({
    "approval_id", "seq", "intent_id", "shape", "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "draft_id", "stance", "target", "title",
    "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "standing", "sound", "sounds", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "entries", "coverage", "covered", "uncovered",
    "current_draft", "next_draft", "progress", "board",
    "current", "order", "cycles", "approved"})
_LIVE_KEYS = (
    "live_draft", "drafts_live", "live_slice",
    "builds_slice", "built_slice", "builds_live",
    "runs_slice", "ran_slice", "runs_live",
    "executes_slice", "executed_slice",
    "executes_live", "live_execution",
    "banks_slice", "banked_live", "banking_live",
    "pushes_slice", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_draft", "sent_draft",
    "posts_note", "posted_note", "approves_live",
    "approved_live")


# ---------------------------------------------------------------------
# Small judges, in the sibling shape.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_outcomes(value: Any) -> Tuple[str, ...]:
    """A draft's verifiable outcomes, held as data.

    The outcomes stand as a list of worded claims;
    an outcome not yet held stands honestly empty -
    no outcome is invented - and a claim that is
    not a string at all refuses.
    """
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError("outcomes must be a list of verifiable outcome lines")
    return tuple(_clean_text(v, "a verifiable outcome") for v in value)


def _check_dependencies(value: Any) -> Tuple[str, ...]:
    """A draft's dependencies: draft ids named as data, or none.

    Each dependency names one draft id; a dependency
    named twice on one draft refuses, and a dependency
    that is not a string at all refuses.
    """
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError("dependencies must be a list of draft ids")
    deps = tuple(_clean_text(v, "a dependency draft id") for v in value)
    if len(set(deps)) != len(deps):
        raise ValueError("a dependency stands twice on one draft")
    return deps


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
                f"{SLICING_RULE}")
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


def normalize_intent_state(value: Any) -> str:
    state = _clean_text(value, "an intent state").lower()
    if state not in INTENT_STATES:
        raise ValueError(
            f"intent state {state!r} is not one of the held "
            f"states: " + ", ".join(INTENT_STATES))
    return state


def normalize_view_filter(value: Any) -> str:
    view_filter = _clean_text(value, "a view filter").lower()
    if view_filter not in VIEW_FILTERS:
        raise ValueError(
            f"view filter {view_filter!r} is not one of the held "
            f"filters: " + ", ".join(VIEW_FILTERS))
    return view_filter


# ---------------------------------------------------------------------
# The held draft: one slice cut from an approved intent.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class DraftRecord:
    """One draft slice, held as data.

    The draft names the approved intent it was
    drafted from, by intent id, its title, its
    verifiable outcomes, held as data, and its
    dependencies, named by draft id. The grain is
    derived, never stored: exactly one verifiable
    outcome is the house grain. A draft whose
    outcomes are not yet held stands with its
    outcomes empty: it stands unsound, named in
    its gaps, and no outcome is invented for it.
    The draft is local data alone - no live build
    stands behind it: holding it builds nothing.
    """

    draft_id: str
    seq: int
    intent_id: str
    title: str
    outcomes: Tuple[str, ...] = ()
    dependencies: Tuple[str, ...] = ()
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "draft_id", _clean_text(self.draft_id, "a draft id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "intent_id", _clean_text(self.intent_id, "an intent id"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a draft title"))
        object.__setattr__(
            self, "outcomes", _check_outcomes(self.outcomes))
        object.__setattr__(
            self, "dependencies", _check_dependencies(self.dependencies))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a draft detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.draft_id

    @property
    def outcome(self) -> str:
        """The draft's one outcome, when it stands at house grain."""
        return self.outcomes[0] if len(self.outcomes) == 1 else ""

    def to_record(self) -> Dict[str, Any]:
        record = {
            "draft_id": self.draft_id, "seq": self.seq,
            "intent_id": self.intent_id, "title": self.title,
            "outcomes": list(self.outcomes),
            "dependencies": list(self.dependencies),
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_draft_ref(value: Any) -> DraftRecord:
    if not isinstance(value, DraftRecord):
        raise ValueError("a draft must be a DraftRecord")
    return value


def validate_draft(draft: Any) -> DraftRecord:
    return _check_draft_ref(draft)


def build_draft(record: Any = None, **kwargs: Any) -> DraftRecord:
    """Build one held draft from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, DraftRecord):
        if kwargs:
            raise ValueError("a draft stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a draft must be a mapping or a DraftRecord")
    _needed(data, _DRAFT_KEYS, "a draft")
    return DraftRecord(
        draft_id=data.get("draft_id"), seq=data.get("seq"),
        intent_id=data.get("intent_id"), title=data.get("title"),
        outcomes=data.get("outcomes"),
        dependencies=data.get("dependencies"),
        detail=data.get("detail"),
        **_provenance(data))


def _cycle_map(book: Any) -> Dict[str, Tuple[str, ...]]:
    """Map each draft standing in a dependency cycle to its cycle.

    Derived from the held drafts alone: a cycle is
    a closed walk of dependencies among held drafts,
    told in walk order, first draft repeated last.
    """
    held = {d.draft_id: d for d in book.drafts}
    found: Dict[str, Tuple[str, ...]] = {}
    state: Dict[str, int] = {}
    stack: List[str] = []

    def visit(node: str) -> None:
        state[node] = 1
        stack.append(node)
        for dep in held[node].dependencies:
            if dep not in held:
                continue
            if state.get(dep) == 1:
                cycle = tuple(stack[stack.index(dep):]) + (dep,)
                for member in cycle[:-1]:
                    found.setdefault(member, cycle)
            elif state.get(dep, 0) == 0:
                visit(dep)
        stack.pop()
        state[node] = 2

    for draft in book.drafts:
        if state.get(draft.draft_id, 0) == 0:
            visit(draft.draft_id)
    return found


def draft_gaps(draft: Any, source: Any = None) -> Tuple[str, ...]:
    """The gaps that keep a draft from standing sound.

    Judged intrinsically from the draft's own
    fields - the house grain - and, when a book
    is named, from the held drafts and intents
    beside it: its dependencies must resolve to
    held drafts, and no cycle may stand in them.
    """
    checked = _check_draft_ref(draft)
    gaps: List[str] = []
    if not checked.outcomes:
        gaps.append("carries no verifiable outcome")
    elif len(checked.outcomes) > 1:
        gaps.append(
            f"claims {len(checked.outcomes)} outcomes, not the "
            f"house grain of one verifiable outcome each")
    if checked.draft_id in checked.dependencies:
        gaps.append(
            f"stands in a dependency cycle: "
            f"{checked.draft_id} > {checked.draft_id}")
    if source is not None:
        book = _source_book(source)
        held_ids = {d.draft_id for d in book.drafts}
        for dep in checked.dependencies:
            if dep not in held_ids:
                gaps.append(
                    f"depends on {dep}, which stands nowhere "
                    f"in this book")
        cycle = _cycle_map(book).get(checked.draft_id)
        if cycle is not None:
            text = (
                f"stands in a dependency cycle: "
                f"{' > '.join(cycle)}")
            if text not in gaps:
                gaps.append(text)
    return tuple(gaps)


def draft_sound(draft: Any, source: Any = None) -> bool:
    return not draft_gaps(draft, source)


def plain_lines(draft: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the draft's own fields."""
    checked = _check_draft_ref(draft)
    return (
        f"Draft: {checked.title}",
        f"Intent: {checked.intent_id}",
        f"Outcome: {checked.outcome if checked.outcome else 'none'}",
        f"Dependencies: "
        f"{', '.join(checked.dependencies) if checked.dependencies else 'none'}",
    )


def segment_of(draft: Any, source: Any = None) -> str:
    checked = _check_draft_ref(draft)
    gaps = draft_gaps(checked, source)
    return (
        f"{checked.draft_id}: {checked.title} - intent: "
        f"'{checked.intent_id}' - outcome: "
        f"'{checked.outcome if checked.outcome else 'none'}' - "
        f"outcomes: {len(checked.outcomes)} - dependencies: "
        f"'{', '.join(checked.dependencies) if checked.dependencies else 'none'}' - "
        f"detail: '{checked.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held intent reference: the approved intent a book drafts from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IntentRef:
    """One intent a slicing book drafts from, held as a reference.

    The record names the intent, the project it
    opens and its standing - approved or
    unapproved - held as data copied from the
    M-202 intent book's own telling. A draft
    stands only from an approved reference: the
    book refuses a draft naming no held reference,
    and a draft from an unapproved one, BY NAME.
    """

    intent_id: str
    seq: int
    project: str
    state: str
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
            self, "state", normalize_intent_state(self.state))
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
            "project": self.project, "state": self.state,
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_intent_ref(value: Any) -> IntentRef:
    if not isinstance(value, IntentRef):
        raise ValueError("an intent reference must be an IntentRef")
    return value


def validate_intent_ref(ref: Any) -> IntentRef:
    return _check_intent_ref(ref)


def build_intent_ref(record: Any = None, **kwargs: Any) -> IntentRef:
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, IntentRef):
        if kwargs:
            raise ValueError(
                "an intent reference stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError(
            "an intent reference must be a mapping or an IntentRef")
    _needed(data, _INTENT_REF_KEYS, "an intent reference")
    return IntentRef(
        intent_id=data.get("intent_id"), seq=data.get("seq"),
        project=data.get("project"), state=data.get("state"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held shape approval: the human approves the shape, as data.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ApprovalRecord:
    """One shape approval, held as data.

    The record names its intent and the shape the
    human approved - the intent's draft ids in
    derived dependency order, held exactly as
    approved. The approval is of the set and its
    order, never of a step: when the derived
    shape moves, this record stands stale, named
    in the board, until a new shape is approved.
    """

    approval_id: str
    seq: int
    intent_id: str
    shape: str
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "approval_id",
            _clean_text(self.approval_id, "an approval id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "intent_id", _clean_text(self.intent_id, "an intent id"))
        object.__setattr__(
            self, "shape", _clean_text(self.shape, "an approved shape"))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an approval detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.approval_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "approval_id": self.approval_id, "seq": self.seq,
            "intent_id": self.intent_id, "shape": self.shape,
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_approval_ref(value: Any) -> ApprovalRecord:
    if not isinstance(value, ApprovalRecord):
        raise ValueError("an approval must be an ApprovalRecord")
    return value


def validate_approval(approval: Any) -> ApprovalRecord:
    return _check_approval_ref(approval)


def build_approval(record: Any = None, **kwargs: Any) -> ApprovalRecord:
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, ApprovalRecord):
        if kwargs:
            raise ValueError(
                "an approval stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError(
            "an approval must be a mapping or an ApprovalRecord")
    _needed(data, _APPROVAL_KEYS, "an approval")
    return ApprovalRecord(
        approval_id=data.get("approval_id"), seq=data.get("seq"),
        intent_id=data.get("intent_id"), shape=data.get("shape"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held stance: a note on a draft, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One draft stance, held as data.

    The record names its draft, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per draft stance
    in a book. The record is data alone: holding
    it builds nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    draft_id: str
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
            self, "draft_id", _clean_text(self.draft_id, "a draft id"))
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
            "draft_id": self.draft_id, "stance": self.stance,
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
        draft_id=data.get("draft_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held view: which intents a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class SlicingView:
    """A view over the book: every draft, the sound, the rest."""

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


def _check_view_ref(value: Any) -> SlicingView:
    if not isinstance(value, SlicingView):
        raise ValueError("a view must be an SlicingView")
    return value


def validate_view(view: Any) -> SlicingView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> SlicingView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, SlicingView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an SlicingView")
    _needed(data, _VIEW_KEYS, "a view")
    return SlicingView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class SlicingPanelRow:
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


def _row_for_draft(draft: DraftRecord,
                     source: Any = None) -> SlicingPanelRow:
    return SlicingPanelRow(
        item_id=draft.draft_id,
        standing="sound" if draft_sound(draft, source) else "unsound",
        label=draft.title, segment=segment_of(draft, source),
        recorded_on=draft.recorded_on)


def _check_row_ref(value: Any) -> SlicingPanelRow:
    if not isinstance(value, SlicingPanelRow):
        raise ValueError("a panel row must be an SlicingPanelRow")
    return value


def validate_row(row: Any, draft: Any = None,
                 source: Any = None) -> SlicingPanelRow:
    checked = _check_row_ref(row)
    if draft is not None:
        derived = _row_for_draft(_check_draft_ref(draft), source)
        if checked != derived:
            raise ValueError(
                f"panel row {checked.item_id!r} does not agree with "
                f"the row derived from its draft")
    return checked


def build_row(row: Any = None, draft: Any = None,
              source: Any = None,
              **kwargs: Any) -> SlicingPanelRow:
    if draft is not None:
        derived = _row_for_draft(_check_draft_ref(draft), source)
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            SlicingPanelRow(**kwargs))
        return validate_row(built, draft, source)
    if isinstance(row, SlicingPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in SOUND_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return SlicingPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return SlicingPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an SlicingPanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[SlicingPanelRow, ...]
                 ) -> Tuple[TargetCount, ...]:
    counts: List[TargetCount] = []
    for standing in SOUND_WORDS:
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
        f"The slicing book holds {total_items} drafts as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {passing_shown} of the shown drafts "
        f"stand sound.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its draft's own fields "
        "- the intent it was drafted from, its one verifiable "
        "outcome at the house grain, and the dependencies it "
        "honestly carries - and no judgement is stored on "
        "any draft.",
        "Soundness is judged from the held records alone: "
        "a draft off the house grain stands unsound, a draft "
        "whose dependencies stand nowhere or stand in a cycle "
        "stands named in its gaps, and the slicing index is "
        "derived from the held drafts, never stored where "
        "it could drift.",
    )


@dataclass(frozen=True)
class SlicingPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[SlicingPanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> SlicingView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, SlicingView):
        return view
    return book.view_for(view)


def shown_drafts(source: Any, view: Any = None
                   ) -> Tuple[DraftRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.drafts
    if resolved.view_filter == "sound":
        return tuple(g for g in book.drafts if draft_sound(g, book))
    return tuple(g for g in book.drafts if not draft_sound(g, book))


def drafts_for_intent(source: Any, intent_id: Any
                      ) -> Tuple[DraftRecord, ...]:
    wanted = _clean_text(intent_id, "an intent id")
    return tuple(
        g for g in _source_book(source).drafts if g.intent_id == wanted)


def passing_drafts(source: Any) -> Tuple[DraftRecord, ...]:
    book = _source_book(source)
    return tuple(g for g in book.drafts if draft_sound(g, book))


def current_draft(source: Any) -> Optional[DraftRecord]:
    """The book's current draft, DERIVED at call time.

    The first held draft, in held order, that does
    not yet stand sound - where the Architect must
    look next. Nothing here is stored: the telling
    is derived from the held drafts alone, so it can
    never go stale against them. A book whose every
    draft stands sound has no current draft.
    """
    book = _source_book(source)
    for draft in book.drafts:
        if not draft_sound(draft, book):
            return draft
    return None


def derive_panel(source: Any, view: Any = None) -> SlicingPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_drafts(book, resolved)
    rows = tuple(_row_for_draft(draft, book) for draft in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.drafts), default="")
    passing = sum(1 for g in shown if draft_sound(g, book))
    return SlicingPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.drafts), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.drafts), len(shown), passing, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> SlicingPanel:
    if not isinstance(value, SlicingPanel):
        raise ValueError("a panel must be an SlicingPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> SlicingPanel:
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
                **kwargs: Any) -> SlicingPanel:
    if isinstance(panel, SlicingPanel):
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
        built = SlicingPanel(
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
    raise ValueError("a panel must be a mapping, an SlicingPanel, or derived")


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
class SlicingVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> SlicingVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_drafts(book, resolved)
    passing = sum(1 for g in shown if draft_sound(g, book))
    latest = max((g.recorded_on for g in shown), default="")
    return SlicingVerdict(
        verdict=_verdict_word(len(shown), passing),
        view_id=resolved.view_id, total_shown=len(shown),
        passing_shown=passing, latest_on=latest)


def _check_verdict_ref(value: Any) -> SlicingVerdict:
    if not isinstance(value, SlicingVerdict):
        raise ValueError("a verdict must be an SlicingVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> SlicingVerdict:
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
                  **kwargs: Any) -> SlicingVerdict:
    if isinstance(verdict, SlicingVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = SlicingVerdict(
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
        "a verdict must be a mapping, an SlicingVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held intents' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexEntry:
    outcome: str
    draft_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "outcome": self.outcome, "draft_id": self.draft_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class SlicingIndex:
    """The slicing index, derived from the held drafts.

    The index names one entry per sound draft, in
    held order - the draft's own one verifiable
    outcome, its draft id and its title - and the
    drafts that do not stand sound, named in its
    gaps. Nothing here is stored on any draft: the
    index is derived at call time from the held
    records alone, so it can never drift from them.
    """

    entries: Tuple[IndexEntry, ...]
    gaps: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "entries": [e.to_record() for e in self.entries],
            "gaps": list(self.gaps),
        }


def derive_index(source: Any) -> SlicingIndex:
    """Derive the slicing index from the book's held drafts."""
    book = _source_book(source)
    entries = tuple(
        IndexEntry(outcome=g.outcome, draft_id=g.draft_id,
                   title=g.title)
        for g in book.drafts if draft_sound(g, book))
    gaps = tuple(
        g.draft_id for g in book.drafts if not draft_sound(g, book))
    return SlicingIndex(entries=entries, gaps=gaps)


def draft_for_outcome(source: Any, outcome: Any) -> Optional[DraftRecord]:
    """The first held draft one outcome reaches, or none - honestly."""
    if outcome is None:
        return None
    if not isinstance(outcome, str):
        raise ValueError("an outcome must be a string naming the outcome")
    wanted = outcome.strip()
    if not wanted:
        return None
    for draft in _source_book(source).drafts:
        if draft.outcome == wanted:
            return draft
    return None


def dependency_cycles(source: Any) -> Tuple[str, ...]:
    """Every dependency cycle among the held drafts, DERIVED.

    One telling per distinct cycle, in held order:
    the cycle's drafts in walk order, first repeated
    last. A book with no cycle tells none.
    """
    book = _source_book(source)
    seen: List[str] = []
    for cycle in _cycle_map(book).values():
        text = " > ".join(cycle)
        if text not in seen:
            seen.append(text)
    return tuple(seen)


def draft_order(source: Any,
                intent_id: Any = None) -> Tuple[DraftRecord, ...]:
    """The held drafts in derived dependency order.

    Each draft stands after every held draft it
    depends on; ties stand in held order. A draft
    standing in a dependency cycle - or depending
    on one - has no place in the order and is left
    out of it, named by dependency_cycles, never
    silently ordered.
    """
    book = _source_book(source)
    drafts = list(book.drafts)
    if intent_id is not None:
        wanted = _clean_text(intent_id, "an intent id")
        drafts = [d for d in drafts if d.intent_id == wanted]
    held_ids = {d.draft_id for d in book.drafts}
    cyclic = set(_cycle_map(book))
    blocked = set(cyclic)
    changed = True
    while changed:
        changed = False
        for draft in book.drafts:
            if draft.draft_id not in blocked and any(
                    dep in blocked for dep in draft.dependencies):
                blocked.add(draft.draft_id)
                changed = True
    order: List[DraftRecord] = []
    placed = set()
    pool = [d for d in drafts if d.draft_id not in blocked]
    while pool:
        progressed = False
        for draft in list(pool):
            deps = [dep for dep in draft.dependencies if dep in held_ids]
            scoped = [dep for dep in deps
                      if any(d.draft_id == dep for d in drafts)]
            if all(dep in placed for dep in scoped):
                order.append(draft)
                placed.add(draft.draft_id)
                pool.remove(draft)
                progressed = True
        if not progressed:
            break
    return tuple(order)


def shape_of(source: Any, intent_id: Any) -> str:
    """One intent's shape, DERIVED at call time.

    The intent's draft ids in derived dependency
    order, joined as one shape line. Drafts left
    out of the order - standing in a cycle - stand
    in no shape: the shape tells only what stands
    ordered, and the cycle is named elsewhere.
    """
    return " > ".join(
        d.draft_id for d in draft_order(source, intent_id))


def approval_for_intent(source: Any,
                        intent_id: Any) -> Optional[ApprovalRecord]:
    """The held shape approval for one intent, or none - honestly."""
    wanted = _clean_text(intent_id, "an intent id")
    for record in _source_book(source).approvals:
        if record.intent_id == wanted:
            return record
    return None


def shape_approved(source: Any, intent_id: Any) -> bool:
    """Whether the held approval agrees with the derived shape.

    The approval stands current only while the
    shape it holds is the shape the book derives
    now; a moved shape leaves it stale, and no
    approval at all approves nothing.
    """
    approval = approval_for_intent(source, intent_id)
    if approval is None:
        return False
    return approval.shape == shape_of(source, intent_id)


def note_for_draft(source: Any, draft_id: Any,
                   stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one draft (and stance, when named)."""
    wanted = _clean_text(draft_id, "a draft id")
    for record in _source_book(source).notes:
        if record.draft_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the intent targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


def board_record(source: Any = None) -> Dict[str, Any]:
    """The slicing board, DERIVED here from the held drafts alone.

    The board counts the held drafts by their
    derived soundness - sound and unsound - names
    the current draft, the first that does not yet
    stand sound, and tells each held intent's
    shape standing: approved while its held
    approval agrees with its derived shape, stale
    or unapproved otherwise. Nothing here is
    stored: the telling is derived at call time.
    """
    book = _source_book(source)
    standings = []
    for standing in SOUND_WORDS:
        number = sum(
            1 for g in book.drafts
            if ("sound" if draft_sound(g, book) else "unsound") == standing)
        standings.append({"standing": standing, "drafts": number})
    current = current_draft(book)
    shapes = []
    for ref in book.intents:
        approval = approval_for_intent(book, ref.intent_id)
        if approval is None:
            standing = "unapproved"
        elif shape_approved(book, ref.intent_id):
            standing = "approved"
        else:
            standing = "stale"
        shapes.append({"intent_id": ref.intent_id, "shape": standing})
    return {
        "type": "slicing_board",
        "slice": SLICING_SLICE,
        "standings": standings,
        "total": len(book.drafts),
        "current_draft": current.draft_id if current is not None else None,
        "shapes": shapes,
        "cycles": list(dependency_cycles(book)),
    }


def roadmap_record() -> Dict[str, Any]:
    """This slice's own roadmap standing, proved from the roadmap itself.

    The record loads this repo's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 slices in 11 parts,
    the banked prefix, the next slice where the
    campaign resumes, and M-203's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(SLICING_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "slicing_roadmap",
        "slice": SLICING_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m203_title": own.title,
        "m203_part": own.part,
        "m203_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: intents, drafts, views, notes and shape approvals held
# together, one pinned panel at most per telling, and no verdict,
# index, shape or order ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class SlicingBook:
    title: str
    intents: Tuple[IntentRef, ...] = ()
    drafts: Tuple[DraftRecord, ...] = ()
    views: Tuple[SlicingView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    approvals: Tuple[ApprovalRecord, ...] = ()
    panels: Tuple[SlicingPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        intents = tuple(_check_intent_ref(g) for g in self.intents)
        drafts = tuple(_check_draft_ref(g) for g in self.drafts)
        views = tuple(_check_view_ref(v) for v in self.views)
        notes = tuple(_check_note_ref(m) for m in self.notes)
        approvals = tuple(_check_approval_ref(a) for a in self.approvals)
        panels = tuple(_check_panel_ref(pn) for pn in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for ref in intents:
            if ref.intent_id in seen_ids:
                raise ValueError(
                    f"two intent references stand under id {ref.intent_id!r}")
            if ref.seq in seen_seqs:
                raise ValueError(
                    f"two intent references stand at sequence {ref.seq}")
            seen_ids.add(ref.intent_id)
            seen_seqs.add(ref.seq)
        draft_ids = set()
        draft_seqs = set()
        for draft in drafts:
            if draft.draft_id in draft_ids:
                raise ValueError(
                    f"two drafts stand under id {draft.draft_id!r}")
            if draft.seq in draft_seqs:
                raise ValueError(
                    f"two drafts stand at sequence {draft.seq}")
            draft_ids.add(draft.draft_id)
            draft_seqs.add(draft.seq)
        by_intent = {ref.intent_id: ref for ref in intents}
        for draft in (drafts if intents else ()):

            ref = by_intent.get(draft.intent_id)
            if ref is None:
                raise ValueError(
                    f"draft {draft.draft_id!r} is drafted from intent "
                    f"{draft.intent_id!r}, which stands nowhere in "
                    f"this book")
            if ref.state != "approved":
                raise ValueError(
                    f"draft {draft.draft_id!r} is drafted from intent "
                    f"{draft.intent_id!r}, which is not approved: "
                    f"no slice is drafted from an unapproved intent")
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
            target = (record.draft_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for draft "
                    f"{record.draft_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per draft target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        approval_ids = set()
        approval_seqs = set()
        approval_intents = set()
        for record in approvals:
            if record.approval_id in approval_ids:
                raise ValueError(
                    f"two approvals stand under id {record.approval_id!r}")
            if record.seq in approval_seqs:
                raise ValueError(
                    f"two approvals stand at sequence {record.seq}")
            if record.intent_id in approval_intents:
                raise ValueError(
                    f"two shape approvals stand for intent "
                    f"{record.intent_id!r}: one approval stands "
                    f"per intent shape")
            if intents and record.intent_id not in by_intent:
                raise ValueError(
                    f"approval {record.approval_id!r} approves intent "
                    f"{record.intent_id!r}, which stands nowhere in "
                    f"this book")
            approval_ids.add(record.approval_id)
            approval_seqs.add(record.seq)
            approval_intents.add(record.intent_id)
        object.__setattr__(
            self, "intents", tuple(sorted(intents, key=lambda g: g.seq)))
        object.__setattr__(
            self, "drafts", tuple(sorted(drafts, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(
            self, "approvals",
            tuple(sorted(approvals, key=lambda a: a.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.drafts + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.draft_id for g in self.drafts) + tuple(
            v.view_id for v in self.views)

    def draft_ids(self) -> Tuple[str, ...]:
        return tuple(g.draft_id for g in self.drafts)

    def intent_ids(self) -> Tuple[str, ...]:
        return tuple(g.intent_id for g in self.intents)

    def draft_for(self, draft_id: Any) -> DraftRecord:
        wanted = _clean_text(draft_id, "a draft id")
        for draft in self.drafts:
            if draft.draft_id == wanted:
                return draft
        raise KeyError(f"no draft named {wanted!r} stands in this book")

    def intent_for(self, intent_id: Any) -> IntentRef:
        wanted = _clean_text(intent_id, "an intent id")
        for ref in self.intents:
            if ref.intent_id == wanted:
                return ref
        raise KeyError(f"no intent named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> SlicingView:
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

    def approval_for(self, approval_id: Any) -> ApprovalRecord:
        wanted = _clean_text(approval_id, "an approval id")
        for record in self.approvals:
            if record.approval_id == wanted:
                return record
        raise KeyError(f"no approval named {wanted!r} stands in this book")

    def item_for(self, item_id: Any) -> Any:
        wanted = _clean_text(item_id, "an item id")
        for draft in self.drafts:
            if draft.draft_id == wanted:
                return draft
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "intents": [g.to_record() for g in self.intents],
            "drafts": [g.to_record() for g in self.drafts],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "approvals": [a.to_record() for a in self.approvals],
            "panels": [pn.to_record() for pn in self.panels],
        }


def _judge_book_panels(book: SlicingBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: SlicingBook) -> None:
    if book.title != "The slicing engine at the M-202 slice boundary":
        raise ValueError("the shipped example book carries another title")
    if len(book.intents) != 3 or len(book.drafts) != 5 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold three intent references, five drafts and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.approvals) != 1:
        raise ValueError("the shipped example book must hold one shape approval")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m202-boundary":
        raise ValueError("the pinned panel is panel-m202-boundary")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "strained" or verdict.passing_shown != 3:
        raise ValueError("the shipped example book verdict must stand strained at three sound of five")
    index = derive_index(book)
    if [e.outcome for e in index.entries] != ["the intent stands held in the user's plain words", "slices stand drafted at the house grain", "the shape stands approved as data"]:
        raise ValueError("the shipped example book index must derive the three held sound drafts in held order")
    if index.gaps != ("draft-two-outcomes", "draft-loose-thread"):
        raise ValueError("the shipped example book must leave the wide and loose drafts honestly unsound, named in its gaps")
    found = draft_for_outcome(book, EXAMPLE_OUTCOME)
    if found is None or found.draft_id != "draft-capture-intent":
        raise ValueError("the shipped example book must reach its opening draft under the example outcome")
    if shape_of(book, "intent-plain-words") != "draft-capture-intent > draft-draft-slices > draft-shape-approval":
        raise ValueError("the shipped example book must derive the opening intent's shape in dependency order")
    if not shape_approved(book, "intent-plain-words"):
        raise ValueError("the shipped example book must hold the opening intent's shape approved")
    first = first_note(book)
    if first is None or first.note_id != "note-note-open":
        raise ValueError("the shipped example book must hold the opening note as its first note road")


def validate_book(data: Any, *, require_example: bool = False) -> SlicingBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, SlicingBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a slicing book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live slice build or execution "
                f"({key!r} is named on it): {SLICING_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its drafts under a view")
    if "slicing_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held drafts at call time")
    if "board" in data or "current_draft" in data:
        raise ValueError(
            "a book stores no board and no current draft: both are "
            "derived from its held drafts at call time")
    if "shape" in data or "order" in data:
        raise ValueError(
            "a book stores no shape and no order: both are derived "
            "from its held drafts at call time; an approval record "
            "holds the shape the human approved")
    if data.get("schema") is not None and (
            data["schema"] != SLICING_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{SLICING_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != SLICING_SLICE):
        raise ValueError(
            f"a book's slice must be {SLICING_SLICE!r}")
    head = data.get("slicing_head") or data.get("slicing_engine") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's slicing head must be a mapping")
    title = head.get("title") or data.get("title")
    intents = tuple(build_intent_ref(g) for g in data.get("intents") or ())
    drafts = tuple(build_draft(g) for g in data.get("drafts") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    approvals = tuple(build_approval(a) for a in data.get("approvals") or ())
    book = SlicingBook(
        title=title, intents=intents, drafts=drafts, views=views,
        notes=notes, approvals=approvals, panels=())
    panels = tuple(
        build_panel(pn, book) for pn in data.get("panels") or ())
    book = SlicingBook(
        title=book.title, intents=book.intents, drafts=book.drafts,
        views=book.views, notes=book.notes,
        approvals=book.approvals, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> SlicingBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (SlicingBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an SlicingBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> SlicingBook:
    return validate_book(data, require_example=require_example)


def load_slicing(
        data: Optional[Dict[str, Any]] = None) -> SlicingBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(SLICING_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_slicing_file(path: Any) -> SlicingBook:
    """Load one slicing file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: intent references, drafts and views held one by one.
# ---------------------------------------------------------------------

class SlicingRegistry:
    """An in-memory holding of intent references, drafts and views.

    The registry is the pure layer's model of a
    session's slicing book: intent references are
    held under their ids, drafts are held under
    their ids, one draft per id and per sequence,
    and views are held in recorded order, one view
    per sequence and per id. Holding is data only -
    nothing held here builds anything, executes
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._intents: List[IntentRef] = []
        self._drafts: List[DraftRecord] = []
        self._views: List[SlicingView] = []
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

    def register_intent_ref(self, item: Any) -> IntentRef:
        """Hold one intent reference, judged whole before held."""
        checked = _check_intent_ref(item)
        return self._register(
            self._intents, checked, "intent_id", "intent reference")

    def register_draft(self, item: Any) -> DraftRecord:
        """Hold one draft, judged whole before held."""
        checked = _check_draft_ref(item)
        return self._register(
            self._drafts, checked, "draft_id", "draft")

    def register_view(self, view: Any) -> SlicingView:
        """Hold one view; a view naming no id takes a fresh one."""
        checked = _check_view_ref(view)
        if not checked.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            checked = build_view({**checked.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, checked, "view_id", "view")

    def register_book(self, book: Any) -> SlicingBook:
        """Hold a whole book's records, under its title."""
        checked = build_book(book)
        if self._title is not None and checked.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {checked.title!r}")
        for ref in checked.intents:
            self.register_intent_ref(ref)
        for draft in checked.drafts:
            self.register_draft(draft)
        for view in checked.views:
            self.register_view(view)
        self._title = checked.title
        return self.book()

    def book(self) -> SlicingBook:
        return SlicingBook(
            title=self._title or "An unheld slicing book",
            intents=tuple(self._intents), drafts=tuple(self._drafts),
            views=tuple(self._views), notes=(), approvals=(), panels=())

    def list_intents(self) -> Tuple[IntentRef, ...]:
        return tuple(self._intents)

    def list_drafts(self) -> Tuple[DraftRecord, ...]:
        return tuple(self._drafts)

    def list_views(self) -> Tuple[SlicingView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._drafts) + tuple(self._views)

    def get_intent(self, intent_id: Any) -> IntentRef:
        return self.book().intent_for(intent_id)

    def get_draft(self, draft_id: Any) -> DraftRecord:
        return self.book().draft_for(draft_id)

    def get_view(self, view_id: Any) -> SlicingView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records shaped for the journal target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> SlicingBook:
    if source is None:
        return load_slicing()
    if isinstance(source, SlicingBook):
        return source
    if isinstance(source, SlicingRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def draft_record(draft: Any, source: Any = None) -> Dict[str, Any]:
    checked = _check_draft_ref(draft)
    book = _source_book(source) if source is not None else None
    record = {
        "type": "slicing_draft",
        "slice": SLICING_SLICE,
        "draft_id": checked.draft_id,
        "intent_id": checked.intent_id,
        "title": checked.title,
        "segment": segment_of(checked, book),
        "sound": draft_sound(checked, book),
        "gaps": list(draft_gaps(checked, book)),
    }
    record.update(_provenance_record(checked))
    return record


def intent_record(ref: Any) -> Dict[str, Any]:
    checked = _check_intent_ref(ref)
    record = {
        "type": "slicing_intent",
        "slice": SLICING_SLICE,
        "intent_id": checked.intent_id,
        "project": checked.project,
        "state": checked.state,
    }
    record.update(_provenance_record(checked))
    return record


def approval_record(record_in: Any) -> Dict[str, Any]:
    checked = _check_approval_ref(record_in)
    record = {
        "type": "slicing_approval",
        "slice": SLICING_SLICE,
        "approval_id": checked.approval_id,
        "intent_id": checked.intent_id,
        "shape": checked.shape,
    }
    record.update(_provenance_record(checked))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    checked = _check_view_ref(view)
    record = {
        "type": "slicing_view",
        "slice": SLICING_SLICE,
        "view_id": checked.view_id, "seq": checked.seq,
        "view_filter": checked.view_filter,
    }
    record.update(_provenance_record(checked))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    checked = _check_note_ref(record_in)
    record = {
        "type": "slicing_note",
        "slice": SLICING_SLICE,
        "note_id": checked.note_id,
        "draft_id": checked.draft_id,
        "stance": checked.stance,
    }
    record.update(_provenance_record(checked))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    checked = validate_panel(panel, source)
    record = {"type": "slicing_panel",
              "slice": SLICING_SLICE}
    record.update(checked.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, SlicingVerdict):
        checked = validate_verdict(verdict, source)
    else:
        checked = derive_verdict(_source_book(verdict), view)
    record = {"type": "slicing_verdict",
              "slice": SLICING_SLICE}
    record.update(checked.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, SlicingIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "slicing_index",
              "slice": SLICING_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    checked = _source_book(book)
    record = {"type": "slicing_book",
              "slice": SLICING_SLICE,
              "title": checked.title}
    record.update(checked.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(draft: Any, source: Any = None) -> str:
    checked = _check_draft_ref(draft)
    return (
        f"{checked.title} - from {checked.intent_id}: "
        f"outcome {checked.outcome if checked.outcome else 'none'}, "
        f"dependencies "
        f"{', '.join(checked.dependencies) if checked.dependencies else 'none'}. "
        f"{checked.detail}")


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The drafts stand {verdict.verdict}: "
        f"{verdict.passing_shown} of {verdict.total_shown} shown "
        f"drafts stand sound.")


def view_plain_words(view: Any) -> str:
    checked = _check_view_ref(view)
    return f"View {checked.view_id}: shows {checked.view_filter} drafts."


def note_plain_words(record_in: Any) -> str:
    checked = _check_note_ref(record_in)
    return (
        f"Note {checked.note_id}: {checked.stance} "
        f"{checked.draft_id}, toward {checked.target}. "
        f"{checked.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, SlicingIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.entries)} sound drafts for "
        f"{len(index.entries)} outcomes; unsound, named in "
        f"its gaps: {gaps}.")


def format_draft(draft: Any, source: Any = None) -> str:
    checked = _check_draft_ref(draft)
    book = _source_book(source) if source is not None else None
    lines = [f"{checked.title} ({checked.draft_id})"]
    lines.extend(plain_lines(checked))
    lines.append(checked.detail)
    if draft_sound(checked, book):
        lines.append(
            "This draft stands sound - one verifiable outcome "
            "at the house grain, its dependencies held and "
            "its intent approved.")
    else:
        lines.append(
            "This draft stands unsound - it stands named in "
            f"its gaps: {', '.join(draft_gaps(checked, book))}, and "
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
        f"Slicing note {checked.stance} {checked.draft_id} "
        f"({checked.note_id}): {checked.title}. {checked.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or reading it builds nothing, executes nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_outcome(source: Any, outcome: Any) -> str:
    draft = draft_for_outcome(source, outcome)
    if draft is not None:
        return format_draft(draft, source)
    wanted = outcome.strip() if isinstance(outcome, str) else outcome
    return (
        f"No held draft stands under outcome {wanted!r} yet - the "
        f"outcome reaches nothing in this book, and no draft is "
        f"invented for it.")


def format_book(source: Any = None, intent_id: Any = None) -> str:
    book = _source_book(source)
    drafts = (drafts_for_intent(book, intent_id)
              if intent_id is not None else book.drafts)
    lines = [f"The Slicing Engine (M-203) - {book.title}"]
    lines.extend(segment_of(draft, book) for draft in drafts)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Slicing panel under view {panel.view_id}:"]
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
    lines = ["Slicing index, derived from the held drafts:"]
    for entry in index.entries:
        lines.append(f"{entry.outcome} - {entry.title} ({entry.draft_id})")
    if index.gaps:
        lines.append(
            "Unsound, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "builds nothing, executes nothing and opens no network.")
    return "\n".join(lines)


def format_slicing_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "The Slicing Engine (M-203)",
        f"{book.title}: {len(book.drafts)} drafts held, "
        f"{len(passing_drafts(book))} drafts standing sound, "
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


def parse_slicing_args(args: Any) -> Tuple[str, Any]:
    """Parse the /slicing grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("draft", "view", "note"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("outcome", "intent"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("index", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
