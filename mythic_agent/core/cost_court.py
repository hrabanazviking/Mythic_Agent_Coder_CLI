"""Cost court (All-Features roadmap slice M-140).

Part VI continues here. The roadmap's words:
``crew runs report cost per member per slice;
the Scribe keeps the ledger that Part XI's
efficiency work reads.``

What already shipped, and what this slice adds:

* The money machinery already exists in pieces.
  The shared rate table is ``core/costs.py``
  (:func:`price` - the single source of truth for
  per-1M-token rates), and the provider layer
  already prices single calls over it
  (``providers/cost_ledger.py``, Slice 046: one
  call priced as usage x model price, with
  provider attribution). The members are the
  shipped crew (``core/crew_members.py``, M-121) -
  and the Scribe named by this slice's roadmap
  words is that casting's own ``scribe`` member.
  Budgets (``core/budgets.py``, M-107) were
  checked and are not composed: a budget judges a
  limit against usage and answers with a verdict;
  a run record names no limit and the court
  delivers no verdict, so this slice holds the
  run records themselves and composes the rate
  table instead. What nothing holds is the court
  itself: a crew run's cost, held per member per
  slice, and the ledger the Scribe keeps of it.
* This slice is that court, as a pure layer: a
  run record validated as data (the member who
  ran, the slice the run served, the model, and
  the input / output tokens - the record's cost
  is DERIVED from the shared rate table, never
  stored on the record), a per-member-per-slice
  report whose totals and account are DERIVED
  from the run records it reports, the Scribe's
  ledger whose rows and account are DERIVED from
  the whole book of run records, the shipped
  data file (``mythic_agent/data/cost_court.yaml``)
  holding one example court book in exactly the
  shape a real court file takes, a loader for a
  court file anywhere on disk, records shaped as
  session news, and a small in-memory registry
  model. This module bills no one, charges
  nothing, calls no model, persists nothing and
  imports no agent / UI code; the agent layer
  owns holding a court book for a session.

Honesty rules, enforced here and pinned by tests:

* **A cost is derived, never stored loose.** A
  run record names tokens and a model, never a
  cost: its cost is read off the shared rate
  table (``core/costs.price``, composed by
  import, never re-implemented), so a record can
  never claim a spend the table does not price.
  A model the table does not know prices at $0
  and is counted as unpriced, exactly as the
  shipped cost layers read unknown models.
* **A report is derived, never stored loose.**
  A report's calls, tokens, cost, unpriced count
  and account are read off the run records of
  one member on one slice, in held order, so a
  stored report that disagrees with the report
  derived from the records it names refuses. A
  report naming no account of its own refuses
  too.
* **The Scribe's ledger is derived, never
  stored loose.** The ledger's rows are the
  book's per-member-per-slice reports, in the
  order the run records first name them; its
  totals are the rows' sums and its account is
  read off the rows, so a stored ledger whose
  keeper, rows, totals or account disagree with
  the derived ledger refuses. The keeper is
  always the Scribe - the shipped casting's own
  ``scribe`` member; a ledger kept by anyone
  else refuses.
* **Members and slices are the shipped layers'
  own.** Member ids read exactly as the M-121
  layer reads them and slice ids exactly as the
  worktrees layer reads them, both composed by
  import, so the member and slice a record names
  answer to exactly the validators a live run
  answers to.
* **Data only - no live road is claimed.** A
  cost here is a validated record held as data:
  no model is called, no bill is issued, nothing
  is charged and nothing here claims a crew run
  happened live. The court is visible through
  this slice's own /costcourt screen, and
  nothing here claims Part XI's efficiency work
  exists - the ledger is only the shape that
  work will read.
* **Malformed refuses.** A duplicate entry id
  in one book, a report or ledger naming a
  record the book holds no record for, and
  unknown keys in a record, a report, a ledger
  or a court mapping all raise instead of being
  skipped or guessed at.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .costs import price as _shared_price
from .crew_members import normalize_member_id
from .validation import ValidationError
from .worktrees import normalize_slice_id

__all__ = [
    "COST_COURT_RESOURCE",
    "COST_COURT_SCHEMA",
    "COST_COURT_SLICE",
    "PLAIN_EXPLANATION",
    "SCRIBE_MEMBER",
    "USAGE",
    "CostBook",
    "CostEntry",
    "CostReport",
    "CourtRegistry",
    "ScribeLedger",
    "book_record",
    "build_book",
    "build_entry",
    "build_ledger",
    "build_report",
    "derive_ledger",
    "derive_report",
    "entry_record",
    "format_cost_court_screen",
    "format_entries",
    "format_entry",
    "format_ledger",
    "format_report",
    "ledger_plain_words",
    "ledger_record",
    "load_cost_court",
    "load_cost_court_file",
    "parse_cost_court_args",
    "plain_words",
    "report_plain_words",
    "report_record",
    "validate_book",
    "validate_entry",
    "validate_ledger",
    "validate_report",
]

COST_COURT_SLICE = "M-140"

#: The packaged data resource holding the example book.
COST_COURT_RESOURCE = "cost_court.yaml"

#: The schema word a court file must carry.
COST_COURT_SCHEMA = "mythic.cost_court/1"

#: The member who keeps the ledger: the shipped
#: M-121 casting's own scribe.
SCRIBE_MEMBER = "scribe"

_ENTRY_KEYS = frozenset({
    "entry_id", "id", "member", "member_id",
    "slice", "slice_id", "model",
    "input_tokens", "input", "prompt_tokens",
    "output_tokens", "output", "completion_tokens",
})

_REPORT_KEYS = frozenset({
    "report_id", "id", "member", "member_id",
    "slice", "slice_id", "entries", "entry_ids",
    "calls", "call_count",
    "input_tokens", "output_tokens",
    "cost", "cost_usd", "spend",
    "unpriced", "unpriced_calls", "unpriced_count",
    "account", "statements",
})

_LEDGER_KEYS = frozenset({
    "ledger_id", "id", "keeper", "scribe",
    "rows", "reports",
    "total_calls", "calls",
    "total_input_tokens", "input_tokens",
    "total_output_tokens", "output_tokens",
    "total_cost", "total_cost_usd", "cost", "cost_usd",
    "account", "statements",
})

_BOOK_KEYS = frozenset({"title", "name"})

_COURT_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "court_note", "guide", "entries", "ledgers",
})

_MODEL_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789-_.:/")

#: The shipped example book's title, held to this
#: by the loader's example check.
_EXAMPLE_TITLE = "Cost court at the M-139 slice boundary"

#: The shipped example's entry ids, in held order,
#: pinned by the loader.
_EXAMPLE_ENTRY_IDS = (
    "entry-m139-forge-a", "entry-m139-forge-b",
    "entry-m139-auditor", "entry-m138-scribe-a",
    "entry-m138-scribe-b")

#: The shipped example's one ledger: kept by the
#: Scribe, its rows and totals pinned by the loader.
_EXAMPLE_LEDGER_ID = "ledger-m139-boundary"

_EXAMPLE_LEDGER_ROWS = (
    ("M-139", "forge_worker"),
    ("M-139", "auditor"),
    ("M-138", "scribe"),
)

_EXAMPLE_LEDGER_TOTALS = (5, 37000, 10500, 0.14145)

_EXAMPLE_LEDGER_ACCOUNT = (
    "The Scribe keeps this ledger: 3 member-slice "
    "row(s) across 2 slice(s).",
    "Total: $0.141450 from 5 call(s), 37000 input "
    "tokens and 10500 output tokens.",
    "Part XI's efficiency work reads this ledger.",
)

#: The shipped example's pinned first report: the
#: forge worker's two M-139 calls, its account
#: pinned word-for-word by the loader.
_EXAMPLE_FIRST_REPORT_ACCOUNT = (
    "Member forge_worker spent $0.135000 on "
    "slice M-139.",
    "2 call(s), 20000 input tokens and 5000 "
    "output tokens on M-139.",
    "Every call was priced from the shared "
    "cost table.",
)

PLAIN_EXPLANATION = (
    "The cost court: a crew run's cost, held as "
    "run records - the member who ran, the slice, "
    "the model and the tokens - with every cost "
    "derived from the shared rate table, never "
    "stored on a record. A report reads one "
    "member's cost on one slice off those records, "
    "derived, never stored loose, and the Scribe "
    "keeps the ledger of the whole book - its rows "
    "the per-member-per-slice reports, derived the "
    "same way - for Part XI's efficiency work to "
    "read. This layer holds costs as data only; "
    "it calls no model, bills no one, charges "
    "nothing and persists nothing itself."
)

USAGE = (
    "Usage: /costcourt, /costcourt show, "
    "/costcourt entry <entry-id>, "
    "/costcourt member <member-id>, "
    "/costcourt slice <slice-id>, "
    "/costcourt ledger"
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


def _check_model(value: Any) -> str:
    text = _clean_text(value, "a model")
    if len(text) > 120 or any(ch not in _MODEL_CHARS for ch in text):
        raise ValueError(
            f"a model must be one word of letters, digits, "
            f"dashes, underscores, dots, slashes and colons, "
            f"got {value!r}")
    return text


def _check_tokens(value: Any, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{what} must be a token count, got {value!r}")
    if value < 0 or value > 100_000_000_000:
        raise ValueError(
            f"{what} must be between 0 and 100000000000, "
            f"got {value!r}")
    return value


def _check_count(value: Any, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{what} must be a count, got {value!r}")
    if value < 0:
        raise ValueError(f"{what} must not be negative, got {value!r}")
    return value


def _check_cost(value: Any, what: str = "a cost") -> float:
    if isinstance(value, bool) \
            or not isinstance(value, (int, float)):
        raise ValueError(f"{what} must be a number, got {value!r}")
    cost = round(float(value), 6)
    if cost < 0:
        raise ValueError(f"{what} must not be negative, got {value!r}")
    return cost


def _entry_cost(entry: "CostEntry") -> Tuple[float, bool]:
    """One record's derived cost: the shared table's own pricing."""
    return _shared_price(
        entry.model, entry.input_tokens, entry.output_tokens)


# ---------------------------------------------------------------------
# The run record: one member's run on one slice, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class CostEntry:
    """One run record: one member's model run on one slice.

    ``member`` is the member who ran; ``slice_id``
    is the slice the run served; ``model`` is the
    model run; ``input_tokens`` / ``output_tokens``
    are the run's token counts. The record names
    no cost: ``cost_usd`` is derived from the
    shared rate table at read time, and ``priced``
    says whether the table knows the model.
    Constructing one validates it.
    """

    entry_id: Optional[str] = None
    member: str = ""
    slice_id: str = ""
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0

    def __post_init__(self) -> None:
        if self.entry_id is not None:
            object.__setattr__(
                self, "entry_id", normalize_member_id(self.entry_id))
        object.__setattr__(
            self, "member", normalize_member_id(self.member))
        object.__setattr__(
            self, "slice_id", normalize_slice_id(self.slice_id))
        object.__setattr__(self, "model", _check_model(self.model))
        object.__setattr__(
            self, "input_tokens",
            _check_tokens(self.input_tokens, "input tokens"))
        object.__setattr__(
            self, "output_tokens",
            _check_tokens(self.output_tokens, "output tokens"))

    @property
    def cost_usd(self) -> float:
        """This run's cost, derived from the shared rate table."""
        return _entry_cost(self)[0]

    @property
    def priced(self) -> bool:
        """Whether the shared rate table prices this run's model."""
        return _entry_cost(self)[1]

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "cost_court_entry",
            "slice": COST_COURT_SLICE,
            "entry_id": self.entry_id,
            "member": self.member,
            "slice_id": self.slice_id,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_usd": self.cost_usd,
            "priced": self.priced,
        }


