"""Context budget made visible (All-Features roadmap slice M-147).

Part VII opens here. The roadmap's words:
``a live meter and a "what's in the context and
why" panel - every file, note, and map section
accounted for in tokens.``

What already shipped, and what this slice adds:

* The context itself is already assembled by
  shipped roads: the context compiler
  (``context/compiler.py``, Slice 051) gathers
  ordered ``ContextBlock`` objects from pluggable
  sources - explicit files, the repo map,
  instructions, symbols, semantic files,
  dependencies and the git diff - each block
  carrying its provenance and its token count
  inside a budget; the token estimator and budget
  planner (``context/budget.py``, Slice 052) count
  tokens with ``tiktoken`` when it is importable
  and a deterministic character heuristic
  otherwise; and the agent's ``ContextBuilder``
  (``agents/context.py``, Slice 15) assembles the
  message list - system prompt, recent turns,
  tool results and older turns - inside a fixed
  budget. Those roads decide WHAT is in the
  context. What nothing holds is the account of
  it, as data: which things are in the context,
  in what tokens, and WHY each one is there.
* This slice is that account, as a pure layer: a
  context item record validated as data (one
  thing in the context - its closed kind, its
  title, its source, the plain-words reason it is
  in the context, and its token count), a budget
  panel book holding a token budget and its items
  in held order, a meter DERIVED from the items
  (their total, the per-kind subtotals, the
  headroom and the over-budget state), a panel
  DERIVED from the items (the "what's in the
  context and why" account: every item's kind,
  source, reason, tokens and share), the shipped
  data file
  (``mythic_agent/data/context_budget.yaml``)
  holding one example panel in exactly the shape
  a real panel file takes, a loader for a panel
  file anywhere on disk, a live measurement road
  that counts real texts into items through the
  shipped ``TokenEstimator`` composed BY IMPORT,
  a road that builds a panel from a compiled
  context's blocks, records shaped as session
  news, and a small in-memory registry model.
  This module compiles no context, calls no
  model, assembles no prompt and imports no
  agent / UI code; the agent layer owns holding
  a panel for a session.

Honesty rules, enforced here and pinned by tests:

* **The kinds are the shipped context's own.**
  An item's kind is one of a closed set the
  shipped context system itself justifies:
  ``system`` (the system prompt, always kept),
  ``instruction`` (workspace instructions merged
  by the instruction source), ``file`` (explicit
  files and the file-shaped sources: symbols,
  semantic files, dependencies, the git diff),
  ``map_section`` (a repo map section),
  ``note`` (a session note), ``history`` (recent
  and older turns the builder carries) and
  ``tool_result`` (a tool call's result). A kind
  outside that set refuses; no kind is invented
  here that the shipped system does not hold.
* **The meter is derived, never stored loose.**
  A panel record names its budget and its items
  and no meter of its own: the total, the
  per-kind subtotals, the headroom (budget minus
  total, negative when over), the over-budget
  state and the usage share are read off the
  items at call time, so a stored ``total`` /
  ``headroom`` / ``usage`` key on an item record
  refuses as an unknown key, and a stored meter
  that disagrees with the meter derived from
  its items refuses.
* **The panel is derived, never stored loose.**
  The panel's rows are the items themselves, in
  held order - each row the item's kind, title,
  source, reason, tokens and share of the whole
  - and its account is read off the rows, so a
  stored panel whose rows, totals or account
  disagree with the panel derived from its
  items refuses.
* **Measurement composes the shipped counter.**
  The live road counts text through the shipped
  ``TokenEstimator`` (``context/budget.py``),
  composed by import, never re-implemented here.
  Its backend is the estimator's own: ``tiktoken``
  when importable, the deterministic heuristic
  otherwise - tests force the heuristic backend
  (``prefer_tiktoken=False``) for determinism,
  because a live ``tiktoken`` install prices text
  differently (the known environment caveat the
  gate slices record).
* **A compiled panel reads blocks as they are.**
  The compiled-context road is duck-typed: it
  reads each block's name, content, tokens,
  priority and provenance by attribute or by
  mapping key, and imports no compiler code, so
  the layering stays clean. An item's source is
  the block's provenance source, its tokens are
  the block's own count (counted from its
  content through the estimator only when the
  block carries none), its reason is read off
  its priority and source, and its kind is read
  off its provenance and source by the one
  stated rule in :func:`panel_from_compiled` -
  an unclassified block is held as a ``note``,
  never invented as a file.
* **Data only - no live road is claimed.** An
  item here is a validated record held as data:
  no context is compiled, no prompt is
  assembled, no model is called and nothing is
  persisted. Holding a panel changes no live
  context assembly - the shipped compiler and
  builder go on exactly as before; this slice
  makes their result visible. The account is
  visible through this slice's own
  /contextbudget screen.
* **Malformed refuses.** A duplicate item id in
  one panel, a negative token count, an unknown
  kind, and unknown keys in an item, a meter, a
  panel or a panel mapping all raise instead of
  being skipped or guessed at.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..context.budget import TokenEstimator
from ..resources import load_resource
from .crew_members import normalize_member_id
from .validation import ValidationError

__all__ = [
    "PLAIN_EXPLANATION",
    "CONTEXT_BUDGET_RESOURCE",
    "CONTEXT_BUDGET_SCHEMA",
    "CONTEXT_BUDGET_SLICE",
    "ITEM_KINDS",
    "USAGE",
    "ContextBudgetPanel",
    "ContextBudgetRegistry",
    "ContextItem",
    "ContextMeter",
    "ContextPanel",
    "KindTotal",
    "PanelRow",
    "book_record",
    "build_budget_panel",
    "build_item",
    "build_meter",
    "build_panel",
    "derive_meter",
    "derive_panel",
    "format_context_budget_screen",
    "format_item",
    "format_items",
    "format_meter",
    "format_panel",
    "item_record",
    "load_context_budget",
    "load_context_budget_file",
    "measure_item",
    "measure_panel",
    "meter_plain_words",
    "meter_record",
    "normalize_kind",
    "panel_from_compiled",
    "panel_plain_words",
    "panel_record",
    "parse_context_budget_args",
    "plain_words",
    "validate_book",
    "validate_item",
    "validate_meter",
    "validate_panel",
]

CONTEXT_BUDGET_SLICE = "M-147"

#: The packaged data resource holding the example panel.
CONTEXT_BUDGET_RESOURCE = "context_budget.yaml"

#: The schema word a context budget file must carry.
CONTEXT_BUDGET_SCHEMA = "mythic.context_budget/1"

#: The kinds one context item may hold, in context
#: order: the kinds the shipped context system
#: itself justifies - the system prompt, workspace
#: instructions, files, a repo map section, a
#: session note, conversation history and a tool
#: result. No other kind is held.
ITEM_KINDS = (
    "system", "instruction", "file", "map_section",
    "note", "history", "tool_result")

_ITEM_KEYS = frozenset({
    "item_id", "id", "kind", "title", "headline",
    "source", "origin", "reason", "why",
    "tokens", "token_count",
})

_KIND_TOTAL_KEYS = frozenset({
    "kind", "tokens", "token_count", "items", "count",
})

_METER_KEYS = frozenset({
    "meter_id", "id", "budget_tokens", "budget",
    "total_tokens", "total", "total_items", "items",
    "headroom_tokens", "headroom", "over_budget", "over",
    "usage_percent", "usage", "kind_totals", "kinds",
    "account", "statements",
})

_ROW_KEYS = frozenset({
    "item_id", "id", "kind", "title", "headline",
    "source", "origin", "reason", "why",
    "tokens", "token_count", "share_percent", "share",
})

_PANEL_KEYS = frozenset({
    "panel_id", "id", "rows", "items",
    "budget_tokens", "budget",
    "total_tokens", "total", "total_items",
    "headroom_tokens", "headroom", "over_budget", "over",
    "account", "statements",
})

_BOOK_KEYS = frozenset({"title", "name"})

_CONTEXT_BUDGET_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "budget_note", "guide", "budget_tokens", "budget",
    "entries", "items", "meters", "panels",
})

#: The shipped example panel's title, held to this
#: by the loader's example check.
_EXAMPLE_TITLE = "Context budget panel at the M-146 slice boundary"

#: The shipped example's budget, pinned by the loader.
_EXAMPLE_BUDGET = 8000

#: The shipped example's item ids, in held order,
#: pinned by the loader: one item of every kind.
_EXAMPLE_ITEM_IDS = (
    "ctx-system-prompt", "ctx-instructions",
    "ctx-file-crew-schedules", "ctx-map-crew",
    "ctx-note-slice", "ctx-history-turns",
    "ctx-tool-result-tests")

#: The shipped example's kinds, in held order,
#: pinned by the loader: every kind held once.
_EXAMPLE_KINDS = ITEM_KINDS

#: The shipped example's derived totals, pinned by
#: the loader: total tokens, item count, headroom
#: and usage percent of the derived meter.
_EXAMPLE_TOTALS = (5660, 7, 2340, 70.8)

#: The shipped example's one meter and one panel.
_EXAMPLE_METER_ID = "meter-m146-boundary"

_EXAMPLE_PANEL_ID = "panel-m146-boundary"

_EXAMPLE_METER_ACCOUNT = (
    "The context holds 5660 of 8000 tokens "
    "(70.8% used); 2340 tokens of headroom remain.",
    "By kind: system 640 tokens in 1 item(s); "
    "instruction 480 tokens in 1 item(s); "
    "file 1520 tokens in 1 item(s); "
    "map_section 720 tokens in 1 item(s); "
    "note 260 tokens in 1 item(s); "
    "history 1180 tokens in 1 item(s); "
    "tool_result 860 tokens in 1 item(s).",
    "The meter is read off the held items at call "
    "time - it is derived, never stored loose.",
)

_EXAMPLE_PANEL_ACCOUNT = (
    "The panel accounts for 7 item(s) in the "
    "context: 5660 token(s) against a budget of "
    "8000, with 2340 token(s) of headroom.",
    "Every item names its kind, its source and "
    "the reason it is in the context; nothing "
    "sits in the context unaccounted for.",
    "The panel is read off the held items at call "
    "time - it is derived, never stored loose, "
    "and holding it changes no live context "
    "assembly.",
)

PLAIN_EXPLANATION = (
    "Context budget made visible: a live meter "
    "and a what's-in-the-context-and-why panel - "
    "every file, note, and map section accounted "
    "for in tokens. A context item names one "
    "thing in the context - its kind (system, "
    "instruction, file, map_section, note, "
    "history or tool_result, the kinds the "
    "shipped context system itself holds), its "
    "title, its source, the plain-words reason "
    "it is in the context, and its token count. "
    "The meter - the total, the per-kind "
    "subtotals, the headroom and the over-budget "
    "state - and the panel - every item's kind, "
    "source, reason, tokens and share - are "
    "derived from the held items, never stored "
    "loose, so a stored meter or panel that "
    "disagrees refuses. This layer holds the "
    "account as data only; it compiles no "
    "context, assembles no prompt, calls no "
    "model and persists nothing itself."
)

USAGE = (
    "Usage: /contextbudget, /contextbudget show, "
    "/contextbudget item <item-id>, "
    "/contextbudget kind <kind>, "
    "/contextbudget meter, /contextbudget panel"
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


def _check_budget(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"a budget must be a count, got {value!r}")
    if value <= 0:
        raise ValueError(f"a budget must be positive, got {value!r}")
    return value


def _check_headroom(value: Any, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{what} must be a count, got {value!r}")
    return value


def _check_percent(value: Any, what: str) -> float:
    if isinstance(value, bool) \
            or not isinstance(value, (int, float)):
        raise ValueError(f"{what} must be a percent, got {value!r}")
    percent = float(value)
    if percent < 0:
        raise ValueError(f"{what} must not be negative, got {value!r}")
    return percent


def _usage_percent(total: int, budget: int) -> float:
    """The usage share of *total* against *budget*, in percent."""
    if budget <= 0:
        return 0.0
    return round(100.0 * total / budget, 1)


def _share_percent(part: int, total: int) -> float:
    """One item's share of the whole context, in percent."""
    if total <= 0:
        return 0.0
    return round(100.0 * part / total, 1)


