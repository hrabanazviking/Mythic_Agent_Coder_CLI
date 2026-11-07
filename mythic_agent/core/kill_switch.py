"""The kill switch everywhere - one halt for everything (M-108).

Part V - Autonomy & Safety. The roadmap's words:
``one key/command halts the coder, the crew,
background jobs, and pending approvals - tested,
instant.``

What already shipped, and what this slice adds:

* The M-103 background tasks layer holds one long
  command as a managed job with a kill road of its
  own (a kill request recorded as data, then
  applied), the M-106 fleet layer holds a crew of
  headless runs as data with verdicts judged
  mechanically, the M-104 keeper watches held work
  for stalls, and the M-107 budgets layer pauses
  work gracefully when a guardrail is reached.
  Nothing in the tree is the one switch that halts
  *everything at once*: the coder's own in-flight
  work, the crew, the background jobs and any
  approval still waiting for an answer.
* This slice is that missing switch, as a pure
  layer in the exact sibling shape: a halt (the
  targets it names - the coder, the crew, the
  background jobs, the pending approvals; one
  switch halts all four by default, and a scoped
  halt naming a subset is data too - who or what
  asked, and a reason as text) validated as data,
  a holdings reading (what the session actually
  holds, in the M-103 job-state words and the
  M-106 crew-status words) validated as data, a
  mechanical judge that reads a halt against a
  holdings reading and returns per-target verdicts
  - halted, already stopped, or nothing held - a
  halt record shaped as session news, and a small
  in-memory registry model with deterministic ids.
  This module starts no process, kills nothing,
  signals nothing, writes no file and changes no
  setting; the agent layer owns holding the
  registry for a session, reading the holdings from
  the real roads, and carrying a halt out in the
  world through those roads.

Honesty rules, enforced here and pinned by tests:

* **A halt is instant and total for its targets.**
  A halt names its targets and halts all of them;
  there is no partial or gradual halt in this
  layer, and no target outside the named set is
  touched by the verdict.
* **Nothing is claimed halted that was not held.**
  A target is halted only when the holdings
  reading shows live work for it: the coder at
  work, a crew task running, a background job
  queued or running, an approval pending. A
  target whose work already finished is reported
  as already stopped, never as newly halted, and
  a target holding nothing is reported as nothing
  held. A crew task that is merely queued - a
  plan, not yet running - is not held work: it
  makes nothing halted.
* **The judge is mechanical.** The per-target
  verdicts and the halt's overall status are
  computed from the holdings reading alone and
  validated on construction, so a verdict can
  never disagree with its own inputs. No other
  signal moves the verdict.
* **A pull is always news.** Every judged halt
  yields one halt record shaped as session news,
  stating each target's outcome in plain words,
  so a pulled switch can never be lost as a mere
  log line.
* **Status is never carried by colour or symbol
  alone.** Every formatter states a halt's
  targets and verdict in words.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Dict, Optional, Tuple

__all__ = [
    "BACKGROUND_ACTIVE_STATES",
    "BACKGROUND_STATES",
    "BACKGROUND_TERMINAL_STATES",
    "CREW_FINISHED_STATUSES",
    "CREW_STATUSES",
    "HALT_OUTCOMES",
    "HALT_STATUSES",
    "HALT_TARGETS",
    "KILL_SWITCH_SLICE",
    "PLAIN_EXPLANATION",
    "USAGE",
    "Halt",
    "HaltHoldings",
    "HaltRegistry",
    "HaltVerdict",
    "Holdings",
    "build_halt",
    "build_holdings",
    "format_halt",
    "format_halt_record",
    "format_halts",
    "format_halts_screen",
    "format_record",
    "format_verdict",
    "halt_record",
    "judge_halt",
    "normalize_halt_id",
    "normalize_halt_target",
    "parse_halt_args",
    "validate_halt",
    "validate_holdings",
    "validate_verdict",
]

KILL_SWITCH_SLICE = "M-108"

#: The halt targets, in roadmap order: the coder
#: itself, its crew, its background jobs, and any
#: approval still waiting for an answer. One
#: switch halts all four by default.
HALT_TARGETS = ("coder", "crew", "background_jobs", "approvals")

#: The per-target outcome words, and the halt's
#: overall status words (the same three readings:
#: the halt's status is the strongest outcome any
#: of its targets earned - see ``judge_halt``).
HALT_OUTCOMES = ("halted", "already_stopped", "nothing_held")
HALT_STATUSES = HALT_OUTCOMES

#: The M-103 background job states, in lifecycle
#: order - the words a holdings reading names a
#: held job in, so a job is never described in two
#: dialects.
BACKGROUND_STATES = (
    "queued", "running", "completed", "failed", "cancelled")

#: Job states that are live work a halt can halt.
BACKGROUND_ACTIVE_STATES = ("queued", "running")

#: Job states that have already stopped.
BACKGROUND_TERMINAL_STATES = ("completed", "failed", "cancelled")

#: The M-106 crew task verdict status words, in
#: lifecycle order - the words a holdings reading
#: names a crew task in.
CREW_STATUSES = (
    "queued", "running", "passed", "failed", "error", "skipped")

#: Crew statuses that have already stopped.
CREW_FINISHED_STATUSES = ("passed", "failed", "error", "skipped")

PLAIN_EXPLANATION = (
    "The kill switch is one halt for everything: "
    "one key or command halts the coder, the crew, "
    "background jobs and pending approvals - "
    "instantly, and totally for the targets named. "
    "A halt names its targets (all four by default; "
    "a scoped halt may name a subset), who or what "
    "asked, and a reason. The judge is mechanical: "
    "a target is halted only when the session "
    "actually holds live work for it - a target "
    "whose work already finished is already "
    "stopped, never newly halted, and a target "
    "holding nothing is nothing held. This layer "
    "holds halts, holdings readings and verdicts "
    "as data only; it kills nothing and signals "
    "nothing itself - the agent layer carries a "
    "halt out through the real roads."
)

USAGE = (
    "Usage: /halt, /halt show, /halt show <halt>, "
    "/halt pull, /halt pull <target>"
)

_HALT_KEYS = frozenset({
    "halt_id", "id", "actor", "requested_by", "by", "who",
    "reason", "why", "targets", "target", "scope",
})

_HOLDINGS_KEYS = frozenset({
    "coder_active", "coder", "coder_working",
    "background_jobs", "jobs",
    "crew_tasks", "crew", "fleet_tasks",
    "pending_approvals", "approvals_pending", "approvals",
})

_TARGET_WORDS = {
    "coder": "coder", "code": "coder", "agent": "coder",
    "crew": "crew", "fleet": "crew",
    "background_jobs": "background_jobs",
    "background": "background_jobs", "jobs": "background_jobs",
    "job": "background_jobs",
    "approvals": "approvals", "approval": "approvals",
}

_ALL_WORDS = ("all", "everything", "everywhere")

_HALT_ID_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789-_.")


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _loose_text(value: Any, what: str) -> str:
    """An optional text field: text, stripped; anything else refuses."""
    if not isinstance(value, str):
        raise ValueError(f"{what} must be text, got {value!r}")
    return value.strip()


def normalize_halt_id(value: Any) -> str:
    """The canonical halt id a word names.

    A halt id is one word of letters, digits,
    dashes, underscores and dots, read with its
    case kept. Anything else raises.
    """
    if isinstance(value, str):
        wanted = value.strip()
        if wanted and all(ch in _HALT_ID_CHARS for ch in wanted):
            return wanted
    raise ValueError(
        f"a halt id must be a non-empty word of letters, "
        f"digits, dashes, underscores and dots, got {value!r}")


def normalize_halt_target(value: Any) -> str:
    """The canonical halt target a word names.

    Reads ``coder`` (or ``agent``), ``crew`` (or
    ``fleet``), ``background_jobs`` (or
    ``background`` / ``jobs``) and ``approvals``
    (or ``approval``), case-insensitively, with
    dashes and spaces read as underscores.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace("-", "_").replace(" ", "_")
        if wanted in _TARGET_WORDS:
            return _TARGET_WORDS[wanted]
    raise ValueError(
        "a halt target must be one of %s, got %r"
        % ("/".join(HALT_TARGETS), value))


