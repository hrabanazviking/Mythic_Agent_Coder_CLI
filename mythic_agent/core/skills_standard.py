"""Cross-app method (roadmap slice M-236).

Part X - Bridges. The roadmap
words: **reusable skill packs (the Agent Skills form) loadable per project and per user; Volmarr’s own skill library is the first citizen.******

What already ships, and what this skill adds:

* Mythic's bridge faces already ship (M-233 consuming, M-234 serving, M-235 the registry, ``mythic_agent/core/mcp_registry.py`` the nearest kin). This slice builds the skills standard that stands beside them: reusable skill packs in the Agent Skills form, each pack held as data naming its skill, its load scope (per project, per user, or not yet scoped), and its instructions, resources and scripts held by reference from its manifest BEFORE any load is granted, with Volmarr's own skill library held as the first citizen and nothing loaded live. The packs book WIRES that skills face as data, in its own module, standing in the M-195 copy-and-share
  book book the M-236 book stands in: one tracker
  per book, and the tracker's charge over one
  pack across its skill held as a book - a
  pack. The shipped packs stand untouched behind
  their seams: this layer holds packs as data
  over the book's skills and rewrites none of them,
  and the packs book keeps its own standing.
  Packs stand on the ledger AS DATA alone: a
  pack carries a ledger ref, a reference held in
  this book; holding, viewing or telling a pack
  skills no pack live, moves no keeper and files
  nothing.
* No charter row names this skill: the M-171 TUI
  redesign charter binds Part VIII alone (M-172
  to M-200) and names M-236 on no row, and the
  skill tests pin that absence live. The M-005
  method charter names no skill row either: its
  own words name the whole of Part IX (M-201
  to M-232) as the part that executes the
  charter; Part X stands on the roadmap's own
  words, and this slice is built to those words.

* A pack is held whole: the skill it
  answers for, found by its skill id; its title;
  the pack steps it walked, held as data in
  walk pack; and the evidence it carries, held
  as data by skill. The pack walk is EXPLICIT:
  its sequence stands as data
  (:data:`STAGES`, :data:`TRANSITIONS`) -
  found, opened, vetted, loaded, held -
  and a pack's standing is DERIVED at
  call time from its held steps and evidence
  alone: a pack that opens anywhere but
  found, steps where the sequence does not
  allow, carries a bare claim in place of held
  evidence, or has not yet found held stands
  open, found in its gaps.
* The evidence is a closed vocabulary in two
  halves: the held evidence - instructions_ref,
  resources_ref, scripts_ref, manifest_ref, scope_ref, evidence
  a tracker can point to - and the bare claims -
  feeling, memory, assertion, summary, which
  stand as no evidence at all. A pack is
  loaded from held evidence alone, never
  from a feeling: a pack holding a
  bare claim stands open, found in its gaps.
* A pack stands only for an ACTIVE
  skill. The book holds each skill it answers
  for as a reference record - its id, its title
  and its standing, active or queued, held as
  data copied from the roadmap's own telling. A
  pack naming a skill that stands
  nowhere in the book refuses BY NAME, and a
  pack for a skill that is not active
  refuses BY NAME beside it: the tracker deals with
  the skill in hand, in roadmap pack, never a
  queued one, and a skill whose pack already
  stands complete is never vetted twice - the
  current pack is derived, so a
  completed skill is never the current pack
  twice.
* The pack's trace is visible. A trace
  record holds one pack's walked steps
  as one trace line, exactly as walked, beside
  the pack. The derived trace is
  computed at call time from the pack's
  held steps; a held trace that no longer agrees
  with it stands stale, found in the ledger - the
  trace is the walk itself, never a retelling
  of it.
* The pack index is DERIVED at call
  time from the held packs - one pack
  per complete pack, under the step it
  stands at - never a second stored copy that
  could drift. A stored index, standing verdict,
  panel, trace, pack or current-pack
  claim on any record refuses by name.
* The current pack is DERIVED at call
  time - the first held pack, in held
  pack, that does not yet stand complete - never
  stored where it could go stale.
* The notes are held as data: a note record
  naming its pack, its stance - note,
  concern, praise, question, a closed
  vocabulary - and what it feeds back toward,
  one record per pack stance; holding
  a note posts none of it, the rule stands as
  data (:data:`PACK_RULE`), and a record
  claiming a pack was actually held,
  captured or promoted live refuses BY NAME.
  The tracker packs - and those packs, too,
  are held as data here, never sent.
* The shipped data file holds one example book
  in exactly the book a real pack
  file takes, a loader reads a file anywhere on
  disk, packs and views are opened as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding a pack book for a session and
  telling from it. This layer reaches no live
  pack: it writes no pack live, files nothing
  to the ledger, captures no candidate, promotes
  nothing, spawns no tracker, destroys nothing,
  publishes nothing, sends nothing as the user,
  exposes no secret, weakens no security and
  opens no network - it holds packs
  as data and tells them.

Honesty rules, enforced here and pinned by tests:

* **The pack walk is explicit.** A
  pack is loaded against the held
  steps and legal steps alone; an illegal step
  stands found in its gaps, never silently
  reordered.
* **Complete stands on held evidence alone.** A
  pack that carries a feeling, a
  memory, an assertion or a summary in place of
  held evidence stands open, found in its gaps:
  a pack is loaded from evidence, not
  vibes.
* **Active skills only, in roadmap pack.** A
  pack for a missing or queued skill
  refuses by name; no pack is invented
  for a skill the tracker has not opened with.
* **Unknown stays unknown.** A pack
  whose steps are not yet held stands with its
  steps empty - no step is invented.
* **The index, panel, verdict, trace, pack
  and current pack are derived, never
  stored.** Each is derived from the held
  packs at call time; a stored one
  refuses by name, so it can never drift.
* **One pack per pack.** Two
  packs standing for one pack id
  refuse by name, and one note record stands per
  pack stance.
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
    "PACK_RESOURCE",
    "PACK_SCHEMA",
    "PACK_SLICE",
    "PACK_RULE",
    "PLAIN_EXPLANATION",
    "THE_PACK_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "COMPLETE_WORDS",
    "SKILL_STATES",
    "LOAD_SCOPES",
    "Any",
    "Dict",
    "List",
    "Optional",
    "TraceRecord",
    "PackRecord",
    "IndexPack",
    "SkillRef",
    "NoteRecord",
    "PackBook",
    "PackIndex",
    "PackPanel",
    "PackPanelRow",
    "PackRegistry",
    "PackVerdict",
    "PackView",
    "TargetCount",
    "trace_for_pack",
    "trace_record",
    "ledger_record",
    "book_record",
    "build_trace",
    "build_book",
    "build_pack",
    "build_skill_ref",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "current_pack",
    "transition_breaks",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "pack_for_check",
    "pack_pack",
    "pack_record",
    "first_note",
    "format_book",
    "format_pack",
    "format_index",
    "format_note",
    "format_stage",
    "format_panel",
    "format_pack_screen",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "skill_record",
    "load_pack",
    "load_pack_file",
    "normalize_skill_state",
    "normalize_scope",
    "normalize_stage",
    "normalize_claim_kind",
    "legal_step",
    "next_stage",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_pack",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_pack_args",
    "green_packs",
    "plain_lines",
    "plain_words",
    "roadmap_record",
    "segment_of",
    "trace_of",
    "trace_current",
    "shown_packs",
    "validate_trace",
    "validate_book",
    "validate_pack",
    "validate_skill_ref",
    "validate_note",
    "validate_panel",
    "validate_row",
    "validate_verdict",
    "validate_view",
    "verdict_plain_words",
    "verdict_record",
    "view_plain_words",
    "view_record",
    "pack_gaps",
    "pack_green",
    "packs_for_skill",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

PACK_SCHEMA = "mythic.skills_standard/1"
PACK_SLICE = "M-236"
THE_PACK_SLICE = PACK_SLICE
PACK_RESOURCE = "skills_standard.yaml"
INDEX_ACTION = "index"
EXAMPLE_STAGE = "held"
STAGE_FIELDS = ("stages", "claims")
COMPLETE_WORDS = ("complete", "open")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "complete", "open")
VERDICT_WORDS = ("held", "held", "blocked")
SKILL_STATES = ("live", "dormant")
LOAD_SCOPES = ("project", "user", "unscoped")
PACK_RULE = "packs are held as data alone: reusable skill packs (the Agent Skills form) loadable per project and per user, Volmarr’s own skill library the first citizen (the load scopes project, user and unscoped, one scope held per skill as data) - one library per book, and the library charge over one pack held as a pack - a pack stands as data, held by reference (a manifest ref), never loaded live - the pack walk stands as an explicit pack sequence - found, opened, vetted, loaded, held - and a pack completes only complete, complete being a state with evidence held - instructions ref, resources ref, scripts ref, manifest ref, scope ref - never a feeling, a memory, an assertion or a summary; reusable skill packs (the Agent Skills form) loadable per project and per user, Volmarr’s own skill library the first citizen - and a pack loaded without vetting, or held before it is loaded, stands open, named in its gaps; a pack on an unscoped skill stands complete only with its load scope held as a scope_ref; finding, opening, viewing and telling a pack loads no skill, installs nothing, runs no script, reads no resource file, spends nothing, spawns no process, opens no network and writes nothing outside held records"
PLAIN_EXPLANATION = "Skills standard (M-236): reusable skill packs (the Agent Skills form) loadable per project and per user; Volmarr’s own skill library is the first citizen."
USAGE = 'Usage: /skillsstandard | /skillsstandard pack <pack-id> | /skillsstandard stage <stage> | /skillsstandard skill <skill-id> | /skillsstandard view <view-id> | /skillsstandard note <note-id> | /skillsstandard index | /skillsstandard panel | /skillsstandard verdict'

STAGES = ("found", "opened", "vetted", "loaded", "held")
HELD_EVIDENCE = ("instructions_ref", "resources_ref", "scripts_ref", "manifest_ref", "scope_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
CLAIM_KINDS = HELD_EVIDENCE + BARE_CLAIMS
TRANSITIONS = {
    "found": ("opened",),
    "opened": ("vetted",),
    "vetted": ("loaded",),
    "loaded": ("found", "held"),
    "held": (),
}


def legal_step(before: Any, after: Any) -> bool:
    """Whether the gate sequence allows one step, DERIVED.

    The machine stands as data in TRANSITIONS:
    inspect steps only to build, build only to
    test, test to repair on a pack or to
    continue on a pass, repair back to build or
    test for the rerun, and continue steps
    nowhere - it is where a pack stands complete.
    A stage outside the machine allows nothing.
    """
    return after in TRANSITIONS.get(before, ())


def next_stage(stage: Any, failed: Any = False) -> Optional[str]:
    """The step the tracker takes next, DERIVED from the sequence.

    Banked leads to opened and opened to
    vetted; vetted leads to loaded; at
    loaded a follow-up banking steps back to found and a finished pack steps to held;
    held is the end of the walk and steps
    nowhere. A step outside the sequence refuses
    by name.
    """
    loaded = normalize_stage(stage)
    if loaded == "found":
        return "opened"
    if loaded == "opened":
        return "vetted"
    if loaded == "vetted":
        return "loaded"
    if loaded == "loaded":
        return "found" if failed else "held"
    return None


_HELDANCE = ("recorded_on", "actor", "source", "origin_session")
_RUN_KEYS = frozenset({
    "pack_id", "seq", "skill_id", "title", "stages",
    "claims", "detail",
} | set(_HELDANCE))
_SLICE_REF_KEYS = frozenset({
    "skill_id", "seq", "title", "state", "scope", "detail",
} | set(_HELDANCE))
_TRACE_KEYS = frozenset({
    "trace_id", "seq", "pack_id", "trace", "detail",
} | set(_HELDANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_HELDANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "pack_id", "stance", "target", "title",
    "detail",
} | set(_HELDANCE))
_DERIVED_KEYS = frozenset({
    "standing", "complete", "greens", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "packs", "coverage", "covered", "uncovered",
    "current_pack", "next_pack", "progress", "ledger",
    "current", "pack", "breaks", "live"})
_LIVE_KEYS = (
    "live_pack", "packs_live", "live_question",
    "packs_raise", "raises_slice", "raised_live",
    "answers_live", "answers_question", "answered_live",
    "delivers_live", "delivered_live", "packs_live",
    "resumed_live", "runs_pack", "paused_live",
    "runs_pack", "ran_pack", "spawns_process",
    "spawned_process", "builds_slice", "built_slice",
    "builds_live", "executes_slice", "executed_slice",
    "executes_live", "live_execution",
    "banks_slice", "banked_live", "pack_live",
    "pushes_slice", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_pack", "sent_pack",
    "posts_note", "held_note", "traces_live",
    "traced_live", "writes_ledger", "wrote_ledger", "files_pack", "filed_live", "spawns_tracker", "spawned_tracker", "sends_pack", "sent_pack", "writes_pack", "wrote_pack")


# ---------------------------------------------------------------------
# Small judges, in the sibling trace.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_stages(value: Any) -> Tuple[str, ...]:
    """A pack's walked stages, held as data.

    The stages stand as a list of stage names in
    walk pack, each one a stage of the explicit
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
    """A pack's asked claims: claim skills found as data.

    Each claim names one skill from the held
    vocabulary - the human skills the gate may ask
    and the code skills it must never ask, both
    held honestly as data - and a skill outside
    the vocabulary refuses.
    """
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError("claims must be a list of claim skills")
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
            out[key] = _clean_text(mapping.get(key), "a recorded_on skill")
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
                f"{what} claims a live gate pack or skill build "
                f"execution ({key!r} is found on it): "
                f"{PACK_RULE}")
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