def normalize_kind(value: Any) -> str:
    """The canonical context item kind a word names.

    A kind is one of :data:`ITEM_KINDS` - the kinds
    the shipped context system itself justifies -
    read case-insensitively with dashes read as
    underscores. Anything else raises.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace("-", "_")
        if wanted in ITEM_KINDS:
            return wanted
    raise ValueError(
        "a context item kind must be one of %s, got %r"
        % ("/".join(ITEM_KINDS), value))


# ---------------------------------------------------------------------
# The context item: one thing in the context, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ContextItem:
    """One thing in the context, accounted for in tokens.

    ``kind`` is the item's kind in the closed set
    the shipped context system justifies;
    ``title`` names the item in plain words;
    ``source`` names where it came from;
    ``reason`` says in plain words WHY it is in
    the context; ``tokens`` is its token count.
    The record names NO total, NO headroom and NO
    share of its own: those are the meter's and
    the panel's derivations, read off the whole
    panel of items, so an item can never claim a
    share its panel does not give it.
    """

    kind: str
    title: str
    source: str
    reason: str
    tokens: int
    item_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.item_id is not None:
            object.__setattr__(
                self, "item_id",
                normalize_member_id(self.item_id))
        object.__setattr__(self, "kind", normalize_kind(self.kind))
        object.__setattr__(
            self, "title", _check_title(self.title, "an item's title"))
        object.__setattr__(
            self, "source",
            _check_title(self.source, "an item's source"))
        object.__setattr__(
            self, "reason",
            _check_long_text(self.reason, "an item's reason"))
        object.__setattr__(
            self, "tokens",
            _check_count(self.tokens, "an item's tokens"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "context_budget_item",
            "slice": CONTEXT_BUDGET_SLICE,
            "item_id": self.item_id,
            "kind": self.kind,
            "title": self.title,
            "source": self.source,
            "reason": self.reason,
            "tokens": self.tokens,
        }


def validate_item(item: Any) -> ContextItem:
    """Validate one context item record into a ContextItem.

    Accepts a ContextItem or a mapping naming a
    ``kind``, a ``title`` (or ``headline``), a
    ``source`` (or ``origin``), a ``reason`` (or
    ``why``), a ``tokens`` count (or
    ``token_count``) and an optional ``item_id``
    (or ``id``). Naming two spellings of one field
    with different values refuses, and unknown
    keys refuse - a stored total, headroom or
    share key among them, because those are
    derived from the whole panel, never stored
    on an item.
    """
    if isinstance(item, ContextItem):
        return item
    if not isinstance(item, dict):
        raise ValueError(
            f"a context item record must be a mapping, "
            f"got {item!r}")
    unknown = set(item) - _ITEM_KEYS
    if unknown:
        raise ValueError(
            "unknown context-item keys: %s"
            % ", ".join(sorted(unknown)))
    kind = _pick_any(item, ("kind",), "kinds")
    if kind is None:
        raise ValueError("a context item record is missing its kind")
    title = _pick_any(item, ("title", "headline"), "titles")
    if title is None:
        raise ValueError("a context item record is missing its title")
    source = _pick_any(item, ("source", "origin"), "sources")
    if source is None:
        raise ValueError("a context item record is missing its source")
    reason = _pick_any(item, ("reason", "why"), "reasons")
    if reason is None:
        raise ValueError("a context item record is missing its reason")
    tokens = _pick_any(item, ("tokens", "token_count"), "token counts")
    if tokens is None:
        raise ValueError("a context item record is missing its tokens")
    kwargs: Dict[str, Any] = {
        "kind": kind, "title": title, "source": source,
        "reason": reason, "tokens": tokens}
    item_id = _pick_any(item, ("item_id", "id"), "item ids")
    if item_id is not None:
        kwargs["item_id"] = item_id
    return ContextItem(**kwargs)


def build_item(item: Any = None, **kwargs: Any) -> ContextItem:
    """Build one validated context item, from a mapping or field words."""
    if isinstance(item, ContextItem) and not kwargs:
        return item
    if isinstance(item, dict) or item is None:
        merged: Dict[str, Any] = {}
        if isinstance(item, dict):
            merged.update(item)
        merged.update(kwargs)
        return validate_item(merged)
    raise ValueError(
        f"a context item record must be a mapping, got {item!r}")


def _check_item_ref(value: Any) -> ContextItem:
    if isinstance(value, ContextItem):
        return value
    if isinstance(value, dict):
        return validate_item(value)
    raise ValueError(f"a context item record is needed, got {value!r}")


def _held_items(source: Any) -> Tuple[ContextItem, ...]:
    """The context items one source holds, in held order."""
    if isinstance(source, ContextBudgetPanel):
        return source.items
    if isinstance(source, ContextBudgetRegistry):
        return source.list_items()
    if isinstance(source, (list, tuple)):
        return tuple(_check_item_ref(e) for e in source)
    raise ValueError(f"context items are needed, got {source!r}")


def _held_items_and_budget(
        source: Any,
        budget_tokens: Any = None) -> Tuple[Tuple[ContextItem, ...], int]:
    """The items and budget one source names, for a derivation."""
    entries = _held_items(source)
    budget = budget_tokens
    if isinstance(source, ContextBudgetPanel):
        if budget is not None and budget != source.budget_tokens:
            raise ValueError(
                "a derivation names one budget: the panel's own "
                "budget or the named one, not two different ones")
        budget = source.budget_tokens
    elif isinstance(source, ContextBudgetRegistry):
        if budget is None:
            budget = source.budget_tokens
    if budget is None:
        raise ValueError(
            "a derivation needs a budget: name budget_tokens")
    return entries, _check_budget(budget)


# ---------------------------------------------------------------------
# The meter: the panel's numbers, derived.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class KindTotal:
    """One kind's subtotal in a meter: its tokens and item count."""

    kind: str
    tokens: int
    items: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", normalize_kind(self.kind))
        object.__setattr__(
            self, "tokens",
            _check_count(self.tokens, "a kind total's tokens"))
        object.__setattr__(
            self, "items",
            _check_count(self.items, "a kind total's items"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "tokens": self.tokens,
            "items": self.items,
        }


def _check_kind_total_ref(value: Any) -> KindTotal:
    if isinstance(value, KindTotal):
        return value
    if isinstance(value, dict):
        unknown = set(value) - _KIND_TOTAL_KEYS
        if unknown:
            raise ValueError(
                "unknown kind-total keys: %s"
                % ", ".join(sorted(unknown)))
        kind = _pick_any(value, ("kind",), "kinds")
        if kind is None:
            raise ValueError("a kind total is missing its kind")
        tokens = _pick_any(value, ("tokens", "token_count"), "tokens")
        if tokens is None:
            raise ValueError("a kind total is missing its tokens")
        items = _pick_any(value, ("items", "count"), "item counts")
        if items is None:
            raise ValueError("a kind total is missing its items")
        return KindTotal(kind=kind, tokens=tokens, items=items)
    raise ValueError(f"a kind total is needed, got {value!r}")


def _meter_account(budget: int, total: int, headroom: int,
                   over: bool,
                   kind_totals: Tuple[KindTotal, ...]) -> Tuple[str, ...]:
    if over:
        first = (
            f"The context holds {total} of {budget} tokens "
            f"({_usage_percent(total, budget):.1f}% used); "
            f"it is over budget by {-headroom} tokens.")
    else:
        first = (
            f"The context holds {total} of {budget} tokens "
            f"({_usage_percent(total, budget):.1f}% used); "
            f"{headroom} tokens of headroom remain.")
    if kind_totals:
        by_kind = "; ".join(
            f"{row.kind} {row.tokens} tokens in {row.items} item(s)"
            for row in kind_totals)
        second = f"By kind: {by_kind}."
    else:
        second = "By kind: nothing is in the context."
    return (
        first,
        second,
        "The meter is read off the held items at call "
        "time - it is derived, never stored loose.",
    )


@dataclass(frozen=True)
class ContextMeter:
    """The context budget meter, derived from the items.

    ``budget_tokens`` is the panel's budget;
    ``total_tokens`` is every item's tokens
    summed; ``total_items`` is the item count;
    ``headroom_tokens`` is budget minus total
    (negative when over); ``over_budget`` is
    whether the total passes the budget;
    ``usage_percent`` is the total's share of the
    budget; ``kind_totals`` are the per-kind
    subtotals in the order the kinds first appear
    among the items; ``account`` is read off
    those numbers. Every figure is a derivation:
    :func:`validate_meter` judged against items
    refuses a meter whose figures disagree with
    the meter those items derive, and a meter
    whose own figures disagree with each other
    refuses at construction.
    """

    budget_tokens: int
    total_tokens: int = 0
    total_items: int = 0
    headroom_tokens: int = 0
    over_budget: bool = False
    usage_percent: float = 0.0
    kind_totals: Tuple[KindTotal, ...] = ()
    account: Tuple[str, ...] = ()
    meter_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.meter_id is not None:
            object.__setattr__(
                self, "meter_id", normalize_member_id(self.meter_id))
        object.__setattr__(
            self, "budget_tokens", _check_budget(self.budget_tokens))
        object.__setattr__(
            self, "total_tokens",
            _check_count(self.total_tokens, "a meter's total tokens"))
        object.__setattr__(
            self, "total_items",
            _check_count(self.total_items, "a meter's total items"))
        object.__setattr__(
            self, "headroom_tokens",
            _check_headroom(self.headroom_tokens, "a meter's headroom"))
        if not isinstance(self.over_budget, bool):
            raise ValueError(
                f"a meter's over-budget state must be true or "
                f"false, got {self.over_budget!r}")
        object.__setattr__(
            self, "usage_percent",
            _check_percent(self.usage_percent, "a meter's usage"))
        if isinstance(self.kind_totals, (str, bytes)) \
                or not isinstance(self.kind_totals, (list, tuple)):
            raise ValueError(
                f"a meter's kind totals must be a list, "
                f"got {self.kind_totals!r}")
        kind_totals = tuple(
            _check_kind_total_ref(row) for row in self.kind_totals)
        seen_kinds = set()
        for row in kind_totals:
            if row.kind in seen_kinds:
                raise ValueError(
                    f"a kind total named {row.kind!r} already exists")
            seen_kinds.add(row.kind)
        object.__setattr__(self, "kind_totals", kind_totals)
        if self.headroom_tokens != self.budget_tokens - self.total_tokens:
            raise ValueError(
                "a meter's headroom must be its own budget "
                "minus its total")
        if self.over_budget != (self.total_tokens > self.budget_tokens):
            raise ValueError(
                "a meter's over-budget state must be its own "
                "total against its budget")
        if self.usage_percent != _usage_percent(
                self.total_tokens, self.budget_tokens):
            raise ValueError(
                "a meter's usage must be its own total's share "
                "of its budget")
        if sum(row.tokens for row in kind_totals) != self.total_tokens:
            raise ValueError(
                "a meter's kind totals must sum to its own total")
        if sum(row.items for row in kind_totals) != self.total_items:
            raise ValueError(
                "a meter's kind totals must count its own items")
        object.__setattr__(self, "account", _check_account(self.account))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "context_budget_meter",
            "slice": CONTEXT_BUDGET_SLICE,
            "meter_id": self.meter_id,
            "budget_tokens": self.budget_tokens,
            "total_tokens": self.total_tokens,
            "total_items": self.total_items,
            "headroom_tokens": self.headroom_tokens,
            "over_budget": self.over_budget,
            "usage_percent": self.usage_percent,
            "kind_totals": [row.to_record() for row in self.kind_totals],
            "account": list(self.account),
        }


