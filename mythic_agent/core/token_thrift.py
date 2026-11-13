"""Token thrift (All-Features roadmap slice M-160).

Part VII continues. The roadmap's words:
``diff-first reading, map-first loading, and
hash-anchored edits measured as a cost line in
'mythic costs' - thrift is a reported virtue.``

What already ships, and what this slice adds:

* Tokens are already counted and priced in this
  repo, on shipped roads: the costs ledger
  (``core/costs.py``) records token usage per model
  and prices it against the shared rate table, the
  cost court (``core/cost_court.py``, M-140) holds
  run records as data and derives their cost from
  that same table, and the context budget
  (``core/context_budget.py``, M-147) makes what is
  in the context - and its token count - visible as
  data. Pinning and protection
  (``core/pinning_protection.py``, M-159) stands
  beside them, and the compaction glass-box
  (``core/compaction_glassbox.py``, M-151) holds
  every compaction as shown, editable data. What
  none of those layers holds is the thrift record
  itself: the declaration, as data, that one read,
  load or edit was taken by a cheaper road - and
  what it saved, measured against the plain road.
* This slice is that declaration, as a pure layer:
  a thrift record is one read, load or edit taken
  by one of the three thrift roads (diff-first
  reading, map-first loading, hash-anchored edits),
  validated as data WITH ITS PROVENANCE WHOLE -
  what was read, loaded or edited, the thrift road
  used, the reference it stands under, the baseline
  measure (what the plain road would have cost, in
  tokens) against the actual measure (what the
  thrift road cost), who recorded it, the day, and
  where it was read from - composed BY IMPORT from
  the shipped holdings it measures (a cost-court
  run record, a context-budget item, a pin, a
  compaction record), each judged by its own
  layer's validation. The shipped data file
  (``mythic_agent/data/token_thrift.yaml``) holds
  one example book in exactly the shape a real book
  file takes, a loader reads a book file anywhere
  on disk, the thrift panel is DERIVED from the
  whole book (every record carried whole, in a
  settled order - thrift is a reported virtue, so
  the panel is the visible surface of what thrift
  saved), a thrift COST LINE is derived for the
  panel's totals priced through the shared rate
  table - the line ``mythic costs`` reports -
  records are shaped as session news, and a small
  in-memory registry model holds records one by
  one. The agent layer owns holding a book for a
  session and reading the session's context onto
  thrift records.

Honesty rules, enforced here and pinned by tests:

* **Thrift is a reported virtue.** Every record a
  book holds stands whole on the derived panel -
  its subject, its road, the tokens it saved, who
  recorded it and the day - in settled order, so
  what thrift saved is never hidden, partial or
  stale: the panel is read off the book at call
  time, and a stored panel whose rows, totals,
  counts or account disagree with the derived one
  refuses.
* **Measured, never claimed.** A thrift record
  names BOTH measures - the baseline and the
  actual - and the saving is derived from them,
  never stored loose: a record whose actual
  measure exceeds its baseline refuses, because
  thrift that costs more than the plain road is
  no thrift, and a record naming no baseline
  refuses, because an unmeasured saving is a
  claim, not a measure. The cost line prices the
  panel's own totals through the shared rate
  table by import: a model the table does not
  know prices at zero and says so, exactly as the
  costs ledger itself bills it.
* **Composed, never duplicated.** A record that
  measures a shipped holding's piece is that
  piece read onto this layer by import and judged
  by its own layer's validation, by reference and
  measure alone: its own words never cross.
* **Data only.** This layer holds thrift as data:
  it reads no file itself beyond its own book
  files, edits no code, calls no model, intercepts
  no live read, load or edit, and persists
  nothing. The cost line is a derivation for
  reporting - it does not itself change what any
  live road spends.
"""

from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .compaction_glassbox import CompactionRecord
from .compaction_glassbox import validate_record as _validate_compaction
from .context_budget import ContextItem
from .context_budget import validate_item as _validate_context_item
from .cost_court import CostEntry
from .cost_court import validate_entry as _validate_cost_entry
from .costs import price as _shared_price
from .crew_members import normalize_member_id
from .pinning_protection import Pin
from .pinning_protection import validate_pin as _validate_pin
from .validation import ValidationError

__all__ = [
    "TOKEN_THRIFT_RESOURCE",
    "TOKEN_THRIFT_SCHEMA",
    "TOKEN_THRIFT_SLICE",
    "THRIFT_ROADS",
    "PLAIN_EXPLANATION",
    "USAGE",
    "ThriftBook",
    "ThriftCostLine",
    "ThriftPanel",
    "ThriftPanelRow",
    "ThriftRecord",
    "ThriftRegistry",
    "ThriftRoadCount",
    "book_record",
    "build_book",
    "build_cost_line",
    "build_panel",
    "build_record",
    "build_row",
    "cost_line_plain_words",
    "cost_line_record",
    "derive_cost_line",
    "derive_panel",
    "format_cost_line",
    "format_panel",
    "format_thrift_record",
    "format_thrift_records",
    "format_token_thrift_screen",
    "inspect_thrift_source",
    "load_token_thrift",
    "load_token_thrift_file",
    "normalize_thrift_road",
    "panel_plain_words",
    "panel_record",
    "parse_thrift_args",
    "plain_words",
    "thrift_from_compaction_record",
    "thrift_from_context_item",
    "thrift_from_cost_entry",
    "thrift_from_pin",
    "thrift_record",
    "thrift_records_from_context",
    "thrift_refs",
    "total_saved",
    "validate_book",
    "validate_cost_line",
    "validate_panel",
    "validate_record",
    "validate_row",
]

TOKEN_THRIFT_SLICE = "M-160"

#: The packaged data resource holding the example book.
TOKEN_THRIFT_RESOURCE = "token_thrift.yaml"

#: The schema word a token-thrift file must carry.
TOKEN_THRIFT_SCHEMA = "mythic.token_thrift/1"

#: The three thrift roads, in panel order: reading
#: a diff instead of the whole file (``diff-first``),
#: loading a map of a thing instead of the thing
#: (``map-first``), and editing against a hash anchor
#: instead of re-reading and rewriting whole
#: (``hash-anchored``) - the roadmap's own three
#: roads. No other road is counted thrifty here.
THRIFT_ROADS = (
    "diff-first", "map-first", "hash-anchored")

_ROAD_RANK = {road: rank for rank, road in enumerate(THRIFT_ROADS)}

_ROAD_ALIASES = {
    "diff-first": "diff-first",
    "diff": "diff-first",
    "diffs": "diff-first",
    "reading": "diff-first",
    "map-first": "map-first",
    "map": "map-first",
    "maps": "map-first",
    "loading": "map-first",
    "hash-anchored": "hash-anchored",
    "hash": "hash-anchored",
    "anchor": "hash-anchored",
    "anchored": "hash-anchored",
    "edit": "hash-anchored",
    "edits": "hash-anchored",
}

_RECORD_KEYS = frozenset({
    "record_id", "id", "subject", "title", "what",
    "road",
    "ref", "reference",
    "baseline_tokens", "baseline",
    "actual_tokens", "actual",
    "recorded_by", "by", "who",
    "recorded_on", "day", "date",
    "source",
})

_ROW_KEYS = frozenset({
    "record_id", "id", "subject", "road",
    "ref", "reference",
    "baseline_tokens", "baseline",
    "actual_tokens", "actual",
    "tokens_saved", "saved",
    "recorded_by", "recorded_on",
})

_ROAD_COUNT_KEYS = frozenset({
    "road", "records", "count", "saved_tokens", "saved"})

_PANEL_KEYS = frozenset({
    "panel_id", "id", "rows", "records",
    "total_records", "total",
    "total_baseline", "baseline",
    "total_actual", "actual",
    "total_saved", "saved",
    "road_counts", "roads",
    "account", "statements",
})

_COST_LINE_KEYS = frozenset({
    "model",
    "baseline_tokens", "baseline",
    "actual_tokens", "actual",
    "tokens_saved", "saved",
    "baseline_cost_usd", "baseline_cost",
    "actual_cost_usd", "actual_cost",
    "saved_cost_usd", "saved_cost",
    "priced",
})

_BOOK_KEYS = frozenset({"title", "name"})

_THRIFT_BOOK_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "canon_note", "guide", "records", "panels",
})

#: The shipped example book's title, held to this
#: by the loader's example check.
_EXAMPLE_TITLE = "Token thrift at the M-159 slice boundary"

#: The shipped example's record ids, in held order,
#: pinned by the loader.
_EXAMPLE_RECORD_IDS = (
    "thrift-diff-pinning", "thrift-map-context",
    "thrift-hash-edit", "thrift-diff-tests")

