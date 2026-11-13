"""Handoff summaries (All-Features roadmap slice M-163).

Part VII continues. The roadmap's words:
``ending a session writes "where things stand"
for the next session or the next human - the
stand-up (M-134) in durable form.``

What already ships, and what this slice adds:

* Where things stand already ships as data on
  shipped roads: the stand-ups
  (``core/stand_ups.py``, M-134) hold the
  coordinator's progress digest in plain words -
  done, doing, blocked, needs-you - derived from
  its entries, never stored; session memory
  (``core/session_memory.py``, M-153) holds a
  session's situation across days; multi-session
  per project (``core/multi_session_projects.py``,
  M-162) holds parallel sessions on one project,
  each under its own journal; and long-session
  endurance (``core/long_session_endurance.py``,
  M-161) holds a long session's measured budgets.
  What none of those layers holds is the handoff
  itself: the durable writing, made when a session
  ends, that the next session or the next human
  reads as the starting panel.
* This slice is that writing, as a pure layer: a
  handoff summary is one ended session's standing,
  validated as data WITH ITS PROVENANCE WHOLE -
  the session it ends, the project and branch it
  stood on, the claims it carries from the
  stand-up (done / doing / blocked / needs-you),
  the session and journal evidence those claims
  stand on, who wrote it, the day, and where it
  was read from - composed BY IMPORT from the
  shipped holdings it stands beside (a stand-up
  report or digest, a session-memory situation, a
  parallel session, a long-session endurance
  record), each judged by its own layer's
  validation. The shipped data file
  (``mythic_agent/data/handoff_summaries.yaml``)
  holds one example book in exactly the shape a
  real book file takes, a loader reads a book file
  anywhere on disk, the handoff panel is DERIVED
  from the whole book (every handoff carried
  whole, in a settled order), a handoff VERDICT is
  derived for the whole book, handoffs are shaped
  as session news, and a small in-memory registry
  model holds handoffs one by one. The agent layer
  owns holding a book for a session and reading
  the session's stand-up onto a handoff.

Honesty rules, enforced here and pinned by tests:

* **Claims carried, never invented.** A handoff's
  claims are the stand-up digest sections of its
  session, carried by reference (entry ids) alone:
  a claim stands in one section only, and a claim
  is handed off once in a book.
* **Evidence whole.** A handoff is derived from
  session and journal evidence, and names that
  evidence: a handoff whose claims disagree with
  the stand-up its evidence derives is refused,
  and a handoff naming no evidence stands on
  nothing and refuses.
* **One handoff per session.** A session ends
  once: a second handoff naming a held session
  refuses, in a book and in the registry alike.
* **Composed, never duplicated.** A handoff that
  stands beside a shipped holding is that holding
  read onto this layer by import and judged by its
  own layer's validation, by reference and count
  alone: its own words never cross.
* **Data only.** This layer holds handoffs as
  data: it reads no file itself beyond its own
  book files, sends nothing, posts nothing,
  schedules nothing, calls no model and persists
  nothing. A handoff standing in a book is a
  recorded writing, never a claim that anything
  was sent to the next session or human.
"""

from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .crew_members import normalize_member_id
from .long_session_endurance import EnduranceRecord
from .long_session_endurance import validate_record as _validate_endurance
from .multi_session_projects import ParallelSession
from .multi_session_projects import validate_session as _validate_parallel
from .session_memory import SessionSituation
from .session_memory import validate_situation as _validate_situation
from .stand_ups import STATUS_KINDS
from .stand_ups import StandUpDigest, StandUpRegistry, StandUpReport
from .stand_ups import digest_stand_up
from .stand_ups import normalize_status as _normalize_status
from .stand_ups import validate_digest as _validate_digest
from .stand_ups import validate_report as _validate_report
from .validation import ValidationError

__all__ = [
    "CLAIM_KINDS",
    "HANDOFF_SUMMARIES_RESOURCE",
    "HANDOFF_SUMMARIES_SCHEMA",
    "HANDOFF_SUMMARIES_SLICE",
    "PLAIN_EXPLANATION",
    "USAGE",
    "EvidenceVerdict",
    "HandoffBook",
    "HandoffPanel",
    "HandoffPanelRow",
    "HandoffRegistry",
    "HandoffSummary",
    "SectionCount",
    "book_record",
    "build_book",
    "build_handoff",
    "build_panel",
    "build_row",
    "build_verdict",
    "derive_panel",
    "derive_verdict",
    "format_handoff",
    "format_handoff_summaries_screen",
    "format_handoffs",
    "format_panel",
    "format_verdict",
    "handoff_from_endurance_record",
    "handoff_from_parallel_session",
    "handoff_from_session_situation",
    "handoff_from_stand_up",
    "handoff_record",
    "handoff_refs",
    "handoffs_from_multi_session_book",
    "inspect_handoff_source",
    "load_handoff_summaries",
    "load_handoff_summaries_file",
    "normalize_claim_kind",
    "panel_plain_words",
    "panel_record",
    "parse_handoffsummary_args",
    "plain_words",
    "total_claims",
    "total_evidence",
    "validate_book",
    "validate_handoff",
    "validate_panel",
    "validate_row",
    "validate_verdict",
    "verdict_plain_words",
    "verdict_record",
]

HANDOFF_SUMMARIES_SLICE = "M-163"

HANDOFF_SUMMARIES_RESOURCE = "handoff_summaries.yaml"

HANDOFF_SUMMARIES_SCHEMA = "mythic.handoff_summaries/1"

#: The four sections a handoff carries, in the
#: stand-up's own order (M-134): finished, under
#: way, held, and waiting on the human's word.
CLAIM_KINDS = STATUS_KINDS

_RECORD_KEYS = frozenset({
    "handoff_id", "id", "title", "name", "subject",
    "session_ref", "session", "project", "branch",
    "done", "doing", "blocked",
    "needs_you", "needs-you", "needs",
    "evidence_refs", "evidence", "refs",
    "written_by", "author", "by", "who",
    "written_on", "day", "date", "source",
})

_ROW_KEYS = frozenset({
    "handoff_id", "id", "title", "session_ref",
    "project", "branch", "done_count", "doing_count",
    "blocked_count", "needs_you_count",
    "claim_count", "claims", "evidence_count", "evidence",
    "written_by", "written_on",
})

_SECTION_COUNT_KEYS = frozenset({"kind", "claims", "count"})

_PANEL_KEYS = frozenset({
    "panel_id", "id", "rows", "handoffs",
    "total_handoffs", "total",
    "total_claims", "claims",
    "total_evidence", "evidence",
    "section_counts", "sections", "account", "statements",
})

_VERDICT_KEYS = frozenset({
    "total_handoffs", "total", "total_claims", "claims",
    "total_evidence", "evidence", "total_blocked", "blocked",
    "total_needs_you", "needs_you", "needs-you",
    "distinct_sessions", "sessions", "verdict",
})

_BOOK_KEYS = frozenset({"title", "name"})

_HANDOFF_BOOK_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "canon_note", "guide", "handoffs", "records", "panels",
})

_EXAMPLE_TITLE = "Handoff summaries at the M-162 slice boundary"

_EXAMPLE_HANDOFF_IDS = (
    "handoff-main-close", "handoff-graph-pause",
    "handoff-thrift-close")

_EXAMPLE_FIRST_HANDOFF_ID = "handoff-main-close"

_EXAMPLE_FIRST_HANDOFF_TITLE = (
    "the endurance day, handed off on the main line")

_EXAMPLE_PANEL_ID = "panel-m162-boundary"

_EXAMPLE_PANEL_ROW_IDS = (
    "handoff-main-close", "handoff-graph-pause",
    "handoff-thrift-close")

_EXAMPLE_PANEL_ACCOUNT = (
    "The handoff panel holds 3 handoffs: "
    "7 claims in all, 6 evidence references: "
    "blocked 1, doing 1, done 4, needs_you 1.",
    "Handoffs stand by project, then day, then "
    "branch, then title, then handoff id, so two "
    "panels of one book diff cleanly, line by line.",
    "Every claim a handoff carries is carried from "
    "the stand-up of its session, and a handoff "
    "whose claims disagree with that evidence is "
    "refused - a handoff states only what its "
    "evidence states.",
    "The panel is read off the book at call time - "
    "it is derived, never stored loose.",
)

PLAIN_EXPLANATION = (
    "Handoff summaries: ending a session writes "
    "where things stand for the next session or "
    "the next human - the stand-up in durable "
    "form. A handoff summary is one ended "
    "session's standing, carried with its "
    "provenance whole: the session it ends, the "
    "project and branch it stood on, the claims "
    "it carries from the stand-up (done, doing, "
    "blocked and needs-you), the session and "
    "journal evidence those claims stand on, who "
    "wrote it, the day, and where it was read "
    "from. A handoff whose claims disagree with "
    "its evidence is refused. The handoff panel "
    "is derived from the book at call time: every "
    "handoff standing whole, by project, then "
    "day, then branch, then title, then handoff "
    "id, and the handoff verdict is derived for "
    "the whole book. This layer holds handoffs "
    "as data only: it sends nothing, posts "
    "nothing, schedules nothing, calls no model "
    "and persists nothing."
)

USAGE = (
    "Usage: /handoffsummary, /handoffsummary show, "
    "/handoffsummary handoff <handoff-id>, "
    "/handoffsummary session <session-ref>, "
    "/handoffsummary panel, /handoffsummary verdict"
)


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_title(value: Any, what: str = "a title") -> str:
    text = _clean_text(value, what)
    if len(text) > 120 or "\x00" in text:
        raise ValueError(
            f"{what} must be plain text of at most "
            f"120 characters, got {len(text)} characters")
    return text


def _check_long_text(value: Any, what: str) -> str:
    text = _clean_text(value, what)
    if len(text) > 2000 or "\x00" in text:
        raise ValueError(
            f"{what} must be plain text of at most "
            f"2000 characters, got {len(text)} characters")
    return text