def _canonical_targets(values: Any) -> Tuple[str, ...]:
    """Halt targets as a validated canonical-order tuple.

    A single word names one target; a list names
    several. The result is deduplicated and put in
    roadmap (``HALT_TARGETS``) order, and an empty
    naming refuses: a halt that names no target
    halts nothing, and that is a refusal, not a
    reading.
    """
    if isinstance(values, str):
        values = (values,)
    if isinstance(values, (str, bytes)) \
            or not isinstance(values, (list, tuple)):
        raise ValueError(
            f"halt targets must be a target word or a list of "
            f"target words, got {values!r}")
    if not values:
        raise ValueError("a halt must name at least one target")
    named = {normalize_halt_target(word) for word in values}
    return tuple(target for target in HALT_TARGETS if target in named)


def _pick(mapping: Dict[str, Any], names: Tuple[str, ...],
          what: str) -> Any:
    """One field from its spellings, or a refusal on conflict."""
    found = [name for name in names if name in mapping]
    if not found:
        return None
    first = mapping[found[0]]
    for name in found[1:]:
        if mapping[name] != first:
            raise ValueError(f"a halt record names two different {what}")
    return first


def _check_bool(value: Any, what: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{what} must be true or false, got {value!r}")
    return value


def _check_pending(value: Any) -> int:
    """Approvals pending: a whole number of 0 or more."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(
            f"pending approvals must be a whole number, got {value!r}")
    if value < 0:
        raise ValueError(
            f"pending approvals must not be negative, got {value!r}")
    return value


# ---------------------------------------------------------------------
# The halt: one switch pulled, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class Halt:
    """One halt: its targets, who asked, and why, as data.

    ``targets`` names what the halt halts, in
    roadmap order; by default it names all four
    targets - one switch halts everything. A
    scoped halt naming a subset is data too.
    ``actor`` is who or what asked, in words (it
    may be empty when nobody is named); ``reason``
    is the reason as text (likewise). A halt is a
    request held as data: it has, by itself,
    stopped nothing yet.

    Constructing one validates it, so a Halt that
    exists is a halt the agent layer could carry
    out.
    """

    targets: Tuple[str, ...] = HALT_TARGETS
    actor: str = ""
    reason: str = ""
    halt_id: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "targets", _canonical_targets(self.targets))
        object.__setattr__(self, "actor", _loose_text(self.actor, "an actor"))
        object.__setattr__(
            self, "reason", _loose_text(self.reason, "a halt reason"))
        if self.halt_id is not None:
            object.__setattr__(
                self, "halt_id", normalize_halt_id(self.halt_id))

    @property
    def display_label(self) -> str:
        name = self.halt_id or "halt"
        if self.actor:
            return f"{name} (pulled by {self.actor})"
        return name

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "halt",
            "slice": KILL_SWITCH_SLICE,
            "halt_id": self.halt_id,
            "targets": list(self.targets),
            "actor": self.actor,
            "reason": self.reason,
        }


def validate_halt(halt: Any) -> Halt:
    """Validate one halt into a Halt.

    Accepts a Halt or a mapping naming an
    optional ``halt_id`` (or ``id``), an ``actor``
    (or ``requested_by`` / ``by`` / ``who``), a
    ``reason`` (or ``why``), and ``targets`` (or
    ``target`` / ``scope``): one target word or a
    list of them, read through
    ``normalize_halt_target``. Naming two
    spellings of one field with different values
    refuses, and unknown keys refuse.
    """
    if isinstance(halt, Halt):
        return halt
    if not isinstance(halt, dict):
        raise ValueError(f"a halt must be a mapping, got {halt!r}")
    unknown = set(halt) - _HALT_KEYS
    if unknown:
        raise ValueError(
            "unknown halt keys: %s" % ", ".join(sorted(unknown)))
    kwargs: Dict[str, Any] = {}
    halt_id = _pick(halt, ("halt_id", "id"), "halt ids")
    if halt_id is not None:
        kwargs["halt_id"] = halt_id
    actor = _pick(halt, ("actor", "requested_by", "by", "who"), "actors")
    if actor is not None:
        kwargs["actor"] = actor
    reason = _pick(halt, ("reason", "why"), "reasons")
    if reason is not None:
        kwargs["reason"] = reason
    targets = _pick(halt, ("targets", "target", "scope"), "targets")
    if targets is not None:
        kwargs["targets"] = targets
    return Halt(**kwargs)


def build_halt(halt: Any = None, **kwargs: Any) -> Halt:
    """Build one validated halt from a mapping or field words."""
    if isinstance(halt, Halt) and not kwargs:
        return halt
    if isinstance(halt, dict) or halt is None:
        merged: Dict[str, Any] = {}
        if isinstance(halt, dict):
            merged.update(halt)
        merged.update(kwargs)
        return validate_halt(merged)
    raise ValueError(f"a halt must be a mapping, got {halt!r}")


def _require_halt(halt: Any) -> Halt:
    if isinstance(halt, Halt):
        return halt
    return validate_halt(halt)


# ---------------------------------------------------------------------
# The holdings reading: what the session actually holds, as data.
# ---------------------------------------------------------------------


def _coerce_entries(value: Any, what: str, id_words: Tuple[str, ...],
                    state_words: Tuple[str, ...],
                    states: Tuple[str, ...]) -> Tuple[Tuple[str, str], ...]:
    """Held (id, state) pairs for one target, validated whole.

    Each entry names its id and its state: as a
    mapping (the id under any of ``id_words``, the
    state under any of ``state_words``), as an
    (id, state) pair, or as an object carrying the
    id and state as attributes under the first of
    each spelling. State words read
    case-insensitively with dashes as underscores;
    an unknown state refuses.
    """
    if value is None:
        return ()
    if isinstance(value, (str, bytes)) \
            or not isinstance(value, (list, tuple)):
        raise ValueError(f"{what} must be a list of held entries")
    entries = []
    for entry in value:
        if isinstance(entry, dict):
            ident = _pick(entry, id_words, f"{what} ids")
            state = _pick(entry, state_words, f"{what} states")
            if ident is None or state is None:
                raise ValueError(
                    f"a {what} entry must name its id and its state")
        elif isinstance(entry, (list, tuple)) and len(entry) == 2:
            ident, state = entry
        else:
            ident = getattr(entry, id_words[0], None)
            state = getattr(entry, state_words[0], None)
            if ident is None or state is None:
                raise ValueError(
                    f"a {what} entry must name its id and its state")
        if not isinstance(ident, str) or not ident.strip():
            raise ValueError(
                f"a {what} id must be non-empty text, got {ident!r}")
        if not isinstance(state, str):
            raise ValueError(
                f"a {what} state must be a word, got {state!r}")
        wanted = state.strip().lower().replace("-", "_")
        if wanted not in states:
            raise ValueError(
                "a %s state must be one of %s, got %r"
                % (what, "/".join(states), state))
        entries.append((ident.strip(), wanted))
    return tuple(entries)


@dataclass(frozen=True)
class HaltHoldings:
    """What the session actually holds, as data.

    ``coder_active`` says whether the coder itself
    is at work. ``background_jobs`` names each held
    background job and its state, in the M-103
    job-state words; ``crew_tasks`` names each crew
    task and its status, in the M-106 crew-status
    words. ``pending_approvals`` counts the
    approvals still waiting for an answer. A
    reading of nothing held - coder at rest, no
    jobs, no tasks, no approvals - is a quiet
    session, not an error.

    Constructing one validates it, so a reading
    that exists never names a state its own
    vocabulary does not know.
    """

    coder_active: bool = False
    background_jobs: Tuple[Tuple[str, str], ...] = ()
    crew_tasks: Tuple[Tuple[str, str], ...] = ()
    pending_approvals: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "coder_active",
            _check_bool(self.coder_active, "coder_active"))
        object.__setattr__(
            self, "background_jobs",
            _coerce_entries(
                self.background_jobs, "background job",
                ("job_id", "id"), ("state", "status"), BACKGROUND_STATES))
        object.__setattr__(
            self, "crew_tasks",
            _coerce_entries(
                self.crew_tasks, "crew task",
                ("task_id", "id"), ("status", "state"), CREW_STATUSES))
        object.__setattr__(
            self, "pending_approvals",
            _check_pending(self.pending_approvals))

    @property
    def background_active_ids(self) -> Tuple[str, ...]:
        """Held jobs still live: queued or running, in listed order."""
        return tuple(
            ident for ident, state in self.background_jobs
            if state in BACKGROUND_ACTIVE_STATES)

    @property
    def background_finished_ids(self) -> Tuple[str, ...]:
        """Held jobs already stopped, in listed order."""
        return tuple(
            ident for ident, state in self.background_jobs
            if state in BACKGROUND_TERMINAL_STATES)

    @property
    def crew_running_ids(self) -> Tuple[str, ...]:
        """Crew tasks running now, in listed order."""
        return tuple(
            ident for ident, status in self.crew_tasks
            if status == "running")

    @property
    def crew_queued_ids(self) -> Tuple[str, ...]:
        """Crew tasks merely queued - plans, not held work."""
        return tuple(
            ident for ident, status in self.crew_tasks
            if status == "queued")

    @property
    def crew_finished_ids(self) -> Tuple[str, ...]:
        """Crew tasks already stopped, in listed order."""
        return tuple(
            ident for ident, status in self.crew_tasks
            if status in CREW_FINISHED_STATUSES)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "halt_holdings",
            "slice": KILL_SWITCH_SLICE,
            "coder_active": self.coder_active,
            "background_jobs": [
                {"job_id": ident, "state": state}
                for ident, state in self.background_jobs],
            "crew_tasks": [
                {"task_id": ident, "status": status}
                for ident, status in self.crew_tasks],
            "pending_approvals": self.pending_approvals,
        }


#: The plainer word for a holdings reading.
Holdings = HaltHoldings


def validate_holdings(holdings: Any) -> HaltHoldings:
    """Validate one holdings reading into a HaltHoldings.

    Accepts a HaltHoldings or a mapping naming any
    of: ``coder_active`` (or ``coder`` /
    ``coder_working``), ``background_jobs`` (or
    ``jobs``), ``crew_tasks`` (or ``crew`` /
    ``fleet_tasks``), and ``pending_approvals``
    (or ``approvals_pending``; an ``approvals``
    naming may be the count itself or a list of
    pending approvals, counted). Unnamed holdings
    read as nothing held. Naming two spellings of
    one field with different values refuses, and
    unknown keys refuse.
    """
    if isinstance(holdings, HaltHoldings):
        return holdings
    if not isinstance(holdings, dict):
        raise ValueError(
            f"a holdings reading must be a mapping, got {holdings!r}")
    unknown = set(holdings) - _HOLDINGS_KEYS
    if unknown:
        raise ValueError(
            "unknown holdings keys: %s" % ", ".join(sorted(unknown)))
    kwargs: Dict[str, Any] = {}
    coder = _pick(
        holdings, ("coder_active", "coder", "coder_working"), "coder states")
    if coder is not None:
        kwargs["coder_active"] = coder
    jobs = _pick(holdings, ("background_jobs", "jobs"), "background jobs")
    if jobs is not None:
        kwargs["background_jobs"] = jobs
    crew = _pick(
        holdings, ("crew_tasks", "crew", "fleet_tasks"), "crew tasks")
    if crew is not None:
        kwargs["crew_tasks"] = crew
    pending = _pick(
        holdings, ("pending_approvals", "approvals_pending"),
        "pending approvals")
    approvals = holdings.get("approvals")
    if approvals is not None:
        counted = len(approvals) if isinstance(approvals, (list, tuple)) \
            else approvals
        if pending is not None and counted != pending:
            raise ValueError(
                "a holdings reading names two different pending "
                "approval counts")
        pending = counted
    if pending is not None:
        kwargs["pending_approvals"] = pending
    return HaltHoldings(**kwargs)


def build_holdings(holdings: Any = None, **kwargs: Any) -> HaltHoldings:
    """Build one validated holdings reading."""
    if isinstance(holdings, HaltHoldings) and not kwargs:
        return holdings
    if isinstance(holdings, dict) or holdings is None:
        merged: Dict[str, Any] = {}
        if isinstance(holdings, dict):
            merged.update(holdings)
        merged.update(kwargs)
        return validate_holdings(merged)
    raise ValueError(
        f"a holdings reading must be a mapping, got {holdings!r}")


def _require_holdings(holdings: Any) -> HaltHoldings:
    if isinstance(holdings, HaltHoldings):
        return holdings
    if holdings is None:
        return HaltHoldings()
    return validate_holdings(holdings)


# ---------------------------------------------------------------------
# The verdict: one halt judged against one holdings reading,
# mechanically.
# ---------------------------------------------------------------------


def _classify(targets: Tuple[str, ...], coder_active: bool,
              background_active: Tuple[str, ...],
              background_finished: Tuple[str, ...],
              crew_running: Tuple[str, ...],
              crew_finished: Tuple[str, ...],
              pending_approvals: int):
    """The (outcomes, status) a holdings reading earns, mechanically.

    ``outcomes`` is (target, outcome) pairs in
    roadmap order over the halt's targets. A
    target is halted only when live work is held
    for it; already stopped when its work exists
    but has finished; nothing held otherwise. The
    status is the strongest outcome earned:
    halted when any target halted, already stopped
    when none halted and any was already stopped,
    nothing held when no target held anything.
    """
    outcomes = []
    for target in targets:
        if target == "coder":
            outcome = "halted" if coder_active else "already_stopped"
        elif target == "crew":
            if crew_running:
                outcome = "halted"
            elif crew_finished:
                outcome = "already_stopped"
            else:
                outcome = "nothing_held"
        elif target == "background_jobs":
            if background_active:
                outcome = "halted"
            elif background_finished:
                outcome = "already_stopped"
            else:
                outcome = "nothing_held"
        else:  # approvals
            outcome = "halted" if pending_approvals > 0 else "nothing_held"
        outcomes.append((target, outcome))
    earned = [outcome for _, outcome in outcomes]
    if "halted" in earned:
        status = "halted"
    elif "already_stopped" in earned:
        status = "already_stopped"
    else:
        status = "nothing_held"
    return tuple(outcomes), status


def _check_id_tuple(value: Any, what: str) -> Tuple[str, ...]:
    if isinstance(value, (str, bytes)) \
            or not isinstance(value, (list, tuple)):
        raise ValueError(f"{what} must be a list of ids")
    cleaned = []
    for ident in value:
        if not isinstance(ident, str) or not ident.strip():
            raise ValueError(f"{what} must name ids as text, got {ident!r}")
        cleaned.append(ident.strip())
    return tuple(cleaned)


@dataclass(frozen=True)
class HaltVerdict:
    """One halt judged against one holdings reading, as data.

    ``outcomes`` names each target's reading -
    halted, already stopped, or nothing held - and
    ``status`` is the strongest of them. The
    holdings the verdict was judged from are
    carried alongside (the coder's state, the held
    jobs and crew tasks by the reading they earned,
    and the pending approval count), and the
    outcomes and status are validated against
    those holdings on construction, so a verdict
    that exists never disagrees with itself.
    """

    halt_id: Optional[str] = None
    actor: str = ""
    reason: str = ""
    targets: Tuple[str, ...] = HALT_TARGETS
    outcomes: Tuple[Tuple[str, str], ...] = ()
    status: str = "nothing_held"
    coder_active: bool = False
    background_active_ids: Tuple[str, ...] = ()
    background_finished_ids: Tuple[str, ...] = ()
    crew_running_ids: Tuple[str, ...] = ()
    crew_queued_ids: Tuple[str, ...] = ()
    crew_finished_ids: Tuple[str, ...] = ()
    pending_approvals: int = 0

    def __post_init__(self) -> None:
        if self.halt_id is not None:
            object.__setattr__(
                self, "halt_id", normalize_halt_id(self.halt_id))
        object.__setattr__(self, "actor", _loose_text(self.actor, "an actor"))
        object.__setattr__(
            self, "reason", _loose_text(self.reason, "a halt reason"))
        object.__setattr__(
            self, "targets", _canonical_targets(self.targets))
        object.__setattr__(
            self, "coder_active",
            _check_bool(self.coder_active, "coder_active"))
        for field_name in (
                "background_active_ids", "background_finished_ids",
                "crew_running_ids", "crew_queued_ids",
                "crew_finished_ids"):
            object.__setattr__(
                self, field_name,
                _check_id_tuple(getattr(self, field_name), field_name))
        object.__setattr__(
            self, "pending_approvals",
            _check_pending(self.pending_approvals))
        if not isinstance(self.status, str) \
                or self.status.strip().lower().replace("-", "_") \
                not in HALT_STATUSES:
            raise ValueError(
                "a halt verdict status must be one of %s, got %r"
                % ("/".join(HALT_STATUSES), self.status))
        object.__setattr__(
            self, "status",
            self.status.strip().lower().replace("-", "_"))
        if isinstance(self.outcomes, (str, bytes)) \
                or not isinstance(self.outcomes, (list, tuple)):
            raise ValueError(
                "a halt verdict's outcomes must be (target, outcome) "
                "pairs")
        cleaned = []
        for pair in self.outcomes:
            if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                raise ValueError(
                    "a halt verdict's outcomes must be (target, "
                    "outcome) pairs")
            target_word, outcome_word = pair
            target = normalize_halt_target(target_word)
            if not isinstance(outcome_word, str) \
                    or outcome_word.strip().lower().replace("-", "_") \
                    not in HALT_OUTCOMES:
                raise ValueError(
                    "a halt outcome must be one of %s, got %r"
                    % ("/".join(HALT_OUTCOMES), outcome_word))
            cleaned.append(
                (target, outcome_word.strip().lower().replace("-", "_")))
        object.__setattr__(self, "outcomes", tuple(cleaned))
        wanted_outcomes, wanted_status = _classify(
            self.targets, self.coder_active,
            self.background_active_ids, self.background_finished_ids,
            self.crew_running_ids, self.crew_finished_ids,
            self.pending_approvals)
        if tuple(self.outcomes) != wanted_outcomes:
            raise ValueError(
                "a halt verdict's outcomes disagree with its "
                "holdings")
        if self.status != wanted_status:
            raise ValueError(
                f"a halt verdict with these holdings is "
                f"{wanted_status}, got {self.status!r}")

    @property
    def outcome_map(self) -> Dict[str, str]:
        """Each named target's outcome, by target."""
        return dict(self.outcomes)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "halt_verdict",
            "slice": KILL_SWITCH_SLICE,
            "halt_id": self.halt_id,
            "actor": self.actor,
            "reason": self.reason,
            "targets": list(self.targets),
            "outcomes": dict(self.outcomes),
            "status": self.status,
            "coder_active": self.coder_active,
            "background_active": list(self.background_active_ids),
            "background_finished": list(self.background_finished_ids),
            "crew_running": list(self.crew_running_ids),
            "crew_queued": list(self.crew_queued_ids),
            "crew_finished": list(self.crew_finished_ids),
            "pending_approvals": self.pending_approvals,
        }


