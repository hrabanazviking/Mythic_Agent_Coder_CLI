"""The fuzzy everything picker (All-Features roadmap slice M-175).

Part VIII - The Beautiful Face - builds here. The
roadmap's words: *files, symbols, commands,
sessions, models, themes - one fuzzy finder
grammar everywhere.*

What already ships, and what this slice adds:

* The shipped tree holds the things a picker
  ranges over in separate rooms, each with its
  own road in and no road across: instruction
  files stand in their canon
  (``core/instruction_files.py``), the shipped
  screens' symbols stand in the M-171 TUI
  redesign charter (``core/tui_redesign_charter.py``),
  sessions stand in the multi-session book
  (``core/multi_session_projects.py``), models
  stand in the capability table
  (``core/model_capabilities.py``), and the
  shipped themes are named by the M-016
  accessibility baseline
  (``core/accessibility_baseline.py``) - while
  slash commands stand on the two chat surfaces
  alone, spelled once per surface. Nothing holds
  one candidate as data beside the others, and
  nothing judges a query the same way over all
  of them: every room is searched in its own
  grammar, or not searched at all.
* The M-171 TUI redesign charter judged the
  subagent picker modal (its S-06 row) KEEP and
  names M-175 as an owning slice: *when the
  fuzzy picker gives every choice one grammar,
  this list joins it; the auto-dismiss on change
  is re-judged there, and the heading takes
  plain words first* - its K-01 judgement strains
  because the heading speaks in costume where
  plain words would land first, and its K-09
  judgement strains because the dropdown
  dismisses the dialog the moment a value
  changes, so a browsing keystroke can commit a
  choice the user was only looking at.
* This slice is that one grammar, as a pure
  layer: one picker candidate validated as data
  WITH ITS PROVENANCE WHOLE - its kind in the
  closed kind set (file, symbol, command,
  session, model, theme, in the roadmap's own
  order), its label, its own detail line and its
  tags. One query grammar judges every kind the
  same way: the query text is read into word
  tokens by one token road, and a candidate's
  score is DERIVED from those tokens against the
  candidate's own label, tags and detail - never
  stored, never ranked by hand. A search is held
  as its own record - the query text, its kind
  filter in the closed filter set, its own words
  and its provenance whole. The panel is DERIVED
  for one held search (its rows the matched
  candidates in ranked order, carrying their
  derived scores and lines, its totals the
  candidates' own counts), and a verdict is
  DERIVED for the whole book under one search.
  Candidates are composed BY IMPORT from the
  shipped rooms the picker ranges over - an
  instruction file, a charter screen's symbol, a
  capability-table model, a multi-session
  session, a baseline-named theme - and a slash
  command candidate is judged by the command
  shape the surfaces speak. The shipped data
  file (``mythic_agent/data/fuzzy_picker.yaml``)
  holds one example book in exactly the shape a
  real picker file takes, a loader reads a
  picker file anywhere on disk, candidates and
  searches are shaped as session news, and a
  small in-memory registry model holds
  candidates and searches one by one. The agent
  layer owns holding candidates for a session
  and standing a search on them.

Honesty rules, enforced here and pinned by tests:

* **One grammar everywhere.** A query is parsed
  by the one token road whatever kind it ranges
  over, and scoring reads the candidate's own
  fields the same way for every kind - there is
  no per-kind grammar to drift apart, and a kind
  filter only narrows which candidates stand in
  the search, never how they are judged.
* **The score is derived, never stored.** A
  candidate carries no score and no rank: a
  mapping naming one refuses. A score exists
  only as the derivation of one query over one
  candidate, and a panel row is judged against
  that derivation - a stored row whose score
  disagrees with its query refuses.
* **Kinds stand in a closed set.** A candidate's
  kind is one of the roadmap's six - file,
  symbol, command, session, model, theme - read
  through its aliases onto the set; any other
  kind refuses, and the picker's panel counts
  kinds in the roadmap's own order.
* **Plain words first, and picking commits
  nothing.** The picker's own words are plain
  (the S-06 heading's lesson), and a search only
  ever LOOKS: standing a search holds the search
  as data and derives its panel - it opens no
  file, runs no command, loads no model, applies
  no theme and joins no session. The S-06
  auto-dismiss is re-judged here in the picker's
  own shape: a search commits no choice at all,
  so there is nothing a browsing keystroke can
  commit by accident.
* **Data only.** This layer holds candidates
  and searches as data: it opens nothing,
  executes nothing, renders no live UI, sends
  nothing, posts nothing, schedules nothing,
  calls no model and persists nothing - a match
  held here is a finding, never the act of
  opening the thing found.
"""

from __future__ import annotations

__all__ = [
    "FUZZY_PICKER_RESOURCE",
    "FUZZY_PICKER_SCHEMA",
    "FUZZY_PICKER_SLICE",
    "KIND_FILTERS",
    "KINDS",
    "PLAIN_EXPLANATION",
    "THE_FUZZY_PICKER_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "Any",
    "Dict",
    "FuzzyPanel",
    "FuzzyPickerBook",
    "FuzzyPickerRegistry",
    "FuzzyVerdict",
    "KindCount",
    "List",
    "Optional",
    "PickerCandidate",
    "PickerPanelRow",
    "PickerSearch",
    "Tuple",
    "book_record",
    "build_book",
    "build_candidate",
    "build_panel",
    "build_row",
    "build_search",
    "build_verdict",
    "candidate_from_command",
    "candidate_from_instruction_file",
    "candidate_from_model",
    "candidate_from_screen_review",
    "candidate_from_session",
    "candidate_from_theme",
    "candidate_record",
    "candidates_with_kind",
    "derive_panel",
    "derive_verdict",
    "format_book",
    "format_candidate",
    "format_fuzzy_picker_screen",
    "format_panel",
    "format_search",
    "format_verdict",
    "inspect_candidate_source",
    "line_of",
    "load_fuzzy_picker",
    "load_fuzzy_picker_file",
    "normalize_kind",
    "normalize_kind_filter",
    "panel_plain_words",
    "panel_record",
    "parse_fuzzy_picker_args",
    "parse_query",
    "plain_words",
    "rank_candidates",
    "score_of",
    "search_plain_words",
    "search_record",
    "total_candidates",
    "validate_book",
    "validate_candidate",
    "validate_panel",
    "validate_row",
    "validate_search",
    "validate_verdict",
    "verdict_plain_words",
    "verdict_record",
]

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .crew_members import normalize_member_id
from .validation import ValidationError

FUZZY_PICKER_SLICE = "M-175"

#: The longer name other layers cite for this slice.
THE_FUZZY_PICKER_SLICE = FUZZY_PICKER_SLICE

FUZZY_PICKER_RESOURCE = "fuzzy_picker.yaml"

FUZZY_PICKER_SCHEMA = "mythic.fuzzy_picker/1"

#: The kinds one candidate may stand under, in
#: the roadmap's own order: files, symbols,
#: commands, sessions, models, themes - one
#: fuzzy finder grammar everywhere.
KINDS = ("file", "symbol", "command", "session", "model", "theme")

_KIND_ALIASES = {
    "file": "file", "files": "file",
    "symbol": "symbol", "symbols": "symbol",
    "command": "command", "commands": "command",
    "session": "session", "sessions": "session",
    "model": "model", "models": "model",
    "theme": "theme", "themes": "theme",
}

#: The kind filters one search may carry, in
#: order: every kind at once, then each kind of
#: the closed set alone.
KIND_FILTERS = ("all",) + KINDS

_KIND_FILTER_ALIASES = {
    "all": "all", "every": "all", "everything": "all",
    "any": "all",
}
_KIND_FILTER_ALIASES.update(_KIND_ALIASES)

#: The words a whole book's verdict under one
#: search may carry: matched while the matches
#: span more than one kind, focused while they
#: stand in one kind alone, empty while no
#: candidate matches.
VERDICT_WORDS = ("matched", "focused", "empty")

_CANDIDATE_KEYS = frozenset({
    "candidate_id", "id", "kind", "type_of",
    "label", "name", "title",
    "detail", "description",
    "tags", "keywords",
    "recorded_on", "day", "date",
    "actor", "by", "who", "source",
    "origin_session", "session"})

_ROW_KEYS = frozenset({
    "candidate_id", "id", "kind", "label",
    "score", "line", "recorded_on"})

_KIND_COUNT_KEYS = frozenset({"kind", "items", "count"})

_PANEL_KEYS = frozenset({
    "panel_id", "id", "search_id", "search",
    "query_text", "query", "kind_filter", "filter",
    "rows", "matches",
    "total_candidates", "candidates",
    "total_matched", "matched",
    "kind_counts", "kinds",
    "as_of", "day", "account", "statements"})

_SEARCH_KEYS = frozenset({
    "search_id", "id", "seq", "sequence", "order",
    "text", "query", "query_text",
    "kind_filter", "filter", "kind",
    "detail", "reason",
    "recorded_on", "day", "date",
    "actor", "by", "who", "source",
    "origin_session", "session"})

_VERDICT_KEYS = frozenset({
    "total_candidates", "candidates",
    "total_matched", "matched",
    "distinct_kinds", "kinds",
    "earliest_on", "earliest", "latest_on", "latest",
    "verdict"})

_BOOK_KEYS = frozenset({"title", "name"})

_FUZZY_PICKER_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "canon_note", "guide", "candidates", "searches",
    "panels"})

_EXAMPLE_TITLE = "Fuzzy Picker at the M-174 slice boundary"

