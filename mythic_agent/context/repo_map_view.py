"""Map in the TUI (All-Features roadmap slice M-045).

Part III — Code Intelligence. M-044 built the repo map; until
this slice no surface showed it: the map served the context
compiler, but the person at the keyboard could not browse
it, could not ask why the coder thinks a file matters, and
could not pin a file they know matters. This slice is the
map made *visible*, on the established system-command road.

What this layer is:

* A pure view over an M-044 :class:`RepoMap`:
  :func:`build_map_view` presents the map's entries for
  browsing — each with the rank M-044 gave it, its score,
  and its own plain reasons — and :func:`resolve_detail`
  answers for one file: its full detail when it is mapped
  (rank, score arithmetic, definitions with signature
  lines, references in and out, every reason), or an honest
  state when it is not (over the budget, skipped with its
  reason, or absent from the build).
* Pinning: the files the user pins are a config setting
  (``repo_map_pins``, a list of workspace-relative paths,
  catalogued in M-009's catalogue like every setting). A
  pinned file is *shown first* in the browse list; pinning
  never changes its rank, its score, or its reasons — the
  view adds one reason of its own ("pinned by you") and
  says plainly that the rank and score are unchanged. A
  pin naming a file the build left out is explained in
  place — over the budget, skipped with the build's own
  reason, or not found — never dressed up as an entry.
* The live roads: ``Agent.repo_map_status()`` builds the
  map for the session's workspace and presents it through
  this view; ``Agent.repo_map_detail()`` answers for one
  file; pin and unpin go through the journaled config
  change the agent layer owns; ``/map`` shows all of it on
  the terminal and TUI system-command roads, sharing this
  module's parser and formatters.

Honesty rules, enforced here and pinned by the slice's tests:

* **Never a second ranking.** The view's scores, ranks,
  and reasons are M-044's own, carried verbatim; display
  order (pinned first) is presentation, and every pinned
  entry still names its true rank.
* **A pin is the user's word, recorded as given.** Pin
  paths are workspace-relative, validated (no absolute
  paths, no ``..`` escape, no duplicates — a malformed
  stored list raises instead of being guessed at). Whether
  the named file exists is the agent layer's check at pin
  time; what the *map* made of it is this view's to say.
* **Nothing is invented for an unmapped file.** Detail
  for an omitted file says it was over the budget; for a
  skipped file it carries the build's own skip reason;
  for an absent file it says no such mappable file was
  found. No state is ever presented as a mapped entry.
"""

from __future__ import annotations

__all__ = [
    "MAP_VIEW_SLICE",
    "PINS_KEY",
    "PLAIN_EXPLANATION",
    "Any",
    "Dict",
    "List",
    "MapDetail",
    "Optional",
    "PinChange",
    "RepoMap",
    "RepoMapView",
    "Tuple",
    "UnmappedPin",
    "ViewEntry",
    "build_map_view",
    "format_map_change",
    "format_map_detail",
    "format_map_pins",
    "format_map_view",
    "normalize_pin_path",
    "parse_map_args",
    "pin_file",
    "pins_from_config",
    "resolve_detail",
    "unpin_file",
]

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .repo_map import MapEntry, RepoMap

#: The slice that owns this module.
MAP_VIEW_SLICE = "M-045"

#: The config key the pins live under.
PINS_KEY = "repo_map_pins"

#: The map view explained in plain words — the sentences
#: every surface shows.
PLAIN_EXPLANATION = (
    "The repo map in the open: /map browses the files the "
    "map ranks highest for your task, each with the reason "
    "the coder thinks it matters — its PageRank from the "
    "reference graph, the task symbols it matched, what it "
    "defines and what it references. /map show <path> gives "
    "one file's full account. Pin a file with /map pin "
    "<path> and it is shown first whenever you browse; a "
    "pin never changes a file's rank or score, and a pinned "
    "file the map left out — over the token budget, "
    "unparseable, or not found — is explained, never "
    "invented as an entry."
)

_USAGE = (
    "Usage: /map [task words] | /map show <path> | "
    "/map pin <path> | /map unpin <path> | /map pins"
)


