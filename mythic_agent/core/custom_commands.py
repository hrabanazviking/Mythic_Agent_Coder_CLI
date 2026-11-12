"""Cross-app method (roadmap slice M-237).

Part X - Bridges. The roadmap
words: **user/project slash commands as small files (prompt templates with arguments) joining the M-176 palace.******

What already ships, and what this command adds:

* Mythic's bridge faces already ship (M-233 consuming, M-234 serving, M-235 the registry, M-236 the skills standard, ``mythic_agent/core/skills_standard.py`` the nearest kin) and the M-176 slash-command palace already stands, holding every shipped command with plain-language descriptions and examples. This slice builds the custom commands that join that palace: user and project slash commands held as small files - prompt templates with arguments - each template held as data naming its command, its file origin (with the user, with a project, or not yet filed), and its template text, declared arguments and example held by reference from its manifest BEFORE any join is granted, with nothing executed and no template expanded live. The templates book WIRES that commands face as data, in its own module, standing in the M-195 copy-and-share
  book book the M-237 book stands in: one tracker
  per book, and the tracker's charge over one
  template across its command held as a book - a
  template. The shipped templates stand untouched behind
  their seams: this layer holds templates as data
  over the book's commands and rewrites none of them,
  and the templates book keeps its own standing.
  Templates stand on the ledger AS DATA alone: a
  template carries a ledger ref, a reference held in
  this book; holding, viewing or telling a template
  commands no template live, moves no keeper and files
  nothing.
* No charter row names this command: the M-171 TUI
  redesign charter binds Part VIII alone (M-172
  to M-200) and names M-237 on no row, and the
  command tests pin that absence live. The M-005
  method charter names no command row either: its
  own words name the whole of Part IX (M-201
  to M-232) as the part that executes the
  charter; Part X stands on the roadmap's own
  words, and this slice is built to those words.

* A template is held whole: the command it
  answers for, drafted by its command id; its title;
  the template steps it walked, held as data in
  walk template; and the evidence it carries, held
  as data by command. The template walk is EXPLICIT:
  its sequence stands as data
  (:data:`STAGES`, :data:`TRANSITIONS`) -
  drafted, checked, filed, joined, held -
  and a template's standing is DERIVED at
  call time from its held steps and evidence
  alone: a template that opens anywhere but
  drafted, steps where the sequence does not
  allow, carries a bare claim in place of held
  evidence, or has not yet drafted held stands
  open, drafted in its gaps.
* The evidence is a closed vocabulary in two
  halves: the held evidence - template_ref,
  arguments_ref, example_ref, manifest_ref, origin_ref, evidence
  a tracker can point to - and the bare claims -
  feeling, memory, assertion, summary, which
  stand as no evidence at all. A template is
  joined from held evidence alone, never
  from a feeling: a template holding a
  bare claim stands open, drafted in its gaps.
* A template stands only for an ACTIVE
  command. The book holds each command it answers
  for as a reference record - its id, its title
  and its standing, active or queued, held as
  data copied from the roadmap's own telling. A
  template naming a command that stands
  nowhere in the book refuses BY NAME, and a
  template for a command that is not active
  refuses BY NAME beside it: the tracker deals with
  the command in hand, in roadmap template, never a
  queued one, and a command whose template already
  stands complete is never filed twice - the
  current template is derived, so a
  completed command is never the current template
  twice.
* The template's trace is visible. A trace
  record holds one template's walked steps
  as one trace line, exactly as walked, beside
  the template. The derived trace is
  computed at call time from the template's
  held steps; a held trace that no longer agrees
  with it stands stale, drafted in the ledger - the
  trace is the walk itself, never a retelling
  of it.
* The template index is DERIVED at call
  time from the held templates - one template
  per complete template, under the step it
  stands at - never a second stored copy that
  could drift. A stored index, standing verdict,
  panel, trace, template or current-template
  claim on any record refuses by name.
* The current template is DERIVED at call
  time - the first held template, in held
  template, that does not yet stand complete - never
  stored where it could go stale.
* The notes are held as data: a note record
  naming its template, its stance - note,
  concern, praise, question, a closed
  vocabulary - and what it feeds back toward,
  one record per template stance; holding
  a note posts none of it, the rule stands as
  data (:data:`TEMPLATE_RULE`), and a record
  claiming a template was actually held,
  captured or promoted live refuses BY NAME.
  The tracker templates - and those templates, too,
  are held as data here, never sent.
* The shipped data file holds one example book
  in exactly the book a real template
  file takes, a loader reads a file anywhere on
  disk, templates and views are checked as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding a template book for a session and
  telling from it. This layer reaches no live
  template: it writes no template live, files nothing
  to the ledger, captures no candidate, promotes
  nothing, spawns no tracker, destroys nothing,
  publishes nothing, sends nothing as the user,
  exposes no secret, weakens no security and
  opens no network - it holds templates
  as data and tells them.

Honesty rules, enforced here and pinned by tests:

* **The template walk is explicit.** A
  template is joined against the held
  steps and legal steps alone; an illegal step
  stands drafted in its gaps, never silently
  reordered.
* **Complete stands on held evidence alone.** A
  template that carries a feeling, a
  memory, an assertion or a summary in place of
  held evidence stands open, drafted in its gaps:
  a template is joined from evidence, not
  vibes.
* **Active commands only, in roadmap template.** A
  template for a missing or queued command
  refuses by name; no template is invented
  for a command the tracker has not checked with.
* **Unknown stays unknown.** A template
  whose steps are not yet held stands with its
  steps empty - no step is invented.
* **The index, panel, verdict, trace, template
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
    "STAGE_FIELDS",
    "STAGES",
    "CLAIM_KINDS",
    "HELD_EVIDENCE",
    "BARE_CLAIMS",
    "TRANSITIONS",
    "EXAMPLE_STAGE",
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
    "COMMAND_STATES",
    "FILE_ORIGINS",
    "Any",
    "Dict",
    "List",
    "Optional",
    "TraceRecord",
    "TemplateRecord",
    "IndexTemplate",
    "CommandRef",
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
    "ledger_record",
    "book_record",
    "build_trace",
    "build_book",
    "build_template",
    "build_command_ref",
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
    "template_template",
    "template_record",
    "first_note",
    "format_book",
    "format_template",
    "format_index",
    "format_note",
    "format_stage",
    "format_panel",
    "format_template_screen",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "command_record",
    "load_template",
    "load_template_file",
    "normalize_command_state",
    "normalize_origin",
    "normalize_stage",
    "normalize_claim_kind",
    "legal_step",
    "next_stage",
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
    "validate_command_ref",
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
    "templates_for_command",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

TEMPLATE_SCHEMA = "mythic.custom_commands/1"
TEMPLATE_SLICE = "M-237"
THE_TEMPLATE_SLICE = TEMPLATE_SLICE
TEMPLATE_RESOURCE = "custom_commands.yaml"
INDEX_ACTION = "index"
EXAMPLE_STAGE = "held"
STAGE_FIELDS = ("stages", "claims")
COMPLETE_WORDS = ("complete", "open")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "complete", "open")
VERDICT_WORDS = ("held", "held", "blocked")
COMMAND_STATES = ("live", "dormant")
FILE_ORIGINS = ("project", "user", "unfiled")
TEMPLATE_RULE = "templates are held as data alone: user/project slash commands as small files (prompt templates with arguments) joining the M-176 palace (the file origins user, project and unfiled, one origin held per command as data) - one palace shelf per book, and the shelf charge over one template held as a template - a template stands as data, held by reference (a manifest ref), never expanded live - the template walk stands as an explicit template sequence - drafted, checked, filed, joined, held - and a template completes only complete, complete being a state with evidence held - template ref, arguments ref, example ref, manifest ref, origin ref - never a feeling, a memory, an assertion or a summary; user/project slash commands as small files (prompt templates with arguments) joining the M-176 palace - and a template joined without filing, or held before it is joined, stands open, named in its gaps; a template on an unfiled command stands complete only with its file origin held as an origin_ref; defining, reading, listing and telling a template executes nothing, expands no template live, spawns no process, opens no network and writes nothing outside held records"
PLAIN_EXPLANATION = "Custom commands (M-237): user/project slash commands as small files (prompt templates with arguments) joining the M-176 palace."
USAGE = 'Usage: /customcommands | /customcommands template <template-id> | /customcommands stage <stage> | /customcommands command <command-id> | /customcommands view <view-id> | /customcommands note <note-id> | /customcommands index | /customcommands panel | /customcommands verdict'

STAGES = ("drafted", "checked", "filed", "joined", "held")
HELD_EVIDENCE = ("template_ref", "arguments_ref", "example_ref", "manifest_ref", "origin_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
CLAIM_KINDS = HELD_EVIDENCE + BARE_CLAIMS
TRANSITIONS = {
    "drafted": ("checked",),
    "checked": ("filed",),
    "filed": ("joined",),
    "joined": ("drafted", "held"),
    "held": (),
}


def legal_step(before: Any, after: Any) -> bool:
    """Whether the gate sequence allows one step, DERIVED.

    The machine stands as data in TRANSITIONS:
    inspect steps only to build, build only to
    test, test to repair on a template or to
    continue on a pass, repair back to build or
    test for the rerun, and continue steps
    nowhere - it is where a template stands complete.
    A stage outside the machine allows nothing.
    """
    return after in TRANSITIONS.get(before, ())


def next_stage(stage: Any, failed: Any = False) -> Optional[str]:
    """The step the tracker takes next, DERIVED from the sequence.

    Banked leads to checked and checked to
    filed; filed leads to joined; at
    joined a follow-up banking steps back to drafted and a finished template steps to held;
    held is the end of the walk and steps
    nowhere. A step outside the sequence refuses
    by name.
    """
    joined = normalize_stage(stage)
    if joined == "drafted":
        return "checked"
    if joined == "checked":
        return "filed"
    if joined == "filed":
        return "joined"
    if joined == "joined":
        return "drafted" if failed else "held"
    return None


_HELDANCE = ("recorded_on", "actor", "source", "origin_session")
_RUN_KEYS = frozenset({
    "template_id", "seq", "command_id", "title", "stages",
    "claims", "detail",
} | set(_HELDANCE))
_SLICE_REF_KEYS = frozenset({
    "command_id", "seq", "title", "state", "origin", "detail",
} | set(_HELDANCE))
_TRACE_KEYS = frozenset({
    "trace_id", "seq", "template_id", "trace", "detail",
} | set(_HELDANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_HELDANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "template_id", "stance", "target", "title",
    "detail",
} | set(_HELDANCE))
_DERIVED_KEYS = frozenset({
    "standing", "complete", "greens", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "templates", "coverage", "covered", "uncovered",
    "current_template", "next_template", "progress", "ledger",
    "current", "template", "breaks", "live"})
_LIVE_KEYS = (
    "live_template", "templates_live", "live_question",
    "templates_raise", "raises_slice", "raised_live",
    "answers_live", "answers_question", "answered_live",
    "delivers_live", "delivered_live", "templates_live",
    "resumed_live", "runs_template", "paused_live",
    "runs_template", "ran_template", "spawns_process",
    "spawned_process", "builds_slice", "built_slice",
    "builds_live", "executes_slice", "executed_slice",
    "executes_live", "live_execution",
    "banks_slice", "banked_live", "template_live",
    "pushes_slice", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_template", "sent_template",
    "posts_note", "held_note", "traces_live",
    "traced_live", "writes_ledger", "wrote_ledger", "files_template", "filed_live", "spawns_tracker", "spawned_tracker", "sends_template", "sent_template", "writes_template", "wrote_template")


# ---------------------------------------------------------------------
# Small judges, in the sibling trace.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_stages(value: Any) -> Tuple[str, ...]:
    """A template's walked stages, held as data.

    The stages stand as a list of stage names in
    walk template, each one a stage of the explicit
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
    """A template's asked claims: claim commands drafted as data.

    Each claim names one command from the held
    vocabulary - the human commands the gate may ask
    and the code commands it must never ask, both
    held honestly as data - and a command outside
    the vocabulary refuses.
    """
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError("claims must be a list of claim commands")
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
            out[key] = _clean_text(mapping.get(key), "a recorded_on command")
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
                f"{what} claims a live gate template or command build "
                f"execution ({key!r} is drafted on it): "
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