_EXAMPLE_CANDIDATE_IDS = (
    "cand-approval-file", "cand-approval-symbol",
    "cand-approval-command", "cand-approval-tests",
    "cand-sliceboard-command", "cand-m174-session",
    "cand-sonnet-model", "cand-viking-theme")

_EXAMPLE_FIRST_CANDIDATE_ID = "cand-approval-file"

_EXAMPLE_FIRST_CANDIDATE_LABEL = (
    "mythic_agent/core/approval_cards.py")

_EXAMPLE_PANEL_ID = "panel-m174-boundary"

_EXAMPLE_AS_OF = "2026-11-09"

_EXAMPLE_SEARCH_IDS = (
    "search-approval", "search-viking-theme")

PLAIN_EXPLANATION = (
    "The Fuzzy Everything Picker: files, symbols, "
    "commands, sessions, models and themes under "
    "one fuzzy finder grammar everywhere. A query "
    "is read into word tokens by the one token "
    "road whatever kind it ranges over, and a "
    "candidate's score is derived from those "
    "tokens against the candidate's own label, "
    "tags and detail - never stored, never ranked "
    "by hand. A kind filter narrows which "
    "candidates stand in a search, never how they "
    "are judged. Candidates are composed from the "
    "shipped rooms the picker ranges over - an "
    "instruction file, a charter screen's symbol, "
    "a capability-table model, a multi-session "
    "session, a baseline-named theme - each held "
    "with its provenance whole. This layer holds "
    "candidates and searches as data only: it "
    "opens nothing, executes nothing, renders no "
    "live UI, sends nothing, posts nothing, "
    "schedules nothing, calls no model and "
    "persists nothing - a match held here is a "
    "finding, never the act of opening the thing "
    "found, and a search commits no choice at all."
)

USAGE = (
    "Usage: /fuzzypicker, /fuzzypicker show, "
    "/fuzzypicker candidate <candidate-id>, "
    "/fuzzypicker search <search-id>, "
    "/fuzzypicker find <words>, "
    "/fuzzypicker kind <kind>, "
    "/fuzzypicker panel, /fuzzypicker verdict"
)

_TOKEN_RE = re.compile(r"[a-z0-9]+")


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


def _check_seq(value: Any) -> int:
    seq = _check_count(value, "a search's sequence")
    if seq < 1:
        raise ValueError(
            f"a search's sequence stands from 1, got {value!r}")
    return seq


def _check_word(value: Any, what: str) -> str:
    try:
        return normalize_member_id(value)
    except ValueError:
        raise ValueError(
            f"{what} must be one plain word, "
            f"got {value!r}") from None


def _check_day(value: Any, what: str = "a day") -> str:
    text = _clean_text(value, what)
    try:
        parsed = date.fromisoformat(text)
    except ValueError:
        raise ValueError(
            f"{what} must be an ISO date "
            f"(YYYY-MM-DD), got {text!r}") from None
    if parsed.isoformat() != text:
        raise ValueError(
            f"{what} must be an ISO date "
            f"(YYYY-MM-DD), got {text!r}")
    return text


def _check_tags(value: Any) -> Tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"a candidate's tags must be a list of words, "
            f"got {value!r}")
    tags = tuple(_check_word(t, "a tag") for t in value)
    if not tags:
        raise ValueError(
            "a candidate carries at least one tag: the "
            "tags are part of what a query is judged "
            "against")
    if len(tags) > 8:
        raise ValueError(
            f"a candidate carries at most 8 tags, "
            f"got {len(tags)}")
    if len({t.lower() for t in tags}) != len(tags):
        raise ValueError("a candidate names one tag twice")
    return tags


def normalize_kind(value: Any) -> str:
    """One kind word, read onto the closed kind set."""
    if not isinstance(value, str):
        raise ValueError(f"a kind must be a word, got {value!r}")
    kind = _KIND_ALIASES.get(value.strip().lower())
    if kind is None:
        raise ValueError(
            "a kind is one of %s, got %r"
            % ("/".join(KINDS), value))
    return kind


def normalize_kind_filter(value: Any) -> str:
    """One kind-filter word, read onto the closed filter set."""
    if not isinstance(value, str):
        raise ValueError(
            f"a kind filter must be a word, got {value!r}")
    kind_filter = _KIND_FILTER_ALIASES.get(value.strip().lower())
    if kind_filter is None:
        raise ValueError(
            "a kind filter is one of %s, got %r"
            % ("/".join(KIND_FILTERS), value))
    return kind_filter


def parse_query(text: Any) -> Tuple[str, ...]:
    """The one token road every query is parsed by.

    The query text is lowered and read into its
    word tokens - runs of letters and digits, in
    the order they stand - the same way for every
    kind the picker ranges over. This is the one
    grammar: no kind parses a query its own way.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"a query must be text, got {text!r}")
    tokens = tuple(_TOKEN_RE.findall(text.lower()))
    if not tokens:
        raise ValueError(
            f"a query names no word token, got {text!r}")
    return tokens


def _subsequence(token: str, label: str) -> bool:
    """True when *token*'s letters stand in *label* in order."""
    if not token:
        return False
    rest = iter(label)
    return all(any(ch == wanted for ch in rest) for wanted in token)


def score_of(candidate: Any, query: Any) -> int:
    """The score one candidate derives under one query.

    Read off the query's tokens against the
    candidate's own label, tags and detail - the
    same reading for every kind: an exact label
    token weighs most, a label the token opens
    weighs next, a label holding the token next,
    a label the token's letters thread in order
    least; a tag named whole outweighs a tag the
    token stands inside; the detail adds its small
    share. A query naming the label whole adds the
    exact-phrase weight. A candidate outside the
    query's kind filter derives no score at all.
    The score is derived at call time - it is
    never a field of the candidate.
    """
    current = _check_candidate_ref(candidate)
    if isinstance(query, PickerSearch):
        text, kind_filter = query.text, query.kind_filter
    elif isinstance(query, dict):
        text = _pick_any(
            query, ("text", "query", "query_text"), "query text")
        if text is None:
            raise ValueError("a query names no query text")
        named = _pick_any(
            query, ("kind_filter", "filter", "kind"), "kind filter")
        kind_filter = (
            normalize_kind_filter(named) if named is not None else "all")
    else:
        text, kind_filter = query, "all"
    if kind_filter != "all" and current.kind != kind_filter:
        return 0
    tokens = parse_query(text)
    label = current.label.lower()
    detail = current.detail.lower()
    tags = tuple(t.lower() for t in current.tags)
    score = 0
    for token in tokens:
        if token == label:
            score += 100
        elif label.startswith(token):
            score += 50
        elif token in label:
            score += 30
        elif _subsequence(token, label):
            score += 10
        if token in tags:
            score += 20
        elif any(token in tag for tag in tags):
            score += 10
        if token in detail:
            score += 5
    if " ".join(tokens) == label:
        score += 100
    return score


def line_of(candidate: Any) -> str:
    """The candidate line one picker candidate derives.

    Read off the candidate's label and kind alone:
    the thing found, and the kind it stands under.
    """
    current = _check_candidate_ref(candidate)
    return f"{current.label} - {current.kind}"


# ---------------------------------------------------------------------
# The candidate: one findable thing, held whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class PickerCandidate:
    """One picker candidate: one findable thing, held whole.

    ``kind`` is the candidate's kind in the closed
    kind set; ``label`` is the name the picker
    shows and the first field a query is judged
    against; ``detail`` is the candidate's own
    line of words; ``tags`` are the candidate's
    own words a query may name. The candidate
    carries NO score and NO rank - those are
    derived from a query at call time, never
    fields. The provenance - the day it was
    recorded, who recorded it, its source and the
    session it was recorded in - rides whole.
    """

    candidate_id: str
    kind: str
    label: str
    detail: str
    tags: Tuple[str, ...]
    recorded_on: str
    actor: str
    source: str
    origin_session: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "candidate_id",
            _check_word(self.candidate_id, "a candidate id"))
        object.__setattr__(self, "kind", normalize_kind(self.kind))
        object.__setattr__(
            self, "label", _check_title(self.label, "the label"))
        object.__setattr__(
            self, "detail",
            _check_long_text(self.detail, "the detail"))
        object.__setattr__(self, "tags", _check_tags(self.tags))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))
        object.__setattr__(
            self, "actor", _check_title(self.actor, "an actor"))
        object.__setattr__(
            self, "source", _check_title(self.source, "a source"))
        object.__setattr__(
            self, "origin_session",
            _check_word(self.origin_session, "an origin session"))

    @property
    def line(self) -> str:
        """The derived candidate line of this candidate."""
        return line_of(self)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "fuzzy_picker_candidate",
            "slice": FUZZY_PICKER_SLICE,
            "candidate_id": self.candidate_id,
            "kind": self.kind,
            "label": self.label,
            "detail": self.detail,
            "tags": list(self.tags),
            "line": self.line,
            "recorded_on": self.recorded_on,
            "actor": self.actor,
            "source": self.source,
            "origin_session": self.origin_session,
        }


def _check_candidate_ref(value: Any) -> PickerCandidate:
    if isinstance(value, PickerCandidate):
        return value
    return validate_candidate(value)