def normalize_pin_path(value: Any) -> str:
    """One pin path, validated and normalised.

    Pins are workspace-relative paths in the map's own
    spelling (``/``-separated, as :class:`RepoMap` records
    them). An absolute path, a ``..`` escape, a backslash,
    or an empty name is refused with :class:`ValueError` —
    a pin the map could never name is a mistake to surface,
    not a value to store.
    """
    if not isinstance(value, str):
        raise ValueError(
            f"A pinned file must be named by its path, "
            f"got {type(value).__name__}")
    path = value.strip()
    if not path:
        raise ValueError("A pinned file must be named by its path")
    if "\\" in path:
        raise ValueError(
            f"Pinned path {value!r} uses backslashes; name the "
            "file with / separators, as the map does")
    if path.startswith("/") or (
            len(path) > 1 and path[1] == ":"):
        raise ValueError(
            f"Pinned path {value!r} is absolute; pins name "
            "files relative to the workspace root")
    parts = [part for part in path.split("/") if part not in ("", ".")]
    if not parts or any(part == ".." for part in parts):
        raise ValueError(
            f"Pinned path {value!r} escapes the workspace; pins "
            "name files inside it, relative to its root")
    return "/".join(parts)


def pins_from_config(config: Dict[str, Any]) -> Tuple[str, ...]:
    """The validated pins stored in *config*, in pin order.

    Absent means no file was ever pinned. A stored value
    that is malformed — not a list, a blank or escaping
    path, the same file named twice — raises
    :class:`ValueError`: pins the user wrote must surface
    broken, never be silently dropped.
    """
    raw = config.get(PINS_KEY) or []
    if not isinstance(raw, list):
        raise ValueError(
            f"{PINS_KEY} must be a list of file paths, "
            f"got {type(raw).__name__}")
    pins: List[str] = []
    for item in raw:
        path = normalize_pin_path(item)
        if path in pins:
            raise ValueError(
                f"{PINS_KEY} names {path} twice; each file "
                "may be pinned once")
        pins.append(path)
    return tuple(pins)


@dataclass(frozen=True)
class PinChange:
    """One validated pin change: the pins before and after.

    ``kind`` is ``"pinned"`` or ``"unpinned"``; ``path`` is
    the file the change names.
    """

    kind: str
    path: str
    before: Tuple[str, ...]
    after: Tuple[str, ...]

    def event(self) -> Dict[str, Any]:
        """The session-event payload for this change."""
        return {"type": "repo_map_pins_changed",
                "action": self.kind, "path": self.path,
                "from": list(self.before), "to": list(self.after)}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        """The change record the agent returns to its callers."""
        return {"kind": self.kind, "path": self.path,
                "from": list(self.before), "to": list(self.after),
                "session_id": session_id, "journaled": journaled}


def pin_file(config: Dict[str, Any], path: Any
             ) -> Tuple[List[str], PinChange]:
    """Pin one file; return (stored pins, change).

    Pure: *config* is not mutated. Pinning a file that is
    already pinned is refused plainly — no change happened,
    so none is recorded.
    """
    before = pins_from_config(config)
    named = normalize_pin_path(path)
    if named in before:
        raise ValueError(
            f"{named} is already pinned; it is already shown "
            "first when you browse the map.")
    after = before + (named,)
    return list(after), PinChange(
        kind="pinned", path=named, before=before, after=after)


def unpin_file(config: Dict[str, Any], path: Any
               ) -> Tuple[List[str], PinChange]:
    """Unpin one file; return (stored pins, change).

    Pure: *config* is not mutated. Unpinning a file that is
    not pinned is refused plainly — no change happened, so
    none is recorded.
    """
    before = pins_from_config(config)
    named = normalize_pin_path(path)
    if named not in before:
        raise ValueError(
            f"{named} is not pinned, so there is nothing to "
            "unpin; see your pins with /map pins.")
    after = tuple(p for p in before if p != named)
    return list(after), PinChange(
        kind="unpinned", path=named, before=before, after=after)


@dataclass(frozen=True)
class ViewEntry:
    """One mapped file as the browse list presents it.

    ``rank`` is the file's true M-044 rank (1-based, in the
    map's own order) — display order never rewrites it.
    ``reasons`` is the entry's own reasons, plus the pin
    reason when the file is pinned.
    """

    entry: MapEntry
    rank: int
    pinned: bool
    reasons: Tuple[str, ...]

    @property
    def path(self) -> str:
        return self.entry.path

    def record(self) -> Dict[str, Any]:
        """This view entry as a plain mapping."""
        record = self.entry.record()
        record["rank"] = self.rank
        record["pinned"] = self.pinned
        record["reasons"] = list(self.reasons)
        return record


