"""Acceptance gates per slice (roadmap slice M-205).

Part IX - The Mythic Method Engine. The roadmap
words: *each slice carries its checks; the Auditor
(M-130) runs them; a slice banks only green -
"banked" is a state with evidence, not a feeling.*

What this slice adds: a gate book, in its own
module, standing in the M-195 copy-and-share book
shape the M-201 to M-204 books stand in. Each
slice in the book carries its gate: the checks
the gate runs, held as data in gate order against
an explicit gate sequence (CHECKS, TRANSITIONS).
An audit record holds one Auditor run of one
slice's gate: the slice it audits, the checks it
ran, and the evidence it holds, by kind. The
evidence kinds are a closed vocabulary in two
halves: held evidence - runner_output, compile_log,
neighbour_log, ledger_row, the evidence a green
standing may rest on - and bare claims - feeling,
memory, assertion, summary, which are not evidence
at all. An audit stands green only when it opens
at charter, steps only where the gate sequence
allows, rests on held evidence alone, and has
reached evidence; anything else stands red, named
in its gaps. A slice banks only green, and banked
is a state with evidence, never a feeling.

An audit stands only for an ACTIVE slice: a record
naming no held slice, or a queued one, refuses BY
NAME at book level. The audit's trace - its ran
checks as one line - is DERIVED at call time, and
a held trace record stands current only while it
agrees. The acceptance index, panel, verdict,
board, trace, order and current audit are DERIVED
at call time, never stored where they could drift,
and a stored one refuses BY NAME, as does a record
claiming a gate was actually run live, a slice
actually banked or pushed. The notes are held as
data beside the book. This layer runs no gate,
runs no Auditor, banks nothing, pushes nothing
and opens no network: it holds gate audits as
data and tells them.
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
    "ACCEPTANCE_RESOURCE",
    "ACCEPTANCE_SCHEMA",
    "ACCEPTANCE_SLICE",
    "ACCEPTANCE_RULE",
    "PLAIN_EXPLANATION",
    "THE_ACCEPTANCE_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "GREEN_WORDS",
    "SLICE_STATES",
    "Any",
    "Dict",
    "List",
    "Optional",
    "TraceRecord",
    "AuditRecord",
    "IndexEntry",
    "SliceRef",
    "NoteRecord",
    "AcceptanceBook",
    "AcceptanceIndex",
    "AcceptancePanel",
    "AcceptancePanelRow",
    "AcceptanceRegistry",
    "AcceptanceVerdict",
    "AcceptanceView",
    "TargetCount",
    "trace_for_audit",
    "trace_record",
    "board_record",
    "book_record",
    "build_trace",
    "build_book",
    "build_audit",
    "build_slice_ref",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "current_audit",
    "transition_breaks",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "audit_for_check",
    "audit_order",
    "audit_record",
    "first_note",
    "format_book",
    "format_audit",
    "format_index",
    "format_note",
    "format_check",
    "format_panel",
    "format_acceptance_screen",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "slice_record",
    "load_acceptance",
    "load_acceptance_file",
    "normalize_slice_state",
    "normalize_check",
    "normalize_claim_kind",
    "legal_step",
    "next_check",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_audit",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_acceptance_args",
    "green_audits",
    "plain_lines",
    "plain_words",
    "roadmap_record",
    "segment_of",
    "trace_of",
    "trace_current",
    "shown_audits",
    "validate_trace",
    "validate_book",
    "validate_audit",
    "validate_slice_ref",
    "validate_note",
    "validate_panel",
    "validate_row",
    "validate_verdict",
    "validate_view",
    "verdict_plain_words",
    "verdict_record",
    "view_plain_words",
    "view_record",
    "audit_gaps",
    "audit_green",
    "audits_for_slice",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

ACCEPTANCE_SCHEMA = "mythic.acceptance_gates/1"
ACCEPTANCE_SLICE = "M-205"
THE_ACCEPTANCE_SLICE = ACCEPTANCE_SLICE
ACCEPTANCE_RESOURCE = "acceptance_gates.yaml"
INDEX_ACTION = "index"
EXAMPLE_CHECK = "evidence"
CHECK_FIELDS = ("checks", "claims")
GREEN_WORDS = ("green", "red")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "green", "red")
VERDICT_WORDS = ("bankable", "held", "blocked")
SLICE_STATES = ("active", "queued")
ACCEPTANCE_RULE = (
    "gate audits are held as data alone: each slice "
    "carries its checks, the Auditor (M-130) runs "
    "them against the explicit gate sequence - "
    "charter, build, test_suite, repair, evidence - "
    "and a slice banks only green, banked being a "
    "state with evidence held - runner output, "
    "compile log, neighbour log, ledger row - never "
    "a feeling, a memory, an assertion or a summary; "
    "holding, viewing and reading an audit runs no "
    "gate, banks nothing and opens no network")
PLAIN_EXPLANATION = (
    "Acceptance gates per slice (M-205): each "
    "slice carries its checks; the Auditor "
    "(M-130) runs them; a slice banks only "
    "green - banked is a state with evidence, "
    "not a feeling.")
USAGE = (
    "Usage: /acceptance | /acceptance audit <audit-id> | "
    "/acceptance check <check> | /acceptance slice <slice-id> | "
    "/acceptance view <view-id> | /acceptance note <note-id> | "
    "/acceptance index | /acceptance panel | /acceptance verdict")

CHECKS = ("charter", "build", "test_suite", "repair", "evidence")
HELD_EVIDENCE = ("runner_output", "compile_log", "neighbour_log", "ledger_row")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
CLAIM_KINDS = HELD_EVIDENCE + BARE_CLAIMS
TRANSITIONS = {
    "charter": ("build",),
    "build": ("test_suite",),
    "test_suite": ("repair", "evidence"),
    "repair": ("build", "test_suite"),
    "evidence": (),
}


def legal_step(before: Any, after: Any) -> bool:
    """Whether the gate sequence allows one step, DERIVED.

    The machine stands as data in TRANSITIONS:
    inspect steps only to build, build only to
    test, test to repair on a failure or to
    continue on a pass, repair back to build or
    test for the rerun, and continue steps
    nowhere - it is where a audit stands complete.
    A check outside the machine allows nothing.
    """
    return after in TRANSITIONS.get(before, ())


def next_check(check: Any, failed: Any = False) -> Optional[str]:
    """The check the gate takes next, DERIVED from the machine.

    Inspect leads to build and build to test;
    at test a failure steps to repair and a pass
    steps to continue; repair steps back to test
    for the rerun; continue is the end of the
    walk and steps nowhere. A check outside the
    machine refuses by name.
    """
    checked = normalize_check(check)
    if checked == "charter":
        return "build"
    if checked == "build":
        return "test_suite"
    if checked == "test_suite":
        return "repair" if failed else "evidence"
    if checked == "repair":
        return "test_suite"
    return None

_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_RUN_KEYS = frozenset({
    "audit_id", "seq", "slice_id", "title", "checks",
    "claims", "detail",
} | set(_PROVENANCE))
_SLICE_REF_KEYS = frozenset({
    "slice_id", "seq", "title", "state", "detail",
} | set(_PROVENANCE))
_TRACE_KEYS = frozenset({
    "trace_id", "seq", "audit_id", "trace", "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "audit_id", "stance", "target", "title",
    "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "standing", "green", "greens", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "entries", "coverage", "covered", "uncovered",
    "current_audit", "next_audit", "progress", "board",
    "current", "order", "breaks", "active"})
_LIVE_KEYS = (
    "live_audit", "audits_live", "live_gate",
    "audits_gate", "ran_gate", "audits_slice",
    "ran_slice", "builds_slice", "built_slice",
    "builds_live", "executes_slice", "executed_slice",
    "executes_live", "live_execution",
    "banks_slice", "banked_live", "banking_live",
    "pushes_slice", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_audit", "sent_audit",
    "posts_note", "posted_note", "traces_live",
    "traced_live")


# ---------------------------------------------------------------------
# Small judges, in the sibling trace.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_checks(value: Any) -> Tuple[str, ...]:
    """A audit's walked checks, held as data.

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
    """A audit's asked claims: claim kinds named as data.

    Each claim names one kind from the closed
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
                f"{what} claims a live gate audit or slice build "
                f"execution ({key!r} is named on it): "
                f"{ACCEPTANCE_RULE}")
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


def normalize_slice_state(value: Any) -> str:
    state = _clean_text(value, "an slice state").lower()
    if state not in SLICE_STATES:
        raise ValueError(
            f"slice state {state!r} is not one of the held "
            f"states: " + ", ".join(SLICE_STATES))
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
# The held audit: one slice cut from an active slice.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class AuditRecord:
    """One audit slice, held as data.

    The audit names the active slice it was
    audited from, by slice id, its title, its
    verifiable checks, held as data, and its
    claims, named by audit id. The grain is
    derived, never stored: exactly one verifiable
    walk is judged against the machine. A audit whose
    checks are not yet held stands with its
    checks empty: it stands red, named in
    its gaps, and no check is invented for it.
    The audit is local data alone - no live build
    stands behind it: holding it builds nothing.
    """

    audit_id: str
    seq: int
    slice_id: str
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
            self, "audit_id", _clean_text(self.audit_id, "a audit id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "slice_id", _clean_text(self.slice_id, "an slice id"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a audit title"))
        object.__setattr__(
            self, "checks", _check_checks(self.checks))
        object.__setattr__(
            self, "claims", _check_claims(self.claims))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a audit detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.audit_id

    @property
    def check(self) -> str:
        """The check the audit stands at: its last walked check."""
        return self.checks[-1] if self.checks else ""

    def to_record(self) -> Dict[str, Any]:
        record = {
            "audit_id": self.audit_id, "seq": self.seq,
            "slice_id": self.slice_id, "title": self.title,
            "checks": list(self.checks),
            "claims": list(self.claims),
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_audit_ref(value: Any) -> AuditRecord:
    if not isinstance(value, AuditRecord):
        raise ValueError("a audit must be a AuditRecord")
    return value


def validate_audit(audit: Any) -> AuditRecord:
    return _check_audit_ref(audit)


def build_audit(record: Any = None, **kwargs: Any) -> AuditRecord:
    """Build one held audit from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, AuditRecord):
        if kwargs:
            raise ValueError("a audit stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a audit must be a mapping or a AuditRecord")
    _needed(data, _RUN_KEYS, "a audit")
    return AuditRecord(
        audit_id=data.get("audit_id"), seq=data.get("seq"),
        slice_id=data.get("slice_id"), title=data.get("title"),
        checks=data.get("checks"),
        claims=data.get("claims"),
        detail=data.get("detail"),
        **_provenance(data))