def validate_candidate(candidate: Any) -> PickerCandidate:
    """Judge one picker candidate whole and return it.

    A mapping is read through its spellings: a
    derived key (``score``, ``rank`` or ``line``)
    refuses - those are derived, never stored - as
    does any key the candidate does not carry, and
    two spellings naming two different values.
    """
    if isinstance(candidate, PickerCandidate):
        return candidate
    if not isinstance(candidate, dict):
        raise ValueError(
            f"a picker candidate must be a mapping, got {candidate!r}")
    unknown = set(candidate) - _CANDIDATE_KEYS
    if unknown:
        raise ValueError(
            f"a picker candidate carries unknown keys: "
            f"{sorted(unknown)}")
    if "type" in candidate:
        raise ValueError(
            "a picker candidate is judged without its news keys")

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(candidate, spellings, what)
        if value is None:
            raise ValueError(f"a picker candidate names no {what}")
        return value

    return PickerCandidate(
        candidate_id=_needed(("candidate_id", "id"), "candidate id"),
        kind=_needed(("kind", "type_of"), "kind"),
        label=_needed(("label", "name", "title"), "label"),
        detail=_needed(("detail", "description"), "detail"),
        tags=_needed(("tags", "keywords"), "tags"),
        recorded_on=_needed(
            ("recorded_on", "day", "date"), "day it was recorded"),
        actor=_needed(("actor", "by", "who"), "actor"),
        source=_needed(("source",), "source"),
        origin_session=_needed(
            ("origin_session", "session"), "origin session"),
    )


def build_candidate(candidate: Any = None, **kwargs: Any) -> PickerCandidate:
    """Build one candidate from a mapping, a candidate, or fields."""
    if kwargs:
        if candidate is not None:
            raise ValueError("a candidate is built one way at a time")
        candidate = kwargs
    return validate_candidate(candidate)


def candidate_from_instruction_file(
        entry: Any = None, *,
        candidate_id: Any,
        recorded_on: Any = "2026-11-09",
        actor: Any = "the coordinator",
        source: Any = "fuzzy picker",
        origin_session: Any = "session-m175",
        tags: Any = None) -> PickerCandidate:
    """Raise one file candidate over a shipped instruction file.

    The entry is judged by its own shipped judge
    first, by import: the candidate's label is the
    entry's path, its detail the entry's filename,
    origin and layer with its reason carried whole.
    """
    from .instruction_files import validate_entry
    if entry is None:
        raise ValueError(
            "an instruction file entry is needed to raise a candidate")
    held = validate_entry(entry)
    if tags is None:
        tags = ("file", "instructions")
    return PickerCandidate(
        candidate_id=candidate_id, kind="file",
        label=held.path,
        detail=(
            f"{held.filename}, a {held.origin} instruction "
            f"file at the {held.layer} layer: {held.reason}"),
        tags=tuple(tags),
        recorded_on=recorded_on, actor=actor,
        source=source, origin_session=origin_session)


def candidate_from_screen_review(
        review: Any = None, *,
        candidate_id: Any,
        recorded_on: Any = "2026-11-09",
        actor: Any = "the coordinator",
        source: Any = "fuzzy picker",
        origin_session: Any = "session-m175",
        tags: Any = None) -> PickerCandidate:
    """Raise one symbol candidate over a charter screen, by import.

    The review is a shipped M-171 charter
    ``ScreenReview``: the candidate's label is the
    screen's symbol, its detail the screen's title
    and surface with its charter verdict.
    """
    from .tui_redesign_charter import ScreenReview
    if not isinstance(review, ScreenReview):
        raise ValueError(
            "a shipped charter screen review is needed to "
            "raise a symbol candidate")
    if tags is None:
        tags = ("screen", "symbol")
    return PickerCandidate(
        candidate_id=candidate_id, kind="symbol",
        label=review.symbol,
        detail=(
            f"{review.title} at {review.surface} - the "
            f"charter's verdict on this screen is "
            f"{review.verdict}."),
        tags=tuple(tags),
        recorded_on=recorded_on, actor=actor,
        source=source, origin_session=origin_session)


def candidate_from_model(
        record: Any = None, *,
        candidate_id: Any,
        recorded_on: Any = "2026-11-09",
        actor: Any = "the coordinator",
        source: Any = "fuzzy picker",
        origin_session: Any = "session-m175",
        tags: Any = None) -> PickerCandidate:
    """Raise one model candidate over the capability table, by import.

    The record is a shipped M-027 ``ModelCapability``
    (or a mapping naming its model): the candidate's
    label is the model's name, its detail the
    providers it is listed under with its recorded
    notes carried whole.
    """
    from .model_capabilities import ModelCapability
    if isinstance(record, ModelCapability):
        held = record
    elif isinstance(record, dict) and isinstance(
            record.get("model"), str) and record.get("model"):
        from .model_capabilities import load_capabilities
        held = load_capabilities().for_model(record["model"])
        if held.model != record["model"]:
            raise ValueError(
                "no capability record stands under that model name")
    else:
        raise ValueError(
            "a shipped model capability record is needed to "
            "raise a model candidate")
    providers = ", ".join(held.providers) if held.providers else (
        "no provider")
    if tags is None:
        tags = ("model",)
    return PickerCandidate(
        candidate_id=candidate_id, kind="model",
        label=held.model,
        detail=(
            f"A model listed under {providers} in the "
            f"shipped capability table: {held.notes}"),
        tags=tuple(tags),
        recorded_on=recorded_on, actor=actor,
        source=source, origin_session=origin_session)


def candidate_from_session(
        session: Any = None, *,
        candidate_id: Any,
        recorded_on: Any = "2026-11-09",
        actor: Any = "the coordinator",
        source: Any = "fuzzy picker",
        origin_session: Any = "session-m175",
        tags: Any = None) -> PickerCandidate:
    """Raise one session candidate over a multi-session session.

    The session is judged by the shipped
    multi-session judge first, by import: the
    candidate's label is the session's title, its
    detail its project, branch and standing.
    """
    from .multi_session_projects import validate_session
    if session is None:
        raise ValueError(
            "a multi-session session is needed to raise a candidate")
    held = validate_session(session)
    if tags is None:
        tags = ("session",)
    return PickerCandidate(
        candidate_id=candidate_id, kind="session",
        label=held.title,
        detail=(
            f"A session on {held.project}, working branch "
            f"{held.branch} and standing {held.state}, "
            f"held under {held.session_ref}."),
        tags=tuple(tags),
        recorded_on=recorded_on, actor=actor,
        source=source, origin_session=origin_session)


def candidate_from_theme(
        name: Any = None, *,
        candidate_id: Any,
        recorded_on: Any = "2026-11-09",
        actor: Any = "the coordinator",
        source: Any = "fuzzy picker",
        origin_session: Any = "session-m175",
        tags: Any = None) -> PickerCandidate:
    """Raise one theme candidate over a shipped theme, by import.

    The theme name is judged against the shipped
    M-016 accessibility baseline by import - the
    core surface that names the shipped themes:
    a name the baseline does not audit refuses,
    and the candidate's detail carries the
    baseline's own verdict on that theme.
    """
    from .accessibility_baseline import load_baseline
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"a theme name is needed, got {name!r}")
    wanted = name.strip()
    baseline = load_baseline()
    for entry in baseline.contrast_entries:
        if entry.theme == wanted:
            if tags is None:
                tags = ("theme",)
            return PickerCandidate(
                candidate_id=candidate_id, kind="theme",
                label=wanted,
                detail=(
                    f"The shipped theme {wanted}, audited in "
                    f"the M-016 accessibility baseline with "
                    f"verdict {entry.verdict}."),
                tags=tuple(tags),
                recorded_on=recorded_on, actor=actor,
                source=source, origin_session=origin_session)
    raise ValueError(
        f"no shipped theme stands under the name {wanted!r} - "
        f"the baseline audits {', '.join(baseline.theme_names())}")


def candidate_from_command(
        command: Any = None, *,
        candidate_id: Any, detail: Any,
        recorded_on: Any = "2026-11-09",
        actor: Any = "the coordinator",
        source: Any = "fuzzy picker",
        origin_session: Any = "session-m175",
        tags: Any = None) -> PickerCandidate:
    """Raise one command candidate over a slash command.

    The command is judged by the shape the two
    chat surfaces speak: one word opening with a
    slash, in the surfaces' own spelling. The
    candidate's label is the command itself, its
    detail the caller's plain words for what the
    command does.
    """
    if not isinstance(command, str) or not command.startswith("/"):
        raise ValueError(
            f"a slash command opens with a slash, got {command!r}")
    _check_word(command[1:], "a command name")
    if command != command.lower() or " " in command:
        raise ValueError(
            f"a slash command is one lowercase word, got {command!r}")
    if tags is None:
        tags = ("command",)
    return PickerCandidate(
        candidate_id=candidate_id, kind="command",
        label=command, detail=detail,
        tags=tuple(tags),
        recorded_on=recorded_on, actor=actor,
        source=source, origin_session=origin_session)


def inspect_candidate_source(piece: Any) -> Dict[str, Any]:
    """Judge one raw candidate piece and name what it is.

    A piece shaped like a candidate - a mapping
    carrying a ``kind`` and a ``label`` - is read
    onto its closed kind without holding a
    candidate. Anything else is named
    not-a-candidate.
    """
    if not isinstance(piece, dict):
        return {"kind": None,
                "reason": "not a mapping - no candidate stands here"}
    kind_in = _pick_any(piece, ("kind", "type_of"), "kind")
    label = _pick_any(piece, ("label", "name", "title"), "label")
    if kind_in is None or label is None:
        return {"kind": None,
                "reason": "no kind or no label named - no candidate "
                          "stands here"}
    try:
        kind = normalize_kind(kind_in)
    except ValueError as exc:
        return {"kind": None, "label": label, "reason": str(exc)}
    return {
        "kind": kind, "label": label,
        "reason": "a candidate piece in the closed kind set"}