#: The shipped example's first record and the subject
#: it measures, pinned by the loader.
_EXAMPLE_FIRST_RECORD_ID = "thrift-diff-pinning"

_EXAMPLE_FIRST_RECORD_SUBJECT = (
    "mythic_agent/core/pinning_protection.py, "
    "read diff-first")

#: The shipped example's one panel id, and its rows
#: in panel order, pinned by the loader.
_EXAMPLE_PANEL_ID = "panel-m159-boundary"

_EXAMPLE_PANEL_ROW_IDS = (
    "thrift-diff-pinning", "thrift-diff-tests",
    "thrift-map-context", "thrift-hash-edit")

_EXAMPLE_PANEL_ACCOUNT = (
    "The thrift panel holds 4 records saving "
    "31460 of 38400 tokens: diff-first 21700, "
    "hash-anchored 2560, map-first 7200.",
    "Records stand by road - diff-first reading "
    "first, then map-first loading, then "
    "hash-anchored edits - then by subject, then "
    "record id, so two panels of one book diff "
    "cleanly, line by line.",
    "Every saving is measured: each record names "
    "its baseline and its actual, and the saving "
    "is read off the two, never claimed.",
    "The panel is read off the book at call time - "
    "it is derived, never stored loose.",
)

PLAIN_EXPLANATION = (
    "Token thrift: diff-first reading, map-first "
    "loading, and hash-anchored edits measured as a "
    "cost line in mythic costs - thrift is a "
    "reported virtue. A thrift record is one read, "
    "load or edit taken by a thrift road, carried "
    "with its provenance whole: what was read, "
    "loaded or edited, the road used, the baseline "
    "tokens the plain road would have cost, the "
    "actual tokens it cost, who recorded it, the "
    "day, and where it was read from. The thrift "
    "panel is derived from the book at call time: "
    "every record standing whole, by road, then "
    "subject, then record id, and the cost line "
    "prices its totals through the shared rate "
    "table. This layer holds thrift as data only: "
    "it reads no files itself, edits no code, "
    "calls no model, intercepts no live read and "
    "persists nothing."
)