def _check_account(value: Any) -> Tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"an account must be a list of statements, "
            f"got {value!r}")
    account = tuple(
        _check_long_text(a, "an account statement")
        for a in value)
    if not account:
        raise ValueError("an account carries at least one statement")
    if len(account) > 16:
        raise ValueError(
            f"an account carries at most 16 statements, "
            f"got {len(account)}")
    if len(set(account)) != len(account):
        raise ValueError("an account states one statement twice")
    return account


def _pick_any(mapping: Dict[str, Any], spellings: Tuple[str, ...],
              what: str) -> Any:
    values = [mapping[s] for s in spellings if s in mapping]
    if not values:
        return None
    if any(value != values[0] for value in values[1:]):
        raise ValueError(f"a record names two different {what}")
    return values[0]


def _check_count(value: Any, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{what} must be a count, got {value!r}")
    if value < 0:
        raise ValueError(f"{what} must not be negative, got {value!r}")
    return value


def _check_word(value: Any, what: str) -> str:
    try:
        return normalize_member_id(value)
    except ValueError:
        raise ValueError(
            f"{what} must be one plain word, "
            f"got {value!r}") from None


_BRANCH_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789-_./")


def _check_branch(value: Any) -> str:
    text = _clean_text(value, "a handoff's branch")
    if len(text) > 120 or any(ch not in _BRANCH_CHARS for ch in text):
        raise ValueError(
            f"a handoff's branch must be a plain branch "
            f"name, got {text!r}")
    if text.startswith(("/", ".", "-")) or text.endswith(("/", ".")) \
            or "//" in text or ".." in text:
        raise ValueError(
            f"a handoff's branch must be a plain branch "
            f"name, got {text!r}")
    return text


def _check_day(value: Any) -> str:
    text = _clean_text(value, "a record's written-on day")
    try:
        parsed = date.fromisoformat(text)
    except ValueError:
        raise ValueError(
            f"a record's written-on day must be an ISO "
            f"date (YYYY-MM-DD), got {text!r}") from None
    if parsed.isoformat() != text:
        raise ValueError(
            f"a record's written-on day must be an ISO "
            f"date (YYYY-MM-DD), got {text!r}")
    return text


def normalize_claim_kind(value: Any) -> str:
    """The canonical claim kind a word names.

    A claim kind is one of :data:`CLAIM_KINDS` -
    the stand-up's own four states (M-134): a claim
    is ``done``, ``doing``, ``blocked`` or
    ``needs_you`` - read by the stand-up layer's own
    normalizer, with its plain faces (``finished``,
    ``in_progress``, ``stuck``, ``needs_human`` and
    kin) read onto them. Anything else raises,
    plainly naming the four.
    """
    return _normalize_status(value)


# ---------------------------------------------------------------------
# The handoff summary: one ended session's standing, whole.
# ---------------------------------------------------------------------


def _check_claims(value: Any, kind: str) -> Tuple[str, ...]:
    if isinstance(value, (str, bytes)) \
            or not isinstance(value, (list, tuple)):
        raise ValueError(
            f"a handoff's {kind} claims must be a list "
            f"of entry ids, got {value!r}")
    claims = tuple(
        _check_word(item, "a claim's entry id") for item in value)
    if len(claims) > 512:
        raise ValueError(
            f"a handoff names at most 512 {kind} claims, "
            f"got {len(claims)}")
    if len(set(claims)) != len(claims):
        raise ValueError(
            f"a handoff names one {kind} claim twice")
    return claims


def _check_evidence(value: Any) -> Tuple[str, ...]:
    if isinstance(value, (str, bytes)) \
            or not isinstance(value, (list, tuple)):
        raise ValueError(
            f"a handoff's evidence must be a list of "
            f"references, got {value!r}")
    refs = tuple(
        _check_word(item, "an evidence reference") for item in value)
    if not refs:
        raise ValueError(
            "a handoff names at least one evidence "
            "reference of its own - a handoff standing "
            "on no evidence states nothing that can "
            "be checked")
    if len(refs) > 512:
        raise ValueError(
            f"a handoff names at most 512 evidence "
            f"references, got {len(refs)}")
    if len(set(refs)) != len(refs):
        raise ValueError(
            "a handoff names one evidence reference twice")
    return refs


@dataclass(frozen=True)
class HandoffSummary:
    """One ended session's standing, written durable, as data.

    ``title`` names the handoff in plain words;
    ``session_ref`` names the session that ended;
    ``project`` is the project it stood on and
    ``branch`` the branch it worked; ``done``,
    ``doing``, ``blocked`` and ``needs_you`` are the
    claims it carries from the stand-up - the entry
    ids standing in each section, each id in one
    section only; ``evidence_refs`` are the session
    and journal references those claims stand on.
    The provenance stands whole beside the handoff:
    ``written_by`` names who wrote it,
    ``written_on`` is the day, and ``source`` names
    where it was read from.
    """

    title: str
    session_ref: str
    project: str
    branch: str
    done: Tuple[str, ...]
    doing: Tuple[str, ...]
    blocked: Tuple[str, ...]
    needs_you: Tuple[str, ...]
    evidence_refs: Tuple[str, ...]
    written_by: str
    written_on: str
    source: str
    handoff_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.handoff_id is not None:
            object.__setattr__(
                self, "handoff_id", normalize_member_id(self.handoff_id))
        object.__setattr__(
            self, "title", _check_title(self.title, "a handoff's title"))
        object.__setattr__(
            self, "session_ref",
            _check_word(self.session_ref, "a handoff's session reference"))
        object.__setattr__(
            self, "project",
            _check_title(self.project, "a handoff's project"))
        object.__setattr__(self, "branch", _check_branch(self.branch))
        seen = []
        for kind in CLAIM_KINDS:
            claims = _check_claims(getattr(self, kind), kind)
            object.__setattr__(self, kind, claims)
            seen.extend(claims)
        if len(set(seen)) != len(seen):
            raise ValueError(
                "a handoff names one claim in two sections")
        if not seen:
            raise ValueError(
                "a handoff names at least one claim - a "
                "handoff that states nothing hands off "
                "nothing")
        object.__setattr__(
            self, "evidence_refs", _check_evidence(self.evidence_refs))
        object.__setattr__(
            self, "written_by",
            _check_title(self.written_by, "a handoff's writer"))
        object.__setattr__(
            self, "written_on", _check_day(self.written_on))
        object.__setattr__(
            self, "source",
            _check_title(self.source, "a handoff's source"))

    def section(self, kind: Any) -> Tuple[str, ...]:
        """One section's claim ids, by its kind word."""
        return getattr(self, normalize_claim_kind(kind))

    def counts(self) -> Dict[str, int]:
        """Each section's size, read off the sections held."""
        return {kind: len(self.section(kind)) for kind in CLAIM_KINDS}

    @property
    def claim_count(self) -> int:
        """How many claims this handoff carries, in all."""
        return sum(self.counts().values())

    @property
    def evidence_count(self) -> int:
        """How many evidence references this handoff names."""
        return len(self.evidence_refs)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "handoff_summaries_handoff",
            "slice": HANDOFF_SUMMARIES_SLICE,
            "handoff_id": self.handoff_id,
            "title": self.title,
            "session_ref": self.session_ref,
            "project": self.project,
            "branch": self.branch,
            "done": list(self.done),
            "doing": list(self.doing),
            "blocked": list(self.blocked),
            "needs_you": list(self.needs_you),
            "evidence_refs": list(self.evidence_refs),
            "claim_count": self.claim_count,
            "evidence_count": self.evidence_count,
            "written_by": self.written_by,
            "written_on": self.written_on,
            "source": self.source,
        }


def _check_handoff_ref(value: Any) -> HandoffSummary:
    if isinstance(value, HandoffSummary):
        return value
    if isinstance(value, dict):
        return validate_handoff(value)
    raise ValueError(f"a handoff summary is needed, got {value!r}")


def _digest_for(source: Any) -> StandUpDigest:
    """The stand-up digest one evidence source yields, by import."""
    if isinstance(source, StandUpDigest):
        return _validate_digest(source)
    if isinstance(source, (StandUpReport, StandUpRegistry)):
        return digest_stand_up(source)
    raise ValueError(f"stand-up evidence is needed, got {source!r}")


def validate_handoff(handoff: Any, evidence: Any = None) -> HandoffSummary:
    """Validate one handoff into a HandoffSummary.

    Accepts a handoff or a mapping naming a ``title``
    (or ``name`` / ``subject``), a ``session_ref``
    (or ``session``), a ``project``, a ``branch``,
    the four claim sections (``needs-you`` /
    ``needs`` also read for the needs_you section),
    ``evidence_refs`` (or ``evidence`` / ``refs``), a
    ``written_by`` (or ``author`` / ``by`` / ``who``),
    a ``written_on`` (or ``day`` / ``date``), a
    ``source`` and an optional ``handoff_id`` (or
    ``id``). Naming two spellings of one field with
    different values refuses, and unknown keys
    refuse. With *evidence* given (a stand-up report,
    registry or digest, judged by the stand-up
    layer), the handoff is also judged against the
    digest that evidence derives: any disagreement
    refuses, because a handoff's claims are carried
    from its evidence, never invented apart from it.
    """
    if isinstance(handoff, HandoffSummary):
        current = handoff
    elif isinstance(handoff, dict):
        unknown = set(handoff) - _RECORD_KEYS
        if unknown:
            raise ValueError(
                "unknown handoff keys: %s"
                % ", ".join(sorted(unknown)))

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            value = _pick_any(handoff, spellings, what)
            if value is None:
                raise ValueError(f"a handoff is missing its {what}")
            return value

        needs = _pick_any(
            handoff, ("needs_you", "needs-you", "needs"),
            "needs-you sections")
        if needs is None:
            raise ValueError("a handoff is missing its needs-you claims")
        kwargs: Dict[str, Any] = {
            "title": _needed(("title", "name", "subject"), "title"),
            "session_ref": _needed(
                ("session_ref", "session"), "session reference"),
            "project": _needed(("project",), "project"),
            "branch": _needed(("branch",), "branch"),
            "done": _needed(("done",), "done claims"),
            "doing": _needed(("doing",), "doing claims"),
            "blocked": _needed(("blocked",), "blocked claims"),
            "needs_you": needs,
            "evidence_refs": _needed(
                ("evidence_refs", "evidence", "refs"), "evidence"),
            "written_by": _needed(
                ("written_by", "author", "by", "who"), "writer"),
            "written_on": _needed(
                ("written_on", "day", "date"), "written-on day"),
            "source": _needed(("source",), "source"),
        }
        named_id = _pick_any(handoff, ("handoff_id", "id"), "handoff ids")
        if named_id is not None:
            kwargs["handoff_id"] = named_id
        current = HandoffSummary(**kwargs)
    else:
        raise ValueError(
            f"a handoff must be a mapping, got {handoff!r}")
    if evidence is not None:
        digest = _digest_for(evidence)
        derived = (digest.done, digest.doing,
                   digest.blocked, digest.needs_you)
        carried = (current.done, current.doing,
                   current.blocked, current.needs_you)
        if carried != derived:
            raise ValueError(
                "a handoff whose claims disagree with "
                "its evidence is refused - the claims a "
                "handoff carries must be the stand-up "
                "digest its evidence derives")
    return current