# ---------------------------------------------------------------------
# The search record: one query, held whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class PickerSearch:
    """One search, held as its own record.

    ``text`` is the query text, parsed by the one
    token road at judgement time; ``kind_filter``
    is the search's filter in the closed filter
    set - it narrows which candidates stand in the
    search, never how they are judged; ``detail``
    is the search's own words. ``seq`` is the
    search's place in the book's recorded order,
    from 1. The provenance rides whole. A search
    carries no results of its own: its panel and
    the book's verdict under it are derived.
    """

    seq: int
    text: str
    kind_filter: str
    detail: str
    recorded_on: str
    actor: str
    source: str
    origin_session: str
    search_id: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "seq", _check_seq(self.seq))
        text = _check_long_text(self.text, "the query text")
        parse_query(text)
        object.__setattr__(self, "text", text)
        object.__setattr__(
            self, "kind_filter", normalize_kind_filter(self.kind_filter))
        object.__setattr__(
            self, "detail",
            _check_long_text(self.detail, "the search's words"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))
        object.__setattr__(
            self, "actor", _check_title(self.actor, "an actor"))
        object.__setattr__(
            self, "source", _check_title(self.source, "a source"))
        object.__setattr__(
            self, "origin_session",
            _check_word(self.origin_session, "an origin session"))
        if self.search_id is not None:
            object.__setattr__(
                self, "search_id",
                _check_word(self.search_id, "a search id"))

    @property
    def tokens(self) -> Tuple[str, ...]:
        """The query's tokens, read by the one token road."""
        return parse_query(self.text)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "fuzzy_picker_search",
            "slice": FUZZY_PICKER_SLICE,
            "search_id": self.search_id,
            "seq": self.seq,
            "text": self.text,
            "kind_filter": self.kind_filter,
            "tokens": list(self.tokens),
            "detail": self.detail,
            "recorded_on": self.recorded_on,
            "actor": self.actor,
            "source": self.source,
            "origin_session": self.origin_session,
        }


def _check_search_ref(value: Any) -> PickerSearch:
    if isinstance(value, PickerSearch):
        return value
    return validate_search(value)


def validate_search(search: Any) -> PickerSearch:
    """Judge one search record whole and return it."""
    if isinstance(search, PickerSearch):
        return search
    if not isinstance(search, dict):
        raise ValueError(
            f"a search record must be a mapping, got {search!r}")
    unknown = set(search) - _SEARCH_KEYS
    if unknown:
        raise ValueError(
            f"a search record carries unknown keys: "
            f"{sorted(unknown)}")
    if "type" in search:
        raise ValueError(
            "a search record is judged without its news keys")

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(search, spellings, what)
        if value is None:
            raise ValueError(f"a search record names no {what}")
        return value

    return PickerSearch(
        search_id=_pick_any(
            search, ("search_id", "id"), "search id"),
        seq=_needed(("seq", "sequence", "order"), "sequence"),
        text=_needed(("text", "query", "query_text"), "query text"),
        kind_filter=_needed(
            ("kind_filter", "filter", "kind"), "kind filter"),
        detail=_needed(("detail", "reason"), "the search's words"),
        recorded_on=_needed(
            ("recorded_on", "day", "date"), "day it was recorded"),
        actor=_needed(("actor", "by", "who"), "actor"),
        source=_needed(("source",), "source"),
        origin_session=_needed(
            ("origin_session", "session"), "origin session"),
    )


def build_search(search: Any = None, **kwargs: Any) -> PickerSearch:
    """Build one search record from a mapping, a record, or fields."""
    if kwargs:
        if search is not None:
            raise ValueError("a search record is built one way at a time")
        search = kwargs
    return validate_search(search)


def rank_candidates(candidates: Any, search: Any) -> Tuple[PickerCandidate, ...]:
    """The candidates one search matches, in ranked order.

    Every candidate is scored by the one derived
    road; the matches are those deriving a score
    above nothing, ranked by score, then by the
    roadmap's kind order, then by label, then by
    candidate id - so two rankings of one book
    under one search always stand in one order.
    """
    held_search = _check_search_ref(search)
    scored = []
    for candidate in candidates:
        current = _check_candidate_ref(candidate)
        value = score_of(current, held_search)
        if value > 0:
            scored.append((current, value))
    scored.sort(key=lambda pair: (
        -pair[1], KINDS.index(pair[0].kind),
        pair[0].label.lower(), pair[0].candidate_id))
    return tuple(candidate for candidate, _ in scored)


# ---------------------------------------------------------------------
# The panel row: one match as the panel carries it.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class PickerPanelRow:
    """One matched candidate as the panel carries it.

    The row carries the candidate's id, its kind,
    its label, its DERIVED score under the panel's
    search, its DERIVED candidate line and its
    recorded day. The detail and the tags never
    stand in a row - the panel is the search at a
    glance.
    """

    candidate_id: str
    kind: str
    label: str
    score: int
    line: str
    recorded_on: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "candidate_id",
            _check_word(self.candidate_id, "a candidate id"))
        object.__setattr__(self, "kind", normalize_kind(self.kind))
        object.__setattr__(
            self, "label", _check_title(self.label, "the label"))
        object.__setattr__(
            self, "score",
            _check_count(self.score, "a row's score"))
        if self.score < 1:
            raise ValueError(
                "a panel row stands only for a match - its "
                "score stands above nothing")
        object.__setattr__(
            self, "line", _check_long_text(self.line, "a candidate line"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))

    def sort_key(self) -> Tuple[Any, ...]:
        return (-self.score, KINDS.index(self.kind),
                self.label.lower(), self.candidate_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "kind": self.kind,
            "label": self.label,
            "score": self.score,
            "line": self.line,
            "recorded_on": self.recorded_on,
        }


def _row_for_candidate(candidate: PickerCandidate,
                       search: Any) -> PickerPanelRow:
    return PickerPanelRow(
        candidate_id=candidate.candidate_id, kind=candidate.kind,
        label=candidate.label, score=score_of(candidate, search),
        line=line_of(candidate), recorded_on=candidate.recorded_on)


def _check_row_ref(value: Any) -> PickerPanelRow:
    if isinstance(value, PickerPanelRow):
        return value
    return validate_row(value)


def validate_row(row: Any, candidate: Any = None,
                 search: Any = None) -> PickerPanelRow:
    """Judge one panel row, against its candidate when named."""
    if isinstance(row, PickerPanelRow):
        current = row
    elif isinstance(row, dict):
        unknown = set(row) - _ROW_KEYS
        if unknown:
            raise ValueError(
                f"a fuzzy panel row carries unknown keys: "
                f"{sorted(unknown)}")

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            value = _pick_any(row, spellings, what)
            if value is None:
                raise ValueError(f"a fuzzy panel row names no {what}")
            return value

        current = PickerPanelRow(
            candidate_id=_needed(("candidate_id", "id"), "candidate id"),
            kind=_needed(("kind",), "kind"),
            label=_needed(("label",), "label"),
            score=_needed(("score",), "score"),
            line=_needed(("line",), "candidate line"),
            recorded_on=_needed(("recorded_on",), "day it was recorded"))
    else:
        raise ValueError(
            f"a fuzzy panel row must be a mapping, got {row!r}")
    if candidate is not None:
        held = _check_candidate_ref(candidate)
        if search is None:
            raise ValueError(
                "a panel row is judged against its candidate "
                "under a named search - the score is derived "
                "from the search, never from the row alone")
        wanted = _row_for_candidate(held, _check_search_ref(search))
        if current != wanted:
            raise ValueError(
                "a fuzzy panel row must be its candidate's own "
                "row under the search - the score and the line "
                "are derived from the candidate, never written "
                "beside it")
    return current


def build_row(row: Any = None, candidate: Any = None,
              search: Any = None,
              **kwargs: Any) -> PickerPanelRow:
    """Build one panel row from a mapping, a row, or its candidate."""
    if candidate is not None:
        if row is not None or kwargs:
            return validate_row(
                row if row is not None else kwargs, candidate, search)
        return _row_for_candidate(
            _check_candidate_ref(candidate), _check_search_ref(search))
    if kwargs:
        if row is not None:
            raise ValueError("a row is built one way at a time")
        row = kwargs
    return validate_row(row)


@dataclass(frozen=True)
class KindCount:
    """How many matched candidates of one kind a panel holds."""

    kind: str
    items: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", normalize_kind(self.kind))
        object.__setattr__(
            self, "items", _check_count(self.items, "a kind's items"))

    def to_record(self) -> Dict[str, Any]:
        return {"kind": self.kind, "items": self.items}


def _check_kind_count_ref(value: Any) -> KindCount:
    if isinstance(value, KindCount):
        return value
    if isinstance(value, dict):
        unknown = set(value) - _KIND_COUNT_KEYS
        if unknown:
            raise ValueError(
                f"a kind count carries unknown keys: "
                f"{sorted(unknown)}")
        kind = _pick_any(value, ("kind",), "kind")
        items = _pick_any(value, ("items", "count"), "items")
        if kind is None or items is None:
            raise ValueError("a kind count names its kind and its items")
        return KindCount(kind=kind, items=items)
    raise ValueError(f"a kind count must be a mapping, got {value!r}")


def _kind_counts(rows: Tuple[PickerPanelRow, ...]) -> Tuple[KindCount, ...]:
    counts: Dict[str, int] = {}
    for row in rows:
        counts[row.kind] = counts.get(row.kind, 0) + 1
    return tuple(
        KindCount(kind=kind, items=counts[kind])
        for kind in KINDS if kind in counts)