def validate_entry(entry: Any) -> CostEntry:
    """Validate one run record into a CostEntry.

    Accepts a CostEntry or a mapping naming a
    ``member`` (or ``member_id``), a ``slice_id``
    (or ``slice``), a ``model``, ``input_tokens``
    (or ``input`` / ``prompt_tokens``),
    ``output_tokens`` (or ``output`` /
    ``completion_tokens``) and an optional
    ``entry_id`` (or ``id``). Naming two spellings
    of one field with different values refuses,
    and unknown keys refuse - a stored cost key
    among them, because a cost is derived, never
    stored.
    """
    if isinstance(entry, CostEntry):
        return entry
    if not isinstance(entry, dict):
        raise ValueError(f"a run record must be a mapping, got {entry!r}")
    unknown = set(entry) - _ENTRY_KEYS
    if unknown:
        raise ValueError(
            "unknown run-record keys: %s" % ", ".join(sorted(unknown)))
    member = _pick_any(entry, ("member", "member_id"), "members")
    if member is None:
        raise ValueError("a run record is missing its member")
    slice_id = _pick_any(entry, ("slice_id", "slice"), "slices")
    if slice_id is None:
        raise ValueError("a run record is missing its slice")
    if "model" not in entry:
        raise ValueError("a run record is missing its model")
    input_tokens = _pick_any(
        entry, ("input_tokens", "input", "prompt_tokens"), "input tokens")
    if input_tokens is None:
        raise ValueError("a run record is missing its input tokens")
    output_tokens = _pick_any(
        entry, ("output_tokens", "output", "completion_tokens"),
        "output tokens")
    if output_tokens is None:
        raise ValueError("a run record is missing its output tokens")
    kwargs: Dict[str, Any] = {
        "member": member, "slice_id": slice_id,
        "model": entry["model"], "input_tokens": input_tokens,
        "output_tokens": output_tokens}
    entry_id = _pick_any(entry, ("entry_id", "id"), "entry ids")
    if entry_id is not None:
        kwargs["entry_id"] = entry_id
    return CostEntry(**kwargs)