USAGE = (
    "Usage: /thrift, /thrift show, "
    "/thrift record <record-id>, "
    "/thrift road <road>, "
    "/thrift panel, /thrift costs"
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


def _check_tokens(value: Any, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{what} must be a token count, got {value!r}")
    if value < 0 or value > 100_000_000_000:
        raise ValueError(
            f"{what} must be between 0 and 100000000000, "
            f"got {value!r}")
    return value


def _check_cost(value: Any, what: str = "a cost") -> float:
    if isinstance(value, bool) \
            or not isinstance(value, (int, float)):
        raise ValueError(f"{what} must be a number, got {value!r}")
    cost = round(float(value), 6)
    if cost < 0:
        raise ValueError(f"{what} must not be negative, got {value!r}")
    return cost


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


def _check_model(value: Any) -> str:
    text = _clean_text(value, "a model")
    if len(text) > 120 or any(
            ch not in "abcdefghijklmnopqrstuvwxyz"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.:/"
            for ch in text):
        raise ValueError(
            f"a model must be one word of letters, digits, "
            f"dashes, underscores, dots, slashes and colons, "
            f"got {value!r}")
    return text


def normalize_thrift_road(value: Any) -> str:
    """The canonical thrift road a word names.

    A road is one of :data:`THRIFT_ROADS` - the
    roadmap's own three cheaper roads - read
    case-insensitively, with their plain faces
    (``diff`` / ``reading``, ``map`` / ``loading``,
    ``hash`` / ``anchor`` / ``edit``) read onto them.
    Anything else raises, plainly naming the three.
    """
    if isinstance(value, str):
        wanted = _ROAD_ALIASES.get(value.strip().lower())
        if wanted is not None:
            return wanted
    raise ValueError(
        "a thrift road must be one of %s, got %r"
        % ("/".join(THRIFT_ROADS), value))


# ---------------------------------------------------------------------
# The thrift record: one cheaper read, load or edit, provenance whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ThriftRecord:
    """One read, load or edit taken by a thrift road, as data.

    ``subject`` is what was read, loaded or edited,
    in plain words; ``road`` is the thrift road used,
    one of the roadmap's own three; ``ref`` is the
    reference the measured thing stands under;
    ``baseline_tokens`` is what the plain road would
    have cost and ``actual_tokens`` what the thrift
    road cost - the saving is derived from the two,
    never stored. The provenance stands whole beside
    the record: ``recorded_by`` names who recorded
    it, ``recorded_on`` is the day, and ``source``
    names where it was read from. A record with any
    provenance word missing is no record at all, and
    a record whose actual measure exceeds its
    baseline is no thrift at all.
    """

    subject: str
    road: str
    ref: str
    baseline_tokens: int
    actual_tokens: int
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
        object.__setattr__(self, "road", normalize_thrift_road(self.road))
        object.__setattr__(
            self, "ref", _check_word(self.ref, "a record's reference"))
        object.__setattr__(
            self, "baseline_tokens",
            _check_tokens(self.baseline_tokens, "baseline tokens"))
        if self.baseline_tokens < 1:
            raise ValueError(
                "a thrift record must carry its baseline "
                "measure - an unmeasured saving is a claim, "
                "not a measure")
        object.__setattr__(
            self, "actual_tokens",
            _check_tokens(self.actual_tokens, "actual tokens"))
        if self.actual_tokens > self.baseline_tokens:
            raise ValueError(
                "a thrift record's actual tokens must not "
                "exceed its baseline tokens - thrift that "
                "costs more than the plain road is no thrift")
        object.__setattr__(
            self, "recorded_by",
            _check_title(self.recorded_by, "a record's recorder"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))
        object.__setattr__(
            self, "source",
            _check_title(self.source, "a record's source"))

    @property
    def tokens_saved(self) -> int:
        """Tokens this record saved, derived from its two measures."""
        return self.baseline_tokens - self.actual_tokens

    @property
    def savings_percent(self) -> float:
        """The saved share of the baseline, derived, one decimal."""
        return round(100.0 * self.tokens_saved / self.baseline_tokens, 1)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "token_thrift_record",
            "slice": TOKEN_THRIFT_SLICE,
            "record_id": self.record_id,
            "subject": self.subject,
            "road": self.road,
            "ref": self.ref,
            "baseline_tokens": self.baseline_tokens,
            "actual_tokens": self.actual_tokens,
            "tokens_saved": self.tokens_saved,
            "savings_percent": self.savings_percent,
            "recorded_by": self.recorded_by,
            "recorded_on": self.recorded_on,
            "source": self.source,
        }


def _check_record_ref(value: Any) -> ThriftRecord:
    if isinstance(value, ThriftRecord):
        return value
    if isinstance(value, dict):
        return validate_record(value)
    raise ValueError(f"a thrift record is needed, got {value!r}")


def validate_record(record: Any) -> ThriftRecord:
    """Validate one thrift record into a ThriftRecord.

    Accepts a record or a mapping naming a ``subject``
    (or ``title`` / ``what``), a ``road``, a ``ref``
    (or ``reference``), ``baseline_tokens`` (or
    ``baseline``), ``actual_tokens`` (or ``actual``),
    a ``recorded_by`` (or ``by`` / ``who``), a
    ``recorded_on`` (or ``day`` / ``date``), a
    ``source`` and an optional ``record_id`` (or
    ``id``). Naming two spellings of one field with
    different values refuses, and unknown keys
    refuse - a stored saving among them, because a
    saving is derived, never stored.
    """
    if isinstance(record, ThriftRecord):
        return record
    if not isinstance(record, dict):
        raise ValueError(f"a thrift record must be a mapping, got {record!r}")
    unknown = set(record) - _RECORD_KEYS
    if unknown:
        raise ValueError(
            "unknown thrift-record keys: %s" % ", ".join(sorted(unknown)))

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(record, spellings, what)
        if value is None:
            raise ValueError(f"a thrift record is missing its {what}")
        return value

    kwargs: Dict[str, Any] = {
        "subject": _needed(("subject", "title", "what"), "subject"),
        "road": _needed(("road",), "road"),
        "ref": _needed(("ref", "reference"), "reference"),
        "baseline_tokens": _needed(
            ("baseline_tokens", "baseline"), "baseline measure"),
        "actual_tokens": _needed(
            ("actual_tokens", "actual"), "actual measure"),
        "recorded_by": _needed(("recorded_by", "by", "who"), "recorder"),
        "recorded_on": _needed(
            ("recorded_on", "day", "date"), "recorded-on day"),
        "source": _needed(("source",), "source"),
    }
    named_id = _pick_any(record, ("record_id", "id"), "record ids")
    if named_id is not None:
        kwargs["record_id"] = named_id
    return ThriftRecord(**kwargs)


def build_record(record: Any = None, **kwargs: Any) -> ThriftRecord:
    """Build one validated thrift record, from a mapping or field words."""
    if isinstance(record, ThriftRecord) and not kwargs:
        return record
    if isinstance(record, dict) or record is None:
        merged: Dict[str, Any] = {}
        if isinstance(record, dict):
            merged.update(record)
        merged.update(kwargs)
        return validate_record(merged)
    raise ValueError(f"a thrift record must be a mapping, got {record!r}")


def _thrift_for(road: str, ref: Optional[str], *, subject: Any,
                baseline_tokens: Any, actual_tokens: Any,
                recorded_by: Any, recorded_on: Any,
                source: Any) -> ThriftRecord:
    """One thrift record for one shipped piece, by road and reference.

    The piece's own words are never read here: only
    its road and the reference it stands under, and
    the measures named beside it. A record measured
    for no named baseline, or recorded by no one,
    refuses. A piece with no reference refuses: a
    record must name which standing thing it
    measured.
    """
    if baseline_tokens is None:
        raise ValueError(
            "a thrift record must carry its baseline "
            "measure: what the plain road would have "
            "cost - an unmeasured saving is a claim, "
            "not a measure")
    if actual_tokens is None:
        raise ValueError(
            "a thrift record must carry its actual "
            "measure: what the thrift road cost")
    if recorded_by is None:
        raise ValueError(
            "a thrift record must name who recorded "
            "it - a saving recorded by no one is no "
            "record")
    if ref is None or (isinstance(ref, str) and not ref.strip()):
        raise ValueError(
            "a thrift record names the reference the "
            "measured thing stood under - a thing with "
            "no reference cannot be measured, by road "
            "alone or otherwise")
    return ThriftRecord(
        subject=subject, road=road, ref=ref,
        baseline_tokens=baseline_tokens,
        actual_tokens=actual_tokens,
        recorded_by=recorded_by, recorded_on=recorded_on,
        source=source)


def inspect_thrift_source(piece: Any) -> Dict[str, Any]:
    """Inspect one shipped piece: its reference and actual measure only.

    The piece is judged by the layer that owns its
    type, never by whichever validator happens to
    accept its shape first - exactly as the sibling
    layers' inspection roads judge. Pieces whose own
    layer carries a token count (a cost-court run
    record, a context-budget item) report it as the
    actual measure; pieces carrying none (a pin, a
    compaction record) report ``None`` - their
    measures are named beside the reference at the
    composition seam. A piece with no reference, or
    a value no shipped layer owns, refuses.
    """
    if isinstance(piece, ThriftRecord):
        return {"ref": piece.ref, "actual_tokens": piece.actual_tokens}
    owned = (
        (CostEntry, _validate_cost_entry, "entry_id", True),
        (ContextItem, _validate_context_item, "item_id", True),
        (Pin, _validate_pin, "ref", False),
        (CompactionRecord, _validate_compaction, "record_id", False),
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
            actual = None
            if counted:
                if isinstance(validated, CostEntry):
                    actual = validated.input_tokens + validated.output_tokens
                else:
                    actual = validated.tokens
            return {"ref": ref, "actual_tokens": actual}
    if isinstance(piece, dict):
        if "baseline_tokens" in piece or "baseline" in piece:
            checked = validate_record(piece)
            return {"ref": checked.ref,
                    "actual_tokens": checked.actual_tokens}
        for kind_type, validator, attr, counted in owned:
            try:
                validated = validator(piece)
            except Exception:
                continue
            ref = getattr(validated, attr, None)
            if ref is None or (
                    isinstance(ref, str) and not ref.strip()):
                continue
            actual = None
            if counted:
                if isinstance(validated, CostEntry):
                    actual = validated.input_tokens + validated.output_tokens
                else:
                    actual = validated.tokens
            return {"ref": ref, "actual_tokens": actual}
    raise ValueError(
        f"no shipped layer owns this piece, got {piece!r}")


def thrift_from_cost_entry(entry: Any, *, road: Any,
                           baseline_tokens: Any, recorded_by: Any,
                           recorded_on: Any,
                           source: Any = "cost court",
                           subject: Any = None) -> ThriftRecord:
    """Build one thrift record from a shipped cost-court run record.

    The entry - the cost court's own record, judged
    by that layer's own validation - is read onto a
    thrift record BY IMPORT by its reference and
    measure alone: its id stands as the record's
    reference and its input and output tokens sum to
    the actual measure - what the run really cost.
    The baseline - what the plain road would have
    cost - is named beside it, as is the thrift road
    and who recorded it. The entry's member, slice
    and model are never read here.
    """
    validated = _validate_cost_entry(entry)
    return _thrift_for(
        normalize_thrift_road(road), validated.entry_id,
        subject=subject if subject is not None else (
            f"cost-court run {validated.entry_id}"),
        baseline_tokens=baseline_tokens,
        actual_tokens=validated.input_tokens + validated.output_tokens,
        recorded_by=recorded_by, recorded_on=recorded_on,
        source=source)


def thrift_from_context_item(item: Any, *, baseline_tokens: Any,
                             recorded_by: Any, recorded_on: Any,
                             road: Any = "map-first",
                             source: Any = "context budget",
                             subject: Any = None) -> ThriftRecord:
    """Build one thrift record from a shipped context-budget item.

    The item - the context budget's own record,
    judged by that layer's own validation - is read
    onto a thrift record BY IMPORT by its reference
    and measure alone: its id stands as the record's
    reference and its token count is the actual
    measure - what loading it cost. Map-first
    loading is its natural road. The baseline is
    named beside it. Its title, source and reason in
    the budget are never read here.
    """
    validated = _validate_context_item(item)
    return _thrift_for(
        normalize_thrift_road(road), validated.item_id,
        subject=subject if subject is not None else (
            f"context item {validated.item_id}"),
        baseline_tokens=baseline_tokens,
        actual_tokens=validated.tokens,
        recorded_by=recorded_by, recorded_on=recorded_on,
        source=source)


def thrift_from_pin(pin: Any, *, road: Any, baseline_tokens: Any,
                    actual_tokens: Any, recorded_by: Any,
                    recorded_on: Any,
                    source: Any = "pinning and protection",
                    subject: Any = None) -> ThriftRecord:
    """Build one thrift record from a shipped pin (M-159).

    The pin - pinning and protection's own record,
    judged by that layer's own validation - is read
    onto a thrift record BY IMPORT by its reference
    alone: the reference it protects stands as the
    record's reference. A pin carries no token count
    of its own, so both measures are named beside
    it. Its subject, reason and pinner are never read
    here.
    """
    validated = _validate_pin(pin)
    return _thrift_for(
        normalize_thrift_road(road), validated.ref,
        subject=subject if subject is not None else (
            f"pinned {validated.kind} {validated.ref}"),
        baseline_tokens=baseline_tokens,
        actual_tokens=actual_tokens,
        recorded_by=recorded_by, recorded_on=recorded_on,
        source=source)


def thrift_from_compaction_record(record: Any, *, road: Any,
                                  baseline_tokens: Any,
                                  actual_tokens: Any,
                                  recorded_by: Any,
                                  recorded_on: Any,
                                  source: Any = "compaction glass-box",
                                  subject: Any = None) -> ThriftRecord:
    """Build one thrift record from a shipped compaction record.

    The record - the glass-box's own record, judged
    by that layer's own validation - is read onto a
    thrift record BY IMPORT by its reference alone:
    its id stands as the record's reference. A
    compaction record carries no token count of its
    own here, so both measures are named beside it.
    Its title, summary and replaced material are
    never read here.
    """
    validated = _validate_compaction(record)
    return _thrift_for(
        normalize_thrift_road(road), validated.record_id,
        subject=subject if subject is not None else (
            f"compaction record {validated.record_id}"),
        baseline_tokens=baseline_tokens,
        actual_tokens=actual_tokens,
        recorded_by=recorded_by, recorded_on=recorded_on,
        source=source)


def _context_items(source: Any) -> Tuple[ContextItem, ...]:
    """The context items one source holds, judged by the budget."""
    from .context_budget import ContextBudgetPanel, ContextBudgetRegistry
    if isinstance(source, ContextBudgetPanel):
        return source.items
    if isinstance(source, ContextBudgetRegistry):
        return source.list_items()
    if isinstance(source, (list, tuple)):
        return tuple(_validate_context_item(item) for item in source)
    if isinstance(source, (ContextItem, dict)):
        return (_validate_context_item(source),)
    raise ValueError(f"context items are needed, got {source!r}")


def thrift_records_from_context(source: Any, *, baselines: Any,
                                recorded_by: Any, recorded_on: Any,
                                road: Any = "map-first"
                                ) -> Tuple[ThriftRecord, ...]:
    """Thrift records read off the shipped context budget.

    The items of a context panel - or of a whole
    context-budget registry - are read onto thrift
    records BY IMPORT, judged by the budget's own
    validation on the way, under one named road and
    one named recorder. Every item's baseline is
    named in *baselines*, a mapping of item id to
    baseline tokens: an item with no named baseline
    refuses the whole road before anything is built,
    because an unmeasured saving is a claim, not a
    measure. Every item's title, source and reason
    stay in the budget: only ids and counts cross.
    """
    if not isinstance(baselines, dict):
        raise ValueError(
            "baselines must be a mapping of item id to "
            "baseline tokens - an unmeasured saving is "
            "a claim, not a measure")
    items = _context_items(source)
    records = []
    for item in items:
        if item.item_id is None or item.item_id not in baselines:
            raise ValueError(
                f"no baseline is named for context item "
                f"{item.item_id!r} - an unmeasured saving "
                f"is a claim, not a measure")
        records.append(thrift_from_context_item(
            item, baseline_tokens=baselines[item.item_id],
            recorded_by=recorded_by, recorded_on=recorded_on,
            road=road))
    return tuple(records)


# ---------------------------------------------------------------------
# The thrift panel: every record carried whole, derived - reported virtue.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ThriftPanelRow:
    """One thrift record carried whole into the panel.

    ``record_id`` names the record; ``subject`` is
    what was read, loaded or edited; ``road`` is the
    thrift road used; ``ref`` is the reference it
    stands under; ``baseline_tokens`` /
    ``actual_tokens`` are its two measures and
    ``tokens_saved`` the saving derived from them;
    ``recorded_by`` and ``recorded_on`` are the
    record's provenance head. :func:`validate_row`
    judged against its record refuses a row whose
    fields disagree with the row they derive, and a
    row whose saving is not its measures' difference
    refuses at construction.
    """

    record_id: str
    subject: str
    road: str
    ref: str
    baseline_tokens: int
    actual_tokens: int
    tokens_saved: int
    recorded_by: str
    recorded_on: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "record_id", normalize_member_id(self.record_id))
        object.__setattr__(
            self, "subject",
            _check_title(self.subject, "a row's subject"))
        object.__setattr__(self, "road", normalize_thrift_road(self.road))
        object.__setattr__(
            self, "ref", _check_word(self.ref, "a row's reference"))
        object.__setattr__(
            self, "baseline_tokens",
            _check_tokens(self.baseline_tokens, "a row's baseline tokens"))
        object.__setattr__(
            self, "actual_tokens",
            _check_tokens(self.actual_tokens, "a row's actual tokens"))
        object.__setattr__(
            self, "tokens_saved",
            _check_tokens(self.tokens_saved, "a row's saved tokens"))
        if self.tokens_saved != self.baseline_tokens - self.actual_tokens:
            raise ValueError(
                "a row's saved tokens must be its own "
                "measures' difference - a saving is "
                "derived, never stored loose")
        object.__setattr__(
            self, "recorded_by",
            _check_title(self.recorded_by, "a row's recorder"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))

    @property
    def sort_key(self) -> Tuple[int, str, str]:
        """This row's place in panel order (derived).

        Rows stand by road - diff-first reading first,
        then map-first loading, then hash-anchored
        edits - then by subject, then record id.
        """
        return (_ROAD_RANK[self.road], self.subject.lower(), self.record_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "token_thrift_panel_row",
            "slice": TOKEN_THRIFT_SLICE,
            "record_id": self.record_id,
            "subject": self.subject,
            "road": self.road,
            "ref": self.ref,
            "baseline_tokens": self.baseline_tokens,
            "actual_tokens": self.actual_tokens,
            "tokens_saved": self.tokens_saved,
            "recorded_by": self.recorded_by,
            "recorded_on": self.recorded_on,
        }


def _row_for_record(record: ThriftRecord) -> ThriftPanelRow:
    return ThriftPanelRow(
        record_id=record.record_id, subject=record.subject,
        road=record.road, ref=record.ref,
        baseline_tokens=record.baseline_tokens,
        actual_tokens=record.actual_tokens,
        tokens_saved=record.tokens_saved,
        recorded_by=record.recorded_by,
        recorded_on=record.recorded_on)


def _check_row_ref(value: Any) -> ThriftPanelRow:
    if isinstance(value, ThriftPanelRow):
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

        return ThriftPanelRow(
            record_id=_needed(("record_id", "id"), "record id"),
            subject=_needed(("subject",), "subject"),
            road=_needed(("road",), "road"),
            ref=_needed(("ref", "reference"), "reference"),
            baseline_tokens=_needed(
                ("baseline_tokens", "baseline"), "baseline tokens"),
            actual_tokens=_needed(
                ("actual_tokens", "actual"), "actual tokens"),
            tokens_saved=_needed(
                ("tokens_saved", "saved"), "saved tokens"),
            recorded_by=_needed(("recorded_by",), "recorder"),
            recorded_on=_needed(("recorded_on",), "recorded-on day"))
    raise ValueError(f"a panel row is needed, got {value!r}")


def validate_row(row: Any, record: Any = None) -> ThriftPanelRow:
    """Validate one panel row into a ThriftPanelRow.

    Accepts a row or a mapping naming a ``record_id``
    (or ``id``), a ``subject``, a ``road``, a ``ref``
    (or ``reference``), ``baseline_tokens``,
    ``actual_tokens``, ``tokens_saved``, a
    ``recorded_by`` and a ``recorded_on``. With
    *record* given, the row is judged against the row
    derived from that record: a stored row whose
    fields disagree with the derived row refuses.
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
              **kwargs: Any) -> ThriftPanelRow:
    """Build one validated row, from a mapping or field words."""
    if isinstance(row, ThriftPanelRow) and not kwargs:
        return validate_row(row, record)
    if isinstance(row, dict) or row is None:
        merged: Dict[str, Any] = {}
        if isinstance(row, dict):
            merged.update(row)
        merged.update(kwargs)
        return validate_row(merged, record)
    return validate_row(row, record)


@dataclass(frozen=True)
class ThriftRoadCount:
    """One road's count in a panel: its records and saving tallied."""

    road: str
    records: int
    saved_tokens: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "road", normalize_thrift_road(self.road))
        object.__setattr__(
            self, "records",
            _check_count(self.records, "a road count's records"))
        object.__setattr__(
            self, "saved_tokens",
            _check_tokens(self.saved_tokens, "a road count's saved tokens"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "road": self.road,
            "records": self.records,
            "saved_tokens": self.saved_tokens,
        }


def _check_road_count_ref(value: Any) -> ThriftRoadCount:
    if isinstance(value, ThriftRoadCount):
        return value
    if isinstance(value, dict):
        unknown = set(value) - _ROAD_COUNT_KEYS
        if unknown:
            raise ValueError(
                "unknown road-count keys: %s"
                % ", ".join(sorted(unknown)))
        road = _pick_any(value, ("road",), "roads")
        if road is None:
            raise ValueError("a road count is missing its road")
        records = _pick_any(value, ("records", "count"), "records")
        if records is None:
            raise ValueError("a road count is missing its records")
        saved = _pick_any(value, ("saved_tokens", "saved"), "savings")
        if saved is None:
            raise ValueError("a road count is missing its saved tokens")
        return ThriftRoadCount(
            road=road, records=records, saved_tokens=saved)
    raise ValueError(f"a road count is needed, got {value!r}")


def _panel_account(total_records: int, total_baseline: int,
                   total_actual: int, total_saved: int,
                   road_counts: Tuple[ThriftRoadCount, ...]
                   ) -> Tuple[str, ...]:
    tallies = ", ".join(
        f"{count.road} {count.saved_tokens}"
        for count in sorted(
            road_counts, key=lambda count: count.road))
    return (
        f"The thrift panel holds {total_records} records "
        f"saving {total_saved} of {total_baseline} tokens: "
        f"{tallies}.",
        "Records stand by road - diff-first reading "
        "first, then map-first loading, then "
        "hash-anchored edits - then by subject, then "
        "record id, so two panels of one book diff "
        "cleanly, line by line.",
        "Every saving is measured: each record names "
        "its baseline and its actual, and the saving "
        "is read off the two, never claimed.",
        "The panel is read off the book at call time - "
        "it is derived, never stored loose.",
    )


@dataclass(frozen=True)
class ThriftPanel:
    """The thrift panel of one book, derived from the whole book.

    ``rows`` are the book's records carried whole, in
    panel order (by road, then subject, then record
    id, so two panels of one book diff cleanly);
    ``total_records`` is the rows' own count and
    ``total_baseline`` / ``total_actual`` /
    ``total_saved`` are the rows' own sums;
    ``road_counts`` are the per-road tallies of every
    record in the book, in the order their roads
    first appear in the panel; ``account`` is read
    off those numbers. A panel whose rows stand out
    of panel order, or whose totals are not its own
    rows' sums, refuses at construction;
    :func:`validate_panel` judged against a book
    refuses a stored panel that disagrees with the
    derived one.
    """

    rows: Tuple[ThriftPanelRow, ...] = ()
    total_records: int = 0
    total_baseline: int = 0
    total_actual: int = 0
    total_saved: int = 0
    road_counts: Tuple[ThriftRoadCount, ...] = ()
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
                "(by road, then subject, then record id)")
        object.__setattr__(self, "rows", rows)
        object.__setattr__(
            self, "total_records",
            _check_count(self.total_records, "a panel's total records"))
        if self.total_records != len(rows):
            raise ValueError(
                "a panel's total records must be its own "
                "rows' count")
        for field, what in (
                ("total_baseline", "total baseline"),
                ("total_actual", "total actual"),
                ("total_saved", "total saved")):
            object.__setattr__(
                self, field,
                _check_tokens(getattr(self, field), f"a panel's {what}"))
        if self.total_baseline != sum(r.baseline_tokens for r in rows):
            raise ValueError(
                "a panel's total baseline must be its own "
                "rows' sum")
        if self.total_actual != sum(r.actual_tokens for r in rows):
            raise ValueError(
                "a panel's total actual must be its own "
                "rows' sum")
        if self.total_saved != sum(r.tokens_saved for r in rows):
            raise ValueError(
                "a panel's total saved must be its own "
                "rows' sum")
        if self.total_saved != self.total_baseline - self.total_actual:
            raise ValueError(
                "a panel's total saved must be its own "
                "totals' difference")
        if isinstance(self.road_counts, (str, bytes)) \
                or not isinstance(self.road_counts, (list, tuple)):
            raise ValueError(
                f"a panel's road counts must be a list, "
                f"got {self.road_counts!r}")
        road_counts = tuple(
            _check_road_count_ref(c) for c in self.road_counts)
        seen_roads = set()
        for count in road_counts:
            if count.road in seen_roads:
                raise ValueError(
                    f"a road count named {count.road!r} "
                    f"already exists")
            seen_roads.add(count.road)
        object.__setattr__(self, "road_counts", road_counts)
        if sum(c.records for c in road_counts) != self.total_records:
            raise ValueError(
                "a panel's road counts must sum to its own "
                "total records")
        if sum(c.saved_tokens for c in road_counts) != self.total_saved:
            raise ValueError(
                "a panel's road counts must sum to its own "
                "total saved")
        tallies: Dict[str, Tuple[int, int]] = {}
        for row in rows:
            n, s = tallies.get(row.road, (0, 0))
            tallies[row.road] = (n + 1, s + row.tokens_saved)
        for count in road_counts:
            if (count.records, count.saved_tokens) != tallies.get(
                    count.road, (0, 0)):
                raise ValueError(
                    "a panel's road counts must be its own "
                    "rows' counts")
        if set(tallies) != {c.road for c in road_counts}:
            raise ValueError(
                "a panel's road counts must name every road "
                "its rows carry")
        object.__setattr__(self, "account", _check_account(self.account))

    def row_for(self, record_id: Any) -> ThriftPanelRow:
        """The panel row one record names in this panel."""
        wanted = normalize_member_id(record_id)
        for row in self.rows:
            if row.record_id == wanted:
                return row
        raise KeyError(f"no row in the panel: record {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "token_thrift_panel",
            "slice": TOKEN_THRIFT_SLICE,
            "panel_id": self.panel_id,
            "rows": [row.to_record() for row in self.rows],
            "total_records": self.total_records,
            "total_baseline": self.total_baseline,
            "total_actual": self.total_actual,
            "total_saved": self.total_saved,
            "road_counts": [c.to_record() for c in self.road_counts],
            "account": list(self.account),
        }