def validate_verdict(verdict: Any) -> HaltVerdict:
    """Validate one verdict into a HaltVerdict.

    A verdict is normally made by ``judge_halt``;
    this accepts a HaltVerdict unchanged, so a
    caller holding one needs no second road.
    """
    if isinstance(verdict, HaltVerdict):
        return verdict
    raise ValueError(f"a halt verdict is needed, got {verdict!r}")


def _require_verdict(verdict: Any) -> HaltVerdict:
    return validate_verdict(verdict)


def judge_halt(halt: Any, holdings: Any = None) -> HaltVerdict:
    """Judge one halt against one holdings reading, mechanically.

    ``halt`` is a Halt (or halt mapping) and
    ``holdings`` a HaltHoldings (or holdings
    mapping); with no holdings named, nothing is
    held. A target is halted only when the reading
    shows live work for it, already stopped when
    its work has finished, and nothing held when
    the session holds nothing for it. No other
    signal moves the verdict.
    """
    checked_halt = _require_halt(halt)
    checked_holdings = _require_holdings(holdings)
    outcomes, status = _classify(
        checked_halt.targets, checked_holdings.coder_active,
        checked_holdings.background_active_ids,
        checked_holdings.background_finished_ids,
        checked_holdings.crew_running_ids,
        checked_holdings.crew_finished_ids,
        checked_holdings.pending_approvals)
    return HaltVerdict(
        halt_id=checked_halt.halt_id, actor=checked_halt.actor,
        reason=checked_halt.reason, targets=checked_halt.targets,
        outcomes=outcomes, status=status,
        coder_active=checked_holdings.coder_active,
        background_active_ids=checked_holdings.background_active_ids,
        background_finished_ids=checked_holdings.background_finished_ids,
        crew_running_ids=checked_holdings.crew_running_ids,
        crew_queued_ids=checked_holdings.crew_queued_ids,
        crew_finished_ids=checked_holdings.crew_finished_ids,
        pending_approvals=checked_holdings.pending_approvals)


