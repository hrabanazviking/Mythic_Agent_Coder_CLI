"""The slash-command palace (All-Features roadmap slice M-176).

Part VIII - The Beautiful Face - builds here. The
roadmap's words: *every command discoverable from
`/` with plain-language descriptions and examples;
custom commands (Part X skills) join the same
palace.*

What already ships, and what this slice adds:

* The shipped tree holds its slash commands
  spelled once per surface - the command handler's
  dispatch, the terminal's own roads and the chat
  screen's routing - with their words living in
  help lines and usage strings on each surface
  alone. Nothing holds one command as data beside
  the others: there is no one room a user can walk
  from `/` and find every command in, each with a
  plain-language description and an example of its
  use, and a custom command of Part X (M-237, the
  user and project slash commands still to come)
  has no standing place beside the shipped ones at
  all.
* The M-171 TUI redesign charter judged the
  subagent picker modal (its S-06 row) KEEP and
  names M-176, beside M-175, among its owning
  slices: *keep the card; when the fuzzy picker
  gives every choice one grammar, this list joins
  it; the auto-dismiss on change is re-judged
  there, and the heading takes plain words first*
  - its K-01 judgement strains because the heading
  speaks in costume where plain words would land
  first, and its K-09 judgement strains because
  the dropdown dismisses the dialog the moment a
  value changes, so a browsing keystroke can
  commit a choice the user was only looking at.
* This slice is that one room, as a pure layer:
  one palace entry validated as data WITH ITS
  PROVENANCE WHOLE - its kind in the closed kind
  set (shipped, custom: the commands the app ships
  itself, and the custom commands of Part X
  joining them on the same terms), its command in
  the shape the surfaces speak, its plain-language
  description, one example of its use and its
  tags. A custom command is first held as its own
  record, judged whole - its command, its plain
  words, its example, the prompt template it would
  speak and the arguments it takes, and whether it
  lives with the user or with a project - and
  joins the palace as an entry of the custom kind,
  on exactly the same terms as a shipped one; Part
  X itself is not built here, and the template is
  held as data, never rendered or run. A browse is
  held as its own record - the words typed after
  `/`, its kind filter in the closed filter set,
  its own words and its provenance whole. The
  panel is DERIVED for one held browse (its rows
  the shown entries in derived order, carrying
  their derived scores and lines, its totals the
  entries' own counts), and a verdict is DERIVED
  for the whole book under one browse. The typed
  words are read into tokens BY IMPORT through the
  shipped M-175 picker's one token road, and
  entries are composed BY IMPORT from the shipped
  rooms the palace ranges over - a slash command
  judged by the command shape the surfaces speak,
  a command candidate of the shipped M-175 picker
  judged whole by its own judge, a custom command
  record judged whole by this layer. The shipped
  data file (``mythic_agent/data/command_palace.yaml``)
  holds one example book in exactly the shape a
  real palace file takes, a loader reads a palace
  file anywhere on disk, entries and browses are
  shaped as session news, and a small in-memory
  registry model holds entries and browses one by
  one. The agent layer owns holding entries for a
  session and standing a browse on them.

Honesty rules, enforced here and pinned by tests:

* **One palace, both kinds.** Shipped and custom
  entries stand in one book under one closed kind
  set and are judged by the same roads: a custom
  command joins on the same terms as a shipped
  one, and a kind filter only narrows which
  entries stand in a browse, never how they are
  judged.
* **The match is derived, never stored.** An
  entry carries no score and no rank: a mapping
  naming one refuses. A score exists only as the
  derivation of one browse over one entry, read
  off the typed tokens - parsed by the M-175
  picker's one token road, imported - against the
  entry's own command, tags, description and
  example, and a panel row is judged against that
  derivation: a stored row whose score disagrees
  with its browse refuses.
* **Plain words first, and browsing commits
  nothing and runs nothing.** The palace's own
  words are plain (the S-06 heading's lesson), and
  a browse only ever LOOKS: standing a browse
  holds the browse as data and derives its panel -
  it runs no command it shows, renders no custom
  command's template, opens no skill and changes
  no session. The S-06 auto-dismiss is re-judged
  here in the palace's own shape: browsing commits
  no choice at all, so there is nothing a browsing
  keystroke can commit by accident - this slice is
  a discoverability layer, a catalogue, and
  nothing is executed by browsing the palace.
* **Data only.** This layer holds entries and
  browses as data: it executes nothing, renders no
  live UI, sends nothing, posts nothing, schedules
  nothing, calls no model and persists nothing -
  an entry held here is a finding, never the act
  of running the command found.
"""

from __future__ import annotations

__all__ = [
    "COMMAND_PALACE_RESOURCE",
    "COMMAND_PALACE_SCHEMA",
    "COMMAND_PALACE_SLICE",
    "ENTRY_KINDS",
    "KIND_FILTERS",
    "PLAIN_EXPLANATION",
    "THE_COMMAND_PALACE_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "Any",
    "CommandPalaceBook",
    "CommandPalaceRegistry",
    "CustomCommand",
    "Dict",
    "List",
    "Optional",
    "PalaceBrowse",
    "PalaceEntry",
    "PalaceKindCount",
    "PalacePanel",
    "PalacePanelRow",
    "PalaceVerdict",
    "Tuple",
    "book_record",
    "browse_plain_words",
    "browse_record",
    "build_book",
    "build_browse",
    "build_custom_command",
    "build_entry",
    "build_panel",
    "build_row",
    "build_verdict",
    "custom_command_record",
    "derive_panel",
    "derive_verdict",
    "entries_with_kind",
    "entry_from_custom_command",
    "entry_from_picker_candidate",
    "entry_from_shipped_command",
    "entry_record",
    "format_book",
    "format_browse",
    "format_command_palace_screen",
    "format_entry",
    "format_panel",
    "format_verdict",
    "inspect_entry_source",
    "line_of",
    "load_command_palace",
    "load_command_palace_file",
    "normalize_kind",
    "normalize_kind_filter",
    "panel_plain_words",
    "panel_record",
    "parse_command_palace_args",
    "plain_words",
    "rank_entries",
    "score_of",
    "total_entries",
    "validate_book",
    "validate_browse",
    "validate_custom_command",
    "validate_entry",
    "validate_panel",
    "validate_row",
    "validate_verdict",
    "verdict_plain_words",
    "verdict_record",
]

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .crew_members import normalize_member_id
from .fuzzy_picker import parse_query
from .validation import ValidationError

COMMAND_PALACE_SLICE = "M-176"

#: The longer name other layers cite for this slice.
THE_COMMAND_PALACE_SLICE = COMMAND_PALACE_SLICE

COMMAND_PALACE_RESOURCE = "command_palace.yaml"

COMMAND_PALACE_SCHEMA = "mythic.command_palace/1"

#: The kinds one entry may stand under, in the
#: roadmap's own order: the commands the app ships
#: itself first, then the custom commands (Part X
#: skills) joining the same palace.
ENTRY_KINDS = ("shipped", "custom")

_KIND_ALIASES = {
    "shipped": "shipped", "builtin": "shipped",
    "built-in": "shipped", "native": "shipped",
    "custom": "custom", "customs": "custom",
    "skill": "custom", "skills": "custom",
}

#: The kind filters one browse may carry, in
#: order: every kind at once, then each kind of
#: the closed set alone.
KIND_FILTERS = ("all",) + ENTRY_KINDS

_KIND_FILTER_ALIASES = {
    "all": "all", "every": "all", "everything": "all",
    "any": "all",
}
_KIND_FILTER_ALIASES.update(_KIND_ALIASES)

#: The homes one custom command may live in, in
#: the Part X order: with the user, or with one
#: project (the M-236 skills standard's own two
#: standings).
CUSTOM_HOMES = ("user", "project")

_HOME_ALIASES = {
    "user": "user", "personal": "user",
    "project": "project", "workspace": "project",
}

#: The words a whole book's verdict under one
#: browse may carry: spanning while the shown
#: entries stand in more than one kind, shelved
#: while they stand in one kind alone, empty while
#: no entry is shown.
VERDICT_WORDS = ("spanning", "shelved", "empty")

_ENTRY_KEYS = frozenset({
    "entry_id", "id", "kind", "type_of",
    "command", "name", "label",
    "description", "detail",
    "example", "usage",
    "tags", "keywords",
    "recorded_on", "day", "date",
    "actor", "by", "who", "source",
    "origin_session", "session"})

_CUSTOM_KEYS = frozenset({
    "custom_id", "id", "command", "name", "label",
    "description", "detail",
    "example", "usage",
    "template", "prompt", "prompt_template",
    "arguments", "args",
    "home", "standing",
    "recorded_on", "day", "date",
    "actor", "by", "who", "source",
    "origin_session", "session"})

_ROW_KEYS = frozenset({
    "entry_id", "id", "kind", "command",
    "score", "line", "recorded_on"})

_KIND_COUNT_KEYS = frozenset({"kind", "items", "count"})

_PANEL_KEYS = frozenset({
    "panel_id", "id", "browse_id", "browse",
    "query_text", "query", "kind_filter", "filter",
    "rows", "shown",
    "total_entries", "entries",
    "total_matched", "matched",
    "kind_counts", "kinds",
    "as_of", "day", "account", "statements"})