def _held_records(source: Any) -> Tuple[ThriftRecord, ...]:
    """The thrift records one source holds, in held order."""
    if isinstance(source, ThriftBook):
        return source.records
    if isinstance(source, ThriftRegistry):
        return source.list_records()
    if isinstance(source, (list, tuple)):
        return tuple(_check_record_ref(item) for item in source)
    raise ValueError(f"thrift records are needed, got {source!r}")


def derive_panel(source: Any) -> ThriftPanel:
    """Derive the thrift panel from one book.

    The rows are the book's records carried whole, in
    panel order: by road, then subject, then record
    id. *source* is a book or a registry. A source
    holding no record refuses - a panel of nothing is
    no panel.
    """
    records = _held_records(source)
    if not records:
        raise ValueError("a panel needs at least one thrift record")
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
        if row.road not in tally:
            tally[row.road] = (0, 0)
            order.append(row.road)
        n, s = tally[row.road]
        tally[row.road] = (n + 1, s + row.tokens_saved)
    road_counts = tuple(
        ThriftRoadCount(
            road=road, records=tally[road][0],
            saved_tokens=tally[road][1])
        for road in order)
    total_baseline = sum(r.baseline_tokens for r in rows)
    total_actual = sum(r.actual_tokens for r in rows)
    total_saved = sum(r.tokens_saved for r in rows)
    return ThriftPanel(
        rows=rows, total_records=len(rows),
        total_baseline=total_baseline, total_actual=total_actual,
        total_saved=total_saved, road_counts=road_counts,
        account=_panel_account(
            len(rows), total_baseline, total_actual,
            total_saved, road_counts))