def _panel_account(total_candidates: int, total_matched: int,
                   kind_counts: Tuple[KindCount, ...],
                   query_text: str, kind_filter: str,
                   as_of: str) -> Tuple[str, ...]:
    kinds = ", ".join(
        f"{count.kind} {count.items}" for count in kind_counts)
    return (
        f"The fuzzy picker holds {total_candidates} candidates as of "
        f"{as_of}: the search {query_text!r} under the {kind_filter} "
        f"filter matches {total_matched} of them: {kinds}.",
        "Rows stand in ranked order, best match first, so "
        "two panels of one search diff cleanly, line by line.",
        "Every score is derived from the query's tokens against "
        "the candidate's own label, tags and detail - no score "
        "is stored on any candidate, and no rank is chosen.",
        "The panel's words are plain words first, and a search "
        "only ever looks: it opens no file, runs no command, "
        "loads no model, applies no theme and joins no session.",
    )


@dataclass(frozen=True)
class FuzzyPanel:
    """The derived panel of one book under one search.

    Rows stand in ranked order - score, then the
    roadmap's kind order, then label, then candidate
    id; the totals are the rows' own counts and the
    kind counts stand in the roadmap's kind order.
    A stored panel is judged whole in
    ``__post_init__``: its totals, its kind counts,
    its ranked order and its account must all be
    the rows' own derived shape - a panel may not
    soften its search.
    """

    panel_id: Optional[str]
    search_id: Optional[str]
    query_text: str
    kind_filter: str
    rows: Tuple[PickerPanelRow, ...]
    total_candidates: int
    total_matched: int
    kind_counts: Tuple[KindCount, ...]
    as_of: str
    account: Tuple[str, ...]

    def __post_init__(self) -> None:
        if self.panel_id is not None:
            object.__setattr__(
                self, "panel_id",
                _check_word(self.panel_id, "a panel id"))
        if self.search_id is not None:
            object.__setattr__(
                self, "search_id",
                _check_word(self.search_id, "a search id"))
        text = _check_long_text(self.query_text, "the query text")
        parse_query(text)
        object.__setattr__(self, "query_text", text)
        object.__setattr__(
            self, "kind_filter",
            normalize_kind_filter(self.kind_filter))
        rows = tuple(_check_row_ref(r) for r in self.rows)
        object.__setattr__(self, "rows", rows)
        ids = [r.candidate_id for r in rows]
        if len(set(ids)) != len(ids):
            raise ValueError("panel rows stand one row per candidate")
        if [r.sort_key() for r in rows] != sorted(
                r.sort_key() for r in rows):
            raise ValueError(
                "panel rows stand in ranked order - score, "
                "then kind order, then label, then candidate id")
        for field in ("total_candidates", "total_matched"):
            object.__setattr__(
                self, field,
                _check_count(getattr(self, field), f"a panel's {field}"))
        counts = tuple(
            _check_kind_count_ref(c) for c in self.kind_counts)
        object.__setattr__(self, "kind_counts", counts)
        object.__setattr__(self, "as_of", _check_day(self.as_of, "an as-of day"))
        object.__setattr__(self, "account", _check_account(self.account))
        if self.total_matched != len(rows):
            raise ValueError("a panel's matched total is its rows' own count")
        if self.total_candidates < self.total_matched:
            raise ValueError(
                "a panel's candidate total cannot stand below "
                "its matched total")
        if counts != _kind_counts(rows):
            raise ValueError("a panel's kind counts are its rows' own counts")
        if rows and self.as_of < max(r.recorded_on for r in rows):
            raise ValueError(
                "a panel's as-of day precedes one of its rows")
        if self.account != _panel_account(
                self.total_candidates, self.total_matched, counts,
                self.query_text, self.kind_filter, self.as_of):
            raise ValueError(
                "a panel's account is its rows' own account, "
                "derived, never written loose")

    def row_for(self, candidate_id: Any) -> PickerPanelRow:
        """The row one candidate id names (KeyError if absent)."""
        wanted = _check_word(candidate_id, "a candidate id")
        for row in self.rows:
            if row.candidate_id == wanted:
                return row
        raise KeyError(f"no row named {wanted!r} stands on the panel")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "fuzzy_picker_panel",
            "slice": FUZZY_PICKER_SLICE,
            "panel_id": self.panel_id,
            "search_id": self.search_id,
            "query_text": self.query_text,
            "kind_filter": self.kind_filter,
            "rows": [r.to_record() for r in self.rows],
            "total_candidates": self.total_candidates,
            "total_matched": self.total_matched,
            "kind_counts": [c.to_record() for c in self.kind_counts],
            "as_of": self.as_of,
            "account": list(self.account),
        }


def _held_candidates(source: Any) -> Tuple[PickerCandidate, ...]:
    if isinstance(source, FuzzyPickerBook):
        return source.candidates
    if isinstance(source, FuzzyPickerRegistry):
        return source.list_candidates()
    if isinstance(source, PickerCandidate):
        return (source,)
    raise ValueError(f"a fuzzy-picker source is needed, got {source!r}")


def _held_searches(source: Any) -> Tuple[PickerSearch, ...]:
    if isinstance(source, FuzzyPickerBook):
        return source.searches
    if isinstance(source, FuzzyPickerRegistry):
        return source.list_searches()
    return ()


def _resolve_search(source: Any, search: Any) -> PickerSearch:
    if search is None:
        raise ValueError(
            "a panel or verdict is derived under a named search")
    if isinstance(search, str):
        wanted = _check_word(search, "a search id")
        for held in _held_searches(source):
            if held.search_id == wanted:
                return held
        raise ValueError(
            f"no search named {wanted!r} stands in the source")
    return _check_search_ref(search)


def _default_search(source: Any) -> PickerSearch:
    """The search a book's own panel stands under, or its first."""
    if isinstance(source, (FuzzyPickerBook, FuzzyPickerRegistry)):
        book = source if isinstance(source, FuzzyPickerBook) else source.book()
        for panel in book.panels:
            if panel.search_id is not None:
                for held in book.searches:
                    if held.search_id == panel.search_id:
                        return held
        if book.searches:
            return book.searches[0]
    raise ValueError("no search stands in the source to derive under")


def derive_panel(source: Any, search: Any = None) -> FuzzyPanel:
    """Derive the panel of a book under one search."""
    held_search = _resolve_search(source, search)
    candidates = _held_candidates(source)
    matched = rank_candidates(candidates, held_search)
    rows = tuple(_row_for_candidate(c, held_search) for c in matched)
    counts = _kind_counts(rows)
    as_of = max((c.recorded_on for c in candidates), default=_EXAMPLE_AS_OF)
    return FuzzyPanel(
        panel_id=None, search_id=held_search.search_id,
        query_text=held_search.text, kind_filter=held_search.kind_filter,
        rows=rows, total_candidates=len(candidates),
        total_matched=len(rows), kind_counts=counts, as_of=as_of,
        account=_panel_account(
            len(candidates), len(rows), counts, held_search.text,
            held_search.kind_filter, as_of))


def validate_panel(panel: Any, source: Any = None) -> FuzzyPanel:
    """Judge one panel whole, against its source when named."""
    if isinstance(panel, FuzzyPanel):
        current = panel
    elif isinstance(panel, dict):
        data = dict(panel)
        data.pop("type", None)
        data.pop("slice", None)
        unknown = set(data) - _PANEL_KEYS
        if unknown:
            raise ValueError(
                f"a fuzzy panel carries unknown keys: "
                f"{sorted(unknown)}")

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            value = _pick_any(data, spellings, what)
            if value is None:
                raise ValueError(f"a fuzzy panel names no {what}")
            return value

        rows_in = _needed(("rows", "matches"), "rows")
        counts_in = _needed(("kind_counts", "kinds"), "kind counts")
        current = FuzzyPanel(
            panel_id=_pick_any(data, ("panel_id", "id"), "panel id"),
            search_id=_pick_any(data, ("search_id", "search"), "search id"),
            query_text=_needed(("query_text", "query"), "query text"),
            kind_filter=_needed(("kind_filter", "filter"), "kind filter"),
            rows=tuple(validate_row(r) for r in rows_in),
            total_candidates=_needed(
                ("total_candidates", "candidates"), "candidate total"),
            total_matched=_needed(("total_matched", "matched"), "matched total"),
            kind_counts=tuple(
                _check_kind_count_ref(c) for c in counts_in),
            as_of=_needed(("as_of", "day"), "as-of day"),
            account=tuple(_needed(("account", "statements"), "account")))
    else:
        raise ValueError(f"a fuzzy panel must be a mapping, got {panel!r}")
    if source is not None:
        held_search = _resolve_search(source, current.search_id)
        derived = derive_panel(source, held_search)
        if (current.search_id != derived.search_id
                or current.query_text != derived.query_text
                or current.kind_filter != derived.kind_filter
                or current.rows != derived.rows
                or current.total_candidates != derived.total_candidates
                or current.total_matched != derived.total_matched
                or current.kind_counts != derived.kind_counts
                or current.as_of != derived.as_of
                or current.account != derived.account):
            raise ValueError(
                "a stored panel must equal the panel its book "
                "derives under its search - the panel is "
                "derived, never stored loose")
    return current


def build_panel(panel: Any = None, source: Any = None,
                search: Any = None, **kwargs: Any) -> FuzzyPanel:
    """Build one panel from a mapping, a panel, or its source."""
    if kwargs:
        if panel is not None:
            raise ValueError("a panel is built one way at a time")
        panel = kwargs
    if panel is None and source is not None:
        return derive_panel(source, search)
    return validate_panel(panel, source)