_BROWSE_KEYS = frozenset({
    "browse_id", "id", "seq", "sequence", "order",
    "text", "query", "query_text",
    "kind_filter", "filter", "kind",
    "detail", "reason",
    "recorded_on", "day", "date",
    "actor", "by", "who", "source",
    "origin_session", "session"})

_VERDICT_KEYS = frozenset({
    "total_entries", "entries",
    "total_matched", "matched",
    "distinct_kinds", "kinds",
    "earliest_on", "earliest", "latest_on", "latest",
    "verdict"})

_BOOK_KEYS = frozenset({"title", "name"})

_COMMAND_PALACE_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "canon_note", "guide", "entries", "browses",
    "panels"})

_EXAMPLE_TITLE = "Command Palace at the M-175 slice boundary"

_EXAMPLE_ENTRY_IDS = (
    "entry-help", "entry-model",
    "entry-approvalcards", "entry-sliceboard",
    "entry-fuzzypicker", "entry-compact",
    "entry-standup", "entry-verse")

_EXAMPLE_FIRST_ENTRY_ID = "entry-help"

_EXAMPLE_FIRST_ENTRY_COMMAND = "/help"

_EXAMPLE_PANEL_ID = "panel-m175-boundary"

_EXAMPLE_AS_OF = "2026-11-09"

_EXAMPLE_BROWSE_IDS = (
    "browse-session", "browse-picker")

PLAIN_EXPLANATION = (
    "The Slash-Command Palace: every command "
    "discoverable from / with a plain-language "
    "description and an example, and custom "
    "commands (Part X skills) standing in the same "
    "palace on the same terms. An entry is one "
    "command held as data - its kind (shipped or "
    "custom), its command in the shape the surfaces "
    "speak, its plain words, one example of its use "
    "and its tags, with its provenance whole. A "
    "browse is the words typed after /, read into "
    "tokens by the shipped M-175 picker's one token "
    "road, and an entry's score under a browse is "
    "derived from those tokens against the entry's "
    "own command, tags, description and example - "
    "never stored, never ranked by hand. A kind "
    "filter narrows which entries stand in a "
    "browse, never how they are judged. A custom "
    "command is first held as its own record, "
    "judged whole - its template held as data, "
    "never rendered or run - and joins the palace "
    "as an entry of the custom kind. This layer "
    "holds entries and browses as data only: it "
    "executes nothing, renders no live UI, sends "
    "nothing, posts nothing, schedules nothing, "
    "calls no model and persists nothing - an entry "
    "held here is a finding, never the act of "
    "running the command found, and browsing "
    "commits no choice at all."
)

USAGE = (
    "Usage: /commandpalace, /commandpalace show, "
    "/commandpalace entry <entry-id>, "
    "/commandpalace browse <browse-id>, "
    "/commandpalace visit <words>, "
    "/commandpalace kind <kind>, "
    "/commandpalace panel, /commandpalace verdict"
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


def _check_seq(value: Any) -> int:
    seq = _check_count(value, "a browse's sequence")
    if seq < 1:
        raise ValueError(
            f"a browse's sequence stands from 1, got {value!r}")
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
            f"an entry's tags must be a list of words, "
            f"got {value!r}")
    tags = tuple(_check_word(t, "a tag") for t in value)
    if not tags:
        raise ValueError(
            "an entry carries at least one tag: the "
            "tags are part of what a browse is judged "
            "against")
    if len(tags) > 8:
        raise ValueError(
            f"an entry carries at most 8 tags, "
            f"got {len(tags)}")
    if len({t.lower() for t in tags}) != len(tags):
        raise ValueError("an entry names one tag twice")
    return tags


def _check_arguments(value: Any) -> Tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"a custom command's arguments must be a "
            f"list of words, got {value!r}")
    arguments = tuple(
        _check_word(a, "an argument") for a in value)
    if len(arguments) > 8:
        raise ValueError(
            f"a custom command takes at most 8 "
            f"arguments, got {len(arguments)}")
    if len({a.lower() for a in arguments}) != len(arguments):
        raise ValueError("a custom command names one argument twice")
    return arguments


def _check_command(value: Any, what: str = "a command") -> str:
    """One slash command, in the shape the surfaces speak.

    One word opening with a slash, in the surfaces'
    own spelling - the same shape the shipped
    M-175 picker judges a command candidate by.
    """
    if not isinstance(value, str) or not value.startswith("/"):
        raise ValueError(
            f"a slash command opens with a slash, got {value!r}")
    _check_word(value[1:], "a command name")
    if value != value.lower() or " " in value:
        raise ValueError(
            f"a slash command is one lowercase word, got {value!r}")
    return value


def normalize_kind(value: Any) -> str:
    """One kind word, read onto the closed kind set."""
    if not isinstance(value, str):
        raise ValueError(f"a kind must be a word, got {value!r}")
    kind = _KIND_ALIASES.get(value.strip().lower())
    if kind is None:
        raise ValueError(
            "a kind is one of %s, got %r"
            % ("/".join(ENTRY_KINDS), value))
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


def normalize_home(value: Any) -> str:
    """One home word, read onto the closed home set."""
    if not isinstance(value, str):
        raise ValueError(f"a home must be a word, got {value!r}")
    home = _HOME_ALIASES.get(value.strip().lower())
    if home is None:
        raise ValueError(
            "a home is one of %s, got %r"
            % ("/".join(CUSTOM_HOMES), value))
    return home


def _subsequence(token: str, name: str) -> bool:
    """True when *token*'s letters stand in *name* in order."""
    if not token:
        return False
    rest = iter(name)
    return all(any(ch == wanted for ch in rest) for wanted in token)


def score_of(entry: Any, browse: Any) -> int:
    """The score one entry derives under one browse.

    Read off the browse's tokens - parsed by the
    shipped M-175 picker's one token road, imported
    - against the entry's own command, tags,
    description and example, the same reading for
    both kinds: an exact command name weighs most,
    a name the token opens weighs next, a name
    holding the token next, a name the token's
    letters thread in order least; a tag named
    whole outweighs a tag the token stands inside;
    the description and the example add their small
    shares. A browse naming the command whole adds
    the exact-phrase weight. An entry outside the
    browse's kind filter derives no score at all.
    The score is derived at call time - it is never
    a field of the entry.
    """
    current = _check_entry_ref(entry)
    if isinstance(browse, PalaceBrowse):
        text, kind_filter = browse.text, browse.kind_filter
    elif isinstance(browse, dict):
        text = _pick_any(
            browse, ("text", "query", "query_text"), "browse text")
        if text is None:
            raise ValueError("a browse names no browse text")
        named = _pick_any(
            browse, ("kind_filter", "filter", "kind"), "kind filter")
        kind_filter = (
            normalize_kind_filter(named) if named is not None else "all")
    else:
        text, kind_filter = browse, "all"
    if kind_filter != "all" and current.kind != kind_filter:
        return 0
    tokens = parse_query(text)
    name = current.command[1:].lower()
    description = current.description.lower()
    example = current.example.lower()
    tags = tuple(t.lower() for t in current.tags)
    score = 0
    for token in tokens:
        if token == name:
            score += 100
        elif name.startswith(token):
            score += 50
        elif token in name:
            score += 30
        elif _subsequence(token, name):
            score += 10
        if token in tags:
            score += 20
        elif any(token in tag for tag in tags):
            score += 10
        if token in description:
            score += 5
        if token in example:
            score += 5
    if " ".join(tokens) == name:
        score += 100
    return score


def line_of(entry: Any) -> str:
    """The entry line one palace entry derives.

    Read off the entry's command and kind alone:
    the command found, and the kind it stands
    under.
    """
    current = _check_entry_ref(entry)
    return f"{current.command} - {current.kind}"


# ---------------------------------------------------------------------
# The entry: one discoverable command, held whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class PalaceEntry:
    """One palace entry: one discoverable command, held whole.

    ``kind`` is the entry's kind in the closed kind
    set; ``command`` is the slash command itself, in
    the shape the surfaces speak; ``description`` is
    the entry's plain-language words for what the
    command does; ``example`` is one example of its
    use; ``tags`` are the entry's own words a browse
    may name. The entry carries NO score and NO
    rank - those are derived from a browse at call
    time, never fields. The provenance - the day it
    was recorded, who recorded it, its source and
    the session it was recorded in - rides whole.
    """

    entry_id: str
    kind: str
    command: str
    description: str
    example: str
    tags: Tuple[str, ...]
    recorded_on: str
    actor: str
    source: str
    origin_session: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "entry_id",
            _check_word(self.entry_id, "an entry id"))
        object.__setattr__(self, "kind", normalize_kind(self.kind))
        object.__setattr__(
            self, "command", _check_command(self.command))
        object.__setattr__(
            self, "description",
            _check_long_text(self.description, "the description"))
        object.__setattr__(
            self, "example",
            _check_long_text(self.example, "the example"))
        if not self.example.lstrip().startswith(self.command):
            raise ValueError(
                "an example shows its own command in use - "
                f"{self.example!r} does not open with "
                f"{self.command!r}")
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
        """The derived entry line of this entry."""
        return line_of(self)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "command_palace_entry",
            "slice": COMMAND_PALACE_SLICE,
            "entry_id": self.entry_id,
            "kind": self.kind,
            "command": self.command,
            "description": self.description,
            "example": self.example,
            "tags": list(self.tags),
            "line": self.line,
            "recorded_on": self.recorded_on,
            "actor": self.actor,
            "source": self.source,
            "origin_session": self.origin_session,
        }