def build_handoff(handoff: Any = None, **kwargs: Any) -> HandoffSummary:
    """Build one validated handoff, from a mapping or field words."""
    if isinstance(handoff, HandoffSummary) and not kwargs:
        return handoff
    if isinstance(handoff, dict) or handoff is None:
        merged: Dict[str, Any] = {}
        if isinstance(handoff, dict):
            merged.update(handoff)
        merged.update(kwargs)
        return validate_handoff(merged)
    raise ValueError(f"a handoff must be a mapping, got {handoff!r}")


def _handoff_for(*, title: Any, session_ref: Any, project: Any,
                 branch: Any, done: Any, doing: Any, blocked: Any,
                 needs_you: Any, evidence_refs: Any,
                 written_by: Any, written_on: Any,
                 source: Any) -> HandoffSummary:
    """One handoff for one shipped piece, by ref and count.

    The piece's own words are never read here: only
    the references and counts named beside it cross.
    A handoff naming no branch, no session, no
    evidence or no writer refuses - a handoff stands
    on a session, with its evidence, or it does not
    stand at all.
    """
    if branch is None or (isinstance(branch, str) and not branch.strip()):
        raise ValueError(
            "a handoff must name the branch its session "
            "stood on - a handoff is read against the "
            "branch it hands off")
    if session_ref is None or (
            isinstance(session_ref, str) and not session_ref.strip()):
        raise ValueError(
            "a handoff must name the session it ends - "
            "a handoff of no session hands off nothing")
    if evidence_refs is None:
        raise ValueError(
            "a handoff must name its evidence - a "
            "handoff standing on no evidence states "
            "nothing that can be checked")
    if written_by is None:
        raise ValueError(
            "a handoff must name who wrote it - a "
            "handoff written by no one is no record")
    return HandoffSummary(
        title=title, session_ref=session_ref, project=project,
        branch=branch, done=done, doing=doing, blocked=blocked,
        needs_you=needs_you, evidence_refs=evidence_refs,
        written_by=written_by, written_on=written_on, source=source)


def _situation_evidence(situation: SessionSituation) -> Tuple[str, ...]:
    """The evidence ids one situation itself names, in held order.

    The carried memory notes', open slices' and
    standing decisions' own ids - references only;
    the pieces' words never cross.
    """
    refs = []
    for note in situation.memory:
        if note.note_id is not None:
            refs.append(note.note_id)
    for slice_ in situation.open_slices:
        refs.append(slice_.slice_id)
    for decision in situation.decisions:
        if decision.decision_id is not None:
            refs.append(decision.decision_id)
    return tuple(refs)


def inspect_handoff_source(piece: Any) -> Dict[str, Any]:
    """Inspect one shipped piece: its references and counts only.

    The piece is judged by the layer that owns its
    type, never by whichever validator happens to
    accept its shape first. A stand-up report or
    digest reports its claim count and boundary; a
    session-memory situation reports its session
    reference and the count of evidence ids it
    itself names; a parallel session reports its
    session reference and its own journal's entry
    count as its evidence count; a long-session
    endurance record reports the reference it stands
    under and one evidence reference (itself); a
    handoff reports itself whole. A piece no shipped
    layer owns refuses.
    """
    if isinstance(piece, HandoffSummary):
        return {"session_ref": piece.session_ref,
                "claim_count": piece.claim_count,
                "evidence_count": piece.evidence_count}
    if isinstance(piece, (StandUpReport, StandUpRegistry,
                          StandUpDigest)):
        digest = _digest_for(piece)
        return {"claim_count": digest.total(),
                "boundary": digest.boundary}
    if isinstance(piece, SessionSituation):
        validated = _validate_situation(piece)
        return {"session_ref": validated.session_ref,
                "claim_count": None,
                "evidence_count": len(_situation_evidence(validated))}
    if isinstance(piece, ParallelSession):
        validated = _validate_parallel(piece)
        return {"session_ref": validated.session_ref,
                "claim_count": None,
                "evidence_count": validated.journal_count}
    if isinstance(piece, EnduranceRecord):
        validated = _validate_endurance(piece)
        return {"session_ref": validated.ref,
                "claim_count": None, "evidence_count": 1}
    if isinstance(piece, dict):
        if "evidence_refs" in piece or "evidence" in piece:
            checked = validate_handoff(piece)
            return {"session_ref": checked.session_ref,
                    "claim_count": checked.claim_count,
                    "evidence_count": checked.evidence_count}
        for validator in (_validate_situation, _validate_parallel,
                          _validate_endurance, _validate_report,
                          _validate_digest):
            try:
                validated = validator(piece)
            except Exception:
                continue
            return inspect_handoff_source(validated)
    raise ValueError(
        f"no shipped layer owns this piece, got {piece!r}")


def handoff_from_stand_up(
        source: Any, *, session_ref: Any, project: Any,
        branch: Any, evidence_refs: Any, written_by: Any,
        written_on: Any, source_word: Any = "stand-ups",
        title: Any = None) -> HandoffSummary:
    """Build one handoff from a session's stand-up, by import.

    The stand-up - a report, a registry or a digest
    (M-134), judged by that layer's own validation
    and derived by its own digest road - is read
    onto a handoff BY IMPORT by its entry ids alone:
    the digest's four sections stand as the
    handoff's claims, in the digest's order. The
    session, project, branch and evidence are named
    beside it. No entry's title, detail or member
    is ever read here - only the ids the digest
    itself carries cross.
    """
    digest = _digest_for(source)
    return _handoff_for(
        title=title if title is not None else (
            f"handoff at the {digest.boundary} boundary"),
        session_ref=session_ref, project=project, branch=branch,
        done=digest.done, doing=digest.doing,
        blocked=digest.blocked, needs_you=digest.needs_you,
        evidence_refs=evidence_refs, written_by=written_by,
        written_on=written_on, source=source_word)


def handoff_from_session_situation(
        situation: Any, *, project: Any, branch: Any,
        done: Any = (), doing: Any = (), blocked: Any = (),
        needs_you: Any = (), evidence_refs: Any = None,
        written_by: Any, written_on: Any,
        source: Any = "session memory",
        title: Any = None) -> HandoffSummary:
    """Build one handoff at the end of a remembered session.

    The situation - session memory's own record
    (M-153), judged by that layer's own validation -
    is read onto a handoff BY IMPORT by its
    reference alone: its session reference stands as
    the handoff's session, and the evidence is the
    ids the situation itself names - its carried
    memory notes, open slices and standing decisions
    - unless evidence is named beside it. The claims
    are named beside it, carried from the session's
    stand-up. The situation's title, workspace and
    carried words are never read here.
    """
    validated = _validate_situation(situation)
    evidence = evidence_refs if evidence_refs is not None else (
        _situation_evidence(validated) or None)
    return _handoff_for(
        title=title if title is not None else (
            f"session {validated.session_ref}"),
        session_ref=validated.session_ref, project=project,
        branch=branch, done=done, doing=doing, blocked=blocked,
        needs_you=needs_you, evidence_refs=evidence,
        written_by=written_by, written_on=written_on, source=source)


def handoff_from_parallel_session(
        session: Any, *, done: Any = (), doing: Any = (),
        blocked: Any = (), needs_you: Any = (),
        evidence_refs: Any = None, written_by: Any = None,
        written_on: Any = None,
        source: Any = "multi-session projects",
        title: Any = None) -> HandoffSummary:
    """Build one handoff at the end of a parallel session.

    The session - multi-session per project's own
    record (M-162), judged by that layer's own
    validation - is read onto a handoff BY IMPORT by
    its references alone: the project, branch and
    session reference it stands under stand as the
    handoff's own, and its evidence is its own
    journal's entries, unless evidence is named
    beside it. The claims are named beside it,
    carried from the session's stand-up; the writer
    and day default to the session's own provenance.
    The session's title is never read here.
    """
    validated = _validate_parallel(session)
    evidence = evidence_refs if evidence_refs is not None else (
        validated.journal_entries)
    return _handoff_for(
        title=title if title is not None else (
            f"session {validated.session_ref}"),
        session_ref=validated.session_ref,
        project=validated.project, branch=validated.branch,
        done=done, doing=doing, blocked=blocked,
        needs_you=needs_you, evidence_refs=evidence,
        written_by=written_by if written_by is not None
        else validated.recorded_by,
        written_on=written_on if written_on is not None
        else validated.recorded_on, source=source)