# ---------------------------------------------------------------------
# The verdict: the whole book under one search, in one word.
# ---------------------------------------------------------------------


def _verdict_word(total_matched: int, distinct_kinds: int) -> str:
    if total_matched == 0:
        return "empty"
    if distinct_kinds > 1:
        return "matched"
    return "focused"


@dataclass(frozen=True)
class FuzzyVerdict:
    """The derived verdict of one whole book under one search.

    The word is read off the matches alone: empty
    while no candidate matches, focused while the
    matches stand in one kind alone, matched while
    they span more than one kind. A stored verdict
    is judged against those tallies in
    ``__post_init__``.
    """

    total_candidates: int
    total_matched: int
    distinct_kinds: int
    earliest_on: str
    latest_on: str
    verdict: str

    def __post_init__(self) -> None:
        for field in ("total_candidates", "total_matched",
                      "distinct_kinds"):
            object.__setattr__(
                self, field,
                _check_count(getattr(self, field), f"a verdict's {field}"))
        object.__setattr__(
            self, "earliest_on", _check_day(self.earliest_on, "an earliest day"))
        object.__setattr__(
            self, "latest_on", _check_day(self.latest_on, "a latest day"))
        if self.latest_on < self.earliest_on:
            raise ValueError("a verdict's latest day precedes its earliest")
        if self.total_matched > self.total_candidates:
            raise ValueError(
                "a verdict's matched tally cannot exceed its "
                "candidate total")
        if self.distinct_kinds > len(KINDS):
            raise ValueError(
                "a verdict's kinds cannot exceed the closed kind set")
        if self.total_matched == 0 and self.distinct_kinds != 0:
            raise ValueError(
                "an empty verdict names no kind among its matches")
        if self.total_matched > 0 and self.distinct_kinds == 0:
            raise ValueError(
                "a verdict with matches names the kinds they span")
        if self.distinct_kinds > self.total_matched:
            raise ValueError(
                "a verdict's kinds cannot exceed its matches")
        word = _clean_text(self.verdict, "a verdict")
        if word not in VERDICT_WORDS:
            raise ValueError(
                f"a verdict is one of {VERDICT_WORDS}, got {word!r}")
        object.__setattr__(self, "verdict", word)
        if word != _verdict_word(self.total_matched, self.distinct_kinds):
            raise ValueError(
                "a verdict's word is derived from its tallies, "
                "never chosen")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "fuzzy_picker_verdict",
            "slice": FUZZY_PICKER_SLICE,
            "total_candidates": self.total_candidates,
            "total_matched": self.total_matched,
            "distinct_kinds": self.distinct_kinds,
            "earliest_on": self.earliest_on,
            "latest_on": self.latest_on,
            "verdict": self.verdict,
        }


def derive_verdict(source: Any, search: Any = None) -> FuzzyVerdict:
    """Derive the verdict of a book under one search."""
    held_search = _resolve_search(source, search)
    candidates = _held_candidates(source)
    matched = rank_candidates(candidates, held_search)
    distinct = len({c.kind for c in matched})
    days = [c.recorded_on for c in candidates]
    return FuzzyVerdict(
        total_candidates=len(candidates), total_matched=len(matched),
        distinct_kinds=distinct,
        earliest_on=min(days) if days else _EXAMPLE_AS_OF,
        latest_on=max(days) if days else _EXAMPLE_AS_OF,
        verdict=_verdict_word(len(matched), distinct))


def _check_verdict_ref(value: Any) -> FuzzyVerdict:
    if isinstance(value, FuzzyVerdict):
        return value
    return validate_verdict(value)


def validate_verdict(verdict: Any, source: Any = None,
                     search: Any = None) -> FuzzyVerdict:
    """Judge one verdict whole, against its source when named."""
    if isinstance(verdict, FuzzyVerdict):
        current = verdict
    elif isinstance(verdict, dict):
        data = dict(verdict)
        data.pop("type", None)
        data.pop("slice", None)
        unknown = set(data) - _VERDICT_KEYS
        if unknown:
            raise ValueError(
                f"a fuzzy verdict carries unknown keys: "
                f"{sorted(unknown)}")

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            value = _pick_any(data, spellings, what)
            if value is None:
                raise ValueError(f"a fuzzy verdict names no {what}")
            return value

        current = FuzzyVerdict(
            total_candidates=_needed(
                ("total_candidates", "candidates"), "candidate total"),
            total_matched=_needed(("total_matched", "matched"), "matched total"),
            distinct_kinds=_needed(
                ("distinct_kinds", "kinds"), "distinct kinds"),
            earliest_on=_needed(("earliest_on", "earliest"), "earliest day"),
            latest_on=_needed(("latest_on", "latest"), "latest day"),
            verdict=_needed(("verdict",), "verdict"))
    else:
        raise ValueError(f"a fuzzy verdict must be a mapping, got {verdict!r}")
    if source is not None:
        derived = derive_verdict(source, search)
        if current != derived:
            raise ValueError(
                "a stored verdict must equal the verdict its "
                "book derives under its search - the verdict "
                "is derived, never stored loose")
    return current


def build_verdict(verdict: Any = None, source: Any = None,
                  search: Any = None, **kwargs: Any) -> FuzzyVerdict:
    """Build one verdict from a mapping, a verdict, or its source."""
    if kwargs:
        if verdict is not None:
            raise ValueError("a verdict is built one way at a time")
        verdict = kwargs
    if verdict is None and source is not None:
        return derive_verdict(source, search)
    return validate_verdict(verdict, source, search)


# ---------------------------------------------------------------------
# The book: one set of candidates and searches, held whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class FuzzyPickerBook:
    """One set of picker candidates and searches, held whole.

    Candidates stand in held order - one candidate
    per candidate id - searches stand in recorded
    order, one search per sequence and per id, and
    every stored panel is judged against the book
    and the search it stands under.
    """

    title: str
    candidates: Tuple[PickerCandidate, ...] = ()
    searches: Tuple[PickerSearch, ...] = ()
    panels: Tuple[FuzzyPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book title"))
        candidates = tuple(_check_candidate_ref(c) for c in self.candidates)
        object.__setattr__(self, "candidates", candidates)
        ids = [c.candidate_id for c in candidates]
        if len(set(ids)) != len(ids):
            raise ValueError("a book holds one candidate per candidate id")
        searches = tuple(_check_search_ref(s) for s in self.searches)
        object.__setattr__(self, "searches", searches)
        seqs = [s.seq for s in searches]
        if seqs != sorted(seqs) or len(set(seqs)) != len(seqs):
            raise ValueError(
                "a book's searches stand in recorded order, "
                "one search per sequence")
        search_ids = [
            s.search_id for s in searches if s.search_id is not None]
        if len(set(search_ids)) != len(search_ids):
            raise ValueError("a book holds one search per search id")
        panels = tuple(validate_panel(p, self) for p in self.panels)
        object.__setattr__(self, "panels", panels)

    def candidate_for(self, candidate_id: Any) -> PickerCandidate:
        """The candidate one id names (KeyError if absent)."""
        wanted = _check_word(candidate_id, "a candidate id")
        for candidate in self.candidates:
            if candidate.candidate_id == wanted:
                return candidate
        raise KeyError(f"no candidate named {wanted!r} stands in the book")

    def search_for(self, search_id: Any) -> PickerSearch:
        """The search one id names (KeyError if absent)."""
        wanted = _check_word(search_id, "a search id")
        for search in self.searches:
            if search.search_id == wanted:
                return search
        raise KeyError(f"no search named {wanted!r} stands in the book")

    def panel_for(self, panel_id: Any) -> FuzzyPanel:
        """The panel one id names (KeyError if absent)."""
        wanted = _check_word(panel_id, "a panel id")
        for panel in self.panels:
            if panel.panel_id == wanted:
                return panel
        raise KeyError(f"no panel named {wanted!r} stands in the book")

    def candidate_ids(self) -> Tuple[str, ...]:
        """The book's candidate ids, in held order."""
        return tuple(c.candidate_id for c in self.candidates)

    def search_ids(self) -> Tuple[Optional[str], ...]:
        """The book's search ids, in recorded order."""
        return tuple(s.search_id for s in self.searches)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "fuzzy_picker_book",
            "slice": FUZZY_PICKER_SLICE,
            "title": self.title,
            "candidates": [c.to_record() for c in self.candidates],
            "searches": [s.to_record() for s in self.searches],
            "panels": [p.to_record() for p in self.panels],
            "candidate_count": len(self.candidates),
            "search_count": len(self.searches),
        }