def derive_meter(source: Any, budget_tokens: Any = None) -> ContextMeter:
    """Derive the meter from context items and their budget.

    The total, the per-kind subtotals (in the
    order the kinds first appear), the headroom,
    the over-budget state, the usage share and
    the account are read off the items alone.
    *source* is a panel book, a registry or the
    items themselves; a bare item list names its
    budget through *budget_tokens*. An empty
    source refuses - a meter of nothing is no
    meter.
    """
    entries, budget = _held_items_and_budget(source, budget_tokens)
    if not entries:
        raise ValueError("a meter needs at least one context item")
    total = sum(entry.tokens for entry in entries)
    order: list = []
    by_kind: Dict[str, list] = {}
    for entry in entries:
        if entry.kind not in by_kind:
            by_kind[entry.kind] = [0, 0]
            order.append(entry.kind)
        by_kind[entry.kind][0] += entry.tokens
        by_kind[entry.kind][1] += 1
    kind_totals = tuple(
        KindTotal(kind=kind, tokens=by_kind[kind][0],
                  items=by_kind[kind][1])
        for kind in order)
    headroom = budget - total
    over = total > budget
    return ContextMeter(
        budget_tokens=budget,
        total_tokens=total,
        total_items=len(entries),
        headroom_tokens=headroom,
        over_budget=over,
        usage_percent=_usage_percent(total, budget),
        kind_totals=kind_totals,
        account=_meter_account(budget, total, headroom, over, kind_totals))