def _check_entry_ref(value: Any) -> PalaceEntry:
    if isinstance(value, PalaceEntry):
        return value
    return validate_entry(value)


def validate_entry(entry: Any) -> PalaceEntry:
    """Judge one palace entry whole and return it.

    A mapping is read through its spellings: a
    derived key (``score``, ``rank`` or ``line``)
    refuses - those are derived, never stored - as
    does any key the entry does not carry, and two
    spellings naming two different values.
    """
    if isinstance(entry, PalaceEntry):
        return entry
    if not isinstance(entry, dict):
        raise ValueError(
            f"a palace entry must be a mapping, got {entry!r}")
    unknown = set(entry) - _ENTRY_KEYS
    if unknown:
        raise ValueError(
            f"a palace entry carries unknown keys: "
            f"{sorted(unknown)}")
    if "type" in entry:
        raise ValueError(
            "a palace entry is judged without its news keys")

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(entry, spellings, what)
        if value is None:
            raise ValueError(f"a palace entry names no {what}")
        return value

    return PalaceEntry(
        entry_id=_needed(("entry_id", "id"), "entry id"),
        kind=_needed(("kind", "type_of"), "kind"),
        command=_needed(("command", "name", "label"), "command"),
        description=_needed(
            ("description", "detail"), "plain-language description"),
        example=_needed(("example", "usage"), "example"),
        tags=_needed(("tags", "keywords"), "tags"),
        recorded_on=_needed(
            ("recorded_on", "day", "date"), "day it was recorded"),
        actor=_needed(("actor", "by", "who"), "actor"),
        source=_needed(("source",), "source"),
        origin_session=_needed(
            ("origin_session", "session"), "origin session"),
    )


def build_entry(entry: Any = None, **kwargs: Any) -> PalaceEntry:
    """Build one entry from a mapping, an entry, or fields."""
    if kwargs:
        if entry is not None:
            raise ValueError("an entry is built one way at a time")
        entry = kwargs
    return validate_entry(entry)


# ---------------------------------------------------------------------
# The custom command: a Part X command, held as its own record.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class CustomCommand:
    """One custom command (Part X), held as its own record.

    ``command`` is the slash command in the
    surfaces' shape; ``description`` is its plain
    words; ``example`` is one example of its use;
    ``template`` is the prompt template the command
    would speak - held as data, never rendered,
    never run (Part X itself is not built here);
    ``arguments`` are the words the command takes;
    ``home`` is where the command lives - with the
    user, or with one project. The provenance rides
    whole. A custom command joins the palace as an
    entry of the custom kind, on the same terms as
    a shipped one.
    """

    custom_id: str
    command: str
    description: str
    example: str
    template: str
    arguments: Tuple[str, ...]
    home: str
    recorded_on: str
    actor: str
    source: str
    origin_session: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "custom_id",
            _check_word(self.custom_id, "a custom command id"))
        object.__setattr__(
            self, "command", _check_command(self.command))
        object.__setattr__(
            self, "description",
            _check_long_text(self.description, "the description"))
        object.__setattr__(
            self, "example",
            _check_long_text(self.example, "the example"))
        if not self.example.lstrip().startswith(self.command):
            raise ValueError(
                "an example shows its own command in use - "
                f"{self.example!r} does not open with "
                f"{self.command!r}")
        object.__setattr__(
            self, "template",
            _check_long_text(self.template, "the prompt template"))
        object.__setattr__(
            self, "arguments", _check_arguments(self.arguments))
        object.__setattr__(self, "home", normalize_home(self.home))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))
        object.__setattr__(
            self, "actor", _check_title(self.actor, "an actor"))
        object.__setattr__(
            self, "source", _check_title(self.source, "a source"))
        object.__setattr__(
            self, "origin_session",
            _check_word(self.origin_session, "an origin session"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "command_palace_custom_command",
            "slice": COMMAND_PALACE_SLICE,
            "custom_id": self.custom_id,
            "command": self.command,
            "description": self.description,
            "example": self.example,
            "template": self.template,
            "arguments": list(self.arguments),
            "home": self.home,
            "recorded_on": self.recorded_on,
            "actor": self.actor,
            "source": self.source,
            "origin_session": self.origin_session,
        }


def validate_custom_command(custom: Any) -> CustomCommand:
    """Judge one custom command record whole and return it.

    The record is judged on its own terms, exactly
    as a shipped command's entry is judged on its
    terms: every field named, the template held as
    data, unknown keys refusing.
    """
    if isinstance(custom, CustomCommand):
        return custom
    if not isinstance(custom, dict):
        raise ValueError(
            f"a custom command must be a mapping, got {custom!r}")
    unknown = set(custom) - _CUSTOM_KEYS
    if unknown:
        raise ValueError(
            f"a custom command carries unknown keys: "
            f"{sorted(unknown)}")
    if "type" in custom:
        raise ValueError(
            "a custom command is judged without its news keys")

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(custom, spellings, what)
        if value is None:
            raise ValueError(f"a custom command names no {what}")
        return value

    return CustomCommand(
        custom_id=_needed(("custom_id", "id"), "custom command id"),
        command=_needed(("command", "name", "label"), "command"),
        description=_needed(
            ("description", "detail"), "plain-language description"),
        example=_needed(("example", "usage"), "example"),
        template=_needed(
            ("template", "prompt", "prompt_template"),
            "prompt template"),
        arguments=_pick_any(
            custom, ("arguments", "args"), "arguments") or (),
        home=_needed(("home", "standing"), "home"),
        recorded_on=_needed(
            ("recorded_on", "day", "date"), "day it was recorded"),
        actor=_needed(("actor", "by", "who"), "actor"),
        source=_needed(("source",), "source"),
        origin_session=_needed(
            ("origin_session", "session"), "origin session"),
    )


def build_custom_command(
        custom: Any = None, **kwargs: Any) -> CustomCommand:
    """Build one custom command from a mapping, a record, or fields."""
    if kwargs:
        if custom is not None:
            raise ValueError(
                "a custom command is built one way at a time")
        custom = kwargs
    return validate_custom_command(custom)


# ---------------------------------------------------------------------
# Composition: the shipped rooms, by import.
# ---------------------------------------------------------------------


def entry_from_shipped_command(
        command: Any = None, *,
        entry_id: Any, description: Any, example: Any,
        recorded_on: Any = "2026-11-09",
        actor: Any = "the coordinator",
        source: Any = "command palace",
        origin_session: Any = "session-m176",
        tags: Any = None) -> PalaceEntry:
    """Raise one shipped entry over a slash command.

    The command is judged by the shape the two chat
    surfaces speak: one word opening with a slash,
    in the surfaces' own spelling. The entry's
    description is the caller's plain words for what
    the command does, and its example shows the
    command in use.
    """
    held_command = _check_command(command)
    if tags is None:
        tags = ("command",)
    return PalaceEntry(
        entry_id=entry_id, kind="shipped",
        command=held_command, description=description,
        example=example,
        tags=tuple(tags),
        recorded_on=recorded_on, actor=actor,
        source=source, origin_session=origin_session)


def entry_from_picker_candidate(
        candidate: Any = None, *,
        entry_id: Any, example: Any,
        recorded_on: Any = "2026-11-09",
        actor: Any = "the coordinator",
        source: Any = "command palace",
        origin_session: Any = "session-m176",
        tags: Any = None) -> PalaceEntry:
    """Raise one shipped entry over a picker command candidate.

    The candidate is judged whole BY IMPORT by the
    shipped M-175 picker's own judge first: only a
    candidate of the picker's command kind stands
    here - the entry's command is the candidate's
    label, its description the candidate's own
    detail line, its tags the candidate's own tags
    unless the caller names others.
    """
    from .fuzzy_picker import validate_candidate
    if candidate is None:
        raise ValueError(
            "a picker candidate is needed to raise an entry")
    held = validate_candidate(candidate)
    if held.kind != "command":
        raise ValueError(
            "only a picker candidate of the command kind "
            f"joins the palace as a shipped entry, got "
            f"{held.kind!r}")
    if tags is None:
        tags = held.tags
    return PalaceEntry(
        entry_id=entry_id, kind="shipped",
        command=held.label, description=held.detail,
        example=example,
        tags=tuple(tags),
        recorded_on=recorded_on, actor=actor,
        source=source, origin_session=origin_session)


def entry_from_custom_command(
        custom: Any = None, *,
        entry_id: Any,
        recorded_on: Any = None,
        actor: Any = None,
        source: Any = None,
        origin_session: Any = None,
        tags: Any = None) -> PalaceEntry:
    """Raise one custom entry over a custom command record.

    The record is judged whole first, on its own
    terms: the entry's command, description and
    example are the record's own, its provenance
    the record's own unless the caller names it
    afresh. The record's template is NOT carried
    into the entry - the palace is a catalogue:
    the template stays on the custom command's own
    record, held as data, and is never rendered or
    run here.
    """
    if custom is None:
        raise ValueError(
            "a custom command record is needed to raise an entry")
    held = validate_custom_command(custom)
    if tags is None:
        tags = ("custom", "skill")
    return PalaceEntry(
        entry_id=entry_id, kind="custom",
        command=held.command, description=held.description,
        example=held.example,
        tags=tuple(tags),
        recorded_on=(
            recorded_on if recorded_on is not None
            else held.recorded_on),
        actor=actor if actor is not None else held.actor,
        source=source if source is not None else held.source,
        origin_session=(
            origin_session if origin_session is not None
            else held.origin_session))


def inspect_entry_source(piece: Any) -> Dict[str, Any]:
    """Judge one raw entry piece and name what it is.

    A piece shaped like an entry - a mapping
    carrying a ``kind`` and a ``command`` - is read
    onto its closed kind without holding an entry.
    Anything else is named not-an-entry.
    """
    if not isinstance(piece, dict):
        return {"kind": None,
                "reason": "not a mapping - no entry stands here"}
    kind_in = _pick_any(piece, ("kind", "type_of"), "kind")
    command = _pick_any(
        piece, ("command", "name", "label"), "command")
    if kind_in is None or command is None:
        return {"kind": None,
                "reason": "no kind or no command named - no entry "
                          "stands here"}
    try:
        kind = normalize_kind(kind_in)
    except ValueError as exc:
        return {"kind": None, "command": command, "reason": str(exc)}
    return {
        "kind": kind, "command": command,
        "reason": "an entry piece in the closed kind set"}


# ---------------------------------------------------------------------
# The browse record: the words typed after /, held whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class PalaceBrowse:
    """One browse, held as its own record.

    ``text`` is the words typed after `/`, parsed by
    the shipped M-175 picker's one token road at
    judgement time; ``kind_filter`` is the browse's
    filter in the closed filter set - it narrows
    which entries stand in the browse, never how
    they are judged; ``detail`` is the browse's own
    words. ``seq`` is the browse's place in the
    book's recorded order, from 1. The provenance
    rides whole. A browse carries no results of its
    own: its panel and the book's verdict under it
    are derived.
    """

    seq: int
    text: str
    kind_filter: str
    detail: str
    recorded_on: str
    actor: str
    source: str
    origin_session: str
    browse_id: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "seq", _check_seq(self.seq))
        text = _check_long_text(self.text, "the browse text")
        parse_query(text)
        object.__setattr__(self, "text", text)
        object.__setattr__(
            self, "kind_filter", normalize_kind_filter(self.kind_filter))
        object.__setattr__(
            self, "detail",
            _check_long_text(self.detail, "the browse's words"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))
        object.__setattr__(
            self, "actor", _check_title(self.actor, "an actor"))
        object.__setattr__(
            self, "source", _check_title(self.source, "a source"))
        object.__setattr__(
            self, "origin_session",
            _check_word(self.origin_session, "an origin session"))
        if self.browse_id is not None:
            object.__setattr__(
                self, "browse_id",
                _check_word(self.browse_id, "a browse id"))

    @property
    def tokens(self) -> Tuple[str, ...]:
        """The browse's tokens, read by the one token road."""
        return parse_query(self.text)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "command_palace_browse",
            "slice": COMMAND_PALACE_SLICE,
            "browse_id": self.browse_id,
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


