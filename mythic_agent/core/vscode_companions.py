"""Cross-app method (roadmap slice M-239).

Part X - Bridges. The roadmap
words: **open-file-at-line, selection-into-context, and diff-in-editor bridges.******

What already ships, and what this editor adds:

* Mythic's bridge faces already ship (M-233 consuming, M-234 serving, M-235 the registry, M-236 the skills standard, M-237 the custom commands, M-238 the installable bundles, ``mythic_agent/core/plugin_bundles.py`` the nearest kin) and the editor embryos already stand in the tree: the VS Code family tasks and keybindings at ``editors/vscode-extension`` and the vim embryo at ``editors/vim-plugin``, with the M-090 editor bridge (``mythic_agent/core/editor_bridge.py``) holding the $EDITOR round-trip. This slice builds the VS Code family companions that grow out of the VS Code embryo: open-file-at-line, selection-into-context, and diff-in-editor bridges, each bridge held as data under one companion record, the file, line, selection, context and diff declared BEFORE any bridge is granted, the companion a local bridge record - terminal-first remains complete without any IDE, no network opened - with nothing opened, sent or shown live. The generic editor-agnostic road is M-240's own slice and is NOT built here: this book speaks for the VS Code family alone. The companions book WIRES that companion face as data, in its own module, standing in the M-195 copy-and-share
  book book the M-239 book stands in: one tracker
  per book, and the tracker's charge over one
  companion across its editor held as a book - a
  companion. The shipped companions stand untouched behind
  their seams: this layer holds companions as data
  over the book's editors and rewrites none of them,
  and the companions book keeps its own standing.
  Companions stand on the ledger AS DATA alone: a
  companion carries a ledger ref, a reference held in
  this book; holding, viewing or telling a companion
  editors no companion live, moves no keeper and files
  nothing.
* No charter row names this editor: the M-171 TUI
  redesign charter binds Part VIII alone (M-172
  to M-200) and names M-239 on no row, and the
  editor tests pin that absence live. The M-005
  method charter names no editor row either: its
  own words name the whole of Part IX (M-201
  to M-232) as the part that executes the
  charter; Part X stands on the roadmap's own
  words, and this slice is built to those words.

* A companion is held whole: the editor it
  answers for, linked by its editor id; its title;
  the companion steps it walked, held as data in
  walk companion; and the evidence it carries, held
  as data by editor. The companion walk is EXPLICIT:
  its sequence stands as data
  (:data:`STAGES`, :data:`TRANSITIONS`) -
  linked, probed, opened, shared, held -
  and a companion's standing is DERIVED at
  call time from its held steps and evidence
  alone: a companion that opens anywhere but
  linked, steps where the sequence does not
  allow, carries a bare claim in place of held
  evidence, or has not yet linked held stands
  open, linked in its gaps.
* The evidence is a closed vocabulary in two
  halves: the held evidence - file_ref,
  line_ref, selection_ref, context_ref, connection_ref, evidence
  a tracker can point to - and the bare claims -
  feeling, memory, assertion, summary, which
  stand as no evidence at all. A companion is
  shared from held evidence alone, never
  from a feeling: a companion holding a
  bare claim stands open, linked in its gaps.
* A companion stands only for an ACTIVE
  editor. The book holds each editor it answers
  for as a reference record - its id, its title
  and its standing, active or queued, held as
  data copied from the roadmap's own telling. A
  companion naming a editor that stands
  nowhere in the book refuses BY NAME, and a
  companion for a editor that is not active
  refuses BY NAME beside it: the tracker deals with
  the editor in hand, in roadmap companion, never a
  queued one, and a editor whose companion already
  stands complete is never opened twice - the
  current companion is derived, so a
  completed editor is never the current companion
  twice.
* The companion's trace is visible. A trace
  record holds one companion's walked steps
  as one trace line, exactly as walked, beside
  the companion. The derived trace is
  computed at call time from the companion's
  held steps; a held trace that no longer agrees
  with it stands stale, linked in the ledger - the
  trace is the walk itself, never a retelling
  of it.
* The companion index is DERIVED at call
  time from the held companions - one companion
  per complete companion, under the step it
  stands at - never a second stored copy that
  could drift. A stored index, standing verdict,
  panel, trace, companion or current-companion
  claim on any record refuses by name.
* The current companion is DERIVED at call
  time - the first held companion, in held
  companion, that does not yet stand complete - never
  stored where it could go stale.
* The notes are held as data: a note record
  naming its companion, its stance - note,
  concern, praise, question, a closed
  vocabulary - and what it feeds back toward,
  one record per companion stance; holding
  a note posts none of it, the rule stands as
  data (:data:`COMPANION_RULE`), and a record
  claiming a companion was actually held,
  captured or promoted live refuses BY NAME.
  The tracker companions - and those companions, too,
  are held as data here, never sent.
* The shipped data file holds one example book
  in exactly the book a real companion
  file takes, a loader reads a file anywhere on
  disk, companions and views are probed as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding a companion book for a session and
  telling from it. This layer reaches no live
  companion: it writes no companion live, files nothing
  to the ledger, captures no candidate, promotes
  nothing, spawns no tracker, destroys nothing,
  publishes nothing, sends nothing as the user,
  exposes no secret, weakens no security and
  opens no network - it holds companions
  as data and tells them.

Honesty rules, enforced here and pinned by tests:

* **The companion walk is explicit.** A
  companion is shared against the held
  steps and legal steps alone; an illegal step
  stands linked in its gaps, never silently
  reordered.
* **Complete stands on held evidence alone.** A
  companion that carries a feeling, a
  memory, an assertion or a summary in place of
  held evidence stands open, linked in its gaps:
  a companion is shared from evidence, not
  vibes.
* **Active editors only, in roadmap companion.** A
  companion for a missing or queued editor
  refuses by name; no companion is invented
  for a editor the tracker has not probed with.
* **Unknown stays unknown.** A companion
  whose steps are not yet held stands with its
  steps empty - no step is invented.
* **The index, panel, verdict, trace, companion
  and current companion are derived, never
  stored.** Each is derived from the held
  companions at call time; a stored one
  refuses by name, so it can never drift.
* **One companion per companion.** Two
  companions standing for one companion id
  refuse by name, and one note record stands per
  companion stance.
* **The notes are data alone.** The records
  hold the feedback; holding, viewing or telling
  them writes nothing, files nothing and posts
  nothing.
"""


from __future__ import annotations