def handoff_from_endurance_record(
        record: Any, *, project: Any, branch: Any,
        done: Any = (), doing: Any = (), blocked: Any = (),
        needs_you: Any = (), evidence_refs: Any,
        session_ref: Any = None, written_by: Any = None,
        written_on: Any = None,
        source: Any = "long-session endurance",
        title: Any = None) -> HandoffSummary:
    """Build one handoff at the end of a measured long session.

    The record - long-session endurance's own record
    (M-161), judged by that layer's own validation -
    is read onto a handoff BY IMPORT by its
    reference alone: the reference it stands under
    stands as the handoff's session, unless a
    session is named beside it. The project, branch,
    claims and evidence are named beside it; the
    writer and day default to the record's own
    provenance. Its subject and figures are never
    read here.
    """
    validated = _validate_endurance(record)
    return _handoff_for(
        title=title if title is not None else (
            f"session {validated.ref}"),
        session_ref=session_ref if session_ref is not None
        else validated.ref,
        project=project, branch=branch, done=done, doing=doing,
        blocked=blocked, needs_you=needs_you,
        evidence_refs=evidence_refs,
        written_by=written_by if written_by is not None
        else validated.recorded_by,
        written_on=written_on if written_on is not None
        else validated.recorded_on, source=source)


def _parallel_sessions(source: Any) -> Tuple[ParallelSession, ...]:
    """The parallel sessions one source holds, judged by M-162."""
    from .multi_session_projects import (
        MultiSessionBook, MultiSessionRegistry)
    if isinstance(source, MultiSessionBook):
        return source.sessions
    if isinstance(source, MultiSessionRegistry):
        return source.list_sessions()
    if isinstance(source, (list, tuple)):
        return tuple(_validate_parallel(item) for item in source)
    if isinstance(source, (ParallelSession, dict)):
        return (_validate_parallel(source),)
    raise ValueError(f"parallel sessions are needed, got {source!r}")


def handoffs_from_multi_session_book(
        source: Any, *, claims_by_session: Any,
        written_by: Any, written_on: Any
        ) -> Tuple[HandoffSummary, ...]:
    """Handoffs read off the shipped multi-session book.

    The parallel sessions of a multi-session book -
    or of a whole multi-session registry - are read
    onto handoffs BY IMPORT, judged by multi-session
    per project's own validation on the way, one
    handoff per session. Each handoff's evidence is
    its session's own journal entries, and its
    claims are the claims named beside this road in
    *claims_by_session*, keyed by session reference:
    a session whose claims are not named refuses the
    whole road before another handoff is built,
    because a handoff's claims are carried from its
    session's stand-up, never invented here. Every
    session's title and words stay in its own layer:
    only references and counts cross.
    """
    if claims_by_session is None:
        raise ValueError(
            "claims must be named for the handoffs - a "
            "handoff's claims are carried from its "
            "session's stand-up, never invented")
    sessions = _parallel_sessions(source)
    handoffs = []
    for session in sessions:
        claims = claims_by_session.get(session.session_ref)
        if claims is None:
            raise ValueError(
                f"no claims are named for session "
                f"{session.session_ref!r} - a handoff's "
                f"claims are carried from its stand-up, "
                f"never invented")
        if not isinstance(claims, dict):
            raise ValueError(
                f"the claims named for session "
                f"{session.session_ref!r} must be a mapping "
                f"of claim sections")
        unknown = set(claims) - set(CLAIM_KINDS)
        if unknown:
            raise ValueError(
                "unknown claim sections for session %r: %s"
                % (session.session_ref, ", ".join(sorted(unknown))))
        handoffs.append(handoff_from_parallel_session(
            session,
            done=tuple(claims.get("done") or ()),
            doing=tuple(claims.get("doing") or ()),
            blocked=tuple(claims.get("blocked") or ()),
            needs_you=tuple(claims.get("needs_you") or ()),
            written_by=written_by, written_on=written_on))
    return tuple(handoffs)


# ---------------------------------------------------------------------
# The handoff panel: every handoff carried whole, derived.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class HandoffPanelRow:
    """One handoff carried whole into the panel.

    Every field is the handoff's own head: its id,
    title, session, project and branch, its four
    sections' counts, its claims in all, its
    evidence count, and its provenance head.
    :func:`validate_row` judged against its handoff
    refuses a row whose fields disagree with the row
    they derive.
    """

    handoff_id: str
    title: str
    session_ref: str
    project: str
    branch: str
    done_count: int
    doing_count: int
    blocked_count: int
    needs_you_count: int
    claim_count: int
    evidence_count: int
    written_by: str
    written_on: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "handoff_id", normalize_member_id(self.handoff_id))
        object.__setattr__(
            self, "title", _check_title(self.title, "a row's title"))
        object.__setattr__(
            self, "session_ref",
            _check_word(self.session_ref, "a row's session reference"))
        object.__setattr__(
            self, "project", _check_title(self.project, "a row's project"))
        object.__setattr__(self, "branch", _check_branch(self.branch))
        tallies = {}
        for kind in CLAIM_KINDS:
            field = f"{kind}_count"
            tallies[kind] = _check_count(
                getattr(self, field), f"a row's {kind} count")
            object.__setattr__(self, field, tallies[kind])
        object.__setattr__(
            self, "claim_count",
            _check_count(self.claim_count, "a row's claim count"))
        if self.claim_count != sum(tallies.values()):
            raise ValueError(
                "a row's claim count must be its own "
                "sections' sum")
        if self.claim_count < 1:
            raise ValueError(
                "a row's claim count must name at least "
                "one claim of its own")
        object.__setattr__(
            self, "evidence_count",
            _check_count(self.evidence_count, "a row's evidence count"))
        if self.evidence_count < 1:
            raise ValueError(
                "a row's evidence count must name at "
                "least one reference of its own")
        object.__setattr__(
            self, "written_by",
            _check_title(self.written_by, "a row's writer"))
        object.__setattr__(
            self, "written_on", _check_day(self.written_on))

    @property
    def sort_key(self) -> Tuple[str, str, str, str, str]:
        """This row's place in panel order (derived).

        Rows stand by project, then day, then branch,
        then title, then handoff id.
        """
        return (self.project.lower(), self.written_on,
                self.branch.lower(), self.title.lower(),
                self.handoff_id)

    def count_for(self, kind: Any) -> int:
        """This row's count in one claim section."""
        return getattr(self, f"{normalize_claim_kind(kind)}_count")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "handoff_summaries_panel_row",
            "slice": HANDOFF_SUMMARIES_SLICE,
            "handoff_id": self.handoff_id,
            "title": self.title,
            "session_ref": self.session_ref,
            "project": self.project,
            "branch": self.branch,
            "done_count": self.done_count,
            "doing_count": self.doing_count,
            "blocked_count": self.blocked_count,
            "needs_you_count": self.needs_you_count,
            "claim_count": self.claim_count,
            "evidence_count": self.evidence_count,
            "written_by": self.written_by,
            "written_on": self.written_on,
        }


def _row_for_handoff(handoff: HandoffSummary) -> HandoffPanelRow:
    counts = handoff.counts()
    return HandoffPanelRow(
        handoff_id=handoff.handoff_id, title=handoff.title,
        session_ref=handoff.session_ref, project=handoff.project,
        branch=handoff.branch, done_count=counts["done"],
        doing_count=counts["doing"], blocked_count=counts["blocked"],
        needs_you_count=counts["needs_you"],
        claim_count=handoff.claim_count,
        evidence_count=handoff.evidence_count,
        written_by=handoff.written_by,
        written_on=handoff.written_on)


def _check_row_ref(value: Any) -> HandoffPanelRow:
    if isinstance(value, HandoffPanelRow):
        return value
    if isinstance(value, dict):
        unknown = set(value) - _ROW_KEYS
        if unknown:
            raise ValueError(
                "unknown row keys: %s" % ", ".join(sorted(unknown)))

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            picked = _pick_any(value, spellings, what)
            if picked is None:
                raise ValueError(f"a row is missing its {what}")
            return picked

        return HandoffPanelRow(
            handoff_id=_needed(("handoff_id", "id"), "handoff id"),
            title=_needed(("title",), "title"),
            session_ref=_needed(("session_ref",), "session reference"),
            project=_needed(("project",), "project"),
            branch=_needed(("branch",), "branch"),
            done_count=_needed(("done_count",), "done count"),
            doing_count=_needed(("doing_count",), "doing count"),
            blocked_count=_needed(("blocked_count",), "blocked count"),
            needs_you_count=_needed(
                ("needs_you_count",), "needs-you count"),
            claim_count=_needed(("claim_count", "claims"), "claim count"),
            evidence_count=_needed(
                ("evidence_count", "evidence"), "evidence count"),
            written_by=_needed(("written_by",), "writer"),
            written_on=_needed(("written_on",), "written-on day"))
    raise ValueError(f"a panel row is needed, got {value!r}")


def validate_row(row: Any, handoff: Any = None) -> HandoffPanelRow:
    """Validate one panel row into a HandoffPanelRow.

    With *handoff* given, the row is judged against
    the row derived from that handoff: a stored row
    whose fields disagree with the derived row
    refuses.
    """
    current = _check_row_ref(row)
    if handoff is not None:
        checked = _check_handoff_ref(handoff)
        derived = _row_for_handoff(checked)
        if current != derived:
            raise ValueError(
                "a stored row disagrees with the row "
                "derived from its handoff")
    return current


def build_row(row: Any = None, handoff: Any = None,
              **kwargs: Any) -> HandoffPanelRow:
    """Build one validated row, from a mapping or field words."""
    if isinstance(row, HandoffPanelRow) and not kwargs:
        return validate_row(row, handoff)
    if isinstance(row, dict) or row is None:
        merged: Dict[str, Any] = {}
        if isinstance(row, dict):
            merged.update(row)
        merged.update(kwargs)
        return validate_row(merged, handoff)
    return validate_row(row, handoff)


@dataclass(frozen=True)
class SectionCount:
    """One claim section's count in a panel: its claims tallied."""

    kind: str
    claims: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "kind", normalize_claim_kind(self.kind))
        object.__setattr__(
            self, "claims",
            _check_count(self.claims, "a section count's claims"))

    def to_record(self) -> Dict[str, Any]:
        return {"kind": self.kind, "claims": self.claims}


