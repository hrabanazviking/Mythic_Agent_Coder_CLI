"""Long-session endurance (All-Features roadmap slice M-161).

Part VII continues. The roadmap's words: ``a
500-turn session stays responsive; journal and
retrieval performance budgets set and measured.``

What already ships, and what this slice adds:

* Sessions already ship as data on shipped roads:
  the session store (``core/sessions.py``) keeps
  workspace transcripts with a write-ahead journal
  (``core/journal.py``), session memory across days
  (``core/session_memory.py``, M-153) holds a
  session's situation - its transcript counted,
  never carried - retrieval over the code graph
  (``core/graph_retrieval.py``, M-152) holds every
  retrieval as a bundle, the context budget
  (``core/context_budget.py``, M-147) makes the
  context's size visible, and token thrift
  (``core/token_thrift.py``, M-160) holds measured
  cheaper reads beside them. What none of those
  layers holds is the endurance record itself: the
  declaration, as data, that a long session's
  performance was given a budget first and then
  measured against it.
* This slice is that declaration, as a pure layer:
  an endurance record is one measurement of one
  subject, taken under one endurance kind (session
  length, journal appends, retrieval,
  responsiveness, context size), validated as data
  WITH ITS PROVENANCE WHOLE - what was measured,
  the kind, the reference it stands under, the
  budget set for it against the value measured,
  who recorded it, the day, and where it was read
  from - composed BY IMPORT from the shipped
  holdings it measures (a session-memory situation,
  a context-budget item, a graph-retrieval bundle,
  a token-thrift record), each judged by its own
  layer's validation. The shipped data file
  (``mythic_agent/data/long_session_endurance.yaml``)
  holds one example book in exactly the shape a
  real book file takes, a loader reads a book file
  anywhere on disk, the endurance panel is DERIVED
  from the whole book (every measurement carried
  whole, in a settled order), an endurance VERDICT
  is derived for the whole book, records are
  shaped as session news, and a small in-memory
  registry model holds records one by one. The
  agent layer owns holding a book for a session
  and reading the session's memory onto endurance
  records.

Honesty rules, enforced here and pinned by tests:

* **A budget is set before it is measured.** Every
  record names BOTH figures - the budget set for
  the subject and the value measured against it -
  and the verdict is derived from the two, never
  stored loose: measuring against no named budget
  refuses, because a measurement with no budget
  set first is a number, not an endurance claim.
* **Over budget is reported, never passed.** A
  measurement that exceeds its budget stands in
  the book exactly as measured, with its derived
  verdict ``over-budget``: the panel counts it,
  the book's verdict names the worst of them, and
  nothing in this layer rounds, caps or hides it.
* **Composed, never duplicated.** A record that
  measures a shipped holding's piece is that
  piece read onto this layer by import and judged
  by its own layer's validation, by reference and
  measure alone: its own words never cross.
* **Data only.** This layer holds endurance as
  data: it reads no file itself beyond its own
  book files, runs no live session, appends to no
  live journal, times no live retrieval, calls no
  model and persists nothing. A 500-turn figure
  stands in a book only as a budget or a measured
  value recorded as data - never as a claim that
  a live 500-turn run happened here.
"""

from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .context_budget import ContextItem
from .context_budget import validate_item as _validate_context_item
from .crew_members import normalize_member_id
from .graph_retrieval import RetrievalBundle
from .graph_retrieval import validate_bundle as _validate_bundle
from .session_memory import SessionSituation
from .session_memory import validate_situation as _validate_situation
from .token_thrift import ThriftRecord
from .token_thrift import validate_record as _validate_thrift_record
from .validation import ValidationError

__all__ = [
    "ENDURANCE_KINDS",
    "ENDURANCE_KIND_UNITS",
    "LONG_SESSION_ENDURANCE_RESOURCE",
    "LONG_SESSION_ENDURANCE_SCHEMA",
    "LONG_SESSION_ENDURANCE_SLICE",
    "PLAIN_EXPLANATION",
    "USAGE",
    "EnduranceBook",
    "EnduranceKindCount",
    "EndurancePanel",
    "EndurancePanelRow",
    "EnduranceRecord",
    "EnduranceRegistry",
    "EnduranceVerdict",
    "book_record",
    "build_book",
    "build_panel",
    "build_record",
    "build_row",
    "build_verdict",
    "derive_panel",
    "derive_verdict",
    "endurance_from_context_item",
    "endurance_from_retrieval_bundle",
    "endurance_from_session_situation",
    "endurance_from_thrift_record",
    "endurance_record",
    "endurance_records_from_session_memory",
    "endurance_refs",
    "format_endurance_record",
    "format_endurance_records",
    "format_long_session_endurance_screen",
    "format_panel",
    "format_verdict",
    "inspect_endurance_source",
    "load_long_session_endurance",
    "load_long_session_endurance_file",
    "normalize_endurance_kind",
    "panel_plain_words",
    "panel_record",
    "parse_endurance_args",
    "plain_words",
    "total_over_budget",
    "validate_book",
    "validate_panel",
    "validate_record",
    "validate_row",
    "validate_verdict",
    "verdict_plain_words",
    "verdict_record",
]

LONG_SESSION_ENDURANCE_SLICE = "M-161"

#: The packaged data resource holding the example book.
LONG_SESSION_ENDURANCE_RESOURCE = "long_session_endurance.yaml"

#: The schema word an endurance file must carry.
LONG_SESSION_ENDURANCE_SCHEMA = "mythic.long_session_endurance/1"

#: The endurance kinds, in panel order: how long a
#: session runs (``session-length``, in turns), how
#: fast its journal takes an append
#: (``journal-append``, in milliseconds), how fast
#: retrieval over the code graph answers
#: (``retrieval``, in milliseconds), how fast a
#: turn answers late in a long session
#: (``responsiveness``, in milliseconds), and how
#: much context the session carries
#: (``context-size``, in tokens). No other kind is
#: measured here.
ENDURANCE_KINDS = (
    "session-length", "journal-append", "retrieval",
    "responsiveness", "context-size")

#: The unit each kind's budget and measure are
#: counted in - derived from the kind, never stored.
ENDURANCE_KIND_UNITS = {
    "session-length": "turns",
    "journal-append": "milliseconds",
    "retrieval": "milliseconds",
    "responsiveness": "milliseconds",
    "context-size": "tokens",
}

_KIND_RANK = {kind: rank for rank, kind in enumerate(ENDURANCE_KINDS)}

_KIND_ALIASES = {
    "session-length": "session-length",
    "session": "session-length",
    "length": "session-length",
    "turns": "session-length",
    "journal-append": "journal-append",
    "journal": "journal-append",
    "append": "journal-append",
    "appends": "journal-append",
    "retrieval": "retrieval",
    "retrieve": "retrieval",
    "search": "retrieval",
    "graph": "retrieval",
    "responsiveness": "responsiveness",
    "response": "responsiveness",
    "responsive": "responsiveness",
    "context-size": "context-size",
    "context": "context-size",
    "size": "context-size",
    "tokens": "context-size",
}

_RECORD_KEYS = frozenset({
    "record_id", "id", "subject", "title", "what",
    "kind",
    "ref", "reference",
    "budget", "budget_value",
    "measured", "measured_value",
    "recorded_by", "by", "who",
    "recorded_on", "day", "date",
    "source",
})

_ROW_KEYS = frozenset({
    "record_id", "id", "subject", "kind",
    "ref", "reference",
    "budget", "budget_value",
    "measured", "measured_value",
    "verdict",
    "recorded_by", "recorded_on",
})

_KIND_COUNT_KEYS = frozenset({
    "kind", "records", "count", "over", "over_budget"})

_PANEL_KEYS = frozenset({
    "panel_id", "id", "rows", "records",
    "total_records", "total",
    "total_within", "within",
    "total_over", "over",
    "kind_counts", "kinds",
    "account", "statements",
})

_VERDICT_KEYS = frozenset({
    "total_records", "total",
    "within_budget", "within",
    "over_budget", "over",
    "verdict",
    "worst_record_id", "worst",
    "worst_over_by", "over_by",
})

_BOOK_KEYS = frozenset({"title", "name"})

_ENDURANCE_BOOK_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "canon_note", "guide", "records", "panels",
})

#: The shipped example book's title, held to this
#: by the loader's example check.
_EXAMPLE_TITLE = "Long-session endurance at the M-160 slice boundary"

#: The shipped example's record ids, in held order,
#: pinned by the loader.
_EXAMPLE_RECORD_IDS = (
    "endurance-session-m160", "endurance-journal-m160",
    "endurance-retrieval-m160", "endurance-response-m160",
    "endurance-context-m160")

#: The shipped example's first record and the subject
#: it measures, pinned by the loader.
_EXAMPLE_FIRST_RECORD_ID = "endurance-session-m160"

_EXAMPLE_FIRST_RECORD_SUBJECT = (
    "the M-160 token-thrift session, at 500 turns")