_TARGET_LABELS = {
    "coder": "the coder",
    "crew": "the crew",
    "background_jobs": "background jobs",
    "approvals": "pending approvals",
}


def _outcome_phrase(target: str, verdict: HaltVerdict) -> str:
    """One target's outcome, in plain words with its held names."""
    outcome = verdict.outcome_map[target]
    label = _TARGET_LABELS[target]
    if target == "coder":
        if outcome == "halted":
            return "the coder halted (it was at work)"
        return "the coder already stopped (it was at rest)"
    if target == "background_jobs":
        if outcome == "halted":
            names = ", ".join(verdict.background_active_ids)
            return f"background jobs halted ({names})"
        if outcome == "already_stopped":
            names = ", ".join(verdict.background_finished_ids)
            return f"background jobs already stopped ({names})"
        return "background jobs: nothing held"
    if target == "crew":
        if outcome == "halted":
            names = ", ".join(verdict.crew_running_ids)
            return f"the crew halted (running: {names})"
        if outcome == "already_stopped":
            names = ", ".join(verdict.crew_finished_ids)
            return f"the crew already stopped ({names})"
        if verdict.crew_queued_ids:
            names = ", ".join(verdict.crew_queued_ids)
            return (
                f"the crew: nothing held (queued tasks are plans, "
                f"not running work: {names})")
        return "the crew: nothing held"
    if outcome == "halted":
        count = verdict.pending_approvals
        word = "approval" if count == 1 else "approvals"
        return f"pending approvals halted ({count} {word} refused)"
    return "pending approvals: nothing held"