def _check_section_count_ref(value: Any) -> SectionCount:
    if isinstance(value, SectionCount):
        return value
    if isinstance(value, dict):
        unknown = set(value) - _SECTION_COUNT_KEYS
        if unknown:
            raise ValueError(
                "unknown section-count keys: %s"
                % ", ".join(sorted(unknown)))
        kind = _pick_any(value, ("kind",), "kinds")
        if kind is None:
            raise ValueError("a section count is missing its kind")
        claims = _pick_any(value, ("claims", "count"), "claims")
        if claims is None:
            raise ValueError("a section count is missing its claims")
        return SectionCount(kind=kind, claims=claims)
    raise ValueError(f"a section count is needed, got {value!r}")


def _panel_account(total_handoffs: int, total_claims: int,
                   total_evidence: int,
                   section_counts: Tuple[SectionCount, ...]
                   ) -> Tuple[str, ...]:
    tallies = ", ".join(
        f"{count.kind} {count.claims}"
        for count in sorted(
            section_counts, key=lambda count: count.kind))
    return (
        f"The handoff panel holds {total_handoffs} handoffs: "
        f"{total_claims} claims in all, {total_evidence} "
        f"evidence references: {tallies}.",
        "Handoffs stand by project, then day, then "
        "branch, then title, then handoff id, so two "
        "panels of one book diff cleanly, line by line.",
        "Every claim a handoff carries is carried from "
        "the stand-up of its session, and a handoff "
        "whose claims disagree with that evidence is "
        "refused - a handoff states only what its "
        "evidence states.",
        "The panel is read off the book at call time - "
        "it is derived, never stored loose.",
    )


@dataclass(frozen=True)
class HandoffPanel:
    """The handoff panel of one book, derived whole.

    ``rows`` are the book's handoffs carried whole,
    in panel order (by project, then day, then
    branch, then title, then handoff id);
    ``total_handoffs`` is the rows' own count,
    ``total_claims`` the sum of their claims and
    ``total_evidence`` the sum of their evidence
    references; ``section_counts`` are the per-kind
    tallies of every claim in the book, in claim-kind
    order; ``account`` is read off those numbers. A
    panel whose rows stand out of panel order, or
    whose tallies are not its own rows' tallies,
    refuses at construction; :func:`validate_panel`
    judged against a book refuses a stored panel
    that disagrees with the derived one.
    """

    rows: Tuple[HandoffPanelRow, ...] = ()
    total_handoffs: int = 0
    total_claims: int = 0
    total_evidence: int = 0
    section_counts: Tuple[SectionCount, ...] = ()
    account: Tuple[str, ...] = ()
    panel_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.panel_id is not None:
            object.__setattr__(
                self, "panel_id", normalize_member_id(self.panel_id))
        if isinstance(self.rows, (str, bytes)) \
                or not isinstance(self.rows, (list, tuple)):
            raise ValueError(
                f"a panel's rows must be a list of rows, "
                f"got {self.rows!r}")
        rows = tuple(_check_row_ref(r) for r in self.rows)
        seen = set()
        for row in rows:
            if row.handoff_id in seen:
                raise ValueError(
                    f"a panel row for handoff {row.handoff_id!r} "
                    f"already exists")
            seen.add(row.handoff_id)
        keys = [row.sort_key for row in rows]
        if keys != sorted(keys):
            raise ValueError(
                "a panel's rows must stand in panel order "
                "(by project, then day, then branch, then "
                "title, then handoff id)")
        object.__setattr__(self, "rows", rows)
        object.__setattr__(
            self, "total_handoffs",
            _check_count(self.total_handoffs, "a panel's total handoffs"))
        if self.total_handoffs != len(rows):
            raise ValueError(
                "a panel's total handoffs must be its own "
                "rows' count")
        object.__setattr__(
            self, "total_claims",
            _check_count(self.total_claims, "a panel's total claims"))
        if self.total_claims != sum(r.claim_count for r in rows):
            raise ValueError(
                "a panel's total claims must be its own "
                "rows' sum")
        object.__setattr__(
            self, "total_evidence",
            _check_count(self.total_evidence, "a panel's total evidence"))
        if self.total_evidence != sum(r.evidence_count for r in rows):
            raise ValueError(
                "a panel's total evidence must be its "
                "own rows' sum")
        if isinstance(self.section_counts, (str, bytes)) \
                or not isinstance(self.section_counts, (list, tuple)):
            raise ValueError(
                f"a panel's section counts must be a list, "
                f"got {self.section_counts!r}")
        section_counts = tuple(
            _check_section_count_ref(c) for c in self.section_counts)
        seen_kinds = set()
        for count in section_counts:
            if count.kind in seen_kinds:
                raise ValueError(
                    f"a section count named {count.kind!r} "
                    f"already exists")
            seen_kinds.add(count.kind)
        object.__setattr__(self, "section_counts", section_counts)
        if sum(c.claims for c in section_counts) != self.total_claims:
            raise ValueError(
                "a panel's section counts must sum to "
                "its own total claims")
        tallies: Dict[str, int] = {kind: 0 for kind in CLAIM_KINDS}
        for row in rows:
            for kind in CLAIM_KINDS:
                tallies[kind] += row.count_for(kind)
        for count in section_counts:
            if count.claims != tallies.get(count.kind, 0):
                raise ValueError(
                    "a panel's section counts must be its "
                    "own rows' counts")
        if {k for k, v in tallies.items() if v} != {
                c.kind for c in section_counts}:
            raise ValueError(
                "a panel's section counts must name "
                "every kind its rows carry")
        object.__setattr__(self, "account", _check_account(self.account))

    def row_for(self, handoff_id: Any) -> HandoffPanelRow:
        """The panel row one handoff names in this panel."""
        wanted = normalize_member_id(handoff_id)
        for row in self.rows:
            if row.handoff_id == wanted:
                return row
        raise KeyError(f"no row in the panel: handoff {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "handoff_summaries_panel",
            "slice": HANDOFF_SUMMARIES_SLICE,
            "panel_id": self.panel_id,
            "rows": [row.to_record() for row in self.rows],
            "total_handoffs": self.total_handoffs,
            "total_claims": self.total_claims,
            "total_evidence": self.total_evidence,
            "section_counts": [c.to_record() for c in self.section_counts],
            "account": list(self.account),
        }


def _held_handoffs(source: Any) -> Tuple[HandoffSummary, ...]:
    if isinstance(source, HandoffBook):
        return source.handoffs
    if isinstance(source, HandoffRegistry):
        return source.list_handoffs()
    if isinstance(source, (list, tuple)):
        return tuple(_check_handoff_ref(item) for item in source)
    raise ValueError(f"handoff summaries are needed, got {source!r}")


def derive_panel(source: Any) -> HandoffPanel:
    """Derive the handoff panel from one book.

    The rows are the book's handoffs carried whole,
    in panel order: by project, then day, then
    branch, then title, then handoff id. *source* is
    a book or a registry. A source holding no
    handoff refuses - a panel of nothing is no panel.
    """
    handoffs = _held_handoffs(source)
    if not handoffs:
        raise ValueError("a panel needs at least one handoff summary")
    rows = []
    for handoff in handoffs:
        if handoff.handoff_id is None:
            raise ValueError(
                "a panel row must name its handoff - a "
                "handoff with no id refuses derivation")
        rows.append(_row_for_handoff(handoff))
    rows = tuple(sorted(rows, key=lambda r: r.sort_key))
    tallies: Dict[str, int] = {kind: 0 for kind in CLAIM_KINDS}
    for row in rows:
        for kind in CLAIM_KINDS:
            tallies[kind] += row.count_for(kind)
    section_counts = tuple(
        SectionCount(kind=kind, claims=tallies[kind])
        for kind in CLAIM_KINDS if tallies[kind])
    total_claims = sum(r.claim_count for r in rows)
    total_evidence = sum(r.evidence_count for r in rows)
    return HandoffPanel(
        rows=rows, total_handoffs=len(rows),
        total_claims=total_claims, total_evidence=total_evidence,
        section_counts=section_counts,
        account=_panel_account(
            len(rows), total_claims, total_evidence, section_counts))