#: The shipped example's one panel id, and its rows
#: in panel order, pinned by the loader.
_EXAMPLE_PANEL_ID = "panel-m160-boundary"

_EXAMPLE_PANEL_ROW_IDS = (
    "endurance-session-m160", "endurance-journal-m160",
    "endurance-retrieval-m160", "endurance-response-m160",
    "endurance-context-m160")

_EXAMPLE_PANEL_ACCOUNT = (
    "The endurance panel holds 5 measurements: "
    "4 within budget, 1 over budget: context-size 1, "
    "journal-append 1, responsiveness 1, retrieval 1, "
    "session-length 1.",
    "Measurements stand by kind - session length "
    "first, then journal appends, then retrieval, "
    "then responsiveness, then context size - then "
    "by subject, then record id, so two panels of "
    "one book diff cleanly, line by line.",
    "Every measurement stands against a budget set "
    "before it was measured: a measurement that "
    "exceeds its budget is reported over budget, "
    "never silently passed.",
    "The panel is read off the book at call time - "
    "it is derived, never stored loose.",
)

PLAIN_EXPLANATION = (
    "Long-session endurance: a 500-turn session "
    "stays responsive - journal and retrieval "
    "performance budgets set and measured. An "
    "endurance record is one measurement of one "
    "subject under one endurance kind, carried with "
    "its provenance whole: what was measured, the "
    "kind, the budget set for it, the value measured "
    "against that budget, who recorded it, the day, "
    "and where it was read from. A budget is set "
    "before it is measured, and a measurement over "
    "its budget is reported over budget, never "
    "silently passed. The endurance panel is "
    "derived from the book at call time: every "
    "measurement standing whole, by kind, then "
    "subject, then record id, and the verdict is "
    "derived for the whole book. This layer sets "
    "and records budgets and measurements as data "
    "only: it runs no live session, appends to no "
    "live journal, times no live retrieval, calls "
    "no model and persists nothing."
)