def normalize_command_state(value: Any) -> str:
    state = _clean_text(value, "an command state").lower()
    if state not in COMMAND_STATES:
        raise ValueError(
            f"command state {state!r} is not one of the held "
            f"states: " + ", ".join(COMMAND_STATES))
    return state


def normalize_origin(value: Any) -> str:
    origin = _clean_text(value, "a file origin").lower()
    if origin not in FILE_ORIGINS:
        raise ValueError(
            f"file origin {origin!r} is not one of the "
            f"custom command file origins: " + ", ".join(FILE_ORIGINS))
    return origin


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
    command = _clean_text(value, "a claim command").lower()
    if command not in CLAIM_KINDS:
        raise ValueError(
            f"claim command {command!r} is not one of the held "
            f"commands: " + ", ".join(CLAIM_KINDS))
    return command

# ---------------------------------------------------------------------
# The held template: one command cut from an active command.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TemplateRecord:
    """One template command, held as data.

    The template names the active command it was
    held from, by command id, its title, its
    verifiable stages, held as data, and its
    claims, drafted by template id. The grain is
    derived, never stored: exactly one verifiable
    walk is filed against the machine. A template whose
    stages are not yet held stands with its
    stages empty: it stands open, drafted in
    its gaps, and no stage is invented for it.
    The template is local data alone - no live build
    stands behind it: holding it builds nothing.
    """

    template_id: str
    seq: int
    command_id: str
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
            self, "template_id", _clean_text(self.template_id, "a template id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "command_id", _clean_text(self.command_id, "an command id"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a template title"))
        object.__setattr__(
            self, "stages", _check_stages(self.stages))
        object.__setattr__(
            self, "claims", _check_claims(self.claims))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a template detail"))
        for key in _HELDANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.template_id

    @property
    def stage(self) -> str:
        """The stage the template stands at: its last walked stage."""
        return self.stages[-1] if self.stages else ""

    def to_record(self) -> Dict[str, Any]:
        record = {
            "template_id": self.template_id, "seq": self.seq,
            "command_id": self.command_id, "title": self.title,
            "stages": list(self.stages),
            "claims": list(self.claims),
            "detail": self.detail,
        }
        for key in _HELDANCE:
            record[key] = getattr(self, key)
        return record


