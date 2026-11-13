"""Cross-app method (roadmap slice M-242).

Part X - Bridges. The roadmap
words: **repos, issues, and PRs on Volmarr's own forge with the same craft as GitHub's (Part IV), once Samverk's own road provides the surfaces.******

What already ships, and what this repo adds:

* Mythic's forge faces already ship (M-233 consuming, M-234 serving, M-235 the registry, M-236 the skills standard, M-237 the custom commands, M-238 the installable bundles, M-239 the VS Code family companions book, M-240 the generic companions book, M-241 the rival importers book, ``mythic_agent/core/rival_importers.py`` the nearest kin) and the seams this slice answers already stand in the tree: the GitHub roads (``mythic_agent/integrations/github.py``, with the Part IV PR craft of M-082) carry repos, issues and PRs on GitHub with the house craft, and the M-083 issue-to-slice book (``mythic_agent/core/issue_slice.py``) names Samverk as its second issue source, refusing honestly until Part X provides the surfaces - this slice is that provision's book: repos, issues and PRs on Volmarr's own forge held to the same craft as GitHub's, each piece of forge work held as data under one exchange record, the repo, issue, pr, review and craft declared BEFORE any standing is granted, the exchange a local record - Samverk's own road provides the surfaces as data here - with no socket opened to the forge and no issue or PR filed live. The bridge book WIRES that forge face as data, in its own module, standing in the M-195 copy-and-share
  book book the M-242 book stands in: one tracker
  per book, and the tracker's charge over one
  exchange across its repo held as a book - a
  exchange. The shipped exchanges stand untouched behind
  their seams: this layer holds exchanges as data
  over the book's repos and rewrites none of them,
  and the exchanges book keeps its own standing.
  Exchanges stand on the ledger AS DATA alone: a
  exchange carries a ledger ref, a reference held in
  this book; holding, viewing or telling a exchange
  repos no exchange live, moves no keeper and files
  nothing.
* No charter row names this repo: the M-171 TUI
  redesign charter binds Part VIII alone (M-172
  to M-200) and names M-242 on no row, and the
  repo tests pin that absence live. The M-005
  method charter names no repo row either: its
  own words name the whole of Part IX (M-201
  to M-232) as the part that executes the
  charter; Part X stands on the roadmap's own
  words, and this slice is built to those words.

* A exchange is held whole: the repo it
  answers for, opened by its repo id; its title;
  the exchange steps it walked, held as data in
  walk exchange; and the evidence it carries, held
  as data by repo. The exchange walk is EXPLICIT:
  its sequence stands as data
  (:data:`STAGES`, :data:`TRANSITIONS`) -
  opened, triaged, crafted, reviewed, held -
  and a exchange's standing is DERIVED at
  call time from its held steps and evidence
  alone: a exchange that opens anywhere but
  opened, steps where the sequence does not
  allow, carries a bare claim in place of held
  evidence, or has not yet opened held stands
  open, opened in its gaps.
* The evidence is a closed vocabulary in two
  halves: the held evidence - repo_ref,
  issue_ref, pr_ref, review_ref, link_ref, evidence
  a tracker can point to - and the bare claims -
  feeling, memory, assertion, summary, which
  stand as no evidence at all. A exchange is
  reviewed from held evidence alone, never
  from a feeling: a exchange holding a
  bare claim stands open, opened in its gaps.
* A exchange stands only for an ACTIVE
  repo. The book holds each repo it answers
  for as a reference record - its id, its title
  and its standing, active or queued, held as
  data copied from the roadmap's own telling. A
  exchange naming a repo that stands
  nowhere in the book refuses BY NAME, and a
  exchange for a repo that is not active
  refuses BY NAME beside it: the tracker deals with
  the repo in hand, in roadmap exchange, never a
  queued one, and a repo whose exchange already
  stands complete is never crafted twice - the
  current exchange is derived, so a
  completed repo is never the current exchange
  twice.
* The exchange's trace is visible. A trace
  record holds one exchange's walked steps
  as one trace line, exactly as walked, beside
  the exchange. The derived trace is
  computed at call time from the exchange's
  held steps; a held trace that no longer agrees
  with it stands stale, opened in the ledger - the
  trace is the walk itself, never a retelling
  of it.
* The exchange index is DERIVED at call
  time from the held exchanges - one exchange
  per complete exchange, under the step it
  stands at - never a second stored copy that
  could drift. A stored index, standing verdict,
  panel, trace, exchange or current-exchange
  claim on any record refuses by name.
* The current exchange is DERIVED at call
  time - the first held exchange, in held
  exchange, that does not yet stand complete - never
  stored where it could go stale.
* The notes are held as data: a note record
  naming its exchange, its stance - note,
  concern, praise, question, a closed
  vocabulary - and what it feeds back toward,
  one record per exchange stance; holding
  a note posts none of it, the rule stands as
  data (:data:`EXCHANGE_RULE`), and a record
  claiming a exchange was actually held,
  captured or promoted live refuses BY NAME.
  The tracker exchanges - and those exchanges, too,
  are held as data here, never sent.
* The shipped data file holds one example book
  in exactly the book a real exchange
  file takes, a loader reads a file anywhere on
  disk, exchanges and views are triaged as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding a exchange book for a session and
  telling from it. This layer reaches no live
  exchange: it writes no exchange live, files nothing
  to the ledger, captures no candidate, promotes
  nothing, spawns no tracker, destroys nothing,
  publishes nothing, sends nothing as the user,
  exposes no secret, weakens no security and
  opens no network - it holds exchanges
  as data and tells them.

Honesty rules, enforced here and pinned by tests:

* **The exchange walk is explicit.** A
  exchange is reviewed against the held
  steps and legal steps alone; an illegal step
  stands opened in its gaps, never silently
  reordered.
* **Complete stands on held evidence alone.** A
  exchange that carries a feeling, a
  memory, an assertion or a summary in place of
  held evidence stands open, opened in its gaps:
  a exchange is reviewed from evidence, not
  vibes.
* **Active repos only, in roadmap exchange.** A
  exchange for a missing or queued repo
  refuses by name; no exchange is invented
  for a repo the tracker has not triaged with.
* **Unknown stays unknown.** A exchange
  whose steps are not yet held stands with its
  steps empty - no step is invented.
* **The index, panel, verdict, trace, exchange
  and current exchange are derived, never
  stored.** Each is derived from the held
  exchanges at call time; a stored one
  refuses by name, so it can never drift.
* **One exchange per exchange.** Two
  exchanges standing for one exchange id
  refuse by name, and one note record stands per
  exchange stance.
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
    "EXCHANGE_RESOURCE",
    "EXCHANGE_SCHEMA",
    "EXCHANGE_SLICE",
    "EXCHANGE_RULE",
    "PLAIN_EXPLANATION",
    "THE_EXCHANGE_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "COMPLETE_WORDS",
    "REPO_STATES",
    "LINKS",
    "Any",
    "Dict",
    "List",
    "Optional",
    "TraceRecord",
    "ExchangeRecord",
    "IndexExchange",
    "RepoRef",
    "NoteRecord",
    "ExchangeBook",
    "ExchangeIndex",
    "ExchangePanel",
    "ExchangePanelRow",
    "ExchangeRegistry",
    "ExchangeVerdict",
    "ExchangeView",
    "TargetCount",
    "trace_for_exchange",
    "trace_record",
    "ledger_record",
    "book_record",
    "build_trace",
    "build_book",
    "build_exchange",
    "build_repo_ref",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "current_exchange",
    "transition_breaks",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "exchange_for_check",
    "exchange_exchange",
    "exchange_record",
    "first_note",
    "format_book",
    "format_exchange",
    "format_index",
    "format_note",
    "format_stage",
    "format_panel",
    "format_exchange_screen",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "repo_record",
    "load_exchange",
    "load_exchange_file",
    "normalize_repo_state",
    "normalize_link",
    "normalize_stage",
    "normalize_claim_kind",
    "legal_step",
    "next_stage",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_exchange",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_exchange_args",
    "green_exchanges",
    "plain_lines",
    "plain_words",
    "roadmap_record",
    "segment_of",
    "trace_of",
    "trace_current",
    "shown_exchanges",
    "validate_trace",
    "validate_book",
    "validate_exchange",
    "validate_repo_ref",
    "validate_note",
    "validate_panel",
    "validate_row",
    "validate_verdict",
    "validate_view",
    "verdict_plain_words",
    "verdict_record",
    "view_plain_words",
    "view_record",
    "exchange_gaps",
    "exchange_green",
    "exchanges_for_repo",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

EXCHANGE_SCHEMA = "mythic.samverk_bridge/1"
EXCHANGE_SLICE = "M-242"
THE_EXCHANGE_SLICE = EXCHANGE_SLICE
EXCHANGE_RESOURCE = "samverk_bridge.yaml"
INDEX_ACTION = "index"
EXAMPLE_STAGE = "held"
STAGE_FIELDS = ("stages", "claims")
COMPLETE_WORDS = ("complete", "open")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "complete", "open")
VERDICT_WORDS = ("held", "held", "blocked")
REPO_STATES = ("live", "dormant")
LINKS = ("native", "mirrored", "unlinked")
EXCHANGE_RULE = "exchanges are held as data alone: repos, issues, and PRs on Volmarr's own forge (Samverk) with the same craft as GitHub's Part IV roads (the links native, mirrored and unlinked, one link held per repo as data) - one exchange shelf per book, and the shelf charge over one exchange held as an exchange - an exchange stands as data, held by reference (a repo ref), never run live - the exchange walk stands as an explicit exchange sequence - opened, triaged, crafted, reviewed, held - and an exchange completes only complete, complete being a state with evidence held - repo ref, issue ref, pr ref, review ref, craft ref, link ref - never a feeling, a memory, an assertion or a summary; a credential or key named in a forge record is never claimed held safely - it is refused by name and lands nowhere, its custody road being Kista - and an exchange reviewed without crafting, or held before it is reviewed, stands open, named in its gaps; an exchange on an unlinked repo stands complete only with its link held as a link_ref; defining, reading, listing and telling an exchange opens no socket to the forge, files no issue, opens no PR and writes nothing outside held records"
PLAIN_EXPLANATION = "Samverk bridge (M-242): repos, issues, and PRs on Volmarr's own forge with the same craft as GitHub's (Part IV), once Samverk's own road provides the surfaces."
USAGE = 'Usage: /samverkbridge | /samverkbridge exchange <exchange-id> | /samverkbridge stage <stage> | /samverkbridge repo <repo-id> | /samverkbridge view <view-id> | /samverkbridge note <note-id> | /samverkbridge index | /samverkbridge panel | /samverkbridge verdict'

STAGES = ("opened", "triaged", "crafted", "reviewed", "held")
HELD_EVIDENCE = ("repo_ref", "issue_ref", "pr_ref", "review_ref", "craft_ref", "link_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
CLAIM_KINDS = HELD_EVIDENCE + BARE_CLAIMS
TRANSITIONS = {
    "opened": ("triaged",),
    "triaged": ("crafted",),
    "crafted": ("reviewed",),
    "reviewed": ("opened", "held"),
    "held": (),
}


def legal_step(before: Any, after: Any) -> bool:
    """Whether the gate sequence allows one step, DERIVED.

    The machine stands as data in TRANSITIONS:
    inspect steps only to build, build only to
    test, test to repair on a exchange or to
    continue on a pass, repair back to build or
    test for the rerun, and continue steps
    nowhere - it is where a exchange stands complete.
    A stage outside the machine allows nothing.
    """
    return after in TRANSITIONS.get(before, ())


def next_stage(stage: Any, failed: Any = False) -> Optional[str]:
    """The step the tracker takes next, DERIVED from the sequence.

    Banked leads to triaged and triaged to
    crafted; crafted leads to reviewed; at
    reviewed a follow-up banking steps back to opened and a finished exchange steps to held;
    held is the end of the walk and steps
    nowhere. A step outside the sequence refuses
    by name.
    """
    reviewed = normalize_stage(stage)
    if reviewed == "opened":
        return "triaged"
    if reviewed == "triaged":
        return "crafted"
    if reviewed == "crafted":
        return "reviewed"
    if reviewed == "reviewed":
        return "opened" if failed else "held"
    return None


_HELDANCE = ("recorded_on", "actor", "repo", "origin_session")
_RUN_KEYS = frozenset({
    "exchange_id", "seq", "repo_id", "title", "stages",
    "claims", "detail",
} | set(_HELDANCE))
_SLICE_REF_KEYS = frozenset({
    "repo_id", "seq", "title", "state", "link", "detail",
} | set(_HELDANCE))
_TRACE_KEYS = frozenset({
    "trace_id", "seq", "exchange_id", "trace", "detail",
} | set(_HELDANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_HELDANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "exchange_id", "stance", "target", "title",
    "detail",
} | set(_HELDANCE))
_DERIVED_KEYS = frozenset({
    "standing", "complete", "greens", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "exchanges", "coverage", "covered", "uncovered",
    "current_exchange", "next_exchange", "progress", "ledger",
    "current", "exchange", "breaks", "live"})
_LIVE_KEYS = (
    "live_exchange", "exchanges_live", "live_question",
    "exchanges_raise", "raises_slice", "raised_live",
    "answers_live", "answers_question", "answered_live",
    "delivers_live", "delivered_live", "exchanges_live",
    "resumed_live", "runs_exchange", "paused_live",
    "runs_exchange", "ran_exchange", "spawns_process",
    "spawned_process", "builds_slice", "built_slice",
    "builds_live", "executes_slice", "executed_slice",
    "executes_live", "live_execution",
    "banks_slice", "banked_live", "exchange_live",
    "pushes_slice", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_exchange", "sent_exchange",
    "posts_note", "held_note", "traces_live",
    "traced_live", "writes_ledger", "wrote_ledger", "files_exchange", "filed_live", "spawns_tracker", "spawned_tracker", "sends_exchange", "sent_exchange", "writes_exchange", "wrote_exchange")


# ---------------------------------------------------------------------
# Small judges, in the sibling trace.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_stages(value: Any) -> Tuple[str, ...]:
    """A exchange's walked stages, held as data.

    The stages stand as a list of stage names in
    walk exchange, each one a stage of the explicit
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
    """A exchange's asked claims: claim repos opened as data.

    Each claim names one repo from the held
    vocabulary - the human repos the gate may ask
    and the code repos it must never ask, both
    held honestly as data - and a repo outside
    the vocabulary refuses.
    """
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError("claims must be a list of claim repos")
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
            out[key] = _clean_text(mapping.get(key), "a recorded_on repo")
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
                f"{what} claims a live gate exchange or repo build "
                f"execution ({key!r} is opened on it): "
                f"{EXCHANGE_RULE}")
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