def validate_panel(panel: Any, source: Any = None
                   ) -> HandoffPanel:
    """Validate one panel into a HandoffPanel.

    Accepts a panel or a mapping naming ``rows`` (or
    ``handoffs``), a ``total_handoffs`` (or
    ``total``), ``total_claims``, ``total_evidence``,
    ``section_counts`` (or ``sections``), an
    ``account`` (or ``statements``) and an optional
    ``panel_id`` (or ``id``). With *source* given (a
    book), the panel is judged against the panel
    derived from that book.
    """
    if isinstance(panel, HandoffPanel):
        current = panel
    elif isinstance(panel, dict):
        unknown = set(panel) - _PANEL_KEYS
        if unknown:
            raise ValueError(
                "unknown panel keys: %s" % ", ".join(sorted(unknown)))
        rows = _pick_any(panel, ("rows", "handoffs"), "rows")
        if rows is None:
            raise ValueError("a panel is missing its rows")
        total = _pick_any(panel, ("total_handoffs", "total"), "totals")
        if total is None:
            raise ValueError("a panel is missing its total handoffs")
        claims = _pick_any(panel, ("total_claims", "claims"), "claim totals")
        if claims is None:
            raise ValueError("a panel is missing its total claims")
        evidence = _pick_any(
            panel, ("total_evidence", "evidence"), "evidence totals")
        if evidence is None:
            raise ValueError("a panel is missing its total evidence")
        section_counts = _pick_any(
            panel, ("section_counts", "sections"), "section counts")
        if section_counts is None:
            raise ValueError("a panel is missing its section counts")
        account = _pick_any(panel, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError("a panel names no account of its own")
        kwargs: Dict[str, Any] = {
            "rows": rows, "total_handoffs": total,
            "total_claims": claims, "total_evidence": evidence,
            "section_counts": section_counts, "account": account}
        panel_id = _pick_any(panel, ("panel_id", "id"), "panel ids")
        if panel_id is not None:
            kwargs["panel_id"] = panel_id
        current = HandoffPanel(**kwargs)
    else:
        raise ValueError(f"a panel must be a mapping, got {panel!r}")
    if source is not None:
        derived = derive_panel(source)
        if (current.rows != derived.rows
                or current.total_handoffs != derived.total_handoffs
                or current.total_claims != derived.total_claims
                or current.total_evidence != derived.total_evidence
                or current.section_counts != derived.section_counts
                or current.account != derived.account):
            raise ValueError(
                "a stored panel disagrees with the panel "
                "derived from its book")
    return current


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> HandoffPanel:
    """Build one validated panel, from a mapping or field words."""
    if isinstance(panel, HandoffPanel) and not kwargs:
        return validate_panel(panel, source)
    if isinstance(panel, dict) or panel is None:
        merged: Dict[str, Any] = {}
        if isinstance(panel, dict):
            merged.update(panel)
        merged.update(kwargs)
        return validate_panel(merged, source)
    return validate_panel(panel, source)


# ---------------------------------------------------------------------
# The handoff verdict: the whole book judged, derived.
# ---------------------------------------------------------------------


def _verdict_word(total_blocked: int, total_needs_you: int) -> str:
    """The verdict word a book's own tallies derive."""
    if total_needs_you:
        return "awaiting-you"
    if total_blocked:
        return "held-up"
    return "standing-clear"


@dataclass(frozen=True)
class EvidenceVerdict:
    """One handoff verdict: a whole book judged, as data.

    ``total_handoffs`` counts the book's handoffs,
    ``total_claims`` their claims in all and
    ``total_evidence`` the evidence references they
    stand on; ``total_blocked`` and
    ``total_needs_you`` are the claims standing
    blocked and waiting on the human's word;
    ``distinct_sessions`` counts how many sessions
    those handoffs end; ``verdict`` is the book's
    word - ``awaiting-you`` when any claim needs the
    human's word, ``held-up`` when claims stand
    blocked and none needs you, ``standing-clear``
    when neither stands. :func:`validate_verdict`
    judged against a book refuses a stored verdict
    that disagrees with the verdict derived from
    that book, and a verdict whose word is not its
    own tallies' word refuses at construction - what
    needs you is never smoothed away.
    """

    total_handoffs: int
    total_claims: int
    total_evidence: int
    total_blocked: int
    total_needs_you: int
    distinct_sessions: int
    verdict: str

    def __post_init__(self) -> None:
        for field, what in (
                ("total_handoffs", "total handoffs"),
                ("total_claims", "total claims"),
                ("total_evidence", "total evidence"),
                ("total_blocked", "total blocked"),
                ("total_needs_you", "total needs-you"),
                ("distinct_sessions", "distinct sessions")):
            object.__setattr__(
                self, field,
                _check_count(getattr(self, field), f"a verdict's {what}"))
        if self.total_handoffs < 1:
            raise ValueError("a verdict judges at least one handoff")
        if self.distinct_sessions < 1 \
                or self.distinct_sessions > self.total_handoffs:
            raise ValueError(
                "a verdict's distinct sessions must stand "
                "between one and its own total handoffs")
        if self.total_blocked + self.total_needs_you > self.total_claims:
            raise ValueError(
                "a verdict's blocked and needs-you claims "
                "must not exceed its own total claims")
        verdict = _clean_text(self.verdict, "a verdict's word")
        expected = _verdict_word(self.total_blocked, self.total_needs_you)
        if verdict != expected:
            raise ValueError(
                "a verdict's word must be its own counts' "
                "word - a verdict is derived, never stored "
                "loose")
        object.__setattr__(self, "verdict", verdict)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "handoff_summaries_verdict",
            "slice": HANDOFF_SUMMARIES_SLICE,
            "total_handoffs": self.total_handoffs,
            "total_claims": self.total_claims,
            "total_evidence": self.total_evidence,
            "total_blocked": self.total_blocked,
            "total_needs_you": self.total_needs_you,
            "distinct_sessions": self.distinct_sessions,
            "verdict": self.verdict,
        }


def derive_verdict(source: Any) -> EvidenceVerdict:
    """Derive the handoff verdict of one book.

    The verdict's tallies are the derived panel's
    own section counts read whole, its distinct
    count is read off the handoffs' actual sessions,
    and its word is read off its blocked and
    needs-you tallies. *source* is a book or a
    registry.
    """
    handoffs = _held_handoffs(source)
    panel = derive_panel(source)
    counts = {c.kind: c.claims for c in panel.section_counts}
    return EvidenceVerdict(
        total_handoffs=panel.total_handoffs,
        total_claims=panel.total_claims,
        total_evidence=panel.total_evidence,
        total_blocked=counts.get("blocked", 0),
        total_needs_you=counts.get("needs_you", 0),
        distinct_sessions=len({h.session_ref for h in handoffs}),
        verdict=_verdict_word(
            counts.get("blocked", 0), counts.get("needs_you", 0)))


def _check_verdict_ref(value: Any) -> EvidenceVerdict:
    if isinstance(value, EvidenceVerdict):
        return value
    if isinstance(value, dict):
        unknown = set(value) - _VERDICT_KEYS
        if unknown:
            raise ValueError(
                "unknown verdict keys: %s" % ", ".join(sorted(unknown)))

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            picked = _pick_any(value, spellings, what)
            if picked is None:
                raise ValueError(f"a verdict is missing its {what}")
            return picked

        needs = _pick_any(
            value, ("total_needs_you", "needs_you", "needs-you"),
            "needs-you totals")
        if needs is None:
            raise ValueError("a verdict is missing its total needs-you")
        return EvidenceVerdict(
            total_handoffs=_needed(
                ("total_handoffs", "total"), "total handoffs"),
            total_claims=_needed(
                ("total_claims", "claims"), "total claims"),
            total_evidence=_needed(
                ("total_evidence", "evidence"), "total evidence"),
            total_blocked=_needed(
                ("total_blocked", "blocked"), "total blocked"),
            total_needs_you=needs,
            distinct_sessions=_needed(
                ("distinct_sessions", "sessions"), "distinct sessions"),
            verdict=_needed(("verdict",), "verdict word"))
    raise ValueError(f"a handoff verdict is needed, got {value!r}")


def validate_verdict(verdict: Any, source: Any = None) -> EvidenceVerdict:
    """Validate one verdict into an EvidenceVerdict.

    With *source* given (a book), the verdict is
    judged against the verdict derived from that
    book: a stored verdict whose tallies, distinct
    count or word disagree with the derived verdict
    refuses.
    """
    current = _check_verdict_ref(verdict)
    if source is not None:
        derived = derive_verdict(source)
        if current != derived:
            raise ValueError(
                "a stored verdict disagrees with the "
                "verdict derived from its book")
    return current


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> EvidenceVerdict:
    """Build one validated verdict, from a mapping or field words."""
    if isinstance(verdict, EvidenceVerdict) and not kwargs:
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict) or verdict is None:
        merged: Dict[str, Any] = {}
        if isinstance(verdict, dict):
            merged.update(verdict)
        merged.update(kwargs)
        return validate_verdict(merged, source)
    return validate_verdict(verdict, source)


# ---------------------------------------------------------------------
# The book: handoffs in held order, panels judged.
# ---------------------------------------------------------------------


def _judge_handoffs(handoffs: Tuple[HandoffSummary, ...],
                    held: Tuple[HandoffSummary, ...] = ()) -> None:
    """Judge handoffs against held writings: the book's laws.

    One handoff per session - a session ends once -
    and no claim standing in two handoffs: a claim
    is handed off once. *held* names handoffs
    already standing (a registry's), judged
    alongside.
    """
    all_handoffs = tuple(held) + tuple(handoffs)
    seen_sessions = set()
    owners: Dict[str, str] = {}
    for handoff in all_handoffs:
        if handoff.session_ref in seen_sessions:
            raise ValueError(
                f"the session {handoff.session_ref!r} "
                f"already has a handoff - a session ends "
                f"once, and is handed off once")
        seen_sessions.add(handoff.session_ref)
        for kind in CLAIM_KINDS:
            for claim in handoff.section(kind):
                if claim in owners:
                    raise ValueError(
                        f"a claim handed off twice: claim "
                        f"{claim!r} stands in two handoffs "
                        f"({owners[claim]!r} and "
                        f"{handoff.session_ref!r}) - a claim "
                        f"is handed off once")
                owners[claim] = handoff.session_ref