def _check_origin_ref(value: Any) -> TemplateRecord:
    if not isinstance(value, TemplateRecord):
        raise ValueError("a template must be a TemplateRecord")
    return value


def validate_template(template: Any) -> TemplateRecord:
    return _check_origin_ref(template)


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
        command_id=data.get("command_id"), title=data.get("title"),
        stages=data.get("stages"),
        claims=data.get("claims"),
        detail=data.get("detail"),
        **_heldance(data))


def _breaks_map(book: Any) -> Dict[str, Tuple[str, ...]]:
    """Map each template to the steps it took outside the machine.

    Derived from the held templates alone: a break is
    one consecutive pair of walked stages the
    explicit gate sequence does not allow, told
    in walk template as before, then after.
    """
    drafted: Dict[str, Tuple[str, ...]] = {}
    for template in book.templates:
        breaks = tuple(
            f"{before} > {after}"
            for before, after in zip(template.stages, template.stages[1:])
            if not legal_step(before, after))
        if breaks:
            drafted[template.template_id] = breaks
    return drafted

def template_gaps(template: Any, source: Any = None) -> Tuple[str, ...]:
    """The gaps that keep a template from standing complete.

    Guarded from the template's own held fields alone -
    its walked steps against the explicit question
    sequence, and its held evidence against the
    held vocabulary: the template opens at
    drafted, steps only where the sequence
    allows, carries held evidence and no bare claim,
    and a template stands complete only when it has
    drafted held. The source names nothing
    further: no gap is borrowed from another
    template.
    """
    joined = _check_origin_ref(template)
    gaps: List[str] = []
    if not joined.stages:
        gaps.append(
            "has passed through no step: the template has not started")
        return tuple(gaps)
    if joined.stages[0] != "drafted":
        gaps.append(
            f"opens at {joined.stages[0]}, not at drafted: "
            f"the template opens with the reflection")
    for before, after in zip(joined.stages, joined.stages[1:]):
        if not legal_step(before, after):
            gaps.append(
                f"steps from {before} to {after}, which the "
                f"template sequence does not allow")
    for command in joined.claims:
        if command in BARE_CLAIMS:
            gaps.append(
                f"carries a {command} claim, a bare claim with no "
                f"held proof: complete stands on held proof alone")
    if source is not None:
        try:
            _ref = _source_book(source).slice_for(joined.command_id)
        except Exception:
            _ref = None
        if _ref is not None and _ref.origin == "unfiled" and \
                "origin_ref" not in joined.claims:
            gaps.append(
                "stands joined on an unfiled command with no "
                "origin_ref held: the file origin for the "
                "command is unproven")
    if joined.stages[-1] != "held":
        gaps.append(
            f"has not reached held: the template stands "
            f"at {joined.stages[-1]}")
    return tuple(gaps)