def _breaks_map(book: Any) -> Dict[str, Tuple[str, ...]]:
    """Map each audit to the steps it took outside the machine.

    Derived from the held audits alone: a break is
    one consecutive pair of walked checks the
    explicit gate sequence does not allow, told
    in walk order as before, then after.
    """
    found: Dict[str, Tuple[str, ...]] = {}
    for audit in book.audits:
        breaks = tuple(
            f"{before} > {after}"
            for before, after in zip(audit.checks, audit.checks[1:])
            if not legal_step(before, after))
        if breaks:
            found[audit.audit_id] = breaks
    return found

def audit_gaps(audit: Any, source: Any = None) -> Tuple[str, ...]:
    """The gaps that keep a audit from standing green.

    Judged from the audit's own held fields alone -
    its walked checks against the explicit state
    machine, and its asked claims against the
    closed vocabulary: the gate opens at inspect,
    steps only where the machine allows, asks the
    human nothing the Auditor can answer, and a audit
    stands green only when it has reached
    continue. The source names nothing further:
    no gap is borrowed from another audit.
    """
    checked = _check_audit_ref(audit)
    gaps: List[str] = []
    if not checked.checks:
        gaps.append(
            "has passed through no check: the gate has not started")
        return tuple(gaps)
    if checked.checks[0] != "charter":
        gaps.append(
            f"opens at {checked.checks[0]}, not at charter: "
            f"the gate opens by reading the charter")
    for before, after in zip(checked.checks, checked.checks[1:]):
        if not legal_step(before, after):
            gaps.append(
                f"steps from {before} to {after}, which the "
                f"gate sequence does not allow")
    for kind in checked.claims:
        if kind in BARE_CLAIMS:
            gaps.append(
                f"asked a {kind} claim the Auditor can answer")
    if checked.checks[-1] != "evidence":
        gaps.append(
            f"has not reached evidence: the gate stands "
            f"at {checked.checks[-1]}")
    return tuple(gaps)