def validate_panel(panel: Any, source: Any = None
                   ) -> ThriftPanel:
    """Validate one panel into a ThriftPanel.

    Accepts a panel or a mapping naming ``rows`` (or
    ``records``), a ``total_records`` (or ``total``),
    ``total_baseline``, ``total_actual``,
    ``total_saved``, ``road_counts`` (or ``roads``),
    an ``account`` (or ``statements``) and an optional
    ``panel_id`` (or ``id``). With *source* given (a
    book), the panel is judged against the panel
    derived from that book: a stored panel whose
    rows, totals, road counts or account disagree
    with the derived panel refuses. A panel naming no
    account refuses too.
    """
    if isinstance(panel, ThriftPanel):
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
        baseline = _pick_any(
            panel, ("total_baseline", "baseline"), "baselines")
        if baseline is None:
            raise ValueError("a panel is missing its total baseline")
        actual = _pick_any(panel, ("total_actual", "actual"), "actuals")
        if actual is None:
            raise ValueError("a panel is missing its total actual")
        saved = _pick_any(panel, ("total_saved", "saved"), "savings")
        if saved is None:
            raise ValueError("a panel is missing its total saved")
        road_counts = _pick_any(
            panel, ("road_counts", "roads"), "road counts")
        if road_counts is None:
            raise ValueError("a panel is missing its road counts")
        account = _pick_any(panel, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError("a panel names no account of its own")
        kwargs: Dict[str, Any] = {
            "rows": rows, "total_records": total,
            "total_baseline": baseline, "total_actual": actual,
            "total_saved": saved, "road_counts": road_counts,
            "account": account}
        panel_id = _pick_any(panel, ("panel_id", "id"), "panel ids")
        if panel_id is not None:
            kwargs["panel_id"] = panel_id
        current = ThriftPanel(**kwargs)
    else:
        raise ValueError(f"a panel must be a mapping, got {panel!r}")
    if source is not None:
        derived = derive_panel(source)
        if (current.rows != derived.rows
                or current.total_records != derived.total_records
                or current.total_baseline != derived.total_baseline
                or current.total_actual != derived.total_actual
                or current.total_saved != derived.total_saved
                or current.road_counts != derived.road_counts
                or current.account != derived.account):
            raise ValueError(
                "a stored panel disagrees with the panel "
                "derived from its book")
    return current


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> ThriftPanel:
    """Build one validated panel, from a mapping or field words."""
    if isinstance(panel, ThriftPanel) and not kwargs:
        return validate_panel(panel, source)
    if isinstance(panel, dict) or panel is None:
        merged: Dict[str, Any] = {}
        if isinstance(panel, dict):
            merged.update(panel)
        merged.update(kwargs)
        return validate_panel(merged, source)
    return validate_panel(panel, source)


# ---------------------------------------------------------------------
# The cost line: the panel's totals, priced - the mythic costs line.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ThriftCostLine:
    """One thrift cost line: a book's totals priced, as data.

    ``model`` names the model the line is priced
    for; ``baseline_tokens`` / ``actual_tokens`` /
    ``tokens_saved`` are the panel's own totals;
    ``baseline_cost_usd`` / ``actual_cost_usd`` /
    ``saved_cost_usd`` are those totals priced
    through the shared rate table - the saving is
    derived from the two priced totals, never stored
    loose; ``priced`` says whether the table knows
    the model (an unknown model prices at zero and
    says so, exactly as the costs ledger bills it).
    :func:`validate_cost_line` judged against a book
    refuses a stored line that disagrees with the
    line derived from that book.
    """

    model: str
    baseline_tokens: int
    actual_tokens: int
    tokens_saved: int
    baseline_cost_usd: float
    actual_cost_usd: float
    saved_cost_usd: float
    priced: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "model", _check_model(self.model))
        object.__setattr__(
            self, "baseline_tokens",
            _check_tokens(self.baseline_tokens, "a line's baseline tokens"))
        object.__setattr__(
            self, "actual_tokens",
            _check_tokens(self.actual_tokens, "a line's actual tokens"))
        object.__setattr__(
            self, "tokens_saved",
            _check_tokens(self.tokens_saved, "a line's saved tokens"))
        if self.tokens_saved != self.baseline_tokens - self.actual_tokens:
            raise ValueError(
                "a cost line's saved tokens must be its own "
                "totals' difference")
        object.__setattr__(
            self, "baseline_cost_usd",
            _check_cost(self.baseline_cost_usd, "a line's baseline cost"))
        object.__setattr__(
            self, "actual_cost_usd",
            _check_cost(self.actual_cost_usd, "a line's actual cost"))
        object.__setattr__(
            self, "saved_cost_usd",
            _check_cost(self.saved_cost_usd, "a line's saved cost"))
        if self.saved_cost_usd != round(
                self.baseline_cost_usd - self.actual_cost_usd, 6):
            raise ValueError(
                "a cost line's saved cost must be its own "
                "priced totals' difference")
        expected_cost, expected_priced = _shared_price(
            self.model, self.baseline_tokens, 0)
        if self.baseline_cost_usd != expected_cost \
                or self.priced != expected_priced:
            raise ValueError(
                "a cost line's baseline cost must be its own "
                "totals priced through the shared rate table")
        actual_cost, _ = _shared_price(self.model, self.actual_tokens, 0)
        if self.actual_cost_usd != actual_cost:
            raise ValueError(
                "a cost line's actual cost must be its own "
                "totals priced through the shared rate table")
        if not isinstance(self.priced, bool):
            raise ValueError("a cost line's priced flag must be a boolean")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "token_thrift_cost_line",
            "slice": TOKEN_THRIFT_SLICE,
            "model": self.model,
            "baseline_tokens": self.baseline_tokens,
            "actual_tokens": self.actual_tokens,
            "tokens_saved": self.tokens_saved,
            "baseline_cost_usd": self.baseline_cost_usd,
            "actual_cost_usd": self.actual_cost_usd,
            "saved_cost_usd": self.saved_cost_usd,
            "priced": self.priced,
        }


