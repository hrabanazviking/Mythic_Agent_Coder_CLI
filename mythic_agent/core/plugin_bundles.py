"""Cross-app method (roadmap slice M-238).

Part X - Bridges. The roadmap
words: **skills + commands + hooks + agents in one installable bundle with a manifest and provenance; local-first, no store required.******

What already ships, and what this plugin adds:

* Mythic's bridge faces already ship (M-233 consuming, M-234 serving, M-235 the registry, M-236 the skills standard, M-237 the custom commands, ``mythic_agent/core/custom_commands.py`` the nearest kin) and the bundle's citizens already stand as books of their own: skills in the M-236 skills-standard book, commands in the M-237 custom-commands book, hooks in the hook packs and agents as files. This slice builds the plugin bundle that gathers those citizens into ONE installable bundle: skills + commands + hooks + agents held together as data under one manifest, the manifest and the bundle's provenance (where the bundle came from, held as data) declared BEFORE any install is granted, the bundle a local directory and manifest - local-first, no store required, no network opened - with nothing installed and nothing loaded live. The bundles book WIRES that bundle face as data, in its own module, standing in the M-195 copy-and-share
  book book the M-238 book stands in: one tracker
  per book, and the tracker's charge over one
  bundle across its plugin held as a book - a
  bundle. The shipped bundles stand untouched behind
  their seams: this layer holds bundles as data
  over the book's plugins and rewrites none of them,
  and the bundles book keeps its own standing.
  Bundles stand on the ledger AS DATA alone: a
  bundle carries a ledger ref, a reference held in
  this book; holding, viewing or telling a bundle
  plugins no bundle live, moves no keeper and files
  nothing.
* No charter row names this plugin: the M-171 TUI
  redesign charter binds Part VIII alone (M-172
  to M-200) and names M-238 on no row, and the
  plugin tests pin that absence live. The M-005
  method charter names no plugin row either: its
  own words name the whole of Part IX (M-201
  to M-232) as the part that executes the
  charter; Part X stands on the roadmap's own
  words, and this slice is built to those words.

* A bundle is held whole: the plugin it
  answers for, assembled by its plugin id; its title;
  the bundle steps it walked, held as data in
  walk bundle; and the evidence it carries, held
  as data by plugin. The bundle walk is EXPLICIT:
  its sequence stands as data
  (:data:`STAGES`, :data:`TRANSITIONS`) -
  assembled, verified, manifested, installed, held -
  and a bundle's standing is DERIVED at
  call time from its held steps and evidence
  alone: a bundle that opens anywhere but
  assembled, steps where the sequence does not
  allow, carries a bare claim in place of held
  evidence, or has not yet assembled held stands
  open, assembled in its gaps.
* The evidence is a closed vocabulary in two
  halves: the held evidence - manifest_ref,
  skills_ref, commands_ref, hooks_ref, provenance_ref, evidence
  a tracker can point to - and the bare claims -
  feeling, memory, assertion, summary, which
  stand as no evidence at all. A bundle is
  installed from held evidence alone, never
  from a feeling: a bundle holding a
  bare claim stands open, assembled in its gaps.
* A bundle stands only for an ACTIVE
  plugin. The book holds each plugin it answers
  for as a reference record - its id, its title
  and its standing, active or queued, held as
  data copied from the roadmap's own telling. A
  bundle naming a plugin that stands
  nowhere in the book refuses BY NAME, and a
  bundle for a plugin that is not active
  refuses BY NAME beside it: the tracker deals with
  the plugin in hand, in roadmap bundle, never a
  queued one, and a plugin whose bundle already
  stands complete is never manifested twice - the
  current bundle is derived, so a
  completed plugin is never the current bundle
  twice.
* The bundle's trace is visible. A trace
  record holds one bundle's walked steps
  as one trace line, exactly as walked, beside
  the bundle. The derived trace is
  computed at call time from the bundle's
  held steps; a held trace that no longer agrees
  with it stands stale, assembled in the ledger - the
  trace is the walk itself, never a retelling
  of it.
* The bundle index is DERIVED at call
  time from the held bundles - one bundle
  per complete bundle, under the step it
  stands at - never a second stored copy that
  could drift. A stored index, standing verdict,
  panel, trace, bundle or current-bundle
  claim on any record refuses by name.
* The current bundle is DERIVED at call
  time - the first held bundle, in held
  bundle, that does not yet stand complete - never
  stored where it could go stale.
* The notes are held as data: a note record
  naming its bundle, its stance - note,
  concern, praise, question, a closed
  vocabulary - and what it feeds back toward,
  one record per bundle stance; holding
  a note posts none of it, the rule stands as
  data (:data:`BUNDLE_RULE`), and a record
  claiming a bundle was actually held,
  captured or promoted live refuses BY NAME.
  The tracker bundles - and those bundles, too,
  are held as data here, never sent.
* The shipped data file holds one example book
  in exactly the book a real bundle
  file takes, a loader reads a file anywhere on
  disk, bundles and views are verified as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding a bundle book for a session and
  telling from it. This layer reaches no live
  bundle: it writes no bundle live, files nothing
  to the ledger, captures no candidate, promotes
  nothing, spawns no tracker, destroys nothing,
  publishes nothing, sends nothing as the user,
  exposes no secret, weakens no security and
  opens no network - it holds bundles
  as data and tells them.

Honesty rules, enforced here and pinned by tests:

* **The bundle walk is explicit.** A
  bundle is installed against the held
  steps and legal steps alone; an illegal step
  stands assembled in its gaps, never silently
  reordered.
* **Complete stands on held evidence alone.** A
  bundle that carries a feeling, a
  memory, an assertion or a summary in place of
  held evidence stands open, assembled in its gaps:
  a bundle is installed from evidence, not
  vibes.
* **Active plugins only, in roadmap bundle.** A
  bundle for a missing or queued plugin
  refuses by name; no bundle is invented
  for a plugin the tracker has not verified with.
* **Unknown stays unknown.** A bundle
  whose steps are not yet held stands with its
  steps empty - no step is invented.
* **The index, panel, verdict, trace, bundle
  and current bundle are derived, never
  stored.** Each is derived from the held
  bundles at call time; a stored one
  refuses by name, so it can never drift.
* **One bundle per bundle.** Two
  bundles standing for one bundle id
  refuse by name, and one note record stands per
  bundle stance.
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
    "BUNDLE_RESOURCE",
    "BUNDLE_SCHEMA",
    "BUNDLE_SLICE",
    "BUNDLE_RULE",
    "PLAIN_EXPLANATION",
    "THE_BUNDLE_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "COMPLETE_WORDS",
    "PLUGIN_STATES",
    "PROVENANCES",
    "Any",
    "Dict",
    "List",
    "Optional",
    "TraceRecord",
    "BundleRecord",
    "IndexBundle",
    "PluginRef",
    "NoteRecord",
    "BundleBook",
    "BundleIndex",
    "BundlePanel",
    "BundlePanelRow",
    "BundleRegistry",
    "BundleVerdict",
    "BundleView",
    "TargetCount",
    "trace_for_bundle",
    "trace_record",
    "ledger_record",
    "book_record",
    "build_trace",
    "build_book",
    "build_bundle",
    "build_plugin_ref",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "current_bundle",
    "transition_breaks",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "bundle_for_check",
    "bundle_bundle",
    "bundle_record",
    "first_note",
    "format_book",
    "format_bundle",
    "format_index",
    "format_note",
    "format_stage",
    "format_panel",
    "format_bundle_screen",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "plugin_record",
    "load_bundle",
    "load_bundle_file",
    "normalize_plugin_state",
    "normalize_provenance",
    "normalize_stage",
    "normalize_claim_kind",
    "legal_step",
    "next_stage",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_bundle",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_bundle_args",
    "green_bundles",
    "plain_lines",
    "plain_words",
    "roadmap_record",
    "segment_of",
    "trace_of",
    "trace_current",
    "shown_bundles",
    "validate_trace",
    "validate_book",
    "validate_bundle",
    "validate_plugin_ref",
    "validate_note",
    "validate_panel",
    "validate_row",
    "validate_verdict",
    "validate_view",
    "verdict_plain_words",
    "verdict_record",
    "view_plain_words",
    "view_record",
    "bundle_gaps",
    "bundle_green",
    "bundles_for_plugin",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

BUNDLE_SCHEMA = "mythic.plugin_bundles/1"
BUNDLE_SLICE = "M-238"
THE_BUNDLE_SLICE = BUNDLE_SLICE
BUNDLE_RESOURCE = "plugin_bundles.yaml"
INDEX_ACTION = "index"
EXAMPLE_STAGE = "held"
STAGE_FIELDS = ("stages", "claims")
COMPLETE_WORDS = ("complete", "open")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "complete", "open")
VERDICT_WORDS = ("held", "held", "blocked")
PLUGIN_STATES = ("live", "dormant")
PROVENANCES = ("local", "project", "unproven")
BUNDLE_RULE = "bundles are held as data alone: skills + commands + hooks + agents in one installable bundle with a manifest and provenance; local-first, no store required (the provenances local, project and unproven, one provenance held per plugin as data) - one bundle shelf per book, and the shelf charge over one bundle held as a bundle - a bundle stands as data, held by reference (a manifest ref), never installed live - the bundle walk stands as an explicit bundle sequence - assembled, verified, manifested, installed, held - and a bundle completes only complete, complete being a state with evidence held - manifest ref, skills ref, commands ref, hooks ref, agents ref, provenance ref - never a feeling, a memory, an assertion or a summary; skills + commands + hooks + agents in one installable bundle with a manifest and provenance; local-first, no store required - and a bundle installed without manifesting, or held before it is installed, stands open, named in its gaps; a bundle on an unproven plugin stands complete only with its provenance held as a provenance_ref; defining, reading, listing and telling a bundle installs nothing, loads no skill live, runs no command, fires no hook, spawns no agent, opens no network and writes nothing outside held records"
PLAIN_EXPLANATION = "Plugin bundles (M-238): skills + commands + hooks + agents in one installable bundle with a manifest and provenance; local-first, no store required."
USAGE = 'Usage: /pluginbundles | /pluginbundles bundle <bundle-id> | /pluginbundles stage <stage> | /pluginbundles plugin <plugin-id> | /pluginbundles view <view-id> | /pluginbundles note <note-id> | /pluginbundles index | /pluginbundles panel | /pluginbundles verdict'

STAGES = ("assembled", "verified", "manifested", "installed", "held")
HELD_EVIDENCE = ("manifest_ref", "skills_ref", "commands_ref", "hooks_ref", "agents_ref", "provenance_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
CLAIM_KINDS = HELD_EVIDENCE + BARE_CLAIMS
TRANSITIONS = {
    "assembled": ("verified",),
    "verified": ("manifested",),
    "manifested": ("installed",),
    "installed": ("assembled", "held"),
    "held": (),
}


def legal_step(before: Any, after: Any) -> bool:
    """Whether the gate sequence allows one step, DERIVED.

    The machine stands as data in TRANSITIONS:
    inspect steps only to build, build only to
    test, test to repair on a bundle or to
    continue on a pass, repair back to build or
    test for the rerun, and continue steps
    nowhere - it is where a bundle stands complete.
    A stage outside the machine allows nothing.
    """
    return after in TRANSITIONS.get(before, ())


def next_stage(stage: Any, failed: Any = False) -> Optional[str]:
    """The step the tracker takes next, DERIVED from the sequence.

    Banked leads to verified and verified to
    manifested; manifested leads to installed; at
    installed a follow-up banking steps back to assembled and a finished bundle steps to held;
    held is the end of the walk and steps
    nowhere. A step outside the sequence refuses
    by name.
    """
    installed = normalize_stage(stage)
    if installed == "assembled":
        return "verified"
    if installed == "verified":
        return "manifested"
    if installed == "manifested":
        return "installed"
    if installed == "installed":
        return "assembled" if failed else "held"
    return None


_HELDANCE = ("recorded_on", "actor", "source", "origin_session")
_RUN_KEYS = frozenset({
    "bundle_id", "seq", "plugin_id", "title", "stages",
    "claims", "detail",
} | set(_HELDANCE))
_SLICE_REF_KEYS = frozenset({
    "plugin_id", "seq", "title", "state", "provenance", "detail",
} | set(_HELDANCE))
_TRACE_KEYS = frozenset({
    "trace_id", "seq", "bundle_id", "trace", "detail",
} | set(_HELDANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_HELDANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "bundle_id", "stance", "target", "title",
    "detail",
} | set(_HELDANCE))
_DERIVED_KEYS = frozenset({
    "standing", "complete", "greens", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "bundles", "coverage", "covered", "uncovered",
    "current_bundle", "next_bundle", "progress", "ledger",
    "current", "bundle", "breaks", "live"})
_LIVE_KEYS = (
    "live_bundle", "bundles_live", "live_question",
    "bundles_raise", "raises_slice", "raised_live",
    "answers_live", "answers_question", "answered_live",
    "delivers_live", "delivered_live", "bundles_live",
    "resumed_live", "runs_bundle", "paused_live",
    "runs_bundle", "ran_bundle", "spawns_process",
    "spawned_process", "builds_slice", "built_slice",
    "builds_live", "executes_slice", "executed_slice",
    "executes_live", "live_execution",
    "banks_slice", "banked_live", "bundle_live",
    "pushes_slice", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_bundle", "sent_bundle",
    "posts_note", "held_note", "traces_live",
    "traced_live", "writes_ledger", "wrote_ledger", "files_bundle", "filed_live", "spawns_tracker", "spawned_tracker", "sends_bundle", "sent_bundle", "writes_bundle", "wrote_bundle")


# ---------------------------------------------------------------------
# Small judges, in the sibling trace.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_stages(value: Any) -> Tuple[str, ...]:
    """A bundle's walked stages, held as data.

    The stages stand as a list of stage names in
    walk bundle, each one a stage of the explicit
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
    """A bundle's asked claims: claim plugins assembled as data.

    Each claim names one plugin from the held
    vocabulary - the human plugins the gate may ask
    and the code plugins it must never ask, both
    held honestly as data - and a plugin outside
    the vocabulary refuses.
    """
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError("claims must be a list of claim plugins")
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
            out[key] = _clean_text(mapping.get(key), "a recorded_on plugin")
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
                f"{what} claims a live gate bundle or plugin build "
                f"execution ({key!r} is assembled on it): "
                f"{BUNDLE_RULE}")
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