USAGE = (
    "Usage: /endurance, /endurance show, "
    "/endurance record <record-id>, "
    "/endurance kind <kind>, "
    "/endurance panel, /endurance verdict"
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


def _check_measure(value: Any, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{what} must be a measure, got {value!r}")
    if value < 0 or value > 100_000_000_000:
        raise ValueError(
            f"{what} must be between 0 and 100000000000, "
            f"got {value!r}")
    return value


def _check_word(value: Any, what: str) -> str:
    """One plain id word, judged as a registry id is."""
    try:
        return normalize_member_id(value)
    except ValueError:
        raise ValueError(
            f"{what} must be one plain word, "
            f"got {value!r}") from None


def _check_day(value: Any) -> str:
    text = _clean_text(value, "a record's recorded-on day")
    try:
        parsed = date.fromisoformat(text)
    except ValueError:
        raise ValueError(
            f"a record's recorded-on day must be an ISO "
            f"date (YYYY-MM-DD), got {text!r}") from None
    if parsed.isoformat() != text:
        raise ValueError(
            f"a record's recorded-on day must be an ISO "
            f"date (YYYY-MM-DD), got {text!r}")
    return text


def normalize_endurance_kind(value: Any) -> str:
    """The canonical endurance kind a word names.

    A kind is one of :data:`ENDURANCE_KINDS` - the
    five things a long session's endurance is
    measured by here - read case-insensitively,
    with their plain faces (``session`` / ``turns``,
    ``journal`` / ``append``, ``search`` / ``graph``,
    ``response``, ``context`` / ``tokens``) read
    onto them. Anything else raises, plainly naming
    the five.
    """
    if isinstance(value, str):
        wanted = _KIND_ALIASES.get(value.strip().lower())
        if wanted is not None:
            return wanted
    raise ValueError(
        "an endurance kind must be one of %s, got %r"
        % ("/".join(ENDURANCE_KINDS), value))


# ---------------------------------------------------------------------
# The endurance record: one measurement against its budget, whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class EnduranceRecord:
    """One measurement of one subject against its budget, as data.

    ``subject`` is what was measured, in plain
    words; ``kind`` is the endurance kind measured,
    one of the five; ``ref`` is the reference the
    measured thing stands under; ``budget`` is the
    performance budget set for it before it was
    measured and ``measured`` the value measured
    against that budget, both counted in the kind's
    own unit - the verdict is derived from the two,
    never stored. The provenance stands whole
    beside the record: ``recorded_by`` names who
    recorded it, ``recorded_on`` is the day, and
    ``source`` names where it was read from. A
    record with any provenance word missing is no
    record at all, and a record with no budget set
    is no measurement at all.
    """

    subject: str
    kind: str
    ref: str
    budget: int
    measured: int
    recorded_by: str
    recorded_on: str
    source: str
    record_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.record_id is not None:
            object.__setattr__(
                self, "record_id", normalize_member_id(self.record_id))
        object.__setattr__(
            self, "subject",
            _check_title(self.subject, "a record's subject"))
        object.__setattr__(
            self, "kind", normalize_endurance_kind(self.kind))
        object.__setattr__(
            self, "ref", _check_word(self.ref, "a record's reference"))
        object.__setattr__(
            self, "budget",
            _check_measure(self.budget, "a record's budget"))
        if self.budget < 1:
            raise ValueError(
                "an endurance record must carry the budget "
                "set for it - a budget is set before it is "
                "measured, and measuring against no named "
                "budget is no measurement")
        object.__setattr__(
            self, "measured",
            _check_measure(self.measured, "a record's measured value"))
        object.__setattr__(
            self, "recorded_by",
            _check_title(self.recorded_by, "a record's recorder"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))
        object.__setattr__(
            self, "source",
            _check_title(self.source, "a record's source"))

    @property
    def unit(self) -> str:
        """The unit this record's two figures are counted in."""
        return ENDURANCE_KIND_UNITS[self.kind]

    @property
    def verdict(self) -> str:
        """This record's verdict, derived from its two figures."""
        return "within-budget" if self.measured <= self.budget \
            else "over-budget"

    @property
    def over_by(self) -> int:
        """How far the measure stands over its budget (0 if within)."""
        return max(0, self.measured - self.budget)

    @property
    def headroom(self) -> int:
        """How far the measure stands under its budget (0 if over)."""
        return max(0, self.budget - self.measured)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "long_session_endurance_record",
            "slice": LONG_SESSION_ENDURANCE_SLICE,
            "record_id": self.record_id,
            "subject": self.subject,
            "kind": self.kind,
            "ref": self.ref,
            "budget": self.budget,
            "measured": self.measured,
            "unit": self.unit,
            "verdict": self.verdict,
            "over_by": self.over_by,
            "recorded_by": self.recorded_by,
            "recorded_on": self.recorded_on,
            "source": self.source,
        }


def _check_record_ref(value: Any) -> EnduranceRecord:
    if isinstance(value, EnduranceRecord):
        return value
    if isinstance(value, dict):
        return validate_record(value)
    raise ValueError(f"an endurance record is needed, got {value!r}")


def validate_record(record: Any) -> EnduranceRecord:
    """Validate one endurance record into an EnduranceRecord.

    Accepts a record or a mapping naming a ``subject``
    (or ``title`` / ``what``), a ``kind``, a ``ref``
    (or ``reference``), a ``budget`` (or
    ``budget_value``), a ``measured`` (or
    ``measured_value``), a ``recorded_by`` (or ``by``
    / ``who``), a ``recorded_on`` (or ``day`` /
    ``date``), a ``source`` and an optional
    ``record_id`` (or ``id``). Naming two spellings
    of one field with different values refuses, and
    unknown keys refuse - a stored verdict among
    them, because a verdict is derived, never stored.
    """
    if isinstance(record, EnduranceRecord):
        return record
    if not isinstance(record, dict):
        raise ValueError(
            f"an endurance record must be a mapping, got {record!r}")
    unknown = set(record) - _RECORD_KEYS
    if unknown:
        raise ValueError(
            "unknown endurance-record keys: %s"
            % ", ".join(sorted(unknown)))

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(record, spellings, what)
        if value is None:
            raise ValueError(f"an endurance record is missing its {what}")
        return value

    kwargs: Dict[str, Any] = {
        "subject": _needed(("subject", "title", "what"), "subject"),
        "kind": _needed(("kind",), "kind"),
        "ref": _needed(("ref", "reference"), "reference"),
        "budget": _needed(("budget", "budget_value"), "budget"),
        "measured": _needed(("measured", "measured_value"), "measure"),
        "recorded_by": _needed(("recorded_by", "by", "who"), "recorder"),
        "recorded_on": _needed(
            ("recorded_on", "day", "date"), "recorded-on day"),
        "source": _needed(("source",), "source"),
    }
    named_id = _pick_any(record, ("record_id", "id"), "record ids")
    if named_id is not None:
        kwargs["record_id"] = named_id
    return EnduranceRecord(**kwargs)


def build_record(record: Any = None, **kwargs: Any) -> EnduranceRecord:
    """Build one validated endurance record, from a mapping or words."""
    if isinstance(record, EnduranceRecord) and not kwargs:
        return record
    if isinstance(record, dict) or record is None:
        merged: Dict[str, Any] = {}
        if isinstance(record, dict):
            merged.update(record)
        merged.update(kwargs)
        return validate_record(merged)
    raise ValueError(
        f"an endurance record must be a mapping, got {record!r}")


def _endurance_for(kind: str, ref: Optional[str], *, subject: Any,
                   budget: Any, measured: Any, recorded_by: Any,
                   recorded_on: Any, source: Any) -> EnduranceRecord:
    """One endurance record for one shipped piece, by kind and ref.

    The piece's own words are never read here: only
    its kind and the reference it stands under, and
    the figures named beside it. A record measured
    against no named budget refuses - a budget is
    set before it is measured - as does a record
    with no measured value or no recorder. A piece
    with no reference refuses: a record must name
    which standing thing it measured.
    """
    if budget is None:
        raise ValueError(
            "an endurance record must carry the budget "
            "set for it: a budget is set before it is "
            "measured - measuring against no named "
            "budget is no measurement")
    if measured is None:
        raise ValueError(
            "an endurance record must carry its measured "
            "value: what was measured against the budget")
    if recorded_by is None:
        raise ValueError(
            "an endurance record must name who recorded "
            "it - a measurement recorded by no one is "
            "no record")
    if ref is None or (isinstance(ref, str) and not ref.strip()):
        raise ValueError(
            "an endurance record names the reference the "
            "measured thing stood under - a thing with "
            "no reference cannot be measured, by kind "
            "alone or otherwise")
    return EnduranceRecord(
        subject=subject, kind=kind, ref=ref, budget=budget,
        measured=measured, recorded_by=recorded_by,
        recorded_on=recorded_on, source=source)


def inspect_endurance_source(piece: Any) -> Dict[str, Any]:
    """Inspect one shipped piece: its reference and measure only.

    The piece is judged by the layer that owns its
    type, never by whichever validator happens to
    accept its shape first - exactly as the sibling
    layers' inspection roads judge. Pieces whose own
    layer carries a count (a session-memory
    situation's transcript count, a context-budget
    item's tokens, a token-thrift record's actual
    tokens) report it as the measure; a piece
    carrying none (a graph-retrieval bundle, which
    holds no latency of its own) reports ``None`` -
    its measure is named beside the reference at
    the composition seam. A piece with no reference,
    or a value no shipped layer owns, refuses.
    """
    if isinstance(piece, EnduranceRecord):
        return {"ref": piece.ref, "measured": piece.measured}
    owned = (
        (SessionSituation, _validate_situation, "session_ref", "count"),
        (ContextItem, _validate_context_item, "item_id", "tokens"),
        (ThriftRecord, _validate_thrift_record, "ref", "tokens"),
        (RetrievalBundle, _validate_bundle, "bundle_id", None),
    )
    for kind_type, validator, attr, counted in owned:
        if isinstance(piece, kind_type):
            validated = validator(piece)
            ref = getattr(validated, attr, None)
            if ref is None or (
                    isinstance(ref, str) and not ref.strip()):
                raise ValueError(
                    "an inspected piece names the reference "
                    "it stands under - this piece carries none")
            measured = None
            if counted == "count":
                measured = validated.transcript_messages
            elif counted == "tokens":
                measured = validated.tokens if isinstance(
                    validated, ContextItem) else validated.actual_tokens
            return {"ref": ref, "measured": measured}
    if isinstance(piece, dict):
        if "budget" in piece or "budget_value" in piece:
            checked = validate_record(piece)
            return {"ref": checked.ref, "measured": checked.measured}
        for kind_type, validator, attr, counted in owned:
            try:
                validated = validator(piece)
            except Exception:
                continue
            ref = getattr(validated, attr, None)
            if ref is None or (
                    isinstance(ref, str) and not ref.strip()):
                continue
            measured = None
            if counted == "count":
                measured = validated.transcript_messages
            elif counted == "tokens":
                measured = validated.tokens if isinstance(
                    validated, ContextItem) else validated.actual_tokens
            return {"ref": ref, "measured": measured}
    raise ValueError(
        f"no shipped layer owns this piece, got {piece!r}")


def endurance_from_session_situation(
        situation: Any, *, budget: Any, recorded_by: Any,
        recorded_on: Any, source: Any = "session memory",
        subject: Any = None) -> EnduranceRecord:
    """Build one endurance record from a session-memory situation.

    The situation - session memory's own record
    (M-153), judged by that layer's own validation -
    is read onto an endurance record BY IMPORT by
    its reference and measure alone: its session
    reference stands as the record's reference and
    its transcript message count is the measured
    value - how long the session ran, in turns -
    under the session-length kind. The budget - the
    session length the session was set to stay
    responsive through - is named beside it. The
    situation's title, workspace and carried memory
    are never read here.
    """
    validated = _validate_situation(situation)
    return _endurance_for(
        "session-length", validated.session_ref,
        subject=subject if subject is not None else (
            f"session {validated.session_ref}"),
        budget=budget, measured=validated.transcript_messages,
        recorded_by=recorded_by, recorded_on=recorded_on,
        source=source)


def endurance_from_context_item(
        item: Any, *, budget: Any, recorded_by: Any,
        recorded_on: Any, source: Any = "context budget",
        subject: Any = None) -> EnduranceRecord:
    """Build one endurance record from a shipped context-budget item.

    The item - the context budget's own record
    (M-147), judged by that layer's own validation -
    is read onto an endurance record BY IMPORT by
    its reference and measure alone: its id stands
    as the record's reference and its token count is
    the measured value, under the context-size kind.
    The budget is named beside it. Its title, source
    and reason in the budget are never read here.
    """
    validated = _validate_context_item(item)
    return _endurance_for(
        "context-size", validated.item_id,
        subject=subject if subject is not None else (
            f"context item {validated.item_id}"),
        budget=budget, measured=validated.tokens,
        recorded_by=recorded_by, recorded_on=recorded_on,
        source=source)


def endurance_from_retrieval_bundle(
        bundle: Any, *, budget: Any, measured: Any,
        recorded_by: Any, recorded_on: Any,
        source: Any = "graph retrieval",
        subject: Any = None) -> EnduranceRecord:
    """Build one endurance record from a graph-retrieval bundle.

    The bundle - graph retrieval's own record
    (M-152), judged by that layer's own validation -
    is read onto an endurance record BY IMPORT by
    its reference alone: its bundle id stands as
    the record's reference, under the retrieval
    kind. A bundle carries no latency of its own,
    so the measured latency and the budget are both
    named beside it. Its query, seeds and pieces
    are never read here.
    """
    validated = _validate_bundle(bundle)
    return _endurance_for(
        "retrieval", validated.bundle_id,
        subject=subject if subject is not None else (
            f"retrieval bundle {validated.bundle_id}"),
        budget=budget, measured=measured,
        recorded_by=recorded_by, recorded_on=recorded_on,
        source=source)


def endurance_from_thrift_record(
        record: Any, *, budget: Any, recorded_by: Any,
        recorded_on: Any, kind: Any = "context-size",
        source: Any = "token thrift",
        subject: Any = None) -> EnduranceRecord:
    """Build one endurance record from a shipped token-thrift record.

    The record - token thrift's own record (M-160),
    judged by that layer's own validation - is read
    onto an endurance record BY IMPORT by its
    reference and measure alone: the reference it
    stands under stands as this record's reference
    and its actual tokens are the measured value.
    Context size is its natural kind. The budget is
    named beside it. Its subject, road and saving
    are never read here.
    """
    validated = _validate_thrift_record(record)
    return _endurance_for(
        normalize_endurance_kind(kind), validated.ref,
        subject=subject if subject is not None else (
            f"thrift record {validated.ref}"),
        budget=budget, measured=validated.actual_tokens,
        recorded_by=recorded_by, recorded_on=recorded_on,
        source=source)


def _situations(source: Any) -> Tuple[SessionSituation, ...]:
    """The situations one source holds, judged by session memory."""
    from .session_memory import SessionMemoryBook, SessionMemoryRegistry
    if isinstance(source, SessionMemoryBook):
        return source.situations
    if isinstance(source, SessionMemoryRegistry):
        return source.list_situations()
    if isinstance(source, (list, tuple)):
        return tuple(_validate_situation(item) for item in source)
    if isinstance(source, (SessionSituation, dict)):
        return (_validate_situation(source),)
    raise ValueError(f"session situations are needed, got {source!r}")


def endurance_records_from_session_memory(
        source: Any, *, budget: Any, recorded_by: Any,
        recorded_on: Any) -> Tuple[EnduranceRecord, ...]:
    """Endurance records read off the shipped session memory.

    The situations of a session-memory book - or of
    a whole session-memory registry - are read onto
    endurance records BY IMPORT, judged by session
    memory's own validation on the way, under the
    session-length kind and one named recorder.
    Every situation is measured against the one
    named *budget*: no budget named refuses the
    whole road before anything is built, because a
    budget is set before it is measured. Every
    situation's title, workspace and carried memory
    stay in session memory: only references and
    counts cross.
    """
    if budget is None:
        raise ValueError(
            "a budget must be named for the session-length "
            "kind - a budget is set before it is measured")
    situations = _situations(source)
    return tuple(
        endurance_from_session_situation(
            situation, budget=budget, recorded_by=recorded_by,
            recorded_on=recorded_on)
        for situation in situations)


# ---------------------------------------------------------------------
# The endurance panel: every measurement carried whole, derived.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class EndurancePanelRow:
    """One endurance record carried whole into the panel.

    ``record_id`` names the record; ``subject`` is
    what was measured; ``kind`` is the endurance
    kind; ``ref`` is the reference it stands under;
    ``budget`` / ``measured`` are its two figures
    and ``verdict`` the verdict derived from them;
    ``recorded_by`` and ``recorded_on`` are the
    record's provenance head. :func:`validate_row`
    judged against its record refuses a row whose
    fields disagree with the row they derive, and a
    row whose verdict is not its figures' verdict
    refuses at construction.
    """

    record_id: str
    subject: str
    kind: str
    ref: str
    budget: int
    measured: int
    verdict: str
    recorded_by: str
    recorded_on: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "record_id", normalize_member_id(self.record_id))
        object.__setattr__(
            self, "subject",
            _check_title(self.subject, "a row's subject"))
        object.__setattr__(
            self, "kind", normalize_endurance_kind(self.kind))
        object.__setattr__(
            self, "ref", _check_word(self.ref, "a row's reference"))
        object.__setattr__(
            self, "budget",
            _check_measure(self.budget, "a row's budget"))
        object.__setattr__(
            self, "measured",
            _check_measure(self.measured, "a row's measured value"))
        verdict = _clean_text(self.verdict, "a row's verdict")
        expected = "within-budget" if self.measured <= self.budget \
            else "over-budget"
        if verdict != expected:
            raise ValueError(
                "a row's verdict must be its own figures' "
                "verdict - a verdict is derived, never "
                "stored loose")
        object.__setattr__(self, "verdict", verdict)
        object.__setattr__(
            self, "recorded_by",
            _check_title(self.recorded_by, "a row's recorder"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))

    @property
    def over_by(self) -> int:
        """How far this row's measure stands over its budget."""
        return max(0, self.measured - self.budget)

    @property
    def sort_key(self) -> Tuple[int, str, str]:
        """This row's place in panel order (derived).

        Rows stand by kind - session length first,
        then journal appends, then retrieval, then
        responsiveness, then context size - then by
        subject, then record id.
        """
        return (_KIND_RANK[self.kind], self.subject.lower(), self.record_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "long_session_endurance_panel_row",
            "slice": LONG_SESSION_ENDURANCE_SLICE,
            "record_id": self.record_id,
            "subject": self.subject,
            "kind": self.kind,
            "ref": self.ref,
            "budget": self.budget,
            "measured": self.measured,
            "verdict": self.verdict,
            "recorded_by": self.recorded_by,
            "recorded_on": self.recorded_on,
        }