def derive_cost_line(source: Any, model: Any = "gpt-4o") -> ThriftCostLine:
    """Derive the thrift cost line of one book, for *model*.

    The line's token totals are the derived panel's
    own totals, and its costs are those totals priced
    through the shared rate table BY IMPORT - the
    same table the costs ledger and the cost court
    price through, so the line ``mythic costs``
    reports is the ledger's own arithmetic, never a
    second table. *source* is a book or a registry.
    """
    checked_model = _check_model(model)
    panel = derive_panel(source)
    baseline_cost, priced = _shared_price(
        checked_model, panel.total_baseline, 0)
    actual_cost, _ = _shared_price(checked_model, panel.total_actual, 0)
    return ThriftCostLine(
        model=checked_model,
        baseline_tokens=panel.total_baseline,
        actual_tokens=panel.total_actual,
        tokens_saved=panel.total_saved,
        baseline_cost_usd=baseline_cost,
        actual_cost_usd=actual_cost,
        saved_cost_usd=round(baseline_cost - actual_cost, 6),
        priced=priced)


def _check_cost_line_ref(value: Any) -> ThriftCostLine:
    if isinstance(value, ThriftCostLine):
        return value
    if isinstance(value, dict):
        unknown = set(value) - _COST_LINE_KEYS
        if unknown:
            raise ValueError(
                "unknown cost-line keys: %s" % ", ".join(sorted(unknown)))

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            picked = _pick_any(value, spellings, what)
            if picked is None:
                raise ValueError(f"a cost line is missing its {what}")
            return picked

        return ThriftCostLine(
            model=_needed(("model",), "model"),
            baseline_tokens=_needed(
                ("baseline_tokens", "baseline"), "baseline tokens"),
            actual_tokens=_needed(
                ("actual_tokens", "actual"), "actual tokens"),
            tokens_saved=_needed(("tokens_saved", "saved"), "saved tokens"),
            baseline_cost_usd=_needed(
                ("baseline_cost_usd", "baseline_cost"), "baseline cost"),
            actual_cost_usd=_needed(
                ("actual_cost_usd", "actual_cost"), "actual cost"),
            saved_cost_usd=_needed(
                ("saved_cost_usd", "saved_cost"), "saved cost"),
            priced=_needed(("priced",), "priced flag"))
    raise ValueError(f"a cost line is needed, got {value!r}")


def validate_cost_line(line: Any, source: Any = None) -> ThriftCostLine:
    """Validate one cost line into a ThriftCostLine.

    Accepts a line or a mapping naming its model, its
    three token totals, its three priced costs and
    its priced flag. Every line is judged against the
    shared rate table at construction. With *source*
    given (a book), the line is judged against the
    line derived from that book for the line's own
    model: a stored line whose totals or costs
    disagree with the derived line refuses.
    """
    current = _check_cost_line_ref(line)
    if source is not None:
        derived = derive_cost_line(source, current.model)
        if current != derived:
            raise ValueError(
                "a stored cost line disagrees with the "
                "line derived from its book")
    return current


def build_cost_line(line: Any = None, source: Any = None,
                    **kwargs: Any) -> ThriftCostLine:
    """Build one validated cost line, from a mapping or field words."""
    if isinstance(line, ThriftCostLine) and not kwargs:
        return validate_cost_line(line, source)
    if isinstance(line, dict) or line is None:
        merged: Dict[str, Any] = {}
        if isinstance(line, dict):
            merged.update(line)
        merged.update(kwargs)
        return validate_cost_line(merged, source)
    return validate_cost_line(line, source)


# ---------------------------------------------------------------------
# The book: thrift records in held order, panels judged.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ThriftBook:
    """One token-thrift book: its records, in held order.

    ``records`` are the thrift records, in held
    order, each with its provenance whole; no two
    records of one book measure the same standing
    thing by the same road - one thing is counted
    once per road in a book. ``panels`` are the
    book's derivations - thrift panels of the whole
    book, each judged against the book by
    :func:`validate_book`; ``canon_note`` is the
    book's own note. The total is the records' own
    count, judged at construction. This book is the
    book file's shape: the shipped example is one
    book, and a real book file is a new file in this
    shape.
    """

    title: str = ""
    records: Tuple[ThriftRecord, ...] = ()
    panels: Tuple[ThriftPanel, ...] = ()
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
            raise ValueError("a thrift book holds at least one record")
        seen_ids = set()
        seen_refs = set()
        for record in records:
            if record.record_id is not None:
                if record.record_id in seen_ids:
                    raise ValueError(
                        f"a thrift record named {record.record_id!r} "
                        f"already exists")
                seen_ids.add(record.record_id)
            key = (record.road, record.ref)
            if key in seen_refs:
                raise ValueError(
                    f"the {record.road} reading of "
                    f"{record.ref!r} is already counted in "
                    f"this book - one thing is counted once "
                    f"per road in a book")
            seen_refs.add(key)
        object.__setattr__(self, "records", records)
        if isinstance(self.panels, (str, bytes)) \
                or not isinstance(self.panels, (list, tuple)):
            raise ValueError(
                f"a book's panels must be a list of panels, "
                f"got {self.panels!r}")
        panels = tuple(
            p if isinstance(p, ThriftPanel)
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

    def record_for(self, record_id: Any) -> ThriftRecord:
        """The thrift record one id names in this book."""
        wanted = normalize_member_id(record_id)
        for record in self.records:
            if record.record_id == wanted:
                return record
        raise KeyError(f"no thrift record in the book: {wanted!r}")

    def record_for_ref(self, road: Any, ref: Any) -> ThriftRecord:
        """The record measuring one standing thing by one road.

        The road is read through the road aliases and
        the reference matched as it stands. A thing no
        record of the book measures by that road
        raises KeyError - thrift is recorded, never
        guessed.
        """
        wanted_road = normalize_thrift_road(road)
        wanted_ref = _check_word(ref, "a record's reference")
        for record in self.records:
            if record.road == wanted_road and record.ref == wanted_ref:
                return record
        raise KeyError(
            f"no record in the book measures the {wanted_road} "
            f"reading standing as {wanted_ref!r}")

    def panel_for(self, panel_id: Any) -> ThriftPanel:
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
            "type": "token_thrift_book",
            "slice": TOKEN_THRIFT_SLICE,
            "title": self.title,
            "record_ids": list(self.record_ids()),
            "record_count": len(self.records),
            "panel_count": len(self.panels),
        }