@dataclass(frozen=True)
class HandoffBook:
    """One handoff book: its handoffs, in held order.

    ``handoffs`` are the handoff summaries, in held
    order, each with its provenance whole, one per
    session, no claim standing in two handoffs.
    ``panels`` are the book's derivations - handoff
    panels of the whole book, each judged against
    the book by :func:`validate_book`; ``canon_note``
    is the book's own note. The total is the
    handoffs' own count, judged at construction.
    """

    title: str = ""
    handoffs: Tuple[HandoffSummary, ...] = ()
    panels: Tuple[HandoffPanel, ...] = ()
    canon_note: str = ""
    total_handoffs: Optional[int] = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book's title"))
        if isinstance(self.handoffs, (str, bytes)) \
                or not isinstance(self.handoffs, (list, tuple)):
            raise ValueError(
                f"a book's handoffs must be a list of "
                f"handoffs, got {self.handoffs!r}")
        handoffs = tuple(_check_handoff_ref(item) for item in self.handoffs)
        if not handoffs:
            raise ValueError("a handoff book holds at least one handoff")
        seen_ids = set()
        for handoff in handoffs:
            if handoff.handoff_id is not None:
                if handoff.handoff_id in seen_ids:
                    raise ValueError(
                        f"a handoff named "
                        f"{handoff.handoff_id!r} already exists")
                seen_ids.add(handoff.handoff_id)
        _judge_handoffs(handoffs)
        object.__setattr__(self, "handoffs", handoffs)
        if isinstance(self.panels, (str, bytes)) \
                or not isinstance(self.panels, (list, tuple)):
            raise ValueError(
                f"a book's panels must be a list of panels, "
                f"got {self.panels!r}")
        panels = tuple(
            p if isinstance(p, HandoffPanel)
            else validate_panel(p)
            for p in self.panels)
        seen_panels = set()
        for panel in panels:
            if panel.panel_id is not None:
                if panel.panel_id in seen_panels:
                    raise ValueError(
                        f"a panel named {panel.panel_id!r} "
                        f"already exists")
                seen_panels.add(panel.panel_id)
        object.__setattr__(self, "panels", panels)
        if not isinstance(self.canon_note, str):
            raise ValueError("a book's note must be text")
        object.__setattr__(self, "canon_note", self.canon_note.strip())
        given = self.total_handoffs
        if given is None:
            object.__setattr__(self, "total_handoffs", len(handoffs))
        else:
            checked = _check_count(given, "a book's total handoffs")
            if checked != len(handoffs):
                raise ValueError(
                    "a book's total handoffs must be its "
                    "own handoffs' count")
            object.__setattr__(self, "total_handoffs", checked)

    def handoff_for(self, handoff_id: Any) -> HandoffSummary:
        """The handoff one id names in this book."""
        wanted = normalize_member_id(handoff_id)
        for handoff in self.handoffs:
            if handoff.handoff_id == wanted:
                return handoff
        raise KeyError(f"no handoff in the book: {wanted!r}")

    def handoff_for_session(self, session_ref: Any) -> HandoffSummary:
        """The handoff ending one session in this book."""
        wanted = _check_word(session_ref, "a session reference")
        for handoff in self.handoffs:
            if handoff.session_ref == wanted:
                return handoff
        raise KeyError(f"no handoff in the book ends {wanted!r}")

    def panel_for(self, panel_id: Any) -> HandoffPanel:
        """The stored panel one id names in this book."""
        wanted = normalize_member_id(panel_id)
        for panel in self.panels:
            if panel.panel_id == wanted:
                return panel
        raise KeyError(f"no panel in the book: {wanted!r}")

    def handoff_ids(self) -> Tuple[str, ...]:
        """Every held handoff id, in held order."""
        return tuple(
            item.handoff_id for item in self.handoffs if item.handoff_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "handoff_summaries_book",
            "slice": HANDOFF_SUMMARIES_SLICE,
            "title": self.title,
            "handoff_ids": list(self.handoff_ids()),
            "handoff_count": len(self.handoffs),
            "panel_count": len(self.panels),
        }


def validate_book(data: Any, *, require_example: bool = False
                  ) -> HandoffBook:
    """Validate one handoff mapping into a book.

    The mapping names a ``schema``, a ``guide``
    mapping (its ``title``), a ``handoffs`` list (or
    ``records``) and an optional ``panels`` list.
    Every handoff stands on its own validation, then
    the whole is judged: handoff ids unique, one
    handoff per session, no claim handed off twice,
    and every stored panel judged against the book.
    With ``require_example`` the shipped example is
    held to its pinned shape.
    """
    if isinstance(data, HandoffBook):
        return data
    if not isinstance(data, dict):
        raise ValidationError(
            f"a handoff book must be a mapping, got {data!r}")
    unknown = set(data) - _HANDOFF_BOOK_KEYS
    if unknown:
        raise ValidationError(
            "unknown handoff-book keys: %s"
            % ", ".join(sorted(unknown)))
    if data.get("schema") != HANDOFF_SUMMARIES_SCHEMA:
        raise ValidationError(
            f"a handoff book must carry schema "
            f"{HANDOFF_SUMMARIES_SCHEMA!r}, "
            f"got {data.get('schema')!r}")
    handoffs = _pick_any(data, ("handoffs", "records"), "handoffs")
    if handoffs is None:
        raise ValidationError("a handoff book is missing its handoffs")
    if not isinstance(handoffs, (list, tuple)):
        raise ValidationError("a handoff book's handoffs must be a list")
    if data.get("panels") is not None \
            and not isinstance(data["panels"], (list, tuple)):
        raise ValidationError("a handoff book's panels must be a list")
    head = data.get("guide") or {}
    if not isinstance(head, dict):
        raise ValidationError("a handoff book's guide must be a mapping")
    unknown_head = set(head) - _BOOK_KEYS
    if unknown_head:
        raise ValidationError(
            "unknown guide keys: %s" % ", ".join(sorted(unknown_head)))
    try:
        title = _pick_any(head, ("title", "name"), "titles")
        if title is None:
            raise ValidationError("a handoff book is missing its title")
        note = data.get("canon_note") or ""
        if not isinstance(note, str):
            raise ValidationError("a handoff book's note must be text")
        book = HandoffBook(
            title=title, handoffs=tuple(handoffs),
            panels=tuple(data.get("panels") or ()), canon_note=note)
        for panel in book.panels:
            validate_panel(panel, book)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    if require_example:
        if book.title != _EXAMPLE_TITLE:
            raise ValidationError(
                "the shipped example handoff book's "
                "title is not the pinned title")
        if book.handoff_ids() != _EXAMPLE_HANDOFF_IDS:
            raise ValidationError(
                "the shipped example's handoffs are not "
                "the pinned handoffs")
        panel = book.panel_for(_EXAMPLE_PANEL_ID)
        if tuple(r.handoff_id for r in panel.rows) != _EXAMPLE_PANEL_ROW_IDS:
            raise ValidationError(
                "the shipped example panel does not name "
                "its pinned rows in panel order")
        if panel.account != _EXAMPLE_PANEL_ACCOUNT:
            raise ValidationError(
                "the shipped example panel does not carry "
                "its pinned account word-for-word")
        first = book.handoffs[0]
        if first.handoff_id != _EXAMPLE_FIRST_HANDOFF_ID \
                or first.title != _EXAMPLE_FIRST_HANDOFF_TITLE:
            raise ValidationError(
                "the shipped example's first handoff is "
                "not its pinned handoff of its pinned title")
    return book


def build_book(book: Any = None, **kwargs: Any) -> HandoffBook:
    """Build one validated book, from a mapping or field words."""
    if isinstance(book, HandoffBook) and not kwargs:
        return book
    if isinstance(book, dict):
        if "schema" in book:
            return validate_book(book)
        merged: Dict[str, Any] = dict(book)
        merged.update(kwargs)
        return HandoffBook(**merged)
    if book is None:
        return HandoffBook(**kwargs)
    raise ValueError(f"a handoff book is needed, got {book!r}")