def normalize_plugin_state(value: Any) -> str:
    state = _clean_text(value, "an plugin state").lower()
    if state not in PLUGIN_STATES:
        raise ValueError(
            f"plugin state {state!r} is not one of the held "
            f"states: " + ", ".join(PLUGIN_STATES))
    return state


def normalize_provenance(value: Any) -> str:
    provenance = _clean_text(value, "a provenance").lower()
    if provenance not in PROVENANCES:
        raise ValueError(
            f"provenance {provenance!r} is not one of the "
            f"plugin bundle provenances: " + ", ".join(PROVENANCES))
    return provenance


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
    plugin = _clean_text(value, "a claim plugin").lower()
    if plugin not in CLAIM_KINDS:
        raise ValueError(
            f"claim plugin {plugin!r} is not one of the held "
            f"plugins: " + ", ".join(CLAIM_KINDS))
    return plugin

# ---------------------------------------------------------------------
# The held bundle: one plugin cut from an active plugin.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class BundleRecord:
    """One bundle plugin, held as data.

    The bundle names the active plugin it was
    held from, by plugin id, its title, its
    verifiable stages, held as data, and its
    claims, assembled by bundle id. The grain is
    derived, never stored: exactly one verifiable
    walk is manifested against the machine. A bundle whose
    stages are not yet held stands with its
    stages empty: it stands open, assembled in
    its gaps, and no stage is invented for it.
    The bundle is local data alone - no live build
    stands behind it: holding it builds nothing.
    """

    bundle_id: str
    seq: int
    plugin_id: str
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
            self, "bundle_id", _clean_text(self.bundle_id, "a bundle id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "plugin_id", _clean_text(self.plugin_id, "an plugin id"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a bundle title"))
        object.__setattr__(
            self, "stages", _check_stages(self.stages))
        object.__setattr__(
            self, "claims", _check_claims(self.claims))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a bundle detail"))
        for key in _HELDANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.bundle_id

    @property
    def stage(self) -> str:
        """The stage the bundle stands at: its last walked stage."""
        return self.stages[-1] if self.stages else ""

    def to_record(self) -> Dict[str, Any]:
        record = {
            "bundle_id": self.bundle_id, "seq": self.seq,
            "plugin_id": self.plugin_id, "title": self.title,
            "stages": list(self.stages),
            "claims": list(self.claims),
            "detail": self.detail,
        }
        for key in _HELDANCE:
            record[key] = getattr(self, key)
        return record