def template_green(template: Any, source: Any = None) -> bool:
    return not template_gaps(template, source)


def plain_lines(template: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the template's own fields."""
    joined = _check_origin_ref(template)
    return (
        f"Template: {joined.title}",
        f"Command: {joined.command_id}",
        f"Stage: {joined.stage if joined.stage else 'none'}",
        f"Claims: "
        f"{', '.join(joined.claims) if joined.claims else 'none'}",
    )


def segment_of(template: Any, source: Any = None) -> str:
    joined = _check_origin_ref(template)
    gaps = template_gaps(joined, source)
    return (
        f"{joined.template_id}: {joined.title} - command: "
        f"'{joined.command_id}' - stage: "
        f"'{joined.stage if joined.stage else 'none'}' - "
        f"stages: {len(joined.stages)} - claims: "
        f"'{', '.join(joined.claims) if joined.claims else 'none'}' - "
        f"detail: '{joined.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held command reference: the active command a book templates from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class CommandRef:
    """One command a template book templates from, held as a reference.

    The record names the command, the title it
    opens and its standing - active or
    queued - held as data copied from the
    M-203 command book's own telling. A template
    stands only from an active reference: the
    book refuses a template naming no held reference,
    and a template from an queued one, BY NAME.
    """

    command_id: str
    seq: int
    title: str
    state: str
    origin: str = "project"
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "command_id", _clean_text(self.command_id, "an command id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a title"))
        object.__setattr__(
            self, "state", normalize_command_state(self.state))
        object.__setattr__(
            self, "origin", normalize_origin(self.origin))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an command detail"))
        for key in _HELDANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.command_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "command_id": self.command_id, "seq": self.seq,
            "title": self.title, "state": self.state,
            "origin": self.origin,
            "detail": self.detail,
        }
        for key in _HELDANCE:
            record[key] = getattr(self, key)
        return record


def _check_command_ref(value: Any) -> CommandRef:
    if not isinstance(value, CommandRef):
        raise ValueError("a command reference must be an CommandRef")
    return value


def validate_command_ref(ref: Any) -> CommandRef:
    return _check_command_ref(ref)