@dataclass(frozen=True)
class UnmappedPin:
    """One pinned file the map build did not rank.

    ``state`` is ``omitted`` (ranked but over the budget),
    ``skipped`` (the build could not parse it — ``reason``
    is the build's own skip reason), or ``absent`` (no such
    mappable file in this build).
    """

    path: str
    state: str
    reason: str

    def record(self) -> Dict[str, Any]:
        """This unmapped pin as a plain mapping."""
        return {"path": self.path, "state": self.state,
                "reason": self.reason}


@dataclass(frozen=True)
class RepoMapView:
    """One built map, presented: entries in display order.

    Display order is pinned files first (in rank order),
    then the rest in rank order. ``entries`` carries each
    file's true rank, so the presentation can always be
    checked against the map itself.
    """

    workspace: str
    query: str
    budget_tokens: int
    entries: Tuple[ViewEntry, ...]
    omitted: Tuple[str, ...]
    skipped: Tuple[Dict[str, str], ...]
    warnings: Tuple[str, ...]
    files_seen: int
    pins: Tuple[str, ...]
    unmapped_pins: Tuple[UnmappedPin, ...]

    def record(self) -> Dict[str, Any]:
        """This view as a plain mapping."""
        return {
            "slice": MAP_VIEW_SLICE,
            "workspace": self.workspace, "query": self.query,
            "budget_tokens": self.budget_tokens,
            "entries": [e.record() for e in self.entries],
            "omitted": list(self.omitted),
            "skipped": [dict(s) for s in self.skipped],
            "warnings": list(self.warnings),
            "files_seen": self.files_seen,
            "pins": list(self.pins),
            "unmapped_pins": [p.record() for p in self.unmapped_pins],
        }


def build_map_view(repo_map: RepoMap,
                   pins: Tuple[str, ...]) -> RepoMapView:
    """Present *repo_map* for browsing, with *pins* honoured.

    The map's entries keep their M-044 order as their rank;
    the view's display order is pinned entries first (rank
    order among themselves), then unpinned entries in rank
    order. Scores and reasons are the map's own, verbatim —
    the only added words are the pin reason on a pinned
    entry. A pin the build did not rank becomes an
    :class:`UnmappedPin` with its honest state.
    """
    pin_set = set(pins)
    ranked: List[ViewEntry] = []
    for index, entry in enumerate(repo_map.entries, start=1):
        pinned = entry.path in pin_set
        reasons = list(entry.reasons)
        if pinned:
            reasons.append(
                "pinned by you — shown first; its rank and "
                "score are the map's own, unchanged")
        ranked.append(ViewEntry(
            entry=entry, rank=index, pinned=pinned,
            reasons=tuple(reasons)))
    display = tuple(
        [e for e in ranked if e.pinned]
        + [e for e in ranked if not e.pinned])
    mapped = {e.path for e in ranked}
    skipped_by_path = {s.path: s.reason for s in repo_map.skipped}
    unmapped: List[UnmappedPin] = []
    for pin in pins:
        if pin in mapped:
            continue
        if pin in repo_map.omitted:
            unmapped.append(UnmappedPin(
                path=pin, state="omitted",
                reason=(
                    "pinned, but this build ranked it beyond "
                    f"the map's {repo_map.budget_tokens}-token "
                    "budget, so it is named as omitted — narrow "
                    "the task or browse again and it may fit")))
        elif pin in skipped_by_path:
            unmapped.append(UnmappedPin(
                path=pin, state="skipped",
                reason=(
                    "pinned, but the map could not parse it: "
                    f"{skipped_by_path[pin]}")))
        else:
            unmapped.append(UnmappedPin(
                path=pin, state="absent",
                reason=(
                    "pinned, but no such mappable file was "
                    "found in this workspace build — the file "
                    "may have moved, or its language is not "
                    "one the map catalogues")))
    return RepoMapView(
        workspace=repo_map.workspace, query=repo_map.query,
        budget_tokens=repo_map.budget_tokens, entries=display,
        omitted=repo_map.omitted,
        skipped=tuple(s.record() for s in repo_map.skipped),
        warnings=repo_map.warnings,
        files_seen=repo_map.files_seen, pins=tuple(pins),
        unmapped_pins=tuple(unmapped))