__all__ = [
    "STAGE_FIELDS",
    "STAGES",
    "CLAIM_KINDS",
    "HELD_EVIDENCE",
    "BARE_CLAIMS",
    "TRANSITIONS",
    "EXAMPLE_STAGE",
    "STANCES",
    "INDEX_ACTION",
    "COMPANION_RESOURCE",
    "COMPANION_SCHEMA",
    "COMPANION_SLICE",
    "COMPANION_RULE",
    "PLAIN_EXPLANATION",
    "THE_COMPANION_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "COMPLETE_WORDS",
    "EDITOR_STATES",
    "CONNECTIONS",
    "Any",
    "Dict",
    "List",
    "Optional",
    "TraceRecord",
    "CompanionRecord",
    "IndexCompanion",
    "EditorRef",
    "NoteRecord",
    "CompanionBook",
    "CompanionIndex",
    "CompanionPanel",
    "CompanionPanelRow",
    "CompanionRegistry",
    "CompanionVerdict",
    "CompanionView",
    "TargetCount",
    "trace_for_companion",
    "trace_record",
    "ledger_record",
    "book_record",
    "build_trace",
    "build_book",
    "build_companion",
    "build_editor_ref",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "current_companion",
    "transition_breaks",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "companion_for_check",
    "companion_companion",
    "companion_record",
    "first_note",
    "format_book",
    "format_companion",
    "format_index",
    "format_note",
    "format_stage",
    "format_panel",
    "format_companion_screen",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "editor_record",
    "load_companion",
    "load_companion_file",
    "normalize_editor_state",
    "normalize_connection",
    "normalize_stage",
    "normalize_claim_kind",
    "legal_step",
    "next_stage",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_companion",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_companion_args",
    "green_companions",
    "plain_lines",
    "plain_words",
    "roadmap_record",
    "segment_of",
    "trace_of",
    "trace_current",
    "shown_companions",
    "validate_trace",
    "validate_book",
    "validate_companion",
    "validate_editor_ref",
    "validate_note",
    "validate_panel",
    "validate_row",
    "validate_verdict",
    "validate_view",
    "verdict_plain_words",
    "verdict_record",
    "view_plain_words",
    "view_record",
    "companion_gaps",
    "companion_green",
    "companions_for_editor",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

COMPANION_SCHEMA = "mythic.vscode_companions/1"
COMPANION_SLICE = "M-239"
THE_COMPANION_SLICE = COMPANION_SLICE
COMPANION_RESOURCE = "vscode_companions.yaml"
INDEX_ACTION = "index"
EXAMPLE_STAGE = "held"
STAGE_FIELDS = ("stages", "claims")
COMPLETE_WORDS = ("complete", "open")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "complete", "open")
VERDICT_WORDS = ("held", "held", "blocked")
EDITOR_STATES = ("live", "dormant")
CONNECTIONS = ("local", "remote", "unlinked")
COMPANION_RULE = "companions are held as data alone: open-file-at-line, selection-into-context, and diff-in-editor bridges for the VS Code family (the connections local, remote and unlinked, one connection held per editor as data) - one companion shelf per book, and the shelf charge over one companion held as a companion - a companion stands as data, held by reference (a file ref), never bridged live - the companion walk stands as an explicit companion sequence - linked, probed, opened, shared, held - and a companion completes only complete, complete being a state with evidence held - file ref, line ref, selection ref, context ref, diff ref, connection ref - never a feeling, a memory, an assertion or a summary; open-file-at-line, selection-into-context, and diff-in-editor bridges for the VS Code family - and a companion shared without opening, or held before it is shared, stands open, named in its gaps; a companion on an unlinked editor stands complete only with its connection held as a connection_ref; defining, reading, listing and telling a companion opens no file live, sends no selection, shows no diff, spawns no editor, opens no network and writes nothing outside held records"
PLAIN_EXPLANATION = "VS Code companions (M-239): open-file-at-line, selection-into-context, and diff-in-editor bridges for the VS Code family."
USAGE = 'Usage: /vscodecompanions | /vscodecompanions companion <companion-id> | /vscodecompanions stage <stage> | /vscodecompanions editor <editor-id> | /vscodecompanions view <view-id> | /vscodecompanions note <note-id> | /vscodecompanions index | /vscodecompanions panel | /vscodecompanions verdict'

STAGES = ("linked", "probed", "opened", "shared", "held")
HELD_EVIDENCE = ("file_ref", "line_ref", "selection_ref", "context_ref", "diff_ref", "connection_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
CLAIM_KINDS = HELD_EVIDENCE + BARE_CLAIMS
TRANSITIONS = {
    "linked": ("probed",),
    "probed": ("opened",),
    "opened": ("shared",),
    "shared": ("linked", "held"),
    "held": (),
}


def legal_step(before: Any, after: Any) -> bool:
    """Whether the gate sequence allows one step, DERIVED.

    The machine stands as data in TRANSITIONS:
    inspect steps only to build, build only to
    test, test to repair on a companion or to
    continue on a pass, repair back to build or
    test for the rerun, and continue steps
    nowhere - it is where a companion stands complete.
    A stage outside the machine allows nothing.
    """
    return after in TRANSITIONS.get(before, ())


def next_stage(stage: Any, failed: Any = False) -> Optional[str]:
    """The step the tracker takes next, DERIVED from the sequence.

    Banked leads to probed and probed to
    opened; opened leads to shared; at
    shared a follow-up banking steps back to linked and a finished companion steps to held;
    held is the end of the walk and steps
    nowhere. A step outside the sequence refuses
    by name.
    """
    shared = normalize_stage(stage)
    if shared == "linked":
        return "probed"
    if shared == "probed":
        return "opened"
    if shared == "opened":
        return "shared"
    if shared == "shared":
        return "linked" if failed else "held"
    return None


_HELDANCE = ("recorded_on", "actor", "source", "origin_session")
_RUN_KEYS = frozenset({
    "companion_id", "seq", "editor_id", "title", "stages",
    "claims", "detail",
} | set(_HELDANCE))
_SLICE_REF_KEYS = frozenset({
    "editor_id", "seq", "title", "state", "connection", "detail",
} | set(_HELDANCE))
_TRACE_KEYS = frozenset({
    "trace_id", "seq", "companion_id", "trace", "detail",
} | set(_HELDANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_HELDANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "companion_id", "stance", "target", "title",
    "detail",
} | set(_HELDANCE))
_DERIVED_KEYS = frozenset({
    "standing", "complete", "greens", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "companions", "coverage", "covered", "uncovered",
    "current_companion", "next_companion", "progress", "ledger",
    "current", "companion", "breaks", "live"})
_LIVE_KEYS = (
    "live_companion", "companions_live", "live_question",
    "companions_raise", "raises_slice", "raised_live",
    "answers_live", "answers_question", "answered_live",
    "delivers_live", "delivered_live", "companions_live",
    "resumed_live", "runs_companion", "paused_live",
    "runs_companion", "ran_companion", "spawns_process",
    "spawned_process", "builds_slice", "built_slice",
    "builds_live", "executes_slice", "executed_slice",
    "executes_live", "live_execution",
    "banks_slice", "banked_live", "companion_live",
    "pushes_slice", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_companion", "sent_companion",
    "posts_note", "held_note", "traces_live",
    "traced_live", "writes_ledger", "wrote_ledger", "files_companion", "filed_live", "spawns_tracker", "spawned_tracker", "sends_companion", "sent_companion", "writes_companion", "wrote_companion")


# ---------------------------------------------------------------------
# Small judges, in the sibling trace.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_stages(value: Any) -> Tuple[str, ...]:
    """A companion's walked stages, held as data.

    The stages stand as a list of stage names in
    walk companion, each one a stage of the explicit
    gate sequence; a walk not yet held stands
    honestly empty - no stage is invented - and
    a name outside the machine refuses.
    """
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError("stages must be a list of gate sequence stages")
    return tuple(normalize_stage(v) for v in value)

def _check_claims(value: Any) -> Tuple[str, ...]:
    """A companion's asked claims: claim editors linked as data.

    Each claim names one editor from the held
    vocabulary - the human editors the gate may ask
    and the code editors it must never ask, both
    held honestly as data - and a editor outside
    the vocabulary refuses.
    """
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError("claims must be a list of claim editors")
    return tuple(normalize_claim_kind(v) for v in value)

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


def _heldance(mapping: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key in _HELDANCE:
        if key == "recorded_on":
            out[key] = _clean_text(mapping.get(key), "a recorded_on editor")
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
                f"{what} claims a live gate companion or editor build "
                f"execution ({key!r} is linked on it): "
                f"{COMPANION_RULE}")
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


def normalize_editor_state(value: Any) -> str:
    state = _clean_text(value, "an editor state").lower()
    if state not in EDITOR_STATES:
        raise ValueError(
            f"editor state {state!r} is not one of the held "
            f"states: " + ", ".join(EDITOR_STATES))
    return state


def normalize_connection(value: Any) -> str:
    connection = _clean_text(value, "a connection").lower()
    if connection not in CONNECTIONS:
        raise ValueError(
            f"connection {connection!r} is not one of the "
            f"editor companion connections: " + ", ".join(CONNECTIONS))
    return connection


def normalize_view_filter(value: Any) -> str:
    view_filter = _clean_text(value, "a view filter").lower()
    if view_filter not in VIEW_FILTERS:
        raise ValueError(
            f"view filter {view_filter!r} is not one of the held "
            f"filters: " + ", ".join(VIEW_FILTERS))
    return view_filter


def normalize_stage(value: Any) -> str:
    stage = _clean_text(value, "a stage").lower()
    if stage not in STAGES:
        raise ValueError(
            f"stage {stage!r} is not one of the held "
            f"stages: " + ", ".join(STAGES))
    return stage


def normalize_claim_kind(value: Any) -> str:
    editor = _clean_text(value, "a claim editor").lower()
    if editor not in CLAIM_KINDS:
        raise ValueError(
            f"claim editor {editor!r} is not one of the held "
            f"editors: " + ", ".join(CLAIM_KINDS))
    return editor

# ---------------------------------------------------------------------
# The held companion: one editor cut from an active editor.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class CompanionRecord:
    """One companion editor, held as data.

    The companion names the active editor it was
    held from, by editor id, its title, its
    verifiable stages, held as data, and its
    claims, linked by companion id. The grain is
    derived, never stored: exactly one verifiable
    walk is opened against the machine. A companion whose
    stages are not yet held stands with its
    stages empty: it stands open, linked in
    its gaps, and no stage is invented for it.
    The companion is local data alone - no live build
    stands behind it: holding it builds nothing.
    """

    companion_id: str
    seq: int
    editor_id: str
    title: str
    stages: Tuple[str, ...] = ()
    claims: Tuple[str, ...] = ()
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "companion_id", _clean_text(self.companion_id, "a companion id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "editor_id", _clean_text(self.editor_id, "an editor id"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a companion title"))
        object.__setattr__(
            self, "stages", _check_stages(self.stages))
        object.__setattr__(
            self, "claims", _check_claims(self.claims))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a companion detail"))
        for key in _HELDANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.companion_id

    @property
    def stage(self) -> str:
        """The stage the companion stands at: its last walked stage."""
        return self.stages[-1] if self.stages else ""

    def to_record(self) -> Dict[str, Any]:
        record = {
            "companion_id": self.companion_id, "seq": self.seq,
            "editor_id": self.editor_id, "title": self.title,
            "stages": list(self.stages),
            "claims": list(self.claims),
            "detail": self.detail,
        }
        for key in _HELDANCE:
            record[key] = getattr(self, key)
        return record