def build_command_ref(record: Any = None, **kwargs: Any) -> CommandRef:
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, CommandRef):
        if kwargs:
            raise ValueError(
                "a command reference stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError(
            "a command reference must be a mapping or an CommandRef")
    _needed(data, _SLICE_REF_KEYS, "a command reference")
    return CommandRef(
        command_id=data.get("command_id"), seq=data.get("seq"),
        title=data.get("title"), state=data.get("state"), origin=data.get("origin") or "project",
        detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The held trace trace: the human approves the trace, as data.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TraceRecord:
    """One trace trace, held as data.

    The record names its command and the trace the
    human active - the command's template ids in
    derived claim template, held exactly as
    active. The trace is of the set and its
    template, never of a step: when the derived
    trace moves, this record stands stale, drafted
    in the ledger, until a new trace is active.
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
            self, "template_id", _clean_text(self.template_id, "an command id"))
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
            "template_id": self.template_id, "trace": self.trace,
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
        template_id=data.get("template_id"), trace=data.get("trace"),
        detail=data.get("detail"),
        **_heldance(data))


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
        for key in _HELDANCE:
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
        template_id=data.get("template_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The held view: which commands a telling shows.
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
        **_heldance(data))


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
    joined = _check_row_ref(row)
    if template is not None:
        derived = _row_for_template(_check_origin_ref(template), source)
        if joined != derived:
            raise ValueError(
                f"panel row {joined.item_id!r} does not agree with "
                f"the row derived from its template")
    return joined


def build_row(row: Any = None, template: Any = None,
              source: Any = None,
              **kwargs: Any) -> TemplatePanelRow:
    if template is not None:
        derived = _row_for_template(_check_origin_ref(template), source)
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
                data.get("recorded_on"), "a row recorded_on command"))
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
        "Rows stand in held template, the template the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its template's own fields "
        "- the command it answers for, the steps it walked in the "
        "open and the evidence it honestly carries - and no "
        "judgement is stored on any template.",
        "Completeness is filed from the held records alone: "
        "a template that steps outside the template sequence, "
        "carries a bare claim in place of held evidence, or has "
        "not drafted held stands open, drafted in its "
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


def templates_for_command(source: Any, command_id: Any
                      ) -> Tuple[TemplateRecord, ...]:
    wanted = _clean_text(command_id, "an command id")
    return tuple(
        g for g in _source_book(source).templates if g.command_id == wanted)


def green_templates(source: Any) -> Tuple[TemplateRecord, ...]:
    book = _source_book(source)
    return tuple(g for g in book.templates if template_green(g, book))


def current_template(source: Any) -> Optional[TemplateRecord]:
    """The book's current template, DERIVED at call time.

    The first held template, in held template, that does
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
    joined = _check_panel_ref(panel)
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(joined.view_id)
                if joined.view_id is not None else None)
        derived = derive_panel(book, view)
        for attr in ("view_id", "view_filter", "rows", "total_items",
                     "total_shown", "target_counts", "as_of", "account"):
            if getattr(joined, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {joined.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return joined


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
            as_of=_clean_text(data.get("as_of"), "an as_of command"),
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
        return "held"
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
    joined = _check_verdict_ref(verdict)
    if joined.verdict not in VERDICT_WORDS:
        raise ValueError(f"verdict {joined.verdict!r} is not a held word")
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(joined.view_id)
                if joined.view_id is not None else None)
        derived = derive_verdict(book, view)
        if joined != derived:
            raise ValueError(
                "the stored verdict disagrees with the verdict "
                "derived from its book")
    return joined


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
            latest_on=_clean_text(data.get("latest_on"), "a latest command"))
        return validate_verdict(built, source)
    if verdict is None and source is not None:
        return derive_verdict(source, kwargs.get("view"))
    raise ValueError(
        "a verdict must be a mapping, an TemplateVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held commands' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexTemplate:
    stage: str
    template_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "stage": self.stage, "template_id": self.template_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class TemplateIndex:
    """The template index, derived from the held templates.

    The index names one template per green template, in
    held template - the template's own one verifiable
    stage, its template id and its title - and the
    templates that do not stand complete, drafted in its
    gaps. Nothing here is stored on any template: the
    index is derived at call time from the held
    records alone, so it can never drift from them.
    """

    templates: Tuple[IndexTemplate, ...]
    gaps: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "templates": [e.to_record() for e in self.templates],
            "gaps": list(self.gaps),
        }


def derive_index(source: Any) -> TemplateIndex:
    """Derive the template index from the book's held templates."""
    book = _source_book(source)
    templates = tuple(
        IndexTemplate(stage=g.stage, template_id=g.template_id,
                   title=g.title)
        for g in book.templates if template_green(g, book))
    gaps = tuple(
        g.template_id for g in book.templates if not template_green(g, book))
    return TemplateIndex(templates=templates, gaps=gaps)


def template_for_check(source: Any, stage: Any) -> Optional[TemplateRecord]:
    """The first held template one stage reaches, or none - honestly."""
    if stage is None:
        return None
    if not isinstance(stage, str):
        raise ValueError("an stage must be a string naming the stage")
    wanted = stage.strip()
    if not wanted:
        return None
    for template in _source_book(source).templates:
        if template.stage == wanted:
            return template
    return None


def transition_breaks(source: Any) -> Tuple[str, ...]:
    """Every step outside the gate sequence, DERIVED.

    One telling per break, in held template: the template
    that took it and the step it took, before,
    then after. A book whose templates all walk inside
    the machine tells none.
    """
    book = _source_book(source)
    return tuple(
        f"{template_id}: {step}"
        for template_id, steps in _breaks_map(book).items()
        for step in steps)

def template_template(source: Any,
              command_id: Any = None) -> Tuple[TemplateRecord, ...]:
    """The held templates in their held template, DERIVED at call time.

    Templates stand in the template the book holds them -
    the template their commands were drafted - optionally
    for one command alone. Nothing here is stored:
    the template is the book's own held template, told.
    """
    book = _source_book(source)
    templates = list(book.templates)
    if command_id is not None:
        wanted = _clean_text(command_id, "a command id")
        templates = [r for r in templates if r.command_id == wanted]
    return tuple(templates)