def normalize_repo_state(value: Any) -> str:
    state = _clean_text(value, "an repo state").lower()
    if state not in REPO_STATES:
        raise ValueError(
            f"repo state {state!r} is not one of the held "
            f"states: " + ", ".join(REPO_STATES))
    return state


def normalize_link(value: Any) -> str:
    link = _clean_text(value, "a link").lower()
    if link not in LINKS:
        raise ValueError(
            f"link {link!r} is not one of the "
            f"repo exchange links: " + ", ".join(LINKS))
    return link


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
    repo = _clean_text(value, "a claim repo").lower()
    if repo not in CLAIM_KINDS:
        raise ValueError(
            f"claim repo {repo!r} is not one of the held "
            f"repos: " + ", ".join(CLAIM_KINDS))
    return repo

# ---------------------------------------------------------------------
# The held exchange: one repo cut from an active repo.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ExchangeRecord:
    """One exchange repo, held as data.

    The exchange names the active repo it was
    held from, by repo id, its title, its
    verifiable stages, held as data, and its
    claims, opened by exchange id. The grain is
    derived, never stored: exactly one verifiable
    walk is crafted against the machine. A exchange whose
    stages are not yet held stands with its
    stages empty: it stands open, opened in
    its gaps, and no stage is invented for it.
    The exchange is local data alone - no live build
    stands behind it: holding it builds nothing.
    """

    exchange_id: str
    seq: int
    repo_id: str
    title: str
    stages: Tuple[str, ...] = ()
    claims: Tuple[str, ...] = ()
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    repo: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "exchange_id", _clean_text(self.exchange_id, "a exchange id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "repo_id", _clean_text(self.repo_id, "an repo id"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a exchange title"))
        object.__setattr__(
            self, "stages", _check_stages(self.stages))
        object.__setattr__(
            self, "claims", _check_claims(self.claims))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a exchange detail"))
        for key in _HELDANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.exchange_id

    @property
    def stage(self) -> str:
        """The stage the exchange stands at: its last walked stage."""
        return self.stages[-1] if self.stages else ""

    def to_record(self) -> Dict[str, Any]:
        record = {
            "exchange_id": self.exchange_id, "seq": self.seq,
            "repo_id": self.repo_id, "title": self.title,
            "stages": list(self.stages),
            "claims": list(self.claims),
            "detail": self.detail,
        }
        for key in _HELDANCE:
            record[key] = getattr(self, key)
        return record