def validate_meter(meter: Any, source: Any = None) -> ContextMeter:
    """Validate one meter into a ContextMeter.

    Accepts a ContextMeter or a mapping naming a
    ``budget_tokens`` (or ``budget``), a
    ``total_tokens`` (or ``total``), a
    ``total_items`` (or ``items``), a
    ``headroom_tokens`` (or ``headroom``), an
    ``over_budget`` state (or ``over``), a
    ``usage_percent`` (or ``usage``),
    ``kind_totals`` (or ``kinds``), an ``account``
    (or ``statements``) and an optional
    ``meter_id`` (or ``id``). With *source* given
    (items with their budget), the meter is
    judged against the meter derived from those
    items: a stored meter whose budget, totals,
    headroom, over-budget state, usage, kind
    totals or account disagree with the derived
    meter refuses. A meter naming no account
    refuses too.
    """
    if isinstance(meter, ContextMeter):
        current = meter
    elif isinstance(meter, dict):
        unknown = set(meter) - _METER_KEYS
        if unknown:
            raise ValueError(
                "unknown meter keys: %s" % ", ".join(sorted(unknown)))
        budget = _pick_any(meter, ("budget_tokens", "budget"), "budgets")
        if budget is None:
            raise ValueError("a meter is missing its budget")
        total = _pick_any(meter, ("total_tokens", "total"), "totals")
        if total is None:
            raise ValueError("a meter is missing its total tokens")
        total_items = _pick_any(meter, ("total_items", "items"), "item totals")
        if total_items is None:
            raise ValueError("a meter is missing its total items")
        headroom = _pick_any(
            meter, ("headroom_tokens", "headroom"), "headrooms")
        if headroom is None:
            raise ValueError("a meter is missing its headroom")
        over = _pick_any(meter, ("over_budget", "over"), "over states")
        if over is None:
            raise ValueError("a meter is missing its over-budget state")
        if not isinstance(over, bool):
            raise ValueError(
                f"a meter's over-budget state must be true or "
                f"false, got {over!r}")
        usage = _pick_any(meter, ("usage_percent", "usage"), "usages")
        if usage is None:
            raise ValueError("a meter is missing its usage")
        kind_totals = _pick_any(
            meter, ("kind_totals", "kinds"), "kind totals")
        if kind_totals is None:
            raise ValueError("a meter is missing its kind totals")
        account = _pick_any(meter, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError("a meter names no account of its own")
        kwargs: Dict[str, Any] = {
            "budget_tokens": budget, "total_tokens": total,
            "total_items": total_items, "headroom_tokens": headroom,
            "over_budget": over, "usage_percent": usage,
            "kind_totals": kind_totals, "account": account}
        meter_id = _pick_any(meter, ("meter_id", "id"), "meter ids")
        if meter_id is not None:
            kwargs["meter_id"] = meter_id
        current = ContextMeter(**kwargs)
    else:
        raise ValueError(f"a meter must be a mapping, got {meter!r}")
    if source is not None:
        derived = derive_meter(source, current.budget_tokens)
        if (current.budget_tokens != derived.budget_tokens
                or current.total_tokens != derived.total_tokens
                or current.total_items != derived.total_items
                or current.headroom_tokens != derived.headroom_tokens
                or current.over_budget != derived.over_budget
                or current.usage_percent != derived.usage_percent
                or current.kind_totals != derived.kind_totals
                or current.account != derived.account):
            raise ValueError(
                "a stored meter disagrees with the meter "
                "derived from its items")
    return current


def build_meter(meter: Any = None, source: Any = None,
                **kwargs: Any) -> ContextMeter:
    """Build one validated meter, from a mapping or field words."""
    if isinstance(meter, ContextMeter) and not kwargs:
        return validate_meter(meter, source)
    if isinstance(meter, dict) or meter is None:
        merged: Dict[str, Any] = {}
        if isinstance(meter, dict):
            merged.update(meter)
        merged.update(kwargs)
        return validate_meter(merged, source)
    return validate_meter(meter, source)


# ---------------------------------------------------------------------
# The panel: what's in the context and why, derived.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class PanelRow:
    """One row of the panel: one item, accounted for.

    The row carries the item's own fields whole -
    its id, kind, title, source, reason and
    tokens - plus ``share_percent``, the item's
    share of the whole context's tokens, which
    the panel judges against its own total.
    """

    kind: str
    title: str
    source: str
    reason: str
    tokens: int
    share_percent: float = 0.0
    item_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.item_id is not None:
            object.__setattr__(
                self, "item_id", normalize_member_id(self.item_id))
        object.__setattr__(self, "kind", normalize_kind(self.kind))
        object.__setattr__(
            self, "title", _check_title(self.title, "a row's title"))
        object.__setattr__(
            self, "source", _check_title(self.source, "a row's source"))
        object.__setattr__(
            self, "reason",
            _check_long_text(self.reason, "a row's reason"))
        object.__setattr__(
            self, "tokens", _check_count(self.tokens, "a row's tokens"))
        object.__setattr__(
            self, "share_percent",
            _check_percent(self.share_percent, "a row's share"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "kind": self.kind,
            "title": self.title,
            "source": self.source,
            "reason": self.reason,
            "tokens": self.tokens,
            "share_percent": self.share_percent,
        }


def _check_row_ref(value: Any) -> PanelRow:
    if isinstance(value, PanelRow):
        return value
    if isinstance(value, dict):
        unknown = set(value) - _ROW_KEYS
        if unknown:
            raise ValueError(
                "unknown panel-row keys: %s"
                % ", ".join(sorted(unknown)))
        kind = _pick_any(value, ("kind",), "kinds")
        if kind is None:
            raise ValueError("a panel row is missing its kind")
        title = _pick_any(value, ("title", "headline"), "titles")
        if title is None:
            raise ValueError("a panel row is missing its title")
        source = _pick_any(value, ("source", "origin"), "sources")
        if source is None:
            raise ValueError("a panel row is missing its source")
        reason = _pick_any(value, ("reason", "why"), "reasons")
        if reason is None:
            raise ValueError("a panel row is missing its reason")
        tokens = _pick_any(value, ("tokens", "token_count"), "tokens")
        if tokens is None:
            raise ValueError("a panel row is missing its tokens")
        share = _pick_any(value, ("share_percent", "share"), "shares")
        if share is None:
            raise ValueError("a panel row is missing its share")
        kwargs: Dict[str, Any] = {
            "kind": kind, "title": title, "source": source,
            "reason": reason, "tokens": tokens,
            "share_percent": share}
        item_id = _pick_any(value, ("item_id", "id"), "item ids")
        if item_id is not None:
            kwargs["item_id"] = item_id
        return PanelRow(**kwargs)
    raise ValueError(f"a panel row is needed, got {value!r}")


def _panel_account(rows: Tuple[PanelRow, ...], budget: int,
                   total: int, headroom: int,
                   over: bool) -> Tuple[str, ...]:
    if over:
        first = (
            f"The panel accounts for {len(rows)} item(s) in "
            f"the context: {total} token(s) against a budget "
            f"of {budget}, over budget by {-headroom} token(s).")
    else:
        first = (
            f"The panel accounts for {len(rows)} item(s) in "
            f"the context: {total} token(s) against a budget "
            f"of {budget}, with {headroom} token(s) of headroom.")
    return (
        first,
        "Every item names its kind, its source and "
        "the reason it is in the context; nothing "
        "sits in the context unaccounted for.",
        "The panel is read off the held items at call "
        "time - it is derived, never stored loose, "
        "and holding it changes no live context "
        "assembly.",
    )


@dataclass(frozen=True)
class ContextPanel:
    """The what's-in-the-context-and-why panel, derived.

    ``rows`` are the panel's items, in held order,
    each carried whole with its share of the
    whole; ``budget_tokens``, ``total_tokens``,
    ``total_items``, ``headroom_tokens`` and
    ``over_budget`` are the meter's own figures
    for the same items, and ``account`` is read
    off the rows and totals. A panel whose totals
    are not its own rows' counts, or whose rows'
    shares are not their shares of its total,
    refuses at construction; :func:`validate_panel`
    judged against items refuses a stored panel
    that disagrees with the derived one.
    """

    rows: Tuple[PanelRow, ...] = ()
    budget_tokens: int = 0
    total_tokens: int = 0
    total_items: int = 0
    headroom_tokens: int = 0
    over_budget: bool = False
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
        seen_ids = set()
        for row in rows:
            if row.item_id is not None:
                if row.item_id in seen_ids:
                    raise ValueError(
                        f"a panel row named {row.item_id!r} "
                        f"already exists")
                seen_ids.add(row.item_id)
        object.__setattr__(self, "rows", rows)
        object.__setattr__(
            self, "budget_tokens", _check_budget(self.budget_tokens))
        object.__setattr__(
            self, "total_tokens",
            _check_count(self.total_tokens, "a panel's total tokens"))
        object.__setattr__(
            self, "total_items",
            _check_count(self.total_items, "a panel's total items"))
        object.__setattr__(
            self, "headroom_tokens",
            _check_headroom(self.headroom_tokens, "a panel's headroom"))
        if not isinstance(self.over_budget, bool):
            raise ValueError(
                f"a panel's over-budget state must be true or "
                f"false, got {self.over_budget!r}")
        total = sum(row.tokens for row in rows)
        if self.total_tokens != total:
            raise ValueError(
                "a panel's token total must be its own "
                "rows' sum")
        if self.total_items != len(rows):
            raise ValueError(
                "a panel's item total must be its own "
                "rows' count")
        if self.headroom_tokens != self.budget_tokens - self.total_tokens:
            raise ValueError(
                "a panel's headroom must be its own budget "
                "minus its total")
        if self.over_budget != (self.total_tokens > self.budget_tokens):
            raise ValueError(
                "a panel's over-budget state must be its own "
                "total against its budget")
        for row in rows:
            if row.share_percent != _share_percent(row.tokens, total):
                raise ValueError(
                    "a panel row's share must be its own "
                    "tokens' share of the panel's total")
        object.__setattr__(self, "account", _check_account(self.account))

    def row_for(self, item_id: Any) -> PanelRow:
        """The row one item id names in this panel."""
        wanted = normalize_member_id(item_id)
        for row in self.rows:
            if row.item_id == wanted:
                return row
        raise KeyError(f"no row in the panel: item {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "context_budget_panel",
            "slice": CONTEXT_BUDGET_SLICE,
            "panel_id": self.panel_id,
            "rows": [row.to_record() for row in self.rows],
            "budget_tokens": self.budget_tokens,
            "total_tokens": self.total_tokens,
            "total_items": self.total_items,
            "headroom_tokens": self.headroom_tokens,
            "over_budget": self.over_budget,
            "account": list(self.account),
        }


def derive_panel(source: Any, budget_tokens: Any = None) -> ContextPanel:
    """Derive the panel from context items and their budget.

    The rows are the items themselves, in held
    order, each with its share of the whole; the
    totals are the items' own counts and the
    account is read off the rows and totals.
    *source* is a panel book, a registry or the
    items themselves; a bare item list names its
    budget through *budget_tokens*. An empty
    source refuses - a panel of nothing is no
    panel.
    """
    entries, budget = _held_items_and_budget(source, budget_tokens)
    if not entries:
        raise ValueError("a panel needs at least one context item")
    total = sum(entry.tokens for entry in entries)
    rows = tuple(
        PanelRow(
            kind=entry.kind, title=entry.title,
            source=entry.source, reason=entry.reason,
            tokens=entry.tokens,
            share_percent=_share_percent(entry.tokens, total),
            item_id=entry.item_id)
        for entry in entries)
    headroom = budget - total
    over = total > budget
    return ContextPanel(
        rows=rows,
        budget_tokens=budget,
        total_tokens=total,
        total_items=len(entries),
        headroom_tokens=headroom,
        over_budget=over,
        account=_panel_account(rows, budget, total, headroom, over))


def validate_panel(panel: Any, source: Any = None) -> ContextPanel:
    """Validate one panel into a ContextPanel.

    Accepts a ContextPanel or a mapping naming
    ``rows`` (or ``items``), a ``budget_tokens``
    (or ``budget``), a ``total_tokens`` (or
    ``total``), a ``total_items``, a
    ``headroom_tokens`` (or ``headroom``), an
    ``over_budget`` state (or ``over``), an
    ``account`` (or ``statements``) and an
    optional ``panel_id`` (or ``id``). With
    *source* given, the panel is judged against
    the panel derived from those items: a stored
    panel whose rows, totals or account disagree
    with the derived panel refuses. A panel
    naming no account refuses too.
    """
    if isinstance(panel, ContextPanel):
        current = panel
    elif isinstance(panel, dict):
        unknown = set(panel) - _PANEL_KEYS
        if unknown:
            raise ValueError(
                "unknown panel keys: %s" % ", ".join(sorted(unknown)))
        rows = _pick_any(panel, ("rows", "items"), "rows")
        if rows is None:
            raise ValueError("a panel is missing its rows")
        budget = _pick_any(panel, ("budget_tokens", "budget"), "budgets")
        if budget is None:
            raise ValueError("a panel is missing its budget")
        total = _pick_any(panel, ("total_tokens", "total"), "totals")
        if total is None:
            raise ValueError("a panel is missing its total tokens")
        total_items = _pick_any(panel, ("total_items",), "item totals")
        if total_items is None:
            raise ValueError("a panel is missing its total items")
        headroom = _pick_any(
            panel, ("headroom_tokens", "headroom"), "headrooms")
        if headroom is None:
            raise ValueError("a panel is missing its headroom")
        over = _pick_any(panel, ("over_budget", "over"), "over states")
        if over is None:
            raise ValueError("a panel is missing its over-budget state")
        if not isinstance(over, bool):
            raise ValueError(
                f"a panel's over-budget state must be true or "
                f"false, got {over!r}")
        account = _pick_any(panel, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError("a panel names no account of its own")
        kwargs: Dict[str, Any] = {
            "rows": rows, "budget_tokens": budget,
            "total_tokens": total, "total_items": total_items,
            "headroom_tokens": headroom, "over_budget": over,
            "account": account}
        panel_id = _pick_any(panel, ("panel_id", "id"), "panel ids")
        if panel_id is not None:
            kwargs["panel_id"] = panel_id
        current = ContextPanel(**kwargs)
    else:
        raise ValueError(f"a panel must be a mapping, got {panel!r}")
    if source is not None:
        derived = derive_panel(source, current.budget_tokens)
        if (current.rows != derived.rows
                or current.budget_tokens != derived.budget_tokens
                or current.total_tokens != derived.total_tokens
                or current.total_items != derived.total_items
                or current.headroom_tokens != derived.headroom_tokens
                or current.over_budget != derived.over_budget
                or current.account != derived.account):
            raise ValueError(
                "a stored panel disagrees with the panel "
                "derived from its items")
    return current


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> ContextPanel:
    """Build one validated panel, from a mapping or field words."""
    if isinstance(panel, ContextPanel) and not kwargs:
        return validate_panel(panel, source)
    if isinstance(panel, dict) or panel is None:
        merged: Dict[str, Any] = {}
        if isinstance(panel, dict):
            merged.update(panel)
        merged.update(kwargs)
        return validate_panel(merged, source)
    return validate_panel(panel, source)


# ---------------------------------------------------------------------
# The budget panel book: items in held order, derivations judged.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ContextBudgetPanel:
    """One context budget panel book: a budget and its items.

    ``budget_tokens`` is the context budget the
    panel accounts against; ``items`` are the
    context item records, in held order;
    ``meters`` and ``panels`` are the panel's
    derivations - a meter and a panel of the
    book, judged against the book's records by
    :func:`validate_book`; ``budget_note`` is the
    book's own note. This book is the panel file's
    shape: the shipped example is one book, and a
    real panel file is a new file in this shape.
    """

    title: str = ""
    budget_tokens: int = 0
    items: Tuple[ContextItem, ...] = ()
    meters: Tuple[ContextMeter, ...] = ()
    panels: Tuple[ContextPanel, ...] = ()
    budget_note: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a panel's title"))
        object.__setattr__(
            self, "budget_tokens", _check_budget(self.budget_tokens))
        if isinstance(self.items, (str, bytes)) \
                or not isinstance(self.items, (list, tuple)):
            raise ValueError(
                f"a panel's items must be a list of item "
                f"records, got {self.items!r}")
        items = tuple(_check_item_ref(e) for e in self.items)
        if not items:
            raise ValueError(
                "a context budget panel holds at least one "
                "context item")
        seen_ids = set()
        for entry in items:
            if entry.item_id is not None:
                if entry.item_id in seen_ids:
                    raise ValueError(
                        f"a context item named {entry.item_id!r} "
                        f"already exists")
                seen_ids.add(entry.item_id)
        object.__setattr__(self, "items", items)
        if isinstance(self.meters, (str, bytes)) \
                or not isinstance(self.meters, (list, tuple)):
            raise ValueError(
                f"a panel's meters must be a list of meters, "
                f"got {self.meters!r}")
        meters = tuple(
            m if isinstance(m, ContextMeter) else validate_meter(m)
            for m in self.meters)
        seen_meters = set()
        for meter in meters:
            if meter.meter_id is not None:
                if meter.meter_id in seen_meters:
                    raise ValueError(
                        f"a meter named {meter.meter_id!r} "
                        f"already exists")
                seen_meters.add(meter.meter_id)
        object.__setattr__(self, "meters", meters)
        if isinstance(self.panels, (str, bytes)) \
                or not isinstance(self.panels, (list, tuple)):
            raise ValueError(
                f"a panel's panels must be a list of panels, "
                f"got {self.panels!r}")
        panels = tuple(
            p if isinstance(p, ContextPanel) else validate_panel(p)
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
        if not isinstance(self.budget_note, str):
            raise ValueError("a panel's note must be text")
        object.__setattr__(
            self, "budget_note", self.budget_note.strip())

    def item_for(self, item_id: Any) -> ContextItem:
        """The context item one id names in this panel."""
        wanted = normalize_member_id(item_id)
        for entry in self.items:
            if entry.item_id == wanted:
                return entry
        raise KeyError(f"no context item in the panel: {wanted!r}")

    def items_for_kind(self, kind: Any) -> Tuple[ContextItem, ...]:
        """Every item of one kind, in held order."""
        wanted = normalize_kind(kind)
        return tuple(e for e in self.items if e.kind == wanted)

    def meter_for(self, meter_id: Any) -> ContextMeter:
        """The meter one id names in this panel."""
        wanted = normalize_member_id(meter_id)
        for meter in self.meters:
            if meter.meter_id == wanted:
                return meter
        raise KeyError(f"no meter in the panel: {wanted!r}")

    def panel_for(self, panel_id: Any) -> ContextPanel:
        """The derived panel one id names in this panel book."""
        wanted = normalize_member_id(panel_id)
        for panel in self.panels:
            if panel.panel_id == wanted:
                return panel
        raise KeyError(f"no panel in the panel book: {wanted!r}")

    def item_ids(self) -> Tuple[str, ...]:
        """Every held item id, in held order."""
        return tuple(e.item_id for e in self.items if e.item_id)

    def kinds(self) -> Tuple[str, ...]:
        """Every held item's kind, in held order."""
        return tuple(e.kind for e in self.items)

    def total_tokens(self) -> int:
        """Every held item's tokens summed, derived at call time."""
        return sum(e.tokens for e in self.items)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "context_budget_book",
            "slice": CONTEXT_BUDGET_SLICE,
            "title": self.title,
            "budget_tokens": self.budget_tokens,
            "item_ids": list(self.item_ids()),
            "item_count": len(self.items),
            "meter_count": len(self.meters),
            "panel_count": len(self.panels),
            "total_tokens": self.total_tokens(),
        }


def validate_book(data: Any, *, require_example: bool = False) -> ContextBudgetPanel:
    """Validate one context budget mapping into a ContextBudgetPanel.

    The mapping names a ``schema`` (the context
    budget schema word), a ``guide`` mapping (its
    ``title``), a ``budget_tokens`` budget (or
    ``budget``), an ``entries`` list (or
    ``items``) and optional ``meters`` and
    ``panels`` lists. Every record stands on its
    own validation, then the whole is judged:
    item ids unique, and every stored meter and
    panel judged against the book's own items.
    With ``require_example`` the shipped example
    is held to its pinned shape: the pinned
    title, budget, records and totals, and the
    meter's and panel's pinned accounts
    word-for-word. Problems raise
    :class:`ValidationError` or ``ValueError``.
    """
    if isinstance(data, ContextBudgetPanel):
        return data
    if not isinstance(data, dict):
        raise ValidationError(
            f"a context budget panel must be a mapping, got {data!r}")
    unknown = set(data) - _CONTEXT_BUDGET_KEYS
    if unknown:
        raise ValidationError(
            "unknown context budget keys: %s" % ", ".join(sorted(unknown)))
    if data.get("schema") != CONTEXT_BUDGET_SCHEMA:
        raise ValidationError(
            f"a context budget panel must carry schema "
            f"{CONTEXT_BUDGET_SCHEMA!r}, got {data.get('schema')!r}")
    entries = _pick_any(data, ("entries", "items"), "entries")
    if entries is None:
        raise ValidationError("a context budget panel is missing its entries")
    if not isinstance(entries, (list, tuple)):
        raise ValidationError("a context budget panel's entries must be a list")
    budget = _pick_any(data, ("budget_tokens", "budget"), "budgets")
    if budget is None:
        raise ValidationError("a context budget panel is missing its budget")
    if data.get("meters") is not None \
            and not isinstance(data["meters"], (list, tuple)):
        raise ValidationError("a context budget panel's meters must be a list")
    if data.get("panels") is not None \
            and not isinstance(data["panels"], (list, tuple)):
        raise ValidationError("a context budget panel's panels must be a list")
    head = data.get("guide") or {}
    if not isinstance(head, dict):
        raise ValidationError("a context budget panel's guide must be a mapping")
    unknown_head = set(head) - _BOOK_KEYS
    if unknown_head:
        raise ValidationError(
            "unknown guide keys: %s" % ", ".join(sorted(unknown_head)))
    try:
        title = _pick_any(head, ("title", "name"), "titles")
        if title is None:
            raise ValidationError("a context budget panel is missing its title")
        note = data.get("budget_note") or ""
        if not isinstance(note, str):
            raise ValidationError("a context budget panel's note must be text")
        book = ContextBudgetPanel(
            title=title, budget_tokens=budget, items=tuple(entries),
            meters=tuple(data.get("meters") or ()),
            panels=tuple(data.get("panels") or ()),
            budget_note=note)
        for meter in book.meters:
            validate_meter(meter, book)
        for panel in book.panels:
            validate_panel(panel, book)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    if require_example:
        if book.title != _EXAMPLE_TITLE:
            raise ValidationError(
                "the shipped example context budget panel's title "
                "is not the pinned title")
        if book.budget_tokens != _EXAMPLE_BUDGET:
            raise ValidationError(
                "the shipped example's budget is not the pinned budget")
        if book.item_ids() != _EXAMPLE_ITEM_IDS:
            raise ValidationError(
                "the shipped example's context items are not "
                "the pinned records")
        if book.kinds() != _EXAMPLE_KINDS:
            raise ValidationError(
                "the shipped example's kinds are not the pinned kinds")
        derived = derive_meter(book)
        totals = (
            derived.total_tokens, derived.total_items,
            derived.headroom_tokens, derived.usage_percent)
        if totals != _EXAMPLE_TOTALS:
            raise ValidationError(
                "the shipped example's items do not derive "
                "their pinned totals")
        meter = book.meter_for(_EXAMPLE_METER_ID)
        if meter.account != _EXAMPLE_METER_ACCOUNT:
            raise ValidationError(
                "the shipped example meter does not carry "
                "its pinned account word-for-word")
        panel = book.panel_for(_EXAMPLE_PANEL_ID)
        if tuple(r.item_id for r in panel.rows) != _EXAMPLE_ITEM_IDS:
            raise ValidationError(
                "the shipped example panel does not name "
                "its pinned rows")
        if panel.account != _EXAMPLE_PANEL_ACCOUNT:
            raise ValidationError(
                "the shipped example panel does not carry "
                "its pinned account word-for-word")
        first = book.items[0]
        if first.kind != "system" or first.tokens != 640:
            raise ValidationError(
                "the shipped example's first item is not "
                "its pinned system prompt")
    return book


def build_budget_panel(panel: Any = None, **kwargs: Any) -> ContextBudgetPanel:
    """Build one validated panel book, from a mapping or field words."""
    if isinstance(panel, ContextBudgetPanel) and not kwargs:
        return panel
    if isinstance(panel, dict):
        if "entries" in panel or "items" in panel or "schema" in panel:
            return validate_book(panel)
        merged: Dict[str, Any] = dict(panel)
        merged.update(kwargs)
        return ContextBudgetPanel(**merged)
    if panel is None:
        return ContextBudgetPanel(**kwargs)
    raise ValueError(f"a context budget panel is needed, got {panel!r}")


def _book_from(data: Any, *, require_example: bool) -> ContextBudgetPanel:
    try:
        return validate_book(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_context_budget(
        data: Optional[Dict[str, Any]] = None) -> ContextBudgetPanel:
    """Load and validate the shipped example panel (or *data*).

    The shipped file is held to the example check:
    the pinned title, budget, item records, meter
    and panel - the M-146 boundary panel, one item
    of every kind the shipped context system
    holds - so the shipped panel covers the
    account this slice exists to hold.
    """
    raw = data if data is not None else load_resource(CONTEXT_BUDGET_RESOURCE)
    return _book_from(raw, require_example=True)


def load_context_budget_file(path: Any) -> ContextBudgetPanel:
    """Load and validate a context budget panel from a file at *path*.

    Any file in the context budget shape, anywhere
    on disk, validated whole - a malformed file
    raises :class:`ValidationError` naming the
    problem, and a missing file raises
    ``FileNotFoundError``. The example check is
    not held: a real panel stands on its own
    records.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _book_from(raw, require_example=False)


# ---------------------------------------------------------------------
# Live roads: measure real texts, and read a compiled context.
# ---------------------------------------------------------------------


def measure_item(kind: Any, title: Any, source: Any, reason: Any,
                 text: Any, *, item_id: Any = None,
                 estimator: Any = None) -> ContextItem:
    """Measure one real text into a context item.

    The item's token count is the shipped
    ``TokenEstimator``'s count of *text*, composed
    by import - never a second counter. With no
    estimator named, a default estimator is made
    (``tiktoken`` when importable, the heuristic
    otherwise, exactly as the shipped layer
    reports); tests name
    ``TokenEstimator(prefer_tiktoken=False)`` for
    the deterministic heuristic backend.
    """
    if not isinstance(text, str):
        raise ValueError(f"a measured text must be text, got {text!r}")
    counter = estimator if estimator is not None else TokenEstimator()
    return ContextItem(
        kind=kind, title=title, source=source, reason=reason,
        tokens=counter.count(text), item_id=item_id)


def measure_panel(title: Any, budget_tokens: Any, specs: Any, *,
                  estimator: Any = None) -> ContextBudgetPanel:
    """Measure real texts into one whole context budget panel.

    Each spec is a mapping naming an item's
    ``kind``, ``title``, ``source`` and ``reason``
    (with the item spellings of
    :func:`validate_item`) plus its ``text``; the
    item's tokens are measured from that text
    through the one estimator. A spec naming
    ``tokens`` refuses - measured items name no
    count of their own - and unknown keys refuse.
    """
    if isinstance(specs, (str, bytes)) \
            or not isinstance(specs, (list, tuple)):
        raise ValueError(f"measured specs must be a list, got {specs!r}")
    counter = estimator if estimator is not None else TokenEstimator()
    items = []
    for spec in specs:
        if not isinstance(spec, dict):
            raise ValueError(f"a measured spec must be a mapping, got {spec!r}")
        unknown = set(spec) - _ITEM_KEYS - {"text"}
        if unknown:
            raise ValueError(
                "unknown measured-spec keys: %s"
                % ", ".join(sorted(unknown)))
        if "tokens" in spec or "token_count" in spec:
            raise ValueError(
                "a measured spec names no tokens of its own: "
                "its count is measured from its text")
        if "text" not in spec:
            raise ValueError("a measured spec is missing its text")
        fields = {k: v for k, v in spec.items() if k != "text"}
        probe = build_item(fields, tokens=0)
        items.append(measure_item(
            probe.kind, probe.title, probe.source, probe.reason,
            spec["text"], item_id=probe.item_id, estimator=counter))
    return ContextBudgetPanel(
        title=title, budget_tokens=budget_tokens, items=tuple(items))


def _block_field(block: Any, name: str, default: Any = None) -> Any:
    if isinstance(block, dict):
        return block.get(name, default)
    return getattr(block, name, default)


def _kind_for_block(source_word: str, name: str,
                    provenance: Dict[str, Any]) -> str:
    """One compiled block's kind, by the stated rule.

    The block's provenance kind answers first
    (``system`` is system; ``tool-round`` is a
    tool result); then the source and block name
    are read for the shipped sources' own words
    (instructions, the repo map, the file-shaped
    sources); an unclassified block is a ``note``.
    """
    prov_kind = provenance.get("kind")
    if prov_kind == "system":
        return "system"
    if prov_kind == "tool-round":
        return "tool_result"
    hay = f"{source_word} {name}".lower()
    if "instruction" in hay:
        return "instruction"
    if "repo-map" in hay or "repo_map" in hay or "map" in hay:
        return "map_section"
    if "system" in hay:
        return "system"
    if "tool" in hay:
        return "tool_result"
    if "history" in hay or "turn" in hay:
        return "history"
    if "note" in hay:
        return "note"
    if "file" in hay or "diff" in hay or "symbol" in hay \
            or "semantic" in hay or "depend" in hay:
        return "file"
    return "note"


def _reason_for_block(source_word: str, priority: Any) -> str:
    if isinstance(priority, int) and priority <= 0:
        return (
            f"Mandatory context from source {source_word}: "
            f"priority {priority} blocks are always kept "
            f"by the compiler.")
    return (
        f"Context compiled from source {source_word} at "
        f"priority {priority}: kept inside the token "
        f"budget by the compiler.")


def _slug(name: str) -> str:
    raw = "".join(ch if ch.isalnum() else "-" for ch in name.lower())
    parts = [part for part in raw.split("-") if part]
    slug = "-".join(parts)[:40].strip("-")
    return slug or "block"


def panel_from_compiled(compiled: Any, *,
                        title: Any = "Compiled context panel",
                        budget_tokens: Any = None,
                        estimator: Any = None) -> ContextBudgetPanel:
    """Build a panel from a compiled context's blocks.

    Duck-typed: *compiled* is a compiled context
    (its ``blocks`` and ``budget_tokens`` read by
    attribute or mapping key) or the blocks
    themselves, in which case *budget_tokens*
    names the budget. Each block becomes one
    item, in block order: its title is the
    block's name, its source is the block's
    provenance source (``compiled-context`` when
    the block names none), its tokens are the
    block's own count - counted from its content
    through the estimator only when the block
    carries none - its reason is read off its
    priority and source, and its kind is read by
    the rule in :func:`_kind_for_block`. Item ids
    are deterministic: ``ctx-<position>-<slug>``
    of the block's name. No compiler code is
    imported: the blocks are read as they are.
    """
    if isinstance(compiled, (list, tuple)):
        blocks = list(compiled)
        budget = budget_tokens
    else:
        blocks = _block_field(compiled, "blocks")
        if blocks is None:
            raise ValueError(
                f"a compiled context with blocks is needed, "
                f"got {compiled!r}")
        blocks = list(blocks)
        budget = budget_tokens
        if budget is None:
            budget = _block_field(compiled, "budget_tokens")
    if budget is None:
        raise ValueError(
            "a compiled context panel needs a budget: "
            "name budget_tokens")
    counter = estimator if estimator is not None else TokenEstimator()
    items = []
    for index, block in enumerate(blocks):
        name = _block_field(block, "name") or f"block-{index + 1}"
        if not isinstance(name, str):
            name = str(name)
        content = _block_field(block, "content") or ""
        tokens = _block_field(block, "tokens") or 0
        if not tokens and content:
            tokens = counter.count(content)
        priority = _block_field(block, "priority", 5)
        provenance = _block_field(block, "provenance") or {}
        if not isinstance(provenance, dict):
            provenance = {}
        source_word = provenance.get("source") or "compiled-context"
        if not isinstance(source_word, str):
            source_word = str(source_word)
        items.append(ContextItem(
            kind=_kind_for_block(source_word, name, provenance),
            title=name,
            source=source_word,
            reason=_reason_for_block(source_word, priority),
            tokens=tokens,
            item_id=f"ctx-{index + 1}-{_slug(name)}"))
    return ContextBudgetPanel(
        title=title, budget_tokens=budget, items=tuple(items))


# ---------------------------------------------------------------------
# The registry model: one panel held item by item, in held order.
# ---------------------------------------------------------------------


class ContextBudgetRegistry:
    """One session's context budget panel, held item by item.

    The registry holds item records and the one
    budget they account against, never meters or
    panels: both are derivations, read off held
    items at call time, so nothing here can hold
    a figure stale.
    """

    def __init__(self, book: Any = None,
                 budget_tokens: Any = None) -> None:
        self._title: Optional[str] = None
        self._budget_tokens: Optional[int] = (
            _check_budget(budget_tokens)
            if budget_tokens is not None else None)
        self._entries: Dict[str, ContextItem] = {}
        self._order: list = []
        self._next_entry = 1
        if book is not None:
            self.register_panel(book)

    @property
    def budget_tokens(self) -> Optional[int]:
        """The budget the held items account against, if one is named."""
        return self._budget_tokens

    def set_budget(self, budget_tokens: Any) -> int:
        """Name the budget the held items account against.

        A budget already named here refuses a
        different one; naming the same budget
        again stands.
        """
        budget = _check_budget(budget_tokens)
        if self._budget_tokens is not None \
                and budget != self._budget_tokens:
            raise ValueError(
                "this registry already holds a budget of "
                f"{self._budget_tokens} tokens")
        self._budget_tokens = budget
        return budget

    def _fresh_item_id(self, held_ids: Any) -> str:
        while f"item-{self._next_entry}" in held_ids:
            self._next_entry += 1
        fresh = f"item-{self._next_entry}"
        self._next_entry += 1
        return fresh

    def register_item(self, item: Any) -> ContextItem:
        """Register one context item into the held panel.

        A record with no id is given a deterministic
        ``item-N`` id. A record id already standing
        here refuses.
        """
        validated = build_item(item)
        held_ids = set(self._entries)
        if validated.item_id is not None \
                and validated.item_id in held_ids:
            raise ValueError(
                f"a context item named "
                f"{validated.item_id!r} already exists")
        if validated.item_id is None:
            validated = replace(
                validated,
                item_id=self._fresh_item_id(held_ids))
        self._entries[validated.item_id] = validated
        self._order.append(validated.item_id)
        return validated

    def register_panel(self, panel: Any) -> ContextBudgetPanel:
        """Register every item of one panel book, in order.

        The first panel held sets the title and the
        budget; a later panel under a different
        title, or against a different budget,
        refuses, as does a panel naming a held item
        id. The panel's meters and panels are
        derivations, not holdings, and are not held.
        """
        validated = build_budget_panel(panel)
        if self._title is not None and validated.title != self._title:
            raise ValueError(
                "this registry already holds a context budget "
                "panel under a different title")
        if self._budget_tokens is not None \
                and validated.budget_tokens != self._budget_tokens:
            raise ValueError(
                "this registry already holds a different budget")
        for entry in validated.items:
            if entry.item_id in self._entries:
                raise ValueError(
                    f"a context item named "
                    f"{entry.item_id!r} already exists")
        self._title = validated.title
        self._budget_tokens = validated.budget_tokens
        for entry in validated.items:
            self.register_item(entry)
        return self.panel()

    def get_item(self, item_id: Any) -> ContextItem:
        """The context item one id names among the held records."""
        wanted = normalize_member_id(item_id)
        if wanted not in self._entries:
            raise KeyError(f"unknown context item: {wanted!r}")
        return self._entries[wanted]

    def list_items(self) -> Tuple[ContextItem, ...]:
        """Every held context item, in the order they were held."""
        return tuple(self._entries[e] for e in self._order)

    def panel(self) -> ContextBudgetPanel:
        """The held items as one validated panel book."""
        if self._title is None:
            raise ValueError("no context budget panel is held yet")
        if self._budget_tokens is None:
            raise ValueError(
                "the held items name no budget yet: a meter "
                "and a panel need the budget they account against")
        return ContextBudgetPanel(
            title=self._title, budget_tokens=self._budget_tokens,
            items=self.list_items())

    def meter(self) -> ContextMeter:
        """Derive the meter of the held items, at call time."""
        return derive_meter(self)

    def panel_view(self) -> ContextPanel:
        """Derive the panel of the held items, at call time."""
        return derive_panel(self)


# ---------------------------------------------------------------------
# Context budget news, shaped as session records.
# ---------------------------------------------------------------------


def item_record(item: Any) -> Dict[str, Any]:
    """The session-news record of one context item."""
    current = item if isinstance(item, ContextItem) \
        else build_item(item)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.title} ({current.kind}) holds "
        f"{current.tokens} tokens in the context: "
        f"{current.reason}")
    return record


def meter_record(meter: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one meter.

    With *source* given, the meter is first judged
    against the items it belongs to.
    """
    current = validate_meter(meter, source)
    record = current.to_record()
    record["news"] = True
    if current.over_budget:
        record["headline"] = (
            f"Context meter: {current.total_tokens} of "
            f"{current.budget_tokens} tokens used - over "
            f"budget by {-current.headroom_tokens}.")
    else:
        record["headline"] = (
            f"Context meter: {current.total_tokens} of "
            f"{current.budget_tokens} tokens used, "
            f"{current.headroom_tokens} tokens of headroom.")
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived panel.

    With *source* given, the panel is first judged
    against the items it belongs to.
    """
    current = validate_panel(panel, source)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"What's in the context and why: "
        f"{current.total_items} item(s), "
        f"{current.total_tokens} tokens against a "
        f"budget of {current.budget_tokens}.")
    return record


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one context budget panel book."""
    current = book if isinstance(book, ContextBudgetPanel) \
        else build_budget_panel(book)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Context budget panel {current.title}: "
        f"{record['item_count']} item(s), "
        f"{record['total_tokens']} tokens against a "
        f"budget of {current.budget_tokens}.")
    return record


def plain_words(item: Any) -> str:
    """One context item, in one plain sentence."""
    current = item if isinstance(item, ContextItem) \
        else build_item(item)
    return (
        f"{current.title} - {current.kind} from "
        f"{current.source}: {current.reason} It holds "
        f"{current.tokens} tokens of the context.")


def meter_plain_words(source: Any) -> str:
    """The meter in plain words, in full.

    Accepts a ContextMeter or a ContextBudgetPanel.
    The meter is told whole - its figures and its
    account.
    """
    if isinstance(source, ContextMeter):
        meter = validate_meter(source)
        title = None
    elif isinstance(source, ContextBudgetPanel):
        meter = derive_meter(source)
        title = source.title
    else:
        raise ValueError(f"a context budget source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append(
        f"Meter: {meter.total_tokens} of {meter.budget_tokens} "
        f"tokens used ({meter.usage_percent:.1f}%), "
        f"{meter.headroom_tokens} tokens of headroom.")
    lines.extend(meter.account)
    return "\n".join(lines)


def panel_plain_words(source: Any) -> str:
    """The panel in plain words, in full.

    Accepts a ContextPanel or a ContextBudgetPanel.
    The panel is told whole - its rows and its
    account.
    """
    if isinstance(source, ContextPanel):
        panel = validate_panel(source)
        title = None
    elif isinstance(source, ContextBudgetPanel):
        panel = derive_panel(source)
        title = source.title
    else:
        raise ValueError(f"a context budget source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("What's in the context and why:")
    for row in panel.rows:
        lines.append(
            f"{row.title} ({row.kind}, {row.tokens} tokens) - "
            f"{row.reason}")
    lines.extend(panel.account)
    return "\n".join(lines)


# ---------------------------------------------------------------------
# Screens: the formatters and the shared /contextbudget grammar.
# ---------------------------------------------------------------------


def _source_panel(source: Any) -> ContextBudgetPanel:
    if source is None:
        return load_context_budget()
    if isinstance(source, ContextBudgetRegistry):
        return source.panel()
    if isinstance(source, ContextBudgetPanel):
        return source
    raise ValueError(f"a context budget panel is needed, got {source!r}")


def format_item(item: Any) -> str:
    """One context item as a screen line."""
    current = item if isinstance(item, ContextItem) \
        else build_item(item)
    return (
        f"{current.item_id or '-'}: {current.kind} - "
        f"{current.title} ({current.tokens} tokens "
        f"from {current.source})")


def format_items(source: Any = None, kind: Any = None) -> str:
    """Context items of one panel, in held order.

    With *kind* given, only the items of that
    kind are shown.
    """
    book = _source_panel(source)
    entries = book.items
    if kind is not None:
        wanted = normalize_kind(kind)
        entries = tuple(e for e in entries if e.kind == wanted)
    lines = [format_item(entry) for entry in entries]
    if not lines:
        lines.append("No context items are held.")
    return "\n".join(lines)


def format_meter(source: Any = None) -> str:
    """The meter as a screen block.

    Accepts a ContextMeter or a ContextBudgetPanel;
    a panel shows the meter it derives, its
    figures over its derived account.
    """
    if isinstance(source, ContextMeter):
        meter = validate_meter(source)
        lines: list = []
    else:
        book = _source_panel(source)
        meter = derive_meter(book)
        lines = [f"Meter in {book.title}:"]
    lines.append(
        f"Context meter: {meter.total_tokens} of "
        f"{meter.budget_tokens} tokens "
        f"({meter.usage_percent:.1f}% used), "
        f"{meter.headroom_tokens} tokens of headroom, "
        f"{meter.total_items} item(s).")
    for row in meter.kind_totals:
        lines.append(
            f"{row.kind}: {row.tokens} tokens "
            f"in {row.items} item(s)")
    lines.extend(meter.account)
    return "\n".join(lines)


def format_panel(source: Any = None) -> str:
    """The panel as a screen block: every item and why.

    Accepts a ContextPanel or a ContextBudgetPanel;
    a panel book shows the panel it derives, its
    rows over its derived account.
    """
    if isinstance(source, ContextPanel):
        panel = validate_panel(source)
        lines: list = []
    else:
        book = _source_panel(source)
        panel = derive_panel(book)
        lines = [f"Panel in {book.title}:"]
    lines.append("What's in the context and why:")
    for row in panel.rows:
        lines.append(
            f"{row.item_id or '-'}: {row.kind} - {row.title} "
            f"({row.tokens} tokens, {row.share_percent:.1f}% "
            f"of the context) - {row.reason}")
    lines.extend(panel.account)
    return "\n".join(lines)


def format_context_budget_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /contextbudget.

    With nothing named, the shipped example
    context budget panel is shown - the example
    this slice ships - so the screen is never
    empty.
    """
    book = _source_panel(source)
    lines = ["Context budget made visible (M-147) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_items(book))
    lines.append("")
    lines.append(format_meter(book))
    lines.append("")
    lines.append(format_panel(book))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_context_budget_args(args: Any) -> Tuple[str, Any]:
    """Parse the /contextbudget grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    context budget panel; ``item <item-id>``
    shows one context item; ``kind <kind>`` shows
    the items of one kind; ``meter`` shows the
    meter derived from the whole panel; ``panel``
    shows the panel derived from the whole panel
    book. Anything else is a usage error naming
    the grammar. Returns ``(action, value-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() in ("show", "list"):
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head in ("meter", "panel") and len(words) == 1:
        return (head, None)
    if head == "item" and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "kind" and len(words) == 2:
        try:
            return (head, normalize_kind(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