def trace_of(source: Any, template_id: Any) -> str:
    """One template's trace, DERIVED at call time.

    The template's walked stages joined as one trace
    line, in walk template. A template that has walked
    nowhere traces empty: the trace tells only
    what stands walked, and the walk is drafted
    elsewhere.
    """
    template = _source_book(source).template_for(template_id)
    return " > ".join(template.stages)

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
    """The held stance target for one template (and stance, when drafted)."""
    wanted = _clean_text(template_id, "a template id")
    for record in _source_book(source).notes:
        if record.template_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the command targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


def ledger_record(source: Any = None) -> Dict[str, Any]:
    """The template ledger, DERIVED here from the held templates alone.

    The ledger counts the held templates by their
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
        "type": "template_well",
        "command": TEMPLATE_SLICE,
        "standings": standings,
        "total": len(book.templates),
        "current_template": current.template_id if current is not None else None,
        "traces": traces,
        "breaks": list(transition_breaks(book)),
    }

def roadmap_record() -> Dict[str, Any]:
    """This command's own roadmap standing, proved from the roadmap itself.

    The record loads this command's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 commands in 11 parts,
    the drafted prefix, the next command where the
    template templates, and M-237's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(TEMPLATE_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "template_roadmap",
        "command": TEMPLATE_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m237_title": own.title,
        "m237_part": own.part,
        "m237_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: commands, templates, views, notes and trace traces held