def _check_link_ref(value: Any) -> ExchangeRecord:
    if not isinstance(value, ExchangeRecord):
        raise ValueError("a exchange must be a ExchangeRecord")
    return value


def validate_exchange(exchange: Any) -> ExchangeRecord:
    return _check_link_ref(exchange)


def build_exchange(record: Any = None, **kwargs: Any) -> ExchangeRecord:
    """Build one held exchange from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, ExchangeRecord):
        if kwargs:
            raise ValueError("a exchange stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a exchange must be a mapping or a ExchangeRecord")
    _needed(data, _RUN_KEYS, "a exchange")
    return ExchangeRecord(
        exchange_id=data.get("exchange_id"), seq=data.get("seq"),
        repo_id=data.get("repo_id"), title=data.get("title"),
        stages=data.get("stages"),
        claims=data.get("claims"),
        detail=data.get("detail"),
        **_heldance(data))


def _breaks_map(book: Any) -> Dict[str, Tuple[str, ...]]:
    """Map each exchange to the steps it took outside the machine.

    Derived from the held exchanges alone: a break is
    one consecutive pair of walked stages the
    explicit gate sequence does not allow, told
    in walk exchange as before, then after.
    """
    opened: Dict[str, Tuple[str, ...]] = {}
    for exchange in book.exchanges:
        breaks = tuple(
            f"{before} > {after}"
            for before, after in zip(exchange.stages, exchange.stages[1:])
            if not legal_step(before, after))
        if breaks:
            opened[exchange.exchange_id] = breaks
    return opened

def exchange_gaps(exchange: Any, repo: Any = None) -> Tuple[str, ...]:
    """The gaps that keep a exchange from standing complete.

    Guarded from the exchange's own held fields alone -
    its walked steps against the explicit question
    sequence, and its held evidence against the
    held vocabulary: the exchange opens at
    opened, steps only where the sequence
    allows, carries held evidence and no bare claim,
    and a exchange stands complete only when it has
    opened held. The repo names nothing
    further: no gap is borrowed from another
    exchange.
    """
    reviewed = _check_link_ref(exchange)
    gaps: List[str] = []
    if not reviewed.stages:
        gaps.append(
            "has passed through no step: the exchange has not started")
        return tuple(gaps)
    if reviewed.stages[0] != "opened":
        gaps.append(
            f"opens at {reviewed.stages[0]}, not at opened: "
            f"the exchange opens with the reflection")
    for before, after in zip(reviewed.stages, reviewed.stages[1:]):
        if not legal_step(before, after):
            gaps.append(
                f"steps from {before} to {after}, which the "
                f"exchange sequence does not allow")
    for repo in reviewed.claims:
        if repo in BARE_CLAIMS:
            gaps.append(
                f"carries a {repo} claim, a bare claim with no "
                f"held proof: complete stands on held proof alone")
    if repo is not None:
        try:
            _ref = _repo_book(repo).slice_for(reviewed.repo_id)
        except Exception:
            _ref = None
        if _ref is not None and _ref.link == "unlinked" and \
                "link_ref" not in reviewed.claims:
            gaps.append(
                "stands reviewed on an unlinked repo with no "
                "link_ref held: the link for the "
                "repo is unlinked")
    if reviewed.stages[-1] != "held":
        gaps.append(
            f"has not reached held: the exchange stands "
            f"at {reviewed.stages[-1]}")
    return tuple(gaps)

def exchange_green(exchange: Any, repo: Any = None) -> bool:
    return not exchange_gaps(exchange, repo)


def plain_lines(exchange: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the exchange's own fields."""
    reviewed = _check_link_ref(exchange)
    return (
        f"Exchange: {reviewed.title}",
        f"Repo: {reviewed.repo_id}",
        f"Stage: {reviewed.stage if reviewed.stage else 'none'}",
        f"Claims: "
        f"{', '.join(reviewed.claims) if reviewed.claims else 'none'}",
    )


def segment_of(exchange: Any, repo: Any = None) -> str:
    reviewed = _check_link_ref(exchange)
    gaps = exchange_gaps(reviewed, repo)
    return (
        f"{reviewed.exchange_id}: {reviewed.title} - repo: "
        f"'{reviewed.repo_id}' - stage: "
        f"'{reviewed.stage if reviewed.stage else 'none'}' - "
        f"stages: {len(reviewed.stages)} - claims: "
        f"'{', '.join(reviewed.claims) if reviewed.claims else 'none'}' - "
        f"detail: '{reviewed.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held repo reference: the active repo a book exchanges from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class RepoRef:
    """One repo a exchange book exchanges from, held as a reference.

    The record names the repo, the title it
    opens and its standing - active or
    queued - held as data copied from the
    M-203 repo book's own telling. A exchange
    stands only from an active reference: the
    book refuses a exchange naming no held reference,
    and a exchange from an queued one, BY NAME.
    """

    repo_id: str
    seq: int
    title: str
    state: str
    link: str = "native"
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    repo: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "repo_id", _clean_text(self.repo_id, "an repo id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a title"))
        object.__setattr__(
            self, "state", normalize_repo_state(self.state))
        object.__setattr__(
            self, "link", normalize_link(self.link))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an repo detail"))
        for key in _HELDANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.repo_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "repo_id": self.repo_id, "seq": self.seq,
            "title": self.title, "state": self.state,
            "link": self.link,
            "detail": self.detail,
        }
        for key in _HELDANCE:
            record[key] = getattr(self, key)
        return record


