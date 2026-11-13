"""Templates (roadmap slice M-217).

Part IX - The Mythic Method Engine. The roadmap
words: **house shapes (feature build, bug hunt, migration, hardening, docs) as starting campaign files.*

What already ships, and what this slice adds:

* The templates book already ships as data
  (M-201, ``core/templates.py``): a roadmap/template
  file (parts, slices, acceptance checks, state) the
  app reads. This slice WIRES the shape that book's
  shape invites - several templates held across
  kinds with one shelf over them - as data, in its
  own module, standing in the M-195 copy-and-share
  book shape the M-217 book stands in: one shapekeeper
  per shape, and the shapekeeper's charge over one
  template across its kind held as a book - a
  template. The shipped roads stand untouched behind
  their seams: this layer holds templates as data
  over the shape's kinds and rewrites none of them,
  and the templates book keeps its own standing.
  Templates stand on the shelf AS DATA alone: a
  template carries a shelf ref, a reference held in
  this book; holding, viewing or telling a template
  runs no template live, moves no keeper and files
  nothing.
* No charter row names this slice: the M-171 TUI
  redesign charter binds Part VIII alone (M-172
  to M-200) and names M-217 on no row, and the
  slice tests pin that absence live. The M-005
  method charter names no slice row either: its
  own words name the whole of Part IX as the
  part that executes the charter, and this slice
  is built to the roadmap words and that
  execution note together.

* A template is held whole: the slice it
  answers for, named by its slice id; its title;
  the template steps it walked, held as data in
  walk order; and the evidence it carries, held
  as data by kind. The template walk is EXPLICIT:
  its sequence stands as data
  (:data:`CHECKS`, :data:`TRANSITIONS`) -
  drafted, shaped, checked, approved, issued -
  and a template's standing is DERIVED at
  call time from its held steps and evidence
  alone: a template that opens anywhere but
  drafted, steps where the sequence does not
  allow, carries a bare claim in place of held
  evidence, or has not yet reached issued stands
  open, named in its gaps.
* The evidence is a closed vocabulary in two
  halves: the held evidence - kind_ref,
  shelf_ref, keeper_record, issue_ref, evidence
  a shapekeeper can point to - and the bare claims -
  feeling, memory, assertion, summary, which
  stand as no evidence at all. A template is
  approved from held evidence alone, never
  from a feeling: a template holding a
  bare claim stands open, named in its gaps.
* A template stands only for an ACTIVE
  slice. The book holds each slice it answers
  for as a reference record - its id, its title
  and its standing, active or queued, held as
  data copied from the roadmap's own telling. A
  template naming a slice that stands
  nowhere in the book refuses BY NAME, and a
  template for a slice that is not active
  refuses BY NAME beside it: the shapekeeper deals with
  the slice in hand, in roadmap order, never a
  queued one, and a slice whose template already
  stands complete is never checked twice - the
  current template is derived, so a
  completed slice is never the current template
  twice.
* The template's trace is visible. A trace
  record holds one template's walked steps
  as one trace line, exactly as walked, beside
  the template. The derived trace is
  computed at call time from the template's
  held steps; a held trace that no longer agrees
  with it stands stale, named in the shelf - the
  trace is the walk itself, never a retelling
  of it.
* The template index is DERIVED at call
  time from the held templates - one entry
  per complete template, under the step it
  stands at - never a second stored copy that
  could drift. A stored index, standing verdict,
  panel, trace, order or current-template
  claim on any record refuses by name.
* The current template is DERIVED at call
  time - the first held template, in held
  order, that does not yet stand complete - never
  stored where it could go stale.
* The notes are held as data: a note record
  naming its template, its stance - note,
  concern, praise, question, a closed
  vocabulary - and what it feeds back toward,
  one record per template stance; holding
  a note posts none of it, the rule stands as
  data (:data:`TEMPLATE_RULE`), and a record
  claiming a template was actually issued,
  captured or promoted live refuses BY NAME.
  The shapekeeper reports - and those reports, too,
  are held as data here, never sent.
* The shipped data file holds one example book
  in exactly the shape a real template
  file takes, a loader reads a file anywhere on
  disk, templates and views are shaped as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding a template book for a session and
  telling from it. This layer reaches no live
  road: it writes no template live, files nothing
  to the ledger, captures no candidate, promotes
  nothing, spawns no shapekeeper, destroys nothing,
  publishes nothing, sends nothing as the user,
  exposes no secret, weakens no security and
  opens no network - it holds templates
  as data and tells them.

Honesty rules, enforced here and pinned by tests:

* **The template walk is explicit.** A
  template is approved against the held
  steps and legal steps alone; an illegal step
  stands named in its gaps, never silently
  reordered.
* **Complete stands on held evidence alone.** A
  template that carries a feeling, a
  memory, an assertion or a summary in place of
  held evidence stands open, named in its gaps:
  a template is approved from evidence, not
  vibes.
* **Active slices only, in roadmap order.** A
  template for a missing or queued slice
  refuses by name; no template is invented
  for a slice the shapekeeper has not dealt with.
* **Unknown stays unknown.** A template
  whose steps are not yet held stands with its
  steps empty - no step is invented.
* **The index, panel, verdict, trace, order
  and current template are derived, never
  stored.** Each is derived from the held
  templates at call time; a stored one
  refuses by name, so it can never drift.
* **One template per template.** Two
  templates standing for one template id
  refuse by name, and one note record stands per
  template stance.
* **The notes are data alone.** The records
  hold the feedback; holding, viewing or telling
  them writes nothing, files nothing and posts
  nothing.
"""


from __future__ import annotations