@dataclass(frozen=True)
class MapDetail:
    """The view's answer for one file.

    ``state`` is ``mapped`` (``entry`` carries the full
    detail), ``omitted``, ``skipped``, or ``absent`` — for
    the unmapped states ``reason`` says why, in the build's
    own words where the build has words.
    """

    path: str
    state: str
    entry: Optional[ViewEntry]
    reason: Optional[str]

    def record(self) -> Dict[str, Any]:
        """This detail as a plain mapping."""
        return {
            "slice": MAP_VIEW_SLICE, "path": self.path,
            "state": self.state,
            "entry": (self.entry.record()
                      if self.entry is not None else None),
            "reason": self.reason,
        }


def _resolve_path(repo_map: RepoMap, named: str) -> str:
    """Resolve a user-named file to the map's own spelling.

    An exact path wins. Otherwise a unique match — the name
    is a file's base name, or the tail of exactly one known
    path — resolves to that path. Several matches raise
    :class:`ValueError` naming them all; no match returns
    the name as given (the caller reports it absent).
    """
    known = ([e.path for e in repo_map.entries]
             + list(repo_map.omitted)
             + [s.path for s in repo_map.skipped])
    if named in known:
        return named
    matches = sorted({
        path for path in known
        if path.rsplit("/", 1)[-1] == named
        or path.endswith("/" + named)})
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise ValueError(
            f"{named!r} names more than one file in the map: "
            f"{', '.join(matches)} — give the fuller path.")
    return named


def resolve_detail(repo_map: RepoMap, pins: Tuple[str, ...],
                   path: Any) -> MapDetail:
    """One file's full account from *repo_map*.

    The name is resolved as the user gave it (see
    :func:`_resolve_path`). A mapped file's detail is its
    view entry — rank, score, and reasons exactly as the
    browse list carries them. An unmapped file's detail is
    its honest state and reason, never an invented entry.
    """
    named = normalize_pin_path(path)
    resolved = _resolve_path(repo_map, named)
    view = build_map_view(repo_map, pins)
    for view_entry in view.entries:
        if view_entry.path == resolved:
            return MapDetail(path=resolved, state="mapped",
                             entry=view_entry, reason=None)
    for unmapped in view.unmapped_pins:
        if unmapped.path == resolved:
            return MapDetail(path=resolved, state=unmapped.state,
                             entry=None, reason=unmapped.reason)
    skipped_by_path = {s.path: s.reason for s in repo_map.skipped}
    if resolved in repo_map.omitted:
        return MapDetail(
            path=resolved, state="omitted", entry=None,
            reason=(
                "The map ranked this file beyond its "
                f"{repo_map.budget_tokens}-token budget for "
                "this build, so it is named as omitted — it "
                "has a rank the budget did not leave room to "
                "show."))
    if resolved in skipped_by_path:
        return MapDetail(
            path=resolved, state="skipped", entry=None,
            reason=(
                "The map could not parse this file: "
                f"{skipped_by_path[resolved]}"))
    return MapDetail(
        path=resolved, state="absent", entry=None,
        reason=(
            "No such mappable file was found in this "
            "workspace build — the file may not exist, or "
            "its language is not one the map catalogues."))


def parse_map_args(text: Any) -> Dict[str, Any]:
    """Parse the ``/map`` slash-command argument string.

    Grammar::

        /map                    -> browse the map (no task)
        /map <task words>       -> browse, ranked for the task
        /map show <path>        -> one file's full detail
        /map pin <path>         -> pin a file
        /map unpin <path>       -> unpin a file
        /map pins               -> list the pins

    The verbs ``show`` / ``pin`` / ``unpin`` / ``pins`` are
    reserved as first words; any other text is the task the
    map is ranked for. Returns a dict with keys ``action``
    (``list`` / ``detail`` / ``pin`` / ``unpin`` / ``pins``),
    ``query`` and ``path``. Raises :class:`ValueError` on a
    usage error.
    """
    if text is None:
        text = ""
    if not isinstance(text, str):
        raise ValueError(
            f"Map arguments must be text, got {type(text).__name__}")
    stripped = text.strip()
    if not stripped:
        return {"action": "list", "query": "", "path": None}
    head, _, rest = stripped.partition(" ")
    verb = head.lower()
    rest = rest.strip()
    if verb == "pins":
        if rest:
            raise ValueError(_USAGE)
        return {"action": "pins", "query": "", "path": None}
    if verb in ("show", "pin", "unpin"):
        if not rest or len(rest.split()) != 1:
            raise ValueError(_USAGE)
        action = {"show": "detail", "pin": "pin",
                  "unpin": "unpin"}[verb]
        return {"action": action, "query": "", "path": rest}
    return {"action": "list", "query": stripped, "path": None}