def normalize_skill_state(value: Any) -> str:
    state = _clean_text(value, "an skill state").lower()
    if state not in SKILL_STATES:
        raise ValueError(
            f"skill state {state!r} is not one of the held "
            f"states: " + ", ".join(SKILL_STATES))
    return state


def normalize_scope(value: Any) -> str:
    scope = _clean_text(value, "a load scope").lower()
    if scope not in LOAD_SCOPES:
        raise ValueError(
            f"load scope {scope!r} is not one of the "
            f"skills load scopes: " + ", ".join(LOAD_SCOPES))
    return scope


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
    skill = _clean_text(value, "a claim skill").lower()
    if skill not in CLAIM_KINDS:
        raise ValueError(
            f"claim skill {skill!r} is not one of the held "
            f"skills: " + ", ".join(CLAIM_KINDS))
    return skill

# ---------------------------------------------------------------------
# The held pack: one skill cut from an active skill.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class PackRecord:
    """One pack skill, held as data.

    The pack names the active skill it was
    held from, by skill id, its title, its
    verifiable stages, held as data, and its
    claims, found by pack id. The grain is
    derived, never stored: exactly one verifiable
    walk is vetted against the machine. A pack whose
    stages are not yet held stands with its
    stages empty: it stands open, found in
    its gaps, and no stage is invented for it.
    The pack is local data alone - no live build
    stands behind it: holding it builds nothing.
    """

    pack_id: str
    seq: int
    skill_id: str
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
            self, "pack_id", _clean_text(self.pack_id, "a pack id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "skill_id", _clean_text(self.skill_id, "an skill id"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a pack title"))
        object.__setattr__(
            self, "stages", _check_stages(self.stages))
        object.__setattr__(
            self, "claims", _check_claims(self.claims))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a pack detail"))
        for key in _HELDANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.pack_id

    @property
    def stage(self) -> str:
        """The stage the pack stands at: its last walked stage."""
        return self.stages[-1] if self.stages else ""

    def to_record(self) -> Dict[str, Any]:
        record = {
            "pack_id": self.pack_id, "seq": self.seq,
            "skill_id": self.skill_id, "title": self.title,
            "stages": list(self.stages),
            "claims": list(self.claims),
            "detail": self.detail,
        }
        for key in _HELDANCE:
            record[key] = getattr(self, key)
        return record