__all__ = [
    "CHECK_FIELDS",
    "CHECKS",
    "CLAIM_KINDS",
    "HELD_EVIDENCE",
    "BARE_CLAIMS",
    "TRANSITIONS",
    "EXAMPLE_CHECK",
    "STANCES",
    "INDEX_ACTION",
    "TEMPLATE_RESOURCE",
    "TEMPLATE_SCHEMA",
    "TEMPLATE_SLICE",
    "TEMPLATE_RULE",
    "PLAIN_EXPLANATION",
    "THE_TEMPLATE_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "COMPLETE_WORDS",
    "KIND_STATES",
    "Any",
    "Dict",
    "List",
    "Optional",
    "TraceRecord",
    "TemplateRecord",
    "IndexEntry",
    "KindRef",
    "NoteRecord",
    "TemplateBook",
    "TemplateIndex",
    "TemplatePanel",
    "TemplatePanelRow",
    "TemplateRegistry",
    "TemplateVerdict",
    "TemplateView",
    "TargetCount",
    "trace_for_template",
    "trace_record",
    "shelf_record",
    "book_record",
    "build_trace",
    "build_book",
    "build_template",
    "build_kind_ref",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "current_template",
    "transition_breaks",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "template_for_check",
    "template_order",
    "template_record",
    "first_note",
    "format_book",
    "format_template",
    "format_index",
    "format_note",
    "format_check",
    "format_panel",
    "format_template_screen",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "kind_record",
    "load_template",
    "load_template_file",
    "normalize_kind_state",
    "normalize_check",
    "normalize_claim_kind",
    "legal_step",
    "next_check",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_template",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_template_args",
    "green_templates",
    "plain_lines",
    "plain_words",
    "roadmap_record",
    "segment_of",
    "trace_of",
    "trace_current",
    "shown_templates",
    "validate_trace",
    "validate_book",
    "validate_template",
    "validate_kind_ref",
    "validate_note",
    "validate_panel",
    "validate_row",
    "validate_verdict",
    "validate_view",
    "verdict_plain_words",
    "verdict_record",
    "view_plain_words",
    "view_record",
    "template_gaps",
    "template_green",
    "templates_for_kind",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

TEMPLATE_SCHEMA = "mythic.campaign_templates/1"
TEMPLATE_SLICE = "M-217"
THE_TEMPLATE_SLICE = TEMPLATE_SLICE
TEMPLATE_RESOURCE = "campaign_templates.yaml"
INDEX_ACTION = "index"
EXAMPLE_CHECK = "issued"
CHECK_FIELDS = ("checks", "claims")
COMPLETE_WORDS = ("complete", "open")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "complete", "open")
VERDICT_WORDS = ("issued", "held", "blocked")
KIND_STATES = ("live", "dormant")
TEMPLATE_RULE = 'templates are held as data alone: several templates across kinds stand with one shelf, keepers per template, and the human sees the whole forge at a issue - a issue stands as data, held by reference (a issue ref), never taken live - the template walk stands as an explicit template sequence - drafted, shaped, checked, approved, issued - and a template completes only complete, complete being a state with evidence held - kind ref, shelf ref, keeper record, issue ref - never a feeling, a memory, an assertion or a summary; holding, viewing and reading a template runs no template live, approves nothing, spawns no process and opens no network'
PLAIN_EXPLANATION = 'Campaign templates (M-217): house shapes (feature build, bug hunt, migration, hardening, docs) as starting campaign files.'
USAGE = 'Usage: /shapes | /shapes template <template-id> | /shapes check <check> | /shapes kind <kind-id> | /shapes view <view-id> | /shapes note <note-id> | /shapes index | /shapes panel | /shapes verdict'

CHECKS = ("drafted", "shaped", "checked", "approved", "issued")
HELD_EVIDENCE = ("kind_ref", "shelf_ref", "keeper_record", "issue_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
CLAIM_KINDS = HELD_EVIDENCE + BARE_CLAIMS
TRANSITIONS = {
    "drafted": ("shaped",),
    "shaped": ("checked",),
    "checked": ("approved",),
    "approved": ("drafted", "issued"),
    "issued": (),
}


def legal_step(before: Any, after: Any) -> bool:
    """Whether the gate sequence allows one step, DERIVED.

    The machine stands as data in TRANSITIONS:
    inspect steps only to build, build only to
    test, test to repair on a failure or to
    continue on a pass, repair back to build or
    test for the rerun, and continue steps
    nowhere - it is where a template stands complete.
    A check outside the machine allows nothing.
    """
    return after in TRANSITIONS.get(before, ())


def next_check(check: Any, failed: Any = False) -> Optional[str]:
    """The step the shapekeeper takes next, DERIVED from the sequence.

    Banked leads to shaped and shaped to
    checked; checked leads to approved; at
    approved a follow-up banking steps back to drafted and a finished template steps to issued;
    issued is the end of the walk and steps
    nowhere. A step outside the sequence refuses
    by name.
    """
    approved = normalize_check(check)
    if approved == "drafted":
        return "shaped"
    if approved == "shaped":
        return "checked"
    if approved == "checked":
        return "approved"
    if approved == "approved":
        return "drafted" if failed else "issued"
    return None


_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_RUN_KEYS = frozenset({
    "template_id", "seq", "kind_id", "title", "checks",
    "claims", "detail",
} | set(_PROVENANCE))
_SLICE_REF_KEYS = frozenset({
    "kind_id", "seq", "title", "state", "detail",
} | set(_PROVENANCE))
_TRACE_KEYS = frozenset({
    "trace_id", "seq", "template_id", "trace", "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "template_id", "stance", "target", "title",
    "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "standing", "complete", "greens", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "entries", "coverage", "covered", "uncovered",
    "current_template", "next_template", "progress", "shelf",
    "current", "order", "breaks", "live"})
_LIVE_KEYS = (
    "live_template", "templates_live", "live_question",
    "templates_raise", "raises_slice", "raised_live",
    "answers_live", "answers_question", "answered_live",
    "delivers_live", "delivered_live", "resumes_live",
    "resumed_live", "pauses_template", "paused_live",
    "runs_template", "ran_template", "spawns_process",
    "spawned_process", "builds_slice", "built_slice",
    "builds_live", "executes_slice", "executed_slice",
    "executes_live", "live_execution",
    "banks_slice", "banked_live", "template_live",
    "pushes_slice", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_template", "sent_template",
    "posts_note", "posted_note", "traces_live",
    "traced_live", "writes_ledger", "wrote_ledger", "files_template", "filed_live", "spawns_shapekeeper", "spawned_shapekeeper", "sends_template", "sent_template", "writes_template", "wrote_template")


# ---------------------------------------------------------------------
# Small judges, in the sibling trace.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_checks(value: Any) -> Tuple[str, ...]:
    """A template's walked checks, held as data.

    The checks stand as a list of check names in
    walk order, each one a check of the explicit
    gate sequence; a walk not yet held stands
    honestly empty - no check is invented - and
    a name outside the machine refuses.
    """
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError("checks must be a list of gate sequence checks")
    return tuple(normalize_check(v) for v in value)

def _check_claims(value: Any) -> Tuple[str, ...]:
    """A template's asked claims: claim kinds named as data.

    Each claim names one kind from the issued
    vocabulary - the human kinds the gate may ask
    and the code kinds it must never ask, both
    held honestly as data - and a kind outside
    the vocabulary refuses.
    """
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError("claims must be a list of claim kinds")
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
                f"{what} claims a live gate template or slice build "
                f"execution ({key!r} is named on it): "
                f"{TEMPLATE_RULE}")
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