def build_entry(entry: Any = None, **kwargs: Any) -> CostEntry:
    """Build one validated run record, from a mapping or field words."""
    if isinstance(entry, CostEntry) and not kwargs:
        return entry
    if isinstance(entry, dict) or entry is None:
        merged: Dict[str, Any] = {}
        if isinstance(entry, dict):
            merged.update(entry)
        merged.update(kwargs)
        return validate_entry(merged)
    raise ValueError(f"a run record must be a mapping, got {entry!r}")


def _check_entry_ref(value: Any) -> CostEntry:
    if isinstance(value, CostEntry):
        return value
    if isinstance(value, dict):
        return validate_entry(value)
    raise ValueError(f"a run record is needed, got {value!r}")


def _held_entries(source: Any) -> Tuple[CostEntry, ...]:
    """The run records one source holds, in held order."""
    if isinstance(source, CostBook):
        return source.entries
    if isinstance(source, CourtRegistry):
        return source.list_entries()
    if isinstance(source, (list, tuple)):
        return tuple(_check_entry_ref(e) for e in source)
    raise ValueError(f"run records are needed, got {source!r}")


# ---------------------------------------------------------------------
# The report: one member's cost on one slice, derived.
# ---------------------------------------------------------------------


def _report_account(member: str, slice_id: str, calls: int,
                    input_tokens: int, output_tokens: int,
                    cost_usd: float, unpriced: int) -> Tuple[str, ...]:
    if unpriced:
        priced_line = (
            f"{unpriced} call(s) used unpriced models "
            f"and billed $0.")
    else:
        priced_line = "Every call was priced from the shared cost table."
    return (
        f"Member {member} spent ${cost_usd:.6f} on "
        f"slice {slice_id}.",
        f"{calls} call(s), {input_tokens} input tokens and "
        f"{output_tokens} output tokens on {slice_id}.",
        priced_line,
    )


@dataclass(frozen=True)
class CostReport:
    """One member's cost on one slice, as data.

    ``entry_ids`` are the run records the report
    reads, in held order; ``calls``, the token
    totals, ``cost_usd`` and ``unpriced_calls``
    are their sums; ``account`` is the plain
    statements the report rests on, derived from
    those records. A report is normally derived
    (see :func:`derive_report`); constructing one
    directly validates its shape only.
    """

    report_id: Optional[str] = None
    member: str = ""
    slice_id: str = ""
    entry_ids: Tuple[str, ...] = ()
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    unpriced_calls: int = 0
    account: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.report_id is not None:
            object.__setattr__(
                self, "report_id", normalize_member_id(self.report_id))
        object.__setattr__(
            self, "member", normalize_member_id(self.member))
        object.__setattr__(
            self, "slice_id", normalize_slice_id(self.slice_id))
        if isinstance(self.entry_ids, (str, bytes)) \
                or not isinstance(self.entry_ids, (list, tuple)):
            raise ValueError(
                f"a report's entries must be a list of entry ids, "
                f"got {self.entry_ids!r}")
        ids = tuple(normalize_member_id(v) for v in self.entry_ids)
        if not ids:
            raise ValueError("a report reads at least one run record")
        if len(set(ids)) != len(ids):
            raise ValueError("a report reads one run record twice")
        object.__setattr__(self, "entry_ids", ids)
        object.__setattr__(
            self, "calls", _check_count(self.calls, "a report's calls"))
        if self.calls != len(ids):
            raise ValueError(
                "a report's calls must count the run records it reads")
        object.__setattr__(
            self, "input_tokens",
            _check_count(self.input_tokens, "a report's input tokens"))
        object.__setattr__(
            self, "output_tokens",
            _check_count(self.output_tokens, "a report's output tokens"))
        object.__setattr__(self, "cost_usd", _check_cost(self.cost_usd))
        object.__setattr__(
            self, "unpriced_calls",
            _check_count(self.unpriced_calls, "a report's unpriced calls"))
        if self.unpriced_calls > self.calls:
            raise ValueError(
                "a report's unpriced calls cannot outnumber its calls")
        object.__setattr__(
            self, "account", _check_account(self.account))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "cost_court_report",
            "slice": COST_COURT_SLICE,
            "report_id": self.report_id,
            "member": self.member,
            "slice_id": self.slice_id,
            "entry_ids": list(self.entry_ids),
            "calls": self.calls,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_usd": self.cost_usd,
            "unpriced_calls": self.unpriced_calls,
            "account": list(self.account),
        }


def derive_report(source: Any, member: Any,
                  slice_id: Any) -> CostReport:
    """Derive one member's report on one slice from run records.

    *source* is a CostBook, a CourtRegistry or a
    list of run records; the report reads every
    held record naming *member* and *slice_id*,
    in held order, and its totals and account are
    read off those records: the calls, the token
    sums, the derived costs' sum and the unpriced
    count. No held record for the pair raises
    ``KeyError``. Deriving is deterministic: the
    same records derive the same report, every
    time.
    """
    entries = _held_entries(source)
    wanted_member = normalize_member_id(member)
    wanted_slice = normalize_slice_id(slice_id)
    held = tuple(
        e for e in entries
        if e.member == wanted_member and e.slice_id == wanted_slice)
    if not held:
        raise KeyError(
            f"no held run records: {wanted_member!r} on "
            f"{wanted_slice!r}")
    if any(e.entry_id is None for e in held):
        raise ValueError(
            "a report's run records must name entry ids - "
            "a report is addressed by the records it reads")
    calls = len(held)
    input_tokens = sum(e.input_tokens for e in held)
    output_tokens = sum(e.output_tokens for e in held)
    cost_usd = round(sum(e.cost_usd for e in held), 6)
    unpriced = sum(1 for e in held if not e.priced)
    return CostReport(
        member=wanted_member, slice_id=wanted_slice,
        entry_ids=tuple(e.entry_id for e in held),
        calls=calls, input_tokens=input_tokens,
        output_tokens=output_tokens, cost_usd=cost_usd,
        unpriced_calls=unpriced,
        account=_report_account(
            wanted_member, wanted_slice, calls, input_tokens,
            output_tokens, cost_usd, unpriced))