def _check_connection_ref(value: Any) -> CompanionRecord:
    if not isinstance(value, CompanionRecord):
        raise ValueError("a companion must be a CompanionRecord")
    return value


def validate_companion(companion: Any) -> CompanionRecord:
    return _check_connection_ref(companion)


def build_companion(record: Any = None, **kwargs: Any) -> CompanionRecord:
    """Build one held companion from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, CompanionRecord):
        if kwargs:
            raise ValueError("a companion stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a companion must be a mapping or a CompanionRecord")
    _needed(data, _RUN_KEYS, "a companion")
    return CompanionRecord(
        companion_id=data.get("companion_id"), seq=data.get("seq"),
        editor_id=data.get("editor_id"), title=data.get("title"),
        stages=data.get("stages"),
        claims=data.get("claims"),
        detail=data.get("detail"),
        **_heldance(data))


def _breaks_map(book: Any) -> Dict[str, Tuple[str, ...]]:
    """Map each companion to the steps it took outside the machine.

    Derived from the held companions alone: a break is
    one consecutive pair of walked stages the
    explicit gate sequence does not allow, told
    in walk companion as before, then after.
    """
    linked: Dict[str, Tuple[str, ...]] = {}
    for companion in book.companions:
        breaks = tuple(
            f"{before} > {after}"
            for before, after in zip(companion.stages, companion.stages[1:])
            if not legal_step(before, after))
        if breaks:
            linked[companion.companion_id] = breaks
    return linked

def companion_gaps(companion: Any, source: Any = None) -> Tuple[str, ...]:
    """The gaps that keep a companion from standing complete.

    Guarded from the companion's own held fields alone -
    its walked steps against the explicit question
    sequence, and its held evidence against the
    held vocabulary: the companion opens at
    linked, steps only where the sequence
    allows, carries held evidence and no bare claim,
    and a companion stands complete only when it has
    linked held. The source names nothing
    further: no gap is borrowed from another
    companion.
    """
    shared = _check_connection_ref(companion)
    gaps: List[str] = []
    if not shared.stages:
        gaps.append(
            "has passed through no step: the companion has not started")
        return tuple(gaps)
    if shared.stages[0] != "linked":
        gaps.append(
            f"opens at {shared.stages[0]}, not at linked: "
            f"the companion opens with the reflection")
    for before, after in zip(shared.stages, shared.stages[1:]):
        if not legal_step(before, after):
            gaps.append(
                f"steps from {before} to {after}, which the "
                f"companion sequence does not allow")
    for editor in shared.claims:
        if editor in BARE_CLAIMS:
            gaps.append(
                f"carries a {editor} claim, a bare claim with no "
                f"held proof: complete stands on held proof alone")
    if source is not None:
        try:
            _ref = _source_book(source).slice_for(shared.editor_id)
        except Exception:
            _ref = None
        if _ref is not None and _ref.connection == "unlinked" and \
                "connection_ref" not in shared.claims:
            gaps.append(
                "stands shared on an unlinked editor with no "
                "connection_ref held: the connection for the "
                "editor is unlinked")
    if shared.stages[-1] != "held":
        gaps.append(
            f"has not reached held: the companion stands "
            f"at {shared.stages[-1]}")
    return tuple(gaps)

def companion_green(companion: Any, source: Any = None) -> bool:
    return not companion_gaps(companion, source)


def plain_lines(companion: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the companion's own fields."""
    shared = _check_connection_ref(companion)
    return (
        f"Companion: {shared.title}",
        f"Editor: {shared.editor_id}",
        f"Stage: {shared.stage if shared.stage else 'none'}",
        f"Claims: "
        f"{', '.join(shared.claims) if shared.claims else 'none'}",
    )