def _check_browse_ref(value: Any) -> PalaceBrowse:
    if isinstance(value, PalaceBrowse):
        return value
    return validate_browse(value)


def validate_browse(browse: Any) -> PalaceBrowse:
    """Judge one browse record whole and return it."""
    if isinstance(browse, PalaceBrowse):
        return browse
    if not isinstance(browse, dict):
        raise ValueError(
            f"a browse record must be a mapping, got {browse!r}")
    unknown = set(browse) - _BROWSE_KEYS
    if unknown:
        raise ValueError(
            f"a browse record carries unknown keys: "
            f"{sorted(unknown)}")
    if "type" in browse:
        raise ValueError(
            "a browse record is judged without its news keys")

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(browse, spellings, what)
        if value is None:
            raise ValueError(f"a browse record names no {what}")
        return value

    return PalaceBrowse(
        browse_id=_pick_any(
            browse, ("browse_id", "id"), "browse id"),
        seq=_needed(("seq", "sequence", "order"), "sequence"),
        text=_needed(("text", "query", "query_text"), "browse text"),
        kind_filter=_needed(
            ("kind_filter", "filter", "kind"), "kind filter"),
        detail=_needed(("detail", "reason"), "the browse's words"),
        recorded_on=_needed(
            ("recorded_on", "day", "date"), "day it was recorded"),
        actor=_needed(("actor", "by", "who"), "actor"),
        source=_needed(("source",), "source"),
        origin_session=_needed(
            ("origin_session", "session"), "origin session"),
    )


def build_browse(browse: Any = None, **kwargs: Any) -> PalaceBrowse:
    """Build one browse record from a mapping, a record, or fields."""
    if kwargs:
        if browse is not None:
            raise ValueError("a browse record is built one way at a time")
        browse = kwargs
    return validate_browse(browse)


def rank_entries(entries: Any, browse: Any) -> Tuple[PalaceEntry, ...]:
    """The entries one browse shows, in derived order.

    Every entry is scored by the one derived road;
    the shown entries are those deriving a score
    above nothing, ordered by score, then by the
    roadmap's kind order, then by command, then by
    entry id - so two panels of one book under one
    browse always stand in one order.
    """
    held_browse = _check_browse_ref(browse)
    scored = []
    for entry in entries:
        current = _check_entry_ref(entry)
        value = score_of(current, held_browse)
        if value > 0:
            scored.append((current, value))
    scored.sort(key=lambda pair: (
        -pair[1], ENTRY_KINDS.index(pair[0].kind),
        pair[0].command.lower(), pair[0].entry_id))
    return tuple(entry for entry, _ in scored)


# ---------------------------------------------------------------------
# The panel row: one shown entry as the panel carries it.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class PalacePanelRow:
    """One shown entry as the panel carries it.

    The row carries the entry's id, its kind, its
    command, its DERIVED score under the panel's
    browse, its DERIVED entry line and its recorded
    day. The description and the example never stand
    in a row - the panel is the browse at a glance.
    """

    entry_id: str
    kind: str
    command: str
    score: int
    line: str
    recorded_on: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "entry_id",
            _check_word(self.entry_id, "an entry id"))
        object.__setattr__(self, "kind", normalize_kind(self.kind))
        object.__setattr__(
            self, "command", _check_command(self.command))
        object.__setattr__(
            self, "score",
            _check_count(self.score, "a row's score"))
        if self.score < 1:
            raise ValueError(
                "a panel row stands only for a shown entry - "
                "its score stands above nothing")
        object.__setattr__(
            self, "line", _check_long_text(self.line, "an entry line"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))

    def sort_key(self) -> Tuple[Any, ...]:
        return (-self.score, ENTRY_KINDS.index(self.kind),
                self.command.lower(), self.entry_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "kind": self.kind,
            "command": self.command,
            "score": self.score,
            "line": self.line,
            "recorded_on": self.recorded_on,
        }


def _row_for_entry(entry: PalaceEntry,
                   browse: Any) -> PalacePanelRow:
    return PalacePanelRow(
        entry_id=entry.entry_id, kind=entry.kind,
        command=entry.command, score=score_of(entry, browse),
        line=line_of(entry), recorded_on=entry.recorded_on)


def _check_row_ref(value: Any) -> PalacePanelRow:
    if isinstance(value, PalacePanelRow):
        return value
    return validate_row(value)


def validate_row(row: Any, entry: Any = None,
                 browse: Any = None) -> PalacePanelRow:
    """Judge one panel row, against its entry when named."""
    if isinstance(row, PalacePanelRow):
        current = row
    elif isinstance(row, dict):
        unknown = set(row) - _ROW_KEYS
        if unknown:
            raise ValueError(
                f"a palace panel row carries unknown keys: "
                f"{sorted(unknown)}")

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            value = _pick_any(row, spellings, what)
            if value is None:
                raise ValueError(f"a palace panel row names no {what}")
            return value

        current = PalacePanelRow(
            entry_id=_needed(("entry_id", "id"), "entry id"),
            kind=_needed(("kind",), "kind"),
            command=_needed(("command",), "command"),
            score=_needed(("score",), "score"),
            line=_needed(("line",), "entry line"),
            recorded_on=_needed(("recorded_on",), "day it was recorded"))
    else:
        raise ValueError(
            f"a palace panel row must be a mapping, got {row!r}")
    if entry is not None:
        held = _check_entry_ref(entry)
        if browse is None:
            raise ValueError(
                "a panel row is judged against its entry "
                "under a named browse - the score is derived "
                "from the browse, never from the row alone")
        wanted = _row_for_entry(held, _check_browse_ref(browse))
        if current != wanted:
            raise ValueError(
                "a palace panel row must be its entry's own "
                "row under the browse - the score and the line "
                "are derived from the entry, never written "
                "beside it")
    return current


def build_row(row: Any = None, entry: Any = None,
              browse: Any = None,
              **kwargs: Any) -> PalacePanelRow:
    """Build one panel row from a mapping, a row, or its entry."""
    if entry is not None:
        if row is not None or kwargs:
            return validate_row(
                row if row is not None else kwargs, entry, browse)
        return _row_for_entry(
            _check_entry_ref(entry), _check_browse_ref(browse))
    if kwargs:
        if row is not None:
            raise ValueError("a row is built one way at a time")
        row = kwargs
    return validate_row(row)