def _check_scope_ref(value: Any) -> PackRecord:
    if not isinstance(value, PackRecord):
        raise ValueError("a pack must be a PackRecord")
    return value


def validate_pack(pack: Any) -> PackRecord:
    return _check_scope_ref(pack)


def build_pack(record: Any = None, **kwargs: Any) -> PackRecord:
    """Build one held pack from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, PackRecord):
        if kwargs:
            raise ValueError("a pack stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a pack must be a mapping or a PackRecord")
    _needed(data, _RUN_KEYS, "a pack")
    return PackRecord(
        pack_id=data.get("pack_id"), seq=data.get("seq"),
        skill_id=data.get("skill_id"), title=data.get("title"),
        stages=data.get("stages"),
        claims=data.get("claims"),
        detail=data.get("detail"),
        **_heldance(data))


def _breaks_map(book: Any) -> Dict[str, Tuple[str, ...]]:
    """Map each pack to the steps it took outside the machine.

    Derived from the held packs alone: a break is
    one consecutive pair of walked stages the
    explicit gate sequence does not allow, told
    in walk pack as before, then after.
    """
    found: Dict[str, Tuple[str, ...]] = {}
    for pack in book.packs:
        breaks = tuple(
            f"{before} > {after}"
            for before, after in zip(pack.stages, pack.stages[1:])
            if not legal_step(before, after))
        if breaks:
            found[pack.pack_id] = breaks
    return found

def pack_gaps(pack: Any, source: Any = None) -> Tuple[str, ...]:
    """The gaps that keep a pack from standing complete.

    Guarded from the pack's own held fields alone -
    its walked steps against the explicit question
    sequence, and its held evidence against the
    held vocabulary: the pack opens at
    found, steps only where the sequence
    allows, carries held evidence and no bare claim,
    and a pack stands complete only when it has
    found held. The source names nothing
    further: no gap is borrowed from another
    pack.
    """
    loaded = _check_scope_ref(pack)
    gaps: List[str] = []
    if not loaded.stages:
        gaps.append(
            "has passed through no step: the pack has not started")
        return tuple(gaps)
    if loaded.stages[0] != "found":
        gaps.append(
            f"opens at {loaded.stages[0]}, not at found: "
            f"the pack opens with the reflection")
    for before, after in zip(loaded.stages, loaded.stages[1:]):
        if not legal_step(before, after):
            gaps.append(
                f"steps from {before} to {after}, which the "
                f"pack sequence does not allow")
    for skill in loaded.claims:
        if skill in BARE_CLAIMS:
            gaps.append(
                f"carries a {skill} claim, a bare claim with no "
                f"held proof: complete stands on held proof alone")
    if source is not None:
        try:
            _ref = _source_book(source).slice_for(loaded.skill_id)
        except Exception:
            _ref = None
        if _ref is not None and _ref.scope == "unscoped" and \
                "scope_ref" not in loaded.claims:
            gaps.append(
                "stands loaded on an unscoped skill with no "
                "scope_ref held: the load scope for the "
                "skill is unproven")
    if loaded.stages[-1] != "held":
        gaps.append(
            f"has not reached held: the pack stands "
            f"at {loaded.stages[-1]}")
    return tuple(gaps)

def pack_green(pack: Any, source: Any = None) -> bool:
    return not pack_gaps(pack, source)


def plain_lines(pack: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the pack's own fields."""
    loaded = _check_scope_ref(pack)
    return (
        f"Pack: {loaded.title}",
        f"Skill: {loaded.skill_id}",
        f"Stage: {loaded.stage if loaded.stage else 'none'}",
        f"Claims: "
        f"{', '.join(loaded.claims) if loaded.claims else 'none'}",
    )