def _halt_headline(verdict: HaltVerdict) -> str:
    name = verdict.halt_id or "halt"
    phrases = "; ".join(
        _outcome_phrase(target, verdict) for target in verdict.targets)
    headline = f"Kill switch pulled ({name}): {phrases}."
    if verdict.actor:
        headline += f" Pulled by {verdict.actor}."
    if verdict.reason:
        headline += f" Reason: {verdict.reason}."
    return headline


def halt_record(halt: Any, holdings: Any = None,
                verdict: Any = None) -> Dict[str, Any]:
    """The session-news record of one pulled switch.

    Every judged halt yields a record - the agent
    layer publishes this record as a session event,
    so a pull is always news and can never be lost
    as a mere log line. ``verdict``, when given, is
    the reading announced instead of a fresh one.
    """
    judged = _require_verdict(verdict) if verdict is not None \
        else judge_halt(halt, holdings)
    return {
        "type": "kill_switch_pulled",
        "news": True,
        "slice": KILL_SWITCH_SLICE,
        "halt_id": judged.halt_id,
        "actor": judged.actor,
        "reason": judged.reason,
        "targets": list(judged.targets),
        "outcomes": dict(judged.outcomes),
        "status": judged.status,
        "coder_active": judged.coder_active,
        "background_active": list(judged.background_active_ids),
        "background_finished": list(judged.background_finished_ids),
        "crew_running": list(judged.crew_running_ids),
        "crew_queued": list(judged.crew_queued_ids),
        "crew_finished": list(judged.crew_finished_ids),
        "pending_approvals": judged.pending_approvals,
        "headline": _halt_headline(judged),
    }