def _row_for_record(record: EnduranceRecord) -> EndurancePanelRow:
    return EndurancePanelRow(
        record_id=record.record_id, subject=record.subject,
        kind=record.kind, ref=record.ref, budget=record.budget,
        measured=record.measured, verdict=record.verdict,
        recorded_by=record.recorded_by,
        recorded_on=record.recorded_on)


def _check_row_ref(value: Any) -> EndurancePanelRow:
    if isinstance(value, EndurancePanelRow):
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

        return EndurancePanelRow(
            record_id=_needed(("record_id", "id"), "record id"),
            subject=_needed(("subject",), "subject"),
            kind=_needed(("kind",), "kind"),
            ref=_needed(("ref", "reference"), "reference"),
            budget=_needed(("budget", "budget_value"), "budget"),
            measured=_needed(("measured", "measured_value"), "measure"),
            verdict=_needed(("verdict",), "verdict"),
            recorded_by=_needed(("recorded_by",), "recorder"),
            recorded_on=_needed(("recorded_on",), "recorded-on day"))
    raise ValueError(f"a panel row is needed, got {value!r}")


def validate_row(row: Any, record: Any = None) -> EndurancePanelRow:
    """Validate one panel row into an EndurancePanelRow.

    Accepts a row or a mapping naming a ``record_id``
    (or ``id``), a ``subject``, a ``kind``, a ``ref``
    (or ``reference``), a ``budget``, a ``measured``,
    a ``verdict``, a ``recorded_by`` and a
    ``recorded_on``. With *record* given, the row is
    judged against the row derived from that record:
    a stored row whose fields disagree with the
    derived row refuses.
    """
    current = _check_row_ref(row)
    if record is not None:
        checked = _check_record_ref(record)
        derived = _row_for_record(checked)
        if current != derived:
            raise ValueError(
                "a stored row disagrees with the row "
                "derived from its record")
    return current


def build_row(row: Any = None, record: Any = None,
              **kwargs: Any) -> EndurancePanelRow:
    """Build one validated row, from a mapping or field words."""
    if isinstance(row, EndurancePanelRow) and not kwargs:
        return validate_row(row, record)
    if isinstance(row, dict) or row is None:
        merged: Dict[str, Any] = {}
        if isinstance(row, dict):
            merged.update(row)
        merged.update(kwargs)
        return validate_row(merged, record)
    return validate_row(row, record)


@dataclass(frozen=True)
class EnduranceKindCount:
    """One kind's count in a panel: its records and overs tallied."""

    kind: str
    records: int
    over: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "kind", normalize_endurance_kind(self.kind))
        object.__setattr__(
            self, "records",
            _check_count(self.records, "a kind count's records"))
        object.__setattr__(
            self, "over",
            _check_count(self.over, "a kind count's over count"))
        if self.over > self.records:
            raise ValueError(
                "a kind count's over count must not exceed "
                "its own records")

    def to_record(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "records": self.records,
            "over": self.over,
        }


def _check_kind_count_ref(value: Any) -> EnduranceKindCount:
    if isinstance(value, EnduranceKindCount):
        return value
    if isinstance(value, dict):
        unknown = set(value) - _KIND_COUNT_KEYS
        if unknown:
            raise ValueError(
                "unknown kind-count keys: %s"
                % ", ".join(sorted(unknown)))
        kind = _pick_any(value, ("kind",), "kinds")
        if kind is None:
            raise ValueError("a kind count is missing its kind")
        records = _pick_any(value, ("records", "count"), "records")
        if records is None:
            raise ValueError("a kind count is missing its records")
        over = _pick_any(value, ("over", "over_budget"), "overs")
        if over is None:
            raise ValueError("a kind count is missing its over count")
        return EnduranceKindCount(kind=kind, records=records, over=over)
    raise ValueError(f"a kind count is needed, got {value!r}")


def _panel_account(total_records: int, total_within: int,
                   total_over: int,
                   kind_counts: Tuple[EnduranceKindCount, ...]
                   ) -> Tuple[str, ...]:
    tallies = ", ".join(
        f"{count.kind} {count.records}"
        for count in sorted(
            kind_counts, key=lambda count: count.kind))
    return (
        f"The endurance panel holds {total_records} measurements: "
        f"{total_within} within budget, {total_over} over "
        f"budget: {tallies}.",
        "Measurements stand by kind - session length "
        "first, then journal appends, then retrieval, "
        "then responsiveness, then context size - then "
        "by subject, then record id, so two panels of "
        "one book diff cleanly, line by line.",
        "Every measurement stands against a budget set "
        "before it was measured: a measurement that "
        "exceeds its budget is reported over budget, "
        "never silently passed.",
        "The panel is read off the book at call time - "
        "it is derived, never stored loose.",
    )


