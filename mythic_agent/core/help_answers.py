"""Help that answers (All-Features roadmap slice M-186).

Part VIII - The Beautiful Face - builds here. The
roadmap's words: *`?` anywhere gives help *for that
screen*; a question box ("how do I undo a commit?")
answered from the local docs by the coder itself.*

What already ships, and what this slice adds:

* The shipped tree already carries plain help
  roads (the terminal ``/help`` line, the chat
  screen's help and usage lines - they stand
  untouched behind a seam). What nothing held is
  *help that answers*, as checkable data: one help
  entry per screen, held whole with its provenance;
  the local docs the question box answers from,
  held whole as data; and the answer itself -
  derived at call time from the held docs, never
  stored and never invented. This slice is that
  book, in its own module.
* A screen's help is held whole: the screen it
  stands for (a closed vocabulary - chat, terminal,
  editor, review, settings, onboarding, lessons,
  command palace), its title and its detail.
  Pressing `?` on a screen shows that screen's held
  help; a screen holding no entry stands honestly
  uncovered, named in the book's gaps - no generic
  help is invented for it.
* A local doc is held whole: its title, its topic
  (a closed vocabulary), its standing, current or
  stale, its detail - the answer text itself - and
  its keywords. The question box answers ONLY from
  these held docs: a question matching a current
  doc is answered from that doc's own words, a
  question matching only a stale doc stands
  unanswered and named stale in its gaps, and a
  question matching no held doc stands honestly
  unanswered, named in its gaps. No answer is ever
  invented, and no live road stands behind one:
  the rule stands as data (:data:`LOCAL_DOCS_RULE`)
  and a record claiming a live search, a network
  lookup or a model answer refuses BY NAME.
* The shipped data file (``mythic_agent/data/
  help_answers.yaml``) holds one example book in
  exactly the shape a real help file takes, a
  loader reads a help file anywhere on disk, docs
  and views are shaped as session news, and a
  small in-memory registry holds records one by
  one. The agent layer owns holding a help book
  for a session and answering from it. This layer
  reaches no live road: it searches nothing live,
  calls no model, opens no network and writes
  nothing - it holds help as data and tells it.

Honesty rules, enforced here and pinned by tests:

* **Local docs alone.** Every answer is derived
  from the held doc records; a claim of a live
  search, network lookup or model answer refuses
  by name.
* **Unanswered stands unanswered.** A question no
  current held doc answers stands unanswered,
  named in its gaps - never an invented answer.
* **Stale never answers.** A stale doc is held
  and told as stale; it answers no question.
* **Uncovered stands uncovered.** A screen with
  no held help entry stands uncovered, named in
  the book's gaps; no screen's help is borrowed
  for another.
* **Answers are derived, never stored.** A stored
  answer, verdict or coverage judgement on any
  record refuses by name.
"""

from __future__ import annotations

__all__ = [
    "ASK_ACTION",
    "EXAMPLE_QUESTION",
    "HELP_ANSWERS_RESOURCE",
    "HELP_ANSWERS_SCHEMA",
    "HELP_ANSWERS_SLICE",
    "LOCAL_DOCS_RULE",
    "PLAIN_EXPLANATION",
    "SCREENS",
    "STANDING_WORDS",
    "THE_HELP_ANSWERS_SLICE",
    "TOPICS",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "Any",
    "Dict",
    "List",
    "Optional",
    "DocRecord",
    "HelpAnswer",
    "HelpBook",
    "HelpCoverage",
    "HelpPanel",
    "HelpPanelRow",
    "HelpRegistry",
    "HelpVerdict",
    "HelpView",
    "ScreenHelp",
    "StandingCount",
    "answer_plain_words",
    "answer_record",
    "book_record",
    "build_book",
    "build_doc",
    "build_panel",
    "build_row",
    "build_screen_help",
    "build_verdict",
    "build_view",
    "coverage_plain_words",
    "coverage_record",
    "covered_screens",
    "derive_answer",
    "derive_coverage",
    "derive_panel",
    "derive_verdict",
    "doc_gaps",
    "doc_passes",
    "doc_plain_words",
    "doc_record",
    "docs_for_standing",
    "format_answer",
    "format_book",
    "format_coverage",
    "format_doc",
    "format_help_answers_screen",
    "format_panel",
    "format_screen",
    "format_screen_help",
    "format_verdict",
    "format_view",
    "help_for_screen",
    "inspect_help_source",
    "load_help_answers",
    "load_help_answers_file",
    "normalize_screen",
    "normalize_standing",
    "normalize_topic",
    "normalize_view_filter",
    "panel_plain_words",
    "panel_record",
    "parse_help_args",
    "passing_docs",
    "plain_lines",
    "plain_words",
    "screen_record",
    "segment_of",
    "shown_docs",
    "total_docs",
    "uncovered_screens",
    "validate_book",
    "validate_doc",
    "validate_panel",
    "validate_row",
    "validate_screen_help",
    "validate_verdict",
    "validate_view",
    "verdict_plain_words",
    "verdict_record",
    "view_plain_words",
    "view_record",
]

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