@dataclass(frozen=True)
class PalaceKindCount:
    """How many shown entries of one kind a panel holds."""

    kind: str
    items: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", normalize_kind(self.kind))
        object.__setattr__(
            self, "items", _check_count(self.items, "a kind's items"))

    def to_record(self) -> Dict[str, Any]:
        return {"kind": self.kind, "items": self.items}


def _check_kind_count_ref(value: Any) -> PalaceKindCount:
    if isinstance(value, PalaceKindCount):
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
        return PalaceKindCount(kind=kind, items=items)
    raise ValueError(f"a kind count must be a mapping, got {value!r}")


def _kind_counts(
        rows: Tuple[PalacePanelRow, ...]) -> Tuple[PalaceKindCount, ...]:
    counts: Dict[str, int] = {}
    for row in rows:
        counts[row.kind] = counts.get(row.kind, 0) + 1
    return tuple(
        PalaceKindCount(kind=kind, items=counts[kind])
        for kind in ENTRY_KINDS if kind in counts)


def _panel_account(total_entries: int, total_matched: int,
                   kind_counts: Tuple[PalaceKindCount, ...],
                   query_text: str, kind_filter: str,
                   as_of: str) -> Tuple[str, ...]:
    kinds = ", ".join(
        f"{count.kind} {count.items}" for count in kind_counts)
    return (
        f"The command palace holds {total_entries} commands as of "
        f"{as_of}: the browse {query_text!r} under the {kind_filter} "
        f"filter shows {total_matched} of them: {kinds}.",
        "Rows stand in derived order, best match first, so "
        "two panels of one browse diff cleanly, line by line.",
        "Every score is derived from the browse's tokens against "
        "the entry's own command, tags, description and example "
        "- no score is stored on any entry, and no order is "
        "chosen by hand.",
        "The palace's words are plain words first, and a browse "
        "only ever looks: it runs no command it shows, renders "
        "no custom command's template and changes no session.",
    )


@dataclass(frozen=True)
class PalacePanel:
    """The derived panel of one book under one browse.

    Rows stand in derived order - score, then the
    roadmap's kind order, then command, then entry
    id; the totals are the rows' own counts and the
    kind counts stand in the roadmap's kind order.
    A stored panel is judged whole in
    ``__post_init__``: its totals, its kind counts,
    its derived order and its account must all be
    the rows' own derived shape - a panel may not
    soften its browse.
    """

    panel_id: Optional[str]
    browse_id: Optional[str]
    query_text: str
    kind_filter: str
    rows: Tuple[PalacePanelRow, ...]
    total_entries: int
    total_matched: int
    kind_counts: Tuple[PalaceKindCount, ...]
    as_of: str
    account: Tuple[str, ...]

    def __post_init__(self) -> None:
        if self.panel_id is not None:
            object.__setattr__(
                self, "panel_id",
                _check_word(self.panel_id, "a panel id"))
        if self.browse_id is not None:
            object.__setattr__(
                self, "browse_id",
                _check_word(self.browse_id, "a browse id"))
        text = _check_long_text(self.query_text, "the browse text")
        parse_query(text)
        object.__setattr__(self, "query_text", text)
        object.__setattr__(
            self, "kind_filter",
            normalize_kind_filter(self.kind_filter))
        rows = tuple(_check_row_ref(r) for r in self.rows)
        object.__setattr__(self, "rows", rows)
        ids = [r.entry_id for r in rows]
        if len(set(ids)) != len(ids):
            raise ValueError("panel rows stand one row per entry")
        if [r.sort_key() for r in rows] != sorted(
                r.sort_key() for r in rows):
            raise ValueError(
                "panel rows stand in derived order - score, "
                "then kind order, then command, then entry id")
        for field in ("total_entries", "total_matched"):
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
        if self.total_entries < self.total_matched:
            raise ValueError(
                "a panel's entry total cannot stand below "
                "its matched total")
        if counts != _kind_counts(rows):
            raise ValueError("a panel's kind counts are its rows' own counts")
        if rows and self.as_of < max(r.recorded_on for r in rows):
            raise ValueError(
                "a panel's as-of day precedes one of its rows")
        if self.account != _panel_account(
                self.total_entries, self.total_matched, counts,
                self.query_text, self.kind_filter, self.as_of):
            raise ValueError(
                "a panel's account is its rows' own account, "
                "derived, never written loose")

    def row_for(self, entry_id: Any) -> PalacePanelRow:
        """The row one entry id names (KeyError if absent)."""
        wanted = _check_word(entry_id, "an entry id")
        for row in self.rows:
            if row.entry_id == wanted:
                return row
        raise KeyError(f"no row named {wanted!r} stands on the panel")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "command_palace_panel",
            "slice": COMMAND_PALACE_SLICE,
            "panel_id": self.panel_id,
            "browse_id": self.browse_id,
            "query_text": self.query_text,
            "kind_filter": self.kind_filter,
            "rows": [r.to_record() for r in self.rows],
            "total_entries": self.total_entries,
            "total_matched": self.total_matched,
            "kind_counts": [c.to_record() for c in self.kind_counts],
            "as_of": self.as_of,
            "account": list(self.account),
        }


def _held_entries(source: Any) -> Tuple[PalaceEntry, ...]:
    if isinstance(source, CommandPalaceBook):
        return source.entries
    if isinstance(source, CommandPalaceRegistry):
        return source.list_entries()
    if isinstance(source, PalaceEntry):
        return (source,)
    raise ValueError(f"a command-palace source is needed, got {source!r}")


def _held_browses(source: Any) -> Tuple[PalaceBrowse, ...]:
    if isinstance(source, CommandPalaceBook):
        return source.browses
    if isinstance(source, CommandPalaceRegistry):
        return source.list_browses()
    return ()


def _resolve_browse(source: Any, browse: Any) -> PalaceBrowse:
    if browse is None:
        raise ValueError(
            "a panel or verdict is derived under a named browse")
    if isinstance(browse, str):
        wanted = _check_word(browse, "a browse id")
        for held in _held_browses(source):
            if held.browse_id == wanted:
                return held
        raise ValueError(
            f"no browse named {wanted!r} stands in the source")
    return _check_browse_ref(browse)


def _default_browse(source: Any) -> PalaceBrowse:
    """The browse a book's own panel stands under, or its first."""
    if isinstance(source, (CommandPalaceBook, CommandPalaceRegistry)):
        book = source if isinstance(source, CommandPalaceBook) else source.book()
        for panel in book.panels:
            if panel.browse_id is not None:
                for held in book.browses:
                    if held.browse_id == panel.browse_id:
                        return held
        if book.browses:
            return book.browses[0]
    raise ValueError("no browse stands in the source to derive under")


def derive_panel(source: Any, browse: Any = None) -> PalacePanel:
    """Derive the panel of a book under one browse."""
    held_browse = _resolve_browse(source, browse)
    entries = _held_entries(source)
    matched = rank_entries(entries, held_browse)
    rows = tuple(_row_for_entry(e, held_browse) for e in matched)
    counts = _kind_counts(rows)
    as_of = max((e.recorded_on for e in entries), default=_EXAMPLE_AS_OF)
    return PalacePanel(
        panel_id=None, browse_id=held_browse.browse_id,
        query_text=held_browse.text, kind_filter=held_browse.kind_filter,
        rows=rows, total_entries=len(entries),
        total_matched=len(rows), kind_counts=counts, as_of=as_of,
        account=_panel_account(
            len(entries), len(rows), counts, held_browse.text,
            held_browse.kind_filter, as_of))


def validate_panel(panel: Any, source: Any = None) -> PalacePanel:
    """Judge one panel whole, against its source when named."""
    if isinstance(panel, PalacePanel):
        current = panel
    elif isinstance(panel, dict):
        data = dict(panel)
        data.pop("type", None)
        data.pop("slice", None)
        unknown = set(data) - _PANEL_KEYS
        if unknown:
            raise ValueError(
                f"a palace panel carries unknown keys: "
                f"{sorted(unknown)}")

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            value = _pick_any(data, spellings, what)
            if value is None:
                raise ValueError(f"a palace panel names no {what}")
            return value

        rows_in = _needed(("rows", "shown"), "rows")
        counts_in = _needed(("kind_counts", "kinds"), "kind counts")
        current = PalacePanel(
            panel_id=_pick_any(data, ("panel_id", "id"), "panel id"),
            browse_id=_pick_any(data, ("browse_id", "browse"), "browse id"),
            query_text=_needed(("query_text", "query"), "browse text"),
            kind_filter=_needed(("kind_filter", "filter"), "kind filter"),
            rows=tuple(validate_row(r) for r in rows_in),
            total_entries=_needed(
                ("total_entries", "entries"), "entry total"),
            total_matched=_needed(("total_matched", "matched"), "matched total"),
            kind_counts=tuple(
                _check_kind_count_ref(c) for c in counts_in),
            as_of=_needed(("as_of", "day"), "as-of day"),
            account=tuple(_needed(("account", "statements"), "account")))
    else:
        raise ValueError(f"a palace panel must be a mapping, got {panel!r}")
    if source is not None:
        held_browse = _resolve_browse(source, current.browse_id)
        derived = derive_panel(source, held_browse)
        if (current.browse_id != derived.browse_id
                or current.query_text != derived.query_text
                or current.kind_filter != derived.kind_filter
                or current.rows != derived.rows
                or current.total_entries != derived.total_entries
                or current.total_matched != derived.total_matched
                or current.kind_counts != derived.kind_counts
                or current.as_of != derived.as_of
                or current.account != derived.account):
            raise ValueError(
                "a stored panel must equal the panel its book "
                "derives under its browse - the panel is "
                "derived, never stored loose")
    return current