def segment_of(pack: Any, source: Any = None) -> str:
    loaded = _check_scope_ref(pack)
    gaps = pack_gaps(loaded, source)
    return (
        f"{loaded.pack_id}: {loaded.title} - skill: "
        f"'{loaded.skill_id}' - stage: "
        f"'{loaded.stage if loaded.stage else 'none'}' - "
        f"stages: {len(loaded.stages)} - claims: "
        f"'{', '.join(loaded.claims) if loaded.claims else 'none'}' - "
        f"detail: '{loaded.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held skill reference: the active skill a book packs from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class SkillRef:
    """One skill a pack book packs from, held as a reference.

    The record names the skill, the title it
    opens and its standing - active or
    queued - held as data copied from the
    M-203 skill book's own telling. A pack
    stands only from an active reference: the
    book refuses a pack naming no held reference,
    and a pack from an queued one, BY NAME.
    """

    skill_id: str
    seq: int
    title: str
    state: str
    scope: str = "project"
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "skill_id", _clean_text(self.skill_id, "an skill id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a title"))
        object.__setattr__(
            self, "state", normalize_skill_state(self.state))
        object.__setattr__(
            self, "scope", normalize_scope(self.scope))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an skill detail"))
        for key in _HELDANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.skill_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "skill_id": self.skill_id, "seq": self.seq,
            "title": self.title, "state": self.state,
            "scope": self.scope,
            "detail": self.detail,
        }
        for key in _HELDANCE:
            record[key] = getattr(self, key)
        return record


def _check_skill_ref(value: Any) -> SkillRef:
    if not isinstance(value, SkillRef):
        raise ValueError("a skill reference must be an SkillRef")
    return value


def validate_skill_ref(ref: Any) -> SkillRef:
    return _check_skill_ref(ref)


def build_skill_ref(record: Any = None, **kwargs: Any) -> SkillRef:
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, SkillRef):
        if kwargs:
            raise ValueError(
                "a skill reference stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError(
            "a skill reference must be a mapping or an SkillRef")
    _needed(data, _SLICE_REF_KEYS, "a skill reference")
    return SkillRef(
        skill_id=data.get("skill_id"), seq=data.get("seq"),
        title=data.get("title"), state=data.get("state"), scope=data.get("scope") or "project",
        detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The held trace trace: the human approves the trace, as data.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TraceRecord:
    """One trace trace, held as data.

    The record names its skill and the trace the
    human active - the skill's pack ids in
    derived claim pack, held exactly as
    active. The trace is of the set and its
    pack, never of a step: when the derived
    trace moves, this record stands stale, found
    in the ledger, until a new trace is active.
    """

    trace_id: str
    seq: int
    pack_id: str
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
            self, "pack_id", _clean_text(self.pack_id, "an skill id"))
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
            "pack_id": self.pack_id, "trace": self.trace,
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
        pack_id=data.get("pack_id"), trace=data.get("trace"),
        detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The held stance: a note on a pack, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One pack stance, held as data.

    The record names its pack, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per pack stance
    in a book. The record is data alone: holding
    it builds nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    pack_id: str
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
            self, "pack_id", _clean_text(self.pack_id, "a pack id"))
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
            "pack_id": self.pack_id, "stance": self.stance,
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
        pack_id=data.get("pack_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The held view: which skills a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class PackView:
    """A view over the book: every pack, the green, the rest."""

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


def _check_view_ref(value: Any) -> PackView:
    if not isinstance(value, PackView):
        raise ValueError("a view must be an PackView")
    return value


def validate_view(view: Any) -> PackView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> PackView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, PackView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an PackView")
    _needed(data, _VIEW_KEYS, "a view")
    return PackView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class PackPanelRow:
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


def _row_for_pack(pack: PackRecord,
                     source: Any = None) -> PackPanelRow:
    return PackPanelRow(
        item_id=pack.pack_id,
        standing="complete" if pack_green(pack, source) else "open",
        label=pack.title, segment=segment_of(pack, source),
        recorded_on=pack.recorded_on)


def _check_row_ref(value: Any) -> PackPanelRow:
    if not isinstance(value, PackPanelRow):
        raise ValueError("a panel row must be an PackPanelRow")
    return value


def validate_row(row: Any, pack: Any = None,
                 source: Any = None) -> PackPanelRow:
    loaded = _check_row_ref(row)
    if pack is not None:
        derived = _row_for_pack(_check_scope_ref(pack), source)
        if loaded != derived:
            raise ValueError(
                f"panel row {loaded.item_id!r} does not agree with "
                f"the row derived from its pack")
    return loaded


def build_row(row: Any = None, pack: Any = None,
              source: Any = None,
              **kwargs: Any) -> PackPanelRow:
    if pack is not None:
        derived = _row_for_pack(_check_scope_ref(pack), source)
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            PackPanelRow(**kwargs))
        return validate_row(built, pack, source)
    if isinstance(row, PackPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in COMPLETE_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return PackPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on skill"))
    if row is None and kwargs:
        return PackPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an PackPanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[PackPanelRow, ...]
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
        f"The pack book holds {total_items} packs as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {green_shown} of the shown packs "
        f"stand complete.",
        "Rows stand in held pack, the pack the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its pack's own fields "
        "- the skill it answers for, the steps it walked in the "
        "open and the evidence it honestly carries - and no "
        "judgement is stored on any pack.",
        "Completeness is vetted from the held records alone: "
        "a pack that steps outside the pack sequence, "
        "carries a bare claim in place of held evidence, or has "
        "not found held stands open, found in its "
        "gaps, and the pack index is derived from the "
        "held packs, never stored where it could drift.",
    )

@dataclass(frozen=True)
class PackPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[PackPanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> PackView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, PackView):
        return view
    return book.view_for(view)