def segment_of(companion: Any, source: Any = None) -> str:
    shared = _check_connection_ref(companion)
    gaps = companion_gaps(shared, source)
    return (
        f"{shared.companion_id}: {shared.title} - editor: "
        f"'{shared.editor_id}' - stage: "
        f"'{shared.stage if shared.stage else 'none'}' - "
        f"stages: {len(shared.stages)} - claims: "
        f"'{', '.join(shared.claims) if shared.claims else 'none'}' - "
        f"detail: '{shared.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held editor reference: the active editor a book companions from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class EditorRef:
    """One editor a companion book companions from, held as a reference.

    The record names the editor, the title it
    opens and its standing - active or
    queued - held as data copied from the
    M-203 editor book's own telling. A companion
    stands only from an active reference: the
    book refuses a companion naming no held reference,
    and a companion from an queued one, BY NAME.
    """

    editor_id: str
    seq: int
    title: str
    state: str
    connection: str = "local"
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "editor_id", _clean_text(self.editor_id, "an editor id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a title"))
        object.__setattr__(
            self, "state", normalize_editor_state(self.state))
        object.__setattr__(
            self, "connection", normalize_connection(self.connection))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an editor detail"))
        for key in _HELDANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.editor_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "editor_id": self.editor_id, "seq": self.seq,
            "title": self.title, "state": self.state,
            "connection": self.connection,
            "detail": self.detail,
        }
        for key in _HELDANCE:
            record[key] = getattr(self, key)
        return record


def _check_editor_ref(value: Any) -> EditorRef:
    if not isinstance(value, EditorRef):
        raise ValueError("a editor reference must be an EditorRef")
    return value


def validate_editor_ref(ref: Any) -> EditorRef:
    return _check_editor_ref(ref)


def build_editor_ref(record: Any = None, **kwargs: Any) -> EditorRef:
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, EditorRef):
        if kwargs:
            raise ValueError(
                "a editor reference stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError(
            "a editor reference must be a mapping or an EditorRef")
    _needed(data, _SLICE_REF_KEYS, "a editor reference")
    return EditorRef(
        editor_id=data.get("editor_id"), seq=data.get("seq"),
        title=data.get("title"), state=data.get("state"), connection=data.get("connection") or "local",
        detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The held trace trace: the human approves the trace, as data.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TraceRecord:
    """One trace trace, held as data.

    The record names its editor and the trace the
    human active - the editor's companion ids in
    derived claim companion, held exactly as
    active. The trace is of the set and its
    companion, never of a step: when the derived
    trace moves, this record stands stale, linked
    in the ledger, until a new trace is active.
    """

    trace_id: str
    seq: int
    companion_id: str
    trace: str
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "trace_id",
            _clean_text(self.trace_id, "an trace id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "companion_id", _clean_text(self.companion_id, "an editor id"))
        object.__setattr__(
            self, "trace", _clean_text(self.trace, "an active trace"))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an trace detail"))
        for key in _HELDANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.trace_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "trace_id": self.trace_id, "seq": self.seq,
            "companion_id": self.companion_id, "trace": self.trace,
            "detail": self.detail,
        }
        for key in _HELDANCE:
            record[key] = getattr(self, key)
        return record


def _check_trace_ref(value: Any) -> TraceRecord:
    if not isinstance(value, TraceRecord):
        raise ValueError("an trace must be an TraceRecord")
    return value


def validate_trace(trace: Any) -> TraceRecord:
    return _check_trace_ref(trace)


def build_trace(record: Any = None, **kwargs: Any) -> TraceRecord:
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, TraceRecord):
        if kwargs:
            raise ValueError(
                "an trace stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError(
            "an trace must be a mapping or an TraceRecord")
    _needed(data, _TRACE_KEYS, "an trace")
    return TraceRecord(
        trace_id=data.get("trace_id"), seq=data.get("seq"),
        companion_id=data.get("companion_id"), trace=data.get("trace"),
        detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The held stance: a note on a companion, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One companion stance, held as data.

    The record names its companion, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per companion stance
    in a book. The record is data alone: holding
    it builds nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    companion_id: str
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
            self, "companion_id", _clean_text(self.companion_id, "a companion id"))
        object.__setattr__(self, "stance", normalize_stance(self.stance))
        object.__setattr__(
            self, "target", _clean_text(self.target, "a stance target"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a stance title"))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a stance detail"))
        for key in _HELDANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.note_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "note_id": self.note_id, "seq": self.seq,
            "companion_id": self.companion_id, "stance": self.stance,
            "target": self.target, "title": self.title,
            "detail": self.detail,
        }
        for key in _HELDANCE:
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
        companion_id=data.get("companion_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The held view: which editors a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class CompanionView:
    """A view over the book: every companion, the green, the rest."""

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
        for key in _HELDANCE:
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
        for key in _HELDANCE:
            record[key] = getattr(self, key)
        return record


def _check_view_ref(value: Any) -> CompanionView:
    if not isinstance(value, CompanionView):
        raise ValueError("a view must be an CompanionView")
    return value


def validate_view(view: Any) -> CompanionView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> CompanionView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, CompanionView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an CompanionView")
    _needed(data, _VIEW_KEYS, "a view")
    return CompanionView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class CompanionPanelRow:
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


def _row_for_companion(companion: CompanionRecord,
                     source: Any = None) -> CompanionPanelRow:
    return CompanionPanelRow(
        item_id=companion.companion_id,
        standing="complete" if companion_green(companion, source) else "open",
        label=companion.title, segment=segment_of(companion, source),
        recorded_on=companion.recorded_on)


def _check_row_ref(value: Any) -> CompanionPanelRow:
    if not isinstance(value, CompanionPanelRow):
        raise ValueError("a panel row must be an CompanionPanelRow")
    return value


def validate_row(row: Any, companion: Any = None,
                 source: Any = None) -> CompanionPanelRow:
    shared = _check_row_ref(row)
    if companion is not None:
        derived = _row_for_companion(_check_connection_ref(companion), source)
        if shared != derived:
            raise ValueError(
                f"panel row {shared.item_id!r} does not agree with "
                f"the row derived from its companion")
    return shared


def build_row(row: Any = None, companion: Any = None,
              source: Any = None,
              **kwargs: Any) -> CompanionPanelRow:
    if companion is not None:
        derived = _row_for_companion(_check_connection_ref(companion), source)
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            CompanionPanelRow(**kwargs))
        return validate_row(built, companion, source)
    if isinstance(row, CompanionPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in COMPLETE_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return CompanionPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on editor"))
    if row is None and kwargs:
        return CompanionPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an CompanionPanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[CompanionPanelRow, ...]
                 ) -> Tuple[TargetCount, ...]:
    counts: List[TargetCount] = []
    for standing in COMPLETE_WORDS:
        number = sum(1 for row in rows if row.standing == standing)
        if number:
            counts.append(TargetCount(standing=standing, items=number))
    return tuple(counts)