def _check_repo_ref(value: Any) -> RepoRef:
    if not isinstance(value, RepoRef):
        raise ValueError("a repo reference must be an RepoRef")
    return value


def validate_repo_ref(ref: Any) -> RepoRef:
    return _check_repo_ref(ref)


def build_repo_ref(record: Any = None, **kwargs: Any) -> RepoRef:
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, RepoRef):
        if kwargs:
            raise ValueError(
                "a repo reference stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError(
            "a repo reference must be a mapping or an RepoRef")
    _needed(data, _SLICE_REF_KEYS, "a repo reference")
    return RepoRef(
        repo_id=data.get("repo_id"), seq=data.get("seq"),
        title=data.get("title"), state=data.get("state"), link=data.get("link") or "native",
        detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The held trace trace: the human approves the trace, as data.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TraceRecord:
    """One trace trace, held as data.

    The record names its repo and the trace the
    human active - the repo's exchange ids in
    derived claim exchange, held exactly as
    active. The trace is of the set and its
    exchange, never of a step: when the derived
    trace moves, this record stands stale, opened
    in the ledger, until a new trace is active.
    """

    trace_id: str
    seq: int
    exchange_id: str
    trace: str
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    repo: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "trace_id",
            _clean_text(self.trace_id, "an trace id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "exchange_id", _clean_text(self.exchange_id, "an repo id"))
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
            "exchange_id": self.exchange_id, "trace": self.trace,
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
        exchange_id=data.get("exchange_id"), trace=data.get("trace"),
        detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The held stance: a note on a exchange, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One exchange stance, held as data.

    The record names its exchange, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per exchange stance
    in a book. The record is data alone: holding
    it builds nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    exchange_id: str
    stance: str
    target: str
    title: str
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    repo: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "note_id", _clean_text(self.note_id, "a stance id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "exchange_id", _clean_text(self.exchange_id, "a exchange id"))
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
            "exchange_id": self.exchange_id, "stance": self.stance,
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
        exchange_id=data.get("exchange_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The held view: which repos a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ExchangeView:
    """A view over the book: every exchange, the green, the rest."""

    view_id: str
    seq: int
    view_filter: str
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    repo: str = ""
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


def _check_view_ref(value: Any) -> ExchangeView:
    if not isinstance(value, ExchangeView):
        raise ValueError("a view must be an ExchangeView")
    return value


def validate_view(view: Any) -> ExchangeView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> ExchangeView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, ExchangeView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an ExchangeView")
    _needed(data, _VIEW_KEYS, "a view")
    return ExchangeView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ExchangePanelRow:
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


def _row_for_exchange(exchange: ExchangeRecord,
                     repo: Any = None) -> ExchangePanelRow:
    return ExchangePanelRow(
        item_id=exchange.exchange_id,
        standing="complete" if exchange_green(exchange, repo) else "open",
        label=exchange.title, segment=segment_of(exchange, repo),
        recorded_on=exchange.recorded_on)


def _check_row_ref(value: Any) -> ExchangePanelRow:
    if not isinstance(value, ExchangePanelRow):
        raise ValueError("a panel row must be an ExchangePanelRow")
    return value


def validate_row(row: Any, exchange: Any = None,
                 repo: Any = None) -> ExchangePanelRow:
    reviewed = _check_row_ref(row)
    if exchange is not None:
        derived = _row_for_exchange(_check_link_ref(exchange), repo)
        if reviewed != derived:
            raise ValueError(
                f"panel row {reviewed.item_id!r} does not agree with "
                f"the row derived from its exchange")
    return reviewed


def build_row(row: Any = None, exchange: Any = None,
              repo: Any = None,
              **kwargs: Any) -> ExchangePanelRow:
    if exchange is not None:
        derived = _row_for_exchange(_check_link_ref(exchange), repo)
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            ExchangePanelRow(**kwargs))
        return validate_row(built, exchange, repo)
    if isinstance(row, ExchangePanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in COMPLETE_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return ExchangePanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on repo"))
    if row is None and kwargs:
        return ExchangePanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an ExchangePanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[ExchangePanelRow, ...]
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
        f"The exchange book holds {total_items} exchanges as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {green_shown} of the shown exchanges "
        f"stand complete.",
        "Rows stand in held exchange, the exchange the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its exchange's own fields "
        "- the repo it answers for, the steps it walked in the "
        "open and the evidence it honestly carries - and no "
        "judgement is stored on any exchange.",
        "Completeness is crafted from the held records alone: "
        "a exchange that steps outside the exchange sequence, "
        "carries a bare claim in place of held evidence, or has "
        "not opened held stands open, opened in its "
        "gaps, and the exchange index is derived from the "
        "held exchanges, never stored where it could drift.",
    )

@dataclass(frozen=True)
class ExchangePanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[ExchangePanelRow, ...]
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


def _resolve_view(repo: Any, view: Any) -> ExchangeView:
    book = _repo_book(repo)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, ExchangeView):
        return view
    return book.view_for(view)


def shown_exchanges(repo: Any, view: Any = None
                   ) -> Tuple[ExchangeRecord, ...]:
    book = _repo_book(repo)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.exchanges
    if resolved.view_filter == "complete":
        return tuple(g for g in book.exchanges if exchange_green(g, book))
    return tuple(g for g in book.exchanges if not exchange_green(g, book))


def exchanges_for_repo(repo: Any, repo_id: Any
                      ) -> Tuple[ExchangeRecord, ...]:
    wanted = _clean_text(repo_id, "an repo id")
    return tuple(
        g for g in _repo_book(repo).exchanges if g.repo_id == wanted)


def green_exchanges(repo: Any) -> Tuple[ExchangeRecord, ...]:
    book = _repo_book(repo)
    return tuple(g for g in book.exchanges if exchange_green(g, book))


def current_exchange(repo: Any) -> Optional[ExchangeRecord]:
    """The book's current exchange, DERIVED at call time.

    The first held exchange, in held exchange, that does
    not yet stand complete - where the Architect must
    look next. Nothing here is stored: the telling
    is derived from the held exchanges alone, so it can
    never go stale against them. A book whose every
    exchange stands complete has no current exchange.
    """
    book = _repo_book(repo)
    for exchange in book.exchanges:
        if not exchange_green(exchange, book):
            return exchange
    return None


def derive_panel(repo: Any, view: Any = None) -> ExchangePanel:
    book = _repo_book(repo)
    resolved = _resolve_view(book, view)
    shown = shown_exchanges(book, resolved)
    rows = tuple(_row_for_exchange(exchange, book) for exchange in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.exchanges), default="")
    green = sum(1 for g in shown if exchange_green(g, book))
    return ExchangePanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.exchanges), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.exchanges), len(shown), green, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> ExchangePanel:
    if not isinstance(value, ExchangePanel):
        raise ValueError("a panel must be an ExchangePanel")
    return value