@dataclass(frozen=True)
class EndurancePanel:
    """The endurance panel of one book, derived from the whole book.

    ``rows`` are the book's records carried whole, in
    panel order (by kind, then subject, then record
    id, so two panels of one book diff cleanly);
    ``total_records`` is the rows' own count,
    ``total_within`` / ``total_over`` are the rows'
    own verdict tallies; ``kind_counts`` are the
    per-kind tallies of every record in the book, in
    the order their kinds first appear in the panel;
    ``account`` is read off those numbers. A panel
    whose rows stand out of panel order, or whose
    tallies are not its own rows' tallies, refuses
    at construction; :func:`validate_panel` judged
    against a book refuses a stored panel that
    disagrees with the derived one.
    """

    rows: Tuple[EndurancePanelRow, ...] = ()
    total_records: int = 0
    total_within: int = 0
    total_over: int = 0
    kind_counts: Tuple[EnduranceKindCount, ...] = ()
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
            if row.record_id in seen:
                raise ValueError(
                    f"a panel row for record {row.record_id!r} "
                    f"already exists")
            seen.add(row.record_id)
        keys = [row.sort_key for row in rows]
        if keys != sorted(keys):
            raise ValueError(
                "a panel's rows must stand in panel order "
                "(by kind, then subject, then record id)")
        object.__setattr__(self, "rows", rows)
        object.__setattr__(
            self, "total_records",
            _check_count(self.total_records, "a panel's total records"))
        if self.total_records != len(rows):
            raise ValueError(
                "a panel's total records must be its own "
                "rows' count")
        for field, what in (
                ("total_within", "total within budget"),
                ("total_over", "total over budget")):
            object.__setattr__(
                self, field,
                _check_count(getattr(self, field), f"a panel's {what}"))
        within = sum(1 for r in rows if r.verdict == "within-budget")
        over = sum(1 for r in rows if r.verdict == "over-budget")
        if self.total_within != within:
            raise ValueError(
                "a panel's total within must be its own "
                "rows' tally")
        if self.total_over != over:
            raise ValueError(
                "a panel's total over must be its own "
                "rows' tally")
        if isinstance(self.kind_counts, (str, bytes)) \
                or not isinstance(self.kind_counts, (list, tuple)):
            raise ValueError(
                f"a panel's kind counts must be a list, "
                f"got {self.kind_counts!r}")
        kind_counts = tuple(
            _check_kind_count_ref(c) for c in self.kind_counts)
        seen_kinds = set()
        for count in kind_counts:
            if count.kind in seen_kinds:
                raise ValueError(
                    f"a kind count named {count.kind!r} "
                    f"already exists")
            seen_kinds.add(count.kind)
        object.__setattr__(self, "kind_counts", kind_counts)
        if sum(c.records for c in kind_counts) != self.total_records:
            raise ValueError(
                "a panel's kind counts must sum to its own "
                "total records")
        if sum(c.over for c in kind_counts) != self.total_over:
            raise ValueError(
                "a panel's kind counts must sum to its own "
                "total over budget")
        tallies: Dict[str, Tuple[int, int]] = {}
        for row in rows:
            n, o = tallies.get(row.kind, (0, 0))
            tallies[row.kind] = (
                n + 1, o + (1 if row.verdict == "over-budget" else 0))
        for count in kind_counts:
            if (count.records, count.over) != tallies.get(
                    count.kind, (0, 0)):
                raise ValueError(
                    "a panel's kind counts must be its own "
                    "rows' counts")
        if set(tallies) != {c.kind for c in kind_counts}:
            raise ValueError(
                "a panel's kind counts must name every kind "
                "its rows carry")
        object.__setattr__(self, "account", _check_account(self.account))

    def row_for(self, record_id: Any) -> EndurancePanelRow:
        """The panel row one record names in this panel."""
        wanted = normalize_member_id(record_id)
        for row in self.rows:
            if row.record_id == wanted:
                return row
        raise KeyError(f"no row in the panel: record {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "long_session_endurance_panel",
            "slice": LONG_SESSION_ENDURANCE_SLICE,
            "panel_id": self.panel_id,
            "rows": [row.to_record() for row in self.rows],
            "total_records": self.total_records,
            "total_within": self.total_within,
            "total_over": self.total_over,
            "kind_counts": [c.to_record() for c in self.kind_counts],
            "account": list(self.account),
        }


def _held_records(source: Any) -> Tuple[EnduranceRecord, ...]:
    """The endurance records one source holds, in held order."""
    if isinstance(source, EnduranceBook):
        return source.records
    if isinstance(source, EnduranceRegistry):
        return source.list_records()
    if isinstance(source, (list, tuple)):
        return tuple(_check_record_ref(item) for item in source)
    raise ValueError(f"endurance records are needed, got {source!r}")


def derive_panel(source: Any) -> EndurancePanel:
    """Derive the endurance panel from one book.

    The rows are the book's records carried whole, in
    panel order: by kind, then subject, then record
    id. *source* is a book or a registry. A source
    holding no record refuses - a panel of nothing is
    no panel.
    """
    records = _held_records(source)
    if not records:
        raise ValueError("a panel needs at least one endurance record")
    rows = []
    for record in records:
        if record.record_id is None:
            raise ValueError(
                "a panel row must name its record - a "
                "record with no id refuses derivation")
        rows.append(_row_for_record(record))
    rows = tuple(sorted(rows, key=lambda r: r.sort_key))
    order: list = []
    tally: Dict[str, Tuple[int, int]] = {}
    for row in rows:
        if row.kind not in tally:
            tally[row.kind] = (0, 0)
            order.append(row.kind)
        n, o = tally[row.kind]
        tally[row.kind] = (
            n + 1, o + (1 if row.verdict == "over-budget" else 0))
    kind_counts = tuple(
        EnduranceKindCount(
            kind=kind, records=tally[kind][0], over=tally[kind][1])
        for kind in order)
    total_within = sum(1 for r in rows if r.verdict == "within-budget")
    total_over = sum(1 for r in rows if r.verdict == "over-budget")
    return EndurancePanel(
        rows=rows, total_records=len(rows),
        total_within=total_within, total_over=total_over,
        kind_counts=kind_counts,
        account=_panel_account(
            len(rows), total_within, total_over, kind_counts))


def validate_panel(panel: Any, source: Any = None
                   ) -> EndurancePanel:
    """Validate one panel into an EndurancePanel.

    Accepts a panel or a mapping naming ``rows`` (or
    ``records``), a ``total_records`` (or ``total``),
    ``total_within``, ``total_over``, ``kind_counts``
    (or ``kinds``), an ``account`` (or ``statements``)
    and an optional ``panel_id`` (or ``id``). With
    *source* given (a book), the panel is judged
    against the panel derived from that book: a
    stored panel whose rows, tallies, kind counts or
    account disagree with the derived panel refuses.
    A panel naming no account refuses too.
    """
    if isinstance(panel, EndurancePanel):
        current = panel
    elif isinstance(panel, dict):
        unknown = set(panel) - _PANEL_KEYS
        if unknown:
            raise ValueError(
                "unknown panel keys: %s" % ", ".join(sorted(unknown)))
        rows = _pick_any(panel, ("rows", "records"), "rows")
        if rows is None:
            raise ValueError("a panel is missing its rows")
        total = _pick_any(panel, ("total_records", "total"), "totals")
        if total is None:
            raise ValueError("a panel is missing its total records")
        within = _pick_any(panel, ("total_within", "within"), "withins")
        if within is None:
            raise ValueError("a panel is missing its total within")
        over = _pick_any(panel, ("total_over", "over"), "overs")
        if over is None:
            raise ValueError("a panel is missing its total over")
        kind_counts = _pick_any(
            panel, ("kind_counts", "kinds"), "kind counts")
        if kind_counts is None:
            raise ValueError("a panel is missing its kind counts")
        account = _pick_any(panel, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError("a panel names no account of its own")
        kwargs: Dict[str, Any] = {
            "rows": rows, "total_records": total,
            "total_within": within, "total_over": over,
            "kind_counts": kind_counts, "account": account}
        panel_id = _pick_any(panel, ("panel_id", "id"), "panel ids")
        if panel_id is not None:
            kwargs["panel_id"] = panel_id
        current = EndurancePanel(**kwargs)
    else:
        raise ValueError(f"a panel must be a mapping, got {panel!r}")
    if source is not None:
        derived = derive_panel(source)
        if (current.rows != derived.rows
                or current.total_records != derived.total_records
                or current.total_within != derived.total_within
                or current.total_over != derived.total_over
                or current.kind_counts != derived.kind_counts
                or current.account != derived.account):
            raise ValueError(
                "a stored panel disagrees with the panel "
                "derived from its book")
    return current


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> EndurancePanel:
    """Build one validated panel, from a mapping or field words."""
    if isinstance(panel, EndurancePanel) and not kwargs:
        return validate_panel(panel, source)
    if isinstance(panel, dict) or panel is None:
        merged: Dict[str, Any] = {}
        if isinstance(panel, dict):
            merged.update(panel)
        merged.update(kwargs)
        return validate_panel(merged, source)
    return validate_panel(panel, source)


# ---------------------------------------------------------------------
# The verdict: the whole book judged, derived - over is named.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class EnduranceVerdict:
    """One endurance verdict: a whole book judged, as data.

    ``total_records`` counts the book's measurements
    and ``within_budget`` / ``over_budget`` tally
    their verdicts; ``verdict`` is the book's word -
    ``enduring`` when nothing stands over budget,
    ``strained`` when anything does;
    ``worst_record_id`` names the measurement
    furthest over its budget (the first such in
    panel order) and ``worst_over_by`` how far over
    it stands, both empty when nothing is over.
    :func:`validate_verdict` judged against a book
    refuses a stored verdict that disagrees with
    the verdict derived from that book.
    """

    total_records: int
    within_budget: int
    over_budget: int
    verdict: str
    worst_record_id: Optional[str] = None
    worst_over_by: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "total_records",
            _check_count(self.total_records, "a verdict's total records"))
        object.__setattr__(
            self, "within_budget",
            _check_count(self.within_budget, "a verdict's within count"))
        object.__setattr__(
            self, "over_budget",
            _check_count(self.over_budget, "a verdict's over count"))
        if self.within_budget + self.over_budget != self.total_records:
            raise ValueError(
                "a verdict's tallies must sum to its own "
                "total records")
        verdict = _clean_text(self.verdict, "a verdict's word")
        expected = "enduring" if self.over_budget == 0 else "strained"
        if verdict != expected:
            raise ValueError(
                "a verdict's word must be its own tallies' "
                "word - a verdict is derived, never stored "
                "loose")
        object.__setattr__(self, "verdict", verdict)
        if self.worst_record_id is not None:
            object.__setattr__(
                self, "worst_record_id",
                normalize_member_id(self.worst_record_id))
        object.__setattr__(
            self, "worst_over_by",
            _check_count(self.worst_over_by, "a verdict's worst over"))
        if self.over_budget == 0:
            if self.worst_record_id is not None \
                    or self.worst_over_by != 0:
                raise ValueError(
                    "a verdict with nothing over budget names "
                    "no worst record")
        else:
            if self.worst_record_id is None or self.worst_over_by < 1:
                raise ValueError(
                    "a verdict with a measurement over budget "
                    "names its worst record and how far over "
                    "it stands - over budget is reported, "
                    "never passed over")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "long_session_endurance_verdict",
            "slice": LONG_SESSION_ENDURANCE_SLICE,
            "total_records": self.total_records,
            "within_budget": self.within_budget,
            "over_budget": self.over_budget,
            "verdict": self.verdict,
            "worst_record_id": self.worst_record_id,
            "worst_over_by": self.worst_over_by,
        }