def _check_provenance_ref(value: Any) -> BundleRecord:
    if not isinstance(value, BundleRecord):
        raise ValueError("a bundle must be a BundleRecord")
    return value


def validate_bundle(bundle: Any) -> BundleRecord:
    return _check_provenance_ref(bundle)


def build_bundle(record: Any = None, **kwargs: Any) -> BundleRecord:
    """Build one held bundle from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, BundleRecord):
        if kwargs:
            raise ValueError("a bundle stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a bundle must be a mapping or a BundleRecord")
    _needed(data, _RUN_KEYS, "a bundle")
    return BundleRecord(
        bundle_id=data.get("bundle_id"), seq=data.get("seq"),
        plugin_id=data.get("plugin_id"), title=data.get("title"),
        stages=data.get("stages"),
        claims=data.get("claims"),
        detail=data.get("detail"),
        **_heldance(data))


def _breaks_map(book: Any) -> Dict[str, Tuple[str, ...]]:
    """Map each bundle to the steps it took outside the machine.

    Derived from the held bundles alone: a break is
    one consecutive pair of walked stages the
    explicit gate sequence does not allow, told
    in walk bundle as before, then after.
    """
    assembled: Dict[str, Tuple[str, ...]] = {}
    for bundle in book.bundles:
        breaks = tuple(
            f"{before} > {after}"
            for before, after in zip(bundle.stages, bundle.stages[1:])
            if not legal_step(before, after))
        if breaks:
            assembled[bundle.bundle_id] = breaks
    return assembled

def bundle_gaps(bundle: Any, source: Any = None) -> Tuple[str, ...]:
    """The gaps that keep a bundle from standing complete.

    Guarded from the bundle's own held fields alone -
    its walked steps against the explicit question
    sequence, and its held evidence against the
    held vocabulary: the bundle opens at
    assembled, steps only where the sequence
    allows, carries held evidence and no bare claim,
    and a bundle stands complete only when it has
    assembled held. The source names nothing
    further: no gap is borrowed from another
    bundle.
    """
    installed = _check_provenance_ref(bundle)
    gaps: List[str] = []
    if not installed.stages:
        gaps.append(
            "has passed through no step: the bundle has not started")
        return tuple(gaps)
    if installed.stages[0] != "assembled":
        gaps.append(
            f"opens at {installed.stages[0]}, not at assembled: "
            f"the bundle opens with the reflection")
    for before, after in zip(installed.stages, installed.stages[1:]):
        if not legal_step(before, after):
            gaps.append(
                f"steps from {before} to {after}, which the "
                f"bundle sequence does not allow")
    for plugin in installed.claims:
        if plugin in BARE_CLAIMS:
            gaps.append(
                f"carries a {plugin} claim, a bare claim with no "
                f"held proof: complete stands on held proof alone")
    if source is not None:
        try:
            _ref = _source_book(source).slice_for(installed.plugin_id)
        except Exception:
            _ref = None
        if _ref is not None and _ref.provenance == "unproven" and \
                "provenance_ref" not in installed.claims:
            gaps.append(
                "stands installed on an unproven plugin with no "
                "provenance_ref held: the provenance for the "
                "plugin is unproven")
    if installed.stages[-1] != "held":
        gaps.append(
            f"has not reached held: the bundle stands "
            f"at {installed.stages[-1]}")
    return tuple(gaps)

def bundle_green(bundle: Any, source: Any = None) -> bool:
    return not bundle_gaps(bundle, source)


def plain_lines(bundle: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the bundle's own fields."""
    installed = _check_provenance_ref(bundle)
    return (
        f"Bundle: {installed.title}",
        f"Plugin: {installed.plugin_id}",
        f"Stage: {installed.stage if installed.stage else 'none'}",
        f"Claims: "
        f"{', '.join(installed.claims) if installed.claims else 'none'}",
    )