def validate_panel(panel: Any, repo: Any = None) -> ExchangePanel:
    """Judge a stored panel against the panel derived from its book.

    Every derived field must agree; the stored
    panel's own name is its identity, not derived
    content (the M-182 exchange).
    """
    reviewed = _check_panel_ref(panel)
    if repo is not None:
        book = _repo_book(repo)
        view = (book.view_for(reviewed.view_id)
                if reviewed.view_id is not None else None)
        derived = derive_panel(book, view)
        for attr in ("view_id", "view_filter", "rows", "total_items",
                     "total_shown", "target_counts", "as_of", "account"):
            if getattr(reviewed, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {reviewed.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return reviewed


def build_panel(panel: Any = None, repo: Any = None,
                **kwargs: Any) -> ExchangePanel:
    if isinstance(panel, ExchangePanel):
        if kwargs:
            raise ValueError("a panel stands whole or by fields, not both")
        return validate_panel(panel, repo)
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
        built = ExchangePanel(
            panel_id=_clean_text(data.get("panel_id"), "a panel id"),
            view_id=data.get("view_id"),
            view_filter=normalize_view_filter(data.get("view_filter")),
            rows=rows,
            total_items=_check_count(
                data.get("total_items"), "a total_items count"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            target_counts=counts,
            as_of=_clean_text(data.get("as_of"), "an as_of repo"),
            account=_check_lines(data.get("account"), "the account"))
        return validate_panel(built, repo)
    if panel is None and repo is not None:
        return derive_panel(repo, kwargs.get("view"))
    raise ValueError("a panel must be a mapping, an ExchangePanel, or derived")


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
class ExchangeVerdict:
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


def derive_verdict(repo: Any, view: Any = None) -> ExchangeVerdict:
    book = _repo_book(repo)
    resolved = _resolve_view(book, view)
    shown = shown_exchanges(book, resolved)
    green = sum(1 for g in shown if exchange_green(g, book))
    latest = max((g.recorded_on for g in shown), default="")
    return ExchangeVerdict(
        verdict=_verdict_word(len(shown), green),
        view_id=resolved.view_id, total_shown=len(shown),
        green_shown=green, latest_on=latest)


def _check_verdict_ref(value: Any) -> ExchangeVerdict:
    if not isinstance(value, ExchangeVerdict):
        raise ValueError("a verdict must be an ExchangeVerdict")
    return value


def validate_verdict(verdict: Any, repo: Any = None) -> ExchangeVerdict:
    reviewed = _check_verdict_ref(verdict)
    if reviewed.verdict not in VERDICT_WORDS:
        raise ValueError(f"verdict {reviewed.verdict!r} is not a held word")
    if repo is not None:
        book = _repo_book(repo)
        view = (book.view_for(reviewed.view_id)
                if reviewed.view_id is not None else None)
        derived = derive_verdict(book, view)
        if reviewed != derived:
            raise ValueError(
                "the stored verdict disagrees with the verdict "
                "derived from its book")
    return reviewed


def build_verdict(verdict: Any = None, repo: Any = None,
                  **kwargs: Any) -> ExchangeVerdict:
    if isinstance(verdict, ExchangeVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, repo)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = ExchangeVerdict(
            verdict=_clean_text(data.get("verdict"), "a verdict"),
            view_id=data.get("view_id"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            green_shown=_check_count(
                data.get("green_shown"), "a green_shown count"),
            latest_on=_clean_text(data.get("latest_on"), "a latest repo"))
        return validate_verdict(built, repo)
    if verdict is None and repo is not None:
        return derive_verdict(repo, kwargs.get("view"))
    raise ValueError(
        "a verdict must be a mapping, an ExchangeVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held repos' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexExchange:
    stage: str
    exchange_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "stage": self.stage, "exchange_id": self.exchange_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class ExchangeIndex:
    """The exchange index, derived from the held exchanges.

    The index names one exchange per green exchange, in
    held exchange - the exchange's own one verifiable
    stage, its exchange id and its title - and the
    exchanges that do not stand complete, opened in its
    gaps. Nothing here is stored on any exchange: the
    index is derived at call time from the held
    records alone, so it can never drift from them.
    """

    exchanges: Tuple[IndexExchange, ...]
    gaps: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "exchanges": [e.to_record() for e in self.exchanges],
            "gaps": list(self.gaps),
        }


def derive_index(repo: Any) -> ExchangeIndex:
    """Derive the exchange index from the book's held exchanges."""
    book = _repo_book(repo)
    exchanges = tuple(
        IndexExchange(stage=g.stage, exchange_id=g.exchange_id,
                   title=g.title)
        for g in book.exchanges if exchange_green(g, book))
    gaps = tuple(
        g.exchange_id for g in book.exchanges if not exchange_green(g, book))
    return ExchangeIndex(exchanges=exchanges, gaps=gaps)


def exchange_for_check(repo: Any, stage: Any) -> Optional[ExchangeRecord]:
    """The first held exchange one stage reaches, or none - honestly."""
    if stage is None:
        return None
    if not isinstance(stage, str):
        raise ValueError("an stage must be a string naming the stage")
    wanted = stage.strip()
    if not wanted:
        return None
    for exchange in _repo_book(repo).exchanges:
        if exchange.stage == wanted:
            return exchange
    return None


def transition_breaks(repo: Any) -> Tuple[str, ...]:
    """Every step outside the gate sequence, DERIVED.

    One telling per break, in held exchange: the exchange
    that took it and the step it took, before,
    then after. A book whose exchanges all walk inside
    the machine tells none.
    """
    book = _repo_book(repo)
    return tuple(
        f"{exchange_id}: {step}"
        for exchange_id, steps in _breaks_map(book).items()
        for step in steps)

def exchange_exchange(repo: Any,
              repo_id: Any = None) -> Tuple[ExchangeRecord, ...]:
    """The held exchanges in their held exchange, DERIVED at call time.

    Exchanges stand in the exchange the book holds them -
    the exchange their repos were opened - optionally
    for one repo alone. Nothing here is stored:
    the exchange is the book's own held exchange, told.
    """
    book = _repo_book(repo)
    exchanges = list(book.exchanges)
    if repo_id is not None:
        wanted = _clean_text(repo_id, "a repo id")
        exchanges = [r for r in exchanges if r.repo_id == wanted]
    return tuple(exchanges)

def trace_of(repo: Any, exchange_id: Any) -> str:
    """One exchange's trace, DERIVED at call time.

    The exchange's walked stages reviewed as one trace
    line, in walk exchange. A exchange that has walked
    nowhere traces empty: the trace tells only
    what stands walked, and the walk is opened
    elsewhere.
    """
    exchange = _repo_book(repo).exchange_for(exchange_id)
    return " > ".join(exchange.stages)

def trace_for_exchange(repo: Any,
                  exchange_id: Any) -> Optional[TraceRecord]:
    """The held trace for one exchange, or none - honestly."""
    wanted = _clean_text(exchange_id, "a exchange id")
    for record in _repo_book(repo).traces:
        if record.exchange_id == wanted:
            return record
    return None

def trace_current(repo: Any, exchange_id: Any) -> bool:
    """Whether the held trace agrees with the derived trace.

    The trace stands current only while the trace
    it holds is the trace the book derives now; a
    moved walk leaves it stale, and no trace at
    all traces nothing.
    """
    trace = trace_for_exchange(repo, exchange_id)
    if trace is None:
        return False
    return trace.trace == trace_of(repo, exchange_id)

def note_for_exchange(repo: Any, exchange_id: Any,
                   stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one exchange (and stance, when opened)."""
    wanted = _clean_text(exchange_id, "a exchange id")
    for record in _repo_book(repo).notes:
        if record.exchange_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(repo: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the repo targets, or none."""
    notes = _repo_book(repo).notes
    return notes[0] if notes else None


def ledger_record(repo: Any = None) -> Dict[str, Any]:
    """The exchange ledger, DERIVED here from the held exchanges alone.

    The ledger counts the held exchanges by their
    derived completeness - green and red - names
    the current exchange, the first that does not yet
    stand complete, tells each held exchange's trace
    standing - current while its held trace
    agrees with its derived trace, stale when it
    has moved, unheld while no trace stands for
    it - and names every step the held exchanges took
    outside the gate sequence. Nothing here is
    stored: the telling is derived at call time.
    """
    book = _repo_book(repo)
    standings = []
    for standing in COMPLETE_WORDS:
        number = sum(
            1 for g in book.exchanges
            if ("complete" if exchange_green(g, book) else "open") == standing)
        standings.append({"standing": standing, "exchange_records": number})
    current = current_exchange(book)
    traces = []
    for exchange in book.exchanges:
        trace = trace_for_exchange(book, exchange.exchange_id)
        if trace is None:
            standing = "unheld"
        elif trace_current(book, exchange.exchange_id):
            standing = "current"
        else:
            standing = "stale"
        traces.append({"exchange_id": exchange.exchange_id, "trace": standing})
    return {
        "type": "exchange_well",
        "repo": EXCHANGE_SLICE,
        "standings": standings,
        "total": len(book.exchanges),
        "current_exchange": current.exchange_id if current is not None else None,
        "traces": traces,
        "breaks": list(transition_breaks(book)),
    }

def roadmap_record() -> Dict[str, Any]:
    """This repo's own roadmap standing, proved from the roadmap itself.

    The record loads this repo's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 repos in 11 parts,
    the opened prefix, the next repo where the
    exchange exchanges, and M-242's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(EXCHANGE_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "exchange_roadmap",
        "repo": EXCHANGE_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m242_title": own.title,
        "m242_part": own.part,
        "m242_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: repos, exchanges, views, notes and trace traces held
# together, one pinned panel at most per telling, and no verdict,
# index, trace or exchange ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ExchangeBook:
    title: str
    repos: Tuple[RepoRef, ...] = ()
    exchanges: Tuple[ExchangeRecord, ...] = ()
    views: Tuple[ExchangeView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    traces: Tuple[TraceRecord, ...] = ()
    panels: Tuple[ExchangePanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        repos = tuple(_check_repo_ref(g) for g in self.repos)
        exchanges = tuple(_check_link_ref(g) for g in self.exchanges)
        views = tuple(_check_view_ref(v) for v in self.views)
        notes = tuple(_check_note_ref(m) for m in self.notes)
        traces = tuple(_check_trace_ref(a) for a in self.traces)
        panels = tuple(_check_panel_ref(pn) for pn in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for ref in repos:
            if ref.repo_id in seen_ids:
                raise ValueError(
                    f"two repo references stand under id {ref.repo_id!r}")
            if ref.seq in seen_seqs:
                raise ValueError(
                    f"two repo references stand at sequence {ref.seq}")
            seen_ids.add(ref.repo_id)
            seen_seqs.add(ref.seq)
        exchange_ids = set()
        exchange_seqs = set()
        for exchange in exchanges:
            if exchange.exchange_id in exchange_ids:
                raise ValueError(
                    f"two exchanges stand under id {exchange.exchange_id!r}")
            if exchange.seq in exchange_seqs:
                raise ValueError(
                    f"two exchanges stand at sequence {exchange.seq}")
            exchange_ids.add(exchange.exchange_id)
            exchange_seqs.add(exchange.seq)
        by_slice = {ref.repo_id: ref for ref in repos}
        for exchange in (exchanges if repos else ()):

            ref = by_slice.get(exchange.repo_id)
            if ref is None:
                raise ValueError(
                    f"exchange {exchange.exchange_id!r} is held from repo "
                    f"{exchange.repo_id!r}, which stands nowhere in "
                    f"this book")
            if ref.state != "live":
                raise ValueError(
                    f"exchange {exchange.exchange_id!r} is held from repo "
                    f"{exchange.repo_id!r}, which is not active: "
                    f"no repo is held from an queued repo")
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
            target = (record.exchange_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for exchange "
                    f"{record.exchange_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per exchange target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        trace_ids = set()
        trace_seqs = set()
        trace_exchanges = set()
        exchange_ids = {exchange.exchange_id for exchange in exchanges}
        for record in traces:
            if record.trace_id in trace_ids:
                raise ValueError(
                    f"two traces stand under id {record.trace_id!r}")
            if record.seq in trace_seqs:
                raise ValueError(
                    f"two traces stand at sequence {record.seq}")
            if record.exchange_id in trace_exchanges:
                raise ValueError(
                    f"two traces stand for exchange "
                    f"{record.exchange_id!r}: one trace stands "
                    f"per exchange walk")
            if exchanges and record.exchange_id not in exchange_ids:
                raise ValueError(
                    f"trace {record.trace_id!r} traces exchange "
                    f"{record.exchange_id!r}, which stands nowhere in "
                    f"this book")
            trace_ids.add(record.trace_id)
            trace_seqs.add(record.seq)
            trace_exchanges.add(record.exchange_id)
        object.__setattr__(
            self, "repos", tuple(sorted(repos, key=lambda g: g.seq)))
        object.__setattr__(
            self, "exchange_records", tuple(sorted(exchanges, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(
            self, "traces",
            tuple(sorted(traces, key=lambda a: a.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.exchanges + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.exchange_id for g in self.exchanges) + tuple(
            v.view_id for v in self.views)

    def exchange_ids(self) -> Tuple[str, ...]:
        return tuple(g.exchange_id for g in self.exchanges)

    def repo_ids(self) -> Tuple[str, ...]:
        return tuple(g.repo_id for g in self.repos)

    def exchange_for(self, exchange_id: Any) -> ExchangeRecord:
        wanted = _clean_text(exchange_id, "a exchange id")
        for exchange in self.exchanges:
            if exchange.exchange_id == wanted:
                return exchange
        raise KeyError(f"no exchange opened {wanted!r} stands in this book")

    def slice_for(self, repo_id: Any) -> RepoRef:
        wanted = _clean_text(repo_id, "an repo id")
        for ref in self.repos:
            if ref.repo_id == wanted:
                return ref
        raise KeyError(f"no repo opened {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> ExchangeView:
        wanted = _clean_text(view_id, "a view id")
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no view opened {wanted!r} stands in this book")

    def note_for(self, note_id: Any) -> NoteRecord:
        wanted = _clean_text(note_id, "a stance id")
        for record in self.notes:
            if record.note_id == wanted:
                return record
        raise KeyError(f"no stance opened {wanted!r} stands in this book")

    def trace_for(self, trace_id: Any) -> TraceRecord:
        wanted = _clean_text(trace_id, "an trace id")
        for record in self.traces:
            if record.trace_id == wanted:
                return record
        raise KeyError(f"no trace opened {wanted!r} stands in this book")

    def item_for(self, item_id: Any) -> Any:
        wanted = _clean_text(item_id, "an item id")
        for exchange in self.exchanges:
            if exchange.exchange_id == wanted:
                return exchange
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item opened {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "repos": [g.to_record() for g in self.repos],
            "exchange_records": [g.to_record() for g in self.exchanges],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "traces": [a.to_record() for a in self.traces],
            "panels": [pn.to_record() for pn in self.panels],
        }


def _judge_book_panels(book: ExchangeBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: ExchangeBook) -> None:
    if book.title != "Samverk bridge at the M-242 slice run":
        raise ValueError("the shipped example book carries another title")
    if len(book.repos) != 3 or len(book.exchanges) != 5 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold three repo references, five exchanges and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.traces) != 1:
        raise ValueError("the shipped example book must hold one trace record")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-samverk":
        raise ValueError("the pinned panel is panel-samverk")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "held" or verdict.green_shown != 3:
        raise ValueError("the shipped example book verdict must stand held at three complete of five")
    index = derive_index(book)
    if [e.stage for e in index.exchanges] != ["held", "held", "held"]:
        raise ValueError("the shipped example book index must derive the three held complete exchanges in held exchange")
    if index.gaps != ("exchange-bare-exchange", "exchange-leaping-exchange"):
        raise ValueError("the shipped example book must leave the bare and leaping exchanges honestly open, opened in its gaps")
    opened = exchange_for_check(book, EXAMPLE_STAGE)
    if opened is None or opened.exchange_id != "exchange-held-exchange":
        raise ValueError("the shipped example book must reach its opening exchange under the example stage")
    if trace_of(book, "exchange-held-exchange") != "opened > triaged > crafted > reviewed > held":
        raise ValueError("the shipped example book must derive the opening exchange's trace from its walked steps")
    if not trace_current(book, "exchange-held-exchange"):
        raise ValueError("the shipped example book must hold the opening exchange's trace current")
    first = first_note(book)
    if first is None or first.note_id != "note-note-first":
        raise ValueError("the shipped example book must hold the opening note as its first note exchange")

def validate_book(data: Any, *, require_example: bool = False) -> ExchangeBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, ExchangeBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a exchange book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live repo build or execution "
                f"({key!r} is opened on it): {EXCHANGE_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its exchanges under a view")
    if "exchange_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held exchanges at call time")
    if "ledger" in data or "current_exchange" in data:
        raise ValueError(
            "a book stores no ledger and no current exchange: both are "
            "derived from its held exchanges at call time")
    if "trace" in data or "exchange" in data:
        raise ValueError(
            "a book stores no trace and no exchange: both are derived "
            "from its held exchanges at call time; an trace record "
            "holds the trace the human active")
    if data.get("schema") is not None and (
            data["schema"] != EXCHANGE_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{EXCHANGE_SCHEMA!r}")
    if data.get("repo") is not None and (
            data["repo"] != EXCHANGE_SLICE):
        raise ValueError(
            f"a book's repo must be {EXCHANGE_SLICE!r}")
    head = data.get("exchange_head") or data.get("samverk_bridge") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's exchange head must be a mapping")
    title = head.get("title") or data.get("title")
    repos = tuple(build_repo_ref(g) for g in data.get("repos") or ())
    exchanges = tuple(build_exchange(g) for g in data.get("exchange_records") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    traces = tuple(build_trace(a) for a in data.get("traces") or ())
    book = ExchangeBook(
        title=title, repos=repos, exchanges=exchanges, views=views,
        notes=notes, traces=traces, panels=())
    panels = tuple(
        build_panel(pn, book) for pn in data.get("panels") or ())
    book = ExchangeBook(
        title=book.title, repos=book.repos, exchanges=book.exchanges,
        views=book.views, notes=book.notes,
        traces=book.traces, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> ExchangeBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (ExchangeBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an ExchangeBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> ExchangeBook:
    return validate_book(data, require_example=require_example)


def load_exchange(
        data: Optional[Dict[str, Any]] = None) -> ExchangeBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(EXCHANGE_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_exchange_file(path: Any) -> ExchangeBook:
    """Load one exchange file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: repo references, exchanges and views held one by one.
# ---------------------------------------------------------------------

class ExchangeRegistry:
    """An in-memory holding of repo references, exchanges and views.

    The registry is the pure layer's model of a
    session's exchange book: repo references are
    held under their ids, exchanges are held under
    their ids, one exchange per id and per sequence,
    and views are held in triaged exchange, one view
    per sequence and per id. Holding is data only -
    nothing held here builds anything, executes
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._slices: List[RepoRef] = []
        self._exchanges: List[ExchangeRecord] = []
        self._views: List[ExchangeView] = []
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

    def register_repo_ref(self, item: Any) -> RepoRef:
        """Hold one repo reference, crafted whole before held."""
        reviewed = _check_repo_ref(item)
        return self._register(
            self._slices, reviewed, "repo_id", "repo reference")

    def register_exchange(self, item: Any) -> ExchangeRecord:
        """Hold one exchange, crafted whole before held."""
        reviewed = _check_link_ref(item)
        return self._register(
            self._exchanges, reviewed, "exchange_id", "exchange")

    def register_view(self, view: Any) -> ExchangeView:
        """Hold one view; a view naming no id takes a fresh one."""
        reviewed = _check_view_ref(view)
        if not reviewed.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            reviewed = build_view({**reviewed.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, reviewed, "view_id", "view")

    def register_book(self, book: Any) -> ExchangeBook:
        """Hold a whole book's records, under its title."""
        reviewed = build_book(book)
        if self._title is not None and reviewed.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {reviewed.title!r}")
        for ref in reviewed.repos:
            self.register_repo_ref(ref)
        for exchange in reviewed.exchanges:
            self.register_exchange(exchange)
        for view in reviewed.views:
            self.register_view(view)
        self._title = reviewed.title
        return self.book()

    def book(self) -> ExchangeBook:
        return ExchangeBook(
            title=self._title or "An unheld exchange book",
            repos=tuple(self._slices), exchanges=tuple(self._exchanges),
            views=tuple(self._views), notes=(), traces=(), panels=())

    def list_slices(self) -> Tuple[RepoRef, ...]:
        return tuple(self._slices)

    def list_exchanges(self) -> Tuple[ExchangeRecord, ...]:
        return tuple(self._exchanges)

    def list_views(self) -> Tuple[ExchangeView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._exchanges) + tuple(self._views)

    def get_slice(self, repo_id: Any) -> RepoRef:
        return self.book().slice_for(repo_id)

    def get_exchange(self, exchange_id: Any) -> ExchangeRecord:
        return self.book().exchange_for(exchange_id)

    def get_view(self, view_id: Any) -> ExchangeView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records traced for the ledger target.
# ---------------------------------------------------------------------

def _repo_book(repo: Any) -> ExchangeBook:
    if repo is None:
        return load_exchange()
    if isinstance(repo, ExchangeBook):
        return repo
    if isinstance(repo, ExchangeRegistry):
        return repo.book()
    return build_book(repo)


def _heldance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _HELDANCE}


def exchange_record(exchange: Any, repo: Any = None) -> Dict[str, Any]:
    reviewed = _check_link_ref(exchange)
    book = _repo_book(repo) if repo is not None else None
    record = {
        "type": "exchange_exchange",
        "repo": EXCHANGE_SLICE,
        "exchange_id": reviewed.exchange_id,
        "repo_id": reviewed.repo_id,
        "title": reviewed.title,
        "segment": segment_of(reviewed, book),
        "complete": exchange_green(reviewed, book),
        "gaps": list(exchange_gaps(reviewed, book)),
    }
    record.update(_heldance_record(reviewed))
    return record


def repo_record(ref: Any) -> Dict[str, Any]:
    reviewed = _check_repo_ref(ref)
    record = {
        "type": "exchange_run",
        "repo": EXCHANGE_SLICE,
        "repo_id": reviewed.repo_id,
        "title": reviewed.title,
        "state": reviewed.state, "link": reviewed.link,
    }
    record.update(_heldance_record(reviewed))
    return record


def trace_record(record_in: Any) -> Dict[str, Any]:
    reviewed = _check_trace_ref(record_in)
    record = {
        "type": "exchange_trace",
        "repo": EXCHANGE_SLICE,
        "trace_id": reviewed.trace_id,
        "exchange_id": reviewed.exchange_id,
        "trace": reviewed.trace,
    }
    record.update(_heldance_record(reviewed))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    reviewed = _check_view_ref(view)
    record = {
        "type": "exchange_view",
        "repo": EXCHANGE_SLICE,
        "view_id": reviewed.view_id, "seq": reviewed.seq,
        "view_filter": reviewed.view_filter,
    }
    record.update(_heldance_record(reviewed))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    reviewed = _check_note_ref(record_in)
    record = {
        "type": "exchange_note",
        "repo": EXCHANGE_SLICE,
        "note_id": reviewed.note_id,
        "exchange_id": reviewed.exchange_id,
        "stance": reviewed.stance,
    }
    record.update(_heldance_record(reviewed))
    return record


def panel_record(panel: Any, repo: Any = None) -> Dict[str, Any]:
    reviewed = validate_panel(panel, repo)
    record = {"type": "exchange_panel",
              "repo": EXCHANGE_SLICE}
    record.update(reviewed.to_record())
    return record


def verdict_record(verdict: Any, repo: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, ExchangeVerdict):
        reviewed = validate_verdict(verdict, repo)
    else:
        reviewed = derive_verdict(_repo_book(verdict), view)
    record = {"type": "exchange_verdict",
              "repo": EXCHANGE_SLICE}
    record.update(reviewed.to_record())
    return record


def index_record(repo: Any) -> Dict[str, Any]:
    if isinstance(repo, ExchangeIndex):
        index = repo
    else:
        index = derive_index(repo)
    record = {"type": "exchange_index",
              "repo": EXCHANGE_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    reviewed = _repo_book(book)
    record = {"type": "exchange_book",
              "repo": EXCHANGE_SLICE,
              "title": reviewed.title}
    record.update(reviewed.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(exchange: Any, repo: Any = None) -> str:
    reviewed = _check_link_ref(exchange)
    return (
        f"{reviewed.title} - from {reviewed.repo_id}: "
        f"stage {reviewed.stage if reviewed.stage else 'none'}, "
        f"claims "
        f"{', '.join(reviewed.claims) if reviewed.claims else 'none'}. "
        f"{reviewed.detail}")


def panel_plain_words(repo: Any, view: Any = None) -> str:
    panel = derive_panel(repo, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(repo: Any, view: Any = None) -> str:
    verdict = derive_verdict(repo, view)
    return (
        f"The exchanges stand {verdict.verdict}: "
        f"{verdict.green_shown} of {verdict.total_shown} shown "
        f"exchanges stand complete.")


def view_plain_words(view: Any) -> str:
    reviewed = _check_view_ref(view)
    return f"View {reviewed.view_id}: shows {reviewed.view_filter} exchanges."


def note_plain_words(record_in: Any) -> str:
    reviewed = _check_note_ref(record_in)
    return (
        f"Note {reviewed.note_id}: {reviewed.stance} "
        f"{reviewed.exchange_id}, toward {reviewed.target}. "
        f"{reviewed.detail}")


def index_plain_words(repo: Any) -> str:
    index = (repo if isinstance(repo, ExchangeIndex)
             else derive_index(repo))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.exchanges)} green exchanges; "
        f"red, opened in its gaps: {gaps}.")

def format_exchange(exchange: Any, repo: Any = None) -> str:
    reviewed = _check_link_ref(exchange)
    book = _repo_book(repo) if repo is not None else None
    lines = [f"{reviewed.title} ({reviewed.exchange_id})"]
    lines.extend(plain_lines(reviewed))
    lines.append(reviewed.detail)
    if exchange_green(reviewed, book):
        lines.append(
            "This exchange stands complete - it walked the question "
            "sequence in the open from opened to held, "
            "and it carries held evidence alone.")
    else:
        lines.append(
            "This exchange stands open - it stands opened in "
            f"its gaps: {', '.join(exchange_gaps(reviewed, book))}, and "
            "nothing is invented for it.")
    return "\n".join(lines)

def format_view(view: Any) -> str:
    reviewed = _check_view_ref(view)
    return (
        f"View {reviewed.view_id}: filter {reviewed.view_filter} - "
        f"{reviewed.detail}")


def format_note(record_in: Any) -> str:
    reviewed = _check_note_ref(record_in)
    lines = [
        f"Exchange note {reviewed.stance} {reviewed.exchange_id} "
        f"({reviewed.note_id}): {reviewed.title}. {reviewed.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or exchange it builds nothing, executes nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_stage(repo: Any, stage: Any) -> str:
    exchange = exchange_for_check(repo, stage)
    if exchange is not None:
        return format_exchange(exchange, repo)
    wanted = stage.strip() if isinstance(stage, str) else stage
    return (
        f"No held exchange stands under stage {wanted!r} yet - the "
        f"stage reaches nothing in this book, and no exchange is "
        f"invented for it.")


def format_book(repo: Any = None, repo_id: Any = None) -> str:
    book = _repo_book(repo)
    exchanges = (exchanges_for_repo(book, repo_id)
              if repo_id is not None else book.exchanges)
    lines = [f"The Samverk Bridge (M-242) - {book.title}"]
    lines.extend(segment_of(exchange, book) for exchange in exchanges)
    return "\n".join(lines)


def format_panel(repo: Any = None, view: Any = None) -> str:
    panel = derive_panel(repo, view)
    lines = [f"Exchange panel under view {panel.view_id}:"]
    lines.extend(row.segment for row in panel.rows)
    lines.extend(panel.account)
    return "\n".join(lines)


def format_verdict(repo: Any = None, view: Any = None) -> str:
    verdict = derive_verdict(repo, view)
    return verdict_plain_words(repo, view) + (
        f" (view {verdict.view_id}, as of {verdict.latest_on})")


def format_index(repo: Any = None) -> str:
    book = _repo_book(repo)
    index = derive_index(book)
    lines = ["Exchange index, derived from the held exchanges:"]
    for exchange in index.exchanges:
        lines.append(f"{exchange.stage} - {exchange.title} ({exchange.exchange_id})")
    if index.gaps:
        lines.append(
            "Red, opened honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "builds nothing, executes nothing and opens no network.")
    return "\n".join(lines)


def format_exchange_screen(repo: Any = None) -> str:
    book = _repo_book(repo)
    lines = [
        "The Samverk Bridge (M-242)",
        f"{book.title}: {len(book.exchanges)} exchanges held, "
        f"{len(green_exchanges(book))} exchanges standing green, "
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


def parse_exchange_args(args: Any) -> Tuple[str, Any]:
    """Parse the /exchange grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("exchange", "view", "note"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("stage", "repo"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("index", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