def derive_verdict(source: Any) -> EnduranceVerdict:
    """Derive the endurance verdict of one book.

    The verdict's tallies are the derived panel's
    own, its word is read off them, and its worst
    record is the panel row furthest over its
    budget - the first such row in panel order, so
    the naming is settled. *source* is a book or a
    registry.
    """
    panel = derive_panel(source)
    worst_id = None
    worst_over = 0
    for row in panel.rows:
        if row.over_by > worst_over:
            worst_over = row.over_by
            worst_id = row.record_id
    return EnduranceVerdict(
        total_records=panel.total_records,
        within_budget=panel.total_within,
        over_budget=panel.total_over,
        verdict="enduring" if panel.total_over == 0 else "strained",
        worst_record_id=worst_id, worst_over_by=worst_over)


def _check_verdict_ref(value: Any) -> EnduranceVerdict:
    if isinstance(value, EnduranceVerdict):
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

        worst = _pick_any(
            value, ("worst_record_id", "worst"), "worst records")
        over_by = _pick_any(
            value, ("worst_over_by", "over_by"), "worst overs")
        return EnduranceVerdict(
            total_records=_needed(
                ("total_records", "total"), "total records"),
            within_budget=_needed(
                ("within_budget", "within"), "within count"),
            over_budget=_needed(("over_budget", "over"), "over count"),
            verdict=_needed(("verdict",), "verdict word"),
            worst_record_id=worst,
            worst_over_by=over_by if over_by is not None else 0)
    raise ValueError(f"an endurance verdict is needed, got {value!r}")


def validate_verdict(verdict: Any, source: Any = None) -> EnduranceVerdict:
    """Validate one verdict into an EnduranceVerdict.

    Accepts a verdict or a mapping naming its three
    tallies, its verdict word, its worst record and
    how far over it stands. With *source* given (a
    book), the verdict is judged against the verdict
    derived from that book: a stored verdict whose
    tallies, word or worst record disagree with the
    derived verdict refuses.
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
                  **kwargs: Any) -> EnduranceVerdict:
    """Build one validated verdict, from a mapping or field words."""
    if isinstance(verdict, EnduranceVerdict) and not kwargs:
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict) or verdict is None:
        merged: Dict[str, Any] = {}
        if isinstance(verdict, dict):
            merged.update(verdict)
        merged.update(kwargs)
        return validate_verdict(merged, source)
    return validate_verdict(verdict, source)


# ---------------------------------------------------------------------
# The book: endurance records in held order, panels judged.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class EnduranceBook:
    """One long-session endurance book: its records, in held order.

    ``records`` are the endurance records, in held
    order, each with its provenance whole; no two
    records of one book measure the same standing
    thing under the same kind - one thing is
    measured once per kind in a book. ``panels`` are
    the book's derivations - endurance panels of the
    whole book, each judged against the book by
    :func:`validate_book`; ``canon_note`` is the
    book's own note. The total is the records' own
    count, judged at construction. This book is the
    book file's shape: the shipped example is one
    book, and a real book file is a new file in this
    shape.
    """

    title: str = ""
    records: Tuple[EnduranceRecord, ...] = ()
    panels: Tuple[EndurancePanel, ...] = ()
    canon_note: str = ""
    total_records: Optional[int] = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book's title"))
        if isinstance(self.records, (str, bytes)) \
                or not isinstance(self.records, (list, tuple)):
            raise ValueError(
                f"a book's records must be a list of "
                f"records, got {self.records!r}")
        records = tuple(_check_record_ref(item) for item in self.records)
        if not records:
            raise ValueError("an endurance book holds at least one record")
        seen_ids = set()
        seen_refs = set()
        for record in records:
            if record.record_id is not None:
                if record.record_id in seen_ids:
                    raise ValueError(
                        f"an endurance record named "
                        f"{record.record_id!r} already exists")
                seen_ids.add(record.record_id)
            key = (record.kind, record.ref)
            if key in seen_refs:
                raise ValueError(
                    f"the {record.kind} measurement of "
                    f"{record.ref!r} is already taken in "
                    f"this book - one thing is measured "
                    f"once per kind in a book")
            seen_refs.add(key)
        object.__setattr__(self, "records", records)
        if isinstance(self.panels, (str, bytes)) \
                or not isinstance(self.panels, (list, tuple)):
            raise ValueError(
                f"a book's panels must be a list of panels, "
                f"got {self.panels!r}")
        panels = tuple(
            p if isinstance(p, EndurancePanel)
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
        given = self.total_records
        if given is None:
            object.__setattr__(self, "total_records", len(records))
        else:
            checked = _check_count(given, "a book's total records")
            if checked != len(records):
                raise ValueError(
                    "a book's total records must be its own "
                    "records' count")
            object.__setattr__(self, "total_records", checked)

    def record_for(self, record_id: Any) -> EnduranceRecord:
        """The endurance record one id names in this book."""
        wanted = normalize_member_id(record_id)
        for record in self.records:
            if record.record_id == wanted:
                return record
        raise KeyError(f"no endurance record in the book: {wanted!r}")

    def record_for_ref(self, kind: Any, ref: Any) -> EnduranceRecord:
        """The record measuring one standing thing under one kind.

        The kind is read through the kind aliases and
        the reference matched as it stands. A thing no
        record of the book measures under that kind
        raises KeyError - endurance is recorded, never
        guessed.
        """
        wanted_kind = normalize_endurance_kind(kind)
        wanted_ref = _check_word(ref, "a record's reference")
        for record in self.records:
            if record.kind == wanted_kind and record.ref == wanted_ref:
                return record
        raise KeyError(
            f"no record in the book measures the {wanted_kind} "
            f"standing as {wanted_ref!r}")

    def panel_for(self, panel_id: Any) -> EndurancePanel:
        """The stored panel one id names in this book."""
        wanted = normalize_member_id(panel_id)
        for panel in self.panels:
            if panel.panel_id == wanted:
                return panel
        raise KeyError(f"no panel in the book: {wanted!r}")

    def record_ids(self) -> Tuple[str, ...]:
        """Every held record id, in held order."""
        return tuple(
            item.record_id for item in self.records if item.record_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "long_session_endurance_book",
            "slice": LONG_SESSION_ENDURANCE_SLICE,
            "title": self.title,
            "record_ids": list(self.record_ids()),
            "record_count": len(self.records),
            "panel_count": len(self.panels),
        }


def validate_book(data: Any, *, require_example: bool = False
                  ) -> EnduranceBook:
    """Validate one endurance mapping into a book.

    The mapping names a ``schema`` (the endurance
    schema word), a ``guide`` mapping (its
    ``title``), a ``records`` list and an optional
    ``panels`` list. Every record stands on its own
    validation, then the whole is judged: record ids
    unique, no thing measured twice under one kind,
    and every stored panel judged against the book
    (a panel the book does not derive refuses). With
    ``require_example`` the shipped example is held
    to its pinned shape: the pinned title, records
    and panel, and the panel's pinned rows and
    account word-for-word. Problems raise
    :class:`ValidationError` or ``ValueError``.
    """
    if isinstance(data, EnduranceBook):
        return data
    if not isinstance(data, dict):
        raise ValidationError(
            f"an endurance book must be a mapping, got {data!r}")
    unknown = set(data) - _ENDURANCE_BOOK_KEYS
    if unknown:
        raise ValidationError(
            "unknown endurance-book keys: %s" % ", ".join(sorted(unknown)))
    if data.get("schema") != LONG_SESSION_ENDURANCE_SCHEMA:
        raise ValidationError(
            f"an endurance book must carry schema "
            f"{LONG_SESSION_ENDURANCE_SCHEMA!r}, "
            f"got {data.get('schema')!r}")
    records = _pick_any(data, ("records",), "records")
    if records is None:
        raise ValidationError("an endurance book is missing its records")
    if not isinstance(records, (list, tuple)):
        raise ValidationError("an endurance book's records must be a list")
    if data.get("panels") is not None \
            and not isinstance(data["panels"], (list, tuple)):
        raise ValidationError("an endurance book's panels must be a list")
    head = data.get("guide") or {}
    if not isinstance(head, dict):
        raise ValidationError("an endurance book's guide must be a mapping")
    unknown_head = set(head) - _BOOK_KEYS
    if unknown_head:
        raise ValidationError(
            "unknown guide keys: %s" % ", ".join(sorted(unknown_head)))
    try:
        title = _pick_any(head, ("title", "name"), "titles")
        if title is None:
            raise ValidationError("an endurance book is missing its title")
        note = data.get("canon_note") or ""
        if not isinstance(note, str):
            raise ValidationError("an endurance book's note must be text")
        book = EnduranceBook(
            title=title, records=tuple(records),
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
                "the shipped example endurance book's title "
                "is not the pinned title")
        if book.record_ids() != _EXAMPLE_RECORD_IDS:
            raise ValidationError(
                "the shipped example's records are not the "
                "pinned records")
        panel = book.panel_for(_EXAMPLE_PANEL_ID)
        if tuple(r.record_id for r in panel.rows) != _EXAMPLE_PANEL_ROW_IDS:
            raise ValidationError(
                "the shipped example panel does not name its "
                "pinned rows in panel order")
        if panel.account != _EXAMPLE_PANEL_ACCOUNT:
            raise ValidationError(
                "the shipped example panel does not carry its "
                "pinned account word-for-word")
        first = book.records[0]
        if first.record_id != _EXAMPLE_FIRST_RECORD_ID \
                or first.subject != _EXAMPLE_FIRST_RECORD_SUBJECT:
            raise ValidationError(
                "the shipped example's first record is not "
                "its pinned record of its pinned subject")
    return book


def build_book(book: Any = None, **kwargs: Any) -> EnduranceBook:
    """Build one validated book, from a mapping or field words."""
    if isinstance(book, EnduranceBook) and not kwargs:
        return book
    if isinstance(book, dict):
        if "schema" in book:
            return validate_book(book)
        merged: Dict[str, Any] = dict(book)
        merged.update(kwargs)
        return EnduranceBook(**merged)
    if book is None:
        return EnduranceBook(**kwargs)
    raise ValueError(f"an endurance book is needed, got {book!r}")


def _book_from(data: Any, *, require_example: bool) -> EnduranceBook:
    try:
        return validate_book(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_long_session_endurance(
        data: Optional[Dict[str, Any]] = None) -> EnduranceBook:
    """Load and validate the shipped example book (or *data*).

    The shipped file is held to the example check:
    the pinned title, records and panel - the M-160
    slice boundary book - so the shipped book covers
    the canon this slice exists to hold.
    """
    raw = data if data is not None else load_resource(
        LONG_SESSION_ENDURANCE_RESOURCE)
    return _book_from(raw, require_example=True)


def load_long_session_endurance_file(path: Any) -> EnduranceBook:
    """Load and validate an endurance book from a file at *path*.

    Any file in the endurance shape, anywhere on
    disk, validated whole - a malformed file raises
    :class:`ValidationError` naming the problem, and
    a missing file raises ``FileNotFoundError``. The
    example check is not held: a real book stands on
    its own records.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _book_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The registry model: one book held record by record.