def normalize_kind_state(value: Any) -> str:
    state = _clean_text(value, "an slice state").lower()
    if state not in KIND_STATES:
        raise ValueError(
            f"slice state {state!r} is not one of the held "
            f"states: " + ", ".join(KIND_STATES))
    return state


def normalize_view_filter(value: Any) -> str:
    view_filter = _clean_text(value, "a view filter").lower()
    if view_filter not in VIEW_FILTERS:
        raise ValueError(
            f"view filter {view_filter!r} is not one of the held "
            f"filters: " + ", ".join(VIEW_FILTERS))
    return view_filter


def normalize_check(value: Any) -> str:
    check = _clean_text(value, "a check").lower()
    if check not in CHECKS:
        raise ValueError(
            f"check {check!r} is not one of the held "
            f"checks: " + ", ".join(CHECKS))
    return check


def normalize_claim_kind(value: Any) -> str:
    kind = _clean_text(value, "a claim kind").lower()
    if kind not in CLAIM_KINDS:
        raise ValueError(
            f"claim kind {kind!r} is not one of the held "
            f"kinds: " + ", ".join(CLAIM_KINDS))
    return kind

# ---------------------------------------------------------------------
# The held template: one slice cut from an active slice.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TemplateRecord:
    """One template slice, held as data.

    The template names the active slice it was
    held from, by slice id, its title, its
    verifiable checks, held as data, and its
    claims, named by template id. The grain is
    derived, never stored: exactly one verifiable
    walk is checked against the machine. A template whose
    checks are not yet held stands with its
    checks empty: it stands open, named in
    its gaps, and no check is invented for it.
    The template is local data alone - no live build
    stands behind it: holding it builds nothing.
    """

    template_id: str
    seq: int
    kind_id: str
    title: str
    checks: Tuple[str, ...] = ()
    claims: Tuple[str, ...] = ()
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "template_id", _clean_text(self.template_id, "a template id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "kind_id", _clean_text(self.kind_id, "an slice id"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a template title"))
        object.__setattr__(
            self, "checks", _check_checks(self.checks))
        object.__setattr__(
            self, "claims", _check_claims(self.claims))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a template detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.template_id

    @property
    def check(self) -> str:
        """The check the template stands at: its last walked check."""
        return self.checks[-1] if self.checks else ""

    def to_record(self) -> Dict[str, Any]:
        record = {
            "template_id": self.template_id, "seq": self.seq,
            "kind_id": self.kind_id, "title": self.title,
            "checks": list(self.checks),
            "claims": list(self.claims),
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_template_ref(value: Any) -> TemplateRecord:
    if not isinstance(value, TemplateRecord):
        raise ValueError("a template must be a TemplateRecord")
    return value


def validate_template(template: Any) -> TemplateRecord:
    return _check_template_ref(template)


def build_template(record: Any = None, **kwargs: Any) -> TemplateRecord:
    """Build one held template from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, TemplateRecord):
        if kwargs:
            raise ValueError("a template stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a template must be a mapping or a TemplateRecord")
    _needed(data, _RUN_KEYS, "a template")
    return TemplateRecord(
        template_id=data.get("template_id"), seq=data.get("seq"),
        kind_id=data.get("kind_id"), title=data.get("title"),
        checks=data.get("checks"),
        claims=data.get("claims"),
        detail=data.get("detail"),
        **_provenance(data))


def _breaks_map(book: Any) -> Dict[str, Tuple[str, ...]]:
    """Map each template to the steps it took outside the machine.

    Derived from the held templates alone: a break is
    one consecutive pair of walked checks the
    explicit gate sequence does not allow, told
    in walk order as before, then after.
    """
    found: Dict[str, Tuple[str, ...]] = {}
    for template in book.templates:
        breaks = tuple(
            f"{before} > {after}"
            for before, after in zip(template.checks, template.checks[1:])
            if not legal_step(before, after))
        if breaks:
            found[template.template_id] = breaks
    return found

def template_gaps(template: Any, source: Any = None) -> Tuple[str, ...]:
    """The gaps that keep a template from standing complete.

    Mapped from the template's own held fields alone -
    its walked steps against the explicit question
    sequence, and its carried evidence against the
    issued vocabulary: the template opens at
    named, steps only where the sequence
    allows, carries held evidence and no bare claim,
    and a template stands complete only when it has
    reached issued. The source names nothing
    further: no gap is borrowed from another
    template.
    """
    approved = _check_template_ref(template)
    gaps: List[str] = []
    if not approved.checks:
        gaps.append(
            "has passed through no step: the template has not started")
        return tuple(gaps)
    if approved.checks[0] != "drafted":
        gaps.append(
            f"opens at {approved.checks[0]}, not at drafted: "
            f"the template opens with the reflection")
    for before, after in zip(approved.checks, approved.checks[1:]):
        if not legal_step(before, after):
            gaps.append(
                f"steps from {before} to {after}, which the "
                f"template sequence does not allow")
    for kind in approved.claims:
        if kind in BARE_CLAIMS:
            gaps.append(
                f"carries a {kind} claim, a bare claim with no "
                f"held proof: complete stands on held proof alone")
    if approved.checks[-1] != "issued":
        gaps.append(
            f"has not reached issued: the template stands "
            f"at {approved.checks[-1]}")
    return tuple(gaps)

def template_green(template: Any, source: Any = None) -> bool:
    return not template_gaps(template, source)


def plain_lines(template: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the template's own fields."""
    approved = _check_template_ref(template)
    return (
        f"Template: {approved.title}",
        f"Kind: {approved.kind_id}",
        f"Check: {approved.check if approved.check else 'none'}",
        f"Claims: "
        f"{', '.join(approved.claims) if approved.claims else 'none'}",
    )


def segment_of(template: Any, source: Any = None) -> str:
    approved = _check_template_ref(template)
    gaps = template_gaps(approved, source)
    return (
        f"{approved.template_id}: {approved.title} - slice: "
        f"'{approved.kind_id}' - check: "
        f"'{approved.check if approved.check else 'none'}' - "
        f"checks: {len(approved.checks)} - claims: "
        f"'{', '.join(approved.claims) if approved.claims else 'none'}' - "
        f"detail: '{approved.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held slice reference: the active slice a book templates from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class KindRef:
    """One slice a template book templates from, held as a reference.

    The record names the slice, the title it
    opens and its standing - active or
    queued - held as data copied from the
    M-203 slice book's own telling. A template
    stands only from an active reference: the
    book refuses a template naming no held reference,
    and a template from an queued one, BY NAME.
    """

    kind_id: str
    seq: int
    title: str
    state: str
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "kind_id", _clean_text(self.kind_id, "an slice id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a title"))
        object.__setattr__(
            self, "state", normalize_kind_state(self.state))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an slice detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.kind_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "kind_id": self.kind_id, "seq": self.seq,
            "title": self.title, "state": self.state,
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_kind_ref(value: Any) -> KindRef:
    if not isinstance(value, KindRef):
        raise ValueError("a slice reference must be an KindRef")
    return value


def validate_kind_ref(ref: Any) -> KindRef:
    return _check_kind_ref(ref)


def build_kind_ref(record: Any = None, **kwargs: Any) -> KindRef:
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, KindRef):
        if kwargs:
            raise ValueError(
                "a slice reference stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError(
            "a slice reference must be a mapping or an KindRef")
    _needed(data, _SLICE_REF_KEYS, "a slice reference")
    return KindRef(
        kind_id=data.get("kind_id"), seq=data.get("seq"),
        title=data.get("title"), state=data.get("state"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held trace trace: the human approves the trace, as data.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TraceRecord:
    """One trace trace, held as data.

    The record names its slice and the trace the
    human active - the slice's template ids in
    derived claim order, held exactly as
    active. The trace is of the set and its
    order, never of a step: when the derived
    trace moves, this record stands stale, named
    in the shelf, until a new trace is active.
    """

    trace_id: str
    seq: int
    template_id: str
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
            self, "template_id", _clean_text(self.template_id, "an slice id"))
        object.__setattr__(
            self, "trace", _clean_text(self.trace, "an active trace"))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an trace detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.trace_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "trace_id": self.trace_id, "seq": self.seq,
            "template_id": self.template_id, "trace": self.trace,
            "detail": self.detail,
        }
        for key in _PROVENANCE:
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
        template_id=data.get("template_id"), trace=data.get("trace"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held stance: a note on a template, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One template stance, held as data.

    The record names its template, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per template stance
    in a book. The record is data alone: holding
    it builds nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    template_id: str
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
            self, "template_id", _clean_text(self.template_id, "a template id"))
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
            "template_id": self.template_id, "stance": self.stance,
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
        template_id=data.get("template_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held view: which slices a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TemplateView:
    """A view over the book: every template, the green, the rest."""

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


def _check_view_ref(value: Any) -> TemplateView:
    if not isinstance(value, TemplateView):
        raise ValueError("a view must be an TemplateView")
    return value


def validate_view(view: Any) -> TemplateView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> TemplateView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, TemplateView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an TemplateView")
    _needed(data, _VIEW_KEYS, "a view")
    return TemplateView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TemplatePanelRow:
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


def _row_for_template(template: TemplateRecord,
                     source: Any = None) -> TemplatePanelRow:
    return TemplatePanelRow(
        item_id=template.template_id,
        standing="complete" if template_green(template, source) else "open",
        label=template.title, segment=segment_of(template, source),
        recorded_on=template.recorded_on)


def _check_row_ref(value: Any) -> TemplatePanelRow:
    if not isinstance(value, TemplatePanelRow):
        raise ValueError("a panel row must be an TemplatePanelRow")
    return value


def validate_row(row: Any, template: Any = None,
                 source: Any = None) -> TemplatePanelRow:
    approved = _check_row_ref(row)
    if template is not None:
        derived = _row_for_template(_check_template_ref(template), source)
        if approved != derived:
            raise ValueError(
                f"panel row {approved.item_id!r} does not agree with "
                f"the row derived from its template")
    return approved


def build_row(row: Any = None, template: Any = None,
              source: Any = None,
              **kwargs: Any) -> TemplatePanelRow:
    if template is not None:
        derived = _row_for_template(_check_template_ref(template), source)
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            TemplatePanelRow(**kwargs))
        return validate_row(built, template, source)
    if isinstance(row, TemplatePanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in COMPLETE_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return TemplatePanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return TemplatePanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an TemplatePanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[TemplatePanelRow, ...]
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
        f"The template book holds {total_items} templates as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {green_shown} of the shown templates "
        f"stand complete.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its template's own fields "
        "- the slice it answers for, the steps it walked in the "
        "open and the evidence it honestly carries - and no "
        "judgement is stored on any template.",
        "Completeness is checked from the held records alone: "
        "a template that steps outside the template sequence, "
        "carries a bare claim in place of held evidence, or has "
        "not reached issued stands open, named in its "
        "gaps, and the template index is derived from the "
        "held templates, never stored where it could drift.",
    )