# ---------------------------------------------------------------------
# The registry model: halts held in the order pulled, ids
# deterministic; the verdict each pull earned held alongside it.
# ---------------------------------------------------------------------


class HaltRegistry:
    """An in-memory registry of halts.

    Halts are held in the order pulled. Ids are
    deterministic: a caller-supplied id is used as
    given (a duplicate refuses), and an unsupplied
    id is the next ``halt-N`` in sequence, skipping
    any number a supplied id already took - no
    randomness a test cannot pin. The verdict a
    pull earned, judged against the holdings at
    pull time, is held alongside its halt; judging
    is a historical reading, never re-judged from
    later holdings. Storage beyond memory (a
    session's journal, a file) is the agent layer's
    concern; this model is neutral.
    """

    def __init__(self) -> None:
        self._halts: Dict[str, Halt] = {}
        self._verdicts: Dict[str, HaltVerdict] = {}
        self._next = 1

    def _fresh_id(self) -> str:
        while f"halt-{self._next}" in self._halts:
            self._next += 1
        halt_id = f"halt-{self._next}"
        self._next += 1
        return halt_id

    def register(self, halt: Any = None, **kwargs: Any) -> Halt:
        """Register one halt and hold it; duplicate ids refuse."""
        if kwargs and isinstance(halt, (Halt, dict)):
            validated = build_halt(halt, **kwargs)
        elif kwargs and halt is None:
            validated = build_halt(**kwargs)
        else:
            if kwargs:
                raise ValueError(
                    "a halt is named twice: as a record and as "
                    "field words")
            validated = _require_halt(halt)
        if validated.halt_id is None:
            validated = replace(validated, halt_id=self._fresh_id())
        elif validated.halt_id in self._halts:
            raise ValueError(
                f"a halt named {validated.halt_id!r} already exists")
        self._halts[validated.halt_id] = validated
        return validated

    def get(self, halt_id: Any) -> Halt:
        """The halt one id names; an unknown id raises KeyError."""
        wanted = normalize_halt_id(halt_id)
        if wanted not in self._halts:
            raise KeyError(f"unknown halt: {wanted!r}")
        return self._halts[wanted]

    def list_halts(self) -> Tuple[Halt, ...]:
        """Every held halt, in the order pulled."""
        return tuple(self._halts.values())

    def judge(self, halt_id: Any, holdings: Any = None) -> HaltVerdict:
        """Judge one held halt against a holdings reading.

        The verdict is held alongside the halt,
        replacing any older verdict for it: a halt
        is judged at its pull, against the holdings
        of that moment. A halt the registry does not
        hold raises KeyError.
        """
        halt = self.get(halt_id)
        verdict = judge_halt(halt, holdings)
        self._verdicts[halt.halt_id] = verdict
        return verdict

    def get_verdict(self, halt_id: Any) -> Optional[HaltVerdict]:
        """One held halt's judged verdict, or None when unjudged."""
        halt = self.get(halt_id)
        return self._verdicts.get(halt.halt_id)

    def list_verdicts(self) -> Tuple[HaltVerdict, ...]:
        """Every judged verdict, in the order the halts were pulled."""
        return tuple(
            self._verdicts[halt.halt_id]
            for halt in self.list_halts()
            if halt.halt_id in self._verdicts)

    def record(self, halt_id: Any,
               holdings: Any = None) -> Dict[str, Any]:
        """One held halt's news record.

        The halt's held verdict is announced; when
        the halt has not been judged yet it is
        judged now against ``holdings`` (nothing
        held when none is named) and that verdict
        is held.
        """
        halt = self.get(halt_id)
        verdict = self._verdicts.get(halt.halt_id)
        if verdict is None:
            verdict = self.judge(halt.halt_id, holdings)
        return halt_record(None, None, verdict)