# ---------------------------------------------------------------------


class EnduranceRegistry:
    """One session's endurance records, held one by one.

    The registry holds records, never panels or
    verdicts: the panel and the verdict are
    derivations, read off the whole held book at
    call time, so nothing here can hold a figure
    stale. A whole book is judged as a book judges
    it - its ids and its measured things against
    the whole book - before its records are held in
    book order. A thing held here is measured once
    per kind: a second record of a held kind and
    reference refuses.
    """

    def __init__(self, book: Any = None) -> None:
        self._title: Optional[str] = None
        self._records: Dict[str, EnduranceRecord] = {}
        self._record_order: list = []
        self._next_record = 1
        if book is not None:
            self.register_book(book)

    def _fresh_record_id(self, held_ids: Any) -> str:
        while f"endurance-{self._next_record}" in held_ids:
            self._next_record += 1
        fresh = f"endurance-{self._next_record}"
        self._next_record += 1
        return fresh

    def _check_ref_free(self, record: EnduranceRecord) -> None:
        for held in self._records.values():
            if held.kind == record.kind and held.ref == record.ref:
                raise ValueError(
                    f"the {record.kind} measurement standing "
                    f"as {record.ref!r} is already taken in "
                    f"this book - one thing is measured once "
                    f"per kind in a book")

    def register_record(self, record: Any) -> EnduranceRecord:
        """Register one endurance record into the held book.

        A record with no id is given a deterministic
        ``endurance-N`` id. A record id already
        standing here refuses, as does a record
        measuring a thing a held record already
        measures under the same kind.
        """
        validated = _check_record_ref(record)
        if validated.record_id is not None \
                and validated.record_id in self._records:
            raise ValueError(
                f"an endurance record named "
                f"{validated.record_id!r} already exists")
        self._check_ref_free(validated)
        return self._hold_record(validated)

    def _hold_record(self, validated: EnduranceRecord) -> EnduranceRecord:
        """Hold one judged record, in held order.

        The caller has already judged the record
        against the held book (its id and its
        measured thing); this is the holding alone,
        with a deterministic ``endurance-N`` id given
        to a record carrying none.
        """
        if validated.record_id is None:
            validated = replace(
                validated,
                record_id=self._fresh_record_id(set(self._records)))
        self._records[validated.record_id] = validated
        self._record_order.append(validated.record_id)
        return validated

    def register_book(self, book: Any) -> EnduranceBook:
        """Register every record of one book, in order.

        The first book held sets the title; a later
        book under a different title refuses, as does
        a book naming a held record id or a held
        measured thing. The book is judged whole
        before anything is held, and the records are
        then held in the book's own order. The book's
        panels are derivations, not holdings, and are
        not held.
        """
        validated = build_book(book)
        if self._title is not None and validated.title != self._title:
            raise ValueError(
                "this registry already holds an endurance "
                "book under a different title")
        for record in validated.records:
            if record.record_id in self._records:
                raise ValueError(
                    f"an endurance record named "
                    f"{record.record_id!r} already exists")
            self._check_ref_free(record)
        self._title = validated.title
        for record in validated.records:
            self._hold_record(record)
        return self.book()

    def get_record(self, record_id: Any) -> EnduranceRecord:
        """The endurance record one id names among the held records."""
        wanted = normalize_member_id(record_id)
        if wanted not in self._records:
            raise KeyError(f"unknown endurance record: {wanted!r}")
        return self._records[wanted]

    def record_for_ref(self, kind: Any, ref: Any) -> EnduranceRecord:
        """The held record measuring one thing under one kind."""
        wanted_kind = normalize_endurance_kind(kind)
        wanted_ref = _check_word(ref, "a record's reference")
        for record_id in self._record_order:
            record = self._records[record_id]
            if record.kind == wanted_kind and record.ref == wanted_ref:
                return record
        raise KeyError(
            f"no record held measures the {wanted_kind} "
            f"standing as {wanted_ref!r}")

    def latest_record(self) -> EnduranceRecord:
        """The most recently held endurance record."""
        if not self._record_order:
            raise ValueError("no endurance record is held yet")
        return self._records[self._record_order[-1]]

    def list_records(self) -> Tuple[EnduranceRecord, ...]:
        """Every held endurance record, in the order they were held."""
        return tuple(self._records[item] for item in self._record_order)

    def book(self) -> EnduranceBook:
        """The held records as one validated book."""
        if self._title is None:
            raise ValueError("no endurance book is held yet")
        return EnduranceBook(
            title=self._title, records=self.list_records())

    def panel(self) -> EndurancePanel:
        """Derive the endurance panel of the whole held book."""
        return derive_panel(self)

    def verdict(self) -> EnduranceVerdict:
        """Derive the endurance verdict of the whole held book."""
        return derive_verdict(self)