def validate_book(data: Any, *, require_example: bool = False
                  ) -> ThriftBook:
    """Validate one token-thrift mapping into a book.

    The mapping names a ``schema`` (the token-thrift
    schema word), a ``guide`` mapping (its ``title``),
    a ``records`` list and an optional ``panels``
    list. Every record stands on its own validation,
    then the whole is judged: record ids unique, no
    thing counted twice by one road, and every stored
    panel judged against the book (a panel the book
    does not derive refuses). With
    ``require_example`` the shipped example is held to
    its pinned shape: the pinned title, records and
    panel, and the panel's pinned rows and account
    word-for-word. Problems raise
    :class:`ValidationError` or ``ValueError``.
    """
    if isinstance(data, ThriftBook):
        return data
    if not isinstance(data, dict):
        raise ValidationError(
            f"a thrift book must be a mapping, got {data!r}")
    unknown = set(data) - _THRIFT_BOOK_KEYS
    if unknown:
        raise ValidationError(
            "unknown thrift-book keys: %s" % ", ".join(sorted(unknown)))
    if data.get("schema") != TOKEN_THRIFT_SCHEMA:
        raise ValidationError(
            f"a thrift book must carry schema "
            f"{TOKEN_THRIFT_SCHEMA!r}, got {data.get('schema')!r}")
    records = _pick_any(data, ("records",), "records")
    if records is None:
        raise ValidationError("a thrift book is missing its records")
    if not isinstance(records, (list, tuple)):
        raise ValidationError("a thrift book's records must be a list")
    if data.get("panels") is not None \
            and not isinstance(data["panels"], (list, tuple)):
        raise ValidationError("a thrift book's panels must be a list")
    head = data.get("guide") or {}
    if not isinstance(head, dict):
        raise ValidationError("a thrift book's guide must be a mapping")
    unknown_head = set(head) - _BOOK_KEYS
    if unknown_head:
        raise ValidationError(
            "unknown guide keys: %s" % ", ".join(sorted(unknown_head)))
    try:
        title = _pick_any(head, ("title", "name"), "titles")
        if title is None:
            raise ValidationError("a thrift book is missing its title")
        note = data.get("canon_note") or ""
        if not isinstance(note, str):
            raise ValidationError("a thrift book's note must be text")
        book = ThriftBook(
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
                "the shipped example thrift book's title is "
                "not the pinned title")
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


def build_book(book: Any = None, **kwargs: Any) -> ThriftBook:
    """Build one validated book, from a mapping or field words."""
    if isinstance(book, ThriftBook) and not kwargs:
        return book
    if isinstance(book, dict):
        if "schema" in book:
            return validate_book(book)
        merged: Dict[str, Any] = dict(book)
        merged.update(kwargs)
        return ThriftBook(**merged)
    if book is None:
        return ThriftBook(**kwargs)
    raise ValueError(f"a thrift book is needed, got {book!r}")