def shown_packs(source: Any, view: Any = None
                   ) -> Tuple[PackRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.packs
    if resolved.view_filter == "complete":
        return tuple(g for g in book.packs if pack_green(g, book))
    return tuple(g for g in book.packs if not pack_green(g, book))


def packs_for_skill(source: Any, skill_id: Any
                      ) -> Tuple[PackRecord, ...]:
    wanted = _clean_text(skill_id, "an skill id")
    return tuple(
        g for g in _source_book(source).packs if g.skill_id == wanted)


def green_packs(source: Any) -> Tuple[PackRecord, ...]:
    book = _source_book(source)
    return tuple(g for g in book.packs if pack_green(g, book))


def current_pack(source: Any) -> Optional[PackRecord]:
    """The book's current pack, DERIVED at call time.

    The first held pack, in held pack, that does
    not yet stand complete - where the Architect must
    look next. Nothing here is stored: the telling
    is derived from the held packs alone, so it can
    never go stale against them. A book whose every
    pack stands complete has no current pack.
    """
    book = _source_book(source)
    for pack in book.packs:
        if not pack_green(pack, book):
            return pack
    return None


def derive_panel(source: Any, view: Any = None) -> PackPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_packs(book, resolved)
    rows = tuple(_row_for_pack(pack, book) for pack in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.packs), default="")
    green = sum(1 for g in shown if pack_green(g, book))
    return PackPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.packs), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.packs), len(shown), green, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> PackPanel:
    if not isinstance(value, PackPanel):
        raise ValueError("a panel must be an PackPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> PackPanel:
    """Judge a stored panel against the panel derived from its book.

    Every derived field must agree; the stored
    panel's own name is its identity, not derived
    content (the M-182 pack).
    """
    loaded = _check_panel_ref(panel)
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(loaded.view_id)
                if loaded.view_id is not None else None)
        derived = derive_panel(book, view)
        for attr in ("view_id", "view_filter", "rows", "total_items",
                     "total_shown", "target_counts", "as_of", "account"):
            if getattr(loaded, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {loaded.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return loaded


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> PackPanel:
    if isinstance(panel, PackPanel):
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
        built = PackPanel(
            panel_id=_clean_text(data.get("panel_id"), "a panel id"),
            view_id=data.get("view_id"),
            view_filter=normalize_view_filter(data.get("view_filter")),
            rows=rows,
            total_items=_check_count(
                data.get("total_items"), "a total_items count"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            target_counts=counts,
            as_of=_clean_text(data.get("as_of"), "an as_of skill"),
            account=_check_lines(data.get("account"), "the account"))
        return validate_panel(built, source)
    if panel is None and source is not None:
        return derive_panel(source, kwargs.get("view"))
    raise ValueError("a panel must be a mapping, an PackPanel, or derived")


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
class PackVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> PackVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_packs(book, resolved)
    green = sum(1 for g in shown if pack_green(g, book))
    latest = max((g.recorded_on for g in shown), default="")
    return PackVerdict(
        verdict=_verdict_word(len(shown), green),
        view_id=resolved.view_id, total_shown=len(shown),
        green_shown=green, latest_on=latest)


def _check_verdict_ref(value: Any) -> PackVerdict:
    if not isinstance(value, PackVerdict):
        raise ValueError("a verdict must be an PackVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> PackVerdict:
    loaded = _check_verdict_ref(verdict)
    if loaded.verdict not in VERDICT_WORDS:
        raise ValueError(f"verdict {loaded.verdict!r} is not a held word")
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(loaded.view_id)
                if loaded.view_id is not None else None)
        derived = derive_verdict(book, view)
        if loaded != derived:
            raise ValueError(
                "the stored verdict disagrees with the verdict "
                "derived from its book")
    return loaded


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> PackVerdict:
    if isinstance(verdict, PackVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = PackVerdict(
            verdict=_clean_text(data.get("verdict"), "a verdict"),
            view_id=data.get("view_id"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            green_shown=_check_count(
                data.get("green_shown"), "a green_shown count"),
            latest_on=_clean_text(data.get("latest_on"), "a latest skill"))
        return validate_verdict(built, source)
    if verdict is None and source is not None:
        return derive_verdict(source, kwargs.get("view"))
    raise ValueError(
        "a verdict must be a mapping, an PackVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held skills' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexPack:
    stage: str
    pack_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "stage": self.stage, "pack_id": self.pack_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class PackIndex:
    """The pack index, derived from the held packs.

    The index names one pack per green pack, in
    held pack - the pack's own one verifiable
    stage, its pack id and its title - and the
    packs that do not stand complete, found in its
    gaps. Nothing here is stored on any pack: the
    index is derived at call time from the held
    records alone, so it can never drift from them.
    """

    packs: Tuple[IndexPack, ...]
    gaps: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "packs": [e.to_record() for e in self.packs],
            "gaps": list(self.gaps),
        }


def derive_index(source: Any) -> PackIndex:
    """Derive the pack index from the book's held packs."""
    book = _source_book(source)
    packs = tuple(
        IndexPack(stage=g.stage, pack_id=g.pack_id,
                   title=g.title)
        for g in book.packs if pack_green(g, book))
    gaps = tuple(
        g.pack_id for g in book.packs if not pack_green(g, book))
    return PackIndex(packs=packs, gaps=gaps)


def pack_for_check(source: Any, stage: Any) -> Optional[PackRecord]:
    """The first held pack one stage reaches, or none - honestly."""
    if stage is None:
        return None
    if not isinstance(stage, str):
        raise ValueError("an stage must be a string naming the stage")
    wanted = stage.strip()
    if not wanted:
        return None
    for pack in _source_book(source).packs:
        if pack.stage == wanted:
            return pack
    return None


def transition_breaks(source: Any) -> Tuple[str, ...]:
    """Every step outside the gate sequence, DERIVED.

    One telling per break, in held pack: the pack
    that took it and the step it took, before,
    then after. A book whose packs all walk inside
    the machine tells none.
    """
    book = _source_book(source)
    return tuple(
        f"{pack_id}: {step}"
        for pack_id, steps in _breaks_map(book).items()
        for step in steps)

def pack_pack(source: Any,
              skill_id: Any = None) -> Tuple[PackRecord, ...]:
    """The held packs in their held pack, DERIVED at call time.

    Packs stand in the pack the book holds them -
    the pack their skills were found - optionally
    for one skill alone. Nothing here is stored:
    the pack is the book's own held pack, told.
    """
    book = _source_book(source)
    packs = list(book.packs)
    if skill_id is not None:
        wanted = _clean_text(skill_id, "a skill id")
        packs = [r for r in packs if r.skill_id == wanted]
    return tuple(packs)

def trace_of(source: Any, pack_id: Any) -> str:
    """One pack's trace, DERIVED at call time.

    The pack's walked stages joined as one trace
    line, in walk pack. A pack that has walked
    nowhere traces empty: the trace tells only
    what stands walked, and the walk is found
    elsewhere.
    """
    pack = _source_book(source).pack_for(pack_id)
    return " > ".join(pack.stages)

def trace_for_pack(source: Any,
                  pack_id: Any) -> Optional[TraceRecord]:
    """The held trace for one pack, or none - honestly."""
    wanted = _clean_text(pack_id, "a pack id")
    for record in _source_book(source).traces:
        if record.pack_id == wanted:
            return record
    return None

def trace_current(source: Any, pack_id: Any) -> bool:
    """Whether the held trace agrees with the derived trace.

    The trace stands current only while the trace
    it holds is the trace the book derives now; a
    moved walk leaves it stale, and no trace at
    all traces nothing.
    """
    trace = trace_for_pack(source, pack_id)
    if trace is None:
        return False
    return trace.trace == trace_of(source, pack_id)

def note_for_pack(source: Any, pack_id: Any,
                   stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one pack (and stance, when found)."""
    wanted = _clean_text(pack_id, "a pack id")
    for record in _source_book(source).notes:
        if record.pack_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the skill targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


def ledger_record(source: Any = None) -> Dict[str, Any]:
    """The pack ledger, DERIVED here from the held packs alone.

    The ledger counts the held packs by their
    derived completeness - green and red - names
    the current pack, the first that does not yet
    stand complete, tells each held pack's trace
    standing - current while its held trace
    agrees with its derived trace, stale when it
    has moved, unheld while no trace stands for
    it - and names every step the held packs took
    outside the gate sequence. Nothing here is
    stored: the telling is derived at call time.
    """
    book = _source_book(source)
    standings = []
    for standing in COMPLETE_WORDS:
        number = sum(
            1 for g in book.packs
            if ("complete" if pack_green(g, book) else "open") == standing)
        standings.append({"standing": standing, "pack_records": number})
    current = current_pack(book)
    traces = []
    for pack in book.packs:
        trace = trace_for_pack(book, pack.pack_id)
        if trace is None:
            standing = "unheld"
        elif trace_current(book, pack.pack_id):
            standing = "current"
        else:
            standing = "stale"
        traces.append({"pack_id": pack.pack_id, "trace": standing})
    return {
        "type": "pack_well",
        "skill": PACK_SLICE,
        "standings": standings,
        "total": len(book.packs),
        "current_pack": current.pack_id if current is not None else None,
        "traces": traces,
        "breaks": list(transition_breaks(book)),
    }

def roadmap_record() -> Dict[str, Any]:
    """This skill's own roadmap standing, proved from the roadmap itself.

    The record loads this skill's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 skills in 11 parts,
    the found prefix, the next skill where the
    pack packs, and M-236's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(PACK_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "pack_roadmap",
        "skill": PACK_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m236_title": own.title,
        "m236_part": own.part,
        "m236_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: skills, packs, views, notes and trace traces held
# together, one pinned panel at most per telling, and no verdict,
# index, trace or pack ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class PackBook:
    title: str
    skills: Tuple[SkillRef, ...] = ()
    packs: Tuple[PackRecord, ...] = ()
    views: Tuple[PackView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    traces: Tuple[TraceRecord, ...] = ()
    panels: Tuple[PackPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        skills = tuple(_check_skill_ref(g) for g in self.skills)
        packs = tuple(_check_scope_ref(g) for g in self.packs)
        views = tuple(_check_view_ref(v) for v in self.views)
        notes = tuple(_check_note_ref(m) for m in self.notes)
        traces = tuple(_check_trace_ref(a) for a in self.traces)
        panels = tuple(_check_panel_ref(pn) for pn in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for ref in skills:
            if ref.skill_id in seen_ids:
                raise ValueError(
                    f"two skill references stand under id {ref.skill_id!r}")
            if ref.seq in seen_seqs:
                raise ValueError(
                    f"two skill references stand at sequence {ref.seq}")
            seen_ids.add(ref.skill_id)
            seen_seqs.add(ref.seq)
        pack_ids = set()
        pack_seqs = set()
        for pack in packs:
            if pack.pack_id in pack_ids:
                raise ValueError(
                    f"two packs stand under id {pack.pack_id!r}")
            if pack.seq in pack_seqs:
                raise ValueError(
                    f"two packs stand at sequence {pack.seq}")
            pack_ids.add(pack.pack_id)
            pack_seqs.add(pack.seq)
        by_slice = {ref.skill_id: ref for ref in skills}
        for pack in (packs if skills else ()):

            ref = by_slice.get(pack.skill_id)
            if ref is None:
                raise ValueError(
                    f"pack {pack.pack_id!r} is held from skill "
                    f"{pack.skill_id!r}, which stands nowhere in "
                    f"this book")
            if ref.state != "live":
                raise ValueError(
                    f"pack {pack.pack_id!r} is held from skill "
                    f"{pack.skill_id!r}, which is not active: "
                    f"no skill is held from an queued skill")
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
            target = (record.pack_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for pack "
                    f"{record.pack_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per pack target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        trace_ids = set()
        trace_seqs = set()
        trace_packs = set()
        pack_ids = {pack.pack_id for pack in packs}
        for record in traces:
            if record.trace_id in trace_ids:
                raise ValueError(
                    f"two traces stand under id {record.trace_id!r}")
            if record.seq in trace_seqs:
                raise ValueError(
                    f"two traces stand at sequence {record.seq}")
            if record.pack_id in trace_packs:
                raise ValueError(
                    f"two traces stand for pack "
                    f"{record.pack_id!r}: one trace stands "
                    f"per pack walk")
            if packs and record.pack_id not in pack_ids:
                raise ValueError(
                    f"trace {record.trace_id!r} traces pack "
                    f"{record.pack_id!r}, which stands nowhere in "
                    f"this book")
            trace_ids.add(record.trace_id)
            trace_seqs.add(record.seq)
            trace_packs.add(record.pack_id)
        object.__setattr__(
            self, "skills", tuple(sorted(skills, key=lambda g: g.seq)))
        object.__setattr__(
            self, "pack_records", tuple(sorted(packs, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(
            self, "traces",
            tuple(sorted(traces, key=lambda a: a.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.packs + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.pack_id for g in self.packs) + tuple(
            v.view_id for v in self.views)

    def pack_ids(self) -> Tuple[str, ...]:
        return tuple(g.pack_id for g in self.packs)

    def skill_ids(self) -> Tuple[str, ...]:
        return tuple(g.skill_id for g in self.skills)

    def pack_for(self, pack_id: Any) -> PackRecord:
        wanted = _clean_text(pack_id, "a pack id")
        for pack in self.packs:
            if pack.pack_id == wanted:
                return pack
        raise KeyError(f"no pack found {wanted!r} stands in this book")

    def slice_for(self, skill_id: Any) -> SkillRef:
        wanted = _clean_text(skill_id, "an skill id")
        for ref in self.skills:
            if ref.skill_id == wanted:
                return ref
        raise KeyError(f"no skill found {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> PackView:
        wanted = _clean_text(view_id, "a view id")
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no view found {wanted!r} stands in this book")

    def note_for(self, note_id: Any) -> NoteRecord:
        wanted = _clean_text(note_id, "a stance id")
        for record in self.notes:
            if record.note_id == wanted:
                return record
        raise KeyError(f"no stance found {wanted!r} stands in this book")

    def trace_for(self, trace_id: Any) -> TraceRecord:
        wanted = _clean_text(trace_id, "an trace id")
        for record in self.traces:
            if record.trace_id == wanted:
                return record
        raise KeyError(f"no trace found {wanted!r} stands in this book")

    def item_for(self, item_id: Any) -> Any:
        wanted = _clean_text(item_id, "an item id")
        for pack in self.packs:
            if pack.pack_id == wanted:
                return pack
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item found {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "skills": [g.to_record() for g in self.skills],
            "pack_records": [g.to_record() for g in self.packs],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "traces": [a.to_record() for a in self.traces],
            "panels": [pn.to_record() for pn in self.panels],
        }


def _judge_book_panels(book: PackBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: PackBook) -> None:
    if book.title != "Skills standard at the M-236 slice run":
        raise ValueError("the shipped example book carries another title")
    if len(book.skills) != 3 or len(book.packs) != 5 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold three skill references, five packs and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.traces) != 1:
        raise ValueError("the shipped example book must hold one trace record")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-skill":
        raise ValueError("the pinned panel is panel-skill")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "held" or verdict.green_shown != 3:
        raise ValueError("the shipped example book verdict must stand held at three complete of five")
    index = derive_index(book)
    if [e.stage for e in index.packs] != ["held", "held", "held"]:
        raise ValueError("the shipped example book index must derive the three held complete packs in held pack")
    if index.gaps != ("pack-bare-pack", "pack-leaping-pack"):
        raise ValueError("the shipped example book must leave the bare and leaping packs honestly open, found in its gaps")
    found = pack_for_check(book, EXAMPLE_STAGE)
    if found is None or found.pack_id != "pack-held-pack":
        raise ValueError("the shipped example book must reach its opening pack under the example stage")
    if trace_of(book, "pack-held-pack") != "found > opened > vetted > loaded > held":
        raise ValueError("the shipped example book must derive the opening pack's trace from its walked steps")
    if not trace_current(book, "pack-held-pack"):
        raise ValueError("the shipped example book must hold the opening pack's trace current")
    first = first_note(book)
    if first is None or first.note_id != "note-note-first":
        raise ValueError("the shipped example book must hold the opening note as its first note pack")

def validate_book(data: Any, *, require_example: bool = False) -> PackBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, PackBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a pack book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live skill build or execution "
                f"({key!r} is found on it): {PACK_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its packs under a view")
    if "pack_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held packs at call time")
    if "ledger" in data or "current_pack" in data:
        raise ValueError(
            "a book stores no ledger and no current pack: both are "
            "derived from its held packs at call time")
    if "trace" in data or "pack" in data:
        raise ValueError(
            "a book stores no trace and no pack: both are derived "
            "from its held packs at call time; an trace record "
            "holds the trace the human active")
    if data.get("schema") is not None and (
            data["schema"] != PACK_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{PACK_SCHEMA!r}")
    if data.get("skill") is not None and (
            data["skill"] != PACK_SLICE):
        raise ValueError(
            f"a book's skill must be {PACK_SLICE!r}")
    head = data.get("pack_head") or data.get("skills_standard") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's pack head must be a mapping")
    title = head.get("title") or data.get("title")
    skills = tuple(build_skill_ref(g) for g in data.get("skills") or ())
    packs = tuple(build_pack(g) for g in data.get("pack_records") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    traces = tuple(build_trace(a) for a in data.get("traces") or ())
    book = PackBook(
        title=title, skills=skills, packs=packs, views=views,
        notes=notes, traces=traces, panels=())
    panels = tuple(
        build_panel(pn, book) for pn in data.get("panels") or ())
    book = PackBook(
        title=book.title, skills=book.skills, packs=book.packs,
        views=book.views, notes=book.notes,
        traces=book.traces, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> PackBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (PackBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an PackBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> PackBook:
    return validate_book(data, require_example=require_example)


def load_pack(
        data: Optional[Dict[str, Any]] = None) -> PackBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(PACK_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_pack_file(path: Any) -> PackBook:
    """Load one pack file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: skill references, packs and views held one by one.
# ---------------------------------------------------------------------

class PackRegistry:
    """An in-memory holding of skill references, packs and views.

    The registry is the pure layer's model of a
    session's pack book: skill references are
    held under their ids, packs are held under
    their ids, one pack per id and per sequence,
    and views are held in opened pack, one view
    per sequence and per id. Holding is data only -
    nothing held here builds anything, executes
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._slices: List[SkillRef] = []
        self._packs: List[PackRecord] = []
        self._views: List[PackView] = []
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

    def register_skill_ref(self, item: Any) -> SkillRef:
        """Hold one skill reference, vetted whole before held."""
        loaded = _check_skill_ref(item)
        return self._register(
            self._slices, loaded, "skill_id", "skill reference")

    def register_pack(self, item: Any) -> PackRecord:
        """Hold one pack, vetted whole before held."""
        loaded = _check_scope_ref(item)
        return self._register(
            self._packs, loaded, "pack_id", "pack")

    def register_view(self, view: Any) -> PackView:
        """Hold one view; a view naming no id takes a fresh one."""
        loaded = _check_view_ref(view)
        if not loaded.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            loaded = build_view({**loaded.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, loaded, "view_id", "view")

    def register_book(self, book: Any) -> PackBook:
        """Hold a whole book's records, under its title."""
        loaded = build_book(book)
        if self._title is not None and loaded.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {loaded.title!r}")
        for ref in loaded.skills:
            self.register_skill_ref(ref)
        for pack in loaded.packs:
            self.register_pack(pack)
        for view in loaded.views:
            self.register_view(view)
        self._title = loaded.title
        return self.book()

    def book(self) -> PackBook:
        return PackBook(
            title=self._title or "An unheld pack book",
            skills=tuple(self._slices), packs=tuple(self._packs),
            views=tuple(self._views), notes=(), traces=(), panels=())

    def list_slices(self) -> Tuple[SkillRef, ...]:
        return tuple(self._slices)

    def list_packs(self) -> Tuple[PackRecord, ...]:
        return tuple(self._packs)

    def list_views(self) -> Tuple[PackView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._packs) + tuple(self._views)

    def get_slice(self, skill_id: Any) -> SkillRef:
        return self.book().slice_for(skill_id)

    def get_pack(self, pack_id: Any) -> PackRecord:
        return self.book().pack_for(pack_id)

    def get_view(self, view_id: Any) -> PackView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records traced for the ledger target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> PackBook:
    if source is None:
        return load_pack()
    if isinstance(source, PackBook):
        return source
    if isinstance(source, PackRegistry):
        return source.book()
    return build_book(source)


def _heldance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _HELDANCE}


def pack_record(pack: Any, source: Any = None) -> Dict[str, Any]:
    loaded = _check_scope_ref(pack)
    book = _source_book(source) if source is not None else None
    record = {
        "type": "pack_pack",
        "skill": PACK_SLICE,
        "pack_id": loaded.pack_id,
        "skill_id": loaded.skill_id,
        "title": loaded.title,
        "segment": segment_of(loaded, book),
        "complete": pack_green(loaded, book),
        "gaps": list(pack_gaps(loaded, book)),
    }
    record.update(_heldance_record(loaded))
    return record


def skill_record(ref: Any) -> Dict[str, Any]:
    loaded = _check_skill_ref(ref)
    record = {
        "type": "pack_run",
        "skill": PACK_SLICE,
        "skill_id": loaded.skill_id,
        "title": loaded.title,
        "state": loaded.state, "scope": loaded.scope,
    }
    record.update(_heldance_record(loaded))
    return record


def trace_record(record_in: Any) -> Dict[str, Any]:
    loaded = _check_trace_ref(record_in)
    record = {
        "type": "pack_trace",
        "skill": PACK_SLICE,
        "trace_id": loaded.trace_id,
        "pack_id": loaded.pack_id,
        "trace": loaded.trace,
    }
    record.update(_heldance_record(loaded))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    loaded = _check_view_ref(view)
    record = {
        "type": "pack_view",
        "skill": PACK_SLICE,
        "view_id": loaded.view_id, "seq": loaded.seq,
        "view_filter": loaded.view_filter,
    }
    record.update(_heldance_record(loaded))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    loaded = _check_note_ref(record_in)
    record = {
        "type": "pack_note",
        "skill": PACK_SLICE,
        "note_id": loaded.note_id,
        "pack_id": loaded.pack_id,
        "stance": loaded.stance,
    }
    record.update(_heldance_record(loaded))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    loaded = validate_panel(panel, source)
    record = {"type": "pack_panel",
              "skill": PACK_SLICE}
    record.update(loaded.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, PackVerdict):
        loaded = validate_verdict(verdict, source)
    else:
        loaded = derive_verdict(_source_book(verdict), view)
    record = {"type": "pack_verdict",
              "skill": PACK_SLICE}
    record.update(loaded.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, PackIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "pack_index",
              "skill": PACK_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    loaded = _source_book(book)
    record = {"type": "pack_book",
              "skill": PACK_SLICE,
              "title": loaded.title}
    record.update(loaded.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(pack: Any, source: Any = None) -> str:
    loaded = _check_scope_ref(pack)
    return (
        f"{loaded.title} - from {loaded.skill_id}: "
        f"stage {loaded.stage if loaded.stage else 'none'}, "
        f"claims "
        f"{', '.join(loaded.claims) if loaded.claims else 'none'}. "
        f"{loaded.detail}")


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The packs stand {verdict.verdict}: "
        f"{verdict.green_shown} of {verdict.total_shown} shown "
        f"packs stand complete.")


def view_plain_words(view: Any) -> str:
    loaded = _check_view_ref(view)
    return f"View {loaded.view_id}: shows {loaded.view_filter} packs."


def note_plain_words(record_in: Any) -> str:
    loaded = _check_note_ref(record_in)
    return (
        f"Note {loaded.note_id}: {loaded.stance} "
        f"{loaded.pack_id}, toward {loaded.target}. "
        f"{loaded.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, PackIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.packs)} green packs; "
        f"red, found in its gaps: {gaps}.")

def format_pack(pack: Any, source: Any = None) -> str:
    loaded = _check_scope_ref(pack)
    book = _source_book(source) if source is not None else None
    lines = [f"{loaded.title} ({loaded.pack_id})"]
    lines.extend(plain_lines(loaded))
    lines.append(loaded.detail)
    if pack_green(loaded, book):
        lines.append(
            "This pack stands complete - it walked the question "
            "sequence in the open from found to held, "
            "and it carries held evidence alone.")
    else:
        lines.append(
            "This pack stands open - it stands found in "
            f"its gaps: {', '.join(pack_gaps(loaded, book))}, and "
            "nothing is invented for it.")
    return "\n".join(lines)

def format_view(view: Any) -> str:
    loaded = _check_view_ref(view)
    return (
        f"View {loaded.view_id}: filter {loaded.view_filter} - "
        f"{loaded.detail}")


def format_note(record_in: Any) -> str:
    loaded = _check_note_ref(record_in)
    lines = [
        f"Pack note {loaded.stance} {loaded.pack_id} "
        f"({loaded.note_id}): {loaded.title}. {loaded.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or pack it builds nothing, executes nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_stage(source: Any, stage: Any) -> str:
    pack = pack_for_check(source, stage)
    if pack is not None:
        return format_pack(pack, source)
    wanted = stage.strip() if isinstance(stage, str) else stage
    return (
        f"No held pack stands under stage {wanted!r} yet - the "
        f"stage reaches nothing in this book, and no pack is "
        f"invented for it.")


def format_book(source: Any = None, skill_id: Any = None) -> str:
    book = _source_book(source)
    packs = (packs_for_skill(book, skill_id)
              if skill_id is not None else book.packs)
    lines = [f"The Skills Standard (M-236) - {book.title}"]
    lines.extend(segment_of(pack, book) for pack in packs)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Pack panel under view {panel.view_id}:"]
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
    lines = ["Pack index, derived from the held packs:"]
    for pack in index.packs:
        lines.append(f"{pack.stage} - {pack.title} ({pack.pack_id})")
    if index.gaps:
        lines.append(
            "Red, found honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "builds nothing, executes nothing and opens no network.")
    return "\n".join(lines)


def format_pack_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "The Skills Standard (M-236)",
        f"{book.title}: {len(book.packs)} packs held, "
        f"{len(green_packs(book))} packs standing green, "
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


def parse_pack_args(args: Any) -> Tuple[str, Any]:
    """Parse the /pack grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("pack", "view", "note"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("stage", "skill"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("index", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