# ---------------------------------------------------------------------
# The visible surface: how the book stands, read off any book.
# ---------------------------------------------------------------------


def endurance_refs(source: Any) -> Tuple[Tuple[str, str], ...]:
    """Every measured thing one source holds, in panel order.

    The visible list of endurance: each held record's
    kind and the reference it measures, in the order
    the derived panel shows them. *source* is a book
    or a registry.
    """
    panel = derive_panel(source)
    return tuple((row.kind, row.ref) for row in panel.rows)


def total_over_budget(source: Any) -> int:
    """The measurements one source holds that stand over budget.

    The derived panel's own total: the count of
    every held record whose measure exceeds its
    budget, read at call time. *source* is a book or
    a registry.
    """
    return derive_panel(source).total_over


# ---------------------------------------------------------------------
# Endurance news, shaped as session records.
# ---------------------------------------------------------------------


def endurance_record(record: Any) -> Dict[str, Any]:
    """The session-news record of one endurance record."""
    current = record if isinstance(record, EnduranceRecord) \
        else build_record(record)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Endurance ({current.kind}): \"{current.subject}\" "
        f"measured {current.measured} {current.unit} against "
        f"a budget of {current.budget} - {current.verdict}, "
        f"recorded by {current.recorded_by} on "
        f"{current.recorded_on}.")
    return record_out


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived panel.

    With *source* given, the panel is first judged
    against the panel that source derives.
    """
    current = validate_panel(panel, source)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Endurance panel: {current.total_records} measurements - "
        f"{current.total_within} within budget, "
        f"{current.total_over} over budget.")
    return record_out


def verdict_record(verdict: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived verdict.

    With *source* given, the verdict is first judged
    against the verdict that source derives.
    """
    current = validate_verdict(verdict, source)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Endurance verdict: {current.verdict} - "
        f"{current.over_budget} of {current.total_records} "
        f"measurements over budget.")
    return record_out


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one endurance book."""
    current = book if isinstance(book, EnduranceBook) \
        else build_book(book)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Long-session endurance {current.title}: "
        f"{record_out['record_count']} measurements held.")
    return record_out


def plain_words(record: Any) -> str:
    """One endurance record, in one plain sentence."""
    current = record if isinstance(record, EnduranceRecord) \
        else build_record(record)
    return (
        f"\"{current.subject}\" was measured under the "
        f"{current.kind} kind ({current.ref}): "
        f"{current.measured} {current.unit} against a "
        f"budget of {current.budget} - {current.verdict}. "
        f"It was recorded by {current.recorded_by} on "
        f"{current.recorded_on} (read from {current.source}).")


def panel_plain_words(source: Any) -> str:
    """The endurance panel in plain words, in full.

    Accepts an EndurancePanel or an EnduranceBook
    (whose derived panel is told). The panel is told
    whole - its rows in panel order and its account.
    """
    if isinstance(source, EndurancePanel):
        panel = validate_panel(source)
        title = None
    elif isinstance(source, EnduranceBook):
        panel = derive_panel(source)
        title = source.title
    else:
        raise ValueError(
            f"an endurance source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Endurance measurements, in panel order:")
    for row in panel.rows:
        lines.append(
            f"{row.record_id}: \"{row.subject}\" - "
            f"the {row.kind} kind ({row.ref}), "
            f"{row.measured} of a budget of {row.budget}, "
            f"{row.verdict}, recorded by {row.recorded_by} "
            f"on {row.recorded_on}")
    lines.extend(panel.account)
    return "\n".join(lines)


def verdict_plain_words(source: Any) -> str:
    """The endurance verdict in plain words.

    Accepts an EnduranceVerdict or an EnduranceBook
    (whose derived verdict is told).
    """
    if isinstance(source, EnduranceVerdict):
        verdict = validate_verdict(source)
    elif isinstance(source, (EnduranceBook, EnduranceRegistry)):
        verdict = derive_verdict(source)
    else:
        raise ValueError(
            f"an endurance source is needed, got {source!r}")
    if verdict.over_budget == 0:
        worst_words = "nothing stands over budget"
    else:
        worst_words = (
            f"the worst is {verdict.worst_record_id}, "
            f"{verdict.worst_over_by} over its budget")
    return (
        f"Endurance verdict: {verdict.verdict} - "
        f"{verdict.within_budget} of {verdict.total_records} "
        f"measurements within budget, {verdict.over_budget} "
        f"over budget; {worst_words}.")


# ---------------------------------------------------------------------
# Screens: the formatters and the /endurance grammar.
# ---------------------------------------------------------------------


def _source_book(source: Any) -> EnduranceBook:
    if source is None:
        return load_long_session_endurance()
    if isinstance(source, EnduranceRegistry):
        return source.book()
    if isinstance(source, EnduranceBook):
        return source
    raise ValueError(f"an endurance book is needed, got {source!r}")


def format_endurance_record(record: Any) -> str:
    """One endurance record as a screen block, provenance whole."""
    current = record if isinstance(record, EnduranceRecord) \
        else build_record(record)
    lines = [
        f"{current.record_id or '-'}: \"{current.subject}\" - "
        f"the {current.kind} kind ({current.ref}), recorded by "
        f"{current.recorded_by} on {current.recorded_on}",
        f"Measured: {current.measured} {current.unit} against "
        f"a budget of {current.budget} - {current.verdict}"
        + (f" by {current.over_by}." if current.over_by else "."),
        f"(read from {current.source})",
        "This record holds endurance as data - it runs "
        "no live session and times nothing itself.",
    ]
    return "\n".join(lines)


def format_endurance_records(source: Any = None, kind: Any = None) -> str:
    """Endurance records of one book, in held order.

    With *kind* named, only the records of that kind
    stand - read through the kind aliases, so a kind
    nothing holds shows its own empty line.
    """
    book = _source_book(source)
    wanted = normalize_endurance_kind(kind) if kind is not None else None
    lines = [
        f"{item.record_id or '-'}: \"{item.subject}\" - "
        f"the {item.kind} kind ({item.ref}), {item.measured} "
        f"of a budget of {item.budget} - {item.verdict}, "
        f"recorded by {item.recorded_by}"
        for item in book.records
        if wanted is None or item.kind == wanted]
    if not lines:
        lines.append("No endurance records are held.")
    return "\n".join(lines)


def format_panel(source: Any = None) -> str:
    """The endurance panel as a screen block: every row, the account.

    Accepts an EndurancePanel or an EnduranceBook; a
    book shows the panel it derives.
    """
    if isinstance(source, EndurancePanel):
        panel = validate_panel(source)
        lines: list = []
    else:
        book = _source_book(source)
        if not book.records:
            return (f"Endurance panel in {book.title}:\n"
                    f"No endurance records are held.")
        panel = derive_panel(book)
        lines = [f"Endurance panel in {book.title}:"]
    lines.append("Endurance measurements, in panel order:")
    for row in panel.rows:
        lines.append(
            f"{row.record_id}: \"{row.subject}\" - "
            f"the {row.kind} kind ({row.ref}), "
            f"{row.measured} of a budget of {row.budget}, "
            f"{row.verdict}, recorded by {row.recorded_by} "
            f"on {row.recorded_on}")
    lines.extend(panel.account)
    return "\n".join(lines)


def format_verdict(source: Any = None) -> str:
    """The endurance verdict as a screen block, for the whole book.

    Accepts an EnduranceVerdict or an EnduranceBook;
    a book shows the verdict it derives.
    """
    if isinstance(source, EnduranceVerdict):
        verdict = validate_verdict(source)
        lines = [verdict_plain_words(verdict)]
    else:
        book = _source_book(source)
        verdict = derive_verdict(book)
        lines = [f"Endurance verdict in {book.title}:",
                 verdict_plain_words(verdict)]
    lines.append(
        "This verdict is a derivation for reporting - "
        "it changes nothing any live session does.")
    return "\n".join(lines)


def format_long_session_endurance_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /endurance.

    With nothing named, the shipped example endurance
    book is shown - the example this slice ships - so
    the screen is never empty.
    """
    book = _source_book(source)
    lines = ["Long-Session Endurance (M-161) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_endurance_records(book))
    lines.append("")
    lines.append(format_panel(book))
    lines.append("")
    lines.append(format_verdict(book))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_endurance_args(args: Any) -> Tuple[str, Any]:
    """Parse the /endurance grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    endurance book; ``record <record-id>`` shows one
    record with its provenance whole; ``kind <kind>``
    shows the records of one kind, the kind read
    through the kind aliases; ``panel`` shows the
    endurance panel derived from the whole book;
    ``verdict`` shows the endurance verdict derived
    for the whole book. Anything else is a usage
    error naming the grammar. Returns
    ``(action, value-or-None)``.
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
    if head == "record" and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "kind" and len(words) == 2:
        try:
            return (head, normalize_endurance_kind(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