# together, one pinned panel at most per telling, and no verdict,
# index, trace or template ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TemplateBook:
    title: str
    commands: Tuple[CommandRef, ...] = ()
    templates: Tuple[TemplateRecord, ...] = ()
    views: Tuple[TemplateView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    traces: Tuple[TraceRecord, ...] = ()
    panels: Tuple[TemplatePanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        commands = tuple(_check_command_ref(g) for g in self.commands)
        templates = tuple(_check_origin_ref(g) for g in self.templates)
        views = tuple(_check_view_ref(v) for v in self.views)
        notes = tuple(_check_note_ref(m) for m in self.notes)
        traces = tuple(_check_trace_ref(a) for a in self.traces)
        panels = tuple(_check_panel_ref(pn) for pn in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for ref in commands:
            if ref.command_id in seen_ids:
                raise ValueError(
                    f"two command references stand under id {ref.command_id!r}")
            if ref.seq in seen_seqs:
                raise ValueError(
                    f"two command references stand at sequence {ref.seq}")
            seen_ids.add(ref.command_id)
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
        by_slice = {ref.command_id: ref for ref in commands}
        for template in (templates if commands else ()):

            ref = by_slice.get(template.command_id)
            if ref is None:
                raise ValueError(
                    f"template {template.template_id!r} is held from command "
                    f"{template.command_id!r}, which stands nowhere in "
                    f"this book")
            if ref.state != "live":
                raise ValueError(
                    f"template {template.template_id!r} is held from command "
                    f"{template.command_id!r}, which is not active: "
                    f"no command is held from an queued command")
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
            self, "commands", tuple(sorted(commands, key=lambda g: g.seq)))
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

    def command_ids(self) -> Tuple[str, ...]:
        return tuple(g.command_id for g in self.commands)

    def template_for(self, template_id: Any) -> TemplateRecord:
        wanted = _clean_text(template_id, "a template id")
        for template in self.templates:
            if template.template_id == wanted:
                return template
        raise KeyError(f"no template drafted {wanted!r} stands in this book")

    def slice_for(self, command_id: Any) -> CommandRef:
        wanted = _clean_text(command_id, "an command id")
        for ref in self.commands:
            if ref.command_id == wanted:
                return ref
        raise KeyError(f"no command drafted {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> TemplateView:
        wanted = _clean_text(view_id, "a view id")
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no view drafted {wanted!r} stands in this book")

    def note_for(self, note_id: Any) -> NoteRecord:
        wanted = _clean_text(note_id, "a stance id")
        for record in self.notes:
            if record.note_id == wanted:
                return record
        raise KeyError(f"no stance drafted {wanted!r} stands in this book")

    def trace_for(self, trace_id: Any) -> TraceRecord:
        wanted = _clean_text(trace_id, "an trace id")
        for record in self.traces:
            if record.trace_id == wanted:
                return record
        raise KeyError(f"no trace drafted {wanted!r} stands in this book")

    def item_for(self, item_id: Any) -> Any:
        wanted = _clean_text(item_id, "an item id")
        for template in self.templates:
            if template.template_id == wanted:
                return template
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item drafted {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "commands": [g.to_record() for g in self.commands],
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
    if book.title != "Custom commands at the M-237 slice run":
        raise ValueError("the shipped example book carries another title")
    if len(book.commands) != 3 or len(book.templates) != 5 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold three command references, five templates and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.traces) != 1:
        raise ValueError("the shipped example book must hold one trace record")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-command":
        raise ValueError("the pinned panel is panel-command")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "held" or verdict.green_shown != 3:
        raise ValueError("the shipped example book verdict must stand held at three complete of five")
    index = derive_index(book)
    if [e.stage for e in index.templates] != ["held", "held", "held"]:
        raise ValueError("the shipped example book index must derive the three held complete templates in held template")
    if index.gaps != ("template-bare-template", "template-leaping-template"):
        raise ValueError("the shipped example book must leave the bare and leaping templates honestly open, drafted in its gaps")
    drafted = template_for_check(book, EXAMPLE_STAGE)
    if drafted is None or drafted.template_id != "template-held-template":
        raise ValueError("the shipped example book must reach its opening template under the example stage")
    if trace_of(book, "template-held-template") != "drafted > checked > filed > joined > held":
        raise ValueError("the shipped example book must derive the opening template's trace from its walked steps")
    if not trace_current(book, "template-held-template"):
        raise ValueError("the shipped example book must hold the opening template's trace current")
    first = first_note(book)
    if first is None or first.note_id != "note-note-first":
        raise ValueError("the shipped example book must hold the opening note as its first note template")

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
                f"the book claims a live command build or execution "
                f"({key!r} is drafted on it): {TEMPLATE_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its templates under a view")
    if "template_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held templates at call time")
    if "ledger" in data or "current_template" in data:
        raise ValueError(
            "a book stores no ledger and no current template: both are "
            "derived from its held templates at call time")
    if "trace" in data or "template" in data:
        raise ValueError(
            "a book stores no trace and no template: both are derived "
            "from its held templates at call time; an trace record "
            "holds the trace the human active")
    if data.get("schema") is not None and (
            data["schema"] != TEMPLATE_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{TEMPLATE_SCHEMA!r}")
    if data.get("command") is not None and (
            data["command"] != TEMPLATE_SLICE):
        raise ValueError(
            f"a book's command must be {TEMPLATE_SLICE!r}")
    head = data.get("template_head") or data.get("custom_commands") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's template head must be a mapping")
    title = head.get("title") or data.get("title")
    commands = tuple(build_command_ref(g) for g in data.get("commands") or ())
    templates = tuple(build_template(g) for g in data.get("template_records") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    traces = tuple(build_trace(a) for a in data.get("traces") or ())
    book = TemplateBook(
        title=title, commands=commands, templates=templates, views=views,
        notes=notes, traces=traces, panels=())
    panels = tuple(
        build_panel(pn, book) for pn in data.get("panels") or ())
    book = TemplateBook(
        title=book.title, commands=book.commands, templates=book.templates,
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
# The registry: command references, templates and views held one by one.
# ---------------------------------------------------------------------

class TemplateRegistry:
    """An in-memory holding of command references, templates and views.

    The registry is the pure layer's model of a
    session's template book: command references are
    held under their ids, templates are held under
    their ids, one template per id and per sequence,
    and views are held in checked template, one view
    per sequence and per id. Holding is data only -
    nothing held here builds anything, executes
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._slices: List[CommandRef] = []
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

    def register_command_ref(self, item: Any) -> CommandRef:
        """Hold one command reference, filed whole before held."""
        joined = _check_command_ref(item)
        return self._register(
            self._slices, joined, "command_id", "command reference")

    def register_template(self, item: Any) -> TemplateRecord:
        """Hold one template, filed whole before held."""
        joined = _check_origin_ref(item)
        return self._register(
            self._templates, joined, "template_id", "template")

    def register_view(self, view: Any) -> TemplateView:
        """Hold one view; a view naming no id takes a fresh one."""
        joined = _check_view_ref(view)
        if not joined.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            joined = build_view({**joined.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, joined, "view_id", "view")

    def register_book(self, book: Any) -> TemplateBook:
        """Hold a whole book's records, under its title."""
        joined = build_book(book)
        if self._title is not None and joined.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {joined.title!r}")
        for ref in joined.commands:
            self.register_command_ref(ref)
        for template in joined.templates:
            self.register_template(template)
        for view in joined.views:
            self.register_view(view)
        self._title = joined.title
        return self.book()

    def book(self) -> TemplateBook:
        return TemplateBook(
            title=self._title or "An unheld template book",
            commands=tuple(self._slices), templates=tuple(self._templates),
            views=tuple(self._views), notes=(), traces=(), panels=())

    def list_slices(self) -> Tuple[CommandRef, ...]:
        return tuple(self._slices)

    def list_templates(self) -> Tuple[TemplateRecord, ...]:
        return tuple(self._templates)

    def list_views(self) -> Tuple[TemplateView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._templates) + tuple(self._views)

    def get_slice(self, command_id: Any) -> CommandRef:
        return self.book().slice_for(command_id)

    def get_template(self, template_id: Any) -> TemplateRecord:
        return self.book().template_for(template_id)

    def get_view(self, view_id: Any) -> TemplateView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records traced for the ledger target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> TemplateBook:
    if source is None:
        return load_template()
    if isinstance(source, TemplateBook):
        return source
    if isinstance(source, TemplateRegistry):
        return source.book()
    return build_book(source)


def _heldance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _HELDANCE}


def template_record(template: Any, source: Any = None) -> Dict[str, Any]:
    joined = _check_origin_ref(template)
    book = _source_book(source) if source is not None else None
    record = {
        "type": "template_template",
        "command": TEMPLATE_SLICE,
        "template_id": joined.template_id,
        "command_id": joined.command_id,
        "title": joined.title,
        "segment": segment_of(joined, book),
        "complete": template_green(joined, book),
        "gaps": list(template_gaps(joined, book)),
    }
    record.update(_heldance_record(joined))
    return record


def command_record(ref: Any) -> Dict[str, Any]:
    joined = _check_command_ref(ref)
    record = {
        "type": "template_run",
        "command": TEMPLATE_SLICE,
        "command_id": joined.command_id,
        "title": joined.title,
        "state": joined.state, "origin": joined.origin,
    }
    record.update(_heldance_record(joined))
    return record


def trace_record(record_in: Any) -> Dict[str, Any]:
    joined = _check_trace_ref(record_in)
    record = {
        "type": "template_trace",
        "command": TEMPLATE_SLICE,
        "trace_id": joined.trace_id,
        "template_id": joined.template_id,
        "trace": joined.trace,
    }
    record.update(_heldance_record(joined))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    joined = _check_view_ref(view)
    record = {
        "type": "template_view",
        "command": TEMPLATE_SLICE,
        "view_id": joined.view_id, "seq": joined.seq,
        "view_filter": joined.view_filter,
    }
    record.update(_heldance_record(joined))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    joined = _check_note_ref(record_in)
    record = {
        "type": "template_note",
        "command": TEMPLATE_SLICE,
        "note_id": joined.note_id,
        "template_id": joined.template_id,
        "stance": joined.stance,
    }
    record.update(_heldance_record(joined))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    joined = validate_panel(panel, source)
    record = {"type": "template_panel",
              "command": TEMPLATE_SLICE}
    record.update(joined.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, TemplateVerdict):
        joined = validate_verdict(verdict, source)
    else:
        joined = derive_verdict(_source_book(verdict), view)
    record = {"type": "template_verdict",
              "command": TEMPLATE_SLICE}
    record.update(joined.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, TemplateIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "template_index",
              "command": TEMPLATE_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    joined = _source_book(book)
    record = {"type": "template_book",
              "command": TEMPLATE_SLICE,
              "title": joined.title}
    record.update(joined.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(template: Any, source: Any = None) -> str:
    joined = _check_origin_ref(template)
    return (
        f"{joined.title} - from {joined.command_id}: "
        f"stage {joined.stage if joined.stage else 'none'}, "
        f"claims "
        f"{', '.join(joined.claims) if joined.claims else 'none'}. "
        f"{joined.detail}")


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
    joined = _check_view_ref(view)
    return f"View {joined.view_id}: shows {joined.view_filter} templates."


def note_plain_words(record_in: Any) -> str:
    joined = _check_note_ref(record_in)
    return (
        f"Note {joined.note_id}: {joined.stance} "
        f"{joined.template_id}, toward {joined.target}. "
        f"{joined.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, TemplateIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.templates)} green templates; "
        f"red, drafted in its gaps: {gaps}.")

def format_template(template: Any, source: Any = None) -> str:
    joined = _check_origin_ref(template)
    book = _source_book(source) if source is not None else None
    lines = [f"{joined.title} ({joined.template_id})"]
    lines.extend(plain_lines(joined))
    lines.append(joined.detail)
    if template_green(joined, book):
        lines.append(
            "This template stands complete - it walked the question "
            "sequence in the open from drafted to held, "
            "and it carries held evidence alone.")
    else:
        lines.append(
            "This template stands open - it stands drafted in "
            f"its gaps: {', '.join(template_gaps(joined, book))}, and "
            "nothing is invented for it.")
    return "\n".join(lines)

def format_view(view: Any) -> str:
    joined = _check_view_ref(view)
    return (
        f"View {joined.view_id}: filter {joined.view_filter} - "
        f"{joined.detail}")


def format_note(record_in: Any) -> str:
    joined = _check_note_ref(record_in)
    lines = [
        f"Template note {joined.stance} {joined.template_id} "
        f"({joined.note_id}): {joined.title}. {joined.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or template it builds nothing, executes nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_stage(source: Any, stage: Any) -> str:
    template = template_for_check(source, stage)
    if template is not None:
        return format_template(template, source)
    wanted = stage.strip() if isinstance(stage, str) else stage
    return (
        f"No held template stands under stage {wanted!r} yet - the "
        f"stage reaches nothing in this book, and no template is "
        f"invented for it.")


def format_book(source: Any = None, command_id: Any = None) -> str:
    book = _source_book(source)
    templates = (templates_for_command(book, command_id)
              if command_id is not None else book.templates)
    lines = [f"The Custom Commands (M-237) - {book.title}"]
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
    for template in index.templates:
        lines.append(f"{template.stage} - {template.title} ({template.template_id})")
    if index.gaps:
        lines.append(
            "Red, drafted honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "builds nothing, executes nothing and opens no network.")
    return "\n".join(lines)


def format_template_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "The Custom Commands (M-237)",
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
    if head in ("stage", "command"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("index", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