# ---------------------------------------------------------------------
# The /halt surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------


def format_halt(halt: Any, verdict: Any = None) -> str:
    """One halt, in plain words, with its verdict when one is given."""
    current = _require_halt(halt)
    checked = _require_verdict(verdict) if verdict is not None else None
    if checked is not None and current.halt_id is not None \
            and checked.halt_id != current.halt_id:
        raise ValueError(
            f"a verdict for halt {checked.halt_id!r} does not "
            f"judge halt {current.halt_id!r}")
    name = current.halt_id or "halt"
    targets = ", ".join(
        _TARGET_LABELS[target] for target in current.targets)
    line = f"{name}: kill switch - targets: {targets}."
    if current.actor:
        line += f" Pulled by {current.actor}."
    if current.reason:
        line += f" Reason: {current.reason}."
    if checked is not None:
        line += f" Verdict: {checked.status}."
    return line


def format_halts(source: Any = None, verdicts: Any = None) -> str:
    """The halts, in plain words, in the order given.

    With no halts at all the text starts with the
    plain statement of that fact. Every line states
    its halt's targets in words.
    """
    if source is None:
        selected: Tuple[Halt, ...] = ()
        by_id: Dict[str, HaltVerdict] = {}
    elif isinstance(source, HaltRegistry):
        selected = source.list_halts()
        by_id = {v.halt_id: v for v in source.list_verdicts()}
    elif isinstance(source, (list, tuple)):
        selected = tuple(_require_halt(h) for h in source)
        by_id = {}
        if verdicts is not None:
            if isinstance(verdicts, (str, bytes)) \
                    or not isinstance(verdicts, (list, tuple)):
                raise ValueError("halt verdicts must be a list of verdicts")
            by_id = {
                v.halt_id: _require_verdict(v) for v in verdicts}
    else:
        raise ValueError("halts must be a registry or a list of halts")
    if not selected:
        return "Kill switch: none pulled. No halt is held."
    lines = [f"Kill switch: {len(selected)} pulled."]
    for halt in selected:
        verdict = by_id.get(halt.halt_id) \
            if halt.halt_id is not None else None
        lines.append(f"  {format_halt(halt, verdict)}")
    return "\n".join(lines)