def _book_from(data: Any, *, require_example: bool) -> HandoffBook:
    try:
        return validate_book(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_handoff_summaries(
        data: Optional[Dict[str, Any]] = None) -> HandoffBook:
    """Load and validate the shipped example book (or *data*)."""
    raw = data if data is not None else load_resource(
        HANDOFF_SUMMARIES_RESOURCE)
    return _book_from(raw, require_example=True)


def load_handoff_summaries_file(path: Any) -> HandoffBook:
    """Load and validate a handoff book from a file at *path*."""
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _book_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The registry model: one book held handoff by handoff.
# ---------------------------------------------------------------------


class HandoffRegistry:
    """One book's handoffs, held one by one.

    The registry holds handoffs, never panels or
    verdicts: the panel and the handoff verdict are
    derivations, read off the whole held book at
    call time. A whole book is judged as a book
    judges it before its handoffs are held in book
    order. A handoff held here stands apart: a
    second handoff ending a held session, or naming
    a held claim, refuses - a session ends once and
    a claim is handed off once.
    """

    def __init__(self, book: Any = None) -> None:
        self._title: Optional[str] = None
        self._handoffs: Dict[str, HandoffSummary] = {}
        self._handoff_order: list = []
        self._next_handoff = 1
        if book is not None:
            self.register_book(book)

    def _fresh_handoff_id(self, held_ids: Any) -> str:
        while f"handoff-{self._next_handoff}" in held_ids:
            self._next_handoff += 1
        fresh = f"handoff-{self._next_handoff}"
        self._next_handoff += 1
        return fresh

    def _check_standing_free(self, handoff: HandoffSummary) -> None:
        _judge_handoffs((handoff,), held=self.list_handoffs())

    def register_handoff(self, handoff: Any) -> HandoffSummary:
        """Register one handoff into the held book."""
        validated = _check_handoff_ref(handoff)
        if validated.handoff_id is not None \
                and validated.handoff_id in self._handoffs:
            raise ValueError(
                f"a handoff named "
                f"{validated.handoff_id!r} already exists")
        self._check_standing_free(validated)
        return self._hold_handoff(validated)

    def _hold_handoff(self, validated: HandoffSummary) -> HandoffSummary:
        if validated.handoff_id is None:
            validated = replace(
                validated,
                handoff_id=self._fresh_handoff_id(set(self._handoffs)))
        self._handoffs[validated.handoff_id] = validated
        self._handoff_order.append(validated.handoff_id)
        return validated

    def register_book(self, book: Any) -> HandoffBook:
        """Register every handoff of one book, in order."""
        validated = build_book(book)
        if self._title is not None and validated.title != self._title:
            raise ValueError(
                "this registry already holds a handoff "
                "book under a different title")
        for handoff in validated.handoffs:
            if handoff.handoff_id in self._handoffs:
                raise ValueError(
                    f"a handoff named "
                    f"{handoff.handoff_id!r} already exists")
        _judge_handoffs(validated.handoffs, held=self.list_handoffs())
        self._title = validated.title
        for handoff in validated.handoffs:
            self._hold_handoff(handoff)
        return self.book()

    def get_handoff(self, handoff_id: Any) -> HandoffSummary:
        """The handoff one id names among the held handoffs."""
        wanted = normalize_member_id(handoff_id)
        if wanted not in self._handoffs:
            raise KeyError(f"unknown handoff: {wanted!r}")
        return self._handoffs[wanted]

    def handoff_for_session(self, session_ref: Any) -> HandoffSummary:
        """The held handoff ending one session."""
        wanted = _check_word(session_ref, "a session reference")
        for handoff_id in self._handoff_order:
            handoff = self._handoffs[handoff_id]
            if handoff.session_ref == wanted:
                return handoff
        raise KeyError(f"no handoff held ends {wanted!r}")

    def latest_handoff(self) -> HandoffSummary:
        """The most recently held handoff."""
        if not self._handoff_order:
            raise ValueError("no handoff is held yet")
        return self._handoffs[self._handoff_order[-1]]

    def list_handoffs(self) -> Tuple[HandoffSummary, ...]:
        """Every held handoff, in the order they were held."""
        return tuple(self._handoffs[item] for item in self._handoff_order)

    def book(self) -> HandoffBook:
        """The held handoffs as one validated book."""
        if self._title is None:
            raise ValueError("no handoff book is held yet")
        return HandoffBook(
            title=self._title, handoffs=self.list_handoffs())

    def panel(self) -> HandoffPanel:
        """Derive the handoff panel of the whole held book."""
        return derive_panel(self)

    def verdict(self) -> EvidenceVerdict:
        """Derive the handoff verdict of the whole held book."""
        return derive_verdict(self)


# ---------------------------------------------------------------------
# The visible surface: how the book stands, read off any book.
# ---------------------------------------------------------------------


def handoff_refs(source: Any) -> Tuple[Tuple[str, str], ...]:
    """Every handoff one source holds, in panel order.

    Each held handoff's session reference and the
    branch its session stood on, in the order the
    derived panel shows them. *source* is a book or
    a registry.
    """
    panel = derive_panel(source)
    return tuple((row.session_ref, row.branch) for row in panel.rows)


def total_claims(source: Any) -> int:
    """The claims one source holds, in all."""
    return derive_panel(source).total_claims


def total_evidence(source: Any) -> int:
    """The evidence references one source holds, in all."""
    return derive_panel(source).total_evidence


# ---------------------------------------------------------------------
# Handoff news, shaped as session records.
# ---------------------------------------------------------------------


def handoff_record(handoff: Any) -> Dict[str, Any]:
    """The session-news record of one handoff summary."""
    current = handoff if isinstance(handoff, HandoffSummary) \
        else build_handoff(handoff)
    counts = current.counts()
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Handoff for session {current.session_ref} on "
        f"{current.branch}: \"{current.title}\" - "
        f"{current.claim_count} claims (done {counts['done']}, "
        f"doing {counts['doing']}, blocked {counts['blocked']}, "
        f"needs-you {counts['needs_you']}) on "
        f"{current.evidence_count} evidence references, "
        f"written by {current.written_by} on "
        f"{current.written_on}.")
    return record_out


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived panel."""
    current = validate_panel(panel, source)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Handoff panel: {current.total_handoffs} handoffs - "
        f"{current.total_claims} claims, "
        f"{current.total_evidence} evidence references.")
    return record_out


def verdict_record(verdict: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived verdict."""
    current = validate_verdict(verdict, source)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Handoff verdict: {current.verdict} - "
        f"{current.total_needs_you} claims need your word, "
        f"{current.total_blocked} blocked, across "
        f"{current.distinct_sessions} sessions.")
    return record_out


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one handoff book."""
    current = book if isinstance(book, HandoffBook) \
        else build_book(book)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Handoff summaries {current.title}: "
        f"{record_out['handoff_count']} handoffs held.")
    return record_out


def plain_words(handoff: Any) -> str:
    """One handoff summary, in one plain sentence."""
    current = handoff if isinstance(handoff, HandoffSummary) \
        else build_handoff(handoff)
    counts = current.counts()
    return (
        f"\"{current.title}\" hands off session "
        f"{current.session_ref} on {current.project} "
        f"(branch {current.branch}): {counts['done']} done, "
        f"{counts['doing']} doing, {counts['blocked']} blocked, "
        f"{counts['needs_you']} needing your word, on "
        f"{current.evidence_count} evidence references. It "
        f"was written by {current.written_by} on "
        f"{current.written_on} (read from {current.source}).")


def panel_plain_words(source: Any) -> str:
    """The handoff panel in plain words, in full."""
    if isinstance(source, HandoffPanel):
        panel = validate_panel(source)
        title = None
    elif isinstance(source, HandoffBook):
        panel = derive_panel(source)
        title = source.title
    else:
        raise ValueError(
            f"a handoff source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Handoff summaries, in panel order:")
    for row in panel.rows:
        lines.append(
            f"{row.handoff_id}: \"{row.title}\" - "
            f"session {row.session_ref} on branch "
            f"{row.branch}, {row.claim_count} claims "
            f"(done {row.done_count}, doing {row.doing_count}, "
            f"blocked {row.blocked_count}, needs-you "
            f"{row.needs_you_count}), {row.evidence_count} "
            f"evidence references, written by "
            f"{row.written_by} on {row.written_on}")
    lines.extend(panel.account)
    return "\n".join(lines)


def verdict_plain_words(source: Any) -> str:
    """The handoff verdict in plain words."""
    if isinstance(source, EvidenceVerdict):
        verdict = validate_verdict(source)
    elif isinstance(source, (HandoffBook, HandoffRegistry)):
        verdict = derive_verdict(source)
    else:
        raise ValueError(
            f"a handoff source is needed, got {source!r}")
    return (
        f"Handoff verdict: {verdict.verdict} - "
        f"{verdict.total_handoffs} handoffs carry "
        f"{verdict.total_claims} claims on "
        f"{verdict.total_evidence} evidence references "
        f"across {verdict.distinct_sessions} sessions: "
        f"{verdict.total_blocked} blocked, "
        f"{verdict.total_needs_you} needing your word.")


# ---------------------------------------------------------------------
# Screens: the formatters and the /handoffsummary grammar.
# ---------------------------------------------------------------------


def _source_book(source: Any) -> HandoffBook:
    if source is None:
        return load_handoff_summaries()
    if isinstance(source, HandoffRegistry):
        return source.book()
    if isinstance(source, HandoffBook):
        return source
    raise ValueError(f"a handoff book is needed, got {source!r}")


def _section_words(label: str, claims: Tuple[str, ...]) -> str:
    if not claims:
        return f"{label}: nothing."
    return f"{label}: {', '.join(claims)}."


def format_handoff(handoff: Any) -> str:
    """One handoff summary as a screen block, provenance whole."""
    current = handoff if isinstance(handoff, HandoffSummary) \
        else build_handoff(handoff)
    lines = [
        f"{current.handoff_id or '-'}: \"{current.title}\" - "
        f"session {current.session_ref} on {current.project}, "
        f"branch {current.branch}, written by "
        f"{current.written_by} on {current.written_on}",
        _section_words("Done", current.done),
        _section_words("Doing", current.doing),
        _section_words("Blocked", current.blocked),
        _section_words("Needs you", current.needs_you),
        f"Evidence: {current.evidence_count} references - "
        f"{', '.join(current.evidence_refs)}. "
        f"(read from {current.source})",
        "This record holds a handoff summary as data - "
        "it sends nothing itself.",
    ]
    return "\n".join(lines)


def format_handoffs(source: Any = None,
                    session_ref: Any = None) -> str:
    """Handoff summaries of one book, in held order.

    With *session_ref* named, only the handoff
    ending that session stands.
    """
    book = _source_book(source)
    wanted = _check_word(
        session_ref, "a session reference") if session_ref is not None else None
    lines = []
    for item in book.handoffs:
        if wanted is not None and item.session_ref != wanted:
            continue
        counts = item.counts()
        lines.append(
            f"{item.handoff_id or '-'}: \"{item.title}\" - "
            f"session {item.session_ref} on branch "
            f"{item.branch}, {item.claim_count} claims "
            f"(done {counts['done']}, doing {counts['doing']}, "
            f"blocked {counts['blocked']}, needs-you "
            f"{counts['needs_you']}), {item.evidence_count} "
            f"evidence references, written by {item.written_by}")
    if not lines:
        lines.append("No handoff summaries are held.")
    return "\n".join(lines)


def format_panel(source: Any = None) -> str:
    """The handoff panel as a screen block."""
    if isinstance(source, HandoffPanel):
        panel = validate_panel(source)
        lines: list = []
    else:
        book = _source_book(source)
        if not book.handoffs:
            return (f"Handoff panel in {book.title}:\n"
                    f"No handoff summaries are held.")
        panel = derive_panel(book)
        lines = [f"Handoff panel in {book.title}:"]
    lines.append("Handoff summaries, in panel order:")
    for row in panel.rows:
        lines.append(
            f"{row.handoff_id}: \"{row.title}\" - "
            f"session {row.session_ref} on branch "
            f"{row.branch}, {row.claim_count} claims "
            f"(done {row.done_count}, doing {row.doing_count}, "
            f"blocked {row.blocked_count}, needs-you "
            f"{row.needs_you_count}), {row.evidence_count} "
            f"evidence references, written by "
            f"{row.written_by} on {row.written_on}")
    lines.extend(panel.account)
    return "\n".join(lines)


def format_verdict(source: Any = None) -> str:
    """The handoff verdict as a screen block, for the whole book."""
    if isinstance(source, EvidenceVerdict):
        verdict = validate_verdict(source)
        lines = [verdict_plain_words(verdict)]
    else:
        book = _source_book(source)
        verdict = derive_verdict(book)
        lines = [f"Handoff verdict in {book.title}:",
                 verdict_plain_words(verdict)]
    lines.append(
        "This verdict is a derivation for reporting - "
        "it changes nothing any live session does.")
    return "\n".join(lines)


def format_handoff_summaries_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /handoffsummary."""
    book = _source_book(source)
    lines = ["Handoff Summaries (M-163) - "
             + PLAIN_EXPLANATION, ""]
    lines.append(format_handoffs(book))
    lines.append("")
    lines.append(format_panel(book))
    lines.append("")
    lines.append(format_verdict(book))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_handoffsummary_args(args: Any) -> Tuple[str, Any]:
    """Parse the /handoffsummary grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    handoff book; ``handoff <handoff-id>`` shows one
    handoff with its provenance whole; ``session
    <session-ref>`` shows the handoff ending one
    session; ``panel`` shows the handoff panel
    derived from the whole book; ``verdict`` shows
    the handoff verdict derived for the whole book.
    Anything else is a usage error naming the
    grammar. Returns ``(action, value-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() in ("show", "list"):
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head in ("panel", "verdict") and len(words) == 1:
        return (head, None)
    if head == "handoff" and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "session" and len(words) == 2:
        try:
            return (head, _check_word(words[1], "a session reference"))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