def segment_of(bundle: Any, source: Any = None) -> str:
    installed = _check_provenance_ref(bundle)
    gaps = bundle_gaps(installed, source)
    return (
        f"{installed.bundle_id}: {installed.title} - plugin: "
        f"'{installed.plugin_id}' - stage: "
        f"'{installed.stage if installed.stage else 'none'}' - "
        f"stages: {len(installed.stages)} - claims: "
        f"'{', '.join(installed.claims) if installed.claims else 'none'}' - "
        f"detail: '{installed.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held plugin reference: the active plugin a book bundles from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class PluginRef:
    """One plugin a bundle book bundles from, held as a reference.

    The record names the plugin, the title it
    opens and its standing - active or
    queued - held as data copied from the
    M-203 plugin book's own telling. A bundle
    stands only from an active reference: the
    book refuses a bundle naming no held reference,
    and a bundle from an queued one, BY NAME.
    """

    plugin_id: str
    seq: int
    title: str
    state: str
    provenance: str = "local"
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "plugin_id", _clean_text(self.plugin_id, "an plugin id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a title"))
        object.__setattr__(
            self, "state", normalize_plugin_state(self.state))
        object.__setattr__(
            self, "provenance", normalize_provenance(self.provenance))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an plugin detail"))
        for key in _HELDANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.plugin_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "plugin_id": self.plugin_id, "seq": self.seq,
            "title": self.title, "state": self.state,
            "provenance": self.provenance,
            "detail": self.detail,
        }
        for key in _HELDANCE:
            record[key] = getattr(self, key)
        return record


def _check_plugin_ref(value: Any) -> PluginRef:
    if not isinstance(value, PluginRef):
        raise ValueError("a plugin reference must be an PluginRef")
    return value


def validate_plugin_ref(ref: Any) -> PluginRef:
    return _check_plugin_ref(ref)


def build_plugin_ref(record: Any = None, **kwargs: Any) -> PluginRef:
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, PluginRef):
        if kwargs:
            raise ValueError(
                "a plugin reference stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError(
            "a plugin reference must be a mapping or an PluginRef")
    _needed(data, _SLICE_REF_KEYS, "a plugin reference")
    return PluginRef(
        plugin_id=data.get("plugin_id"), seq=data.get("seq"),
        title=data.get("title"), state=data.get("state"), provenance=data.get("provenance") or "local",
        detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The held trace trace: the human approves the trace, as data.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TraceRecord:
    """One trace trace, held as data.

    The record names its plugin and the trace the
    human active - the plugin's bundle ids in
    derived claim bundle, held exactly as
    active. The trace is of the set and its
    bundle, never of a step: when the derived
    trace moves, this record stands stale, assembled
    in the ledger, until a new trace is active.
    """

    trace_id: str
    seq: int
    bundle_id: str
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
            self, "bundle_id", _clean_text(self.bundle_id, "an plugin id"))
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
            "bundle_id": self.bundle_id, "trace": self.trace,
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
        bundle_id=data.get("bundle_id"), trace=data.get("trace"),
        detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The held stance: a note on a bundle, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One bundle stance, held as data.

    The record names its bundle, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per bundle stance
    in a book. The record is data alone: holding
    it builds nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    bundle_id: str
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
            self, "bundle_id", _clean_text(self.bundle_id, "a bundle id"))
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
            "bundle_id": self.bundle_id, "stance": self.stance,
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
        bundle_id=data.get("bundle_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The held view: which plugins a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class BundleView:
    """A view over the book: every bundle, the green, the rest."""

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


def _check_view_ref(value: Any) -> BundleView:
    if not isinstance(value, BundleView):
        raise ValueError("a view must be an BundleView")
    return value


def validate_view(view: Any) -> BundleView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> BundleView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, BundleView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an BundleView")
    _needed(data, _VIEW_KEYS, "a view")
    return BundleView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class BundlePanelRow:
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


def _row_for_bundle(bundle: BundleRecord,
                     source: Any = None) -> BundlePanelRow:
    return BundlePanelRow(
        item_id=bundle.bundle_id,
        standing="complete" if bundle_green(bundle, source) else "open",
        label=bundle.title, segment=segment_of(bundle, source),
        recorded_on=bundle.recorded_on)


def _check_row_ref(value: Any) -> BundlePanelRow:
    if not isinstance(value, BundlePanelRow):
        raise ValueError("a panel row must be an BundlePanelRow")
    return value


def validate_row(row: Any, bundle: Any = None,
                 source: Any = None) -> BundlePanelRow:
    installed = _check_row_ref(row)
    if bundle is not None:
        derived = _row_for_bundle(_check_provenance_ref(bundle), source)
        if installed != derived:
            raise ValueError(
                f"panel row {installed.item_id!r} does not agree with "
                f"the row derived from its bundle")
    return installed


def build_row(row: Any = None, bundle: Any = None,
              source: Any = None,
              **kwargs: Any) -> BundlePanelRow:
    if bundle is not None:
        derived = _row_for_bundle(_check_provenance_ref(bundle), source)
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            BundlePanelRow(**kwargs))
        return validate_row(built, bundle, source)
    if isinstance(row, BundlePanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in COMPLETE_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return BundlePanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on plugin"))
    if row is None and kwargs:
        return BundlePanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an BundlePanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[BundlePanelRow, ...]
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
        f"The bundle book holds {total_items} bundles as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {green_shown} of the shown bundles "
        f"stand complete.",
        "Rows stand in held bundle, the bundle the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its bundle's own fields "
        "- the plugin it answers for, the steps it walked in the "
        "open and the evidence it honestly carries - and no "
        "judgement is stored on any bundle.",
        "Completeness is manifested from the held records alone: "
        "a bundle that steps outside the bundle sequence, "
        "carries a bare claim in place of held evidence, or has "
        "not assembled held stands open, assembled in its "
        "gaps, and the bundle index is derived from the "
        "held bundles, never stored where it could drift.",
    )

@dataclass(frozen=True)
class BundlePanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[BundlePanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> BundleView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, BundleView):
        return view
    return book.view_for(view)