def _book_from(data: Any, *, require_example: bool) -> ThriftBook:
    try:
        return validate_book(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_token_thrift(
        data: Optional[Dict[str, Any]] = None) -> ThriftBook:
    """Load and validate the shipped example book (or *data*).

    The shipped file is held to the example check: the
    pinned title, records and panel - the M-159 slice
    boundary book - so the shipped book covers the
    canon this slice exists to hold.
    """
    raw = data if data is not None else load_resource(
        TOKEN_THRIFT_RESOURCE)
    return _book_from(raw, require_example=True)


def load_token_thrift_file(path: Any) -> ThriftBook:
    """Load and validate a thrift book from a file at *path*.

    Any file in the token-thrift shape, anywhere on
    disk, validated whole - a malformed file raises
    :class:`ValidationError` naming the problem, and a
    missing file raises ``FileNotFoundError``. The
    example check is not held: a real book stands on
    its own records.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _book_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The registry model: one book held record by record.
# ---------------------------------------------------------------------


class ThriftRegistry:
    """One session's thrift records, held one by one.

    The registry holds records, never panels or cost
    lines: the panel and the line are derivations,
    read off the whole held book at call time, so
    nothing here can hold a figure stale. A whole
    book is judged as a book judges it - its ids and
    its measured things against the whole book -
    before its records are held in book order. A
    thing held here is counted once per road: a
    second record of a held road and reference
    refuses.
    """

    def __init__(self, book: Any = None) -> None:
        self._title: Optional[str] = None
        self._records: Dict[str, ThriftRecord] = {}
        self._record_order: list = []
        self._next_record = 1
        if book is not None:
            self.register_book(book)

    def _fresh_record_id(self, held_ids: Any) -> str:
        while f"thrift-{self._next_record}" in held_ids:
            self._next_record += 1
        fresh = f"thrift-{self._next_record}"
        self._next_record += 1
        return fresh

    def _check_ref_free(self, record: ThriftRecord) -> None:
        for held in self._records.values():
            if held.road == record.road and held.ref == record.ref:
                raise ValueError(
                    f"the {record.road} reading standing as "
                    f"{record.ref!r} is already counted in "
                    f"this book - one thing is counted once "
                    f"per road in a book")

    def register_record(self, record: Any) -> ThriftRecord:
        """Register one thrift record into the held book.

        A record with no id is given a deterministic
        ``thrift-N`` id. A record id already standing
        here refuses, as does a record measuring a
        thing a held record already counts by the same
        road.
        """
        validated = _check_record_ref(record)
        if validated.record_id is not None \
                and validated.record_id in self._records:
            raise ValueError(
                f"a thrift record named {validated.record_id!r} "
                f"already exists")
        self._check_ref_free(validated)
        return self._hold_record(validated)

    def _hold_record(self, validated: ThriftRecord) -> ThriftRecord:
        """Hold one judged record, in held order.

        The caller has already judged the record
        against the held book (its id and its measured
        thing); this is the holding alone, with a
        deterministic ``thrift-N`` id given to a record
        carrying none.
        """
        if validated.record_id is None:
            validated = replace(
                validated,
                record_id=self._fresh_record_id(set(self._records)))
        self._records[validated.record_id] = validated
        self._record_order.append(validated.record_id)
        return validated

    def register_book(self, book: Any) -> ThriftBook:
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
                "this registry already holds a thrift book "
                "under a different title")
        for record in validated.records:
            if record.record_id in self._records:
                raise ValueError(
                    f"a thrift record named {record.record_id!r} "
                    f"already exists")
            self._check_ref_free(record)
        self._title = validated.title
        for record in validated.records:
            self._hold_record(record)
        return self.book()

    def get_record(self, record_id: Any) -> ThriftRecord:
        """The thrift record one id names among the held records."""
        wanted = normalize_member_id(record_id)
        if wanted not in self._records:
            raise KeyError(f"unknown thrift record: {wanted!r}")
        return self._records[wanted]

    def record_for_ref(self, road: Any, ref: Any) -> ThriftRecord:
        """The held record measuring one standing thing by one road."""
        wanted_road = normalize_thrift_road(road)
        wanted_ref = _check_word(ref, "a record's reference")
        for record_id in self._record_order:
            record = self._records[record_id]
            if record.road == wanted_road and record.ref == wanted_ref:
                return record
        raise KeyError(
            f"no record held measures the {wanted_road} "
            f"reading standing as {wanted_ref!r}")

    def latest_record(self) -> ThriftRecord:
        """The most recently held thrift record."""
        if not self._record_order:
            raise ValueError("no thrift record is held yet")
        return self._records[self._record_order[-1]]

    def list_records(self) -> Tuple[ThriftRecord, ...]:
        """Every held thrift record, in the order they were held."""
        return tuple(self._records[item] for item in self._record_order)

    def book(self) -> ThriftBook:
        """The held records as one validated book."""
        if self._title is None:
            raise ValueError("no thrift book is held yet")
        return ThriftBook(
            title=self._title, records=self.list_records())

    def panel(self) -> ThriftPanel:
        """Derive the thrift panel of the whole held book."""
        return derive_panel(self)

    def cost_line(self, model: Any = "gpt-4o") -> ThriftCostLine:
        """Derive the thrift cost line of the whole held book."""
        return derive_cost_line(self, model)


# ---------------------------------------------------------------------
# The visible surface: what thrift saved, read off any book.
# ---------------------------------------------------------------------


def thrift_refs(source: Any) -> Tuple[Tuple[str, str], ...]:
    """Every measured thing one source holds, in panel order.

    The visible list of thrift: each held record's
    road and the reference it measures, in the order
    the derived panel shows them. *source* is a book
    or a registry.
    """
    panel = derive_panel(source)
    return tuple((row.road, row.ref) for row in panel.rows)


def total_saved(source: Any) -> int:
    """The tokens one source's records saved, in whole.

    The derived panel's own total: the sum of every
    held record's derived saving, read at call time.
    *source* is a book or a registry.
    """
    return derive_panel(source).total_saved


# ---------------------------------------------------------------------
# Thrift news, shaped as session records.
# ---------------------------------------------------------------------


def thrift_record(record: Any) -> Dict[str, Any]:
    """The session-news record of one thrift record."""
    current = record if isinstance(record, ThriftRecord) \
        else build_record(record)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Thrift ({current.road}) saved "
        f"{current.tokens_saved} tokens on "
        f"\"{current.subject}\" ({current.ref}), recorded by "
        f"{current.recorded_by} on {current.recorded_on}.")
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
        f"Thrift panel: {current.total_records} records - "
        f"{current.total_saved} tokens saved, reported.")
    return record_out


def cost_line_record(line: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived cost line.

    With *source* given, the line is first judged
    against the line that source derives for the
    line's own model.
    """
    current = validate_cost_line(line, source)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Thrift cost line ({current.model}): "
        f"{current.tokens_saved} tokens saved, "
        f"${current.saved_cost_usd:.2f} saved.")
    return record_out


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one thrift book."""
    current = book if isinstance(book, ThriftBook) \
        else build_book(book)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Token thrift {current.title}: "
        f"{record_out['record_count']} records held.")
    return record_out


def plain_words(record: Any) -> str:
    """One thrift record, in one plain sentence."""
    current = record if isinstance(record, ThriftRecord) \
        else build_record(record)
    return (
        f"\"{current.subject}\" was taken by the "
        f"{current.road} road ({current.ref}): "
        f"{current.actual_tokens} tokens against a "
        f"baseline of {current.baseline_tokens}, saving "
        f"{current.tokens_saved}. It was recorded by "
        f"{current.recorded_by} on {current.recorded_on} "
        f"(read from {current.source}).")


def panel_plain_words(source: Any) -> str:
    """The thrift panel in plain words, in full.

    Accepts a ThriftPanel or a ThriftBook (whose
    derived panel is told). The panel is told whole -
    its rows in panel order and its account.
    """
    if isinstance(source, ThriftPanel):
        panel = validate_panel(source)
        title = None
    elif isinstance(source, ThriftBook):
        panel = derive_panel(source)
        title = source.title
    else:
        raise ValueError(
            f"a token-thrift source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Thrift records, in panel order:")
    for row in panel.rows:
        lines.append(
            f"{row.record_id}: \"{row.subject}\" - "
            f"the {row.road} road ({row.ref}), "
            f"{row.actual_tokens} of {row.baseline_tokens} "
            f"tokens, saving {row.tokens_saved}, recorded "
            f"by {row.recorded_by} on {row.recorded_on}")
    lines.extend(panel.account)
    return "\n".join(lines)


def cost_line_plain_words(source: Any, model: Any = "gpt-4o") -> str:
    """The thrift cost line in plain words.

    Accepts a ThriftCostLine or a ThriftBook (whose
    derived line for *model* is told).
    """
    if isinstance(source, ThriftCostLine):
        line = validate_cost_line(source)
    elif isinstance(source, (ThriftBook, ThriftRegistry)):
        line = derive_cost_line(source, model)
    else:
        raise ValueError(
            f"a token-thrift source is needed, got {source!r}")
    priced_words = (
        "priced through the shared rate table"
        if line.priced else
        "not priced by the shared rate table - billed "
        "at zero, as the costs ledger bills it")
    return (
        f"Thrift cost line for {line.model}: "
        f"{line.tokens_saved} tokens saved "
        f"({line.actual_tokens} spent against a baseline "
        f"of {line.baseline_tokens}), saving "
        f"${line.saved_cost_usd:.6f} - {priced_words}.")


# ---------------------------------------------------------------------
# Screens: the formatters and the /thrift grammar.
# ---------------------------------------------------------------------


def _source_book(source: Any) -> ThriftBook:
    if source is None:
        return load_token_thrift()
    if isinstance(source, ThriftRegistry):
        return source.book()
    if isinstance(source, ThriftBook):
        return source
    raise ValueError(f"a thrift book is needed, got {source!r}")


def format_thrift_record(record: Any) -> str:
    """One thrift record as a screen block, provenance whole."""
    current = record if isinstance(record, ThriftRecord) \
        else build_record(record)
    lines = [
        f"{current.record_id or '-'}: \"{current.subject}\" - "
        f"the {current.road} road ({current.ref}), recorded by "
        f"{current.recorded_by} on {current.recorded_on}",
        f"Tokens: {current.actual_tokens} spent against a "
        f"baseline of {current.baseline_tokens} - "
        f"{current.tokens_saved} saved "
        f"({current.savings_percent}% of the baseline).",
        f"(read from {current.source})",
        "This record holds thrift as data - it reads "
        "no file and edits no code itself.",
    ]
    return "\n".join(lines)


def format_thrift_records(source: Any = None, road: Any = None) -> str:
    """Thrift records of one book, in held order.

    With *road* named, only the records of that road
    stand - read through the road aliases, so a road
    nothing holds shows its own empty line.
    """
    book = _source_book(source)
    wanted = normalize_thrift_road(road) if road is not None else None
    lines = [
        f"{item.record_id or '-'}: \"{item.subject}\" - "
        f"the {item.road} road ({item.ref}), saving "
        f"{item.tokens_saved} tokens, recorded by "
        f"{item.recorded_by}"
        for item in book.records
        if wanted is None or item.road == wanted]
    if not lines:
        lines.append("No thrift records are held.")
    return "\n".join(lines)


def format_panel(source: Any = None) -> str:
    """The thrift panel as a screen block: every row and the account.

    Accepts a ThriftPanel or a ThriftBook; a book
    shows the panel it derives.
    """
    if isinstance(source, ThriftPanel):
        panel = validate_panel(source)
        lines: list = []
    else:
        book = _source_book(source)
        if not book.records:
            return (f"Thrift panel in {book.title}:\n"
                    f"No thrift records are held.")
        panel = derive_panel(book)
        lines = [f"Thrift panel in {book.title}:"]
    lines.append("Thrift records, in panel order:")
    for row in panel.rows:
        lines.append(
            f"{row.record_id}: \"{row.subject}\" - "
            f"the {row.road} road ({row.ref}), "
            f"{row.actual_tokens} of {row.baseline_tokens} "
            f"tokens, saving {row.tokens_saved}, recorded "
            f"by {row.recorded_by} on {row.recorded_on}")
    lines.extend(panel.account)
    return "\n".join(lines)


def format_cost_line(source: Any = None, model: Any = "gpt-4o") -> str:
    """The thrift cost line as a screen block, for mythic costs.

    Accepts a ThriftCostLine or a ThriftBook; a book
    shows the line it derives for *model*, priced
    through the shared rate table.
    """
    if isinstance(source, ThriftCostLine):
        line = validate_cost_line(source)
        lines = [cost_line_plain_words(line)]
    else:
        book = _source_book(source)
        line = derive_cost_line(book, model)
        lines = [f"Thrift cost line in {book.title}:",
                 cost_line_plain_words(line)]
    lines.append(
        "This line is a derivation for reporting - it "
        "changes nothing any live road spends.")
    return "\n".join(lines)


def format_token_thrift_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /thrift.

    With nothing named, the shipped example thrift
    book is shown - the example this slice ships - so
    the screen is never empty.
    """
    book = _source_book(source)
    lines = ["Token Thrift (M-160) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_thrift_records(book))
    lines.append("")
    lines.append(format_panel(book))
    lines.append("")
    lines.append(format_cost_line(book))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_thrift_args(args: Any) -> Tuple[str, Any]:
    """Parse the /thrift grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the thrift
    book; ``record <record-id>`` shows one record
    with its provenance whole; ``road <road>`` shows
    the records of one road, the road read through
    the road aliases; ``panel`` shows the thrift
    panel derived from the whole book; ``costs``
    shows the thrift cost line derived for the whole
    book. Anything else is a usage error naming the
    grammar. Returns ``(action, value-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() in ("show", "list"):
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head in ("panel", "costs") and len(words) == 1:
        return (head, None)
    if head == "record" and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "road" and len(words) == 2:
        try:
            return (head, normalize_thrift_road(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