HELP_ANSWERS_SCHEMA = "mythic.help_answers/1"
HELP_ANSWERS_SLICE = "M-186"
THE_HELP_ANSWERS_SLICE = HELP_ANSWERS_SLICE
HELP_ANSWERS_RESOURCE = "help_answers.yaml"
ASK_ACTION = "ask"
EXAMPLE_QUESTION = "how do I undo a commit?"
STANDING_WORDS = ("current", "stale")
SCREENS = (
    "chat", "terminal", "editor", "review", "settings",
    "onboarding", "lessons", "command palace")
TOPICS = (
    "getting started", "editing and undo", "providers and keys",
    "files and workspace", "crews and parallel work",
    "memory and context", "sandbox and safety", "plain language")
VIEW_FILTERS = ("all", "current", "stale")
VERDICT_WORDS = ("open", "strained", "shut")
LOCAL_DOCS_RULE = (
    "help answers come from the local docs held on "
    "this machine alone: no live search, no network "
    "lookup and no model call stands behind an "
    "answer - a question no held doc answers stands "
    "unanswered, named in its gaps")
PLAIN_EXPLANATION = (
    "Help that answers (M-186): press ? on any screen "
    "for that screen's help, or ask in the question "
    "box and the coder answers from its local docs "
    "alone.")
USAGE = (
    "Usage: /helpask | /helpask doc <doc-id> | "
    "/helpask ask <words> | /helpask screen <screen> | "
    "/helpask view <view-id> | /helpask standing <standing> | "
    "/helpask panel | /helpask verdict")