def build_panel(panel: Any = None, source: Any = None,
                browse: Any = None, **kwargs: Any) -> PalacePanel:
    """Build one panel from a mapping, a panel, or its source."""
    if kwargs:
        if panel is not None:
            raise ValueError("a panel is built one way at a time")
        panel = kwargs
    if panel is None and source is not None:
        return derive_panel(source, browse)
    return validate_panel(panel, source)


# ---------------------------------------------------------------------
# The verdict: the whole book under one browse, in one word.
# ---------------------------------------------------------------------


def _verdict_word(total_matched: int, distinct_kinds: int) -> str:
    if total_matched == 0:
        return "empty"
    if distinct_kinds > 1:
        return "spanning"
    return "shelved"


@dataclass(frozen=True)
class PalaceVerdict:
    """The derived verdict of one whole book under one browse.

    The word is read off the shown entries alone:
    empty while no entry is shown, shelved while
    the shown entries stand in one kind alone,
    spanning while they span more than one kind. A
    stored verdict is judged against those tallies
    in ``__post_init__``.
    """

    total_entries: int
    total_matched: int
    distinct_kinds: int
    earliest_on: str
    latest_on: str
    verdict: str

    def __post_init__(self) -> None:
        for field in ("total_entries", "total_matched",
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
        if self.total_matched > self.total_entries:
            raise ValueError(
                "a verdict's matched tally cannot exceed its "
                "entry total")
        if self.distinct_kinds > len(ENTRY_KINDS):
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
            "type": "command_palace_verdict",
            "slice": COMMAND_PALACE_SLICE,
            "total_entries": self.total_entries,
            "total_matched": self.total_matched,
            "distinct_kinds": self.distinct_kinds,
            "earliest_on": self.earliest_on,
            "latest_on": self.latest_on,
            "verdict": self.verdict,
        }


def derive_verdict(source: Any, browse: Any = None) -> PalaceVerdict:
    """Derive the verdict of a book under one browse."""
    held_browse = _resolve_browse(source, browse)
    entries = _held_entries(source)
    matched = rank_entries(entries, held_browse)
    distinct = len({e.kind for e in matched})
    days = [e.recorded_on for e in entries]
    return PalaceVerdict(
        total_entries=len(entries), total_matched=len(matched),
        distinct_kinds=distinct,
        earliest_on=min(days) if days else _EXAMPLE_AS_OF,
        latest_on=max(days) if days else _EXAMPLE_AS_OF,
        verdict=_verdict_word(len(matched), distinct))


def _check_verdict_ref(value: Any) -> PalaceVerdict:
    if isinstance(value, PalaceVerdict):
        return value
    return validate_verdict(value)


def validate_verdict(verdict: Any, source: Any = None,
                     browse: Any = None) -> PalaceVerdict:
    """Judge one verdict whole, against its source when named."""
    if isinstance(verdict, PalaceVerdict):
        current = verdict
    elif isinstance(verdict, dict):
        data = dict(verdict)
        data.pop("type", None)
        data.pop("slice", None)
        unknown = set(data) - _VERDICT_KEYS
        if unknown:
            raise ValueError(
                f"a palace verdict carries unknown keys: "
                f"{sorted(unknown)}")

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            value = _pick_any(data, spellings, what)
            if value is None:
                raise ValueError(f"a palace verdict names no {what}")
            return value

        current = PalaceVerdict(
            total_entries=_needed(
                ("total_entries", "entries"), "entry total"),
            total_matched=_needed(("total_matched", "matched"), "matched total"),
            distinct_kinds=_needed(
                ("distinct_kinds", "kinds"), "distinct kinds"),
            earliest_on=_needed(("earliest_on", "earliest"), "earliest day"),
            latest_on=_needed(("latest_on", "latest"), "latest day"),
            verdict=_needed(("verdict",), "verdict"))
    else:
        raise ValueError(f"a palace verdict must be a mapping, got {verdict!r}")
    if source is not None:
        derived = derive_verdict(source, browse)
        if current != derived:
            raise ValueError(
                "a stored verdict must equal the verdict its "
                "book derives under its browse - the verdict "
                "is derived, never stored loose")
    return current


def build_verdict(verdict: Any = None, source: Any = None,
                  browse: Any = None, **kwargs: Any) -> PalaceVerdict:
    """Build one verdict from a mapping, a verdict, or its source."""
    if kwargs:
        if verdict is not None:
            raise ValueError("a verdict is built one way at a time")
        verdict = kwargs
    if verdict is None and source is not None:
        return derive_verdict(source, browse)
    return validate_verdict(verdict, source, browse)


# ---------------------------------------------------------------------
# The book: one set of entries and browses, held whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class CommandPalaceBook:
    """One set of palace entries and browses, held whole.

    Entries stand in held order - one entry per
    entry id and one entry per command - browses
    stand in recorded order, one browse per
    sequence and per id, and every stored panel is
    judged against the book and the browse it
    stands under.
    """

    title: str
    entries: Tuple[PalaceEntry, ...] = ()
    browses: Tuple[PalaceBrowse, ...] = ()
    panels: Tuple[PalacePanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book title"))
        entries = tuple(_check_entry_ref(e) for e in self.entries)
        object.__setattr__(self, "entries", entries)
        ids = [e.entry_id for e in entries]
        if len(set(ids)) != len(ids):
            raise ValueError("a book holds one entry per entry id")
        commands = [e.command for e in entries]
        if len(set(commands)) != len(commands):
            raise ValueError("a book holds one entry per command")
        browses = tuple(_check_browse_ref(b) for b in self.browses)
        object.__setattr__(self, "browses", browses)
        seqs = [b.seq for b in browses]
        if seqs != sorted(seqs) or len(set(seqs)) != len(seqs):
            raise ValueError(
                "a book's browses stand in recorded order, "
                "one browse per sequence")
        browse_ids = [
            b.browse_id for b in browses if b.browse_id is not None]
        if len(set(browse_ids)) != len(browse_ids):
            raise ValueError("a book holds one browse per browse id")
        panels = tuple(validate_panel(p, self) for p in self.panels)
        object.__setattr__(self, "panels", panels)

    def entry_for(self, entry_id: Any) -> PalaceEntry:
        """The entry one id names (KeyError if absent)."""
        wanted = _check_word(entry_id, "an entry id")
        for entry in self.entries:
            if entry.entry_id == wanted:
                return entry
        raise KeyError(f"no entry named {wanted!r} stands in the book")

    def browse_for(self, browse_id: Any) -> PalaceBrowse:
        """The browse one id names (KeyError if absent)."""
        wanted = _check_word(browse_id, "a browse id")
        for browse in self.browses:
            if browse.browse_id == wanted:
                return browse
        raise KeyError(f"no browse named {wanted!r} stands in the book")

    def panel_for(self, panel_id: Any) -> PalacePanel:
        """The panel one id names (KeyError if absent)."""
        wanted = _check_word(panel_id, "a panel id")
        for panel in self.panels:
            if panel.panel_id == wanted:
                return panel
        raise KeyError(f"no panel named {wanted!r} stands in the book")

    def entry_ids(self) -> Tuple[str, ...]:
        """The book's entry ids, in held order."""
        return tuple(e.entry_id for e in self.entries)

    def browse_ids(self) -> Tuple[Optional[str], ...]:
        """The book's browse ids, in recorded order."""
        return tuple(b.browse_id for b in self.browses)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "command_palace_book",
            "slice": COMMAND_PALACE_SLICE,
            "title": self.title,
            "entries": [e.to_record() for e in self.entries],
            "browses": [b.to_record() for b in self.browses],
            "panels": [p.to_record() for p in self.panels],
            "entry_count": len(self.entries),
            "browse_count": len(self.browses),
        }