@dataclass(frozen=True)
class TemplatePanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[TemplatePanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> TemplateView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, TemplateView):
        return view
    return book.view_for(view)


def shown_templates(source: Any, view: Any = None
                   ) -> Tuple[TemplateRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.templates
    if resolved.view_filter == "complete":
        return tuple(g for g in book.templates if template_green(g, book))
    return tuple(g for g in book.templates if not template_green(g, book))


def templates_for_kind(source: Any, kind_id: Any
                      ) -> Tuple[TemplateRecord, ...]:
    wanted = _clean_text(kind_id, "an slice id")
    return tuple(
        g for g in _source_book(source).templates if g.kind_id == wanted)


def green_templates(source: Any) -> Tuple[TemplateRecord, ...]:
    book = _source_book(source)
    return tuple(g for g in book.templates if template_green(g, book))


def current_template(source: Any) -> Optional[TemplateRecord]:
    """The book's current template, DERIVED at call time.

    The first held template, in held order, that does
    not yet stand complete - where the Architect must
    look next. Nothing here is stored: the telling
    is derived from the held templates alone, so it can
    never go stale against them. A book whose every
    template stands complete has no current template.
    """
    book = _source_book(source)
    for template in book.templates:
        if not template_green(template, book):
            return template
    return None


def derive_panel(source: Any, view: Any = None) -> TemplatePanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_templates(book, resolved)
    rows = tuple(_row_for_template(template, book) for template in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.templates), default="")
    green = sum(1 for g in shown if template_green(g, book))
    return TemplatePanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.templates), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.templates), len(shown), green, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> TemplatePanel:
    if not isinstance(value, TemplatePanel):
        raise ValueError("a panel must be an TemplatePanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> TemplatePanel:
    """Judge a stored panel against the panel derived from its book.

    Every derived field must agree; the stored
    panel's own name is its identity, not derived
    content (the M-182 template).
    """
    approved = _check_panel_ref(panel)
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(approved.view_id)
                if approved.view_id is not None else None)
        derived = derive_panel(book, view)
        for attr in ("view_id", "view_filter", "rows", "total_items",
                     "total_shown", "target_counts", "as_of", "account"):
            if getattr(approved, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {approved.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return approved


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> TemplatePanel:
    if isinstance(panel, TemplatePanel):
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
        built = TemplatePanel(
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
    raise ValueError("a panel must be a mapping, an TemplatePanel, or derived")


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
        return "issued"
    if green_shown == 0:
        return "blocked"
    return "held"


@dataclass(frozen=True)
class TemplateVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> TemplateVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_templates(book, resolved)
    green = sum(1 for g in shown if template_green(g, book))
    latest = max((g.recorded_on for g in shown), default="")
    return TemplateVerdict(
        verdict=_verdict_word(len(shown), green),
        view_id=resolved.view_id, total_shown=len(shown),
        green_shown=green, latest_on=latest)


def _check_verdict_ref(value: Any) -> TemplateVerdict:
    if not isinstance(value, TemplateVerdict):
        raise ValueError("a verdict must be an TemplateVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> TemplateVerdict:
    approved = _check_verdict_ref(verdict)
    if approved.verdict not in VERDICT_WORDS:
        raise ValueError(f"verdict {approved.verdict!r} is not a held word")
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(approved.view_id)
                if approved.view_id is not None else None)
        derived = derive_verdict(book, view)
        if approved != derived:
            raise ValueError(
                "the stored verdict disagrees with the verdict "
                "derived from its book")
    return approved


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> TemplateVerdict:
    if isinstance(verdict, TemplateVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = TemplateVerdict(
            verdict=_clean_text(data.get("verdict"), "a verdict"),
            view_id=data.get("view_id"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            green_shown=_check_count(
                data.get("green_shown"), "a green_shown count"),
            latest_on=_clean_text(data.get("latest_on"), "a latest day"))
        return validate_verdict(built, source)
    if verdict is None and source is not None:
        return derive_verdict(source, kwargs.get("view"))
    raise ValueError(
        "a verdict must be a mapping, an TemplateVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held slices' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexEntry:
    check: str
    template_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "check": self.check, "template_id": self.template_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class TemplateIndex:
    """The template index, derived from the held templates.

    The index names one entry per green template, in
    held order - the template's own one verifiable
    check, its template id and its title - and the
    templates that do not stand complete, named in its
    gaps. Nothing here is stored on any template: the
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


def derive_index(source: Any) -> TemplateIndex:
    """Derive the template index from the book's held templates."""
    book = _source_book(source)
    entries = tuple(
        IndexEntry(check=g.check, template_id=g.template_id,
                   title=g.title)
        for g in book.templates if template_green(g, book))
    gaps = tuple(
        g.template_id for g in book.templates if not template_green(g, book))
    return TemplateIndex(entries=entries, gaps=gaps)


def template_for_check(source: Any, check: Any) -> Optional[TemplateRecord]:
    """The first held template one check reaches, or none - honestly."""
    if check is None:
        return None
    if not isinstance(check, str):
        raise ValueError("an check must be a string naming the check")
    wanted = check.strip()
    if not wanted:
        return None
    for template in _source_book(source).templates:
        if template.check == wanted:
            return template
    return None


def transition_breaks(source: Any) -> Tuple[str, ...]:
    """Every step outside the gate sequence, DERIVED.

    One telling per break, in held order: the template
    that took it and the step it took, before,
    then after. A book whose templates all walk inside
    the machine tells none.
    """
    book = _source_book(source)
    return tuple(
        f"{template_id}: {step}"
        for template_id, steps in _breaks_map(book).items()
        for step in steps)

def template_order(source: Any,
              kind_id: Any = None) -> Tuple[TemplateRecord, ...]:
    """The held templates in their held order, DERIVED at call time.

    Templates stand in the order the book holds them -
    the order their slices were taken - optionally
    for one slice alone. Nothing here is stored:
    the order is the book's own held order, told.
    """
    book = _source_book(source)
    templates = list(book.templates)
    if kind_id is not None:
        wanted = _clean_text(kind_id, "a slice id")
        templates = [r for r in templates if r.kind_id == wanted]
    return tuple(templates)

def trace_of(source: Any, template_id: Any) -> str:
    """One template's trace, DERIVED at call time.

    The template's walked checks joined as one trace
    line, in walk order. A template that has walked
    nowhere traces empty: the trace tells only
    what stands walked, and the walk is named
    elsewhere.
    """
    template = _source_book(source).template_for(template_id)
    return " > ".join(template.checks)

def trace_for_template(source: Any,
                  template_id: Any) -> Optional[TraceRecord]:
    """The held trace for one template, or none - honestly."""
    wanted = _clean_text(template_id, "a template id")
    for record in _source_book(source).traces:
        if record.template_id == wanted:
            return record
    return None

def trace_current(source: Any, template_id: Any) -> bool:
    """Whether the held trace agrees with the derived trace.

    The trace stands current only while the trace
    it holds is the trace the book derives now; a
    moved walk leaves it stale, and no trace at
    all traces nothing.
    """
    trace = trace_for_template(source, template_id)
    if trace is None:
        return False
    return trace.trace == trace_of(source, template_id)

def note_for_template(source: Any, template_id: Any,
                   stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one template (and stance, when named)."""
    wanted = _clean_text(template_id, "a template id")
    for record in _source_book(source).notes:
        if record.template_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the slice targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


def shelf_record(source: Any = None) -> Dict[str, Any]:
    """The template shelf, DERIVED here from the held templates alone.

    The shelf counts the held templates by their
    derived completeness - green and red - names
    the current template, the first that does not yet
    stand complete, tells each held template's trace
    standing - current while its held trace
    agrees with its derived trace, stale when it
    has moved, unheld while no trace stands for
    it - and names every step the held templates took
    outside the gate sequence. Nothing here is
    stored: the telling is derived at call time.
    """
    book = _source_book(source)
    standings = []
    for standing in COMPLETE_WORDS:
        number = sum(
            1 for g in book.templates
            if ("complete" if template_green(g, book) else "open") == standing)
        standings.append({"standing": standing, "template_records": number})
    current = current_template(book)
    traces = []
    for template in book.templates:
        trace = trace_for_template(book, template.template_id)
        if trace is None:
            standing = "unheld"
        elif trace_current(book, template.template_id):
            standing = "current"
        else:
            standing = "stale"
        traces.append({"template_id": template.template_id, "trace": standing})
    return {
        "type": "template_shelf",
        "slice": TEMPLATE_SLICE,
        "standings": standings,
        "total": len(book.templates),
        "current_template": current.template_id if current is not None else None,
        "traces": traces,
        "breaks": list(transition_breaks(book)),
    }

def roadmap_record() -> Dict[str, Any]:
    """This slice's own roadmap standing, proved from the roadmap itself.

    The record loads this kind's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 slices in 11 parts,
    the drafted prefix, the next slice where the
    template resumes, and M-217's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(TEMPLATE_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "template_roadmap",
        "slice": TEMPLATE_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m217_title": own.title,
        "m217_part": own.part,
        "m217_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: slices, templates, views, notes and trace traces held
# together, one pinned panel at most per telling, and no verdict,
# index, trace or order ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TemplateBook:
    title: str
    slices: Tuple[KindRef, ...] = ()
    templates: Tuple[TemplateRecord, ...] = ()
    views: Tuple[TemplateView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    traces: Tuple[TraceRecord, ...] = ()
    panels: Tuple[TemplatePanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        slices = tuple(_check_kind_ref(g) for g in self.slices)
        templates = tuple(_check_template_ref(g) for g in self.templates)
        views = tuple(_check_view_ref(v) for v in self.views)
        notes = tuple(_check_note_ref(m) for m in self.notes)
        traces = tuple(_check_trace_ref(a) for a in self.traces)
        panels = tuple(_check_panel_ref(pn) for pn in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for ref in slices:
            if ref.kind_id in seen_ids:
                raise ValueError(
                    f"two slice references stand under id {ref.kind_id!r}")
            if ref.seq in seen_seqs:
                raise ValueError(
                    f"two slice references stand at sequence {ref.seq}")
            seen_ids.add(ref.kind_id)
            seen_seqs.add(ref.seq)
        template_ids = set()
        template_seqs = set()
        for template in templates:
            if template.template_id in template_ids:
                raise ValueError(
                    f"two templates stand under id {template.template_id!r}")
            if template.seq in template_seqs:
                raise ValueError(
                    f"two templates stand at sequence {template.seq}")
            template_ids.add(template.template_id)
            template_seqs.add(template.seq)
        by_slice = {ref.kind_id: ref for ref in slices}
        for template in (templates if slices else ()):

            ref = by_slice.get(template.kind_id)
            if ref is None:
                raise ValueError(
                    f"template {template.template_id!r} is held from slice "
                    f"{template.kind_id!r}, which stands nowhere in "
                    f"this book")
            if ref.state != "live":
                raise ValueError(
                    f"template {template.template_id!r} is held from slice "
                    f"{template.kind_id!r}, which is not active: "
                    f"no slice is held from an queued slice")
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
            target = (record.template_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for template "
                    f"{record.template_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per template target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        trace_ids = set()
        trace_seqs = set()
        trace_templates = set()
        template_ids = {template.template_id for template in templates}
        for record in traces:
            if record.trace_id in trace_ids:
                raise ValueError(
                    f"two traces stand under id {record.trace_id!r}")
            if record.seq in trace_seqs:
                raise ValueError(
                    f"two traces stand at sequence {record.seq}")
            if record.template_id in trace_templates:
                raise ValueError(
                    f"two traces stand for template "
                    f"{record.template_id!r}: one trace stands "
                    f"per template walk")
            if templates and record.template_id not in template_ids:
                raise ValueError(
                    f"trace {record.trace_id!r} traces template "
                    f"{record.template_id!r}, which stands nowhere in "
                    f"this book")
            trace_ids.add(record.trace_id)
            trace_seqs.add(record.seq)
            trace_templates.add(record.template_id)
        object.__setattr__(
            self, "kinds", tuple(sorted(slices, key=lambda g: g.seq)))
        object.__setattr__(
            self, "template_records", tuple(sorted(templates, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(
            self, "traces",
            tuple(sorted(traces, key=lambda a: a.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.templates + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.template_id for g in self.templates) + tuple(
            v.view_id for v in self.views)

    def template_ids(self) -> Tuple[str, ...]:
        return tuple(g.template_id for g in self.templates)

    def kind_ids(self) -> Tuple[str, ...]:
        return tuple(g.kind_id for g in self.slices)

    def template_for(self, template_id: Any) -> TemplateRecord:
        wanted = _clean_text(template_id, "a template id")
        for template in self.templates:
            if template.template_id == wanted:
                return template
        raise KeyError(f"no template named {wanted!r} stands in this book")

    def slice_for(self, kind_id: Any) -> KindRef:
        wanted = _clean_text(kind_id, "an slice id")
        for ref in self.slices:
            if ref.kind_id == wanted:
                return ref
        raise KeyError(f"no slice named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> TemplateView:
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

    def trace_for(self, trace_id: Any) -> TraceRecord:
        wanted = _clean_text(trace_id, "an trace id")
        for record in self.traces:
            if record.trace_id == wanted:
                return record
        raise KeyError(f"no trace named {wanted!r} stands in this book")

    def item_for(self, item_id: Any) -> Any:
        wanted = _clean_text(item_id, "an item id")
        for template in self.templates:
            if template.template_id == wanted:
                return template
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "kinds": [g.to_record() for g in self.slices],
            "template_records": [g.to_record() for g in self.templates],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "traces": [a.to_record() for a in self.traces],
            "panels": [pn.to_record() for pn in self.panels],
        }


def _judge_book_panels(book: TemplateBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: TemplateBook) -> None:
    if book.title != "Campaign templates at the M-217 slice boundary":
        raise ValueError("the shipped example book carries another title")
    if len(book.slices) != 3 or len(book.templates) != 5 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold three slice references, five templates and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.traces) != 1:
        raise ValueError("the shipped example book must hold one trace record")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m216-boundary":
        raise ValueError("the pinned panel is panel-m216-boundary")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "held" or verdict.green_shown != 3:
        raise ValueError("the shipped example book verdict must stand held at three complete of five")
    index = derive_index(book)
    if [e.check for e in index.entries] != ["issued", "issued", "issued"]:
        raise ValueError("the shipped example book index must derive the three held complete templates in held order")
    if index.gaps != ("template-bare-template", "template-leaping-template"):
        raise ValueError("the shipped example book must leave the bare and leaping templates honestly open, named in its gaps")
    found = template_for_check(book, EXAMPLE_CHECK)
    if found is None or found.template_id != "template-held-template":
        raise ValueError("the shipped example book must reach its opening template under the example check")
    if trace_of(book, "template-held-template") != "drafted > shaped > checked > approved > issued":
        raise ValueError("the shipped example book must derive the opening template's trace from its walked steps")
    if not trace_current(book, "template-held-template"):
        raise ValueError("the shipped example book must hold the opening template's trace current")
    first = first_note(book)
    if first is None or first.note_id != "note-note-first":
        raise ValueError("the shipped example book must hold the opening note as its first note road")

def validate_book(data: Any, *, require_example: bool = False) -> TemplateBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, TemplateBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a template book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live slice build or execution "
                f"({key!r} is named on it): {TEMPLATE_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its templates under a view")
    if "template_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held templates at call time")
    if "shelf" in data or "current_template" in data:
        raise ValueError(
            "a book stores no shelf and no current template: both are "
            "derived from its held templates at call time")
    if "trace" in data or "order" in data:
        raise ValueError(
            "a book stores no trace and no order: both are derived "
            "from its held templates at call time; an trace record "
            "holds the trace the human active")
    if data.get("schema") is not None and (
            data["schema"] != TEMPLATE_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{TEMPLATE_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != TEMPLATE_SLICE):
        raise ValueError(
            f"a book's slice must be {TEMPLATE_SLICE!r}")
    head = data.get("template_head") or data.get("campaign_templates") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's template head must be a mapping")
    title = head.get("title") or data.get("title")
    slices = tuple(build_kind_ref(g) for g in data.get("kinds") or ())
    templates = tuple(build_template(g) for g in data.get("template_records") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    traces = tuple(build_trace(a) for a in data.get("traces") or ())
    book = TemplateBook(
        title=title, slices=slices, templates=templates, views=views,
        notes=notes, traces=traces, panels=())
    panels = tuple(
        build_panel(pn, book) for pn in data.get("panels") or ())
    book = TemplateBook(
        title=book.title, slices=book.slices, templates=book.templates,
        views=book.views, notes=book.notes,
        traces=book.traces, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> TemplateBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (TemplateBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an TemplateBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> TemplateBook:
    return validate_book(data, require_example=require_example)


def load_template(
        data: Optional[Dict[str, Any]] = None) -> TemplateBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(TEMPLATE_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_template_file(path: Any) -> TemplateBook:
    """Load one template file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: slice references, templates and views held one by one.
# ---------------------------------------------------------------------

class TemplateRegistry:
    """An in-memory holding of slice references, templates and views.

    The registry is the pure layer's model of a
    session's template book: slice references are
    held under their ids, templates are held under
    their ids, one template per id and per sequence,
    and views are held in shaped order, one view
    per sequence and per id. Holding is data only -
    nothing held here builds anything, executes
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._slices: List[KindRef] = []
        self._templates: List[TemplateRecord] = []
        self._views: List[TemplateView] = []
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

    def register_kind_ref(self, item: Any) -> KindRef:
        """Hold one slice reference, checked whole before held."""
        approved = _check_kind_ref(item)
        return self._register(
            self._slices, approved, "kind_id", "slice reference")

    def register_template(self, item: Any) -> TemplateRecord:
        """Hold one template, checked whole before held."""
        approved = _check_template_ref(item)
        return self._register(
            self._templates, approved, "template_id", "template")

    def register_view(self, view: Any) -> TemplateView:
        """Hold one view; a view naming no id takes a fresh one."""
        approved = _check_view_ref(view)
        if not approved.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            approved = build_view({**approved.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, approved, "view_id", "view")

    def register_book(self, book: Any) -> TemplateBook:
        """Hold a whole book's records, under its title."""
        approved = build_book(book)
        if self._title is not None and approved.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {approved.title!r}")
        for ref in approved.slices:
            self.register_kind_ref(ref)
        for template in approved.templates:
            self.register_template(template)
        for view in approved.views:
            self.register_view(view)
        self._title = approved.title
        return self.book()

    def book(self) -> TemplateBook:
        return TemplateBook(
            title=self._title or "An unheld template book",
            slices=tuple(self._slices), templates=tuple(self._templates),
            views=tuple(self._views), notes=(), traces=(), panels=())

    def list_slices(self) -> Tuple[KindRef, ...]:
        return tuple(self._slices)

    def list_templates(self) -> Tuple[TemplateRecord, ...]:
        return tuple(self._templates)

    def list_views(self) -> Tuple[TemplateView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._templates) + tuple(self._views)

    def get_slice(self, kind_id: Any) -> KindRef:
        return self.book().slice_for(kind_id)

    def get_template(self, template_id: Any) -> TemplateRecord:
        return self.book().template_for(template_id)

    def get_view(self, view_id: Any) -> TemplateView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records traced for the journal target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> TemplateBook:
    if source is None:
        return load_template()
    if isinstance(source, TemplateBook):
        return source
    if isinstance(source, TemplateRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def template_record(template: Any, source: Any = None) -> Dict[str, Any]:
    approved = _check_template_ref(template)
    book = _source_book(source) if source is not None else None
    record = {
        "type": "template_template",
        "slice": TEMPLATE_SLICE,
        "template_id": approved.template_id,
        "kind_id": approved.kind_id,
        "title": approved.title,
        "segment": segment_of(approved, book),
        "complete": template_green(approved, book),
        "gaps": list(template_gaps(approved, book)),
    }
    record.update(_provenance_record(approved))
    return record


def kind_record(ref: Any) -> Dict[str, Any]:
    approved = _check_kind_ref(ref)
    record = {
        "type": "template_slice",
        "slice": TEMPLATE_SLICE,
        "kind_id": approved.kind_id,
        "title": approved.title,
        "state": approved.state,
    }
    record.update(_provenance_record(approved))
    return record


def trace_record(record_in: Any) -> Dict[str, Any]:
    approved = _check_trace_ref(record_in)
    record = {
        "type": "template_trace",
        "slice": TEMPLATE_SLICE,
        "trace_id": approved.trace_id,
        "template_id": approved.template_id,
        "trace": approved.trace,
    }
    record.update(_provenance_record(approved))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    approved = _check_view_ref(view)
    record = {
        "type": "template_view",
        "slice": TEMPLATE_SLICE,
        "view_id": approved.view_id, "seq": approved.seq,
        "view_filter": approved.view_filter,
    }
    record.update(_provenance_record(approved))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    approved = _check_note_ref(record_in)
    record = {
        "type": "template_note",
        "slice": TEMPLATE_SLICE,
        "note_id": approved.note_id,
        "template_id": approved.template_id,
        "stance": approved.stance,
    }
    record.update(_provenance_record(approved))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    approved = validate_panel(panel, source)
    record = {"type": "template_panel",
              "slice": TEMPLATE_SLICE}
    record.update(approved.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, TemplateVerdict):
        approved = validate_verdict(verdict, source)
    else:
        approved = derive_verdict(_source_book(verdict), view)
    record = {"type": "template_verdict",
              "slice": TEMPLATE_SLICE}
    record.update(approved.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, TemplateIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "template_index",
              "slice": TEMPLATE_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    approved = _source_book(book)
    record = {"type": "template_book",
              "slice": TEMPLATE_SLICE,
              "title": approved.title}
    record.update(approved.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(template: Any, source: Any = None) -> str:
    approved = _check_template_ref(template)
    return (
        f"{approved.title} - from {approved.kind_id}: "
        f"check {approved.check if approved.check else 'none'}, "
        f"claims "
        f"{', '.join(approved.claims) if approved.claims else 'none'}. "
        f"{approved.detail}")


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The templates stand {verdict.verdict}: "
        f"{verdict.green_shown} of {verdict.total_shown} shown "
        f"templates stand complete.")


def view_plain_words(view: Any) -> str:
    approved = _check_view_ref(view)
    return f"View {approved.view_id}: shows {approved.view_filter} templates."


def note_plain_words(record_in: Any) -> str:
    approved = _check_note_ref(record_in)
    return (
        f"Note {approved.note_id}: {approved.stance} "
        f"{approved.template_id}, toward {approved.target}. "
        f"{approved.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, TemplateIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.entries)} green templates; "
        f"red, named in its gaps: {gaps}.")

def format_template(template: Any, source: Any = None) -> str:
    approved = _check_template_ref(template)
    book = _source_book(source) if source is not None else None
    lines = [f"{approved.title} ({approved.template_id})"]
    lines.extend(plain_lines(approved))
    lines.append(approved.detail)
    if template_green(approved, book):
        lines.append(
            "This template stands complete - it walked the question "
            "sequence in the open from drafted to issued, "
            "and it carries held evidence alone.")
    else:
        lines.append(
            "This template stands open - it stands named in "
            f"its gaps: {', '.join(template_gaps(approved, book))}, and "
            "nothing is invented for it.")
    return "\n".join(lines)

def format_view(view: Any) -> str:
    approved = _check_view_ref(view)
    return (
        f"View {approved.view_id}: filter {approved.view_filter} - "
        f"{approved.detail}")


def format_note(record_in: Any) -> str:
    approved = _check_note_ref(record_in)
    lines = [
        f"Template note {approved.stance} {approved.template_id} "
        f"({approved.note_id}): {approved.title}. {approved.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or reading it builds nothing, executes nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_check(source: Any, check: Any) -> str:
    template = template_for_check(source, check)
    if template is not None:
        return format_template(template, source)
    wanted = check.strip() if isinstance(check, str) else check
    return (
        f"No held template stands under check {wanted!r} yet - the "
        f"check reaches nothing in this book, and no template is "
        f"invented for it.")


def format_book(source: Any = None, kind_id: Any = None) -> str:
    book = _source_book(source)
    templates = (templates_for_kind(book, kind_id)
              if kind_id is not None else book.templates)
    lines = [f"The Template Gate (M-217) - {book.title}"]
    lines.extend(segment_of(template, book) for template in templates)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Template panel under view {panel.view_id}:"]
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
    lines = ["Template index, derived from the held templates:"]
    for entry in index.entries:
        lines.append(f"{entry.check} - {entry.title} ({entry.template_id})")
    if index.gaps:
        lines.append(
            "Red, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "builds nothing, executes nothing and opens no network.")
    return "\n".join(lines)


def format_template_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "The Template Gate (M-217)",
        f"{book.title}: {len(book.templates)} templates held, "
        f"{len(green_templates(book))} templates standing green, "
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


def parse_template_args(args: Any) -> Tuple[str, Any]:
    """Parse the /template grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("template", "view", "note"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("check", "kind"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("index", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