def shown_bundles(source: Any, view: Any = None
                   ) -> Tuple[BundleRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.bundles
    if resolved.view_filter == "complete":
        return tuple(g for g in book.bundles if bundle_green(g, book))
    return tuple(g for g in book.bundles if not bundle_green(g, book))


def bundles_for_plugin(source: Any, plugin_id: Any
                      ) -> Tuple[BundleRecord, ...]:
    wanted = _clean_text(plugin_id, "an plugin id")
    return tuple(
        g for g in _source_book(source).bundles if g.plugin_id == wanted)


def green_bundles(source: Any) -> Tuple[BundleRecord, ...]:
    book = _source_book(source)
    return tuple(g for g in book.bundles if bundle_green(g, book))


def current_bundle(source: Any) -> Optional[BundleRecord]:
    """The book's current bundle, DERIVED at call time.

    The first held bundle, in held bundle, that does
    not yet stand complete - where the Architect must
    look next. Nothing here is stored: the telling
    is derived from the held bundles alone, so it can
    never go stale against them. A book whose every
    bundle stands complete has no current bundle.
    """
    book = _source_book(source)
    for bundle in book.bundles:
        if not bundle_green(bundle, book):
            return bundle
    return None


def derive_panel(source: Any, view: Any = None) -> BundlePanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_bundles(book, resolved)
    rows = tuple(_row_for_bundle(bundle, book) for bundle in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.bundles), default="")
    green = sum(1 for g in shown if bundle_green(g, book))
    return BundlePanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.bundles), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.bundles), len(shown), green, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> BundlePanel:
    if not isinstance(value, BundlePanel):
        raise ValueError("a panel must be an BundlePanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> BundlePanel:
    """Judge a stored panel against the panel derived from its book.

    Every derived field must agree; the stored
    panel's own name is its identity, not derived
    content (the M-182 bundle).
    """
    installed = _check_panel_ref(panel)
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(installed.view_id)
                if installed.view_id is not None else None)
        derived = derive_panel(book, view)
        for attr in ("view_id", "view_filter", "rows", "total_items",
                     "total_shown", "target_counts", "as_of", "account"):
            if getattr(installed, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {installed.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return installed


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> BundlePanel:
    if isinstance(panel, BundlePanel):
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
        built = BundlePanel(
            panel_id=_clean_text(data.get("panel_id"), "a panel id"),
            view_id=data.get("view_id"),
            view_filter=normalize_view_filter(data.get("view_filter")),
            rows=rows,
            total_items=_check_count(
                data.get("total_items"), "a total_items count"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            target_counts=counts,
            as_of=_clean_text(data.get("as_of"), "an as_of plugin"),
            account=_check_lines(data.get("account"), "the account"))
        return validate_panel(built, source)
    if panel is None and source is not None:
        return derive_panel(source, kwargs.get("view"))
    raise ValueError("a panel must be a mapping, an BundlePanel, or derived")


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
class BundleVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> BundleVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_bundles(book, resolved)
    green = sum(1 for g in shown if bundle_green(g, book))
    latest = max((g.recorded_on for g in shown), default="")
    return BundleVerdict(
        verdict=_verdict_word(len(shown), green),
        view_id=resolved.view_id, total_shown=len(shown),
        green_shown=green, latest_on=latest)


def _check_verdict_ref(value: Any) -> BundleVerdict:
    if not isinstance(value, BundleVerdict):
        raise ValueError("a verdict must be an BundleVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> BundleVerdict:
    installed = _check_verdict_ref(verdict)
    if installed.verdict not in VERDICT_WORDS:
        raise ValueError(f"verdict {installed.verdict!r} is not a held word")
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(installed.view_id)
                if installed.view_id is not None else None)
        derived = derive_verdict(book, view)
        if installed != derived:
            raise ValueError(
                "the stored verdict disagrees with the verdict "
                "derived from its book")
    return installed


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> BundleVerdict:
    if isinstance(verdict, BundleVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = BundleVerdict(
            verdict=_clean_text(data.get("verdict"), "a verdict"),
            view_id=data.get("view_id"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            green_shown=_check_count(
                data.get("green_shown"), "a green_shown count"),
            latest_on=_clean_text(data.get("latest_on"), "a latest plugin"))
        return validate_verdict(built, source)
    if verdict is None and source is not None:
        return derive_verdict(source, kwargs.get("view"))
    raise ValueError(
        "a verdict must be a mapping, an BundleVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held plugins' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexBundle:
    stage: str
    bundle_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "stage": self.stage, "bundle_id": self.bundle_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class BundleIndex:
    """The bundle index, derived from the held bundles.

    The index names one bundle per green bundle, in
    held bundle - the bundle's own one verifiable
    stage, its bundle id and its title - and the
    bundles that do not stand complete, assembled in its
    gaps. Nothing here is stored on any bundle: the
    index is derived at call time from the held
    records alone, so it can never drift from them.
    """

    bundles: Tuple[IndexBundle, ...]
    gaps: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "bundles": [e.to_record() for e in self.bundles],
            "gaps": list(self.gaps),
        }


def derive_index(source: Any) -> BundleIndex:
    """Derive the bundle index from the book's held bundles."""
    book = _source_book(source)
    bundles = tuple(
        IndexBundle(stage=g.stage, bundle_id=g.bundle_id,
                   title=g.title)
        for g in book.bundles if bundle_green(g, book))
    gaps = tuple(
        g.bundle_id for g in book.bundles if not bundle_green(g, book))
    return BundleIndex(bundles=bundles, gaps=gaps)


def bundle_for_check(source: Any, stage: Any) -> Optional[BundleRecord]:
    """The first held bundle one stage reaches, or none - honestly."""
    if stage is None:
        return None
    if not isinstance(stage, str):
        raise ValueError("an stage must be a string naming the stage")
    wanted = stage.strip()
    if not wanted:
        return None
    for bundle in _source_book(source).bundles:
        if bundle.stage == wanted:
            return bundle
    return None


def transition_breaks(source: Any) -> Tuple[str, ...]:
    """Every step outside the gate sequence, DERIVED.

    One telling per break, in held bundle: the bundle
    that took it and the step it took, before,
    then after. A book whose bundles all walk inside
    the machine tells none.
    """
    book = _source_book(source)
    return tuple(
        f"{bundle_id}: {step}"
        for bundle_id, steps in _breaks_map(book).items()
        for step in steps)

def bundle_bundle(source: Any,
              plugin_id: Any = None) -> Tuple[BundleRecord, ...]:
    """The held bundles in their held bundle, DERIVED at call time.

    Bundles stand in the bundle the book holds them -
    the bundle their plugins were assembled - optionally
    for one plugin alone. Nothing here is stored:
    the bundle is the book's own held bundle, told.
    """
    book = _source_book(source)
    bundles = list(book.bundles)
    if plugin_id is not None:
        wanted = _clean_text(plugin_id, "a plugin id")
        bundles = [r for r in bundles if r.plugin_id == wanted]
    return tuple(bundles)

def trace_of(source: Any, bundle_id: Any) -> str:
    """One bundle's trace, DERIVED at call time.

    The bundle's walked stages installed as one trace
    line, in walk bundle. A bundle that has walked
    nowhere traces empty: the trace tells only
    what stands walked, and the walk is assembled
    elsewhere.
    """
    bundle = _source_book(source).bundle_for(bundle_id)
    return " > ".join(bundle.stages)

def trace_for_bundle(source: Any,
                  bundle_id: Any) -> Optional[TraceRecord]:
    """The held trace for one bundle, or none - honestly."""
    wanted = _clean_text(bundle_id, "a bundle id")
    for record in _source_book(source).traces:
        if record.bundle_id == wanted:
            return record
    return None

def trace_current(source: Any, bundle_id: Any) -> bool:
    """Whether the held trace agrees with the derived trace.

    The trace stands current only while the trace
    it holds is the trace the book derives now; a
    moved walk leaves it stale, and no trace at
    all traces nothing.
    """
    trace = trace_for_bundle(source, bundle_id)
    if trace is None:
        return False
    return trace.trace == trace_of(source, bundle_id)

def note_for_bundle(source: Any, bundle_id: Any,
                   stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one bundle (and stance, when assembled)."""
    wanted = _clean_text(bundle_id, "a bundle id")
    for record in _source_book(source).notes:
        if record.bundle_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the plugin targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


def ledger_record(source: Any = None) -> Dict[str, Any]:
    """The bundle ledger, DERIVED here from the held bundles alone.

    The ledger counts the held bundles by their
    derived completeness - green and red - names
    the current bundle, the first that does not yet
    stand complete, tells each held bundle's trace
    standing - current while its held trace
    agrees with its derived trace, stale when it
    has moved, unheld while no trace stands for
    it - and names every step the held bundles took
    outside the gate sequence. Nothing here is
    stored: the telling is derived at call time.
    """
    book = _source_book(source)
    standings = []
    for standing in COMPLETE_WORDS:
        number = sum(
            1 for g in book.bundles
            if ("complete" if bundle_green(g, book) else "open") == standing)
        standings.append({"standing": standing, "bundle_records": number})
    current = current_bundle(book)
    traces = []
    for bundle in book.bundles:
        trace = trace_for_bundle(book, bundle.bundle_id)
        if trace is None:
            standing = "unheld"
        elif trace_current(book, bundle.bundle_id):
            standing = "current"
        else:
            standing = "stale"
        traces.append({"bundle_id": bundle.bundle_id, "trace": standing})
    return {
        "type": "bundle_well",
        "plugin": BUNDLE_SLICE,
        "standings": standings,
        "total": len(book.bundles),
        "current_bundle": current.bundle_id if current is not None else None,
        "traces": traces,
        "breaks": list(transition_breaks(book)),
    }

def roadmap_record() -> Dict[str, Any]:
    """This plugin's own roadmap standing, proved from the roadmap itself.

    The record loads this plugin's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 plugins in 11 parts,
    the assembled prefix, the next plugin where the
    bundle bundles, and M-238's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(BUNDLE_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "bundle_roadmap",
        "plugin": BUNDLE_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m238_title": own.title,
        "m238_part": own.part,
        "m238_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: plugins, bundles, views, notes and trace traces held
# together, one pinned panel at most per telling, and no verdict,
# index, trace or bundle ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class BundleBook:
    title: str
    plugins: Tuple[PluginRef, ...] = ()
    bundles: Tuple[BundleRecord, ...] = ()
    views: Tuple[BundleView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    traces: Tuple[TraceRecord, ...] = ()
    panels: Tuple[BundlePanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        plugins = tuple(_check_plugin_ref(g) for g in self.plugins)
        bundles = tuple(_check_provenance_ref(g) for g in self.bundles)
        views = tuple(_check_view_ref(v) for v in self.views)
        notes = tuple(_check_note_ref(m) for m in self.notes)
        traces = tuple(_check_trace_ref(a) for a in self.traces)
        panels = tuple(_check_panel_ref(pn) for pn in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for ref in plugins:
            if ref.plugin_id in seen_ids:
                raise ValueError(
                    f"two plugin references stand under id {ref.plugin_id!r}")
            if ref.seq in seen_seqs:
                raise ValueError(
                    f"two plugin references stand at sequence {ref.seq}")
            seen_ids.add(ref.plugin_id)
            seen_seqs.add(ref.seq)
        bundle_ids = set()
        bundle_seqs = set()
        for bundle in bundles:
            if bundle.bundle_id in bundle_ids:
                raise ValueError(
                    f"two bundles stand under id {bundle.bundle_id!r}")
            if bundle.seq in bundle_seqs:
                raise ValueError(
                    f"two bundles stand at sequence {bundle.seq}")
            bundle_ids.add(bundle.bundle_id)
            bundle_seqs.add(bundle.seq)
        by_slice = {ref.plugin_id: ref for ref in plugins}
        for bundle in (bundles if plugins else ()):

            ref = by_slice.get(bundle.plugin_id)
            if ref is None:
                raise ValueError(
                    f"bundle {bundle.bundle_id!r} is held from plugin "
                    f"{bundle.plugin_id!r}, which stands nowhere in "
                    f"this book")
            if ref.state != "live":
                raise ValueError(
                    f"bundle {bundle.bundle_id!r} is held from plugin "
                    f"{bundle.plugin_id!r}, which is not active: "
                    f"no plugin is held from an queued plugin")
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
            target = (record.bundle_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for bundle "
                    f"{record.bundle_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per bundle target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        trace_ids = set()
        trace_seqs = set()
        trace_bundles = set()
        bundle_ids = {bundle.bundle_id for bundle in bundles}
        for record in traces:
            if record.trace_id in trace_ids:
                raise ValueError(
                    f"two traces stand under id {record.trace_id!r}")
            if record.seq in trace_seqs:
                raise ValueError(
                    f"two traces stand at sequence {record.seq}")
            if record.bundle_id in trace_bundles:
                raise ValueError(
                    f"two traces stand for bundle "
                    f"{record.bundle_id!r}: one trace stands "
                    f"per bundle walk")
            if bundles and record.bundle_id not in bundle_ids:
                raise ValueError(
                    f"trace {record.trace_id!r} traces bundle "
                    f"{record.bundle_id!r}, which stands nowhere in "
                    f"this book")
            trace_ids.add(record.trace_id)
            trace_seqs.add(record.seq)
            trace_bundles.add(record.bundle_id)
        object.__setattr__(
            self, "plugins", tuple(sorted(plugins, key=lambda g: g.seq)))
        object.__setattr__(
            self, "bundle_records", tuple(sorted(bundles, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(
            self, "traces",
            tuple(sorted(traces, key=lambda a: a.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.bundles + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.bundle_id for g in self.bundles) + tuple(
            v.view_id for v in self.views)

    def bundle_ids(self) -> Tuple[str, ...]:
        return tuple(g.bundle_id for g in self.bundles)

    def plugin_ids(self) -> Tuple[str, ...]:
        return tuple(g.plugin_id for g in self.plugins)

    def bundle_for(self, bundle_id: Any) -> BundleRecord:
        wanted = _clean_text(bundle_id, "a bundle id")
        for bundle in self.bundles:
            if bundle.bundle_id == wanted:
                return bundle
        raise KeyError(f"no bundle assembled {wanted!r} stands in this book")

    def slice_for(self, plugin_id: Any) -> PluginRef:
        wanted = _clean_text(plugin_id, "an plugin id")
        for ref in self.plugins:
            if ref.plugin_id == wanted:
                return ref
        raise KeyError(f"no plugin assembled {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> BundleView:
        wanted = _clean_text(view_id, "a view id")
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no view assembled {wanted!r} stands in this book")

    def note_for(self, note_id: Any) -> NoteRecord:
        wanted = _clean_text(note_id, "a stance id")
        for record in self.notes:
            if record.note_id == wanted:
                return record
        raise KeyError(f"no stance assembled {wanted!r} stands in this book")

    def trace_for(self, trace_id: Any) -> TraceRecord:
        wanted = _clean_text(trace_id, "an trace id")
        for record in self.traces:
            if record.trace_id == wanted:
                return record
        raise KeyError(f"no trace assembled {wanted!r} stands in this book")

    def item_for(self, item_id: Any) -> Any:
        wanted = _clean_text(item_id, "an item id")
        for bundle in self.bundles:
            if bundle.bundle_id == wanted:
                return bundle
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item assembled {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "plugins": [g.to_record() for g in self.plugins],
            "bundle_records": [g.to_record() for g in self.bundles],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "traces": [a.to_record() for a in self.traces],
            "panels": [pn.to_record() for pn in self.panels],
        }


def _judge_book_panels(book: BundleBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: BundleBook) -> None:
    if book.title != "Plugin bundles at the M-238 slice run":
        raise ValueError("the shipped example book carries another title")
    if len(book.plugins) != 3 or len(book.bundles) != 5 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold three plugin references, five bundles and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.traces) != 1:
        raise ValueError("the shipped example book must hold one trace record")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-plugin":
        raise ValueError("the pinned panel is panel-plugin")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "held" or verdict.green_shown != 3:
        raise ValueError("the shipped example book verdict must stand held at three complete of five")
    index = derive_index(book)
    if [e.stage for e in index.bundles] != ["held", "held", "held"]:
        raise ValueError("the shipped example book index must derive the three held complete bundles in held bundle")
    if index.gaps != ("bundle-bare-bundle", "bundle-leaping-bundle"):
        raise ValueError("the shipped example book must leave the bare and leaping bundles honestly open, assembled in its gaps")
    assembled = bundle_for_check(book, EXAMPLE_STAGE)
    if assembled is None or assembled.bundle_id != "bundle-held-bundle":
        raise ValueError("the shipped example book must reach its opening bundle under the example stage")
    if trace_of(book, "bundle-held-bundle") != "assembled > verified > manifested > installed > held":
        raise ValueError("the shipped example book must derive the opening bundle's trace from its walked steps")
    if not trace_current(book, "bundle-held-bundle"):
        raise ValueError("the shipped example book must hold the opening bundle's trace current")
    first = first_note(book)
    if first is None or first.note_id != "note-note-first":
        raise ValueError("the shipped example book must hold the opening note as its first note bundle")

def validate_book(data: Any, *, require_example: bool = False) -> BundleBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, BundleBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a bundle book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live plugin build or execution "
                f"({key!r} is assembled on it): {BUNDLE_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its bundles under a view")
    if "bundle_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held bundles at call time")
    if "ledger" in data or "current_bundle" in data:
        raise ValueError(
            "a book stores no ledger and no current bundle: both are "
            "derived from its held bundles at call time")
    if "trace" in data or "bundle" in data:
        raise ValueError(
            "a book stores no trace and no bundle: both are derived "
            "from its held bundles at call time; an trace record "
            "holds the trace the human active")
    if data.get("schema") is not None and (
            data["schema"] != BUNDLE_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{BUNDLE_SCHEMA!r}")
    if data.get("plugin") is not None and (
            data["plugin"] != BUNDLE_SLICE):
        raise ValueError(
            f"a book's plugin must be {BUNDLE_SLICE!r}")
    head = data.get("bundle_head") or data.get("plugin_bundles") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's bundle head must be a mapping")
    title = head.get("title") or data.get("title")
    plugins = tuple(build_plugin_ref(g) for g in data.get("plugins") or ())
    bundles = tuple(build_bundle(g) for g in data.get("bundle_records") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    traces = tuple(build_trace(a) for a in data.get("traces") or ())
    book = BundleBook(
        title=title, plugins=plugins, bundles=bundles, views=views,
        notes=notes, traces=traces, panels=())
    panels = tuple(
        build_panel(pn, book) for pn in data.get("panels") or ())
    book = BundleBook(
        title=book.title, plugins=book.plugins, bundles=book.bundles,
        views=book.views, notes=book.notes,
        traces=book.traces, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> BundleBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (BundleBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an BundleBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> BundleBook:
    return validate_book(data, require_example=require_example)


def load_bundle(
        data: Optional[Dict[str, Any]] = None) -> BundleBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(BUNDLE_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_bundle_file(path: Any) -> BundleBook:
    """Load one bundle file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: plugin references, bundles and views held one by one.
# ---------------------------------------------------------------------

class BundleRegistry:
    """An in-memory holding of plugin references, bundles and views.

    The registry is the pure layer's model of a
    session's bundle book: plugin references are
    held under their ids, bundles are held under
    their ids, one bundle per id and per sequence,
    and views are held in verified bundle, one view
    per sequence and per id. Holding is data only -
    nothing held here builds anything, executes
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._slices: List[PluginRef] = []
        self._bundles: List[BundleRecord] = []
        self._views: List[BundleView] = []
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

    def register_plugin_ref(self, item: Any) -> PluginRef:
        """Hold one plugin reference, manifested whole before held."""
        installed = _check_plugin_ref(item)
        return self._register(
            self._slices, installed, "plugin_id", "plugin reference")

    def register_bundle(self, item: Any) -> BundleRecord:
        """Hold one bundle, manifested whole before held."""
        installed = _check_provenance_ref(item)
        return self._register(
            self._bundles, installed, "bundle_id", "bundle")

    def register_view(self, view: Any) -> BundleView:
        """Hold one view; a view naming no id takes a fresh one."""
        installed = _check_view_ref(view)
        if not installed.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            installed = build_view({**installed.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, installed, "view_id", "view")

    def register_book(self, book: Any) -> BundleBook:
        """Hold a whole book's records, under its title."""
        installed = build_book(book)
        if self._title is not None and installed.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {installed.title!r}")
        for ref in installed.plugins:
            self.register_plugin_ref(ref)
        for bundle in installed.bundles:
            self.register_bundle(bundle)
        for view in installed.views:
            self.register_view(view)
        self._title = installed.title
        return self.book()

    def book(self) -> BundleBook:
        return BundleBook(
            title=self._title or "An unheld bundle book",
            plugins=tuple(self._slices), bundles=tuple(self._bundles),
            views=tuple(self._views), notes=(), traces=(), panels=())

    def list_slices(self) -> Tuple[PluginRef, ...]:
        return tuple(self._slices)

    def list_bundles(self) -> Tuple[BundleRecord, ...]:
        return tuple(self._bundles)

    def list_views(self) -> Tuple[BundleView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._bundles) + tuple(self._views)

    def get_slice(self, plugin_id: Any) -> PluginRef:
        return self.book().slice_for(plugin_id)

    def get_bundle(self, bundle_id: Any) -> BundleRecord:
        return self.book().bundle_for(bundle_id)

    def get_view(self, view_id: Any) -> BundleView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records traced for the ledger target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> BundleBook:
    if source is None:
        return load_bundle()
    if isinstance(source, BundleBook):
        return source
    if isinstance(source, BundleRegistry):
        return source.book()
    return build_book(source)


def _heldance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _HELDANCE}


def bundle_record(bundle: Any, source: Any = None) -> Dict[str, Any]:
    installed = _check_provenance_ref(bundle)
    book = _source_book(source) if source is not None else None
    record = {
        "type": "bundle_bundle",
        "plugin": BUNDLE_SLICE,
        "bundle_id": installed.bundle_id,
        "plugin_id": installed.plugin_id,
        "title": installed.title,
        "segment": segment_of(installed, book),
        "complete": bundle_green(installed, book),
        "gaps": list(bundle_gaps(installed, book)),
    }
    record.update(_heldance_record(installed))
    return record


def plugin_record(ref: Any) -> Dict[str, Any]:
    installed = _check_plugin_ref(ref)
    record = {
        "type": "bundle_run",
        "plugin": BUNDLE_SLICE,
        "plugin_id": installed.plugin_id,
        "title": installed.title,
        "state": installed.state, "provenance": installed.provenance,
    }
    record.update(_heldance_record(installed))
    return record


def trace_record(record_in: Any) -> Dict[str, Any]:
    installed = _check_trace_ref(record_in)
    record = {
        "type": "bundle_trace",
        "plugin": BUNDLE_SLICE,
        "trace_id": installed.trace_id,
        "bundle_id": installed.bundle_id,
        "trace": installed.trace,
    }
    record.update(_heldance_record(installed))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    installed = _check_view_ref(view)
    record = {
        "type": "bundle_view",
        "plugin": BUNDLE_SLICE,
        "view_id": installed.view_id, "seq": installed.seq,
        "view_filter": installed.view_filter,
    }
    record.update(_heldance_record(installed))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    installed = _check_note_ref(record_in)
    record = {
        "type": "bundle_note",
        "plugin": BUNDLE_SLICE,
        "note_id": installed.note_id,
        "bundle_id": installed.bundle_id,
        "stance": installed.stance,
    }
    record.update(_heldance_record(installed))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    installed = validate_panel(panel, source)
    record = {"type": "bundle_panel",
              "plugin": BUNDLE_SLICE}
    record.update(installed.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, BundleVerdict):
        installed = validate_verdict(verdict, source)
    else:
        installed = derive_verdict(_source_book(verdict), view)
    record = {"type": "bundle_verdict",
              "plugin": BUNDLE_SLICE}
    record.update(installed.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, BundleIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "bundle_index",
              "plugin": BUNDLE_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    installed = _source_book(book)
    record = {"type": "bundle_book",
              "plugin": BUNDLE_SLICE,
              "title": installed.title}
    record.update(installed.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(bundle: Any, source: Any = None) -> str:
    installed = _check_provenance_ref(bundle)
    return (
        f"{installed.title} - from {installed.plugin_id}: "
        f"stage {installed.stage if installed.stage else 'none'}, "
        f"claims "
        f"{', '.join(installed.claims) if installed.claims else 'none'}. "
        f"{installed.detail}")


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The bundles stand {verdict.verdict}: "
        f"{verdict.green_shown} of {verdict.total_shown} shown "
        f"bundles stand complete.")


def view_plain_words(view: Any) -> str:
    installed = _check_view_ref(view)
    return f"View {installed.view_id}: shows {installed.view_filter} bundles."


def note_plain_words(record_in: Any) -> str:
    installed = _check_note_ref(record_in)
    return (
        f"Note {installed.note_id}: {installed.stance} "
        f"{installed.bundle_id}, toward {installed.target}. "
        f"{installed.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, BundleIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.bundles)} green bundles; "
        f"red, assembled in its gaps: {gaps}.")

def format_bundle(bundle: Any, source: Any = None) -> str:
    installed = _check_provenance_ref(bundle)
    book = _source_book(source) if source is not None else None
    lines = [f"{installed.title} ({installed.bundle_id})"]
    lines.extend(plain_lines(installed))
    lines.append(installed.detail)
    if bundle_green(installed, book):
        lines.append(
            "This bundle stands complete - it walked the question "
            "sequence in the open from assembled to held, "
            "and it carries held evidence alone.")
    else:
        lines.append(
            "This bundle stands open - it stands assembled in "
            f"its gaps: {', '.join(bundle_gaps(installed, book))}, and "
            "nothing is invented for it.")
    return "\n".join(lines)

def format_view(view: Any) -> str:
    installed = _check_view_ref(view)
    return (
        f"View {installed.view_id}: filter {installed.view_filter} - "
        f"{installed.detail}")


def format_note(record_in: Any) -> str:
    installed = _check_note_ref(record_in)
    lines = [
        f"Bundle note {installed.stance} {installed.bundle_id} "
        f"({installed.note_id}): {installed.title}. {installed.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or bundle it builds nothing, executes nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_stage(source: Any, stage: Any) -> str:
    bundle = bundle_for_check(source, stage)
    if bundle is not None:
        return format_bundle(bundle, source)
    wanted = stage.strip() if isinstance(stage, str) else stage
    return (
        f"No held bundle stands under stage {wanted!r} yet - the "
        f"stage reaches nothing in this book, and no bundle is "
        f"invented for it.")


def format_book(source: Any = None, plugin_id: Any = None) -> str:
    book = _source_book(source)
    bundles = (bundles_for_plugin(book, plugin_id)
              if plugin_id is not None else book.bundles)
    lines = [f"The Plugin Bundles (M-238) - {book.title}"]
    lines.extend(segment_of(bundle, book) for bundle in bundles)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Bundle panel under view {panel.view_id}:"]
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
    lines = ["Bundle index, derived from the held bundles:"]
    for bundle in index.bundles:
        lines.append(f"{bundle.stage} - {bundle.title} ({bundle.bundle_id})")
    if index.gaps:
        lines.append(
            "Red, assembled honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "builds nothing, executes nothing and opens no network.")
    return "\n".join(lines)


def format_bundle_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "The Plugin Bundles (M-238)",
        f"{book.title}: {len(book.bundles)} bundles held, "
        f"{len(green_bundles(book))} bundles standing green, "
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


def parse_bundle_args(args: Any) -> Tuple[str, Any]:
    """Parse the /bundle grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("bundle", "view", "note"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("stage", "plugin"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("index", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