def format_verdict(verdict: Any = None, holdings: Any = None) -> str:
    """One halt verdict, in plain words, outcomes always stated.

    Accepts a HaltVerdict, or a Halt (or halt
    mapping) judged against ``holdings``.
    """
    if isinstance(verdict, HaltVerdict):
        judged = verdict
    elif verdict is not None:
        judged = judge_halt(verdict, holdings)
    else:
        raise ValueError("format_verdict needs a verdict or a halt")
    phrases = "; ".join(
        _outcome_phrase(target, judged) for target in judged.targets)
    return f"Halt verdict: {judged.status} - {phrases}."


def format_halt_record(record: Any) -> str:
    """One halt news record as its plain headline."""
    if isinstance(record, dict) \
            and record.get("type") == "kill_switch_pulled":
        return str(record["headline"])
    raise ValueError("format_halt_record needs a halt record")


#: The halt record's formatter under its own name.
format_record = format_halt_record


def format_halts_screen(source: Any = None, verdicts: Any = None) -> str:
    """The whole slice, in plain words, for /halt."""
    lines = ["Kill switch (M-108) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_halts(source, verdicts))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_halt_args(args: Any) -> Tuple[str, Optional[str]]:
    """Parse the /halt grammar both surfaces share.

    No words (or ``show``) shows the halts;
    ``show <halt>`` and a bare halt id show one
    halt; ``pull`` pulls the switch on every
    target and ``pull <target>`` pulls it on one
    target alone (``pull all`` is ``pull``). A
    grammar word in the wrong shape - a bare
    target word, a doubled word - is a usage
    error naming the grammar, never a halt id.
    Returns ``(action, halt-id-or-target-or-None)``:
    for ``show`` the second word is a halt id, for
    ``pull`` a canonical target.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None \
        else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() == "show":
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head == "pull":
        if len(words) == 1:
            return ("pull", None)
        if len(words) == 2:
            if words[1].lower() in _ALL_WORDS:
                return ("pull", None)
            try:
                return ("pull", normalize_halt_target(words[1]))
            except ValueError:
                raise ValueError(USAGE) from None
        raise ValueError(USAGE)
    if head == "show" and len(words) == 2:
        try:
            return ("show", normalize_halt_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head in ("show",) or len(words) != 1:
        raise ValueError(USAGE)
    lowered = words[0].lower().replace("-", "_")
    if lowered in _TARGET_WORDS or lowered in _ALL_WORDS:
        raise ValueError(USAGE)
    try:
        return ("show", normalize_halt_id(words[0]))
    except ValueError:
        raise ValueError(USAGE) from None