def audit_green(audit: Any, source: Any = None) -> bool:
    return not audit_gaps(audit, source)


def plain_lines(audit: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the audit's own fields."""
    checked = _check_audit_ref(audit)
    return (
        f"Audit: {checked.title}",
        f"Slice: {checked.slice_id}",
        f"Check: {checked.check if checked.check else 'none'}",
        f"Claims: "
        f"{', '.join(checked.claims) if checked.claims else 'none'}",
    )


def segment_of(audit: Any, source: Any = None) -> str:
    checked = _check_audit_ref(audit)
    gaps = audit_gaps(checked, source)
    return (
        f"{checked.audit_id}: {checked.title} - slice: "
        f"'{checked.slice_id}' - check: "
        f"'{checked.check if checked.check else 'none'}' - "
        f"checks: {len(checked.checks)} - claims: "
        f"'{', '.join(checked.claims) if checked.claims else 'none'}' - "
        f"detail: '{checked.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held slice reference: the active slice a book audits from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class SliceRef:
    """One slice a acceptance book audits from, held as a reference.

    The record names the slice, the title it
    opens and its standing - active or
    queued - held as data copied from the
    M-203 slice book's own telling. A audit
    stands only from an active reference: the
    book refuses a audit naming no held reference,
    and a audit from an queued one, BY NAME.
    """

    slice_id: str
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
            self, "slice_id", _clean_text(self.slice_id, "an slice id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a title"))
        object.__setattr__(
            self, "state", normalize_slice_state(self.state))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an slice detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.slice_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "slice_id": self.slice_id, "seq": self.seq,
            "title": self.title, "state": self.state,
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_slice_ref(value: Any) -> SliceRef:
    if not isinstance(value, SliceRef):
        raise ValueError("a slice reference must be an SliceRef")
    return value


def validate_slice_ref(ref: Any) -> SliceRef:
    return _check_slice_ref(ref)


def build_slice_ref(record: Any = None, **kwargs: Any) -> SliceRef:
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, SliceRef):
        if kwargs:
            raise ValueError(
                "a slice reference stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError(
            "a slice reference must be a mapping or an SliceRef")
    _needed(data, _SLICE_REF_KEYS, "a slice reference")
    return SliceRef(
        slice_id=data.get("slice_id"), seq=data.get("seq"),
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
    human active - the slice's audit ids in
    derived claim order, held exactly as
    active. The trace is of the set and its
    order, never of a step: when the derived
    trace moves, this record stands stale, named
    in the board, until a new trace is active.
    """

    trace_id: str
    seq: int
    audit_id: str
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
            self, "audit_id", _clean_text(self.audit_id, "an slice id"))
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
            "audit_id": self.audit_id, "trace": self.trace,
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
        audit_id=data.get("audit_id"), trace=data.get("trace"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held stance: a note on a audit, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One audit stance, held as data.

    The record names its audit, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per audit stance
    in a book. The record is data alone: holding
    it builds nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    audit_id: str
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
            self, "audit_id", _clean_text(self.audit_id, "a audit id"))
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
            "audit_id": self.audit_id, "stance": self.stance,
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
        audit_id=data.get("audit_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held view: which slices a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class AcceptanceView:
    """A view over the book: every audit, the green, the rest."""

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


def _check_view_ref(value: Any) -> AcceptanceView:
    if not isinstance(value, AcceptanceView):
        raise ValueError("a view must be an AcceptanceView")
    return value


def validate_view(view: Any) -> AcceptanceView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> AcceptanceView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, AcceptanceView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an AcceptanceView")
    _needed(data, _VIEW_KEYS, "a view")
    return AcceptanceView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class AcceptancePanelRow:
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


def _row_for_audit(audit: AuditRecord,
                     source: Any = None) -> AcceptancePanelRow:
    return AcceptancePanelRow(
        item_id=audit.audit_id,
        standing="green" if audit_green(audit, source) else "red",
        label=audit.title, segment=segment_of(audit, source),
        recorded_on=audit.recorded_on)


def _check_row_ref(value: Any) -> AcceptancePanelRow:
    if not isinstance(value, AcceptancePanelRow):
        raise ValueError("a panel row must be an AcceptancePanelRow")
    return value


def validate_row(row: Any, audit: Any = None,
                 source: Any = None) -> AcceptancePanelRow:
    checked = _check_row_ref(row)
    if audit is not None:
        derived = _row_for_audit(_check_audit_ref(audit), source)
        if checked != derived:
            raise ValueError(
                f"panel row {checked.item_id!r} does not agree with "
                f"the row derived from its audit")
    return checked


def build_row(row: Any = None, audit: Any = None,
              source: Any = None,
              **kwargs: Any) -> AcceptancePanelRow:
    if audit is not None:
        derived = _row_for_audit(_check_audit_ref(audit), source)
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            AcceptancePanelRow(**kwargs))
        return validate_row(built, audit, source)
    if isinstance(row, AcceptancePanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in GREEN_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return AcceptancePanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return AcceptancePanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an AcceptancePanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[AcceptancePanelRow, ...]
                 ) -> Tuple[TargetCount, ...]:
    counts: List[TargetCount] = []
    for standing in GREEN_WORDS:
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
        f"The acceptance book holds {total_items} audits as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {green_shown} of the shown audits "
        f"stand green.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its audit's own fields "
        "- the slice it audits, the checks it walked in the "
        "open and the claims it honestly carries - and no "
        "judgement is stored on any audit.",
        "Greenness is judged from the held records alone: "
        "a audit that steps outside the gate sequence, asks a "
        "claim the Auditor can answer, or has not reached "
        "continue stands red, named in its gaps, and the "
        "acceptance index is derived from the held audits, "
        "never stored where it could drift.",
    )

@dataclass(frozen=True)
class AcceptancePanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[AcceptancePanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> AcceptanceView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, AcceptanceView):
        return view
    return book.view_for(view)


def shown_audits(source: Any, view: Any = None
                   ) -> Tuple[AuditRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.audits
    if resolved.view_filter == "green":
        return tuple(g for g in book.audits if audit_green(g, book))
    return tuple(g for g in book.audits if not audit_green(g, book))


def audits_for_slice(source: Any, slice_id: Any
                      ) -> Tuple[AuditRecord, ...]:
    wanted = _clean_text(slice_id, "an slice id")
    return tuple(
        g for g in _source_book(source).audits if g.slice_id == wanted)


def green_audits(source: Any) -> Tuple[AuditRecord, ...]:
    book = _source_book(source)
    return tuple(g for g in book.audits if audit_green(g, book))


def current_audit(source: Any) -> Optional[AuditRecord]:
    """The book's current audit, DERIVED at call time.

    The first held audit, in held order, that does
    not yet stand green - where the Architect must
    look next. Nothing here is stored: the telling
    is derived from the held audits alone, so it can
    never go stale against them. A book whose every
    audit stands green has no current audit.
    """
    book = _source_book(source)
    for audit in book.audits:
        if not audit_green(audit, book):
            return audit
    return None


def derive_panel(source: Any, view: Any = None) -> AcceptancePanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_audits(book, resolved)
    rows = tuple(_row_for_audit(audit, book) for audit in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.audits), default="")
    green = sum(1 for g in shown if audit_green(g, book))
    return AcceptancePanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.audits), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.audits), len(shown), green, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> AcceptancePanel:
    if not isinstance(value, AcceptancePanel):
        raise ValueError("a panel must be an AcceptancePanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> AcceptancePanel:
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
                **kwargs: Any) -> AcceptancePanel:
    if isinstance(panel, AcceptancePanel):
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
        built = AcceptancePanel(
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
    raise ValueError("a panel must be a mapping, an AcceptancePanel, or derived")


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
        return "bankable"
    if green_shown == 0:
        return "blocked"
    return "held"


@dataclass(frozen=True)
class AcceptanceVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> AcceptanceVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_audits(book, resolved)
    green = sum(1 for g in shown if audit_green(g, book))
    latest = max((g.recorded_on for g in shown), default="")
    return AcceptanceVerdict(
        verdict=_verdict_word(len(shown), green),
        view_id=resolved.view_id, total_shown=len(shown),
        green_shown=green, latest_on=latest)


def _check_verdict_ref(value: Any) -> AcceptanceVerdict:
    if not isinstance(value, AcceptanceVerdict):
        raise ValueError("a verdict must be an AcceptanceVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> AcceptanceVerdict:
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
                  **kwargs: Any) -> AcceptanceVerdict:
    if isinstance(verdict, AcceptanceVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = AcceptanceVerdict(
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
        "a verdict must be a mapping, an AcceptanceVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held slices' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexEntry:
    check: str
    audit_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "check": self.check, "audit_id": self.audit_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class AcceptanceIndex:
    """The acceptance index, derived from the held audits.

    The index names one entry per green audit, in
    held order - the audit's own one verifiable
    check, its audit id and its title - and the
    audits that do not stand green, named in its
    gaps. Nothing here is stored on any audit: the
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


def derive_index(source: Any) -> AcceptanceIndex:
    """Derive the acceptance index from the book's held audits."""
    book = _source_book(source)
    entries = tuple(
        IndexEntry(check=g.check, audit_id=g.audit_id,
                   title=g.title)
        for g in book.audits if audit_green(g, book))
    gaps = tuple(
        g.audit_id for g in book.audits if not audit_green(g, book))
    return AcceptanceIndex(entries=entries, gaps=gaps)


def audit_for_check(source: Any, check: Any) -> Optional[AuditRecord]:
    """The first held audit one check reaches, or none - honestly."""
    if check is None:
        return None
    if not isinstance(check, str):
        raise ValueError("an check must be a string naming the check")
    wanted = check.strip()
    if not wanted:
        return None
    for audit in _source_book(source).audits:
        if audit.check == wanted:
            return audit
    return None


def transition_breaks(source: Any) -> Tuple[str, ...]:
    """Every step outside the gate sequence, DERIVED.

    One telling per break, in held order: the audit
    that took it and the step it took, before,
    then after. A book whose audits all walk inside
    the machine tells none.
    """
    book = _source_book(source)
    return tuple(
        f"{audit_id}: {step}"
        for audit_id, steps in _breaks_map(book).items()
        for step in steps)

def audit_order(source: Any,
              slice_id: Any = None) -> Tuple[AuditRecord, ...]:
    """The held audits in their held order, DERIVED at call time.

    Audits stand in the order the book holds them -
    the order their slices were taken - optionally
    for one slice alone. Nothing here is stored:
    the order is the book's own held order, told.
    """
    book = _source_book(source)
    audits = list(book.audits)
    if slice_id is not None:
        wanted = _clean_text(slice_id, "a slice id")
        audits = [r for r in audits if r.slice_id == wanted]
    return tuple(audits)

def trace_of(source: Any, audit_id: Any) -> str:
    """One audit's trace, DERIVED at call time.

    The audit's walked checks joined as one trace
    line, in walk order. A audit that has walked
    nowhere traces empty: the trace tells only
    what stands walked, and the walk is named
    elsewhere.
    """
    audit = _source_book(source).audit_for(audit_id)
    return " > ".join(audit.checks)

def trace_for_audit(source: Any,
                  audit_id: Any) -> Optional[TraceRecord]:
    """The held trace for one audit, or none - honestly."""
    wanted = _clean_text(audit_id, "a audit id")
    for record in _source_book(source).traces:
        if record.audit_id == wanted:
            return record
    return None

def trace_current(source: Any, audit_id: Any) -> bool:
    """Whether the held trace agrees with the derived trace.

    The trace stands current only while the trace
    it holds is the trace the book derives now; a
    moved walk leaves it stale, and no trace at
    all traces nothing.
    """
    trace = trace_for_audit(source, audit_id)
    if trace is None:
        return False
    return trace.trace == trace_of(source, audit_id)

def note_for_audit(source: Any, audit_id: Any,
                   stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one audit (and stance, when named)."""
    wanted = _clean_text(audit_id, "a audit id")
    for record in _source_book(source).notes:
        if record.audit_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the slice targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


def board_record(source: Any = None) -> Dict[str, Any]:
    """The acceptance board, DERIVED here from the held audits alone.

    The board counts the held audits by their
    derived greenness - green and red - names
    the current audit, the first that does not yet
    stand green, tells each held audit's trace
    standing - current while its held trace
    agrees with its derived trace, stale when it
    has moved, unheld while no trace stands for
    it - and names every step the held audits took
    outside the gate sequence. Nothing here is
    stored: the telling is derived at call time.
    """
    book = _source_book(source)
    standings = []
    for standing in GREEN_WORDS:
        number = sum(
            1 for g in book.audits
            if ("green" if audit_green(g, book) else "red") == standing)
        standings.append({"standing": standing, "audits": number})
    current = current_audit(book)
    traces = []
    for audit in book.audits:
        trace = trace_for_audit(book, audit.audit_id)
        if trace is None:
            standing = "unheld"
        elif trace_current(book, audit.audit_id):
            standing = "current"
        else:
            standing = "stale"
        traces.append({"audit_id": audit.audit_id, "trace": standing})
    return {
        "type": "acceptance_board",
        "slice": ACCEPTANCE_SLICE,
        "standings": standings,
        "total": len(book.audits),
        "current_audit": current.audit_id if current is not None else None,
        "traces": traces,
        "breaks": list(transition_breaks(book)),
    }

def roadmap_record() -> Dict[str, Any]:
    """This slice's own roadmap standing, proved from the roadmap itself.

    The record loads this repo's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 slices in 11 parts,
    the banked prefix, the next slice where the
    campaign resumes, and M-205's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(ACCEPTANCE_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "acceptance_roadmap",
        "slice": ACCEPTANCE_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m205_title": own.title,
        "m205_part": own.part,
        "m205_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: slices, audits, views, notes and trace traces held
# together, one pinned panel at most per telling, and no verdict,
# index, trace or order ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class AcceptanceBook:
    title: str
    slices: Tuple[SliceRef, ...] = ()
    audits: Tuple[AuditRecord, ...] = ()
    views: Tuple[AcceptanceView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    traces: Tuple[TraceRecord, ...] = ()
    panels: Tuple[AcceptancePanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        slices = tuple(_check_slice_ref(g) for g in self.slices)
        audits = tuple(_check_audit_ref(g) for g in self.audits)
        views = tuple(_check_view_ref(v) for v in self.views)
        notes = tuple(_check_note_ref(m) for m in self.notes)
        traces = tuple(_check_trace_ref(a) for a in self.traces)
        panels = tuple(_check_panel_ref(pn) for pn in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for ref in slices:
            if ref.slice_id in seen_ids:
                raise ValueError(
                    f"two slice references stand under id {ref.slice_id!r}")
            if ref.seq in seen_seqs:
                raise ValueError(
                    f"two slice references stand at sequence {ref.seq}")
            seen_ids.add(ref.slice_id)
            seen_seqs.add(ref.seq)
        audit_ids = set()
        audit_seqs = set()
        for audit in audits:
            if audit.audit_id in audit_ids:
                raise ValueError(
                    f"two audits stand under id {audit.audit_id!r}")
            if audit.seq in audit_seqs:
                raise ValueError(
                    f"two audits stand at sequence {audit.seq}")
            audit_ids.add(audit.audit_id)
            audit_seqs.add(audit.seq)
        by_slice = {ref.slice_id: ref for ref in slices}
        for audit in (audits if slices else ()):

            ref = by_slice.get(audit.slice_id)
            if ref is None:
                raise ValueError(
                    f"audit {audit.audit_id!r} is audited from slice "
                    f"{audit.slice_id!r}, which stands nowhere in "
                    f"this book")
            if ref.state != "active":
                raise ValueError(
                    f"audit {audit.audit_id!r} is audited from slice "
                    f"{audit.slice_id!r}, which is not active: "
                    f"no slice is audited from an queued slice")
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
            target = (record.audit_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for audit "
                    f"{record.audit_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per audit target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        trace_ids = set()
        trace_seqs = set()
        trace_audits = set()
        audit_ids = {audit.audit_id for audit in audits}
        for record in traces:
            if record.trace_id in trace_ids:
                raise ValueError(
                    f"two traces stand under id {record.trace_id!r}")
            if record.seq in trace_seqs:
                raise ValueError(
                    f"two traces stand at sequence {record.seq}")
            if record.audit_id in trace_audits:
                raise ValueError(
                    f"two traces stand for audit "
                    f"{record.audit_id!r}: one trace stands "
                    f"per audit walk")
            if audits and record.audit_id not in audit_ids:
                raise ValueError(
                    f"trace {record.trace_id!r} traces audit "
                    f"{record.audit_id!r}, which stands nowhere in "
                    f"this book")
            trace_ids.add(record.trace_id)
            trace_seqs.add(record.seq)
            trace_audits.add(record.audit_id)
        object.__setattr__(
            self, "slices", tuple(sorted(slices, key=lambda g: g.seq)))
        object.__setattr__(
            self, "audits", tuple(sorted(audits, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(
            self, "traces",
            tuple(sorted(traces, key=lambda a: a.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.audits + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.audit_id for g in self.audits) + tuple(
            v.view_id for v in self.views)

    def audit_ids(self) -> Tuple[str, ...]:
        return tuple(g.audit_id for g in self.audits)

    def slice_ids(self) -> Tuple[str, ...]:
        return tuple(g.slice_id for g in self.slices)

    def audit_for(self, audit_id: Any) -> AuditRecord:
        wanted = _clean_text(audit_id, "a audit id")
        for audit in self.audits:
            if audit.audit_id == wanted:
                return audit
        raise KeyError(f"no audit named {wanted!r} stands in this book")

    def slice_for(self, slice_id: Any) -> SliceRef:
        wanted = _clean_text(slice_id, "an slice id")
        for ref in self.slices:
            if ref.slice_id == wanted:
                return ref
        raise KeyError(f"no slice named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> AcceptanceView:
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
        for audit in self.audits:
            if audit.audit_id == wanted:
                return audit
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "slices": [g.to_record() for g in self.slices],
            "audits": [g.to_record() for g in self.audits],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "traces": [a.to_record() for a in self.traces],
            "panels": [pn.to_record() for pn in self.panels],
        }


def _judge_book_panels(book: AcceptanceBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: AcceptanceBook) -> None:
    if book.title != "The Acceptance gate at the M-204 slice boundary":
        raise ValueError("the shipped example book carries another title")
    if len(book.slices) != 3 or len(book.audits) != 5 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold three slice references, five audits and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.traces) != 1:
        raise ValueError("the shipped example book must hold one trace record")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m204-boundary":
        raise ValueError("the pinned panel is panel-m204-boundary")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "held" or verdict.green_shown != 3:
        raise ValueError("the shipped example book verdict must stand held at three green of five")
    index = derive_index(book)
    if [e.check for e in index.entries] != ["evidence", "evidence", "evidence"]:
        raise ValueError("the shipped example book index must derive the three held green audits in held order")
    if index.gaps != ("audit-feeling-gate", "audit-skipping-gate"):
        raise ValueError("the shipped example book must leave the feeling and skipping audits honestly red, named in its gaps")
    found = audit_for_check(book, EXAMPLE_CHECK)
    if found is None or found.audit_id != "audit-juggernaut-gate":
        raise ValueError("the shipped example book must reach its opening audit under the example check")
    if trace_of(book, "audit-juggernaut-gate") != "charter > build > test_suite > evidence":
        raise ValueError("the shipped example book must derive the opening audit's trace from its ran checks")
    if not trace_current(book, "audit-juggernaut-gate"):
        raise ValueError("the shipped example book must hold the opening audit's trace current")
    first = first_note(book)
    if first is None or first.note_id != "note-note-first":
        raise ValueError("the shipped example book must hold the opening note as its first note road")


def validate_book(data: Any, *, require_example: bool = False) -> AcceptanceBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, AcceptanceBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a acceptance book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live slice build or execution "
                f"({key!r} is named on it): {ACCEPTANCE_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its audits under a view")
    if "acceptance_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held audits at call time")
    if "board" in data or "current_audit" in data:
        raise ValueError(
            "a book stores no board and no current audit: both are "
            "derived from its held audits at call time")
    if "trace" in data or "order" in data:
        raise ValueError(
            "a book stores no trace and no order: both are derived "
            "from its held audits at call time; an trace record "
            "holds the trace the human active")
    if data.get("schema") is not None and (
            data["schema"] != ACCEPTANCE_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{ACCEPTANCE_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != ACCEPTANCE_SLICE):
        raise ValueError(
            f"a book's slice must be {ACCEPTANCE_SLICE!r}")
    head = data.get("acceptance_head") or data.get("acceptance_gates") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's acceptance head must be a mapping")
    title = head.get("title") or data.get("title")
    slices = tuple(build_slice_ref(g) for g in data.get("slices") or ())
    audits = tuple(build_audit(g) for g in data.get("audits") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    traces = tuple(build_trace(a) for a in data.get("traces") or ())
    book = AcceptanceBook(
        title=title, slices=slices, audits=audits, views=views,
        notes=notes, traces=traces, panels=())
    panels = tuple(
        build_panel(pn, book) for pn in data.get("panels") or ())
    book = AcceptanceBook(
        title=book.title, slices=book.slices, audits=book.audits,
        views=book.views, notes=book.notes,
        traces=book.traces, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> AcceptanceBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (AcceptanceBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an AcceptanceBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> AcceptanceBook:
    return validate_book(data, require_example=require_example)


def load_acceptance(
        data: Optional[Dict[str, Any]] = None) -> AcceptanceBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(ACCEPTANCE_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_acceptance_file(path: Any) -> AcceptanceBook:
    """Load one acceptance file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: slice references, audits and views held one by one.
# ---------------------------------------------------------------------

class AcceptanceRegistry:
    """An in-memory holding of slice references, audits and views.

    The registry is the pure layer's model of a
    session's acceptance book: slice references are
    held under their ids, audits are held under
    their ids, one audit per id and per sequence,
    and views are held in recorded order, one view
    per sequence and per id. Holding is data only -
    nothing held here builds anything, executes
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._slices: List[SliceRef] = []
        self._audits: List[AuditRecord] = []
        self._views: List[AcceptanceView] = []
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

    def register_slice_ref(self, item: Any) -> SliceRef:
        """Hold one slice reference, judged whole before held."""
        checked = _check_slice_ref(item)
        return self._register(
            self._slices, checked, "slice_id", "slice reference")

    def register_audit(self, item: Any) -> AuditRecord:
        """Hold one audit, judged whole before held."""
        checked = _check_audit_ref(item)
        return self._register(
            self._audits, checked, "audit_id", "audit")

    def register_view(self, view: Any) -> AcceptanceView:
        """Hold one view; a view naming no id takes a fresh one."""
        checked = _check_view_ref(view)
        if not checked.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            checked = build_view({**checked.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, checked, "view_id", "view")

    def register_book(self, book: Any) -> AcceptanceBook:
        """Hold a whole book's records, under its title."""
        checked = build_book(book)
        if self._title is not None and checked.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {checked.title!r}")
        for ref in checked.slices:
            self.register_slice_ref(ref)
        for audit in checked.audits:
            self.register_audit(audit)
        for view in checked.views:
            self.register_view(view)
        self._title = checked.title
        return self.book()

    def book(self) -> AcceptanceBook:
        return AcceptanceBook(
            title=self._title or "An unheld acceptance book",
            slices=tuple(self._slices), audits=tuple(self._audits),
            views=tuple(self._views), notes=(), traces=(), panels=())

    def list_slices(self) -> Tuple[SliceRef, ...]:
        return tuple(self._slices)

    def list_audits(self) -> Tuple[AuditRecord, ...]:
        return tuple(self._audits)

    def list_views(self) -> Tuple[AcceptanceView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._audits) + tuple(self._views)

    def get_slice(self, slice_id: Any) -> SliceRef:
        return self.book().slice_for(slice_id)

    def get_audit(self, audit_id: Any) -> AuditRecord:
        return self.book().audit_for(audit_id)

    def get_view(self, view_id: Any) -> AcceptanceView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records traced for the journal target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> AcceptanceBook:
    if source is None:
        return load_acceptance()
    if isinstance(source, AcceptanceBook):
        return source
    if isinstance(source, AcceptanceRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def audit_record(audit: Any, source: Any = None) -> Dict[str, Any]:
    checked = _check_audit_ref(audit)
    book = _source_book(source) if source is not None else None
    record = {
        "type": "acceptance_audit",
        "slice": ACCEPTANCE_SLICE,
        "audit_id": checked.audit_id,
        "slice_id": checked.slice_id,
        "title": checked.title,
        "segment": segment_of(checked, book),
        "green": audit_green(checked, book),
        "gaps": list(audit_gaps(checked, book)),
    }
    record.update(_provenance_record(checked))
    return record


def slice_record(ref: Any) -> Dict[str, Any]:
    checked = _check_slice_ref(ref)
    record = {
        "type": "acceptance_slice",
        "slice": ACCEPTANCE_SLICE,
        "slice_id": checked.slice_id,
        "title": checked.title,
        "state": checked.state,
    }
    record.update(_provenance_record(checked))
    return record


def trace_record(record_in: Any) -> Dict[str, Any]:
    checked = _check_trace_ref(record_in)
    record = {
        "type": "acceptance_trace",
        "slice": ACCEPTANCE_SLICE,
        "trace_id": checked.trace_id,
        "audit_id": checked.audit_id,
        "trace": checked.trace,
    }
    record.update(_provenance_record(checked))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    checked = _check_view_ref(view)
    record = {
        "type": "acceptance_view",
        "slice": ACCEPTANCE_SLICE,
        "view_id": checked.view_id, "seq": checked.seq,
        "view_filter": checked.view_filter,
    }
    record.update(_provenance_record(checked))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    checked = _check_note_ref(record_in)
    record = {
        "type": "acceptance_note",
        "slice": ACCEPTANCE_SLICE,
        "note_id": checked.note_id,
        "audit_id": checked.audit_id,
        "stance": checked.stance,
    }
    record.update(_provenance_record(checked))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    checked = validate_panel(panel, source)
    record = {"type": "acceptance_panel",
              "slice": ACCEPTANCE_SLICE}
    record.update(checked.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, AcceptanceVerdict):
        checked = validate_verdict(verdict, source)
    else:
        checked = derive_verdict(_source_book(verdict), view)
    record = {"type": "acceptance_verdict",
              "slice": ACCEPTANCE_SLICE}
    record.update(checked.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, AcceptanceIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "acceptance_index",
              "slice": ACCEPTANCE_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    checked = _source_book(book)
    record = {"type": "acceptance_book",
              "slice": ACCEPTANCE_SLICE,
              "title": checked.title}
    record.update(checked.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(audit: Any, source: Any = None) -> str:
    checked = _check_audit_ref(audit)
    return (
        f"{checked.title} - from {checked.slice_id}: "
        f"check {checked.check if checked.check else 'none'}, "
        f"claims "
        f"{', '.join(checked.claims) if checked.claims else 'none'}. "
        f"{checked.detail}")


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The audits stand {verdict.verdict}: "
        f"{verdict.green_shown} of {verdict.total_shown} shown "
        f"audits stand green.")


def view_plain_words(view: Any) -> str:
    checked = _check_view_ref(view)
    return f"View {checked.view_id}: shows {checked.view_filter} audits."


def note_plain_words(record_in: Any) -> str:
    checked = _check_note_ref(record_in)
    return (
        f"Note {checked.note_id}: {checked.stance} "
        f"{checked.audit_id}, toward {checked.target}. "
        f"{checked.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, AcceptanceIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.entries)} green audits; "
        f"red, named in its gaps: {gaps}.")

def format_audit(audit: Any, source: Any = None) -> str:
    checked = _check_audit_ref(audit)
    book = _source_book(source) if source is not None else None
    lines = [f"{checked.title} ({checked.audit_id})"]
    lines.extend(plain_lines(checked))
    lines.append(checked.detail)
    if audit_green(checked, book):
        lines.append(
            "This audit stands green - it walked the state "
            "machine in the open from charter to evidence, "
            "and it asked the human nothing the code can "
            "answer.")
    else:
        lines.append(
            "This audit stands red - it stands named in "
            f"its gaps: {', '.join(audit_gaps(checked, book))}, and "
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
        f"Acceptance note {checked.stance} {checked.audit_id} "
        f"({checked.note_id}): {checked.title}. {checked.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or reading it builds nothing, executes nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_check(source: Any, check: Any) -> str:
    audit = audit_for_check(source, check)
    if audit is not None:
        return format_audit(audit, source)
    wanted = check.strip() if isinstance(check, str) else check
    return (
        f"No held audit stands under check {wanted!r} yet - the "
        f"check reaches nothing in this book, and no audit is "
        f"invented for it.")


def format_book(source: Any = None, slice_id: Any = None) -> str:
    book = _source_book(source)
    audits = (audits_for_slice(book, slice_id)
              if slice_id is not None else book.audits)
    lines = [f"The Acceptance Gate (M-205) - {book.title}"]
    lines.extend(segment_of(audit, book) for audit in audits)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Acceptance panel under view {panel.view_id}:"]
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
    lines = ["Acceptance index, derived from the held audits:"]
    for entry in index.entries:
        lines.append(f"{entry.check} - {entry.title} ({entry.audit_id})")
    if index.gaps:
        lines.append(
            "Red, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "builds nothing, executes nothing and opens no network.")
    return "\n".join(lines)


def format_acceptance_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "The Acceptance Gate (M-205)",
        f"{book.title}: {len(book.audits)} audits held, "
        f"{len(green_audits(book))} audits standing green, "
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


def parse_acceptance_args(args: Any) -> Tuple[str, Any]:
    """Parse the /acceptance grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("audit", "view", "note"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("check", "slice"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("index", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