def _judge_book_panels(book: FuzzyPickerBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def validate_book(data: Any, *, require_example: bool = False) -> FuzzyPickerBook:
    """Judge one picker file's data whole and return its book."""
    if isinstance(data, FuzzyPickerBook):
        book = data
        _judge_book_panels(book)
        if require_example:
            _check_example(book)
        return book
    if not isinstance(data, dict):
        raise ValueError(f"a fuzzy-picker book must be a mapping, got {data!r}")
    unknown = set(data) - _FUZZY_PICKER_KEYS
    if unknown:
        raise ValueError(
            f"a fuzzy-picker book carries unknown keys: {sorted(unknown)}")
    if data.get("schema") != FUZZY_PICKER_SCHEMA:
        raise ValueError(
            f"a fuzzy-picker book's schema must be "
            f"{FUZZY_PICKER_SCHEMA!r}, got {data.get('schema')!r}")
    if data.get("slice") != FUZZY_PICKER_SLICE:
        raise ValueError(
            f"a fuzzy-picker book's slice must be "
            f"{FUZZY_PICKER_SLICE!r}, got {data.get('slice')!r}")
    guide = data.get("guide") or {}
    title = _pick_any(guide, ("title", "name"), "title")
    if title is None:
        title = _pick_any(data, ("title", "name"), "title")
    candidates_in = _pick_any(data, ("candidates",), "candidates")
    if candidates_in is None:
        raise ValueError("a fuzzy-picker book names no candidates")
    searches_in = data.get("searches") or []
    panels_in = data.get("panels") or []
    candidates = []
    for raw in candidates_in:
        stored = dict(raw)
        stored.pop("type", None)
        stored.pop("slice", None)
        for derived_key in ("line", "score", "rank"):
            stored.pop(derived_key, None)
        candidates.append(validate_candidate(stored))
    searches = []
    for raw in searches_in:
        stored = dict(raw)
        stored.pop("type", None)
        stored.pop("slice", None)
        stored.pop("tokens", None)
        searches.append(validate_search(stored))
    book = FuzzyPickerBook(
        title=title,
        candidates=tuple(candidates),
        searches=tuple(searches),
        panels=tuple(validate_panel(p) for p in panels_in))
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def _check_example(book: FuzzyPickerBook) -> None:
    if book.title != _EXAMPLE_TITLE:
        raise ValueError(
            f"the shipped example book is {_EXAMPLE_TITLE!r}, "
            f"got {book.title!r}")
    if book.candidate_ids() != _EXAMPLE_CANDIDATE_IDS:
        raise ValueError("the shipped example book's candidates differ")
    first = book.candidates[0]
    if first.candidate_id != _EXAMPLE_FIRST_CANDIDATE_ID or (
            first.label != _EXAMPLE_FIRST_CANDIDATE_LABEL):
        raise ValueError("the shipped example book's first candidate differs")
    if book.search_ids() != _EXAMPLE_SEARCH_IDS:
        raise ValueError("the shipped example book's searches differ")
    if len(book.panels) != 1 or (
            book.panels[0].panel_id != _EXAMPLE_PANEL_ID):
        raise ValueError("the shipped example book's panel differs")
    if book.panels[0].as_of != _EXAMPLE_AS_OF:
        raise ValueError("the shipped example book's as-of day differs")
    derived = derive_panel(book, book.panels[0].search_id)
    if tuple(r.candidate_id for r in book.panels[0].rows) != tuple(
            r.candidate_id for r in derived.rows):
        raise ValueError("the shipped example book's panel rows differ")


def build_book(book: Any = None, **kwargs: Any) -> FuzzyPickerBook:
    """Build one book from a mapping, a book, or fields."""
    if isinstance(book, FuzzyPickerBook) and not kwargs:
        return validate_book(book)
    if kwargs:
        if book is not None:
            raise ValueError("a book is built one way at a time")
        fields = dict(kwargs)
    elif isinstance(book, dict) and (
            "candidates" in book) and (
            "schema" not in book and "guide" not in book
            and "canon_note" not in book):
        fields = dict(book)
    else:
        return _book_from(book, require_example=False)
    unknown = set(fields) - _BOOK_KEYS - {
        "candidates", "searches", "panels"}
    if unknown:
        raise ValueError(
            f"a fuzzy-picker book carries unknown keys: "
            f"{sorted(unknown)}")
    title = _pick_any(fields, ("title", "name"), "title")
    if title is None:
        raise ValueError("a fuzzy-picker book names no title")
    candidates_in = _pick_any(fields, ("candidates",), "candidates") or ()
    return FuzzyPickerBook(
        title=title,
        candidates=tuple(_check_candidate_ref(c) for c in candidates_in),
        searches=tuple(
            _check_search_ref(s) for s in fields.get("searches") or ()),
        panels=tuple(
            validate_panel(p) for p in fields.get("panels") or ()))


def _book_from(data: Any, *, require_example: bool) -> FuzzyPickerBook:
    if isinstance(data, FuzzyPickerBook):
        return validate_book(data, require_example=require_example)
    if isinstance(data, dict):
        return validate_book(data, require_example=require_example)
    raise ValueError(f"a fuzzy-picker book must be a mapping, got {data!r}")


def load_fuzzy_picker(data: Optional[Dict[str, Any]] = None) -> FuzzyPickerBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(FUZZY_PICKER_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_fuzzy_picker_file(path: Any) -> FuzzyPickerBook:
    """Load one picker file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: candidates and searches held one by one.
# ---------------------------------------------------------------------


class FuzzyPickerRegistry:
    """An in-memory holding of picker candidates and searches.

    The registry is the pure layer's model of a
    session's picker: candidates are held under
    their candidate ids, one candidate per id, in
    held order, and searches are held in recorded
    order, one search per sequence and per id.
    Holding is data only - no search held here
    opens the thing it matches, and standing a
    search commits no choice at all.
    """

    def __init__(self, book: Any = None) -> None:
        self._candidates: List[PickerCandidate] = []
        self._searches: List[PickerSearch] = []
        self._title: Optional[str] = None
        if book is not None:
            self.register_book(book)

    def title(self) -> Optional[str]:
        return self._title

    def _fresh_search_id(self, held_ids: Any) -> str:
        n = 1
        while f"search-{n}" in held_ids:
            n += 1
        return f"search-{n}"

    def _check_candidate_free(self, candidate: PickerCandidate) -> None:
        for held in self._candidates:
            if held.candidate_id == candidate.candidate_id:
                raise ValueError(
                    f"a candidate already stands under id "
                    f"{candidate.candidate_id!r}")

    def register_candidate(self, candidate: Any) -> PickerCandidate:
        """Hold one candidate, judged whole before it is held."""
        validated = _check_candidate_ref(candidate)
        self._check_candidate_free(validated)
        self._candidates.append(validated)
        return validated

    def _check_search_free(self, search: PickerSearch) -> None:
        for held in self._searches:
            if search.search_id is not None and (
                    held.search_id == search.search_id):
                raise ValueError(
                    f"a search already stands under id "
                    f"{search.search_id!r}")
            if held.seq == search.seq:
                raise ValueError(
                    f"a search already stands at sequence "
                    f"{search.seq} - the book holds one "
                    f"search per place")

    def register_search(self, search: Any) -> PickerSearch:
        """Hold one search record, judged whole first.

        A search id or a sequence already standing
        here refuses and holds nothing new. A held
        search only ever looks: standing it derives
        its panel and commits no choice.
        """
        validated = _check_search_ref(search)
        self._check_search_free(validated)
        if validated.search_id is None:
            validated = PickerSearch(
                search_id=self._fresh_search_id(
                    {s.search_id for s in self._searches}),
                seq=validated.seq, text=validated.text,
                kind_filter=validated.kind_filter,
                detail=validated.detail,
                recorded_on=validated.recorded_on,
                actor=validated.actor, source=validated.source,
                origin_session=validated.origin_session)
        self._searches.append(validated)
        self._searches.sort(key=lambda s: s.seq)
        return validated

    def register_book(self, book: Any) -> FuzzyPickerBook:
        """Hold a whole book, judged whole first."""
        validated = build_book(book)
        for candidate in validated.candidates:
            self._check_candidate_free(candidate)
        if self._title is None:
            self._title = validated.title
        elif validated.title != self._title:
            raise ValueError(
                "a second book under a different title refuses - "
                "one book stands in one registry")
        for candidate in validated.candidates:
            self._candidates.append(candidate)
        for search in validated.searches:
            self.register_search(search)
        return self.book()

    def get_candidate(self, candidate_id: Any) -> PickerCandidate:
        """The candidate one id names (KeyError if absent)."""
        wanted = _check_word(candidate_id, "a candidate id")
        for candidate in self._candidates:
            if candidate.candidate_id == wanted:
                return candidate
        raise KeyError(f"no candidate named {wanted!r} stands held")

    def get_search(self, search_id: Any) -> PickerSearch:
        """The search record one id names (KeyError if absent)."""
        wanted = _check_word(search_id, "a search id")
        for search in self._searches:
            if search.search_id == wanted:
                return search
        raise KeyError(f"no search named {wanted!r} stands held")

    def latest_search(self) -> PickerSearch:
        """The last search recorded (KeyError if none)."""
        if not self._searches:
            raise KeyError("no search stands held")
        return self._searches[-1]

    def list_candidates(self) -> Tuple[PickerCandidate, ...]:
        return tuple(self._candidates)

    def list_searches(self) -> Tuple[PickerSearch, ...]:
        return tuple(self._searches)

    def book(self) -> FuzzyPickerBook:
        return FuzzyPickerBook(
            title=self._title or "Fuzzy Picker",
            candidates=tuple(self._candidates),
            searches=tuple(self._searches))

    def panel(self, search: Any = None) -> FuzzyPanel:
        return derive_panel(self.book(), search)

    def verdict(self, search: Any = None) -> FuzzyVerdict:
        return derive_verdict(self.book(), search)


def candidates_with_kind(source: Any, kind: Any) -> Tuple[PickerCandidate, ...]:
    """The candidates of one kind, in held order."""
    wanted = normalize_kind(kind)
    return tuple(
        c for c in _held_candidates(source) if c.kind == wanted)


def total_candidates(source: Any) -> int:
    """How many candidates a source holds."""
    return len(_held_candidates(source))


# ---------------------------------------------------------------------
# Session news, plain words, and the screens.
# ---------------------------------------------------------------------


def candidate_record(candidate: Any) -> Dict[str, Any]:
    """The session-news record of one picker candidate."""
    current = _check_candidate_ref(candidate)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Fuzzy picker candidate {current.candidate_id}: "
        f"{line_of(current)}.")
    return record_out


def search_record(search: Any) -> Dict[str, Any]:
    """The session-news record of one search record."""
    current = _check_search_ref(search)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Fuzzy picker search {current.search_id or current.seq}: "
        f"{current.text!r} under the {current.kind_filter} filter - "
        f"{current.detail}")
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived panel."""
    current = validate_panel(panel, source)
    record = current.to_record()
    record["news"] = True
    kinds = ", ".join(
        f"{c.kind} {c.items}" for c in current.kind_counts)
    record["headline"] = (
        f"Fuzzy picker panel as of {current.as_of}: "
        f"{current.total_matched} of {current.total_candidates} "
        f"candidates match {current.query_text!r} under the "
        f"{current.kind_filter} filter ({kinds}).")
    return record


def verdict_record(verdict: Any, source: Any = None,
                   search: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived verdict."""
    current = validate_verdict(verdict, source, search)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Fuzzy picker verdict: {current.verdict} - "
        f"{current.total_matched} of {current.total_candidates} "
        f"candidates matched across {current.distinct_kinds} "
        f"kinds, from {current.earliest_on} to {current.latest_on}.")
    return record


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one picker book."""
    current = book if isinstance(book, FuzzyPickerBook) else build_book(book)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Fuzzy picker {current.title}: "
        f"{record['candidate_count']} candidates named, "
        f"{record['search_count']} searches held.")
    return record


def plain_words(candidate: Any) -> str:
    """One candidate, in one plain sentence."""
    current = _check_candidate_ref(candidate)
    return (
        f"{line_of(current)} - one findable thing on "
        f"candidate {current.candidate_id}: "
        f"{current.detail} It is found by the one grammar, "
        f"and finding it opens nothing.")


def search_plain_words(search: Any) -> str:
    """One search record, in one plain sentence."""
    current = _check_search_ref(search)
    return (
        f"Search {current.search_id or current.seq} looks for "
        f"{current.text!r} under the {current.kind_filter} "
        f"filter, read into the tokens "
        f"{', '.join(current.tokens)} by the one token road, "
        f"recorded on {current.recorded_on} by "
        f"{current.actor}: {current.detail} A search only "
        f"ever looks - it commits no choice at all.")


def panel_plain_words(source: Any, search: Any = None) -> str:
    """The panel in plain words, in full."""
    if isinstance(source, FuzzyPanel):
        panel = validate_panel(source)
        title = None
    elif isinstance(source, (FuzzyPickerBook, FuzzyPickerRegistry)):
        book = source if isinstance(
            source, FuzzyPickerBook) else source.book()
        panel = derive_panel(
            book, search if search is not None
            else _default_search(book))
        title = book.title
    else:
        raise ValueError(f"a fuzzy-picker source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Matches, in ranked order:")
    for row in panel.rows:
        lines.append(
            f"{row.candidate_id}: {row.line} "
            f"(score {row.score}, {row.recorded_on})")
    lines.extend(panel.account)
    return "\n".join(lines)


def verdict_plain_words(source: Any, search: Any = None) -> str:
    """The book verdict in plain words, in full."""
    if isinstance(source, FuzzyVerdict):
        verdict = validate_verdict(source)
    elif isinstance(source, (FuzzyPickerBook, FuzzyPickerRegistry)):
        book = source if isinstance(
            source, FuzzyPickerBook) else source.book()
        verdict = derive_verdict(
            book, search if search is not None
            else _default_search(book))
    else:
        raise ValueError(f"a fuzzy-picker source is needed, got {source!r}")
    return (
        f"Fuzzy picker verdict: {verdict.verdict} - "
        f"{verdict.total_matched} of {verdict.total_candidates} "
        f"candidates matched, across {verdict.distinct_kinds} "
        f"kinds, from {verdict.earliest_on} to "
        f"{verdict.latest_on} - every score is derived from "
        f"the query's tokens against the candidates' own "
        f"fields, by the one grammar.")


def _source_book(source: Any) -> FuzzyPickerBook:
    if source is None:
        return load_fuzzy_picker()
    if isinstance(source, FuzzyPickerRegistry):
        return source.book()
    if isinstance(source, FuzzyPickerBook):
        return source
    if isinstance(source, PickerCandidate):
        return FuzzyPickerBook(title="One picker candidate", candidates=(source,))
    raise ValueError(f"a fuzzy-picker book is needed, got {source!r}")


def format_candidate(candidate: Any) -> str:
    """One picker candidate as a screen block.

    The candidate's kind, label, detail and tags
    stand as their own lines, and its provenance
    stands whole - a match held here is a finding,
    never the act of opening the thing found.
    """
    current = _check_candidate_ref(candidate)
    lines = [
        f"{current.candidate_id}: {line_of(current)}",
        f"Kind: {current.kind}",
        f"Label: {current.label}",
        f"Detail: {current.detail}",
        f"Tags: {', '.join(current.tags)}",
        f"Recorded: on {current.recorded_on} by {current.actor} "
        f"from {current.source} in {current.origin_session}.",
    ]
    return "\n".join(lines)


def format_search(search: Any) -> str:
    """One search record as a screen block."""
    current = _check_search_ref(search)
    lines = [
        f"{current.search_id or '-'}: {current.text!r} "
        f"under the {current.kind_filter} filter",
        f"Tokens: {', '.join(current.tokens)}",
        f"Words: {current.detail}",
        f"Recorded: on {current.recorded_on} by {current.actor} "
        f"from {current.source} in {current.origin_session}.",
    ]
    return "\n".join(lines)


def format_book(source: Any = None, kind: Any = None) -> str:
    """The book as derived lines, in held order.

    By default the lines are every candidate's
    derived line. With ``kind`` only that kind's
    candidates stand in the list.
    """
    book = _source_book(source)
    wanted = normalize_kind(kind) if kind is not None else None
    lines = []
    for candidate in book.candidates:
        if wanted is not None and candidate.kind != wanted:
            continue
        lines.append(f"{candidate.candidate_id}: {line_of(candidate)}")
    if not lines:
        lines.append("No candidates stand in the book on that reading.")
    return "\n".join(lines)


def format_panel(source: Any = None, search: Any = None) -> str:
    """The panel as a screen block: every row and the account."""
    if isinstance(source, FuzzyPanel):
        panel = validate_panel(source)
        lines: list = []
    else:
        book = _source_book(source)
        panel = derive_panel(
            book, search if search is not None
            else _default_search(book))
        lines = [f"Panel in {book.title}:"]
    lines.append("Matches, in ranked order:")
    for row in panel.rows:
        lines.append(
            f"{row.candidate_id}: {row.line} - "
            f"score {row.score} ({row.recorded_on})")
    lines.extend(panel.account)
    return "\n".join(lines)


def format_verdict(source: Any = None, search: Any = None) -> str:
    """The verdict as a screen block."""
    if isinstance(source, FuzzyVerdict):
        verdict = validate_verdict(source)
        title = "the book"
    else:
        book = _source_book(source)
        verdict = derive_verdict(
            book, search if search is not None
            else _default_search(book))
        title = book.title
    return (
        f"Verdict in Fuzzy Picker over {title}: "
        f"{verdict.verdict} - {verdict.total_matched} of "
        f"{verdict.total_candidates} candidates matched, "
        f"across {verdict.distinct_kinds} kinds, from "
        f"{verdict.earliest_on} to {verdict.latest_on}.")


def format_fuzzy_picker_screen(source: Any = None) -> str:
    """The whole fuzzy-picker screen for one book."""
    book = _source_book(source)
    search = _default_search(book)
    panel = derive_panel(book, search)
    verdict = derive_verdict(book, search)
    lines = [
        f"Fuzzy Picker (M-175) - {book.title}",
        format_book(book),
        f"Panel: {panel.total_matched} of "
        f"{panel.total_candidates} candidates match "
        f"{panel.query_text!r} under the "
        f"{panel.kind_filter} filter.",
        f"Verdict: {verdict.verdict}.",
        "A search only looks here - it opens no file, "
        "runs no command, loads no model, applies no "
        "theme and joins no session, and it commits "
        "no choice at all.",
    ]
    return "\n".join(lines)


def parse_fuzzy_picker_args(args: Any) -> Tuple[str, Any]:
    """Parse the /fuzzypicker grammar into (action, target).

    ``""``/``show``/``list`` show the book;
    ``candidate <candidate-id>`` shows one candidate
    whole; ``search <search-id>`` shows one held
    search record; ``find <words>`` derives the
    panel of an ad-hoc search over the book;
    ``kind <kind>`` shows one kind's candidates;
    ``panel`` and ``verdict`` show the derived panel
    and verdict under the book's own search.
    Anything else raises ValueError carrying the
    usage line.
    """
    if args is None:
        return ("show", None)
    if not isinstance(args, str):
        raise ValueError(USAGE)
    parts = args.split()
    if not parts or parts == ["show"] or parts == ["list"]:
        return ("show", None)
    if parts[0] == "candidate" and len(parts) == 2:
        return ("candidate", _check_word(parts[1], "a candidate id"))
    if parts[0] == "search" and len(parts) == 2:
        return ("search", _check_word(parts[1], "a search id"))
    if parts[0] == "find" and len(parts) >= 2:
        return ("find", " ".join(parts[1:]))
    if parts[0] == "kind" and len(parts) == 2:
        try:
            return ("kind", normalize_kind(parts[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if parts == ["panel"]:
        return ("panel", None)
    if parts == ["verdict"]:
        return ("verdict", None)
    raise ValueError(USAGE)