def format_map_view(status: Dict[str, Any]) -> str:
    """The browse list, from an Agent map-status mapping."""
    view = status["view"]
    lines = [
        f"Repo map ({MAP_VIEW_SLICE}): {len(view['entries'])} "
        f"file(s) mapped of {view['files_seen']} seen "
        f"(budget {view['budget_tokens']} tokens)."]
    if view["query"]:
        lines.append(f"Ranked for the task: {view['query']}")
    if not view["entries"]:
        lines.append(
            "  The map is empty for this workspace — no "
            "mappable files were ranked inside the budget.")
    for view_entry in view["entries"]:
        marker = " [pinned]" if view_entry["pinned"] else ""
        lines.append(
            f"  #{view_entry['rank']} {view_entry['path']}{marker}"
            f" — score {view_entry['score']:.4f} "
            f"(PageRank {view_entry['pagerank']:.4f})")
        for reason in view_entry["reasons"]:
            lines.append(f"      {reason}")
    if view["omitted"]:
        lines.append(
            "  Beyond the budget, named not dropped: "
            f"{', '.join(view['omitted'])}")
    for skipped in view["skipped"]:
        lines.append(
            f"  Skipped {skipped['path']}: {skipped['reason']}")
    for unmapped in view["unmapped_pins"]:
        lines.append(
            f"  Pinned but {unmapped['state']}: "
            f"{unmapped['path']} — {unmapped['reason']}")
    for warning in view["warnings"]:
        lines.append(f"  Warning: {warning}")
    lines.append(PLAIN_EXPLANATION)
    return "\n".join(lines)


def format_map_detail(status: Dict[str, Any]) -> str:
    """One file's full account, from an Agent detail mapping."""
    detail = status["detail"]
    if detail["state"] != "mapped":
        return (
            f"{detail['path']} — {detail['state']}: "
            f"{detail['reason']}\n{PLAIN_EXPLANATION}")
    entry = detail["entry"]
    lines = [
        f"{entry['path']} — rank #{entry['rank']} in the map"
        + (" (pinned by you — shown first when browsing; the"
           " rank and score are unchanged)"
           if entry["pinned"] else ""),
        f"  Score {entry['score']:.4f} = PageRank "
        f"{entry['pagerank']:.4f} × "
        f"{(entry['score'] / entry['pagerank'] if entry['pagerank'] else 0.0):.2f}"
        " (task matches multiply the rank; see the reasons).",
        f"  Language {entry['language']}, parsed by "
        f"{entry['backend']}.",
    ]
    if entry["definitions"]:
        lines.append("  Defines:")
        for definition in entry["definitions"]:
            lines.append(
                f"    {definition['signature']} "
                f"(line {definition['line']})")
    else:
        lines.append("  Defines no symbols the catalogue extracts.")
    if entry["references_in"]:
        lines.append(
            f"  Referenced by: {', '.join(entry['references_in'])}")
    if entry["references_out"]:
        lines.append(
            f"  References: {', '.join(entry['references_out'])}")
    lines.append("  Why the coder thinks it matters:")
    for reason in entry["reasons"]:
        lines.append(f"    {reason}")
    lines.append(PLAIN_EXPLANATION)
    return "\n".join(lines)


def format_map_pins(status: Dict[str, Any]) -> str:
    """The pin list, from an Agent pins mapping."""
    pins = status["pins"]
    if not pins:
        return (
            "No files are pinned. Pin one with /map pin "
            "<path> and it is shown first whenever you browse "
            f"the map.\n{PLAIN_EXPLANATION}")
    lines = ["Pinned files (shown first when you browse):"]
    lines.extend(f"  {path}" for path in pins)
    lines.append(PLAIN_EXPLANATION)
    return "\n".join(lines)


def format_map_change(record: Dict[str, Any]) -> str:
    """One plain sentence describing a completed pin change."""
    if record["kind"] == "pinned":
        text = (
            f"Pinned {record['path']}: it is shown first "
            "whenever you browse the map, with its rank and "
            "score unchanged.")
    else:
        text = (
            f"Unpinned {record['path']}: it browses in its "
            "rank order again.")
    if record.get("session_id"):
        text += f" Recorded on session {record['session_id']}."
    return text