def _judge_book_panels(book: CommandPalaceBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def validate_book(data: Any, *, require_example: bool = False) -> CommandPalaceBook:
    """Judge one palace file's data whole and return its book."""
    if isinstance(data, CommandPalaceBook):
        book = data
        _judge_book_panels(book)
        if require_example:
            _check_example(book)
        return book
    if not isinstance(data, dict):
        raise ValueError(f"a command-palace book must be a mapping, got {data!r}")
    unknown = set(data) - _COMMAND_PALACE_KEYS
    if unknown:
        raise ValueError(
            f"a command-palace book carries unknown keys: {sorted(unknown)}")
    if data.get("schema") != COMMAND_PALACE_SCHEMA:
        raise ValueError(
            f"a command-palace book's schema must be "
            f"{COMMAND_PALACE_SCHEMA!r}, got {data.get('schema')!r}")
    if data.get("slice") != COMMAND_PALACE_SLICE:
        raise ValueError(
            f"a command-palace book's slice must be "
            f"{COMMAND_PALACE_SLICE!r}, got {data.get('slice')!r}")
    guide = data.get("guide") or {}
    title = _pick_any(guide, ("title", "name"), "title")
    if title is None:
        title = _pick_any(data, ("title", "name"), "title")
    entries_in = _pick_any(data, ("entries",), "entries")
    if entries_in is None:
        raise ValueError("a command-palace book names no entries")
    browses_in = data.get("browses") or []
    panels_in = data.get("panels") or []
    entries = []
    for raw in entries_in:
        stored = dict(raw)
        stored.pop("type", None)
        stored.pop("slice", None)
        for derived_key in ("line", "score", "rank"):
            stored.pop(derived_key, None)
        entries.append(validate_entry(stored))
    browses = []
    for raw in browses_in:
        stored = dict(raw)
        stored.pop("type", None)
        stored.pop("slice", None)
        stored.pop("tokens", None)
        browses.append(validate_browse(stored))
    book = CommandPalaceBook(
        title=title,
        entries=tuple(entries),
        browses=tuple(browses),
        panels=tuple(validate_panel(p) for p in panels_in))
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def _check_example(book: CommandPalaceBook) -> None:
    if book.title != _EXAMPLE_TITLE:
        raise ValueError(
            f"the shipped example book is {_EXAMPLE_TITLE!r}, "
            f"got {book.title!r}")
    if book.entry_ids() != _EXAMPLE_ENTRY_IDS:
        raise ValueError("the shipped example book's entries differ")
    first = book.entries[0]
    if first.entry_id != _EXAMPLE_FIRST_ENTRY_ID or (
            first.command != _EXAMPLE_FIRST_ENTRY_COMMAND):
        raise ValueError("the shipped example book's first entry differs")
    if book.browse_ids() != _EXAMPLE_BROWSE_IDS:
        raise ValueError("the shipped example book's browses differ")
    if len(book.panels) != 1 or (
            book.panels[0].panel_id != _EXAMPLE_PANEL_ID):
        raise ValueError("the shipped example book's panel differs")
    if book.panels[0].as_of != _EXAMPLE_AS_OF:
        raise ValueError("the shipped example book's as-of day differs")
    derived = derive_panel(book, book.panels[0].browse_id)
    if tuple(r.entry_id for r in book.panels[0].rows) != tuple(
            r.entry_id for r in derived.rows):
        raise ValueError("the shipped example book's panel rows differ")


def build_book(book: Any = None, **kwargs: Any) -> CommandPalaceBook:
    """Build one book from a mapping, a book, or fields."""
    if isinstance(book, CommandPalaceBook) and not kwargs:
        return validate_book(book)
    if kwargs:
        if book is not None:
            raise ValueError("a book is built one way at a time")
        fields = dict(kwargs)
    elif isinstance(book, dict) and (
            "entries" in book) and (
            "schema" not in book and "guide" not in book
            and "canon_note" not in book):
        fields = dict(book)
    else:
        return _book_from(book, require_example=False)
    unknown = set(fields) - _BOOK_KEYS - {
        "entries", "browses", "panels"}
    if unknown:
        raise ValueError(
            f"a command-palace book carries unknown keys: "
            f"{sorted(unknown)}")
    title = _pick_any(fields, ("title", "name"), "title")
    if title is None:
        raise ValueError("a command-palace book names no title")
    entries_in = _pick_any(fields, ("entries",), "entries") or ()
    return CommandPalaceBook(
        title=title,
        entries=tuple(_check_entry_ref(e) for e in entries_in),
        browses=tuple(
            _check_browse_ref(b) for b in fields.get("browses") or ()),
        panels=tuple(
            validate_panel(p) for p in fields.get("panels") or ()))


def _book_from(data: Any, *, require_example: bool) -> CommandPalaceBook:
    if isinstance(data, CommandPalaceBook):
        return validate_book(data, require_example=require_example)
    if isinstance(data, dict):
        return validate_book(data, require_example=require_example)
    raise ValueError(f"a command-palace book must be a mapping, got {data!r}")


def load_command_palace(data: Optional[Dict[str, Any]] = None) -> CommandPalaceBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(COMMAND_PALACE_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_command_palace_file(path: Any) -> CommandPalaceBook:
    """Load one palace file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: entries and browses held one by one.
# ---------------------------------------------------------------------


class CommandPalaceRegistry:
    """An in-memory holding of palace entries and browses.

    The registry is the pure layer's model of a
    session's palace: entries are held under their
    entry ids, one entry per id and per command, in
    held order, and browses are held in recorded
    order, one browse per sequence and per id.
    Holding is data only - no browse held here runs
    the command it shows, and standing a browse
    commits no choice at all.
    """

    def __init__(self, book: Any = None) -> None:
        self._entries: List[PalaceEntry] = []
        self._browses: List[PalaceBrowse] = []
        self._title: Optional[str] = None
        if book is not None:
            self.register_book(book)

    def title(self) -> Optional[str]:
        return self._title

    def _fresh_browse_id(self, held_ids: Any) -> str:
        n = 1
        while f"browse-{n}" in held_ids:
            n += 1
        return f"browse-{n}"

    def _check_entry_free(self, entry: PalaceEntry) -> None:
        for held in self._entries:
            if held.entry_id == entry.entry_id:
                raise ValueError(
                    f"an entry already stands under id "
                    f"{entry.entry_id!r}")
            if held.command == entry.command:
                raise ValueError(
                    f"an entry already stands for command "
                    f"{entry.command!r} - the palace holds one "
                    f"entry per command")

    def register_entry(self, entry: Any) -> PalaceEntry:
        """Hold one entry, judged whole before it is held."""
        validated = _check_entry_ref(entry)
        self._check_entry_free(validated)
        self._entries.append(validated)
        return validated

    def _check_browse_free(self, browse: PalaceBrowse) -> None:
        for held in self._browses:
            if browse.browse_id is not None and (
                    held.browse_id == browse.browse_id):
                raise ValueError(
                    f"a browse already stands under id "
                    f"{browse.browse_id!r}")
            if held.seq == browse.seq:
                raise ValueError(
                    f"a browse already stands at sequence "
                    f"{browse.seq} - the book holds one "
                    f"browse per place")

    def register_browse(self, browse: Any) -> PalaceBrowse:
        """Hold one browse record, judged whole first.

        A browse id or a sequence already standing
        here refuses and holds nothing new. A held
        browse only ever looks: standing it derives
        its panel, runs no command it shows and
        commits no choice.
        """
        validated = _check_browse_ref(browse)
        self._check_browse_free(validated)
        if validated.browse_id is None:
            validated = PalaceBrowse(
                browse_id=self._fresh_browse_id(
                    {b.browse_id for b in self._browses}),
                seq=validated.seq, text=validated.text,
                kind_filter=validated.kind_filter,
                detail=validated.detail,
                recorded_on=validated.recorded_on,
                actor=validated.actor, source=validated.source,
                origin_session=validated.origin_session)
        self._browses.append(validated)
        self._browses.sort(key=lambda b: b.seq)
        return validated

    def register_book(self, book: Any) -> CommandPalaceBook:
        """Hold a whole book, judged whole first."""
        validated = build_book(book)
        for entry in validated.entries:
            self._check_entry_free(entry)
        if self._title is None:
            self._title = validated.title
        elif validated.title != self._title:
            raise ValueError(
                "a second book under a different title refuses - "
                "one book stands in one registry")
        for entry in validated.entries:
            self._entries.append(entry)
        for browse in validated.browses:
            self.register_browse(browse)
        return self.book()

    def get_entry(self, entry_id: Any) -> PalaceEntry:
        """The entry one id names (KeyError if absent)."""
        wanted = _check_word(entry_id, "an entry id")
        for entry in self._entries:
            if entry.entry_id == wanted:
                return entry
        raise KeyError(f"no entry named {wanted!r} stands held")

    def get_browse(self, browse_id: Any) -> PalaceBrowse:
        """The browse record one id names (KeyError if absent)."""
        wanted = _check_word(browse_id, "a browse id")
        for browse in self._browses:
            if browse.browse_id == wanted:
                return browse
        raise KeyError(f"no browse named {wanted!r} stands held")

    def latest_browse(self) -> PalaceBrowse:
        """The last browse recorded (KeyError if none)."""
        if not self._browses:
            raise KeyError("no browse stands held")
        return self._browses[-1]

    def list_entries(self) -> Tuple[PalaceEntry, ...]:
        return tuple(self._entries)

    def list_browses(self) -> Tuple[PalaceBrowse, ...]:
        return tuple(self._browses)

    def book(self) -> CommandPalaceBook:
        return CommandPalaceBook(
            title=self._title or "Command Palace",
            entries=tuple(self._entries),
            browses=tuple(self._browses))

    def panel(self, browse: Any = None) -> PalacePanel:
        return derive_panel(self.book(), browse)

    def verdict(self, browse: Any = None) -> PalaceVerdict:
        return derive_verdict(self.book(), browse)


def entries_with_kind(source: Any, kind: Any) -> Tuple[PalaceEntry, ...]:
    """The entries of one kind, in held order."""
    wanted = normalize_kind(kind)
    return tuple(
        e for e in _held_entries(source) if e.kind == wanted)


def total_entries(source: Any) -> int:
    """How many entries a source holds."""
    return len(_held_entries(source))


# ---------------------------------------------------------------------
# Session news, plain words, and the screens.
# ---------------------------------------------------------------------


def entry_record(entry: Any) -> Dict[str, Any]:
    """The session-news record of one palace entry."""
    current = _check_entry_ref(entry)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Command palace entry {current.entry_id}: "
        f"{line_of(current)}.")
    return record_out


def custom_command_record(custom: Any) -> Dict[str, Any]:
    """The session-news record of one custom command."""
    current = validate_custom_command(custom)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Command palace custom command {current.custom_id}: "
        f"{current.command} at the {current.home} home - "
        f"{current.description}")
    return record


def browse_record(browse: Any) -> Dict[str, Any]:
    """The session-news record of one browse record."""
    current = _check_browse_ref(browse)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Command palace browse {current.browse_id or current.seq}: "
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
        f"Command palace panel as of {current.as_of}: "
        f"{current.total_matched} of {current.total_entries} "
        f"commands show under {current.query_text!r} under the "
        f"{current.kind_filter} filter ({kinds}).")
    return record


def verdict_record(verdict: Any, source: Any = None,
                   browse: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived verdict."""
    current = validate_verdict(verdict, source, browse)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Command palace verdict: {current.verdict} - "
        f"{current.total_matched} of {current.total_entries} "
        f"commands shown across {current.distinct_kinds} "
        f"kinds, from {current.earliest_on} to {current.latest_on}.")
    return record


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one palace book."""
    current = book if isinstance(book, CommandPalaceBook) else build_book(book)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Command palace {current.title}: "
        f"{record['entry_count']} entries named, "
        f"{record['browse_count']} browses held.")
    return record


def plain_words(entry: Any) -> str:
    """One entry, in one plain sentence."""
    current = _check_entry_ref(entry)
    return (
        f"{line_of(current)} - one discoverable command on "
        f"entry {current.entry_id}: "
        f"{current.description} For example: "
        f"{current.example} Finding it here runs nothing.")


def browse_plain_words(browse: Any) -> str:
    """One browse record, in one plain sentence."""
    current = _check_browse_ref(browse)
    return (
        f"Browse {current.browse_id or current.seq} looks for "
        f"{current.text!r} under the {current.kind_filter} "
        f"filter, read into the tokens "
        f"{', '.join(current.tokens)} by the one token road, "
        f"recorded on {current.recorded_on} by "
        f"{current.actor}: {current.detail} A browse only "
        f"ever looks - it runs no command and commits no "
        f"choice at all.")


def panel_plain_words(source: Any, browse: Any = None) -> str:
    """The panel in plain words, in full."""
    if isinstance(source, PalacePanel):
        panel = validate_panel(source)
        title = None
    elif isinstance(source, (CommandPalaceBook, CommandPalaceRegistry)):
        book = source if isinstance(
            source, CommandPalaceBook) else source.book()
        panel = derive_panel(
            book, browse if browse is not None
            else _default_browse(book))
        title = book.title
    else:
        raise ValueError(f"a command-palace source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Shown, in derived order:")
    for row in panel.rows:
        lines.append(
            f"{row.entry_id}: {row.line} "
            f"(score {row.score}, {row.recorded_on})")
    lines.extend(panel.account)
    return "\n".join(lines)


def verdict_plain_words(source: Any, browse: Any = None) -> str:
    """The book verdict in plain words, in full."""
    if isinstance(source, PalaceVerdict):
        verdict = validate_verdict(source)
    elif isinstance(source, (CommandPalaceBook, CommandPalaceRegistry)):
        book = source if isinstance(
            source, CommandPalaceBook) else source.book()
        verdict = derive_verdict(
            book, browse if browse is not None
            else _default_browse(book))
    else:
        raise ValueError(f"a command-palace source is needed, got {source!r}")
    return (
        f"Command palace verdict: {verdict.verdict} - "
        f"{verdict.total_matched} of {verdict.total_entries} "
        f"commands shown, across {verdict.distinct_kinds} "
        f"kinds, from {verdict.earliest_on} to "
        f"{verdict.latest_on} - every score is derived from "
        f"the browse's tokens against the entries' own "
        f"fields, by the one token road.")


def _source_book(source: Any) -> CommandPalaceBook:
    if source is None:
        return load_command_palace()
    if isinstance(source, CommandPalaceRegistry):
        return source.book()
    if isinstance(source, CommandPalaceBook):
        return source
    if isinstance(source, PalaceEntry):
        return CommandPalaceBook(title="One palace entry", entries=(source,))
    raise ValueError(f"a command-palace book is needed, got {source!r}")


def format_entry(entry: Any) -> str:
    """One palace entry as a screen block.

    The entry's kind, command, plain-language
    description and example stand as their own
    lines, and its provenance stands whole - an
    entry held here is a finding, never the act of
    running the command found.
    """
    current = _check_entry_ref(entry)
    lines = [
        f"{current.entry_id}: {line_of(current)}",
        f"Kind: {current.kind}",
        f"Command: {current.command}",
        f"Description: {current.description}",
        f"Example: {current.example}",
        f"Tags: {', '.join(current.tags)}",
        f"Recorded: on {current.recorded_on} by {current.actor} "
        f"from {current.source} in {current.origin_session}.",
    ]
    return "\n".join(lines)


def format_browse(browse: Any) -> str:
    """One browse record as a screen block."""
    current = _check_browse_ref(browse)
    lines = [
        f"{current.browse_id or '-'}: {current.text!r} "
        f"under the {current.kind_filter} filter",
        f"Tokens: {', '.join(current.tokens)}",
        f"Words: {current.detail}",
        f"Recorded: on {current.recorded_on} by {current.actor} "
        f"from {current.source} in {current.origin_session}.",
    ]
    return "\n".join(lines)


def format_book(source: Any = None, kind: Any = None) -> str:
    """The book as derived lines, in held order.

    By default the lines are every entry's derived
    line. With ``kind`` only that kind's entries
    stand in the list.
    """
    book = _source_book(source)
    wanted = normalize_kind(kind) if kind is not None else None
    lines = []
    for entry in book.entries:
        if wanted is not None and entry.kind != wanted:
            continue
        lines.append(f"{entry.entry_id}: {line_of(entry)}")
    if not lines:
        lines.append("No entries stand in the book on that reading.")
    return "\n".join(lines)


def format_panel(source: Any = None, browse: Any = None) -> str:
    """The panel as a screen block: every row and the account."""
    if isinstance(source, PalacePanel):
        panel = validate_panel(source)
        lines: list = []
    else:
        book = _source_book(source)
        panel = derive_panel(
            book, browse if browse is not None
            else _default_browse(book))
        lines = [f"Panel in {book.title}:"]
    lines.append("Shown, in derived order:")
    for row in panel.rows:
        lines.append(
            f"{row.entry_id}: {row.line} - "
            f"score {row.score} ({row.recorded_on})")
    lines.extend(panel.account)
    return "\n".join(lines)


def format_verdict(source: Any = None, browse: Any = None) -> str:
    """The verdict as a screen block."""
    if isinstance(source, PalaceVerdict):
        verdict = validate_verdict(source)
        title = "the book"
    else:
        book = _source_book(source)
        verdict = derive_verdict(
            book, browse if browse is not None
            else _default_browse(book))
        title = book.title
    return (
        f"Verdict in Command Palace over {title}: "
        f"{verdict.verdict} - {verdict.total_matched} of "
        f"{verdict.total_entries} commands shown, "
        f"across {verdict.distinct_kinds} kinds, from "
        f"{verdict.earliest_on} to {verdict.latest_on}.")


def format_command_palace_screen(source: Any = None) -> str:
    """The whole command-palace screen for one book."""
    book = _source_book(source)
    browse = _default_browse(book)
    panel = derive_panel(book, browse)
    verdict = derive_verdict(book, browse)
    lines = [
        f"Command Palace (M-176) - {book.title}",
        format_book(book),
        f"Panel: {panel.total_matched} of "
        f"{panel.total_entries} commands show "
        f"{panel.query_text!r} under the "
        f"{panel.kind_filter} filter.",
        f"Verdict: {verdict.verdict}.",
        "Browsing only looks here - it runs no command "
        "it shows, renders no custom command's "
        "template, opens no skill and changes no "
        "session, and it commits no choice at all.",
    ]
    return "\n".join(lines)


def parse_command_palace_args(args: Any) -> Tuple[str, Any]:
    """Parse the /commandpalace grammar into (action, target).

    ``""``/``show``/``list`` show the book;
    ``entry <entry-id>`` shows one entry whole;
    ``browse <browse-id>`` shows one held browse
    record; ``visit <words>`` derives the panel of
    an ad-hoc browse over the book; ``kind <kind>``
    shows one kind's entries; ``panel`` and
    ``verdict`` show the derived panel and verdict
    under the book's own browse. Anything else
    raises ValueError carrying the usage line.
    """
    if args is None:
        return ("show", None)
    if not isinstance(args, str):
        raise ValueError(USAGE)
    parts = args.split()
    if not parts or parts == ["show"] or parts == ["list"]:
        return ("show", None)
    if parts[0] == "entry" and len(parts) == 2:
        return ("entry", _check_word(parts[1], "an entry id"))
    if parts[0] == "browse" and len(parts) == 2:
        return ("browse", _check_word(parts[1], "a browse id"))
    if parts[0] == "visit" and len(parts) >= 2:
        return ("visit", " ".join(parts[1:]))
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