def _panel_account(total_items: int, total_shown: int,
                   green_shown: int,
                   target_counts: Tuple[TargetCount, ...],
                   view_filter: str, as_of: str) -> Tuple[str, ...]:
    standing_words = ", ".join(
        f"{count.standing} {count.items}"
        for count in target_counts) or "none"
    return (
        f"The companion book holds {total_items} companions as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {green_shown} of the shown companions "
        f"stand complete.",
        "Rows stand in held companion, the companion the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its companion's own fields "
        "- the editor it answers for, the steps it walked in the "
        "open and the evidence it honestly carries - and no "
        "judgement is stored on any companion.",
        "Completeness is opened from the held records alone: "
        "a companion that steps outside the companion sequence, "
        "carries a bare claim in place of held evidence, or has "
        "not linked held stands open, linked in its "
        "gaps, and the companion index is derived from the "
        "held companions, never stored where it could drift.",
    )

@dataclass(frozen=True)
class CompanionPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[CompanionPanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> CompanionView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, CompanionView):
        return view
    return book.view_for(view)


def shown_companions(source: Any, view: Any = None
                   ) -> Tuple[CompanionRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.companions
    if resolved.view_filter == "complete":
        return tuple(g for g in book.companions if companion_green(g, book))
    return tuple(g for g in book.companions if not companion_green(g, book))


def companions_for_editor(source: Any, editor_id: Any
                      ) -> Tuple[CompanionRecord, ...]:
    wanted = _clean_text(editor_id, "an editor id")
    return tuple(
        g for g in _source_book(source).companions if g.editor_id == wanted)


def green_companions(source: Any) -> Tuple[CompanionRecord, ...]:
    book = _source_book(source)
    return tuple(g for g in book.companions if companion_green(g, book))


def current_companion(source: Any) -> Optional[CompanionRecord]:
    """The book's current companion, DERIVED at call time.

    The first held companion, in held companion, that does
    not yet stand complete - where the Architect must
    look next. Nothing here is stored: the telling
    is derived from the held companions alone, so it can
    never go stale against them. A book whose every
    companion stands complete has no current companion.
    """
    book = _source_book(source)
    for companion in book.companions:
        if not companion_green(companion, book):
            return companion
    return None


def derive_panel(source: Any, view: Any = None) -> CompanionPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_companions(book, resolved)
    rows = tuple(_row_for_companion(companion, book) for companion in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.companions), default="")
    green = sum(1 for g in shown if companion_green(g, book))
    return CompanionPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.companions), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.companions), len(shown), green, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> CompanionPanel:
    if not isinstance(value, CompanionPanel):
        raise ValueError("a panel must be an CompanionPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> CompanionPanel:
    """Judge a stored panel against the panel derived from its book.

    Every derived field must agree; the stored
    panel's own name is its identity, not derived
    content (the M-182 companion).
    """
    shared = _check_panel_ref(panel)
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(shared.view_id)
                if shared.view_id is not None else None)
        derived = derive_panel(book, view)
        for attr in ("view_id", "view_filter", "rows", "total_items",
                     "total_shown", "target_counts", "as_of", "account"):
            if getattr(shared, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {shared.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return shared


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> CompanionPanel:
    if isinstance(panel, CompanionPanel):
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
        built = CompanionPanel(
            panel_id=_clean_text(data.get("panel_id"), "a panel id"),
            view_id=data.get("view_id"),
            view_filter=normalize_view_filter(data.get("view_filter")),
            rows=rows,
            total_items=_check_count(
                data.get("total_items"), "a total_items count"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            target_counts=counts,
            as_of=_clean_text(data.get("as_of"), "an as_of editor"),
            account=_check_lines(data.get("account"), "the account"))
        return validate_panel(built, source)
    if panel is None and source is not None:
        return derive_panel(source, kwargs.get("view"))
    raise ValueError("a panel must be a mapping, an CompanionPanel, or derived")


def _check_lines(value: Any, what: str) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError(f"{what} must be a list of lines")
    lines = []
    for line in value:
        lines.append(_clean_text(line, f"a line of {what}"))
    return tuple(lines)


def _verdict_word(total_shown: int, green_shown: int) -> str:
    if total_shown > 0 and green_shown == total_shown:
        return "held"
    if green_shown == 0:
        return "blocked"
    return "held"


@dataclass(frozen=True)
class CompanionVerdict:
    verdict: str
    view_id: Optional[str]
    total_shown: int
    green_shown: int
    latest_on: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict, "view_id": self.view_id,
            "total_shown": self.total_shown,
            "green_shown": self.green_shown,
            "latest_on": self.latest_on,
        }


def derive_verdict(source: Any, view: Any = None) -> CompanionVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_companions(book, resolved)
    green = sum(1 for g in shown if companion_green(g, book))
    latest = max((g.recorded_on for g in shown), default="")
    return CompanionVerdict(
        verdict=_verdict_word(len(shown), green),
        view_id=resolved.view_id, total_shown=len(shown),
        green_shown=green, latest_on=latest)


def _check_verdict_ref(value: Any) -> CompanionVerdict:
    if not isinstance(value, CompanionVerdict):
        raise ValueError("a verdict must be an CompanionVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> CompanionVerdict:
    shared = _check_verdict_ref(verdict)
    if shared.verdict not in VERDICT_WORDS:
        raise ValueError(f"verdict {shared.verdict!r} is not a held word")
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(shared.view_id)
                if shared.view_id is not None else None)
        derived = derive_verdict(book, view)
        if shared != derived:
            raise ValueError(
                "the stored verdict disagrees with the verdict "
                "derived from its book")
    return shared


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> CompanionVerdict:
    if isinstance(verdict, CompanionVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = CompanionVerdict(
            verdict=_clean_text(data.get("verdict"), "a verdict"),
            view_id=data.get("view_id"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            green_shown=_check_count(
                data.get("green_shown"), "a green_shown count"),
            latest_on=_clean_text(data.get("latest_on"), "a latest editor"))
        return validate_verdict(built, source)
    if verdict is None and source is not None:
        return derive_verdict(source, kwargs.get("view"))
    raise ValueError(
        "a verdict must be a mapping, an CompanionVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held editors' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexCompanion:
    stage: str
    companion_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "stage": self.stage, "companion_id": self.companion_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class CompanionIndex:
    """The companion index, derived from the held companions.

    The index names one companion per green companion, in
    held companion - the companion's own one verifiable
    stage, its companion id and its title - and the
    companions that do not stand complete, linked in its
    gaps. Nothing here is stored on any companion: the
    index is derived at call time from the held
    records alone, so it can never drift from them.
    """

    companions: Tuple[IndexCompanion, ...]
    gaps: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "companions": [e.to_record() for e in self.companions],
            "gaps": list(self.gaps),
        }


def derive_index(source: Any) -> CompanionIndex:
    """Derive the companion index from the book's held companions."""
    book = _source_book(source)
    companions = tuple(
        IndexCompanion(stage=g.stage, companion_id=g.companion_id,
                   title=g.title)
        for g in book.companions if companion_green(g, book))
    gaps = tuple(
        g.companion_id for g in book.companions if not companion_green(g, book))
    return CompanionIndex(companions=companions, gaps=gaps)


def companion_for_check(source: Any, stage: Any) -> Optional[CompanionRecord]:
    """The first held companion one stage reaches, or none - honestly."""
    if stage is None:
        return None
    if not isinstance(stage, str):
        raise ValueError("an stage must be a string naming the stage")
    wanted = stage.strip()
    if not wanted:
        return None
    for companion in _source_book(source).companions:
        if companion.stage == wanted:
            return companion
    return None


def transition_breaks(source: Any) -> Tuple[str, ...]:
    """Every step outside the gate sequence, DERIVED.

    One telling per break, in held companion: the companion
    that took it and the step it took, before,
    then after. A book whose companions all walk inside
    the machine tells none.
    """
    book = _source_book(source)
    return tuple(
        f"{companion_id}: {step}"
        for companion_id, steps in _breaks_map(book).items()
        for step in steps)

def companion_companion(source: Any,
              editor_id: Any = None) -> Tuple[CompanionRecord, ...]:
    """The held companions in their held companion, DERIVED at call time.

    Companions stand in the companion the book holds them -
    the companion their editors were linked - optionally
    for one editor alone. Nothing here is stored:
    the companion is the book's own held companion, told.
    """
    book = _source_book(source)
    companions = list(book.companions)
    if editor_id is not None:
        wanted = _clean_text(editor_id, "a editor id")
        companions = [r for r in companions if r.editor_id == wanted]
    return tuple(companions)

def trace_of(source: Any, companion_id: Any) -> str:
    """One companion's trace, DERIVED at call time.

    The companion's walked stages shared as one trace
    line, in walk companion. A companion that has walked
    nowhere traces empty: the trace tells only
    what stands walked, and the walk is linked
    elsewhere.
    """
    companion = _source_book(source).companion_for(companion_id)
    return " > ".join(companion.stages)

def trace_for_companion(source: Any,
                  companion_id: Any) -> Optional[TraceRecord]:
    """The held trace for one companion, or none - honestly."""
    wanted = _clean_text(companion_id, "a companion id")
    for record in _source_book(source).traces:
        if record.companion_id == wanted:
            return record
    return None

def trace_current(source: Any, companion_id: Any) -> bool:
    """Whether the held trace agrees with the derived trace.

    The trace stands current only while the trace
    it holds is the trace the book derives now; a
    moved walk leaves it stale, and no trace at
    all traces nothing.
    """
    trace = trace_for_companion(source, companion_id)
    if trace is None:
        return False
    return trace.trace == trace_of(source, companion_id)

def note_for_companion(source: Any, companion_id: Any,
                   stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one companion (and stance, when linked)."""
    wanted = _clean_text(companion_id, "a companion id")
    for record in _source_book(source).notes:
        if record.companion_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the editor targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


def ledger_record(source: Any = None) -> Dict[str, Any]:
    """The companion ledger, DERIVED here from the held companions alone.

    The ledger counts the held companions by their
    derived completeness - green and red - names
    the current companion, the first that does not yet
    stand complete, tells each held companion's trace
    standing - current while its held trace
    agrees with its derived trace, stale when it
    has moved, unheld while no trace stands for
    it - and names every step the held companions took
    outside the gate sequence. Nothing here is
    stored: the telling is derived at call time.
    """
    book = _source_book(source)
    standings = []
    for standing in COMPLETE_WORDS:
        number = sum(
            1 for g in book.companions
            if ("complete" if companion_green(g, book) else "open") == standing)
        standings.append({"standing": standing, "companion_records": number})
    current = current_companion(book)
    traces = []
    for companion in book.companions:
        trace = trace_for_companion(book, companion.companion_id)
        if trace is None:
            standing = "unheld"
        elif trace_current(book, companion.companion_id):
            standing = "current"
        else:
            standing = "stale"
        traces.append({"companion_id": companion.companion_id, "trace": standing})
    return {
        "type": "companion_well",
        "editor": COMPANION_SLICE,
        "standings": standings,
        "total": len(book.companions),
        "current_companion": current.companion_id if current is not None else None,
        "traces": traces,
        "breaks": list(transition_breaks(book)),
    }

def roadmap_record() -> Dict[str, Any]:
    """This editor's own roadmap standing, proved from the roadmap itself.

    The record loads this editor's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 editors in 11 parts,
    the linked prefix, the next editor where the
    companion companions, and M-239's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(COMPANION_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "companion_roadmap",
        "editor": COMPANION_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m239_title": own.title,
        "m239_part": own.part,
        "m239_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: editors, companions, views, notes and trace traces held
# together, one pinned panel at most per telling, and no verdict,
# index, trace or companion ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class CompanionBook:
    title: str
    editors: Tuple[EditorRef, ...] = ()
    companions: Tuple[CompanionRecord, ...] = ()
    views: Tuple[CompanionView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    traces: Tuple[TraceRecord, ...] = ()
    panels: Tuple[CompanionPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        editors = tuple(_check_editor_ref(g) for g in self.editors)
        companions = tuple(_check_connection_ref(g) for g in self.companions)
        views = tuple(_check_view_ref(v) for v in self.views)
        notes = tuple(_check_note_ref(m) for m in self.notes)
        traces = tuple(_check_trace_ref(a) for a in self.traces)
        panels = tuple(_check_panel_ref(pn) for pn in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for ref in editors:
            if ref.editor_id in seen_ids:
                raise ValueError(
                    f"two editor references stand under id {ref.editor_id!r}")
            if ref.seq in seen_seqs:
                raise ValueError(
                    f"two editor references stand at sequence {ref.seq}")
            seen_ids.add(ref.editor_id)
            seen_seqs.add(ref.seq)
        companion_ids = set()
        companion_seqs = set()
        for companion in companions:
            if companion.companion_id in companion_ids:
                raise ValueError(
                    f"two companions stand under id {companion.companion_id!r}")
            if companion.seq in companion_seqs:
                raise ValueError(
                    f"two companions stand at sequence {companion.seq}")
            companion_ids.add(companion.companion_id)
            companion_seqs.add(companion.seq)
        by_slice = {ref.editor_id: ref for ref in editors}
        for companion in (companions if editors else ()):

            ref = by_slice.get(companion.editor_id)
            if ref is None:
                raise ValueError(
                    f"companion {companion.companion_id!r} is held from editor "
                    f"{companion.editor_id!r}, which stands nowhere in "
                    f"this book")
            if ref.state != "live":
                raise ValueError(
                    f"companion {companion.companion_id!r} is held from editor "
                    f"{companion.editor_id!r}, which is not active: "
                    f"no editor is held from an queued editor")
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
            target = (record.companion_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for companion "
                    f"{record.companion_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per companion target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        trace_ids = set()
        trace_seqs = set()
        trace_companions = set()
        companion_ids = {companion.companion_id for companion in companions}
        for record in traces:
            if record.trace_id in trace_ids:
                raise ValueError(
                    f"two traces stand under id {record.trace_id!r}")
            if record.seq in trace_seqs:
                raise ValueError(
                    f"two traces stand at sequence {record.seq}")
            if record.companion_id in trace_companions:
                raise ValueError(
                    f"two traces stand for companion "
                    f"{record.companion_id!r}: one trace stands "
                    f"per companion walk")
            if companions and record.companion_id not in companion_ids:
                raise ValueError(
                    f"trace {record.trace_id!r} traces companion "
                    f"{record.companion_id!r}, which stands nowhere in "
                    f"this book")
            trace_ids.add(record.trace_id)
            trace_seqs.add(record.seq)
            trace_companions.add(record.companion_id)
        object.__setattr__(
            self, "editors", tuple(sorted(editors, key=lambda g: g.seq)))
        object.__setattr__(
            self, "companion_records", tuple(sorted(companions, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(
            self, "traces",
            tuple(sorted(traces, key=lambda a: a.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.companions + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.companion_id for g in self.companions) + tuple(
            v.view_id for v in self.views)

    def companion_ids(self) -> Tuple[str, ...]:
        return tuple(g.companion_id for g in self.companions)

    def editor_ids(self) -> Tuple[str, ...]:
        return tuple(g.editor_id for g in self.editors)

    def companion_for(self, companion_id: Any) -> CompanionRecord:
        wanted = _clean_text(companion_id, "a companion id")
        for companion in self.companions:
            if companion.companion_id == wanted:
                return companion
        raise KeyError(f"no companion linked {wanted!r} stands in this book")

    def slice_for(self, editor_id: Any) -> EditorRef:
        wanted = _clean_text(editor_id, "an editor id")
        for ref in self.editors:
            if ref.editor_id == wanted:
                return ref
        raise KeyError(f"no editor linked {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> CompanionView:
        wanted = _clean_text(view_id, "a view id")
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no view linked {wanted!r} stands in this book")

    def note_for(self, note_id: Any) -> NoteRecord:
        wanted = _clean_text(note_id, "a stance id")
        for record in self.notes:
            if record.note_id == wanted:
                return record
        raise KeyError(f"no stance linked {wanted!r} stands in this book")

    def trace_for(self, trace_id: Any) -> TraceRecord:
        wanted = _clean_text(trace_id, "an trace id")
        for record in self.traces:
            if record.trace_id == wanted:
                return record
        raise KeyError(f"no trace linked {wanted!r} stands in this book")

    def item_for(self, item_id: Any) -> Any:
        wanted = _clean_text(item_id, "an item id")
        for companion in self.companions:
            if companion.companion_id == wanted:
                return companion
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item linked {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "editors": [g.to_record() for g in self.editors],
            "companion_records": [g.to_record() for g in self.companions],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "traces": [a.to_record() for a in self.traces],
            "panels": [pn.to_record() for pn in self.panels],
        }


def _judge_book_panels(book: CompanionBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: CompanionBook) -> None:
    if book.title != "VS Code companions at the M-239 slice run":
        raise ValueError("the shipped example book carries another title")
    if len(book.editors) != 3 or len(book.companions) != 5 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold three editor references, five companions and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.traces) != 1:
        raise ValueError("the shipped example book must hold one trace record")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-editor":
        raise ValueError("the pinned panel is panel-editor")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "held" or verdict.green_shown != 3:
        raise ValueError("the shipped example book verdict must stand held at three complete of five")
    index = derive_index(book)
    if [e.stage for e in index.companions] != ["held", "held", "held"]:
        raise ValueError("the shipped example book index must derive the three held complete companions in held companion")
    if index.gaps != ("companion-bare-companion", "companion-leaping-companion"):
        raise ValueError("the shipped example book must leave the bare and leaping companions honestly open, linked in its gaps")
    linked = companion_for_check(book, EXAMPLE_STAGE)
    if linked is None or linked.companion_id != "companion-held-companion":
        raise ValueError("the shipped example book must reach its opening companion under the example stage")
    if trace_of(book, "companion-held-companion") != "linked > probed > opened > shared > held":
        raise ValueError("the shipped example book must derive the opening companion's trace from its walked steps")
    if not trace_current(book, "companion-held-companion"):
        raise ValueError("the shipped example book must hold the opening companion's trace current")
    first = first_note(book)
    if first is None or first.note_id != "note-note-first":
        raise ValueError("the shipped example book must hold the opening note as its first note companion")

def validate_book(data: Any, *, require_example: bool = False) -> CompanionBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, CompanionBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a companion book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live editor build or execution "
                f"({key!r} is linked on it): {COMPANION_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its companions under a view")
    if "companion_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held companions at call time")
    if "ledger" in data or "current_companion" in data:
        raise ValueError(
            "a book stores no ledger and no current companion: both are "
            "derived from its held companions at call time")
    if "trace" in data or "companion" in data:
        raise ValueError(
            "a book stores no trace and no companion: both are derived "
            "from its held companions at call time; an trace record "
            "holds the trace the human active")
    if data.get("schema") is not None and (
            data["schema"] != COMPANION_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{COMPANION_SCHEMA!r}")
    if data.get("editor") is not None and (
            data["editor"] != COMPANION_SLICE):
        raise ValueError(
            f"a book's editor must be {COMPANION_SLICE!r}")
    head = data.get("companion_head") or data.get("vscode_companions") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's companion head must be a mapping")
    title = head.get("title") or data.get("title")
    editors = tuple(build_editor_ref(g) for g in data.get("editors") or ())
    companions = tuple(build_companion(g) for g in data.get("companion_records") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    traces = tuple(build_trace(a) for a in data.get("traces") or ())
    book = CompanionBook(
        title=title, editors=editors, companions=companions, views=views,
        notes=notes, traces=traces, panels=())
    panels = tuple(
        build_panel(pn, book) for pn in data.get("panels") or ())
    book = CompanionBook(
        title=book.title, editors=book.editors, companions=book.companions,
        views=book.views, notes=book.notes,
        traces=book.traces, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> CompanionBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (CompanionBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an CompanionBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> CompanionBook:
    return validate_book(data, require_example=require_example)


def load_companion(
        data: Optional[Dict[str, Any]] = None) -> CompanionBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(COMPANION_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_companion_file(path: Any) -> CompanionBook:
    """Load one companion file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: editor references, companions and views held one by one.
# ---------------------------------------------------------------------

class CompanionRegistry:
    """An in-memory holding of editor references, companions and views.

    The registry is the pure layer's model of a
    session's companion book: editor references are
    held under their ids, companions are held under
    their ids, one companion per id and per sequence,
    and views are held in probed companion, one view
    per sequence and per id. Holding is data only -
    nothing held here builds anything, executes
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._slices: List[EditorRef] = []
        self._companions: List[CompanionRecord] = []
        self._views: List[CompanionView] = []
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

    def register_editor_ref(self, item: Any) -> EditorRef:
        """Hold one editor reference, opened whole before held."""
        shared = _check_editor_ref(item)
        return self._register(
            self._slices, shared, "editor_id", "editor reference")

    def register_companion(self, item: Any) -> CompanionRecord:
        """Hold one companion, opened whole before held."""
        shared = _check_connection_ref(item)
        return self._register(
            self._companions, shared, "companion_id", "companion")

    def register_view(self, view: Any) -> CompanionView:
        """Hold one view; a view naming no id takes a fresh one."""
        shared = _check_view_ref(view)
        if not shared.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            shared = build_view({**shared.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, shared, "view_id", "view")

    def register_book(self, book: Any) -> CompanionBook:
        """Hold a whole book's records, under its title."""
        shared = build_book(book)
        if self._title is not None and shared.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {shared.title!r}")
        for ref in shared.editors:
            self.register_editor_ref(ref)
        for companion in shared.companions:
            self.register_companion(companion)
        for view in shared.views:
            self.register_view(view)
        self._title = shared.title
        return self.book()

    def book(self) -> CompanionBook:
        return CompanionBook(
            title=self._title or "An unheld companion book",
            editors=tuple(self._slices), companions=tuple(self._companions),
            views=tuple(self._views), notes=(), traces=(), panels=())

    def list_slices(self) -> Tuple[EditorRef, ...]:
        return tuple(self._slices)

    def list_companions(self) -> Tuple[CompanionRecord, ...]:
        return tuple(self._companions)

    def list_views(self) -> Tuple[CompanionView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._companions) + tuple(self._views)

    def get_slice(self, editor_id: Any) -> EditorRef:
        return self.book().slice_for(editor_id)

    def get_companion(self, companion_id: Any) -> CompanionRecord:
        return self.book().companion_for(companion_id)

    def get_view(self, view_id: Any) -> CompanionView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records traced for the ledger target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> CompanionBook:
    if source is None:
        return load_companion()
    if isinstance(source, CompanionBook):
        return source
    if isinstance(source, CompanionRegistry):
        return source.book()
    return build_book(source)


def _heldance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _HELDANCE}


def companion_record(companion: Any, source: Any = None) -> Dict[str, Any]:
    shared = _check_connection_ref(companion)
    book = _source_book(source) if source is not None else None
    record = {
        "type": "companion_companion",
        "editor": COMPANION_SLICE,
        "companion_id": shared.companion_id,
        "editor_id": shared.editor_id,
        "title": shared.title,
        "segment": segment_of(shared, book),
        "complete": companion_green(shared, book),
        "gaps": list(companion_gaps(shared, book)),
    }
    record.update(_heldance_record(shared))
    return record


def editor_record(ref: Any) -> Dict[str, Any]:
    shared = _check_editor_ref(ref)
    record = {
        "type": "companion_run",
        "editor": COMPANION_SLICE,
        "editor_id": shared.editor_id,
        "title": shared.title,
        "state": shared.state, "connection": shared.connection,
    }
    record.update(_heldance_record(shared))
    return record


def trace_record(record_in: Any) -> Dict[str, Any]:
    shared = _check_trace_ref(record_in)
    record = {
        "type": "companion_trace",
        "editor": COMPANION_SLICE,
        "trace_id": shared.trace_id,
        "companion_id": shared.companion_id,
        "trace": shared.trace,
    }
    record.update(_heldance_record(shared))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    shared = _check_view_ref(view)
    record = {
        "type": "companion_view",
        "editor": COMPANION_SLICE,
        "view_id": shared.view_id, "seq": shared.seq,
        "view_filter": shared.view_filter,
    }
    record.update(_heldance_record(shared))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    shared = _check_note_ref(record_in)
    record = {
        "type": "companion_note",
        "editor": COMPANION_SLICE,
        "note_id": shared.note_id,
        "companion_id": shared.companion_id,
        "stance": shared.stance,
    }
    record.update(_heldance_record(shared))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    shared = validate_panel(panel, source)
    record = {"type": "companion_panel",
              "editor": COMPANION_SLICE}
    record.update(shared.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, CompanionVerdict):
        shared = validate_verdict(verdict, source)
    else:
        shared = derive_verdict(_source_book(verdict), view)
    record = {"type": "companion_verdict",
              "editor": COMPANION_SLICE}
    record.update(shared.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, CompanionIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "companion_index",
              "editor": COMPANION_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    shared = _source_book(book)
    record = {"type": "companion_book",
              "editor": COMPANION_SLICE,
              "title": shared.title}
    record.update(shared.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(companion: Any, source: Any = None) -> str:
    shared = _check_connection_ref(companion)
    return (
        f"{shared.title} - from {shared.editor_id}: "
        f"stage {shared.stage if shared.stage else 'none'}, "
        f"claims "
        f"{', '.join(shared.claims) if shared.claims else 'none'}. "
        f"{shared.detail}")


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The companions stand {verdict.verdict}: "
        f"{verdict.green_shown} of {verdict.total_shown} shown "
        f"companions stand complete.")


def view_plain_words(view: Any) -> str:
    shared = _check_view_ref(view)
    return f"View {shared.view_id}: shows {shared.view_filter} companions."


def note_plain_words(record_in: Any) -> str:
    shared = _check_note_ref(record_in)
    return (
        f"Note {shared.note_id}: {shared.stance} "
        f"{shared.companion_id}, toward {shared.target}. "
        f"{shared.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, CompanionIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.companions)} green companions; "
        f"red, linked in its gaps: {gaps}.")

def format_companion(companion: Any, source: Any = None) -> str:
    shared = _check_connection_ref(companion)
    book = _source_book(source) if source is not None else None
    lines = [f"{shared.title} ({shared.companion_id})"]
    lines.extend(plain_lines(shared))
    lines.append(shared.detail)
    if companion_green(shared, book):
        lines.append(
            "This companion stands complete - it walked the question "
            "sequence in the open from linked to held, "
            "and it carries held evidence alone.")
    else:
        lines.append(
            "This companion stands open - it stands linked in "
            f"its gaps: {', '.join(companion_gaps(shared, book))}, and "
            "nothing is invented for it.")
    return "\n".join(lines)

def format_view(view: Any) -> str:
    shared = _check_view_ref(view)
    return (
        f"View {shared.view_id}: filter {shared.view_filter} - "
        f"{shared.detail}")


def format_note(record_in: Any) -> str:
    shared = _check_note_ref(record_in)
    lines = [
        f"Companion note {shared.stance} {shared.companion_id} "
        f"({shared.note_id}): {shared.title}. {shared.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or companion it builds nothing, executes nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_stage(source: Any, stage: Any) -> str:
    companion = companion_for_check(source, stage)
    if companion is not None:
        return format_companion(companion, source)
    wanted = stage.strip() if isinstance(stage, str) else stage
    return (
        f"No held companion stands under stage {wanted!r} yet - the "
        f"stage reaches nothing in this book, and no companion is "
        f"invented for it.")


def format_book(source: Any = None, editor_id: Any = None) -> str:
    book = _source_book(source)
    companions = (companions_for_editor(book, editor_id)
              if editor_id is not None else book.companions)
    lines = [f"The VS Code Companions (M-239) - {book.title}"]
    lines.extend(segment_of(companion, book) for companion in companions)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Companion panel under view {panel.view_id}:"]
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
    lines = ["Companion index, derived from the held companions:"]
    for companion in index.companions:
        lines.append(f"{companion.stage} - {companion.title} ({companion.companion_id})")
    if index.gaps:
        lines.append(
            "Red, linked honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "builds nothing, executes nothing and opens no network.")
    return "\n".join(lines)


def format_companion_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "The VS Code Companions (M-239)",
        f"{book.title}: {len(book.companions)} companions held, "
        f"{len(green_companions(book))} companions standing green, "
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


def parse_companion_args(args: Any) -> Tuple[str, Any]:
    """Parse the /companion grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("companion", "view", "note"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("stage", "editor"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("index", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
