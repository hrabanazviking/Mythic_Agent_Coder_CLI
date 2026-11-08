"""The @-mention canon (All-Features roadmap slice M-148).

Part VII continues. The roadmap's words:
``@file, @folder, @symbol, @url, @image,
@session, @issue - one grammar for pulling
anything into context, in TUI and headless
alike.``

What already shipped, and what this slice adds:

* Pulling things into the context already has
  shipped roads, one per kind of thing: explicit
  files resolve through the context compiler's
  explicit-files source (``context/files.py``,
  Slice 056 - ``@src/main.py`` in a query resolves
  against the workspace, containment enforced);
  folders are mapped by the repo map
  (``context/repo_map.py`` - ``build_repo_map`` and
  its compiler source); symbols select their
  defining files through the symbol index
  (``context/symbols.py``, Slice 058); a URL is
  fetched by the web tools' fetch road
  (``tools/web_search.py``, M-059 -
  ``Agent.web_fetch``); an image rides the vision
  road (``core/vision_routing.py``, the ``/vision``
  surface); a session is read back from the
  session store (``core/sessions.py`` -
  ``SessionStore``); and an issue is fetched and
  planned through the issue-to-slice road
  (``core/issue_slice.py``, M-083, over the GitHub
  road of Slice 36). Those roads PULL. What
  nothing holds is the one grammar that NAMES a
  pull, as data: a single mention form every kind
  shares, validated once, with the road each kind
  would take named beside it.
* This slice is that grammar, as a pure layer: a
  mention record validated as data (one pull
  named in text - its closed kind, its target,
  the exact text that named it, its source, and
  the plain-words reason it is pulled), a canon
  book holding mentions in held order, a
  resolution plan DERIVED from a mention (the
  shipped road that would pull it, the action
  that road takes, and what it would pull - named,
  never run), an index DERIVED from the whole
  book (its rows the plans themselves, its totals
  the mentions' own counts), the shipped data
  file (``mythic_agent/data/mentions.yaml``)
  holding one example canon in exactly the shape
  a real canon file takes, a loader for a canon
  file anywhere on disk, a parser for mention
  text (the typed forms and the shipped bare
  form), records shaped as session news, and a
  small in-memory registry model. This module
  reads no file, fetches no page, compiles no
  context and imports no agent / UI code; the
  agent layer owns holding a canon for a session.

Honesty rules, enforced here and pinned by tests:

* **The kinds are the roadmap's own seven.**
  A mention's kind is one of a closed set the
  roadmap itself names: ``file``, ``folder``,
  ``symbol``, ``url``, ``image``, ``session`` and
  ``issue``. A kind outside that set refuses -
  in a record, and in parsed text alike: an
  unknown typed mention (``@bogus:x``) refuses
  plainly instead of being guessed at, and a
  typed mention naming no target refuses too.
* **The bare form is the shipped form.** Text
  like ``@src/main.py`` - the form Slice 056
  already resolves - parses as a ``file`` mention
  of that path, exactly as the shipped
  ``extract_mentions`` reads it. Every other kind
  is named in its typed form, ``@kind:target``;
  no second spelling is invented here.
* **A plan names a shipped road, never a new
  one.** Each kind's plan names the road that
  already pulls that kind into the context (the
  explicit-files source for a file, the repo map
  for a folder, the symbol selection for a
  symbol, the web fetch for a URL, the vision
  road for an image, the session store for a
  session, the issue road for an issue) - the
  roads are named as words, composed by naming,
  never imported or re-implemented here.
* **The plan is derived, never stored loose.**
  A plan is read off its mention at call time -
  its kind, target and road are the mention's
  own - so a stored plan judged against its
  mention refuses on any disagreement, and a
  plan record carrying an unknown key refuses.
* **The index is derived, never stored loose.**
  The index's rows are the mentions' plans, in
  held order, and its totals are the mentions'
  own counts, so a stored index whose rows,
  totals or account disagree with the index
  derived from its book refuses.
* **Data only - parsing pulls nothing.** A
  mention here is a validated record held as
  data, and a plan is the NAME of a road: no
  file is read, no page is fetched, no symbol
  is indexed, no session is opened, no issue is
  fetched, no context is compiled and nothing
  is persisted. The pull itself happens only
  when a prompt is later compiled through the
  shipped roads themselves. The canon is
  visible through this slice's own /mentions
  screen.
* **Malformed refuses.** A duplicate mention id
  in one canon, a target that does not fit its
  kind (a URL naming no http(s) address, a
  symbol naming no identifier, a path carrying
  spaces), and unknown keys in a mention, a
  plan, an index or a canon mapping all raise
  instead of being skipped or guessed at.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .crew_members import normalize_member_id
from .validation import ValidationError

__all__ = [
    "PLAIN_EXPLANATION",
    "MENTIONS_RESOURCE",
    "MENTIONS_SCHEMA",
    "MENTIONS_SLICE",
    "MENTION_KINDS",
    "MENTION_ROADS",
    "USAGE",
    "Mention",
    "MentionCanon",
    "MentionIndex",
    "MentionKindCount",
    "MentionPlan",
    "MentionRegistry",
    "book_record",
    "build_canon",
    "build_index",
    "build_mention",
    "build_plan",
    "derive_index",
    "derive_plan",
    "format_mention",
    "format_mention_text",
    "format_mentions",
    "format_mentions_screen",
    "format_index",
    "format_plan",
    "index_plain_words",
    "index_record",
    "load_mentions",
    "load_mentions_file",
    "mention_record",
    "normalize_kind",
    "parse_mention",
    "parse_mentions",
    "parse_mentions_args",
    "plan_plain_words",
    "plan_record",
    "plain_words",
    "validate_book",
    "validate_index",
    "validate_mention",
    "validate_plan",
]

MENTIONS_SLICE = "M-148"

#: The packaged data resource holding the example canon.
MENTIONS_RESOURCE = "mentions.yaml"

#: The schema word a mentions file must carry.
MENTIONS_SCHEMA = "mythic.mentions/1"

#: The kinds one mention may hold, in roadmap
#: order: the seven the roadmap itself names -
#: a file, a folder, a symbol, a URL, an image,
#: a session and an issue. No other kind is held.
MENTION_KINDS = (
    "file", "folder", "symbol", "url",
    "image", "session", "issue")

#: The shipped road each kind's plan names: the
#: road that already pulls that kind into the
#: context, named as words - composed by naming,
#: never imported or re-implemented here.
MENTION_ROADS = {
    "file": (
        "mythic_agent.context.files.resolve_mentions "
        "(ExplicitFilesSource, Slice 056)"),
    "folder": (
        "mythic_agent.context.repo_map.build_repo_map "
        "(RepoMapSource)"),
    "symbol": (
        "mythic_agent.context.symbols.select_by_symbols "
        "(SymbolFilesSource, Slice 058)"),
    "url": (
        "mythic_agent.tools.web_search fetch road "
        "(Agent.web_fetch, M-059)"),
    "image": (
        "mythic_agent.core.vision_routing "
        "(/vision road)"),
    "session": (
        "mythic_agent.core.sessions.SessionStore "
        "(session journal export)"),
    "issue": (
        "mythic_agent.core.issue_slice planning road "
        "over integrations/github.py (M-083, Slice 36)"),
}

#: What each kind's road does, in plain words.
_KIND_ACTIONS = {
    "file": (
        "Resolve the named file against the workspace "
        "and read its text"),
    "folder": (
        "Map the named folder through the repo map"),
    "symbol": (
        "Index the workspace symbols and select the "
        "files defining the named symbol"),
    "url": (
        "Fetch the named page and extract its "
        "readable text"),
    "image": (
        "Attach the named image through the vision "
        "road"),
    "session": (
        "Read the named session from the session "
        "store"),
    "issue": (
        "Fetch the named issue through the issue "
        "road"),
}

#: What each kind's road would pull, in plain words.
_KIND_PULLS = {
    "file": "The file's text, as one context block",
    "folder": (
        "The folder's repo-map section: its files "
        "and their definitions"),
    "symbol": "The files that define the named symbol",
    "url": (
        "The page's readable text, cited into the "
        "journal"),
    "image": (
        "The image itself, for a vision-capable "
        "model"),
    "session": (
        "The named session's recorded turns and "
        "events"),
    "issue": (
        "The issue's title and body, as planned "
        "context"),
}

#: The plain-words reason a parsed mention of
#: each kind carries, until a fuller reason is
#: named for it.
_KIND_REASONS = {
    "file": (
        "The named file is pulled so the coder "
        "works from its true text."),
    "folder": (
        "The named folder is pulled so the coder "
        "sees the shape of that part of the tree."),
    "symbol": (
        "The named symbol is pulled so the coder "
        "sees where it is defined."),
    "url": (
        "The named page is pulled so its words "
        "stand in the context."),
    "image": (
        "The named image is pulled so the coder "
        "can see it."),
    "session": (
        "The named session is pulled so its record "
        "stands in the context."),
    "issue": (
        "The named issue is pulled so its own "
        "words steer the work."),
}

_MENTION_KEYS = frozenset({
    "mention_id", "id", "kind", "target",
    "raw", "text", "source", "origin",
    "reason", "why",
})

_PLAN_KEYS = frozenset({
    "mention_id", "id", "kind", "target",
    "road", "action", "pulls",
})

_KIND_COUNT_KEYS = frozenset({
    "kind", "mentions", "count",
})

_INDEX_KEYS = frozenset({
    "index_id", "id", "rows", "plans",
    "total_mentions", "total", "kind_counts", "kinds",
    "account", "statements",
})

_BOOK_KEYS = frozenset({"title", "name"})

_MENTIONS_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "canon_note", "guide", "entries", "mentions",
    "plans", "indexes",
})

#: The shipped example canon's title, held to
#: this by the loader's example check.
_EXAMPLE_TITLE = "Mention canon at the M-147 slice boundary"

#: The shipped example's mention ids, in held
#: order, pinned by the loader: one mention of
#: every kind.
_EXAMPLE_MENTION_IDS = (
    "mention-file-context-budget", "mention-folder-context",
    "mention-symbol-token-estimator", "mention-url-ast-docs",
    "mention-image-kiosk-snapshot", "mention-session-m147",
    "mention-issue-148")

#: The shipped example's kinds, in held order,
#: pinned by the loader: every kind held once.
_EXAMPLE_KINDS = MENTION_KINDS

#: The shipped example's one plan and index ids.
_EXAMPLE_INDEX_ID = "index-m147-boundary"

_EXAMPLE_INDEX_ACCOUNT = (
    "The canon holds 7 mention(s): file 1, "
    "folder 1, symbol 1, url 1, image 1, "
    "session 1, issue 1.",
    "Every mention names the shipped road that "
    "would pull it into context; parsing and "
    "planning pull nothing in by themselves.",
    "The index is read off the held mentions at "
    "call time - it is derived, never stored "
    "loose.",
)

PLAIN_EXPLANATION = (
    "The @-mention canon: one grammar for pulling "
    "anything into context - @file, @folder, "
    "@symbol, @url, @image, @session, @issue. A "
    "mention names one pull in text: its kind (one "
    "of the roadmap's seven), its target, the exact "
    "text that named it, its source, and the "
    "plain-words reason it is pulled. The bare form "
    "(@src/main.py, the form the shipped "
    "explicit-files road already resolves) parses "
    "as a file mention; every other kind is named "
    "in its typed form, @kind:target, and an "
    "unknown kind refuses plainly. A resolution "
    "plan is derived from a mention at call time: "
    "it names the shipped road that would pull "
    "that kind into context, what that road does, "
    "and what it would pull - named, never run - "
    "and the index is derived from the whole "
    "canon likewise, so a stored plan or index "
    "that disagrees refuses. This layer holds the "
    "grammar as data only: it reads no file, "
    "fetches no page, compiles no context and "
    "persists nothing itself - parsing and "
    "planning pull nothing in."
)

USAGE = (
    "Usage: /mentions, /mentions show, "
    "/mentions mention <mention-id>, "
    "/mentions kind <kind>, "
    "/mentions plan <mention-id>, "
    "/mentions parse <text>, /mentions index"
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


def normalize_kind(value: Any) -> str:
    """The canonical mention kind a word names.

    A kind is one of :data:`MENTION_KINDS` - the
    seven the roadmap itself names - read
    case-insensitively. Anything else raises,
    plainly naming the seven.
    """
    if isinstance(value, str):
        wanted = value.strip().lower()
        if wanted in MENTION_KINDS:
            return wanted
    raise ValueError(
        "a mention kind must be one of %s, got %r"
        % ("/".join(MENTION_KINDS), value))


_PATH_TARGET_RE = re.compile(r"^[A-Za-z0-9_./~+@-]+$")
_SYMBOL_TARGET_RE = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$")
_SESSION_TARGET_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
_ISSUE_TARGET_RE = re.compile(r"^(?:#)?[A-Za-z0-9_.-]+$")


def _check_target(kind: str, value: Any) -> str:
    """One mention's target, judged against its kind."""
    text = _clean_text(value, "a mention's target")
    if len(text) > 300 or "\x00" in text:
        raise ValueError(
            f"a mention's target must be plain text of at "
            f"most 300 characters, got {len(text)} characters")
    if any(ch.isspace() for ch in text):
        raise ValueError(
            f"a {kind} mention's target names no spaces, "
            f"got {text!r}")
    if kind in ("file", "folder", "image"):
        if not _PATH_TARGET_RE.match(text):
            raise ValueError(
                f"a {kind} mention's target must be a path "
                f"of letters, digits and _ . / ~ + @ -, "
                f"got {text!r}")
    elif kind == "symbol":
        if not _SYMBOL_TARGET_RE.match(text):
            raise ValueError(
                f"a symbol mention's target must be a "
                f"symbol name (dots may qualify it), "
                f"got {text!r}")
    elif kind == "url":
        if not (text.startswith("http://")
                or text.startswith("https://")):
            raise ValueError(
                f"a url mention's target must be an "
                f"http(s) address, got {text!r}")
    elif kind == "session":
        if not _SESSION_TARGET_RE.match(text):
            raise ValueError(
                f"a session mention's target must be a "
                f"session id word, got {text!r}")
    elif kind == "issue":
        if not _ISSUE_TARGET_RE.match(text):
            raise ValueError(
                f"an issue mention's target must be an "
                f"issue number or id word, got {text!r}")
    return text