def validate_report(report: Any, source: Any = None) -> CostReport:
    """Validate one report into a CostReport.

    Accepts a CostReport or a mapping naming a
    ``member`` (or ``member_id``), a ``slice_id``
    (or ``slice``), its ``entry_ids`` (or
    ``entries``), ``calls`` (or ``call_count``),
    ``input_tokens``, ``output_tokens``, a
    ``cost_usd`` (or ``cost`` / ``spend``),
    ``unpriced_calls`` (or ``unpriced`` /
    ``unpriced_count``), an ``account`` (or
    ``statements``) and an optional ``report_id``
    (or ``id``). With *source* given (a book, a
    registry or run records), the report is
    judged against the report derived from the
    source's records for its member and slice: a
    stored report whose entries, totals, unpriced
    count or account disagree with the derived
    report refuses, because a report is derived,
    never stored loose. A stored report naming no
    account of its own refuses, for the same
    reason.
    """
    if isinstance(report, CostReport):
        current = report
    elif isinstance(report, dict):
        unknown = set(report) - _REPORT_KEYS
        if unknown:
            raise ValueError(
                "unknown report keys: %s" % ", ".join(sorted(unknown)))
        member = _pick_any(report, ("member", "member_id"), "members")
        if member is None:
            raise ValueError("a report is missing its member")
        slice_id = _pick_any(report, ("slice_id", "slice"), "slices")
        if slice_id is None:
            raise ValueError("a report is missing its slice")
        entry_ids = _pick_any(
            report, ("entry_ids", "entries"), "entry id lists")
        if entry_ids is None:
            raise ValueError("a report is missing its entry ids")
        calls = _pick_any(report, ("calls", "call_count"), "call counts")
        if calls is None:
            raise ValueError("a report is missing its calls")
        if "input_tokens" not in report:
            raise ValueError("a report is missing its input tokens")
        if "output_tokens" not in report:
            raise ValueError("a report is missing its output tokens")
        cost = _pick_any(
            report, ("cost_usd", "cost", "spend"), "costs")
        if cost is None:
            raise ValueError("a report is missing its cost")
        unpriced = _pick_any(
            report, ("unpriced_calls", "unpriced", "unpriced_count"),
            "unpriced counts")
        if unpriced is None:
            raise ValueError("a report is missing its unpriced count")
        account = _pick_any(
            report, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError(
                "a stored report names no account of its own - "
                "derive it from its run records")
        report_id = _pick_any(report, ("report_id", "id"), "report ids")
        current = CostReport(
            report_id=report_id, member=member, slice_id=slice_id,
            entry_ids=entry_ids, calls=calls,
            input_tokens=report["input_tokens"],
            output_tokens=report["output_tokens"], cost_usd=cost,
            unpriced_calls=unpriced, account=account)
    else:
        raise ValueError(f"a report must be a mapping, got {report!r}")
    if source is not None:
        derived = derive_report(source, current.member, current.slice_id)
        judged = (
            current.entry_ids, current.calls, current.input_tokens,
            current.output_tokens, current.cost_usd,
            current.unpriced_calls, current.account)
        expected = (
            derived.entry_ids, derived.calls, derived.input_tokens,
            derived.output_tokens, derived.cost_usd,
            derived.unpriced_calls, derived.account)
        if judged != expected:
            raise ValueError(
                "a stored report disagrees with the report "
                "derived from its run records - a report is "
                "derived, never stored loose")
    return current


def build_report(report: Any = None, source: Any = None,
                 **kwargs: Any) -> CostReport:
    """Build one validated report, from a mapping or field words."""
    if isinstance(report, CostReport) and not kwargs:
        return validate_report(report, source)
    if isinstance(report, dict) or report is None:
        merged: Dict[str, Any] = {}
        if isinstance(report, dict):
            merged.update(report)
        merged.update(kwargs)
        return validate_report(merged, source)
    return validate_report(report, source)


# ---------------------------------------------------------------------
# The Scribe's ledger: the whole book's rows, derived.
# ---------------------------------------------------------------------


def _ledger_account(rows: Tuple[CostReport, ...], total_calls: int,
                    input_tokens: int, output_tokens: int,
                    cost_usd: float) -> Tuple[str, ...]:
    slices = len({r.slice_id for r in rows})
    return (
        f"The Scribe keeps this ledger: {len(rows)} "
        f"member-slice row(s) across {slices} slice(s).",
        f"Total: ${cost_usd:.6f} from {total_calls} call(s), "
        f"{input_tokens} input tokens and {output_tokens} "
        f"output tokens.",
        "Part XI's efficiency work reads this ledger.",
    )


@dataclass(frozen=True)
class ScribeLedger:
    """The Scribe's ledger: one book's cost rows, as data.

    ``keeper`` is always the Scribe; ``rows`` are
    the book's per-member-per-slice reports, in
    the order the run records first name them;
    the totals are the rows' sums; ``account`` is
    the plain statements the ledger rests on,
    derived from its rows. A ledger is normally
    derived (see :func:`derive_ledger`);
    constructing one directly validates its shape
    and that its totals are its rows' own sums.
    """

    ledger_id: Optional[str] = None
    keeper: str = ""
    rows: Tuple[CostReport, ...] = ()
    total_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    account: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.ledger_id is not None:
            object.__setattr__(
                self, "ledger_id", normalize_member_id(self.ledger_id))
        object.__setattr__(
            self, "keeper", normalize_member_id(self.keeper))
        if self.keeper != SCRIBE_MEMBER:
            raise ValueError(
                "the ledger is kept by the Scribe - "
                f"{SCRIBE_MEMBER!r} - and by no one else")
        if isinstance(self.rows, (str, bytes)) \
                or not isinstance(self.rows, (list, tuple)):
            raise ValueError(
                f"a ledger's rows must be a list of reports, "
                f"got {self.rows!r}")
        rows = tuple(
            r if isinstance(r, CostReport) else validate_report(r)
            for r in self.rows)
        if not rows:
            raise ValueError("a ledger holds at least one row")
        seen = set()
        for row in rows:
            key = (row.slice_id, row.member)
            if key in seen:
                raise ValueError(
                    "a ledger holds one row per member per slice: "
                    f"{row.member!r} on {row.slice_id!r} stands twice")
            seen.add(key)
        object.__setattr__(self, "rows", rows)
        object.__setattr__(
            self, "total_calls",
            _check_count(self.total_calls, "a ledger's total calls"))
        object.__setattr__(
            self, "total_input_tokens",
            _check_count(
                self.total_input_tokens, "a ledger's total input tokens"))
        object.__setattr__(
            self, "total_output_tokens",
            _check_count(
                self.total_output_tokens,
                "a ledger's total output tokens"))
        object.__setattr__(
            self, "total_cost_usd", _check_cost(self.total_cost_usd))
        sums = (
            sum(r.calls for r in rows),
            sum(r.input_tokens for r in rows),
            sum(r.output_tokens for r in rows),
            round(sum(r.cost_usd for r in rows), 6))
        named = (
            self.total_calls, self.total_input_tokens,
            self.total_output_tokens, self.total_cost_usd)
        if named != sums:
            raise ValueError(
                "a ledger's totals must be its own rows' sums")
        object.__setattr__(
            self, "account", _check_account(self.account))

    def row_for(self, member: Any, slice_id: Any) -> CostReport:
        """The row one member and slice name in this ledger."""
        wanted_member = normalize_member_id(member)
        wanted_slice = normalize_slice_id(slice_id)
        for row in self.rows:
            if row.member == wanted_member \
                    and row.slice_id == wanted_slice:
                return row
        raise KeyError(
            f"no ledger row: {wanted_member!r} on {wanted_slice!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "cost_court_ledger",
            "slice": COST_COURT_SLICE,
            "ledger_id": self.ledger_id,
            "keeper": self.keeper,
            "rows": [r.to_record() for r in self.rows],
            "total_calls": self.total_calls,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": self.total_cost_usd,
            "account": list(self.account),
        }


def derive_ledger(source: Any) -> ScribeLedger:
    """Derive the Scribe's ledger from one book of run records.

    *source* is a CostBook, a CourtRegistry or a
    list of run records. The rows are the
    per-member-per-slice reports of those records,
    in the order the records first name each
    member-and-slice pair; the totals are the
    rows' sums and the account is read off the
    rows. Deriving is deterministic.
    """
    entries = _held_entries(source)
    if not entries:
        raise ValueError("a ledger needs at least one run record")
    pairs: list = []
    for entry in entries:
        key = (entry.slice_id, entry.member)
        if key not in pairs:
            pairs.append(key)
    rows = tuple(
        derive_report(entries, member, slice_id)
        for slice_id, member in pairs)
    total_calls = sum(r.calls for r in rows)
    total_input = sum(r.input_tokens for r in rows)
    total_output = sum(r.output_tokens for r in rows)
    total_cost = round(sum(r.cost_usd for r in rows), 6)
    return ScribeLedger(
        keeper=SCRIBE_MEMBER, rows=rows,
        total_calls=total_calls, total_input_tokens=total_input,
        total_output_tokens=total_output, total_cost_usd=total_cost,
        account=_ledger_account(
            rows, total_calls, total_input, total_output, total_cost))


def validate_ledger(ledger: Any, source: Any = None) -> ScribeLedger:
    """Validate one ledger into a ScribeLedger.

    Accepts a ScribeLedger or a mapping naming a
    ``keeper`` (or ``scribe``), its ``rows`` (or
    ``reports``), totals (``total_calls``,
    ``total_input_tokens``, ``total_output_tokens``
    and ``total_cost_usd``, each with its shorter
    spellings), an ``account`` (or ``statements``)
    and an optional ``ledger_id`` (or ``id``).
    Every row is read as a report; with *source*
    given, the ledger is judged against the
    ledger derived from the source's records: a
    stored ledger whose rows, totals or account
    disagree with the derived ledger refuses,
    because a ledger is derived, never stored
    loose. A stored ledger naming no account of
    its own refuses, for the same reason.
    """
    if isinstance(ledger, ScribeLedger):
        current = ledger
    elif isinstance(ledger, dict):
        unknown = set(ledger) - _LEDGER_KEYS
        if unknown:
            raise ValueError(
                "unknown ledger keys: %s" % ", ".join(sorted(unknown)))
        keeper = _pick_any(ledger, ("keeper", "scribe"), "keepers")
        if keeper is None:
            raise ValueError("a ledger is missing its keeper")
        rows = _pick_any(ledger, ("rows", "reports"), "row lists")
        if rows is None:
            raise ValueError("a ledger is missing its rows")
        total_calls = _pick_any(
            ledger, ("total_calls", "calls"), "total call counts")
        if total_calls is None:
            raise ValueError("a ledger is missing its total calls")
        total_input = _pick_any(
            ledger, ("total_input_tokens", "input_tokens"),
            "total input tokens")
        if total_input is None:
            raise ValueError("a ledger is missing its total input tokens")
        total_output = _pick_any(
            ledger, ("total_output_tokens", "output_tokens"),
            "total output tokens")
        if total_output is None:
            raise ValueError(
                "a ledger is missing its total output tokens")
        total_cost = _pick_any(
            ledger, ("total_cost_usd", "total_cost", "cost", "cost_usd"),
            "total costs")
        if total_cost is None:
            raise ValueError("a ledger is missing its total cost")
        account = _pick_any(
            ledger, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError(
                "a stored ledger names no account of its own - "
                "derive it from its run records")
        ledger_id = _pick_any(ledger, ("ledger_id", "id"), "ledger ids")
        current = ScribeLedger(
            ledger_id=ledger_id, keeper=keeper, rows=rows,
            total_calls=total_calls, total_input_tokens=total_input,
            total_output_tokens=total_output, total_cost_usd=total_cost,
            account=account)
    else:
        raise ValueError(f"a ledger must be a mapping, got {ledger!r}")
    if source is not None:
        entries = _held_entries(source)
        for row in current.rows:
            validate_report(row, entries)
        derived = derive_ledger(entries)
        judged = (
            current.keeper,
            tuple((r.member, r.slice_id) for r in current.rows),
            current.total_calls, current.total_input_tokens,
            current.total_output_tokens, current.total_cost_usd,
            current.account)
        expected = (
            derived.keeper,
            tuple((r.member, r.slice_id) for r in derived.rows),
            derived.total_calls, derived.total_input_tokens,
            derived.total_output_tokens, derived.total_cost_usd,
            derived.account)
        if judged != expected:
            raise ValueError(
                "a stored ledger disagrees with the ledger "
                "derived from its run records - a ledger is "
                "derived, never stored loose")
    return current


def build_ledger(ledger: Any = None, source: Any = None,
                 **kwargs: Any) -> ScribeLedger:
    """Build one validated ledger, from a mapping or field words."""
    if isinstance(ledger, ScribeLedger) and not kwargs:
        return validate_ledger(ledger, source)
    if isinstance(ledger, dict) or ledger is None:
        merged: Dict[str, Any] = {}
        if isinstance(ledger, dict):
            merged.update(ledger)
        merged.update(kwargs)
        return validate_ledger(merged, source)
    return validate_ledger(ledger, source)


# ---------------------------------------------------------------------
# The court book: run records in held order, ledgers judged.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class CostBook:
    """One cost court book: a run's records, held whole.

    ``entries`` are the run records, in held
    order; ``ledgers`` are Scribe ledgers of the
    book - derivations, judged against the book's
    records by :func:`validate_book`;
    ``court_note`` is the book's own note.
    """

    title: str = ""
    entries: Tuple[CostEntry, ...] = ()
    ledgers: Tuple[ScribeLedger, ...] = ()
    court_note: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book's title"))
        if isinstance(self.entries, (str, bytes)) \
                or not isinstance(self.entries, (list, tuple)):
            raise ValueError(
                f"a book's entries must be a list of run records, "
                f"got {self.entries!r}")
        entries = tuple(_check_entry_ref(e) for e in self.entries)
        if not entries:
            raise ValueError("a court book holds at least one run record")
        seen = set()
        for entry in entries:
            if entry.entry_id is not None:
                if entry.entry_id in seen:
                    raise ValueError(
                        f"a run record named {entry.entry_id!r} "
                        f"already exists")
                seen.add(entry.entry_id)
        object.__setattr__(self, "entries", entries)
        if isinstance(self.ledgers, (str, bytes)) \
                or not isinstance(self.ledgers, (list, tuple)):
            raise ValueError(
                f"a book's ledgers must be a list of ledgers, "
                f"got {self.ledgers!r}")
        ledgers = tuple(
            led if isinstance(led, ScribeLedger)
            else validate_ledger(led)
            for led in self.ledgers)
        seen_ledgers = set()
        for ledger in ledgers:
            if ledger.ledger_id is not None:
                if ledger.ledger_id in seen_ledgers:
                    raise ValueError(
                        f"a ledger named {ledger.ledger_id!r} "
                        f"already exists")
                seen_ledgers.add(ledger.ledger_id)
        object.__setattr__(self, "ledgers", ledgers)
        if not isinstance(self.court_note, str):
            raise ValueError("a book's note must be text")
        object.__setattr__(self, "court_note", self.court_note.strip())

    def entry_for(self, entry_id: Any) -> CostEntry:
        """The run record one id names in this book."""
        wanted = normalize_member_id(entry_id)
        for entry in self.entries:
            if entry.entry_id == wanted:
                return entry
        raise KeyError(f"no run record in the book: {wanted!r}")

    def entries_for(self, member: Any) -> Tuple[CostEntry, ...]:
        """Every run record one member filed, in held order."""
        wanted = normalize_member_id(member)
        return tuple(e for e in self.entries if e.member == wanted)

    def entries_on(self, slice_id: Any) -> Tuple[CostEntry, ...]:
        """Every run record one slice names, in held order."""
        wanted = normalize_slice_id(slice_id)
        return tuple(e for e in self.entries if e.slice_id == wanted)

    def ledger_for(self, ledger_id: Any) -> ScribeLedger:
        """The ledger one id names in this book."""
        wanted = normalize_member_id(ledger_id)
        for ledger in self.ledgers:
            if ledger.ledger_id == wanted:
                return ledger
        raise KeyError(f"no ledger in the book: {wanted!r}")

    def entry_ids(self) -> Tuple[str, ...]:
        """Every held entry id, in held order."""
        return tuple(e.entry_id for e in self.entries if e.entry_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "cost_court_book",
            "slice": COST_COURT_SLICE,
            "title": self.title,
            "entry_ids": list(self.entry_ids()),
            "entry_count": len(self.entries),
            "ledger_count": len(self.ledgers),
        }


def validate_book(data: Any, *, require_example: bool = False) -> CostBook:
    """Validate one court mapping into a CostBook.

    The mapping names a ``schema`` (the court
    schema word), a ``guide`` mapping (its
    ``title``), an ``entries`` list and an
    optional ``ledgers`` list. Every record stands
    on its own validation, then the whole is
    judged: entry ids unique, and every ledger
    judged against the book's own run records.
    With ``require_example`` the shipped example
    is held to its pinned shape: the pinned title,
    entries and ledger, the ledger's pinned rows,
    totals and account word-for-word, and the
    first report's pinned account. Problems raise
    :class:`ValidationError` or ``ValueError``.
    """
    if isinstance(data, CostBook):
        return data
    if not isinstance(data, dict):
        raise ValidationError(
            f"a court book must be a mapping, got {data!r}")
    unknown = set(data) - _COURT_KEYS
    if unknown:
        raise ValidationError(
            "unknown court keys: %s" % ", ".join(sorted(unknown)))
    if data.get("schema") != COST_COURT_SCHEMA:
        raise ValidationError(
            f"a court book must carry schema "
            f"{COST_COURT_SCHEMA!r}, got {data.get('schema')!r}")
    if "entries" not in data:
        raise ValidationError("a court book is missing its entries")
    if not isinstance(data["entries"], (list, tuple)):
        raise ValidationError("a court book's entries must be a list")
    if data.get("ledgers") is not None \
            and not isinstance(data["ledgers"], (list, tuple)):
        raise ValidationError("a court book's ledgers must be a list")
    head = data.get("guide") or {}
    if not isinstance(head, dict):
        raise ValidationError("a court book's guide must be a mapping")
    unknown_head = set(head) - _BOOK_KEYS
    if unknown_head:
        raise ValidationError(
            "unknown guide keys: %s" % ", ".join(sorted(unknown_head)))
    try:
        title = _pick_any(head, ("title", "name"), "titles")
        if title is None:
            raise ValidationError("a court book is missing its title")
        note = data.get("court_note") or ""
        if not isinstance(note, str):
            raise ValidationError("a court book's note must be text")
        book = CostBook(
            title=title, entries=tuple(data["entries"]),
            ledgers=tuple(data.get("ledgers") or ()),
            court_note=note)
        for ledger in book.ledgers:
            validate_ledger(ledger, book.entries)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    if require_example:
        if book.title != _EXAMPLE_TITLE:
            raise ValidationError(
                "the shipped example court book's title is "
                "not the pinned title")
        if book.entry_ids() != _EXAMPLE_ENTRY_IDS:
            raise ValidationError(
                "the shipped example's run records are not "
                "the pinned records")
        ledger = book.ledger_for(_EXAMPLE_LEDGER_ID)
        if ledger.keeper != SCRIBE_MEMBER:
            raise ValidationError(
                "the shipped example ledger is not kept "
                "by the Scribe")
        if tuple((r.slice_id, r.member) for r in ledger.rows) != (
                _EXAMPLE_LEDGER_ROWS):
            raise ValidationError(
                "the shipped example ledger does not name "
                "its pinned rows")
        totals = (
            ledger.total_calls, ledger.total_input_tokens,
            ledger.total_output_tokens, ledger.total_cost_usd)
        if totals != _EXAMPLE_LEDGER_TOTALS:
            raise ValidationError(
                "the shipped example ledger does not carry "
                "its pinned totals")
        if ledger.account != _EXAMPLE_LEDGER_ACCOUNT:
            raise ValidationError(
                "the shipped example ledger does not carry "
                "its pinned account word-for-word")
        first = derive_report(
            book.entries, "forge_worker", "M-139")
        if first.account != _EXAMPLE_FIRST_REPORT_ACCOUNT:
            raise ValidationError(
                "the shipped example's first report does not "
                "carry its pinned account word-for-word")
    return book


def build_book(book: Any = None, **kwargs: Any) -> CostBook:
    """Build one validated book, from a mapping or field words."""
    if isinstance(book, CostBook) and not kwargs:
        return book
    if isinstance(book, dict):
        if "entries" in book or "schema" in book:
            return validate_book(book)
        merged: Dict[str, Any] = dict(book)
        merged.update(kwargs)
        return CostBook(**merged)
    if book is None:
        return CostBook(**kwargs)
    raise ValueError(f"a court book is needed, got {book!r}")


def _book_from(data: Any, *, require_example: bool) -> CostBook:
    try:
        return validate_book(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_cost_court(
        data: Optional[Dict[str, Any]] = None) -> CostBook:
    """Load and validate the shipped example book (or *data*).

    The shipped file is held to the example check:
    the pinned title, run records and ledger - the
    M-139 boundary run priced per member per slice
    and the Scribe's ledger of it - so the shipped
    book covers the boundary this slice exists to
    hold.
    """
    raw = data if data is not None else load_resource(
        COST_COURT_RESOURCE)
    return _book_from(raw, require_example=True)


def load_cost_court_file(path: Any) -> CostBook:
    """Load and validate a court book from a file at *path*.

    Any file in the court shape, anywhere on
    disk, validated whole - a malformed file raises
    :class:`ValidationError` naming the problem,
    and a missing file raises ``FileNotFoundError``.
    The example check is not held: a real court
    book stands on its own records.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _book_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The registry model: one book held record by record, in held order.
# ---------------------------------------------------------------------


class CourtRegistry:
    """One session's court book, held record by record.

    The registry holds run records, never reports
    or ledgers: both are derivations, read off held
    records at call time, so nothing here can hold
    a total stale.
    """

    def __init__(self, book: Any = None) -> None:
        self._title: Optional[str] = None
        self._entries: Dict[str, CostEntry] = {}
        self._order: list = []
        self._next_entry = 1
        if book is not None:
            self.register_book(book)

    def _fresh_entry_id(self, held_ids: Any) -> str:
        while f"court-{self._next_entry}" in held_ids:
            self._next_entry += 1
        fresh = f"court-{self._next_entry}"
        self._next_entry += 1
        return fresh

    def register_entry(self, entry: Any) -> CostEntry:
        """Register one run record into the held book.

        A record with no id is given a deterministic
        ``court-N`` id. A record id already standing
        here refuses.
        """
        validated = build_entry(entry)
        held_ids = set(self._entries)
        if validated.entry_id is not None \
                and validated.entry_id in held_ids:
            raise ValueError(
                f"a run record named {validated.entry_id!r} "
                f"already exists")
        if validated.entry_id is None:
            validated = replace(
                validated, entry_id=self._fresh_entry_id(held_ids))
        self._entries[validated.entry_id] = validated
        self._order.append(validated.entry_id)
        return validated

    def register_book(self, book: Any) -> CostBook:
        """Register every run record of one book, in order.

        The first book held sets the title; a later
        book under a different title refuses, as
        does a book naming a held record id. The
        book's ledgers are derivations, not
        holdings, and are not held.
        """
        validated = build_book(book)
        if self._title is not None and validated.title != self._title:
            raise ValueError(
                "this registry already holds a court book "
                "under a different title")
        for entry in validated.entries:
            if entry.entry_id in self._entries:
                raise ValueError(
                    f"a run record named {entry.entry_id!r} "
                    f"already exists")
        self._title = validated.title
        for entry in validated.entries:
            self.register_entry(entry)
        return self.book()

    def get_entry(self, entry_id: Any) -> CostEntry:
        """The run record one id names among the held records."""
        wanted = normalize_member_id(entry_id)
        if wanted not in self._entries:
            raise KeyError(f"unknown run record: {wanted!r}")
        return self._entries[wanted]

    def list_entries(self) -> Tuple[CostEntry, ...]:
        """Every held run record, in the order they were held."""
        return tuple(self._entries[e] for e in self._order)

    def book(self) -> CostBook:
        """The held run records as one validated book."""
        if self._title is None:
            raise ValueError("no court book is held yet")
        return CostBook(
            title=self._title, entries=self.list_entries())

    def report_for(self, member: Any, slice_id: Any) -> CostReport:
        """Derive one member's report on one slice, at call time.

        The report is derived from the held records
        naming the member and slice, read at call
        time - the registry holds records, and this
        report is derived from them.
        """
        return derive_report(self.list_entries(), member, slice_id)

    def ledger(self) -> ScribeLedger:
        """Derive the Scribe's ledger of the held book, at call time.

        The rows and account are the held records'
        own sums, read at call time.
        """
        return derive_ledger(self.list_entries())


# ---------------------------------------------------------------------
# Court news, shaped as session records.
# ---------------------------------------------------------------------


def entry_record(entry: Any) -> Dict[str, Any]:
    """The session-news record of one run record."""
    current = entry if isinstance(entry, CostEntry) \
        else build_entry(entry)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.member} ran {current.model} on "
        f"{current.slice_id}: ${current.cost_usd:.6f}.")
    return record


def report_record(report: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one per-member-per-slice report.

    With *source* given, the report is first
    judged against the records it belongs to.
    """
    current = validate_report(report, source)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.member} spent ${current.cost_usd:.6f} "
        f"on {current.slice_id} across {current.calls} "
        f"call(s).")
    return record


def ledger_record(ledger: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of the Scribe's ledger.

    With *source* given, the ledger is first
    judged against the records it belongs to.
    """
    current = validate_ledger(ledger, source)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"The Scribe's ledger: ${current.total_cost_usd:.6f} "
        f"across {len(current.rows)} row(s).")
    return record


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one court book."""
    current = book if isinstance(book, CostBook) else build_book(book)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Cost court book {current.title}: "
        f"{record['entry_count']} run record(s), "
        f"{record['ledger_count']} ledger(s).")
    return record


def plain_words(entry: Any) -> str:
    """One run record, in one plain sentence."""
    current = entry if isinstance(entry, CostEntry) \
        else build_entry(entry)
    priced = "priced" if current.priced else "unpriced"
    return (
        f"{current.member} ran {current.model} on "
        f"{current.slice_id}: {current.input_tokens} in / "
        f"{current.output_tokens} out tokens, "
        f"${current.cost_usd:.6f} ({priced}).")


def report_plain_words(source: Any) -> str:
    """Reports in plain words: every report, in full.

    Accepts a CostReport or a CostBook. Each
    report is told whole - its member, its slice
    and its account.
    """
    if isinstance(source, CostReport):
        reports = (validate_report(source),)
        title = None
    elif isinstance(source, CostBook):
        reports = tuple(
            derive_report(
                source.entries, member, slice_id)
            for slice_id, member in _book_pairs(source))
        title = source.title
    else:
        raise ValueError(f"a court source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    for report in reports:
        lines.append(
            f"{report.member} on {report.slice_id} - "
            f"${report.cost_usd:.6f}")
        lines.extend(report.account)
    return "\n".join(lines)


def _book_pairs(book: CostBook) -> Tuple[Tuple[str, str], ...]:
    pairs: list = []
    for entry in book.entries:
        key = (entry.slice_id, entry.member)
        if key not in pairs:
            pairs.append(key)
    return tuple(pairs)


def ledger_plain_words(source: Any) -> str:
    """The Scribe's ledger in plain words, in full.

    Accepts a ScribeLedger or a CostBook. The
    ledger is told whole - its keeper, its rows
    and its account.
    """
    if isinstance(source, ScribeLedger):
        ledger = validate_ledger(source)
        title = None
    elif isinstance(source, CostBook):
        ledger = derive_ledger(source.entries)
        title = source.title
    else:
        raise ValueError(f"a court source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append(f"Ledger kept by {ledger.keeper}:")
    for row in ledger.rows:
        lines.append(
            f"{row.member} on {row.slice_id} - "
            f"${row.cost_usd:.6f} ({row.calls} call(s))")
    lines.extend(ledger.account)
    return "\n".join(lines)


# ---------------------------------------------------------------------
# Screens: the formatters and the shared /costcourt grammar.
# ---------------------------------------------------------------------


def _source_book(source: Any) -> CostBook:
    if source is None:
        return load_cost_court()
    if isinstance(source, CourtRegistry):
        return source.book()
    if isinstance(source, CostBook):
        return source
    raise ValueError(f"a court book is needed, got {source!r}")


def format_entry(entry: Any) -> str:
    """One run record as a screen line."""
    current = entry if isinstance(entry, CostEntry) \
        else build_entry(entry)
    return (
        f"{current.entry_id or '-'}: {current.member} "
        f"{current.model} ({current.slice_id}) "
        f"${current.cost_usd:.6f}")


def format_entries(source: Any = None, member: Any = None) -> str:
    """Run records of one book, in held order.

    With *member* given, only that member's
    records are shown.
    """
    book = _source_book(source)
    entries = book.entries if member is None else book.entries_for(member)
    lines = [format_entry(entry) for entry in entries]
    if not lines:
        lines.append("No run records are held.")
    return "\n".join(lines)


def format_report(source: Any = None) -> str:
    """Reports as screen blocks: member and slice over derived account.

    Accepts a CostReport or a CostBook; a book
    shows every report it derives, in book order.
    """
    if isinstance(source, CostReport):
        reports = (validate_report(source),)
        lines: list = []
    else:
        book = _source_book(source)
        reports = tuple(
            derive_report(book.entries, member, slice_id)
            for slice_id, member in _book_pairs(book))
        lines = [f"Reports in {book.title}:"]
    for report in reports:
        lines.append(
            f"{report.member} on {report.slice_id} - "
            f"${report.cost_usd:.6f} ({report.calls} call(s))")
        lines.extend(report.account)
    if isinstance(source, CostReport):
        return "\n".join(lines)
    if len(lines) == 1:
        lines.append("Nothing here.")
    return "\n".join(lines)


def format_ledger(source: Any = None) -> str:
    """The Scribe's ledger as a screen block.

    Accepts a ScribeLedger or a CostBook; a book
    shows the ledger it derives, its rows over
    its derived account.
    """
    if isinstance(source, ScribeLedger):
        ledger = validate_ledger(source)
        lines: list = []
    else:
        book = _source_book(source)
        ledger = derive_ledger(book.entries)
        lines = [f"Ledger in {book.title}:"]
    lines.append(f"Kept by {ledger.keeper}:")
    for row in ledger.rows:
        lines.append(
            f"{row.member} on {row.slice_id} - "
            f"${row.cost_usd:.6f} ({row.calls} call(s))")
    lines.extend(ledger.account)
    return "\n".join(lines)


def format_cost_court_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /costcourt.

    With nothing named, the shipped example
    court book is shown - the example this
    slice ships - so the screen is never empty.
    """
    book = _source_book(source)
    lines = ["Cost court (M-140) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_entries(book))
    lines.append("")
    lines.append(format_report(book))
    lines.append("")
    lines.append(format_ledger(book))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_cost_court_args(args: Any) -> Tuple[str, Optional[str]]:
    """Parse the /costcourt grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    court book; ``entry <entry-id>`` shows one run
    record; ``member <member-id>`` shows one
    member's records; ``slice <slice-id>`` shows
    one slice's records; ``ledger`` shows the
    Scribe's ledger. Anything else is a usage
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
    if head == "ledger" and len(words) == 1:
        return ("ledger", None)
    if head in ("entry", "member") and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "slice" and len(words) == 2:
        try:
            return (head, normalize_slice_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