_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_DOC_KEYS = frozenset({
    "doc_id", "seq", "title", "topic", "standing", "detail",
    "keywords",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_HELP_KEYS = frozenset({
    "help_id", "seq", "screen", "title", "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "answer", "answers", "answered", "gaps", "segment",
    "plain_lines", "telling", "verdict", "coverage",
    "matched", "matches", "covered", "uncovered"})
_LIVE_KEYS = (
    "live_search", "web_search", "network_search",
    "network_lookup", "online_lookup", "search_the_web",
    "llm_answer", "model_answer", "live_answer")
_STOPWORDS = frozenset({
    "a", "an", "the", "how", "do", "does", "i", "me", "my",
    "to", "of", "in", "on", "for", "is", "are", "can",
    "could", "what", "when", "where", "why", "it", "this",
    "that", "with", "and", "or"})


# ---------------------------------------------------------------------
# Small judges, in the sibling shape.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


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


def _check_lines(value: Any, what: str) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError(f"{what} must be a list of lines")
    lines = []
    for line in value:
        lines.append(_clean_text(line, f"a line of {what}"))
    return tuple(lines)


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
                f"{what} claims a live answer road "
                f"({key!r} is named on it): "
                f"{LOCAL_DOCS_RULE}")
    for key in mapping:
        if key in _DERIVED_KEYS:
            raise ValueError(
                f"{what} carries {key!r}, which is derived from its "
                f"own fields and never stored")
        if key not in allowed:
            raise ValueError(f"{what} carries unknown field {key!r}")


def normalize_standing(value: Any) -> str:
    standing = _clean_text(value, "a doc standing").lower()
    if standing not in STANDING_WORDS:
        raise ValueError(
            f"doc standing {standing!r} is not one of the held "
            f"standing_words: " + ", ".join(STANDING_WORDS))
    return standing


def normalize_topic(value: Any) -> str:
    topic = _clean_text(value, "a topic").lower()
    if topic not in TOPICS:
        raise ValueError(
            f"topic {topic!r} is not one of the named topics: "
            + ", ".join(TOPICS))
    return topic


def normalize_screen(value: Any) -> str:
    screen = _clean_text(value, "a screen").lower()
    if screen not in SCREENS:
        raise ValueError(
            f"screen {screen!r} is not one of the named screens: "
            + ", ".join(SCREENS))
    return screen


def normalize_view_filter(value: Any) -> str:
    view_filter = _clean_text(value, "a view filter").lower()
    if view_filter not in VIEW_FILTERS:
        raise ValueError(
            f"view filter {view_filter!r} is not one of the held "
            f"filters: " + ", ".join(VIEW_FILTERS))
    return view_filter


# ---------------------------------------------------------------------
# The held local doc: one doc the question box answers from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class DocRecord:
    """One local doc, held as data.

    The doc names its title, its topic - one of
    the closed topic vocabulary - its standing,
    current or stale, its detail, which is the
    answer text itself, and its keywords, the
    words a question is matched against. A current
    doc answers; a stale doc is held and told as
    stale and answers nothing: stale never answers
    here. The doc is local data alone - no live
    road stands behind it.
    """

    doc_id: str
    seq: int
    title: str
    topic: str
    standing: str
    detail: str = ""
    keywords: Tuple[str, ...] = ()
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "doc_id", _clean_text(self.doc_id, "a doc id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a title"))
        object.__setattr__(self, "topic", normalize_topic(self.topic))
        object.__setattr__(
            self, "standing", normalize_standing(self.standing))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a doc detail"))
        object.__setattr__(
            self, "keywords", _check_lines(self.keywords, "keywords"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.doc_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "doc_id": self.doc_id, "seq": self.seq,
            "title": self.title, "topic": self.topic,
            "standing": self.standing, "detail": self.detail,
            "keywords": list(self.keywords),
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_doc_ref(value: Any) -> DocRecord:
    if not isinstance(value, DocRecord):
        raise ValueError("a doc must be a DocRecord")
    return value


def validate_doc(doc: Any) -> DocRecord:
    return _check_doc_ref(doc)


def build_doc(doc: Any = None, **kwargs: Any) -> DocRecord:
    """Build one held doc from a mapping or fields."""
    if doc is None:
        data = dict(kwargs)
    elif isinstance(doc, DocRecord):
        if kwargs:
            raise ValueError("a doc stands whole or by fields, not both")
        return doc
    elif isinstance(doc, dict):
        data = dict(doc)
        data.update(kwargs)
    else:
        raise ValueError("a doc must be a mapping or a DocRecord")
    _needed(data, _DOC_KEYS, "a doc")
    return DocRecord(
        doc_id=data.get("doc_id"), seq=data.get("seq"),
        title=data.get("title"), topic=data.get("topic"),
        standing=data.get("standing"), detail=data.get("detail"),
        keywords=data.get("keywords"), **_provenance(data))


def doc_gaps(doc: Any) -> Tuple[str, ...]:
    """The gaps that keep a doc from answering."""
    checked = _check_doc_ref(doc)
    return () if checked.standing == "current" else ("stale",)


def doc_passes(doc: Any) -> bool:
    return not doc_gaps(doc)


def plain_lines(doc: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the doc's own fields."""
    checked = _check_doc_ref(doc)
    return (
        f"Doc: {checked.title}",
        f"Topic: {checked.topic}",
        f"Standing: {checked.standing}",
    )


def segment_of(doc: Any) -> str:
    checked = _check_doc_ref(doc)
    gaps = doc_gaps(checked)
    return (
        f"{checked.doc_id}: {checked.title} in topic "
        f"'{checked.topic}' - standing: '{checked.standing}' - "
        f"detail: '{checked.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held screen help: `?` on one screen, answered for that screen.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ScreenHelp:
    """One screen's help entry, held as data.

    The entry names the screen it stands for - one
    of the closed screen vocabulary - with its
    title and its detail. One entry stands per
    screen in a book; a screen holding no entry
    stands uncovered, and no other screen's help
    is ever borrowed for it.
    """

    help_id: str
    seq: int
    screen: str
    title: str
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "help_id", _clean_text(self.help_id, "a help id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "screen", normalize_screen(self.screen))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a help title"))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a help detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.help_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "help_id": self.help_id, "seq": self.seq,
            "screen": self.screen, "title": self.title,
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_help_ref(value: Any) -> ScreenHelp:
    if not isinstance(value, ScreenHelp):
        raise ValueError("a screen help must be a ScreenHelp")
    return value


def validate_screen_help(help_entry: Any) -> ScreenHelp:
    return _check_help_ref(help_entry)


def build_screen_help(help_entry: Any = None, **kwargs: Any) -> ScreenHelp:
    if help_entry is None:
        data = dict(kwargs)
    elif isinstance(help_entry, ScreenHelp):
        if kwargs:
            raise ValueError(
                "a screen help stands whole or by fields, not both")
        return help_entry
    elif isinstance(help_entry, dict):
        data = dict(help_entry)
        data.update(kwargs)
    else:
        raise ValueError(
            "a screen help must be a mapping or a ScreenHelp")
    _needed(data, _HELP_KEYS, "a screen help")
    return ScreenHelp(
        help_id=data.get("help_id"), seq=data.get("seq"),
        screen=data.get("screen"), title=data.get("title"),
        detail=data.get("detail"), **_provenance(data))


# ---------------------------------------------------------------------
# The held view: which docs a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class HelpView:
    """A view over the book: every doc, the current, the stale."""

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

    def to_record(self) -> Dict[str, Any]:
        record = {
            "view_id": self.view_id, "seq": self.seq,
            "view_filter": self.view_filter, "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_view_ref(value: Any) -> HelpView:
    if not isinstance(value, HelpView):
        raise ValueError("a view must be a HelpView")
    return value


def validate_view(view: Any) -> HelpView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> HelpView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, HelpView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or a HelpView")
    _needed(data, _VIEW_KEYS, "a view")
    return HelpView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


def inspect_help_source(piece: Any) -> Dict[str, Any]:
    """Name what one help source piece is, without judging it."""
    if isinstance(piece, DocRecord):
        return {"kind": "doc", "doc_id": piece.doc_id}
    if isinstance(piece, dict):
        if "doc_id" in piece:
            return {"kind": "doc", "doc_id": piece.get("doc_id")}
        if "view_id" in piece:
            return {"kind": "view", "view_id": piece.get("view_id")}
        if "help_id" in piece:
            return {"kind": "help", "help_id": piece.get("help_id")}
    return {"kind": "unknown", "doc_id": None}


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class HelpPanelRow:
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


def _row_for_doc(doc: DocRecord) -> HelpPanelRow:
    return HelpPanelRow(
        item_id=doc.doc_id, standing=doc.standing,
        label=doc.title, segment=segment_of(doc),
        recorded_on=doc.recorded_on)


def _check_row_ref(value: Any) -> HelpPanelRow:
    if not isinstance(value, HelpPanelRow):
        raise ValueError("a panel row must be a HelpPanelRow")
    return value


def validate_row(row: Any, doc: Any = None) -> HelpPanelRow:
    checked = _check_row_ref(row)
    if doc is not None:
        derived = _row_for_doc(_check_doc_ref(doc))
        if checked != derived:
            raise ValueError(
                f"panel row {checked.item_id!r} does not agree with "
                f"the row derived from its doc")
    return checked


def build_row(row: Any = None, doc: Any = None,
              **kwargs: Any) -> HelpPanelRow:
    if doc is not None:
        derived = _row_for_doc(_check_doc_ref(doc))
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            HelpPanelRow(**kwargs))
        return validate_row(built, doc)
    if isinstance(row, HelpPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        return HelpPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=normalize_standing(data.get("standing")),
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return HelpPanelRow(**kwargs)
    raise ValueError("a panel row must be a mapping or a HelpPanelRow")


@dataclass(frozen=True)
class StandingCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _standing_counts(rows: Tuple[HelpPanelRow, ...]
                     ) -> Tuple[StandingCount, ...]:
    counts: List[StandingCount] = []
    for standing in STANDING_WORDS:
        number = sum(1 for row in rows if row.standing == standing)
        if number:
            counts.append(StandingCount(standing=standing, items=number))
    return tuple(counts)


def _panel_account(total_items: int, total_shown: int,
                   passing_shown: int,
                   standing_counts: Tuple[StandingCount, ...],
                   view_filter: str, as_of: str) -> Tuple[str, ...]:
    standing_words = ", ".join(
        f"{count.standing} {count.items}"
        for count in standing_counts) or "none"
    return (
        f"The help book holds {total_items} docs as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {passing_shown} of the shown docs "
        f"stand current.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its doc's own fields "
        "- the title, the topic it belongs to and "
        "the standing it honestly stands in - and no "
        "judgement is stored on any doc.",
        "Answers come from the local docs alone: a stale doc "
        "answers nothing, and a question no current held doc "
        "answers stands unanswered, named in its gaps.",
    )


@dataclass(frozen=True)
class HelpPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[HelpPanelRow, ...]
    total_items: int
    total_shown: int
    standing_counts: Tuple[StandingCount, ...]
    as_of: str
    account: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "panel_id": self.panel_id, "view_id": self.view_id,
            "view_filter": self.view_filter,
            "rows": [row.to_record() for row in self.rows],
            "total_items": self.total_items,
            "total_shown": self.total_shown,
            "standing_counts": [c.to_record() for c in self.standing_counts],
            "as_of": self.as_of, "account": list(self.account),
        }


def _held_docs(source: Any) -> Tuple[DocRecord, ...]:
    return _source_book(source).docs


def _resolve_view(source: Any, view: Any) -> HelpView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, HelpView):
        return view
    return book.view_for(view)


def shown_docs(source: Any, view: Any = None
               ) -> Tuple[DocRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.docs
    if resolved.view_filter == "current":
        return tuple(d for d in book.docs if doc_passes(d))
    return tuple(d for d in book.docs if not doc_passes(d))


def docs_for_standing(source: Any, standing: Any
                      ) -> Tuple[DocRecord, ...]:
    wanted = normalize_standing(standing)
    return tuple(
        d for d in _source_book(source).docs if d.standing == wanted)


def passing_docs(source: Any) -> Tuple[DocRecord, ...]:
    return tuple(
        d for d in _source_book(source).docs if doc_passes(d))


def total_docs(source: Any) -> int:
    return len(_source_book(source).docs)


def derive_panel(source: Any, view: Any = None) -> HelpPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_docs(book, resolved)
    rows = tuple(_row_for_doc(doc) for doc in shown)
    counts = _standing_counts(rows)
    as_of = max((d.recorded_on for d in book.docs), default="")
    passing = sum(1 for d in shown if doc_passes(d))
    return HelpPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.docs), total_shown=len(shown),
        standing_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.docs), len(shown), passing, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> HelpPanel:
    if not isinstance(value, HelpPanel):
        raise ValueError("a panel must be a HelpPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> HelpPanel:
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
                     "total_shown", "standing_counts", "as_of", "account"):
            if getattr(checked, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {checked.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return checked


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> HelpPanel:
    if isinstance(panel, HelpPanel):
        if kwargs:
            raise ValueError("a panel stands whole or by fields, not both")
        return validate_panel(panel, source)
    if isinstance(panel, dict):
        data = dict(panel)
        data.update(kwargs)
        rows = tuple(build_row(row) for row in data.get("rows") or ())
        counts = tuple(
            StandingCount(
                standing=normalize_standing(c.get("standing")),
                items=_check_count(c.get("items"), "a standing count"))
            for c in data.get("standing_counts") or ()
            if isinstance(c, dict))
        built = HelpPanel(
            panel_id=_clean_text(data.get("panel_id"), "a panel id"),
            view_id=data.get("view_id"),
            view_filter=normalize_view_filter(data.get("view_filter")),
            rows=rows,
            total_items=_check_count(
                data.get("total_items"), "a total_items count"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            standing_counts=counts,
            as_of=_clean_text(data.get("as_of"), "an as_of day"),
            account=_check_lines(data.get("account"), "the account"))
        return validate_panel(built, source)
    if panel is None and source is not None:
        return derive_panel(source, kwargs.get("view"))
    raise ValueError("a panel must be a mapping, a HelpPanel, or derived")


def _verdict_word(total_shown: int, passing_shown: int) -> str:
    if total_shown > 0 and passing_shown == total_shown:
        return "open"
    if passing_shown == 0:
        return "shut"
    return "strained"


@dataclass(frozen=True)
class HelpVerdict:
    verdict: str
    view_id: Optional[str]
    total_shown: int
    passing_shown: int
    latest_on: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict, "view_id": self.view_id,
            "total_shown": self.total_shown,
            "passing_shown": self.passing_shown,
            "latest_on": self.latest_on,
        }


def derive_verdict(source: Any, view: Any = None) -> HelpVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_docs(book, resolved)
    passing = sum(1 for d in shown if doc_passes(d))
    latest = max((d.recorded_on for d in shown), default="")
    return HelpVerdict(
        verdict=_verdict_word(len(shown), passing),
        view_id=resolved.view_id, total_shown=len(shown),
        passing_shown=passing, latest_on=latest)


def _check_verdict_ref(value: Any) -> HelpVerdict:
    if not isinstance(value, HelpVerdict):
        raise ValueError("a verdict must be a HelpVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> HelpVerdict:
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
                  **kwargs: Any) -> HelpVerdict:
    if isinstance(verdict, HelpVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = HelpVerdict(
            verdict=_clean_text(data.get("verdict"), "a verdict"),
            view_id=data.get("view_id"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            passing_shown=_check_count(
                data.get("passing_shown"), "a passing_shown count"),
            latest_on=_clean_text(data.get("latest_on"), "a latest day"))
        return validate_verdict(built, source)
    if verdict is None and source is not None:
        return derive_verdict(source, kwargs.get("view"))
    raise ValueError(
        "a verdict must be a mapping, a HelpVerdict, or derived")


# ---------------------------------------------------------------------
# The answer: derived from the held docs at call time, never held.
# The coverage: which screens hold a help entry, derived likewise.
# ---------------------------------------------------------------------

def _question_tokens(text: Any) -> frozenset:
    cleaned = _clean_text(text, "a question").lower()
    for mark in "?!.,;:'\"()[]":
        cleaned = cleaned.replace(mark, " ")
    return frozenset(
        word for word in cleaned.split() if word not in _STOPWORDS)


def _doc_tokens(doc: DocRecord) -> frozenset:
    words = set()
    for keyword in doc.keywords:
        words.update(_question_tokens(keyword))
    words.update(_question_tokens(doc.topic))
    words.update(_question_tokens(doc.title))
    return frozenset(words)


@dataclass(frozen=True)
class HelpAnswer:
    """One question's answer, derived from the held docs.

    The answer names the question as asked, the
    current docs it matched in held order, the
    stale docs it matched (which answer nothing),
    the answer lines drawn from the matched docs'
    own words, and its gaps. It stands answered
    when at least one current doc matched; a
    question only a stale doc matches stands
    unanswered with the gap ``stale doc``, and a
    question no doc matches stands unanswered with
    the gap ``no local doc``. Nothing here is
    stored on any doc: the answer is derived at
    call time from the held records alone.
    """

    question: str
    matched: Tuple[str, ...]
    stale_matched: Tuple[str, ...]
    lines: Tuple[str, ...]
    gaps: Tuple[str, ...]

    @property
    def answered(self) -> bool:
        return bool(self.matched)

    def to_record(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "matched": list(self.matched),
            "stale_matched": list(self.stale_matched),
            "lines": list(self.lines),
            "gaps": list(self.gaps),
            "answered": self.answered,
        }


def derive_answer(source: Any, question: Any) -> HelpAnswer:
    """Answer one question from the book's held docs alone."""
    book = _source_book(source)
    asked = _clean_text(question, "a question")
    tokens = _question_tokens(asked)
    matched: List[DocRecord] = []
    stale: List[DocRecord] = []
    for doc in book.docs:
        if tokens and tokens & _doc_tokens(doc):
            if doc_passes(doc):
                matched.append(doc)
            else:
                stale.append(doc)
    lines = tuple(
        f"{doc.title}: {doc.detail}" for doc in matched)
    if matched:
        gaps: Tuple[str, ...] = ()
    elif stale:
        gaps = ("stale doc",)
    else:
        gaps = ("no local doc",)
    return HelpAnswer(
        question=asked,
        matched=tuple(doc.doc_id for doc in matched),
        stale_matched=tuple(doc.doc_id for doc in stale),
        lines=lines, gaps=gaps)


@dataclass(frozen=True)
class HelpCoverage:
    """The screens' coverage, derived from the book's help entries."""

    covered: Tuple[str, ...]
    uncovered: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "covered": list(self.covered),
            "uncovered": list(self.uncovered),
        }


def help_for_screen(source: Any, screen: Any) -> Optional[ScreenHelp]:
    """The held help entry for one screen, or none - honestly."""
    wanted = normalize_screen(screen)
    for entry in _source_book(source).helps:
        if entry.screen == wanted:
            return entry
    return None


def covered_screens(source: Any) -> Tuple[str, ...]:
    held = {entry.screen for entry in _source_book(source).helps}
    return tuple(screen for screen in SCREENS if screen in held)


def uncovered_screens(source: Any) -> Tuple[str, ...]:
    held = {entry.screen for entry in _source_book(source).helps}
    return tuple(screen for screen in SCREENS if screen not in held)


def derive_coverage(source: Any) -> HelpCoverage:
    return HelpCoverage(
        covered=covered_screens(source),
        uncovered=uncovered_screens(source))


# ---------------------------------------------------------------------
# The book: docs, views and screen helps held together, one pinned
# panel at most per telling, and no verdict or answer ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class HelpBook:
    title: str
    docs: Tuple[DocRecord, ...] = ()
    views: Tuple[HelpView, ...] = ()
    helps: Tuple[ScreenHelp, ...] = ()
    panels: Tuple[HelpPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        docs = tuple(_check_doc_ref(d) for d in self.docs)
        views = tuple(_check_view_ref(v) for v in self.views)
        helps = tuple(_check_help_ref(h) for h in self.helps)
        panels = tuple(_check_panel_ref(p) for p in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for doc in docs:
            if doc.doc_id in seen_ids:
                raise ValueError(
                    f"two docs stand under id {doc.doc_id!r}")
            if doc.seq in seen_seqs:
                raise ValueError(
                    f"two docs stand at sequence {doc.seq}")
            seen_ids.add(doc.doc_id)
            seen_seqs.add(doc.seq)
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
        help_ids = set()
        help_seqs = set()
        help_screens = set()
        for entry in helps:
            if entry.help_id in help_ids:
                raise ValueError(
                    f"two screen helps stand under id "
                    f"{entry.help_id!r}")
            if entry.seq in help_seqs:
                raise ValueError(
                    f"two screen helps stand at sequence {entry.seq}")
            if entry.screen in help_screens:
                raise ValueError(
                    f"two screen helps stand for screen "
                    f"{entry.screen!r}: one help entry stands "
                    f"per screen")
            help_ids.add(entry.help_id)
            help_seqs.add(entry.seq)
            help_screens.add(entry.screen)
        object.__setattr__(
            self, "docs", tuple(sorted(docs, key=lambda d: d.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "helps", tuple(sorted(helps, key=lambda h: h.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.docs + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(d.doc_id for d in self.docs) + tuple(
            v.view_id for v in self.views)

    def doc_ids(self) -> Tuple[str, ...]:
        return tuple(d.doc_id for d in self.docs)

    def doc_for(self, doc_id: Any) -> DocRecord:
        wanted = _clean_text(doc_id, "a doc id")
        for doc in self.docs:
            if doc.doc_id == wanted:
                return doc
        raise KeyError(f"no doc named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> HelpView:
        wanted = _clean_text(view_id, "a view id")
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no view named {wanted!r} stands in this book")

    def help_for(self, help_id: Any) -> ScreenHelp:
        wanted = _clean_text(help_id, "a help id")
        for entry in self.helps:
            if entry.help_id == wanted:
                return entry
        raise KeyError(f"no screen help named {wanted!r} stands in this book")

    def item_for(self, item_id: Any) -> Any:
        wanted = _clean_text(item_id, "an item id")
        for doc in self.docs:
            if doc.doc_id == wanted:
                return doc
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "docs": [d.to_record() for d in self.docs],
            "views": [v.to_record() for v in self.views],
            "helps": [h.to_record() for h in self.helps],
            "panels": [p.to_record() for p in self.panels],
        }


def _judge_book_panels(book: HelpBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: HelpBook) -> None:
    if book.title != "Help that answers at the M-185 slice boundary":
        raise ValueError("the shipped example book carries another title")
    if len(book.docs) != 6 or len(book.views) != 2:
        raise ValueError(
            "the shipped example book must hold six docs and two views")
    if len(book.helps) != 4:
        raise ValueError(
            "the shipped example book must hold four screen helps")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m185-boundary":
        raise ValueError("the pinned panel is panel-m185-boundary")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "strained" or verdict.passing_shown != 5:
        raise ValueError(
            "the shipped example book's verdict must stand strained "
            "at five current of six")
    answer = derive_answer(book, EXAMPLE_QUESTION)
    if not answer.answered or answer.matched != ("doc-undo-commit",):
        raise ValueError(
            "the shipped example book must answer the roadmap's "
            "example question from its undo doc alone")
    coverage = derive_coverage(book)
    if coverage.uncovered != (
            "review", "settings", "onboarding", "command palace"):
        raise ValueError(
            "the shipped example book must leave the review, "
            "settings, onboarding and command palace screens "
            "honestly uncovered")


def validate_book(data: Any, *, require_example: bool = False) -> HelpBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, HelpBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a help book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live answer road "
                f"({key!r} is named on it): {LOCAL_DOCS_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its docs under a view")
    if "answer" in data or "answers" in data:
        raise ValueError(
            "a book stores no answer: answers are derived from "
            "its held docs at call time")
    if data.get("schema") is not None and (
            data["schema"] != HELP_ANSWERS_SCHEMA):
        raise ValueError(
            f"a book's schema must be {HELP_ANSWERS_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != HELP_ANSWERS_SLICE):
        raise ValueError(
            f"a book's slice must be {HELP_ANSWERS_SLICE!r}")
    guide = data.get("guide") or {}
    if not isinstance(guide, dict):
        raise ValueError("a book's guide must be a mapping")
    title = guide.get("title") or data.get("title")
    docs = tuple(build_doc(d) for d in data.get("docs") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    helps = tuple(
        build_screen_help(h) for h in data.get("helps") or ())
    book = HelpBook(
        title=title, docs=docs, views=views, helps=helps, panels=())
    panels = tuple(
        build_panel(p, book) for p in data.get("panels") or ())
    book = HelpBook(
        title=book.title, docs=book.docs, views=book.views,
        helps=book.helps, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> HelpBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (HelpBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or a HelpBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> HelpBook:
    return validate_book(data, require_example=require_example)


def load_help_answers(
        data: Optional[Dict[str, Any]] = None) -> HelpBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(HELP_ANSWERS_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_help_answers_file(path: Any) -> HelpBook:
    """Load one help file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: docs and views held one by one.
# ---------------------------------------------------------------------

class HelpRegistry:
    """An in-memory holding of docs and views.

    The registry is the pure layer's model of a
    session's help book: docs are held under their
    ids, one doc per id and per sequence, and views
    are held in recorded order, one view per
    sequence and per id. Holding is data only -
    nothing held here searches anything live, calls
    a model, or opens any network.
    """

    def __init__(self, book: Any = None) -> None:
        self._docs: List[DocRecord] = []
        self._views: List[HelpView] = []
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

    def register_doc(self, item: Any) -> DocRecord:
        """Hold one doc, judged whole before held."""
        return self._register(
            self._docs, _check_doc_ref(item), "doc_id", "doc")

    def register_view(self, view: Any) -> HelpView:
        """Hold one view; a view naming no id takes a fresh one."""
        checked = _check_view_ref(view)
        if not checked.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            checked = build_view({**checked.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, checked, "view_id", "view")

    def register_book(self, book: Any) -> HelpBook:
        """Hold a whole book's docs and views, under its title."""
        checked = build_book(book)
        if self._title is not None and checked.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {checked.title!r}")
        for doc in checked.docs:
            self.register_doc(doc)
        for view in checked.views:
            self.register_view(view)
        self._title = checked.title
        return self.book()

    def book(self) -> HelpBook:
        return HelpBook(
            title=self._title or "An unheld help book",
            docs=tuple(self._docs), views=tuple(self._views),
            helps=(), panels=())

    def list_docs(self) -> Tuple[DocRecord, ...]:
        return tuple(self._docs)

    def list_views(self) -> Tuple[HelpView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._docs) + tuple(self._views)

    def get_doc(self, doc_id: Any) -> DocRecord:
        return self.book().doc_for(doc_id)

    def get_view(self, view_id: Any) -> HelpView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records shaped for the journal road.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> HelpBook:
    if source is None:
        return load_help_answers()
    if isinstance(source, HelpBook):
        return source
    if isinstance(source, HelpRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def doc_record(doc: Any, source: Any = None) -> Dict[str, Any]:
    checked = _check_doc_ref(doc)
    record = {
        "type": "help_doc",
        "slice": HELP_ANSWERS_SLICE,
        "doc_id": checked.doc_id,
        "title": checked.title,
        "segment": segment_of(checked),
        "passes": doc_passes(checked),
        "gaps": list(doc_gaps(checked)),
    }
    record.update(_provenance_record(checked))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    checked = _check_view_ref(view)
    record = {
        "type": "help_view",
        "slice": HELP_ANSWERS_SLICE,
        "view_id": checked.view_id, "seq": checked.seq,
        "view_filter": checked.view_filter,
    }
    record.update(_provenance_record(checked))
    return record


def screen_record(entry: Any) -> Dict[str, Any]:
    checked = _check_help_ref(entry)
    record = {
        "type": "help_screen",
        "slice": HELP_ANSWERS_SLICE,
        "help_id": checked.help_id,
        "screen": checked.screen,
    }
    record.update(_provenance_record(checked))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    checked = validate_panel(panel, source)
    record = {"type": "help_panel", "slice": HELP_ANSWERS_SLICE}
    record.update(checked.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, HelpVerdict):
        checked = validate_verdict(verdict, source)
    else:
        checked = derive_verdict(_source_book(verdict), view)
    record = {"type": "help_verdict", "slice": HELP_ANSWERS_SLICE}
    record.update(checked.to_record())
    return record


def answer_record(source: Any, question: Any = None) -> Dict[str, Any]:
    if isinstance(source, HelpAnswer):
        checked = source
    else:
        checked = derive_answer(source, question)
    record = {"type": "help_answer", "slice": HELP_ANSWERS_SLICE}
    record.update(checked.to_record())
    return record


def coverage_record(source: Any) -> Dict[str, Any]:
    coverage = derive_coverage(source)
    record = {"type": "help_coverage", "slice": HELP_ANSWERS_SLICE}
    record.update(coverage.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    checked = _source_book(book)
    record = {"type": "help_book", "slice": HELP_ANSWERS_SLICE,
              "title": checked.title}
    record.update(checked.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(doc: Any, source: Any = None) -> str:
    checked = _check_doc_ref(doc)
    return (
        f"{checked.title} - in topic {checked.topic}: "
        f"{checked.standing}. {checked.detail}")


def doc_plain_words(doc: Any, source: Any = None) -> str:
    return plain_words(doc, source)


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The help book stands {verdict.verdict}: "
        f"{verdict.passing_shown} of {verdict.total_shown} shown "
        f"docs stand current.")


def view_plain_words(view: Any) -> str:
    checked = _check_view_ref(view)
    return f"View {checked.view_id}: shows {checked.view_filter} docs."


def answer_plain_words(source: Any, question: Any = None) -> str:
    answer = (source if isinstance(source, HelpAnswer)
              else derive_answer(source, question))
    if answer.answered:
        return (
            f"Answered from the local docs: "
            f"{', '.join(answer.matched)}.")
    return (
        f"Unanswered - no current local doc answers this "
        f"question (gaps: {', '.join(answer.gaps)}).")


def coverage_plain_words(source: Any) -> str:
    coverage = derive_coverage(source)
    covered = ", ".join(coverage.covered) or "none"
    uncovered = ", ".join(coverage.uncovered) or "none"
    return (
        f"Help stands held for {len(coverage.covered)} of "
        f"{len(SCREENS)} screens ({covered}); uncovered: "
        f"{uncovered}.")


def format_doc(doc: Any, source: Any = None) -> str:
    checked = _check_doc_ref(doc)
    lines = [f"{checked.title} ({checked.doc_id})"]
    lines.extend(plain_lines(checked))
    lines.append(checked.detail)
    if doc_passes(checked):
        lines.append("This doc stands current and answers questions.")
    else:
        lines.append(
            "This doc stands stale - named in its gaps, "
            "answering nothing until it is refreshed.")
    return "\n".join(lines)


def format_view(view: Any) -> str:
    checked = _check_view_ref(view)
    return (
        f"View {checked.view_id}: filter {checked.view_filter} - "
        f"{checked.detail}")


def format_screen_help(entry: Any) -> str:
    checked = _check_help_ref(entry)
    return (
        f"Help for the {checked.screen} screen "
        f"({checked.help_id}): {checked.title}. {checked.detail}")


def format_screen(source: Any, screen: Any) -> str:
    entry = help_for_screen(source, screen)
    if entry is not None:
        return format_screen_help(entry)
    wanted = normalize_screen(screen)
    return (
        f"No held help stands for the {wanted} screen yet - "
        f"it stands uncovered, named in the book's gaps, and "
        f"no other screen's help is borrowed for it.")


def format_book(source: Any = None, standing: Any = None) -> str:
    book = _source_book(source)
    docs = (docs_for_standing(book, standing)
            if standing is not None else book.docs)
    lines = [f"Help That Answers (M-186) - {book.title}"]
    lines.extend(segment_of(doc) for doc in docs)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Help panel under view {panel.view_id}:"]
    lines.extend(row.segment for row in panel.rows)
    lines.extend(panel.account)
    return "\n".join(lines)


def format_verdict(source: Any = None, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return verdict_plain_words(source, view) + (
        f" (view {verdict.view_id}, as of {verdict.latest_on})")


def format_answer(source: Any, question: Any = None) -> str:
    answer = (source if isinstance(source, HelpAnswer)
              else derive_answer(source, question))
    lines = [f"Question: {answer.question}"]
    if answer.answered:
        lines.extend(answer.lines)
        lines.append(
            "Answered from the local docs held on this machine "
            f"({', '.join(answer.matched)}) - no live search, "
            "no network, no model call.")
    else:
        lines.append(
            "This question stands unanswered: no current local "
            f"doc answers it (gaps: {', '.join(answer.gaps)}). "
            "No answer is invented for it.")
    return "\n".join(lines)


def format_coverage(source: Any = None) -> str:
    book = _source_book(source)
    lines = ["Screen help coverage, from the held entries:"]
    for entry in book.helps:
        lines.append(format_screen_help(entry))
    lines.append(coverage_plain_words(book))
    return "\n".join(lines)


def format_help_answers_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "Help That Answers (M-186)",
        f"{book.title}: {len(book.docs)} docs held, "
        f"{len(passing_docs(book))} docs standing current, "
        f"{len(book.helps)} screens holding help.",
    ]
    if book.views:
        panel = derive_panel(book, book.views[0])
        lines.append(
            f"{panel.total_shown} of {panel.total_items} items show "
            f"under the first view.")
        lines.extend(row.segment for row in panel.rows)
    lines.append(coverage_plain_words(book))
    lines.append(PLAIN_EXPLANATION)
    return "\n".join(lines)


def parse_help_args(args: Any) -> Tuple[str, Any]:
    """Parse the /helpask grammar into (action, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("doc", "view", "standing"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("ask", "screen"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("panel", "verdict", "coverage") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