def format_mention_text(mention: Any) -> str:
    """The canonical typed text of one mention.

    Every mention's canonical text is its typed
    form, ``@kind:target`` - the one grammar this
    slice names - whatever spelling first named
    it (a bare ``@path`` file mention's canonical
    text is ``@file:path``).
    """
    current = mention if isinstance(mention, Mention) \
        else build_mention(mention)
    return f"@{current.kind}:{current.target}"


# ---------------------------------------------------------------------
# The mention: one pull named in text, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class Mention:
    """One pull named in text, as a validated record.

    ``kind`` is the mention's kind in the closed
    set the roadmap names; ``target`` is what the
    mention pulls at, judged against its kind;
    ``raw`` is the exact text that named it (its
    canonical typed text when none is named);
    ``source`` names where the mention was
    written; ``reason`` says in plain words WHY
    it is pulled. The record names NO plan of its
    own: the plan is derived from the mention at
    call time, so a mention can never claim a
    road its kind does not name.
    """

    kind: str
    target: str
    source: str
    reason: str
    raw: Optional[str] = None
    mention_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.mention_id is not None:
            object.__setattr__(
                self, "mention_id",
                normalize_member_id(self.mention_id))
        kind = normalize_kind(self.kind)
        object.__setattr__(self, "kind", kind)
        object.__setattr__(
            self, "target", _check_target(kind, self.target))
        object.__setattr__(
            self, "source",
            _check_title(self.source, "a mention's source"))
        object.__setattr__(
            self, "reason",
            _check_long_text(self.reason, "a mention's reason"))
        if self.raw is None:
            object.__setattr__(
                self, "raw", f"@{kind}:{self.target}")
        else:
            object.__setattr__(
                self, "raw",
                _check_title(self.raw, "a mention's text"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "mentions_mention",
            "slice": MENTIONS_SLICE,
            "mention_id": self.mention_id,
            "kind": self.kind,
            "target": self.target,
            "raw": self.raw,
            "source": self.source,
            "reason": self.reason,
        }


def validate_mention(mention: Any) -> Mention:
    """Validate one mention record into a Mention.

    Accepts a Mention or a mapping naming a
    ``kind``, a ``target``, a ``source`` (or
    ``origin``), a ``reason`` (or ``why``), an
    optional ``raw`` text (or ``text``) and an
    optional ``mention_id`` (or ``id``). Naming
    two spellings of one field with different
    values refuses, and unknown keys refuse - a
    stored plan key among them, because the plan
    is derived from the mention, never stored on
    it.
    """
    if isinstance(mention, Mention):
        return mention
    if not isinstance(mention, dict):
        raise ValueError(
            f"a mention record must be a mapping, "
            f"got {mention!r}")
    unknown = set(mention) - _MENTION_KEYS
    if unknown:
        raise ValueError(
            "unknown mention keys: %s"
            % ", ".join(sorted(unknown)))
    kind = _pick_any(mention, ("kind",), "kinds")
    if kind is None:
        raise ValueError("a mention record is missing its kind")
    target = _pick_any(mention, ("target",), "targets")
    if target is None:
        raise ValueError("a mention record is missing its target")
    source = _pick_any(mention, ("source", "origin"), "sources")
    if source is None:
        raise ValueError("a mention record is missing its source")
    reason = _pick_any(mention, ("reason", "why"), "reasons")
    if reason is None:
        raise ValueError("a mention record is missing its reason")
    kwargs: Dict[str, Any] = {
        "kind": kind, "target": target, "source": source,
        "reason": reason}
    raw = _pick_any(mention, ("raw", "text"), "texts")
    if raw is not None:
        kwargs["raw"] = raw
    mention_id = _pick_any(mention, ("mention_id", "id"), "mention ids")
    if mention_id is not None:
        kwargs["mention_id"] = mention_id
    return Mention(**kwargs)


def build_mention(mention: Any = None, **kwargs: Any) -> Mention:
    """Build one validated mention, from a mapping or field words."""
    if isinstance(mention, Mention) and not kwargs:
        return mention
    if isinstance(mention, dict) or mention is None:
        merged: Dict[str, Any] = {}
        if isinstance(mention, dict):
            merged.update(mention)
        merged.update(kwargs)
        return validate_mention(merged)
    raise ValueError(
        f"a mention record must be a mapping, got {mention!r}")


def _check_mention_ref(value: Any) -> Mention:
    if isinstance(value, Mention):
        return value
    if isinstance(value, dict):
        return validate_mention(value)
    raise ValueError(f"a mention record is needed, got {value!r}")


def _held_mentions(source: Any) -> Tuple[Mention, ...]:
    """The mentions one source holds, in held order."""
    if isinstance(source, MentionCanon):
        return source.mentions
    if isinstance(source, MentionRegistry):
        return source.list_mentions()
    if isinstance(source, (list, tuple)):
        return tuple(_check_mention_ref(e) for e in source)
    raise ValueError(f"mentions are needed, got {source!r}")


# ---------------------------------------------------------------------
# The grammar: mention text parsed into mention records.
# ---------------------------------------------------------------------

#: One mention in text: the typed form
#: ``@kind:target`` first, then the shipped bare
#: form ``@path`` of Slice 056. A typed mention
#: naming no target still matches (its empty
#: target refuses in validation, plainly).
_MENTION_TEXT_RE = re.compile(
    r"@([A-Za-z]+):([^\s]*)"
    r"|@([A-Za-z0-9_./-][\w.\-/]*)")

_TRAILING_JUNK = ".,;:!?"


def _trim_target(target: str) -> str:
    """Sentence punctuation riding a target's tail, trimmed."""
    trimmed = target.rstrip(_TRAILING_JUNK)
    while trimmed.endswith(")") and "(" not in trimmed:
        trimmed = trimmed[:-1].rstrip(_TRAILING_JUNK)
    while trimmed.endswith("]") and "[" not in trimmed:
        trimmed = trimmed[:-1].rstrip(_TRAILING_JUNK)
    return trimmed


def parse_mentions(text: Any, *,
                   source: Any = "prompt text") -> Tuple[Mention, ...]:
    """Parse every mention in *text* into mention records.

    The typed forms (``@file:``, ``@folder:``,
    ``@symbol:``, ``@url:``, ``@image:``,
    ``@session:``, ``@issue:``) name their kind;
    the bare form - ``@src/main.py``, the form
    Slice 056 already resolves - parses as a
    ``file`` mention of that path. Mentions stand
    in order of first appearance, deduplicated by
    kind and target. An unknown typed kind
    refuses plainly, naming the seven, as does a
    typed mention naming no target and a target
    that does not fit its kind. Each parsed
    mention carries the kind's plain-words reason
    (see :data:`_KIND_REASONS`) and the named
    *source*. Parsing reads no file, fetches
    nothing and pulls nothing in: it names pulls
    as data, and that is all.
    """
    if not isinstance(text, str):
        raise ValueError(f"mention text must be text, got {text!r}")
    source_word = _check_title(source, "a mention's source")
    found: list = []
    seen = set()
    for match in _MENTION_TEXT_RE.finditer(text):
        if match.group(1) is not None:
            kind = normalize_kind(match.group(1))
            target = _trim_target(match.group(2) or "")
            if not target:
                raise ValueError(
                    f"a @{kind}: mention names no target")
            raw = f"@{match.group(1)}:{target}"
        else:
            kind = "file"
            target = _trim_target(match.group(3) or "")
            if not target:
                continue
            raw = match.group(0)
            if raw != f"@{target}":
                raw = f"@{target}"
        key = (kind, target)
        if key in seen:
            continue
        seen.add(key)
        found.append(Mention(
            kind=kind, target=target, source=source_word,
            reason=_KIND_REASONS[kind], raw=raw))
    return tuple(found)


def parse_mention(text: Any, *,
                  source: Any = "prompt text") -> Mention:
    """Parse exactly one mention out of *text*.

    Text naming no mention, or more than one,
    refuses - this road names one pull.
    """
    found = parse_mentions(text, source=source)
    if not found:
        raise ValueError(f"no mention stands in the text: {text!r}")
    if len(found) > 1:
        raise ValueError(
            f"the text names {len(found)} mentions, not one")
    return found[0]


# ---------------------------------------------------------------------
# The resolution plan: the road a mention would take, derived.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class MentionPlan:
    """One mention's resolution plan, derived from it.

    ``road`` names the shipped road that would
    pull the mention's kind into the context;
    ``action`` says in plain words what that road
    does; ``pulls`` says what it would pull. Every
    field is the mention's own derivation:
    :func:`validate_plan` judged against a mention
    refuses a plan whose kind, target, road,
    action or pulls disagree with the plan that
    mention derives.
    """

    kind: str
    target: str
    road: str
    action: str
    pulls: str
    mention_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.mention_id is not None:
            object.__setattr__(
                self, "mention_id",
                normalize_member_id(self.mention_id))
        kind = normalize_kind(self.kind)
        object.__setattr__(self, "kind", kind)
        object.__setattr__(
            self, "target", _check_target(kind, self.target))
        object.__setattr__(
            self, "road",
            _check_long_text(self.road, "a plan's road"))
        object.__setattr__(
            self, "action",
            _check_long_text(self.action, "a plan's action"))
        object.__setattr__(
            self, "pulls",
            _check_long_text(self.pulls, "a plan's pulls"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "mentions_plan",
            "slice": MENTIONS_SLICE,
            "mention_id": self.mention_id,
            "kind": self.kind,
            "target": self.target,
            "road": self.road,
            "action": self.action,
            "pulls": self.pulls,
        }


def derive_plan(mention: Any) -> MentionPlan:
    """Derive one mention's resolution plan.

    The plan's road, action and pulls are the
    kind's own shipped road words, read off the
    mention alone - the plan names the road that
    WOULD pull the mention; deriving it runs
    nothing.
    """
    current = _check_mention_ref(mention)
    return MentionPlan(
        kind=current.kind, target=current.target,
        road=MENTION_ROADS[current.kind],
        action=_KIND_ACTIONS[current.kind],
        pulls=_KIND_PULLS[current.kind],
        mention_id=current.mention_id)


def _check_plan_ref(value: Any) -> MentionPlan:
    if isinstance(value, MentionPlan):
        return value
    if isinstance(value, dict):
        unknown = set(value) - _PLAN_KEYS
        if unknown:
            raise ValueError(
                "unknown plan keys: %s" % ", ".join(sorted(unknown)))
        kind = _pick_any(value, ("kind",), "kinds")
        if kind is None:
            raise ValueError("a plan is missing its kind")
        target = _pick_any(value, ("target",), "targets")
        if target is None:
            raise ValueError("a plan is missing its target")
        road = _pick_any(value, ("road",), "roads")
        if road is None:
            raise ValueError("a plan is missing its road")
        action = _pick_any(value, ("action",), "actions")
        if action is None:
            raise ValueError("a plan is missing its action")
        pulls = _pick_any(value, ("pulls",), "pulls")
        if pulls is None:
            raise ValueError("a plan is missing what it pulls")
        kwargs: Dict[str, Any] = {
            "kind": kind, "target": target, "road": road,
            "action": action, "pulls": pulls}
        mention_id = _pick_any(value, ("mention_id", "id"), "mention ids")
        if mention_id is not None:
            kwargs["mention_id"] = mention_id
        return MentionPlan(**kwargs)
    raise ValueError(f"a plan is needed, got {value!r}")


def validate_plan(plan: Any, mention: Any = None) -> MentionPlan:
    """Validate one plan into a MentionPlan.

    Accepts a MentionPlan or a mapping naming a
    ``kind``, a ``target``, a ``road``, an
    ``action``, a ``pulls`` and an optional
    ``mention_id`` (or ``id``). With *mention*
    given, the plan is judged against the plan
    derived from that mention: a stored plan
    whose kind, target, road, action, pulls or
    mention id disagree with the derived plan
    refuses.
    """
    current = _check_plan_ref(plan)
    if mention is not None:
        derived = derive_plan(mention)
        if current != derived:
            raise ValueError(
                "a stored plan disagrees with the plan "
                "derived from its mention")
    return current


def build_plan(plan: Any = None, mention: Any = None,
               **kwargs: Any) -> MentionPlan:
    """Build one validated plan, from a mapping or field words."""
    if isinstance(plan, MentionPlan) and not kwargs:
        return validate_plan(plan, mention)
    if isinstance(plan, dict) or plan is None:
        merged: Dict[str, Any] = {}
        if isinstance(plan, dict):
            merged.update(plan)
        merged.update(kwargs)
        return validate_plan(merged, mention)
    return validate_plan(plan, mention)


# ---------------------------------------------------------------------
# The index: the whole canon accounted for, derived.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class MentionKindCount:
    """One kind's count in an index: its mentions tallied."""

    kind: str
    mentions: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", normalize_kind(self.kind))
        object.__setattr__(
            self, "mentions",
            _check_count(self.mentions, "a kind count's mentions"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "mentions": self.mentions,
        }


def _check_kind_count_ref(value: Any) -> MentionKindCount:
    if isinstance(value, MentionKindCount):
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
        mentions = _pick_any(value, ("mentions", "count"), "counts")
        if mentions is None:
            raise ValueError("a kind count is missing its mentions")
        return MentionKindCount(kind=kind, mentions=mentions)
    raise ValueError(f"a kind count is needed, got {value!r}")


def _index_account(rows: Tuple[MentionPlan, ...],
                   kind_counts: Tuple[MentionKindCount, ...]
                   ) -> Tuple[str, ...]:
    if kind_counts:
        by_kind = ", ".join(
            f"{row.kind} {row.mentions}" for row in kind_counts)
        first = f"The canon holds {len(rows)} mention(s): {by_kind}."
    else:
        first = "The canon holds 0 mention(s)."
    return (
        first,
        "Every mention names the shipped road that "
        "would pull it into context; parsing and "
        "planning pull nothing in by themselves.",
        "The index is read off the held mentions at "
        "call time - it is derived, never stored "
        "loose.",
    )


@dataclass(frozen=True)
class MentionIndex:
    """The mention index, derived from the whole canon.

    ``rows`` are the mentions' plans, in held
    order; ``total_mentions`` is the mention
    count; ``kind_counts`` are the per-kind
    tallies in the order the kinds first appear
    among the mentions; ``account`` is read off
    those numbers. An index whose totals are not
    its own rows' counts refuses at construction;
    :func:`validate_index` judged against mentions
    refuses a stored index that disagrees with
    the derived one.
    """

    rows: Tuple[MentionPlan, ...] = ()
    total_mentions: int = 0
    kind_counts: Tuple[MentionKindCount, ...] = ()
    account: Tuple[str, ...] = ()
    index_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.index_id is not None:
            object.__setattr__(
                self, "index_id", normalize_member_id(self.index_id))
        if isinstance(self.rows, (str, bytes)) \
                or not isinstance(self.rows, (list, tuple)):
            raise ValueError(
                f"an index's rows must be a list of plans, "
                f"got {self.rows!r}")
        rows = tuple(_check_plan_ref(r) for r in self.rows)
        seen_ids = set()
        for row in rows:
            if row.mention_id is not None:
                if row.mention_id in seen_ids:
                    raise ValueError(
                        f"an index row named {row.mention_id!r} "
                        f"already exists")
                seen_ids.add(row.mention_id)
        object.__setattr__(self, "rows", rows)
        object.__setattr__(
            self, "total_mentions",
            _check_count(self.total_mentions, "an index's total"))
        if isinstance(self.kind_counts, (str, bytes)) \
                or not isinstance(self.kind_counts, (list, tuple)):
            raise ValueError(
                f"an index's kind counts must be a list, "
                f"got {self.kind_counts!r}")
        kind_counts = tuple(
            _check_kind_count_ref(c) for c in self.kind_counts)
        seen_kinds = set()
        for count in kind_counts:
            if count.kind in seen_kinds:
                raise ValueError(
                    f"a kind count named {count.kind!r} already exists")
            seen_kinds.add(count.kind)
        object.__setattr__(self, "kind_counts", kind_counts)
        if self.total_mentions != len(rows):
            raise ValueError(
                "an index's total must be its own rows' count")
        if sum(c.mentions for c in kind_counts) != self.total_mentions:
            raise ValueError(
                "an index's kind counts must sum to its own total")
        object.__setattr__(self, "account", _check_account(self.account))

    def row_for(self, mention_id: Any) -> MentionPlan:
        """The plan row one mention id names in this index."""
        wanted = normalize_member_id(mention_id)
        for row in self.rows:
            if row.mention_id == wanted:
                return row
        raise KeyError(f"no row in the index: mention {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "mentions_index",
            "slice": MENTIONS_SLICE,
            "index_id": self.index_id,
            "rows": [row.to_record() for row in self.rows],
            "total_mentions": self.total_mentions,
            "kind_counts": [c.to_record() for c in self.kind_counts],
            "account": list(self.account),
        }


def derive_index(source: Any) -> MentionIndex:
    """Derive the index from mentions.

    The rows are the mentions' plans, in held
    order, and the per-kind tallies are read off
    the mentions in the order their kinds first
    appear. *source* is a canon book, a registry
    or the mentions themselves. An empty source
    refuses - an index of nothing is no index.
    """
    entries = _held_mentions(source)
    if not entries:
        raise ValueError("an index needs at least one mention")
    rows = tuple(derive_plan(entry) for entry in entries)
    order: list = []
    tally: Dict[str, int] = {}
    for entry in entries:
        if entry.kind not in tally:
            tally[entry.kind] = 0
            order.append(entry.kind)
        tally[entry.kind] += 1
    kind_counts = tuple(
        MentionKindCount(kind=kind, mentions=tally[kind])
        for kind in order)
    return MentionIndex(
        rows=rows,
        total_mentions=len(entries),
        kind_counts=kind_counts,
        account=_index_account(rows, kind_counts))


def validate_index(index: Any, source: Any = None) -> MentionIndex:
    """Validate one index into a MentionIndex.

    Accepts a MentionIndex or a mapping naming
    ``rows`` (or ``plans``), a ``total_mentions``
    (or ``total``), ``kind_counts`` (or
    ``kinds``), an ``account`` (or ``statements``)
    and an optional ``index_id`` (or ``id``). With
    *source* given (mentions), the index is judged
    against the index derived from those mentions:
    a stored index whose rows, totals, kind counts
    or account disagree with the derived index
    refuses. An index naming no account refuses
    too.
    """
    if isinstance(index, MentionIndex):
        current = index
    elif isinstance(index, dict):
        unknown = set(index) - _INDEX_KEYS
        if unknown:
            raise ValueError(
                "unknown index keys: %s" % ", ".join(sorted(unknown)))
        rows = _pick_any(index, ("rows", "plans"), "rows")
        if rows is None:
            raise ValueError("an index is missing its rows")
        total = _pick_any(
            index, ("total_mentions", "total"), "totals")
        if total is None:
            raise ValueError("an index is missing its total mentions")
        kind_counts = _pick_any(
            index, ("kind_counts", "kinds"), "kind counts")
        if kind_counts is None:
            raise ValueError("an index is missing its kind counts")
        account = _pick_any(index, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError("an index names no account of its own")
        kwargs: Dict[str, Any] = {
            "rows": rows, "total_mentions": total,
            "kind_counts": kind_counts, "account": account}
        index_id = _pick_any(index, ("index_id", "id"), "index ids")
        if index_id is not None:
            kwargs["index_id"] = index_id
        current = MentionIndex(**kwargs)
    else:
        raise ValueError(f"an index must be a mapping, got {index!r}")
    if source is not None:
        derived = derive_index(source)
        if (current.rows != derived.rows
                or current.total_mentions != derived.total_mentions
                or current.kind_counts != derived.kind_counts
                or current.account != derived.account):
            raise ValueError(
                "a stored index disagrees with the index "
                "derived from its mentions")
    return current


def build_index(index: Any = None, source: Any = None,
                **kwargs: Any) -> MentionIndex:
    """Build one validated index, from a mapping or field words."""
    if isinstance(index, MentionIndex) and not kwargs:
        return validate_index(index, source)
    if isinstance(index, dict) or index is None:
        merged: Dict[str, Any] = {}
        if isinstance(index, dict):
            merged.update(index)
        merged.update(kwargs)
        return validate_index(merged, source)
    return validate_index(index, source)


# ---------------------------------------------------------------------
# The canon book: mentions in held order, derivations judged.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class MentionCanon:
    """One mention canon book: its mentions, in held order.

    ``mentions`` are the mention records, in held
    order; ``plans`` and ``indexes`` are the
    canon's derivations - a plan per mention and
    an index of the book, judged against the
    book's records by :func:`validate_book`;
    ``canon_note`` is the book's own note. This
    book is the canon file's shape: the shipped
    example is one book, and a real canon file is
    a new file in this shape.
    """

    title: str = ""
    mentions: Tuple[Mention, ...] = ()
    plans: Tuple[MentionPlan, ...] = ()
    indexes: Tuple[MentionIndex, ...] = ()
    canon_note: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a canon's title"))
        if isinstance(self.mentions, (str, bytes)) \
                or not isinstance(self.mentions, (list, tuple)):
            raise ValueError(
                f"a canon's mentions must be a list of mention "
                f"records, got {self.mentions!r}")
        mentions = tuple(_check_mention_ref(e) for e in self.mentions)
        if not mentions:
            raise ValueError(
                "a mention canon holds at least one mention")
        seen_ids = set()
        for entry in mentions:
            if entry.mention_id is not None:
                if entry.mention_id in seen_ids:
                    raise ValueError(
                        f"a mention named {entry.mention_id!r} "
                        f"already exists")
                seen_ids.add(entry.mention_id)
        object.__setattr__(self, "mentions", mentions)
        if isinstance(self.plans, (str, bytes)) \
                or not isinstance(self.plans, (list, tuple)):
            raise ValueError(
                f"a canon's plans must be a list of plans, "
                f"got {self.plans!r}")
        plans = tuple(
            p if isinstance(p, MentionPlan) else _check_plan_ref(p)
            for p in self.plans)
        seen_plans = set()
        for plan in plans:
            if plan.mention_id is not None:
                if plan.mention_id in seen_plans:
                    raise ValueError(
                        f"a plan named {plan.mention_id!r} "
                        f"already exists")
                seen_plans.add(plan.mention_id)
        object.__setattr__(self, "plans", plans)
        if isinstance(self.indexes, (str, bytes)) \
                or not isinstance(self.indexes, (list, tuple)):
            raise ValueError(
                f"a canon's indexes must be a list of indexes, "
                f"got {self.indexes!r}")
        indexes = tuple(
            i if isinstance(i, MentionIndex) else validate_index(i)
            for i in self.indexes)
        seen_indexes = set()
        for index in indexes:
            if index.index_id is not None:
                if index.index_id in seen_indexes:
                    raise ValueError(
                        f"an index named {index.index_id!r} "
                        f"already exists")
                seen_indexes.add(index.index_id)
        object.__setattr__(self, "indexes", indexes)
        if not isinstance(self.canon_note, str):
            raise ValueError("a canon's note must be text")
        object.__setattr__(
            self, "canon_note", self.canon_note.strip())

    def mention_for(self, mention_id: Any) -> Mention:
        """The mention one id names in this canon."""
        wanted = normalize_member_id(mention_id)
        for entry in self.mentions:
            if entry.mention_id == wanted:
                return entry
        raise KeyError(f"no mention in the canon: {wanted!r}")

    def mentions_for_kind(self, kind: Any) -> Tuple[Mention, ...]:
        """Every mention of one kind, in held order."""
        wanted = normalize_kind(kind)
        return tuple(e for e in self.mentions if e.kind == wanted)

    def plan_for(self, mention_id: Any) -> MentionPlan:
        """The derived plan of the mention one id names."""
        return derive_plan(self.mention_for(mention_id))

    def index_for(self, index_id: Any) -> MentionIndex:
        """The derived index one id names in this canon book."""
        wanted = normalize_member_id(index_id)
        for index in self.indexes:
            if index.index_id == wanted:
                return index
        raise KeyError(f"no index in the canon book: {wanted!r}")

    def mention_ids(self) -> Tuple[str, ...]:
        """Every held mention id, in held order."""
        return tuple(e.mention_id for e in self.mentions if e.mention_id)

    def kinds(self) -> Tuple[str, ...]:
        """Every held mention's kind, in held order."""
        return tuple(e.kind for e in self.mentions)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "mentions_book",
            "slice": MENTIONS_SLICE,
            "title": self.title,
            "mention_ids": list(self.mention_ids()),
            "mention_count": len(self.mentions),
            "plan_count": len(self.plans),
            "index_count": len(self.indexes),
        }


def validate_book(data: Any, *, require_example: bool = False) -> MentionCanon:
    """Validate one mentions mapping into a MentionCanon.

    The mapping names a ``schema`` (the mentions
    schema word), a ``guide`` mapping (its
    ``title``), an ``entries`` list (or
    ``mentions``) and optional ``plans`` and
    ``indexes`` lists. Every record stands on its
    own validation, then the whole is judged:
    mention ids unique, every stored plan judged
    against its mention, and every stored index
    judged against the book's own mentions. With
    ``require_example`` the shipped example is
    held to its pinned shape: the pinned title,
    records and kinds, and the index's pinned
    account word-for-word. Problems raise
    :class:`ValidationError` or ``ValueError``.
    """
    if isinstance(data, MentionCanon):
        return data
    if not isinstance(data, dict):
        raise ValidationError(
            f"a mention canon must be a mapping, got {data!r}")
    unknown = set(data) - _MENTIONS_KEYS
    if unknown:
        raise ValidationError(
            "unknown mentions keys: %s" % ", ".join(sorted(unknown)))
    if data.get("schema") != MENTIONS_SCHEMA:
        raise ValidationError(
            f"a mention canon must carry schema "
            f"{MENTIONS_SCHEMA!r}, got {data.get('schema')!r}")
    entries = _pick_any(data, ("entries", "mentions"), "entries")
    if entries is None:
        raise ValidationError("a mention canon is missing its entries")
    if not isinstance(entries, (list, tuple)):
        raise ValidationError("a mention canon's entries must be a list")
    if data.get("plans") is not None \
            and not isinstance(data["plans"], (list, tuple)):
        raise ValidationError("a mention canon's plans must be a list")
    if data.get("indexes") is not None \
            and not isinstance(data["indexes"], (list, tuple)):
        raise ValidationError("a mention canon's indexes must be a list")
    head = data.get("guide") or {}
    if not isinstance(head, dict):
        raise ValidationError("a mention canon's guide must be a mapping")
    unknown_head = set(head) - _BOOK_KEYS
    if unknown_head:
        raise ValidationError(
            "unknown guide keys: %s" % ", ".join(sorted(unknown_head)))
    try:
        title = _pick_any(head, ("title", "name"), "titles")
        if title is None:
            raise ValidationError("a mention canon is missing its title")
        note = data.get("canon_note") or ""
        if not isinstance(note, str):
            raise ValidationError("a mention canon's note must be text")
        book = MentionCanon(
            title=title, mentions=tuple(entries),
            plans=tuple(data.get("plans") or ()),
            indexes=tuple(data.get("indexes") or ()),
            canon_note=note)
        by_id = {e.mention_id: e for e in book.mentions}
        for plan in book.plans:
            if plan.mention_id is None \
                    or plan.mention_id not in by_id:
                raise ValidationError(
                    "a stored plan names no held mention")
            validate_plan(plan, by_id[plan.mention_id])
        for index in book.indexes:
            validate_index(index, book)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    if require_example:
        if book.title != _EXAMPLE_TITLE:
            raise ValidationError(
                "the shipped example mention canon's title "
                "is not the pinned title")
        if book.mention_ids() != _EXAMPLE_MENTION_IDS:
            raise ValidationError(
                "the shipped example's mentions are not "
                "the pinned records")
        if book.kinds() != _EXAMPLE_KINDS:
            raise ValidationError(
                "the shipped example's kinds are not the pinned kinds")
        if [p.mention_id for p in book.plans] != list(_EXAMPLE_MENTION_IDS):
            raise ValidationError(
                "the shipped example's plans are not "
                "the pinned plans")
        index = book.index_for(_EXAMPLE_INDEX_ID)
        if tuple(r.mention_id for r in index.rows) != _EXAMPLE_MENTION_IDS:
            raise ValidationError(
                "the shipped example index does not name "
                "its pinned rows")
        if index.account != _EXAMPLE_INDEX_ACCOUNT:
            raise ValidationError(
                "the shipped example index does not carry "
                "its pinned account word-for-word")
        first = book.mentions[0]
        if first.kind != "file" \
                or first.target != "mythic_agent/core/context_budget.py":
            raise ValidationError(
                "the shipped example's first mention is not "
                "its pinned file mention")
    return book


def build_canon(canon: Any = None, **kwargs: Any) -> MentionCanon:
    """Build one validated canon book, from a mapping or field words."""
    if isinstance(canon, MentionCanon) and not kwargs:
        return canon
    if isinstance(canon, dict):
        if "schema" in canon:
            return validate_book(canon)
        merged: Dict[str, Any] = dict(canon)
        merged.update(kwargs)
        return MentionCanon(**merged)
    if canon is None:
        return MentionCanon(**kwargs)
    raise ValueError(f"a mention canon is needed, got {canon!r}")


def _book_from(data: Any, *, require_example: bool) -> MentionCanon:
    try:
        return validate_book(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_mentions(
        data: Optional[Dict[str, Any]] = None) -> MentionCanon:
    """Load and validate the shipped example canon (or *data*).

    The shipped file is held to the example check:
    the pinned title, mention records, plans and
    index - the M-147 slice boundary canon, one
    mention of every kind the roadmap names - so
    the shipped canon covers the grammar this
    slice exists to hold.
    """
    raw = data if data is not None else load_resource(MENTIONS_RESOURCE)
    return _book_from(raw, require_example=True)


def load_mentions_file(path: Any) -> MentionCanon:
    """Load and validate a mention canon from a file at *path*.

    Any file in the mentions shape, anywhere on
    disk, validated whole - a malformed file
    raises :class:`ValidationError` naming the
    problem, and a missing file raises
    ``FileNotFoundError``. The example check is
    not held: a real canon stands on its own
    records.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _book_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The registry model: one canon held mention by mention, in held order.
# ---------------------------------------------------------------------


class MentionRegistry:
    """One session's mention canon, held mention by mention.

    The registry holds mention records, never
    plans or indexes: both are derivations, read
    off held mentions at call time, so nothing
    here can hold a figure stale.
    """

    def __init__(self, book: Any = None) -> None:
        self._title: Optional[str] = None
        self._entries: Dict[str, Mention] = {}
        self._order: list = []
        self._next_entry = 1
        if book is not None:
            self.register_canon(book)

    def _fresh_mention_id(self, held_ids: Any) -> str:
        while f"mention-{self._next_entry}" in held_ids:
            self._next_entry += 1
        fresh = f"mention-{self._next_entry}"
        self._next_entry += 1
        return fresh

    def register_mention(self, mention: Any) -> Mention:
        """Register one mention into the held canon.

        A record with no id is given a deterministic
        ``mention-N`` id. A record id already
        standing here refuses, as does a mention
        whose kind and target already stand here -
        one pull is named once.
        """
        validated = build_mention(mention)
        held_ids = set(self._entries)
        if validated.mention_id is not None \
                and validated.mention_id in held_ids:
            raise ValueError(
                f"a mention named "
                f"{validated.mention_id!r} already exists")
        for held in self._entries.values():
            if (held.kind, held.target) == (validated.kind, validated.target):
                raise ValueError(
                    f"a mention of {validated.kind} "
                    f"{validated.target!r} already exists")
        if validated.mention_id is None:
            validated = replace(
                validated,
                mention_id=self._fresh_mention_id(held_ids))
        self._entries[validated.mention_id] = validated
        self._order.append(validated.mention_id)
        return validated

    def register_canon(self, canon: Any) -> MentionCanon:
        """Register every mention of one canon book, in order.

        The first canon held sets the title; a
        later canon under a different title refuses,
        as does a canon naming a held mention id or
        a held kind-and-target. The canon's plans
        and indexes are derivations, not holdings,
        and are not held.
        """
        validated = build_canon(canon)
        if self._title is not None and validated.title != self._title:
            raise ValueError(
                "this registry already holds a mention "
                "canon under a different title")
        for entry in validated.mentions:
            if entry.mention_id in self._entries:
                raise ValueError(
                    f"a mention named "
                    f"{entry.mention_id!r} already exists")
        self._title = validated.title
        for entry in validated.mentions:
            self.register_mention(entry)
        return self.canon()

    def get_mention(self, mention_id: Any) -> Mention:
        """The mention one id names among the held records."""
        wanted = normalize_member_id(mention_id)
        if wanted not in self._entries:
            raise KeyError(f"unknown mention: {wanted!r}")
        return self._entries[wanted]

    def list_mentions(self) -> Tuple[Mention, ...]:
        """Every held mention, in the order they were held."""
        return tuple(self._entries[e] for e in self._order)

    def canon(self) -> MentionCanon:
        """The held mentions as one validated canon book."""
        if self._title is None:
            raise ValueError("no mention canon is held yet")
        return MentionCanon(
            title=self._title, mentions=self.list_mentions())

    def plan_for(self, mention_id: Any) -> MentionPlan:
        """Derive the plan of one held mention, at call time."""
        return derive_plan(self.get_mention(mention_id))

    def index(self) -> MentionIndex:
        """Derive the index of the held mentions, at call time."""
        return derive_index(self)


# ---------------------------------------------------------------------
# Mention news, shaped as session records.
# ---------------------------------------------------------------------


def mention_record(mention: Any) -> Dict[str, Any]:
    """The session-news record of one mention."""
    current = mention if isinstance(mention, Mention) \
        else build_mention(mention)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.raw} pulls {current.kind} "
        f"{current.target} into context: "
        f"{current.reason}")
    return record


def plan_record(plan: Any, mention: Any = None) -> Dict[str, Any]:
    """The session-news record of one resolution plan.

    With *mention* given, the plan is first judged
    against the plan that mention derives.
    """
    current = validate_plan(plan, mention)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Plan for @{current.kind}:{current.target}: "
        f"{current.action} via {current.road}.")
    return record


def index_record(index: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived index.

    With *source* given, the index is first judged
    against the mentions it belongs to.
    """
    current = validate_index(index, source)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Mention index: {current.total_mentions} "
        f"mention(s) named in the canon.")
    return record


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one mention canon book."""
    current = book if isinstance(book, MentionCanon) \
        else build_canon(book)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Mention canon {current.title}: "
        f"{record['mention_count']} mention(s) named.")
    return record


def plain_words(mention: Any) -> str:
    """One mention, in one plain sentence."""
    current = mention if isinstance(mention, Mention) \
        else build_mention(mention)
    return (
        f"{current.raw} - {current.kind} "
        f"{current.target} from {current.source}: "
        f"{current.reason}")


def plan_plain_words(plan: Any) -> str:
    """One resolution plan in plain words, in full.

    The plan is told whole - its road, its action
    and what it would pull.
    """
    current = validate_plan(plan)
    return (
        f"Plan for @{current.kind}:{current.target}: "
        f"{current.action} via {current.road}. "
        f"It would pull: {current.pulls}. "
        f"Planning names the road; it runs nothing.")


def index_plain_words(source: Any) -> str:
    """The index in plain words, in full.

    Accepts a MentionIndex or a MentionCanon.
    The index is told whole - its rows and its
    account.
    """
    if isinstance(source, MentionIndex):
        index = validate_index(source)
        title = None
    elif isinstance(source, MentionCanon):
        index = derive_index(source)
        title = source.title
    else:
        raise ValueError(f"a mentions source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("The @-mention canon:")
    for row in index.rows:
        lines.append(
            f"@{row.kind}:{row.target} - {row.action} "
            f"via {row.road}")
    lines.extend(index.account)
    return "\n".join(lines)


# ---------------------------------------------------------------------
# Screens: the formatters and the shared /mentions grammar.
# ---------------------------------------------------------------------


def _source_canon(source: Any) -> MentionCanon:
    if source is None:
        return load_mentions()
    if isinstance(source, MentionRegistry):
        return source.canon()
    if isinstance(source, MentionCanon):
        return source
    raise ValueError(f"a mention canon is needed, got {source!r}")


def format_mention(mention: Any) -> str:
    """One mention as a screen line."""
    current = mention if isinstance(mention, Mention) \
        else build_mention(mention)
    return (
        f"{current.mention_id or '-'}: {current.kind} - "
        f"{current.target} ({current.raw} "
        f"from {current.source})")


def format_mentions(source: Any = None, kind: Any = None) -> str:
    """Mentions of one canon, in held order.

    With *kind* given, only the mentions of that
    kind are shown.
    """
    book = _source_canon(source)
    entries = book.mentions
    if kind is not None:
        wanted = normalize_kind(kind)
        entries = tuple(e for e in entries if e.kind == wanted)
    lines = [format_mention(entry) for entry in entries]
    if not lines:
        lines.append("No mentions are held.")
    return "\n".join(lines)


def format_plan(plan: Any) -> str:
    """One resolution plan as a screen block."""
    current = validate_plan(plan)
    return (
        f"Plan for {current.mention_id or '-'}: "
        f"@{current.kind}:{current.target}\n"
        f"Road: {current.road}\n"
        f"Action: {current.action}\n"
        f"Would pull: {current.pulls}")


def format_index(source: Any = None) -> str:
    """The index as a screen block: every plan and the account.

    Accepts a MentionIndex or a MentionCanon; a
    canon book shows the index it derives.
    """
    if isinstance(source, MentionIndex):
        index = validate_index(source)
        lines: list = []
    else:
        book = _source_canon(source)
        index = derive_index(book)
        lines = [f"Index in {book.title}:"]
    lines.append("The @-mention canon:")
    for row in index.rows:
        lines.append(
            f"{row.mention_id or '-'}: @{row.kind}:{row.target} "
            f"- {row.action} via {row.road}")
    lines.extend(index.account)
    return "\n".join(lines)


def format_mentions_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /mentions.

    With nothing named, the shipped example
    mention canon is shown - the example this
    slice ships - so the screen is never empty.
    """
    book = _source_canon(source)
    lines = ["The @-mention canon (M-148) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_mentions(book))
    lines.append("")
    lines.append(format_index(book))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_mentions_args(args: Any) -> Tuple[str, Any]:
    """Parse the /mentions grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    mention canon; ``mention <mention-id>`` shows
    one mention; ``kind <kind>`` shows the
    mentions of one kind; ``plan <mention-id>``
    shows one mention's derived plan; ``parse
    <text...>`` parses mentions out of text;
    ``index`` shows the index derived from the
    whole canon. Anything else is a usage error
    naming the grammar. Returns
    ``(action, value-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() in ("show", "list"):
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head == "index" and len(words) == 1:
        return (head, None)
    if head == "mention" and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "plan" and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "kind" and len(words) == 2:
        try:
            return (head, normalize_kind(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "parse" and len(words) >= 2:
        return (head, text.split(None, 1)[1])
    raise ValueError(USAGE)
